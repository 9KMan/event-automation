"""Clean export for downstream clustering."""
import csv
import json
import logging
from pathlib import Path
from typing import List

from event_automation.models import Event

logger = logging.getLogger(__name__)


class Export:
    """Clean export for downstream clustering."""

    def __init__(self):
        """Initialize Export."""
        pass

    def export_events(self, events: List[Event], path: str) -> None:
        """
        Export events to CSV or JSON file.

        Args:
            events: List of Event objects to export
            path: Output file path (.csv or .json)

        Raises:
            ValueError: If file format is not supported
        """
        file_path = Path(path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            self._export_csv(events, file_path)
        elif suffix == ".json":
            self._export_json(events, file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")

        logger.info(f"Exported {len(events)} events to {path}")

    def _export_csv(self, events: List[Event], file_path: Path) -> None:
        """Export events to CSV file."""
        fieldnames = [
            "event_id",
            "title",
            "category",
            "subcategory",
            "start_date",
            "end_date",
            "is_recurring",
            "recurrence_pattern",
            "venue",
            "city",
            "country",
            "verification_status",
            "confidence",
            "verification_source",
            "flags",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for event in events:
                row = {
                    "event_id": event.event_id,
                    "title": event.title,
                    "category": event.category,
                    "subcategory": event.subcategory or "",
                    "start_date": event.start_date.isoformat() if event.start_date else "",
                    "end_date": event.end_date.isoformat() if event.end_date else "",
                    "is_recurring": str(event.is_recurring),
                    "recurrence_pattern": event.recurrence_pattern or "",
                    "venue": event.venue or "",
                    "city": event.city or "",
                    "country": event.country or "",
                    "verification_status": event.verification_status,
                    "confidence": event.confidence,
                    "verification_source": event.verification_source or "",
                    "flags": ";".join(event.flags),
                }
                writer.writerow(row)

    def _export_json(self, events: List[Event], file_path: Path) -> None:
        """Export events to JSON file."""
        data = []

        for event in events:
            data.append(
                {
                    "event_id": event.event_id,
                    "title": event.title,
                    "category": event.category,
                    "subcategory": event.subcategory,
                    "start_date": event.start_date.isoformat() if event.start_date else None,
                    "end_date": event.end_date.isoformat() if event.end_date else None,
                    "is_recurring": event.is_recurring,
                    "recurrence_pattern": event.recurrence_pattern,
                    "venue": event.venue,
                    "city": event.city,
                    "country": event.country,
                    "verification_status": event.verification_status,
                    "confidence": event.confidence,
                    "verification_source": event.verification_source,
                    "flags": event.flags,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "updated_at": event.updated_at.isoformat() if event.updated_at else None,
                }
            )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)