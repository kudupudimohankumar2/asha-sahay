"""Tests for RAG retrieval and grounding."""

import pytest
from services.retrieval_service import RetrievalService, FAISSRetriever


class TestRAGGrounding:
    def test_faiss_retriever_basic(self):
        retriever = FAISSRetriever(dimension=4)
        chunks = [
            {"chunk_id": "c1", "text": "Iron supplements during pregnancy"},
            {"chunk_id": "c2", "text": "Danger signs include bleeding"},
            {"chunk_id": "c3", "text": "ANC visits are important"},
        ]
        embeddings = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ]
        retriever.add_chunks(chunks, embeddings)
        results = retriever.search([1.0, 0.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0]["chunk_id"] == "c1"

    def test_retrieval_service_add_guideline(self):
        svc = RetrievalService()
        svc.add_guideline_chunk("test-chunk", "Test guideline about anemia", "Test Source", "nutrition")
        results = svc.retrieve("anemia guidance")
        assert "guideline_chunks" in results

    def test_retrieval_service_add_patient_memory(self):
        svc = RetrievalService()
        svc.add_patient_memory("p001", "Patient reported headache", "conversation", "2026-03-01")
        results = svc.retrieve("headache", patient_id="p001")
        assert "patient_chunks" in results

    def test_retrieval_returns_scores(self):
        retriever = FAISSRetriever(dimension=4)
        retriever.add_chunks(
            [{"chunk_id": "c1", "text": "test"}],
            [[1.0, 0.0, 0.0, 0.0]],
        )
        results = retriever.search([1.0, 0.0, 0.0, 0.0], top_k=1)
        assert "score" in results[0]
        assert results[0]["score"] > 0

    def test_empty_retriever_returns_empty(self):
        retriever = FAISSRetriever(dimension=4)
        results = retriever.search([1.0, 0.0, 0.0, 0.0], top_k=5)
        assert len(results) == 0

    def test_retrieval_includes_timing(self):
        svc = RetrievalService()
        svc.add_guideline_chunk("tc1", "Test content", "Source", "general")
        results = svc.retrieve("test query")
        assert "retrieval_time_ms" in results
        assert results["retrieval_time_ms"] >= 0
