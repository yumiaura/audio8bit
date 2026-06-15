# audio8bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
![Sound](https://img.shields.io/badge/sound-8--bit%20chiptune-ff69b4.svg)
![Runs offline](https://img.shields.io/badge/runs-100%25%20offline-brightgreen.svg)

어떤 노래든 8비트 비디오 게임 스타일의 음악으로 바꿔보세요 — 바로 터미널에서요.
audio8bit는 노래의 멜로디(그리고 코드)를 찾아내어, 옛날 게임기처럼 레트로한
"칩튠(chiptune)" 사운드로 다시 연주합니다.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | **[한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)**

## 무엇을 하나요

- 노래를 넣으면, 그 노래의 칩튠 버전을 돌려줍니다.
- **노래(보컬)**가 있든 **연주곡(반주)**이든 모두 작동합니다 — 멜로디를
  자동으로 골라냅니다.
- 모든 작업은 여러분의 컴퓨터에서 실행되며, 어떤 것도 업로드되지 않습니다.

## 시작하기 전에

두 가지가 필요합니다:

- **Python 3.9 이상**
- **ffmpeg** — 오디오를 읽고 쓰기 위한 무료 도구입니다.
  `sudo apt install ffmpeg`(Linux) 또는 `brew install ffmpeg`(macOS)로
  설치하세요.

## 설치

```bash
pip install audio8bit
```

> **첫 실행은 느립니다:** 작은 AI 모델(약 80 MB)을 내려받기 때문에 몇 분
> 걸릴 수 있습니다. 정상적인 동작이며 — 이후 실행은 더 빠릅니다.

## 사용하기

```bash
audio8bit -i song.mp3
```

이 명령은 현재 폴더에 `output.mp3`를 만듭니다. 그게 전부입니다. 실행할
때마다 짧은 품질 보고서도 출력되어, 결과가 깔끔하게 나왔는지 확인할 수
있습니다.

다른 결과를 원하시나요? 가장 자주 쓰는 조정 옵션들입니다:

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## 전체 옵션

| Option           | Default          | 하는 일                                       |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | 변환할 노래 (mp3, wav, flac, …)               |
| `-o, --output`   | `output.<type>`  | 결과를 저장할 위치                            |
| `-f, --format`   | same as input    | 다른 형식으로 저장, 예: `ogg`, `wav`          |
| `-s, --source`   | `auto`           | 멜로디를 가져올 곳: `vocals`, `instrumental`, 또는 `auto` |
| `-m, --method`   | `transcribe`     | 음을 찾는 방법: `transcribe`(최상) 또는 `pitch`(더 빠르고 가벼움) |
| `-V, --voices`   | `chords`         | `chords`(화음 포함) 또는 `lead`(멜로디 한 줄) |
| `--transpose`    | `0`              | 키를 반음 단위로 이동 (예: `5`는 위로, `-5`는 아래로) |
| `--bits`         | `8`              | 사운드 해상도, 1–8 (낮을수록 더 거친 소리)    |
| `--rate`         | `22050`          | 샘플 레이트(Hz) (낮을수록 더 레트로함)        |
| `--duty`         | `0.25`           | 펄스파의 음색, 0–1                            |

## 문제가 생기면

- **"ffmpeg not found"** — ffmpeg를 설치하세요(*시작하기 전에* 참고).
- **첫 실행이 멈춘 것 같아요** — AI 모델을 내려받는 중입니다. 몇 분만
  기다려 주세요. 이 과정은 한 번만 일어납니다.
- **노래처럼 들리지 않아요** — `-s vocals` 또는 `-s instrumental`로 올바른
  파트를 고르거나, 멜로디만 원한다면 `-V lead`를 사용해 보세요.

## 작동 원리 (선택해서 읽기)

1. 노래를 여러 파트(보컬, 드럼, 베이스, 그리고 나머지)로 분리합니다.
2. 선택한 파트에서 실제로 연주되는 음들을 감지합니다.
3. 그 음들을 단순한 8비트 "칩" 사운드로 다시 연주하고 파일로 저장합니다.

## License

MIT 라이선스
