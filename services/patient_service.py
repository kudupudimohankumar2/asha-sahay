"""Patient profile management service."""

import json
import logging
from datetime import date, datetime
from typing import List, Optional

from models.patient import Patient, PatientSummary
from models.common import (
    new_id, RiskBand, Trimester, compute_gestational_weeks,
    compute_trimester, compute_edd,
)
from services.db import get_db

logger = logging.getLogger(__name__)


class PatientService:
    def __init__(self):
        self.db = get_db()

    def create_patient(self, patient: Patient) -> Patient:
        """Register a new pregnant woman."""
        if patient.lmp_date:
            patient.gestational_weeks = compute_gestational_weeks(patient.lmp_date)
            patient.trimester = compute_trimester(patient.gestational_weeks)
            if not patient.edd_date:
                patient.edd_date = compute_edd(patient.lmp_date)

        data = patient.model_dump()
        data["known_conditions"] = json.dumps(data.get("known_conditions", []))
        data["current_medications"] = json.dumps(data.get("current_medications", []))
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()
        if data.get("lmp_date"):
            data["lmp_date"] = str(data["lmp_date"])
        if data.get("edd_date"):
            data["edd_date"] = str(data["edd_date"])
        if data.get("trimester"):
            data["trimester"] = data["trimester"].value if hasattr(data["trimester"], "value") else data["trimester"]

        self.db.insert("patients", data)
        logger.info(f"Created patient {patient.patient_id}: {patient.full_name}")
        return patient

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        row = self.db.fetch_one("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        if not row:
            return None
        return self._row_to_patient(row)

    def list_patients(self, village: Optional[str] = None) -> List[PatientSummary]:
        if village:
            rows = self.db.fetch_all(
                "SELECT * FROM patients WHERE village = ? ORDER BY risk_band, edd_date",
                (village,),
            )
        else:
            rows = self.db.fetch_all("SELECT * FROM patients ORDER BY risk_band, edd_date")

        return self._summaries_with_next_visit(rows)

    def update_patient(self, patient_id: str, updates: dict) -> Optional[Patient]:
        if "known_conditions" in updates and isinstance(updates["known_conditions"], list):
            updates["known_conditions"] = json.dumps(updates["known_conditions"])
        if "current_medications" in updates and isinstance(updates["current_medications"], list):
            updates["current_medications"] = json.dumps(updates["current_medications"])
        if "lmp_date" in updates:
            lmp = updates["lmp_date"]
            if isinstance(lmp, date):
                updates["lmp_date"] = lmp.isoformat()
                updates["gestational_weeks"] = compute_gestational_weeks(lmp)
                tri = compute_trimester(updates["gestational_weeks"])
                updates["trimester"] = tri.value
                updates["edd_date"] = compute_edd(lmp).isoformat()

        updates["updated_at"] = datetime.utcnow().isoformat()
        self.db.update("patients", "patient_id", patient_id, updates)
        return self.get_patient(patient_id)

    def update_risk(self, patient_id: str, risk_band: RiskBand, risk_score: float):
        self.db.update("patients", "patient_id", patient_id, {
            "risk_band": risk_band.value,
            "risk_score": risk_score,
            "updated_at": datetime.utcnow().isoformat(),
        })

    def search_patients(self, query: str) -> List[PatientSummary]:
        rows = self.db.fetch_all(
            """SELECT * FROM patients WHERE full_name LIKE ? OR village LIKE ? OR phone LIKE ?
               OR IFNULL(husband_name, '') LIKE ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"),
        )
        return self._summaries_with_next_visit(rows)

    def _next_visit_map(self, patient_ids: List[str]) -> dict:
        if not patient_ids:
            return {}
        placeholders = ",".join(["?"] * len(patient_ids))
        rows = self.db.fetch_all(
            f"""SELECT patient_id, MIN(due_date) AS nd FROM schedules
                WHERE patient_id IN ({placeholders}) AND status != 'completed'
                GROUP BY patient_id""",
            tuple(patient_ids),
        )
        out = {}
        for r in rows:
            if r.get("nd"):
                try:
                    out[r["patient_id"]] = date.fromisoformat(r["nd"])
                except ValueError:
                    pass
        return out

    def _summaries_with_next_visit(self, rows: List[dict]) -> List[PatientSummary]:
        ids = [r["patient_id"] for r in rows]
        nv = self._next_visit_map(ids)
        return [self._row_to_summary(r, next_visit_date=nv.get(r["patient_id"])) for r in rows]

    def get_village_patients(self, village: str) -> List[Patient]:
        rows = self.db.fetch_all(
            "SELECT * FROM patients WHERE village = ?", (village,)
        )
        return [self._row_to_patient(r) for r in rows]

    def count_by_risk(self, village: Optional[str] = None) -> dict:
        where = f"WHERE village = '{village}'" if village else ""
        rows = self.db.fetch_all(
            f"SELECT risk_band, COUNT(*) as cnt FROM patients {where} GROUP BY risk_band"
        )
        return {r["risk_band"]: r["cnt"] for r in rows}

    def _row_to_patient(self, row: dict) -> Patient:
        conditions = row.get("known_conditions", "[]")
        if isinstance(conditions, str):
            try:
                conditions = json.loads(conditions)
            except json.JSONDecodeError:
                conditions = []
        meds = row.get("current_medications", "[]")
        if isinstance(meds, str):
            try:
                meds = json.loads(meds)
            except json.JSONDecodeError:
                meds = []

        rb = row.get("risk_band", "NORMAL")
        try:
            rb_e = RiskBand(rb) if isinstance(rb, str) else rb
        except ValueError:
            rb_e = RiskBand.NORMAL
        tri = row.get("trimester")
        tri_e = None
        if tri:
            try:
                tri_e = Trimester(tri)
            except ValueError:
                tri_e = None

        return Patient(
            patient_id=row["patient_id"],
            asha_worker_id=row.get("asha_worker_id", ""),
            full_name=row["full_name"],
            husband_name=row.get("husband_name", "") or "",
            age=row["age"],
            village=row["village"],
            phone=row.get("phone", ""),
            consent_status=row.get("consent_status", "granted"),
            language_preference=row.get("language_preference", "hi"),
            lmp_date=date.fromisoformat(row["lmp_date"]) if row.get("lmp_date") else None,
            edd_date=date.fromisoformat(row["edd_date"]) if row.get("edd_date") else None,
            gestational_weeks=row.get("gestational_weeks"),
            trimester=tri_e,
            gravida=row.get("gravida", 1),
            parity=row.get("parity", 0),
            known_conditions=conditions,
            current_medications=meds,
            blood_group=row.get("blood_group", ""),
            height_cm=row.get("height_cm"),
            risk_band=rb_e,
            risk_score=row.get("risk_score", 0.0),
        )

    def _row_to_summary(self, row: dict, next_visit_date: Optional[date] = None) -> PatientSummary:
        rb = row.get("risk_band", "NORMAL")
        try:
            rb_e = RiskBand(rb) if isinstance(rb, str) else rb
        except ValueError:
            rb_e = RiskBand.NORMAL
        tri = row.get("trimester")
        tri_e = None
        if tri:
            try:
                tri_e = Trimester(tri)
            except ValueError:
                tri_e = None
        return PatientSummary(
            patient_id=row["patient_id"],
            full_name=row["full_name"],
            husband_name=row.get("husband_name", "") or "",
            age=row["age"],
            village=row["village"],
            trimester=tri_e,
            gestational_weeks=row.get("gestational_weeks"),
            risk_band=rb_e,
            edd_date=date.fromisoformat(row["edd_date"]) if row.get("edd_date") else None,
            next_visit_date=next_visit_date,
        )
