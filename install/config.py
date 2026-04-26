"""Configuração central do pacote de instalação Autoreflex."""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_HOST = os.getenv("AGENT_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("AGENT_PORT", "8090"))
DEFAULT_LLM_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8081")
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
DEFAULT_QDRANT_PATH = os.getenv("QDRANT_PATH", str(BASE_DIR / ".qdrant"))
DEFAULT_QDRANT_COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "org")
DEFAULT_QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
DEFAULT_VECTOR_SIZE = int(os.getenv("EMBEDDING_DIMENSION", "768"))
DEFAULT_DISTANCE = os.getenv("VECTOR_DISTANCE", "Cosine")

DEFAULT_SKILLS_DIR = os.getenv("SKILLS_DIR", str(BASE_DIR / "skills"))
DEFAULT_SKILLS_COLLECTION_PREFIX = os.getenv("SKILLS_COLLECTION_PREFIX", "skills")
DEFAULT_SKILLS_COLLECTION_KEY = os.getenv("SKILLS_COLLECTION_KEY", "global_default")

DEFAULT_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "google/embeddinggemma-300m")
DEFAULT_MODEL_REVISION = os.getenv("EMBEDDING_MODEL_REVISION", "main")
DEFAULT_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", str(BASE_DIR / "models" / "gemma"))
DEFAULT_MODEL_DOWNLOAD_URL = os.getenv(
    "EMBEDDING_MODEL_DOWNLOAD_URL",
    f"https://huggingface.co/{DEFAULT_MODEL_ID}/resolve/{DEFAULT_MODEL_REVISION}",
)
DEFAULT_MODEL_TOKEN = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
DEFAULT_MODEL_DEVICE = os.getenv("EMBEDDING_DEVICE", "auto")
DEFAULT_EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "torch")
DEFAULT_TARGET_ARCHITECTURE = os.getenv("TARGET_ARCHITECTURE", "auto")
DEFAULT_HF_HOME = os.getenv("HF_HOME", str(BASE_DIR / ".hf"))
DEFAULT_HF_HUB_CACHE = os.getenv("HUGGINGFACE_HUB_CACHE", str(BASE_DIR / ".hf" / "hub"))
DEFAULT_TRANSFORMERS_CACHE = os.getenv("TRANSFORMERS_CACHE", str(BASE_DIR / ".hf" / "transformers"))

DEFAULT_LOGS_DIR = os.getenv("LOGS_DIR", str(BASE_DIR / "logs"))
DEFAULT_MODELS_DIR = os.getenv("MODELS_DIR", str(BASE_DIR / "models"))


