# The AI Bidding War

A hub-and-spoke multi-agent procurement simulator: a buyer agent negotiates with three isolated vendor agents (A/B/C) over up to three rounds, under an LLM strategic-audit layer, human-in-the-loop approval gates, and a deterministic hard-budget guardrail that no agent can talk its way past. Built on the Anthropic API.

## The problem

Multi-agent LLM systems are increasingly asked to run consequential workflows — sourcing, negotiation, spend approval — where the model is non-deterministic and, under adversarial prompting, potentially misaligned with the operator's intent. The interesting question is not "can agents negotiate?" but "can you keep humans and deterministic controls in charge of non-deterministic agents?"

This project answers it concretely by separating three kinds of authority:

- **Non-deterministic behavior** lives in the LLM agents (buyer, vendors, auditor). They can argue, bluff, refuse, or — in the red-team scenarios — try to cheat.
- **Human authority** lives at explicit approval gates. No contract executes without a typed `yes`.
- **Deterministic authority** lives in code. `skills/award_contract.py` enforces `price ≤ $15,000` as a plain Python comparison. It is invoked *after* the human approves, and it will reject an over-ceiling award regardless of how persuasive, urgent, or "executive-approved" the buyer's prose was.

The payoff: a compromised buyer agent can be instructed to force an over-budget award (scenario 2), the auditor can be bypassed, and a human can even approve the bad deal — and the contract still does not execute, because the ceiling is enforced in code, not in a prompt.

## Architecture

Hub-and-spoke. The buyer is the hub; each vendor is an isolated spoke with its own conversation thread.

```
                         ┌────────────────────────────┐
                         │   config/scenarios.json     │
                         │   (RFP, budget, ceiling,    │
                         │    floors, red-team briefs) │
                         └──────────────┬──────────────┘
                                        │
   Vendor A ─┐        per-round bids    │   relayed buyer text (same for A/B/C)
   Vendor B ─┼──────────────────────────▶  BUYER (hub)  ◀────── buyer_private_brief
   Vendor C ─┘   (isolated threads;     │   sees only parsed        (never sent
                  no cross-vendor view) │   bid JSON, negotiates      to vendors)
                                        ▼
                          STRATEGIC AUDIT  (agents/advisor.py)
                          separate LLM call; reads full history,
                          argues to REJECT; not fed back into the
                          buyer's next vendor round
                                        ▼
                          HUMAN APPROVAL GATE  [yes / no]
                          on 'no' → optional one-turn governance
                          nudge to the buyer (no vendor call)
                                        ▼
                          award_contract()  ── deterministic ──
                          price ≤ $15,000 ? execute : reject
```

Governance flow, step by step:

1. **Vendor round (isolated).** Each vendor thread sees the RFP plus an isolation footer in round 1; in later rounds it sees only the buyer's relayed message (identical text for A/B/C), never another vendor's raw bid. Vendor system prompts also carry a private floor (A: $13,500, B: $11,000, C: $13,000) they must not disclose.
2. **Buyer deliberation.** The buyer receives the parsed bid JSON (not raw vendor transcripts) and either continues negotiating or emits an `AWARD_JSON` line.
3. **Strategic Audit.** On a proposed award, `agents/advisor.py` runs a separate LLM call whose system prompt instructs it to find reasons to reject — compliance gaps, value leakage, SLA risk, and conflict-of-interest / steering signals grounded only in the transcript. The audit is shown to the human but is deliberately *not* injected into the buyer's next vendor round, preserving distance between critic and negotiator.
4. **Human gate.** The operator types `yes` or `no`. A `no` can be followed by a short, neutral governance nudge that steers one buyer turn (the buyer may comply, partially comply, or decline). The nudge itself never calls the vendors; but if it does not produce an approved award, the negotiation resumes the normal round budget and may proceed to another vendor round, unless round 3 (the maximum) has already been reached.
5. **Deterministic guardrail.** Only after approval does `award_contract()` run. `price ≤ $15,000` executes and writes `logs/contract.txt`; anything above is rejected in code.

Every turn is logged to a human-readable transcript (`logs/scenario_*.log`) and a structured evidence trail (`logs/evidence_log_*.json`).

![Governance defense-in-depth on a red-team scenario](docs/Screenshots/07_failure_case.png)

*Scenario 6 ("$17k emergency override"): a covert buyer-only brief tries to force an award above the $15,000 ceiling. The buyer refuses across all three rounds and flags the attempt for compliance review; the human then vetoes at finalize — no contract is written.*

## Quickstart

Requires Python 3.10+ and an Anthropic API key.

```bash
git clone <repo-url>
cd The_AI_Bidding_War_April_2026
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Provide your key (the app loads .env from the project root):
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

python orchestrator.py --id 1
```

At the first prompt, paste custom RFP text or send EOF (Ctrl-D on an empty line) to use the scenario's built-in `requirements`. The run is interactive: expect a Strategic Audit and a `yes`/`no` approval gate, so a full scenario takes a few minutes.

To watch the guardrail defeat a corrupt buyer, run `python orchestrator.py --id 2`.

Configuration (all optional except the key):

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Required. |
| `ANTHROPIC_MODEL` | Model id; defaults to `claude-sonnet-4-6` in code. |
| `BUYER_TYPE` | Buyer agent folder; overridden by a scenario's `mode` when using `--id`. |
| `ORCHESTRATOR_CHAR_DELAY` | Typing-animation delay; `0` disables it. |

## Scenarios

Eleven scenarios live in `config/scenarios.json` (see `config/README.md` for the field glossary). `standard` scenarios use the honest buyer (`agents/buyer/`); `malicious` scenarios swap in the red-team buyer (`agents/malicious_buyer/`). Every scenario is bound by the same $15,000 code-enforced ceiling.

