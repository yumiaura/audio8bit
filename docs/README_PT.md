## audio8bit - transforme qualquer musica em chiptune de 8 bits

[![CI](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml/badge.svg)](https://github.com/yumiaura/audio8bit/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/audio8bit.svg)](https://pypi.org/project/audio8bit/)
[![Downloads](https://img.shields.io/pepy/dt/audio8bit?label=pypi%20%7C%20downloads&color=brightgreen)](https://pypi.org/project/audio8bit/)
[![Python](https://img.shields.io/pypi/pyversions/audio8bit.svg)](https://pypi.org/project/audio8bit/)

Uma ferramenta de linha de comando que transforma qualquer musica em musica de 8 bits, no estilo de videogame. Ela encontra a melodia (a partir dos vocais ou dos instrumentos) e a reproduz com sons retro de "chiptune", como um console de jogos antigo. Tudo roda localmente.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | **[Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md)** | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

### Requisitos

- **Python 3.9 ou superior**
- **ffmpeg** no seu `PATH` (ele inclui `ffmpeg` e `ffprobe`). Instale com
  `sudo apt install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS).

### Instalacao

```bash
pip install audio8bit
```

Ou a partir do GitHub:

```bash
pip install git+https://github.com/yumiaura/audio8bit.git
```

> **A primeira execucao e lenta:** ela baixa um pequeno modelo de IA (cerca de 80 MB) e pode levar
> alguns minutos. Isso e normal; as execucoes seguintes sao mais rapidas.

### Uso

```bash
# Converte uma musica (detecta automaticamente vocal ou instrumental)
audio8bit -i song.mp3

# Apenas a melodia principal, sem acordes
audio8bit -i song.mp3 -V lead

# Pega a melodia do canto ou dos instrumentos
audio8bit -i song.mp3 -s vocals
audio8bit -i song.mp3 -s instrumental

# Salva em um formato diferente
audio8bit -i song.mp3 -f ogg

# Toca 5 semitons acima
audio8bit -i song.mp3 --transpose 5

# Mostra a ajuda e a versao
audio8bit --help
audio8bit --version
```

### Opcoes de Linha de Comando

- `-i, --input` - arquivo de audio de entrada, obrigatorio (qualquer formato que o ffmpeg consiga ler)
- `-o, --output` - caminho de saida (padrao: `output.<ext>`)
- `-f, --format` - formato de saida, por exemplo `ogg`, `wav` (padrao: o mesmo da entrada)
- `-s, --source` - fonte da melodia: `vocals`, `instrumental`, `auto` (padrao: `auto`)
- `-m, --method` - deteccao de notas: `transcribe` ou `pitch` (padrao: `transcribe`)
- `-V, --voices` - `chords` (com harmonia) ou `lead` (linha unica) (padrao: `chords`)
- `--transpose` - mudanca de tom em semitons (padrao: `0`)
- `--bits` - profundidade de bits, 1-8, quanto menor mais granulado (padrao: `8`)
- `--rate` - taxa de amostragem em Hz, quanto menor mais retro (padrao: `22050`)
- `--duty` - ciclo de trabalho da onda de pulso, 0-1 (padrao: `0.25`)
- `--version` - mostra a versao

Codigos de saida: `0` sucesso, `1` erro de conversao, `2` argumentos invalidos.

### Recursos

- Funciona com musicas **vocais** e **instrumentais** - escolhe a fonte da melodia automaticamente.
- **Transcricao polifonica** (basic-pitch) mantem os acordes e o baixo, ou os reduz a uma unica linha principal.
- Separacao de fontes com **Demucs**, deterministica, de modo que a mesma entrada sempre produz o mesmo resultado.
- Sintese chiptune sem aliasing com dinamica de volume e um limitador suave.
- Transposicao de tom e profundidade de bits, taxa de amostragem e tom de pulso ajustaveis.
- Saida PCM de 8 bits em WAV, ou qualquer formato que o ffmpeg consiga gravar.
- Um relatorio de qualidade apos cada execucao, e tudo roda na sua propria maquina.

### Licenca

[Noncommercial](https://github.com/yumiaura/audio8bit/blob/main/LICENSE)
