# audio8bit

Turn a song's sung melody into a monophonic 8-bit ringtone — like an old phone
or early game console — straight from the command line.

It isolates the vocal, follows its pitch and replays it with a single
square-wave voice ("remove the words, keep the melody"):

1. **Vocal isolation** — [Demucs](https://github.com/adefossez/demucs) (a neural
   source-separation model) extracts the sung melody on its own.
2. **Pitch tracking** — librosa's pYIN follows the fundamental frequency of the
   isolated, monophonic voice over time.
3. **Square-wave synthesis** — one phase-continuous square voice replays the
   melody, optionally snapped to musical semitones.
4. **8-bit output** — quantised to 8-bit PCM at a low sample rate, written as
   WAV or re-encoded to your chosen format.

> **Heads up:** Demucs pulls in PyTorch (a large install) and downloads its
> model (~80 MB) on first run, and separation takes a few seconds per track.
> This is what makes the melody actually recognizable. Everything runs locally.

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
audio8bit -i song.mp3 --no-semitones --duty 0.25
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Input audio (any format ffmpeg can read)     |
| `-o, --output`   | `output.<ext>`   | Output path (overrides `-f`)                 |
| `-f, --format`   | input's format   | Output format/extension, e.g. `ogg`          |
| `--bits`         | `8`              | Bit depth to quantise to (1–8)               |
| `--rate`         | `8000`           | Output sample rate in Hz                     |
| `--duty`         | `0.5`            | Square-wave duty cycle (0–1)                 |
| `--semitones`    | on               | Snap the melody to semitones (`--no-semitones` to disable) |

Exit codes: `0` success, `1` conversion error, `2` bad arguments.

## License

MIT
