#!/usr/bin/env python3
"""
Build evaluation/FINAL_RESULTS_TABLE.md from evaluation/evaluation_results.csv + config/scenarios.json.

The **Phase 3 eval** column is the ``Result`` field on each **Phase_3_Evaluation** row — not ``SUCCESS`` /
``NO_AWARD`` from ``test_cases.csv``. See the note block in the generated Markdown.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT / "evaluation"
EVAL_CSV = EVAL_DIR / "evaluation_results.csv"
SCENARIOS_JSON = ROOT / "config" / "scenarios.json"
OUTPUT_MD = EVAL_DIR / "FINAL_RESULTS_TABLE.md"

PRICE_IN_SUCCESS_RE = re.compile(
    r"\[Guardrail\]\s*SUCCESS:.*?(\$[\d,]+\.?\d*)", re.IGNORECASE | re.DOTALL
)
PRICE_FALLBACK_RE = re.compile(r"\$([\d,]+\.?\d*)")


def load_scenarios() -> dict[int, dict[str, str]]:
    if not SCENARIOS_JSON.is_file():
        return {}
    data = json.loads(SCENARIOS_JSON.read_text(encoding="utf-8"))
    out: dict[int, dict[str, str]] = {}
    for s in data.get("scenarios", []):
        sid = int(s["id"])
        out[sid] = {
            "name": str(s.get("name", "")),
            "description": str(s.get("description", "")),
        }
    return out


def simplify_justification(raw: str) -> str:
    """
    Map Technical_Justification to a short governance line per project rules.
    Order: ERROR → Human Gatekeeper → SUCCESS → fallback.
    Supports harvest format: [Advisor Audit]: ... | [Guardrail]: ...
    """
    if not raw or not raw.strip():
        return "— (no justification recorded)"
    t = raw.strip()
    low = t.lower()

    # Prefer explicit [Guardrail]: segment from harvest_evidence.py
    gr_part = t
    if "| [guardrail]:" in low:
        idx = low.rfind("| [guardrail]:")
        gr_part = t[idx + len("| [Guardrail]:") :].strip()

    gr_low = gr_part.lower()

    if "[guardrail] error" in gr_low or (
        "error:" in gr_low and "budget violation" in gr_low
    ):
        return "Blocked: Budget violation detected by guardrail."

    if "human gatekeeper" in low:
        return "HITL: Human rejected award (Quality/Strategic grounds)."

    if "[guardrail] success" in gr_low or (
        "success:" in gr_low and "contract awarded" in gr_low
    ):
        m = PRICE_IN_SUCCESS_RE.search(gr_part)
        if not m:
            m = re.search(
                r"SUCCESS:.*?for\s*(\$[\d,]+\.?\d*)", gr_part, re.IGNORECASE | re.DOTALL
            )
        if m:
            price = m.group(1).strip()
            if not price.startswith("$"):
                price = "$" + price
        else:
            pf = PRICE_FALLBACK_RE.search(gr_part)
            price = pf.group(0) if pf else "$—"
        return f"Success: {price} target met; Vendor selected."

    return t[:200] + ("…" if len(t) > 200 else "")


def md_cell(s: str) -> str:
    """Escape pipes for Markdown table cells."""
    return s.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = load_scenarios()
    rows_out: list[tuple[str, str, str, str]] = []

    if not EVAL_CSV.is_file():
        OUTPUT_MD.write_text(
            "# Final results\n\n*(evaluation_results.csv not found.)*\n",
            encoding="utf-8",
        )
        print(f"Wrote {OUTPUT_MD} (empty — missing {EVAL_CSV.name})")
        return

    with EVAL_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Criteria", "").strip() != "Phase_3_Evaluation":
                continue
            try:
                sid = int(row.get("Scenario_ID", "").strip())
            except ValueError:
                continue
            meta = scenarios.get(sid, {})
            title = meta.get("name", f"Scenario {sid}")
            goal = meta.get("description", "—")
            phase3_eval = row.get("Result", "").strip() or "—"
            gov = simplify_justification(row.get("Technical_Justification", ""))

            scenario_label = f"{sid}. {title}"
            rows_out.append(
                (scenario_label, goal, phase3_eval, gov)
            )

    # Stable sort by leading number
    rows_out.sort(key=lambda r: int(r[0].split(".", 1)[0]))

    lines = [
        "# Final results table",
        "",
        "Generated from `evaluation/evaluation_results.csv` and `config/scenarios.json`.",
        "",
        "**How to read this table**",
        "",
        "- **`Phase 3 eval`** — The **`Result`** field from the **`Phase_3_Evaluation`** row in "
        "`evaluation_results.csv` (one row per scenario). Same row’s **`Result_Meaning`** column states the "
        "rule in plain language. This is **not** the same column as **`Status`** "
        "in `test_cases.csv` (`SUCCESS` / `NO_AWARD` / …). **`PASS`** follows the harvest rule there, not "
        "“deal closed.” **`PASS` is normal** when **`Status`** is **`NO_AWARD`** after a human veto.",
        "- **`Governance role`** — One-line summary built from the same row’s **`Technical_Justification`**: "
        "prefer guardrail outcome (blocked / success with price), else human gatekeeper rejection, else a "
        "short clip of the Strategic Audit text. Logic: `simplify_justification()` in `scripts/export_evaluation/generate_report_table.py`.",
        "- **Deal outcome and rubric scoring** — **`Status`**, savings, and veto fields live in "
        "**`test_cases.csv`**. **Governance vs negotiation** pass compared to the §2 baseline is tabulated "
        "in **`evaluation_rubric.md` §3** (“Results vs baseline”). Do not infer deal outcome or negotiation "
        "pass from **`Phase 3 eval`** alone — use **`Status`** and §3.",
        "",
        "| Scenario | Goal | Phase 3 eval | Governance role |",
        "| --- | --- | --- | --- |",
    ]
    for scenario, goal, phase3_eval, gov in rows_out:
        lines.append(
            f"| {md_cell(scenario)} | {md_cell(goal)} | {md_cell(phase3_eval)} | {md_cell(gov)} |"
        )

    if not rows_out:
        lines.append("")
        lines.append("*No Phase_3_Evaluation rows found in evaluation/evaluation_results.csv.*")

    lines.append("")
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD} ({len(rows_out)} row(s))")


if __name__ == "__main__":
    main()
