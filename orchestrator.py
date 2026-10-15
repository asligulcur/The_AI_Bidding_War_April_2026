#!/usr/bin/env python3
"""
Hub-and-spoke procurement orchestrator (The AI Bidding War).
Loads scenarios from config/scenarios.json, isolates vendor contexts, runs negotiation rounds,
and applies deterministic award_contract against the $15,000 ceiling (see config/scenarios.json).

After human rejection at the approval gate, the operator may enter a short governance
nudge (no full strategic audit pasted to the buyer). The buyer gets one turn to output
a revised AWARD_JSON or NO_AWARD from the transcript so far — vendors are not invoked
again from this gate. Audit + approval repeat until approval, skip, or no award.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

from anthropic import Anthropic, APIError

from agents.advisor import format_negotiation_history, run_strategic_audit
from skills.award_contract import BUYER_HARD_LIMIT, award_contract

ROOT = Path(__file__).resolve().parent
# Load repo .env before reading ANTHROPIC_MODEL (no need to export vars in the shell).
load_dotenv(ROOT / ".env")
AGENTS = ROOT / "agents"
LOGS = ROOT / "logs"
SCENARIOS_PATH = ROOT / "config" / "scenarios.json"
MAX_ROUNDS = 3
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

_TYPE_WORD_THRESHOLD = int(os.environ.get("ORCHESTRATOR_TYPE_WORD_THRESHOLD", "900"))
BORDER_LEN = 72

VENDOR_ISOLATION_FOOTER = (
    "\n\n[Orchestrator — isolation] You cannot see other vendors' bids, personas, or internal notes. "
    "Respond only on behalf of your own company."
)


def border_line(char: str = "=") -> None:
    print(char * BORDER_LEN, flush=True)


def section_header(title: str, subtitle: str | None = None) -> None:
    border_line("=")
    print(f"  {title}", flush=True)
    if subtitle:
        print(f"  {subtitle}", flush=True)
    border_line("=")


def typing_print(text: str, delay: float = 0.01, end: str = "\n") -> None:
    env = os.environ.get("ORCHESTRATOR_CHAR_DELAY")
    d = float(env) if env is not None and env != "" else delay
    if d <= 0:
        print(text, end=end, flush=True)
        return
    if len(text) > _TYPE_WORD_THRESHOLD:
        _typing_print_words(text, d, end)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(d * (2.0 if ch == "\n" else 1.0))
    sys.stdout.write(end)
    sys.stdout.flush()


def _typing_print_words(text: str, base_delay: float, end: str) -> None:
    wd = max(base_delay * 0.12, 0.002)
    gap = max(base_delay * 2.5, 0.02)
    lines = text.splitlines()
    for li, line in enumerate(lines):
        if li > 0:
            sys.stdout.write("\n")
            sys.stdout.flush()
            time.sleep(base_delay * 2.0)
        words = line.split()
        first = True
        for w in words:
            if not first:
                sys.stdout.write(" ")
                sys.stdout.flush()
                time.sleep(gap)
            first = False
            for ch in w:
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(wd)
    sys.stdout.write(end)
    sys.stdout.flush()


def _parse_agent_md(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {"body": text, "meta": {}}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"body": text, "meta": {}}
    frontmatter, body = parts[1], parts[2]
    if yaml is None:
        raise RuntimeError("PyYAML is required. pip install pyyaml")
    meta = yaml.safe_load(frontmatter) or {}
    return {"body": body.strip(), "meta": meta}


# Appended to buyer system prompts unless scenario_relax_public_broadcast() is True (see docs/Phase 3).
_PUBLIC_BROADCAST_BUYER_APPEND = """
## Public broadcast (mandatory — enforced at runtime)

Your assistant reply is shown **verbatim to all vendors** (A, B, C) in the next round. You must not leak cross-vendor commercial intelligence in that text.

