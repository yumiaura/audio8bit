"""Tests for the on-disk Demucs stem cache."""

import json

import numpy as np
import pytest

from audio8bit import cache


STEMS = {
    "drums": np.linspace(-1.0, 1.0, 500, dtype=np.float32),
    "bass": np.linspace(1.0, -1.0, 500, dtype=np.float32),
    "other": np.zeros(500, dtype=np.float32),
    "vocals": np.full(500, 0.25, dtype=np.float32),
}


class TestDefaultCacheRoot:

    def test_the_environment_variable_wins(self, monkeypatch, tmp_path):
        monkeypatch.setenv("AUDIO8BIT_CACHE_DIR", str(tmp_path / "custom"))
        assert cache.default_cache_root() == tmp_path / "custom"

    def test_expands_a_user_relative_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("AUDIO8BIT_CACHE_DIR", "~/audio8bit-cache")
        assert cache.default_cache_root() == cache.Path.home() / "audio8bit-cache"

    def test_falls_back_to_the_home_cache(self, monkeypatch):
        monkeypatch.delenv("AUDIO8BIT_CACHE_DIR", raising=False)
        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        root = cache.default_cache_root()
        assert root.name == "audio8bit"


class TestCacheKey:

    def test_is_stable(self):
        payload = cache.cache_payload(input_sha256="a" * 64,
                                      demucs_model="htdemucs",
                                      separation_seed=0, shifts=0)
        assert cache.cache_key(payload) == cache.cache_key(payload)

    def test_ignores_key_order(self):
        payload = {"b": 1, "a": 2}
        assert cache.cache_key(payload) == cache.cache_key({"a": 2, "b": 1})

    def test_changes_when_the_input_changes(self):
        first = cache.cache_payload(input_sha256="a" * 64,
                                    demucs_model="htdemucs",
                                    separation_seed=0, shifts=0)
        second = cache.cache_payload(input_sha256="b" * 64,
                                     demucs_model="htdemucs",
                                     separation_seed=0, shifts=0)
        assert cache.cache_key(first) != cache.cache_key(second)

    def test_changes_when_the_model_changes(self):
        first = cache.cache_payload(input_sha256="a" * 64,
                                    demucs_model="htdemucs",
                                    separation_seed=0, shifts=0)
        second = cache.cache_payload(input_sha256="a" * 64,
                                     demucs_model="htdemucs_ft",
                                     separation_seed=0, shifts=0)
        assert cache.cache_key(first) != cache.cache_key(second)


class TestWavRoundTrip:

    def test_preserves_every_sample(self, tmp_path):
        path = tmp_path / "stem.wav"
        cache.write_float32_wav(path, STEMS["drums"], 44100)
        signal, rate = cache.read_float32_wav(path)
        assert rate == 44100
        assert np.array_equal(signal, STEMS["drums"])

    def test_rejects_a_multichannel_signal(self, tmp_path):
        path = tmp_path / "stereo.wav"
        with pytest.raises(ValueError):
            cache.write_float32_wav(path, np.zeros((10, 2), dtype=np.float32),
                                    44100)

    def test_writes_atomically(self, tmp_path):
        path = tmp_path / "stem.wav"
        cache.write_float32_wav(path, STEMS["drums"], 44100)
        assert not path.with_suffix(".wav.tmp").exists()

    def test_reads_a_16bit_pcm_file_too(self, tmp_path):
        path = tmp_path / "pcm16.wav"
        samples = (np.linspace(-1.0, 1.0, 100) * 32767).astype("<i2")
        import struct
        data = samples.tobytes()
        with path.open("wb") as handle:
            handle.write(b"RIFF")
            handle.write(struct.pack("<I", 36 + len(data)))
            handle.write(b"WAVEfmt ")
            handle.write(struct.pack("<IHHIIHH", 16, 1, 1, 44100, 88200, 2, 16))
            handle.write(b"data")
            handle.write(struct.pack("<I", len(data)))
            handle.write(data)
        signal, rate = cache.read_float32_wav(path)
        assert rate == 44100
        assert np.allclose(signal, samples / 32768.0, atol=1e-4)

    def test_rejects_a_file_that_is_not_a_wav(self, tmp_path):
        path = tmp_path / "junk.wav"
        path.write_bytes(b"not a riff file at all")
        with pytest.raises(ValueError):
            cache.read_float32_wav(path)


