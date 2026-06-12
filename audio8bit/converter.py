"""DSP core: turn a song into a chiptune arrangement of its sung melody.

The pipeline extracts the sung melody and re-arranges it the way an 80s game
console would play it:

* vocal isolation — Demucs (a neural source-separation model) extracts the
  vocal stem, i.e. the sung melody on its own, dropping the backing;
* pitch tracking — librosa's pYIN follows the fundamental frequency (f0) of
  the isolated voice over time;
* note extraction — the pitch track is split into discrete notes with
  hysteresis (vibrato and scoops stay inside one note), short voicing gaps
  are bridged, octave errors folded back, flicker dropped;
* musicalisation — note onsets snap to the song's own beat grid (tracked on
  the original mix), the melody is shifted into a ringtone register and
  transposed into a different key;
* chip synthesis — a band-limited pulse lead with vibrato and decay
  envelopes, a triangle bass an octave below on the beats, and a tempo-synced
  echo, all alias-free by construction;
* 8-bit output — the mix is quantised to 8-bit unsigned PCM and written as
  WAV, or re-encoded by ffmpeg to the chosen format;
* validation — the result is scored against "mush" heuristics (note density,
  fragmentation, trills, range, clipping) and a quality report is returned.

Demucs and librosa are heavy dependencies (Demucs pulls in PyTorch and
downloads model weights on first use), so they are imported lazily with a
clear message if they are missing.
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

DEFAULT_RATE = 22050
DEFAULT_BITS = 8
DEFAULT_DUTY = 0.25
DEFAULT_TRANSPOSE = 3

PITCH_TOLERANCE = 0.6
DRIFT_FRAMES = 3
BRIDGE_SECONDS = 0.12
REPEAT_BRIDGE_SECONDS = 0.25
MIN_NOTE_SECONDS = 0.12
OCTAVE_FOLD_SEMITONES = 7
CONTEXT_SECONDS = 4.0

GRID_SNAP_SECONDS = 0.1
FALLBACK_TEMPO = 120.0
REGISTER_CENTER_MIDI = 74
MIDI_FLOOR = 48
MIDI_CEILING = 96
LEAD_START_SECONDS = 0.05

MAX_HARMONICS = 40
NYQUIST_FRACTION = 0.45
VIBRATO_RATE = 5.5
VIBRATO_CENTS = 25.0
VIBRATO_DELAY = 0.12
LEAD_GAIN = 0.6
BASS_GAIN = 0.45
ECHO_FEEDBACK = 0.35


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


def hz_to_midi(frequency):
    """Frequency in Hz to a (fractional) MIDI note number."""
    return 69.0 + 12.0 * np.log2(np.asarray(frequency, dtype=np.float64) / 440.0)


def midi_to_hz(midi):
    """MIDI note number to frequency in Hz."""
    return 440.0 * 2.0 ** ((np.asarray(midi, dtype=np.float64) - 69.0) / 12.0)


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


def segment_notes(f0, voiced, hop, analysis_rate, tolerance=PITCH_TOLERANCE,
                  drift_frames=DRIFT_FRAMES):
    """Split the pitch track into notes with hysteresis.

    A note keeps its pitch (the running median of its frames, in semitones);
    a new note starts only when the pitch stays more than ``tolerance``
    semitones away for ``drift_frames`` consecutive frames. Singing vibrato
    and scoops therefore stay inside one note instead of spraying trills.

    Returns a list of [start_seconds, duration_seconds, midi_float].
    """
    frame_seconds = hop / analysis_rate
    midi = np.full(f0.size, np.nan)
    positive = f0 > 0
    midi[positive] = hz_to_midi(f0[positive])

    notes = []

    def close(start_frame, end_frame, values):
        if values and end_frame >= start_frame:
            notes.append([
                start_frame * frame_seconds,
                (end_frame - start_frame + 1) * frame_seconds,
                float(np.median(values)),
            ])

    start = None
    values = []
    pending = []
    for index in range(f0.size):
        if not (voiced[index] and np.isfinite(midi[index])):
            if start is not None:
                close(start, index - 1, values)
                start, values, pending = None, [], []
            continue
        value = float(midi[index])
        if start is None:
            start, values, pending = index, [value], []
            continue
        center = float(np.median(values))
        if abs(value - center) <= tolerance:
            for held_index, held_value in pending:
                values.append(held_value)
            pending = []
            values.append(value)
            continue
        pending.append((index, value))
        if len(pending) < drift_frames:
            continue
        held = [held_value for held_index, held_value in pending]
        if max(held) - min(held) <= tolerance:
            close(start, pending[0][0] - 1, values)
            start, values = pending[0][0], held
            pending = []
        else:
            held_index, held_value = pending.pop(0)
            values.append(held_value)
    if start is not None:
        close(start, f0.size - 1, values)
    return notes


def merge_notes(notes, bridge_seconds=BRIDGE_SECONDS, tolerance=PITCH_TOLERANCE):
    """Bridge short voicing gaps: join neighbours that are one sung note.

    Consonants and breaths make pYIN drop voicing for a few frames in the
    middle of a held note; if the gap is short and the pitch comes back to
    (nearly) the same place, the two pieces are one note played legato.
    """
    merged = []
    for note in notes:
        if merged:
            previous = merged[-1]
            gap = note[0] - (previous[0] + previous[1])
            if gap <= bridge_seconds and abs(note[2] - previous[2]) <= tolerance:
                total = previous[1] + note[1]
                previous[2] = (previous[2] * previous[1] + note[2] * note[1]) / total
                previous[1] = note[0] + note[1] - previous[0]
                continue
        merged.append(list(note))
    return merged


def absorb_trills(notes, max_middle_seconds=0.15, max_gap_seconds=0.12):
    """Absorb short A-B-A ornament middles into one held note.

    Vibrato straddling a semitone boundary and slow scoops produce a short
    odd-one-out note between two notes of the same pitch; a phone speaker
    plays that as nervous flicker, so the three become one held note.
    """
    out = []
    index = 0
    while index < len(notes):
        if out and index + 1 < len(notes):
            previous = out[-1]
            middle = notes[index]
            following = notes[index + 1]
            if (round(previous[2]) == round(following[2])
                    and round(middle[2]) != round(previous[2])
                    and abs(middle[2] - previous[2]) <= 2.5
                    and middle[1] <= max_middle_seconds
                    and middle[0] - (previous[0] + previous[1]) <= max_gap_seconds
                    and following[0] - (middle[0] + middle[1]) <= max_gap_seconds):
                weight = previous[1] + following[1]
                previous[2] = (previous[2] * previous[1]
                               + following[2] * following[1]) / weight
                previous[1] = following[0] + following[1] - previous[0]
                index += 2
                continue
        out.append(list(notes[index]))
        index += 1
    return out


def fold_octaves(notes, span=OCTAVE_FOLD_SEMITONES, context_seconds=CONTEXT_SECONDS):
    """Fold pitch-tracking octave errors back towards the local melody line."""
    if len(notes) < 3:
        return notes
    starts = np.array([note[0] for note in notes])
    for index, note in enumerate(notes):
        near = np.abs(starts - note[0]) <= context_seconds
        near[index] = False
        if not near.any():
            continue
        weights = np.array([
            max(1, int(other[1] * 100))
            for other, is_near in zip(notes, near) if is_near
        ])
        pitches = np.array([
            other[2] for other, is_near in zip(notes, near) if is_near
        ])
        context = float(np.median(np.repeat(pitches, weights)))
        while note[2] - context > span:
            note[2] -= 12.0
        while context - note[2] > span:
            note[2] += 12.0
    return notes


def decode_mix(path, rate):
    """Decode the original mix to mono float32 at ``rate`` via ffmpeg."""
    ffmpeg = require_tool("ffmpeg")
    command = [
        ffmpeg, "-v", "error", "-i", str(path), "-f", "f32le",
        "-acodec", "pcm_f32le", "-ac", "1", "-ar", str(rate), "pipe:1",
    ]
    completed = subprocess.run(command, capture_output=True)
    if completed.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed to decode '{path}': "
            f"{completed.stderr.decode(errors='replace').strip()}"
        )
    return np.frombuffer(completed.stdout, dtype=np.float32).copy()


def track_beats(mix, mix_rate):
    """Estimate (tempo_bpm, beat_times_seconds) of the original mix."""
    try:
        import librosa
    except ImportError as missing:
        raise ConversionError(
            "librosa is required for beat tracking. "
            "Install it with 'pip install demucs librosa'."
        ) from missing

    tempo, beat_frames = librosa.beat.beat_track(y=mix, sr=mix_rate, hop_length=HOP)
    tempo = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=mix_rate, hop_length=HOP)
    if tempo <= 0 or beat_times.size < 2:
        return FALLBACK_TEMPO, np.zeros(0)
    return tempo, np.asarray(beat_times, dtype=np.float64)


def build_grid(beat_times, tempo, span, subdivisions=2):
    """Times of every beat subdivision covering [0, span] seconds."""
    seconds_per_beat = 60.0 / tempo
    if beat_times.size >= 2:
        beats = list(beat_times)
        while beats[0] - seconds_per_beat >= 0.0:
            beats.insert(0, beats[0] - seconds_per_beat)
        while beats[-1] < span:
            beats.append(beats[-1] + seconds_per_beat)
        beats = np.array(beats)
    else:
        beats = np.arange(0.0, span + seconds_per_beat, seconds_per_beat)
    grid = []
    for left, right in zip(beats[:-1], beats[1:]):
        for step in range(subdivisions):
            grid.append(left + (right - left) * step / subdivisions)
    grid.append(beats[-1])
    return np.array(grid), beats


def quantize_notes(notes, tempo, beat_times, snap_seconds=GRID_SNAP_SECONDS):
    """Snap onsets to the song's eighth grid and durations to sixteenths.

    Also rounds each note to the nearest semitone and marks notes that land
    on a beat (the bass voice plays there). Returns
    [start, duration, midi_int, on_beat] and keeps the lead monophonic.
    """
    span = max(note[0] + note[1] for note in notes)
    grid, beats = build_grid(beat_times, tempo, span)
    sixteenth = 60.0 / tempo / 4.0

    quantized = []
    for start, duration, midi in notes:
        nearest = float(grid[np.argmin(np.abs(grid - start))])
        if abs(nearest - start) <= snap_seconds:
            start = nearest
        steps = max(1, int(round(duration / sixteenth)))
        duration = steps * sixteenth
        on_beat = bool(np.min(np.abs(beats - start)) < 0.01)
        quantized.append([start, duration, int(round(midi)), on_beat])

    quantized.sort(key=lambda note: note[0])
    monophonic = []
    for note in quantized:
        if monophonic:
            previous = monophonic[-1]
            room = note[0] - previous[0]
            if room < sixteenth * 0.5:
                if note[1] > previous[1]:
                    monophonic[-1] = note
                continue
            if previous[0] + previous[1] > note[0]:
                previous[1] = room
        monophonic.append(note)
    return monophonic


def normalize_register(notes, transpose):
    """Shift the melody by octaves into the ringtone register, then transpose."""
    weights = np.array([max(1, int(note[1] * 100)) for note in notes])
    pitches = np.array([note[2] for note in notes])
    median = float(np.median(np.repeat(pitches, weights)))
    shift = 12 * round((REGISTER_CENTER_MIDI - median) / 12.0) + transpose
    for note in notes:
        note[2] += shift
        while note[2] > MIDI_CEILING:
            note[2] -= 12
        while note[2] < MIDI_FLOOR:
            note[2] += 12
    return notes


def trim_leading_silence(notes, lead_seconds=LEAD_START_SECONDS):
    """Shift all notes so the melody starts right away."""
    offset = notes[0][0] - lead_seconds
    if offset <= 0:
        return notes
    for note in notes:
        note[0] -= offset
    return notes


def harmonic_phase(frequency, count, sample_rate, vibrato_rate=VIBRATO_RATE,
                   vibrato_cents=VIBRATO_CENTS, vibrato_delay=VIBRATO_DELAY):
    """Cumulative phase of the fundamental with delayed vibrato."""
    time = np.arange(count) / sample_rate
    depth = np.clip((time - vibrato_delay) / 0.1, 0.0, 1.0)
    cents = vibrato_cents * depth * np.sin(2.0 * np.pi * vibrato_rate * time)
    instantaneous = frequency * 2.0 ** (cents / 1200.0)
    return 2.0 * np.pi * np.cumsum(instantaneous) / sample_rate


def harmonics_below_nyquist(top_frequency, sample_rate):
    """How many harmonics of ``top_frequency`` fit under the alias guard band."""
    if top_frequency <= 0:
        return 0
    return min(MAX_HARMONICS, int(NYQUIST_FRACTION * sample_rate / top_frequency))


def band_limited_pulse(phase, top_frequency, sample_rate, duty=DEFAULT_DUTY):
    """Sum only the pulse harmonics that fit below Nyquist — alias-free.

    A raw ``sign()`` square contains harmonics above Nyquist that fold back
    as a harsh screech; building the wave additively avoids that entirely.
    ``top_frequency`` is the highest instantaneous fundamental (vibrato peak).
    """
    harmonics = harmonics_below_nyquist(top_frequency, sample_rate)
    out = np.zeros(phase.size, dtype=np.float64)
    for harmonic in range(1, max(harmonics, 1) + 1):
        amplitude = (2.0 / (harmonic * np.pi)) * np.sin(harmonic * np.pi * duty)
        if amplitude:
            out += amplitude * np.sin(harmonic * phase)
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    return out / peak if peak > 0 else out


def band_limited_triangle(phase, top_frequency, sample_rate):
    """Band-limited triangle (odd harmonics, 1/k², alternating sign)."""
    harmonics = harmonics_below_nyquist(top_frequency, sample_rate)
    out = np.zeros(phase.size, dtype=np.float64)
    sign = 1.0
    for harmonic in range(1, max(harmonics, 1) + 1, 2):
        out += sign * (8.0 / (np.pi ** 2 * harmonic * harmonic)) * np.sin(harmonic * phase)
        sign = -sign
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    return out / peak if peak > 0 else out


def chip_envelope(count, sample_rate, attack=0.004, decay=0.12, sustain=0.55,
                  release=0.025):
    """Plucky chip envelope: fast attack, exponential decay to a sustain."""
    time = np.arange(count) / sample_rate
    envelope = sustain + (1.0 - sustain) * np.exp(
        -np.maximum(time - attack, 0.0) / (decay / 3.0)
    )
    rise = min(max(int(attack * sample_rate), 1), count)
    envelope[:rise] *= np.linspace(0.0, 1.0, rise)
    fall = min(int(release * sample_rate), count // 2)
    if fall > 0:
        envelope[-fall:] *= np.linspace(1.0, 0.0, fall)
    return envelope


def add_echo(signal, delay_samples, feedback=ECHO_FEEDBACK):
    """Feedback comb echo: each block hears the previous one, quieter."""
    if delay_samples <= 0 or delay_samples >= signal.size:
        return signal
    out = signal.copy()
    for block in range(delay_samples, out.size, delay_samples):
        end = min(block + delay_samples, out.size)
        out[block:end] += feedback * out[block - delay_samples:
                                         block - delay_samples + end - block]
    return out


def render_song(notes, sample_rate, duty, tempo):
    """Render the arrangement: pulse lead + triangle bass + tempo-synced echo."""
    seconds_per_beat = 60.0 / tempo
    echo_delay = int(0.5 * seconds_per_beat * sample_rate)
    span = max(note[0] + note[1] for note in notes)
    total = int((span + 1.5 * seconds_per_beat) * sample_rate) + 1
    lead = np.zeros(total, dtype=np.float64)
    bass = np.zeros(total, dtype=np.float64)

    vibrato_peak = 2.0 ** (VIBRATO_CENTS / 1200.0)
    for start, duration, midi, on_beat in notes:
        count = int(duration * sample_rate)
        if count <= 0:
            continue
        offset = int(start * sample_rate)
        frequency = float(midi_to_hz(midi))
        phase = harmonic_phase(frequency, count, sample_rate)
        tone = band_limited_pulse(phase, frequency * vibrato_peak, sample_rate, duty)
        tone *= chip_envelope(count, sample_rate) * LEAD_GAIN
        end = min(offset + count, total)
        lead[offset:end] += tone[:end - offset]

        if on_beat and midi - 12 >= 24:
            bass_count = int(min(duration, 0.9 * seconds_per_beat) * sample_rate)
            if bass_count <= 0:
                continue
            bass_frequency = frequency / 2.0
            time = np.arange(bass_count) / sample_rate
            bass_phase = 2.0 * np.pi * bass_frequency * time
            bass_tone = band_limited_triangle(bass_phase, bass_frequency, sample_rate)
            bass_tone *= chip_envelope(
                bass_count, sample_rate, decay=0.2, sustain=0.4,
            ) * BASS_GAIN
            end = min(offset + bass_count, total)
            bass[offset:end] += bass_tone[:end - offset]

    mix = add_echo(lead + bass, echo_delay)
    peak = float(np.max(np.abs(mix)))
    if peak > 0:
        mix *= 0.9 / peak
    return mix.astype(np.float32)


def validate_melody(notes, samples_u8, sample_rate):
    """Score the result against "mush" heuristics.

    Returns (all_ok, report_lines). Each check compares a property a
    listenable melody must have against what actually came out, so a bad
    result is flagged objectively instead of discovered by ear.
    """
    durations = np.array([note[1] for note in notes])
    pitches = np.array([note[2] for note in notes])
    starts = np.array([note[0] for note in notes])

    checks = []

    def check(name, value, ok, target):
        checks.append((ok, f"{name}: {value} (target {target})"))

    sounding = float(durations.sum())
    density = len(notes) / sounding if sounding else float("inf")
    check("note density", f"{density:.1f}/s", 0.5 <= density <= 6.0, "0.5-6/s")

    median_duration = float(np.median(durations))
    check("median note length", f"{median_duration * 1000:.0f} ms",
          median_duration >= 0.12, ">= 120 ms")

    short_share = float((durations < 0.1).mean())
    check("notes under 100 ms", f"{short_share * 100:.0f}%",
          short_share < 0.1, "< 10%")

    trills = sum(
        1 for index in range(len(notes) - 2)
        if pitches[index] == pitches[index + 2]
        and pitches[index] != pitches[index + 1]
        and abs(pitches[index] - pitches[index + 1]) <= 2
        and durations[index + 1] < 0.15
    )
    trill_share = trills / len(notes) if notes else 0.0
    check("trill flicker", f"{trills} ({trill_share * 100:.0f}%)",
          trill_share < 0.05, "< 5%")

    pitch_span = float(pitches.max() - pitches.min()) if len(notes) else 0.0
    check("pitch span", f"{pitch_span:.0f} semitones", pitch_span <= 24, "<= 24")

    if len(notes) > 1:
        jumps = np.abs(np.diff(pitches))
        jump_share = float((jumps > 7).mean())
    else:
        jump_share = 0.0
    check("leaps over a fifth", f"{jump_share * 100:.0f}%",
          jump_share < 0.2, "< 20%")

    span = float(starts[-1] + durations[-1] - starts[0]) if len(notes) else 0.0
    coverage = sounding / span if span else 0.0
    check("sound coverage", f"{coverage * 100:.0f}%",
          0.3 <= coverage <= 0.95, "30-95%")

    samples = samples_u8.astype(np.float64) / 127.5 - 1.0
    spectrum = np.abs(np.fft.rfft(samples)) ** 2
    frequencies = np.fft.rfftfreq(samples.size, 1.0 / sample_rate)
    guard = frequencies > 0.92 * (sample_rate / 2.0)
    alias_share = float(spectrum[guard].sum() / spectrum.sum()) if spectrum.sum() else 0.0
    check("energy above the band limit", f"{alias_share * 100:.2f}%",
          alias_share < 0.01, "< 1%")

    clip_share = float(((samples_u8 == 0) | (samples_u8 == 255)).mean())
    check("clipped samples", f"{clip_share * 100:.2f}%", clip_share < 0.01, "< 1%")

    lines = [("ok   " if ok else "MUSH ") + text for ok, text in checks]
    return all(ok for ok, text in checks), lines


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


def extract_notes(f0, voiced, analysis_rate):
    """Pitch track to clean note list.

    Hysteresis segmentation, legato bridging, octave folding, ornament
    absorption, then a wider bridge for repeats of the same pitch (sung
    syllables re-attack the same note) and a flicker cutoff.
    """
    notes = segment_notes(f0, voiced, HOP, analysis_rate)
    notes = merge_notes(notes)
    notes = fold_octaves(notes)
    notes = absorb_trills(notes)
    notes = merge_notes(notes, bridge_seconds=REPEAT_BRIDGE_SECONDS, tolerance=0.5)
    notes = absorb_trills(notes)
    return [note for note in notes if note[1] >= MIN_NOTE_SECONDS]


def convert(input_path, output_path=None, format=None, bits=DEFAULT_BITS,
            rate=DEFAULT_RATE, duty=DEFAULT_DUTY, transpose=DEFAULT_TRANSPOSE):
    """Convert a song into a chiptune melody arrangement and write it to disk.

    Returns (destination_path, quality_ok, quality_report_lines).
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
    if not -24 <= transpose <= 24:
        raise ConversionError(
            f"--transpose must be between -24 and 24 semitones, got {transpose}"
        )

    destination = resolve_output_path(source, output_path, format)

    vocals, sample_rate = separate_vocals(source)
    f0, voiced = track_pitch(vocals, sample_rate)
    if not voiced.any():
        raise ConversionError(
            "No sung melody could be detected (the vocal stem may be empty or "
            "have no clear pitch)."
        )
    f0 = smooth_pitch(f0, voiced, window=5)

    notes = extract_notes(f0, voiced, sample_rate)
    if not notes:
        raise ConversionError(
            "No stable notes could be detected in the melody (try a clearer or "
            "longer track)."
        )

    mix = decode_mix(source, DEFAULT_RATE)
    tempo, beat_times = track_beats(mix, DEFAULT_RATE)

    notes = quantize_notes(notes, tempo, beat_times)
    notes = normalize_register(notes, transpose)
    notes = trim_leading_silence(notes)

    voice = render_song(notes, rate, duty, tempo)
    samples_u8 = to_uint8(quantize(voice, bits))
    write_output(destination, samples_u8, rate, 1)

    quality_ok, report = validate_melody(notes, samples_u8, rate)
    return destination, quality_ok, report
