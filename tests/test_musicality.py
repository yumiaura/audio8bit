"""Tests for the musicality layer used by ``--voices band`` and ``--voices nes``.

Everything works on plain ``(start, end, midi, amplitude)`` event lists, so the
suite needs neither Demucs, basic-pitch nor librosa.
"""

import numpy as np
import pytest

from audio8bit import converter as c


def ev(*specs):
    """Build events from ``(start, duration, midi, amplitude)`` tuples."""
    return [(start, start + duration, midi, amp)
            for start, duration, midi, amp in specs]


# A plain C major triad ladder and its relative minor, A minor. The two share
# every pitch class, so only the duration weighting tells them apart.
C_MAJOR = ev(
    (0.0, 1.0, 60, 1.0),   # C
    (1.0, 1.0, 64, 0.9),   # E
    (2.0, 1.0, 67, 0.9),   # G
    (3.0, 1.0, 72, 0.8),   # C
    (4.0, 1.0, 76, 0.7),   # E
    (5.0, 1.0, 79, 0.6),   # G
)
A_MINOR = ev(
    (0.0, 1.0, 57, 1.0),   # A
    (1.0, 1.0, 60, 0.9),   # C
    (2.0, 1.0, 64, 0.9),   # E
    (3.0, 1.0, 69, 0.8),   # A
    (4.0, 1.0, 72, 0.7),   # C
    (5.0, 1.0, 76, 0.6),   # E
)
# 120 bpm, so a beat every 0.5 s and a bar every 2 s.
BEATS = np.arange(0.0, 8.0, 0.5)


# --------------------------------------------------------------------------
# Key detection
# --------------------------------------------------------------------------

class TestDetectKey:

    def test_detects_c_major(self):
        assert c.detect_key(C_MAJOR)[0] == "C major"

    def test_detects_a_minor(self):
        assert c.detect_key(A_MINOR)[0] == "A minor"

    def test_reports_nothing_without_energy(self):
        assert c.detect_key([]) == (None, None, None, None)

    def test_scale_agrees_with_the_reported_name(self):
        name, scale, tonic, degrees = c.detect_key(A_MINOR)
        assert degrees == c.MINOR_SCALE_DEGREES
        assert scale == frozenset((tonic + d) % 12 for d in degrees)
        assert c.NOTE_NAMES[tonic] in name

    def test_relative_major_and_minor_share_pitch_classes(self):
        major_scale = c.detect_key(C_MAJOR)[1]
        minor_scale = c.detect_key(A_MINOR)[1]
        assert major_scale == minor_scale

    def test_every_mode_and_tonic_is_considered(self):
        # A chromatic sweep must not collapse onto a single answer.
        names = {c.detect_key(ev((0.0, 1.0, 60 + step, 1.0)))[0]
                 for step in range(12)}
        assert len(names) == 12


# --------------------------------------------------------------------------
# Snapping notes into the detected scale
# --------------------------------------------------------------------------

class TestSnapToKey:

    def setup_method(self):
        self.scale = c.detect_key(C_MAJOR)[1]

    def test_moves_off_scale_notes_into_the_scale(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 1.0, 66, 1.0))   # C, F#
        snapped, moved = c.snap_to_key(events, self.scale)
        assert moved == 1
        assert int(snapped[1][2]) % 12 in self.scale
        assert abs(snapped[1][2] - 66) == 1

    def test_prefers_resolving_downwards(self):
        # 61 (C#) can go to 60 or 62; both are in C major, and the docstring
        # promises the lower one.
        events = ev((0.0, 1.0, 61, 1.0))
        snapped, _ = c.snap_to_key(events, self.scale)
        assert snapped[0][2] == 60.0

    def test_leaves_in_scale_notes_untouched(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 1.0, 67, 1.0))
        snapped, moved = c.snap_to_key(events, self.scale)
        assert moved == 0
        assert [p for _, _, p, _ in snapped] == [60.0, 67.0]

    def test_is_idempotent(self):
        events = ev((0.0, 1.0, 66, 1.0), (1.0, 1.0, 70, 1.0))
        once, _ = c.snap_to_key(events, self.scale)
        twice, moved = c.snap_to_key(once, self.scale)
        assert moved == 0
        assert [p for _, _, p, _ in twice] == [p for _, _, p, _ in once]

    def test_keeps_timing_and_amplitude(self):
        events = ev((0.25, 1.5, 66, 0.4))
        snapped, _ = c.snap_to_key(events, self.scale)
        assert snapped[0][0] == 0.25
        assert snapped[0][1] == 1.75
        assert snapped[0][3] == 0.4

    def test_no_scale_means_no_change(self):
        events = ev((0.0, 1.0, 66, 1.0))
        assert c.snap_to_key(events, None) == (events, 0)

    def test_note_list_variant(self):
        notes = [[0.0, 1.0, 66.0], [1.0, 1.0, 60.0]]
        snapped = c.snap_notes_to_key(notes, self.scale)
        assert snapped[0][2] == 65.0
        assert snapped[1][2] == 60.0


