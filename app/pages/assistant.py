"""AI Assistant page: multilingual chat with patient-aware RAG."""

import gradio as gr
from app.components.common import LANGUAGES, RISK_EMOJI, risk_badge


def build_assistant_page():
    gr.Markdown("## AI Assistant (AI सहायक)")

    with gr.Row():
        patient_selector = gr.Dropdown(
            choices=_get_patient_choices(),
            label="Select Patient",
            interactive=True,
        )
        lang_selector = gr.Dropdown(
            choices=[l[1] for l in LANGUAGES],
            value="हिन्दी (Hindi)",
            label="Language",
        )

    gr.Markdown("### Ask a Question")
    gr.Markdown(
        "*You can combine inputs: type a question AND upload a report image, "
        "or record audio AND upload an image.*",
        elem_classes=["text-sm"],
    )

    text_input = gr.Textbox(
        label="Type your question",
        placeholder="e.g., मुझे सिर दर्द हो रहा है / Is her hemoglobin normal?",
        lines=2,
    )
    with gr.Row():
        audio_input = gr.Audio(label="Or record audio", type="numpy", sources=["microphone"])
        image_input = gr.Image(label="Or upload report image", type="filepath")

    with gr.Row():
        send_btn = gr.Button("🚀 Send", variant="primary", size="lg")
        clear_btn = gr.Button("🗑️ Clear", variant="secondary")

    response_html = gr.HTML()
    evidence_html = gr.HTML()

    def process_chat(patient_sel, lang, text, audio, image):
        if not patient_sel:
            return ('<div style="color:red;">Please select a patient first</div>', "")

        pid = patient_sel.split(" | ")[0]
        lang_map = {l[1]: l[0] for l in LANGUAGES}
        lang_code = lang_map.get(lang, "hi")

        audio_bytes = None
        if audio is not None:
            import io
            try:
                import soundfile as sf
                sr, data = audio
                buf = io.BytesIO()
                sf.write(buf, data, sr, format="WAV")
                audio_bytes = buf.getvalue()
            except Exception as e:
                pass

        image_bytes = None
        if image is not None:
            try:
                with open(image, "rb") as f:
                    image_bytes = f.read()
            except Exception:
                pass

        if not text and audio_bytes is None and image_bytes is None:
            return (
                '<div style="color:#f59e0b;">Please provide a question (text, audio, or image)</div>',
                "",
            )

        from services.conversation_service import ConversationService
        conv = ConversationService()
        result = conv.process_message(
            patient_id=pid,
            text=text or None,
            audio_bytes=audio_bytes,
            image_bytes=image_bytes,
            source_language=lang_code,
        )

        response = result.get("translated_response", result.get("ai_response", ""))
        red_flag = result.get("red_flag", False)

        border_color = "#ef4444" if red_flag else "#22c55e"
        flag_banner = ""
        if red_flag:
            flag_banner = (
                '<div style="background:#fef2f2;border:2px solid #ef4444;'
                'border-radius:8px;padding:12px;margin-bottom:8px;">'
                '<strong style="color:#ef4444;">⚠️ EMERGENCY FLAGS DETECTED — Take immediate action</strong>'
                '</div>'
            )

        input_info = _build_input_summary(result)

        resp_html = f"""
        {flag_banner}
        <div style="border:1px solid {border_color};border-radius:12px;padding:16px;margin:8px 0;">
          {input_info}
          <div style="white-space:pre-wrap;line-height:1.6;">{response}</div>
        </div>
        """

        evidence = _build_evidence_html(result)
        return resp_html, evidence

    send_btn.click(
        process_chat,
        inputs=[patient_selector, lang_selector, text_input, audio_input, image_input],
        outputs=[response_html, evidence_html],
    )

    def clear():
        return "", "", None, None, "", ""

    clear_btn.click(
        clear,
        outputs=[text_input, response_html, audio_input, image_input, evidence_html, response_html],
    )


def _build_input_summary(result: dict) -> str:
    """Show what the system understood from each input modality."""
    parts = []
    modality = result.get("modality", "text")

    transcribed = result.get("transcribed_text", "")
    if transcribed:
        parts.append(
            f'<div style="background:#eff6ff;border-radius:6px;padding:8px;margin-bottom:8px;font-size:0.85em;">'
            f'🎤 <strong>Audio transcription:</strong> "{transcribed}"</div>'
        )

    extraction = result.get("image_extraction")
    if extraction:
        findings = extraction.get("extraction", {})
        if isinstance(findings, dict):
            field_data = findings.get("findings", {})
            flags = extraction.get("abnormality_flags", [])
            if field_data or flags:
                items = [f"<strong>{k}:</strong> {v}" for k, v in field_data.items()]
                flag_items = [f'<span style="color:#ef4444;">{f}</span>' for f in flags]
                all_items = items + flag_items
                parts.append(
                    f'<div style="background:#f0fdf4;border-radius:6px;padding:8px;margin-bottom:8px;font-size:0.85em;">'
                    f'📋 <strong>Report extraction:</strong> {" | ".join(all_items)}</div>'
                )

    original = result.get("original_text", "")
    if original and not transcribed and not extraction:
        parts.append(
            f'<div style="font-size:0.85em;color:#6b7280;margin-bottom:8px;">'
            f'💬 Input: {original[:150]}</div>'
        )

    return "".join(parts)


def _build_evidence_html(result: dict) -> str:
    html = '<details style="margin-top:8px;"><summary style="cursor:pointer;font-weight:bold;">📚 Evidence & Context</summary>'

    guidelines = result.get("retrieved_guidelines", [])
    if guidelines:
        html += '<div style="margin-top:8px;"><strong>Retrieved Guidelines:</strong></div>'
        for g in guidelines[:3]:
            score = g.get("score", 0)
            html += (
                f'<div style="background:#f8fafc;border-radius:6px;padding:8px;margin:4px 0;font-size:0.9em;">'
                f'<strong>[{g.get("source", "Guideline")}]</strong> (relevance: {score:.2f})<br/>'
                f'{g.get("text", "")[:200]}...</div>'
            )

    rules = result.get("triggered_rules", [])
    if rules:
        html += '<div style="margin-top:8px;"><strong>Triggered Risk Rules:</strong></div>'
        for r in rules:
            html += (
                f'<div style="background:#fffbeb;border-radius:6px;padding:6px;margin:4px 0;font-size:0.9em;">'
                f'{r.get("name", "")} ({r.get("severity", "")}) — {r.get("details", "")}<br/>'
                f'<em>Source: {r.get("source_ref", "")}</em></div>'
            )

    risk_summary = result.get("risk_summary", "")
    if risk_summary:
        html += (
            f'<div style="margin-top:8px;"><strong>Risk Summary:</strong><br/>'
            f'<pre style="font-size:0.85em;">{risk_summary}</pre></div>'
        )

    html += "</details>"
    return html


def _get_patient_choices():
    from services.patient_service import PatientService
    ps = PatientService()
    patients = ps.list_patients()
    return [f"{p.patient_id} | {p.full_name} ({RISK_EMOJI.get(p.risk_band, '')})" for p in patients]
