import re
from typing import Any

from app.services.data_service import load_documents


def _query_terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[\w-]+", query.casefold()) if len(term) > 2]


def _contains_term(value: str, terms: list[str]) -> bool:
    normalized = value.casefold()
    return any(term in normalized for term in terms)


def search_documents(query: str) -> list[dict[str, Any]]:
    """Run mock keyword search. Replace this implementation with Qdrant/Chroma."""
    terms = _query_terms(query)
    if not terms:
        return []

    results: list[dict[str, Any]] = []
    for document in load_documents():
        title = str(document.get("title", ""))
        text = str(document.get("text", ""))
        metadata = " ".join(
            str(item)
            for field in ("materials", "processes", "properties")
            for item in document.get(field, [])
        )

        score = 0
        if _contains_term(title, terms):
            score += 2
        if _contains_term(text, terms):
            score += 1
        if _contains_term(metadata, terms):
            score += 1
        if score == 0:
            continue

        results.append(
            {
                "document_id": str(document.get("id", "")),
                "title": title,
                "snippet": text[:250] + ("..." if len(text) > 250 else ""),
                "score": score,
                "year": document.get("year"),
                "materials": document.get("materials", []),
                "processes": document.get("processes", []),
                "properties": document.get("properties", []),
            }
        )

    return sorted(results, key=lambda item: (-item["score"], -int(item.get("year") or 0)))[:5]
