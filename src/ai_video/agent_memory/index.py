"""Local Chroma-backed vector index for Agent Experience Memory.

The index is a derived artifact rebuilt from ``docs/record_for_agent/``.
It is intentionally cheap to discard and rebuild because the corpus is
small (<2000 lines) and rebuild is the simplest correct freshness rule.

The index never participates in Production state, manifest, dependency,
or any other canonical owner.  It lives in ``.agent/memory/`` and is
gitignored.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Chroma

from ai_video.agent_memory.chunking import chunk_documents
from ai_video.agent_memory.config import DEFAULT_COLLECTION
from ai_video.agent_memory.corpus import load_documents


def index_exists(index_path: Path) -> bool:
    """Return True when the Chroma index directory looks initialized."""
    path = Path(index_path)
    if not path.is_dir():
        return False
    return (path / "chroma.sqlite3").exists() or any(path.glob("chroma-*"))


def build_index(
    corpus_root: Path,
    index_path: Path,
    embedding: Embeddings,
    collection_name: str = DEFAULT_COLLECTION,
) -> int:
    """Rebuild the Chroma index from ``corpus_root`` into ``index_path``.

    The existing index directory is wiped first because rebuild is the
    simplest correct freshness rule for a small corpus.

    Returns the number of chunks indexed.  ``0`` is a valid result for an
    empty corpus (an empty collection is still created so that subsequent
    ``search`` calls can detect the empty state cleanly).
    """
    index_path = Path(index_path)
    if index_path.exists():
        shutil.rmtree(index_path)
    index_path.mkdir(parents=True, exist_ok=True)

    docs = load_documents(corpus_root)
    chunks = chunk_documents(docs)

    # Chroma will accept the empty list, but to keep the on-disk shape
    # consistent we still create the collection explicitly.
    if not chunks:
        Chroma(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=str(index_path),
        )
        return 0

    Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=str(index_path),
        collection_name=collection_name,
    )
    return len(chunks)


def load_index(
    index_path: Path,
    embedding: Embeddings,
    collection_name: str = DEFAULT_COLLECTION,
) -> Chroma | None:
    """Open an existing Chroma index or return ``None`` if absent/broken."""
    if not index_exists(index_path):
        return None
    try:
        return Chroma(
            collection_name=collection_name,
            embedding_function=embedding,
            persist_directory=str(index_path),
        )
    except Exception:
        return None
