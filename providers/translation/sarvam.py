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

    MAX_CHUNK_LEN = 900

    @timed_call
    def translate(self, text: str, source_lang: str, target_lang: str) -> ProviderResponse:
        if source_lang == target_lang:
            return ProviderResponse(result=text, provider_name="sarvam_translate")

        src_code = SARVAM_LANG_MAP.get(source_lang, source_lang)
        tgt_code = SARVAM_LANG_MAP.get(target_lang, target_lang)

        if len(text) <= self.MAX_CHUNK_LEN:
            return self._translate_chunk(text, src_code, tgt_code)

        chunks = self._split_text(text, self.MAX_CHUNK_LEN)
        translated_parts = []
        for chunk in chunks:
            result = self._translate_chunk(chunk, src_code, tgt_code)
            translated_parts.append(result.result)

        return ProviderResponse(
            result="\n".join(translated_parts),
            provider_name="sarvam_translate",
            model_name="sarvam-translate",
            metadata={"source": src_code, "target": tgt_code, "chunks": len(chunks)},
        )

    def _translate_chunk(self, text: str, src_code: str, tgt_code: str) -> ProviderResponse:
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

    @staticmethod
    def _split_text(text: str, max_len: int) -> list:
        """Split text at paragraph/sentence boundaries to stay under max_len."""
        paragraphs = text.split("\n")
        chunks, current = [], ""
        for para in paragraphs:
            if len(current) + len(para) + 1 <= max_len:
                current = (current + "\n" + para) if current else para
            else:
                if current:
                    chunks.append(current)
                if len(para) <= max_len:
                    current = para
                else:
                    sentences = para.replace(". ", ".\n").split("\n")
                    for sent in sentences:
                        if len(current) + len(sent) + 1 <= max_len:
                            current = (current + " " + sent) if current else sent
                        else:
                            if current:
                                chunks.append(current)
                            current = sent
        if current:
            chunks.append(current)
        return chunks

    def detect_language(self, text: str) -> str:
        """Detect language using Unicode script ranges with Sarvam API fallback."""
        detected = self._heuristic_detect(text)
        if detected != "en":
            return detected

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
            logger.debug(f"Auto-detect API failed, using heuristic result: {e}")

        return detected

    @staticmethod
    def _heuristic_detect(text: str) -> str:
        """Detect Indic language from Unicode script ranges."""
        for ch in text:
            cp = ord(ch)
            if 0x0900 <= cp <= 0x097F:
                return "hi"
            if 0x0C00 <= cp <= 0x0C7F:
                return "te"
            if 0x0C80 <= cp <= 0x0CFF:
                return "kn"
            if 0x0B80 <= cp <= 0x0BFF:
                return "ta"
            if 0x0980 <= cp <= 0x09FF:
                return "bn"
            if 0x0A80 <= cp <= 0x0AFF:
                return "gu"
            if 0x0D00 <= cp <= 0x0D7F:
                return "ml"
            if 0x0A00 <= cp <= 0x0A7F:
                return "pa"
            if 0x0B00 <= cp <= 0x0B7F:
                return "od"
            if 0x0A80 <= cp <= 0x0AFF:
                return "mr"
        return "en"
