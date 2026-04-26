from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.config import sync_agents_file, sync_readme_file
from app.logging_utils import setup_logging
from app.qdrant_bootstrap import ensure_qdrant_runtime, stop_qdrant_runtime
from app.schemas import (
    SkillGetRequest,
    SkillGetResponse,
    SkillIndexRequest,
    SkillIndexResponse,
    SkillSearchItem,
    SkillSearchRequest,
    SkillSearchResponse,
)
from app.skills import SkillService


app = FastAPI(title="Autoreflex")
skill_service = SkillService()
logger = setup_logging("runtime")


def _progress(percent: int, message: str) -> None:
    logger.info("[%3d%%] %s", percent, message)


@app.exception_handler(Exception)
def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def startup() -> None:
    sync_agents_file()
    sync_readme_file()
    ensure_qdrant_runtime()
    try:
        _progress(1, "Iniciando carregamento do modelo local de embeddings")
        skill_service.startup(progress_callback=_progress)
        _progress(90, "Indexando a skill base inicial para habilitar buscas")
        skill_service.ensure_initial_skill_indexed()
        _progress(100, "Servidor pronto para uso")
    except Exception:
        logger.exception("Falha na inicialização do runtime")
        stop_qdrant_runtime()
        raise


@app.on_event("shutdown")
def shutdown() -> None:
    stop_qdrant_runtime()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent/skills/index", response_model=SkillIndexResponse)
def index_skills(request: SkillIndexRequest) -> SkillIndexResponse:
    if request.skill_path:
        skill_path = skill_service.resolve_skill_path(request.skill_path)
        if not skill_path.exists():
            raise HTTPException(status_code=404, detail="Skill não encontrada")
        indexed_chunks = skill_service.index_skill_file(skill_path)
        return SkillIndexResponse(indexed_files=[str(skill_path)], indexed_chunks=indexed_chunks)

    indexed_files = skill_service.index_all_skills()
    return SkillIndexResponse(indexed_files=indexed_files, indexed_chunks=len(indexed_files))


@app.post("/agent/skills/search", response_model=SkillSearchResponse, response_model_exclude_none=True)
def search_skills(request: SkillSearchRequest) -> SkillSearchResponse:
    results = skill_service.search(request.query, request.limit)
    return SkillSearchResponse(results=[SkillSearchItem(**item) for item in results])


@app.post("/agent/skills/get", response_model=SkillGetResponse)
def get_skill(request: SkillGetRequest) -> SkillGetResponse:
    try:
        content = skill_service.get_skill(request.skill_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Skill não encontrada") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SkillGetResponse(skill_path=request.skill_path, content=content)
