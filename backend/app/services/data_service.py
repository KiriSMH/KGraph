import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[3] / "data"


def _load_json(filename: str, fallback: Any) -> Any:
    path = DATA_DIR / filename
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback


def load_documents() -> list[dict[str, Any]]:
    data = _load_json("documents.json", [])
    return data if isinstance(data, list) else []


def load_graph() -> dict[str, list[dict[str, Any]]]:
    data = _load_json("graph.json", {})
    if not isinstance(data, dict):
        return {}
    return {
        "nodes": data.get("nodes", []) if isinstance(data.get("nodes", []), list) else [],
        "edges": data.get("edges", []) if isinstance(data.get("edges", []), list) else [],
    }


def load_hypotheses() -> list[dict[str, Any]]:
    data = _load_json("hypotheses.json", [])
    return data if isinstance(data, list) else []
