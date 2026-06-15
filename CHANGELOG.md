# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## Unreleased

### Removed
- All README status badges (CI, PyPI, Python, license, theme, offline) in every
  language. The README's License section is now just the standard one-line
  pointer to the `LICENSE` file (branch `docs/no-badges`). The CI workflow
  itself is kept; only its badge is gone.

### Added
- CI workflow `.github/workflows/ci.yml`: builds the package and smoke-tests the
  CLI on every push to `main` and on pull requests, so the build-status badge is
  meaningful (branch `ci/build-badges`).
- Live status badges in the README (and all translations): CI build status and
  PyPI version, alongside the existing Python/license/theme badges (branch
  `ci/build-badges`).

### Changed
- Relicensed from MIT to the standard noncommercial **PolyForm Noncommercial
  License 1.0.0** (in `LICENSE`): free for noncommercial use, while commercial
  use requires a separate paid license from the author. The README just states
  "free for noncommercial use — see LICENSE for details" (the commercial terms
  live in the license file, not the README); the license badge reads
  `noncommercial`, `pyproject` points its license at the `LICENSE` file, and all
  10 translations match (branches `chore/noncommercial-license`,
  `chore/standard-license`).

## 0.0.0 - 2026-06-15

### Changed
- Set the package version to `0.0.0` for the first PyPI release (branch
  `chore/pypi-publish`).
- Rewrote `README.md` to be beginner-friendly: plain-language sections (What it
  does / Before you start / Install / Use it / All options / If something goes
  wrong), the deep DSP terms moved out of the main flow, and a short status-badge
  row added (license, Python, theme, offline). All 10 translations were
  re-synced to match (branch `docs/simplify-readme`).
- Re-synced the `docs/README_<LANG>.md` translations (all 10 languages) with the
  current README: the source/method/voices flags, the transcription + chords
  pipeline and the updated defaults are now reflected in every language (branch
  `docs/i18n-refresh`).
- Chord rendering now has dynamics and a smooth limiter (branch
  `feat/chord-dynamics`): each voice is scaled by its transcribed loudness
  (with a floor so soft notes stay audible) instead of every note being equally
  loud, and the summed mix is levelled by an envelope-following limiter instead
  of a global peak-normalise — so a dense chord no longer buries the single
  notes around it. The limiter shapes a low-frequency gain curve (no
  waveshaping), so it stays alias-free.

### Added
- PyPI publish workflow `.github/workflows/publish.yml`: builds and uploads the
  package to pypi.org when a GitHub Release is published (or on manual
  dispatch), using Trusted Publishing/OIDC so no API token is stored in the
  repo (branch `chore/pypi-publish`).
- Polyphonic chord rendering, `-V/--voices {chords,lead}` (default `chords`):
  with `--method transcribe` the output now plays every transcribed note, so
  the harmony and bass are kept instead of a single bare line — much closer to
  the original. `--voices lead` keeps the old single-melody-line behaviour.
  Chords keep their transcribed pitches (only a uniform transpose is applied, so
  the harmony is not scrambled) and are checked with audio-level validation
  (silence/aliasing/clipping) rather than the single-line "mush" heuristics
  (branch `feat/polyphonic-chords`).
- Polyphonic note transcription as the default melody method, `-m/--method
  {transcribe,pitch}` (default `transcribe`). It runs the basic-pitch model on
  the chosen stem and keeps the top line (a skyline melody), so chord-heavy and
  instrumental material no longer comes out as random-sounding notes the way
  frame-by-frame pYIN tracking did. The transcribed notes keep their own
  natural timing instead of being snapped to a beat grid. `--method pitch`
  retains the old pYIN tracker (lighter, no TensorFlow). Adds the `basic-pitch`
  dependency (branch `feat/note-transcription`).
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
- `--transpose` now defaults to `0` (original key) instead of `+3`; a key shift
  is opt-in (branch `feat/polyphonic-chords`).
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
