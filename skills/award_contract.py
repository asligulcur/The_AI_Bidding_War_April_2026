"""
Math guardrail skill: award contract only if price respects buyer hard budget ($15,000).
Invoked by the orchestrator when the buyer commits to an award.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root (parent of /skills)
ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"

BUYER_HARD_LIMIT = 15_000


def award_contract(
    vendor_name: str, price: float | int, ceiling: float | int = BUYER_HARD_LIMIT
) -> str:
    """
    Award a contract if price <= the effective cap; otherwise reject.

    The effective cap is ``min(ceiling, BUYER_HARD_LIMIT)``: a caller (e.g. a
    per-scenario ``hard_budget_ceiling``) can only *tighten* the cap — it can
    never raise it above the $15,000 hard limit. So the enforced value now
    matches what the prompts state, while the safety guarantee ("no award above
    $15,000") holds by construction, no matter what a caller passes.

    On success, overwrites logs/contract.txt with that award only (latest snapshot;
    not appended across runs).
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        p = float(price)
    except (TypeError, ValueError):
        return "ERROR: Invalid price. Negotiation must continue."

    try:
        cap = min(float(ceiling), float(BUYER_HARD_LIMIT))
    except (TypeError, ValueError):
        cap = float(BUYER_HARD_LIMIT)

    if p <= cap:
        msg = f"SUCCESS: Contract Awarded to {vendor_name} for ${p:,.2f}."
        contract_path = LOGS_DIR / "contract.txt"
        contract_path.write_text(
            (
                f"FINAL CONTRACT AWARD\n"
                f"Vendor: {vendor_name}\n"
                f"Annual price (500 seats): ${p:,.2f}\n"
                f"Hard budget cap: ${cap:,.2f}\n"
            ),
            encoding="utf-8",
        )
        return msg

    return (
        f"ERROR: Budget violation. ${cap:,.0f} is the hard limit. Negotiation must continue."
    )


__all__ = ["award_contract", "BUYER_HARD_LIMIT", "LOGS_DIR"]
