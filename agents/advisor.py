"""
Strategic Audit Layer — value audit against RFP before human approval.
"""

from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

ADVISOR_SYSTEM_PROMPT = """You are the Strategic Audit Layer. Your job is to find reasons to REJECT a deal if it doesn't perfectly align with the RFP. Be critical. Look for missing support terms, price discrepancies, and SLA mismatches. Also flag **non-price** integrity risks where the transcript supports it: **conflicts of interest**, **undue preference** for one vendor, **gifts or hospitality**, **prior employment or personal relationships**, **wired specifications**, or **pressure to limit documentation** of alternatives. Do not invent facts—only cite what appears in the negotiation text. Your goal is to ensure the Human Gatekeeper has the full context before signing.

You must perform a structured **Value Audit** against the original RFP requirements. In your output, use Markdown with these sections (use `###` headings):

### Compliance Gaps
Are mandatory features (e.g. 24/7 support, SSO, audit logs) **explicitly confirmed** in the winning vendor's final bid text? Call out anything assumed but not evidenced.

### Value Leakage
Is there a **significantly cheaper** vendor that met core requirements but was passed over for **subjective** reasons? Quantify if possible.

### Risk Assessment
Does the selected vendor show a **lower SLA, weaker support window, or thinner coverage** than the RFP implies? Note operational or compliance risk.

### Conflict of Interest & Process Integrity
Based **only** on the transcript: Does the buyer or narrative suggest **favoritism** not justified by objective RFP criteria (e.g. undisclosed ties, "we always use Vendor X," dismissive treatment of equally qualified bidders)? Any **gifts, entertainment, or side arrangements** implied? Any sign of **specification tailoring** or **steering** without measurable criteria? If none of this appears in the text, state that clearly.

### Strategic Audit Summary
2–4 bullet points the Human Gatekeeper should weigh **before** signing. Include **at least one** bullet on **integrity / fair competition / COI** when the transcript supports it; otherwise include a brief bullet such as "No COI or steering signals identified in the transcript."

Be concise but specific; cite vendor letters (A/B/C) and prices when relevant."""


def format_negotiation_history(
    vendor_histories: dict[str, list[dict[str, str]]],
    conversation_buyer: list[dict[str, str]],
) -> str:
    """Serialize hub + isolated vendor threads for the audit context."""
    parts: list[str] = []
    parts.append("## Buyer (hub) — full thread\n")
    for m in conversation_buyer:
        role = m.get("role", "unknown").upper()
        parts.append(f"**{role}:**\n{m.get('content', '')}\n\n")
    parts.append("## Vendors (A / B / C) — isolated threads as recorded\n")
    for vid in sorted(vendor_histories.keys()):
        parts.append(f"### Vendor {vid}\n")
        for m in vendor_histories[vid]:
            role = m.get("role", "unknown").upper()
            parts.append(f"**{role}:**\n{m.get('content', '')}\n\n")
    return "\n".join(parts)


def run_strategic_audit(
    client: Anthropic,
    *,
    scenario: dict[str, Any],
    rfp: str,
    buyer_recommendation: str,
    negotiation_history_text: str,
    model: str | None = None,
) -> str:
    """
    Run the Strategic Audit Layer on the proposed award.

    Parameters
    ----------
    scenario
        Entry from config/scenarios.json (name, requirements, description, budget, …).
    rfp
        Original RFP text used in this session.
    buyer_recommendation
        Buyer's message containing the award rationale and AWARD_JSON line.
    negotiation_history_text
        Full negotiation history (buyer + vendor threads), e.g. from
        `format_negotiation_history`.
    """
    m = model or DEFAULT_MODEL
    name = str(scenario.get("name", ""))
    requirements = str(scenario.get("requirements", ""))
    description = str(scenario.get("description", ""))
    budget = scenario.get("budget", "")

    user_content = f"""## Scenario (from configuration)
- **Name:** {name}
- **Internal / target budget (reference):** {budget}
- **Requirements (authoritative):**
{requirements}

- **Description:**
{description}

---

## Original RFP used in this session
{rfp}

---

## Buyer's recommendation (proposed award)
{buyer_recommendation}

---

## Full negotiation history
{negotiation_history_text}

---

Produce the Markdown Value Audit as specified in your system instructions. Output **only** the Markdown (no preamble)."""

    msg = client.messages.create(
        model=m,
        max_tokens=4096,
        system=ADVISOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    blocks: list[str] = []
    for b in msg.content:
        if b.type == "text":
            blocks.append(b.text)
    return "\n".join(blocks).strip()


__all__ = [
    "ADVISOR_SYSTEM_PROMPT",
    "DEFAULT_MODEL",
    "format_negotiation_history",
    "run_strategic_audit",
]
