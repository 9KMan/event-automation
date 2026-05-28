"""Parse LLM outputs + Pydantic validation."""
import json
import logging
from typing import List

from event_automation.models import VerificationResult

logger = logging.getLogger(__name__)


class OutputParser:
    """Parse LLM outputs and validate against Pydantic schemas."""

    def parse_cultural_output(self, raw: str) -> List[VerificationResult]:
        """
        Parse cultural verification output.

        Args:
            raw: Raw LLM output string

        Returns:
            List of VerificationResult objects

        Raises:
            ValueError: If output cannot be parsed or validated
        """
        return self._parse_output(raw, "cultural")

    def parse_sports_output(self, raw: str) -> List[VerificationResult]:
        """
        Parse sports verification output.

        Args:
            raw: Raw LLM output string

        Returns:
            List of VerificationResult objects

        Raises:
            ValueError: If output cannot be parsed or validated
        """
        return self._parse_output(raw, "sports")

    def parse_concert_output(self, raw: str) -> List[VerificationResult]:
        """
        Parse concert discovery output.

        Args:
            raw: Raw LLM output string

        Returns:
            List of VerificationResult objects

        Raises:
            ValueError: If output cannot be parsed or validated
        """
        return self._parse_output(raw, "concert")

    def _parse_output(self, raw: str, context: str) -> List[VerificationResult]:
        """Parse raw LLM output into VerificationResult objects."""
        try:
            # Extract JSON from response
            json_str = self._extract_json(raw)
            if not json_str:
                raise ValueError(f"Could not extract JSON from {context} output")

            # Parse JSON
            data = json.loads(json_str)

            # Handle single object or array
            if isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = data
            else:
                raise ValueError(f"Unexpected JSON structure in {context} output")

            # Validate and create VerificationResult objects
            results = []
            for item in items:
                try:
                    result = self._validate_result(item)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Invalid result item in {context}: {e}")
                    # Create a fallback result for invalid items
                    results.append(
                        VerificationResult(
                            event_id=item.get("event_id", "unknown"),
                            proposed_status="needs_review",
                            confidence=0.0,
                            reasoning=f"Parse error: {str(e)}",
                            source_evidence=[],
                            conflicting_fields=[],
                            double_check_passed=False,
                        )
                    )

            return results

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {context} output: {e}")
            raise ValueError(f"Invalid JSON in {context} output: {e}")

    def _extract_json(self, raw: str) -> str:
        """Extract JSON string from raw LLM output."""
        # Try to find JSON array or object
        json_start = raw.find("[")
        json_end = raw.rfind("]")

        if json_start != -1 and json_end != -1 and json_start < json_end:
            return raw[json_start:json_end + 1]

        # Try object
        json_start = raw.find("{")
        json_end = raw.rfind("}")
        if json_start != -1 and json_end != -1:
            # Check if this looks like an array element
            return raw[json_start:json_end + 1]

        # Return the whole thing and let JSON parsing handle errors
        return raw.strip()

    def _validate_result(self, data: dict) -> VerificationResult:
        """Validate and create a VerificationResult from dict data."""
        # Validate required fields
        if "event_id" not in data:
            raise ValueError("Missing event_id")

        # Validate proposed_status
        valid_statuses = ["verified", "conflict", "uncertain", "needs_review"]
        proposed_status = data.get("proposed_status", "needs_review")
        if proposed_status not in valid_statuses:
            logger.warning(f"Invalid status {proposed_status}, defaulting to needs_review")
            proposed_status = "needs_review"

        # Validate confidence
        confidence = data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        # Ensure lists
        source_evidence = data.get("source_evidence", [])
        if not isinstance(source_evidence, list):
            source_evidence = []

        conflicting_fields = data.get("conflicting_fields", [])
        if not isinstance(conflicting_fields, list):
            conflicting_fields = []

        return VerificationResult(
            event_id=data["event_id"],
            proposed_status=proposed_status,
            confidence=confidence,
            reasoning=data.get("reasoning", "No reasoning provided"),
            source_evidence=source_evidence,
            conflicting_fields=conflicting_fields,
            double_check_passed=data.get("double_check_passed", False),
        )