# audio8bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pypi/dm/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

Превратите любую песню в 8-битную музыку в стиле видеоигр - прямо из вашего
терминала. audio8bit находит мелодию песни (и её аккорды) и воспроизводит их
ретро-звуками «чиптюн», как старая игровая приставка.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | **[Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md)** | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## Что это делает

- Дайте ему песню - получите её чиптюн-версию.
- Работает как с песнями, где есть **пение**, так и с **инструментальными** -
  мелодия выбирается автоматически.
- Всё выполняется на вашем собственном компьютере; ничего никуда не загружается.

## Перед началом

Вам понадобятся две вещи:

- **Python 3.9 или новее**
- **ffmpeg** - бесплатный инструмент для чтения и записи аудио. Установите его
  командой `sudo apt install ffmpeg` (Linux) или `brew install ffmpeg` (macOS).

## Установка

```bash
pip install audio8bit
```

> **Первый запуск медленный:** он скачивает небольшую модель ИИ (примерно 80 МБ),
> и это может занять несколько минут. Это нормально - последующие запуски быстрее.

## Использование

```bash
audio8bit -i song.mp3
```

Эта команда создаёт `output.mp3` в текущей папке. Вот и всё. При каждом запуске
также выводится краткий отчёт о качестве, чтобы вы могли убедиться, что результат
получился чистым.

Хотите чего-то другого? Вот самые частые настройки:

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## Все параметры

| Option           | Default          | Что это делает                                |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | Песня для преобразования (mp3, wav, flac, ...)  |
| `-o, --output`   | `output.<type>`  | Куда сохранить результат                       |
| `-f, --format`   | same as input    | Сохранить в другом формате, например `ogg`, `wav` |
| `-s, --source`   | `auto`           | Откуда брать мелодию: `vocals`, `instrumental` или `auto` |
| `-m, --method`   | `transcribe`     | Как находятся ноты: `transcribe` (лучше всего) или `pitch` (быстрее, легче) |
| `-V, --voices`   | `chords`         | `chords` (с гармонией) или `lead` (одна мелодическая линия) |
| `--transpose`    | `0`              | Сдвиг тональности в полутонах (например, `5` вверх, `-5` вниз) |
| `--bits`         | `8`              | Разрешение звука, 1-8 (меньше = грубее)        |
| `--rate`         | `22050`          | Частота дискретизации в Гц (меньше = более ретро) |
| `--duty`         | `0.25`           | Тембр прямоугольной волны, 0-1                 |

## Если что-то пошло не так

- **«ffmpeg not found»** - установите ffmpeg (см. *Перед началом*).
- **Первый запуск как будто завис** - это скачивается модель ИИ; дайте ему
  несколько минут. Так бывает только один раз.
- **Звучит не похоже на песню** - попробуйте `-s vocals` или `-s instrumental`,
  чтобы выбрать нужную часть, либо `-V lead` для одной только мелодии.

## Как это работает (необязательно к прочтению)

1. Разделяет песню на части (вокал, ударные, бас и всё остальное).
2. Определяет, какие ноты реально звучат в выбранной вами части.
3. Воспроизводит эти ноты простыми 8-битными «чип»-звуками и сохраняет файл.

## Лицензия

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