class Settings:
    """Carrega variáveis de ambiente com defaults seguros."""

    def __init__(self) -> None:
        self.host: str = DEFAULT_HOST
        self.port: int = DEFAULT_PORT

        self.llm_url: str = DEFAULT_LLM_URL
        self.qdrant_url: str = DEFAULT_QDRANT_URL
        self.qdrant_path: str = DEFAULT_QDRANT_PATH
        self.qdrant_api_key: Optional[str] = DEFAULT_QDRANT_API_KEY

        self.collection_prefix: str = DEFAULT_QDRANT_COLLECTION_PREFIX
        self.vector_size: int = DEFAULT_VECTOR_SIZE
        self.distance: str = DEFAULT_DISTANCE

        self.max_workers: int = int(os.getenv("LLM_MAX_WORKERS", "2"))
        self.queue_timeout: float = float(os.getenv("AGENT_QUEUE_TIMEOUT", "30"))
        self.request_timeout: float = float(os.getenv("AGENT_REQUEST_TIMEOUT", "300"))

        self.rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
        self.rate_limit_interval: timedelta = timedelta(
            seconds=float(os.getenv("RATE_LIMIT_INTERVAL_SECONDS", "60"))
        )
        self.skills_get_limit: int = int(os.getenv("SKILLS_GET_LIMIT", "3"))
        self.skills_get_interval: timedelta = timedelta(
            seconds=float(os.getenv("SKILLS_GET_INTERVAL_SECONDS", "60"))
        )

        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
        self.chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "80"))

        self.metrics_enabled: bool = os.getenv("ENABLE_METRICS", "1") == "1"
        self.request_logs_enabled: bool = os.getenv("ENABLE_REQUEST_LOGS", "0") == "1"
        # Score mínimo para considerar uma skill relevante.
        # O valor é um float comparado diretamente com o score de similaridade.
        # Mantemos 8 casas decimais no .env para preservar consistência na leitura e no ajuste fino.
        self.skills_min_score: float = float(os.getenv("SKILLS_MIN_SCORE", "0.65500000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        self.agenda_api_url: str = os.getenv("AGENDA_BASE_URL", "http://127.0.0.1:8001")
        self.agenda_api_key: Optional[str] = os.getenv("AGENDA_API_KEY")
        self.agenda_timeout: float = float(os.getenv("AGENDA_TIMEOUT", "5"))

        self.skills_dir: str = DEFAULT_SKILLS_DIR
        self.skills_collection_prefix: str = DEFAULT_SKILLS_COLLECTION_PREFIX
        self.skills_collection_key: str = DEFAULT_SKILLS_COLLECTION_KEY
        self.skills_embed_batch_size: int = int(os.getenv("SKILLS_EMBED_BATCH_SIZE", "1"))
        self.skills_chunk_size: int = int(os.getenv("SKILLS_CHUNK_SIZE", "150"))
        self.skills_chunk_overlap: int = int(os.getenv("SKILLS_CHUNK_OVERLAP", "20"))
        self.skills_chunk_max_chars: int = int(os.getenv("SKILLS_CHUNK_MAX_CHARS", "400"))
        self.skills_upsert_batch_size: int = int(os.getenv("SKILLS_UPSERT_BATCH_SIZE", "128"))

        self.embedding_model_path: str = DEFAULT_MODEL_PATH
        self.embedding_model_id: str = DEFAULT_MODEL_ID
        self.embedding_model_revision: str = DEFAULT_MODEL_REVISION
        self.embedding_model_url: str = DEFAULT_MODEL_DOWNLOAD_URL
        self.embedding_model_token: Optional[str] = DEFAULT_MODEL_TOKEN
        self.embedding_device: str = DEFAULT_MODEL_DEVICE
        self.embedding_backend: str = DEFAULT_EMBEDDING_BACKEND
        self.target_architecture: str = DEFAULT_TARGET_ARCHITECTURE

        self.models_dir: str = DEFAULT_MODELS_DIR
        self.logs_dir: str = DEFAULT_LOGS_DIR
        self.uvicorn_host: str = os.getenv("UVICORN_HOST", self.host)
        self.uvicorn_port: int = int(os.getenv("UVICORN_PORT", str(self.port)))
        self.uvicorn_reload: bool = os.getenv("UVICORN_RELOAD", "0") == "1"
        self.hf_home: str = DEFAULT_HF_HOME
        self.hf_hub_cache: str = DEFAULT_HF_HUB_CACHE
        self.transformers_cache: str = DEFAULT_TRANSFORMERS_CACHE

    def resolve_hf_token(self) -> Optional[str]:
        token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN") or self.embedding_model_token
        if token is None:
            return None
        token = token.strip()
        return token or None

    def build_env_template(self) -> str:
        return "\n".join(
            [
                f"AGENT_HOST={self.host}",
                f"AGENT_PORT={self.port}",
                f"UVICORN_HOST={self.uvicorn_host}",
                f"UVICORN_PORT={self.uvicorn_port}",
                f"UVICORN_RELOAD={'1' if self.uvicorn_reload else '0'}",
                f"LLM_BASE_URL={self.llm_url}",
                f"QDRANT_URL={self.qdrant_url}",
                f"QDRANT_PATH={self.qdrant_path}",
                f"QDRANT_API_KEY={self.qdrant_api_key or ''}",
                f"QDRANT_COLLECTION_PREFIX={self.collection_prefix}",
                f"EMBEDDING_DIMENSION={self.vector_size}",
                f"VECTOR_DISTANCE={self.distance}",
                f"AGENT_QUEUE_TIMEOUT={self.queue_timeout}",
                f"AGENT_REQUEST_TIMEOUT={self.request_timeout}",
                f"LLM_MAX_WORKERS={self.max_workers}",
                f"RATE_LIMIT_REQUESTS={self.rate_limit_requests}",
                f"RATE_LIMIT_INTERVAL_SECONDS={int(self.rate_limit_interval.total_seconds())}",
                f"SKILLS_GET_LIMIT={self.skills_get_limit}",
                f"SKILLS_GET_INTERVAL_SECONDS={int(self.skills_get_interval.total_seconds())}",
                f"CHUNK_SIZE={self.chunk_size}",
                f"CHUNK_OVERLAP={self.chunk_overlap}",
                f"SKILLS_DIR={self.skills_dir}",
                f"SKILLS_COLLECTION_PREFIX={self.skills_collection_prefix}",
                f"SKILLS_COLLECTION_KEY={self.skills_collection_key}",
                f"SKILLS_EMBED_BATCH_SIZE={self.skills_embed_batch_size}",
                f"SKILLS_CHUNK_SIZE={self.skills_chunk_size}",
                f"SKILLS_CHUNK_OVERLAP={self.skills_chunk_overlap}",
                f"SKILLS_CHUNK_MAX_CHARS={self.skills_chunk_max_chars}",
                f"SKILLS_UPSERT_BATCH_SIZE={self.skills_upsert_batch_size}",
                f"EMBEDDING_MODEL_ID={self.embedding_model_id}",
                f"EMBEDDING_MODEL_REVISION={self.embedding_model_revision}",
                f"EMBEDDING_MODEL_PATH={self.embedding_model_path}",
                f"EMBEDDING_MODEL_DOWNLOAD_URL={self.embedding_model_url}",
                f"HUGGINGFACE_TOKEN={self.embedding_model_token or ''}",
                f"HF_TOKEN={self.embedding_model_token or ''}",
                f"EMBEDDING_BACKEND={self.embedding_backend}",
                f"EMBEDDING_DEVICE={self.embedding_device}",
                f"TARGET_ARCHITECTURE={self.target_architecture}",
                f"HF_HOME={self.hf_home}",
                f"HUGGINGFACE_HUB_CACHE={self.hf_hub_cache}",
                f"TRANSFORMERS_CACHE={self.transformers_cache}",
                f"MODELS_DIR={self.models_dir}",
                f"LOGS_DIR={self.logs_dir}",
                f"ENABLE_METRICS={'1' if self.metrics_enabled else '0'}",
                f"ENABLE_REQUEST_LOGS={'1' if self.request_logs_enabled else '0'}",
                f"SKILLS_MIN_SCORE={self.skills_min_score:.8f}",
                f"LOG_LEVEL={self.log_level}",
                f"AGENDA_BASE_URL={self.agenda_api_url}",
                f"AGENDA_API_KEY={self.agenda_api_key or ''}",
                f"AGENDA_TIMEOUT={self.agenda_timeout}",
                "",
            ]
        )

    def build_agents_template(self) -> str:
        return "\n".join(
            [
                "# Memória operacional do projeto Autoreflex",
                "",
                "Este arquivo é criado pelo instalador e serve como instrução base do agente no repositório.",
                "",
                "## Servidor local para consultar habilidades para o agente",
                "- Endereço base: `{{SERVER_ADDRESS}}`",
                "- URL de pesquisa de skills: `{{SKILLS_SEARCH_URL}}`",
                "- Endpoint de skills: `{{SKILLS_SEARCH_URL}}`",
                "- Endpoint de leitura da skill completa: `{{SKILLS_GET_URL}}`",
                "",
                "## Ordem de decisão",
                "1. Usar a memória já presente na conversa.",
                "2. Se não houver resposta suficiente, consultar skills relevantes via endpoint.",
                "3. Se a skill apontar arquivo, função ou linha, seguir isso antes de abrir arquivos grandes.",
                "4. Só depois pesquisar o código do projeto.",
                "",
                "## Regra principal",
                "- Responder e consultar endpoints sempre na língua do usuário.",
                "- O agente deve consultar skills primeiro para economizar tokens.",
                "- A primeira skill a ler ao criar novas skills é a skill base de criação.",
                "- Termo inicial de busca: `criar novas skills`.",
                "- Sequência operacional: buscar -> ler skill completa -> criar nova skill -> indexar.",
                "- Depois da busca, se houver correspondência útil, ler a skill completa pelo endpoint de leitura.",
                "- Quando uma nova skill for salva, o agente deve chamar `POST /agent/skills/index`.",
                "- Toda skill nova deve ser criada com `skills/<nome>.md` e `skills/<nome>.meta.json`.",
                "- O metadata deve conter `name`, `title`, `summary`, `tags`, `language`, `source_skill_path`, `created_at`, `updated_at` e `version`.",
                "- Quando o metadata existir, use-o como atalho de classificação antes de ler a skill completa.",
                "",
            ]
        )

    def build_initial_skill_template(self) -> str:
        return "\n".join(
            [
                "# Criar novas skills",
                "",
                "## Objetivo",
                "Criar skills novas quando o problema for reutilizável e valha a pena ser consultado de novo.",
                "",
                "## Ordem de trabalho",
                "1. Use sua memória de contexto primeiro.",
                "2. Se não houver resposta suficiente, consulte `POST /agent/skills/search`.",
                "3. Se uma skill existente resolver, reutilize-a.",
                "4. Se não houver skill adequada, leia os arquivos necessários do projeto.",
                "5. Depois de resolver, crie uma nova skill em `skills/<nome>.md` e o metadata em `skills/<nome>.meta.json`.",
                "6. Salve os dois arquivos.",
                "7. Depois de salvar, execute `POST /agent/skills/index`.",
                "",
                "## Formato da nova skill",
                "Use o idioma do usuário no título do arquivo e no título Markdown.",
                "",
                "```md",
                "# Título no idioma do usuário",
                "",
                "## Resumo curto",
                "Explique o problema e a solução em poucas linhas.",
                "",
                "## Quando usar",
                "Descreva em que situação essa skill deve ser consultada.",
                "",
                "## Instruções",
                "Liste os passos objetivos para resolver o problema novamente.",
                "",
                "## Metadados",
                "Crie um arquivo `skills/<nome-da-skill>.meta.json` com metadados curtos e estáveis para facilitar busca, cache e reutilização.",
                "",
                "{",
                '  "name": "nome-da-skill",',
                '  "title": "Título no idioma do usuário",',
                '  "summary": "Resumo curto da skill",',
                '  "tags": ["tag1", "tag2"],',
                '  "language": "pt-BR",',
                '  "source_skill_path": "skills/nome-da-skill.md",',
                '  "created_at": "YYYY-MM-DDTHH:MM:SS-03:00",',
                '  "updated_at": "YYYY-MM-DDTHH:MM:SS-03:00",',
                '  "version": 1',
                "}",
                "",
                "Regras:",
                "- mantenha `summary` curto;",
                "- use `tags` com 3 a 8 termos úteis;",
                "- inicie `version` em `1` e atualize quando a skill mudar;",
                "- atualize `updated_at` sempre que editar a skill;",
                "- use o metadata para classificar a skill antes de depender só do conteúdo completo.",
                "",
                "## Arquivos relevantes",
                "- `app/main.py`",
                "- `install/install.py`",
                "",
                "## Observações",
                "Inclua detalhes importantes, limites e cuidados.",
                "```",
                "",
                "## Índice obrigatório",
                "Depois de salvar a skill, indexe com:",
                "",
                "```json",
                "{",
                '  "skill_path": "skills/nome-da-skill.md"',
                "}",
                "```",
                "",
                "Se quiser reindexar tudo:",
                "",
                "```json",
                "{}",
                "```",
                "",
            ]
        )


settings = Settings()
