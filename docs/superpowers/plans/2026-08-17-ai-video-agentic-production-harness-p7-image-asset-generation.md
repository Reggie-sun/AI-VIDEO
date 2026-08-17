# AI-VIDEO Agentic Production Harness P7 Image Asset Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Use superpowers:using-git-worktrees before Task 0 because P6 and P7 are concurrent write lanes.

**Goal:** 在已验收 P2/P2A/P5 contract 上增加 local-only、provider-neutral、durable 的 image asset generation path，让 Codex 能以 exact Character/Scene/reference inputs 生成并注册 image assets，原子切换目标 Shot、Asset Registry 和 P5 graph，同时证明复用、精确失效、crash recovery 与 exact replay。

**Architecture:** 新 `src/ai_video/production/image.py` 独占纯 image request/preview/authorization/result/provenance contract、PNG measured validation、candidate scope validation 与 `ImageAssetProvider` protocol；它不写文件、不调用 Provider、不改 Manifest。`ProductionStateCommitter` 继续是 request/submit-intent/result/receipt、image bytes、project/registry/graph candidate promotion、Manifest activation 和 explicit recovery 的唯一 writer。P7 不修改 `dependency.py`：生成结果通过既有 `AssetRecord(source_kind=generated)` visual seam 进入 P5，目标 Shot 的 exact asset binding 与 candidate project/registry/graph 在一次 final Manifest replace 中切换。

**Tech Stack:** Python 3.11+、Pydantic v2 strict/frozen models、stdlib canonical JSON/SHA-256/PNG IHDR parser、既有 P2A no-follow/fsync/promote-without-overwrite/atomic Manifest replace primitives、既有 P5 graph builder/resolver、pytest deterministic PNG fixtures 与 fake provider。无新 runtime dependency、无 CLI、无 ComfyUI/HyperFrames executable、无 remote/paid Provider、无 network、无 secret、无 quota。

**Spec:** `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`

## Global Constraints

- 本文件只授权未来按 task 执行 P7；它本身不授权 runtime implementation、merge、push、release、真实 image generation、remote egress、P8/P9 或 dependency installation。
- P7 implementation 从 exact accepted P5 base `52eca580dc93ad756f5c5e266e730b4017d48ce1` 建立独立 branch/worktree；不得从当前含 P6 commits/dirty work 的 `main` 直接开发。
- 本计划开始 inspection 时 `main` HEAD 是 `2859110`，随后 P6 writer 在本计划隔离 worktree 中工作期间把 `main` 推进到 `29d5bef`，同时 shared P6 files 仍有未提交修改；`origin/main` 保持 `52eca58`。这证明 P6 是 in-progress 而非 accepted base。P7 不得 stage、commit、rewrite 或覆盖当前 P6 文件，Task 5 必须重新记录未来的 exact clean/reviewed P6 HEAD。
- P7 parallel-safe lane 只拥有新 `production/image.py`、P7 独立 tests，以及只读复用既有 P5 public resolver。所有 shared core edits 必须等 P6 contract freeze 后执行 Task 5。
- 因 `errors.py` 也是 shared core，Tasks 1-4 的 pure lane 暂用既有 typed errors：image bytes/provenance invalid 为 `ASSET_REGISTRY_INVALID`，request/candidate scope invalid 为 `PRODUCTION_STATE_INVALID`。Task 6 在 P6 freeze 后引入专用 `IMAGE_*` codes并同步更新这些断言。
- `ProductionStateCommitter` 仍是唯一 v2 writer/recovery owner；P2 reader、Registry reader、`image.py` 和 `dependency.py` 不得写 state。
- P7 不修改 `src/ai_video/production/dependency.py`，不增加 provider/request nodes，不增加第二 lifecycle owner，不实现 ad-hoc stale propagation。
- P7 不宣称 Character/Scene/reference bytes 变化会自动触发 image regeneration。Codex 必须显式提交新的 exact request；P7 只保证新 output 激活后由既有 P5 graph 精确传播下游失效。自动 upstream-reference regeneration 需要单独批准 graph evolution。
- Asset Registry 继续 immutable、append-only、content-addressed；旧 image record 不覆盖、不删除。新 image 使用新 `asset_id` 与 content-addressed path。
- P7 只接受 local-only injected provider execution。任何 remote/paid image adapter 必须有独立 plan、current API/license/pricing review、Budget Guard、Cloud Egress、secret redaction 和 crash-safe submit gate。
- P7 只接受 PNG output；JPEG/WebP 继续可作为 P2 imported assets，但不进入本 slice 的 generated-output contract。这样无需新增 Pillow runtime dependency。
- P7 不增加 renderer、Composition、timeline、QA/repair、final acceptance、video Provider、frontend、API server 或新 public CLI。
- P6 absent/present 两种 2.5 state 都必须合法：2.3 可独立进入 P7-only 2.5；2.4 可进入 P6+P7 2.5；2.5 上后续 `bootstrap_review_policy()` 不得丢失 P7 evidence。
- 默认 CI 只使用 deterministic fake provider 与 committed synthetic PNG bytes；submit/network/ComfyUI/renderer call count 必须为 0。

---

## Problem Boundary

P7 的 bounded production path 是：

```text
Manifest-selected P2 Project/Registry + P5 graph
+ exact Character/Scene artifacts and registered reference images
+ Codex-authored ImageGenerationRequest(target Shot role, prompt, seed, dimensions)
        |
        v
ProductionStateCommitter.begin_image_generation()
R+1 durable request + preview + local authorization
        |
        v
ProductionStateCommitter.record_image_submit_intent()
R+2 durable intent + one-use DurableImageSubmitPermit
        |
        v
injected ImageAssetProvider.generate()
local-only; returns one PNG result; cannot write project state
        |
        v
image.py measured PNG/hash validation + immutable provenance receipt
        |
        v
exact target Shot revision + append-only Registry candidate
+ existing P5 graph rebuild/resolution (resolver unchanged)
        |
        v
ProductionStateCommitter.activate_image_asset()
one final Manifest replace selects project + registry + graph + lifecycle
        |
        +--> P6 state present: affected reviews/final acceptance become stale
        +--> exact replay: provider/materializer/write call counts all 0
```

### Single Owner

- Problem owner: `src/ai_video/production/image.py` for pure image contract and candidate validation.
- Durable owner: `src/ai_video/production/state_commit.py::ProductionStateCommitter` for every write, permit, activation and recovery.
- Dependency owner: existing `src/ai_video/production/dependency.py::{build_production_dependency_graph,resolve_dependency_state,select_rebuild_nodes}`; P7 only calls these public functions.
- Temporal/render owner: unchanged `ResolvedTimeline` / selected HyperFrames path; P7 does not author or activate render state.
- Creative decision owner: Codex plus exact `ImageGenerationRequest`; provider output cannot silently change target Shot, role, prompt, references, strategy or license.

