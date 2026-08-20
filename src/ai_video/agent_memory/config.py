"""Default paths and settings for Agent Experience Memory."""

from __future__ import annotations

# Default markdown corpus root. The demo reads *.md recursively from here.
DEFAULT_CORPUS_ROOT: str = "docs/record_for_agent"

# Default local vector index directory. Treated as a derived artifact;
# never committed to Git (see .gitignore).
DEFAULT_INDEX_PATH: str = ".agent/memory/index"

# Chroma collection name. Stable across rebuilds.
DEFAULT_COLLECTION: str = "agent_memory"

# Default top-K for retrieval. Configurable via CLI flag.
DEFAULT_TOP_K: int = 5

# Default embedding backend. Choices:
#   "local" -> LocalOnnxMiniLMEmbeddings (offline, requires the local model dir).
#   "fake"  -> DeterministicFakeEmbeddings (deterministic, no model needed).
DEFAULT_EMBEDDING: str = "local"

# Default local embedding model directory. This is the path where the model
# is cached on this machine. If you need to relocate the model, override via
# the AGENT_MEMORY_MODEL_DIR environment variable.
DEFAULT_MODEL_DIR: str = (
    "/home/reggie/.vscode/extensions/"
    "continue.continue-2.0.0-linux-x64/models/all-MiniLM-L6-v2"
)

# Default ONNX filename relative to the model directory.  The Continue VS
# Code extension ships it inside the ``onnx/`` subfolder.
DEFAULT_ONNX_FILE: str = "onnx/model_quantized.onnx"

# Embedding vector size. all-MiniLM-L6-v2 produces 384-dim vectors.
EMBEDDING_DIM: int = 384
