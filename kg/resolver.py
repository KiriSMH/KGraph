import hashlib
import re
from typing import Any


ENTITY_TYPES = {
    "Material",
    "Process",
    "Equipment",
    "Property",
    "Parameter",
    "Experiment",
    "Publication",
    "Expert",
    "Facility",
    "Claim",
}

RELATION_TYPES = {
    "USES_MATERIAL",
    "OPERATES_AT_CONDITION",
    "PRODUCES_OUTPUT",
    "DESCRIBED_IN",
    "VALIDATED_BY",
    "CONTRADICTS",
    "AUTHORED_BY",
    "WORKS_AT",
    "EXPERT_IN",
    "HYPOTHESIZED_RELATED_TO",
}

SYNONYMS = {
    "никель": "nickel",
    "ni": "nickel",
    "nickel": "nickel",
    "медь": "copper",
    "cu": "copper",
    "copper": "copper",
    "электроэкстракция": "electrowinning",
    "электровыделение": "electrowinning",
    "electrowinning": "electrowinning",
    "пвп": "fluidized bed furnace",
    "печь взвешенной плавки": "fluidized bed furnace",
    "fluidized bed furnace": "fluidized bed furnace",
    "вещество б": "material_b",
    "б": "material_b",
    "material b": "material_b",
    "material_b": "material_b",
    "вещество бб": "material_bb",
    "бб": "material_bb",
    "material bb": "material_bb",
    "material_bb": "material_bb",
    "свойство q": "property_q",
    "q": "property_q",
    "property q": "property_q",
    "property_q": "property_q",
    "режим x": "condition_x",
    "x": "condition_x",
    "condition x": "condition_x",
    "condition_x": "condition_x",
    "режим y": "condition_y",
    "y": "condition_y",
    "condition y": "condition_y",
    "condition_y": "condition_y",
    "ti-6al-4v": "ti-6al-4v",
    "ti 6al 4v": "ti-6al-4v",
    "ti64": "ti-6al-4v",
    "титан ti-6al-4v": "ti-6al-4v",
    "прочность": "strength",
    "strength": "strength",
    "пластичность": "ductility",
    "ductility": "ductility",
    "закалка": "quenching",
    "quenching": "quenching",
}

DEDUP_BY_CANONICAL_NAME = {
    "Material",
    "Process",
    "Equipment",
    "Property",
    "Parameter",
    "Expert",
    "Facility",
}

DEDUP_BY_ID = {"Experiment", "Publication", "Claim"}


def normalize_text(value: Any) -> str:
    """Normalize text for matching while preserving Unicode letters."""
    if value is None:
        return ""
    normalized = str(value).strip().lower().replace("ё", "е")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def normalize_name(name: str) -> str:
    normalized = normalize_text(name)
    if normalized in SYNONYMS:
        return SYNONYMS[normalized]
    return re.sub(r"\s+", "_", normalized)


def normalize_entity_type(entity_type: str) -> str:
    normalized = str(entity_type).strip()
    for allowed_type in ENTITY_TYPES:
        if allowed_type.lower() == normalized.lower():
            return allowed_type
    raise ValueError(f"Unsupported entity type: {entity_type}")


def normalize_relation_type(relation_type: str) -> str:
    normalized = str(relation_type).strip().upper()
    if normalized not in RELATION_TYPES:
        raise ValueError(f"Unsupported relation type: {relation_type}")
    return normalized


def _canonical_aliases(name: str, aliases: list[str]) -> list[str]:
    values = {normalize_name(name)}
    values.update(normalize_name(alias) for alias in aliases)
    return sorted(value for value in values if value)


def make_uid(entity: dict[str, Any]) -> str:
    entity_type = normalize_entity_type(entity["type"])
    entity_id = str(entity.get("id") or entity.get("uid") or "").strip()
    canonical_name = normalize_name(entity.get("name") or entity_id)

    if entity_type in DEDUP_BY_ID:
        base = entity_id or f"{entity_type}:{canonical_name}"
    else:
        base = canonical_name

    if not base:
        raise ValueError(f"Cannot build uid for entity without id/name: {entity}")

    safe_base = re.sub(r"[^0-9a-zA-Z_:-]+", "_", base).strip("_")
    if not safe_base:
        safe_base = hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]
    return f"{entity_type.lower()}:{safe_base}"


def resolve_entity(entity: dict[str, Any]) -> dict[str, Any]:
    entity_type = normalize_entity_type(entity["type"])
    entity_id = str(entity.get("id") or entity.get("uid") or "").strip()
    name = str(entity.get("name") or entity_id).strip()
    aliases = entity.get("aliases") or []

    if isinstance(aliases, str):
        aliases = [aliases]

    if not name:
        raise ValueError(f"Entity must have name, id, or uid: {entity}")

    canonical_name = normalize_name(name)
    canonical_aliases = _canonical_aliases(name, aliases)
    resolved = dict(entity)
    resolved["id"] = entity_id or make_uid({"type": entity_type, "name": name})
    resolved["type"] = entity_type
    resolved["name"] = name
    resolved["canonical_name"] = canonical_name
    resolved["aliases"] = aliases
    resolved["canonical_aliases"] = canonical_aliases
    resolved["uid"] = make_uid(resolved)
    return resolved
