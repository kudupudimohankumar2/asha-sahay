"""Sarvam AI translation provider using the official sarvamai SDK."""

import logging
from ..base import TranslationProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)

SARVAM_LANG_MAP = {
    "hi": "hi-IN", "en": "en-IN", "te": "te-IN", "ta": "ta-IN",
    "kn": "kn-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
    "ml": "ml-IN", "pa": "pa-IN", "od": "or-IN", "as": "as-IN",
    "ur": "ur-IN", "sa": "sa-IN", "ne": "ne-IN",
}


class SarvamTranslationProvider(TranslationProvider):
    """Translates text using Sarvam Translate (Mayura / sarvam-translate:v1).

    Accepts a pre-initialized sarvamai.SarvamAI client from the factory.
    """

    def __init__(self, client):
        self._client = client

    @timed_call
    def translate(self, text: str, source_lang: str, target_lang: str) -> ProviderResponse:
        if source_lang == target_lang:
            return ProviderResponse(result=text, provider_name="sarvam_translate")

        src_code = SARVAM_LANG_MAP.get(source_lang, source_lang)
        tgt_code = SARVAM_LANG_MAP.get(target_lang, target_lang)

        try:
            response = self._client.text.translate(
                input=text,
                source_language_code=src_code,
                target_language_code=tgt_code,
            )
            translated = getattr(response, "translated_text", None) or str(response)
            return ProviderResponse(
                result=translated,
                provider_name="sarvam_translate",
                model_name="sarvam-translate",
                metadata={"source": src_code, "target": tgt_code},
            )
        except Exception as e:
            logger.error(f"Sarvam translation failed: {e}")
            return ProviderResponse(result=text, provider_name="sarvam_translate_fallback")

    def detect_language(self, text: str) -> str:
        """Use Sarvam auto-detect via a no-op translate call, fall back to heuristic."""
        try:
            response = self._client.text.translate(
                input=text[:200],
                source_language_code="auto",
                target_language_code="en-IN",
            )
            src = getattr(response, "source_language_code", None)
            if src:
                for short, full in SARVAM_LANG_MAP.items():
                    if full == src:
                        return short
                return src.split("-")[0]
        except Exception as e:
            logger.debug(f"Auto-detect failed, using heuristic: {e}")

        devanagari = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसहा")
        if any(c in devanagari for c in text):
            return "hi"
        return "en"
