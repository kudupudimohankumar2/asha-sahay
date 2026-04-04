"""Shared test fixtures."""

import sys
import os
import pytest
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ["DEMO_MODE"] = "true"
os.environ["REASONING_PROVIDER"] = "mock"
os.environ["TRANSLATION_PROVIDER"] = "mock"
os.environ["SPEECH_PROVIDER"] = "mock"
os.environ["VISION_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """Use a fresh SQLite DB for each test."""
    import services.db as db_mod
    db_mod._connection = None
    db_mod._DEMO_DB_PATH = tmp_path / "test.db"
    yield
    db_mod._connection = None


@pytest.fixture
def sample_patient():
    from models.patient import Patient
    from services.patient_service import PatientService
    p = Patient(
        patient_id="test-patient-001",
        full_name="Test Patient",
        age=25,
        village="TestVillage",
        phone="9999999999",
        language_preference="hi",
        lmp_date=date(2026, 1, 1),
        gravida=1,
        parity=0,
        blood_group="B+",
        height_cm=155,
    )
    PatientService().create_patient(p)
    return p


@pytest.fixture
def normal_observation():
    from models.clinical import Observation
    return Observation(
        patient_id="test-patient-001",
        obs_date=date(2026, 3, 15),
        hemoglobin=12.0,
        systolic_bp=118,
        diastolic_bp=76,
        blood_sugar_fasting=85,
        weight_kg=58,
        urine_protein="nil",
        fetal_movement="normal",
        fetal_heart_rate=142,
    )


@pytest.fixture
def anemic_observation():
    from models.clinical import Observation
    return Observation(
        patient_id="test-patient-001",
        obs_date=date(2026, 3, 15),
        hemoglobin=8.5,
        systolic_bp=110,
        diastolic_bp=72,
        blood_sugar_fasting=88,
        weight_kg=52,
    )


@pytest.fixture
def emergency_observation():
    from models.clinical import Observation
    return Observation(
        patient_id="test-patient-001",
        obs_date=date(2026, 3, 15),
        hemoglobin=6.5,
        systolic_bp=165,
        diastolic_bp=115,
        blood_sugar_fasting=105,
        weight_kg=72,
        urine_protein="++",
        edema="present",
    )
