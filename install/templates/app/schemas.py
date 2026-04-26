from __future__ import annotations

from pydantic import BaseModel, Field


class SkillIndexRequest(BaseModel):
    skill_path: str | None = None


class SkillIndexResponse(BaseModel):
    indexed_files: list[str] = Field(default_factory=list)
    indexed_chunks: int = 0


class SkillSearchRequest(BaseModel):
    query: str
    limit: int = 5


class SkillSearchItem(BaseModel):
    score: float
    skill_path: str | None = None
    skill_name: str | None = None
    summary: str | None = None


class SkillSearchResponse(BaseModel):
    results: list[SkillSearchItem] = Field(default_factory=list)


class SkillGetRequest(BaseModel):
    skill_path: str


class SkillGetResponse(BaseModel):
    skill_path: str
    content: str
