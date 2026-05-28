# Lean Agentic Event Data Automation System

A lean Python AI event automation system that refreshes and verifies a known event universe using modern LLM reasoning with lightweight deterministic control logic.

## Project Description

This system implements an agent-first architecture where:
- **LLM performs semantic reasoning** on event data
- **Orchestration layer** handles routing, batching, retries, double-check validation, and exception surfacing
- **Three specialized workflows**: Cultural Verification, Sports Verification, and Concert Discovery

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd event_automation

# Install dependencies
pip install -e .

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with your API keys:

```
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o
SPORTS_API_KEY=
SELENIUM_HEADLESS=true
```

## Usage

### Run all workflows

```bash
python -m event_automation.main run --intake data/events.csv --output output/events.json --review output/review.xlsx
```

### Pause active runs

```bash
python -m event_automation.main pause
```

### Check status

```bash
python -m event_automation.main status
```

## Module Structure

```
event_automation/
├── orchestration/      # Routing, batching, retries, double-check, conflict handling
├── workflows/         # Cultural, Sports, Concert verification workflows
├── llm/               # LLM client, prompts, output parser, caching
├── data/              # Intake, review output, export
├── controls/           # Run/Pause/Re-run controls
├── models.py          # Pydantic data models
├── config.py          # Configuration management
├── types.py           # Type definitions and constants
└── main.py            # CLI entrypoint
```

## Testing

```bash
pytest tests/
```

## License

MIT