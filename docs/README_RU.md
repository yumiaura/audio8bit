# audio8bit

Превратите песню в 8-битную чиптюн-аранжировку — спетую вокальную партию **или**
инструментал вместе с его гармонией — так, как её сыграла бы игровая консоль 80-х,
прямо из командной строки.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | **[Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md)** | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Программа сохраняет мелодию и переаранжирует её для чип-голосов:

1. **Разделение источников** — [Demucs](https://github.com/adefossez/demucs)
   (нейросетевая модель разделения источников) разбивает песню на дорожки,
   работая детерминированно, так что один и тот же вход всегда даёт один и тот же
   результат. Мелодия берётся из спетого **вокала** или, для инструментала, из
   ведущей **lead**-партии аккомпанемента (с удалёнными ударными и басом);
   `--source auto` использует вокал, когда он действительно есть в песне, и
   инструментал в противном случае.
2. **Поиск нот** (`--method`, по умолчанию `transcribe`) — модель полифонической
   транскрипции ([basic-pitch](https://github.com/spotify/basic-pitch))
   превращает дорожку в настоящие ноты. `--voices chords` (по умолчанию) играет
   каждую ноту, поэтому гармония и бас сохраняются; `--voices lead` следует за
   одной мелодической линией сквозь аккорды (путь Витерби, а не наивная верхняя
   линия, которая скачет между ведущей партией и аккомпанементом). Это держится
   на аккордах и инструменталах, где покадровое отслеживание высоты тона просто
   прыгает между голосами и звучит как случайный шум. `--method pitch` вместо
   этого использует pYIN из librosa, привязанный к ритмической сетке песни
   (монофонический, легче, без TensorFlow).
3. **Музыкализация** — опциональный `--transpose` меняет тональность. `lead`
   сдвигается по октавам в регистр рингтона; `chords` сохраняет
   транскрибированные высоты, чтобы гармония оставалась нетронутой.
   Транскрибированные ноты сохраняют свой естественный тайминг, а не
   привязываются к сетке.
4. **Чип-синтез** — каждая нота представляет собой полосно-ограниченный
   импульсный голос (пути `lead` и `pitch` добавляют вибрато/затухание, а `pitch`
   добавляет треугольный бас и синхронизированное с темпом эхо); без алиасинга по
   построению (суммируются только гармоники ниже частоты Найквиста). `chords`
   масштабирует каждый голос по его транскрибированной громкости для динамики и
   выравнивает микс плавным лимитером, чтобы плотные аккорды не заглушали
   отдельные ноты.
5. **8-битный вывод + отчёт о качестве** — квантуется в 8-битный PCM,
   записывается как WAV или перекодируется в выбранный вами формат, а затем
   оценивается: эвристики мелодической «каши» для одной линии или проверки на
   уровне звука (тишина, алиасинг, клиппинг) для аккордов — так что плохой
   результат отмечается объективно, а не обнаруживается на слух.

> **Внимание:** метод по умолчанию `transcribe` тянет за собой basic-pitch
> (TensorFlow), а Demucs тянет за собой PyTorch — обе установки большие — и
> Demucs при первом запуске скачивает свою модель (~80 МБ). Разделение плюс
> транскрипция занимают несколько минут на трек на CPU. Именно это делает
> мелодию действительно узнаваемой. Всё работает локально.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (поставляется с `ffmpeg` и `ffprobe`) в вашем `PATH`

## Install

```bash
pip install audio8bit
```

Или запускайте прямо из клона (сначала установите зависимости: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## Usage

```bash
audio8bit -i song.mp3                      # -> output.mp3, full chords (keeps the input format)
audio8bit -i song.mp3 -V lead              # a single melody line instead of chords
audio8bit -i track.mp3 -s instrumental     # follow the instrumental, not vocals
audio8bit -i song.mp3 -m pitch             # lighter pYIN method (no TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitones up
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Описание                                     |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Входной аудиофайл (любой формат, который читает ffmpeg) |
| `-o, --output`   | `output.<ext>`   | Путь вывода (переопределяет `-f`)            |
| `-f, --format`   | input's format   | Формат/расширение вывода, например `ogg`     |
| `-s, --source`   | `auto`           | За какой мелодией следовать: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Поиск нот: `transcribe` (полифонический) или `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Вывод transcribe: `chords` (гармония) или `lead` (одна линия) |
| `--transpose`    | `0`              | Сдвиг тональности в полутонах (можно отрицательный) |
| `--bits`         | `8`              | Битовая глубина для квантования (1–8)        |
| `--rate`         | `22050`          | Частота дискретизации вывода в Гц            |
| `--duty`         | `0.25`           | Скважность импульсной волны (0–1)            |

Коды выхода: `0` успех, `1` ошибка конвертации, `2` неверные аргументы. Каждый
запуск завершается отчётом о качестве; непройденные проверки выводят
предупреждение в stderr.

## License

MIT
