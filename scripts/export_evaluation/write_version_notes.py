#!/usr/bin/env python3
"""
Write ``evaluation/version_notes.md`` after a successful harvest export.

Run automatically from ``export_evaluation.py`` / ``pipeline.py``. Safe to run standalone
after ``harvest_evidence.py`` has written ``evaluation/test_cases.csv``.

Reads ``ANTHROPIC_MODEL`` from ``.env`` only (never copies API keys). Attempts
``git rev-parse --short HEAD`` when the project root is a git checkout.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT / "evaluation"
TEST_CASES_CSV = EVAL_DIR / "test_cases.csv"
VERSION_NOTES_MD = EVAL_DIR / "version_notes.md"
ENV_PATH = ROOT / ".env"


def _strip_cell(val: str | None) -> str:
    if val is None:
        return ""
    s = val.strip().strip("'").strip('"').strip()
    return s


def _parse_sid(raw: str) -> int | None:
    s = _strip_cell(raw)
    if not s or not s.isdigit():
        return None
    return int(s)


def load_anthropic_model() -> str:
    """Return ANTHROPIC_MODEL value from .env, or N/A."""
    if not ENV_PATH.is_file():
        return "N/A"
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("ANTHROPIC_MODEL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "N/A"


def git_short_hash() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "N/A"


def read_test_cases_evidence() -> tuple[list[int], dict[int, str]]:
    """Scenario IDs sorted, and map sid -> evidence_or_citation path."""
    if not TEST_CASES_CSV.is_file():
        return [], {}
    rows: list[tuple[int, str]] = []
    with TEST_CASES_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = _parse_sid(row.get("Scenario_ID", "") or "")
            if sid is None:
                continue
            ev = _strip_cell(row.get("evidence_or_citation", "") or "")
            rows.append((sid, ev))
    rows.sort(key=lambda x: x[0])
    by_id = {sid: ev for sid, ev in rows}
    return [sid for sid, _ in rows], by_id


def main() -> None:
    argv = sys.argv[1:]
    allow_fallback = "--allow-fallback" in argv or "-F" in argv

    today = date.today().isoformat()
    model = load_anthropic_model()
    githash = git_short_hash()
    scenario_ids, evidence_by_id = read_test_cases_evidence()

    if not scenario_ids:
        print(f"write_version_notes: no rows in {TEST_CASES_CSV}", file=sys.stderr)
        sys.exit(1)

    lo, hi = min(scenario_ids), max(scenario_ids)
    scenario_range = f"{lo}–{hi}" if len(scenario_ids) == hi - lo + 1 else ", ".join(str(s) for s in scenario_ids)

    harvest_mode = (
        "**allow-fallback** (older log if newest invalid) — see `harvest_evidence.py`"
        if allow_fallback
        else "**strict** (newest log per scenario only)"
    )

    evidence_rows = "\n".join(
        f"| {sid} | `{evidence_by_id.get(sid, 'N/A')}` |"
        for sid in scenario_ids
    )

    git_line = (
        f"`{githash}`"
        if githash != "N/A"
        else "`N/A` (not a git checkout or git unavailable)"
    )

    md = f"""# Evaluation harvest — version pin

**Auto-generated** by `scripts/export_evaluation/write_version_notes.py` when you run `python scripts/export_evaluation.py`. Regenerate by re-running the export; do not rely on stale pins after new logs.

| Field | Value |
|--------|--------|
| **Export date** | {today} |
| **`ANTHROPIC_MODEL`** | `{model}` (from project `.env`) |
| **Scenarios in `test_cases.csv`** | `{scenario_range}` ({len(scenario_ids)} row(s)) |
| **Harvest command** | `python scripts/export_evaluation.py` |
| **Harvest log selection** | {harvest_mode} |
| **`config/scenarios.json`** | As evaluated at export; scenario **`mode`** (`standard` / `malicious`) overrides **`BUYER_TYPE`** when using `orchestrator.py --id` (see project `README.md`). |
| **Git commit** | {git_line} |

## Evidence files (from `test_cases.csv`)

| Scenario_ID | evidence_or_citation |
|-------------|----------------------|
{evidence_rows}

**Authoritative paths:** `evaluation/test_cases.csv` column **`evidence_or_citation`**. Re-run orchestrator scenarios and export again if you replace logs.

## Notes

- With **`orchestrator.py --id`**, per-scenario **`mode`** in **`config/scenarios.json`** overrides **`BUYER_TYPE`** for that run.
- **Model id:** If **`ANTHROPIC_MODEL`** is **`claude-sonnet-4-6`**, that reflects **Anthropic**’s plan to deprecate the earlier Sonnet 4 snapshot (**`claude-sonnet-4-20250514`**) used in Phase 2 **in June 2026**. See **`README.md`** → Known limitations and **`evaluation/failure_log.md`**.
"""

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    VERSION_NOTES_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {VERSION_NOTES_MD}")


if __name__ == "__main__":
    main()
