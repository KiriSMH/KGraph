from fastapi import APIRouter

from app.schemas.requests import HypothesesRequest
from app.schemas.responses import HypothesesResponse
from app.services.data_service import load_hypotheses


router = APIRouter(tags=["hypotheses"])


@router.post("/hypotheses", response_model=HypothesesResponse)
def hypotheses(request: HypothesesRequest) -> dict:
    material = request.material.casefold().strip()
    property_name = request.property.casefold().strip()
    items = load_hypotheses()
    matches = [
        item
        for item in items
        if (material and material in str(item.get("material", "")).casefold())
        or (property_name and property_name in str(item.get("property", "")).casefold())
    ]
    return {"hypotheses": (matches or items[:3])}
