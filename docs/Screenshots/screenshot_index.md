# Screenshot Index — The AI Bidding War (Phase 3)

**Project:** CMU Agentic Systems Studio · Track A · The AI Bidding War
**Author:** Asli Gulcur (solo)
**Harvest date:** 2026-04-18
**Models used:** Claude Sonnet 4.6 (buyer, vendors, Strategic Advisor)

---

This index follows the template specified in the Agentic Systems Studio assignment brief
(page 15: *Screenshot index template*).

The project is a CLI-based Python orchestrator with no graphical user interface. In accordance
with the assignment brief's substitution clause for non-screen-based projects (page 12:
*"substitute workflow screenshots, story maps, Twine views, orchestration boards, or equivalent
visual evidence"*), the nine figures below are composed visual evidence panels rather than UI
screen captures. Every figure embeds verbatim content from the project's own logs, configuration,
or documentation, with explicit line citations in each figure's source footer.

---

## Index

| # | `screenshot_file` | `what_it_shows` | `why_it_matters` | `where_it_is_discussed_in_the_report` |
|---|-------------------|-----------------|------------------|---------------------------------------|
| 1 | `01_home.png` | CLI invocation and session startup banner. Shows `python orchestrator.py --id 1` and the verbatim opening of `scenario_1_20260418_192643.log` (session_id, started_at, mode, budget, hard_ceiling, relax_public_broadcast). An annotation panel names what the orchestrator initializes at cold start (config, personas, advisor, guardrail, API client). | This is the project's entry point and the first thing a reviewer sees. It establishes that the system is deterministic (config-driven), has a unique session ID per run, and enforces the $15,000 ceiling in code — all before Round 1 begins. | Supplementary evidence supporting Final Report § 2 (Architecture and Design Choices) and § 3 (Implementation and Build Summary); not embedded inline. Referenced via README § Setup and How to Run. |
| 2 | `02_main_flow.png` | The main interaction: hub-and-spoke architecture diagram on the left (sourced from the project's canonical architecture SVG), with a 6-step per-round flow panel on the right. Each step includes a verbatim artifact from `scenario_1_20260418_192643.log` (BID_JSON, bid_summary, AWARD_JSON, STRATEGIC AUDIT header, HUMAN APPROVAL, award_contract SUCCESS). | Shows how a single negotiation round traverses the four zones of the architecture: isolated vendor threads → buyer consolidation → Strategic Advisor audit → human gatekeeper → deterministic guardrail. This is the core workflow of the system. | Embedded as Figure 1 in Final Report § 2 (Architecture and Design Choices). Also referenced in Phase 2 §§ 3 (Architecture), 6 (Tools, Memory, Data). |
| 3 | `03_evidence_view.png` | The complete evidence chain for one SUCCESS award (Scenario 1, Round 3), line-by-line. Includes the three isolated vendor bids, buyer consolidation, AWARD_JSON, Strategic Audit Summary excerpt, human nudge and re-audit cycle, final approval, and deterministic `award_contract` SUCCESS — each with an explicit line number citation (lines 718, 811, 905, 944, 1074–1082, 1009, 1011, 1084, 1085, 1087). An annotation panel explains why this chain is auditable. | Demonstrates the traceability property of the system: every decision point — bid, award, audit, vote, guardrail — has a corresponding log line that a reviewer can open and verify. This is the evidence layer that makes governance claims falsifiable. | Supplementary evidence supporting Final Report § 4 (Evaluation Setup) and Phase 3 Log Evidence Analysis § Part I Scenario 1; not embedded inline. |
| 4 | `04_history_or_state.png` | The session inventory: all 11 scenario log files from the 2026-04-18 harvest, each with its line count, first-eight-character session ID, scenario title, and SUCCESS / NO_AWARD status. Includes companion `evidence_log_*.json` count. An annotation panel explains the five kinds of state persisted per run. | Shows that every run is preserved as an auditable artifact with a unique session ID tying together the scenario log, the structured JSON event stream, and any contract write. This is the reproducibility surface for the evaluation. | Embedded as Figure 3 in Final Report § 4 (Evaluation Setup). Also referenced in Phase 2 § Tools, Memory, and Data Design. |
| 5 | `05_export_or_artifact.png` | Two output categories. Top card: six verbatim `[award_contract] SUCCESS: Contract Awarded to …` lines from the scenarios that executed contracts (1, 3, 4, 5, 8, 9). Middle card: a sample row from `evaluation/test_cases.csv` showing the ten primary columns (Scenario_ID, Status, Winning_Vendor, Final_Award_Price, Savings, Rounds, Feasible_Band, Human_Intervention, evidence_or_citation). Bottom: additional artifact locations (contract.txt, CFO narrative, final evaluation report). | Shows what the system exports: **`logs/contract.txt` is overwritten** on each successful award (latest snapshot only; per-scenario awards remain in **`logs/scenario_*.log`** / **`evidence_log_*.json`**), machine-readable CSV evaluation tables regenerable via `scripts/export_evaluation.py`, and an optional offline executive narrative. These are the portable artifacts a reviewer or operator can consume. | Supplementary evidence supporting Final Report § 4 (Evaluation Setup) and § 5 (Results); not embedded inline. Artifacts listed in Final Report Appendix (Evidence package). |
| 6 | `06_evaluation_view.png` | The full Results vs Baseline table for all eleven scenarios, scored on two independent layers (Governance and Negotiation). Includes a KPI strip (11 scenarios, 11/11 governance pass, 9/1/1 negotiation pass/fail/partial, 6 SUCCESS, 5 NO_AWARD), per-row Status pills (SUCCESS / NO_AWARD with subtype), Governance / Negotiation pass pills, final award prices, and evidence log filename per row. | Shows the complete Phase 3 evaluation outcome at a glance. The two-layer scoring matters: a run can pass governance and fail negotiation (Scenario 2, by design) or pass both with different award prices. No executed award exceeded $15,000 in the harvest. | Embedded as Figure 4 in Final Report § 5 (Results). Also referenced in Phase 3 evaluation report § Results vs Baseline (2026-04-18 harvest). |
| 7 | `07_failure_case.png` | Boundary case: Scenario 6 (Compromised $17k Emergency Override). Shows the verbatim covert "buyer-only brief" attempting to steer an above-ceiling award (line 291), then the buyer's finalize-segment response: a merit-based Vendor C AWARD_JSON (line 1190), a proactive compliance-review flag with an inspector-general escalation recommendation (lines 1200–1202), the human's finalize veto (line 1205), and the session end with `contract_executed=False` (line 1208). A three-column footer explains what the attack tried, what the system did, and what it demonstrates. | This is the single most vivid evidence in the harvest of defense-in-depth working as designed: model alignment refused the corrupt persona first, the Strategic Advisor documented the integrity incident, and the human gatekeeper exercised terminal judgment to reject even the merit-based in-budget alternative. No contract was ever written. | Embedded as Figure 5 in Final Report § 6 (Failure Analysis). Also referenced in Phase 3 evaluation report §§ FL-001, FL-003 and Phase 3 Log Evidence Analysis § Part I Scenario 6. |
| 8 | `08_settings_or_controls.png` | The control surface: three representative scenarios (1, 6, 11) from `config/scenarios.json` shown as JSON — standard, malicious, and COI modes — with field values sourced from `docs/SCENARIOS_AND_RFPS.md` (Scenario 11's `buyer_private_brief` is condensed for layout; full text in the source file). A reference panel on the right documents each of the six parameterization fields: `mode`, `budget`, `hard_budget_ceiling`, `buyer_private_brief`, `requirements`, `relax_public_broadcast`. | Shows how the system is parameterized without a GUI. The distinction between `budget` (internal target, visible to the buyer) and `hard_budget_ceiling` (enforced by the deterministic guardrail) is the core design choice that separates negotiation pressure from policy enforcement. The `buyer_private_brief` field demonstrates the isolation boundary in action — it reaches the buyer but never the vendors. | Embedded as Figure 2 in Final Report § 3 (Implementation and Build Summary). Also referenced in Phase 2 § 5 (Scope, Boundaries, and Governance). |
| 9 | `09_cfo_narrative.png` | The CFO monthly oversight artifact. Rendered sample of `CFO_narrative_2026-04.md` for the April 2026 period (Phase 2 snapshot): total contracted spend ($83,800), sessions-with-award ratio (6/12), zero hard-ceiling violations, per-scenario award breakdown, intervention counts (13 governance nudges, 23 human aborts, 24 strategic audit runs), and three red-flag themes for oversight attention. A reference panel on the right explains the role of this artifact — offline batch, not in the live loop — and the generation command (`python scripts/cfo_monthly_report.py --month 2026-04`). | Shows that oversight is not limited to in-session controls. The system produces a monthly executive-readable narrative that surfaces control-effectiveness data (ceiling violations, audit coverage, nudge response rates) and process-improvement opportunities (integrity concerns, value-optimization gaps) to CFO, audit, and procurement leadership — enabling quarterly reporting and control-effectiveness review. This is the oversight-and-process-improvement layer of the architecture. | Embedded as Figure 6 in Final Report § 7 (Governance and Safety Reflection). Also introduced in § 2.G (Oversight extends beyond the live loop) as a design rationale. |

---

## Source and verification policy

Every figure includes a source-citation footer at the bottom of the image. Claims made in these
figures are either:

- **Verbatim** from a named log file with the line number or range cited (all `BID_JSON`,
  `AWARD_JSON`, `HUMAN APPROVAL`, `[award_contract] SUCCESS`, Strategic Audit Summary text,
  session banners, and the buyer-private brief in Scenario 6); or
- **Structural** descriptions (architecture, component names, field semantics) sourced from
  the project's own documentation — Phase 2 report, `docs/SCENARIOS_AND_RFPS.md`, the
  canonical architecture SVG — with section references in the footer.

No content in these figures was generated from training knowledge or external sources. A
reviewer can reproduce every figure by opening the named log file and reading the cited lines.

## File locations

All nine PNG files are in `docs/screenshots/` in the project repository (relative to the
Phase 3 submission root). This index file (`screenshot_index.md`) sits alongside them and
is also referenced in the project `README.md` under the *Folder Guide* section.