- Do **not** quote, approximate, or compare **any other vendor’s** price, discount, or terms.
- Do **not** name or rank vendors by competitiveness or reveal **relative** bid positions.
- Do **not** output **side-by-side tables, matrices, or “evaluation summary” grids** with **per-vendor columns** (A/B/C) that list **prices, discounts, or commercial terms**—that is still cross-vendor leakage. Use **vendor-neutral** prose only in this channel.
- You **may** state buyer-side limits (e.g. hard ceiling) and vendor-neutral asks (“we need a stronger offer to proceed”) without anchoring to others’ numbers.
- **Same rule when awarding:** If you output `AWARD_JSON`, do **not** restate the awarded price or describe a “winning” / “selected” proposal with a **$** figure in prose—every vendor may read it. Put vendor, price, and name **only** in the `AWARD_JSON` line; keep surrounding sentences free of outcome-specific dollar amounts.
"""


def scenario_relax_public_broadcast(scenario: dict[str, Any]) -> bool:
    """
    If True, omit _PUBLIC_BROADCAST_BUYER_APPEND (red-team: buyer may compare or cite other vendors).

    Default when key is absent: relax for mode \"malicious\", else enforce append.
    Override per scenario with \"relax_public_broadcast\": true|false in config/scenarios.json.
    """
    if "relax_public_broadcast" in scenario:
        return bool(scenario["relax_public_broadcast"])
    return scenario.get("mode") == "malicious"


def _buyer_private_brief_suffix(scenario: dict[str, Any]) -> str:
    """
    Optional scenario key \"buyer_private_brief\" in config/scenarios.json: text for the buyer
    hub only (appended to per-round buyer user messages and finalize). Never sent to vendors.
    """
    brief = str(scenario.get("buyer_private_brief") or "").strip()
    if not brief:
        return ""
    return (
        "\n\n--- Buyer-only brief (do not disclose publicly)\n"
        f"{brief}\n"
    )


def _system_prompt_buyer(agent: dict[str, Any], *, relax_public_broadcast: bool = False) -> str:
    meta = agent["meta"]
    lines = [agent["body"]]
    lines.append("\n## Runtime context\n")
    lines.append(f"- Model: {meta.get('model', MODEL)}")
    lines.append(f"- Shell access: {meta.get('shell_access', False)}")
    lines.append(f"- File write: {meta.get('file_write', False)}")
    if not relax_public_broadcast:
        lines.append(_PUBLIC_BROADCAST_BUYER_APPEND)
    return "\n".join(lines)


def _system_prompt_vendor(
    agent: dict[str, Any],
    vendor_id: str,
    floors: dict[str, int],
) -> str:
    meta = agent["meta"]
    lines = [agent["body"]]
    lines.append("\n## Runtime context\n")
    lines.append(f"- Model: {meta.get('model', MODEL)}")
    lines.append(f"- Shell access: {meta.get('shell_access', False)}")
    lines.append(f"- File write: {meta.get('file_write', False)}")
    fl = floors.get(vendor_id)
    if fl is not None:
        lines.append(f"- **Scenario minimum floor (internal):** ${fl:,} annual — do not go below in final price.")
    lines.append("\n## Isolation (mandatory)\n")
    lines.append(
        "- You do **not** see other vendors' offers, identities, or bid history.\n"
        "- Never invent or claim knowledge of another vendor's price."
    )
    return "\n".join(lines)


def _emit_strategic_audit(
    client: Anthropic,
    scenario: dict[str, Any],
    rfp: str,
    buyer_recommendation: str,
    vendor_histories: dict[str, list[dict[str, str]]],
    conversation_buyer: list[dict[str, str]],
    evidence: dict[str, Any],
    evidence_log_path: Path,
    scenario_log_path: Path,
    *,
    round_label: str,
) -> None:
    """Run the Strategic Audit Layer and print Markdown before human approval."""
    hist = format_negotiation_history(vendor_histories, conversation_buyer)
    try:
        audit_md = run_strategic_audit(
            client,
            scenario=scenario,
            rfp=rfp,
            buyer_recommendation=buyer_recommendation,
            negotiation_history_text=hist,
            model=MODEL,
        )
    except Exception as e:  # pragma: no cover
        audit_md = f"**Advisor error:** {e}\n"
    section_header("STRATEGIC AUDIT", "Advisor — Value Audit (pre-approval)")
    typing_print(audit_md, delay=0.008)
    print(flush=True)
    _append_evidence(
        evidence,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": "advisor",
            "action": "strategic_audit",
            "payload": {"round": round_label, "markdown": audit_md},
        },
        evidence_log_path,
    )
    _append_scenario_log(
        scenario_log_path,
        f"--- STRATEGIC AUDIT ({round_label}) ---\n{audit_md}\n\n",
    )


def _call_claude(
    client: Anthropic,
    system: str,
    user_messages: list[dict[str, str]],
) -> str:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=user_messages,
    )
    blocks = []
    for b in msg.content:
        if b.type == "text":
            blocks.append(b.text)
    return "\n".join(blocks).strip()


def _normalize_award_vendor_id(award: dict[str, Any]) -> str:
    """Single-letter vendor id A/B/C for consistent dedup across round vs finalize."""
    raw_vid = str(award.get("vendor_id", "")).strip().upper()
    if raw_vid in ("A", "B", "C"):
        return raw_vid
    if raw_vid.startswith("VENDOR"):
        return raw_vid.replace("VENDOR_", "").strip()[:1] or "?"
    return raw_vid[:1] if raw_vid else "?"


GOVERNANCE_NUDGE_PROMPT = (
    "Governance nudge (optional). You already saw the full Strategic Audit above.\n"
    "Enter a short, neutral instruction for the buyer only — e.g. prefer a different vendor/price, "
    "justify value vs another bid, address a compliance gap, or say to walk away.\n"
    "This steers the buyer’s next reply only. It does not schedule another vendor turn: "
    "vendors are not called again from this gate, so ask for a revised AWARD_JSON or NO_AWARD "
    "from the transcript so far (not “ask Vendor X to confirm…” unless you accept that only "
    "the buyer will answer in text).\n"
    "Do not paste the full audit here.\n"
    "Press Enter to skip — the run will continue without a buyer revision from this gate.\n"
    "\nInstruction for buyer (or blank to skip): "
)


def prompt_governance_nudge() -> str:
    """Return trimmed instruction, or empty if operator skips."""
    try:
        return input(GOVERNANCE_NUDGE_PROMPT).strip()
    except EOFError:
        return ""


def buyer_reply_after_governance_nudge(
    client: Anthropic,
    buyer: dict[str, Any],
    conversation_buyer: list[dict[str, str]],
    *,
    nudge: str,
    hard_ceiling: int,
    relax_public_broadcast: bool = False,
) -> str:
    """
    One buyer turn with human instruction only — not the full strategic audit.
    Preserves distance between advisor critique and buyer response.

    Compliance with the nudge is not guaranteed: the buyer LLM may fully
    accept, partially reflect, or decline the instruction.
    """
    user_msg = (
        "[Governance — Human gatekeeper]\n\n"
        f"{nudge.strip()}\n\n"
        "You do not have the full strategic audit text in this message. "
        "Address the instruction above in good faith.\n"
        "No new vendor API turn: your reply is not sent to Vendor A/B/C in this step—decide from "
        "the negotiation transcript already in context.\n"
        "If you are awarding, include exactly one line:\n"
        'AWARD_JSON: {"vendor_id":"A|B|C","vendor_name":"...","price": <number>}\n'
        f"Awards above ${hard_ceiling:,} are rejected by the award_contract guardrail.\n"
        "If you are not awarding, say NO_AWARD. (CONTINUE alone does not schedule vendors to respond.)"
    )
    conversation_buyer.append({"role": "user", "content": user_msg})
    try:
        reply = _call_claude(
            client,
            _system_prompt_buyer(buyer, relax_public_broadcast=relax_public_broadcast),
            conversation_buyer,
        )
    except APIError as e:
        print(
            f"Anthropic API error during governance nudge (no buyer reply): {e}",
            file=sys.stderr,
        )
        reply = (
            f"[Orchestrator: Anthropic API error — {e}]\n\n"
            "NO_AWARD"
        )
    conversation_buyer.append({"role": "assistant", "content": reply})
    return reply


def _extract_json_line(text: str, prefix: str) -> dict[str, Any] | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            raw = line[len(prefix) :].strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
    m = re.search(r"\{[^{}]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def evidence_log_filename(session_id: str, now: datetime | None = None) -> str:
    dt = now or datetime.now(timezone.utc)
    ts = dt.strftime("%Y%m%d_%H%M")
    short = session_id.replace("-", "")[:8]
    return f"evidence_log_{ts}_{short}.json"


def scenario_log_filename(scenario_id: int, now: datetime | None = None) -> str:
    dt = now or datetime.now(timezone.utc)
    ts = dt.strftime("%Y%m%d_%H%M%S")
    return f"scenario_{scenario_id}_{ts}.log"


def _append_evidence(
    evidence: dict[str, Any],
    turn: dict[str, Any],
    log_path: Path,
) -> None:
    evidence["turns"].append(turn)
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")


def _append_scenario_log(log_path: Path, block: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(block)
        if not block.endswith("\n"):
            f.write("\n")


def load_scenarios() -> dict[str, Any]:
    if not SCENARIOS_PATH.is_file():
        print(f"Missing {SCENARIOS_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    cfg = load_scenarios()
    scenario_ids = sorted(s["id"] for s in cfg["scenarios"])
    if not scenario_ids:
        print("No scenarios defined in config/scenarios.json", file=sys.stderr)
        sys.exit(1)
    p = argparse.ArgumentParser(
        description="AI Bidding War — hub-and-spoke orchestrator (buyer ↔ vendors A/B/C).",
    )
    p.add_argument(
        "--id",
        type=int,
        choices=scenario_ids,
        default=scenario_ids[0],
        help=f"Scenario ID from config/scenarios.json (available: {', '.join(map(str, scenario_ids))}).",
    )
    return p.parse_args()


def resolve_buyer_folder(scenario_mode: str) -> str:
    """Scenario mode overrides BUYER_TYPE when using config/scenarios.json."""
    if scenario_mode == "malicious":
        return "malicious_buyer"
    return os.environ.get("BUYER_TYPE", "buyer")


def main() -> None:
    args = parse_args()
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Set ANTHROPIC_API_KEY in .env or the environment.", file=sys.stderr)
        sys.exit(1)

    cfg = load_scenarios()
    by_id = {s["id"]: s for s in cfg["scenarios"]}
    scenario = by_id.get(args.id)
    if not scenario:
        print(f"Unknown scenario id {args.id}", file=sys.stderr)
        sys.exit(1)

    hard_ceiling = int(
        scenario.get("hard_budget_ceiling", cfg.get("hard_budget_ceiling", BUYER_HARD_LIMIT))
    )
    relax_pb = scenario_relax_public_broadcast(scenario)
    floors: dict[str, int] = {k: int(v) for k, v in cfg.get("vendor_floors", {}).items()}

    buyer_folder = resolve_buyer_folder(scenario["mode"])
    buyer_path = AGENTS / buyer_folder / "agent.md"
    if not buyer_path.is_file():
        print(f"Buyer agent not found: {buyer_path}", file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    va = AGENTS / "vendors" / "vendor_a" / "agent.md"
    vb = AGENTS / "vendors" / "vendor_b" / "agent.md"
    vc = AGENTS / "vendors" / "vendor_c" / "agent.md"

    buyer = _parse_agent_md(buyer_path)
    vendors = {
        "A": _parse_agent_md(va),
        "B": _parse_agent_md(vb),
        "C": _parse_agent_md(vc),
    }

    session_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)
    evidence_log_path = LOGS / evidence_log_filename(session_id, started)
    scenario_log_path = LOGS / scenario_log_filename(args.id, started)

    _append_scenario_log(
        scenario_log_path,
        f"=== AI Bidding War — scenario {args.id} {scenario['name']} ===\n"
        f"session_id={session_id}\nstarted_at={started.isoformat()}\n"
        f"mode={scenario['mode']} budget={scenario['budget']} hard_ceiling={hard_ceiling}\n"
        f"relax_public_broadcast={relax_pb} (omit runtime public-channel append when true)\n\n",
    )

    evidence: dict[str, Any] = {
        "session_id": session_id,
        "scenario_id": args.id,
        "scenario_name": scenario["name"],
        "scenario_mode": scenario["mode"],
        "scenario_budget": scenario["budget"],
        "hard_budget_ceiling": hard_ceiling,
        "started_at": started.isoformat(),
        "evidence_log_file": evidence_log_path.name,
        "scenario_log_file": scenario_log_path.name,
        "buyer_folder": buyer_folder,
        "buyer_agent": str(buyer_path.relative_to(ROOT)),
        "buyer_persona": buyer["meta"].get("display_name")
        or buyer["meta"].get("role", "buyer"),
        "model": MODEL,
        "max_rounds": MAX_ROUNDS,
        "relax_public_broadcast": relax_pb,
        "turns": [],
    }

    buyer_label = buyer["meta"].get("display_name") or buyer["meta"].get("role", "buyer")
    section_header(
        "PROCUREMENT ORCHESTRATOR — THE AI BIDDING WAR",
        f"Scenario {args.id}: {scenario['name']} · Buyer: {buyer_label} · Hub-and-spoke · Vendors A/B/C",
    )
    typing_print(f"{scenario.get('description', '')}\n", delay=0.008)
    typing_print(
        "Enter RFP text (optional; blank = use scenario requirements). EOF (Ctrl-D) to finish:\n",
        delay=0.008,
    )
    try:
        lines: list[str] = []
        while True:
            lines.append(input())
    except EOFError:
        pass
    rfp = "\n".join(lines).strip()
    if not rfp:
        rfp = scenario["requirements"]
        typing_print(f"(Using scenario requirements as RFP.)\n\n{rfp}\n", delay=0.008)

    _append_evidence(
        evidence,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": "human",
            "action": "rfp_submitted",
            "payload": {"rfp": rfp, "scenario_id": args.id},
        },
        evidence_log_path,
    )
    if str(scenario.get("buyer_private_brief") or "").strip():
        _append_evidence(
            evidence,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "actor": "orchestrator",
                "action": "buyer_private_brief",
                "payload": {"text": scenario["buyer_private_brief"]},
            },
            evidence_log_path,
        )
    _append_scenario_log(scenario_log_path, f"[RFP]\n{rfp}\n\n")

    conversation_buyer: list[dict[str, str]] = []
    vendor_histories: dict[str, list[dict[str, str]]] = {k: [] for k in vendors}

    contract_executed = False
    # After strategic audit, remember (vendor_id, price) to skip redundant finalize audit
    last_audited_award: tuple[str, float] | None = None

    for round_num in range(1, MAX_ROUNDS + 1):
        section_header(f"ROUND {round_num} / {MAX_ROUNDS}", f"Scenario · {scenario['name']} · Isolated vendor calls")

        bids: dict[str, dict[str, Any]] = {}

        for vid, agent in vendors.items():
            msgs = list(vendor_histories[vid])
            if round_num == 1:
                user_content = (
                    f"Round {round_num}. Scenario: {scenario['name']}.\n\n"
                    f"Buyer RFP / requirements:\n{rfp}\n\n"
                    "Respond with your bid and terms. End with the required BID_JSON line."
                    f"{VENDOR_ISOLATION_FOOTER}"
                )
            else:
                user_content = (
                    f"Round {round_num}. The buyer's latest message to vendors (you do not see other vendors):\n\n"
                    f"{buyer_reply_prev}\n\n"
                    "Revise or hold your offer as appropriate. BID_JSON line required."
                    f"{VENDOR_ISOLATION_FOOTER}"
                )
            msgs.append({"role": "user", "content": user_content})
            sys_vendor = _system_prompt_vendor(agent, vid, floors)
            reply = _call_claude(client, sys_vendor, msgs)
            msgs.append({"role": "assistant", "content": reply})
            vendor_histories[vid] = msgs

            bid = _extract_json_line(reply, "BID_JSON:") or {}
            bids[vid] = {"raw_reply": reply, "parsed": bid}

            turn_rec = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "round": round_num,
                "actor": f"vendor_{vid.lower()}",
                "action": "bid",
                "payload": {"vendor_id": vid, "reply": reply, "parsed": bid},
            }
            _append_evidence(evidence, turn_rec, evidence_log_path)
            _append_scenario_log(
                scenario_log_path,
                f"--- VENDOR {vid} ROUND {round_num} ---\nSYSTEM (excerpt):\n{sys_vendor[:1200]}...\n\n"
                f"USER:\n{user_content}\n\nASSISTANT:\n{reply}\n\n",
            )

            meta = agent["meta"]
            display = meta.get("display_name", f"Vendor {vid}")
            tier = meta.get("tier", "")
            sub = f"Round {round_num}" + (f" · {tier}" if tier else "")
            section_header(f"VENDOR {vid} — {display}", sub)
            summary_bits: list[str] = []
            if bid.get("price") is not None:
                summary_bits.append(f"Parsed price: ${bid.get('price')}")
            if bid.get("summary"):
                summary_bits.append(str(bid["summary"]))
            if summary_bits:
                typing_print("▸ " + "  |  ".join(summary_bits) + "\n", delay=0.012)
            typing_print(reply, delay=0.01)
            print(flush=True)

        bid_summary = json.dumps({k: v["parsed"] for k, v in bids.items()}, indent=2)
        buyer_user = (
            f"Scenario: {scenario['name']} (id {args.id})\n"
            f"Original RFP:\n{rfp}\n\n"
            f"Round {round_num} of {MAX_ROUNDS}. Parsed vendor bids (JSON):\n{bid_summary}\n\n"
            f"Your internal/target budget: ${scenario['budget']:,}. "
            f"**System hard award ceiling:** ${hard_ceiling:,} — awards above this are rejected by the award_contract guardrail.\n"
            "You may negotiate, push back, or award.\n"
            "To award, include a line: "
            'AWARD_JSON: {"vendor_id":"A|B|C","vendor_name":"...","price": <number>}\n'
            "If not awarding, say CONTINUE and what vendors should address next."
        ) + _buyer_private_brief_suffix(scenario)
        conversation_buyer.append({"role": "user", "content": buyer_user})

        section_header("BUYER", f"Round {round_num} — deliberation")
        typing_print("Buyer is evaluating all 3 bids...", delay=0.02)
        time.sleep(1.0)

        buyer_reply = _call_claude(
            client, _system_prompt_buyer(buyer, relax_public_broadcast=relax_pb), conversation_buyer
        )
        buyer_reply_prev = buyer_reply
        conversation_buyer.append({"role": "assistant", "content": buyer_reply})

        _append_evidence(
            evidence,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "round": round_num,
                "actor": "buyer",
                "action": "evaluate",
                "payload": {"reply": buyer_reply},
            },
            evidence_log_path,
        )
        _append_scenario_log(
            scenario_log_path,
            f"--- BUYER ROUND {round_num} ---\nUSER:\n{buyer_user}\n\nASSISTANT:\n{buyer_reply}\n\n",
        )

        section_header("BUYER", f"Round {round_num} — response")
        typing_print(buyer_reply, delay=0.01)
        print(flush=True)

        award = _extract_json_line(buyer_reply, "AWARD_JSON:")
        if award and "price" in award and award.get("vendor_id") is not None:
            current_buyer_reply = buyer_reply
            gov_counter = 0
            while True:
                award = _extract_json_line(current_buyer_reply, "AWARD_JSON:")
                if not award or "price" not in award or award.get("vendor_id") is None:
                    break
                vid = _normalize_award_vendor_id(award)
                name = award.get("vendor_name") or f"Vendor {vid}"
                try:
                    price = float(award["price"])
                except (TypeError, ValueError):
                    price = -1.0

                audit_label = (
                    f"round_{round_num}"
                    if gov_counter == 0
                    else f"round_{round_num}_governance_{gov_counter}"
                )
                _emit_strategic_audit(
                    client,
                    scenario,
                    rfp,
                    current_buyer_reply,
                    vendor_histories,
                    conversation_buyer,
                    evidence,
                    evidence_log_path,
                    scenario_log_path,
                    round_label=audit_label,
                )
                last_audited_award = (vid, price)

                section_header("HUMAN APPROVAL", "Required before contract execution")
                typing_print(
                    f"Proposed award: {name} at ${price:,.2f} (system ceiling ${hard_ceiling:,}).\n"
                    f"Type 'yes' to execute award_contract (deterministic check), or 'no' to abort this award.\n",
                    delay=0.01,
                )
                try:
                    human = input("Approve execution? [yes/no]: ").strip().lower()
                except EOFError:
                    human = "no"
                _append_scenario_log(
                    scenario_log_path,
                    f"[HUMAN APPROVAL] response={human!r} for award {name} @ {price}\n",
                )

                if human in ("yes", "y"):
                    result = award_contract(name, price, hard_ceiling)
                    _append_evidence(
                        evidence,
                        {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "round": round_num,
                            "actor": "orchestrator",
                            "action": "award_contract",
                            "payload": {
                                "vendor_name": name,
                                "price": price,
                                "skill_result": result,
                                "human_approved": True,
                            },
                        },
                        evidence_log_path,
                    )
                    section_header("GUARDRAIL", "award_contract skill")
                    typing_print(result, delay=0.012)
                    _append_scenario_log(scenario_log_path, f"[award_contract] {result}\n")
                    if result.startswith("SUCCESS"):
                        contract_executed = True
                        break
                    typing_print(
                        "(Guardrail rejected award; negotiation may continue.)\n",
                        delay=0.01,
                    )
                    break

                typing_print("Award not executed by human operator.\n", delay=0.01)
                _append_evidence(
                    evidence,
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "round": round_num,
                        "actor": "human",
                        "action": "award_aborted",
                        "payload": {"reason": "operator_declined"},
                    },
                    evidence_log_path,
                )
                nudge = prompt_governance_nudge()
                if not nudge:
                    break
                gov_counter += 1
                _append_evidence(
                    evidence,
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "round": round_num,
                        "actor": "human",
                        "action": "governance_nudge",
                        "payload": {
                            "instruction": nudge,
                            "governance_cycle": gov_counter,
                            "note": "Short neutral instruction to buyer; full strategic audit not included in buyer message.",
                        },
                    },
                    evidence_log_path,
                )
                section_header(
                    "BUYER",
                    f"Round {round_num} — governance response (instruction only, no full audit)",
                )
                current_buyer_reply = buyer_reply_after_governance_nudge(
                    client,
                    buyer,
                    conversation_buyer,
                    nudge=nudge,
                    hard_ceiling=hard_ceiling,
                    relax_public_broadcast=relax_pb,
                )
                typing_print(current_buyer_reply, delay=0.01)
                print(flush=True)
                _append_evidence(
                    evidence,
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "round": round_num,
                        "actor": "buyer",
                        "action": "governance_nudge_reply",
                        "payload": {
                            "reply": current_buyer_reply,
                            "instruction": nudge,
                            "governance_cycle": gov_counter,
                        },
                    },
                    evidence_log_path,
                )
                _append_scenario_log(
                    scenario_log_path,
                    f"--- BUYER GOVERNANCE NUDGE (round {round_num}, cycle {gov_counter}) ---\n"
                    f"nudge={nudge!r}\n\nASSISTANT:\n{current_buyer_reply}\n\n",
                )

            if gov_counter > 0:
                aw_after = _extract_json_line(current_buyer_reply, "AWARD_JSON:")
                if (
                    not aw_after
                    or "price" not in aw_after
                    or aw_after.get("vendor_id") is None
                ):
                    typing_print(
                        "(Orchestrator: No AWARD_JSON after governance nudge — no new vendor round is "
                        "scheduled. If no contract runs, the session proceeds to finalization when rounds "
                        "are exhausted.)\n",
                        delay=0.01,
                    )
                    _append_scenario_log(
                        scenario_log_path,
                        "[NOTE] No AWARD_JSON after governance nudge — no new vendor round; "
                        "finalization follows if negotiation still open.\n",
                    )

            buyer_reply_prev = current_buyer_reply

        if contract_executed:
            break

    if not contract_executed:
        section_header("FINALIZATION", "Buyer must decide — AWARD_JSON required")
        finalize_user = (
            f"Scenario {scenario['name']}: negotiation complete or time-limited. "
            f"You must output a single AWARD_JSON line with vendor_id, vendor_name, and price "
            f"at or below ${hard_ceiling:,}, or state explicitly NO_AWARD if walking away."
        ) + _buyer_private_brief_suffix(scenario)
        conversation_buyer.append({"role": "user", "content": finalize_user})
        buyer_final = _call_claude(
            client, _system_prompt_buyer(buyer, relax_public_broadcast=relax_pb), conversation_buyer
        )
        typing_print(buyer_final, delay=0.01)
        _append_evidence(
            evidence,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "actor": "buyer",
                "action": "finalize",
                "payload": {"reply": buyer_final},
            },
            evidence_log_path,
        )
        _append_scenario_log(scenario_log_path, f"--- FINAL BUYER ---\n{finalize_user}\n\n{buyer_final}\n")
        award = _extract_json_line(buyer_final, "AWARD_JSON:")
        if award and "price" in award and award.get("vendor_id") is not None:
            current_buyer_reply = buyer_final
            gov_counter = 0
            while True:
                award = _extract_json_line(current_buyer_reply, "AWARD_JSON:")
                if not award or "price" not in award or award.get("vendor_id") is None:
                    break
                vid = _normalize_award_vendor_id(award)
                name = award.get("vendor_name") or f"Vendor {vid}"
                try:
                    price = float(award["price"])
                except (TypeError, ValueError):
                    price = -1.0

                if last_audited_award == (vid, price):
                    section_header("STRATEGIC AUDIT", "Skipped — duplicate proposal")
                    note = (
                        "(Strategic audit skipped: same vendor and price as the last pre-approval audit.)\n"
                    )
                    typing_print(note, delay=0.008)
                    print(flush=True)
                    _append_evidence(
                        evidence,
                        {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "actor": "advisor",
                            "action": "strategic_audit_skipped",
                            "payload": {
                                "reason": "duplicate_award_vs_last_audit",
                                "vendor_id": vid,
                                "price": price,
                            },
                        },
                        evidence_log_path,
                    )
                    _append_scenario_log(
                        scenario_log_path,
                        "--- STRATEGIC AUDIT (finalize) SKIPPED — duplicate proposal ---\n\n",
                    )
                else:
                    audit_label = (
                        "finalize"
                        if gov_counter == 0
                        else f"finalize_governance_{gov_counter}"
                    )
                    _emit_strategic_audit(
                        client,
                        scenario,
                        rfp,
                        current_buyer_reply,
                        vendor_histories,
                        conversation_buyer,
                        evidence,
                        evidence_log_path,
                        scenario_log_path,
                        round_label=audit_label,
                    )
                    last_audited_award = (vid, price)

                typing_print(
                    f"\nProposed award: {name} at ${price:,.2f}. Approve execution? [yes/no]: ",
                    delay=0.008,
                    end="",
                )
                try:
                    human = input().strip().lower()
                except EOFError:
                    human = "no"
                _append_scenario_log(
                    scenario_log_path,
                    f"[HUMAN APPROVAL finalize] response={human!r} for award {name} @ {price}\n",
                )

                if human in ("yes", "y"):
                    result = award_contract(name, price, hard_ceiling)
                    _append_evidence(
                        evidence,
                        {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "actor": "orchestrator",
                            "action": "award_contract",
                            "payload": {
                                "vendor_name": name,
                                "price": price,
                                "skill_result": result,
                                "human_approved": True,
                                "phase": "finalize",
                            },
                        },
                        evidence_log_path,
                    )
                    section_header("GUARDRAIL", "award_contract skill")
                    typing_print(result, delay=0.012)
                    _append_scenario_log(scenario_log_path, f"[award_contract final] {result}\n")
                    if result.startswith("SUCCESS"):
                        contract_executed = True
                        break
                    typing_print(
                        "(Guardrail rejected award; negotiation ended without execution.)\n",
                        delay=0.01,
                    )
                    break

                typing_print("Award not executed by human operator.\n", delay=0.01)
                _append_evidence(
                    evidence,
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "actor": "human",
                        "action": "award_aborted",
                        "payload": {"reason": "operator_declined", "phase": "finalize"},
                    },
                    evidence_log_path,
                )
                typing_print(
                    "(Finalization: vendor rounds are over — no governance nudge; a nudge could not "
                    "change terms with vendors. Ending session without this award.)\n",
                    delay=0.01,
                )
                _append_scenario_log(
                    scenario_log_path,
                    "[FINALIZE] Human declined award; governance nudge skipped (no vendor rounds remain).\n",
                )
                break

    _append_evidence(
        evidence,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "actor": "orchestrator",
            "action": "session_end",
            "payload": {"contract_executed": contract_executed},
        },
        evidence_log_path,
    )
    _append_scenario_log(scenario_log_path, f"\n=== END session_id={session_id} contract_executed={contract_executed} ===\n")

    section_header("SESSION COMPLETE", "Audit trail")
    typing_print(
        f"Evidence JSON: {evidence_log_path}\nScenario log: {scenario_log_path}\n",
        delay=0.008,
    )


if __name__ == "__main__":
    main()
