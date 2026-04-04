"""Mock vision/OCR provider for demo/testing."""

import json
from ..base import VisionExtractionProvider, ProviderResponse, timed_call

DEMO_EXTRACTION = {
    "report_type": "ANC Blood Test Report",
    "patient_name": "Demo Patient",
    "report_date": "2026-03-15",
    "findings": {
        "hemoglobin": 8.5,
        "blood_group": "B+",
        "systolic_bp": 145,
        "diastolic_bp": 95,
        "blood_sugar_fasting": 92,
        "urine_protein": "trace",
        "urine_sugar": "nil",
        "hiv_screening": "negative",
        "syphilis": "negative",
    },
    "observations": [
        "Moderate anemia detected",
        "Blood pressure slightly elevated",
        "Trace protein in urine - monitor"
    ],
    "recommendations": [
        "Increase iron supplementation",
        "Monitor blood pressure weekly",
        "Repeat urine test at next visit"
    ],
    "raw_text": (
        "ANTENATAL CHECK-UP REPORT\n"
        "Patient: Demo Patient\nDate: 15-03-2026\n"
        "Hemoglobin: 8.5 g/dL\nBlood Group: B+\n"
        "BP: 145/95 mmHg\nFasting Blood Sugar: 92 mg/dL\n"
        "Urine Albumin: Trace\nUrine Sugar: Nil\n"
        "HIV Screening: Negative\nVDRL: Negative\n"
        "Impression: Moderate anemia. Borderline hypertension.\n"
        "Advice: Increase IFA, monitor BP weekly."
    ),
}


class MockVisionProvider(VisionExtractionProvider):
    """Returns a realistic demo ANC report extraction."""

    @timed_call
    def extract_from_image(self, image_bytes: bytes) -> ProviderResponse:
        return ProviderResponse(
            result=DEMO_EXTRACTION,
            provider_name="mock_vision",
            metadata={"confidence": 0.85, "demo": True},
        )

    @timed_call
    def extract_from_pdf(self, pdf_bytes: bytes) -> ProviderResponse:
        return ProviderResponse(
            result=DEMO_EXTRACTION,
            provider_name="mock_vision",
            metadata={"confidence": 0.80, "demo": True},
        )
