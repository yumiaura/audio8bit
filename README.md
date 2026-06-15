# audio8bit

Turn a song into an 8-bit chiptune arrangement — the sung vocal **or** the
instrumental, with its harmony — the way an 80s game console would play it,
straight from the command line.

**[English](https://github.com/yumiaura/audio8bit/blob/main/README.md)** | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

It keeps the tune and re-arranges it for chip voices:

1. **Source separation** — [Demucs](https://github.com/adefossez/demucs) (a
   neural source-separation model) splits the song into stems, run
   deterministically so the same input always gives the same result. The melody
   is taken from the sung **vocals** or, for an instrumental, from the backing
   **lead** (drums and bass removed); `--source auto` uses the vocal when the
   song actually has one and the instrumental otherwise.
2. **Note finding** (`--method`, default `transcribe`) — a polyphonic
   transcription model ([basic-pitch](https://github.com/spotify/basic-pitch))
   turns the stem into real notes. `--voices chords` (default) plays every note,
   so harmony and bass are kept; `--voices lead` follows a single melody line
   through the chords (a Viterbi path, not the naive top line which jumps
   between lead and accompaniment). This holds together on chords and
   instrumentals, where frame-by-frame pitch tracking just jumps between voices
   and sounds random. `--method pitch` instead uses librosa's pYIN snapped to
   the song's beat grid (monophonic, lighter, no TensorFlow).
3. **Musicalisation** — an optional `--transpose` changes the key. `lead` is
   octave-shifted into a ringtone register; `chords` keeps the transcribed
   pitches so the harmony stays intact. Transcribed notes keep their own
   natural timing rather than being snapped to a grid.
4. **Chip synthesis** — each note is a band-limited pulse voice (the `lead` and
   `pitch` paths add vibrato/decay, and `pitch` adds a triangle bass and a
   tempo-synced echo); alias-free by construction (only harmonics below Nyquist
   are summed). `chords` scales each voice by its transcribed loudness for
   dynamics and levels the mix with a smooth limiter, so dense chords don't bury
   the single notes.
5. **8-bit output + quality report** — quantised to 8-bit PCM, written as WAV
   or re-encoded to your chosen format, then scored: melodic "mush" heuristics
   for a single line, or audio-level checks (silence, aliasing, clipping) for
   chords — so a bad result is flagged objectively instead of discovered by ear.

> **Heads up:** the default `transcribe` method pulls in basic-pitch
> (TensorFlow) and Demucs pulls in PyTorch — both large installs — and Demucs
> downloads its model (~80 MB) on first run. Separation plus transcription take
> a few minutes per track on CPU. This is what makes the melody actually
> recognizable. Everything runs locally.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (ships `ffmpeg` and `ffprobe`) on your `PATH`

## Install

```bash
pip install audio8bit
```

Or run straight from a clone (install the deps first: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## Usage

```bash
audio8bit -i song.mp3                      # -> output.mp3, full chords (keeps the input format)
audio8bit -i song.mp3 -V lead              # a single melody line instead of chords
audio8bit -i track.mp3 -s instrumental     # follow the instrumental, not vocals
audio8bit -i song.mp3 -m pitch             # lighter pYIN method (no TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitones up
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Input audio (any format ffmpeg can read)     |
| `-o, --output`   | `output.<ext>`   | Output path (overrides `-f`)                 |
| `-f, --format`   | input's format   | Output format/extension, e.g. `ogg`          |
| `-s, --source`   | `auto`           | Melody to follow: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Note finding: `transcribe` (polyphonic) or `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Transcribe output: `chords` (harmony) or `lead` (one line) |
| `--transpose`    | `0`              | Key shift in semitones (negative allowed)    |
| `--bits`         | `8`              | Bit depth to quantise to (1–8)               |
| `--rate`         | `22050`          | Output sample rate in Hz                     |
| `--duty`         | `0.25`           | Pulse-wave duty cycle (0–1)                  |

Exit codes: `0` success, `1` conversion error, `2` bad arguments. Every run
ends with a quality report; failed checks print a warning to stderr.

## License

MIT
