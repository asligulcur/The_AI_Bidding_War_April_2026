#!/usr/bin/env python3
"""
Collect the N most recent orchestrator **evidence session JSON** files per scenario for multi-seed variance.

**Input (only):** ``logs/evidence_log_*.json`` — one file per ``python orchestrator.py`` run, written by the
orchestrator. Metrics are derived by parsing each file's top-level fields and ``turns[]`` (``session_end``,
``award_contract``, etc.).

**Not used:** ``evaluation/test_cases.csv``, ``export_evaluation.py``, or any other harvest — you do **not**
need to re-run the full 11-scenario export.

Default: scenarios **4** and **8**; **N** most recent evidence files per scenario (by file mtime under ``logs/``).

Outputs:
  - ``evaluation/multi_seed_variance/runs.csv``
  - ``evaluation/multi_seed_variance/MULTI_SEED_VARIANCE_REPORT.md``

Usage::

    python scripts/collect_multi_seed_variance.py
    python scripts/collect_multi_seed_variance.py --runs 5 --scenarios 4,8
    python scripts/collect_multi_seed_variance.py --logs-dir logs
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGS_DIR = ROOT / "logs"
EVIDENCE_GLOB = "evidence_log_*.json"
OUT_DIR = ROOT / "evaluation" / "multi_seed_variance"
RUNS_CSV = OUT_DIR / "runs.csv"
REPORT_MD = OUT_DIR / "MULTI_SEED_VARIANCE_REPORT.md"


def _load_evidence(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "turns" not in data:
        return None
    return data


def _extract_run_row(ev: dict[str, Any], evidence_path: str) -> dict[str, Any]:
    sid = ev.get("scenario_id")
    turns: list[dict[str, Any]] = list(ev.get("turns") or [])
    hard = ev.get("hard_budget_ceiling")
    budget = ev.get("scenario_budget")

    contract_executed: bool | None = None
    last_success_award: dict[str, Any] | None = None
    human_declined = False
    guardrail_reject = False

    for t in turns:
        action = t.get("action")
        payload = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        if action == "session_end":
            contract_executed = bool(payload.get("contract_executed"))
        elif action == "award_contract":
            sr = str(payload.get("skill_result") or "")
            if sr.startswith("SUCCESS"):
                last_success_award = {
                    "vendor_name": payload.get("vendor_name"),
                    "price": payload.get("price"),
                }
            else:
                guardrail_reject = True
        elif action == "award_aborted":
            human_declined = True

    status = "SUCCESS" if contract_executed else "NO_AWARD"
    fp = last_success_award.get("price") if last_success_award and contract_executed else None
    wv = last_success_award.get("vendor_name") if last_success_award and contract_executed else ""

    # Final session outcome only — not "human said no once" before a later yes + executed contract.
    session_ended_no_contract = status == "NO_AWARD"

    at_ceiling = ""
    if fp is not None and hard is not None:
        try:
            at_ceiling = "Y" if float(fp) == float(hard) else "N"
        except (TypeError, ValueError):
            at_ceiling = ""

    detail = "walk_away_or_no_contract"
    if contract_executed:
        detail = "contract_executed"
    elif human_declined:
        detail = "human_veto_or_declined"
    elif guardrail_reject:
        detail = "guardrail_rejected_award"

    return {
        "evidence_file": evidence_path,
        "scenario_id": sid,
        "session_id": ev.get("session_id", ""),
        "started_at": ev.get("started_at", ""),
        "model": ev.get("model", ""),
        "hard_budget_ceiling": hard if hard is not None else "",
        "scenario_budget": budget if budget is not None else "",
        "Status": status,
        "Outcome_detail": detail,
        "Final_Award_Price": fp if fp is not None else "",
        "Winning_Vendor": wv if wv else "",
        "At_hard_ceiling": at_ceiling,
        "Session_ended_no_contract": "Y" if session_ended_no_contract else "N",
    }


def _gather_recent(
    scenario_ids: set[int],
    n_each: int,
    logs_dir: Path,
) -> list[tuple[Path, dict[str, Any]]]:
    """Return (path, ev) grouped by scenario, newest mtime first, capped at n_each per sid."""
    by_sid: dict[int, list[tuple[Path, float, dict[str, Any]]]] = {s: [] for s in scenario_ids}

    if not logs_dir.is_dir():
        print(f"collect_multi_seed_variance: logs directory not found: {logs_dir}", file=sys.stderr)
        return []

    for p in sorted(logs_dir.glob(EVIDENCE_GLOB)):
        ev = _load_evidence(p)
        if not ev:
            continue
        sid = ev.get("scenario_id")
        if sid not in scenario_ids:
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        by_sid[sid].append((p, mtime, ev))

    out: list[tuple[Path, dict[str, Any]]] = []
    for sid in sorted(scenario_ids):
        entries = sorted(by_sid[sid], key=lambda x: x[1], reverse=True)[:n_each]
        for path, _mtime, ev in entries:
            out.append((path, ev))
    return out


def _write_csv(rows: list[dict[str, Any]], runs_csv: Path) -> None:
    runs_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "evidence_file",
        "scenario_id",
        "session_id",
        "started_at",
        "model",
        "hard_budget_ceiling",
        "scenario_budget",
        "Status",
        "Outcome_detail",
        "Final_Award_Price",
        "Winning_Vendor",
        "At_hard_ceiling",
        "Session_ended_no_contract",
    ]
    with runs_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def _fmt_dist(counter: Counter) -> str:
    parts = [f"{k}: {v}" for k, v in sorted(counter.items(), key=lambda x: (str(x[0]), x[1]))]
    return "; ".join(parts) if parts else "—"


def _write_report(
    rows: list[dict[str, Any]],
    scenario_ids: list[int],
    n_requested: int,
    report_md: Path,
    runs_csv: Path,
) -> None:
    lines: list[str] = [
        "# Multi-seed variance — outcome distributions",
        "",
        "**Data source:** ``logs/evidence_log_*.json`` only (orchestrator session evidence). **No** ``export_evaluation.py``,",
        "**no** ``test_cases.csv`` — partial re-runs (e.g. scenarios **4** and **8** only) are sufficient.",
        "It supports **Phase 2 instructor feedback** (multi-seed / stochasticity): report **distributions**,",
        "not single point estimates, for **borderline** budget scenarios. The course example named",
        "scenarios **4** and **5** at the **\\$15,000** ceiling; this project uses **4** (near-ceiling tradeoffs)",
        "and **8** (exact **\\$15,000** bind in the pinned harvest) as the robust pair — see project memo.",
        "",
        "## Parameters",
        "",
        f"- **Scenarios included:** {', '.join(map(str, scenario_ids))}",
    ]
    if set(scenario_ids) == {4, 8}:
        lines.append(
            "- **Why 4 and 8:** Phase 2 feedback calls for **borderline** budget stress and outcome **distributions**, not a single run. **4** is the project’s near-**\\$15,000** analysis case (realistic ceiling tradeoffs); **8** is the **exact** **\\$15,000** bind from the pinned harvest, so we sample variance under both **near-ceiling** and **hard** ceiling pressure.",
        )
    lines.extend(
        [
        f"- **Runs per scenario:** up to **{n_requested}** most recent **evidence JSON** files (mtime under ``logs/``).",
        "- **Source files:** ``logs/evidence_log_*.json`` — same artifacts the orchestrator writes each run; **not** the evaluation CSV harvest.",
        "",
        "## Mapping to instructor feedback",
        "",
        "| Feedback theme | How this report addresses it |",
        "|----------------|------------------------------|",
        "| Outcome stability under LLM stochasticity | Multiple independent runs per scenario; frequency tables below. |",
        "| *Distributions* vs point values | Aggregated counts and price buckets — not one harvested row. |",
        "| Borderline / ceiling-relevant stress | Scenarios **4** and **8** (project analysis; legacy **5** not required). |",
        "",
        "## Run table (CSV mirror)",
        "",
        f"Full table: **[``{runs_csv.relative_to(ROOT)}``]({runs_csv.name})**.",
        "",
        "``runs.csv`` column **Session_ended_no_contract** is **Y** only when the session ended **without** an executed contract (**Status** = NO_AWARD), not when a human declined an *earlier* proposal before approving a later one.",
        "",
        "| # | Scenario | Started (UTC) | Model | Status | Final \\$ | Winner | At \\$15k ceiling | No contract |",
        "|---|----------|---------------|-------|--------|-----------|--------|-------------------|-------------|",
        ]
    )

    for i, r in enumerate(rows, 1):
        fp = r.get("Final_Award_Price")
        try:
            fp_s = f"${float(fp):,.2f}" if fp != "" and fp is not None else "—"
        except (TypeError, ValueError):
            fp_s = "—"
        nc = r.get("Session_ended_no_contract", "")
        lines.append(
            f"| {i} | {r.get('scenario_id')} | {str(r.get('started_at', ''))[:19]} | {r.get('model', '')} "
            f"| {r.get('Status')} | {fp_s} | {r.get('Winning_Vendor') or '—'} | {r.get('At_hard_ceiling') or '—'} | {nc} |"
        )

    lines.extend(["", "## Outcome distributions", ""])

    for sid in scenario_ids:
        subset = [r for r in rows if r.get("scenario_id") == sid]
        lines.append(f"### Scenario {sid}")
        lines.append("")
        if not subset:
            lines.append("*No evidence files found for this scenario.*")
            lines.append("")
            continue

        st_counts = Counter(str(r.get("Status")) for r in subset)
        lines.append("- **Status (deal outcome):** " + _fmt_dist(st_counts))
        detail_counts = Counter(str(r.get("Outcome_detail")) for r in subset)
        lines.append("- **Outcome_detail:** " + _fmt_dist(detail_counts))

        success_prices: list[float] = []
        for r in subset:
            if r.get("Status") == "SUCCESS" and r.get("Final_Award_Price") != "":
                try:
                    success_prices.append(float(r["Final_Award_Price"]))
                except (TypeError, ValueError):
                    pass
        if success_prices:
            price_counter: Counter[float] = Counter(success_prices)
            lines.append("- **Final award price (SUCCESS only):** " + _fmt_dist(price_counter))
            at_15 = sum(1 for p in success_prices if abs(p - 15000.0) < 0.01)
            lines.append(
                f"- **SUCCESS runs at \\$15,000.00 (exact):** {at_15} / {len(success_prices)} in this sample."
            )
        else:
            lines.append("- **Final award price:** no SUCCESS runs in this sample.")
        lines.append("")

    lines.extend(
        [
            "## Interpretation (reliability claims)",
            "",
            "Use these frequencies when arguing **whether outcomes are stable** under repeated sampling.",
            "Spread in **Status** or **Final_Award_Price** under SUCCESS shows negotiation outcomes",
            "are **not** deterministic at the LLM layer; **guardrails** and **human gates** remain as in code.",
            "",
            "*Regenerate:* ``python scripts/collect_multi_seed_variance.py``",
            "",
        ]
    )

    report_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Collect multi-seed variance from orchestrator evidence JSON only (logs/evidence_log_*.json). "
            "Does not read evaluation CSVs or require export_evaluation.py."
        )
    )
    p.add_argument(
        "--scenarios",
        default="4,8",
        help="Comma-separated scenario ids (default: 4,8).",
    )
    p.add_argument("--runs", type=int, default=5, help="Most recent N runs per scenario (default: 5).")
    p.add_argument(
        "--logs-dir",
        type=Path,
        default=DEFAULT_LOGS_DIR,
        help=f"Directory containing evidence session JSON (default: {DEFAULT_LOGS_DIR})",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Output directory (default: {ROOT / 'evaluation' / 'multi_seed_variance'})",
    )
    args = p.parse_args()

    out_dir = args.output_dir or (ROOT / "evaluation" / "multi_seed_variance")
    runs_csv = out_dir / "runs.csv"
    report_md = out_dir / "MULTI_SEED_VARIANCE_REPORT.md"
    logs_dir = args.logs_dir.resolve()

    scenario_ids = {int(x.strip()) for x in args.scenarios.split(",") if x.strip()}
    if not scenario_ids:
        print("collect_multi_seed_variance: no scenario ids", file=sys.stderr)
        sys.exit(1)

    pairs = _gather_recent(scenario_ids, args.runs, logs_dir)
    rows: list[dict[str, Any]] = []
    for path, ev in pairs:
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        row = _extract_run_row(ev, str(rel))
        rows.append(row)

    _write_csv(rows, runs_csv)
    _write_report(rows, sorted(scenario_ids), args.runs, report_md, runs_csv)

    print(f"Wrote {runs_csv} ({len(rows)} row(s)) from {logs_dir}/{EVIDENCE_GLOB}")
    print(f"Wrote {report_md}")


if __name__ == "__main__":
    main()