### Old Path to Replace

P5 tests currently prove a future seam by changing an `AssetRecord` to `source_kind=generated` with a synthetic tool identity. That compatibility fixture remains valid for Manifest 2.0-2.4 readers. P7 execution must not treat an arbitrary generated `AssetRecord` as proof of generation: a P7-active output requires exact durable request, submit intent, result/provenance receipt, measured PNG, append-only Registry record and Manifest 2.5 succeeded attempt.

### Unchanged Contracts

- Legacy `validate | run | resume`, Manifest v1 and flat `runs/<run_id>/` remain byte/behavior compatible.
- P2 load remains read-only, no-network, no implicit recovery and no latest-file scan.
- P5 graph remains immutable and contains no request/provider/lifecycle state.
- Existing active render may remain selected after image activation, but its P5 render dependency state must become stale/blocked as computed by the existing resolver; P7 never marks render fresh.
- P6 Review/Repair semantics remain owned by P6. P7 only invokes a P6-owned helper to stale exact review/final state when graph/render identity changes.

## Design Decision

Three approaches were considered:

1. **Selected: provider-neutral local-only contract + injected fake/default executor.** It preserves Agent-first/tool-first architecture, gives durable request/result/provenance and complete no-network acceptance, and avoids choosing an unapproved image vendor or model.
2. **Rejected for this slice: concrete ComfyUI image workflow adapter.** The repository has no approved still-image template/model/binding, and using Legacy Comfy transport would add workflow/model ownership plus in-flight job reconciliation beyond the P7 core.
3. **Rejected for this slice: remote OpenAI/other image API adapter.** It would require a provider choice, current API/license/pricing evidence, remote egress and budget authorization not granted by this request.

The selected path is useful without a packaged vendor: Codex or another approved local tool can implement `ImageAssetProvider`; the repository enforces durable inputs, exact permit binding, measured output and activation. Default acceptance uses an injected deterministic fake. A concrete live adapter is a separate approved slice.

## Parallel Execution Contract

| Lane | May Own While P6 Runs | Must Not Touch While P6 Runs |
| --- | --- | --- |
| P6 | `production/review.py`、MCP review/repair files、P6 tests；shared core until freeze | P7 new image module/tests |
| P7 parallel-safe | `production/image.py`、`tests/test_production_image.py`、early `tests/test_production_image_e2e.py` | `models.py`、`paths.py`、`project.py`、`state_commit.py`、`__init__.py`、`errors.py`、factory/docs |
| P7 post-freeze integration | P7 additions to shared core after rebasing onto accepted P6 | P6 semantic redesign、`dependency.py`、MCP review tools |

Task 5 is a hard merge gate. Tasks 0-4 may proceed in the P7 worktree while P6 runs. Tasks 6-13 may start only after the P6 shared contract is committed, reviewed and the P7 branch is rebased onto that exact commit.

## Canonical Interfaces

`src/ai_video/production/image.py` owns these exact public names:

```python
class ImageProviderParameters(StrictModel):
    seed: int
    width: int
    height: int
    output_format: Literal["png"]
    generation_revision: int

class ImageReferenceBinding(StrictModel):
    role: Literal["character", "scene", "style"]
    creative_artifact_id: str
    creative_revision: int
    creative_content_hash: str
    asset_id: str
    asset_sha256: str

class ImageGenerationRequest(StrictModel):
    request_id: str
    attempt_id: str
    provider_kind: str
    model_id: str
    target_shot_id: str
    target_asset_role: str
    output_asset_id: str
    prompt_text: str
    negative_prompt_text: str
    parameters: ImageProviderParameters
    references: tuple[ImageReferenceBinding, ...]
    base_project: ProjectSnapshotPointer
    base_registry: RegistrySnapshotPointer
    base_dependency_graph: DependencyGraphSnapshotPointer
    request_fingerprint: str

class ImageGenerationPreview(StrictModel):
    request_fingerprint: str
    local_only: Literal[True]
    remote: Literal[False]
    output_count: Literal[1]
    output_mime_type: Literal["image/png"]
    reference_asset_ids: tuple[str, ...]
    reference_total_bytes: int
    preview_fingerprint: str

class ImageGenerationAuthorization(StrictModel):
    request_fingerprint: str
    preview_fingerprint: str
    provider_enabled: Literal[True]
    local_only: Literal[True]
    usage_license: str
    policy_receipt_id: str
    authorization_fingerprint: str

class ImageLocalResourceEvidence(StrictModel):
    elapsed_milliseconds: int
    device_kind: Literal["cpu", "gpu", "unknown"]
    measured_peak_memory_bytes: int | None

class ImageProviderResult(StrictModel):
    request_id: str
    request_fingerprint: str
    image_bytes: bytes
    image_sha256: str
    content_type: Literal["image/png"]
    provider_request_id: str | None
    adapter: ToolIdentity
    resource_evidence: ImageLocalResourceEvidence
    preview_fingerprint: str
    authorization_fingerprint: str
    terminal_status: Literal["succeeded"]
    result_fingerprint: str

class ImageAssetProvider(Protocol):
    def generate(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        permit: "DurableImageSubmitPermit",
    ) -> ImageProviderResult: ...
```

`image.py` uses a `TYPE_CHECKING` import of `state_commit.py::DurableImageSubmitPermit`, matching the existing voice permit pattern and avoiding a runtime cycle. The underlying `_DurableImageSubmitPermit` has no public constructor or serializer; only `ProductionStateCommitter.record_image_submit_intent()` may mint it, and package root does not export it. Provider consumption is atomic and one-use.

### Identity Rules

- `request_fingerprint` hashes provider/model, target Shot/role, exact prompt UTF-8 hashes, parameters, exact references and base project/registry/graph identities; it excludes `attempt_id`.
- `request_id == request_fingerprint`.
- `output_asset_id == "image-" + request_fingerprint`.
- Same desired request after success is exact replay and performs zero material action.
- A deliberate retry after terminal failure requires `generation_revision + 1`; same-desired failure never auto-retries.
- Output path is `assets/files/<image_sha256>.png`.
- Receipt path is `state/images/receipts/<receipt_content_hash>.json`; `AssetRecord.creation_receipt_id` equals that content hash.
- Registry `input_fingerprint` equals `request_fingerprint`; `input_artifact_ids` contain target Shot artifact ID plus exact referenced creative/asset IDs in canonical order.

### Durable Paths

```text
state/images/requests/<request_fingerprint>.json
state/images/previews/<preview_fingerprint>.json
state/images/authorizations/<authorization_fingerprint>.json
state/images/submit-intents/<request_fingerprint>.json
state/images/results/<result_fingerprint>.json
state/images/receipts/<receipt_content_hash>.json
assets/files/<image_sha256>.png
```

