# audio8bit

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Sound](https://img.shields.io/badge/sound-8--bit%20chiptune-ff69b4.svg)
![Runs offline](https://img.shields.io/badge/runs-100%25%20offline-brightgreen.svg)

Transformez n'importe quelle chanson en musique 8 bits, façon jeu vidéo —
directement depuis votre terminal. audio8bit trouve la mélodie de la chanson
(et ses accords) et les rejoue avec des sons rétro « chiptune », comme une
vieille console de jeu.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | **[Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md)** | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## Ce que ça fait

- Donnez-lui une chanson, récupérez une version chiptune de celle-ci.
- Fonctionne que la chanson contienne du **chant** ou qu'elle soit
  **instrumentale** — elle choisit l'air automatiquement.
- Tout s'exécute sur votre propre ordinateur ; rien n'est envoyé en ligne.

## Avant de commencer

Vous avez besoin de deux choses :

- **Python 3.9 ou plus récent**
- **ffmpeg** — un outil gratuit pour lire et écrire de l'audio. Installez-le avec
  `sudo apt install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS).

## Installation

```bash
pip install audio8bit
```

> **La première exécution est lente :** elle télécharge un petit modèle d'IA
> (environ 80 Mo) et peut prendre quelques minutes. C'est normal — les
> exécutions suivantes sont plus rapides.

## Utilisation

```bash
audio8bit -i song.mp3
```

Cela crée `output.mp3` dans le dossier courant. C'est tout. Chaque exécution
affiche aussi un court rapport de qualité pour que vous puissiez vérifier que
le résultat est bien propre.

Vous voulez quelque chose de différent ? Voici les réglages les plus courants :

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## Toutes les options

| Option           | Default          | Ce que ça fait                                |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | La chanson à convertir (mp3, wav, flac, …)    |
| `-o, --output`   | `output.<type>`  | Où enregistrer le résultat                    |
| `-f, --format`   | same as input    | Enregistrer dans un autre type, p. ex. `ogg`, `wav` |
| `-s, --source`   | `auto`           | Où prendre l'air : `vocals`, `instrumental` ou `auto` |
| `-m, --method`   | `transcribe`     | Comment les notes sont trouvées : `transcribe` (le meilleur) ou `pitch` (plus rapide, plus léger) |
| `-V, --voices`   | `chords`         | `chords` (avec harmonie) ou `lead` (une seule ligne mélodique) |
| `--transpose`    | `0`              | Décale la tonalité, en demi-tons (p. ex. `5` plus haut, `-5` plus bas) |
| `--bits`         | `8`              | Résolution du son, 1–8 (plus bas = plus granuleux) |
| `--rate`         | `22050`          | Fréquence d'échantillonnage en Hz (plus bas = plus rétro) |
| `--duty`         | `0.25`           | Couleur sonore de l'onde pulsée, 0–1          |

## En cas de problème

- **« ffmpeg not found »** — installez ffmpeg (voir *Avant de commencer*).
- **La première exécution semble bloquée** — elle télécharge le modèle d'IA ;
  laissez-lui quelques minutes. Cela n'arrive qu'une seule fois.
- **Ça ne ressemble pas à la chanson** — essayez `-s vocals` ou
  `-s instrumental` pour choisir la bonne partie, ou `-V lead` pour seulement
  la mélodie.

## Comment ça marche (lecture facultative)

1. Découpe la chanson en parties (voix, batterie, basse et le reste).
2. Détecte les vraies notes jouées dans la partie que vous avez choisie.
3. Rejoue ces notes avec de simples sons « chip » 8 bits et enregistre le fichier.

## License

Licence MIT
