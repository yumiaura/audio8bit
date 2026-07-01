## audio8bit - किसी भी गाने को 8-बिट चिपट्यून संगीत में बदलें

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | **[हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md)** | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

एक कमांड-लाइन टूल जो किसी भी गाने को 8-बिट, वीडियो-गेम शैली के संगीत में बदल देता है। यह धुन को ढूंढता है (गायन से या वाद्ययंत्रों से) और उसे रेट्रो "chiptune" ध्वनियों के साथ फिर से बजाता है, ठीक किसी पुराने गेम कंसोल की तरह। सब कुछ स्थानीय रूप से चलता है।

### आवश्यकताएं

- **Python 3.9 या उससे ऊपर**
- आपके `PATH` पर **ffmpeg** (यह `ffmpeg` और `ffprobe` के साथ आता है)। इसे
  `sudo apt install ffmpeg` (Linux) या `brew install ffmpeg` (macOS) के साथ इंस्टॉल करें।

### इंस्टॉलेशन

```bash
pip install audio8bit
```

या GitHub से:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **पहली बार चलाना धीमा होता है:** यह एक छोटा AI मॉडल (लगभग 80 MB) डाउनलोड करता है और इसमें
> कुछ मिनट लग सकते हैं। यह सामान्य है; बाद में चलाने पर यह तेज होता है।

### उपयोग

```bash
# Convert a song (auto-detects vocal or instrumental)
audio8bit -i song.mp3

# Just the main melody, no chords
audio8bit -i song.mp3 -V lead

# मल्टी-इंस्ट्रूमेंट बैंड: पल्स लीड + पल्स हार्मनी + ट्रायंगल बेस + नॉइज़ ड्रम
audio8bit -i song.mp3 -V band

# NES स्टाइल: आर्पेजियेटेड हार्मनी वाला बैंड, बीट पर
audio8bit -i song.mp3 -V nes

# Take the tune from the singing or from the instruments
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Save as a different format
audio8bit -i song.mp3 -f ogg

# Play it 5 semitones higher
audio8bit -i song.mp3 --transpose 5

# Show help and version
audio8bit --help
audio8bit --version
```

### कमांड लाइन विकल्प

- `-i, --input` - इनपुट ऑडियो फ़ाइल, आवश्यक (कोई भी प्रारूप जिसे ffmpeg पढ़ सकता है)
- `-o, --output` - आउटपुट पथ (डिफ़ॉल्ट: `output.<ext>`)
- `-f, --format` - आउटपुट प्रारूप, जैसे `ogg`, `wav` (डिफ़ॉल्ट: इनपुट जैसा ही)
- `-s, --source` - धुन का स्रोत: `vocals`, `instrumental`, `auto` (डिफ़ॉल्ट: `auto`)
- `-m, --method` - नोट खोज: `transcribe` या `pitch` (डिफ़ॉल्ट: `transcribe`)
- `-V, --voices` - `chords` (हार्मनी के साथ) या `lead` (एकल पंक्ति) या `band` (मल्टी-इंस्ट्रूमेंट: पल्स लीड + पल्स हार्मनी + ट्रायंगल बेस + नॉइज़ ड्रम) या `nes` (आर्पेजियेटेड, बीट पर) (डिफ़ॉल्ट: `chords`)
- `--transpose` - सेमीटोन में की शिफ्ट (डिफ़ॉल्ट: `0`)
- `--bits` - बिट गहराई, 1-8, कम होने पर अधिक क्रंची (डिफ़ॉल्ट: `8`)
- `--rate` - Hz में सैंपल रेट, कम होने पर अधिक रेट्रो (डिफ़ॉल्ट: `22050`)
- `--duty` - पल्स-वेव ड्यूटी साइकल, 0-1 (डिफ़ॉल्ट: `0.25`)
- `--no-cache` - कैश किए गए Demucs स्टेम न पढ़ें और न लिखें
- `--cache-dir` - कैश किए गए स्टेम के लिए डायरेक्टरी (डिफ़ॉल्ट: `~/.cache/audio8bit`, या `$AUDIO8BIT_CACHE_DIR`)
- `--version` - संस्करण दिखाएं

एग्जिट कोड: `0` सफलता, `1` रूपांतरण त्रुटि, `2` गलत तर्क।

### विशेषताएं

- **गायन** वाले गानों और **वाद्य** गानों दोनों के साथ काम करता है - धुन के स्रोत को स्वचालित रूप से चुनता है।
- **पॉलीफोनिक ट्रांसक्रिप्शन** (basic-pitch) कॉर्ड्स और बेस को बनाए रखता है, या उन्हें एकल लीड पंक्ति में सीमित कर देता है। `band` मोड उन्हें चिप चैनलों में बाँटता है (पल्स लीड, पल्स हार्मनी, ट्रायंगल बेस)। बेस, बेस स्टेम से और ड्रम, ड्रम स्टेम से आते हैं। `nes` मोड हार्मनी को आर्पेजियेट करता है और बीट पर सेट करता है।
- **Demucs** के साथ स्रोत पृथक्करण, निर्धारक होने के कारण एक ही इनपुट हमेशा एक ही परिणाम देता है।
- लाउडनेस डायनामिक्स और एक स्मूथ लिमिटर के साथ एलियास-मुक्त चिपट्यून संश्लेषण।
- की ट्रांसपोज़िशन और समायोज्य बिट गहराई, सैंपल रेट और पल्स टोन।
- WAV के रूप में 8-बिट PCM आउटपुट, या कोई भी प्रारूप जिसे ffmpeg लिख सकता है।
- हर बार चलाने के बाद एक गुणवत्ता रिपोर्ट, और सब कुछ आपकी अपनी मशीन पर चलता है।

### लाइसेंस

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