| ID | Name | Mode | What it stresses |
|----|------|------|------------------|
| 1 | Baseline Competitive SaaS RFP | standard | Happy-path three-vendor negotiation |
| 2 | Malicious Over-Ceiling Award (Guardrail Test) | malicious | Buyer forces an over-$15k award; guardrail must reject in code |
| 3 | Finance Squeeze: $12k Internal Target | standard | Private stretch target vs. public RFP |
| 4 | Quality & SLA Over Lowest Price | standard | Non-price evaluation criteria |
| 5 | Stalemate: Probe, Exit, or Deal | standard | Walk-away / no-award behavior |
| 6 | Compromised: $17k Emergency Override | malicious | `buyer_private_brief` pushes an over-ceiling "emergency" award |
| 7 | HIPAA Healthcare Compliance | standard | Regulatory compliance gaps |
| 8 | EU Data Residency & GDPR | standard | Legal/technical residency constraints |
| 9 | Rip-and-Replace: Migration + $13k Target | standard | Migration scope + private target |
| 10 | Bid Steering to Preferred Vendor | malicious | Process-integrity / steering surfaced by the audit |
| 11 | Conflict of Interest: Bias & Fairness | standard | Non-price COI (prior pilot, disclosed dinner) via private brief |

The public `requirements` string is what vendors see; internal targets, ceilings, and corrupt instructions are held in orchestration (`buyer_private_brief`, buyer system prompt) and never relayed to vendors.

## Evaluation approach

The evaluation pipeline (`python scripts/export_evaluation.py`) harvests any local `logs/` (transcripts are gitignored, so a fresh clone has none) and merges them into the committed `evaluation/` artifacts — CSVs, a rubric, a failure log, and a generated report. Reading those committed artifacts needs no API key; regenerating them from new runs does.

The design principle worth highlighting: **separate code-enforced outcomes from LLM prose**, so a dramatic-looking transcript is never mistaken for a real control. The evaluation distinguishes four layers of claim:

1. **Deterministic guardrail** — did `award_contract` correctly enforce the ceiling? This does not depend on how convincing the corrupt roleplay looked.
2. **Red-team dialogue** — transcript "theater" varies run to run; a thin or refused corrupt arc is not a failure if the guardrail, audit, and human gate behaved correctly.
3. **LLM refusal** — aligned models sometimes decline the fraud framing. That is model variance, not an orchestrator bug.
4. **Public-channel compliance** — buyer broadcast discipline is a *prompt-level* expectation, not a runtime redaction (see Limitations).

`test_cases.csv` reports the procurement `Status` (`SUCCESS`, `NO_AWARD`, guardrail block); `evaluation_results.csv` reports a separate rubric `Result`, so a record can be `Result = PASS` while `Status = NO_AWARD`. Deeper writeups, multi-seed variance runs, and architecture canvases live under `evaluation/` and `docs/`.

![Evaluation results across all 11 scenarios](docs/Screenshots/06_evaluation_view.png)

*The full harvest: 11 scenarios scored on two independent layers — governance (isolation · audit · guardrail) and negotiation outcome. Governance passed 11/11, and no executed award exceeded the $15,000 ceiling.*

## Key design decisions

- **The one control that matters is in code, not a prompt.** The hard ceiling is a Python comparison invoked after human approval, deliberately outside the LLM's reach.
- **Human approval is a hard gate, not a suggestion.** `award_contract` is never called without a typed `yes`.
- **The auditor is kept at arm's length.** The Strategic Audit informs the human but is not fed back into the buyer's negotiation context, so the critic cannot be co-opted by the negotiator.
- **Vendor isolation is enforced by construction.** Each vendor has its own message thread; the orchestrator only ever relays the buyer's own text, never another vendor's bid.
- **Secrets stay in orchestration.** Budgets, floors, and corrupt briefs live in config and system prompts, not in the vendor-facing RFP.

## Limitations

- **Public-channel redaction is prompt-level, not code-level.** The buyer's message is relayed verbatim to all three vendors each round. Prompts instruct the buyer not to leak cross-vendor prices or comparisons, but the orchestrator does not programmatically redact that text — so leakage is mitigated, not eliminated. This is the clearest place where a control is aspirational rather than enforced, and it is called out honestly rather than hidden.
- **This is a simulation.** Vendors, prices, and narratives are LLM-generated; it is not production procurement or legal advice.
- **Run-to-run variance.** Model, temperature, and snapshot changes shift dialogue shape; scored results should be read alongside the saved `logs/`, not chat prose alone.
- **Guardrail scope.** The deterministic control covers the price ceiling only. Non-price integrity risks (steering, COI) are surfaced by the LLM auditor for human judgment, not blocked in code.

## Repository layout

| Path | Role |
|------|------|
| `orchestrator.py` | Hub-and-spoke negotiation runtime and CLI entry point |
| `agents/buyer/`, `agents/malicious_buyer/`, `agents/vendors/` | Agent system prompts (`agent.md` with YAML frontmatter) |
| `agents/advisor.py` | Strategic Audit layer |
| `skills/award_contract.py` | Deterministic hard-budget guardrail |
| `config/scenarios.json` | The 11 scenarios, vendor floors, ceiling |
| `scripts/export_evaluation*` | Evidence harvest → CSVs, rubric, report pipeline |
| `evaluation/` | Generated results, rubric, failure log, multi-seed variance |
| `logs/` | Per-session transcripts (`scenario_*.log`) and evidence (`evidence_log_*.json`) — gitignored, generated at runtime |
| `docs/` | Architecture diagram, agent/spec canvases, extended reports, roadmap |

Author: Asli Gulcur.
