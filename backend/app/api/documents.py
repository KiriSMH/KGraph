from fastapi import APIRouter

from app.schemas.responses import DocumentsResponse
from app.services.data_service import load_documents


router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=DocumentsResponse)
def get_documents() -> dict:
    return {"documents": load_documents()}
