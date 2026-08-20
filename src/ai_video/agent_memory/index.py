"""Scoped, local Chroma index for advisory Agent project knowledge."""

from __future__ import annotations

import gc
import hashlib
import logging
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Sequence

import chromadb
from chromadb.config import Settings
from langchain_core.embeddings import Embeddings

from ai_video.agent_memory.chunking import chunk_documents
from ai_video.agent_memory.config import DEFAULT_EMBED_BATCH_SIZE
from ai_video.agent_memory.corpus import CorpusSpec, load_document_snapshot
from ai_video.agent_memory.manifest import (
    IndexManifest,
    IndexMismatchError,
    create_manifest,
    corpus_digest,
    read_manifest,
    validate_manifest,
    write_manifest,
)


def _client(index_path: Path):
    # chromadb 0.5.x still calls its disabled Posthog client and logs a local
    # signature error. Settings below prevents egress; disabling that logger
    # also keeps CLI JSON/text output clean on old supported environments.
    logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
    return chromadb.PersistentClient(
        path=str(index_path),
        settings=Settings(anonymized_telemetry=False),
    )


def index_exists(index_path: Path) -> bool:
    """Return True only for an initialized index with an identity manifest."""
    path = Path(index_path)
    return path.is_dir() and (path / "chroma.sqlite3").is_file() and (
        path / "manifest.json"
    ).is_file()


def _chunk_id(corpus: CorpusSpec, chunk) -> str:
    metadata = chunk.metadata
    seed = "\0".join(
        (
            corpus.kind,
            str(metadata.get("source", "")),
            str(metadata.get("chunk_index", "")),
            chunk.page_content,
        )
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _build_staging_index(
    corpora: Sequence[CorpusSpec],
    staging_path: Path,
    embedding: Embeddings,
    batch_size: int,
) -> tuple[int, IndexManifest]:
    client = _client(staging_path)
    total = 0
    chunk_counts: dict[str, int] = {}
    corpus_identities: dict[str, tuple[str, int]] = {}
    for corpus in corpora:
        collection = client.get_or_create_collection(
            name=corpus.collection_name,
            metadata={"hnsw:space": "cosine", "corpus_kind": corpus.kind},
        )
        documents, source_sha256, document_count = load_document_snapshot(
            corpus.root,
            corpus=corpus,
        )
        corpus_identities[corpus.kind] = (source_sha256, document_count)
        chunks = chunk_documents(documents)
        chunk_counts[corpus.kind] = len(chunks)
        total += len(chunks)
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            texts = [item.page_content for item in batch]
            collection.add(
                ids=[_chunk_id(corpus, item) for item in batch],
                documents=texts,
                metadatas=[dict(item.metadata) for item in batch],
                embeddings=embedding.embed_documents(texts),
            )
    for corpus in corpora:
        if corpus_digest(corpus.root) != corpus_identities[corpus.kind]:
            raise IndexMismatchError(
                f"corpus {corpus.kind!r} changed during index build; retry required"
            )
    manifest = create_manifest(
        corpora,
        embedding,
        chunk_counts,
        corpus_identities=corpus_identities,
    )
    write_manifest(staging_path, manifest)
    del client
    gc.collect()
    return total, manifest


def build_scoped_index(
    corpora: Sequence[CorpusSpec],
    index_path: Path,
    embedding: Embeddings,
    *,
    batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
) -> int:
    """Build all requested corpora in staging, then replace the derived index."""
    if not corpora:
        raise ValueError("at least one corpus is required")
    if batch_size < 1:
        raise ValueError("index batch_size must be positive")
    kinds = [item.kind for item in corpora]
    if len(kinds) != len(set(kinds)):
        raise ValueError("corpus kinds must be unique")
    for corpus in corpora:
        if not Path(corpus.root).is_dir():
            raise FileNotFoundError(f"corpus not found: {corpus.root}")

    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path = Path(
        tempfile.mkdtemp(
            prefix=f".{index_path.name}.staging-",
            dir=index_path.parent,
        )
    )
    backup_path = index_path.parent / f".{index_path.name}.backup-{uuid.uuid4().hex}"
    old_moved = False
    try:
        total, _ = _build_staging_index(
            corpora,
            staging_path,
            embedding,
            batch_size,
        )
        if index_path.exists():
            os.replace(index_path, backup_path)
            old_moved = True
        os.replace(staging_path, index_path)
        if old_moved:
            shutil.rmtree(backup_path, ignore_errors=True)
        return total
    except Exception:
        if old_moved and not index_path.exists() and backup_path.exists():
            os.replace(backup_path, index_path)
        raise
    finally:
        if staging_path.exists():
            shutil.rmtree(staging_path)


def build_index(
    corpus_root: Path,
    index_path: Path,
    embedding: Embeddings,
    collection_name: str = "agent_memory_experience",
) -> int:
    """Backward-compatible single-experience-corpus build wrapper."""
    corpus = CorpusSpec.experience(Path(corpus_root))
    if collection_name != corpus.collection_name:
        corpus = CorpusSpec(
            kind=corpus.kind,
            root=corpus.root,
            collection_name=collection_name,
            authority=corpus.authority,
        )
    return build_scoped_index((corpus,), index_path, embedding)


def read_index_manifest(index_path: Path) -> IndexManifest:
    return read_manifest(Path(index_path))


def load_index(
    index_path: Path,
    embedding: Embeddings,
    collection_name: str = "agent_memory_experience",
):
    """Open a manifest-backed local Chroma client or return ``None`` if absent."""
    del embedding, collection_name
    if not index_exists(index_path):
        return None
    return _client(Path(index_path))


__all__ = [
    "IndexMismatchError",
    "build_index",
    "build_scoped_index",
    "index_exists",
    "load_index",
    "read_index_manifest",
    "validate_manifest",
]
