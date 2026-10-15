#!/usr/bin/env python3
"""
Aggregate evidence logs for a calendar month (or all time) and generate a CFO-facing
Markdown narrative via Anthropic Claude. System prompt: agents/cfo_narrative/agent.md

This is an **offline batch** reporting job—not invoked by orchestrator.py (unlike buyer/vendor agents).

Usage:
  python scripts/cfo_monthly_report.py --month 2026-03
  python scripts/cfo_monthly_report.py --all

Requires ANTHROPIC_API_KEY and optional ANTHROPIC_MODEL in .env.

**Source of truth:** ``logs/evidence_log_*.json`` only (plus ``config/scenarios.json`` for scenario names)—not ``scenario_*.log`` files.

Progress is printed to stderr before the API call; generation often takes **60–120 seconds**
for many sessions (not frozen). Optional: ``CFO_REPORT_API_TIMEOUT`` (seconds, default 180).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"
SCENARIOS_PATH = ROOT / "config" / "scenarios.json"
CFO_AGENT_PATH = ROOT / "agents" / "cfo_narrative" / "agent.md"
REPORTS_DIR = ROOT / "CFO Reports"
DEFAULT_MODEL = "claude-sonnet-4-6"

STRATEGIC_SUMMARY_RE = re.compile(
    r"###\s*Strategic Audit Summary\s*\n(.*?)(?=\n###\s|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def load_scenarios() -> dict[int, dict[str, Any]]:
    if not SCENARIOS_PATH.is_file():
        return {}
    cfg = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    return {int(s["id"]): s for s in cfg.get("scenarios", [])}


def load_cfo_system_prompt() -> str:
    if not CFO_AGENT_PATH.is_file():
        print(f"Missing {CFO_AGENT_PATH}", file=sys.stderr)
        sys.exit(1)
    text = CFO_AGENT_PATH.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n.*?\n---\s*\n(.*)$", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def parse_started_at(evidence: dict[str, Any]) -> datetime | None:
    raw = evidence.get("started_at")
    if not raw or not isinstance(raw, str):
        return None
    s = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def in_month(dt: datetime | None, year: int, month: int) -> bool:
    if dt is None:
        return False
    return dt.year == year and dt.month == month


def extract_audit_summary_snippet(markdown: str, max_chars: int = 1200) -> str:
    m = STRATEGIC_SUMMARY_RE.search(markdown)
    body = m.group(1).strip() if m else markdown.strip()
    if len(body) > max_chars:
        return body[: max_chars - 3].rstrip() + "..."
    return body


def analyze_session(evidence: dict[str, Any]) -> dict[str, Any]:
    turns = evidence.get("turns") or []
    sid = evidence.get("session_id", "")
    scenario_id = evidence.get("scenario_id")
    scenario_name = evidence.get("scenario_name", "")
    started = evidence.get("started_at", "")
    file_name = evidence.get("evidence_log_file", "")

    strategic_audit_count = 0
    governance_nudges = 0
    governance_replies = 0
    award_aborted = 0
    award_contract_events: list[dict[str, Any]] = []
    contract_executed: bool | None = None

    audit_excerpts: list[str] = []

    for t in turns:
        action = t.get("action", "")
        payload = t.get("payload") or {}
        if action == "strategic_audit":
            strategic_audit_count += 1
            md = payload.get("markdown") or ""
            if md:
                audit_excerpts.append(extract_audit_summary_snippet(md))
        elif action == "governance_nudge":
            governance_nudges += 1
        elif action == "governance_nudge_reply":
            governance_replies += 1
        elif action == "award_aborted":
            award_aborted += 1
        elif action == "award_contract":
            award_contract_events.append(
                {
                    "vendor_name": payload.get("vendor_name"),
                    "price": payload.get("price"),
                    "skill_result": str(payload.get("skill_result", "")),
                    "human_approved": payload.get("human_approved"),
                }
            )
        elif action == "session_end":
            contract_executed = bool(payload.get("contract_executed"))

    successful_prices: list[float] = []
    guardrail_errors = 0
    for ev in award_contract_events:
        sr = ev.get("skill_result") or ""
        if sr.startswith("SUCCESS"):
            p = ev.get("price")
            if isinstance(p, (int, float)):
                successful_prices.append(float(p))
        elif sr.startswith("ERROR") or "ERROR:" in sr:
            guardrail_errors += 1

    last_award = None
    for ev in reversed(award_contract_events):
        sr = ev.get("skill_result") or ""
        if sr.startswith("SUCCESS"):
            last_award = ev
            break

    sum_award = round(sum(successful_prices), 2) if successful_prices else None
    if contract_executed is not True:
        sum_award = None
    elif sum_award is None and last_award:
        p = last_award.get("price")
        if isinstance(p, (int, float)):
            sum_award = round(float(p), 2)

    return {
        "session_id": sid,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "started_at": started,
        "evidence_file": file_name,
        "contract_executed": contract_executed,
        "strategic_audit_count": strategic_audit_count,
        "governance_nudges": governance_nudges,
        "governance_nudge_replies": governance_replies,
        "award_aborted_count": award_aborted,
        "award_contract_events": len(award_contract_events),
        "successful_award_prices": successful_prices,
        "last_successful_award": last_award,
        "guardrail_error_events": guardrail_errors,
        "sum_award_value_if_executed": sum_award,
        "audit_summary_excerpts": audit_excerpts[:5],
    }


def collect_evidence_paths() -> list[Path]:
    if not LOGS_DIR.is_dir():
        return []
    return sorted(LOGS_DIR.glob("evidence_log_*.json"))


def build_facts(
    paths: list[Path],
    *,
    year: int | None,
    month: int | None,
    all_time: bool,
) -> dict[str, Any]:
    scenarios = load_scenarios()
    catalog = {}
    for sid, s in scenarios.items():
        catalog[str(sid)] = {
            "name": s.get("name", ""),
            "budget": s.get("budget"),
            "requirements_preview": (s.get("requirements") or "")[:240],
        }

    sessions_out: list[dict[str, Any]] = []
    for path in paths:
        try:
            evidence = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        dt = parse_started_at(evidence)
        if not all_time and year is not None and month is not None:
            if not in_month(dt, year, month):
                continue
        sess = analyze_session(evidence)
        sessions_out.append(sess)

    total_success_value = sum(
        sum(s["successful_award_prices"]) for s in sessions_out
    )
    total_audits = sum(s["strategic_audit_count"] for s in sessions_out)
    total_nudges = sum(s["governance_nudges"] for s in sessions_out)
    total_aborted = sum(s["award_aborted_count"] for s in sessions_out)
    total_guardrail_errors = sum(s["guardrail_error_events"] for s in sessions_out)
    executed_count = sum(
        1 for s in sessions_out if s.get("contract_executed") is True
    )

    # Deterministic per-scenario rollups (reduces LLM invention in financial narrative)
    by_scenario: dict[str, dict[str, Any]] = {}
    for s in sessions_out:
        key = str(s.get("scenario_id") if s.get("scenario_id") is not None else "unknown")
        if key not in by_scenario:
            by_scenario[key] = {
                "session_count": 0,
                "contracts_executed": 0,
                "sum_successful_award_prices": 0.0,
                "strategic_audit_runs": 0,
                "guardrail_errors": 0,
                "human_award_aborted": 0,
            }
        b = by_scenario[key]
        b["session_count"] += 1
        if s.get("contract_executed") is True:
            b["contracts_executed"] += 1
        b["sum_successful_award_prices"] += sum(s.get("successful_award_prices") or [])
        b["strategic_audit_runs"] += s["strategic_audit_count"]
        b["guardrail_errors"] += s["guardrail_error_events"]
        b["human_award_aborted"] += s["award_aborted_count"]
    for k, b in by_scenario.items():
        b["sum_successful_award_prices"] = round(b["sum_successful_award_prices"], 2)

    period_label = (
        f"{year:04d}-{month:02d}"
        if year is not None and month is not None and not all_time
        else "all_time"
    )

    return {
        "period": {
            "label": period_label,
            "all_time": all_time,
        },
        "scenarios_catalog": catalog,
        "by_scenario_id": by_scenario,
        "sessions": sessions_out,
        "totals": {
            "session_count": len(sessions_out),
            "sessions_with_contract_executed": executed_count,
            "strategic_audit_runs": total_audits,
            "governance_nudges": total_nudges,
            "human_award_aborted_events": total_aborted,
            "guardrail_error_events": total_guardrail_errors,
            "sum_successful_award_prices": round(total_success_value, 2),
        },
    }


def call_claude(
    client: Anthropic,
    system: str,
    facts: dict[str, Any],
    *,
    on_before_request: Callable[[int], None] | None = None,
) -> str:
    # Compact excerpts for user message (avoid huge payloads)
    excerpts: list[str] = []
    for s in facts.get("sessions", []):
        for i, ex in enumerate(s.get("audit_summary_excerpts") or []):
            excerpts.append(
                f"[scenario {s.get('scenario_id')} session {str(s.get('session_id', ''))[:8]} excerpt {i+1}]\n{ex}"
            )
    user_content = (
        "FACTS (JSON — sole source of truth for numbers and session list):\n```json\n"
        + json.dumps(facts, indent=2, default=str)
        + "\n```\n\nAUDIT_EXCERPTS (from Strategic Audit Summary sections in evidence JSON; may be empty):\n"
        + ("\n\n".join(excerpts) if excerpts else "(none)")
    )

    if on_before_request:
        on_before_request(len(user_content))

    msg = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    parts: list[str] = []
    for b in msg.content:
        if b.type == "text":
            parts.append(b.text)
    return "\n".join(parts).strip()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate CFO narrative Markdown from evidence logs.",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--month",
        metavar="YYYY-MM",
        help="Filter sessions by started_at in this UTC month.",
    )
    g.add_argument(
        "--all",
        action="store_true",
        help="Include all evidence logs (ignore month).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Write FACTS JSON to stdout and skip the API call.",
    )
    return p.parse_args()


def main() -> int:
    load_dotenv(ROOT / ".env")
    api_timeout = float(os.environ.get("CFO_REPORT_API_TIMEOUT", "180"))

    args = parse_args()

    year: int | None = None
    month: int | None = None
    all_time = bool(args.all)
    if args.month:
        try:
            parts = args.month.strip().split("-")
            year, month = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            print("Invalid --month; use YYYY-MM", file=sys.stderr)
            return 1

    print("cfo_monthly_report: scanning evidence logs…", file=sys.stderr)
    paths = collect_evidence_paths()
    print(f"cfo_monthly_report: found {len(paths)} evidence file(s) under {LOGS_DIR}", file=sys.stderr)
    facts = build_facts(
        paths,
        year=year,
        month=month,
        all_time=all_time,
    )
    n_sess = facts["totals"]["session_count"]
    print(
        f"cfo_monthly_report: {n_sess} session(s) in period “{facts['period']['label']}”",
        file=sys.stderr,
    )

    if args.dry_run:
        print(json.dumps(facts, indent=2, default=str))
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Set ANTHROPIC_API_KEY in .env or environment.", file=sys.stderr)
        return 1

    system_prompt = load_cfo_system_prompt()
    client = Anthropic(api_key=api_key, timeout=api_timeout)

    def _progress(payload_chars: int) -> None:
        print(
            f"cfo_monthly_report: calling Anthropic API (~{payload_chars // 1000}k chars input; "
            f"often 60–120s, please wait…)",
            file=sys.stderr,
        )

    report_md = call_claude(
        client,
        system_prompt,
        facts,
        on_before_request=_progress,
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_name = (
        f"CFO_narrative_{facts['period']['label']}.md"
        if facts["period"]["label"] != "all_time"
        else "CFO_narrative_all_time.md"
    )
    out_path = REPORTS_DIR / out_name
    header = (
        f"<!-- Generated by cfo_monthly_report.py | period={facts['period']['label']} "
        f"| sessions={facts['totals']['session_count']} -->\n\n"
    )
    out_path.write_text(header + report_md + "\n", encoding="utf-8")
    print(f"Wrote {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
