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

from ai_video.agent_memory.config import (
    DEFAULT_CORPUS_ROOT,
    DEFAULT_EMBEDDING,
    DEFAULT_INDEX_PATH,
    DEFAULT_TOP_K,
)
from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.index import build_index
from ai_video.agent_memory.retrieval import format_text, search


def _resolve(path: str) -> Path:
    return Path(path).resolve()


def cmd_build(args: argparse.Namespace) -> int:
    corpus = _resolve(args.corpus)
    idx = _resolve(args.index)
    if not corpus.is_dir():
        print(f"corpus not found: {corpus}", file=sys.stderr)
        return 2
    embedding = build_embedding(backend=args.embedding)
    n = build_index(
        corpus_root=corpus,
        index_path=idx,
        embedding=embedding,
    )
    print(f"Indexed {n} chunks from {corpus} into {idx}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    corpus = _resolve(args.corpus)
    idx = _resolve(args.index)
    embedding = build_embedding(backend=args.embedding)
    try:
        hits = search(
            args.query,
            top_k=args.top_k,
            corpus_root=corpus,
            index_path=idx,
            embedding=embedding,
        )
    except FileNotFoundError as exc:
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
            "Agent Experience Memory: simple local RAG over "
            "docs/record_for_agent/. Advisory evidence only; never "
            "overrides current code, tests, or runtime truth."
        ),
    )
    parser.add_argument(
        "--corpus",
        default=DEFAULT_CORPUS_ROOT,
        help="Path to the markdown corpus root (default: %(default)s).",
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
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "build",
        help="Wipe and rebuild the local index from the corpus.",
    )
    p_search = sub.add_parser("search", help="Search the local index.")
    p_search.add_argument("query", help="Natural-language query.")
    p_search.add_argument(
        "--top-k",
        type=int,
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
