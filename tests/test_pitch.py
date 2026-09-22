"""Tests for the pYIN post-processing chain (``--method pitch``).

``segment_notes`` onwards is plain NumPy, so the whole note-extraction pipeline
after the pitch tracker can be exercised without librosa.
"""

import numpy as np
import pytest

from audio8bit import converter as c

SAMPLE_RATE = 22050
FRAME_SECONDS = c.HOP / SAMPLE_RATE


def track(*segments):
    """Build an ``(f0, voiced)`` pair from ``(frames, midi)`` segments.

    A segment of ``None`` is an unvoiced stretch.
    """
    f0 = []
    voiced = []
    for frames, midi in segments:
        f0.extend([0.0 if midi is None else float(c.midi_to_hz(midi))] * frames)
        voiced.extend([midi is not None] * frames)
    return np.array(f0, dtype=np.float64), np.array(voiced, dtype=bool)


class TestSmoothPitch:

    def test_suppresses_octave_spikes(self):
        f0 = np.array([440.0, 440.0, 880.0, 440.0, 440.0])
        voiced = np.ones(5, dtype=bool)
        out = c.smooth_pitch(f0, voiced, window=5)
        assert out[2] == pytest.approx(440.0)

    def test_leaves_unvoiced_frames_alone(self):
        f0 = np.array([440.0, 0.0, 440.0])
        voiced = np.array([True, False, True])
        out = c.smooth_pitch(f0, voiced, window=3)
        assert out[1] == 0.0

    def test_an_empty_track_is_returned_as_is(self):
        assert c.smooth_pitch(np.zeros(0), np.zeros(0, dtype=bool)).size == 0


class TestSegmentNotes:

    def test_splits_a_step_into_two_notes(self):
        f0, voiced = track((10, 69), (10, 72))
        notes = c.segment_notes(f0, voiced, c.HOP, SAMPLE_RATE)
        assert len(notes) == 2
        assert notes[0][2] == pytest.approx(69.0, abs=0.01)
        assert notes[1][2] == pytest.approx(72.0, abs=0.01)

    def test_note_lengths_follow_the_frames(self):
        f0, voiced = track((10, 69), (10, 72))
        notes = c.segment_notes(f0, voiced, c.HOP, SAMPLE_RATE)
        assert notes[0][1] == pytest.approx(10 * FRAME_SECONDS)
        assert notes[1][0] == pytest.approx(10 * FRAME_SECONDS)

    def test_singing_vibrato_stays_inside_one_note(self):
        # +/- 25 cents is well inside PITCH_TOLERANCE.
        cents = 25.0 * np.sin(np.linspace(0.0, 8.0 * np.pi, 60))
        f0 = 440.0 * 2.0 ** (cents / 1200.0)
        notes = c.segment_notes(f0, np.ones(60, dtype=bool), c.HOP, SAMPLE_RATE)
        assert len(notes) == 1

    def test_a_real_interval_still_starts_a_new_note(self):
        f0 = np.concatenate([np.full(20, 440.0), np.full(20, 523.25)])
        notes = c.segment_notes(f0, np.ones(40, dtype=bool), c.HOP, SAMPLE_RATE)
        assert len(notes) == 2

    def test_unvoiced_stretches_break_the_line(self):
        f0, voiced = track((10, 69), (10, None), (10, 69))
        notes = c.segment_notes(f0, voiced, c.HOP, SAMPLE_RATE)
        assert len(notes) == 2


class TestMergeNotes:

    def test_bridges_a_short_voicing_gap(self):
        notes = [[0.0, 0.3, 60.0], [0.36, 0.3, 60.0]]
        merged = c.merge_notes(notes)
        assert len(merged) == 1
        assert merged[0][1] == pytest.approx(0.66)

    def test_does_not_bridge_a_long_gap(self):
        notes = [[0.0, 0.3, 60.0], [1.0, 0.3, 60.0]]
        assert len(c.merge_notes(notes)) == 2

    def test_does_not_bridge_a_different_pitch(self):
        notes = [[0.0, 0.3, 60.0], [0.36, 0.3, 62.0]]
        assert len(c.merge_notes(notes)) == 2

    def test_averages_the_pitch_of_a_bridged_pair(self):
        notes = [[0.0, 0.3, 60.0], [0.36, 0.3, 60.4]]
        merged = c.merge_notes(notes)
        assert merged[0][2] == pytest.approx(60.2)


