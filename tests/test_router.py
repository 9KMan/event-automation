"""Unit tests for Router class."""
import pytest

from event_automation.orchestration.router import Router
from event_automation.models import Event, EventSource


def create_test_event(event_id: str, category: str) -> Event:
    """Helper to create a test event."""
    return Event(
        event_id=event_id,
        title=f"Test Event {event_id}",
        category=category,
        source=EventSource(
            source_name="test",
            source_type="manual",
        ),
    )


class TestRouter:
    """Tests for Router class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = Router()

    def test_route_cultural_events(self):
        """Test routing of cultural events."""
        events = [
            create_test_event("e1", "cultural"),
            create_test_event("e2", "cultural"),
        ]
        result = self.router.route(events)

        assert len(result["cultural"]) == 2
        assert len(result["sports"]) == 0
        assert len(result["concert"]) == 0
        assert len(result["unknown"]) == 0

    def test_route_sports_events(self):
        """Test routing of sports events."""
        events = [
            create_test_event("e1", "sports"),
            create_test_event("e2", "sports"),
            create_test_event("e3", "sports"),
        ]
        result = self.router.route(events)

        assert len(result["sports"]) == 3
        assert len(result["cultural"]) == 0
        assert len(result["concert"]) == 0

    def test_route_concert_events(self):
        """Test routing of concert events."""
        events = [
            create_test_event("e1", "concert"),
        ]
        result = self.router.route(events)

        assert len(result["concert"]) == 1
        assert len(result["cultural"]) == 0
        assert len(result["sports"]) == 0

    def test_route_mixed_events(self):
        """Test routing of mixed category events."""
        events = [
            create_test_event("e1", "cultural"),
            create_test_event("e2", "sports"),
            create_test_event("e3", "concert"),
            create_test_event("e4", "cultural"),
        ]
        result = self.router.route(events)

        assert len(result["cultural"]) == 2
        assert len(result["sports"]) == 1
        assert len(result["concert"]) == 1

    def test_route_unknown_category(self):
        """Test handling of unknown category."""
        events = [
            create_test_event("e1", "cultural"),
            Event(
                event_id="e2",
                title="Unknown Category Event",
                category="unknown_category",
                source=EventSource(
                    source_name="test",
                    source_type="manual",
                ),
            ),
        ]
        result = self.router.route(events)

        assert len(result["cultural"]) == 1
        assert len(result["unknown"]) == 1

    def test_route_empty_list(self):
        """Test routing of empty list."""
        result = self.router.route([])

        assert result["cultural"] == []
        assert result["sports"] == []
        assert result["concert"] == []
        assert result["unknown"] == []

    def test_route_single_event(self):
        """Test routing single event."""
        event = create_test_event("e1", "sports")
        result = self.router.route([event])

        assert len(result["sports"]) == 1

    def test_route_single_returns_category(self):
        """Test route_single returns correct category."""
        cultural_event = create_test_event("e1", "cultural")
        assert self.router.route_single(cultural_event) == "cultural"

        sports_event = create_test_event("e2", "sports")
        assert self.router.route_single(sports_event) == "sports"

        concert_event = create_test_event("e3", "concert")
        assert self.router.route_single(concert_event) == "concert"