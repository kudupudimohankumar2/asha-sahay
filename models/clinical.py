"""Clinical data models: reports, observations, encounters."""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import new_id, Modality, RiskBand


class Observation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    observation_id: str = Field(default_factory=new_id)
    patient_id: str
    obs_date: date = Field(default_factory=date.today)
    hemoglobin: Optional[float] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    cholesterol: Optional[float] = None
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
    symptoms: List[str] = Field(default_factory=list)
    next_visit_date: Optional[date] = None
    voice_note_path: Optional[str] = None

    @field_validator("obs_date", mode="before")
    @classmethod
    def _v_obs_date(cls, v):
        if v is None or v == "":
            return date.today()
        if isinstance(v, date):
            return v
        return date.fromisoformat(str(v))

    @field_validator("next_visit_date", mode="before")
    @classmethod
    def _v_next_visit(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, date):
            return v
        return date.fromisoformat(str(v))

    @field_validator("symptoms", mode="before")
    @classmethod
    def _v_symptoms(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except json.JSONDecodeError:
                pass
            return [s.strip() for s in v.split(",") if s.strip()]
        return []


class Report(BaseModel):
    report_id: str = Field(default_factory=new_id)
    patient_id: str
    observation_id: str = ""
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
