"""Pipeline: daily refresh — risk recomputation, schedule updates, dashboard snapshot."""

import logging
from datetime import date

from services.risk_service import RiskService
from services.schedule_service import ScheduleService
from services.dashboard_service import DashboardService
from services.patient_service import PatientService
from services.db import get_db

logger = logging.getLogger(__name__)


def run_daily_refresh():
    """Daily batch job: re-evaluate risks, update overdue schedules, snapshot dashboards."""
    logger.info("=== Starting daily refresh ===")

    logger.info("Step 1: Re-evaluating patient risks...")
    risk_svc = RiskService()
    evaluations = risk_svc.evaluate_all_patients()
    emergency_count = sum(1 for e in evaluations if e.emergency_flag)
    logger.info(f"Risk evaluation complete. {len(evaluations)} patients, {emergency_count} emergencies")

    logger.info("Step 2: Updating overdue schedules...")
    db = get_db()
    today = date.today().isoformat()
    db.execute(
        "UPDATE schedules SET status = 'overdue' WHERE due_date < ? AND status = 'scheduled'",
        (today,),
    )
    db.conn.commit()
    logger.info("Overdue schedules updated")

    logger.info("Step 3: Creating dashboard snapshots...")
    ps = PatientService()
    dash_svc = DashboardService()
    villages = set()
    for p in ps.list_patients():
        villages.add(p.village)
    for village in villages:
        dash_svc.create_snapshot(village, "daily")
    logger.info(f"Dashboard snapshots created for {len(villages)} villages")

    logger.info("=== Daily refresh complete ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_daily_refresh()
