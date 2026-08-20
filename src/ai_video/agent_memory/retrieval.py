"""Search interface and result formatting for Agent Experience Memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.index import load_index


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
) -> List[Hit]:
    """Return the top-K hits for ``query`` against the local Chroma index.

    ``corpus_root`` is currently unused by the search path itself (it is
    accepted so callers can pass the same arguments to ``build`` and
    ``search``); it is documented here for forward compatibility.
    """
    embedding = embedding or build_embedding()
    idx_path = Path(index_path or ".agent/memory/index")
    store = load_index(idx_path, embedding)
    if store is None:
        raise FileNotFoundError(
            f"No Agent Experience Memory index at {idx_path}. "
            "Run `python -m scripts.agent_memory build` first."
        )

    try:
        raw = store.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception:
        raw = [(d, 0.0) for d in store.similarity_search(query, k=top_k)]

    hits: List[Hit] = []
    for doc, score in raw:
        md = doc.metadata or {}
        hits.append(
            Hit(
                source=str(md.get("source", "?")),
                title=str(md.get("title", "?")),
                section=str(md.get("section", "")),
                score=float(score),
                excerpt=_format_excerpt(doc.page_content),
                chunk_index=int(md.get("chunk_index", -1)),
                h1=str(md.get("h1", "")),
                h2=str(md.get("h2", "")),
                h3=str(md.get("h3", "")),
                date=md.get("date"),
            )
        )
    return hits


def format_text(hits: Iterable[Hit]) -> str:
    """Render ``hits`` as a Codex-friendly plain-text block."""
    hits = list(hits)
    if not hits:
        return "No relevant prior records found."

    lines = ["Relevant prior records:", ""]
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. {h.source}")
        lines.append(f"   score: {h.score:.4f}")
        breadcrumb = [s for s in (h.h1, h.h2, h.h3) if s]
        if breadcrumb:
            lines.append(f"   section: {' > '.join(breadcrumb)}")
        elif h.section:
            lines.append(f"   section: {h.section}")
        lines.append(f"   excerpt: {h.excerpt}")
        lines.append("")
    return "\n".join(lines).rstrip()
