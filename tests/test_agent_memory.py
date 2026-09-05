"""Unit tests for Agent Experience Memory.

These tests use the deterministic fake embedding backend so they are
network-free, model-free, and reproducible.  They exercise:

  * markdown corpus iteration and frontmatter tolerance
  * heading-aware chunking preserves file + section metadata
  * Chroma index build + load round-trip
  * top-K retrieval returns the expected known-relevant record
  * text formatter handles both empty and populated hit lists
  * auto-generated ``runs/<run_id>/SUMMARY.md`` are picked up into a
    separate derived index with explicit advisory authority, distinct
    collection name and stable schema-v1 manifest.

The local embedding smoke below runs only when the pinned model cache is
present; the remaining tests intentionally use the deterministic fake backend.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import ai_video.agent_memory.corpus as corpus_module
import ai_video.agent_memory.index as index_module
import ai_video.agent_memory.retrieval as retrieval_module
import scripts.agent_memory as agent_memory_script
from ai_video.agent_memory.chunking import chunk_documents
from ai_video.agent_memory.config import (
    DEFAULT_CORPUS_ROOT,
    DEFAULT_DOCS_ROOT,
    DEFAULT_INDEX_PATH,
    DEFAULT_MODEL_DIR,
    DEFAULT_SUPERPOWERS_ROOT,
    DEFAULT_TOP_N,
    DENSE_NULL_QUERY_ASCII,
    HYBRID_CANDIDATE_TOP_K,
    VALID_SCOPES,
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
from ai_video.agent_memory.hybrid import (
    lexical_relevance_score,
    rank_bm25,
    reciprocal_rank_fusion,
    select_dense_null_query,
)
from ai_video.agent_memory.retrieval import Hit, format_text, search
from scripts.agent_memory import main as agent_memory_main


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


def test_search_keeps_score_at_threshold_and_drops_lower(
    sample_corpus: Path, tmp_path: Path, fake_embedding, monkeypatch
) -> None:
    idx = tmp_path / "idx"
    build_index(
        corpus_root=sample_corpus,
        index_path=idx,
        embedding=fake_embedding,
    )
    query = "threshold boundary"
    null_vector = fake_embedding.embed_query(select_dense_null_query(query))

    class BoundaryCollection:
        def count(self) -> int:
            return 2

        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [null_vector]:
                return {"distances": [[0.32, 0.33]]}
            assert kwargs["n_results"] == 2
            return {
                "ids": [["exact", "below"]],
                "documents": [["first candidate", "second candidate"]],
                "metadatas": [[
                    {
                        "source": "docs/exact.md",
                        "title": "Exact",
                        "section": "Boundary",
                        "chunk_index": 0,
                    },
                    {
                        "source": "docs/below.md",
                        "title": "Below",
                        "section": "Boundary",
                        "chunk_index": 0,
                    },
                ]],
                "distances": [[0.3, 0.31]],
            }

        def get(self, **kwargs):
            return {
                "ids": ["exact", "below"],
                "documents": ["first candidate", "second candidate"],
                "metadatas": [
                    {
                        "source": "docs/exact.md",
                        "title": "Exact",
                        "section": "Boundary",
                        "chunk_index": 0,
                    },
                    {
                        "source": "docs/below.md",
                        "title": "Below",
                        "section": "Boundary",
                        "chunk_index": 0,
                    },
                ],
            }

    class BoundaryStore:
        def get_collection(self, name: str) -> BoundaryCollection:
            assert name == "agent_memory_experience"
            return BoundaryCollection()

    monkeypatch.setattr(retrieval_module, "load_index", lambda *_: BoundaryStore())

    hits = search(
        query,
        top_k=2,
        index_path=idx,
        embedding=fake_embedding,
    )

    assert [hit.source for hit in hits] == ["docs/exact.md"]
    assert hits[0].score == 0.7


def test_search_hybrid_fusion_rescues_exact_lexical_hit(
    sample_corpus: Path, tmp_path: Path, fake_embedding, monkeypatch
) -> None:
    idx = tmp_path / "idx"
    build_index(
        corpus_root=sample_corpus,
        index_path=idx,
        embedding=fake_embedding,
    )

    metadatas = [
        {
            "source": "docs/general.md",
            "title": "General",
            "section": "Production",
            "chunk_index": 0,
        },
        {
            "source": "docs/credential.md",
            "title": "Credential",
            "section": "Provider",
            "chunk_index": 0,
        },
        *(
            {
                "source": f"docs/decoy-{index}.md",
                "title": f"Decoy {index}",
                "section": "Other",
                "chunk_index": 0,
            }
            for index in range(18)
        ),
    ]
    ids = ["general", "credential", *(f"decoy-{index}" for index in range(18))]
    documents = [
        "general production note",
        "ARK_API_KEY credential reference",
        *(f"unrelated material {index}" for index in range(18)),
    ]
    null_vector = fake_embedding.embed_query(select_dense_null_query("ARK_API_KEY"))

    class HybridCollection:
        def count(self) -> int:
            return 20

        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [null_vector]:
                return {"distances": [[0.05, *([0.8] * 19)]]}
            assert kwargs["n_results"] == 20
            return {
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [[0.1, 0.4, *([0.8] * 18)]],
            }

        def get(self, **kwargs):
            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
            }

    class HybridStore:
        def get_collection(self, name: str) -> HybridCollection:
            assert name == "agent_memory_experience"
            return HybridCollection()

    monkeypatch.setattr(retrieval_module, "load_index", lambda *_: HybridStore())

    hits = search(
        "ARK_API_KEY",
        top_k=2,
        index_path=idx,
        embedding=fake_embedding,
    )

    assert [hit.source for hit in hits] == ["docs/credential.md"]
    assert hits[0].dense_score == pytest.approx(0.6)
    assert hits[0].lexical_score > 0
    assert hits[0].lexical_relevance_score >= 0.7
    assert hits[0].admission_lane == "lexical"
    assert hits[0].score >= 0.7
    assert all(hit.score >= 0.7 for hit in hits)

    path_hits = search(
        "docs/credential.md",
        top_k=2,
        index_path=idx,
        embedding=fake_embedding,
    )

    assert path_hits[0].source == "docs/credential.md"
    assert path_hits[0].lexical_relevance_score >= 0.7


def test_hybrid_primitives_match_identifiers_and_chinese_bigrams() -> None:
    identifier_matches = rank_bm25(
        "ARK_API_KEY",
        {
            "credential": "Use the ARK_API_KEY credential reference.",
            "general": "General production guidance.",
        },
        2,
    )
    chinese_matches = rank_bm25(
        "连续性",
        {
            "continuity": "镜头连续性检查",
            "render": "渲染输出",
        },
        2,
    )
    fusion = reciprocal_rank_fusion(
        ((["dense-only", "both"], 1.0), (["both"], 1.0)),
        rank_constant=60,
    )

    assert [match.chunk_id for match in identifier_matches] == ["credential"]
    assert [match.chunk_id for match in chinese_matches] == ["continuity"]
    assert fusion["both"] > fusion["dense-only"]
    assert lexical_relevance_score(0.182322) < 0.7


def test_dense_null_probe_matches_query_writing_system() -> None:
    assert select_dense_null_query("recovery contract") == (
        "zzzxqv_nonexistent_74291"
    )
    assert select_dense_null_query("如何恢复状态") == "与输入无关的随机问题_68243"


def test_weak_common_lexical_match_does_not_bypass_threshold() -> None:
    class CommonTermCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[1.0]]:
                return {"distances": [[0.9, 0.9]]}
            return {
                "ids": [["first", "second"]],
                "documents": [["the first", "the second"]],
                "metadatas": [[
                    {"source": "docs/first.md", "chunk_index": 0},
                    {"source": "docs/second.md", "chunk_index": 0},
                ]],
                "distances": [[0.9, 0.9]],
            }

        def get(self, **kwargs):
            return {
                "ids": ["first", "second"],
                "documents": ["the first", "the second"],
                "metadatas": [
                    {"source": "docs/first.md", "chunk_index": 0},
                    {"source": "docs/second.md", "chunk_index": 0},
                ],
            }

    hits = retrieval_module._search_collection(
        query="the",
        query_vector=[0.0],
        null_query_vector=[1.0],
        collection=CommonTermCollection(),
        available=2,
        limit=2,
        corpus_kind="experience",
        default_authority="advisory_experience",
    )

    assert hits == []


@pytest.mark.parametrize(
    ("dense_scores", "null_score", "expected_sources"),
    [
        ([0.85, 0.83], 0.86, []),
        ([0.90, 0.899], 0.84, []),
        ([0.894879, 0.891401], 0.888775, ["docs/first.md"]),
        ([0.90, 0.83], 0.84, ["docs/first.md"]),
    ],
    ids=[
        "below-null",
        "weak-top1-margin",
        "project-corpus-positive",
        "answerable",
    ],
)
def test_dense_lane_requires_null_excess_and_top1_margin(
    dense_scores: list[float],
    null_score: float,
    expected_sources: list[str],
) -> None:
    class DenseGateCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[0.0]]:
                return {"distances": [[1.0 - null_score] * 2]}
            return {
                "ids": [["first", "second"]],
                "documents": [["first candidate", "second candidate"]],
                "metadatas": [[
                    {"source": "docs/first.md", "chunk_index": 0},
                    {"source": "docs/second.md", "chunk_index": 0},
                ]],
                "distances": [[1.0 - score for score in dense_scores]],
            }

        def get(self, **kwargs):
            return {
                "ids": ["first", "second"],
                "documents": ["first candidate", "second candidate"],
                "metadatas": [
                    {"source": "docs/first.md", "chunk_index": 0},
                    {"source": "docs/second.md", "chunk_index": 0},
                ],
            }

    hits = retrieval_module._search_collection(
        query="unseen-query",
        query_vector=[1.0],
        null_query_vector=[0.0],
        collection=DenseGateCollection(),
        available=2,
        limit=2,
        corpus_kind="experience",
        default_authority="advisory_experience",
    )

    assert [hit.source for hit in hits] == expected_sources
    if hits:
        assert hits[0].admission_lane == "dense"
        assert hits[0].dense_null_score == pytest.approx(null_score)
        assert hits[0].dense_null_excess == pytest.approx(
            dense_scores[0] - null_score
        )
        assert hits[0].dense_top1_margin == pytest.approx(
            dense_scores[0] - dense_scores[1]
        )
        assert hits[0].score == pytest.approx(dense_scores[0])


def test_dense_null_calibration_uses_same_ann_candidate_budget() -> None:
    ids = [f"chunk-{index:02d}" for index in range(30)]
    documents = [f"candidate {index}" for index in range(30)]
    metadatas = [
        {"source": f"docs/{index}.md", "chunk_index": 0}
        for index in range(30)
    ]

    class ApproximateCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[0.0]]:
                if kwargs["n_results"] == 1:
                    return {"distances": [[0.2]]}
                assert kwargs["n_results"] == 30
                return {"distances": [[0.1, *([0.11] * 29)]]}
            assert kwargs["query_embeddings"] == [[1.0]]
            assert kwargs["n_results"] == 30
            return {
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [[0.1, 0.105, *([0.2] * 28)]],
            }

        def get(self, **kwargs):
            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
            }

    hits = retrieval_module._search_collection(
        query="no-match",
        query_vector=[1.0],
        null_query_vector=[0.0],
        collection=ApproximateCollection(),
        available=30,
        limit=8,
        corpus_kind="experience",
        default_authority="advisory_experience",
    )

    assert hits == []


def test_dense_null_calibration_requires_full_candidate_result() -> None:
    class IncompleteNullCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[0.0]]:
                return {"distances": [[0.2]]}
            return {
                "ids": [["first", "second"]],
                "documents": [["first candidate", "second candidate"]],
                "metadatas": [[
                    {"source": "docs/first.md", "chunk_index": 0},
                    {"source": "docs/second.md", "chunk_index": 0},
                ]],
                "distances": [[0.1, 0.2]],
            }

        def get(self, **kwargs):
            return {
                "ids": ["first", "second"],
                "documents": ["first candidate", "second candidate"],
                "metadatas": [
                    {"source": "docs/first.md", "chunk_index": 0},
                    {"source": "docs/second.md", "chunk_index": 0},
                ],
            }

    with pytest.raises(ValueError, match="candidate budget"):
        retrieval_module._search_collection(
            query="no-match",
            query_vector=[1.0],
            null_query_vector=[0.0],
            collection=IncompleteNullCollection(),
            available=2,
            limit=2,
            corpus_kind="experience",
            default_authority="advisory_experience",
        )


@pytest.mark.parametrize(
    ("dense_score", "null_score", "expected_sources"),
    [
        (0.82, 0.81, ["docs/only.md"]),
        (0.814, 0.81, []),
    ],
    ids=["clears-null-excess", "below-null-excess"],
)
def test_dense_single_candidate_uses_null_excess_without_fabricated_margin(
    dense_score: float,
    null_score: float,
    expected_sources: list[str],
) -> None:
    class SingleCandidateCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[0.0]]:
                return {"distances": [[1.0 - null_score]]}
            return {
                "ids": [["only"]],
                "documents": [["only candidate"]],
                "metadatas": [[
                    {"source": "docs/only.md", "chunk_index": 0},
                ]],
                "distances": [[1.0 - dense_score]],
            }

        def get(self, **kwargs):
            return {
                "ids": ["only"],
                "documents": ["only candidate"],
                "metadatas": [
                    {"source": "docs/only.md", "chunk_index": 0},
                ],
            }

    hits = retrieval_module._search_collection(
        query="unseen-query",
        query_vector=[1.0],
        null_query_vector=[0.0],
        collection=SingleCandidateCollection(),
        available=1,
        limit=1,
        corpus_kind="experience",
        default_authority="advisory_experience",
    )

    assert [hit.source for hit in hits] == expected_sources
    if hits:
        assert hits[0].dense_null_excess == pytest.approx(
            dense_score - null_score
        )
        assert hits[0].dense_top1_margin == 0.0
        assert hits[0].admission_lane == "dense"


def test_partial_cjk_bigram_does_not_admit_lexical_lane() -> None:
    ids = ["partial", *(f"decoy-{index}" for index in range(19))]
    documents = ["存在", *(f"无关材料{index}" for index in range(19))]
    metadatas = [
        {"source": f"docs/{chunk_id}.md", "chunk_index": 0}
        for chunk_id in ids
    ]

    class PartialBigramCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[0.0]]:
                return {"distances": [[0.16] * 20]}
            return {
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [[0.15, 0.151, *([0.2] * 18)]],
            }

        def get(self, **kwargs):
            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
            }

    hits = retrieval_module._search_collection(
        query="不存在的紫色大象量子果园",
        query_vector=[1.0],
        null_query_vector=[0.0],
        collection=PartialBigramCollection(),
        available=20,
        limit=8,
        corpus_kind="experience",
        default_authority="advisory_experience",
    )

    assert hits == []


def test_hybrid_uses_top_k_30_and_returns_top_n_8() -> None:
    assert HYBRID_CANDIDATE_TOP_K == 30
    assert DEFAULT_TOP_N == 8

    ids = [f"chunk-{index:02d}" for index in range(40)]
    documents = [f"needle candidate {index}" for index in range(40)]
    metadatas = [
        {
            "source": f"docs/{index}.md",
            "title": f"Candidate {index}",
            "chunk_index": 0,
        }
        for index in range(40)
    ]

    class SizedCollection:
        def query(self, **kwargs):
            if kwargs["query_embeddings"] == [[1.0]]:
                return {"distances": [[0.5] * 30]}
            assert kwargs["n_results"] == 30
            return {
                "ids": [ids[:30]],
                "documents": [documents[:30]],
                "metadatas": [metadatas[:30]],
                "distances": [[0.1, *([0.12] * 29)]],
            }

        def get(self, **kwargs):
            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
            }

    hits = retrieval_module._search_collection(
        query="needle",
        query_vector=[0.0],
        null_query_vector=[1.0],
        collection=SizedCollection(),
        available=40,
        limit=8,
        corpus_kind="experience",
        default_authority="advisory_experience",
    )

    assert len(hits) == 8


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
            admission_lane="lexical",
        )
    ]
    out = format_text(hits)
    assert "Relevant prior records:" in out
    assert "docs/record_for_agent/x.md" in out
    assert "Symptom" in out
    assert "some body text" in out
    assert "admission_lane: lexical" in out


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

    Skipped when the pinned multilingual E5 model cache is missing
    on this machine.  Real end-to-end semantic search is verified by the
    CLI smoke command, not by this unit test.
    """
    from pathlib import Path

    from ai_video.agent_memory.config import DEFAULT_MODEL_DIR

    if not Path(DEFAULT_MODEL_DIR).expanduser().is_dir():
        pytest.skip("local multilingual E5 model cache not present on this machine")
    emb = LocalOnnxMiniLMEmbeddings()
    v = emb.embed_query("hello world")
    assert len(v) == 384
    # Same text -> same vector
    assert emb.embed_query("hello world") == v


