"""Hybrid risk assessment engine: deterministic rules + ML-compatible scoring."""

import json
import logging
from datetime import date, datetime
from typing import List, Optional, Tuple

from models.common import new_id, RiskBand
from models.risk import RiskRule, RiskEvaluation, AlertRecord
from models.patient import Patient
from models.clinical import Observation
from services.db import get_db

logger = logging.getLogger(__name__)

RISK_RULES: List[RiskRule] = [
    RiskRule(
        rule_id="R001", name="Severe Anemia",
        category="lab", condition_description="Hemoglobin critically low",
        threshold_description="Hb < 7 g/dL",
        severity=RiskBand.EMERGENCY,
        action="Immediate referral for transfusion",
        source_ref="MCP Card 2018 / Safe Motherhood Booklet",
    ),
    RiskRule(
        rule_id="R002", name="Severe Hypertension / Pre-eclampsia",
        category="vitals", condition_description="Blood pressure dangerously elevated",
        threshold_description="BP > 160/110 mmHg",
        severity=RiskBand.EMERGENCY,
        action="Immediate referral to FRU",
        source_ref="MCP Card 2018 / Safe Motherhood Booklet",
    ),
    RiskRule(
        rule_id="R003", name="Vaginal Bleeding",
        category="symptom", condition_description="Bleeding during pregnancy",
        threshold_description="Reported by patient or in report",
        severity=RiskBand.EMERGENCY,
        action="Immediate transport to hospital",
        source_ref="MCP Card 2018 - Danger Signs",
    ),
    RiskRule(
        rule_id="R004", name="Convulsions / Seizures",
        category="symptom", condition_description="Convulsions or seizures reported",
        threshold_description="Reported by patient or in report",
        severity=RiskBand.EMERGENCY,
        action="Immediate referral - possible eclampsia",
        source_ref="MCP Card 2018 - Danger Signs",
    ),
    RiskRule(
        rule_id="R005", name="Reduced / Absent Fetal Movement",
        category="symptom", condition_description="Fetal movement reduced or absent",
        threshold_description="Reported by patient, especially in 3rd trimester",
        severity=RiskBand.EMERGENCY,
        action="Immediate referral for fetal assessment",
        source_ref="MCP Card 2018 - Danger Signs",
    ),
    RiskRule(
        rule_id="R006", name="Severe Headache with Visual Disturbance",
        category="symptom", condition_description="Headache with blurred vision",
        threshold_description="Reported combination of severe headache + visual changes",
        severity=RiskBand.EMERGENCY,
        action="Urgent referral - possible pre-eclampsia",
        source_ref="MCP Card 2018 - Danger Signs",
    ),
    RiskRule(
        rule_id="R007", name="Pregnancy-Induced Hypertension",
        category="vitals", condition_description="Elevated blood pressure",
        threshold_description="BP > 140/90 mmHg",
        severity=RiskBand.HIGH_RISK,
        action="Increase monitoring frequency, plan referral",
        source_ref="Safe Motherhood Booklet",
    ),
    RiskRule(
        rule_id="R008", name="Gestational Diabetes Risk",
        category="lab", condition_description="Elevated fasting blood sugar",
        threshold_description="Fasting glucose > 126 mg/dL",
        severity=RiskBand.HIGH_RISK,
        action="Diet management + clinician follow-up",
        source_ref="GDM Guidelines",
    ),
    RiskRule(
        rule_id="R009", name="Moderate Anemia",
        category="lab", condition_description="Hemoglobin below normal",
        threshold_description="Hb 7-10 g/dL",
        severity=RiskBand.ELEVATED,
        action="Increased IFA dosage, nutrition counseling, recheck in 2 weeks",
        source_ref="MCP Card 2018 / IFA Guidelines",
    ),
    RiskRule(
        rule_id="R010", name="Adolescent Pregnancy",
        category="demographic", condition_description="Pregnant woman under 18",
        threshold_description="Age < 18 years",
        severity=RiskBand.HIGH_RISK,
        action="Specialist follow-up, increased monitoring",
        source_ref="High-Risk Pregnancy Guidelines",
    ),
    RiskRule(
        rule_id="R011", name="Advanced Maternal Age",
        category="demographic", condition_description="Pregnant woman over 35",
        threshold_description="Age > 35 years",
        severity=RiskBand.HIGH_RISK,
        action="Increased monitoring, additional screening",
        source_ref="High-Risk Pregnancy Guidelines",
    ),
    RiskRule(
        rule_id="R012", name="Prior C-Section / Stillbirth",
        category="history", condition_description="History of C-section or stillbirth",
        threshold_description="Previous C-section or stillbirth in history",
        severity=RiskBand.HIGH_RISK,
        action="Hospital delivery planning, close monitoring",
        source_ref="MCP Card 2018 - Obstetric History",
    ),
    RiskRule(
        rule_id="R013", name="High Fever",
        category="symptom", condition_description="High fever during pregnancy",
        threshold_description="Temperature > 38.5°C or reported high fever",
        severity=RiskBand.HIGH_RISK,
        action="Refer to PHC for evaluation",
        source_ref="MCP Card 2018 - Danger Signs",
    ),
    RiskRule(
        rule_id="R014", name="Preterm Labour Signs",
        category="symptom", condition_description="Labour pains before 37 weeks",
        threshold_description="Contractions or water breaking before 37 weeks",
        severity=RiskBand.EMERGENCY,
        action="Immediate referral to FRU",
        source_ref="MCP Card 2018 - Danger Signs",
    ),
    RiskRule(
        rule_id="R015", name="Urine Protein Elevated",
        category="lab", condition_description="Protein detected in urine",
        threshold_description="Urine protein positive (not trace)",
        severity=RiskBand.ELEVATED,
        action="Monitor BP closely, repeat test, watch for pre-eclampsia signs",
        source_ref="ANC Guidelines",
    ),
    RiskRule(
        rule_id="R016", name="Excessive Edema",
        category="symptom", condition_description="Swelling all over body",
        threshold_description="Generalized edema reported",
        severity=RiskBand.HIGH_RISK,
        action="Check BP and urine protein, refer if accompanied by headache or visual changes",
        source_ref="MCP Card 2018",
    ),
]


