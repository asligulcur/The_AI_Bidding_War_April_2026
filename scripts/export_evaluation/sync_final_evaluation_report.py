#!/usr/bin/env python3
"""
Write ``evaluation/FINAL_EVALUATION_REPORT.md`` in full on each export.

The file is **generated only** — do not edit it by hand. All content is derived from
the latest harvest: ``test_cases.csv``, ``evaluation_rubric.md`` §3 table,
``evaluation/failure_log.md`` (embedded as a **Failure log** section), and log files under ``logs/`` referenced by
``evidence_or_citation``. The executive cover page is **not** duplicated here; it is injected for HTML/PDF by
``render_final_evaluation_pdf.py`` (``--include-before-body``).

Run after ``fill_evaluation_rubric_section3.py`` and ``generate_failure_log.py``.
Invoked from ``export_evaluation.py``.

Usage::

    python scripts/export_evaluation/sync_final_evaluation_report.py
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT / "evaluation"
RUBRIC_MD = EVAL_DIR / "evaluation_rubric.md"
TEST_CASES = EVAL_DIR / "test_cases.csv"
FAILURE_LOG_MD = EVAL_DIR / "failure_log.md"
REPORT_MD = EVAL_DIR / "FINAL_EVALUATION_REPORT.md"

# Verbatim tails: log-backed scenarios (baseline, red-team, squeeze, compromised).
VERBATIM_SCENARIO_IDS: tuple[int, ...] = (1, 2, 3, 6)

RUBRIC_TABLE_RE = re.compile(
    r"<!-- RUBRIC_SECTION3_TABLE_START -->\s*\n(.*?)\n<!-- RUBRIC_SECTION3_TABLE_END -->",
    re.DOTALL,
)

GENERATED_BANNER = """<!--
  GENERATED FILE — do not edit by hand.
  Regenerate: python scripts/export_evaluation.py
  Source data: evaluation/test_cases.csv, evaluation/evaluation_rubric.md §3,
  evaluation/failure_log.md, logs/ (via evidence_or_citation).
