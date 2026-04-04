"""Local OCR provider using pytesseract for medical report extraction."""

import io
import re
import logging
from typing import Any, Dict, List, Optional

from ..base import VisionExtractionProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)


# Regex patterns for common maternal health report fields
FIELD_PATTERNS = {
    "hemoglobin": [
        r"(?:h[ae]moglobin|hb|hgb)\s*[:=\-]?\s*([\d]+\.?\d*)\s*(?:g/?dl|gm)?",
        r"hb\s*[:=\-]?\s*([\d]+\.?\d*)",
    ],
    "systolic_bp": [
        r"(?:bp|blood\s*pressure)\s*[:=\-]?\s*(\d{2,3})\s*/\s*\d{2,3}",
        r"systolic\s*[:=\-]?\s*(\d{2,3})",
    ],
    "diastolic_bp": [
        r"(?:bp|blood\s*pressure)\s*[:=\-]?\s*\d{2,3}\s*/\s*(\d{2,3})",
        r"diastolic\s*[:=\-]?\s*(\d{2,3})",
    ],
    "blood_sugar_fasting": [
        r"(?:fasting|fbs|fbg)\s*(?:blood\s*)?(?:sugar|glucose)\s*[:=\-]?\s*([\d]+\.?\d*)",
        r"fbs\s*[:=\-]?\s*([\d]+\.?\d*)",
    ],
    "blood_sugar_pp": [
        r"(?:pp|post\s*prandial|ppbs|ppbg)\s*(?:blood\s*)?(?:sugar|glucose)\s*[:=\-]?\s*([\d]+\.?\d*)",
    ],
    "weight_kg": [
        r"weight\s*[:=\-]?\s*([\d]+\.?\d*)\s*(?:kg|kgs)?",
    ],
    "blood_group": [
        r"(?:blood\s*group|blood\s*type)\s*[:=\-]?\s*([ABO]{1,2}[+-])",
    ],
    "urine_protein": [
        r"(?:urine\s*(?:albumin|protein))\s*[:=\-]?\s*(\w+)",
    ],
    "urine_sugar": [
        r"(?:urine\s*sugar|urine\s*glucose)\s*[:=\-]?\s*(\w+)",
    ],
    "fetal_heart_rate": [
        r"(?:fetal\s*heart|fhr|fhs)\s*(?:rate|sound)?\s*[:=\-]?\s*(\d{2,3})\s*(?:bpm)?",
    ],
    "hiv_screening": [
        r"(?:hiv)\s*(?:screening|test|status)?\s*[:=\-]?\s*(positive|negative|reactive|non[\s\-]?reactive)",
    ],
    "syphilis": [
        r"(?:vdrl|syphilis|rpr)\s*[:=\-]?\s*(positive|negative|reactive|non[\s\-]?reactive)",
    ],
}

NUMERIC_FIELDS = {
    "hemoglobin", "systolic_bp", "diastolic_bp",
    "blood_sugar_fasting", "blood_sugar_pp", "weight_kg", "fetal_heart_rate",
}


def _parse_fields(text: str) -> Dict[str, Any]:
    """Extract structured medical fields from OCR text using regex patterns."""
    findings: Dict[str, Any] = {}
    lower = text.lower()

    for field, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, lower, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field in NUMERIC_FIELDS:
                    try:
                        findings[field] = float(value)
                        if field in ("systolic_bp", "diastolic_bp", "fetal_heart_rate"):
                            findings[field] = int(float(value))
                    except ValueError:
                        continue
                else:
                    findings[field] = value
                break
    return findings


def _detect_abnormalities(findings: Dict[str, Any]) -> List[str]:
    flags = []
    hb = findings.get("hemoglobin")
    if hb is not None:
        if hb < 7:
            flags.append("CRITICAL: Severe anemia (Hb < 7 g/dL)")
        elif hb < 10:
            flags.append("WARNING: Moderate anemia (Hb < 10 g/dL)")

    sbp = findings.get("systolic_bp")
    dbp = findings.get("diastolic_bp")
    if sbp and dbp:
        if sbp > 160 or dbp > 110:
            flags.append("CRITICAL: Severe hypertension")
        elif sbp > 140 or dbp > 90:
            flags.append("WARNING: Elevated blood pressure")

    sugar = findings.get("blood_sugar_fasting")
    if sugar and sugar > 126:
        flags.append("WARNING: Elevated fasting blood sugar")

    hiv = findings.get("hiv_screening", "").lower()
    if hiv in ("positive", "reactive"):
        flags.append("CRITICAL: HIV positive/reactive")

    return flags


def _build_result(raw_text: str, findings: Dict[str, Any]) -> Dict[str, Any]:
    abnormalities = _detect_abnormalities(findings)
    observations = []
    if findings.get("hemoglobin"):
        observations.append(f"Hemoglobin: {findings['hemoglobin']} g/dL")
    if findings.get("systolic_bp") and findings.get("diastolic_bp"):
        observations.append(f"BP: {findings['systolic_bp']}/{findings['diastolic_bp']} mmHg")
    if findings.get("blood_sugar_fasting"):
        observations.append(f"Fasting sugar: {findings['blood_sugar_fasting']} mg/dL")

    return {
        "report_type": "Medical Report (OCR Extracted)",
        "report_date": None,
        "findings": findings,
        "observations": observations + abnormalities,
        "recommendations": [],
        "raw_text": raw_text,
    }


class PytesseractVisionProvider(VisionExtractionProvider):
    """Extracts text from images/PDFs using pytesseract, then parses
    structured medical fields via regex patterns."""

    @timed_call
    def extract_from_image(self, image_bytes: bytes) -> ProviderResponse:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            raw_text = pytesseract.image_to_string(img, lang="eng+hin")
        except ImportError as e:
            logger.error(f"pytesseract/PIL not available: {e}")
            raw_text = ""
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raw_text = ""

        findings = _parse_fields(raw_text)
        result = _build_result(raw_text, findings)
        confidence = min(0.9, 0.3 + 0.1 * len(findings))

        return ProviderResponse(
            result=result,
            provider_name="pytesseract_vision",
            metadata={"confidence": confidence, "fields_found": len(findings)},
        )

    @timed_call
    def extract_from_pdf(self, pdf_bytes: bytes) -> ProviderResponse:
        raw_pages: List[str] = []
        try:
            from pdf2image import convert_from_bytes
            import pytesseract

            images = convert_from_bytes(pdf_bytes, dpi=200)
            for page_img in images:
                page_text = pytesseract.image_to_string(page_img, lang="eng+hin")
                raw_pages.append(page_text)
        except ImportError:
            logger.warning("pdf2image not available, attempting direct text extraction")
            try:
                raw_pages.append(pdf_bytes.decode("utf-8", errors="ignore"))
            except Exception:
                raw_pages.append("")
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            raw_pages.append("")

        full_text = "\n---PAGE BREAK---\n".join(raw_pages)
        findings = _parse_fields(full_text)
        result = _build_result(full_text, findings)
        confidence = min(0.85, 0.25 + 0.1 * len(findings))

        return ProviderResponse(
            result=result,
            provider_name="pytesseract_vision",
            metadata={
                "confidence": confidence,
                "fields_found": len(findings),
                "pages": len(raw_pages),
            },
        )
