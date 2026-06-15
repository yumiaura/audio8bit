# audio8bit

把一首歌变成 8 位芯片音乐编曲——演唱的人声**或**带有和声的伴奏——以 80 年代游戏主机播放的方式呈现，全程在命令行中完成。

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | **[中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md)** | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

它保留曲调，并为芯片音色重新编排：

1. **音源分离** —— [Demucs](https://github.com/adefossez/demucs)（一种神经网络音源分离模型）将歌曲拆分为各个音轨，以确定性方式运行，因此相同的输入始终给出相同的结果。旋律取自演唱的**人声**，或者对于纯器乐曲目，取自伴奏的**主奏**（去掉鼓和贝斯）；`--source auto` 在歌曲确实有人声时使用人声，否则使用器乐。
2. **音符识别**（`--method`，默认 `transcribe`）—— 一个复音转录模型（[basic-pitch](https://github.com/spotify/basic-pitch)）将音轨转换成真实的音符。`--voices chords`（默认）会演奏每一个音符，因此和声与贝斯都得以保留；`--voices lead` 则在和弦之间跟随单一的旋律线（采用 Viterbi 路径，而不是那种在主奏与伴奏之间跳来跳去的朴素顶音线）。这种方式在和弦与器乐曲目上能保持连贯，而逐帧的音高追踪只会在各声部之间乱跳，听起来杂乱无章。`--method pitch` 则改用 librosa 的 pYIN，并对齐到歌曲的节拍网格（单音、更轻量、不需要 TensorFlow）。
3. **音乐化** —— 可选的 `--transpose` 可改变调性。`lead` 会做八度移位进入铃声音域；`chords` 保留转录得到的音高，使和声保持完整。转录出的音符保留其自身的自然时值，而不是被对齐到网格上。
4. **芯片合成** —— 每个音符都是一个带限脉冲音色（`lead` 与 `pitch` 路径会加入颤音/衰减，`pitch` 还会加入三角波贝斯以及与速度同步的回声）；从构造上就不会产生混叠（只对低于 Nyquist 的谐波求和）。`chords` 会按照每个音色转录得到的响度进行缩放以体现强弱变化，并用平滑的限幅器对整体混音做电平控制，这样密集的和弦就不会盖住单个音符。
5. **8 位输出 + 质量报告** —— 量化为 8 位 PCM，写为 WAV 或重新编码为你选择的格式，然后进行评分：对单一旋律线采用旋律“糊成一团”的启发式判断，对和弦则采用音频层面的检查（静音、混叠、削波）——这样糟糕的结果会被客观地标记出来，而不是靠耳朵去发现。

> **请注意：** 默认的 `transcribe` 方法会引入 basic-pitch（TensorFlow），而 Demucs 会引入 PyTorch——两者都是庞大的安装包——并且 Demucs 会在首次运行时下载它的模型（约 80 MB）。在 CPU 上，分离加转录每首曲子需要几分钟。这正是让旋律真正可辨认的关键所在。所有处理都在本地运行。

## Requirements

- Python 3.9+
- 你的 `PATH` 上的 [ffmpeg](https://ffmpeg.org/)（自带 `ffmpeg` 和 `ffprobe`）

## Install

```bash
pip install audio8bit
```

或者直接从克隆的仓库运行（先安装依赖：`pip install numpy demucs librosa basic-pitch`）：

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

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | 输入音频（ffmpeg 能读取的任何格式）              |
| `-o, --output`   | `output.<ext>`   | 输出路径（覆盖 `-f`）                           |
| `-f, --format`   | input's format   | 输出格式/扩展名，例如 `ogg`                     |
| `-s, --source`   | `auto`           | 要跟随的旋律：`vocals`、`instrumental`、`auto` |
| `-m, --method`   | `transcribe`     | 音符识别：`transcribe`（复音）或 `pitch`（pYIN） |
| `-V, --voices`   | `chords`         | 转录输出：`chords`（和声）或 `lead`（单一旋律线） |
| `--transpose`    | `0`              | 以半音为单位的调性移动（允许负值）              |
| `--bits`         | `8`              | 量化到的位深度（1–8）                          |
| `--rate`         | `22050`          | 以 Hz 为单位的输出采样率                       |
| `--duty`         | `0.25`           | 脉冲波占空比（0–1）                            |

退出码：`0` 成功，`1` 转换错误，`2` 参数错误。每次运行都会以一份质量报告结束；未通过的检查会向 stderr 打印警告。

## License

MIT 许可证
