"""Prompt templates per workflow (cultural, sports, concert)."""
import json
from typing import List, Dict, Any

from event_automation.models import Event


class PromptTemplates:
    """Prompt templates per workflow."""

    # Historical context placeholder (would be populated with actual data)
    HISTORICAL_CONTEXT = """
Historical Event Patterns:
- Annual festivals typically occur in same month/season
- Major venues have consistent scheduling patterns
- Recurring events have predictable date ranges
""".strip()

    def get_cultural_prompt(self, events: List[Event], historical_events: List[Event] = None) -> str:
        """
        Build cultural verification prompt.

        Args:
            events: List of cultural events to verify
            historical_events: List of historical events for context

        Returns:
            Formatted prompt string
        """
        events_json = self._events_to_json(events)
        historical_json = (
            self._events_to_json(historical_events) if historical_events else "[]"
        )

        return f"""You are verifying cultural events against historical patterns.

Given the following events to verify:
{events_json}

And historical event data:
{historical_json}

Analyze each event and return a JSON array of verification results. For each event:
1. Check if dates are consistent with historical patterns
2. Verify venue and location details
3. Look for known conflicts or discrepancies
4. Identify any future editions that may be announced
5. Assign a confidence score (0-1)

Return a JSON array with this structure:
[
  {{
    "event_id": "string",
    "proposed_status": "verified|conflict|uncertain|needs_review",
    "confidence": 0.0-1.0,
    "reasoning": "string explaining the verification decision",
    "source_evidence": ["list of evidence sources"],
    "conflicting_fields": ["list of fields with conflicts"]
  }}
]

Ensure the JSON is valid and parseable.""".strip()

    def get_sports_prompt(self, events: List[Event]) -> str:
        """
        Build sports verification prompt.

        Args:
            events: List of sports events/fixtures to verify

        Returns:
            Formatted prompt string
        """
        events_json = self._events_to_json(events)

        return f"""You are verifying sports fixtures against approved league schedules.

Given the following sports events/fixtures to verify:
{events_json}

Analyze each event and detect:
1. Schedule changes from known records
2. New fixtures added to the league
3. Time/date modifications that are material
4. Discrepancies between event data and official schedules
5. Home/away venue changes

Return a JSON array with this structure:
[
  {{
    "event_id": "string",
    "proposed_status": "verified|conflict|uncertain|needs_review",
    "confidence": 0.0-1.0,
    "reasoning": "string explaining the verification decision",
    "source_evidence": ["list of evidence sources"],
    "conflicting_fields": ["list of fields with discrepancies"]
  }}
]

Ensure the JSON is valid and parseable.""".strip()

    def get_concert_prompt(self, events: List[Event]) -> str:
        """
        Build concert discovery prompt.

        Args:
            events: List of potential concert/tour events

        Returns:
            Formatted prompt string
        """
        events_json = self._events_to_json(events)

        return f"""You are discovering major concert tours from candidate events.

Given the following potential concert events:
{events_json}

Analyze each event and determine:
1. Is this a major tour or significant artist?
2. Are dates and venues confirmed?
3. Should this be surfaced for human approval?
4. What are the key event details for extraction?
5. Is this a new discovery not in our current database?

Return a JSON array with this structure:
[
  {{
    "event_id": "string",
    "proposed_status": "verified|new_discovery|needs_review",
    "confidence": 0.0-1.0,
    "reasoning": "string explaining the discovery decision",
    "source_evidence": ["list of evidence sources"],
    "conflicting_fields": ["list of fields needing verification"]
  }}
]

Ensure the JSON is valid and parseable.""".strip()

    def get_verification_prompt(self, event: Event, proposed: Dict[str, Any]) -> str:
        """
        Build verification prompt for double-check pass.

        Args:
            event: Original event
            proposed: Proposed verification result

        Returns:
            Formatted prompt string
        """
        return f"""You are verifying an event change proposal.

Event Details:
- ID: {event.event_id}
- Title: {event.title}
- Category: {event.category}
- Start Date: {event.start_date}
- End Date: {event.end_date}
- Venue: {event.venue}
- City: {event.city}

Proposed Change:
{json.dumps(proposed, indent=2)}

Review the proposed change and verify:
1. Is the evidence supporting this change compelling?
2. Are there any contradictions with known patterns?
3. Would this change be consistent with historical data?

Return a JSON object:
{{
  "verified": boolean,
  "reasoning": "string explaining your decision",
  "confidence": 0.0-1.0
}}

Ensure the JSON is valid and parseable.""".strip()

    def _events_to_json(self, events: List[Event]) -> str:
        """Convert events to JSON string."""
        if not events:
            return "[]"

        return json.dumps(
            [
                {
                    "event_id": e.event_id,
                    "title": e.title,
                    "category": e.category,
                    "subcategory": e.subcategory,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "venue": e.venue,
                    "city": e.city,
                    "country": e.country,
                    "is_recurring": e.is_recurring,
                }
                for e in events
            ],
            indent=2,
        )