# audio8bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pypi/dm/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

Verwandle jeden Song in 8-Bit-Musik im Videospiel-Stil - direkt aus deinem
Terminal. audio8bit findet die Melodie des Songs (und seine Akkorde) und spielt
sie mit nostalgischen "Chiptune"-Klängen ab, wie eine alte Spielkonsole.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | **[Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md)** | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## Was es macht

- Gib ihm einen Song und du bekommst eine Chiptune-Version davon zurück.
- Funktioniert, egal ob der Song **Gesang** enthält oder **instrumental** ist -
  die Melodie wird automatisch ausgewählt.
- Alles läuft auf deinem eigenen Computer; nichts wird hochgeladen.

## Bevor du loslegst

Du brauchst zwei Dinge:

- **Python 3.9 oder neuer**
- **ffmpeg** - ein kostenloses Tool zum Lesen und Schreiben von Audio.
  Installiere es mit `sudo apt install ffmpeg` (Linux) oder
  `brew install ffmpeg` (macOS).

## Installation

```bash
pip install audio8bit
```

> **Der erste Start ist langsam:** Es lädt ein kleines KI-Modell (ca. 80 MB)
> herunter und kann ein paar Minuten dauern. Das ist normal - spätere Starts
> sind schneller.

## Verwendung

```bash
audio8bit -i song.mp3
```

Das erstellt `output.mp3` im aktuellen Ordner. Das war's. Bei jedem Durchlauf
wird außerdem ein kurzer Qualitätsbericht ausgegeben, damit du sehen kannst,
dass das Ergebnis sauber geworden ist.

Möchtest du etwas anderes? Hier sind die häufigsten Anpassungen:

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## Alle Optionen

| Option           | Default          | Was es macht                                  |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | Der zu konvertierende Song (mp3, wav, flac, ...) |
| `-o, --output`   | `output.<type>`  | Wo das Ergebnis gespeichert wird              |
| `-f, --format`   | same as input    | Als anderen Typ speichern, z. B. `ogg`, `wav` |
| `-s, --source`   | `auto`           | Woher die Melodie genommen wird: `vocals`, `instrumental` oder `auto` |
| `-m, --method`   | `transcribe`     | Wie Noten gefunden werden: `transcribe` (am besten) oder `pitch` (schneller, leichter) |
| `-V, --voices`   | `chords`         | `chords` (mit Harmonie) oder `lead` (eine einzelne Melodielinie) |
| `--transpose`    | `0`              | Verschiebt die Tonart, in Halbtönen (z. B. `5` hoch, `-5` runter) |
| `--bits`         | `8`              | Klangauflösung, 1-8 (niedriger = kratziger)   |
| `--rate`         | `22050`          | Abtastrate in Hz (niedriger = mehr Retro)     |
| `--duty`         | `0.25`           | Klangfarbe der Pulswelle, 0-1                 |

## Wenn etwas schiefgeht

- **"ffmpeg not found"** - installiere ffmpeg (siehe *Bevor du loslegst*).
- **Der erste Start scheint zu hängen** - es lädt gerade das KI-Modell herunter;
  gib ihm ein paar Minuten. Das passiert nur einmal.
- **Es klingt nicht wie der Song** - probiere `-s vocals` oder `-s instrumental`,
  um den richtigen Teil auszuwählen, oder `-V lead` für nur die Melodie.

## Wie es funktioniert (optionale Lektüre)

1. Teilt den Song in seine Bestandteile auf (Gesang, Schlagzeug, Bass und den Rest).
2. Erkennt die tatsächlich gespielten Noten in dem von dir gewählten Teil.
3. Spielt diese Noten mit einfachen 8-Bit-"Chip"-Klängen ab und speichert die Datei.

## Lizenz

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
