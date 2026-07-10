# Reference research (instructor readings & related work)

**Project:** The AI Bidding War (Track A — hub-and-spoke procurement simulation).

This folder’s **single** reference document: Phase **1** suggested readings (table), **related work** & evaluation methodology (WorldCC / APQC, Kirshner, failure analysis, long-horizon), and an **extended synthesis** (AgenticPay & Jannelli mapped to the repo). PDFs named in the table may live alongside this file when downloaded.

**How to use:** The **Phase 1 table** and **Related work** (through Kirshner + cross-cutting subsections) are the front matter; **Extended synthesis** holds Liu/Jannelli detail, impact, and **subsection 6** (authoritative **pass/fail vs readings**).

---

## Phase 1 suggested readings (instructor references)

These three items were listed at the end of **Phase 1 feedback** (Prof. Rao). **One PDF is saved here**; the other two are publisher-hosted and typically require **institutional login** or purchase—download them via your **CMU library** or browser while on VPN.

| # | Paper | Local file | Link |
|---|--------|------------|------|
| 1 | Kirshner, Pan, Wu, Gould — *Talking Terms: Agent Information in LLM Supply Chain Bargaining* (Decision Sciences, 2025) | *(not bundled — paywall)* | [Wiley Online Library](https://onlinelibrary.wiley.com/doi/10.1111/deci.70010) |
| 2 | Liu, Gu, Song — *AgenticPay: A Multi-Agent LLM Negotiation System for Buyer–Seller Transactions* (arXiv:2602.06008) | **`Liu_et_al_AgenticPay_arxiv2602.06008.pdf`** | [Abstract](https://arxiv.org/abs/2602.06008) · [PDF](https://arxiv.org/pdf/2602.06008.pdf) |
| 3 | Jannelli et al. — *Agentic LLMs in the Supply Chain: Towards Autonomous Multi-Agent Consensus-Seeking* (IJPR, 2025) | **`Agentic LLMs in the supply chain  towards autonomous multi-agent consensus-seeking.pdf`** (if present) | [Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/00207543.2025.2604311) |

**CMU:** Use [CMU Library](https://www.library.cmu.edu/) search by title or DOI to get PDF for (1) if needed.

Automated download of (1) from this environment returned **HTTP 403** (Wiley access control).

---

## Related work & evaluation methodology

This section satisfies **high- and medium-priority** items from the instructor reading list and the internal **reading synthesis**. The **Phase 1 table** (above) is the canonical list of the three papers; notes below focus on **how** they connect to this repo.

---

### Procurement cycle time & ROI context (Phase 2 problem framing)

These sources support the project's **Problem Statement** (why multi-week negotiation cycles—not instant bid collection—motivate structured agentic negotiation). Figures below are **as reported** in each source; they are **not** project-specific measurements.

#### World Commerce & Contracting (WorldCC)

- **World Commerce & Contracting.** *Benchmark Report 2023* (global study of commercial and contract management; June–September 2023 fieldwork). Includes **bid-to-contract** cycle time distributions (e.g. domestic low / medium / high complexity) and finding that **>60%** of template-based transactions still involve **negotiation**; **reducing cycle times** is among top organizational drivers.  
  - PDF: https://www.worldcc.com/Portals/IACCM/Reports/Benchmark-report-2023.pdf  
  - Related sector reports in the same series (e.g. manufacturing/public sector 2024) extend the cycle-time discussion: https://www.worldcc.com/Resources/Benchmark-and-research-reports  

#### APQC (Open Standards Benchmarking)

- **APQC.** “Average cycle time in days for sourcing events for the procurement process group.” *Open Standards Benchmarking* measure **106474** (cross-industry; median **60.0** days from need identified to contract signed; total sample *n* ≈ 3,080). https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/average-cycle-time-days-sourcing-events  

- **APQC.** “Average cycle time in days to establish a contract with a supplier.” *Open Standards Benchmarking* measure **106475** (median **40.0** days from negotiation opened to contract signed; *n* ≈ 3,081). https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/average-cycle-time-days-establish  

**Scenario pass/fail vs. citations:** Per-scenario thresholds live in **`evaluation/evaluation_rubric.md` §2** (course design—not imported from the PDFs). How the readings **complement** that rubric—harvest metrics, Governance vs Negotiation—is spelled out in **Extended synthesis → Impact → subsection 6** below.

---

### Kirshner et al. (*Talking Terms: Agent Information in LLM Supply Chain Bargaining*, *Decision Sciences*, 2025)

**One-line tie-in:** Information structure and **which agent knows what** shapes bargaining outcomes in LLM-mediated supply-chain settings.

**This project:** **Hub-and-spoke isolation** (`vendor_histories` per spoke, buyer **`bid_summary`** from parsed bids only) enforces **asymmetric information** by construction—consistent with the paper’s emphasis on **agent information** in bargaining, without adopting their full experimental setup.

**Citation:** Samuel Kirshner, Yiwen Pan, Xianghua (Jason) Wu, Alex Gould. *Talking Terms: Agent Information in LLM Supply Chain Bargaining.* *Decision Sciences*, 2025. [Wiley Online Library](https://onlinelibrary.wiley.com/doi/10.1111/deci.70010).

**Liu (*AgenticPay*)** and **Jannelli et al.** — Project mapping (structured signals, consensus-before-commitment, partial observability, parallel vs sequential naming) and detailed notes are in **Extended synthesis** below; **pass/fail vs readings** is authoritative in **subsection 6** there.

---

### Failure analysis: language vs structure

**Language alone** is not sufficient for audit or settlement: procurement value lives in **prose**, but **policy execution** requires **structured** machine-parseable fields and deterministic checks.

- **Auditable path:** `BID_JSON` / `AWARD_JSON` in logs, **`award_contract`** outcomes, **`evidence_log_*.json`** turns.  
- **Failure taxonomy:** classify issues as **parse/structure gaps**, **guardrail block**, **human veto**, **model incoherence**, or **walk-away**—not an undifferentiated “model failed.”

This supports **honest failure analysis** (Phase 3) and matches AgenticPay’s **dialogue-to-outcome** perspective.

---

### Long-horizon limits vs our governance stack

Benchmark-style work (including AgenticPay) finds **long-horizon** negotiation **challenging** for LLMs. This project **does not** rely on unbounded self-play:

- **Hard round limit** (3 rounds) bounds strategic drift.  
- **Strategic Advisor** provides a **governance pass** before human approval.  
- **Human gatekeeper** can veto.  
- **Deterministic guardrail** enforces the **hard budget ceiling** regardless of persuasive LLM text.

That combination is the **engineering response** to long-horizon risk: **structure + tools + HITL**, not a larger single prompt.

---

### Citations (for final report)

**Procurement / ROI (problem framing)**

- World Commerce & Contracting. *Benchmark Report 2023.* https://www.worldcc.com/Portals/IACCM/Reports/Benchmark-report-2023.pdf  
- APQC. Open Standards Benchmarking — Measure **106474** (sourcing event cycle time; median 60 days). https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/average-cycle-time-days-sourcing-events  
- APQC. Open Standards Benchmarking — Measure **106475** (establish supplier contract; median 40 days). https://www.apqc.org/resources/benchmarking/open-standards-benchmarking/measures/average-cycle-time-days-establish  

**Academic / course readings**

- Kirshner, S., Pan, Y., Wu, X. (J.), & Gould, A. *Talking Terms: Agent Information in LLM Supply Chain Bargaining.* *Decision Sciences* (2025). https://doi.org/10.1111/deci.70010  
- Liu, X., Gu, S., & Song, D. *AgenticPay: A Multi-Agent LLM Negotiation System for Buyer–Seller Transactions.* arXiv:2602.06008. https://arxiv.org/abs/2602.06008  
- Jannelli, V., et al. *Agentic LLMs in the supply chain: towards autonomous multi-agent consensus-seeking.* *International Journal of Production Research* (2025). DOI: 10.1080/00207543.2025.2604311.

Local PDFs: this folder (`Liu_et_al_AgenticPay_arxiv2602.06008.pdf`, Jannelli PDF when present).

---

## Extended synthesis: AgenticPay (Liu et al.) & Jannelli et al.

Short review of the two PDFs in this folder and how they can inform **The AI Bidding War**—without rebuilding the project as a full benchmark or multi-echelon inventory simulator.

**Sources reviewed**

- Liu, Gu, Song — *AgenticPay* (arXiv:2602.06008) — `Liu_et_al_AgenticPay_arxiv2602.06008.pdf`
- Jannelli et al. — *Agentic LLMs in the supply chain…* (IJPR, 2025) — `Agentic LLMs in the supply chain  towards autonomous multi-agent consensus-seeking.pdf`

The third instructor reference (*Talking Terms*, Kirshner et al., Wiley) is not bundled here; summary tie-in is in **Kirshner et al.** (subsection above).

**Implemented in-repo (high / medium priorities):** see **Related work & evaluation methodology** (Kirshner, failure analysis, long-horizon, citations) and **`evaluation/evaluation_rubric.md`** §**1b–1c**. **Automated metrics:** **`scripts/export_evaluation/harvest_evidence.py`** → **`evaluation/test_cases.csv`** / **`evaluation/evaluation_results.csv`** (`Metrics_Audit`). **Pass/fail vs readings:** **subsection 6** below.

---

### Liu et al. (*AgenticPay*, arXiv) — detailed notes

#### What the paper stresses

- Negotiation as **language-mediated** economic interaction, not only numeric bids.
- **Private** buyer/seller state (reservation prices, constraints) vs **shared** product/market context—aligned with **RFP + hidden floors + hard ceiling**.
- **Parsing** dialogue into **structured actions** (e.g. prices) and scoring outcomes.
- Evaluation along **feasibility, efficiency, welfare** (deal in valid price band, surplus split, speed / rounds).
- **Long-horizon** limits for LLMs in multi-round settings: mitigations in this repo are summarized once under **Long-horizon limits vs our governance stack** (Related work above)—not repeated here.

#### Ideas worth incorporating (good fit)

1. **Richer evaluation metrics (documentation + optional harvest fields)**  
   Beyond binary success: e.g. award in the **bargaining zone** (between chosen vendor’s floor and buyer ceiling), **buyer savings vs opening bid**, **round count to agreement**. Aligns with “feasibility + efficiency” without adopting the full AgenticPay benchmark.

2. **Tie failure analysis to “language vs structure”**  
   Free-text negotiation is auditable when **machine-parseable** signals (`BID_JSON`, `AWARD_JSON`) and logs align—same spirit as dialogue-to-action emphasis in the paper.

3. **Stress-test narrative**  
   Points to the same mitigations as **Long-horizon limits vs our governance stack** (Related work)—do not duplicate that bullet list here.

4. **Optional stretch (low priority)**  
   Their **parallel vs sequential** market modes map loosely to round-based hub-and-spoke; you can **name** that design choice in related work.

---

### Jannelli et al. (*IJPR*, supply chain consensus) — detailed notes

#### What the paper stresses

- **Consensus-seeking** among parties with **different goals** and **partial visibility**—analogous to buyer vs vendors with **isolated** threads.
- **Modular** agent design: perception, memory, **tools**, **communication protocols**.
- **Tools** (deterministic or algorithmic) paired with LLMs can outperform naive policies; **negotiation**-style interaction can move behavior toward **known good practices** (their empirical focus is inventory / bullwhip; yours is **budget + audit + guardrail**).

#### Ideas worth incorporating (light touch)

1. **Reframe the stack in their vocabulary**  
   Strategic Advisor + human gatekeeper + `award_contract` = a **consensus-seeking** layer before commitment: align “soft” LLM agreement with **hard** policy. Useful for a **related-work** paragraph.

2. **Double down on “tools + protocol” in documentation**  
   Orchestration protocol, JSON lines, deterministic guardrail—make this **explicit** in architecture / final report; matches their adoption thesis.

3. **Partial observability**  
   CASN-style **partial observability** mirrors **vendor isolation**—one sentence in problem framing or evaluation methodology.

4. **What not to force into the codebase**  
   **Sequential multi-echelon inventory** and **bullwhip** metrics are a **different** problem than single-buyer multi-vendor RFP negotiation. Use the paper **conceptually** (consensus, tools, protocols), not as a mandate to add inventory dynamics unless you deliberately scope a new scenario.

---

### Suggested priority (practical order)

| Priority | Idea | Effort |
|----------|------|--------|
| High | Add **1–2 evaluation dimensions** inspired by AgenticPay (e.g. zone feasibility, savings vs first round, rounds-to-deal) to `evaluation/evaluation_rubric.md` / final report | Done: §**1b** + `scripts/export_evaluation/harvest_evidence.py` fields; fill **§3** after runs |
| High | **Related work** subsection citing both papers + one sentence each linking to **this** design | Low |
| Medium | **Long-horizon** narrative vs governance stack | Covered in Related work (**Long-horizon limits…**) + Impact #3 |
| Medium | **Consensus-seeking + tools + protocols** framing (Jannelli) for advisor + guardrail | Low |
| Low / optional | Deeper numeric scoring (surplus, welfare split)—only if time | Higher |

---

### Impact once implemented (how the solution improves)

These ideas **do not** replace the orchestrator or personas; they **sharpen what you measure, prove, and defend**.

#### 1. Richer evaluation metrics (bargaining zone, savings vs first bid, rounds-to-deal)

- **Evidence quality:** Move from “it ran and we got a status” to **quantified** negotiation value and efficiency (AgenticPay-style **feasibility / efficiency**).
- **Grading & portfolio:** Reviewers see **numbers** tied to outcomes (savings, award between vendor floor and ceiling, speed to agreement).
- **Debugging:** Pinpoint whether issues are **price**, **rounds**, or **structure**, not vague model noise.

**Runtime behavior** of buyer/vendors can stay the same; the **demonstrated system** gets stronger because claims are **checkable** against the rubric.

#### 2. Explicit “language vs structure” in failure analysis

Expands **Failure analysis: language vs structure** (Related work above): soft LLM text is actionable when paired with **`BID_JSON` / `AWARD_JSON`**, logs, and guardrails; failures get **classified** (parse miss, human veto, guardrail block, model incoherence).

**Impact:** Stronger Phase 3 narrative and `evaluation/failure_log.md`; code changes only if you add **validation** (e.g. warn when JSON is missing).

#### 3. Long-horizon / multi-round narrative (AgenticPay benchmark findings)

Same story as **Long-horizon limits vs our governance stack** (Related work above): 3-round cap + advisor + human gate as **responses to known LLM limits**, not arbitrary choices—mostly **documentation and final report**.

#### 4. Consensus-seeking + tools + protocols (Jannelli-style framing)

- **Role clarity:** Advisor + human + `award_contract` as **consensus before commitment**—aligned with governance literature.
- **Adoption / pitch:** “LLM proposes; **tools and humans** commit” fits enterprise expectations.

**Impact:** Stronger **conceptual** layer for the report and interviews; implementation may be **diagram labels** or one architecture subsection unless you add new tools.

#### 5. Optional: deeper scoring (surplus, welfare split)

- **Research-grade evaluation** and fairness arguments (buyer vs vendor surplus).
- **Comparability** across runs and models.

**Impact:** Higher **implementation** cost (`scripts/export_evaluation/harvest_evidence.py` or spreadsheets). Payoff is **high** for **economic depth**; **low** if the course only needs scenarios + logs.

#### 6. Measurable pass/fail baselines (Phase 1 feedback) and how the readings support them

Course feedback asked for **stated expected outcomes** and **measurable pass/fail** per scenario—not merely “outcome recorded per run” or “depending on negotiation.” The **written criteria** for ambiguous cases (e.g. Budget Squeeze: ≤$12k vs. partial vs. documented `NO_AWARD`; Quality Focus: audit + ≤$15k + quality rationale) live in **`evaluation/evaluation_rubric.md` §2** as **design intent and procurement logic**. Those branches are **not** imported from Liu or Jannelli; they satisfy the **evaluation plan** and instructor expectations.

What the **references** add to the **same area** is complementary:

- **Liu et al. (AgenticPay)** — The paper stresses **dialogue-to-outcome** parsing and **feasibility / efficiency** (valid price band, rounds, savings). The implementation mirrors that in tooling: **`scripts/export_evaluation/harvest_evidence.py`** adds **AgenticPay-style** columns—`Savings_Vs_Winner_Round1`, `Winning_Vendor_Round1_Bid`, `Negotiation_Rounds_Completed`, `Final_Price_In_Feasible_Band`, and a **`Metrics_Audit`** row in **`evaluation/evaluation_results.csv`** when logs are harvested—and **`evaluation/evaluation_rubric.md` §1b** documents them. That strengthens the **reference baseline** for Phase 3: outcomes are **quantified** (zone feasibility, savings, round count), not only a coarse status string.

- **Jannelli et al.** — The paper does **not** set $12k or quality thresholds. It **frames** **Strategic Advisor + human gatekeeper + `award_contract`** as **consensus-seeking before commitment**: soft LLM agreement is **not** sufficient to spend budget; **tools** and **human approval** align execution with policy. That matches the rubric’s **two-layer** scoring—**Governance pass** vs **Negotiation pass** / partial—so a run can **governance-pass** while **negotiation** is partial (e.g. in-band award that misses an internal finance target).

- **Language vs structure** (see **Failure analysis: language vs structure** earlier in this document) — Supports classifying outcomes by **parseable** evidence (`BID_JSON` / `AWARD_JSON`, `award_contract`, `evidence_log_*.json`) instead of an undifferentiated “model did something,” which is the same spirit as rejecting **observation-only** evaluation rows.

**Net:** The readings **strengthen the measurement layer** (§1b–1c, harvest, `Metrics_Audit`) and the **governance-vs-negotiation narrative**; the **explicit per-scenario pass/fail branches** in §2 come from the **course evaluation plan** and **instructor feedback**, implemented in the rubric—not from the PDFs alone.

#### Summary: idea → type of improvement → typical code change

| Idea | Main improvement | Typical code change |
|------|------------------|---------------------|
| Extra metrics in rubric / harvest | Stronger **evidence** and baseline vs actual | `scripts/export_evaluation/harvest_evidence.py` + rubric §**1b** (see §6 above) |
| Pass/fail §2 + readings (Phase 1 feedback) | **§2** = scenario rules; **papers** = measurement + governance frame | Rubric + docs; **§3** filled after runs |
| Failure taxonomy (language vs structure) | Better **failure analysis** & governance story | Mostly docs; optional orchestrator warnings |
| Long-horizon citation | Stronger **justification** of rounds + gates | Docs only |
| Consensus + tools framing | Stronger **architecture narrative** | Docs / diagram |
| Full surplus / welfare math | Strongest **economic** depth | Larger harvest / feature work |

**Bottom line:** Most of these ideas **amplify** what you already built: isolation, JSON, guardrail, advisor, human gate. They improve **how convincingly you prove** success and failure, and **how clearly you explain** the design—what assignment and portfolio readers optimize for.

---

### Next step

If the **Wiley** (*Talking Terms*) PDF is added under this folder, extend this document with **information asymmetry** and supply-chain bargaining angles from that paper in the extended synthesis.

---

*Last updated: consolidated instructor table, related work, and AgenticPay/Jannelli synthesis in one file.*
