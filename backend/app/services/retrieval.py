from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for partially installed envs
    def load_dotenv() -> bool:
        return False


UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"

KNOWN_MATERIALS = ["Ti-6Al-4V", "Al-6061", "Inconel 718", "Steel 09G2S", "09G2S"]
KNOWN_PROCESSES = ["закалка", "отжиг", "лазерная обработка", "прокатка"]
KNOWN_PROPERTIES = ["прочность", "пластичность", "твёрдость", "твердость", "коррозионная стойкость"]


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, based on the NLP participant module."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(cleaned):
        chunks.append(cleaned[start : start + chunk_size])
        start += step
    return chunks


class RetrievalIndex:
    """In-memory retrieval layer: OpenAI embeddings + Qdrant, with local fallback."""

    def __init__(self) -> None:
        self.collection_name = "scientific_papers"
        self.embedding_model = "text-embedding-3-small"
        self.vector_size = 1536
        self._client: Any | None = None
        self._point_struct: Any | None = None
        self._next_point_id = 1
        self._chunks: list[dict[str, Any]] = []
        self._indexed_files: dict[str, tuple[float, int]] = {}
        self._vector_ready = False
        self._vector_error: str | None = None
        self._uploads_scanned = False

    def index_existing_uploads(self) -> None:
        if self._uploads_scanned:
            return
        self._uploads_scanned = True

        if not UPLOAD_DIR.exists():
            return

        for path in UPLOAD_DIR.iterdir():
            if path.is_file() and path.name != ".gitkeep":
                self.index_file(path, path.name)

    def index_file(self, file_path: Path | str, original_name: str | None = None) -> dict[str, Any]:
        path = Path(file_path)
        name = original_name or path.name

        if not path.exists():
            return {"status": "error", "chunks": 0, "message": "Файл не найден."}

        fingerprint = (path.stat().st_mtime, path.stat().st_size)
        path_key = str(path.resolve())
        if self._indexed_files.get(path_key) == fingerprint:
            return {"status": "already_indexed", "chunks": 0, "message": "Файл уже был проиндексирован."}

        text, extraction_message = self._extract_text(path)
        chunks = chunk_text(text)
        if not chunks:
            return {
                "status": "saved_only",
                "chunks": 0,
                "message": extraction_message or "Не удалось извлечь текст для индексации.",
            }

        vector_client = self._ensure_vector_client()
        indexed_with_vectors = 0

        for index, chunk in enumerate(chunks, start=1):
            metadata = self._build_chunk_metadata(name, chunk, index)
            self._chunks.append(metadata)

            if vector_client:
                vector = self._get_embedding(chunk)
                if vector is None:
                    vector_client = None
                    continue

                self._upsert_vector(metadata, vector)
                indexed_with_vectors += 1

        self._indexed_files[path_key] = fingerprint

        if indexed_with_vectors:
            return {
                "status": "indexed",
                "chunks": len(chunks),
                "message": f"Индексировано через embeddings: {indexed_with_vectors} чанков.",
            }

        return {
            "status": "indexed_local",
            "chunks": len(chunks),
            "message": "Embeddings недоступны, включён локальный поиск по чанкам.",
        }

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        self.index_existing_uploads()

        normalized_query = query.strip()
        if not normalized_query or not self._chunks:
            return []

        if self._ensure_vector_client():
            vector = self._get_embedding(normalized_query)
            if vector is not None:
                results = self._search_vectors(vector, top_k)
                if results:
                    return results

        return self._search_locally(normalized_query, top_k)

    def status(self) -> dict[str, Any]:
        return {
            "chunks": len(self._chunks),
            "vector_ready": self._vector_ready,
            "vector_error": self._vector_error,
            "collection": self.collection_name,
        }

    def _ensure_vector_client(self) -> bool:
        if self._vector_ready and self._client is not None:
            return True
        if self._vector_error:
            return False

        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", self.embedding_model)
        if not api_key:
            self._vector_error = "OPENAI_API_KEY не задан."
            return False

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
        except ImportError as exc:
            self._vector_error = f"Не установлены зависимости Qdrant: {exc}"
            return False

        try:
            self._client = QdrantClient(":memory:")
            self._point_struct = PointStruct
            self._client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
        except Exception as exc:  # pragma: no cover - depends on optional Qdrant runtime
            self._vector_error = f"Qdrant недоступен: {exc}"
            self._client = None
            return False

        self._vector_ready = True
        return True

    def _get_embedding(self, text: str) -> list[float] | None:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(model=self.embedding_model, input=text)
            return list(response.data[0].embedding)
        except Exception:
            pass

        try:
            import openai

            openai.api_key = api_key
            response = openai.Embedding.create(input=[text], model=self.embedding_model)
            return list(response["data"][0]["embedding"])
        except Exception as exc:
            self._vector_error = f"OpenAI embeddings недоступны: {exc}"
            return None

    def _upsert_vector(self, metadata: dict[str, Any], vector: list[float]) -> None:
        if self._client is None or self._point_struct is None:
            return

        point_id = self._next_point_id
        self._next_point_id += 1
        metadata["point_id"] = point_id

        point = self._point_struct(id=point_id, vector=vector, payload=metadata)
        self._client.upsert(collection_name=self.collection_name, points=[point])

    def _search_vectors(self, vector: list[float], top_k: int) -> list[dict[str, Any]]:
        if self._client is None:
            return []

        try:
            hits = self._client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k,
            )
        except AttributeError:
            response = self._client.query_points(
                collection_name=self.collection_name,
                query=vector,
                limit=top_k,
            )
            hits = response.points
        except Exception:
            return []

        results: list[dict[str, Any]] = []
        for hit in hits:
            payload = dict(getattr(hit, "payload", {}) or {})
            score = int(round(float(getattr(hit, "score", 0.0) or 0.0) * 100))
            results.append(self._to_search_result(payload, max(score, 1)))
        return results

    def _search_locally(self, query: str, top_k: int) -> list[dict[str, Any]]:
        terms = [term for term in re.findall(r"[\w-]+", query.casefold()) if len(term) > 2]
        if not terms:
            return []

        scored: list[tuple[int, dict[str, Any]]] = []
        for chunk in self._chunks:
            haystack = f"{chunk.get('title', '')} {chunk.get('text', '')}".casefold()
            score = sum(2 if term in str(chunk.get("title", "")).casefold() else 0 for term in terms)
            score += sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._to_search_result(chunk, min(50 + score * 5, 99)) for score, chunk in scored[:top_k]]

    def _to_search_result(self, chunk: dict[str, Any], score: int) -> dict[str, Any]:
        text = str(chunk.get("text", ""))
        return {
            "document_id": str(chunk.get("document_id", "")),
            "title": str(chunk.get("title", "Загруженный документ")),
            "snippet": text[:250] + ("..." if len(text) > 250 else ""),
            "score": score,
            "year": None,
            "materials": list(chunk.get("materials", [])),
            "processes": list(chunk.get("processes", [])),
            "properties": list(chunk.get("properties", [])),
        }

    def _build_chunk_metadata(self, filename: str, chunk: str, index: int) -> dict[str, Any]:
        document_id = f"upload:{filename}:chunk:{index}"
        materials, processes, properties = _extract_known_terms(chunk)
        return {
            "document_id": document_id,
            "title": filename,
            "text": chunk,
            "chunk_index": index,
            "materials": materials,
            "processes": processes,
            "properties": properties,
        }

    def _extract_text(self, path: Path) -> tuple[str, str]:
        suffix = path.suffix.casefold()

        if suffix == ".pdf":
            return self._extract_pdf(path)
        if suffix == ".docx":
            return self._extract_docx(path)
        if suffix == ".json":
            return self._extract_json(path)
        if suffix in {".txt", ".md", ".csv"}:
            return self._read_text_file(path), ""

        return self._read_text_file(path), "Формат не распознан, файл прочитан как текст."

    def _extract_pdf(self, path: Path) -> tuple[str, str]:
        try:
            from pypdf import PdfReader
        except ImportError:
            return "", "Для PDF нужен пакет pypdf."

        try:
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            return "", f"Не удалось прочитать PDF: {exc}"

        return "\n".join(pages), ""

    def _extract_docx(self, path: Path) -> tuple[str, str]:
        try:
            from docx import Document
        except ImportError:
            return "", "Для DOCX нужен пакет python-docx."

        try:
            document = Document(str(path))
            paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        except Exception as exc:
            return "", f"Не удалось прочитать DOCX: {exc}"

        return "\n".join(paragraphs), ""

    def _extract_json(self, path: Path) -> tuple[str, str]:
        raw = self._read_text_file(path)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return raw, "JSON некорректный, файл прочитан как текст."
        return json.dumps(data, ensure_ascii=False, indent=2), ""

    def _read_text_file(self, path: Path) -> str:
        for encoding in ("utf-8", "utf-8-sig", "cp1251"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            except OSError:
                return ""
        return ""


def _extract_known_terms(text: str) -> tuple[list[str], list[str], list[str]]:
    normalized = text.casefold()
    materials = [item for item in KNOWN_MATERIALS if item.casefold() in normalized]
    processes = [item for item in KNOWN_PROCESSES if item.casefold() in normalized]
    properties = [item for item in KNOWN_PROPERTIES if item.casefold() in normalized]
    properties = ["твёрдость" if item == "твердость" else item for item in properties]
    return _unique(materials), _unique(processes), _unique(properties)


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
