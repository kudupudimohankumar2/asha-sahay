"""Ration and nutrition recommendation models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .common import new_id, Trimester


class NutritionRule(BaseModel):
    rule_id: str
    trimester: Optional[Trimester] = None
    condition_tag: str = ""
    calorie_target: int = 0
    protein_target_g: int = 0
    iron_mg: float = 0.0
    calcium_mg: float = 0.0
    folic_acid_mg: float = 0.0
    supplement_recommendation: List[str] = Field(default_factory=list)
    food_recommendations: List[str] = Field(default_factory=list)
    foods_to_avoid: List[str] = Field(default_factory=list)
    source_ref: str = ""


class RationItem(BaseModel):
    item_name: str
    quantity: str
    unit: str
    frequency: str
    category: str
    rationale: str = ""


class RationRecommendation(BaseModel):
    ration_id: str = Field(default_factory=new_id)
    patient_id: str
    week_start: str
    trimester: Optional[Trimester] = None
    calorie_target: int = 0
    protein_target_g: int = 0
    ration_items: List[RationItem] = Field(default_factory=list)
    supplements: List[str] = Field(default_factory=list)
    special_adjustments: List[str] = Field(default_factory=list)
    rationale: str = ""
    rule_basis: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    approval_status: str = "recommended"
    distributed: bool = False


class VillageRationSummary(BaseModel):
    village: str
    week_start: str
    total_beneficiaries: int
    aggregated_items: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    total_supplements: Dict[str, int] = Field(default_factory=dict)
    high_priority_count: int = 0
