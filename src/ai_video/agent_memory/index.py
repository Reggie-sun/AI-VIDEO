"""Scoped, local Chroma index for advisory Agent project knowledge."""

from __future__ import annotations

import hashlib
import fcntl
import logging
import os
import shutil
import sqlite3
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import chromadb
import numpy as np
from chromadb.api.client import SharedSystemClient
from chromadb.config import Settings
from langchain_core.embeddings import Embeddings

from ai_video.agent_memory.chunking import chunk_documents
from ai_video.agent_memory.config import DEFAULT_EMBED_BATCH_SIZE
from ai_video.agent_memory.corpus import (
    CorpusSpec,
    load_document_snapshot,
)
from ai_video.agent_memory.manifest import (
    IndexManifest,
    IndexMismatchError,
    create_manifest,
    corpus_digest,
    read_manifest,
    validate_library_rebuild_candidate_manifest,
    validate_manifest,
    write_manifest,
)


# Chroma accepts large add/get batches; these sizes only bound memory per call.
_REUSE_FETCH_BATCH = 1000
_ADD_BATCH = 512


class IndexBuildInProgressError(RuntimeError):
    """Raised when a non-waiting build finds another builder holding the shard."""


class RefreshBudgetExceededError(RuntimeError):
    """Raised before embedding when a bounded refresh needs too many new chunks."""

    def __init__(self, *, new_chunks: int, limit: int) -> None:
        super().__init__(
            f"refresh needs {new_chunks} new chunk embeddings; "
            f"{limit} remain in this refresh budget"
        )
        self.new_chunks = new_chunks
        self.limit = limit


@dataclass
class EmbeddingBudget:
    """Cap on new chunk embeddings, shared across every shard one caller refreshes."""

    remaining: int

    def reserve(self, new_chunks: int) -> None:
        if new_chunks > self.remaining:
            raise RefreshBudgetExceededError(
                new_chunks=new_chunks,
                limit=self.remaining,
            )
        self.remaining -= new_chunks


_LOGGER = logging.getLogger(__name__)


_IN_PROCESS_ACTIVATION_LOCKS: dict[str, threading.RLock] = {}
_IN_PROCESS_ACTIVATION_LOCKS_GUARD = threading.Lock()


def _in_process_activation_lock(index_path: Path) -> threading.RLock:
    identifier = str(Path(index_path).resolve())
    with _IN_PROCESS_ACTIVATION_LOCKS_GUARD:
        return _IN_PROCESS_ACTIVATION_LOCKS.setdefault(
            identifier,
            threading.RLock(),
        )


