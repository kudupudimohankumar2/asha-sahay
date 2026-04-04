"""Schedule and appointment models."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from .common import new_id, VisitStatus


class ScheduleEntry(BaseModel):
    schedule_id: str = Field(default_factory=new_id)
    patient_id: str
    visit_type: str
    visit_number: Optional[int] = None
    due_date: date
    suggested_slot: str = ""
    facility_name: str = ""
    tests_due: List[str] = Field(default_factory=list)
    status: VisitStatus = VisitStatus.SCHEDULED
    is_pmsma_aligned: bool = False
    escalation_flag: bool = False
    notes: str = ""


class Appointment(BaseModel):
    appointment_id: str = Field(default_factory=new_id)
    patient_id: str
    facility_name: str
    facility_type: str = "PHC"
    scheduled_datetime: datetime
    appointment_type: str = "ANC"
    status: str = "booked"
    notes: str = ""


class DailyTaskList(BaseModel):
    date: date
    village: str
    visits_due: List[ScheduleEntry]
    high_priority: List[ScheduleEntry]
    overdue: List[ScheduleEntry]
    total_patients: int = 0
