# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- New `--voices band` mode: arranges the song as a full chip band instead of one
  pulse voice playing a chord. It keeps the full polyphony on a pulse lead and a
  second pulse harmony (hollow-square duty), adds a triangle bass pitch-tracked
  from the Demucs bass stem, and a seeded noise drum channel (kick + snare/hi-hat)
  from the drums stem - so it sounds like several instruments with a real rhythm
  section. Output stays deterministic.

## 0.0.2 - 2026-06-30

### Added

- On-disk caching of the separated Demucs stems: re-running the same track
  reuses the stems and skips the slow separation step. Keyed by the input file
  hash plus the Demucs model/seed/shift settings; stored under
  `~/.cache/audio8bit` (override with `--cache-dir` or `$AUDIO8BIT_CACHE_DIR`).
  New `--no-cache` and `--cache-dir` flags.

## 0.0.1 - 2026-06-25

### Changed

- Reformatted the README and all 10 translations: an H2 title with a tagline, a
  badge row, the language bar, and `###` sections (Requirements / Installation /
  Usage / Command Line Options / Features / License).

## 0.0.0 - 2026-06-15

First release. audio8bit turns a song into an 8-bit chiptune arrangement of its
melody, from the command line. Licensed under the PolyForm Noncommercial
License (free for noncommercial use; commercial use requires a separate license
from the author).

### Added

- Convert any audio file ffmpeg can read into an 8-bit chiptune track; write it
  as WAV or re-encode to another format (`-f/--format`), with a printed quality
  report after each run.
- Melody source `-s/--source {auto,vocals,instrumental}`: take the tune from the
  sung vocal or from the backing instrumental (drums and bass removed with
  Demucs); `auto` detects which fits.
- Note finding `-m/--method {transcribe,pitch}` (default `transcribe`):
  polyphonic note transcription with basic-pitch, or a lighter pYIN pitch
  tracker.
- Voicing `-V/--voices {chords,lead}` (default `chords`): play the full harmony,
  or reduce it to a single melody line.
- Chip synthesis: band-limited (alias-free) pulse voices with loudness dynamics
  and a smooth limiter; `--transpose`, `--bits`, `--rate` and `--duty` controls.
- `python main.py` runner to use the tool from a clone without installing.
- CI workflow and a PyPI publish workflow (Trusted Publishing).
- README translated into 10 languages under `docs/`.
