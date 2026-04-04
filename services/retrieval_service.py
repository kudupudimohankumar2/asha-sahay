"""RAG retrieval service: Databricks Vector Search + FAISS fallback + patient memory."""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Any

import numpy as np

from models.common import new_id
from providers.config import get_embedding_provider
from services.db import get_db

logger = logging.getLogger(__name__)


# ── Retriever implementations ───────────────────────────────────────

class FAISSRetriever:
    """Local FAISS-based retriever for demo/testing fallback."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._index = None
        self._chunks: List[Dict[str, Any]] = []
        self._embeddings: List[List[float]] = []

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        self._chunks.extend(chunks)
        self._embeddings.extend(embeddings)
        self._rebuild_index()

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._chunks:
            return []

        try:
            import faiss
            if self._index is None:
                self._rebuild_index()
            query_vec = np.array([query_embedding], dtype=np.float32)
            distances, indices = self._index.search(query_vec, min(top_k, len(self._chunks)))
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self._chunks):
                    continue
                chunk = self._chunks[idx].copy()
                chunk["score"] = float(1 / (1 + dist))
                results.append(chunk)
            return results
        except ImportError:
            return self._cosine_search(query_embedding, top_k)

    def _rebuild_index(self):
        try:
            import faiss
            if not self._embeddings:
                return
            data = np.array(self._embeddings, dtype=np.float32)
            self._index = faiss.IndexFlatL2(self.dimension)
            self._index.add(data)
        except ImportError:
            pass

    def _cosine_search(self, query: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Fallback: pure numpy cosine similarity."""
        if not self._embeddings:
            return []
        q = np.array(query, dtype=np.float32)
        q /= np.linalg.norm(q) + 1e-10
        scores = []
        for i, emb in enumerate(self._embeddings):
            e = np.array(emb, dtype=np.float32)
            e /= np.linalg.norm(e) + 1e-10
            score = float(np.dot(q, e))
            scores.append((score, i))
        scores.sort(key=lambda x: -x[0])
        results = []
        for score, idx in scores[:top_k]:
            chunk = self._chunks[idx].copy()
            chunk["score"] = score
            results.append(chunk)
        return results