# ---------------------------------------------------------------------------
# scoped corpora + index identity
# ---------------------------------------------------------------------------


@pytest.fixture
def scoped_corpora(tmp_path: Path) -> tuple[object, object]:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    assert CorpusSpec is not None, "CorpusSpec contract is not implemented"
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity Recovery\n\n"
        "Date: 2026-08-21\n\n"
        "## Fix\nUse the exact terminal frame for the next shot.\n",
        encoding="utf-8",
    )

    superpowers_root = tmp_path / "superpowers"
    (superpowers_root / "specs").mkdir(parents=True)
    (superpowers_root / "specs" / "state-commit.md").write_text(
        "# State Commit Contract\n\n"
        "Status: Superseded\n\n"
        "## Recovery\nProductionStateCommitter owns explicit recovery.\n",
        encoding="utf-8",
    )
    return (
        CorpusSpec.experience(experience_root),
        CorpusSpec.superpowers(superpowers_root),
    )


@pytest.fixture
def project_docs_corpora(tmp_path: Path) -> tuple[Path, tuple[object, object, object]]:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    assert CorpusSpec is not None, "CorpusSpec contract is not implemented"
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "agent-primary-contract-matrix.md").write_text(
        "# Contract Matrix\n\nCurrent single-owner routing.\n",
        encoding="utf-8",
    )
    (docs_root / "v0.2-runtime-baseline.md").write_text(
        "# Runtime Baseline\n\nCurrent executable runtime evidence.\n",
        encoding="utf-8",
    )
    (docs_root / "v0.2-agentic-production-roadmap.md").write_text(
        "# Roadmap\n\nFuture dependency gates.\n",
        encoding="utf-8",
    )
    (docs_root / "ignored.html").write_text("not markdown", encoding="utf-8")
    nested = docs_root / "unclassified"
    nested.mkdir()
    (nested / "not-current.md").write_text(
        "# Nested document\n\nMust not inherit current authority.\n",
        encoding="utf-8",
    )
    research_root = docs_root / "research"
    research_root.mkdir()
    (research_root / "provider.md").write_text(
        "---\nauthority: current_runtime_truth\n---\n"
        "# Provider Research\n\nExternal provider assessment.\n",
        encoding="utf-8",
    )
    deferred_root = docs_root / "when_to_do"
    deferred_root.mkdir()
    (deferred_root / "later.md").write_text(
        "# Deferred Decision\n\nStart only after the named gate passes.\n",
        encoding="utf-8",
    )
    return docs_root, (
        CorpusSpec.current_docs(docs_root),
        CorpusSpec.research(research_root),
        CorpusSpec.deferred(deferred_root),
    )


def test_scoped_documents_preserve_authority_and_status(scoped_corpora) -> None:
    experience, superpowers = scoped_corpora
    exp_doc = load_documents(experience.root, corpus=experience)[0]
    spec_doc = load_documents(superpowers.root, corpus=superpowers)[0]

    assert exp_doc.metadata["corpus_kind"] == "experience"
    assert exp_doc.metadata["authority"] == "advisory_experience"
    assert exp_doc.metadata["document_kind"] == "experience_record"
    assert spec_doc.metadata["corpus_kind"] == "superpowers"
    assert spec_doc.metadata["authority"] == "historical_design_plan"
    assert spec_doc.metadata["document_kind"] == "spec"
    assert spec_doc.metadata["status"] == "Superseded"


def test_learning_subdirectory_has_distinct_non_spoofable_authority(
    tmp_path: Path,
) -> None:
    root = tmp_path / "record_for_agent"
    learning = root / "learning"
    learning.mkdir(parents=True)
    (root / "ordinary.md").write_text(
        "---\n"
        "authority: advisory_learning\n"
        "document_kind: learning_claim\n"
        "---\n"
        "# Ordinary experience\n\nHistorical evidence.\n",
        encoding="utf-8",
    )
    (learning / "h3-anchor.md").write_text(
        "---\n"
        "authority: current_runtime_truth\n"
        "document_kind: runtime_contract\n"
        "---\n"
        "# H3 Anchor Learning\n\n"
        "Scoped current claim with pending confirmation.\n",
        encoding="utf-8",
    )
    corpus = corpus_module.CorpusSpec.experience(root)

    documents = {
        Path(str(document.metadata["source"])).name: document
        for document in load_documents(root, corpus=corpus)
    }

    ordinary = documents["ordinary.md"]
    assert ordinary.metadata["authority"] == "advisory_experience"
    assert ordinary.metadata["document_kind"] == "experience_record"
    claim = documents["h3-anchor.md"]
    assert claim.metadata["corpus_kind"] == "experience"
    assert claim.metadata["authority"] == "advisory_learning"
    assert claim.metadata["document_kind"] == "learning_claim"


def test_experience_record_classification_metadata_survives_all_chunks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "record_for_agent"
    root.mkdir()
    (root / "eligible.md").write_text(
        "---\n"
        "record_kind: media_experiment\n"
        "topic_id: h3-conditioning-attribution\n"
        "learning_eligibility: eligible\n"
        'evidence_index_version: "1"\n'
        "authority: current_runtime_truth\n"
        "document_kind: runtime_contract\n"
        "---\n"
        "# Eligible Record\n\n"
        "## Attempt A\n\nObserved endpoint replacement.\n\n"
        "## Attempt B\n\nObserved a distinct controlled arm.\n",
        encoding="utf-8",
    )
    corpus = corpus_module.CorpusSpec.experience(root)

    document = load_documents(root, corpus=corpus)[0]
    chunks = chunk_documents([document])

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.metadata["record_kind"] == "media_experiment"
        assert chunk.metadata["topic_id"] == "h3-conditioning-attribution"
        assert chunk.metadata["learning_eligibility"] == "eligible"
        assert chunk.metadata["evidence_index_version"] == '"1"'
        assert chunk.metadata["authority"] == "advisory_experience"
        assert chunk.metadata["document_kind"] == "experience_record"


def test_experience_search_projects_allowlisted_record_metadata_without_counting(
    tmp_path: Path,
    fake_embedding,
) -> None:
    root = tmp_path / "record_for_agent"
    root.mkdir()
    (root / "eligible.md").write_text(
        "---\n"
        "record_kind: media_experiment\n"
        "topic_id: h3-conditioning-attribution\n"
        "learning_eligibility: eligible\n"
        'evidence_index_version: "1"\n'
        "authority: current_runtime_truth\n"
        "document_kind: runtime_contract\n"
        "---\n"
        "# H3 Conditioning Attribution\n\n"
        "## Technical Evidence\n\n"
        "conditioning attribution endpoint replacement evidence.\n\n"
        "## Human Evidence\n\n"
        "conditioning attribution human motion evidence.\n",
        encoding="utf-8",
    )
    (root / "legacy.md").write_text(
        "# Legacy Record\n\nLegacy unrelated narrative.\n", encoding="utf-8"
    )
    corpus = corpus_module.CorpusSpec.experience(root)
    index_path = tmp_path / "index"
    index_module.build_scoped_index((corpus,), index_path, fake_embedding)

    hits = search(
        "conditioning attribution evidence",
        top_k=8,
        scope="experience",
        corpora=(corpus,),
        index_path=index_path,
        embedding=fake_embedding,
    )

    eligible_hits = [hit for hit in hits if hit.source.endswith("eligible.md")]
    assert len(eligible_hits) >= 2
    assert {
        (
            hit.record_kind,
            hit.topic_id,
            hit.learning_eligibility,
            hit.evidence_index_version,
        )
        for hit in eligible_hits
    } == {("media_experiment", "h3-conditioning-attribution", "eligible", "1")}
    assert all(hit.authority == "advisory_experience" for hit in eligible_hits)
    assert all(hit.document_kind == "experience_record" for hit in eligible_hits)
    rendered = format_text(eligible_hits)
    assert "record_kind: media_experiment" in rendered
    assert "learning_eligibility: eligible" in rendered
    assert "classification only; not evidence independence or admission" in rendered
    assert "independent evidence count" not in rendered
    payload = eligible_hits[0].to_dict()
    assert payload["topic_id"] == "h3-conditioning-attribution"
    assert payload["evidence_index_version"] == "1"


