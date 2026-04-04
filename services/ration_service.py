"""Scheme-aligned ration and nutrition recommendation engine."""

import json
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from models.common import new_id, Trimester
from models.patient import Patient
from models.clinical import Observation
from models.ration import (
    RationRecommendation, RationItem, VillageRationSummary, NutritionRule,
)
from services.db import get_db

logger = logging.getLogger(__name__)

BASELINE_RULES: Dict[str, dict] = {
    "1st": {
        "calories": 2200, "protein_g": 55,
        "iron_mg": 27, "calcium_mg": 1000, "folic_acid_mg": 0.5,
        "supplements": ["IFA 1 tablet daily", "Folic acid 5mg daily"],
        "ration_items": [
            ("Rice/Wheat", "500g", "g", "daily", "cereals", "Staple energy source"),
            ("Dal/Pulses", "100g", "g", "daily", "protein", "Plant protein and iron"),
            ("Green leafy vegetables", "100g", "g", "daily", "vegetables", "Iron and folic acid"),
            ("Milk", "500ml", "ml", "daily", "dairy", "Calcium and protein"),
            ("Seasonal fruits", "1 serving", "serving", "daily", "fruits", "Vitamins and fiber"),
            ("Jaggery", "20g", "g", "daily", "iron_source", "Iron supplement via food"),
            ("Oil/Ghee", "30ml", "ml", "daily", "fats", "Essential fatty acids"),
            ("Eggs", "1", "piece", "daily", "protein", "Complete protein (if non-veg)"),
        ],
        "source": "MCP Card 2018 / POSHAN 2.0",
    },
    "2nd": {
        "calories": 2500, "protein_g": 65,
        "iron_mg": 27, "calcium_mg": 1200, "folic_acid_mg": 0.5,
        "supplements": ["IFA 1 tablet daily", "Calcium 2 tablets daily", "Albendazole single dose"],
        "ration_items": [
            ("Rice/Wheat", "600g", "g", "daily", "cereals", "Increased energy for fetal growth"),
            ("Dal/Pulses", "120g", "g", "daily", "protein", "Increased protein needs"),
            ("Green leafy vegetables", "150g", "g", "daily", "vegetables", "Iron and folic acid"),
            ("Milk/Curd", "600ml", "ml", "daily", "dairy", "Increased calcium needs"),
            ("Seasonal fruits", "2 servings", "serving", "daily", "fruits", "Vitamins and fiber"),
            ("Jaggery/Dates", "30g", "g", "daily", "iron_source", "Natural iron"),
            ("Oil/Ghee", "35ml", "ml", "daily", "fats", "Essential fatty acids"),
            ("Eggs", "1", "piece", "daily", "protein", "Complete protein"),
            ("Nuts/Dry fruits", "30g", "g", "daily", "micronutrients", "Additional calories and minerals"),
        ],
        "source": "MCP Card 2018 / POSHAN 2.0",
    },
    "3rd": {
        "calories": 2700, "protein_g": 75,
        "iron_mg": 27, "calcium_mg": 1200, "folic_acid_mg": 0.5,
        "supplements": ["IFA 1 tablet daily", "Calcium 2 tablets daily"],
        "ration_items": [
            ("Rice/Wheat", "650g", "g", "daily", "cereals", "Maximum energy for late pregnancy"),
            ("Dal/Pulses", "150g", "g", "daily", "protein", "High protein for fetal brain development"),
            ("Green leafy vegetables", "150g", "g", "daily", "vegetables", "Iron and folic acid"),
            ("Milk/Curd", "600ml", "ml", "daily", "dairy", "Calcium for bone development"),
            ("Seasonal fruits", "2 servings", "serving", "daily", "fruits", "Vitamins and fiber"),
            ("Jaggery/Dates", "30g", "g", "daily", "iron_source", "Natural iron"),
            ("Oil/Ghee", "40ml", "ml", "daily", "fats", "Calorie-dense nutrition"),
            ("Eggs", "1-2", "piece", "daily", "protein", "Complete protein and nutrients"),
            ("Nuts/Dry fruits", "45g", "g", "daily", "micronutrients", "Additional calories and minerals"),
            ("Supplementary nutrition (THR)", "1 packet", "packet", "daily", "supplement", "Anganwadi THR"),
        ],
        "source": "MCP Card 2018 / POSHAN 2.0 / Saksham",
    },
}

