# Lean Agentic Event Data Automation System

## 1. Concept & Vision

A lean Python AI event automation system that refreshes and verifies a known event universe using modern LLM reasoning with lightweight deterministic control logic. Not a traditional software platform — a rapid, lean automation implementation with an agent-first architecture. The LLM performs semantic reasoning; the orchestration layer handles routing, batching, retries, structured output capture, double-check validation, and exception surfacing. Clean, maintainable, built for a developer who cares about precision over ceremony.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                      │
│  routing · batching · retries · double-check · conflict      │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  CULTURAL        │  │  SPORTS          │  │  CONCERT          │
│  VERIFICATION    │  │  VERIFICATION    │  │  DISCOVERY        │
│  WORKFLOW        │  │  WORKFLOW        │  │  WORKFLOW         │
│                  │  │                  │  │                  │
│ · Source audit   │  │ · Fixture ingest │  │ · Tour surface   │
│ · Date confirm   │  │ · Change detect  │  │ · Human approval  │
│ · Future edition │  │ · Discrepancy   │  │ · Event extract   │
│ · Conflict flag  │  │   surface        │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         │                    │                    │
         └──────────┬─────────┴────────────────────┘
                    ▼
         ┌──────────────────────┐
         │   REVIEW OUTPUT      │
         │  (spreadsheet OK)    │
         └──────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   EXPORT OUTPUT      │
         │  (clean event data)  │
         └──────────────────────┘
```

### Agent-First Principle

The LLM is the reasoning engine. The orchestration layer is deliberately thin — it delegates semantic judgment to the LLM, keeps only:
- Routing logic (where does this event go?)
- Batching logic (group events for cost efficiency)
- Retry logic (with backoff, for transient failures)
- Double-check logic (two-pass: propose → verify)
- Structured output capture (Pydantic validation)
- Exception surfacing (flag for human review)

What it is NOT:
- No heavy hard-coded rule engine
- No overbuilt traditional architecture
- No dashboard-first solution
- No generic scraping scripts

---

## 3. Three Workflows + Shared Orchestration

### 3.1 Cultural Verification Workflow

**Purpose:** Verify upcoming editions of cultural events, confirm dates/details, surface future editions, flag conflicts.

**Data sources:** Structured historical event dataset (CSV/JSON import)

**Process:**
1. Load curated event records from intake
2. For each event category, batch events by type
3. Route to LLM for semantic verification:
   - Has this event been held historically at this time?
   - Are dates/details consistent with historical pattern?
   - Is a future edition announced?
   - Are there known conflicts or uncertainties?
4. Capture structured output (verified / conflict / uncertain / new edition)
5. Flag conflicts for human review

**LLM prompt approach:** Context-rich prompts with historical data; structured output schema (Pydantic model)

### 3.2 Sports Verification Workflow

**Purpose:** Monitor approved league universe — ingest fixture schedules, detect changes, surface discrepancies.

**Data sources:** Approved league API endpoints, fixture feeds

**Process:**
1. Ingest current fixture schedules for defined league universe
2. Compare against known event records
3. Route changes to LLM for discrepancy analysis:
   - Schedule change detected — confirm or reject
   - New fixture added — is it in our universe?
   - Time/date modification — flag if material
4. Capture structured output
5. Surface discrepancies for review

### 3.3 Concert Discovery Workflow

**Purpose:** Monitor approved source universe for major tours, support human approval, extract approved event details.

**Data sources:** Approved scraping targets, artist tour RSS/APIs

**Process:**
1. Monitor approved sources for candidate major tours
2. Surface candidates for human approval (simple approval queue)
3. Extract approved event details via LLM-assisted extraction
4. Route confirmed events to export pipeline

### 3.4 Shared Orchestration Layer

**Core responsibilities:**
- **Execution routing:** Route raw events to the correct workflow based on type/category
- **Batching:** Group similar events into LLM batch calls to minimize API cost (batch by category, ~10-20 events per call)
- **Retries:** Exponential backoff for transient failures (API timeout, rate limit); max 3 retries
- **Double-check verification:** Two-pass — pass 1: LLM proposes changes; pass 2: different prompt verifies proposed changes
- **Conflict handling:** When workflows disagree or confidence is low, flag for human review
- **Structured output capture:** All LLM outputs validated against Pydantic schemas
- **Exception surfacing:** Unhandled cases → human review queue (not silent failures)

**Cost minimization strategy:**
- Batch similar events into single LLM calls (10-20 per batch)
- Cache LLM responses for identical/near-identical queries
- Only re-query when source data changes (watermark-based)
- Use cheaper models for classification, expensive models only for verification
- Deduplicate across workflows before calling LLM

---

## 4. Data Model

### Event Record Schema

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class EventSource(BaseModel):
    source_name: str
    source_type: Literal["api", "scraped", "manual"]
    source_url: Optional[str] = None
    last_fetched: Optional[datetime] = None

class Event(BaseModel):
    event_id: str = Field(description="Unique internal event ID")
    title: str
    category: Literal["cultural", "sports", "concert"]
    subcategory: Optional[str] = None
    
    # Date info
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    
    # Location
    venue: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    
    # Verification state
    verification_status: Literal["pending", "verified", "conflict", "uncertain", "new_discovery"] = "pending"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    verification_source: Optional[str] = None
    
    # Metadata
    source: EventSource
    raw_data: Optional[dict] = None
    flags: list[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VerificationResult(BaseModel):
    event_id: str
    proposed_status: Literal["verified", "conflict", "uncertain", "needs_review"]
    confidence: float
    reasoning: str
    source_evidence: list[str]
    conflicting_fields: list[str] = Field(default_factory=list)
    double_check_passed: bool = False
```

