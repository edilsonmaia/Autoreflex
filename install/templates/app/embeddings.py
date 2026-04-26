from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Sequence

from app.config import persist_env_value, settings


@dataclass
class EmbeddingResult:
    vectors: List[List[float]]


class EmbeddingClient:
    MIN_CUDA_CAPABILITY = (7, 5)

    def __init__(self) -> None:
        self.model_path = Path(settings.embedding_model_path)
        self.tokenizer = None
        self.model = None
        self.device = None
        self.torch = None
        self._startup_retrying_cpu = False

    def startup(self, progress_callback: Callable[[int, str], None] | None = None) -> None:
        if self.tokenizer is not None and self.model is not None:
            if progress_callback is not None:
                progress_callback(85, "Modelo já estava carregado na memória")
            return
        from transformers import AutoModel, AutoTokenizer
        import torch as torch_module

        self.torch = torch_module
        requested_cuda = settings.embedding_device != "cpu"
        use_cuda = False
        fallback_reason = None
        if requested_cuda and not self._startup_retrying_cpu:
            if not torch_module.cuda.is_available():
                fallback_reason = "CUDA indisponível; usando CPU"
            else:
                try:
                    capability = torch_module.cuda.get_device_capability()
                except Exception:
                    capability = None
                if capability is None:
                    fallback_reason = "Não foi possível validar a GPU; usando CPU"
                elif capability < self.MIN_CUDA_CAPABILITY:
                    fallback_reason = "GPU incompatível com o build atual do PyTorch; usando CPU"
                else:
                    use_cuda = True
        if fallback_reason is not None and progress_callback is not None:
            progress_callback(20, fallback_reason)
        if fallback_reason is not None and requested_cuda and not self._startup_retrying_cpu:
            self._record_cpu_fallback(progress_callback, fallback_reason)
        self.device = torch_module.device("cuda" if use_cuda else "cpu")

        try:
            if progress_callback is not None:
                progress_callback(10, "Carregando tokenizer do modelo")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
            except ValueError as exc:
                fallback_error = str(exc).lower()
                if "backend tokenizer" not in fallback_error and "sentencepiece" not in fallback_error and "tiktoken" not in fallback_error:
                    raise
                if progress_callback is not None:
                    progress_callback(12, "Recarregando tokenizer em modo compatível")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    local_files_only=True,
                    use_fast=False,
                )

            if progress_callback is not None:
                progress_callback(45, "Carregando pesos do modelo")
            model_kwargs = {"local_files_only": True}
            if use_cuda:
                model_kwargs["torch_dtype"] = torch_module.float16
            self.model = AutoModel.from_pretrained(self.model_path, **model_kwargs)

            if progress_callback is not None:
                progress_callback(80, "Movendo modelo para o dispositivo disponível")
            self.model.to(self.device)
            self.model.eval()
            if progress_callback is not None:
                progress_callback(85, f"Modelo carregado e pronto em {self.device}")
        except Exception as exc:
            if use_cuda and not self._startup_retrying_cpu and self._looks_like_cuda_error(exc):
                self._switch_to_cpu(progress_callback, f"Falha ao iniciar em CUDA: {exc}")
                self._startup_retrying_cpu = True
                try:
                    self.startup(progress_callback=progress_callback)
                finally:
                    self._startup_retrying_cpu = False
                return
            self._reset_model_state()
            raise

    def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        if self.tokenizer is None or self.model is None:
            self.startup()
        assert self.torch is not None
        assert self.tokenizer is not None
        assert self.model is not None

        inputs = self.tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        try:
            with self.torch.no_grad():
                outputs = self.model(**inputs)
                token_embeddings = outputs.last_hidden_state
                mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
                pooled = (token_embeddings * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                normalized = self.torch.nn.functional.normalize(pooled, p=2, dim=1)
            return EmbeddingResult(vectors=normalized.cpu().tolist())
        except Exception as exc:
            if self.device is not None and str(self.device).startswith("cuda") and self._looks_like_cuda_error(exc):
                self._switch_to_cpu(None, f"Falha em tempo de execução com CUDA: {exc}")
                self.startup()
                return self.embed(texts)
            raise

    def _reset_model_state(self) -> None:
        self.tokenizer = None
        self.model = None
        self.device = None

    def _switch_to_cpu(
        self,
        progress_callback: Callable[[int, str], None] | None,
        reason: str,
    ) -> None:
        self._record_cpu_fallback(progress_callback, reason)
        self._reset_model_state()

    def _record_cpu_fallback(
        self,
        progress_callback: Callable[[int, str], None] | None,
        reason: str,
    ) -> None:
        if progress_callback is not None:
            progress_callback(20, reason)
        else:
            print(f"[*] {reason}", flush=True)
        settings.embedding_device = "cpu"
        persist_env_value("EMBEDDING_DEVICE", "cpu")

    @staticmethod
    def _looks_like_cuda_error(exc: Exception) -> bool:
        message = str(exc).lower()
        keywords = (
            "cuda",
            "cudnn",
            "cublas",
            "driver",
            "no kernel image is available",
            "device-side assert",
            "not compatible",
            "gpu",
        )
        return any(keyword in message for keyword in keywords)
