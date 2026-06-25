## audio8bit - verwandle jedes Lied in 8-Bit-Chiptune-Musik

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | **[Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md)** | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Ein Kommandozeilenwerkzeug, das jedes Lied in 8-Bit-Musik im Videospielstil verwandelt. Es findet die Melodie (aus dem Gesang oder den Instrumenten) und spielt sie mit nostalgischen "Chiptune"-Klaengen nach, wie eine alte Spielkonsole. Alles laeuft lokal.

### Voraussetzungen

- **Python 3.9 oder hoeher**
- **ffmpeg** in deinem `PATH` (es bringt `ffmpeg` und `ffprobe` mit). Installiere es mit
  `sudo apt install ffmpeg` (Linux) oder `brew install ffmpeg` (macOS).

### Installation

```bash
pip install audio8bit
```

Oder von GitHub:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **Der erste Lauf ist langsam:** Es laedt ein kleines KI-Modell herunter (etwa 80 MB) und kann
> einige Minuten dauern. Das ist normal; spaetere Laeufe sind schneller.

### Verwendung

```bash
# Convert a song (auto-detects vocal or instrumental)
audio8bit -i song.mp3

# Just the main melody, no chords
audio8bit -i song.mp3 -V lead

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

### Kommandozeilenoptionen

- `-i, --input` - Eingabe-Audiodatei, erforderlich (jedes Format, das ffmpeg lesen kann)
- `-o, --output` - Ausgabepfad (Standard: `output.<ext>`)
- `-f, --format` - Ausgabeformat, z. B. `ogg`, `wav` (Standard: wie die Eingabe)
- `-s, --source` - Melodiequelle: `vocals`, `instrumental`, `auto` (Standard: `auto`)
- `-m, --method` - Notenfindung: `transcribe` oder `pitch` (Standard: `transcribe`)
- `-V, --voices` - `chords` (mit Harmonie) oder `lead` (einzelne Linie) (Standard: `chords`)
- `--transpose` - Tonartverschiebung in Halbtoenen (Standard: `0`)
- `--bits` - Bittiefe, 1-8, niedriger ist knuspriger (Standard: `8`)
- `--rate` - Abtastrate in Hz, niedriger ist nostalgischer (Standard: `22050`)
- `--duty` - Tastverhaeltnis der Pulswelle, 0-1 (Standard: `0.25`)
- `--version` - Version anzeigen

Exit-Codes: `0` Erfolg, `1` Konvertierungsfehler, `2` ungueltige Argumente.

### Funktionen

- Funktioniert mit **Gesangs**-Liedern und **Instrumentalstuecken** - waehlt die Melodiequelle automatisch aus.
- **Polyphone Transkription** (basic-pitch) behaelt die Akkorde und den Bass oder reduziert sie auf eine einzelne Lead-Linie.
- Quellentrennung mit **Demucs**, deterministisch, sodass dieselbe Eingabe immer dasselbe Ergebnis liefert.
- Alias-freie Chiptune-Synthese mit Lautstaerkedynamik und einem weichen Limiter.
- Tonartverschiebung sowie einstellbare Bittiefe, Abtastrate und Pulston.
- 8-Bit-PCM-Ausgabe als WAV oder in jedem Format, das ffmpeg schreiben kann.
- Ein Qualitaetsbericht nach jedem Lauf, und alles laeuft auf deinem eigenen Rechner.

### Lizenz

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
