#!/usr/bin/env python3
"""Render ``docs/Phase 3/CANVAS_SUBMISSION_PACKET.md`` to executive HTML and PDF.

Pipeline: pandoc (Markdown → standalone HTML + embedded CSS + TOC) → optional
Chrome headless ``--print-to-pdf``.

Requires: ``pandoc`` on PATH. PDF step requires Google Chrome (macOS default path
or ``CHROME_PATH``).

Usage (from project root)::

    python scripts/render_canvas_submission_packet.py
    python scripts/render_canvas_submission_packet.py --html-only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "Phase 3" / "CANVAS_SUBMISSION_PACKET.md"
CSS_PATH = ROOT / "docs" / "Phase 3" / "canvas_packet_executive.css"
OUT_HTML = ROOT / "docs" / "Phase 3" / "CANVAS_SUBMISSION_PACKET_executive.html"
OUT_PDF = ROOT / "docs" / "Phase 3" / "CANVAS_SUBMISSION_PACKET_executive.pdf"

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
    ap = argparse.ArgumentParser(
        description="Render Canvas submission packet Markdown to executive HTML/PDF."
    )
    ap.add_argument(
        "--html-only",
        action="store_true",
        help="Skip Chrome PDF (write HTML only).",
    )
    args = ap.parse_args()

    if not MD_PATH.is_file():
        print(f"Missing {MD_PATH}", file=sys.stderr)
        sys.exit(1)
    if not CSS_PATH.is_file():
        print(f"Missing {CSS_PATH}", file=sys.stderr)
        sys.exit(1)

    md_text = MD_PATH.read_text(encoding="utf-8")
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        md_tmp = tmpdir / "packet.md"
        html_tmp = tmpdir / "packet.html"
        md_tmp.write_text(md_text, encoding="utf-8")

        pandoc_cmd = [
            "pandoc",
            str(md_tmp),
            "-f",
            "markdown",
            "-t",
            "html5",
            "--standalone",
            "--embed-resources",
            f"--css={CSS_PATH}",
            "--toc",
            "--toc-depth=2",
            "-o",
            str(html_tmp),
        ]
        r = subprocess.run(pandoc_cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            sys.exit(r.returncode)

        OUT_HTML.write_text(html_tmp.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Wrote {OUT_HTML}")

        if args.html_only:
            return

        try:
            chrome = _chrome_path()
        except FileNotFoundError as e:
            print(f"{e} Skipping PDF; HTML is at {OUT_HTML}", file=sys.stderr)
            sys.exit(0)

        pdf_cmd = [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={OUT_PDF.resolve()}",
            f"file://{OUT_HTML.resolve()}",
        ]
        r2 = subprocess.run(pdf_cmd, capture_output=True, text=True)
        if r2.returncode != 0:
            print(r2.stderr or r2.stdout, file=sys.stderr)
            sys.exit(r2.returncode)

    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
