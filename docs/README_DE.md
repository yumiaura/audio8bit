# audio8bit

Verwandle einen Song in ein 8-Bit-Chiptune-Arrangement seiner gesungenen Melodie — so, wie es eine Spielkonsole aus den 80ern abspielen würde — direkt von der Kommandozeile aus.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | **[Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md)** | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Es entfernt die Worte, behält die Melodie bei und arrangiert sie für Chip-Stimmen neu:

1. **Gesangsisolierung** — [Demucs](https://github.com/adefossez/demucs) (ein neuronales
   Modell zur Quellentrennung) extrahiert die gesungene Melodie für sich allein.
2. **Tonhöhenverfolgung** — librosas pYIN folgt der Grundfrequenz der
   isolierten Stimme über die Zeit.
3. **Notenextraktion** — die Tonhöhenspur wird mit Hysterese in einzelne Noten
   aufgeteilt: Vibrato und Glissandi bleiben innerhalb einer Note, Lücken in der
   Stimmgebung werden überbrückt, Oktavfehler zurückgefaltet und das Flackern von
   Verzierungen aufgefangen.
4. **Musikalisierung** — Noteneinsätze rasten am eigenen Beat-Raster des Songs ein,
   die Melodie wird in eine Klingelton-Lage verschoben und in eine andere
   Tonart transponiert (`--transpose`, Standard +3 Halbtöne).
5. **Chip-Synthese** — eine bandbegrenzte Pulse-Lead-Stimme mit Vibrato und
   Decay-Hüllkurven, ein Dreiecksbass eine Oktave tiefer auf den Beats und ein
   tempo-synchronisiertes Echo; konstruktionsbedingt aliasfrei (nur Harmonische
   unterhalb von Nyquist werden summiert).
6. **8-Bit-Ausgabe + Qualitätsbericht** — quantisiert auf 8-Bit-PCM, geschrieben
   als WAV oder in das von dir gewählte Format umkodiert, dann anhand von
   „Matsch"-Heuristiken bewertet (Notendichte, Fragmentierung, Triller,
   Tonumfang, Clipping), sodass ein schlechtes Ergebnis objektiv markiert wird,
   statt es per Gehör zu entdecken.

> **Achtung:** Demucs zieht PyTorch nach sich (eine große Installation) und lädt
> beim ersten Lauf sein Modell herunter (~80 MB), und die Trennung dauert pro
> Track ein paar Minuten auf der CPU. Genau das macht die Melodie überhaupt
> erst erkennbar. Alles läuft lokal.

## Anforderungen

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (liefert `ffmpeg` und `ffprobe`) in deinem `PATH`

## Installation

```bash
pip install audio8bit
```

Oder direkt aus einem Klon ausführen (installiere zuerst die Abhängigkeiten: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## Verwendung

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Standard         | Beschreibung                                 |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (erforderlich) | Eingabe-Audio (jedes Format, das ffmpeg lesen kann) |
| `-o, --output`   | `output.<ext>`   | Ausgabepfad (überschreibt `-f`)              |
| `-f, --format`   | Format der Eingabe | Ausgabeformat/-erweiterung, z. B. `ogg`    |
| `--transpose`    | `3`              | Tonartverschiebung in Halbtönen (negativ erlaubt) |
| `--bits`         | `8`              | Bittiefe, auf die quantisiert wird (1–8)     |
| `--rate`         | `22050`          | Ausgabe-Abtastrate in Hz                     |
| `--duty`         | `0.25`           | Tastverhältnis der Pulswelle (0–1)           |

Exit-Codes: `0` Erfolg, `1` Konvertierungsfehler, `2` ungültige Argumente. Jeder
Lauf endet mit einem Qualitätsbericht; fehlgeschlagene Prüfungen geben eine
Warnung an stderr aus.

## License

MIT
