# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added
- Project scaffold: packaging (`pyproject.toml`), MIT license, ignore rules
  and changelog (branch `main`).
- DSP core `audio8bit/converter.py`: ffmpeg-based decoding of any audio
  format, bitcrusher pipeline (sample-rate decimation + bit-depth
  quantisation) and 8-bit unsigned PCM WAV output, with optional ffmpeg
  re-encoding to other containers (branch `feat/dsp-core`).
