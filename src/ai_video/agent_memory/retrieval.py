"""Search and formatting for authority-separated Agent project knowledge."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from ai_video.agent_memory.config import (
    DEFAULT_TOP_N,
    DENSE_MIN_NULL_EXCESS,
    DENSE_MIN_TOP1_MARGIN,
    HYBRID_CANDIDATE_TOP_K,
    HYBRID_RRF_K,
    LEXICAL_MIN_QUERY_COVERAGE,
    MINIMUM_RELEVANCE_SCORE,
)
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.hybrid import (
    lexical_relevance_score,
    rank_bm25,
    reciprocal_rank_fusion,
    select_dense_null_query,
)
from ai_video.agent_memory.index import (
    IndexMismatchError,
    load_index,
    validate_index_path,
    validate_materialized_index,
    validate_run_summary_index,
    validate_scoped_index,
)
from ai_video.agent_memory.manifest import IndexManifest


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
    chunk_id: str = ""
    dense_score: Optional[float] = None
    lexical_score: float = 0.0
    lexical_relevance_score: float = 0.0
    lexical_query_coverage: float = 0.0
    fusion_score: float = 0.0
    dense_null_score: float = 0.0
    dense_null_excess: float = 0.0
    dense_top1_margin: float = 0.0
    admission_lane: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _format_excerpt(text: str, max_len: int = 240) -> str:
    """Trim a chunk body to ``max_len`` characters on a whitespace boundary."""
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def _authority_label(corpus_kind: str, authority: str) -> str:
    if authority == "current_project_contract":
        return "authority: current project contract; re-open source before use"
    if authority == "current_runtime_baseline":
        return "authority: current runtime baseline; verify freshness"
    if authority == "current_roadmap":
        return "authority: current roadmap; not runtime truth"
    if corpus_kind == "research":
        return "authority: advisory research; not runtime truth"
    if corpus_kind == "deferred":
        return "authority: deferred decision advisory; not current authorization"
    if corpus_kind == "current_docs":
        return "authority: current project document advisory; re-open source"
    if corpus_kind == "superpowers":
        return "authority: historical design/plan; not runtime truth"
    if corpus_kind == "run_summaries":
        return "authority: auto-generated run summary advisory (not runtime truth)"
    return "authority: advisory experience"


_ALL_SCOPE_ORDER = (
    "experience",
    "superpowers",
    "current_docs",
    "research",
    "deferred",
)
_ALL_SCOPE_WEIGHTS = {
    "experience": 2,
    "superpowers": 2,
    "current_docs": 2,
    "research": 1,
    "deferred": 1,
}


def _allocate_scope_limits(kinds: set[str], top_k: int) -> dict[str, int]:
    """Allocate stable per-corpus quotas while keeping every corpus visible."""
    ordered = [kind for kind in _ALL_SCOPE_ORDER if kind in kinds]
    if not ordered:
        return {}
    if len(ordered) == 1:
        return {ordered[0]: top_k}
    allocations = {kind: 1 for kind in ordered}
    remaining = max(0, top_k - len(ordered))
    if not remaining:
        return allocations
    weight_total = sum(_ALL_SCOPE_WEIGHTS[kind] for kind in ordered)
    raw = {
        kind: remaining * _ALL_SCOPE_WEIGHTS[kind] / weight_total
        for kind in ordered
    }
    for kind in ordered:
        extra = int(raw[kind])
        allocations[kind] += extra
        remaining -= extra
    for kind in sorted(
        ordered,
        key=lambda item: (raw[item] - int(raw[item]), -ordered.index(item)),
        reverse=True,
    )[:remaining]:
        allocations[kind] += 1
    return allocations


def search(
    query: str,
    top_k: int = DEFAULT_TOP_N,
    corpus_root: Optional[Path] = None,
    index_path: Optional[Path] = None,
    embedding=None,
    scope: str = "experience",
    corpora: Optional[Sequence[CorpusSpec]] = None,
    *,
    runs_corpus: Optional[CorpusSpec] = None,
    runs_index_path: Optional[Path] = None,
) -> List[Hit]:
    """Return up to top-K hits meeting the inclusive relevance threshold.

    The index manifest binds corpus bytes, embedding identity and collection
    scope. Search is validation/query-only: missing, partial, or
    identity-mismatched indexes fail closed and require an explicit build.
    Corpus freshness is also validated when the caller supplies ``corpora`` or
    ``corpus_root``; root-free legacy calls can validate only manifest identity
    and physical completeness. Superpowers-only scope never opens the
    run-summary index.
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
    allowed_kinds = (
        set(_ALL_SCOPE_ORDER) if scope == "all" else {scope}
    )
    expected = tuple(corpora or ())
    if not expected and corpus_root is not None:
        expected = (CorpusSpec.experience(Path(corpus_root)),)
    expected = tuple(item for item in expected if item.kind in allowed_kinds)
    requested_kinds = (
        {item.kind for item in expected} if expected else allowed_kinds
    )
    if expected:
        validated_manifest = validate_scoped_index(expected, idx_path, embedding)
    else:
        validated_manifest = validate_materialized_index(
            idx_path,
            embedding,
            requested_kinds,
        )

    # Run-summary inclusion is opt-in via an explicit ``runs_corpus``.
    # When the caller does not provide one we leave the search scoped to
    # experience / superpowers so historical callers that never asked
    # for run-summary retrieval keep their previous behaviour.  The CLI
    # passes the default ``runs_corpus`` explicitly so end users still
    # benefit from retrieval when an explicit build has materialized that
    # index; missing roots contribute zero hits. This avoids silently indexing
    # the repository's real ``runs/`` directory for callers that intentionally
    # kept their search run-free.
    run_spec = (
        runs_corpus
        if runs_corpus is not None
        and scope in {"experience", "all"}
        and runs_corpus.root.is_dir()
        else None
    )
    runs_manifest: IndexManifest | None = None
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
        runs_manifest = validate_run_summary_index(
            runs_index_path,
            run_spec,
            embedding,
        )

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
    manifest = validated_manifest

    indexed = {item.kind: item for item in manifest.corpora}
    missing = requested_kinds - indexed.keys()
    if missing:
        raise IndexMismatchError(
            f"scope(s) {sorted(missing)} not present in index; rebuild required"
        )

    allocations = _allocate_scope_limits(requested_kinds, top_k)

    hits: List[Hit] = []
    query_vector = embedding.embed_query(query)
    null_query_vector = embedding.embed_query(select_dense_null_query(query))
    for kind, limit in allocations.items():
        item = indexed[kind]
        try:
            collection = store.get_collection(item.collection_name)
            available = collection.count()
            if available == 0:
                continue
            hits.extend(
                _search_collection(
                    query=query,
                    query_vector=query_vector,
                    null_query_vector=null_query_vector,
                    collection=collection,
                    available=available,
                    limit=limit,
                    corpus_kind=kind,
                    default_authority=item.authority,
                )
            )
        except Exception as exc:
            raise IndexMismatchError(
                f"index collection for scope {kind!r} is unavailable; rebuild required"
            ) from exc

    # When the caller opted into run-summary inclusion, query the
    # separate run-summary index so auto-generated run notes surface
    # in the same ranked hit list without manual copying.
    if run_spec is not None:
        assert runs_manifest is not None
        hits.extend(
            _search_runs(
                query,
                top_k,
                runs_index_path,
                embedding,
                manifest=runs_manifest,
                query_vector=query_vector,
                null_query_vector=null_query_vector,
            )
        )

    return sorted(hits, key=_hit_sort_key, reverse=True)[:top_k]


