"""ASHA Sahayak — Main Gradio Application (Databricks App entrypoint)."""

import sys
import os
import logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env before anything else touches env vars
try:
    from dotenv import load_dotenv
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("asha_sahayak")

import gradio as gr
from app.components.common import CUSTOM_CSS, LANGUAGES
from app.pages.home import build_home_page
from app.pages.patients import build_patients_page
from app.pages.patient_detail import build_patient_detail_page
from app.pages.assistant import build_assistant_page
from app.pages.dashboard import build_dashboard_page


def ensure_data():
    """Seed the database if empty.

    Checks for synthetic data first (production-grade, from tools/).
    Falls back to demo seed data if synthetic data hasn't been generated.
    """
    from services.db import get_db
    db = get_db()
    count = db.count("patients")
    if count > 0:
        logger.info(f"Database has {count} patients, skipping seed.")
        return

    synthetic_dir = ROOT / "data" / "synthetic"
    has_synthetic = (synthetic_dir / "patients.json").exists()

    if has_synthetic:
        logger.info("Synthetic data found — populating from data/synthetic/...")
        from tools.populate_production_db import populate_all
        populate_all()
    else:
        logger.info("No synthetic data found — seeding demo data...")
        from pipelines.seed_demo_data import seed_all
        seed_all()
        _run_engines()

    logger.info("Data seeding complete.")


def _run_engines():
    """Run risk evaluation and schedule generation for all patients."""
    from services.risk_service import RiskService
    from services.patient_service import PatientService
    from services.schedule_service import ScheduleService

    rs = RiskService()
    ps = PatientService()
    ss = ScheduleService()

    for p in ps.list_patients():
        patient = ps.get_patient(p.patient_id)
        if patient:
            obs = rs.get_latest_observation(patient.patient_id)
            rs.evaluate_patient(patient, obs)
            ss.generate_schedule(patient)


def build_app() -> gr.Blocks:
    ensure_data()

    with gr.Blocks(
        title="ASHA Sahayak (आशा सहायक)",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="emerald",
            secondary_hue="blue",
            font=gr.themes.GoogleFont("Inter"),
        ),
    ) as app:
        gr.Markdown(
            "# 🏥 ASHA Sahayak (आशा सहायक)\n"
            "### AI-Powered Maternal Health Assistant for ASHA Workers",
        )

        with gr.Tabs() as tabs:
            with gr.Tab("🏠 Home", id="home"):
                build_home_page()

            with gr.Tab("👩 Patients", id="patients"):
                build_patients_page()

            with gr.Tab("📋 Patient Detail", id="detail"):
                build_patient_detail_page()

            with gr.Tab("🤖 AI Assistant", id="assistant"):
                build_assistant_page()

            with gr.Tab("📊 Dashboard", id="dashboard"):
                build_dashboard_page()

        gr.Markdown(
            "---\n"
            "*ASHA Sahayak is an assistive tool. Always consult medical professionals for clinical decisions. "
            "Built for BharatBricks Hackathon with Databricks.*"
        )

    return app


app = build_app()

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8080, share=False)
