"""Patient and pregnancy data models."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

from .common import (
    new_id, RiskBand, Trimester, ConsentStatus,
    compute_gestational_weeks, compute_trimester, compute_edd,
)


class Patient(BaseModel):
    patient_id: str = Field(default_factory=new_id)
    asha_worker_id: str = ""
    full_name: str
    husband_name: str = ""
    age: int
    village: str
    phone: str = ""
    consent_status: ConsentStatus = ConsentStatus.GRANTED
    language_preference: str = "hi"

    lmp_date: Optional[date] = None
    edd_date: Optional[date] = None
    gestational_weeks: Optional[int] = None
    trimester: Optional[Trimester] = None

    gravida: int = 1
    parity: int = 0
    known_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    blood_group: str = ""
    height_cm: Optional[float] = None

    risk_band: RiskBand = RiskBand.NORMAL
    risk_score: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def auto_compute_pregnancy_fields(self):
        if self.lmp_date:
            self.gestational_weeks = compute_gestational_weeks(self.lmp_date)
            self.trimester = compute_trimester(self.gestational_weeks)
            if not self.edd_date:
                self.edd_date = compute_edd(self.lmp_date)
        return self


class PatientSummary(BaseModel):
    """Lightweight view for list pages."""
    patient_id: str
    full_name: str
    husband_name: str = ""
    age: int
    village: str
    trimester: Optional[Trimester] = None
    gestational_weeks: Optional[int] = None
    risk_band: RiskBand = RiskBand.NORMAL
    edd_date: Optional[date] = None
    next_visit_date: Optional[date] = None


class AshaWorker(BaseModel):
    worker_id: str = Field(default_factory=new_id)
    full_name: str
    phone: str = ""
    village: str
    language: str = "hi"
    assigned_patients: int = 0
