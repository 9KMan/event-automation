"""Unit tests for OutputParser."""
import pytest

from event_automation.llm.output_parser import OutputParser
from event_automation.models import VerificationResult


class TestOutputParser:
    """Tests for OutputParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = OutputParser()

    def test_parse_cultural_valid_output(self):
        """Test parsing valid cultural output."""
        raw = '''
        [
            {
                "event_id": "e1",
                "proposed_status": "verified",
                "confidence": 0.85,
                "reasoning": "Dates match historical pattern",
                "source_evidence": ["source1", "source2"],
                "conflicting_fields": []
            }
        ]
        '''
        results = self.parser.parse_cultural_output(raw)

        assert len(results) == 1
        assert results[0].event_id == "e1"
        assert results[0].proposed_status == "verified"
        assert results[0].confidence == 0.85
        assert results[0].source_evidence == ["source1", "source2"]

    def test_parse_sports_valid_output(self):
        """Test parsing valid sports output."""
        raw = '''
        [
            {
                "event_id": "s1",
                "proposed_status": "conflict",
                "confidence": 0.4,
                "reasoning": "Schedule change detected",
                "source_evidence": ["fixture_feed"],
                "conflicting_fields": ["start_date", "venue"]
            }
        ]
        '''
        results = self.parser.parse_sports_output(raw)

        assert len(results) == 1
        assert results[0].proposed_status == "conflict"
        assert results[0].conflicting_fields == ["start_date", "venue"]

    def test_parse_concert_valid_output(self):
        """Test parsing valid concert output."""
        raw = '''
        [
            {
                "event_id": "c1",
                "proposed_status": "new_discovery",
                "confidence": 0.75,
                "reasoning": "Major tour detected",
                "source_evidence": ["ticket_sales"],
                "conflicting_fields": []
            }
        ]
        '''
        results = self.parser.parse_concert_output(raw)

        assert len(results) == 1
        assert results[0].proposed_status == "new_discovery"

    def test_parse_multiple_events(self):
        """Test parsing multiple events in output."""
        raw = '''
        [
            {"event_id": "e1", "proposed_status": "verified", "confidence": 0.9, "reasoning": "OK", "source_evidence": [], "conflicting_fields": []},
            {"event_id": "e2", "proposed_status": "conflict", "confidence": 0.4, "reasoning": "Conflict", "source_evidence": [], "conflicting_fields": ["date"]},
            {"event_id": "e3", "proposed_status": "uncertain", "confidence": 0.6, "reasoning": "Unclear", "source_evidence": [], "conflicting_fields": []}
        ]
        '''
        results = self.parser.parse_cultural_output(raw)

        assert len(results) == 3
        assert results[0].event_id == "e1"
        assert results[1].event_id == "e2"
        assert results[2].event_id == "e3"

    def test_parse_invalid_status_defaults_to_needs_review(self):
        """Test that invalid status defaults to needs_review."""
        raw = '''
        [
            {"event_id": "e1", "proposed_status": "invalid_status", "confidence": 0.5, "reasoning": "Test", "source_evidence": [], "conflicting_fields": []}
        ]
        '''
        results = self.parser.parse_cultural_output(raw)

        assert len(results) == 1
        assert results[0].proposed_status == "needs_review"

    def test_parse_confidence_out_of_range_clamped(self):
        """Test that out-of-range confidence is clamped."""
        raw = '''
        [
            {"event_id": "e1", "proposed_status": "verified", "confidence": 1.5, "reasoning": "Test", "source_evidence": [], "conflicting_fields": []}
        ]
        '''
        results = self.parser.parse_cultural_output(raw)

        assert results[0].confidence == 1.0

    def test_parse_missing_event_id(self):
        """Test handling of missing event_id."""
        raw = '''
        [
            {"proposed_status": "verified", "confidence": 0.9, "reasoning": "Test", "source_evidence": [], "conflicting_fields": []}
        ]
        '''
        results = self.parser.parse_cultural_output(raw)

        # Should create fallback result with "unknown" event_id
        assert len(results) == 1
        assert results[0].event_id == "unknown"
        assert results[0].proposed_status == "needs_review"

    def test_parse_invalid_json_raises(self):
        """Test that invalid JSON raises ValueError."""
        raw = "This is not JSON"

        with pytest.raises(ValueError):
            self.parser.parse_cultural_output(raw)

    def test_parse_empty_array(self):
        """Test parsing empty array."""
        raw = "[]"
        results = self.parser.parse_cultural_output(raw)

        assert results == []

    def test_parse_object_instead_of_array(self):
        """Test parsing single object (not array)."""
        raw = '{"event_id": "e1", "proposed_status": "verified", "confidence": 0.9, "reasoning": "Test", "source_evidence": [], "conflicting_fields": []}'
        results = self.parser.parse_cultural_output(raw)

        assert len(results) == 1
        assert results[0].event_id == "e1"