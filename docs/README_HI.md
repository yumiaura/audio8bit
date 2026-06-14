# audio8bit

किसी गाने को उसकी गाई गई धुन के 8-बिट चिपट्यून रूपांतरण में बदलें — ठीक वैसे
जैसे 80 के दशक का कोई गेम कंसोल इसे बजाता — सीधे कमांड लाइन से।

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | **[हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md)** | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

यह शब्दों को हटा देता है, धुन को बनाए रखता है, और इसे चिप आवाज़ों के लिए फिर से व्यवस्थित करता है:

1. **स्वर पृथक्करण (Vocal isolation)** — [Demucs](https://github.com/adefossez/demucs) (एक न्यूरल
   सोर्स-सेपरेशन मॉडल) गाई गई धुन को अकेले निकालता है।
2. **पिच ट्रैकिंग (Pitch tracking)** — librosa का pYIN समय के साथ पृथक की गई
   आवाज़ की मूल आवृत्ति का अनुसरण करता है।
3. **नोट निष्कर्षण (Note extraction)** — पिच ट्रैक को हिस्टैरिसिस के साथ अलग-अलग
   नोटों में विभाजित किया जाता है: वाइब्रेटो और स्कूप एक ही नोट के भीतर रहते हैं,
   वॉइसिंग के अंतराल पाट दिए जाते हैं, ऑक्टेव की त्रुटियाँ वापस मोड़ दी जाती हैं,
   अलंकरण की झिलमिलाहट अवशोषित कर ली जाती है।
4. **संगीतीकरण (Musicalisation)** — नोट के आरंभ गाने के अपने बीट ग्रिड पर स्नैप
   हो जाते हैं, धुन को एक रिंगटोन रजिस्टर में स्थानांतरित किया जाता है और एक
   भिन्न कुंजी में ट्रांसपोज़ किया जाता है (`--transpose`, डिफ़ॉल्ट +3 सेमीटोन)।
5. **चिप संश्लेषण (Chip synthesis)** — वाइब्रेटो और डिके एनवेलप के साथ एक
   बैंड-लिमिटेड पल्स लीड, बीटों पर एक ऑक्टेव नीचे एक ट्रायंगल बेस और एक
   टेम्पो-सिंक्ड इको; निर्माण द्वारा ही एलियास-मुक्त (केवल Nyquist से नीचे के
   हार्मोनिक्स ही जोड़े जाते हैं)।
6. **8-बिट आउटपुट + गुणवत्ता रिपोर्ट** — 8-बिट PCM में क्वांटाइज़ किया गया, WAV
   के रूप में लिखा गया या आपके चुने हुए प्रारूप में फिर से एन्कोड किया गया, फिर
   "मश" ह्यूरिस्टिक्स (नोट घनत्व, खंडन, ट्रिल, रेंज, क्लिपिंग) के विरुद्ध स्कोर
   किया गया ताकि एक खराब परिणाम कान से पता चलने के बजाय वस्तुनिष्ठ रूप से
   चिह्नित हो जाए।

> **ध्यान दें:** Demucs PyTorch को साथ लाता है (एक बड़ा इंस्टॉल) और पहली बार चलने
> पर अपना मॉडल (~80 MB) डाउनलोड करता है, और CPU पर प्रति ट्रैक पृथक्करण में कुछ
> मिनट लगते हैं। यही वह चीज़ है जो धुन को वास्तव में पहचानने योग्य बनाती है। सब
> कुछ स्थानीय रूप से चलता है।

## आवश्यकताएँ

- Python 3.9+
- आपके `PATH` पर [ffmpeg](https://ffmpeg.org/) (जो `ffmpeg` और `ffprobe` के साथ आता है)

## इंस्टॉल

```bash
pip install audio8bit
```

या किसी क्लोन से सीधे चलाएँ (पहले डिपेंडेंसी इंस्टॉल करें: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## उपयोग

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Description                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | इनपुट ऑडियो (कोई भी प्रारूप जिसे ffmpeg पढ़ सके) |
| `-o, --output`   | `output.<ext>`   | आउटपुट पथ (`-f` को ओवरराइड करता है)            |
| `-f, --format`   | input's format   | आउटपुट प्रारूप/एक्सटेंशन, जैसे `ogg`           |
| `--transpose`    | `3`              | सेमीटोन में कुंजी शिफ्ट (ऋणात्मक की अनुमति है)  |
| `--bits`         | `8`              | क्वांटाइज़ करने के लिए बिट गहराई (1–8)          |
| `--rate`         | `22050`          | Hz में आउटपुट सैंपल दर                         |
| `--duty`         | `0.25`           | पल्स-वेव ड्यूटी साइकल (0–1)                    |

एग्ज़िट कोड: `0` सफलता, `1` रूपांतरण त्रुटि, `2` गलत तर्क। हर रन एक गुणवत्ता
रिपोर्ट के साथ समाप्त होता है; विफल जाँचें stderr पर एक चेतावनी प्रिंट करती हैं।

## License

MIT