### Review Output Schema

```python
class ReviewItem(BaseModel):
    event_id: str
    title: str
    category: str
    current_data: dict
    proposed_data: dict
    confidence: float
    source_evidence: list[str]
    flagged_conflicts: list[str]
    needs_human_decision: bool
```

---

## 5. Review Output Layer

Spreadsheet-based output is acceptable. No polished dashboard required.

**Output format:** CSV/Excel with columns:
- event_id, title, category
- current_value (date/venue/details)
- proposed_value
- confidence
- source_evidence (URLs)
- flagged_conflicts
- needs_human_decision (Y/N)

**Controls:**
- Run: execute all workflows
- Pause: halt active runs (no new LLM calls)
- Re-run by category: re-execute specific workflow (cultural / sports / concert)

---

## 6. Module Structure

```
event_automation/
├── orchestration/
│   ├── __init__.py
│   ├── router.py          # Route events to correct workflow
│   ├── batcher.py          # Batch events for cost-efficient LLM calls
│   ├── retry_handler.py    # Exponential backoff, max 3 retries
│   ├── double_check.py     # Two-pass verification logic
│   └── conflict_handler.py # Conflict flagging + human review queue
│
├── workflows/
│   ├── __init__.py
│   ├── cultural.py         # Cultural Verification Workflow
│   ├── sports.py           # Sports Verification Workflow
│   └── concert.py          # Concert Discovery Workflow
│
├── llm/
│   ├── __init__.py
│   ├── client.py           # LLM API client (OpenAI/Anthropic)
│   ├── prompts.py          # Prompt templates per workflow
│   ├── output_parser.py    # Structured output + Pydantic validation
│   └── cache.py            # Response caching for cost minimization
│
├── data/
│   ├── __init__.py
│   ├── intake.py           # Event data intake from historical dataset
│   ├── review_output.py    # Generate spreadsheet review output
│   └── export.py           # Clean export for downstream clustering
│
├── controls/
│   ├── __init__.py
│   └── run_controls.py     # Run / Pause / Re-run by category
│
└── main.py                 # CLI entrypoint
```

---

