# audio8bit

将一首歌曲转换为其演唱旋律的 8-bit 芯片音乐编曲——就像 80 年代游戏主机演奏的那样——直接从命令行完成。

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | **[中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md)** | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

它去除歌词、保留曲调，并为芯片音色重新编排：

1. **人声分离** —— [Demucs](https://github.com/adefossez/demucs)（一种神经网络音源分离模型）单独提取出演唱的旋律。
2. **音高跟踪** —— librosa 的 pYIN 随时间跟踪被分离出的人声的基频。
3. **音符提取** —— 音高轨迹通过滞后处理被切分为离散的音符：颤音和滑音保留在同一个音符内，发声间隙被连接起来，八度错误被折回，装饰音的闪烁被吸收。
4. **音乐化** —— 音符的起始点对齐到歌曲自身的节拍网格，旋律被移动到铃声音域，并被移调到另一个调性（`--transpose`，默认 +3 个半音）。
5. **芯片合成** —— 一条带限的脉冲主音，带有颤音和衰减包络，节拍上有低八度的三角波贝斯，以及与速度同步的回声；从构造上就不会产生混叠（只对低于 Nyquist 的谐波求和）。
6. **8-bit 输出 + 质量报告** —— 量化为 8-bit PCM，写为 WAV 或重新编码为你选择的格式，然后依据“糊成一团”的启发式规则进行评分（音符密度、碎片化程度、颤音、音域、削波），这样糟糕的结果会被客观地标记出来，而不是靠耳朵去发现。

> **请注意：** Demucs 会引入 PyTorch（一个庞大的安装包），并在首次运行时下载它的模型（约 80 MB），在 CPU 上每首曲子的分离需要几分钟。这正是让旋律真正可辨认的关键所在。所有处理都在本地运行。

## 系统要求

- Python 3.9+
- 你的 `PATH` 上的 [ffmpeg](https://ffmpeg.org/)（自带 `ffmpeg` 和 `ffprobe`）

## 安装

```bash
pip install audio8bit
```

或者直接从克隆的仓库运行（先安装依赖：`pip install numpy demucs librosa`）：

```bash
python main.py -i song.mp3
```

## 用法

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | 描述                                          |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | 输入音频（ffmpeg 能读取的任何格式）              |
| `-o, --output`   | `output.<ext>`   | 输出路径（覆盖 `-f`）                          |
| `-f, --format`   | input's format   | 输出格式/扩展名，例如 `ogg`                     |
| `--transpose`    | `3`              | 以半音为单位的调性移动（允许负值）              |
| `--bits`         | `8`              | 量化到的位深度（1–8）                          |
| `--rate`         | `22050`          | 以 Hz 为单位的输出采样率                       |
| `--duty`         | `0.25`           | 脉冲波占空比（0–1）                            |

退出码：`0` 成功，`1` 转换错误，`2` 参数错误。每次运行都会以一份质量报告结束；未通过的检查会向 stderr 打印警告。

## License

MIT 许可证