All paths are project-relative canonical files under existing containment/no-follow rules. Complete unselected files are preserved/reportable orphans; partial owned temp files may be cleaned only by explicit recovery.

## Manifest 2.5 Composition

Manifest 2.5 composes P6 and P7 without making them runtime prerequisites of each other:

- 2.0-2.4 load/serialize unchanged.
- 2.3 may enter P7-only 2.5 with no P6 fields.
- 2.4 may enter P6+P7 2.5 and must preserve every P6 pointer/state exactly.
- A P7-only 2.5 may later run P6 `bootstrap_review_policy()` in place; bootstrap adds P6 state without deleting or rewriting P7 attempts/evidence.
- If any P6 review/repair/final fields are present in 2.5, the full P6 invariants still apply.
- `image_generation` attempts are legal only in 2.5 and use exact phases:

```text
request -> submit_intent -> provider_call -> materialize
-> validate -> candidate -> activate
```

- `succeeded` requires `activate`; `interrupted` is allowed only before submit or in deterministic local materialization/candidate phases; uncertainty at/after submit intent is `outcome_unknown` and never remints a permit.
- Candidate phase requires exact candidate project/registry/graph pointers, dependency-state hash and one image asset ID.

## Atomic Activation and P5 Seam

P7 does not mutate an existing record. Candidate preparation must:

1. Append exactly one generated PNG `AssetRecord` to the existing Registry; every existing record remains equal and ordered.
2. Create exactly one new immutable target Shot revision whose selected `required_asset_roles` entry replaces the old asset ID with `output_asset_id`; all other Shot fields and all other creative artifacts remain equal.
3. Create the next project snapshot pointing to that one new Shot revision and candidate Registry.
4. Build the candidate graph with the existing P5 builder and resolve it against active states.
5. Require the affected set to equal the explicitly changed target Shot visual projection, the replaced/new visual asset path and exact downstream composition/timeline/source/render closure; unrelated Shot/audio/voice/caption nodes remain fresh. This validates output activation, not automatic upstream-reference regeneration.
6. Promote image/receipt/project/registry/graph snapshots, reopen and verify them, then switch all active pointers and lifecycle in one final Manifest replace.
7. If P6 state exists, call its exact identity-change helper so reviews/final acceptance bound to the prior graph/render become stale; do not duplicate P6 adjudication.

## Migration and Rollback

### Migration

- No Asset Registry schema bump: existing 2.0/2.1 `AssetRecord` fields already carry image dimensions, tool, source kind, input fingerprint, creation receipt, license, egress and cost identity.
- Manifest schema advances to 2.5 only on the first durable P7 lifecycle write.
- 2.3 -> 2.5 and 2.4 -> 2.5 are explicit committer transitions. Reader load never upgrades.
- No Legacy migration and no automatic discovery/import of files.

### Operational Rollback

1. Disable `begin_image_generation()` / `generate_image_asset()` entrypoints.
2. Keep 2.5 reader, audit and explicit recovery enabled; never downgrade to 2.4/2.3.
3. Preserve selected image bytes, receipts, Registry records, project revisions and graph snapshots.
4. P6 operations continue on 2.5 when their own policy/state invariants are satisfied.
5. P2-P5 projects and Legacy runtime continue unchanged.
6. No fallback to remote provider, Legacy video pipeline or arbitrary filesystem import.

## File Map

| File | Responsibility | Parallel Ownership |
| --- | --- | --- |
| `src/ai_video/production/image.py` | Pure P7 models, sealing, PNG validation, provider protocol, candidate-scope validation | P7-only; safe before P6 freeze |
| `tests/test_production_image.py` | Pure contract/validation/provider fake tests | P7-only; safe before P6 freeze |
| `tests/test_production_image_e2e.py` | Reuse, lifecycle, exact invalidation, replay proof | P7-only file; state portions after freeze |
| `src/ai_video/production/models.py` | Manifest 2.5 attempt summary/phase fields only | Shared; after Task 5 |
| `src/ai_video/production/paths.py` | Canonical image evidence/output paths | Shared; after Task 5 |
| `src/ai_video/production/project.py` | Read-only exact reopen of selected P7 evidence | Shared; after Task 5 |
| `src/ai_video/production/state_commit.py` | Sole P7 writer/orchestrator/permit/activation/recovery | Shared; after Task 5 |
| `src/ai_video/production/__init__.py` | Reviewed safe public exports | Shared; after Task 5 |
| `src/ai_video/errors.py` | Typed P7 error codes | Shared; after Task 5 |
| `tests/production_project_factory.py` | P7 fixture factory additions | Shared; after Task 5 |
| `src/ai_video/production/dependency.py` | Existing P5 graph/resolver | Read-only; never modify in P7 |

---

### Task 0: Create and Prove the Parallel P7 Worktree

**Files:** no repository file changes.

**Interfaces:**
- Consumes: accepted P5 commit `52eca580dc93ad756f5c5e266e730b4017d48ce1`.
- Produces: isolated branch `codex/p7-image-assets-20260817` and exact `P7_IMPLEMENTATION_BASE` record.

- [ ] **Step 1: Inspect live Git and agents**

Run:

```bash
git status --short --branch
git log --oneline --decorate -12
git rev-parse 52eca580dc93ad756f5c5e266e730b4017d48ce1
git merge-base --is-ancestor 0d663566c4db4542922e38d770608e3e02d53745 52eca580dc93ad756f5c5e266e730b4017d48ce1
```

Expected: the last command exits 0; current P6 dirty files are recorded but untouched.

- [ ] **Step 2: Use `superpowers:using-git-worktrees` to create the P7 lane**

Create the branch/worktree from the exact base, not current `main`. Use the external sibling worktree root so the current repository does not gain an untracked `.worktrees/` directory:

```bash
mkdir -p /home/reggie/vscode_folder/.worktrees
git worktree add /home/reggie/vscode_folder/.worktrees/AI-VIDEO-p7-image-assets-20260817 -b codex/p7-image-assets-20260817 52eca580dc93ad756f5c5e266e730b4017d48ce1
```

Expected: worktree HEAD is exactly `52eca580dc93ad756f5c5e266e730b4017d48ce1`; P6 commits and dirty bytes are absent.

- [ ] **Step 3: Record the base and baseline tests**

Run in the P7 worktree:

```bash
export P7_IMPLEMENTATION_BASE=52eca580dc93ad756f5c5e266e730b4017d48ce1
python -m pytest tests/test_production_models.py tests/test_production_project.py tests/test_production_dependency.py tests/test_production_selective_rebuild.py tests/test_production_state_commit.py tests/test_production_state_recovery.py -q
```

Expected: baseline passes; no network, provider or renderer executable is called.

### Task 1: Define Pure Image Request, Authorization and Result Contracts

