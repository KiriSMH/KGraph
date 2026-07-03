import re
from typing import Any

from app.services.data_service import load_graph


def _matches_query(node: dict[str, Any], query: str) -> bool:
    searchable = f"{node.get('id', '')} {node.get('label', '')}".casefold()
    normalized_query = query.casefold().strip()
    terms = [term for term in re.findall(r"[\w-]+", normalized_query) if len(term) > 2]
    return normalized_query in searchable or any(
        term in searchable or str(node.get("label", "")).casefold() in normalized_query
        for term in terms
    )


def get_subgraph(query: str) -> dict[str, list[dict[str, Any]]]:
    """Read a local subgraph. Replace this JSON traversal with a Neo4j query later."""
    graph = load_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    matched_ids = {node.get("id") for node in nodes if _matches_query(node, query)}

    if not matched_ids:
        return {"nodes": nodes[:8], "edges": edges[:10]}

    related_edges = [
        edge
        for edge in edges
        if edge.get("source") in matched_ids or edge.get("target") in matched_ids
    ]
    related_ids = matched_ids | {
        endpoint
        for edge in related_edges
        for endpoint in (edge.get("source"), edge.get("target"))
    }
    related_nodes = [node for node in nodes if node.get("id") in related_ids]
    return {"nodes": related_nodes, "edges": related_edges}
