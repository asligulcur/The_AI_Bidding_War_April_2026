# Procurement simulation — roadmap (impact vs effort)

**Purpose:** Single index of **future** procurement process and feature options for this repo. Nothing here is required for the **core Track A** deliverable. Use it to pick **portfolio** or **post-submission** work in a disciplined order.

**Legend**

| | |
|--|--|
| **Impact** | **H** = strong payoff for realism, evaluation, or cited research alignment · **M** = meaningful · **L** = niche or narrative-only |
| **Effort** | **L** = days or less · **M** = roughly 1–2 weeks part-time · **H** = multi-week / architectural |
| **Priority** | **P1** = best first bets · **P2** = next wave · **P3** = larger or specialized bets · **P4** = documentation / story without code |

---

## Full matrix: options × impact × effort

| # | Option | Impact | Effort | Priority | Notes |
|---|--------|--------|--------|------------|--------|
| 1 | **Minimal multi-attribute offers** — optional fields on existing `BID_JSON` / `AWARD_JSON` (e.g. `tier`, `support_band`) with **one** canonical `price` for `award_contract` | H | M | **P1** | Detailed design: **[Multi-option negotiation](#multi-option-negotiation)** (below). Bounded slice: one scenario + harvest column + docs. |
| 2 | **Evaluation automation** — batch script to run all scenario IDs, then `scripts/export_evaluation/harvest_evidence.py` + `scripts/export_evaluation/fill_evaluation_rubric_section3.py` (outputs under **`evaluation/`**) | M | L | **P1** | Reduces manual error before demos; no new procurement semantics. |
| 3 | **Weighted scorecard (simple)** — deterministic scoring of **parsed** fields + log excerpt for “shortlist” story | M | M | **P1** | Can prototype **without** LLM committee; feeds two-phase phase-1. |
| 4 | **Two-phase procurement** — phase 1: many suppliers / light responses → **shortlist 3** → phase 2: current orchestrator | H | H | **P2** | Research + design: **[Two-phase procurement](#two-phase-procurement)** (below). Touches runners, CSV prefixes, scenarios. |
| 5 | **Commercial terms beyond price** — optional schema for payment terms, SLA tier, term length; guardrail still on **price** unless policy extended | M | M | **P2** | Legal realism; requires advisor + harvest + rubric awareness. |
| 6 | **Security / risk questionnaire flow** — structured Q&A turn before negotiation (enterprise SaaS pattern) | M | M | **P2** | Mostly new “phase” or scenario family; reuses isolation + logging. |
| 7 | **Multi-stakeholder buyer** — 2+ agent personas with **weights**; conflict resolution or aggregate score | M | H | **P2** | Stress-tests governance; orchestration + prompts + evaluation. |
| 8 | **Two-stage technical / commercial** (sealed phases, public-sector style) | M | H | **P3** | See Oracle-style two-stage RFQ in **[Two-phase procurement](#two-phase-procurement)**; heavy UX/rules. |
| 9 | **Post-award** — implementation milestones, renewal, **change orders** | M | H | **P3** | New state machine; weak overlap with current “award = terminal” flow. |
| 10 | **E-auction / reverse auction** mode | M | H | **P3** | Different mechanism from multi-round bilateral negotiation. |
| 11 | **ESG / diversity / secondary criteria** in scoring | L | M | **P3** | Policy weighting; easy to over-promise without domain review. |
| 12 | **ERP / PO / contract repo integration** (API stubs) | L | H | **P3** | Integration story for employers; not core to agent behavior. |
| 13 | **Narrative-only** — sole-source justification, incumbent bias, protest windows, committee **process** in prose | M | L | **P4** | For final report / interview prep; no code. |

**Reading order:** P1 = best first bets (matrix **Priority** column); P2–P4 follow. Sweet spot for effort: **(1)–(3)**; strategic bets **(4)–(7)**; defer **(8)–(12)** unless scope demands; cheap wins **(13)** and keeping **`docs/Reference Research/Reference_Synthesis.md`** in sync with code and rubric changes.

---

## Links to detailed notes in-repo

| Topic | Where |
|--------|--------|
| Multi-option / structured offers (buyer + vendor) | **[Multi-option negotiation](#multi-option-negotiation)** (below) |
| Wide solicitation → shortlist → finalist negotiation | **[Two-phase procurement](#two-phase-procurement)** (below) |
| Evaluation baseline / pass-fail | **`evaluation/evaluation_rubric.md`** |
| Readings + methodology | **`docs/Reference Research/Reference_Synthesis.md`** |

---

## What not to overload

- Pick **one** **P1** code item and **one** **P2** item per portfolio release cycle; avoid parallel **H**-effort tracks.  
- Any change that touches **`BID_JSON` / `AWARD_JSON`** must update **`scripts/export_evaluation/harvest_evidence.py`** and the **§3** automation expectations in **`scripts/export_evaluation/fill_evaluation_rubric_section3.py`** (see **[Multi-option negotiation](#multi-option-negotiation)** risks).

---

## Multi-option negotiation

**Status:** Future work — not required for the core Track A submission. Use this note when returning to the idea.

**Purpose:** Record design intent for **structured** support when parties offer **more than one** priced package or path (e.g. good / better / best, or buyer counter-options), beyond what prose alone can guarantee in logs and CSVs.

### Current behavior (baseline)

- **Vendors** respond each round with free text plus **one** machine-parseable line: `BID_JSON: { "vendor_id", "price", "summary" }`. The orchestrator stores **one** parsed object per vendor per round (`orchestrator.py`).
- **Buyers** finalize with **one** `AWARD_JSON` line: `vendor_id`, `vendor_name`, `price` — the deterministic guardrail (`skills/award_contract.py`) evaluates **vendor name + price** only.
- **Harvest** (`scripts/export_evaluation/harvest_evidence.py`) assumes **one** price per vendor for round-1 metrics and **one** final award price for savings / bargaining zone.
- Multi-tier or “Option A vs B” content can appear in **natural language** only; there is **no** first-class schema for **multiple simultaneous structured offers** from the **buyer** to vendors.

### Desired enhancement: buyer offering multiple options “in response”

**Idea:** Allow the buyer’s turn (e.g. counter-proposal or “choose one of these paths”) to carry **multiple** explicit options—each with a **price** and short **scope**—so evaluation and audit can see **comparable** structured alternatives, not only narrative.

**Why it might matter:** Aligns with real RFP / negotiation practice where buyers ask vendors to react to **tiered** or **alternative** constructs; supports a clearer **multi-attribute** story alongside cited work (e.g. language-mediated negotiation with structured settlement signals — see **`docs/Reference Research/Reference_Synthesis.md`**).

**Design constraints (if implemented):**

1. **Single binding commitment at award time:** The orchestrator should still converge on **one** `AWARD_JSON` (or successor schema) for `award_contract` — **one** vendor + **one** price for the executed deal (unless the guardrail is intentionally extended, which is out of scope for a minimal slice).
2. **Avoid silent breakage:** Any new JSON shape must be updated in **one** place: prompts, `_extract_json_line` / parsers, **harvest**, and optionally `scripts/export_evaluation/fill_evaluation_rubric_section3.py` heuristics — see risks below.
3. **Prefer a small, testable slice:** Document schema + **one** scenario + harvest fields + one golden log path — not a last-minute full refactor.

### Related: vendor-side multiple structured options

A parallel enhancement is **vendors** emitting **multiple** priced rows in structured form (e.g. array of offers in one `BID_JSON`). That shares the same **harvest** and **guardrail** questions (which price is “round 1” for savings? which line is binding?). See the same risk list.

### Risks (summary)

- **Parsing:** First vs last `BID_JSON` / `AWARD_JSON` line; nested JSON vs one-line regexes in `scripts/export_evaluation/harvest_evidence.py`.
- **Metrics:** `Savings_Vs_Winner_Round1`, `Winning_Vendor_Round1_Bid`, `Final_Price_In_Feasible_Band` assume a **single** comparable price per vendor per round — multi-option requires explicit rules.
- **Scope creep:** Changing all 11 scenarios at once; prefer **one** scenario or a flag-driven path first.

### Suggested implementation order (when/if you pick this up)

1. Write the **schema** (buyer multi-option + how award collapses to one price) in this file or `README.md`.
2. Adjust **buyer** `agent.md` + orchestrator buyer round only for **one** scenario id.
3. Extend **harvest** with optional column(s) or a string summary of chosen vs offered options.
4. Run `scripts/export_evaluation/harvest_evidence.py` + `scripts/export_evaluation/fill_evaluation_rubric_section3.py` and confirm **§3** / CSVs still make sense.
5. Update **evaluation rubric** §2 for that scenario if pass/fail criteria change.

### References (multi-option)

- **[Two-phase procurement](#two-phase-procurement)** — optional **macro** pipeline (many suppliers → shortlist → 3-way negotiation); industry notes and links.
- `orchestrator.py` — `BID_JSON` / `AWARD_JSON` extraction and buyer/vendor loops.
- `scripts/export_evaluation/harvest_evidence.py` — `BID_JSON_LINE_RE`, round-1 extraction, `AWARD_JSON`, `evaluation/test_cases.csv`.
- `evaluation/evaluation_rubric.md` — per-scenario baselines; update if new behavior is scenario-specific.
- `docs/Reference Research/Reference_Synthesis.md` — language vs structure; AgenticPay-style structured signals.

---

## Two-phase procurement

**Status:** Research note + future simulation idea — **not** implemented. The current build is **three vendors in one negotiation loop** (`orchestrator.py`, `config/scenarios.json`). Use this when extending toward a **pipeline** that mirrors enterprise sourcing.

### Idea (stylized)

1. **Phase 1:** Buyer issues an **RFP** (or **RFI**-style qualification) to **many** suppliers (e.g. **15–20**) and collects lighter or full proposals.  
2. **Down-select:** Score or qualify responses, then **shortlist** (e.g. **3**) finalists.  
3. **Phase 2:** Run **structured negotiation** (or a second RFP round) **only** with the shortlist — comparable to the project’s hub-and-spoke, multi-round, guardrailed flow.

This is **illustrative**, not a single statutory rule; real programs vary by category, regulation, and team capacity.

### What external practice tends to say

#### Multi-stage / shortlist patterns are standard

- **RFI → narrow → RFP:** Use a **Request for Information** (or pre-qualification) to screen vendors, then issue a **full RFP** to a **smaller** qualified set. See [Planergy — RFP procurement and pre-qualification](https://planergy.com/blog/rfp-procurement/) (“Pre-Qualify Vendors” / RFI before RFP).  
- **Evaluate → shortlist → deepen:** After proposals, teams **shortlist** finalists for demos, clarification, or **best-and-final** pricing. [Ivalua — vendor selection steps](https://www.ivalua.com/blog/vendor-selection-process/) includes **Create a Shortlist** before negotiation.  
- **Two-stage RFQ (public / regulated):** Technical responses evaluated first, then commercial — e.g. [Oracle Fusion — two-stage RFQ](https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/how-you-use-a-two-stage-rfq.html) (government / public-sector style).

#### Typical **counts** (rules of thumb, not laws)

| Topic | Common guidance in industry articles |
|--------|--------------------------------------|
| How many **invited** to a **single** full RFP | Often **~5–8** “qualified” bidders to balance competition and **evaluation load** — e.g. [Sparrow Genie — RFP process](https://www.sparrowgenie.com/blog/rfp-process). [Responsive — RFP guide](https://www.responsive.io/blog/rfp-process-guide) gives an example: use market research to invite a **short list** (e.g. **~six**) with the goal of **~three** strong options to compare. |
| **Shortlist** for finals | Often **2–4** finalists for deeper steps — [Sparrow Genie](https://www.sparrowgenie.com/blog/rfp-process), [Dryden — RFP timeline](https://www.drydengroup.com/blog/rfp-process-timeline) (“two to four finalists”), [G2 — narrowing to a shortlist](https://learn.g2.com/narrowing-rfp-candidates-into-a-shortlist). |
| **Larger** invitation counts | Some datasets show **many** invitations per event; [Euna Solutions](https://eunasolutions.com/resources/if-i-send-more-vendor-invitation-will-i-get-more-proposals/) notes diminishing returns and that **quality** of targeting matters vs. raw volume. **15–20** can be plausible for a **broad** first wave (e.g. RFI or open market outreach), less often cited as “invite 20 to a **full** heavy RFP” without strong process design. |

#### How to phrase this in a report or portfolio

- **Defensible:** “Real procurement often uses **qualification** and **shortlisting** before final negotiation; our simulation could extend to a **phase-1 market response** and **phase-2 finalist negotiation**.”  
- **Calibrated:** If you use **15–20 → 3**, frame phase 1 as **RFI / qualification / lighter response** unless you also model **evaluation staffing** and **scoring** for 20 full proposals.  
- **Cite:** Use **one or two** of the links above for “industry practice,” not as legal advice.

### Relation to this repository

| Current repo | Possible extension |
|--------------|-------------------|
| **3 vendors**, **3 rounds**, single session | **Phase 1:** batch jobs or scripted agents simulate **N** vendors returning **scores** or **structured summaries**; **Phase 2:** feed **3** vendor personas into the **existing** orchestrator (or duplicate scenario ids). |
| `config/scenarios.json` | New scenario types or a **meta-scenario** runner that chains “qualification” + “finalist run.” |
| Evidence / harvest | Separate CSV or prefix for **phase-1** vs **phase-2** logs to avoid conflating metrics. |

See also **[Multi-option negotiation](#multi-option-negotiation)** (structured multi-option offers within a round). External URLs for this section are cited **inline** above (no duplicate bibliography list).

---

*Last updated: roadmap index plus multi-option and two-phase detail — adjust priorities as course or employer requirements change.*