**Files:**
- Create: `src/ai_video/production/image.py`
- Create: `tests/test_production_image.py`

**Interfaces:**
- Consumes: P2 pointer/asset/tool models and `canonical_sha256()`.
- Produces: `ImageProviderParameters`, `ImageReferenceBinding`, `ImageGenerationRequest`, `ImageGenerationPreview`, `ImageGenerationAuthorization`, `ImageLocalResourceEvidence`, `ImageProviderResult`, `ImageAssetProvider`.

Define test-local helpers in this task: `make_image_request()`, `make_preview_payload()`, `make_authorization()`, `make_image_result()` and exact byte constants `PNG_2X1_RGBA` / `PNG_WITH_TRUNCATED_IHDR`. Helpers must call the public constructors rather than bypassing validation with raw `model_construct()`.

- [ ] **Step 1: Write RED sealing and variant tests**

Add tests with exact names:

```python
def test_image_request_binds_prompt_target_references_and_base_pointers():
    request = make_image_request(target_shot_id="shot-1", generation_revision=1)
    assert request.request_id == request.request_fingerprint
    assert request.output_asset_id == f"image-{request.request_fingerprint}"
    assert tuple(item.role for item in request.references) == ("character", "scene")

def test_image_request_rejects_changed_prompt_under_old_fingerprint():
    request = make_image_request(target_shot_id="shot-1", generation_revision=1)
    payload = request.model_dump(mode="json")
    payload["prompt_text"] = "different prompt"
    with pytest.raises(ValidationError, match="request_fingerprint"):
        ImageGenerationRequest.model_validate(payload)

def test_image_contract_rejects_remote_preview_and_non_png_output():
    with pytest.raises(ValidationError):
        ImageGenerationPreview.model_validate(make_preview_payload(remote=True))
    with pytest.raises(ValidationError):
        ImageProviderParameters(seed=7, width=512, height=512, output_format="jpeg", generation_revision=1)
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_image.py -q`

Expected: collection/import fails because `ai_video.production.image` does not exist.

- [ ] **Step 3: Implement exact strict/frozen models and fingerprint constructors**

Implement `create()` constructors that NFC-normalize neither silently nor permissively: non-NFC prompt input is rejected. Hash exact UTF-8 prompt/negative prompt, canonical reference tuples and exact base pointers. Validate one character reference and one scene reference at minimum, unique `(role, asset_id)` pairs, positive dimensions, `generation_revision >= 1`, and `local_only=True / remote=False`.

Provider protocol signature must be exactly the one in `Canonical Interfaces`; do not add filesystem paths or Manifest callbacks to the provider.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_production_image.py -q`

Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit parallel-safe contract**

```bash
git add src/ai_video/production/image.py tests/test_production_image.py
git commit -m "feat: define p7 image generation contracts"
```

### Task 2: Add Measured PNG and Provenance Validation

**Files:**
- Modify: `src/ai_video/production/image.py`
- Modify: `tests/test_production_image.py`

**Interfaces:**
- Consumes: `ImageProviderResult`, authorization and exact request.
- Produces: `MeasuredPng`, `ImageProvenanceReceipt`, `validate_image_result()` and `image_receipt_semantic_sha256()`.

- [ ] **Step 1: Write RED PNG/result tests**

```python
def test_validate_image_result_uses_measured_png_dimensions_and_hash():
    request = make_image_request(width=2, height=1)
    result = make_image_result(request, png_bytes=PNG_2X1_RGBA)
    measured, receipt = validate_image_result(request, make_authorization(request), result)
    assert (measured.width, measured.height) == (2, 1)
    assert measured.sha256 == hashlib.sha256(PNG_2X1_RGBA).hexdigest()
    assert receipt.request_fingerprint == request.request_fingerprint

@pytest.mark.parametrize("payload", [b"", b"not-png", PNG_WITH_TRUNCATED_IHDR])
def test_validate_image_result_rejects_invalid_png(payload):
    request = make_image_request()
    with pytest.raises(AiVideoError) as error:
        validate_image_result(request, make_authorization(request), make_image_result(request, png_bytes=payload))
    assert error.value.code is ErrorCode.ASSET_REGISTRY_INVALID
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_image.py -q`

Expected: FAIL because measured/result helpers are absent.

- [ ] **Step 3: Implement a bounded stdlib PNG parser**

Validate exact 8-byte PNG signature, first chunk length/type (`IHDR`, 13 bytes), positive big-endian width/height, allowed color type/bit-depth combinations, complete IHDR bytes, result hash, request/preview/authorization fingerprints and requested dimensions. Do not decode pixels and do not add Pillow.

`ImageProvenanceReceipt` must bind request, adapter, sanitized provider request ID, output SHA/size/MIME/dimensions, usage license, policy receipt, exact reference identities, `ImageLocalResourceEvidence` and local/no-egress status. Local monetary `cost_receipt_id` remains `None`; the receipt must not invent a currency cost. Its content hash is deterministic and becomes the creation receipt ID.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_production_image.py -q`

Expected: all Task 1-2 tests pass.

- [ ] **Step 5: Commit measured validation**

```bash
git add src/ai_video/production/image.py tests/test_production_image.py
git commit -m "feat: validate p7 image provenance"
```

### Task 3: Define Exact Candidate Scope Without Writing State

**Files:**
- Modify: `src/ai_video/production/image.py`
- Modify: `tests/test_production_image.py`

**Interfaces:**
- Consumes: loaded base project, exact request/result/receipt, caller-prepared next project/registry/graph and P5 resolution.
- Produces: `validate_image_activation_candidate()` and `ImageActivationCandidate` capability.

Define the `p7_candidate` fixture and its three pure mutation helpers (`replace_unrelated_shot_intent`, `replace_existing_record`, `append_extra_record`) in `tests/test_production_image.py`; each helper returns a full immutable candidate mapping and never writes files.

- [ ] **Step 1: Write RED scope tests**

```python
def test_candidate_appends_one_image_and_changes_only_target_shot_role(p7_candidate):
    checked = validate_image_activation_candidate(**p7_candidate)
    assert checked.image_asset_id == p7_candidate["request"].output_asset_id
    assert checked.changed_shot_ids == ("shot-1",)

def test_candidate_rejects_mutated_character_or_unrelated_shot(p7_candidate):
    tampered = replace_unrelated_shot_intent(p7_candidate)
    with pytest.raises(AiVideoError) as error:
        validate_image_activation_candidate(**tampered)
    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID

def test_candidate_rejects_registry_overwrite_or_extra_asset(p7_candidate):
    for tampered in (replace_existing_record(p7_candidate), append_extra_record(p7_candidate)):
        with pytest.raises(AiVideoError):
            validate_image_activation_candidate(**tampered)
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_image.py -q`

Expected: FAIL because candidate validation is absent.

- [ ] **Step 3: Implement pure scope validation**

