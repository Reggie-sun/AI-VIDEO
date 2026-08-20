"""Markdown corpus loading for docs/record_for_agent/.

This module walks the corpus root, reads every ``*.md`` file, and produces
LangChain ``Document`` objects carrying file-level metadata:

  - ``source``: repository-relative path
  - ``title``: first ``# Title`` heading, or filename fallback
  - ``date``: ``Date: YYYY-MM-DD`` line, if present
  - ``doc_index``: ordinal within the corpus

Frontmatter (YAML between leading ``---`` fences) is parsed best-effort and
merged into metadata when present, but its absence is tolerated.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

from langchain_core.documents import Document


_DATE_LINE = re.compile(r"^Date:\s*(\S+)", re.MULTILINE)
_TITLE_LINE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def iter_markdown_files(root: Path) -> Iterator[Path]:
    """Yield every ``*.md`` file under ``root``, sorted by relative path."""
    root = Path(root)
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*.md")):
        yield path


def parse_title(text: str, fallback: str) -> str:
    """Return the first ``# Title`` heading or ``fallback``."""
    m = _TITLE_LINE.search(text)
    return m.group(1).strip() if m else fallback


def parse_date(text: str) -> str | None:
    """Return the ``Date:`` value or ``None`` when not present."""
    m = _DATE_LINE.search(text)
    return m.group(1) if m else None


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


def load_documents(root: Path) -> list[Document]:
    """Read every markdown file under ``root`` into ``Document`` objects.

    Returns an empty list when ``root`` is missing or empty.
    """
    root = Path(root)
    docs: list[Document] = []
    for idx, path in enumerate(iter_markdown_files(root)):
        text = path.read_text(encoding="utf-8")
        meta = {
            "source": _relative_to_cwd(path),
            "title": parse_title(text, fallback=path.name),
            "date": parse_date(text),
            "doc_index": idx,
        }
        meta.update(parse_frontmatter(text))
        # Chroma rejects None values in metadata; coerce absent fields to "".
        meta = {k: ("" if v is None else v) for k, v in meta.items()}
        docs.append(Document(page_content=text, metadata=meta))
    return docs
