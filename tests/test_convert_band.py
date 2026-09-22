"""End-to-end tests for the ``band``/``nes`` branch of ``convert()``.

The heavy dependencies (Demucs, basic-pitch, librosa) are replaced at the
module boundary, so the whole arrangement decision (key detection, snapping,
the chord arranger, the bass fallback and the quality report) still runs for
real on plain NumPy data.
"""

import numpy as np
import pytest

from audio8bit import converter as c

STEM_RATE = 44100
TEMPO = 120.0
SECONDS = 8.0
BEATS = np.arange(0.5, SECONDS, 0.5)


def make_stems():
    """A four-stem mix: a loud C major vocal, a quiet backing, bass and drums."""
    time = np.arange(int(STEM_RATE * SECONDS)) / STEM_RATE
    scale = [261.63, 329.63, 392.00, 523.25]        # C E G C
    vocals = np.zeros_like(time)
    for index, frequency in enumerate(scale):
        start, stop = index * 2, (index + 1) * 2
        window = (time >= start) & (time < stop)
        vocals[window] += 0.5 * np.sin(
            2.0 * np.pi * frequency * time[window])
    vocals *= 0.5
    other = 0.02 * np.sin(2.0 * np.pi * 1100.0 * time)
    bass = 0.4 * np.sin(2.0 * np.pi * 82.41 * time)      # E2
    drums = np.zeros_like(time)
    for onset in BEATS:
        drums[int(onset * STEM_RATE)] = 1.0
    return {"vocals": vocals.astype(np.float32),
            "other": other.astype(np.float32),
            "bass": bass.astype(np.float32),
            "drums": drums.astype(np.float32)}


def make_events():
    """The same C major ladder as note events, one note per beat.

    Pitch 66 (F#) is deliberately off the C major scale, so the tests can tell
    a run that snaps the notes from one that leaves them alone.
    """
    pitches = [60, 64, 67, 72, 64, 66, 72, 76, 67, 72, 76, 79, 72, 76, 79, 84]
    return [(beat, beat + 0.45, float(pitch), 0.9)
            for beat, pitch in zip(BEATS, pitches)]


@pytest.fixture
def band_run(monkeypatch, tmp_path):
    """Run ``convert()`` on the synthetic stems and capture the report."""
    stems = make_stems()
    events = make_events()
    monkeypatch.setattr(c, "separate_sources",
                        lambda *a, **k: (stems, STEM_RATE))
    monkeypatch.setattr(c, "transcribe_events",
                        lambda signal, rate, picked: list(events))
    monkeypatch.setattr(c, "detect_drums",
                        lambda signal, rate: [(0.5, "kick", 1.0),
                                              (1.0, "snare", 0.8)])
    monkeypatch.setattr(c, "decode_mix", lambda path, rate: stems["vocals"])
    monkeypatch.setattr(c, "track_beats", lambda mix, rate: (TEMPO, BEATS))
    monkeypatch.setattr(c, "bass_from_stem",
                        lambda signal, rate: [[0.0, 1.0, 42.0]])   # F#, off key
    written = {}
    monkeypatch.setattr(c, "write_output",
                        lambda dest, samples, rate, channels:
                        written.update(samples=samples.copy(), rate=rate,
                                       channels=channels))
    (tmp_path / "song.mp3").write_bytes(b"stand-in for the real audio file")

    def run(**kwargs):
        kwargs.setdefault("voices", "band")
        destination, quality_ok, report = c.convert(
            str(tmp_path / "song.mp3"), output_path=str(tmp_path / "out.wav"),
            **kwargs)
        return quality_ok, report, dict(written)

    return run

def line(report, prefix):
    matches = [entry for entry in report if entry.startswith(prefix)]
    assert matches, f"no {prefix!r} line in {report}"
    return matches[0]


