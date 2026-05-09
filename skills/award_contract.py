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


def award_contract(vendor_name: str, price: float | int) -> str:
    """
    Award a contract if price <= $15,000; otherwise reject.

    On success, overwrites logs/contract.txt with that award only (latest snapshot;
    not appended across runs).
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        p = float(price)
    except (TypeError, ValueError):
        return "ERROR: Invalid price. Negotiation must continue."

    if p <= BUYER_HARD_LIMIT:
        msg = f"SUCCESS: Contract Awarded to {vendor_name} for ${p:,.2f}."
        contract_path = LOGS_DIR / "contract.txt"
        contract_path.write_text(
            (
                f"FINAL CONTRACT AWARD\n"
                f"Vendor: {vendor_name}\n"
                f"Annual price (500 seats): ${p:,.2f}\n"
                f"Hard budget cap: ${BUYER_HARD_LIMIT:,.2f}\n"
            ),
            encoding="utf-8",
        )
        return msg

    return (
        "ERROR: Budget violation. $15,000 is the hard limit. Negotiation must continue."
    )


__all__ = ["award_contract", "BUYER_HARD_LIMIT", "LOGS_DIR"]
