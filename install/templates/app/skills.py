from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from app.config import settings
from app.embeddings import EmbeddingClient
from app.qdrant_service import SkillChunk, SkillStore
from app.text_processing import chunk_text, first_non_empty_line


def extract_skill_name(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def extract_skill_summary(text: str) -> str:
    lines = text.splitlines()
    summary = []
    in_body = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_body and summary:
                break
            continue
        if stripped.startswith("#"):
            continue
        in_body = True
        summary.append(stripped)
        if len(" ".join(summary)) > 220:
            break
    return " ".join(summary)[:280]


def _lighten_summary(summary: str, max_length: int = 180) -> str:
    compact = " ".join(summary.split())
    if len(compact) <= max_length:
        return compact
    return compact[: max_length - 3].rstrip() + "..."


class SkillService:
    def __init__(self) -> None:
        self.embedding_client = EmbeddingClient()
        self.store = SkillStore()

    def startup(self, progress_callback=None) -> None:
        self.embedding_client.startup(progress_callback=progress_callback)
        self.store.ensure_collection()
        if progress_callback is not None:
            progress_callback(88, "Coleção vetorial pronta para indexação e busca")

    def ensure_initial_skill_indexed(self) -> None:
        initial_skill = Path(settings.skills_dir) / "criar_novas_skills.md"
        if not initial_skill.exists():
            return
        self.index_skill_file(initial_skill)

    def build_chunks(self, skill_path: Path) -> list[SkillChunk]:
        content = skill_path.read_text(encoding="utf-8")
        skill_name = extract_skill_name(content, skill_path.stem)
        summary = extract_skill_summary(content)
        sha256 = self.store.file_hash(skill_path)
        pieces = chunk_text(content, settings.skills_chunk_size, settings.skills_chunk_overlap)
        total = len(pieces)
        chunks: list[SkillChunk] = []
        for index, piece in enumerate(pieces):
            chunks.append(
                SkillChunk(
                    skill_path=str(skill_path.relative_to(Path(settings.skills_dir))),
                    skill_name=skill_name,
                    summary=summary,
                    chunk_index=index,
                    chunk_total=total,
                    content=piece,
                    sha256=sha256,
                )
            )
        return chunks

    def resolve_skill_path(self, skill_path: str) -> Path:
        base = Path(settings.skills_dir).resolve()
        candidate = Path(skill_path)
        if candidate.is_absolute():
            full_path = candidate.resolve()
        else:
            parts = candidate.parts
            if parts and parts[0].lower() == base.name.lower():
                candidate = Path(*parts[1:])
            full_path = (base / candidate).resolve()
        if base not in full_path.parents and full_path != base:
            raise ValueError("Caminho inválido")
        return full_path

    def index_skill_file(self, skill_path: Path) -> int:
        if not skill_path.exists():
            raise FileNotFoundError(skill_path)
        self.embedding_client.startup()
        chunks = self.build_chunks(skill_path)
        if not chunks:
            return 0
        vectors = self.embedding_client.embed([chunk.content for chunk in chunks]).vectors
        return self.store.upsert_chunks(chunks, vectors)

    def index_all_skills(self) -> list[str]:
        indexed = []
        for skill_path in self.store.list_skill_files():
            self.index_skill_file(skill_path)
            indexed.append(str(skill_path))
        return indexed

    def search(self, query: str, limit: int = 5) -> list[dict]:
        self.embedding_client.startup()
        vector = self.embedding_client.embed([query]).vectors[0]
        search_limit = max(limit * 10, 50)
        results = self.store.search(vector, search_limit)
        payloads: list[dict] = []
        seen_paths: set[str] = set()
        for result in results:
            if result.score is None or float(result.score) < settings.skills_min_score:
                continue
            payload = result.payload or {}
            skill_path = payload.get("skill_path")
            if not skill_path or skill_path in seen_paths:
                continue
            seen_paths.add(skill_path)
            payloads.append(
                {
                    "score": result.score,
                    "skill_path": skill_path,
                    "skill_name": payload.get("skill_name"),
                    "summary": _lighten_summary(payload.get("summary") or ""),
                }
            )
            if len(payloads) >= limit:
                break
        return payloads

    def get_skill(self, skill_path: str) -> str:
        full_path = self.resolve_skill_path(skill_path)
        return full_path.read_text(encoding="utf-8")