# --------------------------------------------------------------------------
# resolve_key(): the key is detected whatever --key-snap says
# --------------------------------------------------------------------------

class TestResolveKey:
    """Regression tests for the ``--key-snap`` / ``--arrange`` coupling.

    ``--arrange`` builds its chord progression from the detected key, so the
    key has to be detected even when the user asked for the off-key notes to
    be left alone. Detecting it only when snapping is on made
    ``--key-snap off`` silently switch the arranger off too.
    """

    def test_key_is_detected_even_when_snapping_is_off(self):
        (_, _, tonic, degrees, note) = c.resolve_key(A_MINOR, key_snap=False)
        assert tonic is not None
        assert degrees == c.MINOR_SCALE_DEGREES
        assert note is not None
        assert "A minor" in note

    def test_snapping_on_moves_the_notes(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 1.0, 66, 1.0))
        snapped, _, _, _, note = c.resolve_key(events, key_snap=True)
        assert int(snapped[1][2]) % 12 in c.detect_key(events)[1]
        assert "snapped" in note

    def test_snapping_off_keeps_every_pitch(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 1.0, 66, 1.0))
        snapped, _, _, _, note = c.resolve_key(events, key_snap=False)
        assert [p for _, _, p, _ in snapped] == [60.0, 66.0]
        assert note is not None
        assert "snapped" not in note

    def test_no_key_means_no_report_and_no_scale(self):
        assert c.resolve_key([], key_snap=True) == ([], None, None, None, None)
        assert c.resolve_key([], key_snap=False) == ([], None, None, None, None)


# --------------------------------------------------------------------------
# The arranger
# --------------------------------------------------------------------------

class TestDiatonicTriads:

    def test_seven_triads_all_inside_the_key(self):
        tonic, degrees = c.detect_key(C_MAJOR)[2], c.detect_key(C_MAJOR)[3]
        triads = c.diatonic_triads(tonic, degrees)
        assert len(triads) == 7
        scale = c.detect_key(C_MAJOR)[1]
        for root, pcs in triads:
            assert pcs[0] == root
            assert all(pc in scale for pc in pcs)

    def test_first_triad_is_the_tonic_triad(self):
        assert c.diatonic_triads(0, c.MAJOR_SCALE_DEGREES)[0] == (0, (0, 4, 7))


class TestDetectChords:

    def setup_method(self):
        tonic, degrees = c.detect_key(C_MAJOR)[2], c.detect_key(C_MAJOR)[3]
        self.triads = c.diatonic_triads(tonic, degrees)

    def test_covers_the_whole_span_without_gaps(self):
        chords = c.detect_chords(C_MAJOR, BEATS, self.triads)
        assert chords
        assert chords[0][0] == 0.0
        assert chords[-1][1] >= max(end for _, end, _, _ in C_MAJOR)
        for (_, end, _, _), (next_start, _, _, _) in zip(chords, chords[1:]):
            assert end == next_start

    def test_uses_only_diatonic_roots(self):
        roots = {root for _, _, root, _ in c.detect_chords(C_MAJOR, BEATS,
                                                            self.triads)}
        assert roots <= {root for root, _ in self.triads}

    def test_silent_stretch_carries_the_previous_chord(self):
        events = ev((0.0, 1.0, 60, 1.0), (4.0, 1.0, 67, 1.0))
        chords = c.detect_chords(events, BEATS, self.triads)
        assert chords
        assert chords[1][2] == chords[0][2]

    def test_needs_beats_and_events(self):
        assert c.detect_chords(C_MAJOR, np.zeros(0), self.triads) == []
        assert c.detect_chords([], BEATS, self.triads) == []


