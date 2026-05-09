# Phase 3 — Vendor-side confidentiality (context and backlog)

## Issue

My discovery as I was running the scenarios -- The hub-and-spoke orchestrator sends **one** buyer assistant reply per round to **every** vendor as the next user turn (`buyer_reply_prev` is identical for A, B, and C). The buyer’s hub turn is informed by **all** vendors’ parsed bids (`bid_summary`). If that reply **quotes, compares, or ranks** offers in natural language, **competitor price and position information is broadcast** to all suppliers. Thread isolation stops vendors from seeing each other’s raw messages, but it does **not** stop leakage through the **shared** buyer prose. That undermines the intended “each vendor only sees public buyer language” story when the model restates cross-vendor commercial detail.

## What we implemented now 

These mitigations are **prompt- and policy-level**: they reduce accidental disclosure but do not provide cryptographic or structural guarantees if the model ignores instructions.

1. **Buyer persona (`agents/buyer/agent.md`)** — Added a **Public broadcast (mandatory)** section: the same text goes to every vendor; do not disclose other vendors’ prices, ranks, or relative positions; use buyer requirements and vendor-neutral language.

2. **Runtime enforcement (`orchestrator.py`)** — `_PUBLIC_BROADCAST_BUYER_APPEND` is appended to the buyer system prompt via `_system_prompt_buyer()` so the rule is not omitted when editing YAML alone.

3. **Red-team default (`orchestrator.py`)** — `scenario_relax_public_broadcast(scenario)` controls whether that append is applied. **Default:** `relax_public_broadcast` is **true** when `mode == "malicious"` (omit the append so malicious scenarios can stress other risks without forcing public-channel compliance), and **false** for standard scenarios. **Override** any scenario with `"relax_public_broadcast": true|false` in `config/scenarios.json`. Evidence JSON and the scenario log record the flag.

   **Example:** Scenario **id 2** sets `"relax_public_broadcast": false` so malicious mode still gets the runtime append (A/B vs ids 6, 10, etc. that use the malicious default).

4. **Award-adjacent broadcast** — Observed slip: the model stayed vendor-neutral in mid-round summaries, then put **outcome** detail in prose (e.g. “winning proposal” at a specific dollar amount) in the same message as `AWARD_JSON`, which all vendors can still see. **Update:** `agents/buyer/agent.md` and `_PUBLIC_BROADCAST_BUYER_APPEND` in `orchestrator.py` now say: do **not** restate the awarded price or “winning/selected” plus a figure in free-form text; put vendor, price, and name **only** in the `AWARD_JSON` line; keep narrative generic. Still prompt-level, not a parser guarantee.

5. **Malicious buyer persona (`agents/malicious_buyer/agent.md`)** — We did **not** duplicate the full Public broadcast block (it would contradict default red-team). Added a short **Orchestrator policy** section: default malicious runs omit the runtime append; when `relax_public_broadcast` is **false** (e.g. scenario **2**), the same runtime rules apply—follow broadcast hygiene for that run even though the persona stays corrupt.

