# audio8bit

노래를 그 노래에서 부른 멜로디의 8비트 칩튠 편곡으로 바꿔줍니다 — 80년대 게임 콘솔이
연주하던 방식 그대로 — 명령줄에서 바로 처리합니다.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | **[한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)**

가사는 제거하고 곡조는 유지하며, 이를 칩 음색으로 다시 편곡합니다:

1. **보컬 분리** — [Demucs](https://github.com/adefossez/demucs)(신경망 기반
   음원 분리 모델)가 부른 멜로디만 따로 추출합니다.
2. **피치 추적** — librosa의 pYIN이 분리된 목소리의 기본 주파수를 시간에 따라
   따라갑니다.
3. **음 추출** — 피치 트랙은 히스테리시스를 사용해 개별 음들로 분리됩니다:
   비브라토와 스쿠프는 하나의 음 안에 유지되고, 발성 간극은 메워지며, 옥타브
   오류는 다시 접히고, 장식음의 떨림은 흡수됩니다.
4. **음악화** — 음의 시작점이 곡 자체의 비트 그리드에 맞춰지고, 멜로디는
   벨소리 음역대로 이동되며 다른 조로 전조됩니다(`--transpose`, 기본값 +3
   반음).
5. **칩 합성** — 비브라토와 감쇠 엔벨로프를 갖춘 대역 제한 펄스 리드, 비트마다
   한 옥타브 아래에 놓이는 삼각파 베이스, 그리고 템포에 동기화된 에코; 설계상
   에일리어스가 없습니다(Nyquist 미만의 배음만 합산됩니다).
6. **8비트 출력 + 품질 보고서** — 8비트 PCM으로 양자화되어 WAV로 작성되거나
   선택한 형식으로 다시 인코딩되며, 그 후 "뭉개짐(mush)" 휴리스틱(음 밀도,
   파편화, 트릴, 음역, 클리핑)에 따라 점수가 매겨집니다. 덕분에 나쁜 결과를
   귀로 발견하는 대신 객관적으로 표시할 수 있습니다.

> **참고:** Demucs는 PyTorch(대용량 설치)를 함께 가져오며 처음 실행할 때
> 모델(~80 MB)을 다운로드하고, CPU에서는 트랙당 분리에 몇 분이 걸립니다. 이것이
> 멜로디를 실제로 알아들을 수 있게 만드는 요소입니다. 모든 처리는 로컬에서
> 실행됩니다.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (`ffmpeg`와 `ffprobe`를 함께 제공)가 `PATH`에 있어야 함

## Install

```bash
pip install audio8bit
```

또는 클론한 저장소에서 바로 실행합니다(먼저 의존성을 설치하세요: `pip install numpy demucs librosa`):

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
| `-i, --input`    | — (required)     | 입력 오디오 (ffmpeg가 읽을 수 있는 모든 형식)     |
| `-o, --output`   | `output.<ext>`   | 출력 경로 (`-f`보다 우선함)                 |
| `-f, --format`   | input's format   | 출력 형식/확장자, 예: `ogg`          |
| `--transpose`    | `3`              | 반음 단위 조 이동 (음수 허용)    |
| `--bits`         | `8`              | 양자화할 비트 심도 (1–8)               |
| `--rate`         | `22050`          | 출력 샘플레이트 (Hz 단위)                     |
| `--duty`         | `0.25`           | 펄스파 듀티 사이클 (0–1)                  |

종료 코드: `0` 성공, `1` 변환 오류, `2` 잘못된 인자. 모든 실행은 품질
보고서로 끝나며, 실패한 검사는 stderr에 경고를 출력합니다.

## License

MIT 라이선스
