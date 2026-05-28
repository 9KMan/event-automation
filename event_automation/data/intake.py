"""Event data intake from historical dataset."""
import csv
import json
import logging
from pathlib import Path
from typing import List, Union

from event_automation.models import Event, EventSource

logger = logging.getLogger(__name__)


class Intake:
    """Event data intake from historical dataset."""

    def __init__(self):
        """Initialize Intake."""
        pass

    def load_events(self, path: str) -> List[Event]:
        """
        Load events from CSV or JSON file.

        Args:
            path: Path to event data file (.csv or .json)

        Returns:
            List of Event objects

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Event data file not found: {path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return self._load_csv(file_path)
        elif suffix == ".json":
            return self._load_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")

    def _load_csv(self, file_path: Path) -> List[Event]:
        """Load events from CSV file."""
        events = []

        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    event = self._parse_csv_row(row)
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse CSV row: {e}")
                    continue

        logger.info(f"Loaded {len(events)} events from CSV: {file_path}")
        return events

    def _load_json(self, file_path: Path) -> List[Event]:
        """Load events from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both single dict and list of dicts
        if isinstance(data, dict):
            data = [data]

        events = []
        for item in data:
            try:
                event = self._parse_json_object(item)
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse JSON object: {e}")
                continue

        logger.info(f"Loaded {len(events)} events from JSON: {file_path}")
        return events

    def _parse_csv_row(self, row: dict) -> Event:
        """Parse a CSV row into an Event object."""
        # Build source info
        source = EventSource(
            source_name=row.get("source_name", "csv_import"),
            source_type=row.get("source_type", "manual"),
            source_url=row.get("source_url"),
        )

        # Parse datetime fields
        from datetime import datetime

        start_date = None
        end_date = None
        created_at = None
        updated_at = None

        if row.get("start_date"):
            try:
                start_date = datetime.fromisoformat(row["start_date"])
            except ValueError:
                pass

        if row.get("end_date"):
            try:
                end_date = datetime.fromisoformat(row["end_date"])
            except ValueError:
                pass

        if row.get("created_at"):
            try:
                created_at = datetime.fromisoformat(row["created_at"])
            except ValueError:
                pass

        if row.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(row["updated_at"])
            except ValueError:
                pass

        # Parse flags
        flags = []
        if row.get("flags"):
            flags = row["flags"].split(";")

        return Event(
            event_id=row["event_id"],
            title=row["title"],
            category=row["category"],
            subcategory=row.get("subcategory"),
            start_date=start_date,
            end_date=end_date,
            is_recurring=row.get("is_recurring", "").lower() == "true",
            recurrence_pattern=row.get("recurrence_pattern"),
            venue=row.get("venue"),
            city=row.get("city"),
            country=row.get("country"),
            verification_status=row.get("verification_status", "pending"),
            confidence=float(row.get("confidence", 0.5)),
            verification_source=row.get("verification_source"),
            source=source,
            raw_data={},
            flags=flags,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _parse_json_object(self, obj: dict) -> Event:
        """Parse a JSON object into an Event object."""
        from datetime import datetime

        # Handle source dict
        source_data = obj.get("source", {})
        if isinstance(source_data, dict):
            source = EventSource(
                source_name=source_data.get("source_name", "json_import"),
                source_type=source_data.get("source_type", "manual"),
                source_url=source_data.get("source_url"),
                last_fetched=source_data.get("last_fetched"),
            )
        else:
            source = EventSource(
                source_name="json_import",
                source_type="manual",
            )

        # Parse datetime fields
        start_date = obj.get("start_date")
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date)
            except ValueError:
                start_date = None

        end_date = obj.get("end_date")
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date)
            except ValueError:
                end_date = None

        created_at = obj.get("created_at", datetime.utcnow())
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.utcnow()

        updated_at = obj.get("updated_at", datetime.utcnow())
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                updated_at = datetime.utcnow()

        return Event(
            event_id=obj["event_id"],
            title=obj["title"],
            category=obj["category"],
            subcategory=obj.get("subcategory"),
            start_date=start_date,
            end_date=end_date,
            is_recurring=obj.get("is_recurring", False),
            recurrence_pattern=obj.get("recurrence_pattern"),
            venue=obj.get("venue"),
            city=obj.get("city"),
            country=obj.get("country"),
            verification_status=obj.get("verification_status", "pending"),
            confidence=float(obj.get("confidence", 0.5)),
            verification_source=obj.get("verification_source"),
            source=source,
            raw_data=obj.get("raw_data", {}),
            flags=obj.get("flags", []),
            created_at=created_at,
            updated_at=updated_at,
        )