class TestBassFromChords:

    def setup_method(self):
        tonic, degrees = c.detect_key(C_MAJOR)[2], c.detect_key(C_MAJOR)[3]
        self.chords = c.detect_chords(C_MAJOR, BEATS,
                                      c.diatonic_triads(tonic, degrees))

    def test_loose_holds_one_root_per_segment(self):
        notes = c.bass_from_chords(self.chords, BEATS, tight=False)
        assert len(notes) == len(self.chords)
        for note, (start, end, root_pc, _) in zip(notes, self.chords):
            assert note[0] == start
            assert note[1] == pytest.approx(end - start)
            assert note[2] % 12 == root_pc

    def test_tight_plays_every_beat(self):
        notes = c.bass_from_chords(self.chords, BEATS, tight=True)
        step = float(np.median(np.diff(BEATS)))
        assert len(notes) > len(self.chords)
        for start, duration, _ in notes:
            assert duration == pytest.approx(step * 0.85)

    def test_tight_puts_the_fifth_on_every_fourth_beat(self):
        notes = c.bass_from_chords(self.chords, BEATS, tight=True)
        assert len(notes) > 4
        # ``beat_index`` counts globally, so every fourth note is the fifth of
        # the chord that started on the previous beat.
        for index in range(3, len(notes), 4):
            assert (notes[index][2] - notes[index - 1][2]) % 12 == 7

    def test_every_note_stays_in_the_bass_register(self):
        for tight in (True, False):
            for _, _, midi in c.bass_from_chords(self.chords, BEATS,
                                                 tight=tight):
                assert c.BASS_ROOT_LOW <= midi <= c.BASS_ROOT_HIGH

    def test_no_chords_means_no_bass(self):
        assert c.bass_from_chords([], BEATS, tight=True) == []


class TestPlanArrangement:
    """Regression tests: the arranger must not depend on ``--key-snap``."""

    def setup_method(self):
        self.tonic, self.degrees = (c.detect_key(C_MAJOR)[2],
                                    c.detect_key(C_MAJOR)[3])

    def test_plans_chords_and_bass_when_a_key_is_known(self):
        chords, bass = c.plan_arrangement(C_MAJOR, BEATS, self.tonic,
                                          self.degrees, tight=False)
        assert chords
        assert bass
        assert len(bass) == len(chords)

    def test_plans_nothing_without_a_key(self):
        assert c.plan_arrangement(C_MAJOR, BEATS, None, None) == ([], [])
        assert c.plan_arrangement(C_MAJOR, BEATS, None, None,
                                  tight=True) == ([], [])

    def test_tight_moves_the_bass_onto_every_beat(self):
        loose_chords, loose_bass = c.plan_arrangement(C_MAJOR, BEATS,
                                                      self.tonic, self.degrees,
                                                      tight=False)
        tight_chords, tight_bass = c.plan_arrangement(C_MAJOR, BEATS,
                                                      self.tonic, self.degrees,
                                                      tight=True)
        assert loose_chords == tight_chords
        assert len(tight_bass) > len(loose_bass)


# --------------------------------------------------------------------------
# Transcription hygiene
# --------------------------------------------------------------------------

