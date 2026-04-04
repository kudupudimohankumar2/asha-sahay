"""Populate the application database from synthetic data files.

Reads generated JSON from data/synthetic/, inserts into the database,
then runs risk evaluation, schedule generation, and ration planning
for every patient.

Usage:
    python -m tools.populate_production_db          # from repo root
    python tools/populate_production_db.py          # direct
"""

import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from models.common import compute_gestational_weeks, compute_trimester, compute_edd, new_id
from services.db import get_db
from pipelines.ingest_guidelines import ingest_reference_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("populate")

SYNTHETIC_DIR = ROOT / "data" / "synthetic"


def _load_json(name: str) -> list:
    path = SYNTHETIC_DIR / name
    if not path.exists():
        logger.error(f"Missing {path} — run 'python -m tools.generate_all' first")
        sys.exit(1)
    return json.loads(path.read_text())


def populate_facilities():
    db = get_db()
    facilities = _load_json("facilities.json")
    for f in facilities:
        f["available_slots"] = json.dumps(f.get("available_slots", []))
        db.insert("facilities", f)
    logger.info(f"Inserted {len(facilities)} facilities")


def populate_asha_workers():
    db = get_db()
    workers = _load_json("asha_workers.json")
    for w in workers:
        db.insert("asha_workers", w)
    logger.info(f"Inserted {len(workers)} ASHA workers")


def populate_patients():
    db = get_db()
    patients = _load_json("patients.json")
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
    logger.info(f"Inserted {len(patients)} patients")


def populate_observations():
    db = get_db()
    observations = _load_json("observations.json")
    for obs in observations:
        data = {"observation_id": new_id()}
        data.update(obs)
        db.insert("observations", data)
    logger.info(f"Inserted {len(observations)} observations")


def populate_medical_thresholds():
    db = get_db()
    thresholds = [
        ("t001", "hemoglobin", "all", 11.0, 15.0, 10.0, None, 7.0, None, "g/dL", "MCP Card 2018"),
        ("t002", "systolic_bp", "all", 90, 120, None, 140, None, 160, "mmHg", "Safe Motherhood Booklet"),
        ("t003", "diastolic_bp", "all", 60, 80, None, 90, None, 110, "mmHg", "Safe Motherhood Booklet"),
        ("t004", "blood_sugar_fasting", "all", 70, 95, None, 126, None, 200, "mg/dL", "GDM Guidelines"),
        ("t005", "blood_sugar_pp", "all", 70, 140, None, 180, None, 250, "mg/dL", "GDM Guidelines"),
        ("t006", "fetal_heart_rate", "2nd_3rd", 120, 160, 110, 170, 100, 180, "bpm", "ANC Guidelines"),
        ("t007", "weight_gain_monthly", "2nd_3rd", 1.0, 2.5, 0.5, 3.0, 0, 4.0, "kg/month", "ICMR"),
        ("t008", "fundal_height", "2nd_3rd", None, None, None, None, None, None, "cm", "ANC Guidelines"),
    ]
    for t in thresholds:
        db.insert("medical_thresholds", {
            "threshold_id": t[0], "parameter_name": t[1], "pregnancy_stage": t[2],
            "normal_min": t[3], "normal_max": t[4], "warning_low": t[5],
            "warning_high": t[6], "critical_low": t[7], "critical_high": t[8],
            "unit": t[9], "source_ref": t[10],
        })
    logger.info(f"Inserted {len(thresholds)} medical thresholds")


def run_engines():
    """Run risk, schedule, and ration engines for all patients."""
    from services.patient_service import PatientService
    from services.risk_service import RiskService
    from services.schedule_service import ScheduleService
    from services.ration_service import RationService

    ps = PatientService()
    rs = RiskService()
    ss = ScheduleService()
    ration = RationService()

    patients = ps.list_patients()
    logger.info(f"Running engines for {len(patients)} patients...")

    for p_summary in patients:
        patient = ps.get_patient(p_summary.patient_id)
        if not patient:
            continue

        obs = rs.get_latest_observation(patient.patient_id)
        risk_eval = rs.evaluate_patient(patient, obs)
        logger.info(f"  {patient.full_name}: risk={risk_eval.risk_band.value} score={risk_eval.risk_score}")

        ss.generate_schedule(patient)

        try:
            ration.generate_recommendation(patient, obs)
        except Exception as e:
            logger.warning(f"  Ration generation skipped for {patient.full_name}: {e}")


def populate_all():
    """Full population pipeline."""
    db = get_db()

    existing = db.count("patients")
    if existing > 0:
        logger.warning(f"Database already has {existing} patients. Skipping population.")
        logger.warning("Delete data/demo.db to start fresh.")
        return

    logger.info("=== Populating production database ===")

    populate_facilities()
    populate_asha_workers()
    populate_patients()
    populate_observations()
    populate_medical_thresholds()

    logger.info("Ingesting reference guidelines into RAG index...")
    ingest_reference_files()

    logger.info("Running risk/schedule/ration engines...")
    run_engines()

    final_count = db.count("patients")
    logger.info(f"=== Population complete: {final_count} patients ===")


if __name__ == "__main__":
    populate_all()