class TestBandArrangement:

    def test_the_default_run_arranges(self, band_run):
        quality_ok, report, written = band_run()
        assert quality_ok, "\n".join(report)
        assert line(report, "voices:") == "voices: band"
        assert "chords:" in line(report, "bass:")
        assert "notes snapped" in line(report, "key:")

    def test_the_render_is_real_audio(self, band_run):
        quality_ok, report, written = band_run()
        assert written["samples"].dtype == np.uint8
        assert written["samples"].size > int(SECONDS * c.DEFAULT_RATE)
        assert written["rate"] == c.DEFAULT_RATE
        assert written["channels"] == 1
        assert float(np.std(written["samples"].astype(np.float64))) > 1.0

    def test_key_snap_off_still_arranges(self, band_run):
        """The regression: ``--key-snap off`` used to disable ``--arrange``."""
        quality_ok, report, written = band_run(key_snap=False)
        assert quality_ok, "\n".join(report)
        assert "chords:" in line(report, "bass:")
        assert "left as transcribed" in line(report, "key:")

    def test_key_snap_off_leaves_the_pitches_alone(self, band_run, monkeypatch):
        seen = {}
        original = c.resolve_key

        def spy(events, key_snap=True):
            result = original(events, key_snap=key_snap)
            seen["pitches"] = [pitch for start, end, pitch, amp in result[0]]
            return result

        monkeypatch.setattr(c, "resolve_key", spy)
        band_run(key_snap=False)
        # The off-key F# survives untouched.
        assert seen["pitches"] == [pitch for start, end, pitch, amp in make_events()]
        assert 66.0 in seen["pitches"]

    def test_the_stem_bass_is_only_snapped_when_key_snap_is_on(
            self, band_run, monkeypatch):
        calls = []
        original = c.snap_notes_to_key

        def spy(notes, scale):
            calls.append(list(notes))
            return original(notes, scale)

        monkeypatch.setattr(c, "snap_notes_to_key", spy)

        # With the arranger off there are no chord roots, so the stem-tracked
        # bass is what gets snapped - or not.
        band_run(arrange=False, key_snap=False)
        assert calls == []

        band_run(arrange=False, key_snap=True)
        assert calls == [[[0.0, 1.0, 42.0]]]

    def test_arrange_off_replays_the_transcription(self, band_run):
        quality_ok, report, written = band_run(arrange=False)
        assert "chords:" not in line(report, "bass:")
        assert "bass: 1 notes" in line(report, "bass:")   # the stem fallback

    def test_echo_adds_a_tail_that_echo_off_does_not(self, band_run):
        dry_ok, dry_report, dry = band_run(echo=False)
        wet_ok, wet_report, wet = band_run(echo=True)
        assert not np.array_equal(dry["samples"], wet["samples"])
        difference = (wet["samples"].astype(np.int32)
                      - dry["samples"].astype(np.int32))
        changed = np.nonzero(difference)[0]
        assert changed.size
        # The echo is the only difference, so it has to still be audible after
        # the last note has ended (the events stop at 7.95 s).
        assert changed.max() > int(8.0 * c.DEFAULT_RATE)

    def test_nes_adds_the_arpeggio_and_beat_quantising(self, band_run):
        quality_ok, report, written = band_run(voices="nes")
        assert "arpeggio, beat-quantised" in line(report, "bass:")
        assert "chords:" in line(report, "bass:")

    def test_the_report_is_deterministic(self, band_run):
        first_ok, first, first_written = band_run()
        second_ok, second, second_written = band_run()
        assert first == second


class TestBandArrangementWithoutAKey:
    """No key means no arranger, whichever way the flags are set."""

    def test_a_single_pitch_class_cannot_be_arranged(self, band_run,
                                                    monkeypatch):
        monkeypatch.setattr(c, "detect_key",
                            lambda events: (None, None, None, None))
        quality_ok, report, written = band_run()
        assert "chords:" not in line(report, "bass:")
        assert not any(entry.startswith("key:") for entry in report)

    def test_a_missing_key_still_produces_audio(self, band_run, monkeypatch):
        monkeypatch.setattr(c, "detect_key",
                            lambda events: (None, None, None, None))
        quality_ok, report, written = band_run()
        assert quality_ok
        assert written["samples"].size > 0
