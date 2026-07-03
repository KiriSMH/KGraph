from pathlib import Path
from typing import Any

from app.services.retrieval import RetrievalIndex


_retrieval_index = RetrievalIndex()


def index_file(file_path: Path | str, original_name: str | None = None) -> dict[str, Any]:
    """Index an uploaded file for semantic search."""
    return _retrieval_index.index_file(file_path, original_name)


def semantic_search(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Search uploaded documents via embeddings/Qdrant, with local fallback."""
    return _retrieval_index.semantic_search(query, top_k=top_k)


def vector_status() -> dict[str, Any]:
    return _retrieval_index.status()
