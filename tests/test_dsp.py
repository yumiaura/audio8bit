"""Tests for the synthesis, levelling and validation helpers.

All of these are plain NumPy, so the suite never touches Demucs, basic-pitch,
librosa or ffmpeg.
"""

import wave
from pathlib import Path

import numpy as np
import pytest

from audio8bit import converter as c


def tone(frequency, seconds=0.25, sample_rate=22050, amplitude=0.5):
    time = np.arange(int(seconds * sample_rate)) / sample_rate
    return (amplitude * np.sin(2.0 * np.pi * frequency * time)).astype(np.float64)


def as_u8(signal, bits=8):
    return c.to_uint8(c.quantize(c.tpdf_dither(signal, bits), bits))


# --------------------------------------------------------------------------
# Band-limited synthesis
# --------------------------------------------------------------------------

class TestHarmonicsBelowNyquist:

    def test_no_harmonics_for_a_non_positive_frequency(self):
        assert c.harmonics_below_nyquist(0.0, 22050) == 0
        assert c.harmonics_below_nyquist(-5.0, 22050) == 0

    def test_scales_with_the_sample_rate(self):
        low = c.harmonics_below_nyquist(440.0, 8000)
        high = c.harmonics_below_nyquist(440.0, 44100)
        assert high > low
        assert low >= 1

    def test_never_exceeds_the_harmonic_cap(self):
        assert c.harmonics_below_nyquist(1.0, 96000) == c.MAX_HARMONICS


class TestBandLimitedPulse:

    def test_is_peak_normalised_and_finite(self):
        phase = 2.0 * np.pi * 440.0 * np.arange(2205) / 22050
        out = c.band_limited_pulse(phase, 440.0, 22050)
        assert np.all(np.isfinite(out))
        assert float(np.max(np.abs(out))) == pytest.approx(1.0)

    def test_is_deterministic(self):
        phase = 2.0 * np.pi * 330.0 * np.arange(1102) / 22050
        assert np.array_equal(c.band_limited_pulse(phase, 330.0, 22050),
                              c.band_limited_pulse(phase, 330.0, 22050))

    def test_keeps_energy_below_the_alias_guard(self):
        # The whole point of building the wave additively: no folded aliasing.
        sample_rate = 22050
        time = np.arange(sample_rate) / sample_rate
        out = c.band_limited_pulse(2.0 * np.pi * 880.0 * time, 880.0,
                                   sample_rate, 0.25)
        share = c.alias_share(as_u8(out), sample_rate)
        assert share < 0.01

    def test_duty_cycle_changes_the_timbre(self):
        sample_rate = 22050
        time = np.arange(4410) / sample_rate
        thin = c.band_limited_pulse(2.0 * np.pi * 440.0 * time, 440.0,
                                    sample_rate, 0.1)
        wide = c.band_limited_pulse(2.0 * np.pi * 440.0 * time, 440.0,
                                    sample_rate, 0.5)
        assert not np.allclose(thin, wide)

    def test_an_empty_phase_gives_an_empty_wave(self):
        assert c.band_limited_pulse(np.zeros(0), 440.0, 22050).size == 0


class TestBandLimitedTriangle:

    def test_is_peak_normalised_and_finite(self):
        phase = 2.0 * np.pi * 220.0 * np.arange(2205) / 22050
        out = c.band_limited_triangle(phase, 220.0, 22050)
        assert np.all(np.isfinite(out))
        assert float(np.max(np.abs(out))) == pytest.approx(1.0)

    def test_is_softer_than_the_pulse(self):
        sample_rate = 22050
        time = np.arange(4410) / sample_rate
        phase = 2.0 * np.pi * 440.0 * time
        pulse = c.band_limited_pulse(phase, 440.0, sample_rate)
        triangle = c.band_limited_triangle(phase, 440.0, sample_rate)
        # Both are peak-normalised, so the triangle's odd-harmonic spectrum
        # puts far less energy above the fundamental than the pulse's does.
        assert not np.allclose(triangle, pulse)

    def test_uses_only_odd_harmonics(self):
        sample_rate = 22050
        fundamental = 220.0
        time = np.arange(sample_rate) / sample_rate
        out = c.band_limited_triangle(2.0 * np.pi * fundamental * time,
                                      fundamental, sample_rate)
        spectrum = np.abs(np.fft.rfft(out))
        freqs = np.fft.rfftfreq(out.size, 1.0 / sample_rate)

        def band(centre, width=15.0):
            return float(spectrum[np.abs(freqs - centre) <= width].sum())

        # 1/k^2 with alternating sign: odd harmonics only, and falling away.
        assert band(2.0 * fundamental) == pytest.approx(0.0, abs=1e-6)
        assert band(4.0 * fundamental) == pytest.approx(0.0, abs=1e-6)
        assert band(3.0 * fundamental) > 0.0
        assert band(fundamental) > band(3.0 * fundamental)


