## audio8bit - 将任意歌曲变成 8 位芯片音乐

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | **[中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md)** | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

一个命令行工具，可将任意歌曲变成 8 位的电子游戏风格音乐。它会找出旋律（来自人声或乐器），并用复古的“芯片音乐”音色重新演奏，就像一台老式游戏机一样。一切都在本地运行。

### 系统要求

- **Python 3.9 或更高版本**
- **ffmpeg** 位于你的 `PATH` 中（它附带 `ffmpeg` 和 `ffprobe`）。使用
  `sudo apt install ffmpeg`（Linux）或 `brew install ffmpeg`（macOS）安装。

### 安装

```bash
pip install audio8bit
```

或从 GitHub 安装：

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **首次运行较慢：** 它会下载一个小型 AI 模型（约 80 MB），可能需要
> 几分钟。这是正常现象；后续运行会更快。

### 用法

```bash
# Convert a song (auto-detects vocal or instrumental)
audio8bit -i song.mp3

# Just the main melody, no chords
audio8bit -i song.mp3 -V lead

# 多乐器乐队：脉冲主音 + 脉冲和声 + 三角波贝斯 + 噪声鼓
audio8bit -i song.mp3 -V band

# NES 风格：琶音和声的乐队，对齐节拍
audio8bit -i song.mp3 -V nes

# Take the tune from the singing or from the instruments
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Save as a different format
audio8bit -i song.mp3 -f ogg

# Play it 5 semitones higher
audio8bit -i song.mp3 --transpose 5

# Show help and version
audio8bit --help
audio8bit --version
```

### 命令行选项

- `-i, --input` - 输入音频文件，必填（ffmpeg 能读取的任意格式）
- `-o, --output` - 输出路径（默认：`output.<ext>`）
- `-f, --format` - 输出格式，例如 `ogg`、`wav`（默认：与输入相同）
- `-s, --source` - 旋律来源：`vocals`、`instrumental`、`auto`（默认：`auto`）
- `-m, --method` - 音符识别：`transcribe` 或 `pitch`（默认：`transcribe`）
- `-V, --voices` - `chords`（带和声）或 `lead`（单声部） 或 `band`（多乐器：脉冲主音 + 脉冲和声 + 三角波贝斯 + 噪声鼓） 或 `nes`（琶音、对齐节拍）（默认：`chords`）
- `--transpose` - 以半音为单位的调式移动（默认：`0`）
- `--bits` - 位深度，1-8，越低越粗糙（默认：`8`）
- `--rate` - 采样率（Hz），越低越复古（默认：`22050`）
- `--duty` - 脉冲波占空比，0-1（默认：`0.25`）
- `--key-snap` - band/nes：把跑调音符对齐到检测出的调性：`on`、`off`（默认：`on`）
- `--arrange` - band/nes：以和弦进行伴奏、根音贝斯和循环鼓点取代转录回放：`on`、`off`（默认：`on`）
- `--echo` - band/nes：旋律上的节拍同步回声：`on`、`off`（默认：`on`）
- `--dither` - band/nes：位量化前的 TPDF 抖动：`on`、`off`（默认：`on`）
- `--no-cache` - 不读取也不写入缓存的 Demucs 分轨
- `--cache-dir` - 缓存分轨的目录（默认：`~/.cache/audio8bit`，或 `$AUDIO8BIT_CACHE_DIR`）
- `--version` - 显示版本

退出码：`0` 成功，`1` 转换错误，`2` 参数错误。

### 功能特性

- 同时支持**人声**歌曲和**纯乐器**作品 - 自动选择旋律来源。
- **复音转录**（basic-pitch）保留和弦与贝斯，或将其简化为单一主旋律线。 `band` 模式将它们分配到不同的芯片声道（脉冲主音、脉冲和声、三角波贝斯）。 贝斯来自贝斯声轨，鼓来自鼓声轨。 `nes` 模式将和声琶音化并对齐节拍。
- 使用 **Demucs** 进行声源分离，结果是确定性的，因此相同的输入始终给出相同的结果。
- 无混叠的芯片音乐合成，带有响度动态和平滑的限幅器。
- 调式移调，以及可调的位深度、采样率和脉冲音色。
- 8 位 PCM 输出为 WAV，或 ffmpeg 能写入的任意格式。
- 每次运行后都会生成质量报告，且一切都在你自己的机器上运行。

### 许可证

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
