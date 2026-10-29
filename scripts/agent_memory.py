#!/usr/bin/env python3
"""CLI entry: build / search authority-separated Agent project knowledge.

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
import subprocess
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
    DEFAULT_DOCS_ROOT,
    DEFAULT_EMBEDDING,
    DEFAULT_EMBED_BATCH_SIZE,
    DEFAULT_INDEX_PATH,
    DEFAULT_SCOPE,
    DEFAULT_SUPERPOWERS_ROOT,
    DEFAULT_TOP_K,
    FOREGROUND_REFRESH_MAX_NEW_CHUNKS,
    VALID_SCOPES,
)
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.embeddings import build_embedding
from ai_video.agent_memory.index import EmbeddingBudget, IndexMismatchError
from ai_video.agent_memory.layout import (
    LegacyProjectIndexError,
    MissingProjectIndexError,
    PROJECT_CORPUS_KINDS,
    build_project_indexes,
    read_project_layout,
    shard_path,
)
from ai_video.agent_memory.maintenance import (
    RefreshRequest,
    enqueue_refresh,
    run_refresh_worker,
)
from ai_video.agent_memory.manifest import (
    LibraryVersionMismatchError,
    corpus_digest,
)
from ai_video.agent_memory.retrieval import format_text, retrieve_project


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
    if args.scope == "all":
        docs_root = _resolve(args.docs_root)
        corpora.extend(
            (
                CorpusSpec.current_docs(docs_root),
                CorpusSpec.research(docs_root / "research"),
                CorpusSpec.deferred(docs_root / "when_to_do"),
            )
        )
    return tuple(corpora)


def _resolve_all_corpora(args: argparse.Namespace) -> tuple[CorpusSpec, ...]:
    docs_root = _resolve(args.docs_root)
    return (
        CorpusSpec.experience(_resolve(args.corpus)),
        CorpusSpec.superpowers(_resolve(args.superpowers_corpus)),
        CorpusSpec.current_docs(docs_root),
        CorpusSpec.research(docs_root / "research"),
        CorpusSpec.deferred(docs_root / "when_to_do"),
    )


def _queue_root() -> Path:
    result = subprocess.run(
        ("git", "rev-parse", "--git-path", "agent-memory-refresh"),
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = _REPO_ROOT / path
    return path.resolve()


def _refresh_request(args: argparse.Namespace) -> RefreshRequest:
    corpora = _resolve_all_corpora(args)
    roots = {item.kind: str(item.root) for item in corpora}
    desired_sources: dict[str, str] = {}
    for corpus in corpora:
        digest, count = corpus_digest(corpus.root, corpus)
        desired_sources[corpus.kind] = f"sha256:{digest}:documents:{count}"
    return RefreshRequest(
        index_root=str(_resolve(args.index)),
        corpus_roots=roots,
        desired_sources=desired_sources,
        embedding_backend=args.embedding,
        batch_size=args.batch_size,
    )


def _enqueue(args: argparse.Namespace, kinds: tuple[str, ...]) -> None:
    result = enqueue_refresh(
        _refresh_request(args),
        kinds,
        queue_root=_queue_root(),
    )
    action = "started" if result.worker_started else "already running"
    print(
        f"Agent Memory refresh queued for {', '.join(result.kinds)}; worker {action}.",
        file=sys.stderr,
    )


def cmd_build(args: argparse.Namespace) -> int:
    idx = _resolve(args.index)
    corpora = _resolve_corpora(args)
    for corpus in corpora:
        if not corpus.root.is_dir():
            print(f"corpus not found: {corpus.root}", file=sys.stderr)
            return 2
    try:
        embedding = build_embedding(backend=args.embedding)
        counts = build_project_indexes(
            corpora=corpora,
            index_root=idx,
            embedding=embedding,
            batch_size=args.batch_size,
            reuse=not args.full,
        )
    except (FileNotFoundError, IndexMismatchError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    roots = ", ".join(f"{item.kind}={item.root}" for item in corpora)
    print(f"Indexed {sum(counts.values())} chunks from {roots} into {idx}")
    return 0


def _refresh_stale_in_foreground(
    args: argparse.Namespace,
    corpora: tuple[CorpusSpec, ...],
    stale_kinds: tuple[str, ...],
    embedding,
) -> tuple[str, ...]:
    """Incrementally refresh small stale shards; return kinds still stale.

    All shards share one bound on new chunk embeddings, and a shard that
    another builder holds is skipped instead of waited on. Anything left stale
    falls back to the detached queue while the validated last-good fragments
    are returned.
    """
    budget = EmbeddingBudget(FOREGROUND_REFRESH_MAX_NEW_CHUNKS)
    refreshed: list[str] = []
    remaining: list[str] = []
    for corpus in corpora:
        if corpus.kind not in stale_kinds:
            continue
        try:
            build_project_indexes(
                (corpus,),
                _resolve(args.index),
                embedding,
                batch_size=args.batch_size,
                embedding_budget=budget,
                wait=False,
            )
        except Exception as exc:
            print(
                f"Agent Memory {corpus.kind} shard not refreshed before search "
                f"({type(exc).__name__}: {exc}).",
                file=sys.stderr,
            )
            remaining.append(corpus.kind)
        else:
            refreshed.append(corpus.kind)
    if refreshed:
        print(
            f"Agent Memory refreshed {', '.join(refreshed)} incrementally before search.",
            file=sys.stderr,
        )
    return tuple(remaining)


def cmd_search(args: argparse.Namespace) -> int:
    idx = _resolve(args.index)
    corpora = _resolve_corpora(args)
    try:
        # Missing/legacy layout is cheap to classify and queue; do this before
        # loading the local embedding model so first-use migration returns fast.
        read_project_layout(idx)
        missing_kinds = [
            corpus.kind
            for corpus in corpora
            if not shard_path(idx, corpus.kind).exists()
        ]
        if missing_kinds:
            raise MissingProjectIndexError(
                "Missing Agent Memory shard(s): "
                f"{', '.join(missing_kinds)}",
                kinds=tuple(missing_kinds),
            )
        embedding = build_embedding(backend=args.embedding)

        def retrieve():
            return retrieve_project(
                args.query,
                top_k=args.top_k,
                corpora=corpora,
                index_root=idx,
                embedding=embedding,
                scope=args.scope,
                allow_stale=True,
            )

        result = retrieve()
        if result.stale_kinds:
            still_stale = _refresh_stale_in_foreground(
                args,
                corpora,
                result.stale_kinds,
                embedding,
            )
            if len(still_stale) < len(result.stale_kinds):
                result = retrieve()
    except (MissingProjectIndexError, LegacyProjectIndexError) as exc:
        kinds = (
            PROJECT_CORPUS_KINDS
            if isinstance(exc, LegacyProjectIndexError)
            else (
                exc.kinds
                if exc.kinds
                else tuple(item.kind for item in corpora)
            )
        )
        try:
            _enqueue(args, tuple(kinds))
        except Exception as queue_exc:
            print(f"{exc}; refresh could not be queued: {queue_exc}", file=sys.stderr)
            return 2
        print(f"{exc}; continue with current repository evidence.", file=sys.stderr)
        return 3
    except LibraryVersionMismatchError as exc:
        if not exc.kinds:
            print(str(exc), file=sys.stderr)
            return 2
        kinds = exc.kinds
        try:
            _enqueue(args, kinds)
        except Exception as queue_exc:
            print(f"{exc}; refresh could not be queued: {queue_exc}", file=sys.stderr)
            return 2
        print(
            "library-incompatible Agent Memory shard(s): "
            f"{', '.join(kinds)}; refresh queued; continue with current "
            "repository evidence.",
            file=sys.stderr,
        )
        return 3
    except (FileNotFoundError, IndexMismatchError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    hits = list(result.hits)
    if result.stale_kinds:
        try:
            _enqueue(args, result.stale_kinds)
        except Exception as exc:
            print(
                f"stale Agent Memory result; refresh queue failed: {exc}",
                file=sys.stderr,
            )
        else:
            print(
                "Returned tagged last-good fragments while stale shards refresh "
                "in the background.",
                file=sys.stderr,
            )
    if args.as_json:
        print(
            json.dumps(
                [h.to_dict() for h in hits], ensure_ascii=False, indent=2
            )
        )
    else:
        print(format_text(hits))
    return 0


def _corpus_from_refresh(kind: str, root: str) -> CorpusSpec:
    path = Path(root)
    factories = {
        "experience": CorpusSpec.experience,
        "superpowers": CorpusSpec.superpowers,
        "current_docs": CorpusSpec.current_docs,
        "research": CorpusSpec.research,
        "deferred": CorpusSpec.deferred,
    }
    try:
        return factories[kind](path)
    except KeyError as exc:
        raise ValueError(f"unknown queued corpus kind: {kind!r}") from exc


def cmd_refresh_worker(args: argparse.Namespace) -> int:
    def build(request: RefreshRequest, kinds: tuple[str, ...]) -> dict[str, int]:
        embedding = build_embedding(backend=request.embedding_backend)
        corpora = tuple(
            _corpus_from_refresh(kind, request.corpus_roots[kind])
            for kind in kinds
        )
        return build_project_indexes(
            corpora,
            Path(request.index_root),
            embedding,
            batch_size=request.batch_size,
        )

    return run_refresh_worker(Path(args.queue_dir), build)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent_memory",
        description=(
            "Agent project knowledge: scoped local RAG over experience records, "
            "current project docs, advisory research, deferred decisions, and "
            "Superpowers specs. Authority is preserved per hit."
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
        help=(
            "Path to the Superpowers corpus; plans/ and artifacts/ are not "
            "indexed (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--docs-root",
        default=DEFAULT_DOCS_ROOT,
        help=(
            "Path to docs/ for all-scope current, research, and deferred "
            "collections (default: %(default)s)."
        ),
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
    p_build = sub.add_parser(
        "build",
        help=(
            "Rebuild the selected shards, reusing stored vectors for unchanged "
            "chunks."
        ),
    )
    p_build.add_argument(
        "--full",
        action="store_true",
        help=(
            "Re-embed every chunk instead of reusing stored vectors; use after "
            "changing how embeddings are computed."
        ),
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
    p_worker = sub.add_parser("_refresh-worker", help=argparse.SUPPRESS)
    p_worker.add_argument("--queue-dir", required=True, help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "search":
        return cmd_search(args)
    if args.cmd == "_refresh-worker":
        return cmd_refresh_worker(args)
    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
