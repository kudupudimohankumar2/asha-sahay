"""Village dashboard page: daily/weekly planning view."""

import json
import gradio as gr
from datetime import date

from app.components.common import risk_badge, RISK_EMOJI


def build_dashboard_page():
    gr.Markdown("## Village Dashboard")

    with gr.Row():
        village_input = gr.Textbox(label="Village", value="Hosahalli")
        load_btn = gr.Button("📊 Load Dashboard", variant="primary")

    summary_html = gr.HTML()
    risk_queue_html = gr.HTML()
    visits_html = gr.HTML()
    ration_html = gr.HTML()
    deliveries_html = gr.HTML()

    def load_dashboard(village):
        from services.dashboard_service import DashboardService
        ds = DashboardService()
        data = ds.get_village_dashboard(village.strip())
        return (
            _render_summary(data),
            _render_risk_queue(data),
            _render_visits(data),
            _render_ration(data),
            _render_deliveries(data),
        )

    load_btn.click(
        load_dashboard,
        inputs=[village_input],
        outputs=[summary_html, risk_queue_html, visits_html, ration_html, deliveries_html],
    )


def _render_summary(data: dict) -> str:
    s = data.get("summary", {})
    total = s.get("total_active_patients", 0)
    tri = s.get("trimester_distribution", {})
    risk = s.get("risk_distribution", {})

    html = f"""
    <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">
      <h3>Village Summary — {data.get('village', '')} ({data.get('date', '')})</h3>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0;">
        <div style="background:#f0fdf4;border-radius:8px;padding:12px;text-align:center;">
          <div style="font-size:1.5em;font-weight:bold;">{total}</div><div>Total</div>
        </div>
        <div style="background:#fef2f2;border-radius:8px;padding:12px;text-align:center;">
          <div style="font-size:1.5em;font-weight:bold;color:#ef4444;">{s.get('emergency_count', 0)}</div><div>Emergency</div>
        </div>
        <div style="background:#fff7ed;border-radius:8px;padding:12px;text-align:center;">
          <div style="font-size:1.5em;font-weight:bold;color:#f97316;">{s.get('high_risk_count', 0)}</div><div>High Risk</div>
        </div>
        <div style="background:#fffbeb;border-radius:8px;padding:12px;text-align:center;">
          <div style="font-size:1.5em;font-weight:bold;color:#eab308;">{s.get('elevated_count', 0)}</div><div>Elevated</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
        <div style="background:#f8fafc;border-radius:8px;padding:10px;text-align:center;">
          <strong>{tri.get('1st', 0)}</strong><br/>1st Trimester
        </div>
        <div style="background:#f8fafc;border-radius:8px;padding:10px;text-align:center;">
          <strong>{tri.get('2nd', 0)}</strong><br/>2nd Trimester
        </div>
        <div style="background:#f8fafc;border-radius:8px;padding:10px;text-align:center;">
          <strong>{tri.get('3rd', 0)}</strong><br/>3rd Trimester
        </div>
      </div>
    </div>
    """
    return html


def _render_risk_queue(data: dict) -> str:
    patients = data.get("high_risk_patients", [])
    alerts = data.get("active_alerts", [])

    html = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;"><h3>🚨 High-Risk Queue</h3>'

    if not patients:
        html += '<p style="color:#22c55e;">No high-risk patients currently. Great!</p>'
    else:
        for p in patients:
            risk = p.get("risk_band", "NORMAL")
            conditions = p.get("known_conditions", "[]")
            if isinstance(conditions, str):
                try:
                    conditions = json.loads(conditions)
                except json.JSONDecodeError:
                    conditions = []
            cond_str = ", ".join(conditions) if conditions else "None"

            html += f"""
            <div style="border-left:4px solid {'#ef4444' if risk == 'EMERGENCY' else '#f97316'};
                         background:#fafafa;border-radius:8px;padding:10px;margin:6px 0;">
              <strong>{p.get('full_name', '')}</strong> {risk_badge(risk)}<br/>
              <span style="font-size:0.9em;">Age: {p.get('age', '')} | Week {p.get('gestational_weeks', '?')} |
              EDD: {p.get('edd_date', '—')}</span><br/>
              <span style="font-size:0.85em;color:#6b7280;">Conditions: {cond_str}</span>
            </div>
            """

    if alerts:
        html += f'<h4 style="margin-top:12px;">Active Alerts ({len(alerts)})</h4>'
        for a in alerts[:5]:
            severity = a.get("severity", "WARNING")
            html += f"""
            <div style="background:#fef2f2;border-radius:6px;padding:6px;margin:4px 0;font-size:0.9em;">
              <strong>{a.get('full_name', '')}</strong> — {severity}<br/>
              {a.get('message', '')[:80]}
            </div>
            """

    html += "</div>"
    return html


def _render_visits(data: dict) -> str:
    today = data.get("todays_visits", [])
    overdue = data.get("overdue_visits", [])

    html = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">'
    html += f"<h3>📅 Today's Schedule ({len(today)} visits)</h3>"

    if not today:
        html += '<p style="color:#6b7280;">No visits scheduled for today</p>'
    else:
        for v in today:
            html += f"""
            <div style="background:#f8fafc;border-radius:6px;padding:8px;margin:4px 0;border:1px solid #e2e8f0;">
              <strong>{v.get('full_name', '')}</strong> — {v.get('visit_type', '')}<br/>
              <span style="font-size:0.85em;">Risk: {v.get('risk_band', '')} | {v.get('trimester', '')}</span>
            </div>
            """

    if overdue:
        html += f'<h4 style="color:#ef4444;margin-top:12px;">Overdue ({len(overdue)})</h4>'
        for v in overdue[:5]:
            html += f"""
            <div style="background:#fef2f2;border-radius:6px;padding:6px;margin:4px 0;font-size:0.9em;">
              <strong>{v.get('full_name', '')}</strong> — {v.get('visit_type', '')} (Due: {v.get('due_date', '')})
            </div>
            """

    html += "</div>"
    return html


def _render_ration(data: dict) -> str:
    ration = data.get("ration_summary", {})
    html = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">'
    html += "<h3>🍚 Ration & Supplements Summary</h3>"

    total = ration.get("total_beneficiaries", 0)
    html += f"<p>Total beneficiaries: <strong>{total}</strong></p>"

    supplements = ration.get("supplements", {})
    if supplements:
        html += "<table style='width:100%;border-collapse:collapse;'>"
        html += '<tr style="background:#f1f5f9;"><th style="padding:6px;">Supplement</th><th style="padding:6px;">Count</th></tr>'
        for name, count in supplements.items():
            html += f'<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:6px;">{name}</td><td style="padding:6px;text-align:center;">{count}</td></tr>'
        html += "</table>"

    html += "</div>"
    return html


def _render_deliveries(data: dict) -> str:
    deliveries = data.get("upcoming_deliveries", [])
    html = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:8px 0;">'
    html += f"<h3>🤰 Upcoming Deliveries (Next 30 Days) — {len(deliveries)}</h3>"

    if not deliveries:
        html += '<p style="color:#6b7280;">No deliveries expected in next 30 days</p>'
    else:
        for d in deliveries:
            risk = d.get("risk_band", "NORMAL")
            html += f"""
            <div style="background:#f8fafc;border-radius:6px;padding:8px;margin:4px 0;">
              <strong>{d.get('full_name', '')}</strong> {risk_badge(risk)}<br/>
              <span style="font-size:0.9em;">EDD: {d.get('edd_date', '—')} | Week: {d.get('gestational_weeks', '?')}</span>
            </div>
            """

    html += "</div>"
    return html
