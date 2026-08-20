"""Markdown corpus loading for the named Agent Memory corpora.

This module walks the corpus root, reads every ``*.md`` file, and produces
LangChain ``Document`` objects carrying file-level metadata:

  - ``source``: working-tree-relative path when available
  - ``title``: first ``# Title`` heading, or filename fallback
  - ``date``: ``Date: YYYY-MM-DD`` line, if present
  - ``doc_index``: ordinal within the corpus

Frontmatter (YAML between leading ``---`` fences) is parsed best-effort and
merged into metadata when present, but its absence is tolerated.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from langchain_core.documents import Document


_DATE_LINE = re.compile(r"^Date:\s*(\S+)", re.MULTILINE)
_TITLE_LINE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_STATUS_LINE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class CorpusSpec:
    """A named corpus with explicit authority and collection identity."""

    kind: str
    root: Path
    collection_name: str
    authority: str

    @classmethod
    def experience(cls, root: Path) -> "CorpusSpec":
        return cls(
            kind="experience",
            root=Path(root),
            collection_name="agent_memory_experience",
            authority="advisory_experience",
        )

    @classmethod
    def superpowers(cls, root: Path) -> "CorpusSpec":
        return cls(
            kind="superpowers",
            root=Path(root),
            collection_name="agent_memory_superpowers",
            authority="historical_design_plan",
        )


def iter_markdown_files(root: Path) -> Iterator[Path]:
    """Yield every ``*.md`` file under ``root``, sorted by relative path."""
    root = Path(root)
    if not root.is_dir():
        return
    resolved_root = root.resolve()
    for path in sorted(root.rglob("*.md")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            path.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        yield path


def parse_title(text: str, fallback: str) -> str:
    """Return the first ``# Title`` heading or ``fallback``."""
    m = _TITLE_LINE.search(text)
    return m.group(1).strip() if m else fallback


def parse_date(text: str) -> str | None:
    """Return the ``Date:`` value or ``None`` when not present."""
    m = _DATE_LINE.search(text)
    return m.group(1) if m else None


def parse_status(text: str) -> str | None:
    """Return the first ``Status:`` value or ``None`` when absent."""
    m = _STATUS_LINE.search(text)
    return m.group(1).strip() if m else None


def parse_frontmatter(text: str) -> dict[str, str]:
    """Best-effort YAML-free frontmatter parser.

    Returns a flat dict of ``key: value`` strings from the leading
    ``---`` / ``---`` block when present; otherwise ``{}``.  We deliberately
    avoid pulling in PyYAML here because the existing record files do not
    use real YAML structures, only flat key/value pairs.
    """
    m = _FRONTMATTER.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def _relative_to_cwd(path: Path) -> str:
    """Return ``path`` relative to the current working directory when possible."""
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _document_kind(path: Path, corpus_kind: str) -> str:
    if corpus_kind == "experience":
        return "experience_record"
    if "specs" in path.parts:
        return "spec"
    if "plans" in path.parts:
        return "plan"
    return "design_note"


def load_documents(
    root: Path,
    *,
    corpus: CorpusSpec | None = None,
) -> list[Document]:
    """Read every markdown file under ``root`` into ``Document`` objects.

    Returns an empty list when ``root`` is missing or empty.
    """
    documents, _, _ = load_document_snapshot(root, corpus=corpus)
    return documents


def load_document_snapshot(
    root: Path,
    *,
    corpus: CorpusSpec | None = None,
) -> tuple[list[Document], str, int]:
    """Read documents once and return the digest of those exact source bytes."""
    root = Path(root)
    corpus = corpus or CorpusSpec.experience(root)
    docs: list[Document] = []
    digest = hashlib.sha256()
    resolved_root = root.resolve()
    for idx, path in enumerate(iter_markdown_files(root)):
        payload = path.read_bytes()
        relative = path.resolve().relative_to(resolved_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
        text = payload.decode("utf-8")
        meta = parse_frontmatter(text)
        # Corpus identity and canonical document metadata are trusted values;
        # untrusted frontmatter must never be able to override them.
        meta.update({
            "source": _relative_to_cwd(path),
            "title": parse_title(text, fallback=path.name),
            "date": parse_date(text),
            "status": parse_status(text),
            "doc_index": idx,
            "corpus_kind": corpus.kind,
            "authority": corpus.authority,
            "document_kind": _document_kind(path, corpus.kind),
        })
        # Chroma rejects None values in metadata; coerce absent fields to "".
        meta = {k: ("" if v is None else v) for k, v in meta.items()}
        docs.append(Document(page_content=text, metadata=meta))
    return docs, digest.hexdigest(), len(docs)