## 7. Out of Scope

- Dashboard / UI
- Traditional rule engine
- Polished web application
- Heavy frontend framework
- Generic scraping without LLM reasoning
- Real-time streaming (batch processing is acceptable)
- Multi-tenant / user management
- Database persistence beyond CSV/JSON export

---

## 8. External Dependencies

| Package | Purpose |
|---------|---------|
| `openai` or `anthropic` | LLM API client |
| `pydantic` | Data validation |
| `selenium` / `playwright` | Browser automation (concert discovery) |
| `requests` / `httpx` | API integration |
| `beautifulsoup4` | HTML parsing |
| `pandas` | Spreadsheet review output |
| `python-dotenv` | Environment config |

---

## 9. Configuration

Environment variables:
```
LLM_API_KEY=           # OpenAI or Anthropic key
LLM_MODEL=             # e.g. gpt-4o, claude-3-5-sonnet
SPORTS_API_KEY=        # Optional: sports data provider
SELENIUM_HEADLESS=     # true/false for browser automation
```

---

## 10. Quality & Testing

- **Unit tests** for orchestration logic (router, batcher, retry handler)
- **Integration tests** for each workflow (mock LLM responses)
- **Output validation** — every LLM output must pass Pydantic schema validation or be flagged as exception
- **Double-check audit** — log all two-pass verification decisions
- **Cost tracking** — log LLM call count and token usage per run

---

## 11. Screening Questions Answers

**Q1: Three workflows + one lean shared orchestration layer?**

Architecture separates workflow-specific reasoning (LLM prompts + domain logic) from cross-cutting concerns (routing, batching, retries, double-check). Each workflow implements the same interface: `def run(events: list[Event]) -> list[VerificationResult]`. The orchestration layer calls the appropriate workflow and handles transport-level concerns. New workflows can be added by implementing the interface without modifying the orchestration core.

**Q2: Minimize recurring LLM/API cost?**

(1) Batch similar events — group 10-20 events of same type into single LLM call. (2) Cache LLM responses keyed on event hash + source hash — identical queries don't repeat API calls. (3) Watermark-based invalidation — only re-call LLM when source data changed. (4) Two-tier model: cheap model for classification (which workflow? what category?), expensive model only for semantic verification. (5) Deduplicate across workflows before calling LLM.

**Q3: Double-check validation for surfaced event changes?**

Two-pass approach. Pass 1: LLM proposes change with reasoning and confidence. Pass 2: Separate verification prompt — given the event data and the proposed change, does the evidence support this? Returns confirmed/rejected with reasoning. Only apply change if both passes agree. Disagreements → human review queue. All decisions logged with evidence chain.

**Q4: Similar automation / AI workflow systems?**

(Will customize with specific examples in cover letter)

**Q5: Estimated hours, timeline, lean fit?**

- Estimated: 40 hours (within 30-50h range)
- Timeline: Day 1-2 intake + architecture; Day 3-5 core workflows; Day 6-7 integration; Day 8-10 review output + export + controls
- Lean fit: Agent-first, no rule engine, no dashboard, structured output, spreadsheet review, minimum viable orchestration. Every component earns its place.

---

## 12. Milestones

### Phase 1: Intake + Core Architecture (8 hrs)
- Project scaffold + dependencies
- Event data intake from historical dataset
- Shared orchestration layer (router, batcher, retry, double-check)
- LLM client + output parser

### Phase 2: Three Workflows (16 hrs)
- Cultural Verification Workflow
- Sports Verification Workflow
- Concert Discovery Workflow
- Conflict handling + human review flagging

### Phase 3: Review + Export + Controls (12 hrs)
- Review output layer (spreadsheet)
- Export pipeline for downstream clustering
- Run/Pause/Re-run controls

### Phase 4: Testing + Polish (4 hrs)
- Unit + integration tests
- Cost tracking + audit logging
- Edge case handling

Total: ~40 hrs | 10 days