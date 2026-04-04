"""Tests for the ration recommendation engine."""

import pytest
from datetime import date
from models.patient import Patient
from models.clinical import Observation
from models.common import Trimester
from services.ration_service import RationService


class TestRationEngine:
    def test_generates_recommendation(self, sample_patient):
        svc = RationService()
        rec = svc.generate_recommendation(sample_patient)
        assert rec.patient_id == sample_patient.patient_id
        assert rec.calorie_target > 0
        assert rec.protein_target_g > 0
        assert len(rec.ration_items) > 0

    def test_trimester_calorie_progression(self):
        from services.patient_service import PatientService
        ps = PatientService()
        svc = RationService()

        p1 = Patient(full_name="P1", age=25, village="V", lmp_date=date(2026, 3, 1))
        p2 = Patient(full_name="P2", age=25, village="V", lmp_date=date(2025, 12, 1))
        p3 = Patient(full_name="P3", age=25, village="V", lmp_date=date(2025, 9, 1))
        ps.create_patient(p1)
        ps.create_patient(p2)
        ps.create_patient(p3)

        r1 = svc.generate_recommendation(p1)
        r2 = svc.generate_recommendation(p2)
        r3 = svc.generate_recommendation(p3)

        assert r1.calorie_target <= r2.calorie_target <= r3.calorie_target

    def test_anemia_adjustment(self, sample_patient):
        svc = RationService()
        obs = Observation(patient_id=sample_patient.patient_id, hemoglobin=8.0)
        rec = svc.generate_recommendation(sample_patient, obs)
        assert any("IFA" in s and "2" in s for s in rec.supplements)
        assert any("anemia" in a.lower() for a in rec.special_adjustments)

    def test_gdm_adjustment(self, sample_patient):
        svc = RationService()
        obs = Observation(patient_id=sample_patient.patient_id, blood_sugar_fasting=135)
        rec = svc.generate_recommendation(sample_patient, obs)
        assert any("gdm" in a.lower() or "glucose" in a.lower() or "glycemic" in a.lower()
                    for a in rec.special_adjustments)

    def test_supplements_included(self, sample_patient):
        svc = RationService()
        rec = svc.generate_recommendation(sample_patient)
        assert len(rec.supplements) > 0
        assert any("IFA" in s for s in rec.supplements)

    def test_rule_basis_documented(self, sample_patient):
        svc = RationService()
        rec = svc.generate_recommendation(sample_patient)
        assert len(rec.rule_basis) > 0

    def test_rationale_generated(self, sample_patient):
        svc = RationService()
        rec = svc.generate_recommendation(sample_patient)
        assert len(rec.rationale) > 50
        assert sample_patient.full_name in rec.rationale

    def test_ration_items_have_categories(self, sample_patient):
        svc = RationService()
        rec = svc.generate_recommendation(sample_patient)
        for item in rec.ration_items:
            assert item.category != ""
            assert item.item_name != ""
            assert item.frequency != ""

    def test_village_aggregation(self, sample_patient):
        from services.patient_service import PatientService
        ps = PatientService()
        ps.create_patient(sample_patient)

        svc = RationService()
        summary = svc.aggregate_village_rations("TestVillage")
        assert summary.total_beneficiaries >= 1
        assert summary.village == "TestVillage"
