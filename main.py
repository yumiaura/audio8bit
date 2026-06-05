"""Run audio8bit straight from the source tree, without installing it.

    python main.py -i song.mp3 -o song_8bit.wav

The repository root is on sys.path when this file is executed, so the
``audio8bit`` package is importable as-is.
"""

import sys

from audio8bit.cli import main

if __name__ == "__main__":
    sys.exit(main())
