# audio8bit

Trasforma una canzone in un arrangiamento chiptune a 8 bit della sua melodia
cantata — proprio come la suonerebbe una console per videogiochi degli anni 80 —
direttamente dalla riga di comando.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | **[Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md)** | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Rimuove le parole, mantiene la melodia e la riarrangia per voci chip:

1. **Isolamento della voce** — [Demucs](https://github.com/adefossez/demucs) (un
   modello neurale di separazione delle sorgenti) estrae la melodia cantata da
   sola.
2. **Tracciamento dell'intonazione** — il pYIN di librosa segue nel tempo la
   frequenza fondamentale della voce isolata.
3. **Estrazione delle note** — la traccia di intonazione viene suddivisa in note
   discrete con isteresi: vibrato e scoop restano all'interno di una sola nota,
   le interruzioni di sonorità vengono colmate, gli errori di ottava ripiegati e
   il tremolio degli ornamenti assorbito.
4. **Musicalizzazione** — gli attacchi delle note si allineano alla griglia
   ritmica della canzone, la melodia viene spostata in un registro da suoneria e
   trasposta in una tonalità diversa (`--transpose`, predefinito +3 semitoni).
5. **Sintesi chip** — un lead a impulsi a banda limitata con vibrato e inviluppi
   di decadimento, un basso a onda triangolare un'ottava più in basso sui battiti
   e un eco sincronizzato al tempo; privo di aliasing per costruzione (vengono
   sommate solo le armoniche al di sotto di Nyquist).
6. **Output a 8 bit + report di qualità** — quantizzato in PCM a 8 bit, scritto
   come WAV o ricodificato nel formato scelto, quindi valutato in base a
   euristiche di "mush" (densità delle note, frammentazione, trilli, estensione,
   clipping) così che un risultato scadente venga segnalato oggettivamente invece
   di essere scoperto a orecchio.

> **Attenzione:** Demucs include PyTorch (un'installazione corposa) e scarica il
> suo modello (~80 MB) alla prima esecuzione, e la separazione richiede alcuni
> minuti per traccia su CPU. È questo che rende la melodia effettivamente
> riconoscibile. Tutto viene eseguito in locale.

## Requisiti

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (include `ffmpeg` e `ffprobe`) nel tuo `PATH`

## Installazione

```bash
pip install audio8bit
```

Oppure esegui direttamente da un clone (installa prima le dipendenze: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## Utilizzo

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Descrizione                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (richiesto)    | Audio di input (qualsiasi formato leggibile da ffmpeg) |
| `-o, --output`   | `output.<ext>`   | Percorso di output (sovrascrive `-f`)        |
| `-f, --format`   | formato dell'input | Formato/estensione di output, es. `ogg`    |
| `--transpose`    | `3`              | Spostamento di tonalità in semitoni (sono ammessi valori negativi) |
| `--bits`         | `8`              | Profondità di bit a cui quantizzare (1–8)    |
| `--rate`         | `22050`          | Frequenza di campionamento di output in Hz   |
| `--duty`         | `0.25`           | Duty cycle dell'onda a impulsi (0–1)         |

Codici di uscita: `0` successo, `1` errore di conversione, `2` argomenti errati.
Ogni esecuzione termina con un report di qualità; i controlli falliti stampano un
avviso su stderr.

## License

MIT
