#!/usr/bin/env python3
"""
Render a CFO narrative Markdown file under ``CFO Reports/`` to an executive-style PDF.

Uses the same pipeline as ``render_phase2_pdf.py``: pandoc → HTML with
``evaluation/executive_report_pdf.css`` → Chrome ``--print-to-pdf``.

Requires: ``pandoc`` on PATH; Google Chrome (default macOS path or ``CHROME_PATH``).

Usage (from project root)::

    python scripts/render_cfo_pdf.py
    python scripts/render_cfo_pdf.py --month 2026-04
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_CFO = ROOT / "CFO Reports"
CSS = ROOT / "evaluation" / "executive_report_pdf.css"

DEFAULT_CHROME_MACOS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


def _chrome_path() -> Path:
    import os

    for key in ("CHROME_PATH", "GOOGLE_CHROME", "PUPPETEER_EXECUTABLE_PATH"):
        p = os.environ.get(key)
        if p and Path(p).is_file():
            return Path(p)
    p = Path(DEFAULT_CHROME_MACOS)
    if p.is_file():
        return p
    raise FileNotFoundError(
        "Google Chrome not found. Set CHROME_PATH to your Chrome/Chromium binary."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Render CFO narrative Markdown to executive PDF.")
    ap.add_argument(
        "--month",
        default="2026-04",
        metavar="YYYY-MM",
        help="Month suffix for CFO_narrative_<month>.md (default: 2026-04)",
    )
    args = ap.parse_args()
    month = args.month.strip()
    md_in = REPORTS_CFO / f"CFO_narrative_{month}.md"
    pdf_out = REPORTS_CFO / f"CFO_narrative_{month}.pdf"

    if not md_in.is_file():
        print(f"Missing {md_in}", file=sys.stderr)
        sys.exit(1)
    if not CSS.is_file():
        print(f"Missing {CSS}", file=sys.stderr)
        sys.exit(1)

    chrome = _chrome_path()
    md_text = md_in.read_text(encoding="utf-8")

    REPORTS_CFO.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        md_path = tmpdir / "cfo.md"
        html_path = tmpdir / "cfo.html"
        md_path.write_text(md_text, encoding="utf-8")

        pandoc_cmd = [
            "pandoc",
            str(md_path),
            "-f",
            "markdown",
            "-t",
            "html5",
            "--standalone",
            "--embed-resources",
            f"--css={CSS}",
            "--toc",
            "--toc-depth=3",
            "--number-sections",
            "-o",
            str(html_path),
        ]
        r = subprocess.run(pandoc_cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            sys.exit(r.returncode)

        pdf_cmd = [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_out.resolve()}",
            f"file://{html_path.resolve()}",
        ]
        r2 = subprocess.run(pdf_cmd, capture_output=True, text=True)
        if r2.returncode != 0:
            print(r2.stderr or r2.stdout, file=sys.stderr)
            sys.exit(r2.returncode)

    print(f"Wrote {pdf_out}")


if __name__ == "__main__":
    main()
