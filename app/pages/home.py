"""Home page: today's summary, quick actions, alerts."""

import gradio as gr
from datetime import date

from app.components.common import risk_badge, RISK_EMOJI


def build_home_page():
    gr.Markdown("## Today's Overview")

    with gr.Row():
        refresh_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")

    summary_html = gr.HTML(value=_get_summary_html())
    alerts_html = gr.HTML(value=_get_alerts_html())
    today_visits_html = gr.HTML(value=_get_today_visits_html())

    def refresh():
        return _get_summary_html(), _get_alerts_html(), _get_today_visits_html()

    refresh_btn.click(refresh, outputs=[summary_html, alerts_html, today_visits_html])


def _get_summary_html() -> str:
    from services.patient_service import PatientService
    ps = PatientService()
    patients = ps.list_patients()
    risk_counts = ps.count_by_risk()
    total = len(patients)

    return f"""
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:12px 0;">
      <div style="background:#f0fdf4;border-radius:12px;padding:16px;text-align:center;">
        <div style="font-size:2em;font-weight:bold;">{total}</div>
        <div>Active Patients</div>
      </div>
      <div style="background:#fef2f2;border-radius:12px;padding:16px;text-align:center;">
        <div style="font-size:2em;font-weight:bold;color:#ef4444;">
          {risk_counts.get('EMERGENCY', 0) + risk_counts.get('HIGH_RISK', 0)}
        </div>
        <div>Need Attention</div>
      </div>
      <div style="background:#fffbeb;border-radius:12px;padding:16px;text-align:center;">
        <div style="font-size:2em;font-weight:bold;color:#eab308;">{risk_counts.get('ELEVATED', 0)}</div>
        <div>Elevated Risk</div>
      </div>
      <div style="background:#f0f9ff;border-radius:12px;padding:16px;text-align:center;">
        <div style="font-size:2em;font-weight:bold;color:#22c55e;">{risk_counts.get('NORMAL', 0)}</div>
        <div>Normal</div>
      </div>
    </div>
    <p style="text-align:center;color:#6b7280;font-size:0.85em;">
      {date.today().strftime('%A, %d %B %Y')}
    </p>
    """


def _get_alerts_html() -> str:
    from services.db import get_db
    db = get_db()
    alerts = db.fetch_all("""
        SELECT a.*, p.full_name FROM alerts a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.active = 1 ORDER BY a.created_at DESC LIMIT 5
    """)
    if not alerts:
        return '<div style="padding:12px;text-align:center;color:#6b7280;">No active alerts</div>'

    html = '<h3>⚠️ Active Alerts</h3>'
    for a in alerts:
        severity = a.get("severity", "WARNING")
        color = "#fef2f2" if severity in ("EMERGENCY", "CRITICAL") else "#fffbeb"
        border = "#ef4444" if severity in ("EMERGENCY", "CRITICAL") else "#eab308"
        html += f"""
        <div style="background:{color};border-left:4px solid {border};border-radius:8px;padding:10px;margin:6px 0;">
          <strong>{a.get('full_name', 'Unknown')}</strong> — {risk_badge(severity)}<br/>
          <span style="font-size:0.9em;">{a.get('message', '')[:100]}</span>
        </div>
        """
    return html


def _get_today_visits_html() -> str:
    from services.schedule_service import ScheduleService
    ss = ScheduleService()
    today_visits = ss.get_due_today()
    overdue = ss.get_overdue()

    html = '<h3>📅 Today\'s Visits</h3>'
    if not today_visits:
        html += '<div style="padding:8px;color:#6b7280;">No visits scheduled for today</div>'
    else:
        for v in today_visits[:5]:
            esc = "🔴 " if v.escalation_flag else ""
            pmsma = " 🏥 PMSMA" if v.is_pmsma_aligned else ""
            html += f"""
            <div style="background:#f8fafc;border-radius:8px;padding:8px;margin:4px 0;border:1px solid #e2e8f0;">
              {esc}<strong>{v.visit_type}</strong>{pmsma}<br/>
              <span style="font-size:0.9em;">Tests: {', '.join(v.tests_due[:3])}</span>
            </div>
            """

    if overdue:
        html += f'<h3 style="color:#ef4444;">⏰ Overdue Visits ({len(overdue)})</h3>'
        for v in overdue[:3]:
            html += f"""
            <div style="background:#fef2f2;border-radius:8px;padding:8px;margin:4px 0;border:1px solid #fca5a5;">
              <strong>{v.visit_type}</strong> — Due: {v.due_date}<br/>
            </div>
            """

    return html
