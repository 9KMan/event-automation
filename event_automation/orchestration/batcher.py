"""Batcher - Batch events for cost-efficient LLM calls."""
import logging
from typing import Dict, List

from event_automation.models import Event

logger = logging.getLogger(__name__)


class Batcher:
    """Batch events for cost-efficient LLM calls (10-20 per batch)."""

    DEFAULT_MIN_BATCH = 10
    DEFAULT_MAX_BATCH = 20

    def __init__(self, min_batch_size: int = DEFAULT_MIN_BATCH, max_batch_size: int = DEFAULT_MAX_BATCH):
        """
        Initialize Batcher.

        Args:
            min_batch_size: Minimum number of events per batch (default 10)
            max_batch_size: Maximum number of events per batch (default 20)
        """
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size

    def batch(
        self, events: list[Event], batch_size: int = None
    ) -> List[List[Event]]:
        """
        Batch events for cost-efficient LLM calls.

        Args:
            events: List of Event objects to batch
            batch_size: Override default batch size (optional)

        Returns:
            List of batches, each containing Event objects
        """
        if not events:
            logger.debug("No events to batch")
            return []

        size = batch_size if batch_size is not None else self.max_batch_size

        # Clamp batch size to valid range
        size = max(self.min_batch_size, min(size, self.max_batch_size))

        batches = []
        for i in range(0, len(events), size):
            batch = events[i : i + size]
            batches.append(batch)
            logger.debug(f"Created batch of {len(batch)} events")

        logger.info(
            f"Batched {len(events)} events into {len(batches)} batches "
            f"(size={size}, min={self.min_batch_size}, max={self.max_batch_size})"
        )

        return batches

    def batch_by_category(
        self, events: list[Event], batch_size: int = None
    ) -> Dict[str, List[List[Event]]]:
        """
        Batch events by category.

        Returns:
            Dict mapping category to list of batches
        """
        from event_automation.orchestration.router import Router

        router = Router()
        routed = router.route(events)

        result = {}
        for category, category_events in routed.items():
            if category != "unknown" and category_events:
                result[category] = self.batch(category_events, batch_size)

        return result