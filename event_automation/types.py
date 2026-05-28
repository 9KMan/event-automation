"""Type definitions and constants for event_automation."""
from typing import Literal

# Category literals
CULTURAL = "cultural"
SPORTS = "sports"
CONCERT = "concert"

# Status constants
PENDING = "pending"
VERIFIED = "verified"
CONFLICT = "conflict"
UNCERTAIN = "uncertain"
NEW_DISCOVERY = "new_discovery"

# Category type
Category = Literal["cultural", "sports", "concert"]

# Status type
Status = Literal["pending", "verified", "conflict", "uncertain", "new_discovery"]

# Workflow result types
WorkflowResult = dict[str, list["VerificationResult"]]

__all__ = [
    "CULTURAL",
    "SPORTS",
    "CONCERT",
    "PENDING",
    "VERIFIED",
    "CONFLICT",
    "UNCERTAIN",
    "NEW_DISCOVERY",
    "Category",
    "Status",
    "WorkflowResult",
]