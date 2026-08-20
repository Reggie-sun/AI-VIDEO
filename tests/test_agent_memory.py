"""Unit tests for Agent Experience Memory.

These tests use the deterministic fake embedding backend so they are
network-free, model-free, and reproducible.  They exercise:

  * markdown corpus iteration and frontmatter tolerance
  * heading-aware chunking preserves file + section metadata
  * Chroma index build + load round-trip
  * top-K retrieval returns the expected known-relevant record
  * text formatter handles both empty and populated hit lists

A separate local smoke command (``make agent-memory-smoke`` style) is
provided by ``scripts/agent_memory.py`` itself; this file intentionally
stays on the deterministic fake backend.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.agent_memory.chunking import chunk_documents
from ai_video.agent_memory.config import (
    DEFAULT_CORPUS_ROOT,
    DEFAULT_INDEX_PATH,
)
from ai_video.agent_memory.corpus import (
    iter_markdown_files,
    load_documents,
    parse_date,
    parse_frontmatter,
    parse_title,
)
from ai_video.agent_memory.embeddings import (
    DeterministicFakeEmbeddings,
    LocalOnnxMiniLMEmbeddings,
    build_embedding,
)
from ai_video.agent_memory.index import build_index, index_exists, load_index
from ai_video.agent_memory.retrieval import Hit, format_text, search


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_embedding() -> DeterministicFakeEmbeddings:
    return DeterministicFakeEmbeddings(size=64)


@pytest.fixture
def sample_corpus(tmp_path: Path) -> Path:
    """A small representative corpus with three known-relevant records."""
    root = tmp_path / "records"
    root.mkdir()
    (root / "2026-08-20-rough-cut-failure.md").write_text(
        "# Rough Cut Failure\n\n"
        "Date: 2026-08-20\n\n"
        "## Problem\n"
        "The 5-minute rough cut leaned on too many repeated reference "
        "images and did not advance the plot.\n\n"
        "## Recovery\n"
        "Reverted to terminal-frame continuity and reduced reference count.\n",
        encoding="utf-8",
    )
    (root / "2026-08-20-h3-continuity.md").write_text(
        "---\n"
        "type: continuity_note\n"
        "domains: h3\n"
        "---\n"
        "# H3 Continuity Drift\n\n"
        "Date: 2026-08-20\n\n"
        "## Symptom\n"
        "H3 multi-shot continuity showed identity drift across shots.\n\n"
        "## Fix\n"
        "Use the exact terminal frame as the next first_frame input.\n",
        encoding="utf-8",
    )
    (root / "2026-08-20-seedance-credential.md").write_text(
        "# Seedance Credential Note\n\n"
        "Date: 2026-08-20\n\n"
        "## Note\n"
        "ARK_API_KEY is the canonical reference, never the raw key.\n",
        encoding="utf-8",
    )
    (root / "ignore.txt").write_text("not markdown")
    (root / "subdir").mkdir()
    (root / "subdir" / "nested.md").write_text(
        "# Nested Note\n\nJust a body without any frontmatter.\n",
        encoding="utf-8",
    )
    return root


# ---------------------------------------------------------------------------
# corpus parsing
# ---------------------------------------------------------------------------


def test_iter_markdown_files_skips_non_markdown(sample_corpus: Path) -> None:
    names = {p.name for p in iter_markdown_files(sample_corpus)}
    assert "2026-08-20-rough-cut-failure.md" in names
    assert "2026-08-20-h3-continuity.md" in names
    assert "2026-08-20-seedance-credential.md" in names
    assert "nested.md" in names
    assert "ignore.txt" not in names


def test_parse_helpers() -> None:
    text = "# Hello World\n\nDate: 2026-08-20\n\nbody"
    assert parse_title(text, "fallback") == "Hello World"
    assert parse_date(text) == "2026-08-20"
    assert parse_date("no date here") is None
    assert parse_title("no heading", "fb") == "fb"


def test_parse_frontmatter_when_absent() -> None:
    assert parse_frontmatter("# Title\n\nbody") == {}


def test_parse_frontmatter_basic() -> None:
    text = "---\ntype: failure\ndomains: continuity\n---\n# Title\n"
    assert parse_frontmatter(text) == {
        "type": "failure",
        "domains": "continuity",
    }


def test_load_documents_metadata(sample_corpus: Path) -> None:
    docs = load_documents(sample_corpus)
    assert len(docs) == 4
    rough = next(d for d in docs if "rough-cut" in d.metadata["source"])
    assert rough.metadata["title"] == "Rough Cut Failure"
    assert rough.metadata["date"] == "2026-08-20"
    h3 = next(d for d in docs if "h3-continuity" in d.metadata["source"])
    assert h3.metadata["type"] == "continuity_note"
    assert h3.metadata["domains"] == "h3"
    nested = next(d for d in docs if "nested" in d.metadata["source"])
    assert "type" not in nested.metadata


# ---------------------------------------------------------------------------
# chunking
# ---------------------------------------------------------------------------


def test_chunk_documents_preserves_metadata(sample_corpus: Path) -> None:
    docs = load_documents(sample_corpus)
    chunks = chunk_documents(docs)
    assert chunks, "expected at least one chunk"
    for chunk in chunks:
        md = chunk.metadata
        for key in ("source", "title", "chunk_index", "section"):
            assert key in md
    sectioned = [c for c in chunks if c.metadata.get("section")]
    assert sectioned, "expected at least one heading-tagged chunk"
    rough_chunks = [c for c in chunks if "rough-cut" in c.metadata["source"]]
    assert any(
        "Problem" in c.metadata.get("section", "") for c in rough_chunks
    ), "rough cut Problem section should be its own chunk"


# ---------------------------------------------------------------------------
# index + retrieval wiring
# ---------------------------------------------------------------------------


def test_build_index_creates_directory(
    sample_corpus: Path, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    n = build_index(
        corpus_root=sample_corpus,
        index_path=idx,
        embedding=fake_embedding,
    )
    assert n > 0
    assert index_exists(idx)


def test_build_index_is_idempotent(
    sample_corpus: Path, tmp_path: Path, fake_embedding
) -> None:
    """Two builds from the same corpus produce equivalent chunk counts.

    Note: rebuilding into the *same* directory inside one process trips a
    ChromaSQLite file-handle caching edge case in chromadb 0.5.x, so we
    compare two builds in separate directories.  That is the user-facing
    contract we care about (reproducibility of the index), not the in-place
    rebuild.
    """
    idx_a = tmp_path / "idx_a"
    idx_b = tmp_path / "idx_b"
    n1 = build_index(
        corpus_root=sample_corpus,
        index_path=idx_a,
        embedding=fake_embedding,
    )
    n2 = build_index(
        corpus_root=sample_corpus,
        index_path=idx_b,
        embedding=fake_embedding,
    )
    assert n1 == n2
    assert n1 > 0
    # Both indexes should be queryable.
    store_a = load_index(idx_a, fake_embedding)
    store_b = load_index(idx_b, fake_embedding)
    assert store_a is not None
    assert store_b is not None


def test_search_returns_expected_record_for_rough_cut(
    sample_corpus: Path, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_index(
        corpus_root=sample_corpus, index_path=idx, embedding=fake_embedding
    )
    hits = search(
        "5 minute rough cut reference image and plot progression",
        top_k=3,
        index_path=idx,
        embedding=fake_embedding,
    )
    assert hits, "search should return at least one hit"
    sources = [h.source for h in hits]
    assert any("rough-cut" in s for s in sources), (
        f"expected rough cut record in top-k, got: {sources}"
    )


def test_search_returns_expected_record_for_h3(
    sample_corpus: Path, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_index(
        corpus_root=sample_corpus, index_path=idx, embedding=fake_embedding
    )
    hits = search(
        "H3 multi-shot continuity identity drift terminal first_frame",
        top_k=3,
        index_path=idx,
        embedding=fake_embedding,
    )
    sources = [h.source for h in hits]
    assert any("h3-continuity" in s for s in sources), (
        f"expected H3 continuity record in top-k, got: {sources}"
    )


def test_search_returns_expected_record_for_seedance(
    sample_corpus: Path, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_index(
        corpus_root=sample_corpus, index_path=idx, embedding=fake_embedding
    )
    hits = search(
        "Seedance Provider credential ARK_API_KEY",
        top_k=3,
        index_path=idx,
        embedding=fake_embedding,
    )
    sources = [h.source for h in hits]
    assert any("seedance-credential" in s for s in sources), (
        f"expected seedance credential record in top-k, got: {sources}"
    )


def test_search_missing_index_raises(tmp_path: Path, fake_embedding) -> None:
    with pytest.raises(FileNotFoundError):
        search(
            "anything",
            index_path=tmp_path / "missing",
            embedding=fake_embedding,
        )


def test_index_exists_false_for_missing(tmp_path: Path) -> None:
    assert not index_exists(tmp_path / "missing")


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------


def test_format_text_empty_returns_no_results_message() -> None:
    assert "No relevant prior records" in format_text([])


def test_format_text_includes_sources_and_excerpt() -> None:
    hits = [
        Hit(
            source="docs/record_for_agent/x.md",
            title="X",
            section="Symptom",
            score=0.91,
            excerpt="some body text",
            chunk_index=0,
            h1="X",
            h2="Symptom",
            h3="",
            date="2026-08-20",
        )
    ]
    out = format_text(hits)
    assert "Relevant prior records:" in out
    assert "docs/record_for_agent/x.md" in out
    assert "Symptom" in out
    assert "some body text" in out


# ---------------------------------------------------------------------------
# embedding factory
# ---------------------------------------------------------------------------


def test_build_embedding_local_requires_model_dir(monkeypatch) -> None:
    monkeypatch.setenv("AGENT_MEMORY_MODEL_DIR", "/nonexistent/path")
    with pytest.raises(FileNotFoundError):
        build_embedding(backend="local")


def test_build_embedding_fake_does_not_require_files() -> None:
    emb = build_embedding(backend="fake")
    v = emb.embed_query("hello")
    assert len(v) == 384
    # deterministic: same input => same vector
    assert emb.embed_query("hello") == v


def test_default_paths_have_expected_shape() -> None:
    assert DEFAULT_CORPUS_ROOT.endswith("record_for_agent")
    assert DEFAULT_INDEX_PATH.startswith(".agent")


# ---------------------------------------------------------------------------
# local embedding (skipped when the model cache is unavailable)
# ---------------------------------------------------------------------------


def test_local_onnx_embedding_loads_when_cache_present() -> None:
    """Smoke test: the local embedding loads when the model is on disk.

    Skipped when the Continue VS Code extension model cache is missing
    on this machine.  Real end-to-end semantic search is verified by the
    CLI smoke command, not by this unit test.
    """
    from pathlib import Path

    from ai_video.agent_memory.config import DEFAULT_MODEL_DIR

    if not Path(DEFAULT_MODEL_DIR).is_dir():
        pytest.skip("local MiniLM model cache not present on this machine")
    emb = LocalOnnxMiniLMEmbeddings()
    v = emb.embed_query("hello world")
    assert len(v) == 384
    # Same text -> same vector
    assert emb.embed_query("hello world") == v
