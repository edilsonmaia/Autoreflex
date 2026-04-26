from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import cast

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


def _load_install_config() -> ModuleType:
    config_path = BASE_DIR / "install" / "config.py"
    spec = importlib.util.spec_from_file_location("_costafavero_install_config", config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar {config_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_install_config = _load_install_config()
Settings = cast(type, _install_config.Settings)
settings = _install_config.settings


def persist_env_value(key: str, value: str) -> None:
    env_path = BASE_DIR / ".env"
    line_prefix = f"{key}="
    replacement = f"{line_prefix}{value}"

    lines: list[str]
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    updated = False
    for index, line in enumerate(lines):
        if line.startswith(line_prefix):
            lines[index] = replacement
            updated = True
            break

    if not updated:
        lines.append(replacement)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value


def sync_agents_file() -> None:
    template_path = BASE_DIR / "install" / "templates" / "root" / "agents.md"
    agents_path = BASE_DIR / "agents.md"
    if not template_path.exists():
        return

    content = template_path.read_text(encoding="utf-8")
    server_address = f"http://{settings.uvicorn_host}:{settings.uvicorn_port}"
    content = content.replace("{{SERVER_ADDRESS}}", server_address)
    content = content.replace("{{SKILLS_SEARCH_URL}}", f"{server_address}/agent/skills/search")
    content = content.replace("{{SKILLS_GET_URL}}", f"{server_address}/agent/skills/get")
    content = content.replace("{{SKILLS_DIR}}", settings.skills_dir)
    content = content.replace("{{QDRANT_URL}}", settings.qdrant_url)
    content = content.replace("{{LLM_URL}}", settings.llm_url)
    content = content.replace("{{EMBEDDING_MODEL_PATH}}", settings.embedding_model_path)
    agents_path.write_text(content, encoding="utf-8")


def sync_readme_file() -> None:
    template_path = BASE_DIR / "install" / "templates" / "root" / "README.md"
    readme_path = BASE_DIR / "README.md"
    if not template_path.exists():
        return

    content = template_path.read_text(encoding="utf-8")
    server_address = f"http://{settings.uvicorn_host}:{settings.uvicorn_port}"
    content = content.replace("{{SERVER_ADDRESS}}", server_address)
    content = content.replace("{{SKILLS_SEARCH_URL}}", f"{server_address}/agent/skills/search")
    content = content.replace("{{SKILLS_GET_URL}}", f"{server_address}/agent/skills/get")
    content = content.replace("{{QDRANT_URL}}", settings.qdrant_url)
    content = content.replace("{{EMBEDDING_MODEL_PATH}}", settings.embedding_model_path)
    readme_path.write_text(content, encoding="utf-8")