def test_legacy_hit_supplemental_metadata_defaults_preserve_text_output() -> None:
    hit = Hit(
        source="docs/record_for_agent/legacy.md",
        title="Legacy",
        section="",
        score=0.91,
        excerpt="Historical narrative.",
        chunk_index=0,
        h1="Legacy",
        h2="",
        h3="",
        date="2026-08-20",
        admission_lane="lexical",
    )

    rendered = format_text((hit,))
    payload = hit.to_dict()

    assert hit.record_kind == ""
    assert hit.topic_id == ""
    assert hit.learning_eligibility == ""
    assert hit.evidence_index_version == ""
    assert "record_kind:" not in rendered
    assert payload["record_kind"] == ""


def test_learning_authority_is_rendered_as_confirmable_not_executable() -> None:
    hit = Hit(
        source="docs/record_for_agent/learning/h3-anchor.md",
        title="H3 Anchor Learning",
        section="Evidence Assessment",
        score=0.94,
        excerpt="Bounded claim.",
        chunk_index=0,
        h1="H3 Anchor Learning",
        h2="Evidence Assessment",
        h3="",
        date="2026-08-28",
        corpus_kind="experience",
        authority="advisory_learning",
        document_kind="learning_claim",
        admission_lane="lexical",
    )

    rendered = format_text((hit,))

    assert "authority: advisory learning claim" in rendered
    assert "verify confirmation and adoption state" in rendered
    assert "not execution authorization" in rendered


def test_experience_search_preserves_learning_claim_metadata(
    tmp_path: Path,
    fake_embedding,
) -> None:
    root = tmp_path / "record_for_agent"
    learning = root / "learning"
    learning.mkdir(parents=True)
    (learning / "terminal-anchor.md").write_text(
        "# Terminal Anchor Claim\n\n"
        "## Failure Pattern\n"
        "Incompatible terminal anchor causes scene replacement.\n",
        encoding="utf-8",
    )
    corpus = corpus_module.CorpusSpec.experience(root)
    index_path = tmp_path / "index"
    index_module.build_scoped_index((corpus,), index_path, fake_embedding)

    hits = search(
        "incompatible terminal anchor scene replacement",
        top_k=4,
        scope="experience",
        corpora=(corpus,),
        index_path=index_path,
        embedding=fake_embedding,
    )

    claim = next(hit for hit in hits if hit.document_kind == "learning_claim")
    assert claim.authority == "advisory_learning"
    assert claim.corpus_kind == "experience"


def test_project_docs_are_partitioned_by_path_and_authority(
    project_docs_corpora,
) -> None:
    _, (current_docs, research, deferred) = project_docs_corpora

    current = load_documents(current_docs.root, corpus=current_docs)
    research_docs = load_documents(research.root, corpus=research)
    deferred_docs = load_documents(deferred.root, corpus=deferred)

    assert {doc.metadata["document_kind"] for doc in current} == {
        "contract_matrix",
        "runtime_baseline",
        "roadmap",
    }
    assert {doc.metadata["authority"] for doc in current} == {
        "current_project_contract",
        "current_runtime_baseline",
        "current_roadmap",
    }
    assert all(doc.metadata["corpus_kind"] == "current_docs" for doc in current)
    assert {doc.metadata["source"] for doc in current} == {
        str(current_docs.root / "agent-primary-contract-matrix.md"),
        str(current_docs.root / "v0.2-runtime-baseline.md"),
        str(current_docs.root / "v0.2-agentic-production-roadmap.md"),
    }
    assert research_docs[0].metadata["authority"] == "advisory_research"
    assert research_docs[0].metadata["document_kind"] == "research_note"
    assert deferred_docs[0].metadata["authority"] == "deferred_decision_advisory"
    assert deferred_docs[0].metadata["document_kind"] == "deferred_decision"


def test_current_docs_digest_excludes_nested_authority_lanes(
    project_docs_corpora,
) -> None:
    docs_root, (current_docs, _, _) = project_docs_corpora
    before = index_module.corpus_digest(current_docs.root, current_docs)

    (docs_root / "research" / "second.md").write_text(
        "# More Research\n\nMust stay outside current docs.\n",
        encoding="utf-8",
    )
    assert index_module.corpus_digest(current_docs.root, current_docs) == before

    (docs_root / "v0.2-runtime-baseline.md").write_text(
        "# Runtime Baseline\n\nFresh current evidence.\n",
        encoding="utf-8",
    )
    assert index_module.corpus_digest(current_docs.root, current_docs) != before


def test_all_scope_uses_stable_five_corpus_quota(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    fake_embedding,
    monkeypatch,
) -> None:
    _, project_corpora = project_docs_corpora
    corpora = (*scoped_corpora, *project_corpora)
    idx = tmp_path / "idx"
    index_module.build_scoped_index(corpora, idx, fake_embedding)
    observed: dict[str, int] = {}

    def record_search_collection(**kwargs):
        observed[kwargs["corpus_kind"]] = kwargs["limit"]
        return []

    monkeypatch.setattr(
        retrieval_module,
        "_search_collection",
        record_search_collection,
    )

    assert search(
        "project decision",
        top_k=8,
        scope="all",
        corpora=corpora,
        index_path=idx,
        embedding=fake_embedding,
    ) == []
    assert observed == {
        "experience": 2,
        "superpowers": 2,
        "current_docs": 2,
        "research": 1,
        "deferred": 1,
    }
    manifest = index_module.read_index_manifest(idx)
    assert manifest.schema_version == 1
    assert {item.kind for item in manifest.corpora} == set(observed)


def test_frontmatter_cannot_override_corpus_authority(tmp_path: Path) -> None:
    root = tmp_path / "superpowers"
    root.mkdir()
    (root / "hostile.md").write_text(
        "---\n"
        "authority: current_runtime_truth\n"
        "corpus_kind: experience\n"
        "document_kind: runtime_contract\n"
        "---\n"
        "# Historical proposal\n",
        encoding="utf-8",
    )
    corpus = corpus_module.CorpusSpec.superpowers(root)

    document = load_documents(root, corpus=corpus)[0]

    assert document.metadata["authority"] == "historical_design_plan"
    assert document.metadata["corpus_kind"] == "superpowers"
    assert document.metadata["document_kind"] == "design_note"


