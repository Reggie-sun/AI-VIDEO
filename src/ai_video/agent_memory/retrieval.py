"""Search interface and result formatting for Agent Experience Memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.index import (
    IndexMismatchError,
    ensure_run_summary_index,
    load_index,
    read_index_manifest,
    validate_index_path,
    validate_manifest,
    validate_run_summary_index,
)


@dataclass
class Hit:
    """A single retrieval hit returned to the caller / CLI."""

    source: str
    title: str
    section: str
    score: float
    excerpt: str
    chunk_index: int
    h1: str
    h2: str
    h3: str
    date: Optional[str]
    corpus_kind: str = "experience"
    authority: str = "advisory_experience"
    document_kind: str = "experience_record"
    status: str = ""
    # Auto-generated run-summary fields. ``run_id``/``run_family``/``run_version``
    # and ``summary_sha256`` are populated only for ``run_summary`` hits.
    run_id: str = ""
    run_family: str = ""
    run_version: int = 0
    summary_sha256: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _format_excerpt(text: str, max_len: int = 240) -> str:
    """Trim a chunk body to ``max_len`` characters on a whitespace boundary."""
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def _authority_label(corpus_kind: str) -> str:
    if corpus_kind == "superpowers":
        return "authority: historical design/plan; not runtime truth"
    if corpus_kind == "run_summaries":
        return "authority: auto-generated run summary advisory (not runtime truth)"
    return "authority: advisory experience"


def search(
    query: str,
    top_k: int = 5,
    corpus_root: Optional[Path] = None,
    index_path: Optional[Path] = None,
    embedding=None,
    scope: str = "experience",
    corpora: Optional[Sequence[CorpusSpec]] = None,
    *,
    runs_corpus: Optional[CorpusSpec] = None,
    runs_index_path: Optional[Path] = None,
) -> List[Hit]:
    """Return the top-K hits for ``query`` against the local Chroma index.

    The index manifest binds corpus bytes, embedding identity and collection
    scope. When callers provide corpus roots, stale source bytes fail closed.

    Experience / all scopes transparently ensure the separate
    ``run_summaries`` derived index is current so users never need a
    manual copy or build to surface auto-generated run summaries.
    Superpowers-only scope never opens the run-summary index.
    """
    if top_k < 1:
        raise ValueError("top_k must be positive")
    valid_scopes = {"experience", "superpowers", "all"}
    if scope not in valid_scopes:
        raise ValueError(f"unknown Agent Memory scope: {scope!r}")
    embedding = embedding or build_embedding()
    idx_path = Path(index_path or ".agent/memory/index")
    runs_index_path = Path(
        runs_index_path or ".agent/memory/run-summaries"
    )

    # Run-summary inclusion is opt-in via an explicit ``runs_corpus``.
    # When the caller does not provide one we leave the search scoped to
    # experience / superpowers so historical callers that never asked
    # for run-summary retrieval keep their previous behaviour.  The CLI
    # passes the default ``runs_corpus`` explicitly so end users still
    # benefit from automatic retrieval; missing roots contribute zero hits.
    # Experience and all scopes transparently ensure the run-summary
    # derived index is current *only when* the caller opted in by
    # providing an explicit runs corpus.  This avoids silently indexing
    # the repository's real ``runs/`` directory for callers that
    # intentionally kept their search run-free.
    run_spec = (
        runs_corpus
        if runs_corpus is not None
        and scope in {"experience", "all"}
        and runs_corpus.root.is_dir()
        else None
    )
    if run_spec is not None:
        protected_paths = [
            idx_path,
            run_spec.root,
            *(item.root for item in (corpora or ())),
        ]
        if corpus_root is not None:
            protected_paths.append(Path(corpus_root))
        validate_index_path(
            runs_index_path,
            tuple(protected_paths),
            label="run-summary index",
        )
        ensure_run_summary_index(run_spec, runs_index_path, embedding)

    try:
        store = load_index(idx_path, embedding)
    except Exception as exc:
        raise IndexMismatchError(
            f"cannot open Agent Memory index at {idx_path}; rebuild required"
        ) from exc
    if store is None:
        raise FileNotFoundError(
            f"No Agent Experience Memory index at {idx_path}. "
            "Run `python -m scripts.agent_memory build` first."
        )
    manifest = read_index_manifest(idx_path)
    expected = tuple(corpora or ())
    if not expected and corpus_root is not None:
        expected = (CorpusSpec.experience(Path(corpus_root)),)
    if scope == "all":
        requested_kinds = {"experience", "superpowers"}
    else:
        requested_kinds = {scope}
    expected = tuple(item for item in expected if item.kind in requested_kinds)
    validate_manifest(manifest, expected, embedding)

    indexed = {item.kind: item for item in manifest.corpora}
    missing = requested_kinds - indexed.keys()
    if missing:
        raise IndexMismatchError(
            f"scope(s) {sorted(missing)} not present in index; rebuild required"
        )

    if scope == "all":
        experience_k = max(1, (top_k + 1) // 2)
        superpowers_k = max(1, top_k // 2)
        allocations = {"experience": experience_k, "superpowers": superpowers_k}
    else:
        allocations = {scope: top_k}

    hits: List[Hit] = []
    query_vector = embedding.embed_query(query)
    for kind, limit in allocations.items():
        item = indexed[kind]
        try:
            collection = store.get_collection(item.collection_name)
            available = collection.count()
            if available == 0:
                continue
            raw = collection.query(
                query_embeddings=[query_vector],
                n_results=min(limit, available),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise IndexMismatchError(
                f"index collection for scope {kind!r} is unavailable; rebuild required"
            ) from exc
        documents = raw.get("documents", [[]])[0] or []
        metadatas = raw.get("metadatas", [[]])[0] or []
        distances = raw.get("distances", [[]])[0] or []
        for text, md, distance in zip(documents, metadatas, distances):
            md = md or {}
            hits.append(
                Hit(
                    source=str(md.get("source", "?")),
                    title=str(md.get("title", "?")),
                    section=str(md.get("section", "")),
                    score=1.0 - float(distance),
                    excerpt=_format_excerpt(text or ""),
                    chunk_index=int(md.get("chunk_index", -1)),
                    h1=str(md.get("h1", "")),
                    h2=str(md.get("h2", "")),
                    h3=str(md.get("h3", "")),
                    date=md.get("date"),
                    corpus_kind=str(md.get("corpus_kind", kind)),
                    authority=str(md.get("authority", item.authority)),
                    document_kind=str(md.get("document_kind", "")),
                    status=str(md.get("status", "")),
                )
            )

    # When the caller opted into run-summary inclusion, query the
    # separate run-summary index so auto-generated run notes surface
    # in the same ranked hit list without manual copying.
    if run_spec is not None:
        hits.extend(
            _search_runs(
                query,
                top_k,
                run_spec,
                runs_index_path,
                embedding,
            )
        )

    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]


def _search_runs(
    query: str,
    top_k: int,
    runs_corpus: CorpusSpec,
    runs_index_path: Path,
    embedding,
) -> List[Hit]:
    """Search the validated run-summary index or fail closed."""
    runs_index_path = Path(runs_index_path)
    if not runs_index_path.exists() or not (
        runs_index_path / "chroma.sqlite3"
    ).is_file() or not (runs_index_path / "manifest.json").is_file():
        raise IndexMismatchError("run-summary index disappeared during search")
    try:
        store = load_index(runs_index_path, embedding)
        manifest = validate_run_summary_index(
            runs_index_path,
            runs_corpus,
            embedding,
        )
    except Exception as exc:
        raise IndexMismatchError(
            "cannot open the current run-summary index"
        ) from exc
    if store is None:
        raise IndexMismatchError("run-summary index disappeared during search")
    indexed = {item.kind: item for item in manifest.corpora}
    item = indexed.get("run_summaries")
    if item is None:
        raise IndexMismatchError("run-summary collection is missing from its index")
    try:
        collection = store.get_collection(item.collection_name)
        available = collection.count()
        if available != item.chunk_count:
            raise IndexMismatchError("run-summary collection changed during search")
        if available == 0:
            return []
        raw = collection.query(
            query_embeddings=[embedding.embed_query(query)],
            n_results=min(top_k, available),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        raise IndexMismatchError(
            "run-summary index collection is unavailable"
        ) from exc
    documents = raw.get("documents", [[]])[0] or []
    metadatas = raw.get("metadatas", [[]])[0] or []
    distances = raw.get("distances", [[]])[0] or []
    hits: List[Hit] = []
    for text, md, distance in zip(documents, metadatas, distances):
        md = md or {}
        hits.append(
            Hit(
                source=str(md.get("source", "?")),
                title=str(md.get("title", "?")),
                section=str(md.get("section", "")),
                score=1.0 - float(distance),
                excerpt=_format_excerpt(text or ""),
                chunk_index=int(md.get("chunk_index", -1)),
                h1=str(md.get("h1", "")),
                h2=str(md.get("h2", "")),
                h3=str(md.get("h3", "")),
                date=md.get("date"),
                corpus_kind=str(md.get("corpus_kind", "run_summaries")),
                authority=str(md.get("authority", item.authority)),
                document_kind=str(md.get("document_kind", "run_summary")),
                status=str(md.get("status", "")),
                run_id=str(md.get("run_id", "")),
                run_family=str(md.get("run_family", "")),
                run_version=int(md.get("run_version", 0) or 0),
                summary_sha256=str(md.get("summary_sha256", "")),
            )
        )
    return hits


def format_text(hits: Iterable[Hit]) -> str:
    """Render ``hits`` as a Codex-friendly plain-text block."""
    hits = list(hits)
    if not hits:
        return "No relevant prior records found."

    lines = ["Relevant prior records:", "", "Project knowledge is advisory.", ""]
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. {h.source}")
        lines.append(f"   score: {h.score:.4f}")
        lines.append(f"   {_authority_label(h.corpus_kind)}")
        if h.status:
            lines.append(f"   document status: {h.status}")
        if h.corpus_kind == "run_summaries":
            lines.append(f"   run_id: {h.run_id}")
            if h.run_family:
                lines.append(f"   run_family: {h.run_family}")
            if h.run_version:
                lines.append(f"   run_version: {h.run_version}")
            if h.summary_sha256:
                lines.append(f"   summary_sha256: {h.summary_sha256}")
        breadcrumb = [s for s in (h.h1, h.h2, h.h3) if s]
        if breadcrumb:
            lines.append(f"   section: {' > '.join(breadcrumb)}")
        elif h.section:
            lines.append(f"   section: {h.section}")
        lines.append(f"   excerpt: {h.excerpt}")
        lines.append("")
    return "\n".join(lines).rstrip()
