"""FastAPI REST API — wraps existing service layer for the React frontend."""

import json
import logging
import os
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

api = FastAPI(title="ASHA Sahayak API", version="2.0.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response schemas ──────────────────────────────────────────────

class PatientCreate(BaseModel):
    full_name: str
    age: int
    village: str
    phone: str = ""
    language_preference: str = "hi"
    lmp_date: str
    gravida: int = 1
    parity: int = 0
    blood_group: str = "Unknown"
    known_conditions: list[str] = []
    current_medications: list[str] = []


class ChatRequest(BaseModel):
    text: Optional[str] = None
    source_language: str = "hi"
    mode: str = "general"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _patient_to_dict(p) -> dict:
    return {
        "patient_id": p.patient_id,
        "full_name": p.full_name,
        "age": p.age,
        "village": p.village,
        "phone": getattr(p, "phone", ""),
        "language_preference": getattr(p, "language_preference", "hi"),
        "lmp_date": str(p.lmp_date) if p.lmp_date else None,
        "edd_date": str(p.edd_date) if p.edd_date else None,
        "gestational_weeks": p.gestational_weeks,
        "trimester": p.trimester if isinstance(p.trimester, str) else (p.trimester.value if p.trimester else None),
        "gravida": getattr(p, "gravida", 1),
        "parity": getattr(p, "parity", 0),
        "blood_group": getattr(p, "blood_group", ""),
        "known_conditions": getattr(p, "known_conditions", []),
        "current_medications": getattr(p, "current_medications", []),
        "risk_band": p.risk_band if isinstance(p.risk_band, str) else (p.risk_band.value if p.risk_band else "NORMAL"),
        "risk_score": getattr(p, "risk_score", 0.0),
    }


def _summary_to_dict(p) -> dict:
    return {
        "patient_id": p.patient_id,
        "full_name": p.full_name,
        "age": p.age,
        "village": p.village,
        "trimester": p.trimester,
        "gestational_weeks": p.gestational_weeks,
        "risk_band": p.risk_band,
        "edd_date": str(p.edd_date) if p.edd_date else None,
    }


# ── Health Check ─────────────────────────────────────────────────────────────

@api.get("/health")
def health_check():
    """Provider connectivity check."""
    from providers.config import _get_sarvam_key
    has_key = bool(_get_sarvam_key())
    return {
        "status": "ok",
        "sarvam_key_configured": has_key,
        "providers": {
            "reasoning": os.getenv("REASONING_PROVIDER", "mock"),
            "translation": os.getenv("TRANSLATION_PROVIDER", "mock"),
            "speech": os.getenv("SPEECH_PROVIDER", "mock"),
            "vision": os.getenv("VISION_PROVIDER", "mock"),
            "embeddings": os.getenv("EMBEDDING_PROVIDER", "mock"),
        },
    }


# ── Stats ───────────────────────────────────────────────────────────────────

@api.get("/stats")
def get_stats():
    from services.patient_service import PatientService
    ps = PatientService()
    patients = ps.list_patients()
    risk_counts = ps.count_by_risk()
    total = len(patients)

    villages = set()
    for p in patients:
        villages.add(p.village)

    return {
        "total_patients": total,
        "emergency": risk_counts.get("EMERGENCY", 0),
        "high_risk": risk_counts.get("HIGH_RISK", 0),
        "elevated": risk_counts.get("ELEVATED", 0),
        "normal": risk_counts.get("NORMAL", 0),
        "need_attention": risk_counts.get("EMERGENCY", 0) + risk_counts.get("HIGH_RISK", 0),
        "villages": len(villages),
        "village_names": sorted(villages),
        "date": date.today().isoformat(),
    }


# ── Alerts ──────────────────────────────────────────────────────────────────

@api.get("/alerts")
def get_alerts():
    from services.db import get_db
    db = get_db()
    alerts = db.fetch_all("""
        SELECT a.*, p.full_name FROM alerts a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.active = 1 ORDER BY a.created_at DESC LIMIT 20
    """)
    return alerts or []


# ── Schedule endpoints ──────────────────────────────────────────────────────

@api.get("/schedule/today")
def get_today_visits():
    from services.schedule_service import ScheduleService
    ss = ScheduleService()
    visits = ss.get_due_today()
    result = []
    for v in visits:
        result.append({
            "schedule_id": v.schedule_id,
            "patient_id": v.patient_id,
            "visit_type": v.visit_type,
            "due_date": str(v.due_date),
            "tests_due": v.tests_due,
            "status": v.status.value if hasattr(v.status, "value") else v.status,
            "is_pmsma_aligned": v.is_pmsma_aligned,
            "escalation_flag": v.escalation_flag,
        })
    return result


@api.get("/schedule/overdue")
def get_overdue_visits():
    from services.schedule_service import ScheduleService
    ss = ScheduleService()
    visits = ss.get_overdue()
    result = []
    for v in visits:
        result.append({
            "schedule_id": v.schedule_id,
            "patient_id": v.patient_id,
            "visit_type": v.visit_type,
            "due_date": str(v.due_date),
            "tests_due": v.tests_due,
            "status": v.status.value if hasattr(v.status, "value") else v.status,
            "is_pmsma_aligned": v.is_pmsma_aligned,
            "escalation_flag": v.escalation_flag,
        })
    return result


# ── Patients ────────────────────────────────────────────────────────────────

@api.get("/patients")
def list_patients(search: Optional[str] = Query(None), village: Optional[str] = Query(None)):
    from services.patient_service import PatientService
    ps = PatientService()
    if search:
        patients = ps.search_patients(search)
    elif village:
        patients = ps.list_patients(village=village)
    else:
        patients = ps.list_patients()
    return [_summary_to_dict(p) for p in patients]


@api.post("/patients")
def create_patient(req: PatientCreate):
    from models.patient import Patient
    from services.patient_service import PatientService
    from services.schedule_service import ScheduleService
    from services.risk_service import RiskService

    try:
        lmp = date.fromisoformat(req.lmp_date.strip())
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    patient = Patient(
        full_name=req.full_name.strip(),
        age=req.age,
        village=req.village.strip(),
        phone=req.phone.strip(),
        language_preference=req.language_preference,
        lmp_date=lmp,
        gravida=req.gravida,
        parity=req.parity,
        blood_group=req.blood_group,
        known_conditions=req.known_conditions,
        current_medications=req.current_medications,
    )

    ps = PatientService()
    patient = ps.create_patient(patient)

    ScheduleService().generate_schedule(patient)
    RiskService().evaluate_patient(patient)

    return _patient_to_dict(patient)


@api.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    from services.patient_service import PatientService
    ps = PatientService()
    patient = ps.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    return _patient_to_dict(patient)


# ── Risk ────────────────────────────────────────────────────────────────────

@api.get("/patients/{patient_id}/risk")
def get_risk(patient_id: str):
    from services.patient_service import PatientService
    from services.risk_service import RiskService

    ps = PatientService()
    rs = RiskService()
    patient = ps.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    obs = rs.get_latest_observation(patient_id)
    evaluation = rs.evaluate_patient(patient, obs)

    return {
        "risk_band": evaluation.risk_band.value if hasattr(evaluation.risk_band, "value") else evaluation.risk_band,
        "risk_score": evaluation.risk_score,
        "triggered_rules": evaluation.triggered_rules,
        "reason_codes": evaluation.reason_codes,
        "suggested_next_action": evaluation.suggested_next_action,
        "emergency_flag": evaluation.emergency_flag,
        "escalation_recommendation": getattr(evaluation, "escalation_recommendation", ""),
    }


# ── Schedule ────────────────────────────────────────────────────────────────

@api.get("/patients/{patient_id}/schedule")
def get_schedule(patient_id: str):
    from services.schedule_service import ScheduleService
    ss = ScheduleService()
    schedule = ss.get_patient_schedule(patient_id)
    result = []
    for entry in schedule:
        result.append({
            "schedule_id": entry.schedule_id,
            "visit_type": entry.visit_type,
            "due_date": str(entry.due_date),
            "tests_due": entry.tests_due,
            "status": entry.status.value if hasattr(entry.status, "value") else entry.status,
            "is_pmsma_aligned": entry.is_pmsma_aligned,
            "escalation_flag": entry.escalation_flag,
        })
    return result


# ── Ration ──────────────────────────────────────────────────────────────────

@api.get("/patients/{patient_id}/ration")
def get_ration(patient_id: str):
    from services.patient_service import PatientService
    from services.ration_service import RationService
    from services.risk_service import RiskService

    ps = PatientService()
    patient = ps.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    obs = RiskService().get_latest_observation(patient_id)
    rec = RationService().generate_recommendation(patient, obs)

    items = []
    for item in rec.ration_items:
        items.append({
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "frequency": item.frequency,
            "category": getattr(item, "category", ""),
        })

    return {
        "week_start": str(rec.week_start),
        "calorie_target": rec.calorie_target,
        "protein_target_g": rec.protein_target_g,
        "ration_items": items,
        "supplements": rec.supplements,
        "special_adjustments": getattr(rec, "special_adjustments", []),
        "rationale": rec.rationale,
        "rule_basis": rec.rule_basis,
    }


# ── Observations ────────────────────────────────────────────────────────────

@api.get("/patients/{patient_id}/observations")
def get_observations(patient_id: str):
    from services.db import get_db
    db = get_db()
    rows = db.fetch_all(
        "SELECT * FROM observations WHERE patient_id = ? ORDER BY obs_date DESC",
        (patient_id,),
    )
    return rows or []


# ── Chat ────────────────────────────────────────────────────────────────────

@api.post("/patients/{patient_id}/chat")
def chat(patient_id: str, req: ChatRequest):
    from services.conversation_service import ConversationService
    conv = ConversationService()
    result = conv.process_message(
        patient_id=patient_id,
        text=req.text,
        audio_bytes=None,
        image_bytes=None,
        source_language=req.source_language,
        mode=req.mode,
    )
    return result


@api.post("/patients/{patient_id}/chat/multipart")
async def chat_multipart(
    patient_id: str,
    text: Optional[str] = Form(None),
    source_language: str = Form("hi"),
    mode: str = Form("general"),
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """Multipart chat: supports text + audio + image in a single request."""
    from services.conversation_service import ConversationService
    conv = ConversationService()
    audio_bytes = await audio.read() if audio else None
    image_bytes = await image.read() if image else None
    result = conv.process_message(
        patient_id=patient_id,
        text=text,
        audio_bytes=audio_bytes,
        image_bytes=image_bytes,
        source_language=source_language,
        mode=mode,
    )
    return result


# ── Documents ───────────────────────────────────────────────────────────────

@api.post("/patients/{patient_id}/documents")
async def upload_document(patient_id: str, file: UploadFile = File(...)):
    from services.document_service import DocumentService
    doc_svc = DocumentService()
    file_bytes = await file.read()
    content_type = file.content_type or "application/pdf"
    result = doc_svc.process_upload(patient_id, file_bytes, content_type, file.filename or "upload")
    return result


# ── Dashboard ───────────────────────────────────────────────────────────────

@api.get("/dashboard/{village}")
def get_dashboard(village: str):
    from services.dashboard_service import DashboardService
    ds = DashboardService()
    return ds.get_village_dashboard(village.strip())