class TestCleanEvents:

    def test_drops_short_and_quiet_litter(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 0.01, 72, 0.02))
        cleaned = c.clean_events(events)
        assert [p for _, _, p, _ in cleaned] == [60]

    def test_keeps_short_but_loud_notes(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 0.01, 72, 1.0))
        cleaned = c.clean_events(events)
        assert len(cleaned) == 2

    def test_bridges_legato_gaps_on_the_same_pitch(self):
        events = ev((0.0, 0.5, 60, 0.9), (0.55, 0.5, 60, 0.9))
        cleaned = c.clean_events(events)
        assert len(cleaned) == 1
        assert cleaned[0][1] == pytest.approx(1.05)

    def test_does_not_bridge_different_pitches(self):
        events = ev((0.0, 0.5, 60, 0.9), (0.55, 0.5, 62, 0.9))
        assert len(c.clean_events(events)) == 2

    def test_never_returns_empty_for_a_non_empty_input(self):
        # The loudest event can never be quieter than a quarter of itself, so
        # the litter filter always keeps at least one note.
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 0.01, 72, 0.01))
        assert c.clean_events(events)

    def test_empty_stays_empty(self):
        assert c.clean_events([]) == []

    def test_output_is_sorted_by_time(self):
        events = ev((2.0, 0.5, 64, 1.0), (0.0, 0.5, 60, 1.0),
                    (1.0, 0.5, 62, 1.0))
        starts = [start for start, _, _, _ in c.clean_events(events)]
        assert starts == sorted(starts)


# --------------------------------------------------------------------------
# Melody extraction
# --------------------------------------------------------------------------

class TestMelodyLine:

    def test_follows_the_loudest_smooth_line(self):
        texture = ev(
            (0.0, 0.5, 72, 1.0), (0.0, 0.5, 60, 0.4),
            (0.5, 0.5, 74, 1.0), (0.5, 0.5, 62, 0.4),
            (1.0, 0.5, 76, 1.0), (1.0, 0.5, 64, 0.4),
            (1.5, 0.5, 74, 1.0), (1.5, 0.5, 62, 0.4),
        )
        line = c.melody_line(texture)
        assert [int(pitch) for _, _, pitch in line] == [72, 74, 76, 74]

    def test_empty_events_give_no_notes(self):
        assert c.melody_line([]) == []

    def test_drops_notes_below_the_length_floor(self):
        texture = ev((0.0, 0.02, 72, 1.0), (0.5, 0.5, 72, 1.0))
        line = c.melody_line(texture)
        assert all(duration >= c.MELODY_MIN_SECONDS for _, duration, _ in line)

    def test_register_is_centred_on_the_weighted_median(self):
        pitches = np.array([pitch for _, _, pitch, _ in C_MAJOR])
        weights = np.array([max(1, int((end - start) * amp * 100))
                            for start, end, _, amp in C_MAJOR])
        centre = float(np.median(np.repeat(pitches, weights)))
        low, high = c.melody_register(C_MAJOR)
        assert low == pytest.approx(centre - c.MELODY_REGISTER_LOW)
        assert high == pytest.approx(centre + c.MELODY_REGISTER_HIGH)

    def test_register_is_wide_enough_to_hold_the_melody(self):
        low, high = c.melody_register(C_MAJOR)
        assert low < min(pitch for _, _, pitch, _ in C_MAJOR)
        assert max(pitch for _, _, pitch, _ in C_MAJOR) < high

    def test_candidates_stay_inside_the_band(self):
        frames = 5
        candidates = c.frame_candidates(C_MAJOR, frames, c.MELODY_FRAME,
                                        60.0, 72.0)
        assert len(candidates) == frames
        for slot in candidates:
            assert all(60.0 <= pitch <= 72.0 for pitch in slot)

    def test_viterbi_path_has_one_state_per_frame(self):
        events = ev((0.0, 1.0, 60, 1.0), (1.0, 1.0, 67, 1.0))
        candidates = c.frame_candidates(events, 10, c.MELODY_FRAME, 55.0, 75.0)
        path = c.melody_path(candidates)
        assert len(path) == 10
        assert set(path) <= {None, 60, 67}


# --------------------------------------------------------------------------
# Beat grid and quantisation
# --------------------------------------------------------------------------

