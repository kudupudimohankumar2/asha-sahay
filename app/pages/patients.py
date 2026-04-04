"""Patients page: list, search, register."""

import gradio as gr
from datetime import date

from app.components.common import risk_badge, RISK_EMOJI, LANGUAGES


def build_patients_page():
    gr.Markdown("## Patient Management")

    with gr.Row():
        search_input = gr.Textbox(label="Search patients", placeholder="Name, village, phone...")
        search_btn = gr.Button("🔍 Search", variant="secondary")

    patients_html = gr.HTML(value=_get_patients_list_html())

    search_btn.click(_search_patients, inputs=[search_input], outputs=[patients_html])
    search_input.submit(_search_patients, inputs=[search_input], outputs=[patients_html])

    gr.Markdown("---\n### Register New Patient")

    with gr.Column():
        name_input = gr.Textbox(label="Full Name *", placeholder="e.g., Lakshmi Devi")

        with gr.Row():
            age_input = gr.Number(label="Age *", value=25, minimum=14, maximum=50)
            village_input = gr.Textbox(label="Village *", value="Hosahalli")

        with gr.Row():
            phone_input = gr.Textbox(label="Phone", placeholder="98XXXXXXXX")
            lang_input = gr.Dropdown(
                choices=[l[1] for l in LANGUAGES],
                value="हिन्दी (Hindi)",
                label="Language",
            )

        lmp_input = gr.Textbox(label="Last Menstrual Period (YYYY-MM-DD) *", placeholder="2026-01-15")

        with gr.Row():
            gravida_input = gr.Number(label="Gravida", value=1, minimum=1)
            parity_input = gr.Number(label="Parity", value=0, minimum=0)

        blood_group_input = gr.Dropdown(
            choices=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"],
            value="Unknown",
            label="Blood Group",
        )
        conditions_input = gr.Textbox(label="Known Conditions (comma-separated)", placeholder="e.g., anemia, previous c-section")
        medications_input = gr.Textbox(label="Current Medications (comma-separated)", placeholder="e.g., IFA tablet, calcium")

        register_btn = gr.Button("✅ Register Patient", variant="primary", size="lg")
        register_result = gr.HTML()

    def register_patient(name, age, village, phone, lang, lmp, gravida, parity, blood, conditions, meds):
        if not name or not village or not lmp:
            return '<div style="color:red;">Please fill required fields (Name, Village, LMP)</div>'

        try:
            lmp_date = date.fromisoformat(lmp.strip())
        except ValueError:
            return '<div style="color:red;">Invalid date format. Use YYYY-MM-DD</div>'

        lang_code_map = {l[1]: l[0] for l in LANGUAGES}
        lang_code = lang_code_map.get(lang, "hi")

        from models.patient import Patient
        from services.patient_service import PatientService

        patient = Patient(
            full_name=name.strip(),
            age=int(age),
            village=village.strip(),
            phone=phone.strip(),
            language_preference=lang_code,
            lmp_date=lmp_date,
            gravida=int(gravida),
            parity=int(parity),
            blood_group=blood,
            known_conditions=[c.strip() for c in conditions.split(",") if c.strip()],
            current_medications=[m.strip() for m in meds.split(",") if m.strip()],
        )

        ps = PatientService()
        patient = ps.create_patient(patient)

        from services.schedule_service import ScheduleService
        ss = ScheduleService()
        ss.generate_schedule(patient)

        from services.risk_service import RiskService
        rs = RiskService()
        rs.evaluate_patient(patient)

        return f"""
        <div style="background:#f0fdf4;border:1px solid #22c55e;border-radius:12px;padding:16px;margin-top:12px;">
          <h3 style="color:#22c55e;">Patient Registered Successfully!</h3>
          <p><strong>{patient.full_name}</strong> | Age: {patient.age} | Village: {patient.village}</p>
          <p>EDD: {patient.edd_date} | Trimester: {patient.trimester} | Week: {patient.gestational_weeks}</p>
          <p>Risk Band: {risk_badge(patient.risk_band)}</p>
          <p style="font-size:0.85em;">ID: {patient.patient_id}</p>
        </div>
        """

    register_btn.click(
        register_patient,
        inputs=[name_input, age_input, village_input, phone_input, lang_input,
                lmp_input, gravida_input, parity_input, blood_group_input,
                conditions_input, medications_input],
        outputs=[register_result],
    )


def _get_patients_list_html(query: str = "") -> str:
    from services.patient_service import PatientService
    ps = PatientService()

    if query:
        patients = ps.search_patients(query)
    else:
        patients = ps.list_patients()

    if not patients:
        return '<div style="padding:16px;text-align:center;color:#6b7280;">No patients found</div>'

    html = f'<div style="margin:8px 0;color:#6b7280;">{len(patients)} patients</div>'
    for p in patients:
        emoji = RISK_EMOJI.get(p.risk_band, "⚪")
        weeks = f"{p.gestational_weeks}w" if p.gestational_weeks else "—"
        tri = p.trimester or "—"
        edd = str(p.edd_date) if p.edd_date else "—"

        html += f"""
        <div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;margin:8px 0;
                     border-left:4px solid {'#ef4444' if p.risk_band in ('HIGH_RISK','EMERGENCY') else '#22c55e'};">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong style="font-size:1.1em;">{p.full_name}</strong>
            {risk_badge(p.risk_band)}
          </div>
          <div style="color:#6b7280;font-size:0.9em;margin-top:4px;">
            Age: {p.age} | {tri} trimester ({weeks}) | EDD: {edd}
          </div>
          <div style="color:#6b7280;font-size:0.85em;">
            Village: {p.village} | ID: {p.patient_id[:8]}...
          </div>
        </div>
        """
    return html


def _search_patients(query: str) -> str:
    return _get_patients_list_html(query)
