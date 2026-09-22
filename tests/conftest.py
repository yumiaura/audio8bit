"""Make the repository root importable so the suite runs from a plain clone.

The tests only need NumPy (and the stdlib); Demucs, basic-pitch and librosa are
imported lazily by the code under test, so nothing here pulls them in.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
