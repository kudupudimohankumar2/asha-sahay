"""Village dashboard aggregation service."""

import json
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from models.common import new_id, RiskBand
from services.db import get_db

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(self):
        self.db = get_db()

    def get_village_dashboard(self, village: str) -> Dict[str, Any]:
        """Generate complete dashboard payload for a village."""
        today = date.today()

        summary = self._get_village_summary(village)
        todays_visits = self._get_todays_visits(village, today)
        overdue = self._get_overdue_visits(village, today)
        high_risk = self._get_high_risk_patients(village)
        active_alerts = self._get_active_alerts(village)
        upcoming_deliveries = self._get_upcoming_deliveries(village, today)
        ration_summary = self._get_ration_summary(village)

        return {
            "village": village,
            "date": today.isoformat(),
            "summary": summary,
            "todays_visits": todays_visits,
            "overdue_visits": overdue,
            "high_risk_patients": high_risk,
            "active_alerts": active_alerts,
            "upcoming_deliveries": upcoming_deliveries,
            "ration_summary": ration_summary,
        }

    def _get_village_summary(self, village: str) -> Dict[str, Any]:
        total = self.db.count("patients", "village = ?", (village,))

        risk_rows = self.db.fetch_all(
            "SELECT risk_band, COUNT(*) as cnt FROM patients WHERE village = ? GROUP BY risk_band",
            (village,),
        )
        risk_dist = {r["risk_band"]: r["cnt"] for r in risk_rows}

        tri_rows = self.db.fetch_all(
            "SELECT trimester, COUNT(*) as cnt FROM patients WHERE village = ? GROUP BY trimester",
            (village,),
        )
        tri_dist = {r["trimester"]: r["cnt"] for r in tri_rows if r["trimester"]}

        return {
            "total_active_patients": total,
            "risk_distribution": risk_dist,
            "trimester_distribution": tri_dist,
            "normal_count": risk_dist.get("NORMAL", 0),
            "elevated_count": risk_dist.get("ELEVATED", 0),
            "high_risk_count": risk_dist.get("HIGH_RISK", 0),
            "emergency_count": risk_dist.get("EMERGENCY", 0),
        }

    def _get_todays_visits(self, village: str, today: date) -> List[Dict]:
        rows = self.db.fetch_all("""
            SELECT s.*, p.full_name, p.risk_band, p.trimester, p.gestational_weeks
            FROM schedules s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE p.village = ? AND s.due_date = ? AND s.status = 'scheduled'
            ORDER BY s.escalation_flag DESC
        """, (village, today.isoformat()))
        return rows

    def _get_overdue_visits(self, village: str, today: date) -> List[Dict]:
        rows = self.db.fetch_all("""
            SELECT s.*, p.full_name, p.risk_band, p.trimester
            FROM schedules s
            JOIN patients p ON s.patient_id = p.patient_id
            WHERE p.village = ? AND s.due_date < ? AND s.status IN ('scheduled', 'overdue')
            ORDER BY s.due_date
        """, (village, today.isoformat()))
        return rows

    def _get_high_risk_patients(self, village: str) -> List[Dict]:
        rows = self.db.fetch_all("""
            SELECT patient_id, full_name, age, trimester, gestational_weeks,
                   risk_band, risk_score, edd_date, known_conditions
            FROM patients
            WHERE village = ? AND risk_band IN ('HIGH_RISK', 'EMERGENCY')
            ORDER BY
              CASE WHEN risk_band = 'EMERGENCY' THEN 0 ELSE 1 END,
              risk_score DESC
        """, (village,))
        return rows

    def _get_active_alerts(self, village: str) -> List[Dict]:
        rows = self.db.fetch_all("""
            SELECT a.*, p.full_name
            FROM alerts a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE p.village = ? AND a.active = 1
            ORDER BY a.created_at DESC
        """, (village,))
        return rows

    def _get_upcoming_deliveries(self, village: str, today: date) -> List[Dict]:
        from datetime import timedelta
        thirty_days = (today + timedelta(days=30)).isoformat()
        rows = self.db.fetch_all("""
            SELECT patient_id, full_name, edd_date, risk_band, gestational_weeks
            FROM patients
            WHERE village = ? AND edd_date BETWEEN ? AND ?
            ORDER BY edd_date
        """, (village, today.isoformat(), thirty_days))
        return rows

    def _get_ration_summary(self, village: str) -> Dict[str, Any]:
        rows = self.db.fetch_all("""
            SELECT r.supplements, r.calorie_target, r.protein_target_g
            FROM ration_plans r
            JOIN patients p ON r.patient_id = p.patient_id
            WHERE p.village = ?
        """, (village,))

        if not rows:
            return {"total_beneficiaries": 0, "supplements": {}}

        supplement_counts: Dict[str, int] = {}
        for row in rows:
            supps = row.get("supplements", "[]")
            if isinstance(supps, str):
                try:
                    supps = json.loads(supps)
                except json.JSONDecodeError:
                    supps = []
            for s in supps:
                supplement_counts[s] = supplement_counts.get(s, 0) + 1

        return {
            "total_beneficiaries": len(rows),
            "supplements": supplement_counts,
            "avg_calorie_target": sum(r.get("calorie_target", 0) for r in rows) / max(len(rows), 1),
        }

    def create_snapshot(self, village: str, snapshot_type: str = "daily"):
        """Create a persisted dashboard snapshot for historical tracking."""
        data = self.get_village_dashboard(village)
        self.db.insert("dashboard_snapshots", {
            "snapshot_id": new_id(),
            "village": village,
            "snapshot_date": date.today().isoformat(),
            "snapshot_type": snapshot_type,
            "data_json": json.dumps(data, default=str),
        })
        logger.info(f"Created {snapshot_type} snapshot for {village}")
