# audio8bit

楽曲を、その歌唱メロディの8ビット・チップチューン・アレンジへと変換します。まるで80年代のゲーム機が奏でるように。すべてコマンドラインから実行できます。

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | **[日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md)** | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

歌詞を取り除き、メロディを残し、それをチップ音源用に再アレンジします。

1. **ボーカルの分離** — [Demucs](https://github.com/adefossez/demucs)（ニューラル音源分離モデル）が歌唱メロディだけを抽出します。
2. **ピッチ追跡** — librosa の pYIN が、分離された声の基本周波数を時間に沿って追跡します。
3. **ノート抽出** — ピッチトラックはヒステリシスを用いて個々のノートに分割されます。ビブラートやしゃくり上げは一つのノート内に収め、発声の途切れは橋渡しし、オクターブ誤差は折り返して補正し、装飾音のちらつきは吸収します。
4. **音楽化** — ノートの発音タイミングは楽曲自身のビートグリッドにスナップし、メロディは着信音の音域へ移され、別のキーへ移調されます（`--transpose`、デフォルトは +3 半音）。
5. **チップシンセシス** — ビブラートとディケイ・エンベロープを備えた帯域制限されたパルス・リード、ビート上で1オクターブ下に重なるトライアングル・ベース、そしてテンポに同期したエコー。構造上エイリアスが生じません（Nyquist 周波数より下の倍音のみが合成されます）。
6. **8ビット出力 + 品質レポート** — 8ビット PCM に量子化し、WAV として書き出すか、選択した形式へ再エンコードします。その後「もたつき」を判定するヒューリスティック（ノート密度、断片化、トリル、音域、クリッピング）でスコアリングし、悪い結果は耳で気づくのではなく客観的に指摘されます。

> **ご注意:** Demucs は PyTorch（サイズの大きいインストール）を必要とし、初回実行時にモデル（約 80 MB）をダウンロードします。また、CPU では1曲あたりの分離に数分かかります。これこそがメロディを実際に聞き取れるものにしている要素です。すべてはローカルで実行されます。

## Requirements

- Python 3.9+
- `PATH` 上の [ffmpeg](https://ffmpeg.org/)（`ffmpeg` と `ffprobe` を同梱）

## Install

```bash
pip install audio8bit
```

または、クローンから直接実行します（まず依存関係をインストールしてください: `pip install numpy demucs librosa`）:

```bash
python main.py -i song.mp3
```

## Usage

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | 入力音声（ffmpeg が読み込める任意の形式）       |
| `-o, --output`   | `output.<ext>`   | 出力パス（`-f` を上書き）                      |
| `-f, --format`   | input's format   | 出力形式/拡張子、例: `ogg`                     |
| `--transpose`    | `3`              | 半音単位のキーシフト（負の値も可）             |
| `--bits`         | `8`              | 量子化するビット深度（1〜8）                   |
| `--rate`         | `22050`          | 出力サンプルレート（Hz）                       |
| `--duty`         | `0.25`           | パルス波のデューティ比（0〜1）                 |

終了コード: `0` 成功、`1` 変換エラー、`2` 引数エラー。実行のたびに品質レポートが出力され、チェックに失敗した項目は stderr に警告を表示します。

## License

MIT ライセンス
