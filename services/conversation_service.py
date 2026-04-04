"""Multilingual conversational AI service with patient-aware RAG."""

import json
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List

from models.common import new_id, Modality
from models.clinical import Encounter
from models.patient import Patient
from providers.config import (
    get_translation_provider,
    get_speech_provider,
    get_reasoning_provider,
)
from services.db import get_db
from services.retrieval_service import RetrievalService
from services.risk_service import RiskService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are ASHA Sahayak, an AI assistant for ASHA health workers in India.

Your role:
- Help ASHA workers manage pregnant women's health
- Provide guidance based on government maternal health guidelines (MCP Card, Safe Motherhood Booklet, PMSMA)
- Flag danger signs and recommend appropriate action
- Always be supportive, clear, and actionable

Rules:
- Never prescribe medications — only recommend seeking medical consultation
- Always mention if a condition requires urgent referral
- Provide evidence from guidelines when giving advice
- If unsure, recommend the ASHA worker consult the ANM or Medical Officer
- Structure responses with: Assessment, Recommended Actions, Evidence, Risk Note

Current patient context will be provided. Use it to give personalized guidance."""


class ConversationService:
    def __init__(self):
        self.db = get_db()
        self.translation = get_translation_provider()
        self.speech = get_speech_provider()
        self.reasoning = get_reasoning_provider()
        self.retrieval = RetrievalService()
        self.risk_service = RiskService()

    def process_message(
        self,
        patient_id: str,
        text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        image_bytes: Optional[bytes] = None,
        source_language: str = "hi",
        mode: str = "general",
    ) -> Dict[str, Any]:
        """Full RAG pipeline: input -> normalize -> retrieve -> reason -> respond.

        Input handling priority:
          - Audio: always transcribe; result becomes the user query
          - Image: always extract via OCR; findings become report context
          - Text: used as the user query if no audio
        All three can be combined: audio provides the query, image provides
        report context, text is used as fallback query.
        """
        modality = Modality.TEXT
        original_text = text or ""
        transcribed_text = ""
        image_extraction = None
        image_context = ""

        # ── Step 1: Transcribe audio if present ─────────────────────────
        if audio_bytes:
            modality = Modality.AUDIO
            try:
                stt_result = self.speech.transcribe(audio_bytes, source_language)
                transcribed_text = (stt_result.result or "").strip()
                logger.info(f"Transcribed audio ({stt_result.provider_name}): {transcribed_text[:100]}")
            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                transcribed_text = ""

            if transcribed_text:
                original_text = transcribed_text
            elif not original_text:
                original_text = "[audio could not be transcribed]"

        # ── Step 2: Extract image/report if present (always, regardless of text) ──
        if image_bytes:
            if modality == Modality.TEXT:
                modality = Modality.IMAGE
            try:
                from services.document_service import DocumentService
                doc_service = DocumentService()
                image_extraction = doc_service.process_upload(
                    patient_id, image_bytes, "image/jpeg", "chat_image.jpg",
                )
                extracted = image_extraction.get("extraction", {})
                findings = extracted.get("findings", {}) if isinstance(extracted, dict) else {}
                flags = image_extraction.get("abnormality_flags", [])

                context_parts = []
                if findings:
                    for k, v in findings.items():
                        context_parts.append(f"{k}: {v}")
                observations = extracted.get("observations", []) if isinstance(extracted, dict) else []
                for obs in observations:
                    context_parts.append(obs)
                if flags:
                    context_parts.append("Flags: " + "; ".join(flags))

                image_context = "Uploaded report findings: " + " | ".join(context_parts) if context_parts else ""
                logger.info(f"Extracted {len(findings)} fields from uploaded image")
            except Exception as e:
                logger.error(f"Image extraction failed: {e}")
                image_context = "[image could not be processed]"

            if not original_text or original_text == "[audio could not be transcribed]":
                original_text = image_context or "Please analyze the uploaded report."

        if not original_text.strip():
            return {
                "encounter_id": "",
                "original_text": "",
                "translated_query": "",
                "ai_response": "No input received. Please type a question, record audio, or upload an image.",
                "translated_response": "No input received.",
                "retrieved_guidelines": [],
                "retrieved_patient_context": [],
                "risk_summary": "",
                "triggered_rules": [],
                "red_flag": False,
                "modality": modality.value,
                "source_language": source_language,
                "confidence": 0.0,
                "transcribed_text": "",
                "image_extraction": None,
            }

        # ── Step 3: Translate to English pivot ──────────────────────────
        detected_lang = self.translation.detect_language(original_text)
        if detected_lang != "en":
            translation_result = self.translation.translate(original_text, detected_lang, "en")
            translated_text = translation_result.result
        else:
            translated_text = original_text

        # ── Step 4: Build patient context ───────────────────────────────
        from services.patient_service import PatientService
        ps = PatientService()
        patient = ps.get_patient(patient_id)
        patient_context = self._build_patient_context(patient) if patient else "No patient context available."

        # ── Step 5: RAG retrieval ───────────────────────────────────────
        retrieval_results = self.retrieval.retrieve(
            query=translated_text,
            patient_id=patient_id,
            top_k_guidelines=5,
            top_k_patient=3,
        )

        # ── Step 6: Risk assessment ─────────────────────────────────────
        risk_context = ""
        triggered_rules = []
        if patient:
            obs = self.risk_service.get_latest_observation(patient_id)
            symptoms = self._extract_symptoms(translated_text)
            if image_context:
                symptoms.extend(self._extract_symptoms(image_context))
                symptoms = list(dict.fromkeys(symptoms))
            risk_eval = self.risk_service.evaluate_patient(patient, obs, symptoms)
            risk_context = self._format_risk_context(risk_eval)
            triggered_rules = risk_eval.triggered_rules

        # ── Step 7: Compose prompt with all context ─────────────────────
        guideline_context = self._format_retrieval_context(retrieval_results)

        prompt = self._compose_prompt(
            query=translated_text,
            patient_context=patient_context,
            guideline_context=guideline_context,
            risk_context=risk_context,
            image_context=image_context,
            mode=mode,
        )

        # ── Step 8: Generate response ───────────────────────────────────
        reasoning_result = self.reasoning.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1024,
        )
        ai_response = reasoning_result.result

        # ── Step 9: Translate response back ─────────────────────────────
        if source_language != "en":
            translated_response = self.translation.translate(ai_response, "en", source_language).result
        else:
            translated_response = ai_response

        # ── Step 10: Persist encounter ──────────────────────────────────
        all_symptoms = self._extract_symptoms(translated_text)
        if image_context:
            all_symptoms.extend(self._extract_symptoms(image_context))
            all_symptoms = list(dict.fromkeys(all_symptoms))

        encounter = Encounter(
            patient_id=patient_id,
            modality=modality,
            source_language=source_language,
            original_text=original_text,
            normalized_text=original_text,
            translated_text=translated_text,
            summary=translated_text[:200],
            symptoms=all_symptoms,
            ai_response=ai_response,
            translated_response=translated_response,
            retrieved_chunks=retrieval_results.get("guideline_chunks", []),
            risk_snapshot={"triggered_rules": triggered_rules} if triggered_rules else None,
            red_flag=any(r.get("severity") == "EMERGENCY" for r in triggered_rules),
        )
        self._persist_encounter(encounter)

        # ── Step 11: Add to patient memory ──────────────────────────────
        memory_text = f"Q: {translated_text}\nA: {ai_response[:300]}"
        if image_context:
            memory_text = f"Report: {image_context[:200]}\n{memory_text}"
        self.retrieval.add_patient_memory(
            patient_id=patient_id,
            text=memory_text,
            chunk_type="conversation",
            source_date=date.today().isoformat(),
        )

        return {
            "encounter_id": encounter.encounter_id,
            "original_text": original_text,
            "translated_query": translated_text,
            "ai_response": ai_response,
            "translated_response": translated_response,
            "retrieved_guidelines": retrieval_results.get("guideline_chunks", []),
            "retrieved_patient_context": retrieval_results.get("patient_chunks", []),
            "risk_summary": risk_context,
            "triggered_rules": triggered_rules,
            "red_flag": encounter.red_flag,
            "modality": modality.value,
            "source_language": source_language,
            "confidence": reasoning_result.metadata.get("confidence", 0.8),
            "transcribed_text": transcribed_text,
            "image_extraction": image_extraction,
        }

    def get_patient_history(self, patient_id: str, limit: int = 10) -> List[Dict]:
        rows = self.db.fetch_all(
            "SELECT * FROM encounters WHERE patient_id = ? ORDER BY encounter_time DESC LIMIT ?",
            (patient_id, limit),
        )
        return rows

    def _build_patient_context(self, patient: Patient) -> str:
        parts = [
            f"Patient: {patient.full_name}, Age: {patient.age}",
            f"Village: {patient.village}",
            f"Gestational weeks: {patient.gestational_weeks}, Trimester: {patient.trimester}",
            f"EDD: {patient.edd_date}",
            f"Gravida: {patient.gravida}, Parity: {patient.parity}",
            f"Risk band: {patient.risk_band}",
        ]
        if patient.known_conditions:
            parts.append(f"Known conditions: {', '.join(patient.known_conditions)}")
        if patient.current_medications:
            parts.append(f"Medications: {', '.join(patient.current_medications)}")

        obs = self.risk_service.get_latest_observation(patient.patient_id)
        if obs:
            vitals = []
            if obs.hemoglobin is not None:
                vitals.append(f"Hb: {obs.hemoglobin} g/dL")
            if obs.systolic_bp and obs.diastolic_bp:
                vitals.append(f"BP: {obs.systolic_bp}/{obs.diastolic_bp}")
            if obs.weight_kg:
                vitals.append(f"Weight: {obs.weight_kg} kg")
            if obs.blood_sugar_fasting:
                vitals.append(f"Fasting sugar: {obs.blood_sugar_fasting}")
            if vitals:
                parts.append(f"Latest vitals ({obs.obs_date}): {', '.join(vitals)}")

        history = self._get_recent_conversation_summary(patient.patient_id)
        if history:
            parts.append(f"\nRecent conversation history:\n{history}")

        return "\n".join(parts)

    def _get_recent_conversation_summary(self, patient_id: str, limit: int = 3) -> str:
        """Fetch the last few encounters to give the model conversational continuity."""
        rows = self.db.fetch_all(
            "SELECT translated_text, ai_response, encounter_time "
            "FROM encounters WHERE patient_id = ? "
            "ORDER BY encounter_time DESC LIMIT ?",
            (patient_id, limit),
        )
        if not rows:
            return ""
        summaries = []
        for r in reversed(rows):
            q = (r.get("translated_text") or "")[:150]
            a = (r.get("ai_response") or "")[:200]
            t = r.get("encounter_time", "")
            summaries.append(f"[{t}] ASHA asked: {q}\nAssistant replied: {a}")
        return "\n".join(summaries)

    def _format_retrieval_context(self, results: Dict) -> str:
        parts = []
        for chunk in results.get("guideline_chunks", []):
            parts.append(f"[Guideline - {chunk.get('source', 'unknown')}]: {chunk.get('text', '')[:500]}")
        for chunk in results.get("patient_chunks", []):
            parts.append(f"[Patient History]: {chunk.get('text', '')[:300]}")
        return "\n\n".join(parts) if parts else "No specific guidelines retrieved."

    def _format_risk_context(self, risk_eval) -> str:
        if not risk_eval.triggered_rules:
            return "Current risk: NORMAL. No active risk flags."
        parts = [f"Risk band: {risk_eval.risk_band.value} (score: {risk_eval.risk_score})"]
        for rule in risk_eval.triggered_rules:
            parts.append(f"- {rule['name']}: {rule.get('details', '')} → {rule['action']}")
        if risk_eval.emergency_flag:
            parts.insert(0, "⚠️ EMERGENCY FLAGS DETECTED")
        return "\n".join(parts)

    def _compose_prompt(
        self, query: str, patient_context: str,
        guideline_context: str, risk_context: str,
        image_context: str = "", mode: str = "general",
    ) -> str:
        sections = [f"ASHA worker query: {query}"]

        if image_context:
            sections.append(f"--- UPLOADED REPORT DATA ---\n{image_context}")

        sections.append(f"--- PATIENT CONTEXT ---\n{patient_context}")
        sections.append(f"--- RISK ASSESSMENT ---\n{risk_context}")
        sections.append(f"--- RELEVANT GUIDELINES ---\n{guideline_context}")

        sections.append(
            "--- INSTRUCTIONS ---\n"
            "Provide a helpful, actionable response to the ASHA worker's query.\n"
            "Include: assessment, recommended actions, evidence from guidelines, and risk notes.\n"
            "If report data was uploaded, analyze the findings and flag any abnormal values.\n"
            "If any danger signs are present, clearly flag them.\n"
            f"Mode: {mode}"
        )

        return "\n\n".join(sections)

    def _extract_symptoms(self, text: str) -> List[str]:
        symptom_keywords = {
            "headache": "headache", "सिर दर्द": "headache",
            "bleeding": "bleeding", "खून": "bleeding", "रक्तस्राव": "bleeding",
            "vomiting": "vomiting", "उल्टी": "vomiting",
            "fever": "fever", "बुखार": "fever",
            "swelling": "swelling", "सूजन": "swelling",
            "dizzy": "dizziness", "चक्कर": "dizziness",
            "pain": "abdominal pain", "दर्द": "pain",
            "blurred": "blurred vision", "धुंधला": "blurred vision",
            "convulsion": "convulsions", "दौरा": "convulsions",
            "not moving": "reduced fetal movement",
            "हिल नहीं": "reduced fetal movement",
            "breathless": "breathlessness",
        }
        found = []
        lower = text.lower()
        for keyword, symptom in symptom_keywords.items():
            if keyword in lower and symptom not in found:
                found.append(symptom)
        return found

    def _persist_encounter(self, enc: Encounter):
        self.db.insert("encounters", {
            "encounter_id": enc.encounter_id,
            "patient_id": enc.patient_id,
            "encounter_time": enc.encounter_time.isoformat(),
            "modality": enc.modality.value,
            "source_language": enc.source_language,
            "original_text": enc.original_text,
            "normalized_text": enc.normalized_text,
            "translated_text": enc.translated_text,
            "summary": enc.summary,
            "symptoms": json.dumps(enc.symptoms),
            "extracted_health_updates": json.dumps(enc.extracted_health_updates),
            "ai_response": enc.ai_response,
            "translated_response": enc.translated_response,
            "retrieved_chunks": json.dumps(enc.retrieved_chunks, default=str),
            "risk_snapshot": json.dumps(enc.risk_snapshot) if enc.risk_snapshot else "",
            "red_flag": 1 if enc.red_flag else 0,
            "escalation_status": enc.escalation_status,
        })