class DatabricksVSRetriever:
    """Retriever backed by Databricks Vector Search.

    Uses the VS SDK to query DELTA_SYNC indexes created by
    notebooks/create_vector_index.py.
    """

    def __init__(self, endpoint_name: str, index_name: str):
        self._endpoint = endpoint_name
        self._index_name = index_name
        self._vs_client = None
        self._index = None

    def _get_index(self):
        if self._index is not None:
            return self._index
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            self._index = w.vector_search_indexes.get_index(
                index_name=self._index_name,
            )
            logger.info(f"Connected to VS index: {self._index_name}")
            return self._index
        except Exception as e:
            logger.error(f"Failed to connect to VS index {self._index_name}: {e}")
            return None

    def search(self, query_text: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Query Databricks Vector Search using text (server-side embedding)."""
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            response = w.vector_search_indexes.query_index(
                index_name=self._index_name,
                columns=["chunk_id", "chunk_text", "source_name", "category"],
                query_text=query_text,
                num_results=top_k,
                filters_json=json.dumps(filters) if filters else None,
            )
            results = []
            if response and hasattr(response, "result") and response.result:
                data_array = response.result.data_array or []
                columns = [c.name for c in (response.manifest.columns or [])]
                for row in data_array:
                    chunk = dict(zip(columns, row))
                    chunk["score"] = chunk.pop("score", 0.0) if "score" in chunk else 0.0
                    chunk["text"] = chunk.pop("chunk_text", "")
                    results.append(chunk)
            return results
        except Exception as e:
            logger.error(f"VS query failed: {e}")
            return []

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        logger.info("DatabricksVSRetriever: chunks are added via Delta table writes, not direct insertion")


# ── Main service ────────────────────────────────────────────────────

def _use_databricks_vs() -> bool:
    """Determine whether to use Databricks Vector Search or FAISS fallback."""
    return bool(os.getenv("DATABRICKS_HOST")) and os.getenv("USE_VECTOR_SEARCH", "").lower() in ("1", "true", "yes")


class RetrievalService:
    """Orchestrates retrieval from guideline and patient memory indices."""

    def __init__(self):
        self.db = get_db()
        self.embedding_provider = get_embedding_provider()
        self._use_vs = _use_databricks_vs()

        if self._use_vs:
            catalog = os.getenv("CATALOG_NAME", "asha_sahayak")
            endpoint = os.getenv("VS_ENDPOINT", "asha_vs_endpoint")
            self.guideline_retriever = DatabricksVSRetriever(
                endpoint_name=endpoint,
                index_name=f"{catalog}.serving.guideline_vs_index",
            )
            self.patient_retriever = DatabricksVSRetriever(
                endpoint_name=endpoint,
                index_name=f"{catalog}.serving.patient_memory_vs_index",
            )
            logger.info("Using Databricks Vector Search retrievers")
        else:
            self.guideline_retriever = FAISSRetriever(self.embedding_provider.dimension)
            self.patient_retriever = FAISSRetriever(self.embedding_provider.dimension)
            logger.info("Using FAISS local retrievers")

        self._initialized = False

    def initialize(self):
        """Load chunks from DB into local retrievers (FAISS path only)."""
        if self._initialized:
            return
        if self._use_vs:
            self._initialized = True
            return

        guideline_rows = self.db.fetch_all("SELECT * FROM guideline_chunks")
        if guideline_rows:
            chunks = [{"chunk_id": r["chunk_id"], "text": r["chunk_text"],
                        "source": r.get("source_name", ""), "category": r.get("category", "")}
                       for r in guideline_rows]
            embeddings = []
            for r in guideline_rows:
                emb = r.get("embedding", "")
                if isinstance(emb, str) and emb:
                    try:
                        embeddings.append(json.loads(emb))
                    except json.JSONDecodeError:
                        resp = self.embedding_provider.embed_single(r["chunk_text"])
                        embeddings.append(resp.result)
                else:
                    resp = self.embedding_provider.embed_single(r["chunk_text"])
                    embeddings.append(resp.result)
            self.guideline_retriever.add_chunks(chunks, embeddings)
            logger.info(f"Loaded {len(chunks)} guideline chunks into FAISS")

        patient_rows = self.db.fetch_all("SELECT * FROM patient_memory_chunks")
        if patient_rows:
            chunks = [{"chunk_id": r["chunk_id"], "text": r["chunk_text"],
                        "patient_id": r.get("patient_id", ""), "type": r.get("chunk_type", "")}
                       for r in patient_rows]
            embeddings = []
            for r in patient_rows:
                emb = r.get("embedding", "")
                if isinstance(emb, str) and emb:
                    try:
                        embeddings.append(json.loads(emb))
                    except json.JSONDecodeError:
                        resp = self.embedding_provider.embed_single(r["chunk_text"])
                        embeddings.append(resp.result)
                else:
                    resp = self.embedding_provider.embed_single(r["chunk_text"])
                    embeddings.append(resp.result)
            self.patient_retriever.add_chunks(chunks, embeddings)

        self._initialized = True

    def retrieve(
        self,
        query: str,
        patient_id: Optional[str] = None,
        top_k_guidelines: int = 5,
        top_k_patient: int = 3,
    ) -> Dict[str, Any]:
        """Retrieve relevant guideline and patient context for a query."""
        self.initialize()
        start = time.time()

        if self._use_vs:
            guideline_results = self.guideline_retriever.search(
                query_text=query, top_k=top_k_guidelines,
            )
            patient_results = []
            if patient_id:
                patient_results = self.patient_retriever.search(
                    query_text=query, top_k=top_k_patient,
                    filters={"patient_id": patient_id},
                )
        else:
            query_resp = self.embedding_provider.embed_single(query)
            query_embedding = query_resp.result
            guideline_results = self.guideline_retriever.search(query_embedding, top_k_guidelines)
            patient_results = []
            if patient_id:
                all_patient = self.patient_retriever.search(query_embedding, top_k_patient * 3)
                patient_results = [r for r in all_patient if r.get("patient_id") == patient_id][:top_k_patient]

        elapsed = (time.time() - start) * 1000
        self._log_retrieval(query, patient_id, guideline_results, patient_results, elapsed)

        return {
            "guideline_chunks": guideline_results,
            "patient_chunks": patient_results,
            "retrieval_time_ms": elapsed,
            "query": query,
        }

    def add_guideline_chunk(self, chunk_id: str, text: str, source: str, category: str):
        """Add a new guideline chunk to the index."""
        resp = self.embedding_provider.embed_single(text)
        embedding = resp.result

        if isinstance(self.guideline_retriever, FAISSRetriever):
            self.guideline_retriever.add_chunks(
                [{"chunk_id": chunk_id, "text": text, "source": source, "category": category}],
                [embedding],
            )

        self.db.insert("guideline_chunks", {
            "chunk_id": chunk_id,
            "guideline_id": chunk_id,
            "chunk_index": 0,
            "chunk_text": text,
            "source_name": source,
            "category": category,
            "embedding": json.dumps(embedding),
        })

    def add_patient_memory(self, patient_id: str, text: str, chunk_type: str, source_date: str):
        """Add patient conversation/observation memory."""
        resp = self.embedding_provider.embed_single(text)
        embedding = resp.result
        chunk_id = new_id()

        if isinstance(self.patient_retriever, FAISSRetriever):
            self.patient_retriever.add_chunks(
                [{"chunk_id": chunk_id, "text": text, "patient_id": patient_id, "type": chunk_type}],
                [embedding],
            )

        self.db.insert("patient_memory_chunks", {
            "chunk_id": chunk_id,
            "patient_id": patient_id,
            "chunk_type": chunk_type,
            "chunk_text": text,
            "source_date": source_date,
            "embedding": json.dumps(embedding),
        })

    def _log_retrieval(
        self, query: str, patient_id: Optional[str],
        guidelines: list, patient_chunks: list, elapsed: float,
    ):
        self.db.insert("audit_log", {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "action": "retrieval",
            "entity_type": "rag_query",
            "entity_id": patient_id or "global",
            "details": json.dumps({
                "query": query[:200],
                "guideline_count": len(guidelines),
                "patient_chunk_count": len(patient_chunks),
                "retrieval_time_ms": round(elapsed, 1),
                "backend": "databricks_vs" if self._use_vs else "faiss",
            }),
        })
