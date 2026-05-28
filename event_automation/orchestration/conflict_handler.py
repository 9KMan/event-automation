"""ConflictHandler - Flag conflicts and route to human review queue."""
import logging
from typing import List

from event_automation.models import Event, VerificationResult, ReviewItem

logger = logging.getLogger(__name__)

# Confidence threshold for automatic approval
CONFIDENCE_THRESHOLD = 0.6


class ConflictHandler:
    """Flag conflicts and route to human review queue."""

    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD):
        """
        Initialize ConflictHandler.

        Args:
            confidence_threshold: Minimum confidence for auto-approval (default 0.6)
        """
        self.confidence_threshold = confidence_threshold

    def handle_conflict(
        self, event: Event, result: VerificationResult
    ) -> ReviewItem:
        """
        Create a ReviewItem for events with conflict/uncertain status
        or low confidence.

        Args:
            event: Original event
            result: Verification result

        Returns:
            ReviewItem for human review queue, or None if auto-approved
        """
        needs_review = self._needs_human_review(result)

        if not needs_review:
            logger.info(f"Event {event.event_id} auto-approved (confidence={result.confidence})")
            return None

        review_item = self._create_review_item(event, result)
        logger.info(
            f"Event {event.event_id} flagged for review: "
            f"status={result.proposed_status}, confidence={result.confidence}"
        )

        return review_item

    def handle_batch(
        self, events: List[Event], results: List[VerificationResult]
    ) -> List[ReviewItem]:
        """
        Process a batch of events and results.

        Returns:
            List of ReviewItems that need human review
        """
        review_items = []

        for event, result in zip(events, results):
            review_item = self.handle_conflict(event, result)
            if review_item is not None:
                review_items.append(review_item)

        logger.info(
            f"Batch processed: {len(events)} events, "
            f"{len(review_items)} flagged for review"
        )

        return review_items

    def _needs_human_review(self, result: VerificationResult) -> bool:
        """Determine if result needs human review."""
        # Status-based flags
        if result.proposed_status in ["conflict", "uncertain", "needs_review"]:
            return True

        # Low confidence threshold
        if result.confidence < self.confidence_threshold:
            return True

        # Has conflicting fields
        if result.conflicting_fields:
            return True

        return False

    def _create_review_item(
        self, event: Event, result: VerificationResult
    ) -> ReviewItem:
        """Create a ReviewItem from event and verification result."""
        return ReviewItem(
            event_id=event.event_id,
            title=event.title,
            category=event.category,
            current_data={
                "start_date": event.start_date.isoformat() if event.start_date else None,
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "venue": event.venue,
                "city": event.city,
                "verification_status": event.verification_status,
                "confidence": event.confidence,
            },
            proposed_data={
                "proposed_status": result.proposed_status,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "source_evidence": result.source_evidence,
                "conflicting_fields": result.conflicting_fields,
            },
            confidence=result.confidence,
            source_evidence=result.source_evidence,
            flagged_conflicts=result.conflicting_fields,
            needs_human_decision=True,
        )