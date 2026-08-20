#!/usr/bin/env python3
"""CLI entry: build / search Agent Experience Memory.

This is a developer / Codex authoring tool, not a Production runtime.
Retrieved records are advisory evidence only and never override
current code, tests, or runtime truth.

Usage:
    python -m scripts.agent_memory build
    python -m scripts.agent_memory search "5min rough cut continuity"
    python -m scripts.agent_memory search "..." --top-k 8 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Make the ``src`` layout importable when the consumer invokes this CLI
# without setting ``PYTHONPATH=src``.  Codex, Claude, and humans all run
# the same one-liner ``python -m scripts.agent_memory ...`` regardless of
# their working directory, so the entry script must self-bootstrap.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_SRC_DIR = _REPO_ROOT / "src"
# Repo root is added so ``scripts`` is discoverable from any cwd when the
# consumer runs ``python -m scripts.agent_memory ...``.
for _path in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


from ai_video.agent_memory.config import (
    DEFAULT_CORPUS_ROOT,
    DEFAULT_EMBEDDING,
    DEFAULT_EMBED_BATCH_SIZE,
    DEFAULT_INDEX_PATH,
    DEFAULT_SCOPE,
    DEFAULT_SUPERPOWERS_ROOT,
    DEFAULT_TOP_K,
    VALID_SCOPES,
)
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.index import IndexMismatchError, build_scoped_index
from ai_video.agent_memory.retrieval import format_text, search


def _resolve(path: str) -> Path:
    """Resolve ``path`` to an absolute path.

    Relative inputs are anchored to the repository root (not the
    consumer's cwd), so the CLI is portable across worktrees, sandboxes,
    and CI shells.
    """
    p = Path(path)
    if not p.is_absolute():
        p = _REPO_ROOT / p
    return p.resolve()


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def _resolve_corpora(args: argparse.Namespace) -> tuple[CorpusSpec, ...]:
    corpora: list[CorpusSpec] = []
    if args.scope in {"experience", "all"}:
        corpora.append(CorpusSpec.experience(_resolve(args.corpus)))
    if args.scope in {"superpowers", "all"}:
        corpora.append(CorpusSpec.superpowers(_resolve(args.superpowers_corpus)))
    return tuple(corpora)


def cmd_build(args: argparse.Namespace) -> int:
    idx = _resolve(args.index)
    corpora = _resolve_corpora(args)
    for corpus in corpora:
        if not corpus.root.is_dir():
            print(f"corpus not found: {corpus.root}", file=sys.stderr)
            return 2
    try:
        embedding = build_embedding(backend=args.embedding)
        n = build_scoped_index(
            corpora=corpora,
            index_path=idx,
            embedding=embedding,
            batch_size=args.batch_size,
        )
    except (FileNotFoundError, IndexMismatchError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    roots = ", ".join(f"{item.kind}={item.root}" for item in corpora)
    print(f"Indexed {n} chunks from {roots} into {idx}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    idx = _resolve(args.index)
    corpora = _resolve_corpora(args)
    try:
        embedding = build_embedding(backend=args.embedding)
        hits = search(
            args.query,
            top_k=args.top_k,
            corpora=corpora,
            index_path=idx,
            embedding=embedding,
            scope=args.scope,
        )
    except (FileNotFoundError, IndexMismatchError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.as_json:
        print(
            json.dumps(
                [h.to_dict() for h in hits], ensure_ascii=False, indent=2
            )
        )
    else:
        print(format_text(hits))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent_memory",
        description=(
            "Agent project knowledge: scoped local RAG over experience records "
            "and optional docs/superpowers/. Advisory evidence only; never "
            "overrides current code, tests, or runtime truth."
        ),
    )
    parser.add_argument(
        "--corpus",
        default=DEFAULT_CORPUS_ROOT,
        help="Path to the markdown corpus root (default: %(default)s).",
    )
    parser.add_argument(
        "--superpowers-corpus",
        default=DEFAULT_SUPERPOWERS_ROOT,
        help="Path to the Superpowers plans/specs corpus (default: %(default)s).",
    )
    parser.add_argument(
        "--scope",
        choices=VALID_SCOPES,
        default=DEFAULT_SCOPE,
        help="Corpus scope to build/search (default: %(default)s).",
    )
    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX_PATH,
        help="Path to the local index directory (default: %(default)s).",
    )
    parser.add_argument(
        "--embedding",
        choices=("local", "fake"),
        default=DEFAULT_EMBEDDING,
        help=(
            "Embedding backend (default: %(default)s). "
            "'fake' is deterministic and intended for tests."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=_positive_int,
        default=DEFAULT_EMBED_BATCH_SIZE,
        help="Index embedding/add batch size (default: %(default)s).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "build",
        help="Wipe and rebuild the local index from the corpus.",
    )
    p_search = sub.add_parser("search", help="Search the local index.")
    p_search.add_argument("query", help="Natural-language query.")
    p_search.add_argument(
        "--top-k",
        type=_positive_int,
        default=DEFAULT_TOP_K,
        dest="top_k",
        help="Number of hits to return (default: %(default)s).",
    )
    p_search.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON instead of formatted text.",
    )

    args = parser.parse_args(argv)
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "search":
        return cmd_search(args)
    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
