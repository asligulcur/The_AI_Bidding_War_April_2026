# The AI Bidding War

Hub-and-spoke **multi-agent procurement**: a **buyer** and **three isolated vendors (A/B/C)** negotiate for up to **three rounds**, with **Strategic Audit** (LLM), **human approval**, optional **governance nudges**, and a **deterministic $15,000** award guardrail (`skills/award_contract.py`).

**Vendor-visible buyer text:** The same buyer assistant message is relayed to every vendor each round; prompts aim to limit cross-vendor leakage in that shared channel.

**Project video:** see **[Walkthrough video](#walkthrough-video)**. Submit with **`Final Project AI Bidding War.zip`**.

---

## Team members

| Name | Role |
|------|------|
| **Asli Gulcur** | Solo author — design, implementation, evaluation |

---

## Selected track

**Track A — Technical Build** (CMU Agentic Systems Studio)

---

## Contents

- [Team members](#team-members)
- [Selected track](#selected-track)
- [Setup instructions](#setup-instructions)
- [How to run or access the project](#how-to-run-or-access-the-project)
- [Required dependencies or platforms](#required-dependencies-or-platforms)
- [Folder guide](#folder-guide)
- [Walkthrough video](#walkthrough-video)
- [Scenarios](#scenarios)
- [Evaluation and outputs](#evaluation-and-outputs)
- [Known limitations](#known-limitations)
- [Scripts](#scripts)
- [Evaluation folder](#evaluation-folder) (detailed semantics & CSV notes)
- [Governance flow](#governance-flow)
- [Canvas submission packet (export to PDF)](#canvas-submission-packet-export-to-pdf)
- [Optional: CFO, diagrams](#optional-cfo-diagrams)

---

## Setup instructions

From the **project root** (directory containing **`orchestrator.py`**):

1. **Python 3.10+** (3.12 recommended).
2. Create a virtual environment and install dependencies:

```bash
cd "/path/to/Final Project AI Bidding War"
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Create **`.env`** in the project root (do not commit secrets):

| Variable | Purpose |
|----------|---------|
| **`ANTHROPIC_API_KEY`** | Required to **re-run** the orchestrator or offline CFO narrative. |
| **`ANTHROPIC_MODEL`** | Optional; if unset, code falls back to **`claude-sonnet-4-6`**. **Phase 2** snapshot id and **Anthropic** deprecation window: **Known limitations** (model lifecycle). |
| **`BUYER_TYPE`** | Optional; overridden by scenario **`mode`** when using **`--id`**. |
| **`ORCHESTRATOR_CHAR_DELAY`** | Optional; `0` disables typing effect. |
| **`ORCHESTRATOR_TYPE_WORD_THRESHOLD`** | Optional; long messages switch to word-by-word display. |

---

## How to run or access the project

**Primary runtime (interactive CLI):**

```bash
python orchestrator.py --id <N>
```

- **`--id`** — Scenario id from **`config/scenarios.json`** (1–11; default is smallest id, usually **1**).
- **RFP** — On the first prompt, paste custom text or send **EOF** (Ctrl-D on an empty line) to use the scenario **`requirements`**.

**Quick smoke run:** `python orchestrator.py --id 1` — allow several minutes; Strategic Audit and **human approval** (`yes` / `no`) are part of the flow.

**Regenerate evaluation artifacts** (after `logs/` contains runs):

```bash
python scripts/export_evaluation.py
```

Optional: `python scripts/export_evaluation.py --allow-fallback` if the newest log per scenario is unusable.

**Review vs re-run:** Reading committed **`evaluation/`** and **`logs/`** does **not** require an API key. **Re-running** the orchestrator or **`scripts/cfo_monthly_report.py`** needs **`ANTHROPIC_API_KEY`**.

**Outcomes:** You may see a completed award, **`NO_AWARD`**, or a **guardrail block** (scenario **2** is adversarial by design). A successful guardrail write **overwrites** **`logs/contract.txt`** with that award only (not a cumulative history); full history lives in **`logs/scenario_*.log`** and **`logs/evidence_log_*.json`**.

---

## Required dependencies or platforms

| Category | Requirement |
|----------|-------------|
| **Runtime** | Python **3.10+** (3.12 recommended); packages from **`requirements.txt`**. |
| **LLM** | **Anthropic** API (**`ANTHROPIC_API_KEY`** in **`.env`**) for orchestrator and CFO narrative script. |
| **Optional — PDF / HTML** | **pandoc** and **Google Chrome** on `PATH` (or **`CHROME_PATH`**) if you run **`scripts/render_canvas_submission_packet.py`**, **`scripts/render_cfo_pdf.py`**, or **`scripts/render_ai_usage_pdf.py`**. Not required for orchestrator, harvest, or CFO Markdown generation. |
| **Platform** | macOS / Linux / Windows supported for Python; paths in docs assume Unix-style shell unless noted. |

---

## Folder guide

| Path | Role |
|------|------|
| **`orchestrator.py`**, **`config/scenarios.json`**, **`agents/`**, **`skills/award_contract.py`** | Negotiation runtime |
| **`evaluation/`** | CSVs, rubric, **`FINAL_EVALUATION_REPORT.md`**, failure log, **`multi_seed_variance/`** — see **[Evaluation and outputs](#evaluation-and-outputs)** and **[Evaluation folder](#evaluation-folder)** |
| **`scripts/`** | **`export_evaluation.py`** pipeline, PDF helpers, CFO script — see **[Scripts](#scripts)** |
| **`docs/Phase 1/`** | Phase 1 PDF export |
| **`docs/Phase 2/`** | Archived Phase 2 PDF(s) (e.g. **`Phase 2 AI_Usage.pdf`**) |
| **`docs/Phase 3/`** | **`Phase3_Final_Report_4_21_2026.pdf`**, **`Phase3_Log_Evidence_Analysis.pdf`**, **`Phase3_Supplementary_Evaluation_Report.pdf`**, **`Phase3_AI_USAGE.pdf`**, **`Multi Seed Variance Evaluation 4_21_2026.pdf`**, **`CANVAS_SUBMISSION_PACKET.md`**, **`CANVAS_SUBMISSION_PACKET_executive.html`** / **`CANVAS_SUBMISSION_PACKET_executive.pdf`** ( **`scripts/render_canvas_submission_packet.py`** ), **`canvas_packet_executive.css`**, **`SCENARIOS_AND_RFPS.md`** |
| **`docs/Canvases/`** | Multi-agent **architecture & spec** canvases (**`MA_ArchCanvas_The_AI_Bidding_War.html`**, **`MA_SpecCanvas_The_AI_Bidding_War.html`**) and **`agents/`** per-role / component HTML |
| **`docs/Future Roadmap/`** | **`PHASE_3_IMPLEMENTATION.md`** (buyer public-channel policy, backlog), **`procurement_roadmap.md`** |
| **`docs/Reference Research/`** | **`Reference_Synthesis.md`** |
| **`docs/Screenshots/`** | **`screenshot_index.md`** and screenshot assets |
| **`docs/System Architecture Diagram/`** | **`ai_bidding_war_system_architecture.svg`** |
| **`media/`** | **`The AI Bidding War - Procurement (5 mins).mov`** — see **[Walkthrough video](#walkthrough-video)** |
| **`CFO Reports/`** | Optional executive Markdown (e.g. **`CFO_narrative_*.md`**) from **`cfo_monthly_report.py`** |
| **`logs/`** | Session logs and evidence JSON |
| **`config/README.md`** | Short glossary for **`scenarios.json`** fields |
| **`requirements.txt`**, **`package.json`** | Python dependencies; optional Node metadata |
| **`Dockerfile`**, **`docker-compose.yml`** | Optional container build — **not used** for author workflow or Phase 3 runs (primary path: venv + **`python orchestrator.py`**) |

---

## Walkthrough video

**Submitted walkthrough:** **`media/The AI Bidding War - Procurement (5 mins).mov`** **(~5 min)** — inline with the Phase 2 feedback.

**Video (Scenario 2 — model id for recording only):** The on-screen **malicious buyer / guardrail** segment may be recorded with **`python orchestrator.py --id 2`** and **`ANTHROPIC_MODEL=claude-sonnet-4-20250514`** (Phase 2 Model) in **`.env`**. **Anthropic** has announced deprecation of that id in **June 2026**; use it **for that demo segment** only so the **governance chain** (Strategic Audit, HITL, `award_contract`) is easy to follow. **This project’s Phase 3 default** in **`.env`** is **`claude-sonnet-4-6`**; **evaluation** and the pinned **2026-04-18** harvest in **`evaluation/`** reflect **4.6**. The **orchestrator and guardrails** are unchanged — only LLM *dialogue shape* varies; see **FL-001** ([`evaluation/failure_log.md#fl-001`](evaluation/failure_log.md#fl-001)). Restore **`claude-sonnet-4-6`** in **`.env`** after any session that used **`claude-sonnet-4-20250514`** (Phase 2 Model).

---

## Scenarios

Definitions, vendor floors, and optional per-scenario keys (e.g. **`hard_budget_ceiling`**, **`relax_public_broadcast`**, **`buyer_private_brief`**) are in **`config/scenarios.json`**. Summary: **`config/README.md`**.

| ID | Name | `mode` |
|----|------|--------|
| 1 | Baseline Competitive SaaS RFP | standard |
| 2 | Malicious Over-Ceiling Award (Guardrail Test) | malicious |
| 3 | Finance Squeeze: $12k Internal Target | standard |
| 4 | Quality & SLA Over Lowest Price | standard |
| 5 | Stalemate: Probe, Exit, or Deal | standard |
| 6 | Compromised: $17k Emergency Override | malicious |
| 7 | HIPAA Healthcare Compliance | standard |
| 8 | EU Data Residency & GDPR | standard |
| 9 | Rip-and-Replace: Migration + $13k Target | standard |
| 10 | Bid Steering to Preferred Vendor | malicious |
| 11 | Conflict of Interest: Bias & Fairness | standard |

**Buyer folder:** **`mode == "malicious"`** → **`agents/malicious_buyer/`**; otherwise **`agents/buyer/`**.

---

## Evaluation and outputs

**From runs** (orchestrator / guardrail):

| Output | Description |
|--------|-------------|
| **`logs/scenario_*.log`** | Human-readable transcripts |
| **`logs/evidence_log_*.json`** | Structured evidence (turns, audits, awards) — source for harvest and CFO narrative |
| **`logs/contract.txt`** | **Overwritten** when an award executes via guardrail — reflects the **latest** successful award only |
| **`evaluation/*`** | After **`export_evaluation.py`**: rubric, CSVs, tables, **`FINAL_EVALUATION_REPORT.md`**, **`failure_log.md`**, **`version_notes.md`**, **`multi_seed_variance/`** (see **[Scripts](#scripts)**) |
| **`CFO Reports/*.md`** | Optional portfolio narrative (offline batch) |
| **`docs/`** | Phase 2/3 narrative, architecture diagram, canvases; in-repo Phase 3 **`Phase3_AI_USAGE.pdf`**; other Phase 3 **written PDFs** for Canvas may be **zip-only** — see **folder guide** and **[Canvas submission packet](#canvas-submission-packet-export-to-pdf)** |

**Evaluation materials** (where to read results):

| Goal | Where |
|------|--------|
| **Measured results & appendix** | **`evaluation/FINAL_EVALUATION_REPORT.md`** (generated from harvest; do not edit by hand). Produced by **`python scripts/export_evaluation.py`**. |
| **Per-scenario baselines & scored comparison** | **`evaluation/evaluation_rubric.md`** (sections 2–3) |
| **Analysis of logs** | **`docs/Phase 3/Phase3_Log_Evidence_Analysis.pdf`** — narrative review of transcripts and structured evidence. |
| **Architecture & evaluation design** | **`docs/Canvases/`**, **`docs/System Architecture Diagram/`**, **`docs/Phase 3/SCENARIOS_AND_RFPS.md`**, **`docs/Future Roadmap/`** |
| **Multi-seed variance (Phase 2 feedback)** | **`evaluation/multi_seed_variance/`** — **`README.md`**, **`runs.csv`**, **`MULTI_SEED_VARIANCE_REPORT.md`**. Regenerate: **[Scripts](#scripts)** → Scenario runs (multi-seed bullet). |

**Core artifacts (under `evaluation/`):**

- **`test_cases.csv`**, **`evaluation_results.csv`** — harvested from **`logs/`**
- **`FINAL_RESULTS_TABLE.md`** — compact results table
- **`failure_log.md`** — boundary / failure cases
- **`version_notes.md`** — model, date, git hash, evidence snapshot (written at end of export)
- **`multi_seed_variance/`** — re-run outcome distributions (scenarios **4** and **8**; instructor writeups often cite **4** and **5**)

**Status vs Result:** **`test_cases.csv`** → **`Status`** is deal outcome (**`SUCCESS`**, **`NO_AWARD`**, …). **`evaluation_results.csv`** → **`Phase_3_Evaluation`** → **`Result`** is a separate rubric check — not the same as **`Status`**. Each row includes **`Result_Meaning`**. **LLM wording** varies by run; **guardrails**, **harvested columns**, and the report should align with **saved logs** and **code** (see also **[Known limitations](#known-limitations)** — transcript variance). Deeper read — four evaluation claims, **`Status`/`Result`**, and **CSV** semantics: **[Evaluation folder](#evaluation-folder)**.

---

## Known limitations

- **Model lifecycle (Anthropic)** — **`.env`** and code fallbacks use **`claude-sonnet-4-6`**. **Anthropic** **will** deprecate **`claude-sonnet-4-20250514`** (Phase 2 Model) in **June 2026**; use the old id only to compare with archived Phase 2 transcripts. Transcript behavior (including malicious / red-team **dialogue shape**) can differ between snapshots even when **`award_contract`** and orchestration are unchanged—see **`evaluation/failure_log.md`**. 
- **Simulation lab** — Vendors, prices, and narratives are LLM-generated; not production procurement or legal advice.
- **Transcript variance** — Model, temperature, and run-to-run dialogue differ; scored results should be read alongside **`logs/`** and harvest rules, not chat prose alone.
- **Public buyer channel** — Buyer prompts discourage cross-vendor leakage in shared text; the orchestrator does **not** programmatically redact buyer messages before relay. Leakage risk is **mitigated in prompts**, not eliminated in code.
- **Human-in-the-loop** — Approvals and consistency at **`[HUMAN APPROVAL]`** gates affect outcomes and harvest fields (e.g. **`Human_Intervention`**).
- **Export pipeline** — **`FINAL_EVALUATION_REPORT.md`** is **overwritten** by **`scripts/export_evaluation/sync_final_evaluation_report.py`**; do not hand-edit for persistence.

---

## Scripts

Run commands from the **project root** (directory containing **`orchestrator.py`**). Paths below are under **`scripts/`** unless noted.

### Scenario runs (one at a time)

For a fresh harvest after code or prompt changes, run each scenario from the repo root with **`ANTHROPIC_API_KEY`** (and optionally **`ANTHROPIC_MODEL`**) in **`.env`**:

```bash
python orchestrator.py --id <1–11>
```

- **RFP:** On the first prompt, **Ctrl-D** (EOF) on an empty line uses the scenario **`requirements`** from **`config/scenarios.json`**.
- **Interactive:** Strategic Audit and **human approval** (`yes` / `no`) are part of the flow — stay consistent with how you want each case scored (see **`evaluation/evaluation_rubric.md`**).
- **After all scenarios you care about have new `logs/`:** run **`python scripts/export_evaluation.py`** once.
- **`evaluation/version_notes.md`** is **generated** at the end of **`python scripts/export_evaluation.py`** (`write_version_notes.py`).
- **Multi-seed variance (instructor Phase 2 feedback):** run **`python orchestrator.py --id 4`** and **`--id 8`** several times each (same **`.env`**; **`claude-sonnet-4-6`**). Then **`python scripts/collect_multi_seed_variance.py`** — reads **`logs/evidence_log_*.json`** only (no **`export_evaluation.py`** / **`test_cases.csv`**). Writes **`evaluation/multi_seed_variance/runs.csv`** and **`MULTI_SEED_VARIANCE_REPORT.md`** (most recent **5** evidence files per scenario). **Flags and file semantics:** **`evaluation/multi_seed_variance/README.md`**.

### Evaluation pipeline

Single entrypoint:

```bash
python scripts/export_evaluation.py
```

Optional harvest fallback: `--allow-fallback` (forwards to harvest only).

| Step (in order) | Script | Output / effect |
|-----------------|--------|-----------------|
| Harvest | **`export_evaluation/harvest_evidence.py`** | **`evaluation/test_cases.csv`**, **`evaluation/evaluation_results.csv`** from **`logs/`** |
| Rubric §3 | **`export_evaluation/fill_evaluation_rubric_section3.py`** | Updates **`evaluation/evaluation_rubric.md`** section 3 |
| Table | **`export_evaluation/generate_report_table.py`** | **`evaluation/FINAL_RESULTS_TABLE.md`** |
| Failure log | **`export_evaluation/generate_failure_log.py`** | **`evaluation/failure_log.md`** |
| Sync report | **`export_evaluation/sync_final_evaluation_report.py`** | **`evaluation/FINAL_EVALUATION_REPORT.md`**: **rewrites entire file** (§3, harvest, evidence paths, verbatim 1/2/3/6, Appendix A) — do not edit by hand |
| Version pin | **`export_evaluation/write_version_notes.py`** | **`evaluation/version_notes.md`** (model, date, git hash, evidence table from **`test_cases.csv`**) |

**Semantics** (**`Status`** vs **`Result`**, three-layer claims), **CSV column** definitions, and **harvest** behavior (by default, **newest** matching log per scenario id under **`logs/`**): **[Evaluation folder](#evaluation-folder)**.

### Other tooling

| Script | Purpose |
|--------|---------|
| **`render_ai_usage_pdf.py`** | Optional **`docs/Phase 3/AI_USAGE.md`** → **`Phase3_AI_USAGE.pdf`** — **pandoc** + **Chrome**; skip if you maintain the PDF only (see **[Required dependencies](#required-dependencies-or-platforms)**). |
| **`render_canvas_submission_packet.py`** | **`docs/Phase 3/CANVAS_SUBMISSION_PACKET.md`** → **`CANVAS_SUBMISSION_PACKET_executive.html`** + **`CANVAS_SUBMISSION_PACKET_executive.pdf`** — **pandoc** + **Chrome**; use **`--html-only`** if PDF is not needed. |
| **`render_cfo_pdf.py`** | **`CFO Reports/CFO_narrative_*.md`** → PDF — same tools. |
| **`cfo_monthly_report.py`** | Evidence JSON → **`CFO Reports/`** narratives (Anthropic API) |
| **`generate_agent_canvas_html.py`** | Optional canvas regeneration — target paths in script |
| **`ensure-openclaw-path.sh`** | Shell helper |
| **`collect_multi_seed_variance.py`** | **`evaluation/multi_seed_variance/`** — see **`README.md`**; run command in **[Scripts](#scripts)** → Scenario runs. |

**Main runtime:** `python orchestrator.py --id <N>`.

---

## Evaluation folder

### Evaluation claims — four layers (read this)

Separate **code-enforced outcomes** from **LLM prose** so transcripts are not over-interpreted.

1. **Deterministic guardrail** — `award_contract` enforces the hard ceiling; that does **not** depend on how dramatic corrupt **roleplay** looks in the log.
2. **Red-team dialogue** — Transcript “theater” varies; thin or refused corrupt arcs are **not** automatic failures if guardrail, audit, and HITL behaved correctly.
3. **LLM refusal** — Models may decline fraud framing; see **`docs/Phase 3/Phase3_AI_USAGE.pdf`** — **variance**, not an **`orchestrator.py`** bug.
4. **Public-channel compliance** — Buyer broadcast rules are **prompt-level**; the runtime does **not** redact relayed buyer text (leakage / FL-004: **`evaluation/evaluation_rubric.md`**, **`docs/Future Roadmap/PHASE_3_IMPLEMENTATION.md`**).

**Harvest specifics** (e.g. **`Human_Intervention`**, Scenario **2** pass criteria, **`version_notes`**, public **`requirements`** vs **`buyer_private_brief`**) — **`evaluation/evaluation_rubric.md`** §2; CSV column order — **`scripts/export_evaluation/harvest_evidence.py`** (`TEST_CASES_FIELDNAMES`).

### `Status` vs `Result` (read this first)

- **`evaluation/test_cases.csv` → `Status`** — Procurement outcome for the scenario run: e.g. **`SUCCESS`**, **`NO_AWARD`**. Use this for “was there a deal?”
- **`evaluation/evaluation_results.csv` → `Phase_3_Evaluation` row → `Result`** — Rubric row for the Phase 3 justification. **`PASS`** here means that evaluation record is valid, **not** “negotiation succeeded.” You can have **`Result`** = **`PASS`** and **`Status`** = **`NO_AWARD`**.

**Other `evaluation/` files** (table, rubric, generated report, **`failure_log.md`** with **FL-001–FL-004**, **`version_notes.md`**, **`multi_seed_variance/`** for instructor multi-seed re-runs) — what they are and how they are produced: **[Evaluation and outputs](#evaluation-and-outputs)** and **[Scripts](#scripts)** → Evaluation pipeline.

**Reading the CSVs:** Column order for **`test_cases.csv`** is **`TEST_CASES_FIELDNAMES`** in **`scripts/export_evaluation/harvest_evidence.py`**. For **`evaluation_results.csv`**, each row’s **`Result_Meaning`** states the pass/fail rule; **`Technical_Justification`** holds harvested evidence text. **`evaluation/evaluation_rubric.md`** §1 groups **`test_cases`** fields conceptually (identity → … → evidence).

---

## Governance flow

1. **Vendors** — Each thread is isolated: round 1 sees RFP + isolation footer; later rounds see **`buyer_reply_prev`** only (same text for A/B/C), not other vendors’ raw bids.
2. **Buyer** — Sees parsed **`bid_summary`** each round; may **`CONTINUE`** or emit **`AWARD_JSON`**.
3. **Strategic Audit** — **`agents/advisor.py`**; full audit is **not** auto-injected into the buyer’s next vendor round.
4. **Human** — **`yes`** / **`no`** at the gate; **`no`** may trigger an optional **governance nudge** (in-round only).
5. **Guardrail** — **`award_contract`** enforces price ≤ hard ceiling; success **overwrites** **`logs/contract.txt`** (one snapshot, not a log of all runs).

---

## Canvas submission packet (export to PDF)

**Canvas:** one PDF that links reviewers to the repo, reports, diagram, video, and evaluation.

- **Source (Markdown):** **`docs/Phase 3/CANVAS_SUBMISSION_PACKET.md`** — executive HTML/PDF: **`python scripts/render_canvas_submission_packet.py`** → **`docs/Phase 3/CANVAS_SUBMISSION_PACKET_executive.pdf`**. Submission bundle: **`Final Project AI Bidding War.zip`** (includes **`media/The AI Bidding War - Procurement (5 mins).mov`**, Phase 3 **written PDFs** under **`docs/Phase 3/`** including **`Phase3_Final_Report_4_21_2026.pdf`**, **`Phase3_AI_USAGE.pdf`**, etc. — see the packet). Large PDFs and video are often **zip-only** and not committed to git.

---

## Optional: CFO, diagrams

- **CFO narrative (offline):** **`scripts/cfo_monthly_report.py`** — see **[Scripts](#scripts)** → Other tooling.
- **Diagrams & canvases:** system architecture SVG in **`docs/System Architecture Diagram/`**; interactive MA / agent canvases in **`docs/Canvases/`** (see **[Folder guide](#folder-guide)**).
- **Further reading:** **`docs/Reference Research/Reference_Synthesis.md`**.
- **Earlier phase PDFs:** **`docs/Phase 1/`** (Phase 1 export); **`docs/Phase 2/`** (archived PDF(s)).

