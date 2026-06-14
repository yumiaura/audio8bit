# audio8bit

Turn a song into an 8-bit chiptune arrangement of its sung melody — the way an
80s game console would play it — straight from the command line.

**[English](https://github.com/yumiaura/audio8bit/blob/main/README.md)** | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

It removes the words, keeps the tune, and re-arranges it for chip voices:

1. **Vocal isolation** — [Demucs](https://github.com/adefossez/demucs) (a neural
   source-separation model) extracts the sung melody on its own.
2. **Pitch tracking** — librosa's pYIN follows the fundamental frequency of the
   isolated voice over time.
3. **Note extraction** — the pitch track is split into discrete notes with
   hysteresis: vibrato and scoops stay inside one note, voicing gaps are
   bridged, octave errors folded back, ornament flicker absorbed.
4. **Musicalisation** — note onsets snap to the song's own beat grid, the
   melody is shifted into a ringtone register and transposed into a different
   key (`--transpose`, default +3 semitones).
5. **Chip synthesis** — a band-limited pulse lead with vibrato and decay
   envelopes, a triangle bass an octave below on the beats and a tempo-synced
   echo; alias-free by construction (only harmonics below Nyquist are summed).
6. **8-bit output + quality report** — quantised to 8-bit PCM, written as WAV
   or re-encoded to your chosen format, then scored against "mush" heuristics
   (note density, fragmentation, trills, range, clipping) so a bad result is
   flagged objectively instead of discovered by ear.

> **Heads up:** Demucs pulls in PyTorch (a large install) and downloads its
> model (~80 MB) on first run, and separation takes a few minutes per track on
> CPU. This is what makes the melody actually recognizable. Everything runs
> locally.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (ships `ffmpeg` and `ffprobe`) on your `PATH`

## Install

```bash
pip install audio8bit
```

Or run straight from a clone (install the deps first: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## Usage

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Input audio (any format ffmpeg can read)     |
| `-o, --output`   | `output.<ext>`   | Output path (overrides `-f`)                 |
| `-f, --format`   | input's format   | Output format/extension, e.g. `ogg`          |
| `--transpose`    | `3`              | Key shift in semitones (negative allowed)    |
| `--bits`         | `8`              | Bit depth to quantise to (1–8)               |
| `--rate`         | `22050`          | Output sample rate in Hz                     |
| `--duty`         | `0.25`           | Pulse-wave duty cycle (0–1)                  |

Exit codes: `0` success, `1` conversion error, `2` bad arguments. Every run
ends with a quality report; failed checks print a warning to stderr.

## License

MIT
