# audio8bit

Verwandelt einen Song in ein 8-Bit-Chiptune-Arrangement — die gesungene Stimme
**oder** das Instrumental samt seiner Harmonie — so, wie es eine Spielekonsole
aus den 80ern abspielen würde, direkt von der Kommandozeile aus.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | **[Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md)** | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Es behält die Melodie bei und arrangiert sie für Chip-Stimmen neu:

1. **Quellentrennung** — [Demucs](https://github.com/adefossez/demucs) (ein
   neuronales Modell zur Quellentrennung) zerlegt den Song in Stems, und zwar
   deterministisch, sodass dieselbe Eingabe stets dasselbe Ergebnis liefert. Die
   Melodie wird aus den gesungenen **vocals** oder, bei einem Instrumental, aus
   dem begleitenden **lead** entnommen (Schlagzeug und Bass entfernt);
   `--source auto` verwendet die Stimme, wenn der Song tatsächlich eine hat, und
   ansonsten das Instrumental.
2. **Notenerkennung** (`--method`, Standard `transcribe`) — ein polyphones
   Transkriptionsmodell ([basic-pitch](https://github.com/spotify/basic-pitch))
   wandelt den Stem in echte Noten um. `--voices chords` (Standard) spielt jede
   Note, sodass Harmonie und Bass erhalten bleiben; `--voices lead` folgt einer
   einzelnen Melodielinie durch die Akkorde (ein Viterbi-Pfad, nicht die naive
   oberste Linie, die zwischen Lead und Begleitung hin- und herspringt). Das hält
   bei Akkorden und Instrumentals zusammen, wo eine Bild-für-Bild-Tonhöhenerkennung
   einfach zwischen den Stimmen springt und zufällig klingt. `--method pitch`
   verwendet stattdessen librosas pYIN, eingerastet auf das Beat-Raster des Songs
   (monophon, leichter, kein TensorFlow).
3. **Musikalisierung** — ein optionales `--transpose` ändert die Tonart. `lead`
   wird oktavweise in eine Klingelton-Lage verschoben; `chords` behält die
   transkribierten Tonhöhen bei, damit die Harmonie intakt bleibt. Transkribierte
   Noten behalten ihr eigenes natürliches Timing, anstatt auf ein Raster
   eingerastet zu werden.
4. **Chip-Synthese** — jede Note ist eine bandbegrenzte Pulse-Stimme (die `lead`-
   und `pitch`-Pfade fügen Vibrato/Decay hinzu, und `pitch` ergänzt einen
   Dreiecksbass und ein tempo-synchronisiertes Echo); aliasfrei durch Konstruktion
   (nur Harmonische unterhalb von Nyquist werden summiert). `chords` skaliert jede
   Stimme anhand ihrer transkribierten Lautstärke für Dynamik und nivelliert den
   Mix mit einem sanften Limiter, sodass dichte Akkorde die einzelnen Noten nicht
   übertönen.
5. **8-Bit-Ausgabe + Qualitätsbericht** — quantisiert auf 8-Bit-PCM, geschrieben
   als WAV oder in das von dir gewählte Format umkodiert, dann bewertet:
   melodische „Matsch"-Heuristiken für eine einzelne Linie oder Prüfungen auf
   Audio-Ebene (Stille, Aliasing, Clipping) für Akkorde — sodass ein schlechtes
   Ergebnis objektiv markiert wird, statt es per Gehör zu entdecken.

> **Achtung:** die Standardmethode `transcribe` zieht basic-pitch (TensorFlow)
> nach sich und Demucs zieht PyTorch nach sich — beides große Installationen —
> und Demucs lädt sein Modell (~80 MB) beim ersten Lauf herunter. Trennung plus
> Transkription dauern pro Track ein paar Minuten auf der CPU. Genau das macht die
> Melodie überhaupt erst erkennbar. Alles läuft lokal.

## Anforderungen

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (liefert `ffmpeg` und `ffprobe`) in deinem `PATH`

## Installation

```bash
pip install audio8bit
```

Oder direkt aus einem Klon ausführen (installiere zuerst die Abhängigkeiten: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## Verwendung

```bash
audio8bit -i song.mp3                      # -> output.mp3, full chords (keeps the input format)
audio8bit -i song.mp3 -V lead              # a single melody line instead of chords
audio8bit -i track.mp3 -s instrumental     # follow the instrumental, not vocals
audio8bit -i song.mp3 -m pitch             # lighter pYIN method (no TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitones up
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Standard         | Beschreibung                                 |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (erforderlich) | Eingabe-Audio (jedes Format, das ffmpeg lesen kann) |
| `-o, --output`   | `output.<ext>`   | Ausgabepfad (überschreibt `-f`)              |
| `-f, --format`   | Format der Eingabe | Ausgabeformat/-erweiterung, z. B. `ogg`    |
| `-s, --source`   | `auto`           | Zu folgende Melodie: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Notenerkennung: `transcribe` (polyphon) oder `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Transkriptionsausgabe: `chords` (Harmonie) oder `lead` (eine Linie) |
| `--transpose`    | `0`              | Tonartverschiebung in Halbtönen (negativ erlaubt) |
| `--bits`         | `8`              | Bittiefe, auf die quantisiert wird (1–8)     |
| `--rate`         | `22050`          | Ausgabe-Abtastrate in Hz                     |
| `--duty`         | `0.25`           | Tastverhältnis der Pulswelle (0–1)           |

Exit-Codes: `0` Erfolg, `1` Konvertierungsfehler, `2` ungültige Argumente. Jeder
Lauf endet mit einem Qualitätsbericht; fehlgeschlagene Prüfungen geben eine
Warnung an stderr aus.

## License

MIT-Lizenz