class RiskService:
    def __init__(self):
        self.db = get_db()
        self.rules = RISK_RULES

    def evaluate_patient(
        self,
        patient: Patient,
        latest_obs: Optional[Observation] = None,
        reported_symptoms: Optional[List[str]] = None,
    ) -> RiskEvaluation:
        """Run all deterministic rules against patient state and observations."""
        triggered = []
        symptoms = [s.lower() for s in (reported_symptoms or [])]
        conditions = [c.lower() for c in (patient.known_conditions or [])]

        for rule in self.rules:
            hit, details = self._check_rule(rule, patient, latest_obs, symptoms, conditions)
            if hit:
                triggered.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "severity": rule.severity.value,
                    "action": rule.action,
                    "details": details,
                    "source_ref": rule.source_ref,
                })

        risk_band, risk_score = self._compute_band_and_score(triggered)
        emergency = risk_band == RiskBand.EMERGENCY
        reason_codes = [t["rule_id"] for t in triggered]

        if emergency:
            action = "IMMEDIATE REFERRAL: " + "; ".join(t["action"] for t in triggered if t["severity"] == "EMERGENCY")
            escalation = "Transport to nearest FRU/District Hospital immediately. Call ambulance."
        elif risk_band == RiskBand.HIGH_RISK:
            action = "URGENT: " + "; ".join(set(t["action"] for t in triggered[:3]))
            escalation = "Schedule specialist consultation within 48 hours"
        elif risk_band == RiskBand.ELEVATED:
            action = "; ".join(set(t["action"] for t in triggered[:3]))
            escalation = "Increase monitoring frequency"
        else:
            action = "Continue routine ANC schedule"
            escalation = ""

        evaluation = RiskEvaluation(
            patient_id=patient.patient_id,
            risk_band=risk_band,
            risk_score=risk_score,
            triggered_rules=triggered,
            reason_codes=reason_codes,
            suggested_next_action=action,
            emergency_flag=emergency,
            escalation_recommendation=escalation,
        )

        self._persist_risk(patient.patient_id, evaluation)
        return evaluation

    def _check_rule(
        self,
        rule: RiskRule,
        patient: Patient,
        obs: Optional[Observation],
        symptoms: List[str],
        conditions: List[str],
    ) -> Tuple[bool, str]:
        """Check a single rule. Returns (triggered, detail_string)."""

        if rule.rule_id == "R001" and obs and obs.hemoglobin is not None:
            if obs.hemoglobin < 7.0:
                return True, f"Hb={obs.hemoglobin} g/dL (critical <7)"

        if rule.rule_id == "R002" and obs:
            if obs.systolic_bp and obs.diastolic_bp:
                if obs.systolic_bp > 160 or obs.diastolic_bp > 110:
                    return True, f"BP={obs.systolic_bp}/{obs.diastolic_bp} mmHg (>160/110)"

        if rule.rule_id == "R003":
            bleeding_terms = ["bleeding", "blood", "खून", "रक्तस्राव", "vaginal bleeding"]
            if any(t in s for s in symptoms for t in bleeding_terms):
                return True, "Vaginal bleeding reported"

        if rule.rule_id == "R004":
            if any(t in s for s in symptoms for t in ["convulsion", "seizure", "fits", "दौरा"]):
                return True, "Convulsions/seizures reported"

        if rule.rule_id == "R005":
            fm_terms = ["reduced fetal", "no movement", "baby not moving", "बच्चा हिल नहीं", "absent"]
            if any(t in s for s in symptoms for t in fm_terms):
                return True, "Reduced/absent fetal movement"
            if obs and obs.fetal_movement and obs.fetal_movement.lower() in ("reduced", "absent"):
                return True, f"Fetal movement: {obs.fetal_movement}"

        if rule.rule_id == "R006":
            has_headache = any(t in s for s in symptoms for t in ["headache", "सिर दर्द"])
            has_vision = any(t in s for s in symptoms for t in ["blur", "vision", "आंख", "दिखाई"])
            if has_headache and has_vision:
                return True, "Severe headache with visual disturbance"

        if rule.rule_id == "R007" and obs:
            if obs.systolic_bp and obs.diastolic_bp:
                if obs.systolic_bp > 140 or obs.diastolic_bp > 90:
                    return True, f"BP={obs.systolic_bp}/{obs.diastolic_bp} mmHg (>140/90)"

        if rule.rule_id == "R008" and obs and obs.blood_sugar_fasting:
            if obs.blood_sugar_fasting > 126:
                return True, f"Fasting glucose={obs.blood_sugar_fasting} mg/dL (>126)"

        if rule.rule_id == "R009" and obs and obs.hemoglobin is not None:
            if 7.0 <= obs.hemoglobin < 10.0:
                return True, f"Hb={obs.hemoglobin} g/dL (moderate anemia 7-10)"

        if rule.rule_id == "R010" and patient.age < 18:
            return True, f"Age={patient.age} (<18, adolescent pregnancy)"

        if rule.rule_id == "R011" and patient.age > 35:
            return True, f"Age={patient.age} (>35, advanced maternal age)"

        if rule.rule_id == "R012":
            high_risk_history = ["c-section", "caesarean", "stillbirth", "lscs", "cesarean"]
            if any(h in c for c in conditions for h in high_risk_history):
                return True, "History: " + ", ".join(c for c in conditions if any(h in c for h in high_risk_history))

        if rule.rule_id == "R013":
            if any(t in s for s in symptoms for t in ["fever", "बुखार", "high temperature"]):
                return True, "High fever reported"

        if rule.rule_id == "R014":
            preterm_terms = ["preterm", "labour pain", "water breaking", "leaking", "premature"]
            weeks = patient.gestational_weeks or 40
            if weeks < 37 and any(t in s for s in symptoms for t in preterm_terms):
                return True, f"Preterm signs at {weeks} weeks"

        if rule.rule_id == "R015" and obs and obs.urine_protein:
            positive_vals = ["positive", "+", "++", "+++", "1+", "2+", "3+"]
            if obs.urine_protein.lower().strip() in positive_vals:
                return True, f"Urine protein: {obs.urine_protein}"

        if rule.rule_id == "R016":
            edema_terms = ["swelling", "edema", "oedema", "सूजन", "swelling all over"]
            if any(t in s for s in symptoms for t in edema_terms):
                return True, "Excessive edema reported"
            if obs and obs.edema and obs.edema.lower() in ("yes", "present", "++", "+++"):
                return True, f"Edema: {obs.edema}"

        return False, ""

    def _compute_band_and_score(self, triggered: List[dict]) -> Tuple[RiskBand, float]:
        if not triggered:
            return RiskBand.NORMAL, 0.0

        severity_weights = {"EMERGENCY": 100, "HIGH_RISK": 60, "ELEVATED": 30, "NORMAL": 0}
        max_severity = max(triggered, key=lambda t: severity_weights.get(t["severity"], 0))

        score = min(100.0, sum(severity_weights.get(t["severity"], 0) for t in triggered))
        band = RiskBand(max_severity["severity"])

        return band, score

    def _persist_risk(self, patient_id: str, evaluation: RiskEvaluation):
        from services.db import get_db
        db = get_db()

        db.update("patients", "patient_id", patient_id, {
            "risk_band": evaluation.risk_band.value,
            "risk_score": evaluation.risk_score,
            "updated_at": datetime.utcnow().isoformat(),
        })

        if evaluation.emergency_flag or evaluation.risk_band in (RiskBand.HIGH_RISK, RiskBand.EMERGENCY):
            alert_data = {
                "alert_id": new_id(),
                "patient_id": patient_id,
                "severity": evaluation.risk_band.value,
                "alert_type": "risk_evaluation",
                "reason_codes": json.dumps(evaluation.reason_codes),
                "message": evaluation.suggested_next_action,
                "created_at": datetime.utcnow().isoformat(),
                "active": 1,
            }
            db.insert("alerts", alert_data)

    def get_latest_observation(self, patient_id: str) -> Optional[Observation]:
        row = self.db.fetch_one(
            "SELECT * FROM observations WHERE patient_id = ? ORDER BY obs_date DESC LIMIT 1",
            (patient_id,),
        )
        if not row:
            return None
        return Observation(**{k: v for k, v in row.items() if k in Observation.model_fields})

    def evaluate_all_patients(self) -> List[RiskEvaluation]:
        """Batch re-evaluate all active patients."""
        from services.patient_service import PatientService
        ps = PatientService()
        patients = ps.list_patients()
        results = []
        for summary in patients:
            patient = ps.get_patient(summary.patient_id)
            if patient:
                obs = self.get_latest_observation(patient.patient_id)
                result = self.evaluate_patient(patient, obs)
                results.append(result)
        return results
