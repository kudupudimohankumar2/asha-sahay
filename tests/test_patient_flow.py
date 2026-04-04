"""Tests for the patient registration and management flow."""

import pytest
from datetime import date
from models.patient import Patient
from models.common import RiskBand, Trimester
from services.patient_service import PatientService


class TestPatientFlow:
    def test_create_patient(self, sample_patient):
        assert sample_patient.patient_id is not None
        assert sample_patient.gestational_weeks is not None
        assert sample_patient.trimester is not None
        assert sample_patient.edd_date is not None

    def test_get_patient(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)
        retrieved = ps.get_patient(sample_patient.patient_id)
        assert retrieved is not None
        assert retrieved.full_name == sample_patient.full_name

    def test_list_patients(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)
        patients = ps.list_patients()
        assert len(patients) >= 1

    def test_update_patient(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)
        updated = ps.update_patient(sample_patient.patient_id, {"phone": "8888888888"})
        assert updated is not None
        assert updated.phone == "8888888888"

    def test_auto_compute_gestational_fields(self):
        p = Patient(
            full_name="Auto Compute",
            age=25,
            village="V",
            lmp_date=date(2026, 1, 1),
        )
        assert p.gestational_weeks is not None
        assert p.trimester is not None
        assert p.edd_date is not None

    def test_search_patients(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)
        results = ps.search_patients("Test")
        assert len(results) >= 1

    def test_count_by_risk(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)
        counts = ps.count_by_risk()
        assert isinstance(counts, dict)

    def test_update_risk(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)
        ps.update_risk(sample_patient.patient_id, RiskBand.HIGH_RISK, 75.0)
        updated = ps.get_patient(sample_patient.patient_id)
        assert updated.risk_band in ("HIGH_RISK", RiskBand.HIGH_RISK)