class TestAbsorbTrills:

    def test_absorbs_a_short_odd_one_out(self):
        notes = [[0.0, 0.3, 60.0], [0.32, 0.05, 62.0], [0.4, 0.3, 60.0]]
        out = c.absorb_trills(notes)
        assert len(out) == 1
        assert out[0][2] == pytest.approx(60.0)

    def test_keeps_a_long_middle_note(self):
        notes = [[0.0, 0.3, 60.0], [0.32, 0.4, 62.0], [0.8, 0.3, 60.0]]
        assert len(c.absorb_trills(notes)) == 3

    def test_keeps_a_genuine_turn(self):
        notes = [[0.0, 0.3, 60.0], [0.32, 0.05, 67.0], [0.4, 0.3, 60.0]]
        assert len(c.absorb_trills(notes)) == 3


class TestOctaveFolding:

    def test_fold_keeps_a_line_with_no_octave_errors(self):
        notes = [[0.0, 1.0, 60.0], [1.0, 1.0, 62.0], [2.0, 1.0, 64.0]]
        out = c.fold_octaves([list(note) for note in notes])
        assert [round(note[2]) for note in out] == [60, 62, 64]

    def test_fold_needs_something_to_compare_against(self):
        notes = [[0.0, 1.0, 60.0], [1.0, 1.0, 84.0]]
        assert c.fold_octaves([list(note) for note in notes]) == notes

    def test_collapse_keeps_every_note_within_an_octave_of_the_centre(self):
        notes = [[0.0, 1.0, 60.0], [1.0, 1.0, 84.0], [2.0, 1.0, 59.0]]
        out = c.collapse_octaves([list(note) for note in notes])
        weights = np.array([max(1, int(note[1] * 100)) for note in notes])
        centre = float(np.median(np.repeat([note[2] for note in notes],
                                           weights)))
        assert all(abs(note[2] - centre) <= c.OCTAVE_COLLAPSE_SEMITONES
                   for note in out)

    def test_collapse_leaves_a_tight_line_alone(self):
        notes = [[0.0, 1.0, 60.0], [1.0, 1.0, 62.0]]
        out = c.collapse_octaves([list(note) for note in notes])
        assert [note[2] for note in out] == [60.0, 62.0]

    def test_collapse_of_nothing_is_nothing(self):
        assert c.collapse_octaves([]) == []


class TestExtractNotes:

    def test_bridges_a_repeat_of_the_same_pitch(self):
        f0, voiced = track((20, 69), (5, None), (20, 69))
        notes = c.extract_notes(f0, voiced, SAMPLE_RATE)
        assert len(notes) == 1
        assert notes[0][1] >= c.MIN_NOTE_SECONDS

    def test_drops_notes_shorter_than_the_floor(self):
        f0, voiced = track((2, 69), (10, None), (20, 72))
        notes = c.extract_notes(f0, voiced, SAMPLE_RATE)
        assert all(note[1] >= c.MIN_NOTE_SECONDS for note in notes)

    def test_keeps_a_clean_two_note_line(self):
        f0, voiced = track((20, 69), (20, 72))
        notes = c.extract_notes(f0, voiced, SAMPLE_RATE)
        assert [round(note[2]) for note in notes] == [69, 72]

    def test_is_deterministic(self):
        f0, voiced = track((20, 69), (3, None), (20, 72), (2, None), (20, 74))
        first = c.extract_notes(f0, voiced, SAMPLE_RATE)
        second = c.extract_notes(f0, voiced, SAMPLE_RATE)
        assert first == second


class TestBassLine:

    def test_keeps_the_lowest_active_note(self):
        events = [(0.0, 1.0, 48.0, 0.9), (0.0, 1.0, 72.0, 1.0)]
        notes = c.bass_line(events)
        assert notes
        assert all(note[2] == 48.0 for note in notes)

    def test_folds_into_the_bass_register(self):
        events = [(0.0, 1.0, 79.0, 1.0)]
        notes = c.bass_line(events)
        assert notes[0][2] <= c.BASS_REGISTER_CEILING

    def test_no_events_means_no_bass(self):
        assert c.bass_line([]) == []
