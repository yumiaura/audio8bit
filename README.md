# audio8bit

Convert any audio file into 8-bit / chiptune-style sound from the command line.

It runs a classic **bitcrusher** over the audio — lowering the sample rate
(aliasing, "pixelated" feel) and reducing the bit depth (gritty, stepped
sound) — and writes a real 8-bit unsigned PCM WAV.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (ships `ffmpeg` and `ffprobe`) on your `PATH`

## Install

```bash
pip install audio8bit
```

## Usage

```bash
audio8bit -i song.mp3                 # -> song_8bit.wav next to the input
audio8bit -i song.mp3 -o crushed.wav  # explicit output
audio8bit -i song.flac --bits 4 --rate 11025 --mono
```

| Flag            | Default               | Description                              |
| --------------- | --------------------- | ---------------------------------------- |
| `-i, --input`   | — (required)          | Input audio (any format ffmpeg can read) |
| `-o, --output`  | `<input>_8bit.wav`    | Output path; non-`.wav` is re-encoded    |
| `--bits`        | `8`                   | Bit depth to quantise to (1–8)           |
| `--rate`        | `8000`                | Target sample rate in Hz                 |
| `--mono`        | off                   | Downmix to a single channel              |

Exit codes: `0` success, `1` conversion error, `2` bad arguments.

## License

MIT
