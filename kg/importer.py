import json
from pathlib import Path
from typing import Any

from kg.neo4j_client import Neo4jClient
from kg.resolver import normalize_relation_type, resolve_entity


ENTITY_LOOKUP_QUERY = """
MATCH (e:Entity)
WHERE e.uid = $ref
   OR e.id = $ref
   OR e.canonical_name = $canonical_ref
   OR $canonical_ref IN e.canonical_aliases
RETURN e.uid AS uid
LIMIT 1
"""


def import_json_file(client: Neo4jClient, json_path: str | Path) -> dict[str, int]:
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    imported_entities: dict[str, str] = {}
    stats = {
        "publications": 0,
        "entities": 0,
        "claims": 0,
        "relations": 0,
        "hypotheses": 0,
    }

    for source in _as_list(data.get("sources") or data.get("source")):
        entity = _source_to_publication(source)
        resolved = merge_entity(client, entity)
        _remember_entity(imported_entities, entity, resolved)
        stats["publications"] += 1

    for entity in data.get("entities", []):
        resolved = merge_entity(client, entity)
        _remember_entity(imported_entities, entity, resolved)
        stats["entities"] += 1

    for claim in data.get("claims", []):
        entity = dict(claim)
        entity["type"] = "Claim"
        resolved = merge_entity(client, entity)
        _remember_entity(imported_entities, entity, resolved)
        stats["claims"] += 1

    for relation in data.get("relations", []):
        merge_relation(client, relation, imported_entities)
        stats["relations"] += 1

    for hypothesis in data.get("hypotheses", []):
        relation = dict(hypothesis)
        relation["type"] = "HYPOTHESIZED_RELATED_TO"
        relation["evidence_type"] = "hypothesis"
        relation["visual_style"] = "dashed"
        relation.setdefault("confidence", 0.5)
        merge_relation(client, relation, imported_entities)
        stats["hypotheses"] += 1

    return stats


def merge_entity(client: Neo4jClient, entity: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_entity(entity)
    entity_type = resolved["type"]

    query = f"""
    MERGE (e:Entity:{entity_type} {{uid: $uid}})
    SET e += $properties
    RETURN e.uid AS uid
    """
    client.write(query, {"uid": resolved["uid"], "properties": resolved})
    return resolved


def merge_relation(
    client: Neo4jClient,
    relation: dict[str, Any],
    imported_entities: dict[str, str] | None = None,
) -> None:
    relation_type = normalize_relation_type(relation["type"])
    source_uid = resolve_entity_ref(client, relation["source"], imported_entities)
    target_uid = resolve_entity_ref(client, relation["target"], imported_entities)

    properties = {
        key: value
        for key, value in relation.items()
        if key not in {"source", "target", "type"}
    }

    if relation_type == "HYPOTHESIZED_RELATED_TO":
        properties["evidence_type"] = "hypothesis"
        properties["visual_style"] = "dashed"
        properties.setdefault("confidence", 0.5)
    else:
        properties.setdefault("evidence_type", "fact")
        properties.setdefault("visual_style", "solid")
        properties.setdefault("confidence", 1.0)

    query = f"""
    MATCH (source:Entity {{uid: $source_uid}})
    MATCH (target:Entity {{uid: $target_uid}})
    MERGE (source)-[r:{relation_type}]->(target)
    SET r += $properties
    """
    client.write(
        query,
        {
            "source_uid": source_uid,
            "target_uid": target_uid,
            "properties": properties,
        },
    )


def resolve_entity_ref(
    client: Neo4jClient,
    ref: str,
    imported_entities: dict[str, str] | None = None,
) -> str:
    if imported_entities and ref in imported_entities:
        return imported_entities[ref]

    pseudo_entity = {"type": "Material", "name": ref}
    canonical_ref = resolve_entity(pseudo_entity)["canonical_name"]
    rows = client.read(
        ENTITY_LOOKUP_QUERY,
        {
            "ref": ref,
            "canonical_ref": canonical_ref,
        },
    )

    if not rows:
        raise ValueError(f"Cannot resolve entity reference: {ref}")
    return rows[0]["uid"]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _source_to_publication(source: Any) -> dict[str, Any]:
    if isinstance(source, str):
        return {
            "id": source,
            "type": "Publication",
            "name": source,
        }

    entity = dict(source)
    entity["type"] = "Publication"
    entity.setdefault("id", entity.get("uid") or entity.get("name"))
    entity.setdefault("name", entity["id"])
    return entity


def _remember_entity(
    imported_entities: dict[str, str],
    original: dict[str, Any],
    resolved: dict[str, Any],
) -> None:
    for key in ("uid", "id", "name"):
        value = original.get(key) or resolved.get(key)
        if value:
            imported_entities[str(value)] = resolved["uid"]

    for alias in resolved.get("aliases", []):
        imported_entities[str(alias)] = resolved["uid"]

