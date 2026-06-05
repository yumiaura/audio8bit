"""Command-line interface for audio8bit."""

import argparse
import sys

from audio8bit import version
from audio8bit.converter import (
    DEFAULT_BITS,
    DEFAULT_DUTY,
    DEFAULT_RATE,
    ConversionError,
    convert,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="audio8bit",
        description="Turn a song into a monophonic 8-bit melody: strip the "
                    "vocals, follow the leading pitch and replay it as a single "
                    "square-wave voice, like an old phone ringtone or game "
                    "console.",
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
        "--bits", type=int, default=DEFAULT_BITS,
        help=f"bit depth to quantise to, 1-8 (default: {DEFAULT_BITS})",
    )
    parser.add_argument(
        "--rate", type=int, default=DEFAULT_RATE,
        help=f"output sample rate in Hz (default: {DEFAULT_RATE})",
    )
    parser.add_argument(
        "--duty", type=float, default=DEFAULT_DUTY,
        help=f"square-wave duty cycle, 0-1 (default: {DEFAULT_DUTY})",
    )
    parser.add_argument(
        "--semitones", action=argparse.BooleanOptionalAction, default=True,
        help="snap the melody to musical semitones (default: on)",
    )
    parser.add_argument(
        "--version", action="version", version=f"audio8bit {version}",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = convert(
            args.input,
            output_path=args.output,
            format=args.format,
            bits=args.bits,
            rate=args.rate,
            duty=args.duty,
            semitones=args.semitones,
        )
    except ConversionError as error:
        print(f"audio8bit: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
