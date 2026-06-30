## audio8bit - あらゆる曲を8ビットのチップチューン音楽に変換

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | **[日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md)** | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

あらゆる曲を8ビットのテレビゲーム風音楽に変換するコマンドラインツールです。(ボーカルや楽器から)メロディを見つけ出し、昔のゲーム機のようなレトロな「チップチューン」サウンドで再生します。すべてローカルで動作します。

### 動作要件

- **Python 3.9 以上**
- `PATH` 上に **ffmpeg** があること(`ffmpeg` と `ffprobe` が同梱されています)。
  `sudo apt install ffmpeg`(Linux)または `brew install ffmpeg`(macOS)でインストールしてください。

### インストール

```bash
pip install audio8bit
```

または GitHub から:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **初回の実行は遅いです:** 小さなAIモデル(約80 MB)をダウンロードするため、
> 数分かかることがあります。これは正常な動作で、以降の実行は速くなります。

### 使い方

```bash
# 曲を変換する(ボーカルか楽器かを自動検出)
audio8bit -i song.mp3

# メインメロディだけ、コードなし
audio8bit -i song.mp3 -V lead

# 歌から、または楽器からメロディを取り出す
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# 別の形式で保存する
audio8bit -i song.mp3 -f ogg

# 5半音高く演奏する
audio8bit -i song.mp3 --transpose 5

# ヘルプとバージョンを表示する
audio8bit --help
audio8bit --version
```

### コマンドラインオプション

- `-i, --input` - 入力オーディオファイル、必須(ffmpeg が読み込めるあらゆる形式)
- `-o, --output` - 出力先パス(デフォルト: `output.<ext>`)
- `-f, --format` - 出力形式、例: `ogg`, `wav`(デフォルト: 入力と同じ)
- `-s, --source` - メロディの取得元: `vocals`, `instrumental`, `auto`(デフォルト: `auto`)
- `-m, --method` - 音符の検出方法: `transcribe` または `pitch`(デフォルト: `transcribe`)
- `-V, --voices` - `chords`(ハーモニーあり)または `lead`(単旋律)(デフォルト: `chords`)
- `--transpose` - 半音単位のキーシフト(デフォルト: `0`)
- `--bits` - ビット深度、1-8、低いほど荒い音に(デフォルト: `8`)
- `--rate` - サンプルレート(Hz)、低いほどレトロに(デフォルト: `22050`)
- `--duty` - パルス波のデューティ比、0-1(デフォルト: `0.25`)
- `--no-cache` - キャッシュした Demucs ステムを読み書きしない
- `--cache-dir` - キャッシュ用ステムのディレクトリ（デフォルト: `~/.cache/audio8bit`、または `$AUDIO8BIT_CACHE_DIR`）
- `--version` - バージョンを表示する

終了コード: `0` 成功、`1` 変換エラー、`2` 引数の誤り。

### 機能

- **ボーカル**曲と**インストゥルメンタル**の両方に対応 - メロディの取得元を自動で選びます。
- **ポリフォニックなトランスクリプション**(basic-pitch)により、コードやベースを保持したり、単一のリード旋律に減らしたりできます。
- **Demucs** による音源分離は決定論的なので、同じ入力からは常に同じ結果が得られます。
- エイリアスのないチップチューン合成に、ラウドネスのダイナミクスと滑らかなリミッターを備えています。
- キーの移調、ビット深度、サンプルレート、パルス音の調整が可能です。
- 8ビット PCM の WAV 出力、または ffmpeg が書き込めるあらゆる形式に対応します。
- 実行ごとに品質レポートを生成し、すべてが自分のマシン上で動作します。

### ライセンス

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
