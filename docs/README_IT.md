# audio8bit

Trasforma una canzone in un arrangiamento chiptune a 8 bit — la voce cantata
**oppure** lo strumentale, con la sua armonia — nel modo in cui la
riprodurrebbe una console di gioco degli anni '80, direttamente dalla riga di
comando.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | **[Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md)** | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Mantiene la melodia e la riarrangia per le voci del chip:

1. **Separazione delle sorgenti** — [Demucs](https://github.com/adefossez/demucs)
   (un modello neurale di separazione delle sorgenti) divide la canzone in stem,
   eseguito in modo deterministico così che lo stesso input produca sempre lo
   stesso risultato. La melodia viene presa dalla **voce** cantata oppure, per
   uno strumentale, dal **lead** di accompagnamento (batteria e basso rimossi);
   `--source auto` usa la voce quando la canzone ne ha effettivamente una e lo
   strumentale in caso contrario.
2. **Individuazione delle note** (`--method`, predefinito `transcribe`) — un
   modello di trascrizione polifonica
   ([basic-pitch](https://github.com/spotify/basic-pitch)) trasforma lo stem in
   note reali. `--voices chords` (predefinito) suona ogni nota, così armonia e
   basso vengono mantenuti; `--voices lead` segue una singola linea melodica
   attraverso gli accordi (un percorso di Viterbi, non l'ingenua linea
   superiore che salta tra lead e accompagnamento). Questo regge sugli accordi e
   sugli strumentali, dove il tracciamento dell'intonazione fotogramma per
   fotogramma salta semplicemente tra le voci e suona casuale. `--method pitch`
   usa invece il pYIN di librosa agganciato alla griglia ritmica della canzone
   (monofonico, più leggero, senza TensorFlow).
3. **Musicalizzazione** — un `--transpose` opzionale cambia la tonalità. `lead`
   viene spostato di ottava in un registro da suoneria; `chords` mantiene le
   intonazioni trascritte così che l'armonia resti intatta. Le note trascritte
   mantengono il proprio timing naturale invece di essere agganciate a una
   griglia.
4. **Sintesi chip** — ogni nota è una voce a impulso a banda limitata (i
   percorsi `lead` e `pitch` aggiungono vibrato/decadimento, e `pitch` aggiunge
   un basso a onda triangolare e un eco sincronizzato al tempo); priva di alias
   per costruzione (vengono sommate solo le armoniche al di sotto di Nyquist).
   `chords` scala ogni voce in base alla sua intensità trascritta per ottenere
   dinamica e livella il mix con un limiter morbido, così che gli accordi densi
   non seppelliscano le singole note.
5. **Output a 8 bit + report di qualità** — quantizzato in PCM a 8 bit, scritto
   come WAV o ricodificato nel formato scelto, poi valutato: euristiche di
   "mush" melodica per una singola linea, oppure controlli a livello audio
   (silenzio, aliasing, clipping) per gli accordi — così che un risultato
   scadente venga segnalato oggettivamente invece di essere scoperto a orecchio.

> **Attenzione:** il metodo predefinito `transcribe` include basic-pitch
> (TensorFlow) e Demucs include PyTorch — entrambe installazioni corpose — e
> Demucs scarica il suo modello (~80 MB) alla prima esecuzione. La separazione
> più la trascrizione richiedono alcuni minuti per traccia su CPU. È questo che
> rende la melodia effettivamente riconoscibile. Tutto viene eseguito in locale.

## Requisiti

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (include `ffmpeg` e `ffprobe`) nel tuo `PATH`

## Installazione

```bash
pip install audio8bit
```

Oppure esegui direttamente da un clone (installa prima le dipendenze: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## Utilizzo

```bash
audio8bit -i song.mp3                      # -> output.mp3, full chords (keeps the input format)
audio8bit -i song.mp3 -V lead              # a single melody line instead of chords
audio8bit -i track.mp3 -s instrumental     # follow the instrumental, not vocals
audio8bit -i song.mp3 -m pitch             # lighter pYIN method (no TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitones up
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Descrizione                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (richiesto)    | Audio di input (qualsiasi formato leggibile da ffmpeg) |
| `-o, --output`   | `output.<ext>`   | Percorso di output (sovrascrive `-f`)        |
| `-f, --format`   | formato dell'input | Formato/estensione di output, es. `ogg`    |
| `-s, --source`   | `auto`           | Melodia da seguire: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Individuazione note: `transcribe` (polifonico) o `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Output di trascrizione: `chords` (armonia) o `lead` (una linea) |
| `--transpose`    | `0`              | Spostamento di tonalità in semitoni (sono ammessi valori negativi) |
| `--bits`         | `8`              | Profondità di bit a cui quantizzare (1–8)    |
| `--rate`         | `22050`          | Frequenza di campionamento di output in Hz   |
| `--duty`         | `0.25`           | Duty cycle dell'onda a impulsi (0–1)         |

Codici di uscita: `0` successo, `1` errore di conversione, `2` argomenti errati.
Ogni esecuzione termina con un report di qualità; i controlli falliti stampano un
avviso su stderr.

## Licenza

MIT
