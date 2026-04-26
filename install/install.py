from __future__ import annotations

import os
import json
import platform
import re
import subprocess
import sys
import shutil
import socket
import time
import importlib.util
import getpass
import traceback
from pathlib import Path
from typing import Callable, Optional, Tuple

try:
    from .config import settings
    from .logging_utils import setup_logging
except ImportError:  # pragma: no cover - execução direta do script
    from config import settings
    from logging_utils import setup_logging


logger = setup_logging("installer")


def log(message: str) -> None:
    print(f"[*] {message}")
    logger.info("%s", message)


def error(message: str) -> None:
    print(f"[!] ERRO: {message}")
    if sys.exc_info()[0] is not None:
        logger.error("%s\n%s", message, traceback.format_exc())
    else:
        logger.error("%s", message)
    raise SystemExit(1)


class AutoreflexInstaller:
    MIN_TORCH_CUDA_CAPABILITY = (7, 5)
    RUNTIME_PACKAGES = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("python-dotenv", "dotenv"),
        ("qdrant-client", "qdrant_client"),
        ("transformers", "transformers"),
        ("huggingface-hub", "huggingface_hub"),
    ]

    def __init__(self) -> None:
        self.source_root = Path(__file__).resolve().parent
        self.template_root = self.source_root / "templates"
        self.target_root = self.source_root.parent
        self.system_name = platform.system().lower()
        self.machine = platform.machine().strip().lower()
        self.architecture = self.detect_architecture()
        self.is_windows = self.system_name == "windows"
        self.running_in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
        self.current_python = Path(sys.executable)
        self.venv_path = Path(sys.prefix) if self.running_in_venv else self.target_root / ".venv"
        self.venv_python = (
            self.current_python
            if self.running_in_venv
            else self.venv_path / ("Scripts" if self.is_windows else "bin") / ("python.exe" if self.is_windows else "python")
        )
        self.model_id = settings.embedding_model_id
        self.model_path = Path(settings.embedding_model_path)
        self.torch_index_url = os.getenv("TORCH_INDEX_URL")
        self.embedding_backend = self.detect_embedding_backend()
        self.cuda_version = self.detect_cuda_version()
        self.gpu_compute_capability = self.detect_gpu_compute_capability()
        self.selected_embedding_device = "cpu"
        self.qdrant_process: Optional[subprocess.Popen[bytes]] = None
        self.started_qdrant_runtime = False

    def run(self) -> None:
        choice = self.show_initial_menu()
        if choice == "2":
            self.run_existing_system()
            return
        if choice == "3":
            self.repair_installation()
            return
        if choice != "1":
            log("Encerrando.")
            return
        self.bootstrap_fresh_installation()

    def show_initial_menu(self) -> str:
        print()
        print("================================")
        print(" Autoreflex")
        print("================================")
        print("1) Instalar do zero")
        print("2) Rodar sistema já instalado")
        print("3) Reparar instalação")
        print("4) Sair")
        print()
        while True:
            try:
                choice = input("Escolha uma opção [1-4]: ").strip()
            except EOFError:
                log("Entrada interativa indisponível. Assumindo instalação do zero.")
                return "1"
            if choice in {"1", "2", "3", "4"}:
                return choice
            print("Opção inválida. Digite 1, 2, 3 ou 4.")

    def run_existing_system(self) -> None:
        self.check_python_version()
        runtime_python = self.resolve_runtime_python()
        if runtime_python is None:
            error("Não foi encontrado um ambiente instalado para iniciar o sistema.")
        self.venv_python = runtime_python
        self.validate_existing_installation()
        self.run_server()

    def repair_installation(self) -> None:
        self._run_bootstrap_sequence(refresh_embedding_device=True, validate_existing=True)

    def bootstrap_fresh_installation(self) -> None:
        self.prompt_for_hf_token()
        self._run_bootstrap_sequence(refresh_embedding_device=False, validate_existing=False)

    def _run_bootstrap_sequence(self, refresh_embedding_device: bool, validate_existing: bool) -> None:
        steps: list[tuple[str, Callable[[], None]]] = [
            ("Validando token do Hugging Face", self.ensure_hf_token_if_needed),
            ("Validando acesso ao modelo do Hugging Face", self.validate_hf_model_access),
            ("Validando ambiente Python e arquitetura", self.check_python_version),
            ("Garantindo estrutura de diretórios", self.ensure_structure),
            ("Preparando arquivos base do projeto", self.ensure_scaffold),
            ("Preparando ambiente virtual", self.ensure_venv),
            ("Atualizando pip e ferramentas base", self.bootstrap_pip),
            ("Avaliando PyTorch e suporte CUDA", self.install_torch),
            ("Instalando dependências do runtime", self.install_requirements),
            ("Gerando arquivo .env", lambda: self.write_env_file(refresh_embedding_device=refresh_embedding_device)),
            ("Validando estado do modelo local", self.ensure_valid_embedding_model_state),
            ("Baixando modelo local de embeddings", self.download_embedding_model),
        ]
        if validate_existing:
            steps.append(("Validando instalação existente", self.validate_existing_installation))
        steps.append(("Iniciando servidor local", self.run_server))
        total = len(steps)
        for index, (title, action) in enumerate(steps, start=1):
            self._run_bootstrap_step(index, total, title, action)

    def _run_bootstrap_step(self, index: int, total: int, title: str, action: Callable[[], None]) -> None:
        log(f"Etapa {index}/{total}: {title}")
        action()
        log(f"Etapa {index}/{total} concluída: {title}")

    def prompt_for_hf_token(self) -> None:
        if self.is_embedding_model_ready(self.model_path):
            log("Modelo local já está pronto; token do Hugging Face não é necessário.")
            return

        existing_token = settings.resolve_hf_token()
        print()
        print("Antes de continuar, precisamos do token do Hugging Face.")
        print("O modelo de embeddings usado neste projeto está em um repositório restrito e só baixa com autenticação.")
        print("Crie ou copie seu token em: https://huggingface.co/settings/tokens")
        print("Ele será salvo no .env e também registrado como variável de ambiente para esta sessão.")

        if existing_token:
            print()
            print("Encontramos um token já configurado no ambiente ou no .env.")
            use_existing = self._prompt_yes_no("Deseja usar esse mesmo token? [S/n]: ", default=True)
            if use_existing:
                self.validate_hf_model_access(existing_token)
                self.store_hf_token(existing_token)
                log("Token existente reutilizado e registrado no ambiente desta sessão.")
                return
            print("Tudo bem. Cole um novo token abaixo para substituir o atual.")
        else:
            print("Cole seu token abaixo para continuar.")

        token = self._prompt_secret("Token do Hugging Face: ").strip()
        if not token:
            error("Nenhum token foi informado. A instalação foi interrompida antes de instalar qualquer dependência.")

        self.validate_hf_model_access(token)
        self.store_hf_token(token)
        log("Token do Hugging Face registrado no ambiente e no .env.")

    def _prompt_secret(self, prompt: str) -> str:
        if self.is_windows:
            print("Token do Hugging Face (cole e pressione Enter):")
            return input().strip()
        try:
            return getpass.getpass(prompt)
        except (EOFError, OSError):
            return input(prompt)

    def _prompt_yes_no(self, prompt: str, default: bool = True) -> bool:
        suffix = "S/n" if default else "s/N"
        full_prompt = prompt.replace("[S/n]", f"[{suffix}]")
        while True:
            try:
                answer = input(full_prompt).strip().lower()
            except EOFError:
                return default
            if not answer:
                return default
            if answer in {"s", "sim", "y", "yes"}:
                return True
            if answer in {"n", "nao", "não", "no"}:
                return False
            print("Responda com s ou n.")

    def store_hf_token(self, token: str) -> None:
        os.environ["HF_TOKEN"] = token
        os.environ["HUGGINGFACE_TOKEN"] = token
        settings.embedding_model_token = token
        self._write_env_token("HF_TOKEN", token)
        self._write_env_token("HUGGINGFACE_TOKEN", token)

    def _write_env_token(self, key: str, value: str) -> None:
        env_file = self.target_root / ".env"
        line_prefix = f"{key}="
        replacement = f"{line_prefix}{value}"

        lines: list[str]
        if env_file.exists():
            lines = env_file.read_text(encoding="utf-8").splitlines()
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

        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def resolve_hf_token(self) -> Optional[str]:
        return settings.resolve_hf_token()

    def get_hf_token_for_download(self) -> Optional[str]:
        return settings.resolve_hf_token()

    def ensure_hf_token_if_needed(self) -> None:
        if self.is_embedding_model_ready(self.model_path):
            log("Modelo local já está pronto; token do Hugging Face não é necessário.")
            return
        if self.get_hf_token_for_download():
            log("Token do Hugging Face encontrado; download do modelo poderá prosseguir.")
            return
        error(
            "Token do Hugging Face ausente na configuração carregada por install/config.py. "
            "Adicione HF_TOKEN ou HUGGINGFACE_TOKEN ao arquivo .env antes de iniciar a instalação. "
            "O setup foi interrompido antes de instalar qualquer dependência."
        )

    def validate_hf_model_access(self, token: Optional[str] = None) -> None:
        if self.is_embedding_model_ready(self.model_path):
            log("Modelo local já está pronto; validação do token do Hugging Face não é necessária.")
            return

        effective_token = token or self.get_hf_token_for_download()
        if not effective_token:
            error(
                "Token do Hugging Face ausente na configuração carregada por install/config.py. "
                "Adicione HF_TOKEN ou HUGGINGFACE_TOKEN ao arquivo .env antes de iniciar a instalação. "
                "O setup foi interrompido antes de validar o acesso ao modelo."
            )

        try:
            from huggingface_hub import HfApi

            api = HfApi()
            api.whoami(token=effective_token)
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            lowered = message.lower()
            if any(keyword in lowered for keyword in ("401", "unauthorized", "invalid", "expired", "authentication")):
                error(
                    "Token do Hugging Face inválido, expirado ou sem autenticação válida. "
                    "Gere um novo token e tente novamente."
                )
            error(f"Falha ao autenticar no Hugging Face: {message}")

        try:
            from huggingface_hub import HfApi

            api = HfApi()
            api.model_info(self.model_id, token=effective_token)
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            lowered = message.lower()
            if any(keyword in lowered for keyword in ("403", "forbidden", "permission", "gated", "access denied", "unauthorized")):
                error(
                    "Token do Hugging Face autenticou, mas não tem permissão para acessar o modelo de embeddings. "
                    "Ajuste as permissões do token ou use um token com acesso ao repositório do modelo."
                )
            error(f"Falha ao verificar permissão de acesso ao modelo do Hugging Face: {message}")

    def check_python_version(self) -> None:
        if sys.version_info < (3, 12):
            error("Este projeto requer Python 3.12 ou superior.")
        if not self.is_supported_architecture():
            error(f"Arquitetura não suportada: {self.machine or 'desconhecida'}")
        log(
            f"Ambiente detectado: {platform.system()} / {self.architecture} / Python "
            f"{sys.version_info.major}.{sys.version_info.minor}"
        )

    def detect_architecture(self) -> str:
        machine = self.machine
        if machine in {"amd64", "x86_64", "x64"}:
            return "x86_64"
        if machine in {"arm64", "aarch64"}:
            return "arm64"
        if machine in {"i386", "i686", "x86"}:
            return "x86_32"
        return machine or "unknown"

    def is_supported_architecture(self) -> bool:
        return self.architecture in {"x86_64", "arm64"}

    def ensure_structure(self) -> None:
        log("Garantindo estrutura de diretórios...")
        for directory in (
            self.target_root / "app",
            settings.models_dir,
            settings.logs_dir,
            settings.qdrant_path,
            settings.skills_dir,
            Path(settings.skills_dir) / "documentos",
            settings.embedding_model_path,
        ):
            Path(directory).mkdir(parents=True, exist_ok=True)

    def ensure_scaffold(self) -> None:
        self.copy_template_tree("app", self.target_root / "app")
        self.copy_template_tree("root", self.target_root)
        self.copy_template_tree("skills", Path(settings.skills_dir))
        self.copy_file_if_missing(self.source_root / "requirements.txt", self.target_root / "requirements.txt")
        self.write_agents_file()

    def copy_template_tree(self, template_subdir: str, target_dir: Path) -> None:
        template_dir = self.template_root / template_subdir
        if not template_dir.exists():
            error(f"Template ausente: {template_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
        for template_file in template_dir.rglob("*"):
            if not template_file.is_file():
                continue
            relative_path = template_file.relative_to(template_dir)
            self.copy_file_if_missing(template_file, target_dir / relative_path)

    @staticmethod
    def copy_file_if_missing(source_file: Path, target_file: Path) -> None:
        if target_file.exists():
            return
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)

    def write_agents_file(self) -> None:
        agents_path = self.target_root / "agents.md"
        template_path = self.template_root / "root" / "agents.md"
        if not template_path.exists():
            error(f"Template ausente: {template_path}")
        server_address = f"http://{settings.uvicorn_host}:{settings.uvicorn_port}"
        content = template_path.read_text(encoding="utf-8")
        content = content.replace("{{SERVER_ADDRESS}}", server_address)
        content = content.replace("{{SKILLS_SEARCH_URL}}", f"{server_address}/agent/skills/search")
        content = content.replace("{{SKILLS_GET_URL}}", f"{server_address}/agent/skills/get")
        content = content.replace("{{SKILLS_DIR}}", settings.skills_dir)
        content = content.replace("{{QDRANT_URL}}", settings.qdrant_url)
        content = content.replace("{{LLM_URL}}", settings.llm_url)
        content = content.replace("{{EMBEDDING_MODEL_PATH}}", settings.embedding_model_path)
        agents_path.write_text(content, encoding="utf-8")

    def ensure_venv(self) -> None:
        if self.running_in_venv:
            log(f"Usando venv ativo: {self.venv_path}")
            return
        if self.venv_python.exists():
            log("Ambiente virtual já existe.")
            return
        log("Criando ambiente virtual (.venv)...")
        subprocess.run([self.current_python, "-m", "venv", str(self.venv_path)], check=True)

    def resolve_runtime_python(self) -> Optional[Path]:
        candidates = []
        if self.running_in_venv and self.venv_python.exists():
            candidates.append(self.venv_python)
        project_venv_python = self.target_root / ".venv" / ("Scripts" if self.is_windows else "bin") / (
            "python.exe" if self.is_windows else "python"
        )
        if project_venv_python.exists():
            candidates.append(project_venv_python)
        if self.venv_python.exists():
            candidates.append(self.venv_python)
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def validate_existing_installation(self) -> None:
        required_paths = [
            self.target_root / "app" / "main.py",
            self.target_root / "app" / "config.py",
            self.target_root / "agents.md",
            Path(settings.skills_dir) / "criar_novas_skills.md",
        ]
        missing = [str(path) for path in required_paths if not path.exists()]
        if missing:
            error("Instalação existente incompleta. Arquivos ausentes: " + ", ".join(missing))

    def bootstrap_pip(self) -> None:
        log("Atualizando pip...")
        self._run_venv([self.venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        self.ensure_bootstrap_package("setuptools")
        self.ensure_bootstrap_package("wheel")

    def ensure_bootstrap_package(self, package_name: str) -> None:
        check = subprocess.run(
            [
                self.venv_python,
                "-c",
                (
                    "import importlib.util, sys; "
                    f"sys.exit(0 if importlib.util.find_spec('{package_name}') else 1)"
                ),
            ],
            check=False,
        )
        if check.returncode == 0:
            log(f"{package_name} já instalado.")
            return
        log(f"Instalando {package_name}...")
        self._run_venv([self.venv_python, "-m", "pip", "install", package_name])

    def install_torch(self) -> None:
        log("Verificando suporte CUDA e instalação do PyTorch...")
        if self.embedding_backend != "torch":
            log(f"Backend de embeddings '{self.embedding_backend}' não exige PyTorch. Pulando instalação.")
            self.selected_embedding_device = "cpu"
            return
        installed_probe = self.inspect_installed_torch()
        if installed_probe is not None:
            if installed_probe["gpu_compatible"]:
                log("PyTorch já instalado e compatível com a GPU local.")
                self.selected_embedding_device = "cuda"
            else:
                log("PyTorch já instalado, mas sem compatibilidade válida com a GPU local.")
                log("Mantendo execução em CPU.")
                self.selected_embedding_device = "cpu"
            return
        if self.gpu_compute_capability is None:
            if self.cuda_version is None:
                log("Nenhum suporte CUDA detectado. Instalando PyTorch CPU.")
            else:
                log(
                    "Não foi possível confirmar uma GPU compatível com o build atual do PyTorch. "
                    "Instalando PyTorch CPU."
                )
            self._install_torch_cpu()
            self.selected_embedding_device = "cpu"
            return
        if self.gpu_compute_capability < self.MIN_TORCH_CUDA_CAPABILITY:
            log(
                "GPU detectada com compute capability "
                f"{self.cuda_version_str(self.gpu_compute_capability)}; "
                "este build atual do PyTorch CUDA não é compatível com ela."
            )
            log("Instalando PyTorch CPU para manter o runtime funcional.")
            self._install_torch_cpu()
            self.selected_embedding_device = "cpu"
            return
        if self.cuda_version is None:
            log("Não foi possível confirmar a versão do CUDA. Instalando PyTorch CPU.")
            self._install_torch_cpu()
            self.selected_embedding_device = "cpu"
            return
        torch_index_url = self.torch_index_url or self.select_torch_cuda_index(self.cuda_version)
        if torch_index_url is None:
            log(f"CUDA detectado ({self.cuda_version_str(self.cuda_version)}), mas sem wheel compatível mapeado.")
            log("Instalando PyTorch CPU para evitar falha de compatibilidade.")
            self._install_torch_cpu()
            self.selected_embedding_device = "cpu"
            return
        log(
            f"CUDA detectado ({self.cuda_version_str(self.cuda_version)}); "
            f"instalando PyTorch compatível em {torch_index_url}"
        )
        self._run_venv([self.venv_python, "-m", "pip", "install", "torch", "--index-url", torch_index_url])
        self.selected_embedding_device = "cuda"

    def _install_torch_cpu(self) -> None:
        self._run_venv(
            [
                self.venv_python,
                "-m",
                "pip",
                "install",
                "torch",
                "--index-url",
                "https://download.pytorch.org/whl/cpu",
            ]
        )

    def inspect_installed_torch(self) -> Optional[dict[str, object]]:
        check = subprocess.run(
            [self.venv_python, "-c", "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('torch') else 1)"],
            check=False,
        )
        if check.returncode != 0:
            return None

        probe_script = """
import json
try:
    import torch
except Exception as exc:
    print(json.dumps({"importable": False, "error": str(exc)}))
    raise SystemExit(1)

gpu_available = bool(torch.cuda.is_available())
arch_list = []
if hasattr(torch.cuda, "get_arch_list"):
    try:
        arch_list = list(torch.cuda.get_arch_list())
    except Exception:
        arch_list = []

capability = None
if gpu_available:
    try:
        capability = torch.cuda.get_device_capability()
    except Exception:
        capability = None

payload = {
    "importable": True,
    "version": getattr(torch, "__version__", ""),
    "torch_cuda": getattr(torch.version, "cuda", None),
    "gpu_available": gpu_available,
    "arch_list": arch_list,
    "capability": capability,
}
print(json.dumps(payload))
"""
        result = subprocess.run(
            [self.venv_python, "-c", probe_script],
            capture_output=True,
            text=True,
            check=False,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        if not output:
            return None
        try:
            payload = json.loads(output.splitlines()[-1])
        except json.JSONDecodeError:
            return None
        if not payload.get("importable"):
            return None

        gpu_available = bool(payload.get("gpu_available"))
        arch_list = {str(item).lower() for item in payload.get("arch_list", []) if item}
        capability = payload.get("capability")
        gpu_compatible = False
        if gpu_available and isinstance(capability, (list, tuple)) and len(capability) >= 2:
            gpu_tag = f"sm_{int(capability[0])}{int(capability[1])}"
            gpu_compatible = gpu_tag in arch_list
        payload["gpu_compatible"] = gpu_compatible
        return payload

    def install_requirements(self) -> None:
        requirements_file = self.source_root / "requirements.txt"
        if not requirements_file.exists():
            error("requirements.txt não encontrado dentro da pasta install.")
        log(f"Instalando dependências do projeto a partir de {requirements_file}...")
        self._run_venv([self.venv_python, "-m", "pip", "install", "-r", str(requirements_file)])
        self.ensure_runtime_packages()

    def ensure_runtime_packages(self) -> None:
        for pip_name, import_name in self.RUNTIME_PACKAGES:
            if self.is_module_available(import_name):
                log(f"{pip_name} já instalado.")
                continue
            log(f"Instalando dependência do runtime: {pip_name}...")
            self._run_venv([self.venv_python, "-m", "pip", "install", pip_name])

    @staticmethod
    def is_module_available(module_name: str) -> bool:
        return importlib.util.find_spec(module_name) is not None

    def write_env_file(self, refresh_embedding_device: bool = False) -> None:
        env_file = self.target_root / ".env"
        if env_file.exists():
            existing_lines = env_file.read_text(encoding="utf-8").splitlines()
            filtered_lines = [line for line in existing_lines if not line.startswith("AGENT_API_KEY=")]
            removed_legacy_key = filtered_lines != existing_lines
            if refresh_embedding_device:
                filtered_lines = self._replace_or_append_env_line(
                    filtered_lines,
                    "EMBEDDING_DEVICE",
                    self.selected_embedding_device,
                )
            if filtered_lines != existing_lines:
                if removed_legacy_key:
                    log("Atualizando .env existente e removendo chave de agente legada.")
                else:
                    log("Atualizando .env existente.")
                env_file.write_text("\n".join(filtered_lines) + ("\n" if filtered_lines else ""), encoding="utf-8")
            else:
                log(".env já existe; preservando arquivo atual.")
            return
        log("Criando .env padrão...")
        env_template = settings.build_env_template()
        token_value = self.get_hf_token_for_download() or ""
        env_template = env_template.replace(f"HUGGINGFACE_TOKEN={settings.embedding_model_token or ''}", f"HUGGINGFACE_TOKEN={token_value}")
        env_template = env_template.replace(f"HF_TOKEN={settings.embedding_model_token or ''}", f"HF_TOKEN={token_value}")
        env_template = env_template.replace(f"TARGET_ARCHITECTURE={settings.target_architecture}", f"TARGET_ARCHITECTURE={self.architecture}")
        env_template = env_template.replace(f"EMBEDDING_MODEL_PATH={settings.embedding_model_path}", f"EMBEDDING_MODEL_PATH={self.target_root / 'models' / 'gemma'}")
        env_template = env_template.replace(
            f"EMBEDDING_DEVICE={settings.embedding_device}",
            f"EMBEDDING_DEVICE={self.selected_embedding_device}",
        )
        env_file.write_text(env_template, encoding="utf-8")

    @staticmethod
    def _replace_or_append_env_line(lines: list[str], key: str, value: str) -> list[str]:
        prefix = f"{key}="
        replacement = f"{prefix}{value}"
        updated = False
        result = []
        for line in lines:
            if line.startswith(prefix):
                if not updated:
                    result.append(replacement)
                    updated = True
                continue
            result.append(line)
        if not updated:
            result.append(replacement)
        return result

    def ensure_valid_embedding_model_state(self) -> None:
        model_path = self.target_root / "models" / "gemma"
        if not model_path.exists():
            return
        if self.is_embedding_model_ready(model_path):
            return
        if any(model_path.iterdir()):
            log("Modelo local presente, mas incompleto ou inconsistente. Recriando do zero...")
            shutil.rmtree(model_path, ignore_errors=True)
        model_path.mkdir(parents=True, exist_ok=True)

    def download_embedding_model(self) -> None:
        log("Baixando modelo local de embeddings...")
        model_path = self.target_root / "models" / "gemma"
        if model_path.exists() and any(model_path.iterdir()):
            log("Modelo local já presente.")
            return
        if not self.is_module_available("huggingface_hub"):
            log("Dependência `huggingface_hub` ausente. Instalando antes do download do modelo...")
            self._run_venv([self.venv_python, "-m", "pip", "install", "huggingface-hub"])
        token = self.get_hf_token_for_download()
        token_repr = repr(token)
        try:
            self._run_venv(
                [
                    self.venv_python,
                    "-c",
                    (
                        "from huggingface_hub import snapshot_download; "
                        f"token = {token_repr}; "
                        f"snapshot_download(repo_id='{self.model_id}', local_dir=r'{model_path}', "
                        "resume_download=True, token=token)"
                    ),
                ]
            )
        except subprocess.CalledProcessError as exc:
            log(f"Aviso: não foi possível baixar o modelo automaticamente ({exc}).")
            log(f"Baixe manualmente em {model_path}; sem isso o runtime local não conseguirá subir embeddings.")

    @staticmethod
    def is_embedding_model_ready(model_path: Path) -> bool:
        if not model_path.exists() or not model_path.is_dir():
            return False
        if not any(model_path.iterdir()):
            return False
        has_config = (model_path / "config.json").exists()
        has_tokenizer = any(
            (model_path / filename).exists()
            for filename in ("tokenizer.json", "tokenizer.model", "spiece.model", "vocab.json")
        )
        has_weights = any(
            (model_path / filename).exists()
            for filename in (
                "model.safetensors",
                "pytorch_model.bin",
                "model.onnx",
                "model.safetensors.index.json",
                "pytorch_model.bin.index.json",
            )
        )
        return has_config and has_tokenizer and has_weights
    def run_server(self) -> None:
        if not self.is_module_available("uvicorn"):
            error("A dependência uvicorn não está instalada. Verifique o passo de instalação de dependências.")
        command = [
            self.venv_python,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            settings.uvicorn_host,
            "--port",
            str(settings.uvicorn_port),
        ]
        if settings.uvicorn_reload:
            command.append("--reload")
        log("Iniciando servidor com o comando:")
        log(" ".join(str(part) for part in command))
        subprocess.run(command, check=True)

    def _run_venv(self, command: list[str]) -> None:
        subprocess.run(command, check=True)

    def detect_cuda_version(self) -> Optional[Tuple[int, int]]:
        if shutil.which("nvidia-smi") is None:
            return None
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, check=False)
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        match = re.search(r"CUDA Version:\s*([\d.]+)", output)
        if not match:
            return None
        return self.parse_version(match.group(1))

    def detect_gpu_compute_capability(self) -> Optional[Tuple[int, int]]:
        if shutil.which("nvidia-smi") is None:
            return None
        queries = ("compute_cap", "compute_capability")
        for query in queries:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    f"--query-gpu={query}",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
            if output:
                first_value = output.splitlines()[0].strip()
                parsed = self.parse_version(first_value)
                if parsed is not None:
                    return parsed

        result = subprocess.run(["nvidia-smi", "-q"], capture_output=True, text=True, check=False)
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        match = re.search(r"Compute Capability\s*:\s*([\d.]+)", output)
        if not match:
            return None
        return self.parse_version(match.group(1))

    @staticmethod
    def parse_version(value: str) -> Optional[Tuple[int, int]]:
        parts = value.strip().split(".")
        if not parts:
            return None
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return major, minor
        except ValueError:
            return None

    def detect_embedding_backend(self) -> str:
        configured = (settings.embedding_backend or "auto").strip().lower()
        if configured != "auto":
            return configured

        model_path = self.model_path
        if model_path.exists():
            names = {item.name.lower() for item in model_path.rglob("*")}
            if any(name.endswith(".onnx") for name in names) or "onnx" in names:
                return "onnx"
            if "model.safetensors" in names or "pytorch_model.bin" in names or "config.json" in names:
                return "torch"
        return "torch"

    @staticmethod
    def cuda_version_str(version: Tuple[int, int]) -> str:
        return f"{version[0]}.{version[1]}"

    def select_torch_cuda_index(self, cuda_version: Tuple[int, int]) -> Optional[str]:
        candidates = [
            ((13, 0), "https://download.pytorch.org/whl/cu130"),
            ((12, 8), "https://download.pytorch.org/whl/cu128"),
            ((12, 6), "https://download.pytorch.org/whl/cu126"),
            ((12, 4), "https://download.pytorch.org/whl/cu124"),
            ((12, 1), "https://download.pytorch.org/whl/cu121"),
            ((11, 8), "https://download.pytorch.org/whl/cu118"),
        ]
        for minimum_version, index_url in candidates:
            if cuda_version >= minimum_version:
                return index_url
        return None


if __name__ == "__main__":
    AutoreflexInstaller().run()

