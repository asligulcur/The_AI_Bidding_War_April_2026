# Multi-seed variance — outcome distributions

**Data source:** ``logs/evidence_log_*.json`` only (orchestrator session evidence). **No** ``export_evaluation.py``,
**no** ``test_cases.csv`` — partial re-runs (e.g. scenarios **4** and **8** only) are sufficient.
It supports **Phase 2 instructor feedback** (multi-seed / stochasticity): report **distributions**,
not single point estimates, for **borderline** budget scenarios. The course example named
scenarios **4** and **5** at the **\$15,000** ceiling; this project uses **4** (near-ceiling tradeoffs)
and **8** (exact **\$15,000** bind in the pinned harvest) as the robust pair — see project memo.

## Parameters

- **Scenarios included:** 4, 8
- **Why 4 and 8:** Phase 2 feedback calls for **borderline** budget stress and outcome **distributions**, not a single run. **4** is the project’s near-**\$15,000** analysis case (realistic ceiling tradeoffs); **8** is the **exact** **\$15,000** bind from the pinned harvest, so we sample variance under both **near-ceiling** and **hard** ceiling pressure.
- **Runs per scenario:** up to **5** most recent **evidence JSON** files (mtime under ``logs/``).
- **Source files:** ``logs/evidence_log_*.json`` — same artifacts the orchestrator writes each run; **not** the evaluation CSV harvest.

## Mapping to instructor feedback

| Feedback theme | How this report addresses it |
|----------------|------------------------------|
| Outcome stability under LLM stochasticity | Multiple independent runs per scenario; frequency tables below. |
| *Distributions* vs point values | Aggregated counts and price buckets — not one harvested row. |
| Borderline / ceiling-relevant stress | Scenarios **4** and **8** (project analysis; legacy **5** not required). |

## Run table (CSV mirror)

Full table: **[``evaluation/multi_seed_variance/runs.csv``](runs.csv)**.

``runs.csv`` column **Session_ended_no_contract** is **Y** only when the session ended **without** an executed contract (**Status** = NO_AWARD), not when a human declined an *earlier* proposal before approving a later one.

| # | Scenario | Started (UTC) | Model | Status | Final \$ | Winner | At \$15k ceiling | No contract |
|---|----------|---------------|-------|--------|-----------|--------|-------------------|-------------|
| 1 | 4 | 2026-04-20T22:31:31 | claude-sonnet-4-6 | SUCCESS | $13,500.00 | Vendor C | N | N |
| 2 | 4 | 2026-04-20T22:22:45 | claude-sonnet-4-6 | NO_AWARD | — | — | — | Y |
| 3 | 4 | 2026-04-20T22:15:06 | claude-sonnet-4-6 | SUCCESS | $13,500.00 | Vendor C | N | N |
| 4 | 4 | 2026-04-20T22:05:39 | claude-sonnet-4-6 | SUCCESS | $15,000.00 | Vendor A | Y | N |
| 5 | 4 | 2026-04-20T21:56:58 | claude-sonnet-4-6 | SUCCESS | $14,500.00 | Vendor A | N | N |
| 6 | 8 | 2026-04-20T23:05:03 | claude-sonnet-4-6 | SUCCESS | $14,200.00 | Vendor A | N | N |
| 7 | 8 | 2026-04-20T22:59:03 | claude-sonnet-4-6 | SUCCESS | $13,500.00 | Vendor C | N | N |
| 8 | 8 | 2026-04-20T22:52:16 | claude-sonnet-4-6 | NO_AWARD | — | — | — | Y |
| 9 | 8 | 2026-04-20T22:45:30 | claude-sonnet-4-6 | SUCCESS | $13,500.00 | Vendor C | N | N |
| 10 | 8 | 2026-04-20T22:37:08 | claude-sonnet-4-6 | SUCCESS | $14,200.00 | Vendor A | N | N |

## Outcome distributions

### Scenario 4

- **Status (deal outcome):** NO_AWARD: 1; SUCCESS: 4
- **Outcome_detail:** contract_executed: 4; human_veto_or_declined: 1
- **Final award price (SUCCESS only):** 13500.0: 2; 14500.0: 1; 15000.0: 1
- **SUCCESS runs at \$15,000.00 (exact):** 1 / 4 in this sample.

### Scenario 8

- **Status (deal outcome):** NO_AWARD: 1; SUCCESS: 4
- **Outcome_detail:** contract_executed: 4; human_veto_or_declined: 1
- **Final award price (SUCCESS only):** 13500.0: 2; 14200.0: 2
- **SUCCESS runs at \$15,000.00 (exact):** 0 / 4 in this sample.

## Interpretation (reliability claims)

Use these frequencies when arguing **whether outcomes are stable** under repeated sampling.
Spread in **Status** or **Final_Award_Price** under SUCCESS shows negotiation outcomes
are **not** deterministic at the LLM layer; **guardrails** and **human gates** remain as in code.

*Regenerate:* ``python scripts/collect_multi_seed_variance.py``