CONDITION_ADJUSTMENTS = {
    "anemia_moderate": {
        "supplement_add": ["IFA increased to 2 tablets daily (morning + evening)", "Vitamin C with iron tablet"],
        "food_add": [
            ("Beetroot", "50g", "g", "daily", "iron_source", "Rich in iron for anemia"),
            ("Amla/Lemon", "1", "piece", "daily", "vitamin_c", "Enhances iron absorption"),
        ],
        "food_avoid": ["Tea/coffee with meals (inhibits iron absorption)"],
        "rationale": "Moderate anemia (Hb 7-10): Increased iron intake per IFA guidelines",
    },
    "anemia_severe": {
        "supplement_add": ["Injectable iron as prescribed", "IFA 2 tablets daily", "Urgent referral if Hb < 5"],
        "food_add": [
            ("Liver/Meat (if non-veg)", "50g", "g", "3x/week", "iron_source", "Heme iron for severe anemia"),
        ],
        "food_avoid": ["Tea/coffee near meals"],
        "rationale": "Severe anemia (Hb < 7): Emergency iron supplementation per protocol",
    },
    "gdm_risk": {
        "supplement_add": ["Blood sugar monitoring", "Low GI diet plan"],
        "calorie_adjust": -300,
        "food_add": [
            ("Oats/Brown rice", "replace white rice", "", "daily", "low_gi", "Low glycemic index"),
            ("Extra vegetables", "100g", "g", "daily", "fiber", "Fiber for blood sugar control"),
        ],
        "food_avoid": ["Refined sugar", "White rice in excess", "Sweet fruits in large quantities", "Processed foods"],
        "rationale": "GDM risk: Low glycemic diet with increased fiber and protein",
    },
    "underweight": {
        "supplement_add": ["THR from Anganwadi", "Extra supplementary nutrition"],
        "calorie_adjust": 300,
        "food_add": [
            ("Extra ghee/oil", "15ml", "ml", "daily", "calorie_dense", "Additional calorie-dense food"),
            ("THR packet", "1 extra", "packet", "daily", "supplement", "Anganwadi supplementary nutrition"),
        ],
        "food_avoid": [],
        "rationale": "Underweight: Additional calorie-dense nutrition per POSHAN 2.0 / Saksham",
    },
    "hypertension": {
        "supplement_add": ["BP monitoring at home if possible"],
        "food_add": [],
        "food_avoid": ["Excessive salt", "Pickles", "Processed/packaged foods"],
        "rationale": "Hypertension: Reduced sodium intake, DASH-style dietary pattern",
    },
}


