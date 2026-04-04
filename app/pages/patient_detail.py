"""Patient detail page: profile, timeline, reports, risk, schedule, ration."""

import json
import gradio as gr
from datetime import date

from app.components.common import risk_badge, RISK_EMOJI


def build_patient_detail_page():
    gr.Markdown("## Patient Detail")

    with gr.Row():
        patient_selector = gr.Dropdown(
            choices=_get_patient_choices(),
            label="Select Patient",
            interactive=True,
        )
        load_btn = gr.Button("📋 Load", variant="primary")

    profile_html = gr.HTML()
    risk_html = gr.HTML()
    schedule_html = gr.HTML()
    ration_html = gr.HTML()

    gr.Markdown("### Upload Report (PDF / Image)")
    with gr.Row():
        file_upload = gr.File(label="Upload EHR / Report", file_types=[".pdf", ".jpg", ".jpeg", ".png"])
        upload_btn = gr.Button("📤 Process Report", variant="secondary")
    upload_result = gr.HTML()

    def load_patient(selected):
        if not selected:
            return ("Select a patient", "", "", "")
        pid = selected.split(" | ")[0] if " | " in selected else selected
        return (
            _get_profile_html(pid),
            _get_risk_html(pid),
            _get_schedule_html(pid),
            _get_ration_html(pid),
        )

    load_btn.click(load_patient, inputs=[patient_selector],
                   outputs=[profile_html, risk_html, schedule_html, ration_html])

    def process_report(selected, file):
        if not selected or not file:
            return '<div style="color:red;">Select a patient and upload a file</div>'
        pid = selected.split(" | ")[0] if " | " in selected else selected

        with open(file.name, "rb") as f:
            file_bytes = f.read()
        file_type = "image/jpeg" if file.name.lower().endswith((".jpg", ".jpeg", ".png")) else "application/pdf"

        from services.document_service import DocumentService
        doc_svc = DocumentService()
        result = doc_svc.process_upload(pid, file_bytes, file_type, file.name.split("/")[-1])

        flags_html = ""
        for flag in result.get("abnormality_flags", []):
            color = "#ef4444" if "CRITICAL" in flag else "#eab308"
            flags_html += f'<div style="color:{color};font-weight:bold;">⚠️ {flag}</div>'

        extraction = result.get("extraction", {})
        findings = extraction.get("findings", {}) if isinstance(extraction, dict) else {}
        findings_html = ""
        for k, v in findings.items():
            findings_html += f"<tr><td style='padding:4px 8px;'>{k}</td><td style='padding:4px 8px;'><strong>{v}</strong></td></tr>"

        return f"""
        <div style="background:#f0fdf4;border:1px solid #22c55e;border-radius:12px;padding:16px;margin-top:12px;">
          <h3>Report Processed (Confidence: {result.get('confidence', 0):.0%})</h3>
          {flags_html}
          <table style="width:100%;margin-top:8px;">{findings_html}</table>
          <p style="font-size:0.85em;color:#6b7280;margin-top:8px;">Report ID: {result.get('report_id', '')}</p>
        </div>
        """

    upload_btn.click(process_report, inputs=[patient_selector, file_upload], outputs=[upload_result])


def _get_patient_choices():
    from services.patient_service import PatientService
    ps = PatientService()
    patients = ps.list_patients()
    return [f"{p.patient_id} | {p.full_name} ({RISK_EMOJI.get(p.risk_band, '')})" for p in patients]


def _get_profile_html(patient_id: str) -> str:
    from services.patient_service import PatientService
    ps = PatientService()
    patient = ps.get_patient(patient_id)
    if not patient:
        return '<div style="color:red;">Patient not found</div>'

    conditions = ", ".join(patient.known_conditions) if patient.known_conditions else "None"
    meds = ", ".join(patient.current_medications) if patient.current_medications else "None"

    return f"""
    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">
      <h3>{patient.full_name} {risk_badge(patient.risk_band)}</h3>
      <table style="width:100%;">
        <tr><td style="padding:4px;">Age</td><td><strong>{patient.age}</strong></td>
            <td>Village</td><td><strong>{patient.village}</strong></td></tr>
        <tr><td>Phone</td><td><strong>{patient.phone or '—'}</strong></td>
            <td>Blood Group</td><td><strong>{patient.blood_group or '—'}</strong></td></tr>
        <tr><td>LMP</td><td><strong>{patient.lmp_date}</strong></td>
            <td>EDD</td><td><strong>{patient.edd_date}</strong></td></tr>
        <tr><td>Weeks</td><td><strong>{patient.gestational_weeks}</strong></td>
            <td>Trimester</td><td><strong>{patient.trimester}</strong></td></tr>
        <tr><td>Gravida</td><td><strong>{patient.gravida}</strong></td>
            <td>Parity</td><td><strong>{patient.parity}</strong></td></tr>
      </table>
      <div style="margin-top:8px;">
        <strong>Conditions:</strong> {conditions}<br/>
        <strong>Medications:</strong> {meds}
      </div>
    </div>
    """


