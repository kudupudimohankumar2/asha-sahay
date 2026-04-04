"""Mock embedding provider for demo/testing."""

import hashlib
import numpy as np
from typing import List

from ..base import EmbeddingProvider, ProviderResponse, timed_call

DIMENSION = 384


class MockEmbeddingProvider(EmbeddingProvider):
    """Generates deterministic pseudo-embeddings from text hashes."""

    @timed_call
    def embed(self, texts: List[str]) -> ProviderResponse:
        embeddings = [self._hash_embed(t) for t in texts]
        return ProviderResponse(
            result=embeddings,
            provider_name="mock_embedding",
            metadata={"count": len(texts)},
        )

    @timed_call
    def embed_single(self, text: str) -> ProviderResponse:
        return ProviderResponse(
            result=self._hash_embed(text),
            provider_name="mock_embedding",
        )

    @property
    def dimension(self) -> int:
        return DIMENSION

    @staticmethod
    def _hash_embed(text: str) -> List[float]:
        h = hashlib.sha256(text.encode()).digest()
        rng = np.random.RandomState(int.from_bytes(h[:4], "big"))
        vec = rng.randn(DIMENSION).astype(np.float32)
        vec /= np.linalg.norm(vec)
        return vec.tolist()
