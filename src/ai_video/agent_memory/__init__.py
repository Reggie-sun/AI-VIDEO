"""Scoped local RAG over experience records and Superpowers plans/specs.

This module is a developer / Codex authoring tool, not a Production runtime.
It performs semantic retrieval over a small Markdown corpus of prior failure
and recovery notes and returns source + score + excerpt for Codex to read.

The retrieved records are advisory evidence only and never override
current code, tests, or runtime truth.

Auto-generated ``runs/<run_id>/SUMMARY.md`` files are picked up into a
separate derived index via the ``run_summaries`` corpus kind; they never
piggyback on the main experience/superpowers index.
"""

from ai_video.agent_memory.config import (
    DEFAULT_COLLECTION,
    DEFAULT_CORPUS_ROOT,
    DEFAULT_INDEX_PATH,
    DEFAULT_RUNS_INDEX_PATH,
    DEFAULT_RUNS_ROOT,
    DEFAULT_SCOPE,
    DEFAULT_SUPERPOWERS_ROOT,
    DEFAULT_TOP_K,
    RUN_SUMMARIES_COLLECTION,
)
from ai_video.agent_memory.corpus import CorpusSpec
from ai_video.agent_memory.embeddings import (
    DeterministicFakeEmbeddings,
    LocalOnnxMiniLMEmbeddings,
    build_embedding,
)
from ai_video.agent_memory.index import (
    IndexMismatchError,
    build_index,
    build_scoped_index,
    index_exists,
    load_index,
    read_index_manifest,
)
from ai_video.agent_memory.retrieval import Hit, format_text, search

__all__ = [
    # config
    "DEFAULT_CORPUS_ROOT",
    "DEFAULT_SUPERPOWERS_ROOT",
    "DEFAULT_RUNS_ROOT",
    "DEFAULT_INDEX_PATH",
    "DEFAULT_RUNS_INDEX_PATH",
    "DEFAULT_SCOPE",
    "DEFAULT_TOP_K",
    "DEFAULT_COLLECTION",
    "RUN_SUMMARIES_COLLECTION",
    "CorpusSpec",
    # embeddings
    "LocalOnnxMiniLMEmbeddings",
    "DeterministicFakeEmbeddings",
    "build_embedding",
    # index
    "build_index",
    "build_scoped_index",
    "load_index",
    "index_exists",
    "read_index_manifest",
    "IndexMismatchError",
    # retrieval
    "Hit",
    "search",
    "format_text",
]
