# audio8bit

把任何一首歌变成 8 位、电子游戏风格的音乐——直接在你的终端里完成。
audio8bit 会找出歌曲的旋律（以及它的和弦），并用复古的
“chiptune”（芯片音乐）音色重新演奏出来，就像一台老式游戏机一样。

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | **[中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md)** | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## 它能做什么

- 给它一首歌，它会返回这首歌的 chiptune 版本。
- 无论歌曲是**有人声演唱**还是**纯器乐**都能处理——它会自动挑选出曲调。
- 一切都在你自己的电脑上运行；不会上传任何东西。

## 开始之前

你需要两样东西：

- **Python 3.9 或更新版本**
- **ffmpeg**——一个用于读取和写入音频的免费工具。安装方法：
  `sudo apt install ffmpeg`（Linux）或 `brew install ffmpeg`（macOS）。

## 安装

```bash
pip install audio8bit
```

> **第一次运行会比较慢：** 它会下载一个小型 AI 模型（约 80 MB），可能
> 需要几分钟。这是正常的——之后的运行会更快。

## 使用方法

```bash
audio8bit -i song.mp3
```

这会在当前文件夹里生成 `output.mp3`。就这么简单。每次运行还会
打印一份简短的质量报告，让你看到结果是否干净。

想要不一样的效果？下面是最常用的几种调整：

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## 所有选项

| Option           | Default          | 它的作用                                       |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | 要转换的歌曲（mp3、wav、flac……）                |
| `-o, --output`   | `output.<type>`  | 结果保存到哪里                                  |
| `-f, --format`   | same as input    | 保存为不同的格式，例如 `ogg`、`wav`             |
| `-s, --source`   | `auto`           | 从哪里提取曲调：`vocals`、`instrumental` 或 `auto` |
| `-m, --method`   | `transcribe`     | 如何找出音符：`transcribe`（最佳）或 `pitch`（更快、更轻量） |
| `-V, --voices`   | `chords`         | `chords`（带和声）或 `lead`（单一旋律线） |
| `--transpose`    | `0`              | 移调，以半音为单位（例如 `5` 升高，`-5` 降低） |
| `--bits`         | `8`              | 音频位深，1–8（越低越粗糙）                     |
| `--rate`         | `22050`          | 采样率，单位 Hz（越低越复古）                   |
| `--duty`         | `0.25`           | 脉冲波的音色，0–1                              |

## 如果出了问题

- **“ffmpeg not found”**——请安装 ffmpeg（见*开始之前*）。
- **第一次运行好像卡住了**——它正在下载 AI 模型；请给它几分钟。
  这只会发生一次。
- **听起来不像原曲**——试试 `-s vocals` 或 `-s instrumental` 来
  挑选正确的部分，或者用 `-V lead` 只保留旋律。

## 它的工作原理（选读）

1. 把歌曲拆分成若干部分（人声、鼓、贝斯，以及其余部分）。
2. 检测你所选部分中实际演奏的音符。
3. 用简单的 8 位“芯片”音色重新演奏这些音符，并保存文件。

## 许可证

本项目采用 PolyForm Noncommercial License 许可 — 详见 [LICENSE](https://github.com/yumiaura/audio8bit/blob/main/LICENSE) 文件。
