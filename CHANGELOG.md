# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## Unreleased

### Changed
- Melody extraction now isolates the sung vocal with Demucs and tracks its
  pitch with librosa's pYIN, instead of `L − R` cancellation plus
  autocorrelation on the full mix — the resulting ringtone is actually
  recognizable. Adds `demucs` and `librosa` dependencies (PyTorch, model
  downloaded on first run); branch `feat/demucs-melody`.
- Core behaviour is now monophonic melody synthesis instead of a raw
  bitcrusher: the input has its vocals removed (`L − R` centre cancellation),
  its leading pitch tracked by autocorrelation, and is replayed as a single
  square-wave voice in the style of old phone ringtones / game consoles
  (branch `feat/melody-synth`). New `--duty` and `--semitones/--no-semitones`
  flags; the now-irrelevant `--mono` flag was removed.

- Default output is now `output.<ext>` in the current directory and keeps the
  input's format by default; new `-f/--format` flag overrides the output
  format (e.g. `ogg`), while an explicit `-o` still wins (branch
  `feat/output-format`).

### Added
- Project scaffold: packaging (`pyproject.toml`), MIT license, ignore rules
  and changelog (branch `main`).
- DSP core `audio8bit/converter.py`: ffmpeg-based decoding of any audio
  format, bitcrusher pipeline (sample-rate decimation + bit-depth
  quantisation) and 8-bit unsigned PCM WAV output, with optional ffmpeg
  re-encoding to other containers (branch `feat/dsp-core`).
- Command-line interface `audio8bit` (`audio8bit/cli.py`) with `-i/--input`,
  `-o/--output`, `--bits`, `--rate`, `--mono` and `--version`, wired as a
  `console_scripts` entry point; exit codes 0/1/2 (branch `feat/cli`).
- Compact `README.md`: what it does, requirements, install, usage examples
  and a flag reference (branch `docs/readme`).
- Root `main.py` runner so the package can be used straight from a clone
  without installing (`python main.py ...`); README documents it
  (branch `feat/run-without-install`).
