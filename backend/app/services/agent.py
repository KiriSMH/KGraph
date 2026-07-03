from typing import Any

from app.services.agent_service import generate_agent_response


def chat(query: str) -> dict[str, Any]:
    """Stable integration point for the product agent."""
    return generate_agent_response(query)
