"""Pipeline: weekly village summary — ration aggregation and planning."""

import logging
from services.patient_service import PatientService
from services.ration_service import RationService
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


def run_weekly_summary():
    """Weekly batch job: aggregate rations, create weekly planning summary."""
    logger.info("=== Starting weekly summary ===")

    ps = PatientService()
    ration_svc = RationService()
    dash_svc = DashboardService()

    villages = set()
    for p in ps.list_patients():
        villages.add(p.village)

    for village in villages:
        logger.info(f"Processing village: {village}")
        summary = ration_svc.aggregate_village_rations(village)
        logger.info(
            f"  {village}: {summary.total_beneficiaries} beneficiaries, "
            f"{summary.high_priority_count} high-priority"
        )
        dash_svc.create_snapshot(village, "weekly")

    logger.info(f"=== Weekly summary complete for {len(villages)} villages ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_weekly_summary()
