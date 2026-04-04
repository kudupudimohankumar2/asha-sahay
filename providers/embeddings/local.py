"""Local sentence-transformers embedding provider (CPU-friendly, multilingual)."""

import logging
from typing import List

from ..base import EmbeddingProvider, ProviderResponse, timed_call

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
DIMENSION = 384


class LocalEmbeddingProvider(EmbeddingProvider):
    """Uses sentence-transformers for local CPU-based multilingual embeddings.

    Default model (intfloat/multilingual-e5-small) supports 100+ languages
    including Hindi, Kannada, Telugu, Tamil, Bengali, Marathi, Gujarati,
    Malayalam, Punjabi, and Odia.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self._model_name = model_name
        self._model = None
        self._fallback = None

    def _load_model(self):
        if self._model is not None:
            return True
        if self._fallback is not None:
            return False
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info(f"Loaded embedding model: {self._model_name}")
            return True
        except ImportError:
            logger.warning("sentence-transformers not available, falling back to mock embeddings")
            from .mock import MockEmbeddingProvider
            self._fallback = MockEmbeddingProvider()
            return False
        except Exception as e:
            logger.warning(f"Failed to load {self._model_name}: {e}, falling back to mock")
            from .mock import MockEmbeddingProvider
            self._fallback = MockEmbeddingProvider()
            return False

    def _prepare_text(self, text: str) -> str:
        """Prepend query prefix required by E5 models."""
        if "e5" in self._model_name.lower():
            return f"query: {text}"
        return text

    @timed_call
    def embed(self, texts: List[str]) -> ProviderResponse:
        if not self._load_model():
            return self._fallback.embed(texts)
        prepared = [self._prepare_text(t) for t in texts]
        embeddings = self._model.encode(prepared, normalize_embeddings=True)
        return ProviderResponse(
            result=embeddings.tolist(),
            provider_name="local_embedding",
            model_name=self._model_name,
            metadata={"count": len(texts)},
        )

    @timed_call
    def embed_single(self, text: str) -> ProviderResponse:
        if not self._load_model():
            return self._fallback.embed_single(text)
        prepared = self._prepare_text(text)
        embedding = self._model.encode([prepared], normalize_embeddings=True)[0]
        return ProviderResponse(
            result=embedding.tolist(),
            provider_name="local_embedding",
            model_name=self._model_name,
        )

    @property
    def dimension(self) -> int:
        return DIMENSION
