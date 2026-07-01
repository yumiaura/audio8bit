## audio8bit - 어떤 곡이든 8비트 칩튠 음악으로 바꾸기

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | **[한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)**

어떤 곡이든 8비트 비디오 게임 스타일의 음악으로 바꿔주는 명령줄 도구입니다. (보컬이나 악기에서) 멜로디를 찾아내어 옛날 게임기처럼 레트로한 "칩튠" 사운드로 다시 연주합니다. 모든 작업은 로컬에서 실행됩니다.

### 요구 사항

- **Python 3.9 이상**
- `PATH`에 있는 **ffmpeg** (`ffmpeg`와 `ffprobe`가 함께 제공됩니다). 다음 명령으로 설치하세요.
  `sudo apt install ffmpeg` (Linux) 또는 `brew install ffmpeg` (macOS).

### 설치

```bash
pip install audio8bit
```

또는 GitHub에서:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **첫 실행은 느립니다:** 작은 AI 모델(약 80 MB)을 다운로드하므로
> 몇 분 정도 걸릴 수 있습니다. 정상적인 현상이며, 이후 실행은 더 빠릅니다.

### 사용법

```bash
# 곡 변환 (보컬 또는 연주곡을 자동 감지)
audio8bit -i song.mp3

# 메인 멜로디만, 코드 없이
audio8bit -i song.mp3 -V lead

# 멀티 악기 밴드: 펄스 리드 + 펄스 하모니 + 삼각파 베이스 + 노이즈 드럼
audio8bit -i song.mp3 -V band

# 노래에서 또는 악기에서 멜로디 가져오기
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# 다른 형식으로 저장
audio8bit -i song.mp3 -f ogg

# 5 반음 높여서 재생
audio8bit -i song.mp3 --transpose 5

# 도움말과 버전 표시
audio8bit --help
audio8bit --version
```

### 명령줄 옵션

- `-i, --input` - 입력 오디오 파일, 필수 (ffmpeg가 읽을 수 있는 모든 형식)
- `-o, --output` - 출력 경로 (기본값: `output.<ext>`)
- `-f, --format` - 출력 형식, 예: `ogg`, `wav` (기본값: 입력과 동일)
- `-s, --source` - 멜로디 소스: `vocals`, `instrumental`, `auto` (기본값: `auto`)
- `-m, --method` - 음 찾기: `transcribe` 또는 `pitch` (기본값: `transcribe`)
- `-V, --voices` - `chords` (화음 포함) 또는 `lead` (단일 라인) 또는 `band` (멀티 악기: 펄스 리드 + 펄스 하모니 + 삼각파 베이스 + 노이즈 드럼) (기본값: `chords`)
- `--transpose` - 반음 단위의 키 이동 (기본값: `0`)
- `--bits` - 비트 깊이, 1-8, 낮을수록 더 거칠어집니다 (기본값: `8`)
- `--rate` - Hz 단위의 샘플 레이트, 낮을수록 더 레트로합니다 (기본값: `22050`)
- `--duty` - 펄스파 듀티 사이클, 0-1 (기본값: `0.25`)
- `--no-cache` - 캐시된 Demucs 스템을 읽거나 쓰지 않음
- `--cache-dir` - 캐시된 스템을 저장할 디렉터리 (기본값: `~/.cache/audio8bit`, 또는 `$AUDIO8BIT_CACHE_DIR`)
- `--version` - 버전 표시

종료 코드: `0` 성공, `1` 변환 오류, `2` 잘못된 인수.

### 기능

- **보컬** 곡과 **연주곡** 모두 지원 - 멜로디 소스를 자동으로 선택합니다.
- **다성 전사**(basic-pitch)로 코드와 베이스를 유지하거나, 단일 리드 라인으로 줄여줍니다. `band` 모드는 이를 칩 채널로 나눕니다 (펄스 리드, 펄스 하모니, 삼각파 베이스). 베이스는 베이스 스템에서, 드럼은 드럼 스템에서 가져옵니다.
- **Demucs**를 이용한 음원 분리, 결정론적이므로 동일한 입력은 항상 동일한 결과를 냅니다.
- 라우드니스 다이내믹스와 부드러운 리미터를 갖춘 에일리어스 없는 칩튠 합성.
- 키 전조와 조정 가능한 비트 깊이, 샘플 레이트, 펄스 톤.
- WAV로 출력되는 8비트 PCM, 또는 ffmpeg가 쓸 수 있는 모든 형식.
- 매 실행 후 품질 보고서를 제공하며, 모든 작업이 여러분 자신의 컴퓨터에서 실행됩니다.

### 라이선스

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
