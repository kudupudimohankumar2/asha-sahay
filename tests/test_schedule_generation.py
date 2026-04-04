"""Tests for the ANC scheduling engine."""

import pytest
from datetime import date, timedelta
from models.patient import Patient
from models.common import RiskBand, VisitStatus
from services.schedule_service import ScheduleService


class TestScheduleGeneration:
    def test_generates_full_schedule(self, sample_patient):
        svc = ScheduleService()
        entries = svc.generate_schedule(sample_patient)
        assert len(entries) >= 7

    def test_no_schedule_without_lmp(self):
        svc = ScheduleService()
        patient = Patient(full_name="No LMP", age=25, village="V")
        entries = svc.generate_schedule(patient)
        assert len(entries) == 0

    def test_visit_types_correct(self, sample_patient):
        svc = ScheduleService()
        entries = svc.generate_schedule(sample_patient)
        types = [e.visit_type for e in entries if "ANC" in e.visit_type]
        assert len(types) >= 7

    def test_tests_due_populated(self, sample_patient):
        svc = ScheduleService()
        entries = svc.generate_schedule(sample_patient)
        for entry in entries:
            if "ANC" in entry.visit_type:
                assert len(entry.tests_due) > 0

    def test_pmsma_alignment_check(self, sample_patient):
        svc = ScheduleService()
        entries = svc.generate_schedule(sample_patient)
        pmsma_aligned = [e for e in entries if e.is_pmsma_aligned]
        # May or may not have PMSMA-aligned dates depending on LMP
        assert all(e.due_date.day == 9 for e in pmsma_aligned)

    def test_high_risk_gets_extra_visits(self):
        from services.patient_service import PatientService
        svc = ScheduleService()
        patient = Patient(
            full_name="High Risk", age=30, village="V",
            lmp_date=date(2025, 10, 1),
            risk_band=RiskBand.HIGH_RISK,
        )
        PatientService().create_patient(patient)
        entries = svc.generate_schedule(patient)
        monitoring = [e for e in entries if "Monitoring" in e.visit_type]
        assert len(monitoring) > 0

    def test_overdue_detection(self, sample_patient):
        svc = ScheduleService()
        sample_patient.lmp_date = date(2025, 6, 1)
        entries = svc.generate_schedule(sample_patient)
        overdue = [e for e in entries if e.status == VisitStatus.OVERDUE or str(e.status) == "overdue"]
        assert len(overdue) > 0

    def test_next_pmsma_date(self):
        svc = ScheduleService()
        ref = date(2026, 4, 1)
        pmsma = svc.get_next_pmsma_date(ref)
        assert pmsma.day == 9
        assert pmsma >= ref

    def test_daily_task_list(self, sample_patient):
        svc = ScheduleService()
        svc.generate_schedule(sample_patient)
        task_list = svc.get_daily_task_list("TestVillage")
        assert task_list.village == "TestVillage"

    def test_schedule_entry_has_facility(self, sample_patient):
        svc = ScheduleService()
        entries = svc.generate_schedule(sample_patient)
        for entry in entries:
            assert entry.facility_name != ""
