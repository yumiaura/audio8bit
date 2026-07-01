## audio8bit - turn any song into 8-bit chiptune music

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

**[English](https://github.com/yumiaura/audio8bit/blob/main/README.md)** | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

A command-line tool that turns any song into 8-bit, video-game-style music. It finds the melody (from the vocals or the instruments) and replays it with retro "chiptune" sounds, like an old game console. Everything runs locally.

### Requirements

- **Python 3.9 or higher**
- **ffmpeg** on your `PATH` (it ships `ffmpeg` and `ffprobe`). Install it with
  `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (macOS).

### Installation

```bash
pip install audio8bit
```

Or from GitHub:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **First run is slow:** it downloads a small AI model (about 80 MB) and can take
> a few minutes. That is normal; later runs are faster.

### Usage

```bash
# Convert a song (auto-detects vocal or instrumental)
audio8bit -i song.mp3

# Just the main melody, no chords
audio8bit -i song.mp3 -V lead

# Multi-instrument band: pulse lead + pulse harmony + triangle bass
audio8bit -i song.mp3 -V band

# Take the tune from the singing or from the instruments
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Save as a different format
audio8bit -i song.mp3 -f ogg

# Play it 5 semitones higher
audio8bit -i song.mp3 --transpose 5

# Show help and version
audio8bit --help
audio8bit --version
```

### Command Line Options

- `-i, --input` - input audio file, required (any format ffmpeg can read)
- `-o, --output` - output path (default: `output.<ext>`)
- `-f, --format` - output format, e.g. `ogg`, `wav` (default: same as input)
- `-s, --source` - melody source: `vocals`, `instrumental`, `auto` (default: `auto`)
- `-m, --method` - note finding: `transcribe` or `pitch` (default: `transcribe`)
- `-V, --voices` - `chords` (one voice, with harmony), `lead` (single line), or `band` (multi-instrument: pulse lead + pulse harmony + triangle bass) (default: `chords`)
- `--transpose` - key shift in semitones (default: `0`)
- `--bits` - bit depth, 1-8, lower is crunchier (default: `8`)
- `--rate` - sample rate in Hz, lower is more retro (default: `22050`)
- `--duty` - pulse-wave duty cycle, 0-1 (default: `0.25`)
- `--no-cache` - do not read or write cached Demucs stems
- `--cache-dir` - directory for cached stems (default: `~/.cache/audio8bit`, or `$AUDIO8BIT_CACHE_DIR`)
- `--version` - show version

Exit codes: `0` success, `1` conversion error, `2` bad arguments.

### Features

- Works with **vocal** songs and **instrumentals** - picks the melody source automatically.
- **Polyphonic transcription** (basic-pitch) keeps the chords and bass, reduces them to a single lead line, or splits them across chip channels as a multi-instrument band (pulse lead, pulse harmony, triangle bass).
- Source separation with **Demucs**, deterministic so the same input always gives the same result.
- Alias-free chiptune synthesis with loudness dynamics and a smooth limiter.
- Key transposition and adjustable bit depth, sample rate and pulse tone.
- 8-bit PCM output as WAV, or any format ffmpeg can write.
- A quality report after every run, and everything runs on your own machine.

### License

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
