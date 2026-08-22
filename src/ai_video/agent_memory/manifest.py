"""Identity manifest for the derived Agent Memory index."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from ai_video.agent_memory.corpus import (
    CorpusSpec,
    iter_markdown_files,
    load_run_summary_documents,
)
from ai_video.agent_memory.embeddings import EmbeddingIdentity, embedding_identity


MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "manifest.json"


class IndexMismatchError(RuntimeError):
    """Raised when an index does not match its requested corpus/model identity."""


@dataclass(frozen=True)
class CorpusManifest:
    kind: str
    root: str
    collection_name: str
    authority: str
    source_sha256: str
    document_count: int
    chunk_count: int


@dataclass(frozen=True)
class IndexManifest:
    schema_version: int
    corpora: tuple[CorpusManifest, ...]
    embedding: EmbeddingIdentity
    chunk_size: int
    chunk_overlap: int
    metric: str
    library_versions: Mapping[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


def _display_root(root: Path) -> str:
    # A manifest can be validated from any working directory.  Storing the
    # canonical absolute root avoids false stale-index failures when the same
    # repository is invoked from a subdirectory.
    return str(root.resolve())


def corpus_digest(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    paths = list(iter_markdown_files(root))
    resolved_root = root.resolve()
    for path in paths:
        relative = path.resolve().relative_to(resolved_root).as_posix()
        payload = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest(), len(paths)


def run_summary_digest(root: Path) -> tuple[str, int]:
    """Digest only of the run summaries that will actually be indexed.

    Distinct from :func:`corpus_digest` so that the separate derived index
    manifest for ``run_summaries`` binds exactly to the bytes that survive
    the highest-version-per-family filter, not to every file under
    ``runs/``.  Missing or empty roots return an empty digest.
    """
    _, source_sha256, count = load_run_summary_documents(root)
    return source_sha256, count


def _library_versions() -> dict[str, str]:
    output: dict[str, str] = {}
    for package in (
        "chromadb",
        "langchain-core",
        "langchain-text-splitters",
        "numpy",
        "onnxruntime",
        "transformers",
    ):
        try:
            output[package] = version(package)
        except PackageNotFoundError:
            output[package] = "missing"
    return output


def create_manifest(
    corpora: Sequence[CorpusSpec],
    embedding,
    chunk_counts: Mapping[str, int],
    *,
    corpus_identities: Mapping[str, tuple[str, int]] | None = None,
    chunk_size: int = 800,
    chunk_overlap: int = 80,
) -> IndexManifest:
    corpus_items: list[CorpusManifest] = []
    for corpus in corpora:
        if corpus_identities is None:
            if corpus.kind == "run_summaries":
                source_sha256, document_count = run_summary_digest(corpus.root)
            else:
                source_sha256, document_count = corpus_digest(corpus.root)
        else:
            source_sha256, document_count = corpus_identities[corpus.kind]
        corpus_items.append(
            CorpusManifest(
                kind=corpus.kind,
                root=_display_root(corpus.root),
                collection_name=corpus.collection_name,
                authority=corpus.authority,
                source_sha256=source_sha256,
                document_count=document_count,
                chunk_count=chunk_counts[corpus.kind],
            )
        )
    return IndexManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        corpora=tuple(corpus_items),
        embedding=embedding_identity(embedding),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        metric="cosine",
        library_versions=_library_versions(),
    )


def write_manifest(index_path: Path, manifest: IndexManifest) -> None:
    payload = json.dumps(
        manifest.to_dict(),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    (Path(index_path) / MANIFEST_FILENAME).write_text(payload + "\n", encoding="utf-8")


def read_manifest(index_path: Path) -> IndexManifest:
    path = Path(index_path) / MANIFEST_FILENAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        corpora = tuple(CorpusManifest(**item) for item in payload["corpora"])
        embedding = EmbeddingIdentity(**payload["embedding"])
        return IndexManifest(
            schema_version=int(payload["schema_version"]),
            corpora=corpora,
            embedding=embedding,
            chunk_size=int(payload["chunk_size"]),
            chunk_overlap=int(payload["chunk_overlap"]),
            metric=str(payload["metric"]),
            library_versions=dict(payload["library_versions"]),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise IndexMismatchError(f"invalid Agent Memory index manifest: {path}") from exc


def validate_manifest(
    manifest: IndexManifest,
    corpora: Iterable[CorpusSpec],
    embedding,
) -> None:
    if manifest.schema_version != MANIFEST_SCHEMA_VERSION:
        raise IndexMismatchError("index manifest schema mismatch; rebuild required")
    if manifest.embedding != embedding_identity(embedding):
        raise IndexMismatchError("index embedding identity mismatch; rebuild required")
    if (manifest.chunk_size, manifest.chunk_overlap, manifest.metric) != (
        800,
        80,
        "cosine",
    ):
        raise IndexMismatchError("index chunking/metric identity mismatch; rebuild required")
    if dict(manifest.library_versions) != _library_versions():
        raise IndexMismatchError("index library version mismatch; rebuild required")

    indexed = {item.kind: item for item in manifest.corpora}
    for corpus in corpora:
        item = indexed.get(corpus.kind)
        if item is None:
            raise IndexMismatchError(
                f"scope {corpus.kind!r} is not present in the index; rebuild required"
            )
        if (
            item.collection_name != corpus.collection_name
            or item.authority != corpus.authority
        ):
            raise IndexMismatchError(
                f"corpus contract mismatch for {corpus.kind!r}; rebuild required"
            )
        if corpus.kind == "run_summaries":
            digest, document_count = run_summary_digest(corpus.root)
        else:
            digest, document_count = corpus_digest(corpus.root)
        if (
            item.source_sha256 != digest
            or item.document_count != document_count
            or item.root != _display_root(corpus.root)
        ):
            raise IndexMismatchError(
                f"stale corpus {corpus.kind!r}; rebuild the Agent Memory index"
            )
