"""Router - Route events to correct workflow based on category."""
import logging
from typing import Dict, List

from event_automation.models import Event

logger = logging.getLogger(__name__)


class Router:
    """Route events to correct workflow based on category (cultural/sports/concert)."""

    CATEGORIES = ["cultural", "sports", "concert", "unknown"]

    def route(self, events: list[Event]) -> Dict[str, list[Event]]:
        """
        Route events to correct workflow based on category.

        Args:
            events: List of Event objects to route

        Returns:
            Dict with keys: "cultural", "sports", "concert", "unknown"
        """
        result = {
            "cultural": [],
            "sports": [],
            "concert": [],
            "unknown": [],
        }

        for event in events:
            category = event.category
            if category in result:
                result[category].append(event)
                logger.debug(f"Routed event {event.event_id} to {category}")
            else:
                result["unknown"].append(event)
                logger.warning(f"Unknown category for event {event.event_id}: {category}")

        logger.info(
            f"Routed {len(events)} events: "
            f"cultural={len(result['cultural'])}, "
            f"sports={len(result['sports'])}, "
            f"concert={len(result['concert'])}, "
            f"unknown={len(result['unknown'])}"
        )

        return result

    def route_single(self, event: Event) -> str:
        """
        Route a single event and return its category.

        Args:
            event: Event object to route

        Returns:
            Category string: "cultural", "sports", "concert", or "unknown"
        """
        if event.category in self.CATEGORIES[:-1]:  # All except "unknown"
            return event.category
        return "unknown"