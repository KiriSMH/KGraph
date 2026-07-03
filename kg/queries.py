from typing import Any

from kg.neo4j_client import Neo4jClient
from kg.resolver import normalize_name


def get_subgraph(client: Neo4jClient, entity_name: str, depth: int = 2, limit: int = 50) -> dict[str, list[dict[str, Any]]]:
    depth = max(1, min(int(depth), 5))
    limit = max(1, int(limit))
    canonical_name = normalize_name(entity_name)

    query = f"""
    MATCH (root:Entity {{canonical_name: $canonical_name}})
    MATCH path = (root)-[*1..{depth}]-(neighbor:Entity)
    WITH path
    LIMIT $limit
    WITH collect(path) AS paths
    UNWIND paths AS path
    UNWIND nodes(path) AS node
    WITH paths, collect(DISTINCT node) AS nodes
    UNWIND paths AS path
    UNWIND relationships(path) AS relationship
    RETURN nodes, collect(DISTINCT relationship) AS relationships
    """

    rows = client.read(query, {"canonical_name": canonical_name, "limit": limit})
    if not rows:
        return {"nodes": [], "relationships": []}

    row = rows[0]
    return {
        "nodes": [_serialize_node(node) for node in row["nodes"]],
        "relationships": [_serialize_relationship(rel) for rel in row["relationships"]],
    }


def get_hypotheses(client: Neo4jClient, limit: int = 50) -> dict[str, list[dict[str, Any]]]:
    query = """
    MATCH (source:Entity)-[relationship:HYPOTHESIZED_RELATED_TO]->(target:Entity)
    RETURN source, relationship, target
    LIMIT $limit
    """
    rows = client.read(query, {"limit": max(1, int(limit))})

    nodes_by_uid = {}
    relationships = []
    for row in rows:
        source = row["source"]
        target = row["target"]
        relationship = row["relationship"]
        nodes_by_uid[source["uid"]] = _serialize_node(source)
        nodes_by_uid[target["uid"]] = _serialize_node(target)
        relationships.append(_serialize_relationship(relationship))

    return {
        "nodes": list(nodes_by_uid.values()),
        "relationships": relationships,
    }


def _serialize_node(node: Any) -> dict[str, Any]:
    properties = dict(node)
    return {
        "uid": properties.get("uid"),
        "id": properties.get("id"),
        "labels": list(node.labels),
        "properties": properties,
    }


def _serialize_relationship(relationship: Any) -> dict[str, Any]:
    return {
        "element_id": relationship.element_id,
        "type": relationship.type,
        "start_node": relationship.start_node.element_id,
        "end_node": relationship.end_node.element_id,
        "properties": dict(relationship),
    }
