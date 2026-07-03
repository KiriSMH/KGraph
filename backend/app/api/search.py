from fastapi import APIRouter

from app.schemas.requests import SearchRequest
from app.schemas.responses import SearchResponse
from app.services.search_service import search_documents


router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> dict:
    return {"results": search_documents(request.query)}
