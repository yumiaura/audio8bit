"""DSP core: turn a song into a recognizable monophonic 8-bit melody.

The pipeline isolates the sung melody and replays it with a single square-wave
voice — the sound of old monophonic phone ringtones and early game consoles:

* vocal isolation — Demucs (a neural source-separation model) extracts the
  vocal stem, i.e. the sung melody on its own, dropping the backing;
* pitch tracking — librosa's pYIN follows the fundamental frequency (f0) of the
  isolated, now-monophonic voice over time, which is far more reliable than
  analysing a full mix;
* square-wave synthesis — one phase-continuous square voice replays the pitch
  contour (optionally snapped to musical semitones), gated by voicing;
* 8-bit output — the voice is quantised to 8-bit unsigned PCM at a low sample
  rate and written as WAV, or re-encoded by ffmpeg to the chosen format.

Demucs and librosa are heavy dependencies (Demucs pulls in PyTorch and
downloads model weights on first use), so they are imported lazily with a
clear message if they are missing. "Remove the words, keep the melody": the
lyrics and vocal timbre are gone, only the tune remains.
"""

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

DEMUCS_MODEL = "htdemucs"
HOP = 512
PITCH_FMIN = 65.0
PITCH_FMAX = 2093.0

DEFAULT_RATE = 8000
DEFAULT_BITS = 8
DEFAULT_DUTY = 0.5


class ConversionError(Exception):
    """Raised when conversion fails for a reason worth showing to the user."""


def require_tool(name):
    """Return the absolute path to a required external tool or raise."""
    path = shutil.which(name)
    if path is None:
        raise ConversionError(
            f"'{name}' not found. Install ffmpeg (it ships ffmpeg and ffprobe), "
            "e.g. 'sudo apt install ffmpeg' or 'brew install ffmpeg'."
        )
    return path


def separate_vocals(path):
    """Isolate the vocal stem with Demucs and return (mono_signal, sample_rate)."""
    try:
        import torch
        from demucs.apply import apply_model
        from demucs.audio import AudioFile
        from demucs.pretrained import get_model
    except ImportError as missing:
        raise ConversionError(
            "demucs is required to isolate the melody. "
            "Install it with 'pip install demucs librosa'."
        ) from missing

    model = get_model(DEMUCS_MODEL)
    model.cpu().eval()
    if "vocals" not in model.sources:
        raise ConversionError(
            f"Demucs model has no 'vocals' stem (got: {', '.join(model.sources)})."
        )

    wav = AudioFile(str(path)).read(
        streams=0, samplerate=model.samplerate, channels=model.audio_channels,
    )
    reference = wav.mean(0)
    wav = (wav - reference.mean()) / (reference.std() + 1e-8)
    with torch.no_grad():
        sources = apply_model(model, wav[None], device="cpu", progress=False)[0]
    sources = sources * reference.std() + reference.mean()

    vocals = sources[model.sources.index("vocals")].mean(0)
    return vocals.cpu().numpy().astype(np.float32), int(model.samplerate)


def track_pitch(signal, sample_rate, hop=HOP, fmin=PITCH_FMIN, fmax=PITCH_FMAX):
    """Follow the fundamental frequency of a monophonic signal with pYIN.

    Returns (f0, voiced): f0 in Hz (0 where unvoiced) and a boolean mask, one
    value per analysis frame.
    """
    try:
        import librosa
    except ImportError as missing:
        raise ConversionError(
            "librosa is required for pitch tracking. "
            "Install it with 'pip install demucs librosa'."
        ) from missing

    f0, voiced_flag, voiced_prob = librosa.pyin(
        signal, sr=sample_rate, fmin=fmin, fmax=fmax, hop_length=hop,
    )
    f0 = np.nan_to_num(f0, nan=0.0)
    voiced = np.asarray(voiced_flag, dtype=bool) & (f0 > 0)
    return f0.astype(np.float64), voiced


def smooth_pitch(f0, voiced, window=5):
    """Median-filter the voiced f0 values to suppress octave jumps and spikes."""
    if f0.size == 0:
        return f0
    out = f0.copy()
    half = window // 2
    for index in range(f0.size):
        if not voiced[index]:
            continue
        lo, hi = max(0, index - half), min(f0.size, index + half + 1)
        neighbourhood = f0[lo:hi][voiced[lo:hi]]
        if neighbourhood.size:
            out[index] = float(np.median(neighbourhood))
    return out


def snap_to_semitones(f0):
    """Snap each positive f0 to the nearest equal-temperament semitone."""
    out = np.zeros_like(f0)
    tuned = f0 > 0
    midi = np.round(69.0 + 12.0 * np.log2(f0[tuned] / 440.0))
    out[tuned] = 440.0 * 2.0 ** ((midi - 69.0) / 12.0)
    return out


