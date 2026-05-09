# Multi-seed variance (standalone)

**Input:** **`logs/evidence_log_*.json`** only (orchestrator session / scenario evidence JSON).  
The script parses each file directly — **no** `export_evaluation.py`, **no** `test_cases.csv`, **no** full 11-scenario harvest.

**Output:**

| File | Purpose |
|------|---------|
| **`runs.csv`** | One row per included evidence session (latest N per selected scenario id). **`Session_ended_no_contract`** = **Y** only when the session ended with **no** executed contract (**Status** NO_AWARD), not for intermediate human *no* before a later *yes*. |
| **`MULTI_SEED_VARIANCE_REPORT.md`** | Outcome **distributions**, mapping to Phase 2 multi-seed feedback. |

Regenerate after new orchestrator runs:

```bash
python scripts/collect_multi_seed_variance.py
python scripts/collect_multi_seed_variance.py --runs 5 --scenarios 4,8 --logs-dir logs
```

Default: **5** most recent `evidence_log_*.json` files per scenario **4** and **8** (by mtime under `logs/`).
