"""Canonical per-corpus layout for the project-level Agent Memory index."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from langchain_core.embeddings import Embeddings

from ai_video.agent_memory.config import DEFAULT_EMBED_BATCH_SIZE
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.index import (
    build_scoped_index,
    index_activation_lock,
    index_exists,
    release_index_client,
    validate_index_path,
)
from ai_video.agent_memory.manifest import IndexMismatchError


LAYOUT_SCHEMA_VERSION = 1
LAYOUT_FILENAME = "layout.json"
PROJECT_CORPUS_KINDS = (
    "experience",
    "superpowers",
    "current_docs",
    "research",
    "deferred",
)


class LegacyProjectIndexError(IndexMismatchError):
    """Raised when the old shared main index requires a one-time migration."""


class MissingProjectIndexError(FileNotFoundError):
    """Raised when canonical derived layout or a requested shard is absent."""

    def __init__(self, message: str, *, kinds: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.kinds = tuple(kinds)


@dataclass(frozen=True)
class ProjectIndexLayout:
    schema_version: int
    layout: str
    shards: dict[str, str]


def shard_path(index_root: Path, corpus_kind: str) -> Path:
    """Return the contained leaf path for a canonical project corpus."""
    if corpus_kind not in PROJECT_CORPUS_KINDS:
        raise ValueError(f"unknown project corpus kind: {corpus_kind!r}")
    root = Path(index_root).resolve()
    leaf = (root / corpus_kind).resolve()
    if leaf.parent != root:
        raise ValueError("project index shard must be directly contained by its root")
    return leaf


def _canonical_layout() -> ProjectIndexLayout:
    return ProjectIndexLayout(
        schema_version=LAYOUT_SCHEMA_VERSION,
        layout="per_corpus",
        shards={kind: kind for kind in PROJECT_CORPUS_KINDS},
    )


def _write_layout(index_root: Path) -> None:
    payload = _canonical_layout()
    path = Path(index_root) / LAYOUT_FILENAME
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    temporary.write_text(
        json.dumps(
            {
                "schema_version": payload.schema_version,
                "layout": payload.layout,
                "shards": payload.shards,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def read_project_layout(index_root: Path) -> ProjectIndexLayout:
    """Read and strictly validate the canonical root marker."""
    root = Path(index_root)
    path = root / LAYOUT_FILENAME
    if index_exists(root):
        raise LegacyProjectIndexError(
            f"legacy shared Agent Memory index at {root}; "
            "one-time all-scope migration required"
        )
    if not root.exists():
        raise MissingProjectIndexError(
            f"No sharded Agent Memory index at {root}"
        )
    if not path.is_file():
        raise IndexMismatchError(
            f"unrecognized or incomplete project index layout at {root}"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        layout = ProjectIndexLayout(
            schema_version=int(raw["schema_version"]),
            layout=str(raw["layout"]),
            shards={str(key): str(value) for key, value in raw["shards"].items()},
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise IndexMismatchError(f"invalid project index layout: {path}") from exc
    if layout != _canonical_layout():
        raise IndexMismatchError("project index layout identity mismatch")
    return layout


def _build_into_empty_root(
    corpora: Sequence[CorpusSpec],
    root: Path,
    embedding: Embeddings,
    batch_size: int,
) -> dict[str, int]:
    root.mkdir(parents=True, exist_ok=False)
    counts: dict[str, int] = {}
    for corpus in corpora:
        counts[corpus.kind] = build_scoped_index(
            (corpus,),
            shard_path(root, corpus.kind),
            embedding,
            batch_size=batch_size,
        )
    _write_layout(root)
    return counts


def build_project_indexes(
    corpora: Sequence[CorpusSpec],
    index_root: Path,
    embedding: Embeddings,
    *,
    batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
) -> dict[str, int]:
    """Build requested corpus shards; legacy roots migrate only as a full set."""
    if not corpora:
        raise ValueError("at least one project corpus is required")
    kinds = tuple(item.kind for item in corpora)
    if len(kinds) != len(set(kinds)):
        raise ValueError("corpus kinds must be unique")
    unknown = set(kinds) - set(PROJECT_CORPUS_KINDS)
    if unknown:
        raise ValueError(f"non-project corpus kinds cannot use main layout: {unknown}")
    root = Path(index_root).resolve()
    validate_index_path(root, tuple(item.root for item in corpora), label="index root")
    for corpus in corpora:
        if not corpus.root.is_dir():
            raise FileNotFoundError(f"corpus not found: {corpus.root}")

    legacy = index_exists(root)
    if legacy and set(kinds) != set(PROJECT_CORPUS_KINDS):
        raise LegacyProjectIndexError(
            f"legacy shared Agent Memory index at {root}; "
            "run an all-scope build once to migrate"
        )
    if root.exists() and not legacy:
        read_project_layout(root)
        counts: dict[str, int] = {}
        for corpus in corpora:
            counts[corpus.kind] = build_scoped_index(
                (corpus,),
                shard_path(root, corpus.kind),
                embedding,
                batch_size=batch_size,
            )
        return counts

    root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{root.name}.layout-staging-", dir=root.parent)
    )
    shutil.rmtree(staging)
    backup = root.parent / f".{root.name}.layout-backup-{uuid.uuid4().hex}"
    moved = False
    try:
        counts = _build_into_empty_root(corpora, staging, embedding, batch_size)
        with index_activation_lock(root, exclusive=True):
            if root.exists():
                release_index_client(root)
                os.replace(root, backup)
                moved = True
            os.replace(staging, root)
        if moved:
            shutil.rmtree(backup, ignore_errors=True)
        return counts
    except Exception:
        with index_activation_lock(root, exclusive=True):
            if moved and not root.exists() and backup.exists():
                os.replace(backup, root)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
