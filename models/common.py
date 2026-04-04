"""Shared enumerations and base types."""

from enum import Enum
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


class RiskBand(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH_RISK = "HIGH_RISK"
    EMERGENCY = "EMERGENCY"


class Trimester(str, Enum):
    FIRST = "1st"
    SECOND = "2nd"
    THIRD = "3rd"


class Modality(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"


class VisitStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    MISSED = "missed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class ConsentStatus(str, Enum):
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"


def compute_gestational_weeks(lmp_date: date, ref_date: Optional[date] = None) -> int:
    ref = ref_date or date.today()
    delta = ref - lmp_date
    return max(0, delta.days // 7)


def compute_trimester(weeks: int) -> Trimester:
    if weeks <= 13:
        return Trimester.FIRST
    elif weeks <= 27:
        return Trimester.SECOND
    else:
        return Trimester.THIRD


def compute_edd(lmp_date: date) -> date:
    """Naegele's rule: EDD = LMP + 280 days."""
    from datetime import timedelta
    return lmp_date + timedelta(days=280)


class AuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str
    entity_type: str
    entity_id: str
    actor: str = "system"
    details: Optional[dict] = None