6. **Comparison-table slip** — The model may still output a **side-by-side “evaluation” table** with per-vendor prices or terms (A/B/C columns), which is broadcast to everyone. **Update:** `agents/buyer/agent.md` and `_PUBLIC_BROADCAST_BUYER_APPEND` explicitly forbid such tables in the shared channel; **[README.md § Evaluation folder](../../README.md#evaluation-folder)** notes that **no code** parses or redacts buyer text before relay. Still prompt-level only.

## Suggested implementation to further address it (Phase 3 backlog)

Use these when you need **stronger** isolation, **automated** cleanup, or **explicit** separation of private vs public buyer text.

### Option A — Per-vendor buyer messages (structural isolation)

**Idea:** Stop using one `buyer_reply_prev` for every vendor. After each round, produce **one buyer message per vendor** (or one structured output split into three), each conditioned only on shared scenario / RFP / ceilings and **that vendor’s** parsed bid (optional: carefully defined aggregates only).

**Pros:** Strongest alignment with real procurement firewalls; other vendors’ prices need not appear in text destined for a competitor.

**Cons:** More orchestration (multiple buyer calls or one multi-section response), higher latency and cost, and you must define fair generic competition without a single shared broadcast.

**Implementation sketch:** Extend `orchestrator.py` so `vendor_histories[id]` receive `buyer_reply_prev[id]`; build three buyer user prompts or one prompt that outputs `PUBLIC_MESSAGE_A`, `PUBLIC_MESSAGE_B`, `PUBLIC_MESSAGE_C`.

### Option B — Automated redaction / post-processing

**Idea:** Keep a single buyer reply; run a **deterministic filter** or a **small LLM pass** that strips or rewrites lines that match other vendors’ known prices from `bid_summary` before storing text shown to vendors.

**Pros:** One buyer call per round; can catch some slips after the fact.

**Cons:** Fragile (paraphrases, implicit comparisons); false positives may remove useful feedback; needs tests against logs.

**Implementation sketch:** After the buyer call, pass reply text + `bid_summary` into a redactor; persist only redacted text in `buyer_reply_prev` (or per-vendor copies).

### Option C — Two-phase buyer (internal vs public)

**Idea:** Buyer first produces **private** reasoning with full `bid_summary`, then a second call (or structured second block) produces **only** the public-safe text vendors see.

**Pros:** Separates strategic reasoning from broadcast copy; pairs well with Option B on the public block.

**Cons:** Two model steps per round; the second step must still obey rules unless combined with redaction.

---

**Suggested iteration order:** **Option A** if you need a defensible claim that competitor-specific numbers never appear in vendor-visible text; **Option B** as a safety net with the current or per-vendor design; **Option C** when you want cleaner separation of reasoning and broadcast without yet splitting threads.

## Recommendation (keep for later reference)

- **Course / demo / default stance:** The Phase 2 mitigations above are enough: they document the issue, reduce accidental leakage, and keep malicious scenarios able to omit the runtime append on purpose. **Do not build Phase 3** unless you need structural confidentiality or a rubric explicitly requires it.

- **Writing / evaluation stance:** State honestly that isolation is **per-thread**, while **shared** buyer prose can still leak if the model misbehaves; malicious runs may **relax** the append by design. Link this file rather than implying perfect secrecy.

- **When to invest in Phase 3:** Only if you must **claim** that competitor-specific numbers never appear in vendor-visible text — then prioritize **Option A** (per-vendor buyer messages); more prompt tuning is not a substitute.

- **Lightweight next step (if needed):** Add a short limitation paragraph in Phase 2 narrative or **`Phase3_AI_USAGE.pdf`** pointing here; revisit Phase 3 only after feedback or a new project phase.

---

## File checklist

### Updated with the recent public-broadcast / relax work (reference)

| Area | Files |
|------|--------|
| **Runtime** | `orchestrator.py` — `_PUBLIC_BROADCAST_BUYER_APPEND` (includes **award/closing** rule; **no** side-by-side A/B/C commercial tables; no restated outcome price in prose when `AWARD_JSON` is present), `scenario_relax_public_broadcast()`, `_system_prompt_buyer(...)`, evidence + scenario log fields |
| **Buyer personas** | `agents/buyer/agent.md` — Public broadcast + **Awards and closing copy** + **no comparison tables**; `agents/malicious_buyer/agent.md` — **Orchestrator policy** (relax vs enforced append), no duplicate full broadcast block |
| **Evaluation** | [README § Evaluation folder](../../README.md#evaluation-folder) — notes **public-channel compliance** is prompt-level, not code-enforced |
| **Scenarios** | `config/scenarios.json` — e.g. scenario id **2** has `relax_public_broadcast: false` (explicit override) |
| **Canvases (HTML)** | `docs/Canvases/agents/AgentCanvas_Buyer.html`, `AgentCanvas_MaliciousBuyer.html`, `AgentCanvas_VendorA.html`, `AgentCanvas_VendorB.html`, `AgentCanvas_VendorC.html`, `AgentCanvas_StrategicAdvisor.html`, `ComponentCanvas_Orchestrator.html`, `ComponentCanvas_HumanGatekeeper.html`; `docs/Canvases/MA_ArchCanvas_The_AI_Bidding_War.html`, `docs/Canvases/MA_SpecCanvas_The_AI_Bidding_War.html` |
| **This doc** | `docs/Future Roadmap/PHASE_3_IMPLEMENTATION.md` |

### Worth updating when you implement Phase 3 backlog (Options A–C)

| Priority | Files / artifacts |
|----------|-------------------|
| **Code** | `orchestrator.py` (core); possibly new module for redaction or per-vendor prompt builders; `agents/buyer/agent.md` if buyer instructions change |
| **Config** | `config/scenarios.json` if new flags or behaviors per scenario |
| **Docs** | `README.md`; Phase 2 archive (`docs/Phase 2/*.pdf`); `docs/Phase 3/Phase3_AI_USAGE.pdf`; `evaluation/evaluation_rubric.md` if scoring assumptions change |
| **Diagrams / canvases** | `docs/System Architecture Diagram/*` if message flow changes; refresh MA / component canvases to match new data paths |
| **Tests / logs** | Any `scripts/` or harvest steps that assume a single `buyer_reply_prev`; add regression checks against sample logs if you add redaction |
