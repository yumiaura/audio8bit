# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added
- `-s/--source {auto,vocals,instrumental}` (default `auto`): the melody can now
  be taken from the **instrumental lead** (Demucs' `other` stem, drums and bass
  removed), not only the sung vocal — so purely instrumental tracks work. `auto`
  picks the vocal when the song actually has one and the instrumental
  otherwise. Demucs separation now returns all stems and a small loudness test
  drives the choice (branch `feat/instrumental-source`).

### Fixed
- The melody is far more recognizable and now reproducible (branch
  `fix/recognizable-melody`):
  - Demucs separation is deterministic (`shifts=0` plus a fixed torch seed);
    previously its random shift-and-average trick changed the melody on every
    run of the same file.
  - pYIN is restricted to the singing range (98–880 Hz instead of 65–2093 Hz),
    which cut octave-tracking errors from ~12% to ~5% on the test track.
  - A `collapse_octaves` step clamps the few remaining octave outliers to
    within an octave of the melody centre, halving the pitch span (34 → 16
    semitones) with only a few percent fidelity cost.
  - The "sound coverage" quality check no longer flags a sparse melody as mush
    (a song with long instrumental stretches is legitimately sparse); it only
    flags a near-empty result or a non-stop drone now.

### Added
- Translated READMEs in `docs/README_<LANG>.md` for 10 languages (Spanish,
  Portuguese, French, German, Italian, Russian, Chinese, Japanese, Hindi,
  Korean) with a language navigation bar at the top of every README, matching
  the `wachawo/checkcrontab` layout (branch `docs/i18n`).
- Local Claude Code project notes in `CLAUDE.md`, kept out of git via
  `.gitignore` (branch `chore/claude-md`).

### Changed
- The output is now a full chiptune arrangement instead of bare beeps: notes
  are extracted with hysteresis (vibrato/scoops stay inside one note, voicing
  gaps bridged, octave errors folded, A-B-A ornament flicker absorbed), onsets
  snap to the song's own beat grid, the melody is shifted into a ringtone
  register, and the sound is a pulse lead with vibrato and decay envelopes
  plus a triangle bass on the beats and a tempo-synced echo. Defaults moved
  to `--rate 22050` and `--duty 0.25`; branch `feat/chiptune-arranger`.

### Added
- `--transpose N` flag (default +3): plays the melody in a different key,
  negative values allowed (branch `feat/chiptune-arranger`).
- Anti-mush quality validation: every conversion ends with a report scoring
  note density, fragmentation, trills, pitch range, coverage, aliasing and
  clipping, with a stderr warning when a check fails (branch
  `feat/chiptune-arranger`).

### Fixed
- Synthesis no longer screeches: the raw `sign()` square aliased badly at low
  sample rates. Replaced with discrete note segmentation (snap to semitones,
  group same-pitch frames, drop flicker) and band-limited pulse synthesis
  (only harmonics below Nyquist) with per-note envelopes — clean retro beeps
  instead of noise. Default `--rate` raised to 11025; `--semitones` flag
  removed (snapping is always on); branch `fix/anti-alias-notes`.

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
