"""Command-line interface for audio8bit."""

from __future__ import annotations

import argparse
import sys

from audio8bit import version
from audio8bit.converter import (
    DEFAULT_BITS,
    DEFAULT_DUTY,
    DEFAULT_METHOD,
    DEFAULT_RATE,
    DEFAULT_SOURCE,
    DEFAULT_TRANSPOSE,
    DEFAULT_VOICES,
    METHOD_CHOICES,
    SOURCE_CHOICES,
    VOICES_CHOICES,
    ConversionError,
    convert,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audio8bit",
        description=(
            "Turn a song into an 8-bit chiptune arrangement: take a "
            "melody (the sung vocal or the instrumental lead) with "
            "Demucs, extract its notes, snap them to the song's beat, "
            "transpose into a new key and replay them with a pulse "
            "lead, triangle bass and echo — like an 80s game console."
        ),
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="path to the input audio file (any format ffmpeg can read)",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="output path (default: 'output.' using the input's format)",
    )

    parser.add_argument(
        "-f",
        "--format",
        help="output format/extension, e.g. ogg, mp3, wav "
        "(default: keep the input's format)",
    )

    parser.add_argument(
        "-s",
        "--source",
        choices=SOURCE_CHOICES,
        default=DEFAULT_SOURCE,
        help=(
            "which melody to follow: 'vocals' (the sung line), "
            "'instrumental' (the backing lead, drums and bass removed), or "
            f"'auto' (default: {DEFAULT_SOURCE})"
        ),
    )

    parser.add_argument(
        "-m",
        "--method",
        choices=METHOD_CHOICES,
        default=DEFAULT_METHOD,
        help=(
            "how to find the notes: 'transcribe' (polyphonic note model; best "
            "for chords/instrumentals) or 'pitch' (lighter pYIN tracker snapped "
            f"to the beat) (default: {DEFAULT_METHOD})"
        ),
    )

    parser.add_argument(
        "-V",
        "--voices",
        choices=VOICES_CHOICES,
        default=DEFAULT_VOICES,
        help=(
            "with --method transcribe: 'chords' plays every note "
            "(harmony and bass kept) or 'lead' plays a single melody line "
            f"(default: {DEFAULT_VOICES})"
        ),
    )

    parser.add_argument(
        "--transpose",
        type=int,
        default=DEFAULT_TRANSPOSE,
        help=(
            "shift the melody into another key by this many semitones, "
            f"negative allowed (default: +{DEFAULT_TRANSPOSE})"
        ),
    )

    parser.add_argument(
        "--bits",
        type=int,
        default=DEFAULT_BITS,
        help=f"bit depth to quantise to, 1-8 (default: {DEFAULT_BITS})",
    )

    parser.add_argument(
        "--rate",
        type=int,
        default=DEFAULT_RATE,
        help=f"output sample rate in Hz (default: {DEFAULT_RATE})",
    )

    parser.add_argument(
        "--duty",
        type=float,
        default=DEFAULT_DUTY,
        help=f"pulse-wave duty cycle, 0-1 (default: {DEFAULT_DUTY})",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="do not read or write cached Demucs stems",
    )

    parser.add_argument(
        "--cache-dir",
        help=(
            "directory for cached stems "
            "(default: ~/.cache/audio8bit, or AUDIO8BIT_CACHE_DIR)"
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"audio8bit {version}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
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
            source=args.source,
            method=args.method,
            voices=args.voices,
            use_cache=not args.no_cache,
            cache_dir=args.cache_dir,
        )
    except ConversionError as error:
        print(f"audio8bit: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {output}")
    print("Quality report (anti-mush checks):")

    for line in report:
        print(f" {line}")

    if not quality_ok:
        print(
            "audio8bit: warning: some quality checks failed - "
            "the result may not sound musical",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
