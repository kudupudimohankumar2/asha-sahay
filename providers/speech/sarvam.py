"""Sarvam AI speech-to-text provider using the official sarvamai SDK."""

import io
import logging
from ..base import SpeechToTextProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)

SARVAM_LANG_MAP = {
    "hi": "hi-IN", "en": "en-IN", "te": "te-IN", "ta": "ta-IN",
    "kn": "kn-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
    "ml": "ml-IN", "pa": "pa-IN", "od": "or-IN",
}


class SarvamSpeechProvider(SpeechToTextProvider):
    """Transcribes audio using Sarvam Saaras v3.

    Accepts a pre-initialized sarvamai.SarvamAI client from the factory.
    """

    def __init__(self, client, model: str = "saaras:v3"):
        self._client = client
        self._model = model

    @timed_call
    def transcribe(self, audio_bytes: bytes, language: str = "hi") -> ProviderResponse:
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            response = self._client.speech_to_text.transcribe(
                file=audio_file,
                model=self._model,
                mode="transcribe",
            )
            transcript = getattr(response, "transcript", None) or str(response)
            detected_lang = getattr(response, "language_code", language)
            return ProviderResponse(
                result=transcript,
                provider_name="sarvam_stt",
                model_name=self._model,
                metadata={
                    "language": detected_lang,
                    "model": self._model,
                },
            )
        except Exception as e:
            logger.error(f"Sarvam STT failed: {e}")
            return ProviderResponse(
                result="[transcription failed]",
                provider_name="sarvam_stt_error",
                metadata={"error": str(e)},
            )