-->
"""


def _strip_cell(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip().strip("'").strip('"').strip()


def _parse_sid(raw: str) -> int | None:
    s = raw.strip().strip("'\"")
    if not s or not s.isdigit():
        return None
    return int(s)


def extract_section3_table_from_rubric(text: str) -> str | None:
    m = RUBRIC_TABLE_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _inject_scenario_title_column(
    table_body: str, tc_rows: list[tuple[int, dict[str, str]]]
) -> str:
    """Insert `Scenario_Title` from CSV after `Scenario ID` for scanability."""
    sid_to_title = {
        sid: _strip_cell(r.get("Scenario_Title") or "") for sid, r in tc_rows
    }
    lines_out: list[str] = []
    for ln in table_body.splitlines():
        stripped = ln.strip()
        if not stripped.startswith("|"):
            lines_out.append(ln)
            continue
        inner = [c.strip() for c in stripped.strip("|").split("|")]
        if not inner:
            lines_out.append(ln)
            continue
        if all(re.match(r"^[-:]+$", c or "-") for c in inner):
            new_inner = [inner[0], "---", *inner[1:]]
            lines_out.append("| " + " | ".join(new_inner) + " |")
            continue
        if inner[0].strip() == "Scenario ID":
            new_inner = [inner[0], "Scenario (title)", *inner[1:]]
            lines_out.append("| " + " | ".join(new_inner) + " |")
            continue
        sid_str = inner[0].strip()
        if sid_str.isdigit():
            sid = int(sid_str)
            title = sid_to_title.get(sid, "")
            title = title.replace("|", " ")
            if len(title) > 72:
                title = title[:69].rstrip() + "…"
            new_inner = [inner[0], title or "—", *inner[1:]]
            lines_out.append("| " + " | ".join(new_inner) + " |")
            continue
        lines_out.append(ln)
    return "\n".join(lines_out)


def _parse_money_amount(s: str) -> float | None:
    """Parse a leading $12,500 or 12500 from a cell."""
    t = _strip_cell(s)
    if not t or t.upper() == "N/A":
        return None
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)", t.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _load_test_case_rows() -> list[tuple[int, dict[str, str]]]:
    rows: list[tuple[int, dict[str, str]]] = []
    if not TEST_CASES.is_file():
        return rows
    with TEST_CASES.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = _parse_sid(row.get("Scenario_ID", "") or "")
            if sid is not None:
                rows.append((sid, row))
    rows.sort(key=lambda x: x[0])
    return rows


def _negotiation_column_counts(table_body: str) -> tuple[int, int, int]:
    """Count pass / fail / partial in the §3 Negotiation column."""
    lines = [ln for ln in table_body.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return 0, 0, 0
    header_cells = [c.strip() for c in lines[0].split("|")]
    try:
        neg_i = next(i for i, c in enumerate(header_cells) if "Negotiation" in c)
    except StopIteration:
        neg_i = 5

    p = f = par = 0
    for ln in lines[2:]:
        if re.match(r"^\|\s*-+", ln.strip()):
            continue
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) <= neg_i + 1:
            continue
        cell = cells[neg_i].lower()
        if "partial" in cell:
            par += 1
        elif "fail" in cell:
            f += 1
        elif "pass" in cell:
            p += 1
    return p, f, par


def _governance_y_count(table_body: str) -> int:
    lines = [ln for ln in table_body.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return 0
    header_cells = [c.strip() for c in lines[0].split("|")]
    try:
        gov_i = next(i for i, c in enumerate(header_cells) if "Governance" in c)
    except StopIteration:
        gov_i = 4
    n = 0
    for ln in lines[2:]:
        if re.match(r"^\|\s*-+", ln.strip()):
            continue
        cells = [c.strip() for c in ln.split("|")]
        if len(cells) <= gov_i + 1:
            continue
        if cells[gov_i].upper().startswith("Y"):
            n += 1
    return n


@dataclass(frozen=True)
class HarvestMetrics:
    success_ids: list[int]
    no_award_ids: list[int]
    headroom_sum: float
    max_success_award: float | None


def _harvest_metrics(rows: list[tuple[int, dict[str, str]]]) -> HarvestMetrics:
    success_ids: list[int] = []
    no_award_ids: list[int] = []
    headroom_sum = 0.0
    max_success_award: float | None = None

    for sid, row in rows:
        st = _strip_cell(row.get("Status"))
        if st == "SUCCESS":
            success_ids.append(sid)
            amt = _parse_money_amount(row.get("Final_Award_Price") or "")
            if amt is not None:
                max_success_award = amt if max_success_award is None else max(max_success_award, amt)
            sav = _parse_money_amount(row.get("Savings_Vs_Buyer_Budget") or "")
            if sav is not None:
                headroom_sum += sav
        elif st == "NO_AWARD":
            no_award_ids.append(sid)

    return HarvestMetrics(
        success_ids=success_ids,
        no_award_ids=no_award_ids,
        headroom_sum=headroom_sum,
        max_success_award=max_success_award,
    )


def build_harvest_snapshot() -> str:
    if not TEST_CASES.is_file():
        return "*(`test_cases.csv` not found.)*\n"

    rows = _load_test_case_rows()
    lines = [
        "## Harvest snapshot — savings, rounds, feasibility {#harvest-snapshot}",
        "",
        "From **`evaluation/test_cases.csv`** (same harvest as §3).",
        "",
        "| ID | `Status` | Final award | Savings vs buyer budget | Savings vs winner R1 | Feasible band | Rounds |",
        "|----|----------|-------------|-------------------------|----------------------|---------------|--------|",
    ]
    for sid, row in rows:
        st = _strip_cell(row.get("Status"))
        price = _strip_cell(row.get("Final_Award_Price"))
        sav_b = _strip_cell(row.get("Savings_Vs_Buyer_Budget"))
        sav_r = _strip_cell(row.get("Savings_Vs_Winner_Round1"))
        band = _strip_cell(row.get("Final_Price_In_Feasible_Band"))
        rnd = _strip_cell(row.get("Negotiation_Rounds_Completed"))
        if st == "SUCCESS" and price:
            fa = price
        else:
            fa = "—"
        if not sav_b:
            sav_b = "—"
        if not sav_r:
            sav_r = "—"
        if not band:
            band = "N/A"
        lines.append(
            f"| {sid} | {st} | {fa} | {sav_b} | {sav_r} | {band} | {rnd or '—'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _failure_log_embed_body(raw_full: str) -> str:
    """Drop only the # Failure log title; keep full body (executive framing, Phase 2 vs 3, FL sections)."""
    raw = raw_full.strip()
    if raw.startswith("# Failure log"):
        raw = raw[len("# Failure log") :].lstrip()
    if raw.startswith("**Harvest:**") or raw.startswith("**This log**") or raw.startswith("This appendix records") or raw.startswith("**Role (rubric §4):**") or raw.startswith("**What this is:**"):
        return raw.strip() + "\n"
    snap = raw.find("**Snapshot")
    for marker in (
        "### For executives: two different questions",
        "### How to read this log",
        "### LLM model: previous default → current, and why",
        "### Model and iteration context",
    ):
        idx = raw.find(marker)
        if idx != -1 and (snap == -1 or idx < snap):
            return raw[idx:].strip() + "\n"
    if snap != -1:
        return raw[snap:].strip() + "\n"
    return raw + "\n"


