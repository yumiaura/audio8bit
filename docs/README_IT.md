## audio8bit - trasforma qualsiasi canzone in musica chiptune a 8 bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | **[Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md)** | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Uno strumento da riga di comando che trasforma qualsiasi canzone in musica a 8 bit in stile videogioco. Individua la melodia (dalla voce o dagli strumenti) e la riproduce con suoni retro "chiptune", come una vecchia console per videogiochi. Tutto viene eseguito in locale.

### Requisiti

- **Python 3.9 o superiore**
- **ffmpeg** nel tuo `PATH` (include `ffmpeg` e `ffprobe`). Installalo con
  `sudo apt install ffmpeg` (Linux) o `brew install ffmpeg` (macOS).

### Installazione

```bash
pip install audio8bit
```

Oppure da GitHub:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **La prima esecuzione e' lenta:** scarica un piccolo modello di IA (circa 80 MB) e puo' richiedere
> qualche minuto. E' normale; le esecuzioni successive sono piu' veloci.

### Utilizzo

```bash
# Convert a song (auto-detects vocal or instrumental)
audio8bit -i song.mp3

# Just the main melody, no chords
audio8bit -i song.mp3 -V lead

# Band multi-strumento: lead a impulso + armonia a impulso + basso a triangolo
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

### Opzioni della riga di comando

- `-i, --input` - file audio di ingresso, obbligatorio (qualsiasi formato che ffmpeg puo' leggere)
- `-o, --output` - percorso di uscita (predefinito: `output.<ext>`)
- `-f, --format` - formato di uscita, es. `ogg`, `wav` (predefinito: lo stesso dell'ingresso)
- `-s, --source` - sorgente della melodia: `vocals`, `instrumental`, `auto` (predefinito: `auto`)
- `-m, --method` - individuazione delle note: `transcribe` o `pitch` (predefinito: `transcribe`)
- `-V, --voices` - `chords` (con armonia) o `lead` (linea singola) o `band` (multi-strumento: lead a impulso + armonia a impulso + basso a triangolo) (predefinito: `chords`)
- `--transpose` - cambio di tonalita' in semitoni (predefinito: `0`)
- `--bits` - profondita' di bit, 1-8, piu' basso e' piu' grezzo (predefinito: `8`)
- `--rate` - frequenza di campionamento in Hz, piu' bassa e' piu' retro (predefinito: `22050`)
- `--duty` - duty cycle dell'onda a impulsi, 0-1 (predefinito: `0.25`)
- `--no-cache` - non leggere né scrivere gli stem di Demucs nella cache
- `--cache-dir` - directory per gli stem in cache (predefinito: `~/.cache/audio8bit`, oppure `$AUDIO8BIT_CACHE_DIR`)
- `--version` - mostra la versione

Codici di uscita: `0` successo, `1` errore di conversione, `2` argomenti errati.

### Funzionalita'

- Funziona con canzoni **vocali** e **strumentali** - sceglie automaticamente la sorgente della melodia.
- **Trascrizione polifonica** (basic-pitch) mantiene gli accordi e il basso, oppure li riduce a una singola linea principale. La modalita `band` li distribuisce su canali chip (lead a impulso, armonia a impulso, basso a triangolo).
- Separazione delle sorgenti con **Demucs**, deterministica, cosi' lo stesso ingresso produce sempre lo stesso risultato.
- Sintesi chiptune senza aliasing con dinamica del volume e un limiter morbido.
- Trasposizione di tonalita' e profondita' di bit, frequenza di campionamento e tono degli impulsi regolabili.
- Uscita PCM a 8 bit come WAV, o qualsiasi formato che ffmpeg puo' scrivere.
- Un report sulla qualita' dopo ogni esecuzione, e tutto viene eseguito sulla tua macchina.

### Licenza

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
