# TODOS

## ComfyUI Client

### Extract Asset Manager When Image Handling Grows

**What:** Extract asset resolution, upload caching, and content-hash reuse into an Asset Manager module when Comfy client image handling grows beyond simple upload/register behavior.

**Why:** Prevents the Comfy client from becoming a mixed HTTP, filesystem, cache, and validation module as reference-image workflows grow.

**Context:** The engineering review reduced MVP scope by folding image prep into `comfy_client.py`. The design doc now treats Asset Manager as a future extraction point. Revisit this when repeated image-cache, dedupe, hash, or cross-run reuse logic appears in the client.

**Effort:** M
**Priority:** P3
**Depends on:** Real usage showing repeated image-cache or dedupe logic in `comfy_client.py`.

### Add WebSocket Progress Listener

**What:** Add WebSocket progress and execution-error listener to the Comfy client after polling MVP works.

**Why:** Gives users live feedback during long local generations and catches execution errors earlier.

**Context:** Current design keeps WebSocket as future work and uses lifecycle polling for v1. Start in `comfy_client.py` after mocked polling tests and real ComfyUI smoke testing are stable. The listener should filter messages by `prompt_id`, surface current node/progress in the CLI, and preserve polling/history as the fallback source of truth.

**Effort:** M
**Priority:** P2
**Depends on:** Phase 2 single-shot ComfyUI execution and lifecycle polling.

## Run Artifacts

### Add Safe Old-Run Cleanup

**What:** Add an `ai-video clean-runs` command or retention policy after the MVP proves artifact layout.

**Why:** Prevents local video artifacts, failed attempts, normalized clips, and snapshots from filling disk over repeated experiments.

**Context:** The MVP keeps all run artifacts for debugging and tells users to delete old run directories manually. Revisit this after the run manifest and artifact layout are stable enough to delete or archive safely.

**Effort:** M
**Priority:** P3
**Depends on:** Stable run directory structure and artifact manifest format.

## Completed
