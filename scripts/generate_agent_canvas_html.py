#!/usr/bin/env python3
"""
Generate one-page Agent Canvas HTML files (three-zone specification layout) for
The AI Bidding War agents and components. Output: docs/Canvases/agents/

Usage: python scripts/generate_agent_canvas_html.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "Canvases" / "agents"

CSS_BLOCK = """  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Palatino Linotype', 'Book Antiqua', Palatino, Georgia, serif;
    background: #F7F8FA;
    padding: 20px 16px;
    min-height: 100vh;
  }
  .container { max-width: 1060px; margin: 0 auto; }
  .header { margin-bottom: 16px; }
  .header-bar {
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 2px solid #990000; padding-bottom: 8px;
  }
  .header-bar h1 {
    font: 700 24px/1.2 Georgia, 'Palatino Linotype', serif;
    color: #1a1a2e; letter-spacing: -0.3px;
  }
  .header-bar .course { font: 600 10px Georgia, serif; color: #990000; }
  .subtitle {
    font-size: 11px; color: #5a5a6a; line-height: 1.5;
    margin-top: 6px; font-style: italic;
  }
  .canvas { position: relative; }
  .flow-indicator {
    position: absolute; left: -18px; top: 20px; bottom: 20px;
    width: 4px; border-radius: 2px;
    background: linear-gradient(to bottom, #2B579A 0%, #2B579A 28%, #0D6B5E 35%, #0D6B5E 65%, #5E35B1 72%, #5E35B1 100%);
    opacity: 0.25;
  }
  .zone {
    border-radius: 10px; padding: 10px 14px 14px; position: relative;
    margin-bottom: 12px;
  }
  .zone:last-child { margin-bottom: 0; }
  .zone-1 { background: #F0F4FA; border: 1px solid #B8CCE4; }
  .zone-2 {
    background: #EBF7F4; border: 2px solid #8ECFC4;
    padding: 12px 16px 16px;
    box-shadow: 0 2px 16px rgba(13,107,94,0.08);
  }
  .zone-3 { background: #F3EEFC; border: 1px solid #C5B3E6; }
  .zone-badge {
    display: inline-flex; align-items: center; gap: 6px;
    margin-bottom: 10px; padding: 3px 12px 3px 8px;
    border-radius: 4px;
  }
  .zone-badge-1 { background: #D6E4F5; border: 1px solid #B8CCE4; }
  .zone-badge-2 { background: #B2E0D6; border: 1px solid #8ECFC4; }
  .zone-badge-3 { background: #DDD0F0; border: 1px solid #C5B3E6; }
  .zone-num {
    width: 18px; height: 18px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font: 700 10px Georgia, serif; color: #fff;
  }
  .zone-num-1 { background: #2B579A; }
  .zone-num-2 { background: #0D6B5E; }
  .zone-num-3 { background: #5E35B1; }
  .zone-label {
    font: 700 9px Georgia, serif; letter-spacing: 2px;
    text-transform: uppercase;
  }
  .zone-label-1 { color: #2B579A; }
  .zone-label-2 { color: #0D6B5E; }
  .zone-label-3 { color: #5E35B1; }
  .row { display: grid; gap: 10px; margin-bottom: 10px; }
  .row:last-child { margin-bottom: 0; }
  .row-full { grid-template-columns: 1fr; }
  .row-half { grid-template-columns: 1fr 1fr; }
  .field {
    background: #FFFFFF; border-radius: 6px;
    padding: 10px 14px; position: relative;
    border: 1px solid rgba(0,0,0,0.07);
  }
  .field-z1 { border-left: 3.5px solid #2B579A; }
  .field-z2 { border-left: 3.5px solid #0D6B5E; }
  .field-z3 { border-left: 3.5px solid #5E35B1; }
  .field.bookend-1 {
    background: linear-gradient(135deg, #FFFFFF 0%, #F0F4FA 100%);
    border-color: rgba(43,87,154,0.25);
  }
  .field.bookend-3 {
    background: linear-gradient(135deg, #FFFFFF 0%, #F3EEFC 100%);
    border-color: rgba(94,53,177,0.25);
  }
  .field-num {
    position: absolute; top: 8px; right: 10px;
    width: 20px; height: 20px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font: 700 9px Georgia, serif;
  }
  .field-num-1 { background: #D6E4F5; border: 1px solid #B8CCE4; color: #2B579A; }
  .field-num-2 { background: #B2E0D6; border: 1px solid #8ECFC4; color: #0D6B5E; }
  .field-num-3 { background: #DDD0F0; border: 1px solid #C5B3E6; color: #5E35B1; }
  .field-header {
    display: flex; align-items: center; gap: 7px;
    margin-bottom: 7px; padding-right: 28px;
  }
  .field-icon { font-size: 15px; line-height: 1; }
  .field-title { font: 700 12px Georgia, serif; }
  .field-title.prominent { font-size: 13.5px; }
  .field-title-1 { color: #2B579A; }
  .field-title-2 { color: #0D6B5E; }
  .field-title-3 { color: #5E35B1; }
  .field-text { font-size: 11px; line-height: 1.6; color: #3a3a4a; }
  .field-rows { display: flex; flex-direction: column; gap: 2px; }
  .field-row { display: flex; gap: 6px; font-size: 10.5px; line-height: 1.5; }
  .field-row-label {
    font-weight: 700; min-width: 76px; flex-shrink: 0;
    font-size: 9.5px; text-transform: uppercase; letter-spacing: 0.3px;
    padding-top: 1px;
  }
  .field-row-label-1 { color: #2B579A; }
  .field-row-label-2 { color: #0D6B5E; }
  .field-row-label-3 { color: #5E35B1; }
  .field-row-text { color: #3a3a4a; }
  .watermark {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-2deg);
    font: 700 14px Georgia, serif;
    letter-spacing: 6px; text-transform: uppercase;
    color: rgba(13,107,94,0.07);
    pointer-events: none; white-space: nowrap;
  }
  .footer {
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid #ddd; padding-top: 8px; margin-top: 14px;
  }
  .footer-left { font-size: 9.5px; color: #999; font-style: italic; }
  .footer-right { font-size: 9px; color: #bbb; }
  @media print {
    body { padding: 10px; }
    .flow-indicator { display: none; }
  }"""


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def rows_html(items: list[tuple[str, str, int]]) -> str:
    """(label, text, color_class 1|2|3)"""
    parts = []
    for lab, txt, c in items:
        parts.append(
            f'<div class="field-row">\n'
            f'              <span class="field-row-label field-row-label-{c}">{esc(lab)}</span>\n'
            f'              <span class="field-row-text">{esc(txt)}</span>\n'
            f"            </div>"
        )
    return "\n".join(parts)


def canvas_page(
    title: str,
    subtitle: str,
    purpose: str,
    task: str,
    stakeholders: list[tuple[str, str]],
    io_in: str,
    io_out: str,
    allow_tools: str,
    deny_tools: str,
    autonomy: list[tuple[str, str]],
    rules: list[tuple[str, str]],
    memory: list[tuple[str, str]],
    failures: list[tuple[str, str]],
    success: list[tuple[str, str]],
    footer_note: str,
) -> str:
    sh_rows = [(a, b, 1) for a, b in stakeholders]
    auto_rows = [(a, b, 2) for a, b in autonomy]
    rule_rows = [(a, b, 2) for a, b in rules]
    mem_rows = [(a, b, 3) for a, b in memory]
    fail_rows = [(a, b, 3) for a, b in failures]
    suc_rows = [(a, b, 3) for a, b in success]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>
{CSS_BLOCK}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <div class="header-bar">
      <h1>Agent System Specification Canvas</h1>
      <span class="course">94815 · Agentic Technologies · L6 · Track A</span>
    </div>
    <div class="subtitle">{esc(subtitle)}</div>
  </div>

  <div class="container canvas">
    <div class="flow-indicator"></div>
    <div class="zone zone-1">
      <div class="zone-badge zone-badge-1">
      <span class="zone-num zone-num-1">1</span>
      <span class="zone-label zone-label-1">System Intent</span>
    </div>
      <div class="row row-full"><div class="field field-z1 bookend-1">
      <div class="field-num field-num-1">1</div>
      <div class="field-header">
        <span class="field-icon">🎯</span>
        <span class="field-title prominent field-title-1">Use Case / Purpose</span>
      </div>
      <div class="field-text">{esc(purpose)}</div>
    </div></div>
<div class="row row-half"><div class="field field-z1">
      <div class="field-num field-num-1">2</div>
      <div class="field-header">
        <span class="field-icon">✂️</span>
        <span class="field-title field-title-1">Task Slice / Goal</span>
      </div>
      <div class="field-text">{esc(task)}</div>
    </div><div class="field field-z1">
      <div class="field-num field-num-1">3</div>
      <div class="field-header">
        <span class="field-icon">👥</span>
        <span class="field-title field-title-1">Users / Stakeholders</span>
      </div>
      <div class="field-rows">
{rows_html(sh_rows)}
</div>
    </div></div>

    </div><div class="zone zone-2">
      <div class="zone-badge zone-badge-2">
      <span class="zone-num zone-num-2">2</span>
      <span class="zone-label zone-label-2">Bounded Behavior</span>
    </div>
      <div class="row row-half"><div class="field field-z2">
      <div class="field-num field-num-2">4</div>
      <div class="field-header">
        <span class="field-icon">⇄</span>
        <span class="field-title field-title-2">Inputs / Outputs</span>
      </div>
      <div class="field-rows">
{rows_html([("IN", io_in, 2), ("OUT", io_out, 2)])}
</div>
    </div><div class="field field-z2">
      <div class="field-num field-num-2">5</div>
      <div class="field-header">
        <span class="field-icon">🔧</span>
        <span class="field-title field-title-2">Tools / Permissions</span>
      </div>
      <div class="field-rows">
{rows_html([("ALLOW", allow_tools, 2), ("DENY", deny_tools, 2)])}
</div>
    </div></div>
<div class="row row-half"><div class="field field-z2">
      <div class="field-num field-num-2">6</div>
      <div class="field-header">
        <span class="field-icon">🛡️</span>
        <span class="field-title field-title-2">Autonomy / Human Checkpoints</span>
      </div>
      <div class="field-rows">
{rows_html(auto_rows)}
</div>
    </div><div class="field field-z2">
      <div class="field-num field-num-2">7</div>
      <div class="field-header">
        <span class="field-icon">📜</span>
        <span class="field-title field-title-2">Operating Rules / Policies</span>
      </div>
      <div class="field-rows">
{rows_html(rule_rows)}
</div>
    </div></div>

      <div class="watermark">Bounded Agentic System</div>
    </div><div class="zone zone-3">
      <div class="zone-badge zone-badge-3">
      <span class="zone-num zone-num-3">3</span>
      <span class="zone-label zone-label-3">Context & Evaluation</span>
    </div>
      <div class="row row-half"><div class="field field-z3">
      <div class="field-num field-num-3">8</div>
      <div class="field-header">
        <span class="field-icon">💾</span>
        <span class="field-title field-title-3">Memory / Context</span>
      </div>
      <div class="field-rows">
{rows_html(mem_rows)}
</div>
    </div><div class="field field-z3">
      <div class="field-num field-num-3">9</div>
      <div class="field-header">
        <span class="field-icon">⚠️</span>
        <span class="field-title field-title-3">Failure Conditions / Escalations</span>
      </div>
      <div class="field-rows">
{rows_html(fail_rows)}
</div>
    </div></div>
<div class="row row-full"><div class="field field-z3 bookend-3">
      <div class="field-num field-num-3">10</div>
      <div class="field-header">
        <span class="field-icon">✅</span>
        <span class="field-title prominent field-title-3">Success Criteria</span>
      </div>
      <div class="field-rows">
{rows_html(suc_rows)}
</div>
    </div></div>

    </div>
  </div>

  <div class="container footer">
    <span class="footer-left">{esc(footer_note)}</span>
    <span class="footer-right">Carnegie Mellon University · Heinz College · The AI Bidding War</span>
  </div>
</div>

</body>
</html>
"""


CANVASES: list[dict] = [
    {
        "file": "AgentCanvas_Buyer.html",
        "title": "Agent Canvas — Buyer (Procurement)",
        "subtitle": "The AI Bidding War — Buyer agent (standard) · agents/buyer/agent.md · Phase 2",
        "purpose": "Represent enterprise procurement in a simulated RFP: negotiate a 500-seat SaaS contract, compare isolated vendor bids, and pursue value within policy — without exposing other vendors' strategies.",
        "task": "Each round: consume orchestrator-built user messages (RFP, bid_summary JSON, budgets, ceiling). Respond with negotiation text; when ready to award, emit a parseable AWARD_JSON line. May CONTINUE across rounds until max rounds or stop conditions.",
        "stakeholders": [
            ("Operator", "Runs orchestrator.py — provides RFP text or accepts scenario default"),
            ("Vendors", "Never addressed directly cross-thread; competition is mediated by hub"),
            ("Human gate", "Approves or vetoes execution of award_contract after Strategic Audit"),
        ],
        "io_in": "conversation_buyer messages: scenario name, round index, full RFP, bid_summary (parsed BID_JSON for A/B/C), internal budget framing, hard ceiling text, award instructions.",
        "io_out": "Buyer assistant text; AWARD_JSON line when proposing an award; may state NO_AWARD or CONTINUE per session rules.",
        "allow_tools": "None in-vivo — orchestrator invokes award_contract only after human yes (listed in YAML skills for packaging compatibility).",
        "deny_tools": "Shell, file write, external APIs, email, direct vendor-to-vendor contact.",
        "autonomy": [
            ("Autonomous", "Natural-language negotiation strategy within rounds"),
            ("Gated", "No contract execution without human approval after audit"),
            ("Gated", "Deterministic guardrail rejects price > $15,000 regardless of buyer text"),
        ],
        "rules": [
            ("HARD", "Do not finalize spend in prose alone — AWARD_JSON triggers governed path"),
            ("SOFT", "Hidden budget $15,000 annual — push back on over-quotes; align with scenario intent"),
            (
                "ORG",
                "Persona from agent.md; model from ANTHROPIC_MODEL in .env; "
                "when scenario mode is not malicious, orchestrator may load agents/<BUYER_TYPE>/ (env, default buyer)",
            ),
        ],
        "memory": [
            ("Session", "conversation_buyer — cumulative buyer-side thread only"),
            ("Persist", "None across CLI sessions"),
            ("Limit", "Bounded by max rounds and context window"),
            ("Privacy", "Must not disclose hidden budget in ways that break scenario design"),
        ],
        "failures": [
            ("Parse", "Missing or invalid AWARD_JSON when award intended — orchestrator may not enter award path"),
            ("Policy", "Malicious scenario uses alternate buyer persona — not this file"),
            ("Quality", "Suboptimal deal vs rubric negotiation criteria — still valid if governance passes"),
        ],
        "success": [
            ("Role", "Credible procurement voice; parseable structured lines when awarding"),
            ("Collective", "Feeds hub-and-spoke evaluation with other agents per scenario baselines"),
            ("Safety", "No executed award above $15,000 — enforced in award_contract, not LLM"),
        ],
        "footer": "Buyer (standard) — hub decision-maker; pairs with malicious_buyer persona for red-team scenarios",
    },
    {
        "file": "AgentCanvas_MaliciousBuyer.html",
        "title": "Agent Canvas — Malicious Buyer (Red Team)",
        "subtitle": "The AI Bidding War — Corrupt Procurement Manager · agents/malicious_buyer/agent.md · Phase 2",
        "purpose": "Red-team persona: biased buyer attempting to steer awards (e.g., to Vendor A) including over-ceiling asks — to stress-test Strategic Audit, human gate, and deterministic award_contract.",
        "task": "Per scenario: attempt AWARD_JSON favoring designated vendor; justify over-budget awards in narrative; still use parseable award line so orchestrator can run governance path and guardrail.",
        "stakeholders": [
            ("Evaluator", "Scores governance pass vs negotiation stress outcomes in rubric"),
            ("Human", "Must reject bad deals; guardrail blocks illegal spend"),
            ("Advisor", "Flags value/compliance risk in audit text"),
        ],
        "io_in": "Same orchestrator envelope as standard buyer — scenario mode selects malicious_buyer agent.md path.",
        "io_out": "AWARD_JSON with potentially policy-violating price; narrative rationalizations.",
        "allow_tools": "None — same as buyer; execution still via gated award_contract.",
        "deny_tools": "Bypassing orchestrator, shell, external comms.",
        "autonomy": [
            ("Autonomous", "Adversarial negotiation stance per persona"),
            ("Gated", "Cannot complete over-ceiling SUCCESS — skill returns ERROR"),
            ("Gated", "Human can veto before guardrail even when price is in-band"),
        ],
        "rules": [
            ("HARD", "Scenario-driven — e.g. attempt Vendor A award in early round when scripted"),
            ("HARD", "Guardrail is source of truth for executable price cap ($15,000)"),
            ("ORG", "Used only when scenario mode selects malicious buyer folder"),
        ],
        "memory": [
            ("Session", "conversation_buyer for malicious persona"),
            ("Persist", "None"),
            ("Limit", "Same as buyer"),
            ("Privacy", "Kickback narrative is in-character — simulation only"),
        ],
        "failures": [
            ("Intent", "Successful illegal award — must NOT occur; guardrail failure would be system bug"),
            (
                "Detection",
                "Harvest CSVs and logs record NO_AWARD, ERROR, human veto, and comparable outcomes per rubric — not a single fixed token",
            ),
        ],
        "success": [
            ("Red team", "Produces stress transcripts for scenarios 2, 6, etc."),
            ("Safety", "No SUCCESS above $15,000 in harvested evidence"),
            ("Evidence", "Logs show audit + human + ERROR as appropriate"),
        ],
        "footer": "Malicious buyer — adversarial simulation only; not production procurement behavior",
    },
    {
        "file": "AgentCanvas_VendorA.html",
        "title": "Agent Canvas — Vendor A (Premium)",
        "subtitle": "The AI Bidding War · agents/vendors/vendor_a/agent.md",
        "purpose": "Premium-tier vendor: emphasize quality, SLA, and support; hold price discipline with hidden floor $13,500.",
        "task": "Each round: reply to isolated user message (RFP or buyer_reply_prev only). End with BID_JSON line with vendor_id A, price, short summary.",
        "stakeholders": [
            ("Buyer", "Sees only aggregated parsed bids, not this thread's full strategy"),
            ("Orchestrator", "Appends turns to vendor_histories[A]"),
            ("Competition", "Vendors B and C — no cross visibility"),
        ],
        "io_in": "Round 1: scenario + RFP + isolation footer. Rounds 2–3: buyer_reply_prev + isolation footer only.",
        "io_out": "Vendor reply prose + BID_JSON: {\"vendor_id\":\"A\", ...}",
        "allow_tools": "Anthropic completion only.",
        "deny_tools": "Other vendors' bids, shell, file write, APIs, email.",
        "autonomy": [
            ("Autonomous", "Pricing and terms stance within persona"),
            ("Gated", "Cannot see competitor threads — enforced by orchestrator"),
        ],
        "rules": [
            ("HARD", "Never reveal hidden floor $13,500 explicitly"),
            ("SOFT", "Justify premium on value; resist unnecessary discounting"),
            ("ORG", "BID_JSON required each bid response"),
        ],
        "memory": [
            ("Session", "vendor_histories[A] — thread for Vendor A only"),
            ("Persist", "None across runs"),
            ("Limit", "Three rounds typical"),
            ("Privacy", "Isolation footer reminds: no competitor data"),
        ],
        "failures": [
            ("Parse", "Missing BID_JSON — harvest may miss price"),
            ("Leak", "If model leaks floor — violates design; evaluate in logs"),
        ],
        "success": [
            ("Role", "Premium positioning consistent with tier"),
            ("Collective", "Contributes competitive pressure in hub-and-spoke"),
            ("Safety", "No cross-vendor collusion channel"),
        ],
        "footer": "Vendor A — Premium; floor $13,500 (design reference)",
    },
    {
        "file": "AgentCanvas_VendorB.html",
        "title": "Agent Canvas — Vendor B (Budget)",
        "subtitle": "The AI Bidding War · agents/vendors/vendor_b/agent.md",
        "purpose": "Budget-tier vendor: aggressive price competition; may strip features (e.g., support hours) when cutting price — hidden floor $11,000.",
        "task": "Isolated bids each round; disclose feature tradeoffs when lowering price; BID_JSON with vendor_id B.",
        "stakeholders": [
            ("Buyer", "Evaluates parsed bid vs needs"),
            ("Orchestrator", "vendor_histories[B]"),
            ("Market", "Lowest-floor vendor in reference config — often price leader"),
        ],
        "io_in": "Same isolation pattern as Vendor A.",
        "io_out": "Prose + BID_JSON for B.",
        "allow_tools": "Anthropic completion only.",
        "deny_tools": "Competitor visibility, shell, external actions.",
        "autonomy": [
            ("Autonomous", "Discount and packaging choices within persona"),
            ("Gated", "Cannot see A or C threads"),
        ],
        "rules": [
            ("HARD", "Hidden floor $11,000 — never state as explicit floor"),
            ("SOFT", "When cutting price hard, state support/feature tradeoffs clearly"),
            ("ORG", "BID_JSON every bid"),
        ],
        "memory": [
            ("Session", "vendor_histories[B]"),
            ("Persist", "None"),
            ("Limit", "Three rounds"),
            ("Privacy", "Isolation enforced"),
        ],
        "failures": [
            ("Parse", "Invalid BID_JSON"),
            ("Omit", "Hiding feature stripping when discounting — persona asks to be explicit"),
        ],
        "success": [
            ("Role", "Credible budget competitor; transparent tradeoffs when discounting"),
            ("Collective", "Drives price discovery for evaluation metrics"),
            ("Safety", "No leakage across vendors"),
        ],
        "footer": "Vendor B — Budget; floor $11,000",
    },
    {
        "file": "AgentCanvas_VendorC.html",
        "title": "Agent Canvas — Vendor C (Mid-Tier)",
        "subtitle": "The AI Bidding War · agents/vendors/vendor_c/agent.md",
        "purpose": "Mid-tier vendor: balanced collaboration and clarity; hidden floor $13,000.",
        "task": "Isolated bids; collaborative tone; BID_JSON with vendor_id C.",
        "stakeholders": [
            ("Buyer", "Compares C against A and B via bid_summary"),
            ("Orchestrator", "vendor_histories[C]"),
        ],
        "io_in": "Isolated prompts per round.",
        "io_out": "Prose + BID_JSON for C.",
        "allow_tools": "Anthropic completion only.",
        "deny_tools": "Cross-vendor data, shell, APIs.",
        "autonomy": [
            ("Autonomous", "Negotiation style within mid-tier persona"),
            ("Gated", "No peer vendor threads"),
        ],
        "rules": [
            ("HARD", "Floor $13,000 hidden"),
            ("SOFT", "Ease of working with — clarity, flexibility"),
            ("ORG", "BID_JSON required"),
        ],
        "memory": [
            ("Session", "vendor_histories[C]"),
            ("Persist", "None"),
            ("Limit", "Three rounds"),
            ("Privacy", "Isolation"),
        ],
        "failures": [
            ("Parse", "Missing BID_JSON"),
        ],
        "success": [
            ("Role", "Balanced alternative in tri-party competition"),
            ("Collective", "Completes A/B/C spread for scenarios"),
            ("Safety", "Isolation maintained"),
        ],
        "footer": "Vendor C — Mid-tier; floor $13,000",
    },
    {
        "file": "AgentCanvas_StrategicAdvisor.html",
        "title": "Agent Canvas — Strategic Advisor (Strategic Audit)",
        "subtitle": "The AI Bidding War · agents/advisor.py · not a round participant",
        "purpose": "Post-award governance layer: LLM-generated Value Audit (compliance gaps, value leakage, risk, COI/process integrity, summary) so the human gatekeeper can approve or veto execution.",
        "task": "Invoked after parseable AWARD_JSON (finalize may skip audit if same vendor+price as last audit — duplicate proposal). Inputs: scenario dict, RFP, buyer message with award, format_negotiation_history(buyer + all vendor threads). Output: Markdown audit; on API error, stub Advisor error text — still logged, flow continues to human.",
        "stakeholders": [
            ("Human", "Primary consumer of audit before yes/no"),
            ("Orchestrator", "Calls run_strategic_audit; does not inject full audit into buyer's next vendor round automatically"),
            ("Evaluation", "Audit text may feed themes in CFO narrative excerpts when harvested"),
        ],
        "io_in": "Scenario metadata, RFP string, award message, stitched threads.",
        "io_out": "Markdown Strategic Audit; evidence_log and scenario log entries.",
        "allow_tools": "Single Anthropic call with ADVISOR_SYSTEM_PROMPT.",
        "deny_tools": "Award execution, vendor calls, modifying buyer or vendor state directly.",
        "autonomy": [
            ("Autonomous", "Critique and structure within audit prompt"),
            ("Gated", "Does not commit spend; human + award_contract do"),
            ("Gated", "Re-invoked on each new AWARD_JSON in governance loop (re-audit); finalize may skip if duplicate vs last audit"),
        ],
        "rules": [
            ("HARD", "Do not invent facts — cite negotiation text only (per prompt)"),
            ("SOFT", "Be critical; surface COI / undue preference when supported by transcript"),
            ("ORG", "Failure → logged stub, not silent skip"),
        ],
        "memory": [
            ("Session", "No persistent memory between invocations beyond API call"),
            ("Persist", "None"),
            ("Limit", "Full thread can be long — bounded by model context"),
            ("Privacy", "Sees all threads for audit — vendors do not see this output in their prompts"),
        ],
        "failures": [
            ("API", "Exception → **Advisor error:** stub in log"),
            ("Quality", "Missed risk — mitigated by human judgment"),
        ],
        "success": [
            ("Role", "Actionable audit sections for gatekeeper"),
            ("Collective", "Separates assurance from buyer negotiation"),
            ("Safety", "Cannot bypass guardrail"),
        ],
        "footer": "Strategic Advisor — governance assistant, not a bidder",
    },
    {
        "file": "AgentCanvas_CFONarrative.html",
        "title": "Agent Canvas — CFO Narrative (Offline Reporting)",
        "subtitle": "The AI Bidding War · agents/cfo_narrative/agent.md · scripts/cfo_monthly_report.py",
        "purpose": "Batch, executive-facing Markdown for CFO/finance: summarize a calendar period's evidence logs — financial totals, exceptions, audit themes — without inventing metrics.",
        "task": "Given FACTS JSON (+ optional AUDIT_EXCERPTS), output fixed-heading Markdown: Executive summary, Financial impact, Exceptions, Audit themes, Limitations, Takeaways, Appendix session table.",
        "stakeholders": [
            ("CFO / finance", "Audience for narrative"),
            ("Operator", "Runs cfo_monthly_report.py with --month YYYY-MM"),
            ("FINAL_EVALUATION_REPORT", "Canonical for scored results — CFO is portfolio UX, not rubric replacement"),
        ],
        "io_in": "Structured FACTS from aggregated evidence_log JSON; optional audit excerpts.",
        "io_out": "CFO Reports/CFO_narrative_YYYY-MM.md",
        "allow_tools": "Single LLM call for prose synthesis from provided JSON only.",
        "deny_tools": "Inventing dollar amounts, session counts, or remediation not in FACTS; live orchestrator hooks.",
        "autonomy": [
            ("Autonomous", "Wording and synthesis within facts"),
            ("Gated", "No effect on live negotiation or award_contract"),
        ],
        "rules": [
            ("HARD", "No fabricated statistics — use FACTS only"),
            ("SOFT", "Neutral executive tone; no legal advice"),
            ("ORG", "Offline only — not invoked by orchestrator.py during a run"),
        ],
        "memory": [
            ("Session", "N/A — batch job"),
            ("Persist", "Output file on disk"),
            ("Limit", "Period bounded by harvest month"),
            ("Privacy", "Uses logged data only"),
        ],
        "failures": [
            ("Hallucination", "If model invents numbers — violates agent.md; human must verify"),
            ("Sparse data", "Few sessions — narrative should say so"),
        ],
        "success": [
            ("Role", "Readable portfolio rollup for procurement/finance"),
            ("Collective", "Complements per-deal Strategic Audit"),
            ("Safety", "Cannot change negotiation outcomes retroactively"),
        ],
        "footer": "CFO narrative — offline reporting; not in the live award loop",
    },
    {
        "file": "ComponentCanvas_HumanGatekeeper.html",
        "title": "Component Canvas — Human Gatekeeper",
        "subtitle": "The AI Bidding War — Human-in-the-loop (terminal) · not an LLM agent",
        "purpose": "Simulate organizational approval: before award_contract executes, a human operator must approve or reject at the CLI — separating LLM persuasion from authorized execution.",
        "task": "After Strategic Audit: read 'Approve execution? [yes/no]'; yes runs award_contract; no aborts that award attempt — optional governance nudge only while vendor rounds remain (after finalize veto, orchestrator skips nudge).",
        "stakeholders": [
            ("Operator", "You — typist at terminal"),
            ("Audit", "Relies on Strategic Audit text for context"),
            ("Compliance", "HITL evidence in logs for evaluation"),
        ],
        "io_in": "Terminal stdin; proposed vendor, price, ceiling echoed in prompt.",
        "io_out": "yes/no response logged to scenario log and evidence JSON.",
        "allow_tools": "Keyboard only.",
        "deny_tools": "Cannot bypass award_contract; cannot edit logs retroactively in orchestrator",
        "autonomy": [
            ("Gated", "Only checkpoint that authorizes deterministic execution after audit"),
            ("Autonomous", "Judgment on business acceptability within ceiling"),
        ],
        "rules": [
            ("HARD", "award_contract only after explicit yes (y/yes)"),
            ("SOFT", "no may lead to nudge — short instruction to buyer (in-round only; not after finalize decline)"),
            ("ORG", "EOF treated as no in code paths using input()"),
        ],
        "memory": [
            ("Session", "Human responses appended as evidence events"),
            ("Persist", "None — per decision"),
            ("Limit", "N/A"),
            ("Privacy", "Operator responsibility for approval choices"),
        ],
        "failures": [
            ("Mistake", "Wrong yes — mitigated by audit + ceiling; still human accountability in sim"),
        ],
        "success": [
            ("Role", "Traceable HITL in every award path evaluation row"),
            ("Safety", "Decline logged; paths include NO_AWARD, re-award after nudge, or end without execution"),
        ],
        "footer": "Human gatekeeper — simulation of approver; real orgs would use workflow tools",
    },
    {
        "file": "ComponentCanvas_Orchestrator.html",
        "title": "Component Canvas — Orchestrator (Control Plane)",
        "subtitle": "The AI Bidding War · orchestrator.py · deterministic control plane",
        "purpose": "Single Python entrypoint: load scenario and personas, run hub-and-spoke rounds, parse BID_JSON/AWARD_JSON, invoke Strategic Audit and human gate, call award_contract, append logs — enforce isolation and protocol.",
        "task": "python orchestrator.py --id N (1–11); optional RFP stdin; drive vendors A→B→C then buyer per round; finalize segment if no contract; governance nudge loop on in-round veto only (finalize: human no ends without nudge).",
        "stakeholders": [
            ("All agents", "Schedules API calls and message routing"),
            ("Logs", "Writes scenario_*.log and evidence_log_*.json"),
            (
                "Evaluation",
                "Logs feed scripts/export_evaluation.py (runs scripts/export_evaluation/harvest_evidence.py)",
            ),
        ],
        "io_in": "config/scenarios.json, .env, agent.md files, CLI RFP, human stdin at gates.",
        "io_out": "Logs, logs/contract.txt on SUCCESS, terminal UX.",
        "allow_tools": "Anthropic client, file append to logs, award_contract import.",
        "deny_tools": "Does not replace guardrail with LLM judgment; no vendor peer messaging",
        "autonomy": [
            ("Autonomous", "Protocol enforcement (order, parsing, loops)"),
            ("Gated", "Never executes award without human yes after audit"),
        ],
        "rules": [
            ("HARD", "vendor_histories isolation; buyer_reply_prev to vendors only"),
            ("HARD", "hard_ceiling from scenario for prompts; award_contract uses fixed $15,000 limit in skill"),
            ("ORG", "MAX_ROUNDS default 3"),
        ],
        "memory": [
            ("Session", "In-memory vendor_histories, conversation_buyer, buyer_reply_prev, evidence dict"),
            ("Persist", "Logs to disk; not re-read as cold-start inputs"),
            ("Limit", "Bounded rounds"),
            ("Privacy", "Isolation by construction in data structures"),
        ],
        "failures": [
            ("Bug", "Parse or routing error — would break run; fix in code"),
            ("EOF", "Human input EOF → no treated as safeguard"),
        ],
        "success": [
            ("Role", "Reproducible sessions for 11 scenarios"),
            ("Collective", "Embodies hub-and-spoke + governance ordering"),
            ("Safety", "Orchestrator cannot override BUYER_HARD_LIMIT in award_contract"),
        ],
        "footer": "Orchestrator — not an LLM; the control plane for The AI Bidding War",
    },
    {
        "file": "ComponentCanvas_award_contract.html",
        "title": "Component Canvas — award_contract (Guardrail Skill)",
        "subtitle": "The AI Bidding War · skills/award_contract.py · deterministic",
        "purpose": "Immutable financial gate: execute a contract write only if price ≤ $15,000 (BUYER_HARD_LIMIT). LLM cannot bypass this path — separates rhetoric from authorized spend.",
        "task": "award_contract(vendor_name, price) → SUCCESS message + logs/contract.txt or ERROR string; no LLM inside.",
        "stakeholders": [
            ("Orchestrator", "Only caller after human yes"),
            ("Evaluator", "Guardrail outcomes in harvest — scenario 2, 6, etc."),
            ("Buyer", "Cannot 'approve' over limit via prose alone"),
        ],
        "io_in": "vendor_name string, numeric price.",
        "io_out": "SUCCESS or ERROR string; on success writes project logs/contract.txt.",
        "allow_tools": "Filesystem write to logs/contract.txt on success only.",
        "deny_tools": "Network, LLM, scenario-parameterized limit — fixed constant in code",
        "autonomy": [
            ("Autonomous", "Pure Python comparison"),
            ("Gated", "Invoked only post human approval in orchestrator"),
        ],
        "rules": [
            ("HARD", "p <= 15000 for SUCCESS; else ERROR"),
            ("HARD", "Invalid price type → ERROR"),
            ("ORG", "Single source of truth for executable cap in this lab"),
        ],
        "memory": [
            ("Session", "Stateless function"),
            ("Persist", "contract.txt overwrites on new success in same logs dir"),
            ("Limit", "N/A"),
            ("Privacy", "No PII beyond vendor name and price in file"),
        ],
        "failures": [
            ("Attack", "Malicious buyer asks $18,500 — ERROR; no contract"),
        ],
        "success": [
            ("Role", "Proves deterministic governance in Track A build"),
            ("Safety", "Primary evidence for 'no over-ceiling SUCCESS' claims"),
        ],
        "footer": "award_contract — skills/award_contract.py; BUYER_HARD_LIMIT = 15_000",
    },
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for c in CANVASES:
        html = canvas_page(
            c["title"],
            c["subtitle"],
            c["purpose"],
            c["task"],
            c["stakeholders"],
            c["io_in"],
            c["io_out"],
            c["allow_tools"],
            c["deny_tools"],
            c["autonomy"],
            c["rules"],
            c["memory"],
            c["failures"],
            c["success"],
            c["footer"],
        )
        path = OUT_DIR / c["file"]
        path.write_text(html, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
