import os
import re
import socket
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.services.data_service import load_graph
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _matches_query(node: dict[str, Any], query: str) -> bool:
    searchable = f"{node.get('id', '')} {node.get('label', '')}".casefold()
    normalized_query = query.casefold().strip()
    terms = [term for term in re.findall(r"[\w-]+", normalized_query) if len(term) > 2]
    return normalized_query in searchable or any(
        term in searchable or str(node.get("label", "")).casefold() in normalized_query
        for term in terms
    )


def _get_mock_subgraph(query: str) -> dict[str, list[dict[str, Any]]]:
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


def _node_type(labels: list[str], properties: dict[str, Any]) -> str:
    if properties.get("type"):
        return str(properties["type"])
    for label in labels:
        if label != "Entity":
            return label
    return "Entity"


def _adapt_neo4j_subgraph(subgraph: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    element_to_uid: dict[str, str] = {}

    for node in subgraph.get("nodes", []):
        properties = node.get("properties", {})
        uid = node.get("uid") or properties.get("uid") or node.get("id") or properties.get("id")
        if not uid:
            continue

        element_id = node.get("element_id")
        if element_id:
            element_to_uid[str(element_id)] = str(uid)

        nodes.append(
            {
                "id": str(uid),
                "label": str(properties.get("name") or properties.get("canonical_name") or uid),
                "type": _node_type(node.get("labels", []), properties),
            }
        )

    edges: list[dict[str, Any]] = []
    known_node_ids = {node["id"] for node in nodes}
    for relationship in subgraph.get("relationships", []):
        source = (
            relationship.get("start_node_uid")
            or relationship.get("source_uid")
            or element_to_uid.get(str(relationship.get("start_node")))
        )
        target = (
            relationship.get("end_node_uid")
            or relationship.get("target_uid")
            or element_to_uid.get(str(relationship.get("end_node")))
        )
        if not source or not target:
            continue

        source = str(source)
        target = str(target)
        if source not in known_node_ids or target not in known_node_ids:
            continue

        properties = relationship.get("properties", {})
        edges.append(
            {
                "source": source,
                "target": target,
                "label": str(properties.get("effect") or relationship.get("type") or "RELATED_TO"),
            }
        )

    return {"nodes": nodes, "edges": edges}


def _find_neo4j_entity_name(client: Any, query: str) -> str | None:
    normalized_query = query.casefold().strip()
    if not normalized_query:
        return None

    cypher = """
    MATCH (e:Entity)
    WITH e,
         toLower(toString(coalesce(e.name, ""))) AS name,
         toLower(toString(coalesce(e.canonical_name, ""))) AS canonical_name,
         [alias IN coalesce(e.aliases, []) | toLower(toString(alias))] AS aliases,
         [alias IN coalesce(e.canonical_aliases, []) | toLower(toString(alias))] AS canonical_aliases
    WHERE (size(name) > 2 AND $query CONTAINS name)
       OR (size(canonical_name) > 2 AND $query CONTAINS canonical_name)
       OR any(alias IN aliases WHERE size(alias) > 2 AND $query CONTAINS alias)
       OR any(alias IN canonical_aliases WHERE size(alias) > 2 AND $query CONTAINS alias)
    RETURN coalesce(e.name, e.canonical_name, e.id, e.uid) AS entity_name,
           size(coalesce(e.name, e.canonical_name, e.id, e.uid)) AS score
    ORDER BY score DESC
    LIMIT 1
    """
    rows = client.read(cypher, {"query": normalized_query})
    if not rows:
        return None
    return rows[0].get("entity_name")


def _is_neo4j_reachable() -> bool:
    load_dotenv()
    load_dotenv(REPO_ROOT / ".env")

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    parsed = urlparse(uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 7687

    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def _get_neo4j_subgraph(query: str) -> dict[str, list[dict[str, Any]]]:
    if not _is_neo4j_reachable():
        raise ConnectionError("Neo4j is not reachable")

    from kg.neo4j_client import Neo4jClient
    from kg.queries import get_subgraph as get_kg_subgraph

    client = Neo4jClient()
    try:
        entity_name = _find_neo4j_entity_name(client, query) or query
        subgraph = get_kg_subgraph(client, entity_name)
    finally:
        client.close()

    adapted = _adapt_neo4j_subgraph(subgraph)
    if not adapted["nodes"]:
        raise ValueError(f"Neo4j has no entity for query: {query}")
    return adapted


def get_subgraph(query: str) -> dict[str, list[dict[str, Any]]]:
    """Read from Neo4j first and fall back to local mock graph data."""
    try:
        return _get_neo4j_subgraph(query)
    except Exception:
        return _get_mock_subgraph(query)
