"""Create and list clinical observations (visits) with optional media."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Optional

from models.common import new_id
from services.db import get_db
from services.document_service import DocumentService

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "data" / "uploads"


def _parse_symptoms(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return []
        try:
            return [x.strip() for x in json.loads(s) if x]
        except json.JSONDecodeError:
            return [p.strip() for p in s.split(",") if p.strip()]
    return []


def create_observation(
    patient_id: str,
    *,
    obs_date: Optional[date] = None,
    systolic_bp: Optional[int] = None,
    diastolic_bp: Optional[int] = None,
    cholesterol: Optional[float] = None,
    weight_kg: Optional[float] = None,
    hemoglobin: Optional[float] = None,
    symptoms: Any = None,
    next_visit_date: Optional[date] = None,
    notes: str = "",
    voice_bytes: Optional[bytes] = None,
    voice_filename: str = "voice.webm",
    pathology_files: Optional[List[tuple[bytes, str, str]]] = None,
) -> dict[str, Any]:
    """
    pathology_files: list of (bytes, content_type, filename)
    """
    db = get_db()
    obs_id = new_id()
    od = obs_date or date.today()
    sym_list = _parse_symptoms(symptoms)

    voice_path = ""
    if voice_bytes:
        UPLOADS.mkdir(parents=True, exist_ok=True)
        ext = Path(voice_filename).suffix or ".webm"
        dest = UPLOADS / patient_id / f"voice_{obs_id}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(voice_bytes)
        voice_path = str(dest.relative_to(ROOT))

    row = {
        "observation_id": obs.observation_id,
        "patient_id": patient_id,
        "obs_date": od.isoformat(),
        "hemoglobin": hemoglobin,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "blood_sugar_fasting": None,
        "blood_sugar_pp": None,
        "weight_kg": weight_kg,
        "urine_protein": None,
        "urine_sugar": None,
        "edema": None,
        "fetal_movement": None,
        "fetal_heart_rate": None,
        "fundal_height_cm": None,
        "pallor": None,
        "source_report_id": None,
        "notes": notes or "",
        "cholesterol": cholesterol,
        "symptoms": json.dumps(sym_list),
        "next_visit_date": next_visit_date.isoformat() if next_visit_date else None,
        "voice_note_path": voice_path,
    }
    db.insert("observations", row)

    report_ids: List[str] = []
    doc = DocumentService()
    for item in pathology_files or []:
        b, ctype, fname = item[0], item[1], item[2]
        r = doc.process_upload(
            patient_id,
            b,
            ctype,
            fname,
            observation_id=obs_id,
        )
        report_ids.append(r.get("report_id", ""))

    from services.risk_service import RiskService
    from services.patient_service import PatientService

    ps = PatientService()
    patient = ps.get_patient(patient_id)
    if patient:
        latest = RiskService().get_latest_observation(patient_id)
        RiskService().evaluate_patient(patient, latest)

    return {"observation_id": obs_id, "report_ids": report_ids}
