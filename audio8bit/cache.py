from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path
from typing import Any

import numpy as np


CACHE_VERSION = 1
STEM_FORMAT = "float32-wav-mono-v1"
HASH_CHUNK_SIZE = 1024 * 1024


def default_cache_root() -> Path:
    """Return the default cache root.

    Priority:
    1. AUDIO8BIT_CACHE_DIR
    2. LOCALAPPDATA/audio8bit on Windows
    3. XDG_CACHE_HOME/audio8bit on Unix
    4. ~/.cache/audio8bit
    """

    override = os.environ.get("AUDIO8BIT_CACHE_DIR")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "audio8bit"
        return Path.home() / "AppData" / "Local" / "audio8bit"

    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        return Path(xdg_cache_home) / "audio8bit"

    return Path.home() / ".cache" / "audio8bit"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(HASH_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def cache_payload(
    *,
    input_sha256: str,
    demucs_model: str,
    separation_seed: int,
    shifts: int,
) -> dict[str, Any]:
    """Build the stable payload used to identify a stem cache entry."""

    return {
        "cache_version": CACHE_VERSION,
        "stem_format": STEM_FORMAT,
        "input_sha256": input_sha256,
        "demucs_model": demucs_model,
        "separation_seed": separation_seed,
        "shifts": shifts,
        "channels": "mono",
    }


def cache_key(payload: dict[str, Any]) -> str:
    """Return a stable cache key for a payload."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stem_cache_dir(
    input_path: Path,
    *,
    demucs_model: str,
    separation_seed: int,
    shifts: int,
    cache_dir: str | Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Return the cache directory and metadata payload for a source file."""

    input_sha256 = sha256_file(input_path)
    payload = cache_payload(
        input_sha256=input_sha256,
        demucs_model=demucs_model,
        separation_seed=separation_seed,
        shifts=shifts,
    )

    root = Path(cache_dir).expanduser() if cache_dir else default_cache_root()
    return root / "stems" / cache_key(payload), payload


def write_float32_wav(path: Path, signal: np.ndarray, sample_rate: int) -> None:
    """Write a mono float32 WAV without requiring scipy/soundfile.

    This writes WAVE_FORMAT_IEEE_FLOAT:
    - format tag: 3
    - channels: 1
    - bits per sample: 32
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    mono = np.asarray(signal, dtype="<f4")
    if mono.ndim != 1:
        raise ValueError("cached stems must be mono 1-D arrays")

    data = mono.tobytes()
    data_size = len(data)
    fmt_size = 16
    riff_size = 4 + (8 + fmt_size) + (8 + data_size)

    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with tmp_path.open("wb") as handle:
        handle.write(b"RIFF")
        handle.write(struct.pack("<I", riff_size))
        handle.write(b"WAVE")

        handle.write(b"fmt ")
        handle.write(struct.pack("<I", fmt_size))
        handle.write(
            struct.pack(
                "<HHIIHH",
                3,  # WAVE_FORMAT_IEEE_FLOAT
                1,  # mono
                int(sample_rate),
                int(sample_rate) * 4,
                4,
                32,
            )
        )

        handle.write(b"data")
        handle.write(struct.pack("<I", data_size))
        handle.write(data)

    os.replace(tmp_path, path)


def read_float32_wav(path: Path) -> tuple[np.ndarray, int]:
    """Read a mono/stereo float32 WAV written by write_float32_wav.

    Also accepts 16-bit PCM as a small convenience, but cache writes use
    float32 so stem amplitude is preserved.
    """

    with path.open("rb") as handle:
        if handle.read(4) != b"RIFF":
            raise ValueError(f"not a RIFF file: {path}")

        handle.read(4)

        if handle.read(4) != b"WAVE":
            raise ValueError(f"not a WAVE file: {path}")

        fmt: tuple[int, int, int, int] | None = None
        data: bytes | None = None

        while True:
            chunk_id = handle.read(4)
            if not chunk_id:
                break

            if len(chunk_id) != 4:
                raise ValueError(f"truncated WAV chunk in {path}")

            chunk_size = struct.unpack("<I", handle.read(4))[0]
            chunk_data = handle.read(chunk_size)

            if chunk_size % 2:
                handle.read(1)

            if chunk_id == b"fmt ":
                if chunk_size < 16:
                    raise ValueError(f"invalid fmt chunk in {path}")

                audio_format, channels, sample_rate, byte_rate, align, bits = struct.unpack(
                    "<HHIIHH",
                    chunk_data[:16],
                )
                fmt = (audio_format, channels, sample_rate, bits)

            elif chunk_id == b"data":
                data = chunk_data

        if fmt is None:
            raise ValueError(f"missing fmt chunk in {path}")

        if data is None:
            raise ValueError(f"missing data chunk in {path}")

        audio_format, channels, sample_rate, bits = fmt

        if channels < 1:
            raise ValueError(f"invalid channel count in {path}: {channels}")

        if audio_format == 3 and bits == 32:
            samples = np.frombuffer(data, dtype="<f4").astype(np.float32, copy=True)
        elif audio_format == 1 and bits == 16:
            samples = (
                np.frombuffer(data, dtype="<i2").astype(np.float32, copy=True) / 32768.0
            )
        else:
            raise ValueError(
                f"unsupported cached WAV format in {path}: "
                f"format={audio_format}, bits={bits}"
            )

        if samples.size % channels:
            raise ValueError(f"cached WAV has incomplete frames: {path}")

        samples = samples.reshape(-1, channels)

        if channels > 1:
            samples = samples.mean(axis=1)
        else:
            samples = samples[:, 0]

        return samples.astype(np.float32, copy=False), int(sample_rate)


def load_cached_stems(
    input_path: Path,
    *,
    demucs_model: str,
    separation_seed: int,
    shifts: int,
    cache_dir: str | Path | None = None,
) -> tuple[dict[str, np.ndarray], int] | None:
    """Load cached stems if a complete matching cache entry exists."""

    entry_dir, payload = stem_cache_dir(
        input_path,
        demucs_model=demucs_model,
        separation_seed=separation_seed,
        shifts=shifts,
        cache_dir=cache_dir,
    )

    metadata_path = entry_dir / "metadata.json"

    if not metadata_path.is_file():
        return None

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        if metadata.get("payload") != payload:
            return None

        sample_rate = int(metadata["sample_rate"])
        stem_names = list(metadata["stems"])

        stems: dict[str, np.ndarray] = {}

        for name in stem_names:
            stem_path = entry_dir / f"{name}.wav"

            if not stem_path.is_file():
                return None

            signal, stem_rate = read_float32_wav(stem_path)

            if stem_rate != sample_rate:
                return None

            stems[name] = signal

        return stems, sample_rate

    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def save_cached_stems(
    input_path: Path,
    stems: dict[str, np.ndarray],
    sample_rate: int,
    *,
    demucs_model: str,
    separation_seed: int,
    shifts: int,
    cache_dir: str | Path | None = None,
) -> Path:
    """Save separated stems and metadata to the cache."""

    entry_dir, payload = stem_cache_dir(
        input_path,
        demucs_model=demucs_model,
        separation_seed=separation_seed,
        shifts=shifts,
        cache_dir=cache_dir,
    )

    entry_dir.mkdir(parents=True, exist_ok=True)

    stem_names = sorted(stems)

    for name in stem_names:
        safe_name = "".join(char for char in name if char.isalnum() or char in "-_")
        if not safe_name:
            raise ValueError(f"invalid stem name: {name!r}")

        write_float32_wav(entry_dir / f"{safe_name}.wav", stems[name], sample_rate)

    metadata = {
        "payload": payload,
        "sample_rate": int(sample_rate),
        "stems": stem_names,
    }

    metadata_path = entry_dir / "metadata.json"
    tmp_metadata_path = metadata_path.with_suffix(".json.tmp")

    tmp_metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(tmp_metadata_path, metadata_path)

    return entry_dir
