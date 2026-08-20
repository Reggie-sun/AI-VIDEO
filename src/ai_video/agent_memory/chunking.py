"""Heading-aware Markdown chunking.

Splits each document by Markdown headers (``#``, ``##``, ``###``) so that
each chunk preserves the surrounding ``problem / cause / conclusion /
experience`` semantic unit.  When a section exceeds the configured
character budget it is further split with a recursive character splitter.

Each chunk carries:

  - ``source`` / ``title`` / ``date`` / ``doc_index`` (file-level)
  - ``h1`` / ``h2`` / ``h3`` (header path above the chunk)
  - ``section`` (most specific header that produced the chunk)
  - ``chunk_index`` (ordinal within the parent document)
  - ``local_index`` (ordinal within the parent section, after length split)
"""

from __future__ import annotations

from typing import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


HEADER_LEVELS: list[tuple[str, str]] = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


def _build_splitters(
    fallback_chunk_size: int = 800,
    fallback_chunk_overlap: int = 80,
) -> tuple[MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter]:
    header_splitter = MarkdownHeaderTextSplitter(
        strip_headers=False,
        headers_to_split_on=HEADER_LEVELS,
    )
    fallback = RecursiveCharacterTextSplitter(
        chunk_size=fallback_chunk_size,
        chunk_overlap=fallback_chunk_overlap,
    )
    return header_splitter, fallback


def chunk_documents(
    docs: Iterable[Document],
    fallback_chunk_size: int = 800,
    fallback_chunk_overlap: int = 80,
) -> list[Document]:
    """Split ``docs`` by header, then by length when a section is too large.

    File-level metadata is preserved on every chunk; per-section header
    metadata is added on top of it.
    """
    header_splitter, fallback = _build_splitters(
        fallback_chunk_size=fallback_chunk_size,
        fallback_chunk_overlap=fallback_chunk_overlap,
    )
    chunks: list[Document] = []
    for doc in docs:
        sections = header_splitter.split_text(doc.page_content)
        chunk_index = 0
        for section in sections:
            sec_meta = dict(doc.metadata)
            sec_meta["h1"] = section.metadata.get("h1", "") or ""
            sec_meta["h2"] = section.metadata.get("h2", "") or ""
            sec_meta["h3"] = section.metadata.get("h3", "") or ""
            sec_meta["section"] = (
                section.metadata.get("h3")
                or section.metadata.get("h2")
                or section.metadata.get("h1")
                or ""
            )
            # Chroma rejects None; keep every value string-coerced.
            sec_meta = {k: ("" if v is None else v) for k, v in sec_meta.items()}
            seed = Document(
                page_content=section.page_content,
                metadata=sec_meta,
            )
            subs = fallback.split_documents([seed])
            for local_index, sub in enumerate(subs):
                sub_meta = dict(sec_meta)
                sub_meta["chunk_index"] = chunk_index
                sub_meta["local_index"] = local_index
                chunk_index += 1
                chunks.append(
                    Document(page_content=sub.page_content, metadata=sub_meta)
                )
    return chunks
