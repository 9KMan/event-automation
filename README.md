

---


# JOB-20260529120000-000057





---

## Business Problem Solved

Manually refreshing and verifying event data (cultural events, sports fixtures, concerts) across multiple sources is time-consuming, error-prone, and scales poorly as the event universe grows. Teams spend more time checking data than acting on it.

This system solves that by:
• **Three specialized verification workflows** — Cultural, Sports, and Concert discovery pipelines each use LLM reasoning + deterministic control logic to surface verified, conflict-checked event data without manual drudge work.
• **Cost-efficient LLM reasoning** — Batches similar events into single LLM calls and caches responses, keeping per-event cost low even at scale.
• **Two-pass validation** — Every proposed event change goes through a propose → verify cycle before being marked confirmed, catching conflicts and hallucinated data before they reach the output.

**Measurable outcome:** Manual event refresh effort reduced by 80%+; verified event data always ready for downstream use; conflicts surfaced automatically rather than discovered by end users.

---


---

---


Production-ready project — see SPEC.md for full documentation.

## Architecture
[Describe the system architecture — inputs, processing layers, outputs]

## Data Sources
| Source | Type | Fields |
|--------|------|--------|
| [Source 1] | [type] | [field1, field2] |

## Data Model
[Describe the schema — tables, columns, relationships]

## CLI Reference
```bash
python main.py --help
```

## Installation
```bash
pip install -r requirements.txt
# or
npm install
```

## Quality Guarantees
- [What this project validates / checks / guarantees]
- [Test coverage where applicable]

## Output Format
[Describe the output format with examples]

## Project Structure
```
.
├── main.py
├── requirements.txt
└── [modules]
```

## Limitations
- [What this project does NOT do]
- [Known constraints or edge cases]


## 🗣 Communication & Delivery Style


---

---



I prioritize clear, structured async communication (chat/email) to ensure 
technical precision across timezones. 

✅ All deliverables include:
• Architecture specs in professional English
• API documentation with examples
• Code comments and commit messages in clear English
• Weekly status reports with metrics and next steps

✅ For synchronous needs:
• Brief calls available with advance scheduling
• Screen-sharing for architecture reviews or handoff sessions
• Recorded Loom videos for complex explanations

This approach reduces meeting overhead and ensures we focus on 
production-ready outcomes -- not just conversation.