Require old Registry prefix equality; exactly one appended IMAGE/GENERATED/PNG record; canonical output path/hash/dimensions/tool/request fingerprint/receipt/license; exactly one target Shot artifact revision change; only the target role asset tuple changes; project refs and candidate Registry pointer match; graph equals the existing builder output; P5 resolution contains no unrelated nodes.

Return a frozen `ImageActivationCandidate` carrying exact prepared artifacts and expected pointers. The capability must have no public constructor; it is returned only by validation and consumed by `ProductionStateCommitter` after Task 8.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_production_image.py tests/test_production_dependency.py tests/test_production_selective_rebuild.py -q`

Expected: pass; `git diff -- src/ai_video/production/dependency.py` is empty.

- [ ] **Step 5: Commit candidate validator**

```bash
git add src/ai_video/production/image.py tests/test_production_image.py
git commit -m "feat: validate p7 image activation scope"
```

### Task 4: Prove Stable Character/Scene Reuse Against the Existing P5 Seam

**Files:**
- Create or modify: `tests/test_production_image_e2e.py`
- Modify only if fixture helpers are local to this file: `tests/test_production_image.py`
- Read only: `src/ai_video/production/dependency.py`

**Interfaces:**
- Consumes: pure P7 request/candidate contracts and current P5 public builder/resolver.
- Produces: deterministic two-Shot stable-reference reuse and explicit-request invalidation proof before state integration.

Define a test-local frozen `P7ReuseFixture` plus `explicitly_replace_shot_1_request()`, `generated_asset_ids()` and `unrelated_voice_caption_nodes_remain_fresh()` in `tests/test_production_image_e2e.py`. The explicit replacement helper derives the next asset ID from the new request fingerprint; it never uses a hard-coded asset ID.

- [ ] **Step 1: Write the two-Shot stable-reference reuse proof**

```python
def test_image_requests_reuse_stable_character_scene_references(p7_reuse_fixture):
    shot_1, shot_2 = p7_reuse_fixture.requests
    assert shot_1.references == shot_2.references
    assert shot_1.target_shot_id != shot_2.target_shot_id
    assert shot_1.output_asset_id != shot_2.output_asset_id

def test_explicit_new_shot_1_prompt_changes_only_shot_1_output(p7_reuse_fixture):
    candidate = explicitly_replace_shot_1_request(p7_reuse_fixture)
    assert generated_asset_ids(candidate) == {candidate.new_request.output_asset_id}
    assert unrelated_voice_caption_nodes_remain_fresh(candidate)
```

The test must not mutate shared references or claim automatic regeneration. Both requests bind the same exact Character/Scene reference identities, while prompts and output asset IDs remain per-Shot.

- [ ] **Step 2: Run the matrix**

Run: `python -m pytest tests/test_production_image.py tests/test_production_image_e2e.py tests/test_production_dependency.py tests/test_production_selective_rebuild.py -q`

Expected: pass with no provider call, no write and no `dependency.py` diff.

- [ ] **Step 3: Prove scope exclusions**

```python
def test_p7_pure_lane_has_no_renderer_review_video_or_remote_provider():
    import ai_video.production.image as image_mod
    exported = set(image_mod.__all__)
    assert "ImageAssetProvider" in exported
    assert not {"VideoProvider", "RemoteImageProvider", "render_with_hyperframes"} & exported
```

- [ ] **Step 4: Commit parallel-safe reuse proof**

```bash
git add tests/test_production_image.py tests/test_production_image_e2e.py
git commit -m "test: prove p7 character scene reuse scope"
```

### Task 5: P6 Contract Freeze and Rebase Gate

**Files:** no edits until all checks pass.

**Interfaces:**
- Consumes: reviewed/accepted P6 commit with Manifest 2.4 and no dirty shared files.
- Produces: exact `P6_ACCEPTED_BASE` and rebased P7 branch ready for shared integration.

- [ ] **Step 1: Verify P6 is a committed, reviewed base**

Run in the P6/main tree:

```bash
git status --short --branch
git log --oneline --decorate -12
git diff --check
python -m pytest tests/test_production_models.py tests/test_production_project.py tests/test_production_state_commit.py tests/test_production_state_recovery.py tests/test_production_review.py tests/test_production_repair.py -q
```

Expected: shared files are clean, P6 tests pass, independent review verdict is accept or accept-with-resolved-concerns. If shared P6 files remain dirty, stop here; Tasks 6-13 are blocked, not waived.

- [ ] **Step 2: Record exact P6 base and ownership handoff**

```bash
export P6_ACCEPTED_BASE="$(git rev-parse HEAD)"
git show -s --format='%H %s' "$P6_ACCEPTED_BASE"
```

Record exact file ownership handoff for `models.py`, `paths.py`, `project.py`, `state_commit.py`, `__init__.py`, `errors.py`, factory and docs.

- [ ] **Step 3: Rebase the isolated P7 branch**

Run in the P7 worktree:

```bash
git status --short --branch
git rebase "$P6_ACCEPTED_BASE"
python -m pytest tests/test_production_image.py tests/test_production_image_e2e.py tests/test_production_models.py tests/test_production_state_commit.py -q
```

Expected: P7-only commits replay cleanly; P6 files remain semantically unchanged; focused tests pass.

### Task 6: Compose Manifest 2.5 Image Lifecycle with P6 2.4

**Files:**
- Modify: `src/ai_video/production/models.py`
- Modify: `src/ai_video/production/paths.py`
- Modify: `src/ai_video/errors.py`
- Modify: `tests/test_production_models.py`
- Modify: `tests/test_production_image.py`

**Interfaces:**
- Consumes: accepted P6 2.4 models and pure P7 identities.
- Produces: `ImageRequestReceipt`, image attempt phases, Manifest 2.5 composition and canonical path helpers.

- [ ] **Step 1: Write RED 2.5 compatibility tests**

```python
def test_manifest_25_accepts_p7_only_state_from_23():
    manifest = make_manifest_25(active_qa_policy=None, image_attempts=(make_image_attempt(),))
    assert manifest.schema_version == "2.5"
    assert manifest.active_qa_policy is None

def test_manifest_25_preserves_complete_p6_state():
    p6 = make_manifest_24_with_review_state()
    p7 = add_image_attempt_as_25(p6)
    assert p7.active_qa_policy == p6.active_qa_policy
    assert p7.review_states == p6.review_states
    assert p7.active_final_acceptance == p6.active_final_acceptance

