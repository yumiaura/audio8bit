"""Command-line interface for audio8bit."""

import argparse
import sys

from audio8bit import version
from audio8bit.converter import (
    DEFAULT_BITS,
    DEFAULT_DUTY,
    DEFAULT_RATE,
    DEFAULT_TRANSPOSE,
    ConversionError,
    convert,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="audio8bit",
        description="Turn a song into an 8-bit chiptune arrangement: isolate "
                    "the sung melody (Demucs), extract its notes, snap them to "
                    "the song's beat, transpose into a new key and replay them "
                    "with a pulse lead, triangle bass and echo — like an 80s "
                    "game console.",
    )
    parser.add_argument(
        "-i", "--input", required=True,
        help="path to the input audio file (any format ffmpeg can read)",
    )
    parser.add_argument(
        "-o", "--output",
        help="output path (default: 'output.<ext>' using the input's format)",
    )
    parser.add_argument(
        "-f", "--format",
        help="output format/extension, e.g. ogg, mp3, wav "
             "(default: keep the input's format)",
    )
    parser.add_argument(
        "--transpose", type=int, default=DEFAULT_TRANSPOSE,
        help="shift the melody into another key by this many semitones, "
             f"negative allowed (default: +{DEFAULT_TRANSPOSE})",
    )
    parser.add_argument(
        "--bits", type=int, default=DEFAULT_BITS,
        help=f"bit depth to quantise to, 1-8 (default: {DEFAULT_BITS})",
    )
    parser.add_argument(
        "--rate", type=int, default=DEFAULT_RATE,
        help=f"output sample rate in Hz (default: {DEFAULT_RATE})",
    )
    parser.add_argument(
        "--duty", type=float, default=DEFAULT_DUTY,
        help=f"pulse-wave duty cycle, 0-1 (default: {DEFAULT_DUTY})",
    )
    parser.add_argument(
        "--version", action="version", version=f"audio8bit {version}",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output, quality_ok, report = convert(
            args.input,
            output_path=args.output,
            format=args.format,
            bits=args.bits,
            rate=args.rate,
            duty=args.duty,
            transpose=args.transpose,
        )
    except ConversionError as error:
        print(f"audio8bit: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    print("Quality report (anti-mush checks):")
    for line in report:
        print(f"  {line}")
    if not quality_ok:
        print(
            "audio8bit: warning: some quality checks failed - "
            "the result may not sound musical",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
