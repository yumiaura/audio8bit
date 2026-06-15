# audio8bit

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pypi/dm/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

Transforme qualquer música em som 8-bit, no estilo de videogame - direto do seu
terminal. O audio8bit encontra a melodia da música (e seus acordes) e a
reproduz com sons retrô de "chiptune", como um console de jogos antigo.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | **[Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md)** | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

## O que ele faz

- Dê uma música e receba de volta uma versão chiptune dela.
- Funciona tanto se a música tiver **canto** quanto se for **instrumental** -
  ele escolhe a melodia automaticamente.
- Tudo roda no seu próprio computador; nada é enviado para a internet.

## Antes de começar

Você precisa de duas coisas:

- **Python 3.9 ou mais recente**
- **ffmpeg** - uma ferramenta gratuita para ler e gravar áudio. Instale com
  `sudo apt install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS).

## Instalação

```bash
pip install audio8bit
```

> **A primeira execução é lenta:** ela baixa um pequeno modelo de IA (cerca de
> 80 MB) e pode levar alguns minutos. Isso é normal - as execuções seguintes
> são mais rápidas.

## Como usar

```bash
audio8bit -i song.mp3
```

Isso cria `output.mp3` na pasta atual. É só isso. Cada execução também
imprime um breve relatório de qualidade para que você veja que o resultado
saiu limpo.

Quer algo diferente? Aqui estão os ajustes mais comuns:

```bash
audio8bit -i song.mp3 -V lead          # apenas a melodia principal, sem acordes
audio8bit -i song.mp3 -s vocals        # seguir o canto
audio8bit -i song.mp3 -s instrumental  # seguir os instrumentos
audio8bit -i song.mp3 --transpose 5    # tocar 5 semitons mais agudo
audio8bit -i song.mp3 -f ogg           # salvar como .ogg em vez de .mp3
```

## Todas as opções

| Option           | Default          | O que faz                                     |
| ---------------- | ---------------- | --------------------------------------------- |
| `-i, --input`    | required         | A música a converter (mp3, wav, flac, ...)      |
| `-o, --output`   | `output.<type>`  | Onde salvar o resultado                       |
| `-f, --format`   | same as input    | Salvar em outro tipo, ex.: `ogg`, `wav`       |
| `-s, --source`   | `auto`           | De onde tirar a melodia: `vocals`, `instrumental` ou `auto` |
| `-m, --method`   | `transcribe`     | Como as notas são encontradas: `transcribe` (melhor) ou `pitch` (mais rápido, mais leve) |
| `-V, --voices`   | `chords`         | `chords` (com harmonia) ou `lead` (uma única linha de melodia) |
| `--transpose`    | `0`              | Muda o tom, em semitons (ex.: `5` para cima, `-5` para baixo) |
| `--bits`         | `8`              | Resolução do som, 1-8 (menor = mais áspero)   |
| `--rate`         | `22050`          | Taxa de amostragem em Hz (menor = mais retrô) |
| `--duty`         | `0.25`           | Timbre da onda quadrada (pulse wave), 0-1     |

## Se algo der errado

- **"ffmpeg not found"** - instale o ffmpeg (veja *Antes de começar*).
- **A primeira execução parece travada** - ela está baixando o modelo de IA;
  dê alguns minutos. Isso só acontece uma vez.
- **Não soa como a música** - tente `-s vocals` ou `-s instrumental` para
  escolher a parte certa, ou `-V lead` para apenas a melodia.

## Como funciona (leitura opcional)

1. Divide a música em partes (vocais, bateria, baixo e o restante).
2. Detecta as notas que estão realmente sendo tocadas na parte que você escolheu.
3. Reproduz essas notas com sons "chip" simples de 8-bit e salva o arquivo.

## Licença

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
