"""Mock translation provider for demo/testing."""

from ..base import TranslationProvider, ProviderResponse, timed_call

DEMO_TRANSLATIONS = {
    ("hi", "en"): {
        "मुझे सिर दर्द हो रहा है": "I am having a headache",
        "मुझे उल्टी आ रही है": "I am having vomiting",
        "बच्चा हिल नहीं रहा": "The baby is not moving",
        "मुझे खून आ रहा है": "I am bleeding",
        "मेरा ब्लड प्रेशर बहुत है": "My blood pressure is very high",
        "मुझे चक्कर आ रहे हैं": "I am feeling dizzy",
        "पैरों में सूजन है": "There is swelling in legs",
        "मुझे बुखार है": "I have fever",
    },
    ("en", "hi"): {
        "Your hemoglobin is low": "आपका हीमोग्लोबिन कम है",
        "Please visit the PHC": "कृपया PHC जाएं",
        "Take iron tablets daily": "रोज़ आयरन की गोली लें",
        "Your next checkup is due": "आपका अगला चेकअप बकाया है",
        "Emergency: Please go to hospital immediately": "आपातकाल: कृपया तुरंत अस्पताल जाएं",
    },
}


class MockTranslationProvider(TranslationProvider):
    """Returns canned translations for common maternal health phrases."""

    @timed_call
    def translate(self, text: str, source_lang: str, target_lang: str) -> ProviderResponse:
        if source_lang == target_lang:
            return ProviderResponse(result=text, provider_name="mock_translation")

        pair = (source_lang, target_lang)
        translations = DEMO_TRANSLATIONS.get(pair, {})
        result = translations.get(text, f"[{target_lang}] {text}")

        return ProviderResponse(
            result=result,
            provider_name="mock_translation",
            metadata={"source_lang": source_lang, "target_lang": target_lang},
        )

    def detect_language(self, text: str) -> str:
        hindi_chars = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसहा")
        if any(c in hindi_chars for c in text):
            return "hi"
        return "en"
