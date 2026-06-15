# audio8bit

किसी भी गाने को 8‑बिट, वीडियो‑गेम जैसी म्यूज़िक में बदलें — सीधे अपने टर्मिनल से।
audio8bit गाने की धुन (और उसके कॉर्ड) ढूँढ़ता है और उन्हें पुराने ज़माने की
"chiptune" आवाज़ों के साथ फिर से बजाता है, जैसे कोई पुराना गेम कंसोल।

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | [Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md) | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | **[हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md)** | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## यह क्या करता है

- इसे एक गाना दें, बदले में उसका chiptune रूप पाएँ।
- चाहे गाने में **गायन** हो या वह **इंस्ट्रुमेंटल** हो — यह दोनों के साथ काम
  करता है और धुन अपने आप चुन लेता है।
- सब कुछ आपके अपने कंप्यूटर पर चलता है; कुछ भी अपलोड नहीं होता।

## शुरू करने से पहले

आपको दो चीज़ें चाहिए:

- **Python 3.9 या उससे नया**
- **ffmpeg** — ऑडियो पढ़ने और लिखने के लिए एक मुफ़्त टूल। इसे
  `sudo apt install ffmpeg` (Linux) या `brew install ffmpeg` (macOS) से इंस्टॉल करें।

## इंस्टॉल

```bash
pip install audio8bit
```

> **पहली बार चलाना धीमा होता है:** यह एक छोटा AI मॉडल (लगभग 80 MB) डाउनलोड करता है और
> इसमें कुछ मिनट लग सकते हैं। यह सामान्य है — बाद की बार तेज़ चलती हैं।

## इसका इस्तेमाल करें

```bash
audio8bit -i song.mp3
```

यह मौजूदा फ़ोल्डर में `output.mp3` बनाता है। बस इतना ही। हर बार चलने पर एक छोटी
क्वालिटी रिपोर्ट भी प्रिंट होती है ताकि आप देख सकें कि नतीजा साफ़‑सुथरा निकला है।

कुछ अलग चाहिए? यहाँ सबसे आम बदलाव दिए गए हैं:

```bash
audio8bit -i song.mp3 -V lead          # just the main melody, no chords
audio8bit -i song.mp3 -s vocals        # follow the singing
audio8bit -i song.mp3 -s instrumental  # follow the instruments
audio8bit -i song.mp3 --transpose 5    # play it 5 semitones higher
audio8bit -i song.mp3 -f ogg           # save as .ogg instead of .mp3
```

## सभी विकल्प

| Option           | Default          | यह क्या करता है                               |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | बदलने के लिए गाना (mp3, wav, flac, …)          |
| `-o, --output`   | `output.<type>`  | नतीजा कहाँ सहेजना है                           |
| `-f, --format`   | same as input    | किसी अलग प्रकार में सहेजें, जैसे `ogg`, `wav`  |
| `-s, --source`   | `auto`           | धुन कहाँ से लेनी है: `vocals`, `instrumental`, या `auto` |
| `-m, --method`   | `transcribe`     | नोट्स कैसे ढूँढ़े जाएँ: `transcribe` (सबसे अच्छा) या `pitch` (तेज़, हल्का) |
| `-V, --voices`   | `chords`         | `chords` (हार्मनी के साथ) या `lead` (एक धुन की लाइन) |
| `--transpose`    | `0`              | की को सेमीटोन में बदलें (जैसे `5` ऊपर, `-5` नीचे) |
| `--bits`         | `8`              | साउंड रिज़ॉल्यूशन, 1–8 (कम = ज़्यादा क्रंची)   |
| `--rate`         | `22050`          | सैंपल रेट Hz में (कम = ज़्यादा रेट्रो)          |
| `--duty`         | `0.25`           | पल्स वेव का टोन रंग, 0–1                       |

## अगर कुछ गड़बड़ हो जाए

- **"ffmpeg not found"** — ffmpeg इंस्टॉल करें (*शुरू करने से पहले* देखें)।
- **पहली बार चलना अटका हुआ लगता है** — यह AI मॉडल डाउनलोड कर रहा है; इसे कुछ
  मिनट दें। यह सिर्फ़ एक बार होता है।
- **यह गाने जैसा नहीं लगता** — सही हिस्सा चुनने के लिए `-s vocals` या
  `-s instrumental` आज़माएँ, या सिर्फ़ धुन के लिए `-V lead` इस्तेमाल करें।

## यह कैसे काम करता है (वैकल्पिक पढ़ाई)

1. गाने को हिस्सों में बाँटता है (vocals, drums, bass, और बाकी)।
2. आपके चुने हुए हिस्से में असल में बज रहे नोट्स का पता लगाता है।
3. उन नोट्स को सरल 8‑बिट "chip" आवाज़ों के साथ फिर से बजाता है और फ़ाइल सहेज देता है।

## लाइसेंस

यह प्रोजेक्ट PolyForm Noncommercial License के अंतर्गत लाइसेंस्ड है — विवरण के लिए [LICENSE](https://github.com/yumiaura/audio8bit/blob/main/LICENSE) फ़ाइल देखें।
