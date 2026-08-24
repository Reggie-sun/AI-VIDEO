"""Default paths and settings for Agent Experience Memory."""

from __future__ import annotations

# Named markdown corpora. Experience remains the backward-compatible default;
# Superpowers plans/specs are opt-in because they have a different authority.
DEFAULT_CORPUS_ROOT: str = "docs/record_for_agent"
DEFAULT_SUPERPOWERS_ROOT: str = "docs/superpowers"
# Auto-generated runs/<run_id>/SUMMARY.md files live alongside the Legacy
# runtime. They are indexed into a *separate* derived collection so they
# never piggyback on the experience corpus or change the main index.
DEFAULT_RUNS_ROOT: str = "runs"
DEFAULT_SCOPE: str = "experience"
VALID_SCOPES: tuple[str, ...] = ("experience", "superpowers", "all")

# Default local vector index directory. Treated as a derived artifact;
# never committed to Git (see .gitignore).
DEFAULT_INDEX_PATH: str = ".agent/memory/index"
# Separate derived index for auto-generated run summaries. It is rebuilt
# on demand by the main search when the corpus digest changes; no CLI
# ``build`` invocation is required for it to surface hits.
DEFAULT_RUNS_INDEX_PATH: str = ".agent/memory/run-summaries"

# Chroma collection name. Stable across rebuilds.
DEFAULT_COLLECTION: str = "agent_memory_experience"
SUPERPOWERS_COLLECTION: str = "agent_memory_superpowers"
RUN_SUMMARIES_COLLECTION: str = "agent_memory_run_summaries"

# Agent-facing Top-N. ``DEFAULT_TOP_K`` remains the public CLI compatibility
# name for the existing ``--top-k`` option.
DEFAULT_TOP_N: int = 8
DEFAULT_TOP_K: int = DEFAULT_TOP_N

# Inclusive relevance gate applied to the final merged retrieval candidates.
MINIMUM_RELEVANCE_SCORE: float = 0.7

# Hybrid retrieval keeps the existing dense index and adds a local lexical
# lane over the same indexed chunks. Reciprocal-rank fusion only determines
# ordering; the relevance gate above remains the Agent-facing admission rule.
HYBRID_CANDIDATE_TOP_K: int = 30
HYBRID_RRF_K: int = 60

# Dense-only admission is calibrated against a language-matched nonsense
# query over the same collection. A candidate must clear both the null
# baseline and, when Top-2 exists, the real query's Top-1 separation before
# its cosine score can satisfy the public relevance gate. These values are
# calibrated against the checked-in project corpus and pinned local E5 model.
DENSE_NULL_QUERY_ASCII: str = "zzzxqv_nonexistent_74291"
DENSE_NULL_QUERY_CJK: str = "无相关项目知识_68243"
DENSE_MIN_NULL_EXCESS: float = 0.005
DENSE_MIN_TOP1_MARGIN: float = 0.003
LEXICAL_MIN_QUERY_COVERAGE: float = 0.3

# Default embedding backend. Choices:
#   "local" -> LocalOnnxMiniLMEmbeddings (offline, requires the local model dir).
#   "fake"  -> DeterministicFakeEmbeddings (deterministic, no model needed).
DEFAULT_EMBEDDING: str = "local"

# Pinned multilingual E5 model identity. Model bytes are an explicit local
# prerequisite; the runtime never downloads them or falls back to a network.
DEFAULT_MODEL_ID: str = "intfloat/multilingual-e5-small"
DEFAULT_MODEL_REVISION: str = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
DEFAULT_MODEL_DIR: str = (
    "~/.cache/ai-video/agent-memory/"
    "intfloat-multilingual-e5-small-614241f622f5"
)

# Default ONNX filename relative to the pinned Hugging Face model directory.
DEFAULT_ONNX_FILE: str = "onnx/model_qint8_avx512_vnni.onnx"
DEFAULT_ONNX_SHA256: str = (
    "dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88"
)
DEFAULT_EMBED_BATCH_SIZE: int = 8

# Embedding vector size. multilingual-e5-small produces 384-dim vectors.
EMBEDDING_DIM: int = 384
