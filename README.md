# audio8bit

Turn a song into a monophonic 8-bit melody — like an old phone ringtone or
early game console — straight from the command line.

It strips the vocals, follows the leading pitch and replays it with a single
square-wave voice:

1. **Vocal removal** — for stereo input, centre-panned content (lead vocals,
   usually kick/bass) is cancelled by subtracting the channels (`L − R`),
   leaving the backing instruments.
2. **Pitch tracking** — short frames are analysed by autocorrelation to follow
   the fundamental frequency over time (with a voiced/unvoiced gate).
3. **Square-wave synthesis** — one phase-continuous square voice replays the
   melody, optionally snapped to musical semitones.
4. **8-bit output** — quantised to 8-bit PCM at a low sample rate, written as
   WAV or re-encoded to your chosen format.

Runs on `numpy` and `ffmpeg` only — no machine-learning models. The melody is
extracted from a full mix, so the result is an approximation, not a transcription.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (ships `ffmpeg` and `ffprobe`) on your `PATH`

## Install

```bash
pip install audio8bit
```

Or run straight from a clone, without installing — only `numpy` is needed:

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