def test_manifest_24_rejects_explicit_image_fields():
    payload = make_manifest_24_with_review_state().model_dump(mode="json")
    payload["attempts"] = [make_image_attempt_payload()]
    with pytest.raises(ValidationError, match="2.4.*image"):
        ProductionManifest.model_validate(payload)
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_models.py tests/test_production_image.py -q`

Expected: FAIL because schema 2.5/image attempt fields do not exist.

- [ ] **Step 3: Implement 2.5 conditional invariants**

Add `ErrorCode.IMAGE_REQUEST_INVALID`, `IMAGE_ASSET_INVALID`, `IMAGE_PROVIDER_FAILED`, `IMAGE_PROVIDER_OUTCOME_UNKNOWN`, then update the Task 1-4 pure tests/helpers so request/candidate failures use `IMAGE_REQUEST_INVALID` and PNG/result failures use `IMAGE_ASSET_INVALID`. Add image request summary, phase, provider request ID, candidate image IDs and exact graph candidate requirements to `StateCommitAttempt`; serialize image fields only for `operation="image_generation"`.

For 2.5, run P6 invariants when any P6 field exists; do not require P6 state for P7-only manifests. Reject P7 fields in 2.0-2.4. Extend P6-aware operations/version checks to preserve 2.5 without weakening 2.4.

- [ ] **Step 4: Add canonical path helpers and run tests**

Run:

```bash
python -m pytest tests/test_production_models.py tests/test_production_image.py tests/test_production_review.py tests/test_production_repair.py -q
```

Expected: pass; all old schema round-trips remain unchanged.

- [ ] **Step 5: Commit schema composition**

```bash
git add src/ai_video/production/models.py src/ai_video/production/paths.py src/ai_video/errors.py tests/test_production_models.py tests/test_production_image.py
git commit -m "feat: compose p7 image lifecycle state"
```

### Task 7: Make the Reader Reopen Exact P7 Provenance Without Writing

**Files:**
- Modify: `src/ai_video/production/project.py`
- Modify: `tests/test_production_project.py`
- Modify: `tests/production_project_factory.py`

**Interfaces:**
- Consumes: Manifest-selected 2.5 attempts, active project/registry and canonical image receipt paths.
- Produces: read-only exact verification of active P7 generated images.

- [ ] **Step 1: Write RED reader tests**

```python
def test_loader_reopens_selected_p7_image_receipt_and_exact_png(p7_committed_project):
    loaded = load_production_project(p7_committed_project)
    image = next(asset for asset in loaded.registry.assets if asset.asset_id.startswith("image-"))
    assert image.source_kind is AssetSourceKind.GENERATED

@pytest.mark.parametrize("mutation", ["receipt_hash", "png_bytes", "request_id", "decoy_latest"])
def test_loader_rejects_tampered_or_decoy_p7_evidence(p7_committed_project, mutation):
    mutate_p7_evidence(p7_committed_project, mutation)
    with pytest.raises(AiVideoError):
        load_production_project(p7_committed_project)
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_project.py -q`

Expected: FAIL because 2.5/P7 evidence reopen is absent.

- [ ] **Step 3: Implement exact, read-only reopen**

For succeeded P7 attempts selected by active project/registry, derive receipt path only from `creation_receipt_id`, reopen with existing containment/no-follow helpers, verify semantic/file hashes, request/output/Registry/Shot role identities and measured PNG. Do not scan `state/images`, choose newest, create directories, recover or rewrite.

- [ ] **Step 4: Run reader and isolation tests**

```bash
python -m pytest tests/test_production_project.py tests/test_production_registry.py tests/test_production_validation.py tests/test_config.py tests/test_cli.py -q
```

Expected: pass; input mtimes unchanged and no network.

- [ ] **Step 5: Commit reader support**

```bash
git add src/ai_video/production/project.py tests/test_production_project.py tests/production_project_factory.py
git commit -m "feat: verify p7 image provenance on load"
```

### Task 8: Persist Request and Submit Intent Before Provider Execution

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/test_production_image_e2e.py`

**Interfaces:**
- Consumes: exact request/preview/authorization and Manifest 2.3/2.4/2.5.
- Produces: `begin_image_generation()`, `record_image_submit_intent()` and one-use `DurableImageSubmitPermit` type alias over private `_DurableImageSubmitPermit`.

- [ ] **Step 1: Write RED durable-intent tests**

```python
def test_image_submit_requires_durable_request_and_exact_local_authorization(p7_committer):
    request, preview, authorization = make_image_call_bundle(p7_committer)
    with pytest.raises(AiVideoError):
        p7_committer.record_image_submit_intent(request, preview, authorization)
    p7_committer.begin_image_generation(request, preview, authorization)
    permit = p7_committer.record_image_submit_intent(request, preview, authorization)
    assert permit._validate_image_generation_permit(request_fingerprint=request.request_fingerprint)

def test_stale_or_remote_image_authorization_has_zero_submit(p7_committer, counting_provider):
    request, preview, authorization = make_image_call_bundle(p7_committer)
    p7_committer.begin_image_generation(request, preview, authorization)
    with pytest.raises(AiVideoError):
        p7_committer.generate_image_asset(request, make_remote_preview(preview), authorization, counting_provider)
    assert counting_provider.calls == 0
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_state_commit.py tests/test_production_image_e2e.py -q`

Expected: FAIL because P7 committer methods/permit are absent.

- [ ] **Step 3: Implement R+1/R+2 under the existing lock**

R+1 writes, file-fsyncs, promotes, directory-fsyncs and reopens exact request/preview/authorization artifacts, then records a running 2.5 attempt. R+2 writes/reopens submit intent and only after durable Manifest replace mints a process-local permit bound to attempt/request/auth/base project/registry/graph. The provider consumes it atomically at the execution boundary.

Reject another running/outcome-unknown attempt, stale pointers, nonlocal preview, mismatched license/policy, reused attempt ID and second permit mint.

- [ ] **Step 4: Run state tests**

Run: `python -m pytest tests/test_production_state_commit.py tests/test_production_image.py tests/test_production_image_e2e.py -q`

Expected: pass through submit-intent phase; no provider is called except injected counting fake in explicit tests.

- [ ] **Step 5: Commit durable intent**

```bash
git add src/ai_video/production/state_commit.py tests/test_production_state_commit.py tests/test_production_image_e2e.py
git commit -m "feat: persist p7 image submit intent"
```

### Task 9: Materialize and Atomically Activate Image, Project, Registry and Graph

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `src/ai_video/production/__init__.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/test_production_image_e2e.py`

**Interfaces:**
- Consumes: one-use permit, fake provider result and validated `ImageActivationCandidate`.
- Produces: `generate_image_asset()` and `activate_image_asset()` safe public path.

- [ ] **Step 1: Write RED activation tests**

