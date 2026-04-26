from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, unquote_plus

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.config import settings
from app.logging_utils import setup_logging


app = FastAPI(title="Autoreflex Qdrant Runtime")
STORE_ROOT = Path(settings.qdrant_path)
COLLECTIONS_DIR = STORE_ROOT / "collections"
logger = setup_logging("qdrant")


def _response(result: Any, status: str = "ok", time: float = 0.0) -> dict[str, Any]:
    return {"time": time, "status": status, "result": result}


def _collection_file(collection_name: str) -> Path:
    return COLLECTIONS_DIR / f"{quote_plus(collection_name)}.json"


def _load_collection(collection_name: str) -> dict[str, Any]:
    path = _collection_file(collection_name)
    if not path.exists():
        raise FileNotFoundError(collection_name)
    return json.loads(path.read_text(encoding="utf-8"))


def _save_collection(data: dict[str, Any]) -> None:
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = _collection_file(data["name"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _collection_payload(data: dict[str, Any]) -> dict[str, Any]:
    vector_size = data.get("vector_size", 0)
    vector_config = data.get("vectors_config")
    if vector_config is None:
        vector_config = {"size": vector_size, "distance": data.get("distance", "Cosine")}
    return {
        "status": "green",
        "optimizer_status": "ok",
        "vectors_count": len(data.get("points", [])),
        "indexed_vectors_count": len(data.get("points", [])),
        "points_count": len(data.get("points", [])),
        "segments_count": 1,
        "config": {
            "params": {
                "vectors": vector_config,
                "shard_number": 1,
                "replication_factor": 1,
                "write_consistency_factor": 1,
                "on_disk_payload": False,
                "sparse_vectors": None,
            },
            "hnsw_config": {
                "m": 16,
                "ef_construct": 100,
                "full_scan_threshold": 10000,
                "max_indexing_threads": 0,
                "on_disk": False,
                "payload_m": None,
            },
            "optimizer_config": {
                "deleted_threshold": 0.2,
                "vacuum_min_vector_number": 1000,
                "default_segment_number": 1,
                "max_segment_size": None,
                "memmap_threshold": None,
                "indexing_threshold": None,
                "flush_interval_sec": 5,
                "max_optimization_threads": None,
            },
            "wal_config": {
                "wal_capacity_mb": 32,
                "wal_segments_ahead": 0,
            },
            "quantization_config": None,
        },
        "payload_schema": {},
    }


def _vector_to_list(value: Any) -> list[float]:
    if isinstance(value, list):
        if value and isinstance(value[0], (int, float)):
            return [float(item) for item in value]
        if value and isinstance(value[0], list):
            return [float(item) for item in value[0]]
    if isinstance(value, dict):
        for key in ("vector", "values"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [float(item) for item in nested]
        if value:
            first = next(iter(value.values()))
            return _vector_to_list(first)
    return []


def _point_vector(point: dict[str, Any]) -> list[float]:
    return _vector_to_list(point.get("vector"))


def _cosine_score(query: list[float], vector: list[float]) -> float:
    if not query or not vector:
        return 0.0
    length = min(len(query), len(vector))
    query = query[:length]
    vector = vector[:length]
    dot = sum(a * b for a, b in zip(query, vector))
    query_norm = math.sqrt(sum(a * a for a in query))
    vector_norm = math.sqrt(sum(b * b for b in vector))
    if query_norm == 0.0 or vector_norm == 0.0:
        return 0.0
    return dot / (query_norm * vector_norm)


def _ensure_store() -> None:
    COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)


@app.exception_handler(Exception)
def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/collections")
def get_collections() -> dict[str, Any]:
    _ensure_store()
    collections = []
    for path in sorted(COLLECTIONS_DIR.glob("*.json")):
        collections.append({"name": unquote_plus(path.stem)})
    return _response({"collections": collections})


@app.get("/collections/{collection_name}")
def get_collection(collection_name: str) -> dict[str, Any]:
    try:
        data = _load_collection(collection_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collection not found") from exc
    return _response(_collection_payload(data))


@app.put("/collections/{collection_name}")
def create_collection(collection_name: str, body: dict[str, Any]) -> dict[str, Any]:
    vectors = body.get("vectors")
    if vectors is None:
        raise HTTPException(status_code=400, detail="Campo 'vectors' ausente ou inválido")
    data = {
        "name": collection_name,
        "vectors_config": vectors,
        "vector_size": _extract_vector_size(vectors),
        "distance": _extract_distance(vectors),
        "points": [],
    }
    _save_collection(data)
    return _response(True)


@app.put("/collections/{collection_name}/points")
def upsert_points(collection_name: str, body: dict[str, Any]) -> dict[str, Any]:
    try:
        data = _load_collection(collection_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Collection not found")

    points = body.get("points")
    if points is None and isinstance(body.get("batch"), dict):
        batch = body["batch"]
        ids = batch.get("ids", [])
        vectors = batch.get("vectors", [])
        payloads = batch.get("payloads")
        points = []
        for index, point_id in enumerate(ids):
            point: dict[str, Any] = {
                "id": point_id,
                "vector": vectors[index] if index < len(vectors) else [],
                "payload": payloads[index] if payloads is not None and index < len(payloads) else None,
            }
            points.append(point)
    if points is None:
        points = []

    existing = {str(point["id"]): point for point in data.get("points", [])}
    for point in points:
        point_id = str(point.get("id"))
        existing[point_id] = {
            "id": point.get("id"),
            "vector": point.get("vector"),
            "payload": point.get("payload"),
        }
    data["points"] = list(existing.values())
    _save_collection(data)
    return _response({"status": "acknowledged", "operation_id": 1})


@app.post("/collections/{collection_name}/points/search")
def search_points(collection_name: str, body: dict[str, Any]) -> dict[str, Any]:
    try:
        data = _load_collection(collection_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collection not found") from exc

    vector = body.get("vector")
    if vector is None:
        vector = body.get("query_vector")
    if vector is None:
        raise HTTPException(status_code=400, detail="Campo 'vector' ausente")
    query = _vector_to_list(vector)
    limit = int(body.get("limit", 10))

    results = []
    for point in data.get("points", []):
        point_vector = _point_vector(point)
        score = _cosine_score(query, point_vector)
        results.append(
            {
                "id": point.get("id"),
                "version": 0,
                "score": score,
                "payload": point.get("payload"),
                "vector": None,
                "shard_key": None,
                "order_value": None,
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return _response(results[:limit])


def _extract_vector_size(vectors: Any) -> int:
    if isinstance(vectors, dict) and "size" in vectors:
        return int(vectors["size"])
    if isinstance(vectors, dict):
        for value in vectors.values():
            if isinstance(value, dict) and "size" in value:
                return int(value["size"])
    return 0


def _extract_distance(vectors: Any) -> str:
    if isinstance(vectors, dict) and "distance" in vectors:
        return str(vectors["distance"])
    if isinstance(vectors, dict):
        for value in vectors.values():
            if isinstance(value, dict) and "distance" in value:
                return str(value["distance"])
    return "Cosine"
