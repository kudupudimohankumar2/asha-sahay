"""Mock speech-to-text provider for demo/testing."""

from ..base import SpeechToTextProvider, ProviderResponse, timed_call

DEMO_TRANSCRIPTIONS = [
    "मुझे सिर दर्द हो रहा है और चक्कर आ रहे हैं",
    "बच्चा ठीक से हिल रहा है",
    "मेरा वजन बढ़ रहा है लेकिन पैरों में सूजन है",
    "मुझे कल से बुखार है",
    "मैंने आज आयरन की गोली ली",
]


class MockSpeechProvider(SpeechToTextProvider):
    """Returns a canned Hindi transcription for demo purposes."""

    def __init__(self):
        self._counter = 0

    @timed_call
    def transcribe(self, audio_bytes: bytes, language: str = "hi") -> ProviderResponse:
        text = DEMO_TRANSCRIPTIONS[self._counter % len(DEMO_TRANSCRIPTIONS)]
        self._counter += 1
        return ProviderResponse(
            result=text,
            provider_name="mock_stt",
            metadata={"language": language, "demo": True},
        )