```python
def test_image_activation_switches_exact_project_registry_graph_once(p7_runtime):
    before = p7_runtime.read_manifest()
    result = p7_runtime.generate_shot_image("shot-1")
    after = p7_runtime.read_manifest()
    assert result.asset_id.startswith("image-")
    assert after.active_project != before.active_project
    assert after.active_registry != before.active_registry
    assert after.active_dependency_graph != before.active_dependency_graph
    assert succeeded_image_attempt(after).candidate_image_asset_ids == (result.asset_id,)

def test_image_activation_does_not_mark_render_fresh(p7_runtime):
    p7_runtime.generate_shot_image("shot-1")
    states = {item.node_id: item for item in p7_runtime.read_manifest().dependency_states}
    assert states["render:main"].lifecycle in {DependencyLifecycle.STALE, DependencyLifecycle.BLOCKED}
```

- [ ] **Step 2: Run RED tests**

Run: `python -m pytest tests/test_production_state_commit.py tests/test_production_image_e2e.py -q`

Expected: FAIL because result activation is absent.

- [ ] **Step 3: Implement result persistence and candidate activation**

Persist provider result metadata immediately; materialize PNG to owned temp; rehash/reopen; write immutable provenance receipt; invoke the injected deterministic candidate preparer; call `validate_image_activation_candidate()`; promote exact image/project/registry/graph files; reopen every candidate; perform one final Manifest replace selecting all pointers and succeeded lifecycle.

If P6 fields are present, call the accepted P6 identity-drift helper with old/new graph/render identities so exact affected reviews/final acceptance stale. Do not import or duplicate P6 private adjudication.

- [ ] **Step 4: Export only safe surfaces and run tests**

Package root may export reviewed request/result/protocol models and `ProductionStateCommitter.generate_image_asset`; it must not export permit constructors, raw snapshot writer or a concrete remote provider.

Run:

```bash
python -m pytest tests/test_production_state_commit.py tests/test_production_image.py tests/test_production_image_e2e.py tests/test_production_dependency.py tests/test_production_selective_rebuild.py tests/test_production_review.py -q
```

Expected: pass; `git diff -- src/ai_video/production/dependency.py` remains empty.

- [ ] **Step 5: Commit atomic activation**

```bash
git add src/ai_video/production/state_commit.py src/ai_video/production/__init__.py tests/test_production_state_commit.py tests/test_production_image_e2e.py
git commit -m "feat: activate p7 image assets atomically"
```

### Task 10: Add Crash Recovery, Unknown Outcome and Exact Replay

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_recovery.py`
- Modify: `tests/helpers/p2a_crash_worker.py`
- Modify: `tests/test_production_image_e2e.py`

**Interfaces:**
- Consumes: P2A/P6 explicit recovery machinery and P7 phase/evidence identities.
- Produces: fail-closed P7 crash classification and idempotent replay.

- [ ] **Step 1: Add crash matrix tests**

Cover exact checkpoints:

```text
request temp write/fsync/promotion/directory fsync/reopen
submit-intent Manifest replace before/after
provider boundary before/after permit consume
PNG temp write/fsync/promotion/directory fsync/reopen
receipt/project/registry/graph candidate promotion
candidate Manifest replace before/after
final active Manifest replace before/after/directory fsync/reopen
```

Core assertions:

```python
def test_image_unknown_outcome_never_remints_permit_or_resubmits(crashed_p7_project):
    report = recover_production_state(crashed_p7_project.root)
    assert report.manifest_revision_after >= report.manifest_revision_before
    assert crashed_p7_project.provider.calls == 1
    with pytest.raises(AiVideoError) as error:
        crashed_p7_project.committer.generate_image_asset(*crashed_p7_project.same_request)
    assert error.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert crashed_p7_project.provider.calls == 1

def test_exact_image_replay_has_zero_provider_materializer_and_writes(p7_runtime):
    first = p7_runtime.generate_shot_image("shot-1")
    counters = p7_runtime.reset_counters()
    second = p7_runtime.generate_shot_image("shot-1")
    assert second == first
    assert counters.snapshot() == {"provider": 0, "materializer": 0, "manifest": 0}
```

- [ ] **Step 2: Run RED recovery tests**

Run: `python -m pytest tests/test_production_state_recovery.py tests/test_production_image_e2e.py -q`

Expected: new P7 cases fail before recovery support.

- [ ] **Step 3: Extend explicit recovery only**

Recovery must accept only exact old or exact new project/registry/graph tuple, never guess mixed activation, never reissue permit, never call provider, preserve complete orphan image/receipt/snapshots and clean only bounded non-succeeded owned temps. P7-only/P6+P7 2.5 fields must survive recovery unchanged except exact attempt status transition.

- [ ] **Step 4: Run recovery suites**

```bash
python -m pytest tests/test_production_state_recovery.py tests/test_production_state_commit.py tests/test_production_image_e2e.py tests/test_production_review.py tests/test_production_repair.py -q
```

Expected: pass with provider call counts fixed by each fixture.

- [ ] **Step 5: Commit recovery**

```bash
git add src/ai_video/production/state_commit.py tests/test_production_state_recovery.py tests/helpers/p2a_crash_worker.py tests/test_production_image_e2e.py
git commit -m "feat: recover p7 image generation state"
```

### Task 11: Prove the P7 Character/Scene Reuse Acceptance Path

**Files:**
- Modify: `tests/test_production_image_e2e.py`
- Modify: `tests/production_project_factory.py`

**Interfaces:**
- Consumes: complete P7 lifecycle and existing P5/P6 contracts.
- Produces: final deterministic P7 exit-gate evidence.

- [ ] **Step 1: Build one two-Shot fixture**

The fixture has one Character, one Scene, shared registered reference images, two `static_image` Shots, two exact P7 requests, no audio/provider/video/render executable. Fake provider returns two deterministic PNGs and records request bindings.

- [ ] **Step 2: Assert reuse and isolated prompt mutation**

```python
def test_two_shots_reuse_character_scene_but_keep_distinct_image_provenance(p7_reuse_runtime):
    first = p7_reuse_runtime.generate_all()
    assert first.provider_calls == 2
    assert first.requests[0].references == first.requests[1].references
    assert first.assets[0].creation_receipt_id != first.assets[1].creation_receipt_id
    second = p7_reuse_runtime.change_only_shot_1_prompt_and_generate()
    assert second.provider_calls == 1
    assert second.changed_asset_ids == (second.shot_1_asset_id,)
    assert second.shot_2_asset_id == first.shot_2_asset_id
```

- [ ] **Step 3: Assert explicit output replacement and unrelated-domain freshness**

```python
def test_explicit_shot_1_replacement_stales_only_exact_consumers(p7_reuse_runtime):
    result = p7_reuse_runtime.change_only_shot_1_prompt_and_generate()
    assert result.provider_calls == 1
    assert result.changed_shot_ids == ("shot-1",)
    assert result.unrelated_voice_caption_nodes_are_fresh
    assert result.video_provider_calls == 0
    assert result.renderer_calls == 0
```

- [ ] **Step 4: Run canonical P7 focused command**

```bash
python -m pytest \
  tests/test_production_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_validation.py \
  tests/test_production_project.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_review.py \
  tests/test_production_repair.py -q
