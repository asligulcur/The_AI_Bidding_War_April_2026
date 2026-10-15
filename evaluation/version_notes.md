# Evaluation harvest — version pin

**Auto-generated** by `scripts/export_evaluation/write_version_notes.py` when you run `python scripts/export_evaluation.py`. Regenerate by re-running the export; do not rely on stale pins after new logs.

| Field | Value |
|--------|--------|
| **Export date** | 2026-04-18 |
| **`ANTHROPIC_MODEL`** | `claude-sonnet-4-6` (from project `.env`) |
| **Scenarios in `test_cases.csv`** | `1–11` (11 row(s)) |
| **Harvest command** | `python scripts/export_evaluation.py` |
| **Harvest log selection** | **strict** (newest log per scenario only) |
| **`config/scenarios.json`** | As evaluated at export; scenario **`mode`** (`standard` / `malicious`) overrides **`BUYER_TYPE`** when using `orchestrator.py --id` (see project `README.md`). |
| **Git commit** | `N/A` (not a git checkout or git unavailable) |

## Evidence files (from `test_cases.csv`)

| Scenario_ID | evidence_or_citation |
|-------------|----------------------|
| 1 | `logs/scenario_1_20260418_192643.log` |
| 2 | `logs/scenario_2_20260418_193523.log` |
| 3 | `logs/scenario_3_20260418_195620.log` |
| 4 | `logs/scenario_4_20260418_200020.log` |
| 5 | `logs/scenario_5_20260418_200759.log` |
| 6 | `logs/scenario_6_20260418_201407.log` |
| 7 | `logs/scenario_7_20260418_201816.log` |
| 8 | `logs/scenario_8_20260418_202603.log` |
| 9 | `logs/scenario_9_20260418_203033.log` |
| 10 | `logs/scenario_10_20260418_203717.log` |
| 11 | `logs/scenario_11_20260418_204116.log` |

**Authoritative paths:** `evaluation/test_cases.csv` column **`evidence_or_citation`**. Re-run orchestrator scenarios and export again if you replace logs.

## Notes

- With **`orchestrator.py --id`**, per-scenario **`mode`** in **`config/scenarios.json`** overrides **`BUYER_TYPE`** for that run.
- **Model id:** If **`ANTHROPIC_MODEL`** is **`claude-sonnet-4-6`**, that reflects **Anthropic**’s plan to deprecate the earlier Sonnet 4 snapshot (**`claude-sonnet-4-20250514`**) used in Phase 2 **in June 2026**. See **`README.md`** → Known limitations and **`evaluation/failure_log.md`**.
