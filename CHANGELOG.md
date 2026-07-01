# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- New `--voices band` and `--voices nes` modes: arrange the song as a full chip
  band instead of one pulse voice playing a chord. Both use a pulse lead, a
  triangle bass and a seeded noise drum channel (kick / snare / hi-hat, with
  velocity) from the drums stem. `band` plays loose with a sustained harmony;
  `nes` arpeggiates the harmony NES-style, adds vibrato to sustained lead
  notes, and snaps the notes and drums to the song's beat grid. Output stays
  deterministic.
- Musicality package for `band`/`nes`:
  - Key detection (Krumhansl-Schmuckler) with off-key notes snapped to the
    scale, plus transcription cleanup (litter dropped, legato bridged); the
    report shows e.g. `key: E major (64 notes snapped)`.
  - An arranger instead of transcription replay: the accompaniment is the
    detected diatonic chord progression played as clean voiced triads
    (sustained for `band`, arpeggiated for `nes`), the bass plays chord roots
    (held / root-fifth quarters), and `nes` loops the dominant per-bar drum
    pattern. The stem-tracked bass remains the fallback.
  - Mix: the harmony bed is level-trimmed and ducks under the lead
    (sidechain-style) so the melody always reads on top; the lead slides
    (portamento) between adjacent legato notes.
  - Production: a tempo-synced echo on the melodic bus (rhythm stays dry),
    beat accents on the `nes` lead/drums, loudness normalisation to a fixed
    RMS, and seeded TPDF dither before the bit quantiser.

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
