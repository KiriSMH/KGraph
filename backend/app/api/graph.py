from fastapi import APIRouter

from app.schemas.requests import GraphRequest
from app.schemas.responses import GraphResponse
from app.services.graph_service import get_subgraph


router = APIRouter(tags=["graph"])


@router.post("/graph", response_model=GraphResponse)
def graph(request: GraphRequest) -> dict:
    return get_subgraph(request.query)
