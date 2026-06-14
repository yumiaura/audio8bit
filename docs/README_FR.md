# audio8bit

Transformez une chanson en un arrangement chiptune 8 bits de sa mélodie chantée — à la manière dont une console de jeu des années 80 la jouerait — directement depuis la ligne de commande.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | **[Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md)** | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Il supprime les paroles, conserve l'air et le réarrange pour des voix de puce :

1. **Isolation vocale** — [Demucs](https://github.com/adefossez/demucs) (un modèle
   neuronal de séparation de sources) extrait la mélodie chantée toute seule.
2. **Suivi de hauteur** — le pYIN de librosa suit la fréquence fondamentale de la
   voix isolée au fil du temps.
3. **Extraction des notes** — le suivi de hauteur est découpé en notes discrètes avec
   hystérésis : le vibrato et les glissandos restent à l'intérieur d'une même note, les
   silences de phonation sont comblés, les erreurs d'octave sont repliées et le
   scintillement des ornements est absorbé.
4. **Musicalisation** — les attaques des notes s'alignent sur la propre grille rythmique
   de la chanson, la mélodie est déplacée dans un registre de sonnerie et transposée dans
   une tonalité différente (`--transpose`, par défaut +3 demi-tons).
5. **Synthèse chip** — un lead à onde pulsée à bande limitée avec vibrato et enveloppes
   de décroissance, une basse triangle une octave en dessous sur les temps et un écho
   synchronisé au tempo ; sans repliement par construction (seules les harmoniques en
   dessous de Nyquist sont sommées).
6. **Sortie 8 bits + rapport de qualité** — quantifiée en PCM 8 bits, écrite en WAV
   ou réencodée dans le format de votre choix, puis évaluée selon des heuristiques de
   « bouillie » (densité des notes, fragmentation, trilles, étendue, écrêtage) afin
   qu'un mauvais résultat soit signalé objectivement plutôt que découvert à l'oreille.

> **À noter :** Demucs entraîne PyTorch (une installation volumineuse) et télécharge son
> modèle (~80 Mo) au premier lancement, et la séparation prend quelques minutes par piste
> sur CPU. C'est ce qui rend la mélodie réellement reconnaissable. Tout fonctionne
> localement.

## Prérequis

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (fournit `ffmpeg` et `ffprobe`) dans votre `PATH`

## Installation

```bash
pip install audio8bit
```

Ou exécutez directement depuis un clone (installez d'abord les dépendances : `pip install numpy demucs librosa`) :

```bash
python main.py -i song.mp3
```

## Utilisation

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Audio d'entrée (tout format lisible par ffmpeg) |
| `-o, --output`   | `output.<ext>`   | Chemin de sortie (remplace `-f`)             |
| `-f, --format`   | input's format   | Format/extension de sortie, p. ex. `ogg`     |
| `--transpose`    | `3`              | Décalage de tonalité en demi-tons (négatif autorisé) |
| `--bits`         | `8`              | Profondeur de bits cible pour la quantification (1–8) |
| `--rate`         | `22050`          | Fréquence d'échantillonnage de sortie en Hz  |
| `--duty`         | `0.25`           | Rapport cyclique de l'onde pulsée (0–1)      |

Codes de sortie : `0` succès, `1` erreur de conversion, `2` arguments incorrects. Chaque
exécution se termine par un rapport de qualité ; les vérifications échouées affichent un
avertissement sur stderr.

## License

Licence MIT
