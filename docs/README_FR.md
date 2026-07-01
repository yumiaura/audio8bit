## audio8bit - transformez n'importe quelle chanson en musique chiptune 8 bits

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | **[Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md)** | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Un outil en ligne de commande qui transforme n'importe quelle chanson en musique 8 bits, facon jeu video. Il trouve la melodie (a partir du chant ou des instruments) et la rejoue avec des sons retro "chiptune", comme une vieille console de jeu. Tout s'execute en local.

### Prerequis

- **Python 3.9 ou plus recent**
- **ffmpeg** dans votre `PATH` (il fournit `ffmpeg` et `ffprobe`). Installez-le avec
  `sudo apt install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS).

### Installation

```bash
pip install audio8bit
```

Ou depuis GitHub :

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **La premiere execution est lente :** elle telecharge un petit modele d'IA (environ 80 Mo) et peut prendre
> quelques minutes. C'est normal ; les executions suivantes sont plus rapides.

### Utilisation

```bash
# Convertir une chanson (detecte automatiquement le chant ou l'instrumental)
audio8bit -i song.mp3

# Seulement la melodie principale, sans accords
audio8bit -i song.mp3 -V lead

# Groupe multi-instruments : lead pulse + harmonie pulse + basse triangle + batterie de bruit
audio8bit -i song.mp3 -V band

# Style NES : le groupe avec harmonie en arpege, cale sur le rythme
audio8bit -i song.mp3 -V nes

# Prendre l'air a partir du chant ou des instruments
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Enregistrer dans un format different
audio8bit -i song.mp3 -f ogg

# Le jouer 5 demi-tons plus haut
audio8bit -i song.mp3 --transpose 5

# Afficher l'aide et la version
audio8bit --help
audio8bit --version
```

### Options en ligne de commande

- `-i, --input` - fichier audio d'entree, requis (tout format que ffmpeg peut lire)
- `-o, --output` - chemin de sortie (par defaut : `output.<ext>`)
- `-f, --format` - format de sortie, p. ex. `ogg`, `wav` (par defaut : identique a l'entree)
- `-s, --source` - source de la melodie : `vocals`, `instrumental`, `auto` (par defaut : `auto`)
- `-m, --method` - detection des notes : `transcribe` ou `pitch` (par defaut : `transcribe`)
- `-V, --voices` - `chords` (avec harmonie) ou `lead` (ligne unique) ou `band` (multi-instruments : lead pulse + harmonie pulse + basse triangle + batterie de bruit) ou `nes` (arpege, cale sur le rythme) (par defaut : `chords`)
- `--transpose` - decalage de tonalite en demi-tons (par defaut : `0`)
- `--bits` - profondeur de bits, 1-8, plus c'est bas plus c'est granuleux (par defaut : `8`)
- `--rate` - frequence d'echantillonnage en Hz, plus c'est bas plus c'est retro (par defaut : `22050`)
- `--duty` - rapport cyclique de l'onde pulsee, 0-1 (par defaut : `0.25`)
- `--no-cache` - ne pas lire ni écrire les stems Demucs en cache
- `--cache-dir` - répertoire pour les stems en cache (par défaut : `~/.cache/audio8bit`, ou `$AUDIO8BIT_CACHE_DIR`)
- `--version` - afficher la version

Codes de sortie : `0` succes, `1` erreur de conversion, `2` mauvais arguments.

### Fonctionnalites

- Fonctionne avec les chansons **vocales** et les **instrumentaux** - choisit automatiquement la source de la melodie.
- **Transcription polyphonique** (basic-pitch) qui conserve les accords et la basse, ou les reduit a une seule ligne melodique. Le mode `band` les repartit sur des canaux chip (lead pulse, harmonie pulse, basse triangle). La basse vient du stem de basse et la batterie du stem de batterie. Le mode `nes` arpege l'harmonie et la cale sur le rythme.
- Separation des sources avec **Demucs**, deterministe : la meme entree donne toujours le meme resultat.
- Synthese chiptune sans repliement, avec dynamique de volume et un limiteur doux.
- Transposition de tonalite et profondeur de bits, frequence d'echantillonnage et tonalite pulsee reglables.
- Sortie PCM 8 bits en WAV, ou tout format que ffmpeg peut ecrire.
- Un rapport de qualite apres chaque execution, et tout s'execute sur votre propre machine.

### Licence

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