def test_scoped_index_manifest_binds_corpora_and_embedding(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    read_index_manifest = getattr(index_module, "read_index_manifest", None)
    assert build_scoped_index is not None
    assert read_index_manifest is not None
    count = build_scoped_index(
        corpora=scoped_corpora,
        index_path=idx,
        embedding=fake_embedding,
        batch_size=2,
    )

    assert count > 0
    manifest = read_index_manifest(idx)
    assert manifest.schema_version == 1
    assert {item.kind for item in manifest.corpora} == {
        "experience",
        "superpowers",
    }
    assert manifest.embedding.dimension == 64
    assert manifest.embedding.backend == "fake"
    assert all(item.source_sha256 for item in manifest.corpora)


def test_scoped_search_rejects_stale_corpus_without_rebuild(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    assert build_scoped_index is not None
    build_scoped_index(
        corpora=scoped_corpora,
        index_path=idx,
        embedding=fake_embedding,
    )
    experience, _ = scoped_corpora
    manifest_before = (idx / "manifest.json").read_bytes()
    (experience.root / "continuity.md").write_text(
        "# Changed after index build\n\nThe stale corpus contains relay motion.\n",
        encoding="utf-8",
    )

    with pytest.raises(index_module.IndexMismatchError, match="stale corpus"):
        search(
            "relay motion",
            scope="experience",
            corpora=scoped_corpora,
            index_path=idx,
            embedding=fake_embedding,
        )

    assert (idx / "manifest.json").read_bytes() == manifest_before


def test_scoped_search_does_not_build_missing_project_index(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="build.*first"):
        search(
            "terminal frame continuity",
            scope="experience",
            corpora=scoped_corpora,
            index_path=idx,
            embedding=fake_embedding,
        )

    assert not idx.exists()


def test_scoped_search_rejects_requested_scope_missing_from_index(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    experience, superpowers = scoped_corpora
    idx = tmp_path / "idx"
    index_module.build_scoped_index((experience,), idx, fake_embedding)

    with pytest.raises(index_module.IndexMismatchError, match="not present"):
        search(
            "ProductionStateCommitter recovery",
            scope="superpowers",
            corpora=scoped_corpora,
            index_path=idx,
            embedding=fake_embedding,
        )

    assert {
        item.kind for item in index_module.read_index_manifest(idx).corpora
    } == {"experience"}


def test_scoped_search_keeps_embedding_identity_mismatch_fail_closed(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    index_module.build_scoped_index(scoped_corpora, idx, fake_embedding)
    replacement = DeterministicFakeEmbeddings(size=32)
    IndexMismatchError = getattr(index_module, "IndexMismatchError", RuntimeError)

    with pytest.raises(IndexMismatchError, match="embedding identity mismatch"):
        search(
            "terminal frame continuity",
            scope="experience",
            corpora=scoped_corpora,
            index_path=idx,
            embedding=replacement,
        )

    assert index_module.read_index_manifest(idx).embedding.dimension == 64


def test_scoped_search_keeps_partial_collection_fail_closed(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    experience, _ = scoped_corpora
    idx = tmp_path / "idx"
    index_module.build_scoped_index((experience,), idx, fake_embedding)
    collection = index_module.load_index(idx, fake_embedding).get_collection(
        experience.collection_name
    )
    collection.delete(ids=[collection.get()["ids"][0]])
    IndexMismatchError = getattr(index_module, "IndexMismatchError", RuntimeError)

    with pytest.raises(IndexMismatchError, match="chunk count mismatch"):
        search(
            "terminal frame continuity",
            scope="experience",
            corpora=(experience,),
            index_path=idx,
            embedding=fake_embedding,
        )


def test_scoped_search_does_not_hide_corruption_behind_stale_corpus_refresh(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    experience, _ = scoped_corpora
    idx = tmp_path / "idx"
    index_module.build_scoped_index((experience,), idx, fake_embedding)
    original_digest = index_module.read_index_manifest(
        idx
    ).corpora[0].source_sha256
    collection = index_module.load_index(idx, fake_embedding).get_collection(
        experience.collection_name
    )
    collection.delete(ids=[collection.get()["ids"][0]])
    (experience.root / "continuity.md").write_text(
        "# Changed while index is corrupt\n\nNew corpus bytes.\n",
        encoding="utf-8",
    )
    IndexMismatchError = getattr(index_module, "IndexMismatchError", RuntimeError)

    with pytest.raises(IndexMismatchError, match="chunk count mismatch"):
        search(
            "new corpus bytes",
            scope="experience",
            corpora=(experience,),
            index_path=idx,
            embedding=fake_embedding,
        )

    assert (
        index_module.read_index_manifest(idx).corpora[0].source_sha256
        == original_digest
    )


def test_search_without_corpus_roots_rejects_partial_index(
    sample_corpus: Path, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    index_module.build_index(sample_corpus, idx, fake_embedding)
    collection = index_module.load_index(idx, fake_embedding).get_collection(
        "agent_memory_experience"
    )
    collection.delete(ids=[collection.get(limit=1)["ids"][0]])

    with pytest.raises(index_module.IndexMismatchError, match="chunk count mismatch"):
        search(
            "continuity",
            index_path=idx,
            embedding=fake_embedding,
        )


def test_build_rejects_corpus_changed_while_embedding(
    scoped_corpora, tmp_path: Path, fake_embedding, monkeypatch
) -> None:
    idx = tmp_path / "idx"
    experience, _ = scoped_corpora
    original = fake_embedding.embed_documents
    mutated = False

    def mutate_after_first_batch(texts):
        nonlocal mutated
        vectors = original(texts)
        if not mutated:
            mutated = True
            (experience.root / "continuity.md").write_text(
                "# Changed during build\n",
                encoding="utf-8",
            )
        return vectors

    monkeypatch.setattr(fake_embedding, "embed_documents", mutate_after_first_batch)

    with pytest.raises(RuntimeError, match="changed during index build"):
        index_module.build_scoped_index(
            corpora=scoped_corpora,
            index_path=idx,
            embedding=fake_embedding,
            batch_size=1,
        )
    assert not idx.exists()
    staging_prefix = str(idx.parent / f".{idx.name}.staging-")
    assert not any(
        identifier.startswith(staging_prefix)
        for identifier in index_module.SharedSystemClient._identifier_to_system
    )


def test_scoped_search_returns_both_corpora_with_truth_labels(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    assert build_scoped_index is not None
    build_scoped_index(
        corpora=scoped_corpora,
        index_path=idx,
        embedding=fake_embedding,
    )

    hits = search(
        "recovery terminal frame",
        top_k=4,
        scope="all",
        corpora=scoped_corpora,
        index_path=idx,
        embedding=fake_embedding,
    )
    assert {hit.corpus_kind for hit in hits} == {"experience", "superpowers"}
    rendered = format_text(hits)
    assert "advisory experience" in rendered
    assert "historical design/plan; not runtime truth" in rendered


def test_local_embedding_batches_and_uses_e5_prefixes(monkeypatch, tmp_path) -> None:
    model_dir = tmp_path / "model"
    (model_dir / "onnx").mkdir(parents=True)
    (model_dir / "onnx" / "model.onnx").write_bytes(b"fixture")

    class FakeTokenizer:
        def __call__(self, texts, **kwargs):
            calls.append(list(texts))
            import numpy as np

            width = 3
            return {
                "input_ids": np.ones((len(texts), width), dtype=np.int64),
                "attention_mask": np.ones((len(texts), width), dtype=np.int64),
            }

    class FakeInput:
        name = "input_ids"

    class FakeMaskInput:
        name = "attention_mask"

    class FakeSession:
        def __init__(self, *args, **kwargs):
            pass

        def get_inputs(self):
            return [FakeInput(), FakeMaskInput()]

        def run(self, _, feeds):
            import numpy as np

            batch, width = feeds["input_ids"].shape
            return [np.ones((batch, width, 4), dtype=np.float32)]

    calls: list[list[str]] = []
    monkeypatch.setattr(
        "transformers.AutoTokenizer.from_pretrained",
        lambda *args, **kwargs: FakeTokenizer(),
    )
    monkeypatch.setattr("onnxruntime.InferenceSession", FakeSession)

    embedding = LocalOnnxMiniLMEmbeddings(
        model_dir=str(model_dir),
        onnx_file="onnx/model.onnx",
        batch_size=2,
    )
    vectors = embedding.embed_documents(["甲", "乙", "丙", "丁", "戊"])
    embedding.embed_query("连续性")

    assert len(vectors) == 5
    assert [len(call) for call in calls] == [2, 2, 1, 1]
    assert all(text.startswith("passage: ") for call in calls[:3] for text in call)
    assert calls[-1] == ["query: 连续性"]


def test_cli_builds_and_searches_all_scopes(
    scoped_corpora, project_docs_corpora, tmp_path: Path, capsys
) -> None:
    experience, superpowers = scoped_corpora
    docs_root, _ = project_docs_corpora
    idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "all",
        "--corpus",
        str(experience.root),
        "--superpowers-corpus",
        str(superpowers.root),
        "--docs-root",
        str(docs_root),
        "--index",
        str(idx),
        "--runs-root",
        str(tmp_path / "missing_runs"),
        "--runs-index",
        str(runs_idx),
    ]
    assert agent_memory_main([*common, "build"]) == 0
    assert agent_memory_main([*common, "search", "recovery", "--json"]) == 0
    output = capsys.readouterr().out
    assert '"corpus_kind": "experience"' in output
    assert '"corpus_kind": "superpowers"' in output
    from ai_video.agent_memory.layout import shard_path

    assert {
        kind
        for kind in (
            "experience",
            "superpowers",
            "current_docs",
            "research",
            "deferred",
        )
        if index_module.read_index_manifest(shard_path(idx, kind)).corpora[0].kind
        == kind
    } == {
        "experience",
        "superpowers",
        "current_docs",
        "research",
        "deferred",
    }


def test_cli_all_scope_queues_only_library_incompatible_shards(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    experience, superpowers = scoped_corpora
    docs_root, _ = project_docs_corpora
    idx = tmp_path / "idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "all",
        "--corpus",
        str(experience.root),
        "--superpowers-corpus",
        str(superpowers.root),
        "--docs-root",
        str(docs_root),
        "--index",
        str(idx),
        "--runs-root",
        str(tmp_path / "missing_runs"),
    ]
    assert agent_memory_main([*common, "build"]) == 0
    capsys.readouterr()

    from ai_video.agent_memory.layout import shard_path

    for kind in ("superpowers", "research"):
        manifest_path = shard_path(idx, kind) / "manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["library_versions"]["chromadb"] = "0.5.23"
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    incompatible_leaves = {
        shard_path(idx, kind).resolve() for kind in ("superpowers", "research")
    }
    original_client = index_module._client

    def reject_migrating_incompatible_leaf(index_path):
        if Path(index_path).resolve() in incompatible_leaves:
            pytest.fail("library-incompatible shards must not open through Chroma")
        return original_client(index_path)

    monkeypatch.setattr(index_module, "_client", reject_migrating_incompatible_leaf)
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )

    result = agent_memory_main([*common, "search", "recovery", "--json"])

    assert result == 3
    assert queued == [("superpowers", "research")]
    assert (
        "library-incompatible Agent Memory shard(s): superpowers, research"
        in capsys.readouterr().err
    )


def test_cli_library_mismatch_does_not_hide_physical_corruption(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    monkeypatch,
) -> None:
    experience, superpowers = scoped_corpora
    docs_root, project_corpora = project_docs_corpora
    idx = tmp_path / "idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "all",
        "--corpus",
        str(experience.root),
        "--superpowers-corpus",
        str(superpowers.root),
        "--docs-root",
        str(docs_root),
        "--index",
        str(idx),
        "--runs-root",
        str(tmp_path / "missing_runs"),
    ]
    assert agent_memory_main([*common, "build"]) == 0

    from ai_video.agent_memory.layout import shard_path

    leaf = shard_path(idx, "superpowers")
    manifest_path = leaf / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["library_versions"]["chromadb"] = "0.5.23"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    research = next(item for item in project_corpora if item.kind == "research")
    research_leaf = shard_path(idx, "research")
    collection = index_module.load_index(
        research_leaf,
        DeterministicFakeEmbeddings(),
    ).get_collection(research.collection_name)
    collection.delete(ids=[collection.get(limit=1)["ids"][0]])
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: pytest.fail("physical corruption must not enqueue"),
    )

    assert agent_memory_main([*common, "search", "recovery", "--json"]) == 2


def test_cli_library_mismatch_race_queues_only_changed_shard(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    monkeypatch,
) -> None:
    from ai_video.agent_memory.manifest import LibraryVersionMismatchError

    experience, superpowers = scoped_corpora
    docs_root, _ = project_docs_corpora
    idx = tmp_path / "idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "all",
        "--corpus",
        str(experience.root),
        "--superpowers-corpus",
        str(superpowers.root),
        "--docs-root",
        str(docs_root),
        "--index",
        str(idx),
        "--runs-root",
        str(tmp_path / "missing_runs"),
    ]
    assert agent_memory_main([*common, "build"]) == 0

    original_validate = retrieval_module.validate_scoped_index
    validation_calls: dict[str, int] = {}

    def replace_research_after_preflight(corpora, index_path, embedding):
        kind = corpora[0].kind
        validation_calls[kind] = validation_calls.get(kind, 0) + 1
        if kind == "research" and validation_calls[kind] == 2:
            manifest_path = Path(index_path) / "manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["library_versions"]["chromadb"] = "0.5.23"
            manifest_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            raise LibraryVersionMismatchError()
        return original_validate(corpora, index_path, embedding)

    monkeypatch.setattr(
        retrieval_module,
        "validate_scoped_index",
        replace_research_after_preflight,
    )
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )

    assert agent_memory_main([*common, "search", "recovery", "--json"]) == 3
    assert queued == [("research",)]


def test_cli_library_mismatch_race_does_not_hide_corruption(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    monkeypatch,
) -> None:
    from ai_video.agent_memory.manifest import LibraryVersionMismatchError

    experience, superpowers = scoped_corpora
    docs_root, project_corpora = project_docs_corpora
    research = next(item for item in project_corpora if item.kind == "research")
    idx = tmp_path / "idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "all",
        "--corpus",
        str(experience.root),
        "--superpowers-corpus",
        str(superpowers.root),
        "--docs-root",
        str(docs_root),
        "--index",
        str(idx),
        "--runs-root",
        str(tmp_path / "missing_runs"),
    ]
    assert agent_memory_main([*common, "build"]) == 0

    original_validate = retrieval_module.validate_scoped_index
    validation_calls: dict[str, int] = {}

    def replace_corrupt_research_after_preflight(corpora, index_path, embedding):
        kind = corpora[0].kind
        validation_calls[kind] = validation_calls.get(kind, 0) + 1
        if kind == "research" and validation_calls[kind] == 2:
            manifest_path = Path(index_path) / "manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["library_versions"]["chromadb"] = "0.5.23"
            manifest_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            collection = index_module.load_index(
                index_path,
                embedding,
            ).get_collection(research.collection_name)
            collection.delete(ids=[collection.get(limit=1)["ids"][0]])
            raise LibraryVersionMismatchError()
        return original_validate(corpora, index_path, embedding)

    monkeypatch.setattr(
        retrieval_module,
        "validate_scoped_index",
        replace_corrupt_research_after_preflight,
    )
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: pytest.fail("physical corruption must not enqueue"),
    )

    assert agent_memory_main([*common, "search", "recovery", "--json"]) == 2


def test_cli_build_materializes_run_summaries_before_search(
    sample_runs_root: Path, tmp_path: Path, capsys
) -> None:
    experience = tmp_path / "record_for_agent"
    experience.mkdir()
    (experience / "continuity.md").write_text(
        "# Continuity\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "experience",
        "--corpus",
        str(experience),
        "--runs-root",
        str(sample_runs_root),
        "--index",
        str(main_idx),
        "--runs-index",
        str(runs_idx),
    ]
    assert agent_memory_main([*common, "build"]) == 0
    capsys.readouterr()
    assert runs_idx.is_dir()

    assert agent_memory_main(
        [*common, "search", "continuity failure", "--top-k", "8", "--json"]
    ) == 0
    hits = json.loads(capsys.readouterr().out)

    assert any(hit["document_kind"] == "run_summary" for hit in hits)
    assert runs_idx.is_dir()


