# audio8bit

Transforme uma música em um arranjo chiptune de 8 bits de sua melodia cantada — do
jeito que um console de videogame dos anos 80 a tocaria — direto da linha de comando.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | **[Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md)** | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Ele remove as palavras, mantém a melodia e a rearranja para vozes de chip:

1. **Isolamento vocal** — o [Demucs](https://github.com/adefossez/demucs) (um modelo
   neural de separação de fontes) extrai a melodia cantada isoladamente.
2. **Rastreamento de tom** — o pYIN do librosa acompanha a frequência fundamental da
   voz isolada ao longo do tempo.
3. **Extração de notas** — o rastreamento de tom é dividido em notas discretas com
   histerese: vibrato e deslizes permanecem dentro de uma nota, lacunas de vocalização
   são preenchidas, erros de oitava são revertidos e a oscilação de ornamentos é
   absorvida.
4. **Musicalização** — os inícios das notas se alinham à própria grade de batidas da
   música, a melodia é deslocada para um registro de toque de celular e transposta para
   uma tonalidade diferente (`--transpose`, padrão +3 semitons).
5. **Síntese de chip** — uma voz principal de pulso com banda limitada com vibrato e
   envelopes de decaimento, um baixo de onda triangular uma oitava abaixo nas batidas e
   um eco sincronizado ao andamento; livre de aliasing por construção (apenas harmônicos
   abaixo de Nyquist são somados).
6. **Saída de 8 bits + relatório de qualidade** — quantizada para PCM de 8 bits, gravada
   como WAV ou recodificada para o formato de sua escolha, depois avaliada por heurísticas
   de "papa" (densidade de notas, fragmentação, trinados, extensão, clipping), de modo que
   um resultado ruim seja sinalizado objetivamente em vez de descoberto de ouvido.

> **Atenção:** o Demucs traz o PyTorch (uma instalação grande) e baixa seu modelo
> (~80 MB) na primeira execução, e a separação leva alguns minutos por faixa na
> CPU. É isso que torna a melodia de fato reconhecível. Tudo roda
> localmente.

## Requisitos

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (inclui `ffmpeg` e `ffprobe`) no seu `PATH`

## Instalação

```bash
pip install audio8bit
```

Ou execute diretamente a partir de um clone (instale as dependências primeiro: `pip install numpy demucs librosa`):

```bash
python main.py -i song.mp3
```

## Uso

```bash
audio8bit -i song.mp3                 # -> output.mp3 (keeps the input format)
audio8bit -i song.mp3 -f ogg          # -> output.ogg
audio8bit -i song.mp3 -o ring.wav     # explicit output path
audio8bit -i song.mp3 --transpose -5  # darker key, 5 semitones down
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Descrição                                    |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (obrigatório)  | Áudio de entrada (qualquer formato que o ffmpeg leia) |
| `-o, --output`   | `output.<ext>`   | Caminho de saída (sobrepõe `-f`)             |
| `-f, --format`   | formato da entrada | Formato/extensão de saída, ex.: `ogg`      |
| `--transpose`    | `3`              | Mudança de tonalidade em semitons (negativos permitidos) |
| `--bits`         | `8`              | Profundidade de bits para quantizar (1–8)    |
| `--rate`         | `22050`          | Taxa de amostragem de saída em Hz            |
| `--duty`         | `0.25`           | Ciclo de trabalho da onda de pulso (0–1)     |

Códigos de saída: `0` sucesso, `1` erro de conversão, `2` argumentos inválidos. Toda execução
termina com um relatório de qualidade; verificações que falham imprimem um aviso no stderr.

## License

MIT
