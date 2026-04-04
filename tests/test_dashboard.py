"""Tests for the dashboard service."""

import pytest
from datetime import date
from services.dashboard_service import DashboardService
from services.patient_service import PatientService


class TestDashboard:
    def test_empty_village_dashboard(self):
        ds = DashboardService()
        data = ds.get_village_dashboard("EmptyVillage")
        assert data["village"] == "EmptyVillage"
        assert data["summary"]["total_active_patients"] == 0

    def test_dashboard_with_patients(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)

        ds = DashboardService()
        data = ds.get_village_dashboard("TestVillage")
        assert data["summary"]["total_active_patients"] >= 1

    def test_dashboard_structure(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)

        ds = DashboardService()
        data = ds.get_village_dashboard("TestVillage")

        assert "summary" in data
        assert "todays_visits" in data
        assert "overdue_visits" in data
        assert "high_risk_patients" in data
        assert "active_alerts" in data
        assert "upcoming_deliveries" in data
        assert "ration_summary" in data

    def test_create_snapshot(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)

        ds = DashboardService()
        ds.create_snapshot("TestVillage", "daily")

        from services.db import get_db
        db = get_db()
        count = db.count("dashboard_snapshots", "village = ?", ("TestVillage",))
        assert count >= 1

    def test_risk_distribution(self, sample_patient):
        ps = PatientService()
        ps.create_patient(sample_patient)

        ds = DashboardService()
        data = ds.get_village_dashboard("TestVillage")
        risk_dist = data["summary"]["risk_distribution"]
        assert isinstance(risk_dist, dict)
