"""Seed demo data: patients, observations, facilities, guidelines."""

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.common import new_id, compute_gestational_weeks, compute_trimester, compute_edd
from services.db import get_db
from pipelines.ingest_guidelines import ingest_reference_files

logger = logging.getLogger(__name__)
SEED_DIR = Path(__file__).parent.parent / "data" / "seed"


def seed_all():
    """Seed all demo data."""
    logging.basicConfig(level=logging.INFO)
    logger.info("=== Seeding demo data ===")

    seed_facilities()
    seed_patients()
    seed_observations()
    seed_reference_thresholds()
    ingest_reference_files()

    logger.info("=== Demo data seeding complete ===")


def seed_patients():
    db = get_db()
    patients_file = SEED_DIR / "demo_patients.json"
    patients = json.loads(patients_file.read_text())

    for p in patients:
        lmp = date.fromisoformat(p["lmp_date"])
        weeks = compute_gestational_weeks(lmp)
        trimester = compute_trimester(weeks)
        edd = compute_edd(lmp)

        db.insert("patients", {
            "patient_id": p["patient_id"],
            "asha_worker_id": p.get("asha_worker_id", ""),
            "full_name": p["full_name"],
            "age": p["age"],
            "village": p["village"],
            "phone": p.get("phone", ""),
            "consent_status": "granted",
            "language_preference": p.get("language_preference", "hi"),
            "lmp_date": p["lmp_date"],
            "edd_date": edd.isoformat(),
            "gestational_weeks": weeks,
            "trimester": trimester.value,
            "gravida": p.get("gravida", 1),
            "parity": p.get("parity", 0),
            "known_conditions": json.dumps(p.get("known_conditions", [])),
            "current_medications": json.dumps(p.get("current_medications", [])),
            "blood_group": p.get("blood_group", ""),
            "height_cm": p.get("height_cm"),
            "risk_band": "NORMAL",
            "risk_score": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })
        logger.info(f"  Seeded patient: {p['full_name']} ({p['scenario']})")

    db.insert("asha_workers", {
        "worker_id": "demo-asha-001",
        "full_name": "Kavitha R.",
        "phone": "9900112233",
        "village": "Hosahalli",
        "language": "kn",
    })
    logger.info(f"  Seeded {len(patients)} patients + 1 ASHA worker")


def seed_observations():
    db = get_db()
    obs_file = SEED_DIR / "demo_observations.json"
    observations = json.loads(obs_file.read_text())

    for obs in observations:
        data = {"observation_id": new_id()}
        data.update(obs)
        db.insert("observations", data)
    logger.info(f"  Seeded {len(observations)} observations")


def seed_facilities():
    db = get_db()
    fac_file = SEED_DIR / "demo_facilities.json"
    facilities = json.loads(fac_file.read_text())

    for f in facilities:
        f["available_slots"] = json.dumps(f.get("available_slots", []))
        db.insert("facilities", f)
    logger.info(f"  Seeded {len(facilities)} facilities")


def seed_reference_thresholds():
    db = get_db()
    thresholds = [
        ("t001", "hemoglobin", "all", 11.0, 15.0, 10.0, None, 7.0, None, "g/dL", "MCP Card 2018"),
        ("t002", "systolic_bp", "all", 90, 120, None, 140, None, 160, "mmHg", "Safe Motherhood"),
        ("t003", "diastolic_bp", "all", 60, 80, None, 90, None, 110, "mmHg", "Safe Motherhood"),
        ("t004", "blood_sugar_fasting", "all", 70, 95, None, 126, None, 200, "mg/dL", "GDM Guidelines"),
        ("t005", "fetal_heart_rate", "2nd_3rd", 120, 160, 110, 170, 100, 180, "bpm", "ANC Guidelines"),
    ]
    for t in thresholds:
        db.insert("medical_thresholds", {
            "threshold_id": t[0], "parameter_name": t[1], "pregnancy_stage": t[2],
            "normal_min": t[3], "normal_max": t[4], "warning_low": t[5],
            "warning_high": t[6], "critical_low": t[7], "critical_high": t[8],
            "unit": t[9], "source_ref": t[10],
        })
    logger.info(f"  Seeded {len(thresholds)} medical thresholds")


if __name__ == "__main__":
    seed_all()