def _hit_sort_key(hit: Hit) -> tuple[float, float, float, float]:
    """Order admitted hits by fusion, then deterministic lane scores."""
    return (
        hit.fusion_score,
        hit.score,
        hit.lexical_score,
        hit.dense_score if hit.dense_score is not None else -1.0,
    )


def _lexical_document(text: str, metadata: dict) -> str:
    """Combine chunk body and canonical locator metadata for lexical search."""
    fields = (
        text,
        metadata.get("source", ""),
        metadata.get("title", ""),
        metadata.get("section", ""),
        metadata.get("h1", ""),
        metadata.get("h2", ""),
        metadata.get("h3", ""),
    )
    return "\n".join(str(field) for field in fields if field)


def _search_collection(
    *,
    query: str,
    query_vector: Sequence[float],
    null_query_vector: Sequence[float],
    collection,
    available: int,
    limit: int,
    corpus_kind: str,
    default_authority: str,
) -> List[Hit]:
    """Fuse dense and lexical candidates from one validated collection."""
    candidate_limit = min(HYBRID_CANDIDATE_TOP_K, available)
    dense_raw = collection.query(
        query_embeddings=[query_vector],
        n_results=candidate_limit,
        include=["documents", "metadatas", "distances"],
    )
    null_raw = collection.query(
        query_embeddings=[null_query_vector],
        n_results=1,
        include=["distances"],
    )
    lexical_raw = collection.get(include=["documents", "metadatas"])

    dense_ids = dense_raw.get("ids", [[]])[0] or []
    dense_documents = dense_raw.get("documents", [[]])[0] or []
    dense_metadatas = dense_raw.get("metadatas", [[]])[0] or []
    dense_distances = dense_raw.get("distances", [[]])[0] or []
    if not (
        len(dense_ids)
        == len(dense_documents)
        == len(dense_metadatas)
        == len(dense_distances)
    ):
        raise ValueError("dense retrieval result fields have inconsistent lengths")
    null_distances = null_raw.get("distances", [[]])[0] or []
    if len(null_distances) != 1:
        raise ValueError("dense null calibration must return exactly one distance")

    lexical_ids = lexical_raw.get("ids", []) or []
    lexical_documents = lexical_raw.get("documents", []) or []
    lexical_metadatas = lexical_raw.get("metadatas", []) or []
    if not (
        len(lexical_ids) == len(lexical_documents) == len(lexical_metadatas)
    ):
        raise ValueError("lexical retrieval corpus fields have inconsistent lengths")

    records = {
        str(chunk_id): (text or "", metadata or {})
        for chunk_id, text, metadata in zip(
            lexical_ids,
            lexical_documents,
            lexical_metadatas,
        )
    }
    for chunk_id, text, metadata in zip(
        dense_ids,
        dense_documents,
        dense_metadatas,
    ):
        records.setdefault(str(chunk_id), (text or "", metadata or {}))

    dense_ranking = [str(chunk_id) for chunk_id in dense_ids]
    dense_scores = {
        str(chunk_id): 1.0 - float(distance)
        for chunk_id, distance in zip(dense_ids, dense_distances)
    }
    ordered_dense_scores = [dense_scores[chunk_id] for chunk_id in dense_ranking]
    dense_top1_margin = (
        ordered_dense_scores[0] - ordered_dense_scores[1]
        if len(ordered_dense_scores) > 1
        else 0.0
    )
    dense_margin_admitted = (
        len(ordered_dense_scores) == 1
        or dense_top1_margin >= DENSE_MIN_TOP1_MARGIN
    )
    dense_null_score = 1.0 - float(null_distances[0])
    lexical_matches = rank_bm25(
        query,
        {
            chunk_id: _lexical_document(text, metadata)
            for chunk_id, (text, metadata) in records.items()
        },
        min(HYBRID_CANDIDATE_TOP_K, available),
    )
    lexical_ranking = [match.chunk_id for match in lexical_matches]
    lexical_scores = {match.chunk_id: match.score for match in lexical_matches}
    lexical_coverages = {
        match.chunk_id: match.query_coverage for match in lexical_matches
    }
    fusion_scores = reciprocal_rank_fusion(
        ((dense_ranking, 1.0), (lexical_ranking, 1.0)),
        rank_constant=HYBRID_RRF_K,
    )

    hits: List[Hit] = []
    for chunk_id in fusion_scores:
        text, md = records[chunk_id]
        dense_score = dense_scores.get(chunk_id)
        lexical_score = lexical_scores.get(chunk_id, 0.0)
        lexical_query_coverage = lexical_coverages.get(chunk_id, 0.0)
        bounded_lexical_score = lexical_relevance_score(lexical_score)
        dense_null_excess = (
            dense_score - dense_null_score if dense_score is not None else 0.0
        )
        lexical_admitted = (
            bounded_lexical_score >= MINIMUM_RELEVANCE_SCORE
            and lexical_query_coverage >= LEXICAL_MIN_QUERY_COVERAGE
        )
        dense_admitted = (
            dense_score is not None
            and dense_score >= MINIMUM_RELEVANCE_SCORE
            and dense_null_excess >= DENSE_MIN_NULL_EXCESS
            and dense_margin_admitted
        )
        if not lexical_admitted and not dense_admitted:
            continue
        if lexical_admitted and dense_admitted:
            admission_lane = "hybrid"
        elif lexical_admitted:
            admission_lane = "lexical"
        else:
            admission_lane = "dense"
        score = max(
            bounded_lexical_score if lexical_admitted else 0.0,
            dense_score if dense_admitted and dense_score is not None else 0.0,
        )
        hits.append(
            Hit(
                source=str(md.get("source", "?")),
                title=str(md.get("title", "?")),
                section=str(md.get("section", "")),
                score=score,
                excerpt=_format_excerpt(text),
                chunk_index=int(md.get("chunk_index", -1)),
                h1=str(md.get("h1", "")),
                h2=str(md.get("h2", "")),
                h3=str(md.get("h3", "")),
                date=md.get("date"),
                corpus_kind=str(md.get("corpus_kind", corpus_kind)),
                authority=str(md.get("authority", default_authority)),
                document_kind=str(md.get("document_kind", "")),
                status=str(md.get("status", "")),
                run_id=str(md.get("run_id", "")),
                run_family=str(md.get("run_family", "")),
                run_version=int(md.get("run_version", 0) or 0),
                summary_sha256=str(md.get("summary_sha256", "")),
                chunk_id=chunk_id,
                dense_score=dense_score,
                lexical_score=lexical_score,
                lexical_relevance_score=bounded_lexical_score,
                lexical_query_coverage=lexical_query_coverage,
                fusion_score=fusion_scores[chunk_id],
                dense_null_score=dense_null_score,
                dense_null_excess=dense_null_excess,
                dense_top1_margin=dense_top1_margin,
                admission_lane=admission_lane,
            )
        )
    return sorted(hits, key=_hit_sort_key, reverse=True)[:limit]


