"""Pipeline: ingest maternal-health guideline documents into the RAG index."""

import json
import logging
import os
from pathlib import Path
from typing import List

from models.common import new_id
from services.db import get_db
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

REFERENCE_DIR = Path(__file__).parent.parent / "data" / "sample_reference"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks by character count."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def ingest_reference_files():
    """Load all reference files from data/sample_reference into the RAG index."""
    db = get_db()
    retrieval = RetrievalService()

    if not REFERENCE_DIR.exists():
        logger.warning(f"Reference directory not found: {REFERENCE_DIR}")
        return

    files = list(REFERENCE_DIR.glob("*.md")) + list(REFERENCE_DIR.glob("*.txt"))
    logger.info(f"Found {len(files)} reference files to ingest")

    total_chunks = 0
    for filepath in files:
        source_name = filepath.stem.replace("_", " ").title()
        text = filepath.read_text(encoding="utf-8")
        category = _infer_category(filepath.stem)

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            chunk_id = new_id()
            guideline_id = new_id()

            db.insert("guidelines", {
                "guideline_id": guideline_id,
                "source_name": source_name,
                "category": category,
                "language": "en",
                "title": f"{source_name} - Part {i+1}",
                "chunk_text": chunk,
                "source_url": "",
                "effective_date": "2024-01-01",
            })

            retrieval.add_guideline_chunk(
                chunk_id=chunk_id,
                text=chunk,
                source=source_name,
                category=category,
            )
            total_chunks += 1

    logger.info(f"Ingested {total_chunks} guideline chunks from {len(files)} files")
    return total_chunks


def _infer_category(filename: str) -> str:
    mapping = {
        "anc": "antenatal_care",
        "danger": "danger_signs",
        "nutrition": "nutrition",
        "pmsma": "pmsma",
        "iron": "nutrition",
        "ifa": "nutrition",
        "schedule": "scheduling",
        "risk": "risk_assessment",
        "postpartum": "postnatal_care",
    }
    lower = filename.lower()
    for key, cat in mapping.items():
        if key in lower:
            return cat
    return "general"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_reference_files()