def synthesize_square(f0, voiced, hop, analysis_rate, out_rate, duty=DEFAULT_DUTY):
    """Render the pitch contour as a single phase-continuous square voice."""
    frames = f0.size
    total = int(frames * hop / analysis_rate * out_rate)
    if total <= 0:
        return np.zeros(0, dtype=np.float32)

    positions = np.arange(total) * analysis_rate / (hop * out_rate)
    frame_index = np.minimum(positions.astype(int), frames - 1)
    pitch = f0[frame_index]
    gate = smooth_gate(voiced[frame_index].astype(np.float32), out_rate)

    phase = np.cumsum(2.0 * np.pi * pitch / out_rate)
    wave_shape = np.where((phase % (2.0 * np.pi)) < duty * 2.0 * np.pi, 1.0, -1.0)
    return (wave_shape * gate * 0.7).astype(np.float32)


def smooth_gate(gate, sample_rate):
    """Round voicing on/off edges over ~5 ms to avoid clicks."""
    width = max(1, int(0.005 * sample_rate))
    kernel = np.ones(width) / width
    return np.convolve(gate, kernel, mode="same")


def quantize(samples, bits):
    """Quantise [-1, 1] float samples to `bits` levels, return float in [-1, 1]."""
    levels = (1 << bits) - 1
    clipped = np.clip(samples, -1.0, 1.0)
    stepped = np.round((clipped + 1.0) * 0.5 * levels)
    return stepped / levels * 2.0 - 1.0


def to_uint8(samples):
    """Map [-1, 1] float samples to 8-bit unsigned PCM bytes (centre 128)."""
    scaled = np.round((np.clip(samples, -1.0, 1.0) + 1.0) * 0.5 * 255.0)
    return scaled.astype(np.uint8)


def write_wav(path, samples_u8, sample_rate, channels):
    """Write interleaved uint8 samples as an 8-bit unsigned PCM WAV file."""
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(1)
        handle.setframerate(sample_rate)
        handle.writeframes(samples_u8.reshape(-1).tobytes())


def reencode(wav_path, output_path):
    """Re-encode a WAV into another container/codec chosen by output extension."""
    ffmpeg = require_tool("ffmpeg")
    command = [ffmpeg, "-v", "error", "-y", "-i", str(wav_path), str(output_path)]
    completed = subprocess.run(command, capture_output=True)
    if completed.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed to write '{output_path}': "
            f"{completed.stderr.decode(errors='replace').strip()}"
        )


def resolve_output_path(input_path, output_path=None, format=None):
    """Decide where to write the result.

    Precedence: an explicit ``output_path`` wins; otherwise the base name is
    always ``output`` and the extension comes from ``format`` when given, or
    falls back to the input file's own extension (so the original format is
    preserved by default).
    """
    if output_path:
        return Path(output_path)
    if format:
        return Path(f"output.{format.lstrip('.').lower()}")
    suffix = Path(input_path).suffix or ".wav"
    return Path(f"output{suffix}")


def write_output(destination, samples_u8, sample_rate, channels):
    """Write 8-bit samples to destination, re-encoding when it is not WAV."""
    if destination.suffix.lower() == ".wav":
        write_wav(destination, samples_u8, sample_rate, channels)
        return
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        tmp_wav = Path(handle.name)
    try:
        write_wav(tmp_wav, samples_u8, sample_rate, channels)
        reencode(tmp_wav, destination)
    finally:
        tmp_wav.unlink(missing_ok=True)


def convert(input_path, output_path=None, format=None, bits=DEFAULT_BITS,
            rate=DEFAULT_RATE, duty=DEFAULT_DUTY, semitones=True):
    """Convert a song into a monophonic 8-bit melody and write it to disk.

    Returns the path that was written.
    """
    source = Path(input_path)
    if not source.is_file():
        raise ConversionError(f"Input file not found: '{input_path}'")
    if not 1 <= bits <= 8:
        raise ConversionError(f"--bits must be between 1 and 8, got {bits}")
    if rate < 1000:
        raise ConversionError(f"--rate must be at least 1000 Hz, got {rate}")
    if not 0.0 < duty < 1.0:
        raise ConversionError(f"--duty must be between 0 and 1, got {duty}")

    destination = resolve_output_path(source, output_path, format)

    vocals, sample_rate = separate_vocals(source)
    f0, voiced = track_pitch(vocals, sample_rate)
    if not voiced.any():
        raise ConversionError(
            "No sung melody could be detected (the vocal stem may be empty or "
            "have no clear pitch)."
        )
    f0 = smooth_pitch(f0, voiced)
    if semitones:
        f0 = snap_to_semitones(f0)

    voice = synthesize_square(f0, voiced, HOP, sample_rate, rate, duty)
    samples_u8 = to_uint8(quantize(voice, bits))
    write_output(destination, samples_u8, rate, 1)
    return destination
