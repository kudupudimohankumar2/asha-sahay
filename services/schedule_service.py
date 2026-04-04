"""ANC scheduling engine aligned with MCP Card and PMSMA guidelines."""

import json
import logging
from datetime import date, timedelta
from typing import List, Optional

from models.common import new_id, VisitStatus, RiskBand
from models.patient import Patient
from models.schedule import ScheduleEntry, DailyTaskList
from services.db import get_db

logger = logging.getLogger(__name__)

ANC_SCHEDULE = [
    {"visit": 1, "week_start": 0,  "week_end": 12, "type": "ANC-1 (Registration)",
     "tests": ["Registration", "Blood group & Rh", "Hemoglobin", "Urine albumin & sugar",
                "HIV screening", "Syphilis (VDRL)", "Blood pressure", "Weight", "TT-1"]},
    {"visit": 2, "week_start": 14, "week_end": 20, "type": "ANC-2",
     "tests": ["Hemoglobin", "Blood pressure", "Weight", "Urine albumin & sugar",
                "TT-2", "Ultrasonography", "Fetal heart rate"]},
    {"visit": 3, "week_start": 24, "week_end": 28, "type": "ANC-3",
     "tests": ["Hemoglobin", "Blood pressure", "Weight", "Urine albumin & sugar",
                "GDM screening", "Fetal heart rate", "Abdominal examination"]},
    {"visit": 4, "week_start": 30, "week_end": 34, "type": "ANC-4",
     "tests": ["Hemoglobin", "Blood pressure", "Weight", "Urine albumin & sugar",
                "Fetal heart rate", "Fetal position", "Abdominal examination"]},
    {"visit": 5, "week_start": 34, "week_end": 36, "type": "ANC-5",
     "tests": ["Blood pressure", "Weight", "Fetal heart rate", "Fetal position",
                "Birth preparedness review"]},
    {"visit": 6, "week_start": 36, "week_end": 38, "type": "ANC-6",
     "tests": ["Blood pressure", "Weight", "Fetal heart rate", "Fetal position",
                "Delivery plan review"]},
    {"visit": 7, "week_start": 38, "week_end": 40, "type": "ANC-7",
     "tests": ["Blood pressure", "Weight", "Fetal heart rate", "Fetal position",
                "Signs of labour education"]},
]


