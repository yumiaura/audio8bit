# audio8bit

노래를 8비트 칩튠 편곡으로 바꿔보세요 — 부른 보컬 **또는** 화음이 있는
반주를, 80년대 게임 콘솔이 연주하듯이, 커맨드 라인에서 바로.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | **[한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)**

곡조를 유지하면서 칩 음색으로 다시 편곡합니다:

1. **음원 분리** — [Demucs](https://github.com/adefossez/demucs)(신경망 기반
   음원 분리 모델)가 노래를 스템으로 나누며, 결정론적으로 실행되어 같은 입력은
   항상 같은 결과를 냅니다. 멜로디는 부른 **보컬**에서 가져오거나, 연주곡의
   경우에는 (드럼과 베이스를 제거한) 반주의 **리드**에서 가져옵니다.
   `--source auto`는 노래에 실제로 보컬이 있을 때는 보컬을, 그렇지 않을 때는
   반주를 사용합니다.
2. **음 찾기** (`--method`, 기본값 `transcribe`) — 다성 채보 모델
   ([basic-pitch](https://github.com/spotify/basic-pitch))이 스템을 실제 음으로
   바꿉니다. `--voices chords`(기본값)는 모든 음을 연주하므로 화음과 베이스가
   유지됩니다. `--voices lead`는 화음 사이로 하나의 멜로디 라인을 따라갑니다
   (리드와 반주 사이를 오가는 단순한 최상단 라인이 아니라 Viterbi 경로입니다).
   이 방식은 화음과 연주곡에서도 안정적으로 유지되는데, 프레임 단위 피치 추적은
   보이스 사이를 그냥 오가며 무작위처럼 들립니다. `--method pitch`는 대신 곡의
   비트 그리드에 스냅된 librosa의 pYIN을 사용합니다(단성, 더 가벼움, TensorFlow
   불필요).
3. **음악화** — 선택적인 `--transpose`로 조를 바꿉니다. `lead`는 옥타브를
   이동해 벨소리 음역대로 옮깁니다. `chords`는 채보된 음높이를 유지해 화음이
   그대로 보존됩니다. 채보된 음은 그리드에 스냅되지 않고 고유의 자연스러운
   타이밍을 유지합니다.
4. **칩 합성** — 각 음은 대역 제한된 펄스 보이스입니다(`lead`와 `pitch`
   경로는 비브라토/감쇠를 추가하고, `pitch`는 삼각파 베이스와 템포에 동기화된
   에코를 추가합니다). 설계상 에일리어스가 없습니다(Nyquist 미만의 배음만
   합산됩니다). `chords`는 다이내믹을 위해 각 보이스를 채보된 음량으로
   스케일링하고 부드러운 리미터로 믹스 레벨을 맞추므로, 빽빽한 화음이 단음을
   묻어버리지 않습니다.
5. **8비트 출력 + 품질 보고서** — 8비트 PCM으로 양자화하여 WAV로 작성하거나
   선택한 형식으로 다시 인코딩한 뒤 점수를 매깁니다: 단일 라인에는 멜로디
   "뭉개짐(mush)" 휴리스틱을, 화음에는 오디오 수준 검사(무음, 에일리어싱,
   클리핑)를 적용합니다 — 그래서 나쁜 결과를 귀로 발견하는 대신 객관적으로
   표시합니다.

> **참고:** 기본 `transcribe` 방식은 basic-pitch(TensorFlow)를 함께 가져오고
> Demucs는 PyTorch를 함께 가져옵니다 — 둘 다 설치 용량이 큽니다 — 그리고
> Demucs는 처음 실행할 때 모델(~80 MB)을 다운로드합니다. CPU에서는 분리와
> 채보에 트랙당 몇 분이 걸립니다. 이것이 멜로디를 실제로 알아들을 수 있게
> 만드는 요소입니다. 모든 처리는 로컬에서 실행됩니다.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (`ffmpeg`와 `ffprobe`를 함께 제공)가 `PATH`에 있어야 함

## Install

```bash
pip install audio8bit
```

또는 클론한 저장소에서 바로 실행합니다(먼저 의존성을 설치하세요: `pip install numpy demucs librosa basic-pitch`):

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

| Flag             | Default          | 설명                                          |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | 입력 오디오 (ffmpeg가 읽을 수 있는 모든 형식)     |
| `-o, --output`   | `output.<ext>`   | 출력 경로 (`-f`보다 우선함)                 |
| `-f, --format`   | input's format   | 출력 형식/확장자, 예: `ogg`          |
| `-s, --source`   | `auto`           | 따라갈 멜로디: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | 음 찾기: `transcribe`(다성) 또는 `pitch`(pYIN) |
| `-V, --voices`   | `chords`         | 채보 출력: `chords`(화음) 또는 `lead`(한 라인) |
| `--transpose`    | `0`              | 반음 단위 조 이동 (음수 허용)    |
| `--bits`         | `8`              | 양자화할 비트 심도 (1–8)               |
| `--rate`         | `22050`          | 출력 샘플레이트 (Hz 단위)                     |
| `--duty`         | `0.25`           | 펄스파 듀티 사이클 (0–1)                  |

종료 코드: `0` 성공, `1` 변환 오류, `2` 잘못된 인자. 모든 실행은 품질
보고서로 끝나며, 실패한 검사는 stderr에 경고를 출력합니다.

## License

MIT 라이선스