def build_failure_log_section(today: str) -> str:
    if not FAILURE_LOG_MD.is_file():
        return (
            f"## Failure log ({today}) {{#failure-log}}\n\n"
            "*(`evaluation/failure_log.md` not found — run `generate_failure_log.py` first.)*\n"
        )

    raw = FAILURE_LOG_MD.read_text(encoding="utf-8")
    body = _failure_log_embed_body(raw)

    return (
        f"## Failure log ({today}) {{#failure-log}}\n\n"
        "Embedded from **`evaluation/failure_log.md`** (same harvest as **`evaluation/test_cases.csv`**). "
        "Refresh: **`python scripts/export_evaluation.py`**.\n\n"
        + body
    )


def _is_verbatim_keep_line(ln: str) -> bool:
    s = ln.strip()
    if not s:
        return False
    if s.startswith("==="):
        return True
    if "[award_contract]" in ln:
        return True
    if "[HUMAN APPROVAL" in ln:
        return True
    if "[FINALIZE]" in ln:
        return True
    if "AWARD_JSON" in ln:
        return True
    if "System hard award ceiling" in ln:
        return True
    return False


def _dedupe_consecutive(lines: list[str]) -> list[str]:
    out: list[str] = []
    prev: str | None = None
    for ln in lines:
        if ln == prev:
            continue
        out.append(ln)
        prev = ln
    return out


def _dedupe_global_first(lines: list[str]) -> list[str]:
    """Drop later repeats of the same line (log tails often repeat guardrail text)."""
    seen: set[str] = set()
    out: list[str] = []
    for ln in lines:
        if ln in seen:
            continue
        seen.add(ln)
        out.append(ln)
    return out


def extract_log_tail_excerpt(log_text: str, *, max_keep: int = 14) -> str:
    lines = log_text.splitlines()
    end_idx: int | None = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("=== END session_id="):
            end_idx = i
            break
    if end_idx is None:
        return "*No `=== END session_id=` line found in log.*"

    kept: list[str] = []
    scanned = 0
    for i in range(end_idx, -1, -1):
        scanned += 1
        if scanned > 600:
            break
        ln = lines[i].rstrip()
        if _is_verbatim_keep_line(ln):
            kept.append(ln)
        if len(kept) >= max_keep:
            break
    kept.reverse()
    kept = _dedupe_consecutive(kept)
    kept = _dedupe_global_first(kept)
    return "\n".join(kept) if kept else "*No matching technical lines near session end.*"


def _row_for_sid(rows: list[tuple[int, dict[str, str]]], sid: int) -> dict[str, str] | None:
    for s, row in rows:
        if s == sid:
            return row
    return None


def build_verbatim_excerpts(today: str) -> str:
    """Log tails only — no grader prose; data from ``test_cases.csv`` + ``logs/``."""
    lines_out: list[str] = [
        "### Verbatim log excerpts {#verbatim-log-excerpts}",
        "",
        f"Technical tails from **`logs/`** for scenarios {', '.join(map(str, VERBATIM_SCENARIO_IDS))}, "
        "selected by **`evidence_or_citation`** in **`evaluation/test_cases.csv`**. "
        "Each excerpt walks backward from `=== END session_id=` and keeps award / guardrail / finalize "
        "landmarks; consecutive and repeated identical lines are collapsed for readability.",
        "",
    ]
    tc_rows = _load_test_case_rows()
    for sid in VERBATIM_SCENARIO_IDS:
        row = _row_for_sid(tc_rows, sid)
        if row is None:
            lines_out.append(f"#### Scenario {sid} — *(missing in test_cases.csv)*\n")
            continue

        title = _strip_cell(row.get("Scenario_Title"))
        st = _strip_cell(row.get("Status"))
        ab = _strip_cell(row.get("actual_behavior"))
        ev = _strip_cell(row.get("evidence_or_citation"))
        if not title:
            title = f"Scenario {sid}"
        lines_out.append(f"#### Scenario {sid} — {title} (`{st}`)")
        lines_out.append("")
        if ab:
            lines_out.append(f"**Harvest:** {ab}")
        else:
            lines_out.append(f"**Harvest:** `Status` = `{st}`.")
        if ev:
            lines_out.append(f"**Log:** `{ev}`")
        lines_out.append("")

        if not ev:
            lines_out.append("*No log path in `evidence_or_citation`.*")
            lines_out.append("")
            continue

        log_path = ROOT / ev
        if not log_path.is_file():
            lines_out.append(f"*Log file not found: `{ev}`*")
            lines_out.append("")
            continue

        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        excerpt = extract_log_tail_excerpt(log_text)
        lines_out.append("```")
        lines_out.extend(excerpt.split("\n"))
        lines_out.append("```")
        lines_out.append("")

    return "\n".join(lines_out).rstrip() + "\n"