class ScheduleService:
    def __init__(self):
        self.db = get_db()

    def generate_schedule(self, patient: Patient) -> List[ScheduleEntry]:
        """Generate full ANC schedule for a patient based on LMP."""
        if not patient.lmp_date:
            return []

        entries = []
        current_weeks = patient.gestational_weeks or 0

        for anc in ANC_SCHEDULE:
            target_week = (anc["week_start"] + anc["week_end"]) // 2
            due_date = patient.lmp_date + timedelta(weeks=target_week)

            is_pmsma = self._check_pmsma_alignment(due_date)

            status = VisitStatus.SCHEDULED
            if due_date < date.today():
                completed = self._is_visit_completed(patient.patient_id, anc["visit"])
                status = VisitStatus.COMPLETED if completed else VisitStatus.OVERDUE

            escalation = False
            if patient.risk_band in (RiskBand.HIGH_RISK, RiskBand.EMERGENCY):
                escalation = True

            facility = self._suggest_facility(patient, anc["visit"])

            entry = ScheduleEntry(
                patient_id=patient.patient_id,
                visit_type=anc["type"],
                visit_number=anc["visit"],
                due_date=due_date,
                tests_due=anc["tests"],
                status=status,
                is_pmsma_aligned=is_pmsma,
                escalation_flag=escalation,
                facility_name=facility,
                suggested_slot="09:00-11:00" if is_pmsma else "10:00-12:00",
            )
            entries.append(entry)

        if patient.risk_band in (RiskBand.HIGH_RISK, RiskBand.EMERGENCY):
            entries = self._add_extra_visits(patient, entries)

        self._persist_schedule(entries)
        return entries

    def get_patient_schedule(self, patient_id: str) -> List[ScheduleEntry]:
        rows = self.db.fetch_all(
            "SELECT * FROM schedules WHERE patient_id = ? ORDER BY due_date",
            (patient_id,),
        )
        return [self._row_to_entry(r) for r in rows]

    def get_due_today(self, village: Optional[str] = None) -> List[ScheduleEntry]:
        today = date.today().isoformat()
        if village:
            rows = self.db.fetch_all("""
                SELECT s.* FROM schedules s
                JOIN patients p ON s.patient_id = p.patient_id
                WHERE s.due_date = ? AND s.status = 'scheduled' AND p.village = ?
                ORDER BY s.escalation_flag DESC
            """, (today, village))
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM schedules WHERE due_date = ? AND status = 'scheduled'",
                (today,),
            )
        return [self._row_to_entry(r) for r in rows]

    def get_overdue(self, village: Optional[str] = None) -> List[ScheduleEntry]:
        today = date.today().isoformat()
        if village:
            rows = self.db.fetch_all("""
                SELECT s.* FROM schedules s
                JOIN patients p ON s.patient_id = p.patient_id
                WHERE s.due_date < ? AND s.status IN ('scheduled', 'overdue') AND p.village = ?
                ORDER BY s.due_date
            """, (today, village))
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM schedules WHERE due_date < ? AND status IN ('scheduled', 'overdue') ORDER BY due_date",
                (today,),
            )
        return [self._row_to_entry(r) for r in rows]

    def mark_completed(self, schedule_id: str):
        self.db.update("schedules", "schedule_id", schedule_id, {
            "status": VisitStatus.COMPLETED.value,
        })

    def get_daily_task_list(self, village: str, target_date: Optional[date] = None) -> DailyTaskList:
        target = target_date or date.today()
        today_str = target.isoformat()

        due_rows = self.db.fetch_all("""
            SELECT s.* FROM schedules s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE s.due_date = ? AND p.village = ? AND s.status = 'scheduled'
        """, (today_str, village))

        overdue_rows = self.db.fetch_all("""
            SELECT s.* FROM schedules s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE s.due_date < ? AND p.village = ? AND s.status IN ('scheduled', 'overdue')
        """, (today_str, village))

        high_priority_rows = self.db.fetch_all("""
            SELECT s.* FROM schedules s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE p.village = ? AND s.status = 'scheduled'
              AND (s.escalation_flag = 1 OR p.risk_band IN ('HIGH_RISK', 'EMERGENCY'))
              AND s.due_date <= ?
        """, (village, today_str))

        total = self.db.count("patients", "village = ?", (village,))

        return DailyTaskList(
            date=target,
            village=village,
            visits_due=[self._row_to_entry(r) for r in due_rows],
            high_priority=[self._row_to_entry(r) for r in high_priority_rows],
            overdue=[self._row_to_entry(r) for r in overdue_rows],
            total_patients=total,
        )

    def get_next_pmsma_date(self, from_date: Optional[date] = None) -> date:
        ref = from_date or date.today()
        if ref.day <= 9:
            return ref.replace(day=9)
        if ref.month == 12:
            return date(ref.year + 1, 1, 9)
        return date(ref.year, ref.month + 1, 9)

    def _check_pmsma_alignment(self, visit_date: date) -> bool:
        """PMSMA clinics happen on the 9th of every month."""
        return visit_date.day == 9

    def _is_visit_completed(self, patient_id: str, visit_number: int) -> bool:
        row = self.db.fetch_one(
            "SELECT COUNT(*) as cnt FROM schedules WHERE patient_id = ? AND visit_number = ? AND status = 'completed'",
            (patient_id, visit_number),
        )
        return row and row["cnt"] > 0

    def _suggest_facility(self, patient: Patient, visit_number: int) -> str:
        if patient.risk_band in (RiskBand.HIGH_RISK, RiskBand.EMERGENCY):
            return "District Hospital / FRU"
        if visit_number == 1:
            return "Sub-centre / PHC"
        return "PHC / Gram Panchayat Health Centre"

    def _add_extra_visits(
        self, patient: Patient, entries: List[ScheduleEntry]
    ) -> List[ScheduleEntry]:
        """High-risk patients get biweekly visits in 3rd trimester."""
        if not patient.lmp_date:
            return entries

        existing_dates = {e.due_date for e in entries}
        week_28 = patient.lmp_date + timedelta(weeks=28)
        week_40 = patient.lmp_date + timedelta(weeks=40)

        current = week_28
        extra_num = 100
        while current <= week_40:
            if current not in existing_dates and current >= date.today():
                entries.append(ScheduleEntry(
                    patient_id=patient.patient_id,
                    visit_type="High-Risk Monitoring",
                    visit_number=extra_num,
                    due_date=current,
                    tests_due=["Blood pressure", "Weight", "Fetal heart rate"],
                    status=VisitStatus.SCHEDULED,
                    escalation_flag=True,
                    facility_name="District Hospital / FRU",
                    suggested_slot="09:00-11:00",
                ))
                extra_num += 1
            current += timedelta(days=14)

        entries.sort(key=lambda e: e.due_date)
        return entries

    def _persist_schedule(self, entries: List[ScheduleEntry]):
        for entry in entries:
            self.db.insert("schedules", {
                "schedule_id": entry.schedule_id,
                "patient_id": entry.patient_id,
                "visit_type": entry.visit_type,
                "visit_number": entry.visit_number,
                "due_date": entry.due_date.isoformat(),
                "suggested_slot": entry.suggested_slot,
                "facility_name": entry.facility_name,
                "tests_due": json.dumps(entry.tests_due),
                "status": entry.status.value,
                "is_pmsma_aligned": 1 if entry.is_pmsma_aligned else 0,
                "escalation_flag": 1 if entry.escalation_flag else 0,
                "notes": entry.notes,
            })

    def _row_to_entry(self, row: dict) -> ScheduleEntry:
        tests = row.get("tests_due", "[]")
        if isinstance(tests, str):
            try:
                tests = json.loads(tests)
            except json.JSONDecodeError:
                tests = []
        return ScheduleEntry(
            schedule_id=row["schedule_id"],
            patient_id=row["patient_id"],
            visit_type=row.get("visit_type", ""),
            visit_number=row.get("visit_number"),
            due_date=date.fromisoformat(row["due_date"]) if row.get("due_date") else date.today(),
            suggested_slot=row.get("suggested_slot", ""),
            facility_name=row.get("facility_name", ""),
            tests_due=tests,
            status=row.get("status", "scheduled"),
            is_pmsma_aligned=bool(row.get("is_pmsma_aligned", 0)),
            escalation_flag=bool(row.get("escalation_flag", 0)),
            notes=row.get("notes", ""),
        )
