"""DSP core: turn a song into a chiptune arrangement of its melody.

The pipeline transcribes a song's melody (with its harmony) and re-arranges it
the way an 80s game console would play it:

* source separation — Demucs (a neural source-separation model) splits the song
  into stems; the melody is taken from the sung ``vocals`` or, for an
  instrumental, from the backing lead in the ``other`` stem (drums and bass
  removed). ``auto`` uses the vocal when the song actually has one;
* note finding — by default a polyphonic transcription model (basic-pitch)
  turns the stem into real notes. ``--voices chords`` (default) plays every
  note, keeping harmony and bass; ``--voices lead`` follows one melody line
  through them with a Viterbi path (loudest-but-smooth, not the naive top line
  which jumps between lead and accompaniment). ``--method pitch`` instead uses
  librosa's pYIN snapped to the song's beat grid (monophonic, lighter, no
  TensorFlow);
* musicalisation — a uniform transpose can change the key; ``lead`` is also
  octave-shifted into a ringtone register, while ``chords`` keeps the
  transcribed pitches so the harmony stays intact. Transcribed notes keep
  their own natural timing rather than being quantised onto a grid;
* chip synthesis — each note is a band-limited pulse voice (the ``lead`` and
  ``pitch`` paths add vibrato/decay and, for ``pitch``, a triangle bass and a
  tempo-synced echo), all alias-free by construction;
* 8-bit output — the mix is quantised to 8-bit unsigned PCM and written as
  WAV, or re-encoded by ffmpeg to the chosen format;
* validation — a quality report is returned: melodic "mush" heuristics for a
  single line, or audio-level checks (silence, aliasing, clipping) for chords.

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
SEPARATION_SEED = 0
HOP = 512

# Melody source. "vocals" tracks the sung line; "instrumental" tracks the lead
# of the backing (drums and bass removed, i.e. Demucs' "other" stem); "auto"
# picks vocals when the song actually has a vocal and the instrumental
# otherwise. Each source gets its own pitch search band.
SOURCE_AUTO = "auto"
SOURCE_VOCALS = "vocals"
SOURCE_INSTRUMENTAL = "instrumental"
SOURCE_CHOICES = (SOURCE_AUTO, SOURCE_VOCALS, SOURCE_INSTRUMENTAL)
DEFAULT_SOURCE = SOURCE_AUTO

PITCH_FMIN = 98.0
PITCH_FMAX = 880.0
INSTRUMENT_FMIN = 130.0
INSTRUMENT_FMAX = 1000.0

# Melody-extraction method. "transcribe" runs a polyphonic note-transcription
# model (basic-pitch) and keeps the top line, which holds up on chord-heavy or
# instrumental material where frame-by-frame pitch tracking jumps between
# voices; "pitch" is the lighter pYIN tracker (no TensorFlow) and suits a
# cleanly monophonic source.
METHOD_TRANSCRIBE = "transcribe"
METHOD_PITCH = "pitch"
METHOD_CHOICES = (METHOD_TRANSCRIBE, METHOD_PITCH)
DEFAULT_METHOD = METHOD_TRANSCRIBE

# How many voices to play from a transcription. "chords" plays every
# transcribed note, so harmony and bass are kept (fuller, closer to the song);
# "lead" reduces it to a single melody line. Only applies to --method transcribe
# (pYIN is monophonic). "chords" keeps the notes' real pitches (a per-note
# octave shift would wreck the harmony), so only a uniform transpose is applied.
VOICES_CHORDS = "chords"
VOICES_LEAD = "lead"
VOICES_CHOICES = (VOICES_CHORDS, VOICES_LEAD)
DEFAULT_VOICES = VOICES_CHORDS
CHORD_MIN_SECONDS = 0.04
# Each chord voice is scaled by its transcribed loudness for real dynamics; the
# floor keeps soft notes audible. A smooth envelope limiter then tames dense
# chords without a global peak-normalise squashing the single notes — and
# without waveshaping, which would fold harmonics past Nyquist and re-alias.
CHORD_AMP_FLOOR = 0.2
LIMITER_THRESHOLD = 0.7
LIMITER_WINDOW_MS = 20.0

MELODY_FRAME = 0.02
MELODY_MIN_SECONDS = 0.06
MELODY_MERGE_GAP = 0.05
# Melody is searched in a band around the duration-and-loudness-weighted median
# pitch, so bass and high pads do not pull the line away.
MELODY_REGISTER_LOW = 9
MELODY_REGISTER_HIGH = 15
# Picking the loudest note each instant ("skyline") jumps between the lead and
# whatever chord tone is on top. Instead a Viterbi path trades note loudness
# against pitch distance, so the line stays smooth; a rest state lets it drop
# out when nothing in the band is loud enough.
MELODY_SMOOTHING = 0.5
MELODY_REST_LEVEL = 0.3
MELODY_REST_SWITCH = 2.0

# Auto: treat the vocal as present (and pick it over the instrumental) when its
# loudness is at least this fraction of the instrumental's, and above a floor.
VOCAL_PRESENCE_RATIO = 0.2
VOCAL_PRESENCE_FLOOR = 0.01

DEFAULT_RATE = 22050
DEFAULT_BITS = 8
DEFAULT_DUTY = 0.25
DEFAULT_TRANSPOSE = 0

PITCH_TOLERANCE = 0.6
DRIFT_FRAMES = 3
BRIDGE_SECONDS = 0.12
REPEAT_BRIDGE_SECONDS = 0.25
MIN_NOTE_SECONDS = 0.12
OCTAVE_FOLD_SEMITONES = 7
CONTEXT_SECONDS = 4.0
OCTAVE_COLLAPSE_SEMITONES = 12

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


def separate_sources(path):
    """Split a song into its Demucs stems.

    Returns ``(stems, sample_rate)`` where ``stems`` maps each source name
    (``drums``, ``bass``, ``other``, ``vocals``) to a mono float32 signal.
    """
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

    wav = AudioFile(str(path)).read(
        streams=0, samplerate=model.samplerate, channels=model.audio_channels,
    )
    reference = wav.mean(0)
    wav = (wav - reference.mean()) / (reference.std() + 1e-8)
    # shifts=0 disables the random shift-and-average trick so the same input
    # always yields the same stems; the seed pins any remaining randomness.
    # Without this the melody (and so the whole output) changes run to run.
    torch.manual_seed(SEPARATION_SEED)
    with torch.no_grad():
        sources = apply_model(
            model, wav[None], device="cpu", progress=False, shifts=0,
        )[0]
    sources = sources * reference.std() + reference.mean()

    stems = {
        name: sources[index].mean(0).cpu().numpy().astype(np.float32)
        for index, name in enumerate(model.sources)
    }
    return stems, int(model.samplerate)


def signal_rms(signal):
    """Root-mean-square level of a signal (its loudness)."""
    if signal is None or signal.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(signal.astype(np.float64) ** 2)))


def select_melody(stems, source):
    """Pick the stem to take the melody from and its pitch search band.

    Returns ``(signal, fmin, fmax, label)``. The vocal stem carries the sung
    line; the ``other`` stem carries the backing lead (drums and bass gone).
    ``auto`` uses the vocal only when it is actually present in the mix.
    """
    vocals = stems.get("vocals")
    instrumental = stems.get("other")
    if instrumental is None:
        raise ConversionError(
            "Demucs returned no 'other' stem to take an instrumental melody "
            f"from (got: {', '.join(stems)})."
        )

    if source == SOURCE_VOCALS:
        if vocals is None:
            raise ConversionError("Demucs returned no 'vocals' stem.")
        return vocals, PITCH_FMIN, PITCH_FMAX, "vocals"
    if source == SOURCE_INSTRUMENTAL:
        return instrumental, INSTRUMENT_FMIN, INSTRUMENT_FMAX, "instrumental"

    vocal_level = signal_rms(vocals)
    instrumental_level = signal_rms(instrumental)
    threshold = max(VOCAL_PRESENCE_FLOOR, VOCAL_PRESENCE_RATIO * instrumental_level)
    if vocal_level >= threshold:
        return vocals, PITCH_FMIN, PITCH_FMAX, "vocals (auto)"
    return instrumental, INSTRUMENT_FMIN, INSTRUMENT_FMAX, "instrumental (auto)"


def write_wav16(path, signal, sample_rate):
    """Write a mono float signal as a 16-bit signed PCM WAV (for transcription)."""
    peak = float(np.max(np.abs(signal))) or 1.0
    scaled = np.clip(signal / peak * 0.95, -1.0, 1.0)
    samples = (scaled * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(samples.tobytes())


def transcribe_notes(signal, sample_rate):
    """Transcribe a (possibly polyphonic) signal into notes with basic-pitch.

    Returns a list of (start_seconds, end_seconds, midi_pitch, amplitude).
    Unlike pYIN this is a trained polyphonic model, so it reports real note
    onsets across overlapping voices instead of one wandering pitch per frame.
    """
    try:
        from basic_pitch.inference import predict
    except ImportError as missing:
        raise ConversionError(
            "basic-pitch is required for note transcription. Install it with "
            "'pip install basic-pitch', or use --method pitch."
        ) from missing
    try:
        from basic_pitch import ICASSP_2022_MODEL_PATH
        model = ICASSP_2022_MODEL_PATH
    except ImportError:
        model = None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        tmp_wav = Path(handle.name)
    try:
        write_wav16(tmp_wav, signal, sample_rate)
        result = predict(str(tmp_wav), model) if model is not None else predict(str(tmp_wav))
    finally:
        tmp_wav.unlink(missing_ok=True)

    note_events = result[2]
    return [
        (float(event[0]), float(event[1]), int(event[2]), float(event[3]))
        for event in note_events
    ]


def melody_register(events):
    """Pitch band the melody is searched in, around its weighted-median pitch."""
    pitches = np.array([pitch for start, end, pitch, amplitude in events])
    weights = np.array([
        max(1, int((end - start) * amplitude * 100))
        for start, end, pitch, amplitude in events
    ])
    center = float(np.median(np.repeat(pitches, weights)))
    return center - MELODY_REGISTER_LOW, center + MELODY_REGISTER_HIGH


def frame_candidates(events, frames, frame, low, high):
    """For each time frame, the in-band notes sounding then as {pitch: loudness}."""
    candidates = [{} for _ in range(frames)]
    for start, end, pitch, amplitude in events:
        if not low <= pitch <= high:
            continue
        first = max(0, int(start / frame))
        last = min(frames - 1, int(end / frame))
        for index in range(first, last + 1):
            slot = candidates[index]
            if amplitude > slot.get(pitch, 0.0):
                slot[pitch] = amplitude
    return candidates


def melody_path(candidates, smoothing=MELODY_SMOOTHING, rest_level=MELODY_REST_LEVEL,
                rest_switch=MELODY_REST_SWITCH):
    """Viterbi: the smoothest loud line through the candidates, with rests.

    Each frame's state is one of its candidate pitches or a rest. Reward is the
    note's loudness; the transition cost is ``smoothing`` per semitone moved, so
    the path prefers staying near the previous pitch over jumping to a louder
    but distant chord tone. Returns one pitch (or None) per frame.
    """
    rest = None
    states = [list(slot.items()) + [(rest, rest_level)] for slot in candidates]
    scores = [reward for pitch, reward in states[0]]
    back = [[None] * len(states[0])]
    for index in range(1, len(states)):
        previous = states[index - 1]
        row_scores = []
        row_back = []
        for pitch, reward in states[index]:
            best_value = None
            best_prev = 0
            for prev_index, (prev_pitch, prev_reward) in enumerate(previous):
                if prev_pitch is None or pitch is None:
                    cost = 0.0 if prev_pitch == pitch else rest_switch
                else:
                    cost = abs(prev_pitch - pitch)
                value = scores[prev_index] - smoothing * cost
                if best_value is None or value > best_value:
                    best_value = value
                    best_prev = prev_index
            row_scores.append(reward + best_value)
            row_back.append(best_prev)
        scores = row_scores
        back.append(row_back)

    index = len(states) - 1
    state = max(range(len(scores)), key=lambda k: scores[k])
    path = [None] * len(states)
    while index >= 0:
        path[index] = states[index][state][0]
        state = back[index][state]
        index -= 1
    return path


def melody_line(events, frame=MELODY_FRAME, min_seconds=MELODY_MIN_SECONDS,
                merge_gap=MELODY_MERGE_GAP):
    """Extract one monophonic melody from transcribed polyphonic notes.

    Keeps notes in the melodic register, then follows the loudest line that
    stays smooth (see ``melody_path``) instead of the naive top line, which
    jumps between the lead and accompaniment and sounds like random keys.
    Returns [start_seconds, duration_seconds, midi_pitch].
    """
    if not events:
        return []
    low, high = melody_register(events)
    end = max(end_time for start, end_time, pitch, amplitude in events)
    frames = int(end / frame) + 1
    candidates = frame_candidates(events, frames, frame, low, high)
    path = melody_path(candidates)

    notes = []
    index = 0
    while index < frames:
        if path[index] is None:
            index += 1
            continue
        run = index
        while run < frames and path[run] == path[index]:
            run += 1
        notes.append([index * frame, (run - index) * frame, float(path[index])])
        index = run

    merged = []
    for note in notes:
        if (merged and abs(merged[-1][2] - note[2]) < 0.5
                and note[0] - (merged[-1][0] + merged[-1][1]) <= merge_gap):
            merged[-1][1] = note[0] + note[1] - merged[-1][0]
        else:
            merged.append(note)
    return [note for note in merged if note[1] >= min_seconds]


def render_melody(notes, sample_rate, duty=DEFAULT_DUTY):
    """Render a monophonic note line as a clean chip lead at its natural timing.

    Transcribed notes already carry musical onsets and lengths, so there is no
    beat grid to snap to — that snapping is what made earlier output robotic.
    """
    span = max(start + duration for start, duration, midi in notes)
    total = int(span * sample_rate) + sample_rate
    buffer = np.zeros(total, dtype=np.float64)
    for start, duration, midi in notes:
        count = int(duration * sample_rate)
        if count <= 0:
            continue
        frequency = float(midi_to_hz(midi))
        time = np.arange(count) / sample_rate
        tone = band_limited_pulse(2.0 * np.pi * frequency * time, frequency,
                                  sample_rate, duty)
        tone *= chip_envelope(count, sample_rate) * LEAD_GAIN
        offset = int(start * sample_rate)
        end = min(offset + count, total)
        buffer[offset:end] += tone[:end - offset]
    peak = float(np.max(np.abs(buffer)))
    if peak > 0:
        buffer *= 0.9 / peak
    return buffer.astype(np.float32)


def smooth_envelope(signal, window):
    """Centred moving average of ``signal`` over ``window`` samples (O(n))."""
    if window <= 1:
        return np.abs(signal)
    half = window // 2
    padded = np.pad(np.abs(signal), (half, window - 1 - half), mode="edge")
    cumulative = np.cumsum(np.insert(padded, 0, 0.0))
    return (cumulative[window:] - cumulative[:-window]) / window


def soft_limiter(signal, sample_rate, threshold=LIMITER_THRESHOLD,
                 window_ms=LIMITER_WINDOW_MS):
    """Tame loud (dense) stretches with a smooth gain, leaving quiet parts alone.

    A peak-normalise scales the whole mix down to the busiest chord, which
    buries the single notes. Instead this follows a smoothed amplitude envelope
    and pulls the gain down only where it exceeds ``threshold``. The gain is a
    low-frequency curve, so multiplying by it adds no audible harmonics (no
    aliasing) — unlike tanh-style waveshaping.
    """
    window = max(1, int(window_ms / 1000.0 * sample_rate))
    envelope = np.maximum(smooth_envelope(signal, window), 1e-6)
    gain = np.minimum(1.0, threshold / envelope)
    gain = smooth_envelope(gain, window)
    out = signal * gain
    peak = float(np.max(np.abs(out)))
    if peak > 0.95:
        out *= 0.95 / peak
    return out


def render_chords(events, sample_rate, duty=DEFAULT_DUTY, transpose=0,
                  min_seconds=CHORD_MIN_SECONDS):
    """Render every transcribed note, so harmony and bass are kept (polyphony).

    Each note is a band-limited pulse voice scaled by its transcribed loudness
    (so the mix has real dynamics), summed, then levelled by a smooth limiter.
    Pitches are kept as transcribed (only a uniform ``transpose`` is applied) so
    the chords stay intact — a per-note octave shift would scramble the harmony.
    """
    notes = [event for event in events if event[1] - event[0] >= min_seconds]
    if not notes:
        notes = list(events)
    span = max(end for start, end, pitch, amplitude in notes)
    total = int(span * sample_rate) + sample_rate
    buffer = np.zeros(total, dtype=np.float64)
    for start, end, pitch, amplitude in notes:
        count = int((end - start) * sample_rate)
        if count <= 0:
            continue
        frequency = float(midi_to_hz(pitch + transpose))
        time = np.arange(count) / sample_rate
        tone = band_limited_pulse(2.0 * np.pi * frequency * time, frequency,
                                  sample_rate, duty)
        loudness = CHORD_AMP_FLOOR + (1.0 - CHORD_AMP_FLOOR) * min(1.0, amplitude)
        tone *= chip_envelope(count, sample_rate) * loudness
        offset = int(start * sample_rate)
        stop = min(offset + count, total)
        buffer[offset:stop] += tone[:stop - offset]
    return soft_limiter(buffer, sample_rate).astype(np.float32)


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


def collapse_octaves(notes, limit=OCTAVE_COLLAPSE_SEMITONES):
    """Fold octave outliers to within ``limit`` semitones of the melody centre.

    Even after local folding, pitch tracking leaves a few notes a whole octave
    off the line. Clamping every note to within an octave of the
    duration-weighted median pitch removes those audible jumps and caps the
    overall span, with almost no effect on the real contour (measured: the
    span drops by half while pitch fidelity falls only a few percent).
    """
    if not notes:
        return notes
    weights = np.array([max(1, int(note[1] * 100)) for note in notes])
    pitches = np.array([note[2] for note in notes])
    center = float(np.median(np.repeat(pitches, weights)))
    for note in notes:
        while note[2] - center > limit:
            note[2] -= 12.0
        while center - note[2] > limit:
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
          jump_share < 0.3, "< 30%")

    span = float(starts[-1] + durations[-1] - starts[0]) if len(notes) else 0.0
    coverage = sounding / span if span else 0.0
    # A sparse melody (long instrumental stretches with no singing) is normal,
    # not mush; only flag a near-empty result or a non-stop drone.
    check("sound coverage", f"{coverage * 100:.0f}%",
          0.12 <= coverage <= 0.97, "12-97%")

    aliasing = alias_share(samples_u8, sample_rate)
    check("energy above the band limit", f"{aliasing * 100:.2f}%",
          aliasing < 0.01, "< 1%")

    clip_share = float(((samples_u8 == 0) | (samples_u8 == 255)).mean())
    check("clipped samples", f"{clip_share * 100:.2f}%", clip_share < 0.01, "< 1%")

    lines = [("ok   " if ok else "MUSH ") + text for ok, text in checks]
    return all(ok for ok, text in checks), lines


def alias_share(samples_u8, sample_rate):
    """Fraction of spectral energy above the band-limit guard (folded aliasing)."""
    samples = samples_u8.astype(np.float64) / 127.5 - 1.0
    spectrum = np.abs(np.fft.rfft(samples)) ** 2
    frequencies = np.fft.rfftfreq(samples.size, 1.0 / sample_rate)
    guard = frequencies > 0.92 * (sample_rate / 2.0)
    return float(spectrum[guard].sum() / spectrum.sum()) if spectrum.sum() else 0.0


def validate_audio(samples_u8, sample_rate, note_count):
    """Audio-level checks for the polyphonic path (melodic "mush" ones don't fit).

    A chord render is not a single line, so note density, trills, span and leaps
    are meaningless; this just confirms the result has content, stays alias-free
    and does not clip.
    """
    checks = []

    def check(name, value, ok, target):
        checks.append((ok, f"{name}: {value} (target {target})"))

    check("transcribed notes", f"{note_count}", note_count > 0, "> 0")

    loudness = float(np.std(samples_u8.astype(np.float64)))
    check("not silent", f"std {loudness:.1f}", loudness > 1.0, "> 1")

    aliasing = alias_share(samples_u8, sample_rate)
    check("energy above the band limit", f"{aliasing * 100:.2f}%",
          aliasing < 0.01, "< 1%")

    clip_share = float(((samples_u8 == 0) | (samples_u8 == 255)).mean())
    check("clipped samples", f"{clip_share * 100:.2f}%", clip_share < 0.01, "< 1%")

    lines = [("ok   " if ok else "BAD  ") + text for ok, text in checks]
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

    Hysteresis segmentation, legato bridging, octave folding (local then a
    global collapse onto the melody centre), ornament absorption, then a wider
    bridge for repeats of the same pitch (sung syllables re-attack the same
    note) and a flicker cutoff.
    """
    notes = segment_notes(f0, voiced, HOP, analysis_rate)
    notes = merge_notes(notes)
    notes = fold_octaves(notes)
    notes = collapse_octaves(notes)
    notes = absorb_trills(notes)
    notes = merge_notes(notes, bridge_seconds=REPEAT_BRIDGE_SECONDS, tolerance=0.5)
    notes = absorb_trills(notes)
    return [note for note in notes if note[1] >= MIN_NOTE_SECONDS]


def extract_by_pitch(signal, sample_rate, fmin, fmax, picked, transpose, origin):
    """Old path: pYIN pitch track, then snap the notes onto the song's beat."""
    f0, voiced = track_pitch(signal, sample_rate, fmin=fmin, fmax=fmax)
    if not voiced.any():
        raise ConversionError(
            f"No melody could be detected in the {picked} (it may be empty or "
            "have no clear pitch). Try --source vocals or --source instrumental."
        )
    f0 = smooth_pitch(f0, voiced, window=5)
    notes = extract_notes(f0, voiced, sample_rate)
    if not notes:
        raise ConversionError(
            "No stable notes could be detected in the melody (try a clearer or "
            "longer track)."
        )
    mix = decode_mix(origin, DEFAULT_RATE)
    tempo, beat_times = track_beats(mix, DEFAULT_RATE)
    notes = quantize_notes(notes, tempo, beat_times)
    notes = normalize_register(notes, transpose)
    notes = trim_leading_silence(notes)
    return notes, tempo


def transcribe_events(signal, sample_rate, picked):
    """Transcribe a stem to notes, raising if nothing comes back."""
    events = transcribe_notes(signal, sample_rate)
    if not events:
        raise ConversionError(
            f"No notes could be transcribed from the {picked} (try a clearer "
            "track, or --source instrumental / --source vocals)."
        )
    return events


def lead_from_events(events, transpose):
    """Reduce transcribed notes to one melody line in the ringtone register."""
    notes = melody_line(events)
    if not notes:
        raise ConversionError("No melodic line could be extracted from the notes.")
    notes = normalize_register(notes, transpose)
    notes = trim_leading_silence(notes)
    return notes


def convert(input_path, output_path=None, format=None, bits=DEFAULT_BITS,
            rate=DEFAULT_RATE, duty=DEFAULT_DUTY, transpose=DEFAULT_TRANSPOSE,
            source=DEFAULT_SOURCE, method=DEFAULT_METHOD, voices=DEFAULT_VOICES):
    """Convert a song into a chiptune arrangement and write it to disk.

    ``source`` chooses the stem (``vocals``/``instrumental``/``auto``).
    ``method`` chooses how notes are found (``transcribe``/``pitch``).
    ``voices`` (transcribe only) chooses ``chords`` (every note, harmony kept)
    or ``lead`` (a single melody line).

    Returns (destination_path, quality_ok, quality_report_lines).
    """
    origin = Path(input_path)
    if not origin.is_file():
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
    if source not in SOURCE_CHOICES:
        raise ConversionError(
            f"--source must be one of {', '.join(SOURCE_CHOICES)}, got '{source}'"
        )
    if method not in METHOD_CHOICES:
        raise ConversionError(
            f"--method must be one of {', '.join(METHOD_CHOICES)}, got '{method}'"
        )
    if voices not in VOICES_CHOICES:
        raise ConversionError(
            f"--voices must be one of {', '.join(VOICES_CHOICES)}, got '{voices}'"
        )

    destination = resolve_output_path(origin, output_path, format)

    stems, sample_rate = separate_sources(origin)
    signal, fmin, fmax, picked = select_melody(stems, source)
    info = [f"melody source: {picked}", f"method: {method}"]

    if method == METHOD_TRANSCRIBE and voices == VOICES_CHORDS:
        events = transcribe_events(signal, sample_rate, picked)
        voice = render_chords(events, rate, duty, transpose)
        samples_u8 = to_uint8(quantize(voice, bits))
        write_output(destination, samples_u8, rate, 1)
        quality_ok, report = validate_audio(samples_u8, rate, len(events))
        info.append("voices: chords")
        return destination, quality_ok, info + report

    if method == METHOD_TRANSCRIBE:
        events = transcribe_events(signal, sample_rate, picked)
        notes = lead_from_events(events, transpose)
        voice = render_melody(notes, rate, duty)
        info.append("voices: lead")
    else:
        notes, tempo = extract_by_pitch(
            signal, sample_rate, fmin, fmax, picked, transpose, origin,
        )
        voice = render_song(notes, rate, duty, tempo)

    samples_u8 = to_uint8(quantize(voice, bits))
    write_output(destination, samples_u8, rate, 1)
    quality_ok, report = validate_melody(notes, samples_u8, rate)
    return destination, quality_ok, info + report
