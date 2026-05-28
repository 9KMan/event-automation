"""Generate spreadsheet review output."""
import io
import logging
from typing import List

try:
    import pandas as pd
except ImportError:
    pd = None

from event_automation.models import ReviewItem

logger = logging.getLogger(__name__)


class ReviewOutput:
    """Generate spreadsheet review output."""

    def __init__(self):
        """Initialize ReviewOutput."""
        pass

    def generate_review(self, review_items: List[ReviewItem]) -> bytes:
        """
        Generate Excel review spreadsheet.

        Args:
            review_items: List of ReviewItem objects to include in review

        Returns:
            Excel file as bytes

        Raises:
            ImportError: If pandas is not installed
        """
        if pd is None:
            raise ImportError("pandas is required for review output generation")

        if not review_items:
            logger.warning("No review items to generate")
            return b""

        # Build DataFrame
        data = []
        for item in review_items:
            data.append(
                {
                    "event_id": item.event_id,
                    "title": item.title,
                    "category": item.category,
                    "current_value": self._format_current_value(item.current_data),
                    "proposed_value": self._format_proposed_value(item.proposed_data),
                    "confidence": item.confidence,
                    "source_evidence": "; ".join(item.source_evidence),
                    "flagged_conflicts": "; ".join(item.flagged_conflicts),
                    "needs_human_decision": "Y" if item.needs_human_decision else "N",
                }
            )

        df = pd.DataFrame(data)

        # Write to Excel bytes
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Review", index=False)

        output.seek(0)
        logger.info(f"Generated review spreadsheet with {len(review_items)} items")
        return output.read()

    def _format_current_value(self, current_data: dict) -> str:
        """Format current data as a readable string."""
        parts = []
        if current_data.get("start_date"):
            parts.append(f"Start: {current_data['start_date']}")
        if current_data.get("venue"):
            parts.append(f"Venue: {current_data['venue']}")
        if current_data.get("city"):
            parts.append(f"City: {current_data['city']}")
        if current_data.get("verification_status"):
            parts.append(f"Status: {current_data['verification_status']}")
        return ", ".join(parts) if parts else "N/A"

    def _format_proposed_value(self, proposed_data: dict) -> str:
        """Format proposed data as a readable string."""
        parts = []
        if proposed_data.get("proposed_status"):
            parts.append(f"Status: {proposed_data['proposed_status']}")
        if proposed_data.get("reasoning"):
            reasoning = proposed_data["reasoning"]
            if len(reasoning) > 100:
                reasoning = reasoning[:100] + "..."
            parts.append(f"Reason: {reasoning}")
        return ", ".join(parts) if parts else "N/A"

    def generate_csv(self, review_items: List[ReviewItem]) -> str:
        """
        Generate CSV review output.

        Args:
            review_items: List of ReviewItem objects

        Returns:
            CSV string
        """
        if not review_items:
            return ""

        lines = [
            "event_id,title,category,current_value,proposed_value,confidence,"
            "source_evidence,flagged_conflicts,needs_human_decision"
        ]

        for item in review_items:
            lines.append(
                f"{self._escape_csv(item.event_id)},"
                f"{self._escape_csv(item.title)},"
                f"{self._escape_csv(item.category)},"
                f"{self._escape_csv(self._format_current_value(item.current_data))},"
                f"{self._escape_csv(self._format_proposed_value(item.proposed_data))},"
                f"{item.confidence},"
                f"{self._escape_csv('; '.join(item.source_evidence))},"
                f"{self._escape_csv('; '.join(item.flagged_conflicts))},"
                f"{'Y' if item.needs_human_decision else 'N'}"
            )

        return "\n".join(lines)

    def _escape_csv(self, value: str) -> str:
        """Escape a value for CSV."""
        if not value:
            return ""
        value = str(value)
        if '"' in value or "," in value or "\n" in value:
            return '"' + value.replace('"', '""') + '"'
        return value