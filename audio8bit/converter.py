"""DSP core: turn a song into a monophonic 8-bit melody.

The pipeline strips the vocals, follows the leading pitch and replays it with a
single square-wave voice — the sound of old monophonic phone ringtones and
early game consoles:

* vocal removal — for stereo input, centre-panned content (lead vocals, and
  usually kick/bass) is cancelled by subtracting the channels (``L - R``),
  leaving the backing instruments whose melody we follow;
* pitch tracking — short overlapping frames are analysed by autocorrelation to
  estimate the fundamental frequency (f0) over time, with a voiced/unvoiced
  gate;
* square-wave synthesis — a single phase-continuous square voice replays the
  pitch contour (optionally snapped to musical semitones), gated by voicing;
* 8-bit output — the voice is quantised to 8-bit unsigned PCM at a low sample
  rate and written as WAV, or re-encoded by ffmpeg to the chosen format.

Everything runs on numpy and ffmpeg only — no machine-learning dependencies.
The melody is extracted from a full mix, so the result is an approximation,
not a transcription.
"""

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

ANALYSIS_RATE = 22050
FRAME = 2048
HOP = 512
FMIN = 80.0
FMAX = 1000.0
VOICED_THRESHOLD = 0.3

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


def probe_audio(path):
    """Return (sample_rate, channels) of the input via ffprobe."""
    ffprobe = require_tool("ffprobe")
    command = [
        ffprobe, "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels",
        "-of", "csv=p=0", str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0 or not completed.stdout.strip():
        raise ConversionError(
            f"Could not read audio stream from '{path}'. "
            f"ffprobe said: {completed.stderr.strip() or 'no audio stream found'}"
        )
    fields = completed.stdout.strip().splitlines()[0].split(",")
    sample_rate, channels = int(fields[0]), int(fields[1])
    return sample_rate, channels


def decode_to_float(path, sample_rate, channels):
    """Decode the input to interleaved float32 samples via ffmpeg.

    Returns a 2-D array shaped (frames, channels) in the range [-1, 1].
    """
    ffmpeg = require_tool("ffmpeg")
    command = [
        ffmpeg, "-v", "error", "-i", str(path),
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", str(channels), "-ar", str(sample_rate),
        "pipe:1",
    ]
    completed = subprocess.run(command, capture_output=True)
    if completed.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed to decode '{path}': "
            f"{completed.stderr.decode(errors='replace').strip()}"
        )
    samples = np.frombuffer(completed.stdout, dtype=np.float32)
    if samples.size == 0:
        raise ConversionError(f"Decoded no audio samples from '{path}'.")
    return samples.reshape(-1, channels)


def remove_vocals(samples):
    """Cancel centre-panned content and return a mono signal.

    For stereo, ``L - R`` removes anything identical in both channels (lead
    vocals, and usually centred drums/bass), leaving the panned backing. Mono
    input has nothing to cancel and is passed through.
    """
    if samples.shape[1] >= 2:
        mono = samples[:, 0] - samples[:, 1]
    else:
        mono = samples[:, 0]
    return mono.astype(np.float32)


def track_pitch(signal, sample_rate, frame=FRAME, hop=HOP,
                fmin=FMIN, fmax=FMAX, voiced_threshold=VOICED_THRESHOLD):
    """Estimate the fundamental frequency per frame by autocorrelation.

    Returns (f0, voiced): f0 in Hz (0 where unvoiced) and a boolean mask, one
    value per analysis frame.
    """
    count = signal.size
    min_lag = max(2, int(sample_rate / fmax))
    max_lag = min(frame - 1, int(sample_rate / fmin))
    frames = 1 + max(0, (count - frame) // hop)
    f0 = np.zeros(frames, dtype=np.float64)
    voiced = np.zeros(frames, dtype=bool)
    if frames == 0 or max_lag <= min_lag:
        return f0, voiced

    global_rms = float(np.sqrt(np.mean(signal ** 2))) + 1e-9
    size = 1
    while size < 2 * frame:
        size <<= 1

    for index in range(frames):
        start = index * hop
        block = signal[start:start + frame]
        block = block - block.mean()
        if float(np.sqrt(np.mean(block ** 2))) < 0.1 * global_rms:
            continue
        spectrum = np.fft.rfft(block, size)
        autocorr = np.fft.irfft(spectrum * np.conj(spectrum))[:max_lag + 1]
        if autocorr[0] <= 0:
            continue
        peak = int(np.argmax(autocorr[min_lag:max_lag + 1])) + min_lag
        if autocorr[peak] / autocorr[0] < voiced_threshold:
            continue
        lag = refine_peak(autocorr, peak, max_lag)
        f0[index] = sample_rate / lag
        voiced[index] = True
    return f0, voiced


def refine_peak(autocorr, peak, max_lag):
    """Parabolic interpolation of an autocorrelation peak for sub-sample lag."""
    if peak <= 0 or peak >= max_lag:
        return float(peak)
    left, centre, right = autocorr[peak - 1], autocorr[peak], autocorr[peak + 1]
    denominator = left - 2.0 * centre + right
    if denominator == 0:
        return float(peak)
    return peak + 0.5 * (left - right) / denominator


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

    src_rate, src_channels = probe_audio(source)
    channels = 2 if src_channels >= 2 else 1
    samples = decode_to_float(source, ANALYSIS_RATE, channels)

    mono = remove_vocals(samples)
    f0, voiced = track_pitch(mono, ANALYSIS_RATE)
    f0 = smooth_pitch(f0, voiced)
    if semitones:
        f0 = snap_to_semitones(f0)
    if not voiced.any():
        raise ConversionError(
            "No melody could be detected (the track may be silent after vocal "
            "removal, or have no clear pitch)."
        )

    voice = synthesize_square(f0, voiced, HOP, ANALYSIS_RATE, rate, duty)
    samples_u8 = to_uint8(quantize(voice, bits))
    write_output(destination, samples_u8, rate, 1)
    return destination
