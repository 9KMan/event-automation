"""DoubleCheck - Two-pass verification: pass1 proposes, pass2 verifies."""
import logging
from typing import Any

from event_automation.models import Event, VerificationResult

logger = logging.getLogger(__name__)


class DoubleCheck:
    """Two-pass verification: pass1 proposes, pass2 verifies."""

    def __init__(self, llm_client: Any):
        """
        Initialize DoubleCheck.

        Args:
            llm_client: LLM client for making verification calls
        """
        self.llm_client = llm_client

    async def double_check(
        self, event: Event, proposed: VerificationResult
    ) -> VerificationResult:
        """
        Perform two-pass verification on a proposed result.

        Pass 1: Original verification result was proposed
        Pass 2: Separate verification prompt confirms or rejects proposed change

        Args:
            event: Original event
            proposed: Proposed verification result from pass 1

        Returns:
            VerificationResult with double_check_passed field set
        """
        logger.info(f"Starting double-check for event {event.event_id}")

        # Build verification prompt
        verification_prompt = self._build_verification_prompt(event, proposed)

        # Make verification call
        system_prompt = (
            "You are a verification assistant. Your task is to confirm or reject "
            "proposed event verification results. Be strict but fair. "
            "Return a JSON object with fields: verified (boolean), reasoning (string), "
            "confidence (float between 0 and 1)."
        )

        try:
            response = await self.llm_client.complete(
                prompt=verification_prompt, system_prompt=system_prompt
            )

            # Parse verification response
            verification = self._parse_verification_response(response)

            # Update the proposed result with double-check status
            proposed.double_check_passed = verification["verified"]
            proposed.confidence = verification["confidence"]
            proposed.reasoning = (
                f"[Double-check: {verification['reasoning']}] "
                f"{proposed.reasoning}"
            )

            status = "PASSED" if verification["verified"] else "FAILED"
            logger.info(f"Double-check {status} for event {event.event_id}")

            return proposed

        except Exception as e:
            logger.error(f"Double-check failed for event {event.event_id}: {e}")
            proposed.double_check_passed = False
            proposed.reasoning = f"[Double-check ERROR: {str(e)}] {proposed.reasoning}"
            return proposed

    def _build_verification_prompt(
        self, event: Event, proposed: VerificationResult
    ) -> str:
        """Build prompt for verification pass."""
        return f"""Review the following event verification:

Event Details:
- ID: {event.event_id}
- Title: {event.title}
- Category: {event.category}
- Start Date: {event.start_date}
- End Date: {event.end_date}
- Venue: {event.venue}
- City: {event.city}

Current Event Data:
{event.model_dump_json(indent=2)}

Proposed Verification Result:
- Status: {proposed.proposed_status}
- Confidence: {proposed.confidence}
- Reasoning: {proposed.reasoning}
- Evidence: {proposed.source_evidence}
- Conflicting Fields: {proposed.conflicting_fields}

Does the evidence support this proposed verification? Consider:
1. Is the historical pattern consistent?
2. Are the dates accurate?
3. Is the venue correct?
4. Are there any contradictions?

Return your verification as JSON with:
- verified: boolean (true if you agree with the proposed result)
- reasoning: string explaining your decision
- confidence: float (0-1) reflecting certainty in this verification
"""

    def _parse_verification_response(self, response: str) -> dict:
        """Parse LLM verification response."""
        import json

        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                # Validate required fields
                if "verified" not in data:
                    data["verified"] = False
                if "reasoning" not in data:
                    data["reasoning"] = "No reasoning provided"
                if "confidence" not in data:
                    data["confidence"] = 0.5

                return data
        except json.JSONDecodeError:
            pass

        # Fallback: return uncertain result
        logger.warning("Could not parse verification response, defaulting to failed")
        return {
            "verified": False,
            "reasoning": "Could not parse verification response",
            "confidence": 0.5,
        }