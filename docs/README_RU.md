## audio8bit - превратите любую песню в 8-битную чиптюн-музыку

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | **[Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md)** | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Инструмент командной строки, который превращает любую песню в 8-битную музыку в стиле видеоигр. Он находит мелодию (из вокала или из инструментов) и воспроизводит ее ретро-звуками "чиптюн", как старая игровая приставка. Все работает локально.

### Требования

- **Python 3.9 или новее**
- **ffmpeg** в вашем `PATH` (поставляется с `ffmpeg` и `ffprobe`). Установите его командой
  `sudo apt install ffmpeg` (Linux) или `brew install ffmpeg` (macOS).

### Установка

```bash
pip install audio8bit
```

Или из GitHub:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **Первый запуск медленный:** он скачивает небольшую модель ИИ (примерно 80 МБ),
> и это может занять несколько минут. Это нормально; последующие запуски быстрее.

### Использование

```bash
# Преобразовать песню (автоматически определяет вокал или инструментал)
audio8bit -i song.mp3

# Только основная мелодия, без аккордов
audio8bit -i song.mp3 -V lead

# Мультиинструментальный бэнд: pulse-лид + pulse-гармония + triangle-бас + noise-ударные
audio8bit -i song.mp3 -V band

# В стиле NES: бэнд с арпеджированной гармонией, в долю
audio8bit -i song.mp3 -V nes

# Взять мелодию из пения или из инструментов
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Сохранить в другом формате
audio8bit -i song.mp3 -f ogg

# Воспроизвести на 5 полутонов выше
audio8bit -i song.mp3 --transpose 5

# Показать справку и версию
audio8bit --help
audio8bit --version
```

### Параметры командной строки

- `-i, --input` - входной аудиофайл, обязательный (любой формат, который умеет читать ffmpeg)
- `-o, --output` - путь вывода (по умолчанию: `output.<ext>`)
- `-f, --format` - формат вывода, например `ogg`, `wav` (по умолчанию: тот же, что у входного файла)
- `-s, --source` - источник мелодии: `vocals`, `instrumental`, `auto` (по умолчанию: `auto`)
- `-m, --method` - поиск нот: `transcribe` или `pitch` (по умолчанию: `transcribe`)
- `-V, --voices` - `chords` (с гармонией) или `lead` (одна линия) или `band` (мультиинструмент: pulse-лид + pulse-гармония + triangle-бас + noise-ударные) или `nes` (арпеджио, в долю) (по умолчанию: `chords`)
- `--transpose` - сдвиг тональности в полутонах (по умолчанию: `0`)
- `--bits` - разрешение звука, 1-8, чем меньше, тем грубее (по умолчанию: `8`)
- `--rate` - частота дискретизации в Гц, чем меньше, тем более ретро (по умолчанию: `22050`)
- `--duty` - коэффициент заполнения прямоугольной волны, 0-1 (по умолчанию: `0.25`)
- `--key-snap` - band/nes: подтягивает внетональные ноты к найденной тональности: `on`, `off` (по умолчанию: `on`)
- `--arrange` - band/nes: аккомпанемент по аккордовой прогрессии, бас по корням и залупленные ударные вместо проигрывания транскрипции: `on`, `off` (по умолчанию: `on`)
- `--echo` - band/nes: эхо в темпе песни на мелодии: `on`, `off` (по умолчанию: `on`)
- `--dither` - band/nes: TPDF-дизер перед битовым квантованием: `on`, `off` (по умолчанию: `on`)
- `--no-cache` - не читать и не записывать кэш стемов Demucs
- `--cache-dir` - каталог для кэша стемов (по умолчанию: `~/.cache/audio8bit`, или `$AUDIO8BIT_CACHE_DIR`)
- `--version` - показать версию

Коды выхода: `0` успех, `1` ошибка преобразования, `2` неверные аргументы.

### Возможности

- Работает с **вокальными** песнями и **инструменталами** - источник мелодии выбирается автоматически.
- **Полифоническая транскрипция** (basic-pitch) сохраняет аккорды и бас или сводит их к одной ведущей линии. Режим `band` распределяет их по чип-каналам (pulse-лид, pulse-гармония, triangle-бас). Бас берётся из bass-стема, а ударные из drums-стема. Режим `nes` арпеджирует гармонию и ставит всё в долю.
- Разделение источников с помощью **Demucs**, детерминированное, поэтому один и тот же вход всегда даёт один и тот же результат.
- Синтез чиптюна без алиасинга с динамикой громкости и плавным лимитером.
- Транспонирование тональности и настраиваемые разрешение звука, частота дискретизации и тон импульса.
- 8-битный вывод PCM в виде WAV или в любом формате, который умеет записывать ffmpeg.
- Отчёт о качестве после каждого запуска, и всё работает на вашем собственном компьютере.

### Лицензия

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
