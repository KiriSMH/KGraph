import re
import sys
from pathlib import Path
from typing import Any

from app.services.data_service import load_graph


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _matches_query(node: dict[str, Any], query: str) -> bool:
    searchable = f"{node.get('id', '')} {node.get('label', '')}".casefold()
    normalized_query = query.casefold().strip()
    terms = [term for term in re.findall(r"[\w-]+", normalized_query) if len(term) > 2]
    return normalized_query in searchable or any(
        term in searchable or str(node.get("label", "")).casefold() in normalized_query
        for term in terms
    )


def get_subgraph(query: str) -> dict[str, list[dict[str, Any]]]:
    """Return a graph for the UI, preferring Neo4j and falling back to mock JSON."""
    neo4j_graph = _get_neo4j_subgraph(query)
    if neo4j_graph["nodes"]:
        return neo4j_graph
    return _get_mock_subgraph(query)


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


def _get_neo4j_subgraph(query: str) -> dict[str, list[dict[str, Any]]]:
    try:
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        from kg.neo4j_client import Neo4jClient
        from kg.queries import get_subgraph as get_kg_subgraph

        client = Neo4jClient()
    except Exception:
        return {"nodes": [], "edges": []}

    try:
        entity_name = _find_neo4j_entity_name(client, query)
        if not entity_name:
            return {"nodes": [], "edges": []}

        graph = get_kg_subgraph(client, entity_name)
        return _adapt_neo4j_graph(graph)
    except Exception:
        return {"nodes": [], "edges": []}
    finally:
        try:
            client.close()
        except Exception:
            pass


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


def _adapt_neo4j_graph(graph: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    raw_nodes = graph.get("nodes", [])
    raw_relationships = graph.get("relationships", [])
    element_id_to_node_id: dict[str, str] = {}
    nodes: list[dict[str, Any]] = []

    for node in raw_nodes:
        properties = node.get("properties", {})
        node_id = str(
            node.get("uid")
            or properties.get("uid")
            or node.get("id")
            or properties.get("id")
            or node.get("element_id")
        )
        label = str(
            properties.get("name")
            or properties.get("label")
            or properties.get("canonical_name")
            or properties.get("id")
            or node_id
        )
        node_type = str(properties.get("type") or _first_domain_label(node.get("labels", [])))

        if node.get("element_id"):
            element_id_to_node_id[str(node["element_id"])] = node_id

        nodes.append({"id": node_id, "label": label, "type": node_type})

    edges: list[dict[str, Any]] = []
    for relationship in raw_relationships:
        source = (
            relationship.get("source_uid")
            or element_id_to_node_id.get(str(relationship.get("start_node")))
        )
        target = (
            relationship.get("target_uid")
            or element_id_to_node_id.get(str(relationship.get("end_node")))
        )
        if not source or not target:
            continue

        edges.append(
            {
                "source": str(source),
                "target": str(target),
                "label": str(relationship.get("type", "RELATED_TO")),
            }
        )

    return {"nodes": nodes, "edges": edges}


def _first_domain_label(labels: list[str]) -> str:
    for label in labels:
        if label != "Entity":
            return label
    return "Entity"
