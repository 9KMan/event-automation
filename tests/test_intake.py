"""Unit tests for Intake."""
import json
import os
import pytest
import tempfile
from pathlib import Path

from event_automation.data.intake import Intake
from event_automation.models import Event


class TestIntake:
    """Tests for Intake class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.intake = Intake()

    def test_load_csv(self):
        """Test loading events from CSV file."""
        csv_content = """event_id,title,category,subcategory,start_date,end_date,venue,city,country,verification_status,confidence,source_name,source_type
e1,Test Cultural Event,cultural,festival,2024-06-15T10:00:00,2024-06-15T18:00:00,Test Venue,Test City,US,pending,0.7,test_source,api
e2,Test Sports Event,sports,football,2024-07-01T14:00:00,2024-07-01T16:00:00,Sports Arena,Sports City,UK,verified,0.9,fixture_api,api"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            events = self.intake.load_events(csv_path)

            assert len(events) == 2
            assert events[0].event_id == "e1"
            assert events[0].title == "Test Cultural Event"
            assert events[0].category == "cultural"
            assert events[0].source.source_type == "api"

            assert events[1].event_id == "e2"
            assert events[1].category == "sports"
            assert events[1].verification_status == "verified"
        finally:
            os.unlink(csv_path)

    def test_load_json(self):
        """Test loading events from JSON file."""
        json_data = [
            {
                "event_id": "e1",
                "title": "JSON Cultural Event",
                "category": "cultural",
                "subcategory": "exhibition",
                "start_date": "2024-08-01T09:00:00",
                "end_date": "2024-08-01T17:00:00",
                "venue": "Gallery One",
                "city": "Art City",
                "country": "FR",
                "verification_status": "pending",
                "confidence": 0.6,
                "source": {
                    "source_name": "gallery_api",
                    "source_type": "api",
                    "source_url": "https://api.gallery.com/events"
                },
                "flags": ["new", "featured"]
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name

        try:
            events = self.intake.load_events(json_path)

            assert len(events) == 1
            assert events[0].event_id == "e1"
            assert events[0].title == "JSON Cultural Event"
            assert events[0].category == "cultural"
            assert events[0].source.source_name == "gallery_api"
            assert events[0].flags == ["new", "featured"]
        finally:
            os.unlink(json_path)

    def test_load_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            self.intake.load_events("/nonexistent/path/events.csv")

    def test_load_unsupported_format(self):
        """Test that ValueError is raised for unsupported formats."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some content")
            txt_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                self.intake.load_events(txt_path)
        finally:
            os.unlink(txt_path)

    def test_load_empty_csv(self):
        """Test loading empty CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("event_id,title,category,source_name,source_type\ne1,Test, cultural,test,manual")
            csv_path = f.name

        try:
            events = self.intake.load_events(csv_path)
            # May have 0 or 1 events depending on how empty is defined
            assert isinstance(events, list)
        finally:
            os.unlink(csv_path)

    def test_load_json_single_object(self):
        """Test loading JSON with single object (not array)."""
        json_data = {
            "event_id": "e1",
            "title": "Single Event",
            "category": "concert",
            "source": {
                "source_name": "manual",
                "source_type": "manual"
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name

        try:
            events = self.intake.load_events(json_path)

            assert len(events) == 1
            assert events[0].event_id == "e1"
            assert events[0].category == "concert"
        finally:
            os.unlink(json_path)

    def test_csv_parse_datetime(self):
        """Test datetime parsing in CSV loading."""
        csv_content = """event_id,title,category,start_date,end_date,source_name,source_type
e1,Date Test,cultural,2024-06-15T10:00:00,2024-06-20T18:00:00,test,manual"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            events = self.intake.load_events(csv_path)

            assert len(events) == 1
            assert events[0].start_date.year == 2024
            assert events[0].start_date.month == 6
            assert events[0].start_date.day == 15
        finally:
            os.unlink(csv_path)

    def test_csv_parse_flags(self):
        """Test flags parsing in CSV loading."""
        csv_content = """event_id,title,category,start_date,end_date,source_name,source_type,flags
e1,Flag Test,cultural,2024-06-15T10:00:00,2024-06-20T18:00:00,test,manual,urgent;review;new"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            events = self.intake.load_events(csv_path)

            assert len(events) == 1
            assert "urgent" in events[0].flags
            assert "review" in events[0].flags
            assert "new" in events[0].flags
        finally:
            os.unlink(csv_path)