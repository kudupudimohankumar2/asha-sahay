"""Pipeline: batch risk re-evaluation for all active patients."""

import logging
from services.risk_service import RiskService

logger = logging.getLogger(__name__)


def run_risk_refresh():
    """Re-evaluate all patients' risk bands."""
    logger.info("Starting risk refresh...")
    risk_svc = RiskService()
    results = risk_svc.evaluate_all_patients()

    stats = {}
    for r in results:
        band = r.risk_band.value
        stats[band] = stats.get(band, 0) + 1

    logger.info(f"Risk refresh complete. Distribution: {stats}")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_risk_refresh()
