# audio8bit

Convierte una canción en un arreglo chiptune de 8 bits — la voz cantada **o**
la parte instrumental, con su armonía — tal como lo reproduciría una consola de
videojuegos de los años 80, directamente desde la línea de comandos.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | **[Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md)** | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Conserva la melodía y la rearregla para voces de chip:

1. **Separación de fuentes** — [Demucs](https://github.com/adefossez/demucs) (un
   modelo neuronal de separación de fuentes) divide la canción en pistas, y se
   ejecuta de forma determinista para que la misma entrada produzca siempre el
   mismo resultado. La melodía se toma de la **voz** cantada o, para una pieza
   instrumental, de la **melodía principal** de acompañamiento (con la batería y
   el bajo eliminados); `--source auto` usa la voz cuando la canción realmente
   tiene una y la parte instrumental en caso contrario.
2. **Búsqueda de notas** (`--method`, por defecto `transcribe`) — un modelo de
   transcripción polifónica ([basic-pitch](https://github.com/spotify/basic-pitch))
   convierte la pista en notas reales. `--voices chords` (por defecto) reproduce
   cada nota, de modo que se conservan la armonía y el bajo; `--voices lead` sigue
   una única línea melódica a través de los acordes (un camino de Viterbi, no la
   ingenua línea superior que salta entre la melodía principal y el
   acompañamiento). Esto se mantiene coherente en acordes y piezas
   instrumentales, donde el seguimiento de tono cuadro por cuadro simplemente
   salta entre voces y suena aleatorio. `--method pitch` usa en su lugar el pYIN
   de librosa ajustado a la cuadrícula rítmica de la canción (monofónico, más
   ligero, sin TensorFlow).
3. **Musicalización** — una opción `--transpose` opcional cambia la tonalidad.
   `lead` se desplaza de octava a un registro de tono de llamada; `chords`
   conserva los tonos transcritos para que la armonía permanezca intacta. Las
   notas transcritas mantienen su propia temporización natural en lugar de
   ajustarse a una cuadrícula.
4. **Síntesis de chip** — cada nota es una voz de pulso con ancho de banda
   limitado (los caminos `lead` y `pitch` añaden vibrato/decaimiento, y `pitch`
   añade un bajo de onda triangular y un eco sincronizado con el tempo); libre de
   aliasing por construcción (solo se suman los armónicos por debajo de Nyquist).
   `chords` escala cada voz según su sonoridad transcrita para dar dinámica y
   nivela la mezcla con un limitador suave, de modo que los acordes densos no
   entierren las notas individuales.
5. **Salida de 8 bits + informe de calidad** — cuantizada a PCM de 8 bits,
   escrita como WAV o recodificada al formato que elijas, y luego evaluada:
   heurísticas de "papilla" melódica para una sola línea, o comprobaciones a
   nivel de audio (silencio, aliasing, recorte) para los acordes — de modo que un
   mal resultado quede señalado objetivamente en lugar de descubrirse de oído.

> **Atención:** el método `transcribe` por defecto arrastra basic-pitch
> (TensorFlow) y Demucs arrastra PyTorch — ambas son instalaciones grandes — y
> Demucs descarga su modelo (~80 MB) en la primera ejecución. La separación más
> la transcripción tardan unos minutos por pista en CPU. Esto es lo que hace que
> la melodía sea realmente reconocible. Todo se ejecuta localmente.

## Requisitos

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (incluye `ffmpeg` y `ffprobe`) en tu `PATH`

## Instalación

```bash
pip install audio8bit
```

O ejecútalo directamente desde un clon (instala primero las dependencias: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## Uso

```bash
audio8bit -i song.mp3                      # -> output.mp3, acordes completos (conserva el formato de entrada)
audio8bit -i song.mp3 -V lead              # una única línea melódica en lugar de acordes
audio8bit -i track.mp3 -s instrumental     # sigue la parte instrumental, no la voz
audio8bit -i song.mp3 -m pitch             # método pYIN más ligero (sin TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitonos hacia arriba
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Descripción                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (requerido)    | Audio de entrada (cualquier formato que ffmpeg pueda leer) |
| `-o, --output`   | `output.<ext>`   | Ruta de salida (anula `-f`)                  |
| `-f, --format`   | formato de la entrada | Formato/extensión de salida, p. ej. `ogg` |
| `-s, --source`   | `auto`           | Melodía a seguir: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Búsqueda de notas: `transcribe` (polifónica) o `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Salida de transcripción: `chords` (armonía) o `lead` (una línea) |
| `--transpose`    | `0`              | Cambio de tonalidad en semitonos (se permiten negativos) |
| `--bits`         | `8`              | Profundidad de bits a la que cuantizar (1–8) |
| `--rate`         | `22050`          | Frecuencia de muestreo de salida en Hz       |
| `--duty`         | `0.25`           | Ciclo de trabajo de la onda de pulso (0–1)   |

Códigos de salida: `0` éxito, `1` error de conversión, `2` argumentos
incorrectos. Cada ejecución termina con un informe de calidad; las
comprobaciones fallidas imprimen una advertencia en stderr.

## Licencia

MIT
