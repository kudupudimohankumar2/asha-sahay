"""Abstract base classes for all AI providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProviderResponse:
    """Standard response wrapper from any provider."""
    result: Any
    provider_name: str = ""
    model_name: str = ""
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TranslationProvider(ABC):
    """Translate text between languages."""

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> ProviderResponse:
        ...

    @abstractmethod
    def detect_language(self, text: str) -> str:
        ...


class SpeechToTextProvider(ABC):
    """Convert audio to text."""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, language: str = "hi") -> ProviderResponse:
        ...


class TextToSpeechProvider(ABC):
    """Convert text to audio (stretch goal)."""

    @abstractmethod
    def synthesize(self, text: str, language: str = "hi") -> ProviderResponse:
        ...


class VisionExtractionProvider(ABC):
    """Extract text/structure from images and PDFs."""

    @abstractmethod
    def extract_from_image(self, image_bytes: bytes) -> ProviderResponse:
        ...

    @abstractmethod
    def extract_from_pdf(self, pdf_bytes: bytes) -> ProviderResponse:
        ...


class EmbeddingProvider(ABC):
    """Generate text embeddings."""

    @abstractmethod
    def embed(self, texts: List[str]) -> ProviderResponse:
        ...

    @abstractmethod
    def embed_single(self, text: str) -> ProviderResponse:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...


class ReasoningProvider(ABC):
    """Generate reasoned responses from an LLM."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> ProviderResponse:
        ...

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        response_schema: Optional[Dict] = None,
    ) -> ProviderResponse:
        ...


def timed_call(func):
    """Decorator to measure provider call latency."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        if isinstance(result, ProviderResponse):
            result.latency_ms = elapsed
        logger.info(f"{func.__qualname__} completed in {elapsed:.1f}ms")
        return result
    return wrapper
