"""Search interface and result formatting for Agent Experience Memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.index import (
    IndexMismatchError,
    load_index,
    read_index_manifest,
    validate_manifest,
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

    def to_dict(self) -> dict:
        return asdict(self)


def _format_excerpt(text: str, max_len: int = 240) -> str:
    """Trim a chunk body to ``max_len`` characters on a whitespace boundary."""
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def search(
    query: str,
    top_k: int = 5,
    corpus_root: Optional[Path] = None,
    index_path: Optional[Path] = None,
    embedding=None,
    scope: str = "experience",
    corpora: Optional[Sequence[CorpusSpec]] = None,
) -> List[Hit]:
    """Return the top-K hits for ``query`` against the local Chroma index.

    The index manifest binds corpus bytes, embedding identity and collection
    scope. When callers provide corpus roots, stale source bytes fail closed.
    """
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if scope not in {"experience", "superpowers", "all"}:
        raise ValueError(f"unknown Agent Memory scope: {scope!r}")
    embedding = embedding or build_embedding()
    idx_path = Path(index_path or ".agent/memory/index")
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
    requested_kinds = {scope} if scope != "all" else {"experience", "superpowers"}
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
    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]


def format_text(hits: Iterable[Hit]) -> str:
    """Render ``hits`` as a Codex-friendly plain-text block."""
    hits = list(hits)
    if not hits:
        return "No relevant prior records found."

    lines = ["Relevant prior records:", "", "Project knowledge is advisory.", ""]
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. {h.source}")
        lines.append(f"   score: {h.score:.4f}")
        if h.corpus_kind == "superpowers":
            lines.append("   authority: historical design/plan; not runtime truth")
        else:
            lines.append("   authority: advisory experience")
        if h.status:
            lines.append(f"   document status: {h.status}")
        breadcrumb = [s for s in (h.h1, h.h2, h.h3) if s]
        if breadcrumb:
            lines.append(f"   section: {' > '.join(breadcrumb)}")
        elif h.section:
            lines.append(f"   section: {h.section}")
        lines.append(f"   excerpt: {h.excerpt}")
        lines.append("")
    return "\n".join(lines).rstrip()