def _get_risk_html(patient_id: str) -> str:
    from services.patient_service import PatientService
    from services.risk_service import RiskService

    ps = PatientService()
    rs = RiskService()
    patient = ps.get_patient(patient_id)
    if not patient:
        return ""

    obs = rs.get_latest_observation(patient_id)
    evaluation = rs.evaluate_patient(patient, obs)

    html = f"""
    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">
      <h3>Risk Assessment {risk_badge(evaluation.risk_band.value)}</h3>
      <p>Score: {evaluation.risk_score:.0f}/100</p>
    """

    if evaluation.triggered_rules:
        html += '<div style="margin-top:8px;"><strong>Triggered Rules:</strong></div>'
        for rule in evaluation.triggered_rules:
            severity = rule["severity"]
            color = "#ef4444" if severity == "EMERGENCY" else "#f97316" if severity == "HIGH_RISK" else "#eab308"
            html += f"""
            <div style="border-left:3px solid {color};padding:6px 10px;margin:4px 0;background:#fafafa;border-radius:4px;">
              <strong>{rule['name']}</strong> ({severity})<br/>
              <span style="font-size:0.9em;">{rule.get('details', '')}</span><br/>
              <span style="font-size:0.85em;color:#6b7280;">Action: {rule['action']}</span><br/>
              <span style="font-size:0.8em;color:#9ca3af;">Source: {rule.get('source_ref', '')}</span>
            </div>
            """
    else:
        html += '<p style="color:#22c55e;">No risk flags detected. Continue routine care.</p>'

    if evaluation.emergency_flag:
        html += f"""
        <div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:12px;margin-top:8px;">
          <strong style="color:#ef4444;">EMERGENCY ACTION REQUIRED</strong><br/>
          {evaluation.suggested_next_action}
        </div>
        """

    html += "</div>"
    return html


def _get_schedule_html(patient_id: str) -> str:
    from services.schedule_service import ScheduleService
    ss = ScheduleService()
    schedule = ss.get_patient_schedule(patient_id)

    if not schedule:
        return '<div style="padding:12px;color:#6b7280;">No schedule generated yet</div>'

    html = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;"><h3>ANC Schedule</h3>'
    for entry in schedule[:8]:
        status = entry.status
        if hasattr(status, "value"):
            status = status.value
        if status == "completed":
            icon, bg = "✅", "#f0fdf4"
        elif status == "overdue":
            icon, bg = "⏰", "#fef2f2"
        else:
            icon, bg = "📅", "#f8fafc"

        pmsma = " 🏥 PMSMA" if entry.is_pmsma_aligned else ""
        esc = " 🔴" if entry.escalation_flag else ""
        tests = ", ".join(entry.tests_due[:3]) + ("..." if len(entry.tests_due) > 3 else "")

        html += f"""
        <div style="background:{bg};border-radius:8px;padding:8px;margin:4px 0;border:1px solid #e2e8f0;">
          {icon} <strong>{entry.visit_type}</strong>{pmsma}{esc}<br/>
          <span style="font-size:0.9em;">Due: {entry.due_date} | Status: {status}</span><br/>
          <span style="font-size:0.85em;color:#6b7280;">Tests: {tests}</span>
        </div>
        """
    html += "</div>"
    return html


def _get_ration_html(patient_id: str) -> str:
    from services.patient_service import PatientService
    from services.ration_service import RationService
    from services.risk_service import RiskService

    ps = PatientService()
    rs = RationService()
    risk_svc = RiskService()

    patient = ps.get_patient(patient_id)
    if not patient:
        return ""

    obs = risk_svc.get_latest_observation(patient_id)
    rec = rs.generate_recommendation(patient, obs)

    html = f"""
    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">
      <h3>Ration Recommendation</h3>
      <p>Week: {rec.week_start} | Target: {rec.calorie_target} cal, {rec.protein_target_g}g protein</p>
      <table style="width:100%;border-collapse:collapse;">
        <tr style="background:#f1f5f9;">
          <th style="padding:6px;text-align:left;">Item</th>
          <th style="padding:6px;">Quantity</th>
          <th style="padding:6px;">Frequency</th>
        </tr>
    """
    for item in rec.ration_items:
        html += f"""
        <tr style="border-bottom:1px solid #e2e8f0;">
          <td style="padding:6px;">{item.item_name}</td>
          <td style="padding:6px;text-align:center;">{item.quantity} {item.unit}</td>
          <td style="padding:6px;text-align:center;">{item.frequency}</td>
        </tr>
        """

    html += "</table>"

    if rec.supplements:
        html += '<div style="margin-top:8px;"><strong>Supplements:</strong></div><ul>'
        for s in rec.supplements:
            html += f"<li>{s}</li>"
        html += "</ul>"

    if rec.special_adjustments:
        html += '<div style="margin-top:8px;"><strong>Special Adjustments:</strong></div><ul>'
        for a in rec.special_adjustments:
            html += f"<li>{a}</li>"
        html += "</ul>"

    if rec.rule_basis:
        html += '<div style="margin-top:8px;font-size:0.85em;color:#6b7280;"><strong>Rule Basis:</strong> '
        html += " | ".join(rec.rule_basis) + "</div>"

    html += "</div>"
    return html
