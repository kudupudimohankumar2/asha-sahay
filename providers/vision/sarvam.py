"""Sarvam Vision provider for document intelligence using the sarvamai SDK.

Uses the async job-based Document Intelligence API:
  create_job → upload_file → start → wait_until_complete → download_output
"""

import io
import os
import re
import json
import tempfile
import zipfile
import logging
from typing import Any, Dict, List

from ..base import VisionExtractionProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)


def _parse_markdown_fields(md_text: str) -> Dict[str, Any]:
    """Extract structured medical fields from Sarvam Vision markdown output."""
    findings: Dict[str, Any] = {}
    lower = md_text.lower()

    patterns = {
        "hemoglobin": r"(?:h[ae]moglobin|hb|hgb)\s*[:\|]?\s*([\d]+\.?\d*)",
        "systolic_bp": r"(?:bp|blood\s*pressure)\s*[:\|]?\s*(\d{2,3})\s*/\s*\d{2,3}",
        "diastolic_bp": r"(?:bp|blood\s*pressure)\s*[:\|]?\s*\d{2,3}\s*/\s*(\d{2,3})",
        "blood_sugar_fasting": r"(?:fasting|fbs)\s*(?:blood\s*)?(?:sugar|glucose)\s*[:\|]?\s*([\d]+\.?\d*)",
        "weight_kg": r"weight\s*[:\|]?\s*([\d]+\.?\d*)\s*(?:kg)?",
        "blood_group": r"(?:blood\s*group|type)\s*[:\|]?\s*([ABO]{1,2}[+-])",
        "urine_protein": r"(?:urine\s*(?:albumin|protein))\s*[:\|]?\s*(\w+)",
        "urine_sugar": r"(?:urine\s*sugar)\s*[:\|]?\s*(\w+)",
        "fetal_heart_rate": r"(?:fetal\s*heart|fhr)\s*(?:rate)?\s*[:\|]?\s*(\d{2,3})",
    }

    numeric = {"hemoglobin", "systolic_bp", "diastolic_bp", "blood_sugar_fasting", "weight_kg", "fetal_heart_rate"}
    for field, pattern in patterns.items():
        m = re.search(pattern, lower, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if field in numeric:
                try:
                    findings[field] = float(val)
                    if field in ("systolic_bp", "diastolic_bp", "fetal_heart_rate"):
                        findings[field] = int(float(val))
                except ValueError:
                    pass
            else:
                findings[field] = val

    return findings


class SarvamVisionProvider(VisionExtractionProvider):
    """Uses Sarvam Vision Document Intelligence for medical report extraction.

    Accepts a pre-initialized sarvamai.SarvamAI client from the factory.
    """

    def __init__(self, client, language: str = "en-IN", output_format: str = "md"):
        self._client = client
        self._language = language
        self._output_format = output_format

    def _process_document(self, file_path: str) -> Dict[str, Any]:
        """Run the full Sarvam Vision job pipeline."""
        job = self._client.document_intelligence.create_job(
            language=self._language,
            output_format=self._output_format,
        )
        logger.info(f"Sarvam Vision job created: {job.job_id}")

        job.upload_file(file_path)
        job.start()
        status = job.wait_until_complete()
        logger.info(f"Sarvam Vision job completed: {status.job_state}")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.zip")
            job.download_output(output_path)

            md_text = ""
            with zipfile.ZipFile(output_path, "r") as zf:
                for name in zf.namelist():
                    if name.endswith(".md") or name.endswith(".html"):
                        md_text += zf.read(name).decode("utf-8", errors="ignore")
                        md_text += "\n"

        findings = _parse_markdown_fields(md_text)
        observations = []
        abnormalities = []

        hb = findings.get("hemoglobin")
        if hb is not None:
            if hb < 7:
                abnormalities.append("CRITICAL: Severe anemia (Hb < 7)")
            elif hb < 10:
                abnormalities.append("WARNING: Moderate anemia")
        sbp = findings.get("systolic_bp")
        dbp = findings.get("diastolic_bp")
        if sbp and dbp:
            if sbp > 160 or dbp > 110:
                abnormalities.append("CRITICAL: Severe hypertension")
            elif sbp > 140 or dbp > 90:
                abnormalities.append("WARNING: Elevated blood pressure")

        return {
            "report_type": "Medical Report (Sarvam Vision)",
            "report_date": None,
            "findings": findings,
            "observations": observations + abnormalities,
            "recommendations": [],
            "raw_text": md_text[:5000],
        }

    @timed_call
    def extract_from_image(self, image_bytes: bytes) -> ProviderResponse:
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name

            result = self._process_document(tmp_path)
            confidence = min(0.95, 0.5 + 0.1 * len(result.get("findings", {})))

            return ProviderResponse(
                result=result,
                provider_name="sarvam_vision",
                metadata={"confidence": confidence},
            )
        except Exception as e:
            logger.error(f"Sarvam Vision image extraction failed: {e}")
            from .pytesseract_provider import PytesseractVisionProvider
            return PytesseractVisionProvider().extract_from_image(image_bytes)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    @timed_call
    def extract_from_pdf(self, pdf_bytes: bytes) -> ProviderResponse:
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            result = self._process_document(tmp_path)
            confidence = min(0.95, 0.5 + 0.1 * len(result.get("findings", {})))

            return ProviderResponse(
                result=result,
                provider_name="sarvam_vision",
                metadata={"confidence": confidence},
            )
        except Exception as e:
            logger.error(f"Sarvam Vision PDF extraction failed: {e}")
            from .pytesseract_provider import PytesseractVisionProvider
            return PytesseractVisionProvider().extract_from_pdf(pdf_bytes)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
