# audio8bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
![Sound](https://img.shields.io/badge/sound-8--bit%20chiptune-ff69b4.svg)
![Runs offline](https://img.shields.io/badge/runs-100%25%20offline-brightgreen.svg)

Trasforma qualsiasi canzone in musica a 8 bit, in stile videogioco — direttamente
dal tuo terminale. audio8bit trova la melodia della canzone (e i suoi accordi) e
la riproduce con suoni "chiptune" retro, come una vecchia console per videogiochi.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | **[Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md)** | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## Cosa fa

- Dagli una canzone e ottieni in cambio una sua versione chiptune.
- Funziona sia che la canzone abbia il **canto** sia che sia **strumentale** —
  sceglie la melodia automaticamente.
- Tutto viene eseguito sul tuo computer; non viene caricato nulla online.

## Prima di iniziare

Ti servono due cose:

- **Python 3.9 o più recente**
- **ffmpeg** — uno strumento gratuito per leggere e scrivere audio. Installalo con
  `sudo apt install ffmpeg` (Linux) o `brew install ffmpeg` (macOS).

## Installazione

```bash
pip install audio8bit
```

> **La prima esecuzione è lenta:** scarica un piccolo modello di intelligenza
> artificiale (circa 80 MB) e può richiedere qualche minuto. È normale — le
> esecuzioni successive sono più veloci.

## Come usarlo

```bash
audio8bit -i song.mp3
```

Questo crea `output.mp3` nella cartella corrente. Tutto qui. Ogni esecuzione
stampa anche un breve report sulla qualità, così puoi vedere che il risultato è
venuto pulito.

Vuoi qualcosa di diverso? Ecco le modifiche più comuni:

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## Tutte le opzioni

| Option           | Default          | Cosa fa                                       |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | La canzone da convertire (mp3, wav, flac, …)  |
| `-o, --output`   | `output.<type>`  | Dove salvare il risultato                     |
| `-f, --format`   | same as input    | Salva in un tipo diverso, es. `ogg`, `wav`    |
| `-s, --source`   | `auto`           | Da dove prendere la melodia: `vocals`, `instrumental` o `auto` |
| `-m, --method`   | `transcribe`     | Come si trovano le note: `transcribe` (migliore) o `pitch` (più veloce e leggero) |
| `-V, --voices`   | `chords`         | `chords` (con armonia) o `lead` (una sola linea melodica) |
| `--transpose`    | `0`              | Cambia la tonalità, in semitoni (es. `5` su, `-5` giù) |
| `--bits`         | `8`              | Risoluzione del suono, 1–8 (più basso = più grezzo) |
| `--rate`         | `22050`          | Frequenza di campionamento in Hz (più bassa = più retro) |
| `--duty`         | `0.25`           | Colore tonale dell'onda a impulsi, 0–1        |

## Se qualcosa va storto

- **"ffmpeg not found"** — installa ffmpeg (vedi *Prima di iniziare*).
- **La prima esecuzione sembra bloccata** — sta scaricando il modello di
  intelligenza artificiale; concedigli qualche minuto. Succede solo una volta.
- **Non somiglia alla canzone** — prova `-s vocals` o `-s instrumental` per
  scegliere la parte giusta, oppure `-V lead` per avere solo la melodia.

## Come funziona (lettura facoltativa)

1. Divide la canzone in parti (voce, batteria, basso e il resto).
2. Rileva le note effettivamente suonate nella parte che hai scelto.
3. Riproduce quelle note con semplici suoni "chip" a 8 bit e salva il file.

## License

Licenza MIT
