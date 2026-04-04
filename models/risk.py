"""Risk assessment models."""

from typing import List, Optional
from pydantic import BaseModel

from .common import RiskBand


class RiskRule(BaseModel):
    rule_id: str
    name: str
    category: str
    condition_description: str
    threshold_description: str
    severity: RiskBand
    action: str
    source_ref: str = "MCP Card / Safe Motherhood Guidelines"


class RiskEvaluation(BaseModel):
    patient_id: str
    risk_band: RiskBand
    risk_score: float
    triggered_rules: List[dict]
    reason_codes: List[str]
    suggested_next_action: str
    emergency_flag: bool = False
    escalation_recommendation: str = ""
    confidence: float = 1.0

    @property
    def is_urgent(self) -> bool:
        return self.risk_band in (RiskBand.HIGH_RISK, RiskBand.EMERGENCY)


class AlertRecord(BaseModel):
    alert_id: str
    patient_id: str
    severity: str
    alert_type: str
    reason_codes: List[str]
    message: str
    created_at: str
    resolved_at: Optional[str] = None
    active: bool = True
