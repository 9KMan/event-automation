"""Unit tests for DoubleCheck."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from event_automation.orchestration.double_check import DoubleCheck
from event_automation.models import Event, EventSource, VerificationResult


def create_test_event(event_id: str = "e1") -> Event:
    """Helper to create a test event."""
    return Event(
        event_id=event_id,
        title="Test Event",
        category="cultural",
        source=EventSource(
            source_name="test",
            source_type="manual",
        ),
    )


def create_proposed_result(event_id: str = "e1") -> VerificationResult:
    """Helper to create a test verification result."""
    return VerificationResult(
        event_id=event_id,
        proposed_status="verified",
        confidence=0.8,
        reasoning="Initial verification passed",
        source_evidence=["source1"],
        conflicting_fields=[],
        double_check_passed=False,
    )


class TestDoubleCheck:
    """Tests for DoubleCheck class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = AsyncMock()
        self.double_check = DoubleCheck(self.mock_llm_client)

    @pytest.mark.asyncio
    async def test_double_check_pass(self):
        """Test double-check when verification passes."""
        # Set up mock to return a "verified" response
        self.mock_llm_client.complete.return_value = '{"verified": true, "reasoning": "Evidence supports proposed change", "confidence": 0.85}'

        event = create_test_event("e1")
        proposed = create_proposed_result("e1")

        result = await self.double_check.double_check(event, proposed)

        assert result.double_check_passed is True
        assert result.confidence == 0.85
        assert "Double-check: Evidence supports proposed change" in result.reasoning

    @pytest.mark.asyncio
    async def test_double_check_fail(self):
        """Test double-check when verification fails."""
        # Set up mock to return a "rejected" response
        self.mock_llm_client.complete.return_value = '{"verified": false, "reasoning": "Evidence does not support change", "confidence": 0.4}'

        event = create_test_event("e1")
        proposed = create_proposed_result("e1")
        proposed.confidence = 0.9

        result = await self.double_check.double_check(event, proposed)

        assert result.double_check_passed is False
        assert result.confidence == 0.4
        assert "Double-check: Evidence does not support change" in result.reasoning

    @pytest.mark.asyncio
    async def test_double_check_exception(self):
        """Test double-check when LLM call fails."""
        self.mock_llm_client.complete.side_effect = Exception("API Error")

        event = create_test_event("e1")
        proposed = create_proposed_result("e1")

        result = await self.double_check.double_check(event, proposed)

        assert result.double_check_passed is False
        assert "Double-check ERROR" in result.reasoning

    @pytest.mark.asyncio
    async def test_double_check_invalid_response(self):
        """Test double-check with invalid JSON response."""
        self.mock_llm_client.complete.return_value = "Invalid JSON response"

        event = create_test_event("e1")
        proposed = create_proposed_result("e1")

        result = await self.double_check.double_check(event, proposed)

        # Should default to failed verification
        assert result.double_check_passed is False

    @pytest.mark.asyncio
    async def test_double_check_multiple_events(self):
        """Test double-check across multiple events."""
        self.mock_llm_client.complete.return_value = '{"verified": true, "reasoning": "OK", "confidence": 0.9}'

        events = [create_test_event(f"e{i}") for i in range(3)]
        results = [create_proposed_result(f"e{i}") for i in range(3)]

        for event, proposed in zip(events, results):
            result = await self.double_check.double_check(event, proposed)
            assert result.double_check_passed is True