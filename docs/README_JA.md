# audio8bit

楽曲を8ビットのチップチューン・アレンジに変換します。歌われたボーカル**または**ハーモニー付きの伴奏を、80年代のゲーム機が鳴らすようなサウンドで、コマンドラインから直接生成できます。

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | **[日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md)** | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

メロディを保ちつつ、チップ音源向けに再アレンジします。

1. **音源分離** — [Demucs](https://github.com/adefossez/demucs)（ニューラル音源分離モデル）が楽曲をステムに分割します。決定論的に実行されるため、同じ入力からは常に同じ結果が得られます。メロディは歌われた**ボーカル**から、またはインストゥルメンタルの場合は伴奏の**リード**（ドラムとベースを除去したもの）から取得します。`--source auto` は、楽曲に実際にボーカルがある場合はボーカルを、そうでない場合はインストゥルメンタルを使用します。
2. **音符検出**（`--method`、デフォルトは `transcribe`）— ポリフォニックな採譜モデル（[basic-pitch](https://github.com/spotify/basic-pitch)）がステムを実際の音符に変換します。`--voices chords`（デフォルト）はすべての音符を鳴らすため、ハーモニーとベースが保たれます。`--voices lead` はコードを通して単一のメロディラインを追います（単純に最高音を拾うとリードと伴奏の間を飛び移ってしまいますが、ここではそうではなくViterbi経路を使います）。これによりコードやインストゥルメンタルでもまとまりが保たれます。フレームごとのピッチ追跡では声部間を飛び移ってランダムに聞こえてしまうのです。`--method pitch` はその代わりに、楽曲のビートグリッドにスナップさせたlibrosaのpYINを使います（モノフォニックで軽量、TensorFlow不要）。
3. **音楽化** — 任意の `--transpose` でキーを変更できます。`lead` は着信音のような音域へオクターブ移動されます。`chords` は採譜されたピッチをそのまま保つため、ハーモニーが損なわれません。採譜された音符はグリッドにスナップされず、それぞれ本来の自然なタイミングを保ちます。
4. **チップ合成** — 各音符は帯域制限されたパルス音源です（`lead` と `pitch` の経路にはビブラートとディケイが加わり、`pitch` にはさらに三角波のベースとテンポ同期のエコーが加わります）。構造上エイリアスが生じません（Nyquist周波数未満の倍音のみを加算するため）。`chords` はダイナミクスのために各音源を採譜されたラウドネスに応じてスケーリングし、滑らかなリミッターでミックスをレベリングします。これにより密なコードが単音を埋もれさせることがありません。
5. **8ビット出力＋品質レポート** — 8ビットPCMに量子化し、WAVとして書き出すか、選択した形式に再エンコードした上で採点します。単一ラインに対してはメロディの「ぐちゃぐちゃ感」を測るヒューリスティクスを、コードに対してはオーディオレベルのチェック（無音、エイリアシング、クリッピング）を行います。これにより、悪い結果が耳で気づかれる前に客観的に検出されます。

> **ご注意:** デフォルトの `transcribe` メソッドは basic-pitch（TensorFlow）を、Demucs は PyTorch を必要とします。いずれも大規模なインストールであり、Demucs は初回実行時にモデル（約80MB）をダウンロードします。分離と採譜には、CPUで1トラックあたり数分かかります。これがメロディを実際に聞き取れるものにしているのです。すべてローカルで実行されます。

## Requirements

- Python 3.9+
- `PATH` 上の [ffmpeg](https://ffmpeg.org/)（`ffmpeg` と `ffprobe` を同梱）

## Install

```bash
pip install audio8bit
```

または、クローンから直接実行します（まず依存関係をインストールしてください: `pip install numpy demucs librosa basic-pitch`）:

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
| `-i, --input`    | — (required)     | 入力音声（ffmpeg が読み込める任意の形式）     |
| `-o, --output`   | `output.<ext>`   | 出力パス（`-f` を上書き）                     |
| `-f, --format`   | input's format   | 出力形式/拡張子、例: `ogg`                    |
| `-s, --source`   | `auto`           | 追うメロディ: `vocals`、`instrumental`、`auto` |
| `-m, --method`   | `transcribe`     | 音符検出: `transcribe`（ポリフォニック）または `pitch`（pYIN） |
| `-V, --voices`   | `chords`         | transcribe の出力: `chords`（ハーモニー）または `lead`（単一ライン） |
| `--transpose`    | `0`              | 半音単位のキーシフト（負の値も可）           |
| `--bits`         | `8`              | 量子化するビット深度（1〜8）                  |
| `--rate`         | `22050`          | 出力サンプルレート（Hz）                      |
| `--duty`         | `0.25`           | パルス波のデューティ比（0〜1）                |

終了コード: `0` 成功、`1` 変換エラー、`2` 引数エラー。実行のたびに品質レポートが出力され、チェックに失敗した項目は stderr に警告を表示します。

## License

MIT ライセンス
