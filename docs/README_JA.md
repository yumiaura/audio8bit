# audio8bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
[![License: noncommercial](https://img.shields.io/badge/license-noncommercial-orange.svg)](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
![Sound](https://img.shields.io/badge/sound-8--bit%20chiptune-ff69b4.svg)
![Runs offline](https://img.shields.io/badge/runs-100%25%20offline-brightgreen.svg)

どんな曲でも、ターミナルから 8 ビットのゲーム風音楽に変えられます。
audio8bit は曲のメロディー（とコード）を見つけ出し、昔のゲーム機のような
レトロな「チップチューン」サウンドで再生します。

**[日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md)** | [English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## できること

- 曲を渡すと、そのチップチューン版が返ってきます。
- 曲に**歌**が入っていても、**インストゥルメンタル**でも動作します。メロディーは
  自動で選び取ります。
- すべてあなたのパソコン上で動作し、何もアップロードされません。

## 始める前に

次の 2 つが必要です。

- **Python 3.9 以降**
- **ffmpeg** — 音声の読み書きに使える無料ツールです。`sudo apt install ffmpeg`
  （Linux）または `brew install ffmpeg`（macOS）でインストールしてください。

## インストール

```bash
pip install audio8bit
```

> **初回の実行は遅いです。** 小さな AI モデル（約 80 MB）をダウンロードするため、
> 数分かかることがあります。これは正常な動作で、2 回目以降は速くなります。

## 使い方

```bash
audio8bit -i song.mp3
```

これでカレントフォルダーに `output.mp3` が作られます。それだけです。実行ごとに
短い品質レポートも表示されるので、結果がきれいに仕上がったか確認できます。

別の仕上がりにしたいですか？ よく使う調整は次のとおりです。

```bash
audio8bit -i song.mp3 -V lead          # メインメロディーだけ、コードなし
audio8bit -i song.mp3 -s vocals        # 歌に合わせる
audio8bit -i song.mp3 -s instrumental  # 楽器に合わせる
audio8bit -i song.mp3 --transpose 5    # 5 半音高く演奏する
audio8bit -i song.mp3 -f ogg           # .mp3 ではなく .ogg で保存する
```

## すべてのオプション

| Option           | Default          | 働き                                          |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | 変換する曲（mp3, wav, flac, …）               |
| `-o, --output`   | `output.<type>`  | 結果の保存先                                  |
| `-f, --format`   | same as input    | 別の形式で保存する。例: `ogg`、`wav`          |
| `-s, --source`   | `auto`           | メロディーを取り出す場所: `vocals`、`instrumental`、または `auto` |
| `-m, --method`   | `transcribe`     | 音符の見つけ方: `transcribe`（最良）または `pitch`（高速・軽量） |
| `-V, --voices`   | `chords`         | `chords`（ハーモニーあり）または `lead`（メロディー 1 本のみ） |
| `--transpose`    | `0`              | キーを半音単位でずらす（例: `5` で上、`-5` で下） |
| `--bits`         | `8`              | 音の解像度、1〜8（小さいほど荒い音に）        |
| `--rate`         | `22050`          | サンプルレート（Hz、低いほどレトロに）        |
| `--duty`         | `0.25`           | パルス波の音色、0〜1                          |

## うまくいかないとき

- **「ffmpeg not found」** — ffmpeg をインストールしてください（*始める前に* を参照）。
- **初回の実行が止まっているように見える** — AI モデルをダウンロード中です。数分
  待ってください。これは一度だけ起こります。
- **元の曲のように聞こえない** — `-s vocals` または `-s instrumental` で正しい
  パートを選ぶか、メロディーだけにしたい場合は `-V lead` を試してください。

## しくみ（読みたい人向け）

1. 曲をパート（ボーカル、ドラム、ベース、その他）に分けます。
2. 選んだパートで実際に演奏されている音符を検出します。
3. それらの音符をシンプルな 8 ビットの「チップ」サウンドで再生し、ファイルに保存します。

## ライセンス

非商用利用は無料です。詳細は [LICENSE](https://github.com/yumiaura/audio8bit/blob/main/LICENSE) を参照してください。