class TestChipEnvelope:

    def test_starts_and_ends_at_silence(self):
        envelope = c.chip_envelope(2205, 22050)
        assert envelope[0] == pytest.approx(0.0, abs=1e-9)
        assert envelope[-1] == pytest.approx(0.0, abs=1e-9)

    def test_never_exceeds_unity(self):
        assert float(np.max(c.chip_envelope(4410, 22050))) <= 1.0

    def test_rises_then_decays(self):
        envelope = c.chip_envelope(22050, 22050, attack=0.01, decay=0.2)
        assert float(np.max(envelope)) > 0.9
        assert np.all(np.diff(envelope[:200]) >= -1e-12)

    def test_a_zero_length_note_gives_an_empty_envelope(self):
        assert c.chip_envelope(0, 22050).size == 0


# --------------------------------------------------------------------------
# Levelling, echo and quantisation
# --------------------------------------------------------------------------

class TestSmoothEnvelope:

    def test_a_window_of_one_is_just_the_rectified_signal(self):
        signal = np.array([-1.0, 2.0, -3.0])
        assert np.array_equal(c.smooth_envelope(signal, 1), np.abs(signal))

    def test_matches_a_direct_moving_average(self):
        rng = np.random.default_rng(3)
        signal = rng.normal(0.0, 1.0, 500)
        window = 11
        expected = np.convolve(np.abs(signal), np.ones(window) / window,
                               mode="same")
        half = window // 2
        interior = slice(half, signal.size - half)
        assert np.allclose(c.smooth_envelope(signal, window)[interior],
                           expected[interior], atol=1e-9)

    def test_pads_the_edges_instead_of_zeroing_them(self):
        assert np.allclose(c.smooth_envelope(np.ones(10), 5), 1.0)

    def test_survives_a_window_larger_than_the_signal(self):
        out = c.smooth_envelope(np.ones(3), 64)
        assert out.shape == (3,)
        assert np.allclose(out, 1.0)


