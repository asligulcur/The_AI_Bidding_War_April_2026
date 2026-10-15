#!/usr/bin/env python3
"""
Compatibility entrypoint for the evaluation export pipeline.

Equivalent to::

    python -m scripts.export_evaluation
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.export_evaluation.pipeline import main

if __name__ == "__main__":
    main()
