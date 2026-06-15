# audio8bit

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Sound](https://img.shields.io/badge/sound-8--bit%20chiptune-ff69b4.svg)
![Runs offline](https://img.shields.io/badge/runs-100%25%20offline-brightgreen.svg)

Convierte cualquier canción en música de 8 bits, al estilo de los videojuegos,
directamente desde tu terminal. audio8bit encuentra la melodía de la canción
(y sus acordes) y la vuelve a tocar con sonidos retro "chiptune", como los de
una vieja consola de videojuegos.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | **[Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md)** | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## Qué hace

- Dale una canción y recibirás una versión chiptune de ella.
- Funciona tanto si la canción tiene **voz** como si es **instrumental**: elige
  la melodía automáticamente.
- Todo se ejecuta en tu propia computadora; no se sube nada.

## Antes de empezar

Necesitas dos cosas:

- **Python 3.9 o más reciente**
- **ffmpeg**: una herramienta gratuita para leer y escribir audio. Instálala con
  `sudo apt install ffmpeg` (Linux) o `brew install ffmpeg` (macOS).

## Instalación

```bash
pip install audio8bit
```

> **La primera ejecución es lenta:** descarga un pequeño modelo de IA (unos
> 80 MB) y puede tardar unos minutos. Es normal: las siguientes ejecuciones son
> más rápidas.

## Cómo usarlo

```bash
audio8bit -i song.mp3
```

Esto crea `output.mp3` en la carpeta actual. Eso es todo. Cada ejecución también
imprime un breve informe de calidad para que puedas ver que el resultado salió
limpio.

¿Quieres algo diferente? Estos son los ajustes más comunes:

```bash
audio8bit -i song.mp3 -V lead          # solo la melodía principal, sin acordes
audio8bit -i song.mp3 -s vocals        # sigue la voz
audio8bit -i song.mp3 -s instrumental  # sigue los instrumentos
audio8bit -i song.mp3 --transpose 5    # tócala 5 semitonos más alto
audio8bit -i song.mp3 -f ogg           # guarda como .ogg en vez de .mp3
```

## Todas las opciones

| Option           | Default          | Qué hace                                       |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | La canción a convertir (mp3, wav, flac, …)     |
| `-o, --output`   | `output.<type>`  | Dónde guardar el resultado                      |
| `-f, --format`   | same as input    | Guardar como otro tipo, p. ej. `ogg`, `wav`    |
| `-s, --source`   | `auto`           | De dónde tomar la melodía: `vocals`, `instrumental` o `auto` |
| `-m, --method`   | `transcribe`     | Cómo se encuentran las notas: `transcribe` (mejor) o `pitch` (más rápido y ligero) |
| `-V, --voices`   | `chords`         | `chords` (con armonía) o `lead` (una sola línea melódica) |
| `--transpose`    | `0`              | Cambia la tonalidad, en semitonos (p. ej. `5` arriba, `-5` abajo) |
| `--bits`         | `8`              | Resolución del sonido, 1–8 (más bajo = más crujiente) |
| `--rate`         | `22050`          | Frecuencia de muestreo en Hz (más baja = más retro) |
| `--duty`         | `0.25`           | Color del tono de la onda de pulso, 0–1        |

## Si algo sale mal

- **"ffmpeg not found"**: instala ffmpeg (consulta *Antes de empezar*).
- **La primera ejecución parece atascada**: está descargando el modelo de IA;
  dale unos minutos. Solo ocurre una vez.
- **No suena como la canción**: prueba con `-s vocals` o `-s instrumental` para
  elegir la parte correcta, o `-V lead` para obtener solo la melodía.

## Cómo funciona (lectura opcional)

1. Divide la canción en partes (voz, batería, bajo y el resto).
2. Detecta las notas reales que se tocan en la parte que elegiste.
3. Vuelve a tocar esas notas con sencillos sonidos "chip" de 8 bits y guarda el
   archivo.

## Licencia

MIT
