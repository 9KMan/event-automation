"""Unit tests for Batcher class."""
import pytest

from event_automation.orchestration.batcher import Batcher
from event_automation.models import Event, EventSource


def create_test_event(event_id: str) -> Event:
    """Helper to create a test event."""
    return Event(
        event_id=event_id,
        title=f"Test Event {event_id}",
        category="cultural",
        source=EventSource(
            source_name="test",
            source_type="manual",
        ),
    )


class TestBatcher:
    """Tests for Batcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.batcher = Batcher()

    def test_batch_default_size(self):
        """Test batching with default size."""
        events = [create_test_event(f"e{i}") for i in range(25)]
        batches = self.batcher.batch(events)

        # With default max_batch=20, 25 events should create 2 batches
        assert len(batches) == 2
        assert len(batches[0]) == 20
        assert len(batches[1]) == 5

    def test_batch_custom_size(self):
        """Test batching with custom size."""
        events = [create_test_event(f"e{i}") for i in range(10)]
        batches = self.batcher.batch(events, batch_size=3)

        # 10 events with size 3 should create 4 batches (3,3,3,1)
        assert len(batches) == 4
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 3
        assert len(batches[3]) == 1

    def test_batch_empty_list(self):
        """Test batching empty list."""
        batches = self.batcher.batch([])
        assert batches == []

    def test_batch_single_item(self):
        """Test batching single item."""
        events = [create_test_event("e1")]
        batches = self.batcher.batch(events)

        assert len(batches) == 1
        assert len(batches[0]) == 1

    def test_batch_exact_size(self):
        """Test batching when events fit exactly in batches."""
        events = [create_test_event(f"e{i}") for i in range(20)]
        batches = self.batcher.batch(events, batch_size=10)

        assert len(batches) == 2
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10

    def test_batch_min_batch_size(self):
        """Test that batcher respects min_batch_size."""
        batcher = Batcher(min_batch_size=5, max_batch_size=10)
        events = [create_test_event(f"e{i}") for i in range(3)]
        batches = batcher.batch(events)

        # 3 events with min_batch=5 should return as single batch (not split)
        assert len(batches) == 1

    def test_batch_by_category(self):
        """Test batch_by_category method."""
        events = [
            Event(
                event_id="e1",
                title="Cultural 1",
                category="cultural",
                source=EventSource(source_name="test", source_type="manual"),
            ),
            Event(
                event_id="e2",
                title="Cultural 2",
                category="cultural",
                source=EventSource(source_name="test", source_type="manual"),
            ),
            Event(
                event_id="e3",
                title="Sports 1",
                category="sports",
                source=EventSource(source_name="test", source_type="manual"),
            ),
        ]
        batches_by_cat = self.batcher.batch_by_category(events, batch_size=10)

        assert "cultural" in batches_by_cat
        assert "sports" in batches_by_cat
        assert len(batches_by_cat["cultural"]) == 1
        assert len(batches_by_cat["sports"]) == 1

    def test_batch_respects_max(self):
        """Test that batcher respects max_batch_size."""
        batcher = Batcher(max_batch_size=15)
        events = [create_test_event(f"e{i}") for i in range(50)]
        batches = batcher.batch(events)

        # Max 15 per batch
        for batch in batches[:-1]:  # All but last
            assert len(batch) <= 15