from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Sequence

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings


@dataclass
class SkillChunk:
    skill_path: str
    skill_name: str
    summary: str
    chunk_index: int
    chunk_total: int
    content: str
    sha256: str


class SkillStore:
    def __init__(self) -> None:
        self.client = self._create_client()
        self.collection_name = f"{settings.skills_collection_prefix}_{settings.skills_collection_key}"

    def _create_client(self) -> QdrantClient:
        client_kwargs = {"url": settings.qdrant_url}
        if settings.qdrant_api_key:
            client_kwargs["api_key"] = settings.qdrant_api_key
        try:
            client = QdrantClient(**client_kwargs)
            client.get_collections()
            return client
        except Exception:
            local_path = Path(settings.qdrant_path)
            local_path.mkdir(parents=True, exist_ok=True)
            return QdrantClient(path=str(local_path))

    def ensure_collection(self) -> None:
        try:
            self.client.get_collection(self.collection_name)
            return
        except Exception:
            pass
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=settings.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_chunks(self, chunks: Sequence[SkillChunk], vectors: Sequence[Sequence[float]]) -> int:
        self.ensure_collection()
        points: List[models.PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chunk.skill_path}:{chunk.chunk_index}:{chunk.sha256}"))
            payload = {
                "skill_path": chunk.skill_path,
                "skill_name": chunk.skill_name,
                "summary": chunk.summary,
                "chunk_index": chunk.chunk_index,
                "chunk_total": chunk.chunk_total,
                "content": chunk.content,
                "sha256": chunk.sha256,
            }
            points.append(models.PointStruct(id=point_id, vector=list(vector), payload=payload))
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def search(self, vector: Sequence[float], limit: int) -> list[models.ScoredPoint]:
        self.ensure_collection()
        response = self._query_points(vector, limit)
        return self._normalize_search_results(response)

    def _query_points(self, vector: Sequence[float], limit: int) -> Any:
        if hasattr(self.client, "query_points"):
            return self.client.query_points(
                collection_name=self.collection_name,
                query=list(vector),
                limit=limit,
                with_payload=True,
            )
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=list(vector),
            limit=limit,
            with_payload=True,
        )

    @staticmethod
    def _normalize_search_results(response: Any) -> list[models.ScoredPoint]:
        if response is None:
            return []
        if isinstance(response, list):
            return response
        points = getattr(response, "points", None)
        if points is not None:
            return list(points)
        result = getattr(response, "result", None)
        if result is not None:
            return list(result)
        return list(response)

    def list_skill_files(self) -> list[Path]:
        root = Path(settings.skills_dir)
        if not root.exists():
            return []
        files = []
        for path in root.rglob("*.md"):
            if "documentos" in path.parts:
                continue
            files.append(path)
        return sorted(files)

    @staticmethod
    def file_hash(path: Path) -> str:
        digest = hashlib.sha256()
        digest.update(path.read_bytes())
        return digest.hexdigest()
