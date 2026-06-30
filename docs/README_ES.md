## audio8bit - convierte cualquier cancion en musica chiptune de 8 bits

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | **[Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md)** | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Una herramienta de linea de comandos que convierte cualquier cancion en musica de 8 bits, al estilo de los videojuegos. Encuentra la melodia (de la voz o de los instrumentos) y la vuelve a tocar con sonidos retro "chiptune", como una vieja consola de videojuegos. Todo se ejecuta localmente.

### Requisitos

- **Python 3.9 o mas reciente**
- **ffmpeg** en tu `PATH` (incluye `ffmpeg` y `ffprobe`). Instalalo con
  `sudo apt install ffmpeg` (Linux) o `brew install ffmpeg` (macOS).

### Instalacion

```bash
pip install audio8bit
```

O desde GitHub:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **La primera ejecucion es lenta:** descarga un pequeno modelo de IA (unos 80 MB) y puede tardar
> unos minutos. Es normal; las ejecuciones posteriores son mas rapidas.

### Uso

```bash
# Convierte una cancion (detecta automaticamente voz o instrumental)
audio8bit -i song.mp3

# Solo la melodia principal, sin acordes
audio8bit -i song.mp3 -V lead

# Toma la melodia del canto o de los instrumentos
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Guardar en un formato diferente
audio8bit -i song.mp3 -f ogg

# Reproducirla 5 semitonos mas alta
audio8bit -i song.mp3 --transpose 5

# Mostrar ayuda y version
audio8bit --help
audio8bit --version
```

### Opciones de linea de comandos

- `-i, --input` - archivo de audio de entrada, obligatorio (cualquier formato que ffmpeg pueda leer)
- `-o, --output` - ruta de salida (predeterminado: `output.<ext>`)
- `-f, --format` - formato de salida, p. ej. `ogg`, `wav` (predeterminado: igual que la entrada)
- `-s, --source` - fuente de la melodia: `vocals`, `instrumental`, `auto` (predeterminado: `auto`)
- `-m, --method` - busqueda de notas: `transcribe` o `pitch` (predeterminado: `transcribe`)
- `-V, --voices` - `chords` (con armonia) o `lead` (una sola linea) (predeterminado: `chords`)
- `--transpose` - cambio de tonalidad en semitonos (predeterminado: `0`)
- `--bits` - profundidad de bits, 1-8, mas bajo es mas crujiente (predeterminado: `8`)
- `--rate` - frecuencia de muestreo en Hz, mas baja es mas retro (predeterminado: `22050`)
- `--duty` - ciclo de trabajo de la onda de pulso, 0-1 (predeterminado: `0.25`)
- `--no-cache` - no leer ni escribir stems de Demucs en caché
- `--cache-dir` - directorio para los stems en caché (por defecto: `~/.cache/audio8bit`, o `$AUDIO8BIT_CACHE_DIR`)
- `--version` - mostrar la version

Codigos de salida: `0` exito, `1` error de conversion, `2` argumentos incorrectos.

### Caracteristicas

- Funciona con canciones **vocales** e **instrumentales** - elige la fuente de la melodia automaticamente.
- **Transcripcion polifonica** (basic-pitch) conserva los acordes y el bajo, o los reduce a una sola linea melodica.
- Separacion de fuentes con **Demucs**, determinista para que la misma entrada siempre de el mismo resultado.
- Sintesis chiptune sin aliasing con dinamica de sonoridad y un limitador suave.
- Transposicion de tonalidad y profundidad de bits, frecuencia de muestreo y tono de pulso ajustables.
- Salida PCM de 8 bits como WAV, o cualquier formato que ffmpeg pueda escribir.
- Un informe de calidad despues de cada ejecucion, y todo se ejecuta en tu propia maquina.

### Licencia

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
