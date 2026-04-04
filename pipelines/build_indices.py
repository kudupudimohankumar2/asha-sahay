"""Pipeline: build or rebuild vector search indices."""

import logging
from services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


def build_indices():
    """Rebuild retrieval indices from database chunks."""
    logger.info("Building retrieval indices...")
    retrieval = RetrievalService()
    retrieval.initialize()
    logger.info("Indices built successfully")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_indices()
