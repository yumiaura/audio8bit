# audio8bit

Transformez une chanson en arrangement chiptune 8-bit — la voix chantée **ou**
l'instrumental, avec son harmonie — comme le jouerait une console de jeu des
années 80, directement depuis la ligne de commande.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | **[Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md)** | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Il conserve l'air et le réarrange pour des voix de puce :

1. **Séparation des sources** — [Demucs](https://github.com/adefossez/demucs) (un
   modèle neuronal de séparation de sources) découpe la chanson en pistes,
   exécuté de façon déterministe afin que la même entrée donne toujours le même
   résultat. La mélodie est tirée des **voix** chantées ou, pour un instrumental,
   du **lead** d'accompagnement (batterie et basse retirées) ; `--source auto`
   utilise la voix lorsque la chanson en comporte réellement une, et
   l'instrumental sinon.
2. **Détection des notes** (`--method`, valeur par défaut `transcribe`) — un
   modèle de transcription polyphonique
   ([basic-pitch](https://github.com/spotify/basic-pitch)) convertit la piste en
   véritables notes. `--voices chords` (par défaut) joue chaque note, ce qui
   préserve l'harmonie et la basse ; `--voices lead` suit une seule ligne
   mélodique à travers les accords (un chemin de Viterbi, et non la naïve ligne
   supérieure qui saute entre le lead et l'accompagnement). Cela tient la route
   sur les accords et les instrumentaux, là où un suivi de hauteur image par
   image se contente de sauter entre les voix et sonne au hasard. `--method pitch`
   utilise plutôt le pYIN de librosa aligné sur la grille rythmique de la chanson
   (monophonique, plus léger, sans TensorFlow).
3. **Mise en musique** — un `--transpose` optionnel change la tonalité. Le `lead`
   est décalé d'une octave vers un registre de sonnerie ; les `chords`
   conservent les hauteurs transcrites pour que l'harmonie reste intacte. Les
   notes transcrites conservent leur propre timing naturel au lieu d'être
   alignées sur une grille.
4. **Synthèse de puce** — chaque note est une voix d'impulsion à bande limitée
   (les chemins `lead` et `pitch` ajoutent vibrato/déclin, et `pitch` ajoute une
   basse triangulaire et un écho synchronisé au tempo) ; sans repliement par
   construction (seules les harmoniques en dessous de Nyquist sont sommées). Les
   `chords` mettent à l'échelle chaque voix selon son volume transcrit pour la
   dynamique et nivellent le mixage avec un limiteur doux, afin que les accords
   denses n'enterrent pas les notes isolées.
5. **Sortie 8-bit + rapport de qualité** — quantifiée en PCM 8-bit, écrite en WAV
   ou réencodée dans le format de votre choix, puis évaluée : des heuristiques de
   « bouillie » mélodique pour une ligne unique, ou des contrôles au niveau audio
   (silence, repliement, écrêtage) pour les accords — ainsi un mauvais résultat
   est signalé objectivement plutôt que découvert à l'oreille.

> **À noter :** la méthode par défaut `transcribe` entraîne basic-pitch
> (TensorFlow) et Demucs entraîne PyTorch — deux installations volumineuses — et
> Demucs télécharge son modèle (~80 Mo) au premier lancement. La séparation plus
> la transcription prennent quelques minutes par piste sur CPU. C'est ce qui rend
> la mélodie réellement reconnaissable. Tout fonctionne localement.

## Prérequis

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (fournit `ffmpeg` et `ffprobe`) dans votre `PATH`

## Installation

```bash
pip install audio8bit
```

Ou exécutez directement depuis un clone (installez d'abord les dépendances : `pip install numpy demucs librosa basic-pitch`) :

```bash
python main.py -i song.mp3
```

## Utilisation

```bash
audio8bit -i song.mp3                      # -> output.mp3, full chords (keeps the input format)
audio8bit -i song.mp3 -V lead              # a single melody line instead of chords
audio8bit -i track.mp3 -s instrumental     # follow the instrumental, not vocals
audio8bit -i song.mp3 -m pitch             # lighter pYIN method (no TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitones up
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Audio d'entrée (tout format lisible par ffmpeg) |
| `-o, --output`   | `output.<ext>`   | Chemin de sortie (remplace `-f`)             |
| `-f, --format`   | input's format   | Format/extension de sortie, p. ex. `ogg`     |
| `-s, --source`   | `auto`           | Mélodie à suivre : `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Détection des notes : `transcribe` (polyphonique) ou `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Sortie de transcription : `chords` (harmonie) ou `lead` (une ligne) |
| `--transpose`    | `0`              | Décalage de tonalité en demi-tons (négatif autorisé) |
| `--bits`         | `8`              | Profondeur de bits cible pour la quantification (1–8) |
| `--rate`         | `22050`          | Fréquence d'échantillonnage de sortie en Hz  |
| `--duty`         | `0.25`           | Rapport cyclique de l'onde pulsée (0–1)      |

Codes de sortie : `0` succès, `1` erreur de conversion, `2` arguments incorrects.
Chaque exécution se termine par un rapport de qualité ; les vérifications échouées
affichent un avertissement sur stderr.

## License

Licence MIT
