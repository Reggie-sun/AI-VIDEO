"""Agent Experience Memory: simple, local, read-only RAG over docs/record_for_agent/.

This module is a developer / Codex authoring tool, not a Production runtime.
It performs semantic retrieval over a small Markdown corpus of prior failure
and recovery notes and returns source + score + excerpt for Codex to read.

The retrieved records are advisory evidence only and never override
current code, tests, or runtime truth.
"""

from ai_video.agent_memory.config import (
    DEFAULT_COLLECTION,
    DEFAULT_CORPUS_ROOT,
    DEFAULT_INDEX_PATH,
    DEFAULT_TOP_K,
)
from ai_video.agent_memory.embeddings import (
    DeterministicFakeEmbeddings,
    LocalOnnxMiniLMEmbeddings,
    build_embedding,
)
from ai_video.agent_memory.index import build_index, index_exists, load_index
from ai_video.agent_memory.retrieval import Hit, format_text, search

__all__ = [
    # config
    "DEFAULT_CORPUS_ROOT",
    "DEFAULT_INDEX_PATH",
    "DEFAULT_TOP_K",
    "DEFAULT_COLLECTION",
    # embeddings
    "LocalOnnxMiniLMEmbeddings",
    "DeterministicFakeEmbeddings",
    "build_embedding",
    # index
    "build_index",
    "load_index",
    "index_exists",
    # retrieval
    "Hit",
    "search",
    "format_text",
]
