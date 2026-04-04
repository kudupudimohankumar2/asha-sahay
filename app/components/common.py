"""Shared UI components and styling."""

RISK_COLORS = {
    "NORMAL": "#22c55e",
    "ELEVATED": "#eab308",
    "HIGH_RISK": "#f97316",
    "EMERGENCY": "#ef4444",
}

RISK_LABELS = {
    "NORMAL": "Normal",
    "ELEVATED": "Elevated",
    "HIGH_RISK": "High Risk",
    "EMERGENCY": "Emergency",
}

RISK_EMOJI = {
    "NORMAL": "🟢",
    "ELEVATED": "🟡",
    "HIGH_RISK": "🟠",
    "EMERGENCY": "🔴",
}

LANGUAGES = [
    ("hi", "हिन्दी (Hindi)"),
    ("en", "English"),
    ("kn", "ಕನ್ನಡ (Kannada)"),
    ("te", "తెలుగు (Telugu)"),
    ("ta", "தமிழ் (Tamil)"),
    ("mr", "मराठी (Marathi)"),
    ("bn", "বাংলা (Bengali)"),
    ("gu", "ગુજરાતી (Gujarati)"),
    ("ml", "മലയാളം (Malayalam)"),
    ("pa", "ਪੰਜਾਬੀ (Punjabi)"),
]


def risk_badge(risk_band: str) -> str:
    color = RISK_COLORS.get(risk_band, "#6b7280")
    emoji = RISK_EMOJI.get(risk_band, "⚪")
    label = RISK_LABELS.get(risk_band, risk_band)
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:0.85em;">{emoji} {label}</span>'


def format_weeks(weeks):
    if weeks is None:
        return "—"
    return f"{weeks}w"


def format_date(d):
    if d is None:
        return "—"
    return str(d)


CUSTOM_CSS = """
.gradio-container { max-width: 480px !important; margin: 0 auto; }
.risk-normal { color: #22c55e; font-weight: bold; }
.risk-elevated { color: #eab308; font-weight: bold; }
.risk-high { color: #f97316; font-weight: bold; }
.risk-emergency { color: #ef4444; font-weight: bold; }
button { min-height: 48px !important; font-size: 16px !important; }
.patient-card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; margin: 8px 0; }
.alert-card { background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 8px; margin: 4px 0; }
.stat-card { background: #f8fafc; border-radius: 12px; padding: 16px; text-align: center; }
"""
