from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    title: str
    text: str
    materials: list[str] = Field(default_factory=list)
    processes: list[str] = Field(default_factory=list)
    properties: list[str] = Field(default_factory=list)
    year: int


class SearchResult(BaseModel):
    document_id: str
    title: str
    snippet: str
    score: int
    year: int | None = None
    materials: list[str] = Field(default_factory=list)
    processes: list[str] = Field(default_factory=list)
    properties: list[str] = Field(default_factory=list)


class Node(BaseModel):
    id: str
    label: str
    type: str


class Edge(BaseModel):
    source: str
    target: str
    label: str


class GraphResponse(BaseModel):
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class DocumentsResponse(BaseModel):
    documents: list[Document] = Field(default_factory=list)


class SearchResponse(BaseModel):
    results: list[SearchResult] = Field(default_factory=list)


class HypothesesResponse(BaseModel):
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    follow_up_questions: list[str] = Field(default_factory=list)
    documents: list[SearchResult] = Field(default_factory=list)
    graph: GraphResponse
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
