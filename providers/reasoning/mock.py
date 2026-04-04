"""Mock reasoning provider for demo/testing."""

import json
from typing import Optional, Dict
from ..base import ReasoningProvider, ProviderResponse, timed_call

MATERNAL_RESPONSES = {
    "headache": (
        "Based on the patient's profile and guidelines:\n\n"
        "**Assessment:** Headache during pregnancy can indicate elevated blood pressure or pre-eclampsia, "
        "especially in the 2nd/3rd trimester.\n\n"
        "**Recommended Actions:**\n"
        "1. Check blood pressure immediately\n"
        "2. Check for visual disturbances, swelling\n"
        "3. If BP > 140/90, refer to PHC urgently\n"
        "4. Ensure adequate rest and hydration\n\n"
        "**Evidence:** MCP Card danger signs - Headache with blurred vision requires immediate referral. "
        "Safe Motherhood Booklet recommends BP check at every ANC visit.\n\n"
        "**Risk Note:** Monitor closely. If accompanied by blurred vision or swelling, treat as EMERGENCY."
    ),
    "bleeding": (
        "**URGENT ALERT**\n\n"
        "Vaginal bleeding during pregnancy is a danger sign requiring immediate medical attention.\n\n"
        "**Immediate Actions:**\n"
        "1. DO NOT delay - transport to nearest hospital/FRU immediately\n"
        "2. Keep the woman lying down and calm\n"
        "3. Call ambulance (toll-free number)\n"
        "4. Do NOT give anything by mouth\n\n"
        "**Evidence:** MCP Card 2018 - Bleeding during pregnancy is classified as EMERGENCY. "
        "Safe Motherhood Booklet: Contact FRU immediately for vaginal bleeding.\n\n"
        "**Risk Level:** EMERGENCY - Immediate referral required."
    ),
    "iron": (
        "**Iron and Anemia Guidance:**\n\n"
        "As per government guidelines:\n"
        "- Take 1 IFA tablet daily starting from 4th month\n"
        "- If anemic (Hb < 11): Take 2 IFA tablets daily\n"
        "- Total minimum 180 tablets during pregnancy\n"
        "- Take with Vitamin C (lemon/amla) for better absorption\n"
        "- Avoid tea/coffee near meal times\n\n"
        "**Diet Recommendations:**\n"
        "- Green leafy vegetables (spinach, fenugreek)\n"
        "- Jaggery, dates, beetroot\n"
        "- Eggs, meat, fish (if non-vegetarian)\n\n"
        "**Evidence:** MCP Card 2018, POSHAN 2.0 guidelines.\n"
        "**Next Action:** Recheck hemoglobin at next ANC visit."
    ),
    "default": (
        "Based on the patient's current status and maternal health guidelines:\n\n"
        "**General Advice:**\n"
        "1. Continue regular ANC visits as scheduled\n"
        "2. Take IFA tablets and calcium supplements daily\n"
        "3. Eat one extra meal daily with variety\n"
        "4. Rest 2 hours during day + 8 hours at night\n"
        "5. Report any danger signs immediately\n\n"
        "**Danger Signs to Watch:**\n"
        "- Bleeding, severe headache, blurred vision\n"
        "- Convulsions, high fever, reduced fetal movement\n"
        "- Severe swelling, breathlessness\n\n"
        "**Evidence:** MCP Card 2018, Safe Motherhood Booklet.\n"
        "**Next Action:** Continue monitoring. Next ANC visit as per schedule."
    ),
}


class MockReasoningProvider(ReasoningProvider):
    """Returns contextually appropriate maternal health guidance for demo."""

    @timed_call
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> ProviderResponse:
        lower = prompt.lower()

        response = MATERNAL_RESPONSES["default"]
        for keyword, resp in MATERNAL_RESPONSES.items():
            if keyword in lower:
                response = resp
                break

        return ProviderResponse(
            result=response,
            provider_name="mock_reasoning",
            model_name="mock-maternal-v1",
            input_tokens=len(prompt.split()),
            output_tokens=len(response.split()),
        )

    @timed_call
    def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        response_schema: Optional[Dict] = None,
    ) -> ProviderResponse:
        structured = {
            "assessment": "Based on patient context and guidelines",
            "risk_level": "NORMAL",
            "recommendations": [
                "Continue regular ANC visits",
                "Take IFA and calcium daily",
                "Report danger signs immediately",
            ],
            "evidence": ["MCP Card 2018", "Safe Motherhood Booklet"],
            "next_actions": ["Schedule next ANC visit", "Monitor vitals"],
            "confidence": 0.8,
        }
        return ProviderResponse(
            result=structured,
            provider_name="mock_reasoning",
            model_name="mock-maternal-v1",
        )
