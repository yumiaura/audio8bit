# audio8bit

Convierte una canción en un arreglo chiptune de 8 bits de su melodía cantada — tal como lo
reproduciría una consola de videojuegos de los años 80 — directamente desde la línea de comandos.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | **[Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md)** | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Quita las palabras, conserva la melodía y la reorganiza para voces de chip:

1. **Aislamiento vocal** — [Demucs](https://github.com/adefossez/demucs) (un modelo neuronal
   de separación de fuentes) extrae la melodía cantada por sí sola.
2. **Seguimiento de tono** — el pYIN de librosa sigue la frecuencia fundamental de la
   voz aislada a lo largo del tiempo.
3. **Extracción de notas** — la pista de tono se divide en notas discretas con
   histéresis: el vibrato y los glissandos permanecen dentro de una sola nota, los huecos de
   sonoridad se enlazan, los errores de octava se repliegan y el parpadeo de los ornamentos se absorbe.
4. **Musicalización** — los inicios de las notas se ajustan a la propia cuadrícula rítmica de la canción, la
   melodía se desplaza a un registro de tono de llamada y se transpone a una tonalidad
   diferente (`--transpose`, valor predeterminado +3 semitonos).
5. **Síntesis de chip** — una voz principal de pulso con ancho de banda limitado, con envolventes de vibrato y
   decaimiento, un bajo de onda triangular una octava por debajo en los tiempos y un
   eco sincronizado con el tempo; libre de aliasing por construcción (solo se suman los armónicos por debajo de Nyquist).
6. **Salida de 8 bits + informe de calidad** — cuantizada a PCM de 8 bits, escrita como WAV
   o recodificada al formato que elijas, y luego evaluada según heurísticas de "papilla"
   (densidad de notas, fragmentación, trinos, rango, recorte) para que un mal resultado quede
   señalado objetivamente en lugar de descubrirse de oído.

> **Atención:** Demucs arrastra PyTorch (una instalación grande) y descarga su
> modelo (~80 MB) en la primera ejecución, y la separación tarda unos minutos por pista en
> CPU. Esto es lo que hace que la melodía sea realmente reconocible. Todo se ejecuta
> localmente.

## Requisitos

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (incluye `ffmpeg` y `ffprobe`) en tu `PATH`

## Instalación

```bash
pip install audio8bit
```

O ejecútalo directamente desde un clon (instala primero las dependencias: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## Uso

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Descripción                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (requerido)    | Audio de entrada (cualquier formato que ffmpeg pueda leer) |
| `-o, --output`   | `output.<ext>`   | Ruta de salida (anula `-f`)                  |
| `-f, --format`   | formato de la entrada | Formato/extensión de salida, p. ej. `ogg` |
| `--transpose`    | `3`              | Cambio de tonalidad en semitonos (se permiten negativos) |
| `--bits`         | `8`              | Profundidad de bits a la que cuantizar (1–8) |
| `--rate`         | `22050`          | Frecuencia de muestreo de salida en Hz       |
| `--duty`         | `0.25`           | Ciclo de trabajo de la onda de pulso (0–1)   |

Códigos de salida: `0` éxito, `1` error de conversión, `2` argumentos incorrectos. Cada ejecución
termina con un informe de calidad; las comprobaciones fallidas imprimen una advertencia en stderr.

## License

Licencia MIT