def build_evidence_paths_table(rows: list[tuple[int, dict[str, str]]]) -> str:
    lines = [
        "### Evidence log paths {#evidence-paths}",
        "",
        "| Scenario_ID | `evidence_or_citation` |",
        "|-------------|--------------------------|",
    ]
    for sid, row in rows:
        ev = _strip_cell(row.get("evidence_or_citation")) or "—"
        lines.append(f"| {sid} | `{ev}` |")
    lines.append("")
    return "\n".join(lines)


def build_full_report(today: str) -> str:
    tc_rows = _load_test_case_rows()

    table_body = ""
    if RUBRIC_MD.is_file():
        rubric_text = RUBRIC_MD.read_text(encoding="utf-8")
        table_body = extract_section3_table_from_rubric(rubric_text) or ""
    if not table_body:
        table_body = "*(`evaluation_rubric.md` §3 table not found.)*\n"

    table_body = table_body.replace(
        "| Baseline expected (§2) |",
        "| Baseline expected (§2.3) |",
        1,
    )
    table_body = _inject_scenario_title_column(table_body, tc_rows)

    np, nf, npar = _negotiation_column_counts(table_body)
    gov_n = _governance_y_count(table_body)
    hm = _harvest_metrics(tc_rows)

    success_ids = hm.success_ids
    no_award_ids = hm.no_award_ids
    headroom = hm.headroom_sum
    max_aw = hm.max_success_award
    nsc = len(tc_rows)

    headroom_s = f"${headroom:,.0f}" if headroom == int(headroom) else f"${headroom:,.2f}"
    max_aw_s = f"${max_aw:,.2f}" if max_aw is not None else "—"
    id_hi = tc_rows[-1][0] if tc_rows else 0

    parts: list[str] = [
        GENERATED_BANNER.rstrip(),
        "",
        f"# Supplementary Evaluation Report — The AI Bidding War {{#supplementary-evaluation-report}}",
        "",
        f"*Generated {today} by `scripts/export_evaluation/sync_final_evaluation_report.py`. "
        "Baselines and scoring definitions: **`evaluation/evaluation_rubric.md`**.*",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| **Export date** | " + today + " |",
        "| **Harvest inputs** | `evaluation/test_cases.csv`, `logs/` (per `evidence_or_citation`) |",
        "| **Rubric §3** | `evaluation/evaluation_rubric.md` |",
        "| **Pin** | `evaluation/version_notes.md` |",
        "",
        "## Executive summary {#executive-summary}",
        "",
        "Metrics below are **computed from** the §3 table and **`test_cases.csv`** for this export.",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Scenarios | {nsc} (IDs 1–{id_hi}) |" if nsc else "| Scenarios | 0 |",
        f"| Governance pass (§3 column) | {gov_n} / {nsc} |",
        f"| Negotiation (§3): pass / fail / partial | {np} / {nf} / {npar} |",
        f"| `Status` = `SUCCESS` | {len(success_ids)} — {', '.join(map(str, success_ids)) or '—'} |",
        f"| `Status` = `NO_AWARD` | {len(no_award_ids)} — {', '.join(map(str, no_award_ids)) or '—'} |",
        f"| Sum of `Savings_Vs_Buyer_Budget` (`SUCCESS` only) | {headroom_s} |",
        f"| Max `Final_Award_Price` (`SUCCESS` only) | {max_aw_s} (hard ceiling $15,000) |",
        "",
        "**Savings total:** The figure in the row above is the **sum of `Savings_Vs_Buyer_Budget`** "
        "from **`evaluation/test_cases.csv`** taken **only for rows with `Status` = `SUCCESS`**. "
        "Rows with `NO_AWARD` (or any non-success status) **do not** contribute; it is **not** a sum over all scenarios.",
        "",
        build_harvest_snapshot(),
        "",
        "## Results vs baseline {#results-vs-baseline}",
        "",
        f"From **`evaluation/evaluation_rubric.md`** §3 (`RUBRIC_SECTION3_TABLE_*`), filled for **{today}**.",
        "",
        f"#### Results vs baseline ({today} harvest)",
        "",
        table_body,
        "",
        build_evidence_paths_table(tc_rows),
        build_verbatim_excerpts(today),
        "---",
        "",
        build_failure_log_section(today),
        "---",
        "",
        "*End of report (generated).*",
        "",
    ]
    return "\n".join(parts)


def main() -> None:
    today = date.today().isoformat()
    body = build_full_report(today)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(body, encoding="utf-8")
    print(f"Wrote {REPORT_MD} (full generated report for {today})")


if __name__ == "__main__":
    main()
