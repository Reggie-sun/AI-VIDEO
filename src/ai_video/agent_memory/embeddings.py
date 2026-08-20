"""Embedding backends for Agent Experience Memory.

Two backends are supported:

* ``LocalOnnxMiniLMEmbeddings`` — uses the local ONNX ``all-MiniLM-L6-v2``
  model that ships with the Continue VS Code extension.  Fully offline,
  no PyTorch or ``sentence-transformers`` dependency at runtime.

* ``DeterministicFakeEmbeddings`` — deterministic, hash-based vectors
  intended for unit tests and the retrieval wiring smoke test.  No model
  file required.

The ``build_embedding`` factory selects the backend by name.  The CLI
defaults to ``"local"``; tests pass ``"fake"`` explicitly.
"""

from __future__ import annotations

import hashlib
import os
from typing import Iterable, List

import numpy as np

from langchain_core.embeddings import Embeddings

from ai_video.agent_memory.config import (
    DEFAULT_MODEL_DIR,
    DEFAULT_ONNX_FILE,
    EMBEDDING_DIM,
)


class LocalOnnxMiniLMEmbeddings(Embeddings):
    """Local ``all-MiniLM-L6-v2`` ONNX embedding wrapper.

    Computes mean-pooled, L2-normalized 384-dim sentence embeddings using
    the ``onnxruntime`` CPU provider.  No network calls; relies entirely on
    a model directory present on disk.
    """

    def __init__(
        self,
        model_dir: str | None = None,
        onnx_file: str | None = None,
    ) -> None:
        self.model_dir = model_dir or os.environ.get(
            "AGENT_MEMORY_MODEL_DIR", DEFAULT_MODEL_DIR
        )
        self.onnx_file = onnx_file or DEFAULT_ONNX_FILE
        if not os.path.isdir(self.model_dir):
            raise FileNotFoundError(
                f"Local MiniLM model directory not found: {self.model_dir}. "
                "Set AGENT_MEMORY_MODEL_DIR or pass model_dir explicitly."
            )
        onnx_path = os.path.join(self.model_dir, self.onnx_file)
        if not os.path.isfile(onnx_path):
            raise FileNotFoundError(f"ONNX model file missing: {onnx_path}")
        # Import lazily so that test environments without onnxruntime still
        # work as long as the 'fake' backend is selected.
        from transformers import AutoTokenizer  # type: ignore[import-not-found]
        import onnxruntime as ort  # type: ignore[import-not-found]

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        self._session = ort.InferenceSession(
            onnx_path, providers=["CPUExecutionProvider"]
        )

    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        return self._embed(list(texts))

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

    def _embed(self, texts: List[str]) -> List[List[float]]:
        encoded = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )
        feeds = {
            "input_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"],
            "token_type_ids": encoded.get(
                "token_type_ids", np.zeros_like(encoded["input_ids"])
            ),
        }
        last_hidden = self._session.run(None, feeds)[0]
        emb = self._mean_pool(last_hidden, encoded["attention_mask"])
        emb = emb / np.clip(
            np.linalg.norm(emb, axis=1, keepdims=True), 1e-9, None
        )
        return emb.astype(np.float32).tolist()

    @staticmethod
    def _mean_pool(
        last_hidden: np.ndarray, mask: np.ndarray
    ) -> np.ndarray:
        mask_f = mask.astype(np.float32)[:, :, None]
        summed = (last_hidden * mask_f).sum(axis=1)
        denom = np.clip(mask_f.sum(axis=1), 1e-9, None)
        return summed / denom


class DeterministicFakeEmbeddings(Embeddings):
    """Deterministic hash-based embedding for tests.

    Produces the same vector for the same input string on every call.
    Quality is meaningless; the only requirement is that the retrieval
    pipeline be exercised end-to-end with stable inputs.
    """

    def __init__(self, size: int = EMBEDDING_DIM, seed: int = 0xC0FFEE) -> None:
        self.size = size
        self._seed = seed

    def _vector(self, text: str) -> List[float]:
        digest = hashlib.sha256(
            f"{self._seed}::{text}".encode("utf-8")
        ).digest()
        # Stretch 32 bytes into ``size`` floats deterministically.
        rng = np.random.default_rng(
            int.from_bytes(digest[:8], "big") ^ self._seed
        )
        vec = rng.standard_normal(self.size).astype(np.float32)
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._vector(text)


def build_embedding(backend: str = "local") -> Embeddings:
    """Return the embedding implementation matching ``backend``.

    ``backend`` values:

    * ``"local"`` — :class:`LocalOnnxMiniLMEmbeddings` (default).
    * ``"fake"``  — :class:`DeterministicFakeEmbeddings` (tests only).
    """
    if backend == "local":
        return LocalOnnxMiniLMEmbeddings()
    if backend == "fake":
        return DeterministicFakeEmbeddings()
    raise ValueError(
        f"unknown embedding backend: {backend!r} (expected 'local' or 'fake')"
    )
