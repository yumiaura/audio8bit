# audio8bit

Transforme uma música em um arranjo chiptune de 8 bits — o vocal cantado **ou**
o instrumental, com sua harmonia — do jeito que um console de videogame dos anos
80 a tocaria, direto da linha de comando.

[English](https://github.com/yumiaura/audio8bit/blob/main/README.md) | [Español](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ES.md) | **[Português](https://github.com/yumiaura/audio8bit/blob/main/docs/README_PT.md)** | [Français](https://github.com/yumiaura/audio8bit/blob/main/docs/README_FR.md) | [Deutsch](https://github.com/yumiaura/audio8bit/blob/main/docs/README_DE.md) | [Italiano](https://github.com/yumiaura/audio8bit/blob/main/docs/README_IT.md) | [Русский](https://github.com/yumiaura/audio8bit/blob/main/docs/README_RU.md) | [中文](https://github.com/yumiaura/audio8bit/blob/main/docs/README_ZH.md) | [日本語](https://github.com/yumiaura/audio8bit/blob/main/docs/README_JA.md) | [हिन्दी](https://github.com/yumiaura/audio8bit/blob/main/docs/README_HI.md) | [한국어](https://github.com/yumiaura/audio8bit/blob/main/docs/README_KR.md)

Ele mantém a melodia e a rearranja para vozes de chip:

1. **Separação de fontes** — o [Demucs](https://github.com/adefossez/demucs) (um
   modelo neural de separação de fontes) divide a música em faixas (stems),
   executado de forma determinística para que a mesma entrada sempre produza o
   mesmo resultado. A melodia é extraída dos **vocais** cantados ou, no caso de
   um instrumental, da **lead** de acompanhamento (com bateria e baixo
   removidos); `--source auto` usa o vocal quando a música realmente tem um e o
   instrumental caso contrário.
2. **Detecção de notas** (`--method`, padrão `transcribe`) — um modelo de
   transcrição polifônica ([basic-pitch](https://github.com/spotify/basic-pitch))
   transforma o stem em notas reais. `--voices chords` (padrão) toca todas as
   notas, mantendo a harmonia e o baixo; `--voices lead` segue uma única linha
   melódica através dos acordes (um caminho de Viterbi, e não a ingênua linha
   superior que pula entre a lead e o acompanhamento). Isso se mantém coeso em
   acordes e instrumentais, onde o rastreamento de tom quadro a quadro
   simplesmente pula entre as vozes e soa aleatório. `--method pitch` usa, em vez
   disso, o pYIN do librosa alinhado à grade de batidas da música (monofônico,
   mais leve, sem TensorFlow).
3. **Musicalização** — um `--transpose` opcional muda a tonalidade. A `lead` é
   deslocada em oitavas para um registro de toque de celular; `chords` mantém os
   tons transcritos para que a harmonia permaneça intacta. As notas transcritas
   mantêm seu próprio tempo natural em vez de serem alinhadas a uma grade.
4. **Síntese de chip** — cada nota é uma voz de pulso com banda limitada (os
   caminhos `lead` e `pitch` adicionam vibrato/decaimento, e o `pitch` adiciona
   um baixo de onda triangular e um eco sincronizado ao andamento); livre de
   aliasing por construção (apenas os harmônicos abaixo de Nyquist são somados).
   `chords` escalona cada voz pela sua intensidade transcrita para obter dinâmica
   e nivela a mixagem com um limitador suave, de modo que acordes densos não
   soterrem as notas isoladas.
5. **Saída de 8 bits + relatório de qualidade** — quantizada para PCM de 8 bits,
   gravada como WAV ou recodificada para o formato de sua escolha, depois
   avaliada: heurísticas de "papa" melódica para uma única linha, ou verificações
   em nível de áudio (silêncio, aliasing, clipping) para acordes — de modo que um
   resultado ruim seja sinalizado objetivamente em vez de descoberto de ouvido.

> **Atenção:** o método padrão `transcribe` traz o basic-pitch (TensorFlow) e o
> Demucs traz o PyTorch — ambas instalações grandes — e o Demucs baixa seu
> modelo (~80 MB) na primeira execução. A separação mais a transcrição levam
> alguns minutos por faixa na CPU. É isso que torna a melodia de fato
> reconhecível. Tudo roda localmente.

## Requisitos

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (inclui `ffmpeg` e `ffprobe`) no seu `PATH`

## Instalação

```bash
pip install audio8bit
```

Ou execute diretamente a partir de um clone (instale as dependências primeiro: `pip install numpy demucs librosa basic-pitch`):

```bash
python main.py -i song.mp3
```

## Uso

```bash
audio8bit -i song.mp3                      # -> output.mp3, acordes completos (mantém o formato de entrada)
audio8bit -i song.mp3 -V lead              # uma única linha melódica em vez de acordes
audio8bit -i track.mp3 -s instrumental     # segue o instrumental, não os vocais
audio8bit -i song.mp3 -m pitch             # método pYIN mais leve (sem TensorFlow)
audio8bit -i song.mp3 -f ogg               # -> output.ogg
audio8bit -i song.mp3 --transpose 5        # 5 semitons acima
audio8bit -i song.mp3 --duty 0.5 --rate 11025
```

| Flag             | Default          | Descrição                                    |
| ---------------- | ---------------- | -------------------------------------------- |
| `-i, --input`    | — (obrigatório)  | Áudio de entrada (qualquer formato que o ffmpeg leia) |
| `-o, --output`   | `output.<ext>`   | Caminho de saída (sobrepõe `-f`)             |
| `-f, --format`   | formato da entrada | Formato/extensão de saída, ex.: `ogg`      |
| `-s, --source`   | `auto`           | Melodia a seguir: `vocals`, `instrumental`, `auto` |
| `-m, --method`   | `transcribe`     | Detecção de notas: `transcribe` (polifônico) ou `pitch` (pYIN) |
| `-V, --voices`   | `chords`         | Saída do transcribe: `chords` (harmonia) ou `lead` (uma linha) |
| `--transpose`    | `0`              | Mudança de tonalidade em semitons (negativos permitidos) |
| `--bits`         | `8`              | Profundidade de bits para quantizar (1–8)    |
| `--rate`         | `22050`          | Taxa de amostragem de saída em Hz            |
| `--duty`         | `0.25`           | Ciclo de trabalho da onda de pulso (0–1)     |

Códigos de saída: `0` sucesso, `1` erro de conversão, `2` argumentos inválidos.
Toda execução termina com um relatório de qualidade; verificações que falham
imprimem um aviso no stderr.

## License

Licença MIT