def test_cli_build_validates_run_index_path_before_main_index_write(
    sample_runs_root: Path, tmp_path: Path, capsys
) -> None:
    experience = tmp_path / "record_for_agent"
    experience.mkdir()
    (experience / "continuity.md").write_text(
        "# Continuity\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    main_idx = tmp_path / "idx"

    assert agent_memory_main(
        [
            "--embedding",
            "fake",
            "--scope",
            "experience",
            "--corpus",
            str(experience),
            "--runs-root",
            str(sample_runs_root),
            "--index",
            str(main_idx),
            "--runs-index",
            str(main_idx),
            "build",
        ]
    ) == 2

    assert "must not overlap" in capsys.readouterr().err
    assert not main_idx.exists()


def test_search_rejects_missing_run_summary_index_without_build(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    experience = corpus_module.CorpusSpec.experience(experience_root)
    runs = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    index_module.build_scoped_index((experience,), main_idx, fake_embedding)

    with pytest.raises(index_module.IndexMismatchError, match="run-summary index"):
        search(
            "continuity failure",
            scope="experience",
            corpora=(experience,),
            runs_corpus=runs,
            index_path=main_idx,
            runs_index_path=runs_idx,
            embedding=fake_embedding,
        )

    assert not runs_idx.exists()


def test_cli_build_reports_changed_corpus_without_traceback(
    scoped_corpora, tmp_path: Path, monkeypatch, capsys
) -> None:
    experience, _ = scoped_corpora

    def reject_changed_corpus(**kwargs):
        raise index_module.IndexMismatchError(
            "corpus 'experience' changed during index build; retry required"
        )

    monkeypatch.setattr(
        agent_memory_script,
        "build_scoped_index",
        reject_changed_corpus,
    )
    result = agent_memory_script.main(
        [
            "--embedding",
            "fake",
            "--scope",
            "experience",
            "--corpus",
            str(experience.root),
            "--index",
            str(tmp_path / "idx"),
            "build",
        ]
    )

    assert result == 2
    assert "changed during index build" in capsys.readouterr().err


def test_cli_search_fails_closed_when_collection_is_missing(
    scoped_corpora, tmp_path: Path, capsys, monkeypatch
) -> None:
    experience, _ = scoped_corpora
    idx = tmp_path / "idx"
    embedding = DeterministicFakeEmbeddings()
    from ai_video.agent_memory.layout import build_project_indexes, shard_path

    build_project_indexes((experience,), idx, embedding)
    client = index_module.load_index(shard_path(idx, "experience"), embedding)
    client.delete_collection(experience.collection_name)
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: pytest.fail("BROKEN index must not enqueue refresh"),
    )

    result = agent_memory_main(
        [
            "--embedding",
            "fake",
            "--scope",
            "experience",
            "--corpus",
            str(experience.root),
            "--index",
            str(idx),
            "--runs-root",
            str(tmp_path / "missing-runs"),
            "search",
            "continuity",
        ]
    )

    assert result == 2
    assert "index collection" in capsys.readouterr().err


def test_local_multilingual_retrieval_ranks_chinese_contract(tmp_path: Path) -> None:
    if not Path(DEFAULT_MODEL_DIR).expanduser().is_dir():
        pytest.skip("local multilingual E5 cache not present on this machine")
    root = tmp_path / "record_for_agent"
    root.mkdir()
    (root / "continuity.md").write_text(
        "# 镜头连续性\n\n## Contract\n"
        "上一镜头的终止帧必须作为下一镜头的首帧输入，保持角色身份一致。\n",
        encoding="utf-8",
    )
    (root / "audio.md").write_text(
        "# 音频混音\n\n## Contract\n旁白、环境音与背景音乐按时间线混合。\n",
        encoding="utf-8",
    )
    corpus = corpus_module.CorpusSpec.experience(root)
    idx = tmp_path / "idx"
    embedding = LocalOnnxMiniLMEmbeddings()
    index_module.build_scoped_index((corpus,), idx, embedding)

    hits = search(
        "怎样保持跨镜头角色连续性和首尾帧衔接？",
        top_k=1,
        scope="experience",
        corpora=(corpus,),
        index_path=idx,
        embedding=embedding,
    )
    assert hits[0].title == "镜头连续性"


def test_local_multilingual_project_corpus_answerability_calibration(
    tmp_path: Path,
) -> None:
    if not Path(DEFAULT_MODEL_DIR).expanduser().is_dir():
        pytest.skip("local multilingual E5 cache not present on this machine")
    docs_root = tmp_path / "docs-snapshot"
    shutil.copytree(Path(DEFAULT_DOCS_ROOT), docs_root)
    corpora = (
        corpus_module.CorpusSpec.experience(
            docs_root
            / Path(DEFAULT_CORPUS_ROOT).relative_to(DEFAULT_DOCS_ROOT)
        ),
        corpus_module.CorpusSpec.superpowers(
            docs_root
            / Path(DEFAULT_SUPERPOWERS_ROOT).relative_to(DEFAULT_DOCS_ROOT)
        ),
        corpus_module.CorpusSpec.current_docs(docs_root),
        corpus_module.CorpusSpec.research(docs_root / "research"),
        corpus_module.CorpusSpec.deferred(docs_root / "when_to_do"),
    )
    idx = tmp_path / "project-corpus-index"
    embedding = LocalOnnxMiniLMEmbeddings()
    index_module.build_scoped_index(corpora, idx, embedding)

    relevant = search(
        "怎样保持跨镜头角色连续性和首尾帧衔接？",
        top_k=8,
        scope="all",
        corpora=corpora,
        index_path=idx,
        embedding=embedding,
    )
    assert relevant
    assert any(
        "continuity" in hit.source
        and hit.admission_lane in {"dense", "hybrid"}
        for hit in relevant
    )

    assert search(
        "不存在的紫色大象量子果园",
        top_k=8,
        scope="all",
        corpora=corpora,
        index_path=idx,
        embedding=embedding,
    ) == []

    ascii_null_hits = search(
        DENSE_NULL_QUERY_ASCII,
        top_k=8,
        scope="all",
        corpora=corpora,
        index_path=idx,
        embedding=embedding,
    )
    assert not any(
        hit.admission_lane in {"dense", "hybrid"}
        for hit in ascii_null_hits
    )
    assert any(
        hit.admission_lane == "lexical"
        and hit.source.endswith(
            "2026-08-29-record-evidence-identity-validation.md"
        )
        for hit in ascii_null_hits
    )
    assert search(
        "zzzyxqv_absent_memory_topic_98431",
        top_k=8,
        scope="all",
        corpora=corpora,
        index_path=idx,
        embedding=embedding,
    ) == []


# ---------------------------------------------------------------------------
# run-summary auto-retrieval (separate derived index)
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_runs_root(tmp_path: Path) -> Path:
    """A repository-shaped ``runs/`` directory with mixed validity."""
    runs = tmp_path / "runs"
    runs.mkdir()
    # Two valid run summaries (different families, status required).
    (runs / "shot-failure-20260820-v0").mkdir()
    (runs / "shot-failure-20260820-v0" / "SUMMARY.md").write_text(
        "# Shot Failure Run v0\n\n"
        "Status: `TECHNICAL_FAIL__REJECTED`\n\n"
        "## Summary\nInitial versioned attempt.\n",
        encoding="utf-8",
    )
    (runs / "shot-failure-20260820-v1").mkdir()
    (runs / "shot-failure-20260820-v1" / "SUMMARY.md").write_text(
        "# Shot Failure Run v1\n\n"
        "Status: `TECHNICAL_FAIL__REJECTED`\n\n"
        "## Summary\nRough cut failed continuity acceptance.\n",
        encoding="utf-8",
    )
    (runs / "shot-failure-20260820-v2").mkdir()
    (runs / "shot-failure-20260820-v2" / "SUMMARY.md").write_text(
        "# Shot Failure Run v2\n\n"
        "Status: `CREATIVE_FAIL__REJECTED_UNACTIVATED`\n\n"
        "## Summary\nV2 repair also failed continuity.\n",
        encoding="utf-8",
    )
    (runs / "smoke-20260822-v1").mkdir()
    (runs / "smoke-20260822-v1" / "SUMMARY.md").write_text(
        "# Smoke Run v1\n\n"
        "Status: `TECHNICAL_PASS`\n\n"
        "## Summary\nProvider chain ran end to end without error.\n",
        encoding="utf-8",
    )
    (runs / "legacy-smoke").mkdir()
    (runs / "legacy-smoke" / "SUMMARY.md").write_text(
        "# Legacy Smoke Run\n\n"
        "Status: `TECHNICAL_PASS`\n\n"
        "## Summary\nUnversioned runs remain individually searchable.\n",
        encoding="utf-8",
    )
    # Nested evidence folder MUST NOT be indexed.
    (runs / "shot-failure-20260820-v1" / "evidence").mkdir()
    (runs / "shot-failure-20260820-v1" / "evidence" / "review.md").write_text(
        "# Nested review\n\nStatus: `TECHNICAL_PASS`\n\nBody.\n",
        encoding="utf-8",
    )
    # Markdown files directly under runs/ MUST NOT be indexed.
    (runs / "orphan.md").write_text(
        "# Orphan\n\nStatus: `TECHNICAL_PASS`\n\nBody.\n",
        encoding="utf-8",
    )
    # Two-level directory MUST NOT be indexed.
    (runs / "deeper").mkdir()
    (runs / "deeper" / "extra").mkdir()
    (runs / "deeper" / "extra" / "SUMMARY.md").write_text(
        "# Too Deep\n\nStatus: `TECHNICAL_PASS`\n\nBody.\n",
        encoding="utf-8",
    )
    # File without Status MUST NOT be indexed.
    (runs / "no-status-v1").mkdir()
    (runs / "no-status-v1" / "SUMMARY.md").write_text(
        "# No Status Summary\n\nNo status line here at all.\n",
        encoding="utf-8",
    )
    # Wrong filename MUST NOT be indexed.
    (runs / "wrong-name-v1").mkdir()
    (runs / "wrong-name-v1" / "NOTES.md").write_text(
        "# Wrong Name\n\nStatus: `TECHNICAL_PASS`\n\nBody.\n",
        encoding="utf-8",
    )
    # Symlink MUST NOT be indexed.
    target = runs / "shot-failure-20260820-v1" / "SUMMARY.md"
    (runs / "symlink-v1").mkdir()
    try:
        (runs / "symlink-v1" / "SUMMARY.md").symlink_to(target)
    except (OSError, NotImplementedError):
        pass
    return runs


def test_iter_run_summary_files_filters_to_one_level_only(
    sample_runs_root: Path,
) -> None:
    iter_run_summary_files = getattr(
        corpus_module, "iter_run_summary_files", None
    )
    assert iter_run_summary_files is not None, (
        "iter_run_summary_files contract is not implemented"
    )
    entries = [item for item in iter_run_summary_files(sample_runs_root)]
    paths = [item.path for item in entries]
    names = sorted(p.parent.name for p in paths)
    # Should include only valid one-level SUMMARY.md files (discovery
    # itself does not require Status; the Status check lives in the
    # document loader so the loader can fail closed without polluting
    # the discovery helper used by tests and external callers).
    assert "shot-failure-20260820-v1" in names
    assert "shot-failure-20260820-v2" in names
    assert "smoke-20260822-v1" in names
    # Must exclude: wrong-name, deeper, evidence, symlink.
    assert "wrong-name-v1" not in names
    assert "deeper" not in names
    assert "evidence" not in names
    # Must exclude orphans at top level.
    assert "orphan.md" not in [p.name for p in paths]


def test_iter_run_summary_files_returns_family_and_version(
    sample_runs_root: Path,
) -> None:
    iter_run_summary_files = getattr(
        corpus_module, "iter_run_summary_files", None
    )
    assert iter_run_summary_files is not None
    results = {
        item.path: (item.run_family, item.run_version)
        for item in iter_run_summary_files(sample_runs_root)
    }
    # Trailing -vN becomes run_family/run_version.
    for path, (family, version) in results.items():
        if path.parent.name == "shot-failure-20260820-v1":
            assert family == "shot-failure-20260820"
            assert version == 1
        elif path.parent.name == "smoke-20260822-v1":
            assert family == "smoke-20260822"
            assert version == 1


def test_run_summary_corpus_spec_metadata(sample_runs_root: Path) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    load_documents = getattr(corpus_module, "load_documents", None)
    assert CorpusSpec is not None
    assert load_documents is not None
    spec = CorpusSpec.run_summaries(sample_runs_root)
    assert spec.kind == "run_summaries"
    assert spec.collection_name == "agent_memory_run_summaries"
    assert spec.authority == "auto_generated_run_summary_advisory"
    docs = load_documents(sample_runs_root, corpus=spec)
    sources = {doc.metadata["source"] for doc in docs}
    # Highest version per family should be indexed; v1 only when no v2 sibling.
    assert any("shot-failure-20260820-v2" in s for s in sources)
    assert any("smoke-20260822-v1" in s for s in sources)
    assert any("legacy-smoke" in s for s in sources)
    # Lower-version sibling must be skipped by the loader.
    assert not any(
        s.endswith("shot-failure-20260820-v1/SUMMARY.md") for s in sources
    )
    assert not any(
        s.endswith("shot-failure-20260820-v0/SUMMARY.md") for s in sources
    )
    # Status-less files MUST be skipped by the loader.
    assert not any(
        s.endswith("no-status-v1/SUMMARY.md") for s in sources
    )
    # Authority and document_kind are bound by corpus, not frontmatter.
    for doc in docs:
        assert doc.metadata["authority"] == "auto_generated_run_summary_advisory"
        assert doc.metadata["corpus_kind"] == "run_summaries"
        assert doc.metadata["document_kind"] == "run_summary"
        assert doc.metadata["status"]
        assert doc.metadata["run_id"]
        assert doc.metadata["run_family"]
        assert isinstance(doc.metadata["run_version"], int)
        assert doc.metadata["summary_sha256"]
    legacy = next(doc for doc in docs if doc.metadata["run_id"] == "legacy-smoke")
    assert legacy.metadata["run_family"] == "legacy-smoke"
    assert legacy.metadata["run_version"] == 0


def test_statusless_newer_version_does_not_hide_valid_summary(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    (runs / "camera-check-v1").mkdir(parents=True)
    (runs / "camera-check-v1" / "SUMMARY.md").write_text(
        "# Camera Check v1\n\nStatus: `TECHNICAL_PASS`\n\nValid result.\n",
        encoding="utf-8",
    )
    (runs / "camera-check-v2").mkdir()
    (runs / "camera-check-v2" / "SUMMARY.md").write_text(
        "# Camera Check v2\n\nIncomplete auto-generated summary.\n",
        encoding="utf-8",
    )

    docs = load_documents(runs, corpus=corpus_module.CorpusSpec.run_summaries(runs))

    assert [doc.metadata["run_id"] for doc in docs] == ["camera-check-v1"]


def test_run_summaries_search_returns_run_summary_hit(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    assert CorpusSpec is not None and build_scoped_index is not None
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "note.md").write_text(
        "# Experience Note\n\nGeneral continuity note.\n",
        encoding="utf-8",
    )
    experience = CorpusSpec.experience(experience_root)
    spec = CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    build_scoped_index(
        corpora=(experience,),
        index_path=main_idx,
        embedding=fake_embedding,
    )
    build_scoped_index(
        corpora=(spec,),
        index_path=runs_idx,
        embedding=fake_embedding,
    )
    hits = search(
        "continuity failure",
        top_k=5,
        scope="experience",
        corpora=(experience,),
        runs_corpus=spec,
        index_path=main_idx,
        runs_index_path=runs_idx,
        embedding=fake_embedding,
    )
    assert hits, "expected at least one run-summary hit"
    hit = next(h for h in hits if "shot-failure" in h.source)
    assert hit.corpus_kind == "run_summaries"
    assert hit.document_kind == "run_summary"
    assert hit.authority == "auto_generated_run_summary_advisory"
    assert hit.run_id
    assert hit.run_family
    assert hit.run_version >= 1
    assert hit.summary_sha256
    assert hit.status
    # Highest version must win (v2 above v1).
    assert hit.run_version == 2
    rendered = format_text(hits)
    assert "auto-generated run summary advisory" in rendered


def test_experience_search_includes_run_summary_hits(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    assert CorpusSpec is not None and build_scoped_index is not None
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity Note\n\n## Fix\nUse exact terminal frame.\n",
        encoding="utf-8",
    )
    experience = CorpusSpec.experience(experience_root)
    runs = CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    build_scoped_index(
        corpora=(experience,),
        index_path=main_idx,
        embedding=fake_embedding,
    )
    build_scoped_index(
        corpora=(runs,),
        index_path=runs_idx,
        embedding=fake_embedding,
    )
    # Search only queries the run-summary index materialized by build.
    hits = search(
        "shot failure continuity",
        top_k=4,
        scope="experience",
        corpora=(experience,),
        runs_corpus=runs,
        index_path=main_idx,
        runs_index_path=runs_idx,
        embedding=fake_embedding,
    )
    kinds = {hit.corpus_kind for hit in hits}
    assert "run_summaries" in kinds
    assert "experience" in kinds
    assert {
        item.kind for item in index_module.read_index_manifest(main_idx).corpora
    } == {"experience"}
    assert {
        item.kind for item in index_module.read_index_manifest(runs_idx).corpora
    } == {"run_summaries"}


def test_run_summary_index_path_must_not_overlap_main_index(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity Note\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    experience = corpus_module.CorpusSpec.experience(experience_root)
    runs = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    index_module.build_scoped_index((experience,), main_idx, fake_embedding)
    manifest_before = (main_idx / "manifest.json").read_bytes()

    with pytest.raises(ValueError, match="must not overlap"):
        search(
            "continuity",
            scope="experience",
            corpora=(experience,),
            runs_corpus=runs,
            index_path=main_idx,
            runs_index_path=main_idx,
            embedding=fake_embedding,
        )

    assert (main_idx / "manifest.json").read_bytes() == manifest_before
    assert {
        item.kind for item in index_module.read_index_manifest(main_idx).corpora
    } == {"experience"}


def test_run_summary_index_path_must_not_overlap_source_roots(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    experience_path = experience_root / "continuity.md"
    experience_path.write_text(
        "# Continuity Note\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    experience = corpus_module.CorpusSpec.experience(experience_root)
    runs = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    index_module.build_scoped_index((experience,), main_idx, fake_embedding)
    summary_path = sample_runs_root / "shot-failure-20260820-v2" / "SUMMARY.md"
    summary_before = summary_path.read_bytes()
    experience_before = experience_path.read_bytes()

    for unsafe_path in (
        sample_runs_root,
        sample_runs_root / "derived-index",
        experience_root,
    ):
        with pytest.raises(ValueError, match="must not overlap"):
            search(
                "continuity",
                scope="experience",
                corpora=(experience,),
                runs_corpus=runs,
                index_path=main_idx,
                runs_index_path=unsafe_path,
                embedding=fake_embedding,
            )

    assert summary_path.read_bytes() == summary_before
    assert experience_path.read_bytes() == experience_before


def test_scoped_index_path_must_not_overlap_its_corpus(
    sample_runs_root: Path, fake_embedding
) -> None:
    runs = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    summary_path = sample_runs_root / "shot-failure-20260820-v2" / "SUMMARY.md"
    summary_before = summary_path.read_bytes()

    with pytest.raises(ValueError, match="must not overlap"):
        index_module.build_scoped_index(
            (runs,),
            sample_runs_root / "derived-index",
            fake_embedding,
        )

    assert summary_path.read_bytes() == summary_before


def test_experience_search_rejects_newer_run_version_until_explicit_build(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity Note\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    experience = corpus_module.CorpusSpec.experience(experience_root)
    runs = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    index_module.build_scoped_index((experience,), main_idx, fake_embedding)
    index_module.build_scoped_index((runs,), runs_idx, fake_embedding)
    manifest_before = (runs_idx / "manifest.json").read_bytes()
    (sample_runs_root / "shot-failure-20260820-v3").mkdir()
    (sample_runs_root / "shot-failure-20260820-v3" / "SUMMARY.md").write_text(
        "# Shot Failure Run v3\n\n"
        "Status: `CREATIVE_PASS`\n\n"
        "## Summary\nGimbal yaw correction accepted.\n",
        encoding="utf-8",
    )

    with pytest.raises(index_module.IndexMismatchError, match="stale corpus"):
        search(
            "gimbal yaw correction accepted",
            top_k=8,
            scope="experience",
            corpora=(experience,),
            runs_corpus=runs,
            index_path=main_idx,
            runs_index_path=runs_idx,
            embedding=fake_embedding,
        )

    assert (runs_idx / "manifest.json").read_bytes() == manifest_before
    index_module.build_scoped_index((runs,), runs_idx, fake_embedding)
    refreshed = search(
        "gimbal yaw correction accepted",
        top_k=8,
        scope="experience",
        corpora=(experience,),
        runs_corpus=runs,
        index_path=main_idx,
        runs_index_path=runs_idx,
        embedding=fake_embedding,
    )

    run_sources = [hit.source for hit in refreshed if hit.corpus_kind == "run_summaries"]
    assert any("shot-failure-20260820-v3/SUMMARY.md" in item for item in run_sources)
    assert not any("shot-failure-20260820-v2/SUMMARY.md" in item for item in run_sources)
    staging_prefix = str(runs_idx.parent / f".{runs_idx.name}.staging-")
    assert not any(
        identifier.startswith(staging_prefix)
        for identifier in index_module.SharedSystemClient._identifier_to_system
    )


@pytest.mark.parametrize("corruption", ("missing_collection", "chunk_count"))
def test_experience_search_rejects_corrupt_run_summary_index(
    sample_runs_root: Path,
    tmp_path: Path,
    fake_embedding,
    corruption: str,
) -> None:
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity Note\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    experience = corpus_module.CorpusSpec.experience(experience_root)
    runs = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    index_module.build_scoped_index((experience,), main_idx, fake_embedding)
    index_module.build_scoped_index((runs,), runs_idx, fake_embedding)
    manifest_before = (runs_idx / "manifest.json").read_bytes()
    client = index_module.load_index(runs_idx, fake_embedding)
    collection = client.get_collection(runs.collection_name)
    if corruption == "missing_collection":
        client.delete_collection(runs.collection_name)
    else:
        first_id = collection.get(limit=1)["ids"][0]
        collection.delete(ids=[first_id])

    message = (
        "run-summary collection is unavailable"
        if corruption == "missing_collection"
        else "run-summary collection chunk count mismatch"
    )
    with pytest.raises(index_module.IndexMismatchError, match=message):
        search(
            "continuity failure",
            top_k=8,
            scope="experience",
            corpora=(experience,),
            runs_corpus=runs,
            index_path=main_idx,
            runs_index_path=runs_idx,
            embedding=fake_embedding,
        )

    assert (runs_idx / "manifest.json").read_bytes() == manifest_before
    index_module.build_scoped_index((runs,), runs_idx, fake_embedding)
    repaired = search(
        "continuity failure",
        top_k=8,
        scope="experience",
        corpora=(experience,),
        runs_corpus=runs,
        index_path=main_idx,
        runs_index_path=runs_idx,
        embedding=fake_embedding,
    )

    assert any(hit.corpus_kind == "run_summaries" for hit in repaired)
    manifest = index_module.read_index_manifest(runs_idx)
    expected_chunks = manifest.corpora[0].chunk_count
    rebuilt_client = index_module.load_index(runs_idx, fake_embedding)
    assert rebuilt_client.get_collection(runs.collection_name).count() == expected_chunks


def test_superpowers_search_excludes_run_summaries(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    assert CorpusSpec is not None and build_scoped_index is not None
    superpowers_root = tmp_path / "superpowers"
    superpowers_root.mkdir()
    (superpowers_root / "specs").mkdir()
    (superpowers_root / "specs" / "state-commit.md").write_text(
        "# State Commit Contract\n\n## Recovery\n"
        "ProductionStateCommitter owns explicit recovery.\n",
        encoding="utf-8",
    )
    superpowers = CorpusSpec.superpowers(superpowers_root)
    runs = CorpusSpec.run_summaries(sample_runs_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    build_scoped_index(
        corpora=(superpowers,),
        index_path=main_idx,
        embedding=fake_embedding,
    )
    hits = search(
        "recovery",
        top_k=4,
        scope="superpowers",
        corpora=(superpowers,),
        runs_corpus=runs,
        index_path=main_idx,
        runs_index_path=runs_idx,
        embedding=fake_embedding,
    )
    assert hits, "expected at least one superpowers hit"
    assert {h.corpus_kind for h in hits} == {"superpowers"}
    assert not runs_idx.exists()


def test_run_summaries_missing_root_returns_no_hits(
    tmp_path: Path, fake_embedding
) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    assert CorpusSpec is not None
    runs = CorpusSpec.run_summaries(tmp_path / "missing_runs")
    experience_root = tmp_path / "record_for_agent"
    experience_root.mkdir()
    (experience_root / "continuity.md").write_text(
        "# Continuity\n\nUse exact terminal frames.\n",
        encoding="utf-8",
    )
    experience = CorpusSpec.experience(experience_root)
    main_idx = tmp_path / "idx"
    runs_idx = tmp_path / "runs_idx"
    index_module.build_scoped_index((experience,), main_idx, fake_embedding)
    hits = search(
        "terminal frames",
        top_k=3,
        scope="experience",
        corpora=(experience,),
        runs_corpus=runs,
        index_path=main_idx,
        runs_index_path=runs_idx,
        embedding=fake_embedding,
    )
    assert hits
    assert {hit.corpus_kind for hit in hits} == {"experience"}
    assert not runs_idx.exists()


def test_run_summaries_index_digest_marks_stale(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    assert CorpusSpec is not None and build_scoped_index is not None
    spec = CorpusSpec.run_summaries(sample_runs_root)
    runs_idx = tmp_path / "runs_idx"
    build_scoped_index(
        corpora=(spec,),
        index_path=runs_idx,
        embedding=fake_embedding,
    )
    # Add a new valid run summary AFTER the index was built.
    (sample_runs_root / "newly-added-v1").mkdir()
    (sample_runs_root / "newly-added-v1" / "SUMMARY.md").write_text(
        "# New Run\n\nStatus: `TECHNICAL_PASS`\n\n## Summary\nNew entry.\n",
        encoding="utf-8",
    )
    # Validate_manifest for run-summaries should fail closed because the
    # corpus changed since the index was built.
    IndexMismatchError = getattr(index_module, "IndexMismatchError", RuntimeError)
    with pytest.raises(IndexMismatchError):
        index_module.validate_manifest(
            index_module.read_index_manifest(runs_idx),
            (spec,),
            fake_embedding,
        )


def test_run_summaries_index_schema_version_remains_one(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    CorpusSpec = getattr(corpus_module, "CorpusSpec", None)
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    read_index_manifest = getattr(index_module, "read_index_manifest", None)
    assert (
        CorpusSpec is not None
        and build_scoped_index is not None
        and read_index_manifest is not None
    )
    spec = CorpusSpec.run_summaries(sample_runs_root)
    runs_idx = tmp_path / "runs_idx"
    build_scoped_index(
        corpora=(spec,),
        index_path=runs_idx,
        embedding=fake_embedding,
    )
    manifest = read_index_manifest(runs_idx)
    assert manifest.schema_version == 1
    kinds = {item.kind for item in manifest.corpora}
    assert kinds == {"run_summaries"}


def test_public_scopes_remain_backward_compatible(fake_embedding) -> None:
    assert VALID_SCOPES == ("experience", "superpowers", "all")
    with pytest.raises(ValueError, match="unknown Agent Memory scope"):
        search("run only", scope="run_summaries", embedding=fake_embedding)


def test_run_summary_validation_rejects_embedding_identity_until_explicit_build(
    sample_runs_root: Path, tmp_path: Path, fake_embedding
) -> None:
    spec = corpus_module.CorpusSpec.run_summaries(sample_runs_root)
    runs_idx = tmp_path / "runs_idx"
    index_module.build_scoped_index((spec,), runs_idx, fake_embedding)
    assert index_module.read_index_manifest(runs_idx).embedding.dimension == 64

    replacement = DeterministicFakeEmbeddings(size=32)
    with pytest.raises(index_module.IndexMismatchError, match="embedding"):
        index_module.validate_run_summary_index(runs_idx, spec, replacement)

    assert index_module.read_index_manifest(runs_idx).embedding.dimension == 64
    index_module.build_scoped_index((spec,), runs_idx, replacement)

    assert index_module.read_index_manifest(runs_idx).embedding.dimension == 32


# ---------------------------------------------------------------------------
# non-blocking sharded project retrieval + refresh maintenance
# ---------------------------------------------------------------------------


def test_scoped_validation_classifies_source_drift_as_stale(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.manifest import StaleIndexError

    experience, _ = scoped_corpora
    idx = tmp_path / "idx"
    index_module.build_scoped_index((experience,), idx, fake_embedding)
    (experience.root / "continuity.md").write_text(
        "# Fresh source bytes\n\nChanged after materialization.\n",
        encoding="utf-8",
    )

    with pytest.raises(StaleIndexError, match="stale corpus"):
        index_module.validate_scoped_index((experience,), idx, fake_embedding)


def test_library_rebuild_candidate_rejects_uncheckpointed_database(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes, shard_path

    experience, _ = scoped_corpora
    root = tmp_path / "project-index"
    build_project_indexes((experience,), root, fake_embedding)
    leaf = shard_path(root, "experience")
    manifest_path = leaf / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["library_versions"]["chromadb"] = "0.5.23"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path(f"{leaf / 'chroma.sqlite3'}-wal").write_bytes(b"uncheckpointed")

    with pytest.raises(index_module.IndexMismatchError, match="uncheckpointed"):
        index_module.validate_library_rebuild_candidate(
            (experience,),
            leaf,
            fake_embedding,
        )


def test_library_rebuild_candidate_rejects_malformed_version_identity(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes, shard_path

    experience, _ = scoped_corpora
    root = tmp_path / "project-index"
    build_project_indexes((experience,), root, fake_embedding)
    leaf = shard_path(root, "experience")
    manifest_path = leaf / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["library_versions"].pop("chromadb")
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(index_module.IndexMismatchError, match="invalid index library"):
        index_module.validate_library_rebuild_candidate(
            (experience,),
            leaf,
            fake_embedding,
        )


def test_stale_fallback_rejects_different_corpus_root_identity(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes
    from ai_video.agent_memory.retrieval import retrieve_project

    experience, _ = scoped_corpora
    root = tmp_path / "project-index"
    build_project_indexes((experience,), root, fake_embedding)
    replacement_root = tmp_path / "replacement-experience"
    shutil.copytree(experience.root, replacement_root)
    replacement = corpus_module.CorpusSpec.experience(replacement_root)

    with pytest.raises(index_module.IndexMismatchError, match="root identity"):
        retrieve_project(
            "exact terminal frame",
            scope="experience",
            corpora=(replacement,),
            index_root=root,
            embedding=fake_embedding,
            allow_stale=True,
        )


def test_project_layout_materializes_one_leaf_per_corpus(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    fake_embedding,
) -> None:
    from ai_video.agent_memory.layout import (
        build_project_indexes,
        read_project_layout,
        shard_path,
    )

    _, project_corpora = project_docs_corpora
    corpora = (*scoped_corpora, *project_corpora)
    root = tmp_path / "project-index"

    counts = build_project_indexes(corpora, root, fake_embedding)

    assert set(counts) == {item.kind for item in corpora}
    assert read_project_layout(root).schema_version == 1
    for corpus in corpora:
        manifest = index_module.read_index_manifest(shard_path(root, corpus.kind))
        assert [item.kind for item in manifest.corpora] == [corpus.kind]


def test_project_layout_narrow_refresh_preserves_unrelated_shard(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes, shard_path

    experience, superpowers = scoped_corpora
    root = tmp_path / "project-index"
    build_project_indexes(scoped_corpora, root, fake_embedding)
    untouched = shard_path(root, superpowers.kind) / "manifest.json"
    untouched_before = untouched.read_bytes()
    (experience.root / "continuity.md").write_text(
        "# Refreshed continuity\n\nUse the exact terminal frame.\n",
        encoding="utf-8",
    )

    counts = build_project_indexes((experience,), root, fake_embedding)

    assert set(counts) == {"experience"}
    assert untouched.read_bytes() == untouched_before


def test_activation_lock_serializes_same_process_chroma_readers(
    tmp_path: Path,
) -> None:
    import threading

    leaf = tmp_path / "index" / "experience"
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()

    def first_reader() -> None:
        with index_module.index_activation_lock(leaf, exclusive=False):
            first_entered.set()
            assert release_first.wait(timeout=2)

    def second_reader() -> None:
        with index_module.index_activation_lock(leaf, exclusive=False):
            second_entered.set()

    first = threading.Thread(target=first_reader)
    second = threading.Thread(target=second_reader)
    first.start()
    assert first_entered.wait(timeout=1)
    second.start()
    assert not second_entered.wait(timeout=0.05)
    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert second_entered.is_set()


def test_project_retrieval_returns_tagged_last_good_for_stale_shard(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes, shard_path
    from ai_video.agent_memory.retrieval import retrieve_project

    experience, _ = scoped_corpora
    root = tmp_path / "project-index"
    build_project_indexes((experience,), root, fake_embedding)
    manifest_path = shard_path(root, "experience") / "manifest.json"
    manifest_before = manifest_path.read_bytes()
    (experience.root / "continuity.md").write_text(
        "# New unrelated source\n\nThe old exact terminal frame text is gone.\n",
        encoding="utf-8",
    )

    result = retrieve_project(
        "exact terminal frame",
        top_k=8,
        scope="experience",
        corpora=(experience,),
        index_root=root,
        embedding=fake_embedding,
        allow_stale=True,
    )

    assert result.stale_kinds == ("experience",)
    assert result.hits
    assert {hit.index_freshness for hit in result.hits} == {"stale"}
    assert manifest_path.read_bytes() == manifest_before


def test_project_retrieval_never_hides_corruption_behind_stale_fallback(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes, shard_path
    from ai_video.agent_memory.retrieval import retrieve_project

    experience, _ = scoped_corpora
    root = tmp_path / "project-index"
    build_project_indexes((experience,), root, fake_embedding)
    leaf = shard_path(root, "experience")
    collection = index_module.load_index(leaf, fake_embedding).get_collection(
        experience.collection_name
    )
    collection.delete(ids=[collection.get(limit=1)["ids"][0]])
    (experience.root / "continuity.md").write_text(
        "# Stale and corrupt\n",
        encoding="utf-8",
    )

    with pytest.raises(index_module.IndexMismatchError, match="chunk count mismatch"):
        retrieve_project(
            "continuity",
            scope="experience",
            corpora=(experience,),
            index_root=root,
            embedding=fake_embedding,
            allow_stale=True,
        )


def test_project_retrieval_embeds_query_once_across_shards(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    fake_embedding,
    monkeypatch,
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes
    from ai_video.agent_memory.retrieval import retrieve_project

    _, project_corpora = project_docs_corpora
    corpora = (*scoped_corpora, *project_corpora)
    root = tmp_path / "project-index"
    build_project_indexes(corpora, root, fake_embedding)
    original = fake_embedding.embed_query
    calls: list[str] = []

    def record_query(text: str):
        calls.append(text)
        return original(text)

    monkeypatch.setattr(fake_embedding, "embed_query", record_query)

    retrieve_project(
        "project recovery",
        scope="all",
        corpora=corpora,
        index_root=root,
        embedding=fake_embedding,
    )

    assert len(calls) == 2


def test_refresh_queue_merges_kinds_and_avoids_duplicate_worker(
    tmp_path: Path,
) -> None:
    from ai_video.agent_memory.maintenance import RefreshRequest, enqueue_refresh

    queue_root = tmp_path / "queue"
    request = RefreshRequest(
        index_root=str(tmp_path / "index"),
        runs_index_path=str(tmp_path / "runs-index"),
        corpus_roots={
            "experience": str(tmp_path / "experience"),
            "superpowers": str(tmp_path / "superpowers"),
        },
        desired_sources={"experience": "v1", "superpowers": "v1"},
        embedding_backend="fake",
        batch_size=8,
    )
    launches: list[tuple[str, ...]] = []

    class Process:
        pid = 4242

    def launch(command):
        launches.append(tuple(command))
        return Process()

    first = enqueue_refresh(
        request,
        ("experience",),
        queue_root=queue_root,
        launch=launch,
        process_alive=lambda pid: pid == 4242,
    )
    second = enqueue_refresh(
        request,
        ("superpowers",),
        queue_root=queue_root,
        launch=launch,
        process_alive=lambda pid: pid == 4242,
    )

    assert first.worker_started is True
    assert second.worker_started is False
    assert launches and len(launches) == 1
    pending = json.loads((queue_root / first.queue_key / "pending.json").read_text())
    assert pending["kinds"] == ["experience", "superpowers"]


def test_refresh_worker_health_checks_exact_worker_argv(
    tmp_path: Path, monkeypatch
) -> None:
    import os

    from ai_video.agent_memory.maintenance import _pid_alive

    queue_dir = (tmp_path / "queue").resolve()
    assert _pid_alive(os.getpid()) is True
    assert _pid_alive(os.getpid(), queue_dir) is False

    worker_argv = b"\0".join(
        (
            b"python",
            b"-m",
            b"scripts.agent_memory",
            b"_refresh-worker",
            b"--queue-dir",
            str(queue_dir).encode("utf-8"),
            b"",
        )
    )
    monkeypatch.setattr(Path, "read_bytes", lambda path: worker_argv)
    assert _pid_alive(os.getpid(), queue_dir) is True
    assert _pid_alive(os.getpid(), tmp_path / "other-queue") is False

    def unreadable(path):
        raise OSError("proc unavailable")

    monkeypatch.setattr(Path, "read_bytes", unreadable)
    assert _pid_alive(os.getpid(), queue_dir) is False


def test_refresh_worker_drains_pending_and_records_sanitized_status(
    tmp_path: Path,
) -> None:
    from ai_video.agent_memory.maintenance import (
        RefreshRequest,
        enqueue_refresh,
        run_refresh_worker,
    )

    queue_root = tmp_path / "queue"
    request = RefreshRequest(
        index_root=str(tmp_path / "index"),
        runs_index_path=str(tmp_path / "runs-index"),
        corpus_roots={"experience": str(tmp_path / "experience")},
        desired_sources={"experience": "v1"},
        embedding_backend="fake",
        batch_size=8,
    )

    class Process:
        pid = 4242

    queued = enqueue_refresh(
        request,
        ("experience",),
        queue_root=queue_root,
        launch=lambda command: Process(),
        process_alive=lambda pid: False,
    )
    queue_dir = queue_root / queued.queue_key
    observed: list[tuple[str, ...]] = []

    result = run_refresh_worker(
        queue_dir,
        lambda queued_request, kinds: observed.append(kinds) or {"experience": 3},
    )

    assert result == 0
    assert observed == [("experience",)]
    assert not (queue_dir / "pending.json").exists()
    assert not (queue_dir / "worker.json").exists()
    status = json.loads((queue_dir / "status.json").read_text())
    assert status == {
        "counts": {"experience": 3},
        "kinds": ["experience"],
        "status": "ready",
    }


def test_refresh_worker_failure_drains_request_enqueued_during_build(
    tmp_path: Path,
) -> None:
    import os

    from ai_video.agent_memory.maintenance import (
        RefreshRequest,
        enqueue_refresh,
        run_refresh_worker,
    )

    queue_root = tmp_path / "queue"
    request = RefreshRequest(
        index_root=str(tmp_path / "index"),
        runs_index_path=str(tmp_path / "runs-index"),
        corpus_roots={
            "experience": str(tmp_path / "experience"),
            "superpowers": str(tmp_path / "superpowers"),
        },
        desired_sources={"experience": "v1", "superpowers": "v1"},
        embedding_backend="fake",
        batch_size=8,
    )

    class Process:
        pid = 4242

    queued = enqueue_refresh(
        request,
        ("experience",),
        queue_root=queue_root,
        launch=lambda command: Process(),
        process_alive=lambda pid: False,
    )
    queue_dir = queue_root / queued.queue_key
    observed: list[tuple[str, ...]] = []

    def build(queued_request, kinds):
        observed.append(kinds)
        if kinds == ("experience",):
            enqueue_refresh(
                request,
                ("superpowers",),
                queue_root=queue_root,
                launch=lambda command: pytest.fail("active worker must be reused"),
                process_alive=lambda pid: pid == os.getpid(),
            )
            raise RuntimeError("sensitive provider payload must not be recorded")
        return {"superpowers": 2}

    result = run_refresh_worker(queue_dir, build)

    assert result == 0
    assert observed == [("experience",), ("superpowers",)]
    assert not (queue_dir / "pending.json").exists()
    assert not (queue_dir / "worker.json").exists()
    status_text = (queue_dir / "status.json").read_text(encoding="utf-8")
    assert "sensitive provider payload" not in status_text
    assert json.loads(status_text) == {
        "counts": {"superpowers": 2},
        "kinds": ["superpowers"],
        "status": "ready",
    }


def test_refresh_worker_dedupes_same_identity_enqueued_while_in_flight(
    tmp_path: Path,
) -> None:
    import os

    from ai_video.agent_memory.maintenance import (
        RefreshRequest,
        enqueue_refresh,
        run_refresh_worker,
    )

    queue_root = tmp_path / "queue"
    request = RefreshRequest(
        index_root=str(tmp_path / "index"),
        runs_index_path=str(tmp_path / "runs-index"),
        corpus_roots={"experience": str(tmp_path / "experience")},
        desired_sources={"experience": "v1"},
        embedding_backend="fake",
        batch_size=8,
    )

    class Process:
        pid = 4242

    queued = enqueue_refresh(
        request,
        ("experience",),
        queue_root=queue_root,
        launch=lambda command: Process(),
        process_alive=lambda pid: False,
    )
    queue_dir = queue_root / queued.queue_key
    observed: list[tuple[str, ...]] = []

    def build(queued_request, kinds):
        observed.append(kinds)
        enqueue_refresh(
            request,
            ("experience",),
            queue_root=queue_root,
            launch=lambda command: pytest.fail("active worker must be reused"),
            process_alive=lambda pid: pid == os.getpid(),
        )
        return {"experience": 3}

    result = run_refresh_worker(queue_dir, build)

    assert result == 0
    assert observed == [("experience",)]
    assert not (queue_dir / "pending.json").exists()


def test_refresh_worker_keeps_new_source_identity_enqueued_while_in_flight(
    tmp_path: Path,
) -> None:
    import os
    from dataclasses import replace

    from ai_video.agent_memory.maintenance import (
        RefreshRequest,
        enqueue_refresh,
        run_refresh_worker,
    )

    queue_root = tmp_path / "queue"
    request = RefreshRequest(
        index_root=str(tmp_path / "index"),
        runs_index_path=str(tmp_path / "runs-index"),
        corpus_roots={"experience": str(tmp_path / "experience")},
        desired_sources={"experience": "v1"},
        embedding_backend="fake",
        batch_size=8,
    )
    request_v2 = replace(request, desired_sources={"experience": "v2"})

    class Process:
        pid = 4242

    queued = enqueue_refresh(
        request,
        ("experience",),
        queue_root=queue_root,
        launch=lambda command: Process(),
        process_alive=lambda pid: False,
    )
    queue_dir = queue_root / queued.queue_key
    observed: list[str] = []

    def build(queued_request, kinds):
        observed.append(queued_request.desired_sources["experience"])
        if observed == ["v1"]:
            follow_up = enqueue_refresh(
                request_v2,
                ("experience",),
                queue_root=queue_root,
                launch=lambda command: pytest.fail("active worker must be reused"),
                process_alive=lambda pid: pid == os.getpid(),
            )
            assert follow_up.queue_key == queued.queue_key
        return {"experience": 3}

    result = run_refresh_worker(queue_dir, build)

    assert result == 0
    assert observed == ["v1", "v2"]
    assert not (queue_dir / "pending.json").exists()


def test_cli_refresh_worker_materializes_only_queued_project_shard(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    from ai_video.agent_memory.layout import shard_path
    from ai_video.agent_memory.maintenance import enqueue_refresh

    experience, superpowers = scoped_corpora
    docs_root, _ = project_docs_corpora
    index_root = tmp_path / "index"
    args = SimpleNamespace(
        corpus=str(experience.root),
        superpowers_corpus=str(superpowers.root),
        docs_root=str(docs_root),
        runs_root=str(tmp_path / "missing-runs"),
        index=str(index_root),
        runs_index=str(tmp_path / "runs-index"),
        embedding="fake",
        batch_size=8,
    )
    request = agent_memory_script._refresh_request(args)

    class Process:
        pid = 4242

    queued = enqueue_refresh(
        request,
        ("experience",),
        queue_root=tmp_path / "queue",
        launch=lambda command: Process(),
        process_alive=lambda pid: False,
    )

    result = agent_memory_script.cmd_refresh_worker(
        SimpleNamespace(queue_dir=str(tmp_path / "queue" / queued.queue_key))
    )

    assert result == 0
    assert index_module.index_exists(shard_path(index_root, "experience"))
    assert not shard_path(index_root, "superpowers").exists()


def test_cli_stale_search_returns_last_good_and_queues_refresh(
    scoped_corpora, tmp_path: Path, capsys, monkeypatch
) -> None:
    experience, _ = scoped_corpora
    idx = tmp_path / "idx"
    common = [
        "--embedding",
        "fake",
        "--scope",
        "experience",
        "--corpus",
        str(experience.root),
        "--index",
        str(idx),
        "--runs-root",
        str(tmp_path / "missing-runs"),
    ]
    assert agent_memory_main([*common, "build"]) == 0
    capsys.readouterr()
    (experience.root / "continuity.md").write_text(
        "# Changed source\n\nNew bytes after the last-good index.\n",
        encoding="utf-8",
    )
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )
    result = agent_memory_main(
        [*common, "search", "exact terminal frame", "--json"]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert '"index_freshness": "stale"' in captured.out
    assert "tagged last-good" in captured.err
    assert queued == [("experience",)]


def test_cli_missing_layout_queues_without_foreground_build(
    scoped_corpora, tmp_path: Path, capsys, monkeypatch
) -> None:
    experience, _ = scoped_corpora
    idx = tmp_path / "missing-index"
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )
    monkeypatch.setattr(
        agent_memory_script,
        "build_embedding",
        lambda **kwargs: pytest.fail("missing layout must queue before model load"),
    )

    result = agent_memory_main(
        [
            "--embedding",
            "fake",
            "--scope",
            "experience",
            "--corpus",
            str(experience.root),
            "--index",
            str(idx),
            "--runs-root",
            str(tmp_path / "missing-runs"),
            "search",
            "continuity",
        ]
    )

    assert result == 3
    assert queued == [("experience",)]
    assert not idx.exists()
    assert "continue with current repository evidence" in capsys.readouterr().err


def test_cli_missing_embedding_is_broken_and_never_queued(
    scoped_corpora, tmp_path: Path, capsys, monkeypatch, fake_embedding
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes

    experience, _ = scoped_corpora
    idx = tmp_path / "index"
    build_project_indexes((experience,), idx, fake_embedding)
    monkeypatch.setattr(
        agent_memory_script,
        "build_embedding",
        lambda **kwargs: (_ for _ in ()).throw(FileNotFoundError("model missing")),
    )
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: pytest.fail("missing embedding must not enqueue"),
    )

    result = agent_memory_main(
        [
            "--embedding",
            "local",
            "--scope",
            "experience",
            "--corpus",
            str(experience.root),
            "--index",
            str(idx),
            "--runs-root",
            str(tmp_path / "missing-runs"),
            "search",
            "continuity",
        ]
    )

    assert result == 2
    assert "model missing" in capsys.readouterr().err


def test_cli_missing_run_shard_queues_only_run_summaries(
    scoped_corpora,
    sample_runs_root: Path,
    tmp_path: Path,
    capsys,
    monkeypatch,
    fake_embedding,
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes

    experience, _ = scoped_corpora
    idx = tmp_path / "index"
    build_project_indexes((experience,), idx, fake_embedding)
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )
    monkeypatch.setattr(
        agent_memory_script,
        "build_embedding",
        lambda **kwargs: pytest.fail("missing run shard must queue before model load"),
    )

    result = agent_memory_main(
        [
            "--embedding",
            "fake",
            "--scope",
            "experience",
            "--corpus",
            str(experience.root),
            "--index",
            str(idx),
            "--runs-root",
            str(sample_runs_root),
            "--runs-index",
            str(tmp_path / "missing-runs-index"),
            "search",
            "continuity",
        ]
    )

    assert result == 3
    assert queued == [("run_summaries",)]
    assert "continue with current repository evidence" in capsys.readouterr().err


def test_cli_partial_all_layout_queues_all_missing_shards_before_model_load(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    capsys,
    monkeypatch,
    fake_embedding,
) -> None:
    from ai_video.agent_memory.layout import build_project_indexes

    experience, superpowers = scoped_corpora
    docs_root, _ = project_docs_corpora
    idx = tmp_path / "index"
    build_project_indexes((experience,), idx, fake_embedding)
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )
    monkeypatch.setattr(
        agent_memory_script,
        "build_embedding",
        lambda **kwargs: pytest.fail("partial layout must queue before model load"),
    )

    result = agent_memory_main(
        [
            "--embedding",
            "fake",
            "--scope",
            "all",
            "--corpus",
            str(experience.root),
            "--superpowers-corpus",
            str(superpowers.root),
            "--docs-root",
            str(docs_root),
            "--index",
            str(idx),
            "--runs-root",
            str(tmp_path / "missing-runs"),
            "search",
            "recovery",
        ]
    )

    assert result == 3
    assert queued == [
        ("superpowers", "current_docs", "research", "deferred")
    ]
    assert "continue with current repository evidence" in capsys.readouterr().err


def test_cli_legacy_migration_also_queues_missing_eligible_runs(
    scoped_corpora,
    project_docs_corpora,
    sample_runs_root: Path,
    tmp_path: Path,
    capsys,
    monkeypatch,
    fake_embedding,
) -> None:
    experience, superpowers = scoped_corpora
    docs_root, project_corpora = project_docs_corpora
    idx = tmp_path / "legacy"
    index_module.build_scoped_index(
        (*scoped_corpora, *project_corpora),
        idx,
        fake_embedding,
    )
    queued: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_memory_script,
        "_enqueue",
        lambda args, kinds: queued.append(tuple(kinds)),
    )
    monkeypatch.setattr(
        agent_memory_script,
        "build_embedding",
        lambda **kwargs: pytest.fail("legacy migration must queue before model load"),
    )

    result = agent_memory_main(
        [
            "--embedding",
            "fake",
            "--scope",
            "experience",
            "--corpus",
            str(experience.root),
            "--superpowers-corpus",
            str(superpowers.root),
            "--docs-root",
            str(docs_root),
            "--index",
            str(idx),
            "--runs-root",
            str(sample_runs_root),
            "--runs-index",
            str(tmp_path / "missing-runs-index"),
            "search",
            "continuity",
        ]
    )

    assert result == 3
    assert queued == [
        (
            "experience",
            "superpowers",
            "current_docs",
            "research",
            "deferred",
            "run_summaries",
        )
    ]
    assert "continue with current repository evidence" in capsys.readouterr().err


def test_legacy_shared_index_requires_full_migration(
    scoped_corpora,
    project_docs_corpora,
    tmp_path: Path,
    fake_embedding,
) -> None:
    from ai_video.agent_memory.layout import (
        LegacyProjectIndexError,
        build_project_indexes,
        read_project_layout,
        shard_path,
    )

    experience, _ = scoped_corpora
    _, project_corpora = project_docs_corpora
    all_corpora = (*scoped_corpora, *project_corpora)
    root = tmp_path / "legacy"
    index_module.build_scoped_index(all_corpora, root, fake_embedding)

    with pytest.raises(LegacyProjectIndexError, match="all-scope"):
        build_project_indexes((experience,), root, fake_embedding)

    build_project_indexes(all_corpora, root, fake_embedding)

    assert read_project_layout(root).layout == "per_corpus"
    assert not (root / "manifest.json").exists()
    assert index_module.index_exists(shard_path(root, "experience"))
