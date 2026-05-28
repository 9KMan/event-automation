"""All Pydantic models for event_automation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class EventSource(BaseModel):
    source_name: str
    source_type: Literal["api", "scraped", "manual"]
    source_url: Optional[str] = None
    last_fetched: Optional[datetime] = None


class Event(BaseModel):
    event_id: str = Field(description="Unique internal event ID")
    title: str
    category: Literal["cultural", "sports", "concert"]
    subcategory: Optional[str] = None

    # Date info
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

    # Location
    venue: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    # Verification state
    verification_status: Literal["pending", "verified", "conflict", "uncertain", "new_discovery"] = "pending"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    verification_source: Optional[str] = None

    # Metadata
    source: EventSource
    raw_data: Optional[dict] = None
    flags: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VerificationResult(BaseModel):
    event_id: str
    proposed_status: Literal["verified", "conflict", "uncertain", "needs_review"]
    confidence: float
    reasoning: str
    source_evidence: list[str]
    conflicting_fields: list[str] = Field(default_factory=list)
    double_check_passed: bool = False


class ReviewItem(BaseModel):
    event_id: str
    title: str
    category: str
    current_data: dict
    proposed_data: dict
    confidence: float
    source_evidence: list[str]
    flagged_conflicts: list[str]
    needs_human_decision: bool