class TestBuildGrid:

    def test_subdivides_every_beat(self):
        grid, beats = c.build_grid(BEATS, 120.0, 2.0, subdivisions=4)
        assert len(grid) == 4 * (len(beats) - 1) + 1
        assert grid[0] == 0.0
        assert grid[-1] >= 2.0
        assert np.allclose(np.diff(grid[:4]), 0.125)

    def test_falls_back_to_a_constant_grid_without_beats(self):
        grid, beats = c.build_grid(np.zeros(0), 120.0, 2.0)
        assert beats[0] == 0.0
        assert np.allclose(np.diff(beats), 0.5)
        assert grid[-1] >= 2.0

    def test_grid_is_monotonic(self):
        grid, _ = c.build_grid(BEATS, 120.0, 4.0, subdivisions=2)
        assert np.all(np.diff(grid) > 0)


class TestQuantizeNotes:

    NOTES = [[0.02, 0.4, 60.4], [0.55, 0.4, 62.4], [1.2, 0.4, 64.4]]

    def quantized(self):
        return c.quantize_notes(self.NOTES, 120.0, BEATS)

    def test_snaps_onsets_onto_the_eighth_grid(self):
        grid, _ = c.build_grid(BEATS, 120.0, 2.0, subdivisions=2)
        for start, _, _, _ in self.quantized():
            assert np.min(np.abs(grid - start)) < 1e-9

    def test_rounds_pitches_to_integers(self):
        assert all(isinstance(pitch, int) for _, _, pitch, _ in self.quantized())

    def test_quantises_durations_to_sixteenths(self):
        sixteenth = 60.0 / 120.0 / 4.0
        for _, duration, _, _ in self.quantized():
            assert duration / sixteenth == pytest.approx(round(
                duration / sixteenth))

    def test_keeps_the_line_monophonic(self):
        notes = self.quantized()
        for previous, following in zip(notes, notes[1:]):
            assert previous[0] + previous[1] <= following[0] + 1e-9

    def test_marks_notes_that_land_on_a_beat(self):
        flags = [on_beat for _, _, _, on_beat in self.quantized()]
        assert True in flags and False in flags
        for start, _, _, on_beat in self.quantized():
            assert on_beat == (np.min(np.abs(BEATS - start)) < 0.01)


# --------------------------------------------------------------------------
# Register handling
# --------------------------------------------------------------------------

class TestNormalizeRegister:

    def test_centres_the_line_on_the_ringtone_register(self):
        notes = [[0.0, 1.0, 40.0], [1.0, 1.0, 45.0]]
        shifted = c.normalize_register([list(n) for n in notes], 0)
        median = float(np.median([note[2] for note in shifted]))
        assert abs(median - c.REGISTER_CENTER_MIDI) <= 6

    def test_preserves_the_contour(self):
        notes = [[0.0, 1.0, 40.0], [1.0, 1.0, 45.0], [2.0, 1.0, 52.0]]
        shifted = c.normalize_register([list(n) for n in notes], 0)
        original = [note[2] for note in notes]
        result = [note[2] for note in shifted]
        assert [b - a for a, b in zip(original, original[1:])] == \
            [b - a for a, b in zip(result, result[1:])]

    def test_transpose_is_applied_on_top_of_the_octave_shift(self):
        notes = [[0.0, 1.0, 62.0]]
        plain = c.normalize_register([list(n) for n in notes], 0)
        shifted = c.normalize_register([list(n) for n in notes], 3)
        assert shifted[0][2] - plain[0][2] == 3

    def test_stays_inside_the_midi_bounds(self):
        notes = [[0.0, 1.0, 30.0], [1.0, 1.0, 95.0]]
        for note in c.normalize_register([list(n) for n in notes], 0):
            assert c.MIDI_FLOOR <= note[2] <= c.MIDI_CEILING


class TestTrimLeadingSilence:

    def test_shifts_the_first_note_forward(self):
        notes = [[2.0, 1.0, 60.0], [3.0, 1.0, 62.0]]
        trimmed = c.trim_leading_silence(notes)
        assert trimmed[0][0] == pytest.approx(c.LEAD_START_SECONDS)
        assert trimmed[1][0] == pytest.approx(1.0 + c.LEAD_START_SECONDS)

    def test_leaves_a_line_that_already_starts_promptly(self):
        notes = [[0.0, 1.0, 60.0]]
        assert c.trim_leading_silence(notes) == notes
