"""Embedding backends for Agent Experience Memory.

Two backends are supported:

* ``LocalOnnxMiniLMEmbeddings`` — uses a pinned local ONNX export of
  ``intfloat/multilingual-e5-small``.  It applies the model's required
  ``query:`` / ``passage:`` prefixes and never downloads model bytes.

* ``DeterministicFakeEmbeddings`` — deterministic, hash-based vectors
  intended for unit tests and the retrieval wiring smoke test.  No model
  file required.

The ``build_embedding`` factory selects the backend by name.  The CLI
defaults to ``"local"``; tests pass ``"fake"`` explicitly.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import numpy as np

from langchain_core.embeddings import Embeddings

from ai_video.agent_memory.config import (
    DEFAULT_EMBED_BATCH_SIZE,
    DEFAULT_MODEL_ID,
    DEFAULT_MODEL_DIR,
    DEFAULT_MODEL_REVISION,
    DEFAULT_ONNX_FILE,
    DEFAULT_ONNX_SHA256,
    EMBEDDING_DIM,
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class EmbeddingIdentity:
    backend: str
    model_id: str
    revision: str
    dimension: int
    onnx_file: str
    model_sha256: str


def embedding_identity(embedding: Embeddings) -> EmbeddingIdentity:
    if isinstance(embedding, LocalOnnxMiniLMEmbeddings):
        return embedding.identity
    if isinstance(embedding, DeterministicFakeEmbeddings):
        return EmbeddingIdentity(
            backend="fake",
            model_id="deterministic-sha256",
            revision=f"seed-{embedding.seed}",
            dimension=embedding.size,
            onnx_file="",
            model_sha256="",
        )
    raise TypeError(f"unsupported embedding identity: {type(embedding).__name__}")


class LocalOnnxMiniLMEmbeddings(Embeddings):
    """Local ``intfloat/multilingual-e5-small`` ONNX embedding wrapper.

    Computes mean-pooled, L2-normalized 384-dim sentence embeddings using
    the ``onnxruntime`` CPU provider.  No network calls; relies entirely on
    a model directory present on disk.
    """

    def __init__(
        self,
        model_dir: str | None = None,
        onnx_file: str | None = None,
        batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
    ) -> None:
        raw_model_dir = model_dir or os.environ.get(
            "AGENT_MEMORY_MODEL_DIR", DEFAULT_MODEL_DIR
        )
        self.model_dir = str(Path(raw_model_dir).expanduser())
        self.onnx_file = onnx_file or DEFAULT_ONNX_FILE
        if batch_size < 1:
            raise ValueError("embedding batch_size must be positive")
        self.batch_size = batch_size
        if not os.path.isdir(self.model_dir):
            raise FileNotFoundError(
                f"Local multilingual E5 model directory not found: {self.model_dir}. "
                "Set AGENT_MEMORY_MODEL_DIR or pass model_dir explicitly."
            )
        onnx_path = os.path.join(self.model_dir, self.onnx_file)
        if not os.path.isfile(onnx_path):
            raise FileNotFoundError(f"ONNX model file missing: {onnx_path}")
        model_sha256 = _file_sha256(Path(onnx_path))
        if self.onnx_file == DEFAULT_ONNX_FILE and model_sha256 != DEFAULT_ONNX_SHA256:
            raise ValueError(
                "multilingual E5 ONNX bytes do not match the pinned model revision"
            )
        # Import lazily so that test environments without onnxruntime still
        # work as long as the 'fake' backend is selected.
        from transformers import AutoTokenizer  # type: ignore[import-not-found]
        import onnxruntime as ort  # type: ignore[import-not-found]

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_dir,
            local_files_only=True,
        )
        session_options = ort.SessionOptions()
        session_options.enable_cpu_mem_arena = False
        session_options.intra_op_num_threads = min(4, os.cpu_count() or 1)
        session_options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            onnx_path,
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
        self._input_names = {item.name for item in self._session.get_inputs()}
        self.identity = EmbeddingIdentity(
            backend="local",
            model_id=DEFAULT_MODEL_ID,
            revision=DEFAULT_MODEL_REVISION,
            dimension=EMBEDDING_DIM,
            onnx_file=self.onnx_file,
            model_sha256=model_sha256,
        )

    def embed_documents(self, texts: Iterable[str]) -> List[List[float]]:
        return self._embed([f"passage: {text}" for text in texts])

    def embed_query(self, text: str) -> List[float]:
        return self._embed([f"query: {text}"])[0]

    def _embed(self, texts: List[str]) -> List[List[float]]:
        output: List[List[float]] = []
        for start in range(0, len(texts), self.batch_size):
            output.extend(self._embed_batch(texts[start : start + self.batch_size]))
        return output

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        encoded = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )
        feeds = {
            name: value
            for name, value in {
                "input_ids": encoded["input_ids"],
                "attention_mask": encoded["attention_mask"],
                "token_type_ids": encoded.get(
                    "token_type_ids", np.zeros_like(encoded["input_ids"])
                ),
            }.items()
            if name in self._input_names
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

    @property
    def seed(self) -> int:
        return self._seed

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