def _search_runs(
    query: str,
    top_k: int,
    runs_index_path: Path,
    embedding,
    *,
    manifest: IndexManifest,
    query_vector: Sequence[float],
    null_query_vector: Sequence[float],
) -> List[Hit]:
    """Search the validated run-summary index or fail closed."""
    runs_index_path = Path(runs_index_path)
    if not runs_index_path.exists() or not (
        runs_index_path / "chroma.sqlite3"
    ).is_file() or not (runs_index_path / "manifest.json").is_file():
        raise IndexMismatchError("run-summary index disappeared during search")
    try:
        store = load_index(runs_index_path, embedding)
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
        return _search_collection(
            query=query,
            query_vector=query_vector,
            null_query_vector=null_query_vector,
            collection=collection,
            available=available,
            limit=top_k,
            corpus_kind="run_summaries",
            default_authority=item.authority,
        )
    except Exception as exc:
        raise IndexMismatchError(
            "run-summary index collection is unavailable"
        ) from exc


def format_text(hits: Iterable[Hit]) -> str:
    """Render ``hits`` as a Codex-friendly plain-text block."""
    hits = list(hits)
    if not hits:
        return "No relevant prior records found."

    lines = ["Relevant prior records:", "", "Project knowledge is advisory.", ""]
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. {h.source}")
        lines.append(f"   score: {h.score:.4f}")
        if h.admission_lane:
            lines.append(f"   admission_lane: {h.admission_lane}")
        lines.append(f"   {_authority_label(h.corpus_kind, h.authority)}")
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
