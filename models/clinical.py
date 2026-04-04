"""Clinical data models: reports, observations, encounters."""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .common import new_id, Modality, RiskBand


class Observation(BaseModel):
    observation_id: str = Field(default_factory=new_id)
    patient_id: str
    obs_date: date = Field(default_factory=date.today)
    hemoglobin: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_sugar_fasting: Optional[float] = None
    blood_sugar_pp: Optional[float] = None
    weight_kg: Optional[float] = None
    urine_protein: Optional[str] = None
    urine_sugar: Optional[str] = None
    edema: Optional[str] = None
    fetal_movement: Optional[str] = None
    fetal_heart_rate: Optional[int] = None
    fundal_height_cm: Optional[float] = None
    pallor: Optional[str] = None
    source_report_id: Optional[str] = None
    notes: str = ""


class Report(BaseModel):
    report_id: str = Field(default_factory=new_id)
    patient_id: str
    file_path: str = ""
    file_type: str = ""
    report_date: date = Field(default_factory=date.today)
    extracted_json: Dict[str, Any] = Field(default_factory=dict)
    extracted_text: str = ""
    extractor_confidence: float = 0.0
    abnormality_flags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Encounter(BaseModel):
    encounter_id: str = Field(default_factory=new_id)
    patient_id: str
    encounter_time: datetime = Field(default_factory=datetime.utcnow)
    modality: Modality = Modality.TEXT
    source_language: str = "hi"
    original_text: str = ""
    normalized_text: str = ""
    translated_text: str = ""
    summary: str = ""
    symptoms: List[str] = Field(default_factory=list)
    extracted_health_updates: Dict[str, Any] = Field(default_factory=dict)
    ai_response: str = ""
    translated_response: str = ""
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    risk_snapshot: Optional[Dict[str, Any]] = None
    red_flag: bool = False
    escalation_status: str = "none"


class Medication(BaseModel):
    medication_id: str = Field(default_factory=new_id)
    patient_id: str
    name: str
    dosage: str = ""
    frequency: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribed_by: str = ""
    active: bool = True


class PatientFlag(BaseModel):
    flag_id: str = Field(default_factory=new_id)
    patient_id: str
    flag_type: str
    severity: str
    reason: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    active: bool = True
