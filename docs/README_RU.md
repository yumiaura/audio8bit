# audio8bit

Превратите песню в 8-битную чиптюн-аранжировку её спетой мелодии — так, как
её сыграла бы игровая консоль 80-х, — прямо из командной строки.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | **[Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md)** | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Программа убирает слова, сохраняет мотив и переаранжирует его для чип-голосов:

1. **Изоляция вокала** — [Demucs](https://github.com/adefossez/demucs) (нейросетевая
   модель разделения источников) выделяет спетую мелодию отдельно.
2. **Отслеживание высоты тона** — pYIN из librosa отслеживает основную частоту
   изолированного голоса во времени.
3. **Извлечение нот** — дорожка высоты тона разбивается на дискретные ноты с
   гистерезисом: вибрато и подъезды остаются внутри одной ноты, пробелы в
   фонации сшиваются, октавные ошибки сворачиваются обратно, мерцание
   орнаментов поглощается.
4. **Музыкализация** — атаки нот привязываются к собственной ритмической сетке
   песни, мелодия сдвигается в регистр рингтона и транспонируется в другую
   тональность (`--transpose`, по умолчанию +3 полутона).
5. **Чип-синтез** — полосно-ограниченный импульсный лид с вибрато и затухающими
   огибающими, треугольный бас на октаву ниже на долях и синхронизированное с
   темпом эхо; без алиасинга по построению (суммируются только гармоники ниже
   частоты Найквиста).
6. **8-битный вывод + отчёт о качестве** — квантование до 8-битного PCM, запись
   в WAV или перекодирование в выбранный вами формат, затем оценка по
   эвристикам «каши» (плотность нот, фрагментация, трели, диапазон, клиппинг),
   так что плохой результат отмечается объективно, а не обнаруживается на слух.

> **Внимание:** Demucs тянет за собой PyTorch (большая установка) и при первом
> запуске скачивает свою модель (~80 МБ), а разделение занимает несколько минут
> на трек на CPU. Именно это делает мелодию действительно узнаваемой. Всё
> работает локально.

## Требования

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (поставляется с `ffmpeg` и `ffprobe`) в вашем `PATH`

## Установка

```bash
pip install audio8bit
```

Или запускайте прямо из клона (сначала установите зависимости: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## Использование

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Описание                                     |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | Входной аудиофайл (любой формат, который читает ffmpeg) |
| `-o, --output`   | `output.<ext>`   | Путь вывода (переопределяет `-f`)            |
| `-f, --format`   | input's format   | Формат/расширение вывода, например `ogg`     |
| `--transpose`    | `3`              | Сдвиг тональности в полутонах (можно отрицательный) |
| `--bits`         | `8`              | Битовая глубина для квантования (1–8)        |
| `--rate`         | `22050`          | Частота дискретизации вывода в Гц            |
| `--duty`         | `0.25`           | Скважность импульсной волны (0–1)            |

Коды выхода: `0` успех, `1` ошибка конвертации, `2` неверные аргументы. Каждый
запуск завершается отчётом о качестве; непройденные проверки выводят
предупреждение в stderr.

## License

MIT
