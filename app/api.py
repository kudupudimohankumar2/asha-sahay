"""FastAPI REST API — wraps existing service layer for the React frontend."""

import json
import logging
import os
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

api = FastAPI(title="ASHA Sahayak API", version="2.0.0")

ROOT = Path(__file__).resolve().parent.parent


@api.on_event("startup")
def _startup():
    from services.auth_service import ensure_demo_user

    ensure_demo_user()

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
    husband_name: str = ""
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


class RegisterRequest(BaseModel):
    email: str
    username: str
    full_name: str
    phone: str = ""
    password: str


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


# ── Helpers ─────────────────────────────────────────────────────────────────

def _patient_to_dict(p) -> dict:
    return {
        "patient_id": p.patient_id,
        "full_name": p.full_name,
        "husband_name": getattr(p, "husband_name", "") or "",
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
    rb = p.risk_band
    if hasattr(rb, "value"):
        rb = rb.value
    tr = p.trimester
    if hasattr(tr, "value"):
        tr = tr.value
    return {
        "patient_id": p.patient_id,
        "full_name": p.full_name,
        "husband_name": getattr(p, "husband_name", "") or "",
        "age": p.age,
        "village": p.village,
        "trimester": tr,
        "gestational_weeks": p.gestational_weeks,
        "risk_band": rb,
        "edd_date": str(p.edd_date) if p.edd_date else None,
        "next_visit_date": str(p.next_visit_date) if getattr(p, "next_visit_date", None) else None,
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


# ── Auth ────────────────────────────────────────────────────────────────────

@api.post("/auth/register")
def auth_register(req: RegisterRequest):
    from services.auth_service import make_token, register_user

    try:
        user = register_user(
            email=req.email,
            username=req.username,
            full_name=req.full_name,
            password=req.password,
            phone=req.phone,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    token = make_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@api.post("/auth/login")
def auth_login(req: LoginRequest):
    from services.auth_service import login_user, make_token

    user = login_user(req.email_or_username, req.password)
    if not user:
        raise HTTPException(401, "Invalid email/username or password")
    token = make_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@api.get("/auth/me")
def auth_me(request: Request):
    from services.auth_service import verify_token

    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    user = verify_token(auth[7:].strip())
    if not user:
        raise HTTPException(401, "Invalid session")
    return user


# ── Stats ───────────────────────────────────────────────────────────────────

@api.get("/stats")
def get_stats():
    from services.patient_service import PatientService
    from services.schedule_service import ScheduleService
    from services.db import get_db

    ps = PatientService()
    patients = ps.list_patients()
    risk_counts = ps.count_by_risk()
    total = len(patients)

    villages = set()
    for p in patients:
        villages.add(p.village)

    high_risk_cases = risk_counts.get("EMERGENCY", 0) + risk_counts.get("HIGH_RISK", 0)
    overdue = ScheduleService().get_overdue()
    actions_pending = len(overdue)

    today = date.today()
    ym = today.strftime("%Y-%m")
    db = get_db()
    del_row = db.fetch_one(
        """
        SELECT COUNT(*) AS c FROM patients
        WHERE edd_date IS NOT NULL AND substr(edd_date, 1, 7) = ?
        """,
        (ym,),
    )
    deliveries_this_month = int(del_row["c"]) if del_row else 0

    return {
        "total_patients": total,
        "emergency": risk_counts.get("EMERGENCY", 0),
        "high_risk": risk_counts.get("HIGH_RISK", 0),
        "elevated": risk_counts.get("ELEVATED", 0),
        "normal": risk_counts.get("NORMAL", 0),
        "need_attention": risk_counts.get("EMERGENCY", 0) + risk_counts.get("HIGH_RISK", 0),
        "high_risk_cases": high_risk_cases,
        "actions_pending": actions_pending,
        "deliveries_this_month": deliveries_this_month,
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
        husband_name=(req.husband_name or "").strip(),
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


@api.get("/patients/{patient_id}/clinical-summary")
def get_clinical_summary(patient_id: str):
    """Narrative summary for AI Clinical Summary card (rule-based, no LLM)."""
    from services.patient_service import PatientService
    from services.risk_service import RiskService

    ps = PatientService()
    rs = RiskService()
    patient = ps.get_patient(patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    obs = rs.get_latest_observation(patient_id)
    ev = rs.evaluate_patient(patient, obs)

    parts = [
        f"{patient.full_name} ({patient.age}y) from {patient.village} is under ANC follow-up.",
    ]
    if getattr(patient, "husband_name", None):
        parts.append(f"Spouse: {patient.husband_name}.")
    if patient.gestational_weeks is not None:
        tri = patient.trimester.value if hasattr(patient.trimester, "value") else patient.trimester
        parts.append(
            f"Estimated gestational age ~{patient.gestational_weeks} weeks ({tri} trimester)."
        )
    parts.append(
        f"Current risk band: {ev.risk_band.value if hasattr(ev.risk_band, 'value') else ev.risk_band} "
        f"(score {ev.risk_score:.0f}/100)."
    )
    if obs:
        bp = (
            f"{obs.systolic_bp}/{obs.diastolic_bp} mmHg"
            if obs.systolic_bp and obs.diastolic_bp
            else "not recorded"
        )
        hb = f"{obs.hemoglobin} g/dL" if obs.hemoglobin is not None else "not recorded"
        parts.append(f"Latest vitals on record ({obs.obs_date}): BP {bp}; Hb {hb}.")
        if obs.weight_kg is not None:
            parts.append(f"Weight {obs.weight_kg} kg.")
        if obs.symptoms:
            parts.append(f"Reported symptoms/notes: {', '.join(obs.symptoms)}.")
    else:
        parts.append("No structured visit observations recorded yet.")
    if ev.suggested_next_action:
        parts.append(f"Suggested action: {ev.suggested_next_action}")

    return {"summary": " ".join(parts)}


@api.post("/patients/{patient_id}/observations")
async def create_observation_endpoint(
    patient_id: str,
    payload: str = Form(...),
    voice: Optional[UploadFile] = File(None),
    pathology: Optional[List[UploadFile]] = File(None),
):
    """Multipart: `payload` JSON string for vitals; optional voice + pathology files."""
    from services.patient_service import PatientService
    from services.observation_service import create_observation

    ps = PatientService()
    if not ps.get_patient(patient_id):
        raise HTTPException(404, "Patient not found")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON in payload")

    od = None
    if data.get("obs_date"):
        try:
            od = date.fromisoformat(str(data["obs_date"]).strip()[:10])
        except ValueError:
            pass
    nvd = None
    if data.get("next_visit_date"):
        try:
            nvd = date.fromisoformat(str(data["next_visit_date"]).strip()[:10])
        except ValueError:
            pass

    voice_bytes = await voice.read() if voice else None
    vname = voice.filename if voice else "voice.webm"

    pathology_items = []
    for f in pathology or []:
        b = await f.read()
        if b:
            pathology_items.append((b, f.content_type or "application/octet-stream", f.filename or "pathology"))

    sym = data.get("symptoms")
    if isinstance(sym, str) and sym.strip():
        sym = [s.strip() for s in sym.split(",") if s.strip()]

    result = create_observation(
        patient_id,
        obs_date=od,
        systolic_bp=_opt_int(data.get("systolic_bp")),
        diastolic_bp=_opt_int(data.get("diastolic_bp")),
        cholesterol=_opt_float(data.get("cholesterol")),
        weight_kg=_opt_float(data.get("weight_kg")),
        hemoglobin=_opt_float(data.get("hemoglobin")),
        symptoms=sym if sym else data.get("symptoms"),
        next_visit_date=nvd,
        notes=(data.get("notes") or "").strip(),
        voice_bytes=voice_bytes,
        voice_filename=vname,
        pathology_files=pathology_items or None,
    )
    return result


def _opt_int(v):
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _opt_float(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@api.get("/patients/{patient_id}/reports")
def list_patient_reports(patient_id: str):
    from services.document_service import DocumentService
    from services.patient_service import PatientService

    if not PatientService().get_patient(patient_id):
        raise HTTPException(404, "Patient not found")
    rows = DocumentService().get_patient_reports(patient_id)
    out = []
    for r in rows or []:
        ej = r.get("extracted_json") or "{}"
        if isinstance(ej, str):
            try:
                ej = json.loads(ej)
            except json.JSONDecodeError:
                ej = {}
        flags = r.get("abnormality_flags") or "[]"
        if isinstance(flags, str):
            try:
                flags = json.loads(flags)
            except json.JSONDecodeError:
                flags = []
        out.append({
            "report_id": r["report_id"],
            "patient_id": r["patient_id"],
            "observation_id": r.get("observation_id") or "",
            "file_path": r.get("file_path", ""),
            "file_type": r.get("file_type", ""),
            "report_date": r.get("report_date"),
            "extracted_json": ej,
            "extractor_confidence": r.get("extractor_confidence", 0),
            "abnormality_flags": flags,
        })
    return out


@api.get("/patients/{patient_id}/observations/{observation_id}/voice")
def get_observation_voice(patient_id: str, observation_id: str):
    from services.db import get_db
    from services.patient_service import PatientService

    if not PatientService().get_patient(patient_id):
        raise HTTPException(404, "Patient not found")
    db = get_db()
    row = db.fetch_one(
        "SELECT * FROM observations WHERE observation_id = ? AND patient_id = ?",
        (observation_id, patient_id),
    )
    if not row or not row.get("voice_note_path"):
        raise HTTPException(404, "Voice note not found")
    path = ROOT / row["voice_note_path"]
    if not path.is_file():
        raise HTTPException(404, "Audio file missing")
    return FileResponse(path, media_type="audio/webm")


@api.get("/patients/{patient_id}/reports/{report_id}/media")
def get_report_media(patient_id: str, report_id: str):
    from services.db import get_db
    from services.patient_service import PatientService

    if not PatientService().get_patient(patient_id):
        raise HTTPException(404, "Patient not found")
    db = get_db()
    row = db.fetch_one(
        "SELECT * FROM reports WHERE report_id = ? AND patient_id = ?",
        (report_id, patient_id),
    )
    if not row:
        raise HTTPException(404, "Report not found")
    rel = row.get("file_path") or ""
    path = ROOT / rel
    if not path.is_file():
        raise HTTPException(404, "File not found on server")
    media_type = row.get("file_type") or "application/octet-stream"
    return FileResponse(path, media_type=media_type)


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