@contextmanager
def index_activation_lock(index_path: Path, *, exclusive: bool):
    """Coordinate short index activation with validation/query readers."""
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = index_path.parent / f".{index_path.name}.activation.lock"
    # Chroma caches one SharedSystem per path inside a process. Serializing
    # same-process readers prevents one caller from stopping that shared client
    # while another reader is still querying it; cross-process readers retain
    # shared flock semantics.
    with _in_process_activation_lock(index_path):
        with lock_path.open("a+b") as handle:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH,
            )
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _index_build_lock(index_path: Path, *, wait: bool = True):
    """Serialize builders without blocking readers during staging work."""
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = index_path.parent / f".{index_path.name}.build.lock"
    with lock_path.open("a+b") as handle:
        try:
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX if wait else fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError as exc:
            raise IndexBuildInProgressError(
                f"another Agent Memory build holds {index_path}"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _client(index_path: Path):
    # chromadb 0.5.x still calls its disabled Posthog client and logs a local
    # signature error. Settings below prevents egress; disabling that logger
    # also keeps CLI JSON/text output clean on old supported environments.
    logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
    return chromadb.PersistentClient(
        path=str(index_path),
        settings=Settings(anonymized_telemetry=False),
    )


def _release_cached_client(index_path: Path) -> None:
    """Stop Chroma's path-scoped system before replacing its SQLite directory.

    A system that failed to open (for example over a corrupt SQLite file) can
    raise from ``stop()``; dropping it from the cache is still the only safe
    outcome, so release never masks the caller's own error or recovery build.
    """
    identifier = str(Path(index_path))
    system = SharedSystemClient._identifier_to_system.pop(identifier, None)
    if system is not None:
        try:
            system.stop()
        except Exception:
            pass


def release_index_client(index_path: Path) -> None:
    """Release a path-scoped Chroma client before another process activates it."""
    _release_cached_client(Path(index_path))


def index_exists(index_path: Path) -> bool:
    """Return True only for an initialized index with an identity manifest."""
    path = Path(index_path)
    return path.is_dir() and (path / "chroma.sqlite3").is_file() and (
        path / "manifest.json"
    ).is_file()


def _chunk_id(corpus: CorpusSpec, chunk) -> str:
    """Hash a chunk by corpus, root-relative path, position, and text.

    ``source`` metadata is relative to the caller's working directory; ids use
    the corpus-root-relative path so vector reuse survives a different cwd.
    """
    metadata = chunk.metadata
    source = Path(str(metadata.get("source", "")))
    try:
        locator = source.resolve().relative_to(Path(corpus.root).resolve()).as_posix()
    except (OSError, ValueError):
        locator = str(source)
    seed = "\0".join(
        (
            corpus.kind,
            locator,
            str(metadata.get("chunk_index", "")),
            chunk.page_content,
        )
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def validate_index_path(
    index_path: Path,
    protected_paths: Sequence[Path],
    *,
    label: str = "index",
) -> None:
    """Reject index directories that overlap source or sibling index paths."""
    resolved_index = Path(index_path).resolve()
    for protected_path in protected_paths:
        resolved_protected = Path(protected_path).resolve()
        if (
            resolved_index == resolved_protected
            or resolved_index in resolved_protected.parents
            or resolved_protected in resolved_index.parents
        ):
            raise ValueError(
                f"{label} path must not overlap protected path: "
                f"{resolved_index} vs {resolved_protected}"
            )
def _reusable_embeddings(
    index_path: Path,
    corpus: CorpusSpec,
    embedding: Embeddings,
    chunk_ids: Sequence[str],
) -> dict[str, np.ndarray]:
    """Return stored vectors for unchanged chunks of a compatible active shard.

    Chunk ids hash corpus kind, corpus-root-relative path, position, and text,
    so a stored vector is reusable only when the manifest proves the same
    schema, embedding model, chunking, and library versions. Any doubt falls
    back to re-embedding.
    """
    index_path = Path(index_path)
    if not chunk_ids or not index_exists(index_path):
        return {}
    try:
        manifest = read_manifest(index_path)
        validate_manifest(manifest, (), embedding)
    except IndexMismatchError as exc:
        _LOGGER.info("not reusing vectors from %s: %s", index_path, exc)
        return {}
    item = {entry.kind: entry for entry in manifest.corpora}.get(corpus.kind)
    if item is None or item.collection_name != corpus.collection_name:
        return {}
    reused: dict[str, np.ndarray] = {}
    with index_activation_lock(index_path, exclusive=False):
        try:
            collection = _client(index_path).get_collection(item.collection_name)
            for start in range(0, len(chunk_ids), _REUSE_FETCH_BATCH):
                stored = collection.get(
                    ids=list(chunk_ids[start : start + _REUSE_FETCH_BATCH]),
                    include=["embeddings"],
                )
                # Chroma returns rows in storage order, so pair each vector
                # with its returned id rather than the requested position.
                for chunk_id, vector in zip(stored["ids"], stored["embeddings"]):
                    reused[str(chunk_id)] = np.asarray(vector, dtype=np.float32)
        except Exception as exc:
            _LOGGER.warning(
                "cannot reuse vectors from %s; re-embedding (%s: %s)",
                index_path,
                type(exc).__name__,
                exc,
            )
            return {}
        finally:
            _release_cached_client(index_path)
    return reused


def _build_staging_index(
    corpora: Sequence[CorpusSpec],
    staging_path: Path,
    embedding: Embeddings,
    batch_size: int,
    *,
    reuse_from: Path | None = None,
    embedding_budget: EmbeddingBudget | None = None,
) -> tuple[int, IndexManifest]:
    planned = []
    for corpus in corpora:
        documents, source_sha256, document_count = load_document_snapshot(
            corpus.root,
            corpus=corpus,
        )
        chunks = chunk_documents(documents)
        ids = [_chunk_id(corpus, item) for item in chunks]
        reused = (
            _reusable_embeddings(reuse_from, corpus, embedding, ids)
            if reuse_from is not None
            else {}
        )
        identity = (source_sha256, document_count)
        planned.append((corpus, chunks, ids, reused, identity))
    new_chunks = sum(
        1
        for _, _, ids, reused, _ in planned
        for chunk_id in ids
        if chunk_id not in reused
    )
    if embedding_budget is not None:
        embedding_budget.reserve(new_chunks)

    client = _client(staging_path)
    total = 0
    chunk_counts: dict[str, int] = {}
    corpus_identities: dict[str, tuple[str, int]] = {}
    for corpus, chunks, ids, reused, identity in planned:
        corpus_identities[corpus.kind] = identity
        chunk_counts[corpus.kind] = len(chunks)
        total += len(chunks)
        collection = client.get_or_create_collection(
            name=corpus.collection_name,
            metadata={"hnsw:space": "cosine", "corpus_kind": corpus.kind},
        )
        missing = [
            index for index, chunk_id in enumerate(ids) if chunk_id not in reused
        ]
        vectors = {chunk_id: reused[chunk_id] for chunk_id in ids if chunk_id in reused}
        for start in range(0, len(missing), batch_size):
            batch = missing[start : start + batch_size]
            embedded = embedding.embed_documents(
                [chunks[index].page_content for index in batch]
            )
            for index, vector in zip(batch, embedded):
                vectors[ids[index]] = np.asarray(vector, dtype=np.float32)
        for start in range(0, len(chunks), _ADD_BATCH):
            batch_chunks = chunks[start : start + _ADD_BATCH]
            batch_ids = ids[start : start + _ADD_BATCH]
            collection.add(
                ids=batch_ids,
                documents=[item.page_content for item in batch_chunks],
                metadatas=[dict(item.metadata) for item in batch_chunks],
                embeddings=[vectors[chunk_id] for chunk_id in batch_ids],
            )
    for corpus in corpora:
        if corpus_digest(corpus.root, corpus) != corpus_identities[corpus.kind]:
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
    return total, manifest


def build_scoped_index(
    corpora: Sequence[CorpusSpec],
    index_path: Path,
    embedding: Embeddings,
    *,
    batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
    embedding_budget: EmbeddingBudget | None = None,
    wait: bool = True,
    reuse: bool = True,
) -> int:
    """Build all requested corpora in staging, then replace the derived index.

    With ``reuse`` (the default) unchanged chunks keep vectors from the
    compatible active index, so only new or edited chunks are embedded; pass
    ``reuse=False`` after changing how embeddings are computed. ``embedding_budget``
    bounds the new embeddings and ``wait=False`` refuses to queue behind another
    builder; both fail before the active index is touched.
    """
    if not corpora:
        raise ValueError("at least one corpus is required")
    if batch_size < 1:
        raise ValueError("index batch_size must be positive")
    index_path = Path(index_path)
    validate_index_path(
        index_path,
        tuple(corpus.root for corpus in corpora),
    )
    kinds = [item.kind for item in corpora]
    if len(kinds) != len(set(kinds)):
        raise ValueError("corpus kinds must be unique")
    for corpus in corpora:
        if not Path(corpus.root).is_dir():
            raise FileNotFoundError(f"corpus not found: {corpus.root}")

    with _index_build_lock(index_path, wait=wait):
        index_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = Path(
            tempfile.mkdtemp(
                prefix=f".{index_path.name}.staging-",
                dir=index_path.parent,
            )
        )
        backup_path = (
            index_path.parent / f".{index_path.name}.backup-{uuid.uuid4().hex}"
        )
        old_moved = False
        try:
            total, _ = _build_staging_index(
                corpora,
                staging_path,
                embedding,
                batch_size,
                reuse_from=index_path if reuse else None,
                embedding_budget=embedding_budget,
            )
            _release_cached_client(staging_path)
            with index_activation_lock(index_path, exclusive=True):
                if index_path.exists():
                    _release_cached_client(index_path)
                    os.replace(index_path, backup_path)
                    old_moved = True
                os.replace(staging_path, index_path)
            if old_moved:
                shutil.rmtree(backup_path, ignore_errors=True)
            return total
        except Exception:
            if old_moved:
                with index_activation_lock(index_path, exclusive=True):
                    if not index_path.exists() and backup_path.exists():
                        os.replace(backup_path, index_path)
            raise
        finally:
            _release_cached_client(staging_path)
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


def _validate_index_collections(
    index_path: Path,
    corpus_kinds: Iterable[str],
    manifest: IndexManifest,
) -> None:
    indexed = {item.kind: item for item in manifest.corpora}
    try:
        client = _client(Path(index_path))
    except Exception as exc:
        raise IndexMismatchError(
            f"Agent Memory index at {index_path} cannot be opened; "
            "explicit build required"
        ) from exc
    for kind in corpus_kinds:
        item = indexed[kind]
        try:
            actual_chunks = client.get_collection(item.collection_name).count()
        except Exception as exc:
            raise IndexMismatchError(
                f"index collection for scope {kind!r} is unavailable; "
                "explicit build required"
            ) from exc
        if actual_chunks != item.chunk_count:
            raise IndexMismatchError(
                f"index collection for scope {kind!r} chunk count mismatch; "
                "explicit build required"
            )


def _validate_index_collections_read_only(
    index_path: Path,
    corpus_kinds: Iterable[str],
    manifest: IndexManifest,
) -> None:
    """Inspect an incompatible Chroma store without allowing schema migration."""
    database = Path(index_path).resolve() / "chroma.sqlite3"
    for suffix in ("-wal", "-journal"):
        sidecar = Path(f"{database}{suffix}")
        if sidecar.exists() and sidecar.stat().st_size:
            raise IndexMismatchError(
                "library-incompatible index has uncheckpointed database state; "
                "explicit build required"
            )
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(
            f"{database.as_uri()}?mode=ro&immutable=1",
            uri=True,
        )
        connection.execute("PRAGMA query_only = ON")
        if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise IndexMismatchError(
                "library-incompatible index database failed integrity check"
            )
        indexed = {item.kind: item for item in manifest.corpora}
        for kind in corpus_kinds:
            item = indexed[kind]
            segments = connection.execute(
                """
                SELECT segments.id, segments.scope
                FROM collections
                JOIN segments ON segments.collection = collections.id
                WHERE collections.name = ?
                """,
                (item.collection_name,),
            ).fetchall()
            metadata_segments = [row[0] for row in segments if row[1] == "METADATA"]
            vector_segments = [row[0] for row in segments if row[1] == "VECTOR"]
            if len(metadata_segments) != 1 or len(vector_segments) != 1:
                raise IndexMismatchError(
                    f"index collection for scope {kind!r} is unavailable; "
                    "explicit build required"
                )
            actual_chunks = connection.execute(
                "SELECT COUNT(*) FROM embeddings WHERE segment_id = ?",
                (metadata_segments[0],),
            ).fetchone()[0]
            if actual_chunks != item.chunk_count:
                raise IndexMismatchError(
                    f"index collection for scope {kind!r} chunk count mismatch; "
                    "explicit build required"
                )
    except IndexMismatchError:
        raise
    except (OSError, sqlite3.Error, TypeError) as exc:
        raise IndexMismatchError(
            "library-incompatible index cannot be verified read-only; "
            "explicit build required"
        ) from exc
    finally:
        if connection is not None:
            connection.close()


def validate_materialized_index(
    index_path: Path,
    embedding: Embeddings,
    corpus_kinds: Iterable[str],
) -> IndexManifest:
    """Validate manifest identity and physical collections without source roots."""
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(
            f"No Agent Memory index at {index_path}. "
            "Run `python -m scripts.agent_memory --scope <scope> build` first."
        )
    if not index_exists(index_path):
        raise IndexMismatchError(
            f"Agent project RAG index at {index_path} is incomplete; "
            "explicit build required"
        )
    manifest = read_index_manifest(index_path)
    validate_manifest(manifest, (), embedding)
    kinds = tuple(dict.fromkeys(corpus_kinds))
    indexed = {item.kind: item for item in manifest.corpora}
    missing = set(kinds) - indexed.keys()
    if missing:
        raise IndexMismatchError(
            f"scope(s) {sorted(missing)} not present in index; rebuild required"
        )
    _validate_index_collections(index_path, kinds, manifest)
    return manifest


def validate_library_rebuild_candidate(
    corpora: Sequence[CorpusSpec],
    index_path: Path,
    embedding: Embeddings,
) -> IndexManifest:
    """Accept only a physically valid shard whose sole contract drift is libraries."""
    if not corpora:
        raise ValueError("at least one corpus is required")
    index_path = Path(index_path)
    validate_index_path(index_path, tuple(corpus.root for corpus in corpora))
    for corpus in corpora:
        if not corpus.root.is_dir():
            raise FileNotFoundError(f"corpus not found: {corpus.root}")
    if not index_exists(index_path):
        raise IndexMismatchError(
            f"Agent project RAG index at {index_path} is incomplete; "
            "explicit rebuild required"
        )
    manifest = read_index_manifest(index_path)
    validate_library_rebuild_candidate_manifest(manifest, corpora, embedding)
    kinds = tuple(corpus.kind for corpus in corpora)
    if tuple(item.kind for item in manifest.corpora) != kinds:
        raise IndexMismatchError(
            "library-incompatible shard contains unexpected corpora"
        )
    _validate_index_collections_read_only(index_path, kinds, manifest)
    return manifest


def validate_scoped_index(
    corpora: Sequence[CorpusSpec],
    index_path: Path,
    embedding: Embeddings,
) -> IndexManifest:
    """Validate a materialized project index without rebuilding it."""
    if not corpora:
        raise ValueError("at least one corpus is required")
    index_path = Path(index_path)
    validate_index_path(index_path, tuple(corpus.root for corpus in corpora))
    for corpus in corpora:
        if not corpus.root.is_dir():
            raise FileNotFoundError(f"corpus not found: {corpus.root}")
    if not index_path.exists():
        raise FileNotFoundError(
            f"No Agent Memory index at {index_path}. "
            "Run `python -m scripts.agent_memory --scope <scope> build` first."
        )
    if not index_exists(index_path):
        raise IndexMismatchError(
            f"Agent project RAG index at {index_path} is incomplete; "
            "explicit rebuild required"
        )
    manifest = read_index_manifest(index_path)
    # Validate the immutable index identity before touching Chroma, but inspect
    # physical collections before reporting corpus freshness. A stale source
    # must not hide a missing or truncated collection.
    validate_manifest(manifest, (), embedding)
    indexed = {item.kind: item for item in manifest.corpora}
    present_corpora: list[CorpusSpec] = []
    for corpus in corpora:
        item = indexed.get(corpus.kind)
        if item is None:
            continue
        if (
            item.collection_name != corpus.collection_name
            or item.authority != corpus.authority
        ):
            validate_manifest(manifest, (corpus,), embedding)
        present_corpora.append(corpus)
    _validate_index_collections(
        index_path,
        (corpus.kind for corpus in present_corpora),
        manifest,
    )
    validate_manifest(manifest, corpora, embedding)
    return manifest


__all__ = [
    "EmbeddingBudget",
    "IndexBuildInProgressError",
    "IndexMismatchError",
    "RefreshBudgetExceededError",
    "build_index",
    "build_scoped_index",
    "index_exists",
    "load_index",
    "read_index_manifest",
    "validate_index_path",
    "validate_library_rebuild_candidate",
    "validate_materialized_index",
    "validate_manifest",
    "validate_scoped_index",
]