class RationService:
    def __init__(self):
        self.db = get_db()

    def generate_recommendation(
        self,
        patient: Patient,
        latest_obs: Optional[Observation] = None,
    ) -> RationRecommendation:
        """Generate a scheme-aligned weekly ration recommendation."""
        trimester_key = self._get_trimester_key(patient.trimester)
        baseline = BASELINE_RULES.get(trimester_key, BASELINE_RULES["2nd"])

        calories = baseline["calories"]
        protein = baseline["protein_g"]
        supplements = list(baseline["supplements"])
        ration_items = [
            RationItem(
                item_name=name, quantity=qty, unit=unit,
                frequency=freq, category=cat, rationale=rat,
            )
            for name, qty, unit, freq, cat, rat in baseline["ration_items"]
        ]
        special_adjustments = []
        rule_basis = [f"Baseline: {trimester_key} trimester ({baseline['source']})"]

        applicable_conditions = self._detect_conditions(patient, latest_obs)
        for condition in applicable_conditions:
            adj = CONDITION_ADJUSTMENTS.get(condition, {})
            if not adj:
                continue

            supplements.extend(adj.get("supplement_add", []))
            calories += adj.get("calorie_adjust", 0)
            special_adjustments.append(adj.get("rationale", condition))

            for item_tuple in adj.get("food_add", []):
                name, qty, unit, freq, cat, rat = item_tuple
                ration_items.append(RationItem(
                    item_name=name, quantity=qty, unit=unit,
                    frequency=freq, category=cat, rationale=rat,
                ))

            for avoid_item in adj.get("food_avoid", []):
                special_adjustments.append(f"Avoid: {avoid_item}")

            rule_basis.append(f"Condition adjustment: {condition}")

        week_start = self._current_week_start()
        rationale = self._build_rationale(patient, trimester_key, applicable_conditions, latest_obs)

        recommendation = RationRecommendation(
            patient_id=patient.patient_id,
            week_start=week_start.isoformat(),
            trimester=patient.trimester,
            calorie_target=calories,
            protein_target_g=protein,
            ration_items=ration_items,
            supplements=list(set(supplements)),
            special_adjustments=special_adjustments,
            rationale=rationale,
            rule_basis=rule_basis,
            source_refs=[baseline["source"]],
        )

        self._persist(recommendation)
        return recommendation

    def _detect_conditions(self, patient: Patient, obs: Optional[Observation]) -> List[str]:
        conditions = []
        known = [c.lower() for c in (patient.known_conditions or [])]

        if obs and obs.hemoglobin is not None:
            if obs.hemoglobin < 7.0:
                conditions.append("anemia_severe")
            elif obs.hemoglobin < 10.0:
                conditions.append("anemia_moderate")

        if obs and obs.blood_sugar_fasting and obs.blood_sugar_fasting > 126:
            conditions.append("gdm_risk")
        if any("diabetes" in c or "gdm" in c for c in known):
            conditions.append("gdm_risk")

        if obs and obs.systolic_bp and obs.systolic_bp > 140:
            conditions.append("hypertension")
        if any("hypertension" in c or "bp" in c for c in known):
            conditions.append("hypertension")

        if obs and obs.weight_kg and patient.height_cm:
            bmi = obs.weight_kg / ((patient.height_cm / 100) ** 2)
            if bmi < 18.5:
                conditions.append("underweight")

        return list(set(conditions))

    def _build_rationale(
        self, patient: Patient, trimester: str,
        conditions: List[str], obs: Optional[Observation],
    ) -> str:
        parts = [
            f"Ration recommendation for {patient.full_name} "
            f"({trimester} trimester, Week {patient.gestational_weeks or '?'}).",
            "",
            "Basis:",
            f"- Trimester-based baseline from POSHAN 2.0 / MCP Card guidelines",
        ]
        if obs and obs.hemoglobin is not None:
            parts.append(f"- Current Hb: {obs.hemoglobin} g/dL")
        if conditions:
            parts.append(f"- Condition adjustments applied: {', '.join(conditions)}")
        parts.extend([
            "",
            "This is a recommendation aligned with government nutrition schemes. "
            "Actual distribution should be coordinated with the Anganwadi Centre.",
            "",
            "Sources: MCP Card 2018, POSHAN 2.0, Saksham (ICDS), IFA Guidelines",
        ])
        return "\n".join(parts)

    def aggregate_village_rations(self, village: str) -> VillageRationSummary:
        """Aggregate weekly ration needs for a village."""
        from services.patient_service import PatientService
        ps = PatientService()
        patients = ps.get_village_patients(village)

        week_start = self._current_week_start()
        aggregated_items: Dict = {}
        total_supplements: Dict = {}
        high_priority = 0

        for patient in patients:
            obs_row = self.db.fetch_one(
                "SELECT * FROM observations WHERE patient_id = ? ORDER BY obs_date DESC LIMIT 1",
                (patient.patient_id,),
            )
            obs = None
            if obs_row:
                obs = Observation(**{k: v for k, v in obs_row.items() if k in Observation.model_fields})

            rec = self.generate_recommendation(patient, obs)

            for item in rec.ration_items:
                key = item.item_name
                if key not in aggregated_items:
                    aggregated_items[key] = {"quantity": 0, "unit": item.unit, "beneficiaries": 0}
                try:
                    qty = float(item.quantity.replace("g", "").replace("ml", "").strip().split("-")[0])
                    aggregated_items[key]["quantity"] += qty * 7
                except (ValueError, IndexError):
                    aggregated_items[key]["quantity"] += 7
                aggregated_items[key]["beneficiaries"] += 1

            for supp in rec.supplements:
                total_supplements[supp] = total_supplements.get(supp, 0) + 1

            if patient.risk_band in ("HIGH_RISK", "EMERGENCY"):
                high_priority += 1

        return VillageRationSummary(
            village=village,
            week_start=week_start.isoformat(),
            total_beneficiaries=len(patients),
            aggregated_items=aggregated_items,
            total_supplements=total_supplements,
            high_priority_count=high_priority,
        )

    def _persist(self, rec: RationRecommendation):
        self.db.insert("ration_plans", {
            "ration_id": rec.ration_id,
            "patient_id": rec.patient_id,
            "week_start": rec.week_start,
            "trimester": rec.trimester.value if rec.trimester and hasattr(rec.trimester, "value") else str(rec.trimester),
            "calorie_target": rec.calorie_target,
            "protein_target_g": rec.protein_target_g,
            "recommendation_json": json.dumps([item.model_dump() for item in rec.ration_items]),
            "supplements": json.dumps(rec.supplements),
            "special_adjustments": json.dumps(rec.special_adjustments),
            "rationale": rec.rationale,
            "rule_basis": json.dumps(rec.rule_basis),
            "approval_status": rec.approval_status,
            "distributed": 0,
        })

    @staticmethod
    def _get_trimester_key(trimester) -> str:
        if trimester is None:
            return "2nd"
        val = trimester.value if hasattr(trimester, "value") else str(trimester)
        return val.replace("st", "").replace("nd", "").replace("rd", "").strip() or "2nd"

    @staticmethod
    def _current_week_start() -> date:
        today = date.today()
        return today - timedelta(days=today.weekday())