class TestSoftLimiter:

    def test_leaves_a_quiet_signal_alone(self):
        rng = np.random.default_rng(4)
        signal = rng.normal(0.0, 0.05, 4096)
        assert np.allclose(c.soft_limiter(signal, 22050), signal)

    def test_never_exceeds_the_output_ceiling(self):
        signal = 0.95 * np.sin(2.0 * np.pi * 440.0 * np.arange(44100) / 22050)
        out = c.soft_limiter(signal, 22050)
        assert float(np.max(np.abs(out))) <= 0.95 + 1e-12

    def test_pulls_the_loudest_stretch_down(self):
        sample_rate = 22050
        signal = np.concatenate([
            0.2 * np.ones(sample_rate // 2),
            0.98 * np.ones(sample_rate // 2),
        ])
        out = c.soft_limiter(signal, sample_rate)
        quiet = float(np.max(np.abs(out[:sample_rate // 4])))
        loud = float(np.max(np.abs(out[-sample_rate // 4:])))
        assert quiet == pytest.approx(0.2)          # left completely alone
        assert loud == pytest.approx(c.LIMITER_THRESHOLD, rel=0.02)


class TestAddEcho:

    def test_keeps_the_length(self):
        signal = tone(440.0, seconds=1.0)
        out = c.add_echo(signal, 5512)
        assert out.shape == signal.shape

    def test_repeats_the_signal_quieter(self):
        sample_rate = 22050
        delay = sample_rate // 4
        signal = np.zeros(sample_rate)
        signal[:delay] = 1.0
        out = c.add_echo(signal, delay)
        # The echo lands a quarter of a second later, where the original is
        # silent, and each repeat is ECHO_FEEDBACK times the one before it.
        assert out[0] == pytest.approx(1.0)
        assert out[delay] == pytest.approx(c.ECHO_FEEDBACK)
        assert out[2 * delay] == pytest.approx(c.ECHO_FEEDBACK ** 2)

    def test_a_delay_past_the_end_is_a_no_op(self):
        signal = tone(440.0)
        assert np.array_equal(c.add_echo(signal, signal.size + 1), signal)
        assert np.array_equal(c.add_echo(signal, 0), signal)


class TestNormalizeLoudness:

    def test_hits_the_target_rms(self):
        rng = np.random.default_rng(5)
        signal = rng.normal(0.0, 0.1, 8192)
        out = c.normalize_loudness(signal)
        rms = float(np.sqrt(np.mean(out.astype(np.float64) ** 2)))
        assert rms == pytest.approx(c.TARGET_RMS, rel=0.02)

    def test_caps_the_peak(self):
        rng = np.random.default_rng(6)
        signal = rng.normal(0.0, 0.5, 8192)
        out = c.normalize_loudness(signal)
        assert float(np.max(np.abs(out))) <= 0.95

    def test_silence_stays_silent(self):
        silence = np.zeros(64, dtype=np.float32)
        assert np.array_equal(c.normalize_loudness(silence), silence)


class TestDitherAndQuantise:

    def test_dither_is_deterministic(self):
        signal = np.zeros(2048, dtype=np.float32)
        assert np.array_equal(c.tpdf_dither(signal, 8),
                              c.tpdf_dither(signal, 8))

    def test_dither_stays_within_one_lsb(self):
        levels = (1 << 8) - 1
        lsb = 2.0 / levels
        signal = np.zeros(4096, dtype=np.float32)
        noise = c.tpdf_dither(signal, 8) - signal
        assert float(np.max(np.abs(noise))) <= lsb + 1e-6

    def test_quantise_maps_the_rails_exactly(self):
        out = c.quantize(np.array([-1.0, 1.0], dtype=np.float32), 8)
        assert out[0] == -1.0
        assert out[1] == 1.0

    def test_quantise_uses_the_requested_number_of_levels(self):
        values = np.linspace(-1.0, 1.0, 2000)
        assert len(np.unique(c.quantize(values, 4))) <= 1 << 4
        assert len(np.unique(c.quantize(values, 8))) <= 1 << 8

    def test_uint8_mapping(self):
        out = c.to_uint8(np.array([-1.0, 0.0, 1.0], dtype=np.float32))
        assert out[0] == 0
        assert out[1] == 128
        assert out[2] == 255

    def test_uint8_round_trips_through_the_validator(self):
        samples = as_u8(tone(440.0))
        assert samples.dtype == np.uint8
        assert samples.min() >= 0 and samples.max() <= 255


class TestAliasShare:

    def test_silence_has_no_energy(self):
        assert c.alias_share(np.full(512, 128, dtype=np.uint8), 22050) == 0.0

    def test_a_band_limited_tone_stays_under_the_guard(self):
        assert c.alias_share(as_u8(tone(880.0)), 22050) < 0.01

    def test_full_scale_noise_reports_aliasing(self):
        rng = np.random.default_rng(8)
        noise = c.to_uint8(rng.uniform(-1.0, 1.0, 8192).astype(np.float32))
        assert c.alias_share(noise, 22050) > 0.01


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def sample_events(count=6, span=3.0):
    rng = np.random.default_rng(11)
    events = []
    for index in range(count):
        start = index * span / count
        events.append((start, start + span / count * 0.8,
                       float(60 + index % 7), float(0.5 + 0.5 * rng.random())))
    return events


class TestRenderers:

    def test_render_melody_is_long_enough_and_levelled(self):
        notes = [[index * 0.5, 0.45, 60.0 + index % 5] for index in range(16)]
        out = c.render_melody(notes, 22050)
        assert np.all(np.isfinite(out))
        assert out.size >= int((16 * 0.5) * 22050)
        assert float(np.max(np.abs(out))) <= 0.9 + 1e-6

    def test_render_chords_is_levelled_and_keeps_every_note(self):
        events = sample_events()
        out = c.render_chords(events, 22050)
        assert np.all(np.isfinite(out))
        assert float(np.max(np.abs(out))) <= 0.95 + 1e-6
        assert out.size >= int(3.0 * 22050)

    def test_render_chords_applies_the_transpose(self):
        events = [(0.0, 1.0, 60.0, 1.0)]
        plain = c.render_chords(events, 22050, transpose=0)
        shifted = c.render_chords(events, 22050, transpose=12)
        assert not np.allclose(plain, shifted)

    @pytest.mark.parametrize("arp", [False, True])
    def test_render_band_is_finite_and_deterministic(self, arp):
        events = sample_events()
        lead = [[s, e - s, p] for s, e, p, amp in events]
        first = c.render_band(events, 22050, 0.25, 0, lead_notes=lead,
                              bass_notes=[], drum_hits=[(0.0, "kick", 1.0)],
                              arp=arp, vibrato=arp, chords=[], echo_delay=0)
        second = c.render_band(events, 22050, 0.25, 0, lead_notes=lead,
                               bass_notes=[], drum_hits=[(0.0, "kick", 1.0)],
                               arp=arp, vibrato=arp, chords=[], echo_delay=0)
        assert np.all(np.isfinite(first))
        assert np.array_equal(first, second)

    def test_render_band_without_events_still_returns_audio(self):
        out = c.render_band([], 22050)
        assert out.size == 22050
        assert float(np.max(np.abs(out))) == 0.0

    def test_pad_arp_and_chord_voices_all_produce_output(self):
        events = sample_events()
        total = int(3.0 * 22050)
        for render in (c.render_pad, c.render_arp):
            assert render(events, 22050, 0, total).size == total
        chords = [(0.0, 1.0, 0, (0, 4, 7)), (1.0, 2.0, 5, (5, 9, 0))]
        assert c.render_chord_pad(chords, 22050, 0, total).size == total
        assert c.render_chord_arp(chords, 22050, 0, total).size == total

    def test_render_song_mixes_a_lead_and_a_bass(self):
        notes = [[index * 0.5, 0.45, 60 + index % 4, index % 2 == 0]
                 for index in range(12)]
        out = c.render_song(notes, 22050, 0.25, 120.0)
        assert np.all(np.isfinite(out))
        assert float(np.max(np.abs(out))) <= 0.9 + 1e-6
        # The echo tail means the render outlasts the last note.
        assert out.size > int((12 * 0.5) * 22050)


class TestNoiseBurst:

    @pytest.mark.parametrize("kind", ["kick", "snare", "hat"])
    def test_is_peak_normalised(self, kind):
        out = c.noise_burst(22050, np.random.default_rng(0), kind)
        assert float(np.max(np.abs(out))) == pytest.approx(1.0)

    def test_is_deterministic_for_a_given_seed(self):
        first = c.noise_burst(22050, np.random.default_rng(4), "snare")
        second = c.noise_burst(22050, np.random.default_rng(4), "snare")
        assert np.array_equal(first, second)

    def test_the_kinds_are_distinguishable(self):
        rng = np.random.default_rng(0)
        kick = c.noise_burst(22050, np.random.default_rng(0), "kick")
        hat = c.noise_burst(22050, np.random.default_rng(0), "hat")
        assert kick.size > hat.size


class TestDrumHelpers:

    HITS = [(0.0, "kick", 1.0), (0.5, "snare", 0.9), (1.0, "hat", 0.8),
            (1.5, "kick", 0.95), (2.0, "snare", 0.85), (2.3, "hat", 0.7)]

    def test_snap_drums_only_moves_onsets_inside_the_window(self):
        grid = np.arange(0.0, 4.0, 0.25)
        hits = [(0.02, "kick", 1.0), (0.9, "snare", 0.5)]
        snapped = c.snap_drums(hits, grid, snap_seconds=0.05)
        assert snapped[0][0] == 0.0
        assert snapped[1][0] == 0.9

    def test_snap_drums_passes_hits_through_without_a_grid(self):
        assert c.snap_drums(self.HITS, None) == self.HITS
        assert c.snap_drums(self.HITS, np.zeros(0)) == self.HITS

    def test_accent_drums_boosts_only_on_beat_hits(self):
        beats = np.arange(0.0, 4.0, 0.5)
        out = c.accent_drums(self.HITS, beats)
        by_time = {onset: velocity for onset, kind, velocity in out}
        assert by_time[0.5] == pytest.approx(0.9 * c.BEAT_ACCENT)
        assert by_time[1.0] == pytest.approx(0.8 * c.BEAT_ACCENT)
        assert by_time[2.3] == pytest.approx(0.7)      # off the beat

    def test_accent_drums_never_exceeds_the_ceiling(self):
        beats = np.arange(0.0, 4.0, 0.5)
        # The boost is capped, so even a very loud hit cannot push the mix over.
        assert c.accent_drums([(0.0, "kick", 1.2)], beats)[0][2] == \
            pytest.approx(1.25)
        assert c.accent_drums([(0.0, "kick", 0.5)], beats)[0][2] == \
            pytest.approx(0.5 * c.BEAT_ACCENT)

    def test_drum_pattern_falls_back_when_there_is_too_little_material(self):
        beats = np.arange(0.0, 2.0, 0.5)
        hits = [(0.0, "kick", 1.0), (0.5, "snare", 0.9)]
        assert c.drum_pattern(hits, beats) == hits

    def test_drum_pattern_repeats_a_voted_slot_every_bar(self):
        beats = np.arange(0.0, 8.0, 0.5)      # four bars of 4/4
        hits = [(index * 2.0, "kick", 1.0) for index in range(4)]
        pattern = c.drum_pattern(hits, beats)
        assert len(pattern) == 4
        assert all(kind == "kick" for onset, kind, velocity in pattern)
        assert [round(onset, 6) for onset, kind, velocity in pattern] == [0.0, 2.0, 4.0, 6.0]


# --------------------------------------------------------------------------
# Quality gates
# --------------------------------------------------------------------------

GOOD_LINE = [[index * 0.5, 0.45, 60 + index % 8] for index in range(24)]


class TestValidateMelody:

    # The nine "mush" heuristics a listenable single line has to clear.
    CHECKS = ("note density", "median note length", "notes under 100 ms",
              "trill flicker", "pitch span", "leaps over a fifth",
              "sound coverage", "energy above the band limit",
              "clipped samples")

    def render(self):
        voice = c.render_melody(GOOD_LINE, 22050)
        return as_u8(voice)

    def test_a_well_formed_line_passes(self):
        ok, lines = c.validate_melody(GOOD_LINE, self.render(), 22050)
        assert ok, "\n".join(lines)

    def test_every_check_reports_a_target(self):
        ok, lines = c.validate_melody(GOOD_LINE, self.render(), 22050)
        joined = "\n".join(lines)
        for name in self.CHECKS:
            assert name in joined
        assert all("target" in line for line in lines)

    def test_a_mushy_line_is_flagged(self):
        mush = [[index * 0.03, 0.02, 60 + (index * 7) % 24]
                for index in range(60)]
        ok, lines = c.validate_melody(mush, self.render(), 22050)
        assert not ok
        assert any(line.startswith("MUSH") for line in lines)

    def test_silence_is_flagged(self):
        # The two audio checks are about aliasing and clipping, so a flat
        # mid-scale signal trips the clipping gate.
        ok, lines = c.validate_melody(
            GOOD_LINE, np.full(22050, 255, dtype=np.uint8), 22050)
        assert not ok
        assert any("clipped samples" in line and line.startswith("MUSH")
                   for line in lines)


class TestValidateAudio:

    def test_real_audio_passes(self):
        ok, lines = c.validate_audio(as_u8(tone(440.0)), 22050, 12)
        assert ok, "\n".join(lines)

    def test_silence_fails(self):
        ok, lines = c.validate_audio(np.full(4096, 128, dtype=np.uint8),
                                     22050, 0)
        assert not ok
        assert sum(1 for line in lines if line.startswith("BAD")) == 2

    def test_clipping_is_flagged(self):
        clipped = np.full(4096, 255, dtype=np.uint8)
        ok, lines = c.validate_audio(clipped, 22050, 5)
        assert not ok


# --------------------------------------------------------------------------
# Output plumbing
# --------------------------------------------------------------------------

class TestResolveOutputPath:

    def test_defaults_to_the_input_format(self):
        assert c.resolve_output_path("song.mp3") == Path("output.mp3")

    def test_format_overrides_the_extension(self):
        assert c.resolve_output_path("song.mp3", format=".OGG") == \
            Path("output.ogg")

    def test_an_explicit_path_wins(self):
        assert c.resolve_output_path("song.mp3", "elsewhere/name.wav") == \
            Path("elsewhere/name.wav")

    def test_an_extensionless_input_falls_back_to_wav(self):
        assert c.resolve_output_path("song") == Path("output.wav")


class TestWriteWav:

    def test_writes_8bit_unsigned_pcm(self, tmp_path):
        samples = as_u8(tone(440.0))
        path = tmp_path / "out.wav"
        c.write_wav(path, samples, 22050, 1)
        with wave.open(str(path), "rb") as handle:
            assert handle.getnchannels() == 1
            assert handle.getsampwidth() == 1
            assert handle.getframerate() == 22050
            assert handle.getnframes() == samples.size

    def test_write_output_writes_wav_directly(self, tmp_path):
        samples = as_u8(tone(440.0))
        path = tmp_path / "direct.wav"
        c.write_output(path, samples, 22050, 1)
        assert path.is_file()
        with wave.open(str(path), "rb") as handle:
            assert handle.getnframes() == samples.size


class TestRequireTool:

    def test_raises_a_friendly_error_for_a_missing_tool(self):
        with pytest.raises(c.ConversionError) as excinfo:
            c.require_tool("definitely-not-a-real-tool-8bit")
        assert "ffmpeg" in str(excinfo.value)

    def test_returns_the_path_when_the_tool_exists(self, monkeypatch):
        monkeypatch.setattr(c.shutil, "which", lambda name: "/usr/bin/" + name)
        assert c.require_tool("ffmpeg") == "/usr/bin/ffmpeg"
