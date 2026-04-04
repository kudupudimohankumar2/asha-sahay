"""Document upload, extraction, and processing service."""

import json
import logging
from datetime import date, datetime
from typing import Optional, Dict, Any

from models.common import new_id
from models.clinical import Report, Observation
from providers.config import get_vision_provider
from services.db import get_db

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.db = get_db()
        self.vision = get_vision_provider()

    def process_upload(
        self,
        patient_id: str,
        file_bytes: bytes,
        file_type: str,
        file_name: str = "",
    ) -> Dict[str, Any]:
        """Process an uploaded document: extract, parse, store."""
        report_id = new_id()
        file_path = f"uploads/{patient_id}/{report_id}_{file_name}"

        if file_type in ("image/jpeg", "image/png", "image/jpg", "jpg", "png", "jpeg"):
            extraction = self.vision.extract_from_image(file_bytes)
        elif file_type in ("application/pdf", "pdf"):
            extraction = self.vision.extract_from_pdf(file_bytes)
        else:
            extraction = self.vision.extract_from_image(file_bytes)

        extracted = extraction.result
        confidence = extraction.metadata.get("confidence", 0.5)

        report = Report(
            report_id=report_id,
            patient_id=patient_id,
            file_path=file_path,
            file_type=file_type,
            report_date=date.today(),
            extracted_json=extracted if isinstance(extracted, dict) else {},
            extracted_text=extracted.get("raw_text", "") if isinstance(extracted, dict) else str(extracted),
            extractor_confidence=confidence,
            abnormality_flags=self._detect_abnormalities(extracted),
        )
        self._persist_report(report)

        observation = self._create_observation_from_extraction(patient_id, report_id, extracted)
        if observation:
            self._persist_observation(observation)

        from services.retrieval_service import RetrievalService
        rs = RetrievalService()
        summary = self._build_memory_text(extracted, report.abnormality_flags)
        rs.add_patient_memory(
            patient_id=patient_id,
            text=summary,
            chunk_type="report_extraction",
            source_date=date.today().isoformat(),
        )

        return {
            "report_id": report_id,
            "extraction": extracted,
            "confidence": confidence,
            "abnormality_flags": report.abnormality_flags,
            "observation_created": observation is not None,
        }

    def get_patient_reports(self, patient_id: str):
        rows = self.db.fetch_all(
            "SELECT * FROM reports WHERE patient_id = ? ORDER BY report_date DESC",
            (patient_id,),
        )
        return rows

    def _detect_abnormalities(self, extracted: Any) -> list:
        flags = []
        if not isinstance(extracted, dict):
            return flags
        findings = extracted.get("findings", {})

        hb = findings.get("hemoglobin")
        if hb is not None:
            if hb < 7:
                flags.append("CRITICAL: Severe anemia (Hb < 7)")
            elif hb < 10:
                flags.append("WARNING: Moderate anemia (Hb 7-10)")

        sbp = findings.get("systolic_bp")
        dbp = findings.get("diastolic_bp")
        if sbp and dbp:
            if sbp > 160 or dbp > 110:
                flags.append("CRITICAL: Severe hypertension")
            elif sbp > 140 or dbp > 90:
                flags.append("WARNING: Elevated blood pressure")

        sugar = findings.get("blood_sugar_fasting")
        if sugar and sugar > 126:
            flags.append("WARNING: Elevated fasting blood sugar")

        urine_p = findings.get("urine_protein")
        if urine_p and urine_p.lower() not in ("nil", "negative", "trace", ""):
            flags.append("WARNING: Urine protein positive")

        return flags

    def _create_observation_from_extraction(
        self, patient_id: str, report_id: str, extracted: Any,
    ) -> Optional[Observation]:
        if not isinstance(extracted, dict):
            return None
        findings = extracted.get("findings", {})
        if not findings:
            return None

        return Observation(
            patient_id=patient_id,
            obs_date=date.today(),
            hemoglobin=findings.get("hemoglobin"),
            systolic_bp=findings.get("systolic_bp"),
            diastolic_bp=findings.get("diastolic_bp"),
            blood_sugar_fasting=findings.get("blood_sugar_fasting"),
            weight_kg=findings.get("weight_kg"),
            urine_protein=findings.get("urine_protein"),
            urine_sugar=findings.get("urine_sugar"),
            fetal_heart_rate=findings.get("fetal_heart_rate"),
            source_report_id=report_id,
            notes="; ".join(extracted.get("observations", [])),
        )

    def _build_memory_text(self, extracted: Any, flags: list) -> str:
        parts = [f"Report uploaded on {date.today().isoformat()}."]
        if isinstance(extracted, dict):
            for key, val in extracted.get("findings", {}).items():
                parts.append(f"{key}: {val}")
            for obs in extracted.get("observations", []):
                parts.append(f"Observation: {obs}")
            for rec in extracted.get("recommendations", []):
                parts.append(f"Recommendation: {rec}")
        if flags:
            parts.append("Flags: " + "; ".join(flags))
        return " | ".join(parts)

    def _persist_report(self, report: Report):
        self.db.insert("reports", {
            "report_id": report.report_id,
            "patient_id": report.patient_id,
            "file_path": report.file_path,
            "file_type": report.file_type,
            "report_date": report.report_date.isoformat(),
            "extracted_json": json.dumps(report.extracted_json),
            "extracted_text": report.extracted_text,
            "extractor_confidence": report.extractor_confidence,
            "abnormality_flags": json.dumps(report.abnormality_flags),
            "created_at": datetime.utcnow().isoformat(),
        })

    def _persist_observation(self, obs: Observation):
        self.db.insert("observations", {
            "observation_id": obs.observation_id,
            "patient_id": obs.patient_id,
            "obs_date": obs.obs_date.isoformat(),
            "hemoglobin": obs.hemoglobin,
            "systolic_bp": obs.systolic_bp,
            "diastolic_bp": obs.diastolic_bp,
            "blood_sugar_fasting": obs.blood_sugar_fasting,
            "blood_sugar_pp": obs.blood_sugar_pp,
            "weight_kg": obs.weight_kg,
            "urine_protein": obs.urine_protein,
            "urine_sugar": obs.urine_sugar,
            "edema": obs.edema,
            "fetal_movement": obs.fetal_movement,
            "fetal_heart_rate": obs.fetal_heart_rate,
            "fundal_height_cm": obs.fundal_height_cm,
            "pallor": obs.pallor,
            "source_report_id": obs.source_report_id,
            "notes": obs.notes,
        })