```

Expected: all pass; no network, ComfyUI, HyperFrames, video Provider, remote image Provider, secret or quota.

- [ ] **Step 5: Commit acceptance proof**

```bash
git add tests/test_production_image_e2e.py tests/production_project_factory.py
git commit -m "test: prove p7 image reuse acceptance"
```

### Task 12: Document Only Verified P7 Runtime Truth

**Files:**
- Modify after runtime acceptance: `AGENTS.md`
- Modify after runtime acceptance: `README.md`
- Modify after runtime acceptance: `docs/agent-primary-contract-matrix.md`
- Modify after runtime acceptance: `docs/v0.2-runtime-baseline.md`
- Modify after runtime acceptance: `docs/v0.2-agentic-production-roadmap.md`

**Interfaces:**
- Consumes: verified P7 code/tests and live Git truth.
- Produces: current behavior docs; no proposed behavior presented as implemented.

- [ ] **Step 1: Capture live evidence**

```bash
git status --short --branch
git log --oneline --decorate -15
git rev-list --left-right --count origin/main...HEAD
```

- [ ] **Step 2: Update exact runtime boundaries**

Document provider-neutral local-only contract, no concrete/live provider, Character/Scene reuse, generated PNG provenance, Manifest 2.5 composition, single committer, existing P5 resolver reuse, exact replay/recovery and no renderer/video generation. State local merge/push/release truth from Git at that time; do not copy planned test counts.

- [ ] **Step 3: Check stale/planned language**

```bash
rg -n "P6|P7|Manifest 2.5|ImageAssetProvider|image generation|push|release|remote|Provider" \
  AGENTS.md README.md docs/agent-primary-contract-matrix.md docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md
```

- [ ] **Step 4: Commit docs separately**

```bash
git add AGENTS.md README.md docs/agent-primary-contract-matrix.md docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md
git commit -m "docs: record accepted p7 image runtime"
```

### Task 13: Final Verification, Independent Review and Handoff

**Files:** no new implementation files; review only.

**Interfaces:**
- Consumes: complete P7 branch after Task 12.
- Produces: verified diff, independent verdict and exact publish boundary.

- [ ] **Step 1: Run canonical focused and Legacy isolation suites**

Run Task 11 focused command, then:

```bash
python -m pytest tests/test_config.py tests/test_cli.py tests/test_pipeline.py tests/test_resume_e2e.py tests/test_manifest.py tests/test_comfy_client.py -q
python -m pytest -q
```

Expected: all suites pass from the known P7 worktree; no live external action.

- [ ] **Step 2: Run mechanical checks**

```bash
git diff --check "$P7_IMPLEMENTATION_BASE"...HEAD
git diff --name-status "$P7_IMPLEMENTATION_BASE"...HEAD
git log --oneline --decorate "$P7_IMPLEMENTATION_BASE"..HEAD
git diff "$P7_IMPLEMENTATION_BASE"...HEAD -- src/ai_video/production/dependency.py
```

Expected: final command is empty; every changed line maps to P7 or the explicit P6/P7 Manifest 2.5 integration.

- [ ] **Step 3: Dispatch an independent reviewer**

Reviewer must inspect exact request/permit binding, P6/P7 2.5 composition, Registry append-only behavior, target-only Shot mutation, P5 affected set, P6 review staleness, crash windows, replay counts, loader no-write behavior, exports and scope exclusions.

Verdict format: `accept | accept with concerns | reject`, blocking issues, non-blocking concerns, evidence and minimal follow-up. Parent verifies each blocking claim directly.

- [ ] **Step 4: Resolve findings and rerun affected suites**

Each fix gets its own targeted RED/GREEN test and precise commit. Rerun canonical focused, Legacy and full suites after the last fix.

- [ ] **Step 5: Report without publishing automatically**

Report branch, exact HEAD, `P6_ACCEPTED_BASE`, test results, review verdict, P7-only vs shared integration diff, remaining risks and local-vs-origin truth. Completion does not imply merge, push, release, live provider authorization or P8/P9 authorization.

---

## Canonical Focused Verification

```bash
python -m pytest \
  tests/test_production_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_validation.py \
  tests/test_production_project.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_review.py \
  tests/test_production_repair.py -q
```

## Acceptance Checklist

P7 runtime may be called implemented only when all are true:

1. P7 runs in its own branch/worktree and never overwrites P6 dirty/shared work.
2. Pure image contracts were developed before the shared integration gate; shared files changed only after accepted P6 freeze/rebase.
3. One exact request binds target Shot/role, prompt, seed/dimensions, Character/Scene/reference identities and base pointers.
4. R+1 request and R+2 submit intent are durable before provider execution; permit is one-use and non-serializable.
5. Default acceptance is local-only fake/no-network; remote/paid submit count is 0.
6. PNG bytes/hash/size/dimensions are measured locally and exact; provider claims cannot override measured facts.
7. Registry appends one new record and never mutates/deletes old records.
8. Exactly one target Shot role changes per request; provider cannot alter unrelated creative intent.
9. Project/Registry/graph/lifecycle switch atomically in one final Manifest replace.
10. `dependency.py` is unchanged; existing P5 resolver proves exact downstream invalidation and unrelated freshness.
11. P6 absent/present Manifest 2.5 variants work; P6 fields are preserved and P7-only 2.5 can bootstrap P6 policy in place.
12. P6 review/final state becomes stale only through the P6-owned exact identity helper when relevant state exists.
13. Exact replay performs zero provider/materializer/write calls; same-desired failure does not auto-retry.
14. Unknown outcome never remints a permit or blind resubmits; recovery is explicit and fail closed.
15. Two Shots reuse one stable Character/Scene reference set; an explicit new prompt request regenerates one target image. No automatic reference-driven regeneration is claimed.
16. No video Provider, renderer execution, CLI, frontend, new dependency, remote egress, secret or quota enters scope.
17. Focused, Legacy and full suites pass from a known worktree state; independent review has no unresolved blockers.
18. Docs describe only verified behavior and distinguish local merge, push and release.

## Remaining Risks Deliberately Outside P7

- No concrete ComfyUI, OpenAI or other remote image adapter is selected or shipped.
- No live image quality/identity evaluator is claimed; P6 semantic evidence rules remain unchanged.
- P7 outputs PNG only; generated JPEG/WebP support needs a separately justified measured decoder/dependency decision.
- Character/Scene/reference changes do not automatically schedule image regeneration in this slice. That behavior requires a separately approved P5 graph/input evolution because P7 is forbidden to modify the dependency resolver.
- Base AI Comic E2E still requires an independently accepted integration of P6 review/repair, P7 images, P4 voice/captions and P3 render.
- P8 generated-video Providers and P9 hardening remain separately gated.
