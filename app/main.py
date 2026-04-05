"""ASHA Sahayak — Main Application (Databricks App entrypoint).

Serves the React frontend (from app/static/) and the FastAPI REST API.
Falls back to the Gradio UI if the React build is not present.
"""

import sys
import os
import logging
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("asha_sahayak")

STATIC_DIR = Path(__file__).parent / "static"
USE_REACT = STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists()


def ensure_data():
    """Seed the database if empty."""
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


def build_fastapi_app():
    """Build the FastAPI app that serves both the API and the React frontend."""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    from app.api import api as api_router

    app = FastAPI(title="ASHA Sahayak", version="2.0.0")
    app.mount("/api", api_router)

    if USE_REACT:
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = STATIC_DIR / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(STATIC_DIR / "index.html"))

    return app


def build_gradio_app():
    """Fallback: build the legacy Gradio UI."""
    import gradio as gr
    from app.components.common import CUSTOM_CSS
    from app.pages.home import build_home_page
    from app.pages.patients import build_patients_page
    from app.pages.patient_detail import build_patient_detail_page
    from app.pages.assistant import build_assistant_page
    from app.pages.dashboard import build_dashboard_page

    with gr.Blocks(
        title="ASHA Sahayak (आशा सहायक)",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="emerald",
            secondary_hue="blue",
            font=gr.themes.GoogleFont("Inter"),
        ),
    ) as gradio_app:
        gr.Markdown(
            "# 🏥 ASHA Sahayak (आशा सहायक)\n"
            "### AI-Powered Maternal Health Assistant for ASHA Workers",
        )
        with gr.Tabs():
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
            "*ASHA Sahayak is an assistive tool. Always consult medical professionals "
            "for clinical decisions. Built for BharatBricks Hackathon with Databricks.*"
        )

    return gradio_app


# Seed data at import time so it's ready before any request
ensure_data()

if USE_REACT:
    logger.info("React frontend found in app/static/ — serving FastAPI + React SPA")
    app = build_fastapi_app()
else:
    logger.info("No React build found — falling back to Gradio UI")
    app = build_gradio_app()


if __name__ == "__main__":
    if USE_REACT:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    else:
        app.launch(
            server_name="0.0.0.0",
            server_port=8080,
            show_error=True,
            quiet=False,
            prevent_thread_lock=False,
            share=True,
        )
