#!/usr/bin/env python3
"""
Orchestrate evaluation export steps (subprocess to sibling modules in this package).

All arguments are forwarded to ``harvest_evidence.py`` only (e.g. ``--allow-fallback``).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG = Path(__file__).resolve().parent


def _run(script_name: str, extra: list[str] | None = None) -> int:
    cmd = [sys.executable, str(PKG / script_name)]
    if extra:
        cmd.extend(extra)
    return subprocess.run(cmd, cwd=ROOT).returncode


def main() -> None:
    harvest_args = sys.argv[1:]
    code = _run("harvest_evidence.py", harvest_args)
    if code != 0:
        sys.exit(code)
    code = _run("fill_evaluation_rubric_section3.py")
    if code != 0:
        sys.exit(code)
    code = _run("generate_report_table.py")
    if code != 0:
        sys.exit(code)
    code = _run("generate_failure_log.py")
    if code != 0:
        sys.exit(code)
    code = _run("sync_final_evaluation_report.py")
    if code != 0:
        sys.exit(code)
    code = _run("write_version_notes.py", harvest_args)
    sys.exit(code)


if __name__ == "__main__":
    main()
