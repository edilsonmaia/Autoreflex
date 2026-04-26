from __future__ import annotations

from typing import Iterable, List


def chunk_text(text: str, size: int, overlap: int) -> List[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    if size <= 0:
        return [cleaned]

    step = max(1, size - max(0, overlap))
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start += step
    return chunks


def first_non_empty_line(lines: Iterable[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped:
            return stripped
    return ""

