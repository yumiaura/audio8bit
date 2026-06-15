# audio8bit

किसी गाने को 8-बिट चिपट्यून व्यवस्था में बदलें — गाई गई आवाज़ **या**
वाद्य संगीत, उसकी सुर-संगति के साथ — ठीक वैसे जैसे 80 के दशक का कोई गेम कंसोल
इसे बजाता, सीधे कमांड लाइन से।

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | **[हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md)** | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

यह धुन को बनाए रखता है और इसे चिप आवाज़ों के लिए फिर से व्यवस्थित करता है:

1. **स्रोत पृथक्करण (Source separation)** — [Demucs](https://github.com/adefossez/demucs)
   (एक न्यूरल सोर्स-सेपरेशन मॉडल) गाने को स्टेम्स में विभाजित करता है, जो
   निर्धारक रूप से चलता है ताकि एक ही इनपुट हमेशा एक ही परिणाम दे। धुन गाई गई
   **vocals** से ली जाती है या, किसी वाद्य संगीत के लिए, पृष्ठभूमि के **lead**
   से (ड्रम और बेस हटाकर); `--source auto` तब vocal का उपयोग करता है जब गाने में
   वास्तव में कोई आवाज़ हो और अन्यथा वाद्य संगीत का।
2. **नोट खोजना (Note finding)** (`--method`, डिफ़ॉल्ट `transcribe`) — एक
   पॉलीफ़ोनिक ट्रांसक्रिप्शन मॉडल ([basic-pitch](https://github.com/spotify/basic-pitch))
   स्टेम को असली नोटों में बदल देता है। `--voices chords` (डिफ़ॉल्ट) हर नोट
   बजाता है, इसलिए सुर-संगति और बेस बने रहते हैं; `--voices lead` कॉर्ड्स के बीच
   से एक ही धुन की पंक्ति का अनुसरण करता है (एक Viterbi पथ, न कि वह भोली ऊपरी
   पंक्ति जो lead और संगत के बीच कूदती रहती है)। यह कॉर्ड्स और वाद्य संगीत पर एक
   साथ टिका रहता है, जहाँ फ्रेम-दर-फ्रेम पिच ट्रैकिंग बस आवाज़ों के बीच कूदती है
   और यादृच्छिक सुनाई देती है। `--method pitch` इसके बजाय गाने के बीट ग्रिड से
   स्नैप की गई librosa की pYIN का उपयोग करता है (मोनोफ़ोनिक, हल्का, बिना
   TensorFlow)।
3. **संगीतीकरण (Musicalisation)** — एक वैकल्पिक `--transpose` कुंजी बदल देता है।
   `lead` को रिंगटोन रजिस्टर में ऑक्टेव-स्थानांतरित किया जाता है; `chords`
   ट्रांसक्राइब की गई पिचों को बनाए रखता है ताकि सुर-संगति बरकरार रहे।
   ट्रांसक्राइब किए गए नोट किसी ग्रिड पर स्नैप होने के बजाय अपना स्वयं का
   प्राकृतिक समय बनाए रखते हैं।
4. **चिप संश्लेषण (Chip synthesis)** — प्रत्येक नोट एक बैंड-लिमिटेड पल्स आवाज़
   है (`lead` और `pitch` पथ वाइब्रेटो/डिके जोड़ते हैं, और `pitch` एक ट्रायंगल
   बेस और एक टेम्पो-सिंक्ड इको जोड़ता है); निर्माण द्वारा ही एलियास-मुक्त (केवल
   Nyquist से नीचे के हार्मोनिक्स ही जोड़े जाते हैं)। `chords` गतिशीलता के लिए
   प्रत्येक आवाज़ को उसकी ट्रांसक्राइब की गई प्रबलता के अनुसार मापता है और मिश्रण
   को एक सहज लिमिटर से समतल करता है, ताकि घने कॉर्ड्स अकेले नोटों को दबा न दें।
5. **8-बिट आउटपुट + गुणवत्ता रिपोर्ट** — 8-बिट PCM में क्वांटाइज़ किया गया, WAV
   के रूप में लिखा गया या आपके चुने हुए प्रारूप में फिर से एन्कोड किया गया, फिर
   स्कोर किया गया: एकल पंक्ति के लिए मधुर "मश" ह्यूरिस्टिक्स, या कॉर्ड्स के लिए
   ऑडियो-स्तरीय जाँचें (मौन, एलियासिंग, क्लिपिंग) — ताकि एक खराब परिणाम कान से
   पता चलने के बजाय वस्तुनिष्ठ रूप से चिह्नित हो जाए।

> **ध्यान दें:** डिफ़ॉल्ट `transcribe` विधि basic-pitch (TensorFlow) को साथ
> लाती है और Demucs PyTorch को साथ लाता है — दोनों बड़े इंस्टॉल हैं — और Demucs
> पहली बार चलने पर अपना मॉडल (~80 MB) डाउनलोड करता है। पृथक्करण के साथ-साथ
> ट्रांसक्रिप्शन CPU पर प्रति ट्रैक कुछ मिनट लेते हैं। यही वह चीज़ है जो धुन को
> वास्तव में पहचानने योग्य बनाती है। सब कुछ स्थानीय रूप से चलता है।

## आवश्यकताएँ

- Python 3.9+
- आपके `PATH` पर [ffmpeg](https://ffmpeg.org/) (जो `ffmpeg` और `ffprobe` के साथ आता है)

## इंस्टॉल

```bash
pip install audio8bit
```

या किसी क्लोन से सीधे चलाएँ (पहले डिपेंडेंसी इंस्टॉल करें: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## उपयोग

```bash
audio8bit -i song.mp3                      # -> output.mp3, full chords (keeps the input format)
audio8bit -i song.mp3 -V lead              # a single melody line instead of chords
audio8bit -i track.mp3 -s instrumental     # follow the instrumental, not vocals
audio8bit -i song.mp3 -m pitch             # lighter pYIN method (no TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitones up
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | विवरण                                  |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (required)     | इनपुट ऑडियो (कोई भी प्रारूप जिसे ffmpeg पढ़ सके) |
| `-o, --output`   | `output.<ext>`   | आउटपुट पथ (`-f` को ओवरराइड करता है)            |
| `-f, --format`   | input's format   | आउटपुट प्रारूप/एक्सटेंशन, जैसे `ogg`           |
| `-s, --source`   | `auto`           | अनुसरण करने योग्य धुन: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | नोट खोजना: `transcribe` (पॉलीफ़ोनिक) या `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | ट्रांसक्राइब आउटपुट: `chords` (सुर-संगति) या `lead` (एक पंक्ति) |
| `--transpose`    | `0`              | सेमीटोन में कुंजी शिफ्ट (ऋणात्मक की अनुमति है)  |
| `--bits`         | `8`              | क्वांटाइज़ करने के लिए बिट गहराई (1–8)          |
| `--rate`         | `22050`          | Hz में आउटपुट सैंपल दर                         |
| `--duty`         | `0.25`           | पल्स-वेव ड्यूटी साइकल (0–1)                    |

एग्ज़िट कोड: `0` सफलता, `1` रूपांतरण त्रुटि, `2` गलत तर्क। हर रन एक गुणवत्ता
रिपोर्ट के साथ समाप्त होता है; विफल जाँचें stderr पर एक चेतावनी प्रिंट करती हैं।

## License

MIT लाइसेंस
