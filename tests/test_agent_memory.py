"""Unit tests for Agent Experience Memory.

These tests use the deterministic fake embedding backend so they are
network-free, model-free, and reproducible.  They exercise:

  * markdown corpus iteration and frontmatter tolerance
  * heading-aware chunking preserves file + section metadata
  * Chroma index build + load round-trip
  * top-K retrieval returns the expected known-relevant record
  * text formatter handles both empty and populated hit lists

The local embedding smoke below runs only when the pinned model cache is
present; the remaining tests intentionally use the deterministic fake backend.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ai_video.agent_memory.corpus as corpus_module
import ai_video.agent_memory.index as index_module
import scripts.agent_memory as agent_memory_script
from ai_video.agent_memory.chunking import chunk_documents
from ai_video.agent_memory.config import (
    DEFAULT_CORPUS_ROOT,
    DEFAULT_INDEX_PATH,
    DEFAULT_MODEL_DIR,
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


def test_scoped_search_rejects_stale_corpus(
    scoped_corpora, tmp_path: Path, fake_embedding
) -> None:
    idx = tmp_path / "idx"
    build_scoped_index = getattr(index_module, "build_scoped_index", None)
    IndexMismatchError = getattr(index_module, "IndexMismatchError", RuntimeError)
    assert build_scoped_index is not None
    build_scoped_index(
        corpora=scoped_corpora,
        index_path=idx,
        embedding=fake_embedding,
    )
    experience, _ = scoped_corpora
    (experience.root / "continuity.md").write_text(
        "# Changed after index build\n",
        encoding="utf-8",
    )

    with pytest.raises(IndexMismatchError, match="stale corpus"):
        search(
            "terminal frame continuity",
            scope="experience",
            corpora=scoped_corpora,
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
    scoped_corpora, tmp_path: Path, capsys
) -> None:
    experience, superpowers = scoped_corpora
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
        "--index",
        str(idx),
    ]
    assert agent_memory_main([*common, "build"]) == 0
    assert agent_memory_main([*common, "search", "recovery", "--json"]) == 0
    output = capsys.readouterr().out
    assert '"corpus_kind": "experience"' in output
    assert '"corpus_kind": "superpowers"' in output


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
    scoped_corpora, tmp_path: Path, capsys
) -> None:
    experience, _ = scoped_corpora
    idx = tmp_path / "idx"
    embedding = DeterministicFakeEmbeddings()
    index_module.build_scoped_index((experience,), idx, embedding)
    client = index_module.load_index(idx, embedding)
    client.delete_collection(experience.collection_name)

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
