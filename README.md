# audio8bit

Turn any song into 8‑bit, video‑game‑style music — right from your terminal.
audio8bit finds the song's melody (and its chords) and replays them with retro
"chiptune" sounds, like an old game console.

**[English](https://github.com/yumiaura/audio8bit/blob/main/README.md)** | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## What it does

- Give it a song, get back a chiptune version of it.
- Works whether the song has **singing** or is **instrumental** — it picks the
  tune automatically.
- Everything runs on your own computer; nothing is uploaded.

## Before you start

You need two things:

- **Python 3.9 or newer**
- **ffmpeg** — a free tool for reading and writing audio. Install it with
  `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (macOS).

## Install

```bash
pip install audio8bit
```

> **First run is slow:** it downloads a small AI model (about 80 MB) and can
> take a few minutes. That's normal — later runs are faster.

## Use it

```bash
audio8bit -i song.mp3
```

This creates `output.mp3` in the current folder. That's it. Each run also
prints a short quality report so you can see the result came out clean.

Want something different? Here are the most common tweaks:

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## All options

| Option           | Default          | What it does                                  |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | The song to convert (mp3, wav, flac, …)       |
| `-o, --output`   | `output.<type>`  | Where to save the result                      |
| `-f, --format`   | same as input    | Save as a different type, e.g. `ogg`, `wav`   |
| `-s, --source`   | `auto`           | Where to take the tune: `vocals`, `instrumental`, or `auto` |
| `-m, --method`   | `transcribe`     | How notes are found: `transcribe` (best) or `pitch` (faster, lighter) |
| `-V, --voices`   | `chords`         | `chords` (with harmony) or `lead` (one melody line) |
| `--transpose`    | `0`              | Shift the key, in semitones (e.g. `5` up, `-5` down) |
| `--bits`         | `8`              | Sound resolution, 1–8 (lower = crunchier)     |
| `--rate`         | `22050`          | Sample rate in Hz (lower = more retro)        |
| `--duty`         | `0.25`           | Tone colour of the pulse wave, 0–1            |

## If something goes wrong

- **"ffmpeg not found"** — install ffmpeg (see *Before you start*).
- **The first run seems stuck** — it's downloading the AI model; give it a few
  minutes. It only happens once.
- **It doesn't sound like the song** — try `-s vocals` or `-s instrumental` to
  pick the right part, or `-V lead` for just the melody.

## How it works (optional reading)

1. Splits the song into parts (vocals, drums, bass, and the rest).
2. Detects the actual notes being played in the part you chose.
3. Replays those notes with simple 8‑bit "chip" sounds and saves the file.

## License

This project is licensed under the PolyForm Noncommercial License — see the [LICENSE](https://github.com/yumiaura/audio8bit/blob/main/LICENSE) file for details.
