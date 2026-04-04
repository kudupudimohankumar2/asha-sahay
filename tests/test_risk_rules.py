"""Tests for the risk assessment engine."""

import pytest
from datetime import date
from models.patient import Patient
from models.clinical import Observation
from models.common import RiskBand
from services.risk_service import RiskService


class TestRiskRules:
    def test_normal_patient_no_risks(self, sample_patient, normal_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, normal_observation)
        assert result.risk_band == RiskBand.NORMAL
        assert result.emergency_flag is False
        assert len(result.triggered_rules) == 0

    def test_severe_anemia_triggers_emergency(self, sample_patient):
        svc = RiskService()
        obs = Observation(patient_id=sample_patient.patient_id, hemoglobin=6.5)
        result = svc.evaluate_patient(sample_patient, obs)
        assert result.risk_band == RiskBand.EMERGENCY
        assert result.emergency_flag is True
        assert any(r["rule_id"] == "R001" for r in result.triggered_rules)

    def test_moderate_anemia_triggers_elevated(self, sample_patient):
        svc = RiskService()
        obs = Observation(patient_id=sample_patient.patient_id, hemoglobin=8.5)
        result = svc.evaluate_patient(sample_patient, obs)
        assert result.risk_band == RiskBand.ELEVATED
        assert any(r["rule_id"] == "R009" for r in result.triggered_rules)

    def test_severe_hypertension_emergency(self, sample_patient):
        svc = RiskService()
        obs = Observation(patient_id=sample_patient.patient_id, systolic_bp=165, diastolic_bp=115)
        result = svc.evaluate_patient(sample_patient, obs)
        assert result.risk_band == RiskBand.EMERGENCY
        assert any(r["rule_id"] == "R002" for r in result.triggered_rules)

    def test_mild_hypertension_high_risk(self, sample_patient):
        svc = RiskService()
        obs = Observation(patient_id=sample_patient.patient_id, systolic_bp=145, diastolic_bp=95)
        result = svc.evaluate_patient(sample_patient, obs)
        assert any(r["rule_id"] == "R007" for r in result.triggered_rules)
        assert result.risk_band in (RiskBand.HIGH_RISK, RiskBand.EMERGENCY)

    def test_vaginal_bleeding_emergency(self, sample_patient, normal_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, normal_observation, ["vaginal bleeding"])
        assert result.emergency_flag is True
        assert any(r["rule_id"] == "R003" for r in result.triggered_rules)

    def test_convulsions_emergency(self, sample_patient, normal_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, normal_observation, ["convulsion"])
        assert result.emergency_flag is True
        assert any(r["rule_id"] == "R004" for r in result.triggered_rules)

    def test_reduced_fetal_movement(self, sample_patient, normal_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, normal_observation, ["baby not moving"])
        assert result.emergency_flag is True
        assert any(r["rule_id"] == "R005" for r in result.triggered_rules)

    def test_headache_with_vision_emergency(self, sample_patient, normal_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, normal_observation, ["severe headache", "blurred vision"])
        assert any(r["rule_id"] == "R006" for r in result.triggered_rules)

    def test_adolescent_pregnancy(self):
        from services.patient_service import PatientService
        svc = RiskService()
        teen = Patient(full_name="Teen", age=16, village="V", lmp_date=date(2026, 1, 1))
        PatientService().create_patient(teen)
        result = svc.evaluate_patient(teen)
        assert any(r["rule_id"] == "R010" for r in result.triggered_rules)

    def test_advanced_maternal_age(self):
        from services.patient_service import PatientService
        svc = RiskService()
        older = Patient(full_name="Older", age=38, village="V", lmp_date=date(2026, 1, 1))
        PatientService().create_patient(older)
        result = svc.evaluate_patient(older)
        assert any(r["rule_id"] == "R011" for r in result.triggered_rules)

    def test_prior_csection_history(self, sample_patient):
        sample_patient.known_conditions = ["previous c-section"]
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient)
        assert any(r["rule_id"] == "R012" for r in result.triggered_rules)

    def test_gdm_risk(self, sample_patient):
        svc = RiskService()
        obs = Observation(patient_id=sample_patient.patient_id, blood_sugar_fasting=135)
        result = svc.evaluate_patient(sample_patient, obs)
        assert any(r["rule_id"] == "R008" for r in result.triggered_rules)

    def test_multiple_triggers_highest_wins(self, sample_patient, emergency_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, emergency_observation)
        assert result.risk_band == RiskBand.EMERGENCY
        assert len(result.triggered_rules) >= 2

    def test_risk_output_structure(self, sample_patient, normal_observation):
        svc = RiskService()
        result = svc.evaluate_patient(sample_patient, normal_observation)
        assert hasattr(result, "risk_band")
        assert hasattr(result, "risk_score")
        assert hasattr(result, "triggered_rules")
        assert hasattr(result, "reason_codes")
        assert hasattr(result, "suggested_next_action")
        assert hasattr(result, "emergency_flag")
        assert hasattr(result, "escalation_recommendation")
