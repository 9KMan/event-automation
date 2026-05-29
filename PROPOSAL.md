# Lean Agentic Event Data Automation System — Proposal

## Architecture: Three Workflows, One Lean Orchestration Layer

The key architectural question is how to keep the orchestration layer lean while supporting three distinct semantic workflows. Here's the approach:

**Separation of concerns by design:**
- Workflows (cultural / sports / concert) contain domain-specific reasoning: prompts, source connectors, domain validation
- Orchestration layer handles only transport logic: routing, batching, retries, double-check, conflict flagging
- Interface contract: every workflow implements `def run(events: list[Event]) -> list[VerificationResult]` — adding a new workflow means implementing the interface, not touching orchestration

**Shared orchestration is deliberately thin:**
```
Routing     → which workflow handles this event?
Batching    → group events for cost-efficient LLM calls (10-20 per batch)
Retries     → exponential backoff, max 3, only on transient failures
Double-check→ two-pass verification (propose → verify), disagreements → human review
Structured output → Pydantic validation on every LLM response
Exception surfacing → no silent failures, every exception → review queue
```

This is not a rule engine — it's a lightweight control layer that delegates semantic reasoning to the LLM.

---

## Minimizing Recurring LLM/API Cost

Five-layer cost minimization strategy:

1. **Batch similar events** — group events by type/category. One LLM call for 15 cultural events is ~15x cheaper than 15 individual calls. Batching logic is deterministic and source-aware.

2. **Response caching** — cache LLM responses keyed on `hash(event_data + source_hash)`. If the source data hasn't changed, the cached response is valid. Cache invalidation via watermark: only re-call when source timestamp advances.

3. **Two-tier model selection** — use cheap models (GPT-4o-mini, Claude Haiku) for classification/routing decisions, expensive models (GPT-4o, Claude Sonnet) only for semantic verification. Classification happens once; verification happens on filtered subset.

4. **Deduplication before LLM call** — events that appear in multiple sources are resolved before batching. No duplicate LLM calls for the same semantic entity.

5. **Watermark-based incremental runs** — full runs only on first intake; subsequent runs only re-process events whose source data has changed since last run. Event universe doesn't change daily — most runs touch only delta.

---

## Double-Check Validation for Surfaced Event Changes

Two-pass verification is the core of the quality strategy:

**Pass 1 — Propose:**
Prompt provides: event historical record + current proposed data + source evidence.
LLM returns: proposed change, confidence (0-1), reasoning, source citations.

**Pass 2 — Verify:**
Separate prompt with different framing: given the evidence, does the proposed change hold?
LLM returns: confirmed / rejected / uncertain with reasoning.

**Only apply if both passes agree.** Disagreements → human review queue with both LLM responses surfaced.

All decisions logged with full evidence chain: event_id, pass1_response, pass2_response, final_decision, timestamp. Audit trail for every change.

---

## Estimated Implementation: 40 hours | 10 days

| Phase | Hours | Days | Deliverables |
|-------|-------|------|-------------|
| Intake + Core Architecture | 8 | 1-2 | Project scaffold, event intake, orchestration layer, LLM client |
| Three Workflows | 16 | 3-5 | Cultural, Sports, Concert workflows with conflict handling |
| Review + Export + Controls | 12 | 6-7 | Spreadsheet review, export pipeline, run/pause/re-run controls |
| Testing + Polish | 4 | 8-10 | Unit/integration tests, cost tracking, edge cases |

---

## Why This Fits Lean Agentic Implementation

- **No rule engine** — semantic reasoning delegated to LLM, not hard-coded
- **No dashboard** — spreadsheet output, no UI framework
- **No overbuilt architecture** — thin orchestration, workflow interfaces, minimum viable abstractions
- **Agent-first** — LLM does the reasoning; Python orchestrates the reasoning process
- **Structured output** — Pydantic validation on every LLM response, not raw text parsing
- **Double-check** — quality via verification passes, not by adding more rules

This is a lean automation system: a Python orchestration layer with strong LLM integration, not a traditional software platform.


🎁 Included with this proposal:
✅ Public PoC repo with working code + architecture spec
✅ Async-first communication: clear updates via chat/email, no meeting overhead
✅ 30 days of post-delivery support for questions and minor adjustments

If this aligns with your needs, I can expand the PoC to full production delivery within the timeline above. Happy to answer any questions or share additional architecture diagrams.

Best regards,
Mongkolpoj Phanutaecha
Principal Data Platform Architect | AI-Augmented Engineering Factory
Bangkok, Thailand (GMT+7) | Open to Remote Contracts
