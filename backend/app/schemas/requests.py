from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)


class GraphRequest(BaseModel):
    query: str = Field(min_length=1)


class HypothesesRequest(BaseModel):
    material: str = ""
    property: str = ""


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