class TestStemCache:

    def key(self, tmp_path, sha):
        payload = cache.cache_payload(input_sha256=sha,
                                      demucs_model="htdemucs",
                                      separation_seed=0, shifts=0)
        return payload

    def test_round_trips_every_stem(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        saved = cache.save_cached_stems(source, STEMS, 44100,
                                        demucs_model="htdemucs",
                                        separation_seed=0, shifts=0,
                                        cache_dir=tmp_path)
        assert saved.is_dir()
        loaded = cache.load_cached_stems(source, demucs_model="htdemucs",
                                         separation_seed=0, shifts=0,
                                         cache_dir=tmp_path)
        assert loaded is not None
        stems, rate = loaded
        assert rate == 44100
        assert set(stems) == set(STEMS)
        for name, signal in STEMS.items():
            assert np.array_equal(stems[name], signal)

    def test_a_missing_entry_returns_none(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        assert cache.load_cached_stems(source, demucs_model="htdemucs",
                                       separation_seed=0, shifts=0,
                                       cache_dir=tmp_path) is None

    def test_a_different_input_misses_the_cache(self, tmp_path):
        first = tmp_path / "one.mp3"
        second = tmp_path / "two.mp3"
        first.write_bytes(b"one")
        second.write_bytes(b"two")
        cache.save_cached_stems(first, STEMS, 44100, demucs_model="htdemucs",
                                separation_seed=0, shifts=0, cache_dir=tmp_path)
        assert cache.load_cached_stems(second, demucs_model="htdemucs",
                                       separation_seed=0, shifts=0,
                                       cache_dir=tmp_path) is None

    def test_a_different_model_misses_the_cache(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        cache.save_cached_stems(source, STEMS, 44100, demucs_model="htdemucs",
                                separation_seed=0, shifts=0, cache_dir=tmp_path)
        assert cache.load_cached_stems(source, demucs_model="htdemucs_ft",
                                       separation_seed=0, shifts=0,
                                       cache_dir=tmp_path) is None

    def test_a_corrupt_entry_returns_none(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        cache.save_cached_stems(source, STEMS, 44100, demucs_model="htdemucs",
                                separation_seed=0, shifts=0, cache_dir=tmp_path)
        entry, _ = cache.stem_cache_dir(source, demucs_model="htdemucs",
                                        separation_seed=0, shifts=0,
                                        cache_dir=tmp_path)
        (entry / "metadata.json").write_text("{ not json", encoding="utf-8")
        assert cache.load_cached_stems(source, demucs_model="htdemucs",
                                       separation_seed=0, shifts=0,
                                       cache_dir=tmp_path) is None

    def test_a_missing_stem_file_returns_none(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        cache.save_cached_stems(source, STEMS, 44100, demucs_model="htdemucs",
                                separation_seed=0, shifts=0, cache_dir=tmp_path)
        entry, _ = cache.stem_cache_dir(source, demucs_model="htdemucs",
                                        separation_seed=0, shifts=0,
                                        cache_dir=tmp_path)
        (entry / "vocals.wav").unlink()
        assert cache.load_cached_stems(source, demucs_model="htdemucs",
                                       separation_seed=0, shifts=0,
                                       cache_dir=tmp_path) is None

    def test_metadata_records_the_payload(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        entry = cache.save_cached_stems(source, STEMS, 44100,
                                        demucs_model="htdemucs",
                                        separation_seed=0, shifts=0,
                                        cache_dir=tmp_path)
        metadata = json.loads((entry / "metadata.json").read_text("utf-8"))
        assert metadata["sample_rate"] == 44100
        assert sorted(metadata["stems"]) == sorted(STEMS)
        assert metadata["payload"]["input_sha256"] == cache.sha256_file(source)

    def test_rejects_an_unusable_stem_name(self, tmp_path):
        source = tmp_path / "song.mp3"
        source.write_bytes(b"fake audio")
        with pytest.raises(ValueError):
            cache.save_cached_stems(source, {"!!!": STEMS["drums"]}, 44100,
                                    demucs_model="htdemucs",
                                    separation_seed=0, shifts=0,
                                    cache_dir=tmp_path)


class TestSha256:

    def test_matches_hashlib(self, tmp_path):
        import hashlib
        path = tmp_path / "song.mp3"
        path.write_bytes(b"some bytes to hash")
        assert cache.sha256_file(path) == hashlib.sha256(
            b"some bytes to hash").hexdigest()
