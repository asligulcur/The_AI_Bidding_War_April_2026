# Configuration

| File | Role |
|------|------|
| **`scenarios.json`** | Scenarios **1–11**: **`id`**, **`name`**, **`mode`** (`standard` \| `malicious`), **`budget`**, **`requirements`** (public RFP text — **also** what vendors see in round 1), **`description`**. Optional: **`hard_budget_ceiling`**, **`relax_public_broadcast`** (overrides default for buyer public-channel runtime rules — see **`docs/Future Roadmap/PHASE_3_IMPLEMENTATION.md`**), **`buyer_private_brief`** (buyer hub only — corrupt or internal instructions **not** sent to vendors; see **`docs/Phase 3/Phase3_AI_USAGE.pdf`**). |
| **Root keys** | **`hard_budget_ceiling`** (default **15000**), **`vendor_floors`**, **`vendor_b_notes`** |

Consumed by **`orchestrator.py`**, harvest/export scripts under **`scripts/export_evaluation/`**, **`scripts/cfo_monthly_report.py`**, and related tooling.
