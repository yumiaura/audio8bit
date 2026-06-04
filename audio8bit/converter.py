"""DSP core: decode any audio with ffmpeg, bitcrush it, write 8-bit PCM WAV.

The "8-bit" character comes from a classic bitcrusher made of two stages:

* sample-rate decimation (sample & hold) — drops the effective rate to a low
  value (default 8 kHz), producing aliasing and the "pixelated" feel;
* bit-depth reduction — quantises sample amplitudes to a few levels (default
  8 bits, i.e. 256 steps), producing the gritty, stepped sound.

The result is written as real 8-bit unsigned PCM (`pcm_u8`) WAV via the stdlib
`wave` module. If the requested output is not a `.wav`, ffmpeg re-encodes the
crushed WAV into the chosen container (the 8-bit character is already baked
into the samples).
"""

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

DEFAULT_RATE = 8000
DEFAULT_BITS = 8


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


def decimate(samples, factor):
    """Sample-and-hold down by an integer factor, then keep one in every factor.

    Holding the value before decimating preserves the aliased, crunchy
    character rather than cleanly low-passing it out.
    """
    if factor <= 1:
        return samples
    frames = (samples.shape[0] // factor) * factor
    if frames == 0:
        return samples[:1]
    trimmed = samples[:frames]
    held = trimmed.reshape(-1, factor, samples.shape[1])[:, 0, :]
    return held


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


def default_output_for(input_path):
    """Return the default output path '<stem>_8bit.wav' next to the input."""
    source = Path(input_path)
    return source.with_name(f"{source.stem}_8bit.wav")


def convert(input_path, output_path=None, bits=DEFAULT_BITS,
            rate=DEFAULT_RATE, mono=False):
    """Convert an audio file to 8-bit sound and write it to disk.

    Returns the path that was written.
    """
    source = Path(input_path)
    if not source.is_file():
        raise ConversionError(f"Input file not found: '{input_path}'")
    if not 1 <= bits <= 8:
        raise ConversionError(f"--bits must be between 1 and 8, got {bits}")
    if rate < 1000:
        raise ConversionError(f"--rate must be at least 1000 Hz, got {rate}")

    destination = Path(output_path) if output_path else default_output_for(source)

    src_rate, src_channels = probe_audio(source)
    channels = 1 if mono else src_channels
    samples = decode_to_float(source, src_rate, channels)

    factor = max(1, src_rate // rate)
    target_rate = src_rate // factor

    crushed = quantize(decimate(samples, factor), bits)
    samples_u8 = to_uint8(crushed)

    if destination.suffix.lower() == ".wav":
        write_wav(destination, samples_u8, target_rate, channels)
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_wav = Path(tmp.name)
        try:
            write_wav(tmp_wav, samples_u8, target_rate, channels)
            reencode(tmp_wav, destination)
        finally:
            tmp_wav.unlink(missing_ok=True)

    return destination
