from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for partially installed envs
    def load_dotenv() -> bool:
        return False


UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"
YANDEX_EMBEDDING_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
DEFAULT_YANDEX_DOC_EMBEDDING_MODEL = "text-search-doc/latest"
DEFAULT_YANDEX_QUERY_EMBEDDING_MODEL = "text-search-query/latest"

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
    """In-memory retrieval layer: Yandex embeddings + Qdrant, with local fallback."""

    def __init__(self) -> None:
        self.collection_name = "scientific_papers"
        self.doc_embedding_model = DEFAULT_YANDEX_DOC_EMBEDDING_MODEL
        self.query_embedding_model = DEFAULT_YANDEX_QUERY_EMBEDDING_MODEL
        self.vector_size = 0
        self._client: Any | None = None
        self._distance: Any | None = None
        self._vector_params: Any | None = None
        self._point_struct: Any | None = None
        self._next_point_id = 1
        self._chunks: list[dict[str, Any]] = []
        self._indexed_files: dict[str, tuple[float, int]] = {}
        self._vector_ready = False
        self._collection_ready = False
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
                vector = self._get_embedding(chunk, purpose="document")
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
            "message": "Yandex embeddings недоступны, включён локальный поиск по чанкам.",
        }

    def semantic_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        self.index_existing_uploads()

        normalized_query = query.strip()
        if not normalized_query or not self._chunks:
            return []

        if self._ensure_vector_client():
            vector = self._get_embedding(normalized_query, purpose="query")
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
            "provider": "yandex",
        }

    def _ensure_vector_client(self) -> bool:
        if self._client is not None:
            return True

        load_dotenv()

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct
        except ImportError as exc:
            self._vector_error = f"Не установлены зависимости Qdrant: {exc}"
            return False

        try:
            self._client = QdrantClient(":memory:")
            self._distance = Distance
            self._vector_params = VectorParams
            self._point_struct = PointStruct
        except Exception as exc:  # pragma: no cover - depends on optional Qdrant runtime
            self._vector_error = f"Qdrant недоступен: {exc}"
            self._client = None
            return False

        return True

    def _get_embedding(self, text: str, purpose: str) -> list[float] | None:
        load_dotenv()
        api_key = os.getenv("YANDEX_API_KEY")
        folder_id = os.getenv("YANDEX_FOLDER_ID")
        if not api_key or not folder_id:
            self._vector_error = "YANDEX_API_KEY или YANDEX_FOLDER_ID не заданы."
            return None

        self.doc_embedding_model = os.getenv(
            "YANDEX_EMBEDDING_DOC_MODEL",
            self.doc_embedding_model,
        )
        self.query_embedding_model = os.getenv(
            "YANDEX_EMBEDDING_QUERY_MODEL",
            self.query_embedding_model,
        )
        model_name = self.query_embedding_model if purpose == "query" else self.doc_embedding_model
        model_uri = _build_yandex_embedding_model_uri(folder_id, model_name)

        payload = {
            "modelUri": model_uri,
            "text": text,
        }
        request = urllib.request.Request(
            YANDEX_EMBEDDING_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Api-Key {api_key}",
                "Content-Type": "application/json",
                "x-folder-id": folder_id,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            self._vector_error = f"Yandex embeddings вернули HTTP {exc.code}."
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self._vector_error = f"Yandex embeddings недоступны: {exc}"
            return None

        embedding = data.get("embedding") or data.get("result", {}).get("embedding")
        if not isinstance(embedding, list) or not embedding:
            self._vector_error = "Yandex embeddings вернули пустой вектор."
            return None

        try:
            return [float(value) for value in embedding]
        except (TypeError, ValueError):
            self._vector_error = "Yandex embeddings вернули некорректный вектор."
            return None

    def _upsert_vector(self, metadata: dict[str, Any], vector: list[float]) -> None:
        if self._client is None or self._point_struct is None:
            return
        if not self._ensure_collection(len(vector)):
            return

        point_id = self._next_point_id
        self._next_point_id += 1
        metadata["point_id"] = point_id

        point = self._point_struct(id=point_id, vector=vector, payload=metadata)
        self._client.upsert(collection_name=self.collection_name, points=[point])

    def _ensure_collection(self, vector_size: int) -> bool:
        if self._client is None or self._distance is None or self._vector_params is None:
            return False

        if self._collection_ready:
            if vector_size != self.vector_size:
                self._vector_error = (
                    f"Размерность Yandex embeddings изменилась: {self.vector_size} -> {vector_size}."
                )
                return False
            return True

        try:
            self._client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=self._vector_params(size=vector_size, distance=self._distance.COSINE),
            )
        except Exception as exc:
            self._vector_error = f"Не удалось создать Qdrant collection: {exc}"
            return False

        self.vector_size = vector_size
        self._collection_ready = True
        self._vector_ready = True
        return True

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


def _build_yandex_embedding_model_uri(folder_id: str, model_name: str) -> str:
    if model_name.startswith("emb://"):
        return model_name
    return f"emb://{folder_id}/{model_name}"


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
