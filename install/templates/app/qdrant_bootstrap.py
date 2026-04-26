from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from app.config import settings


_qdrant_process: subprocess.Popen[bytes] | None = None


def _probe_port(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_qdrant_runtime() -> None:
    global _qdrant_process
    if _probe_port("127.0.0.1", 6333):
        return
    if _qdrant_process is not None and _qdrant_process.poll() is None:
        return

    Path(settings.qdrant_path).mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.qdrant_runtime:app",
        "--host",
        "127.0.0.1",
        "--port",
        "6333",
        "--log-level",
        "warning",
    ]
    popen_kwargs: dict[str, object] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        popen_kwargs["startupinfo"] = startupinfo
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    _qdrant_process = subprocess.Popen(command, **popen_kwargs)
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if _probe_port("127.0.0.1", 6333):
            return
        if _qdrant_process.poll() is not None:
            raise RuntimeError("Qdrant local encerrou inesperadamente ao iniciar.")
        time.sleep(0.25)
    raise RuntimeError("Qdrant local não ficou disponível na porta 6333 a tempo.")


def stop_qdrant_runtime() -> None:
    global _qdrant_process
    if _qdrant_process is None:
        return
    if _qdrant_process.poll() is None:
        _qdrant_process.terminate()
        try:
            _qdrant_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _qdrant_process.kill()
    _qdrant_process = None
