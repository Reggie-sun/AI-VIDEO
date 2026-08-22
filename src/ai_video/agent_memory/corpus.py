"""Markdown corpus loading for the named Agent Memory corpora.

This module walks the corpus root, reads every ``*.md`` file, and produces
LangChain ``Document`` objects carrying file-level metadata:

  - ``source``: working-tree-relative path when available
  - ``title``: first ``# Title`` heading, or filename fallback
  - ``date``: ``Date: YYYY-MM-DD`` line, if present
  - ``doc_index``: ordinal within the corpus

Frontmatter (YAML between leading ``---`` fences) is parsed best-effort and
merged into metadata when present, but its absence is tolerated.

Auto-generated ``runs/<run_id>/SUMMARY.md`` files are picked up via a
separate ``run_summaries`` corpus kind that lives next to the existing
``experience`` and ``superpowers`` corpora.  They never piggyback on the
main index and never override Production runtime authority.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, NamedTuple

from langchain_core.documents import Document


_DATE_LINE = re.compile(r"^Date:\s*(\S+)", re.MULTILINE)
_TITLE_LINE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_STATUS_LINE = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
_RUN_VERSION_SUFFIX = re.compile(r"^(?P<family>.+)-v(?P<version>\d+)$")


class RunSummaryEntry(NamedTuple):
    """A single auto-generated ``runs/<run_id>/SUMMARY.md`` candidate."""

    path: Path
    run_id: str
    run_family: str
    run_version: int


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

    @classmethod
    def run_summaries(cls, root: Path) -> "CorpusSpec":
        """Auto-generated ``runs/<run_id>/SUMMARY.md`` corpus.

        Distinct authority so callers can never confuse it with hand-written
        experience records or historical design plans.  The collection is
        intentionally separate from the main index.
        """
        return cls(
            kind="run_summaries",
            root=Path(root),
            collection_name="agent_memory_run_summaries",
            authority="auto_generated_run_summary_advisory",
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
    if corpus_kind == "run_summaries":
        return "run_summary"
    if "specs" in path.parts:
        return "spec"
    if "plans" in path.parts:
        return "plan"
    return "design_note"


def parse_run_id(run_id: str) -> tuple[str, int] | None:
    """Split ``run-id-vN`` into ``(family, version)`` when the suffix matches.

    Returns ``None`` for run ids without a trailing ``-v<integer>`` suffix.
    Such summaries remain eligible as individually named runs.
    """
    m = _RUN_VERSION_SUFFIX.match(run_id)
    if not m:
        return None
    return m.group("family"), int(m.group("version"))


def iter_run_summary_files(root: Path) -> Iterator[RunSummaryEntry]:
    """Yield every ``runs/<run_id>/SUMMARY.md`` candidate as a tagged entry.

    Only exact one-level child directories are considered. Symlinks,
    files at the root level, files in nested subdirectories, and files with
    non-``SUMMARY.md`` names are all skipped. ``run_id`` is derived from the parent
    directory name; ``run_family`` and ``run_version`` are parsed from
    the trailing ``-vN`` suffix when present. Otherwise the family is the
    complete run id and the version is zero.
    """
    root = Path(root)
    if not root.is_dir():
        return
    resolved_root = root.resolve()
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if not entry.is_dir() or entry.is_symlink():
            continue
        run_id = entry.name
        summary = entry / "SUMMARY.md"
        if not summary.exists() or summary.is_symlink() or not summary.is_file():
            continue
        try:
            summary.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        family_version = parse_run_id(run_id)
        family, version = (run_id, 0)
        if family_version is not None:
            family, version = family_version
        yield RunSummaryEntry(
            path=summary,
            run_id=run_id,
            run_family=family,
            run_version=version,
        )


def _select_highest_version(
    entries: list[RunSummaryEntry],
) -> list[RunSummaryEntry]:
    """Keep only the entry with the largest ``run_version`` per family.

    Families without a parseable ``-vN`` suffix are kept individually so
    they still surface in retrieval; they are not collapsed into a
    synthetic "unversioned" bucket.
    """
    best_by_family: dict[str, RunSummaryEntry] = {}
    unversioned: list[RunSummaryEntry] = []
    for entry in entries:
        if entry.run_family == entry.run_id:
            unversioned.append(entry)
            continue
        current = best_by_family.get(entry.run_family)
        if current is None or entry.run_version > current.run_version:
            best_by_family[entry.run_family] = entry
    return [*best_by_family.values(), *unversioned]


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


def load_run_summary_documents(root: Path) -> tuple[list[Document], str, int]:
    """Load ``runs/<run_id>/SUMMARY.md`` into Documents with run-id metadata.

    The returned digest hashes only the bytes of the files that survive
    the highest-version-per-family filter so the manifest can detect
    stale corpora precisely.  Missing roots return an empty digest and
    empty document list rather than raising.
    """
    root = Path(root)
    if not root.is_dir():
        return [], hashlib.sha256(b"").hexdigest(), 0

    eligible: list[RunSummaryEntry] = []
    payloads: dict[Path, tuple[bytes, str]] = {}
    for entry in iter_run_summary_files(root):
        try:
            payload = entry.path.read_bytes()
            text = payload.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        status = parse_status(text)
        if not status:
            continue
        eligible.append(entry)
        payloads[entry.path] = (payload, status)

    selected = _select_highest_version(eligible)

    docs: list[Document] = []
    digest = hashlib.sha256()
    resolved_root = root.resolve()
    for idx, entry in enumerate(sorted(selected, key=lambda item: item.run_id)):
        payload, status = payloads[entry.path]
        try:
            relative = (
                entry.path.resolve().relative_to(resolved_root).as_posix()
            )
        except ValueError:
            continue
        text = payload.decode("utf-8")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
        summary_sha256 = hashlib.sha256(payload).hexdigest()
        meta = {
            "source": _relative_to_cwd(entry.path),
            "title": parse_title(text, fallback=entry.run_id),
            "date": parse_date(text),
            "status": status,
            "doc_index": idx,
            "corpus_kind": "run_summaries",
            "authority": "auto_generated_run_summary_advisory",
            "document_kind": "run_summary",
            "run_id": entry.run_id,
            "run_family": entry.run_family,
            "run_version": int(entry.run_version),
            "summary_sha256": summary_sha256,
        }
        meta = {k: ("" if v is None else v) for k, v in meta.items()}
        docs.append(Document(page_content=text, metadata=meta))
    return docs, digest.hexdigest(), len(docs)


def load_document_snapshot(
    root: Path,
    *,
    corpus: CorpusSpec | None = None,
) -> tuple[list[Document], str, int]:
    """Read documents once and return the digest of those exact source bytes."""
    root = Path(root)
    corpus = corpus or CorpusSpec.experience(root)
    if corpus.kind == "run_summaries":
        return load_run_summary_documents(root)
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
