# AI-VIDEO P7.1 Hybrid Local Image Production Implementation Plan

Execution status: Milestones 0-6 and the applicable offline verification/review portion of Milestone 9 are implemented on local `main`. Milestone 7 live smoke and Milestone 8 blind benchmark remain blocked on their separate explicit authorizations; no live or quality acceptance is claimed.

**Goal:** 在 accepted Base AI Comic E2E 之后，为 P7 增加 loopback-only ComfyUI local image adapter、Qwen/FLUX sealed execution profiles、truthful ChatGPT web human-import path 和 evidence-based quality gate，同时保留现有 durable lifecycle、single writer、P5/P6 ownership 与 Legacy behavior。

**Scope:** P7.1 local image execution、manual web-image import、deterministic fakes、compatibility/live smoke gate、blind benchmark 和 verified runtime-truth docs。

**Contract Surfaces:** `ImageAssetProvider`、`ImageGenerationRequest.model_id`、P7 R+1/R+2 evidence、`ProductionStateCommitter`、ComfyUI transport/workflow binding、import receipt、PNG/provenance、Project/Registry/Graph activation、replay/recovery。

**Invariants:** Manifest 2.5、Asset Registry schema、public CLI、P5 resolver ownership、P6 review ownership、Base AI Comic no-network CI 和 Legacy local ComfyUI semantics remain unchanged。No second writer, remote fallback, browser automation or API key。

**Current / Target Behavior:** Current P7 has only deterministic injected Provider acceptance. Target behavior adds explicit real local execution through one sealed adapter and truthful human imports; no lane is enabled by default。

**Compatibility:** Existing P7 fake requests/evidence/replay remain byte- and behavior-compatible. The current `/home/reggie/ComfyUI` checkout is inspected first and never updated implicitly. No schema migration is planned。

**Out of Scope:** P8/P9、video Provider、new public CLI、OpenAI Image API、unattended ChatGPT automation、remote ComfyUI、automatic reference regeneration、model quality claims before benchmark。

**Acceptance Criteria:** Spec section 14 plus fresh focused/full tests, Architecture Gate, one explicitly authorized local smoke session, blind benchmark gate and independent review with no blocker。

**Verification:** Exact commands are defined per milestone and in Final Verification。Default commands use `-p no:cacheprovider` and network-denial fixtures。

**Spec / ADR:** `docs/superpowers/specs/2026-08-18-ai-video-p7-1-hybrid-local-image-production.md`

## Authorization Boundary

This plan is an execution design only. It does **not** authorize:

- model or workflow downloads；
- dependency installation；
- modification/update/rebase of `/home/reggie/ComfyUI`；
- GPU generation or live ComfyUI requests；
- runtime implementation；
- merge、push、release or publish。

Runtime Task 0 may begin only after Base AI Comic E2E is accepted and the user grants a new P7.1 implementation authorization. Download and live-smoke milestones each require their own explicit authorization at execution time.

## File Map

The exact implementation file set must be revalidated at Task 0. The intended minimal surface is:

### New production contracts and adapter

- Create `src/ai_video/production/comfy_image.py` — sealed `LocalImageExecutionProfile`, image workflow binding/rendering/output collection, loopback validation and concrete `ComfyLocalImageProvider`。
- Create `src/ai_video/production/image_import.py` — pure `HumanImageImportReceipt`, PNG/source/approval validation and exact candidate-scope validation。
- Modify `src/ai_video/comfy_client.py` — only if required, add byte-returning artifact fetch or structured history helper while preserving all Legacy methods。
- Modify `src/ai_video/workflow_renderer.py` and optionally create `src/ai_video/workflow_binding.py` — extract/reuse generic JSON-path mutation only if RED tests prove direct reuse is unsafe; do not move video semantics into Production code。

### Existing P7 single-writer integration

- Modify `src/ai_video/production/_state_commit_image_intent.py` — conditionally persist/reopen exact local execution profile as R+1 evidence before permit minting。
- Modify `src/ai_video/production/_state_commit_image_activation.py` — only the minimal profile/result identity verification needed around existing Provider execution; retain replay-before-write and unknown-outcome behavior。
- Modify `src/ai_video/production/_image_project_reader.py` — reopen selected local profile and human import receipt by exact content hash, without scans/writes。
- Modify `src/ai_video/production/_state_commit_transaction.py` or the existing `commit_project_registry` owner — activate human imports through the existing transaction; do not add a new Manifest operation unless a separate schema gate is approved。
- Modify `src/ai_video/production/paths.py` — canonical content-addressed paths for execution profiles/import receipts only。
- Modify `src/ai_video/production/state_commit.py` — façade wiring only; no second implementation owner。
- Modify `src/ai_video/production/__init__.py` — export only reviewed safe profile/import models; never export permit constructors or raw writers。

### Planned profiles, workflows and bindings

- Create `workflows/profiles/p7_1_qwen_image_edit_2511.json`。
- Create `workflows/profiles/p7_1_flux2_klein_4b.json`。
- Create `workflows/templates/p7_1_qwen_image_edit_2511_api.json`。
- Create `workflows/bindings/p7_1_qwen_image_edit_2511_binding.yaml`。
- Create `workflows/templates/p7_1_flux2_klein_4b_api.json`。
- Create `workflows/bindings/p7_1_flux2_klein_4b_binding.yaml`。

These files are not created in this planning turn. The workflow files must be pinned derivatives of the applicable official templates shipped by `comfyui_workflow_templates`, not newly invented graphs. Their source package/version, source template path and SHA-256 are fixed after compatibility review; mutable upstream `main` URLs are evidence sources, not runtime inputs. Binding files own the approved local filename/parameter substitutions and must not overwrite the installed official templates。

### Planned tests and fixtures

- Create `tests/test_production_comfy_image.py`。
- Create `tests/test_production_image_import.py`。
- Create `tests/test_production_p7_1_local_image_e2e.py`。
- Create `tests/fixtures/p7_1/qwen_profile.json` and `tests/fixtures/p7_1/flux_profile.json` with fake digests only。
- Create `tests/fixtures/p7_1/qwen_workflow_api.json` and `tests/fixtures/p7_1/flux_workflow_api.json` using minimal synthetic nodes, not redistributed model files。
- Modify `tests/test_comfy_client.py`、`tests/test_workflow_loader.py`、`tests/test_workflow_renderer.py` only for reused boundary regressions。
- Modify `tests/test_production_state_commit.py`、`tests/test_production_state_recovery.py`、`tests/test_production_project.py` and `tests/production_project_factory.py` for profile/import/replay/recovery evidence。
- Create `scripts/check_p7_1_comfy_compatibility.py` as a read-only host preflight that inventories all Comfy model categories, performs header-only diffusion detection and compares official-template lineage/bindings without loading model tensors。
- Create `scripts/smoke_p7_1_local_image.py` only for an explicit live local smoke; it is not a public product CLI。
- Create `docs/benchmarks/p7-1-hybrid-image-inputs.json` and `docs/benchmarks/p7-1-hybrid-image-results.json` only after benchmark cases/results exist; generated benchmark images remain outside Git unless separately approved as small fixtures。

### Runtime-truth documentation after acceptance

- Modify `AGENTS.md`、`README.md`、`docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md` and `docs/v0.2-agentic-production-roadmap.md` only after verified runtime acceptance。

### Explicitly unchanged unless an independent gate is approved

- `src/ai_video/production/models.py` and Manifest schema。
- `src/ai_video/production/registry.py` and Asset Registry schema。
- `src/ai_video/production/dependency.py`。
- `src/ai_video/production/review.py` and `repair.py`。
- `src/ai_video/pipeline.py`、Legacy Manifest/layout and public CLI。
- `/home/reggie/ComfyUI` during repository implementation tasks。

## Major Milestones

### Milestone 0: Freeze the Accepted Base and Reconfirm Authorization

**Files:** Read only; no repository modifications。

**Owner / Dependencies:** Parent agent。Requires accepted Base AI Comic E2E and explicit P7.1 runtime implementation authorization。

**Contract:** Record exact Git base, worktree ownership, current runtime truth, local ComfyUI state and official source snapshot before any write。

**RED:** Treat any of these as a hard failure: Base E2E not accepted, P7 not integrated in the chosen base, dirty/conflicting writer, target file ownership overlap, or missing explicit authorization。

**Implementation Notes:**

1. Read current rules/spec/plan and inspect live agents。
2. Run:

```bash
git status --short --branch
git log --oneline --decorate -15
git rev-list --left-right --count origin/main...HEAD
git worktree list --porcelain
rg -n "Base AI Comic|P7|Manifest 2.5|ImageAssetProvider" \
  AGENTS.md docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md
git -C /home/reggie/ComfyUI status --short --branch
git -C /home/reggie/ComfyUI rev-parse HEAD
export P7_1_IMPLEMENTATION_BASE="$(git rev-parse HEAD)"
```

3. Verify Base E2E focused tests from the accepted base; do not borrow counts from another worktree。

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_production_image_e2e.py \
  tests/test_production_state_recovery.py -q
```

**Acceptance:** Exact accepted base and writer lane are recorded; `/home/reggie/ComfyUI` remains unchanged; no download/network generation occurs。

**Verification:** Commands above plus `git status --short` unchanged。

---

### Milestone 1: Define Sealed Profiles and a Deterministic Fake Adapter First

**Files:**

- Create `src/ai_video/production/comfy_image.py`
- Create `tests/test_production_comfy_image.py`
- Create fake profile/workflow fixtures under `tests/fixtures/p7_1/`

**Contract:** A strict/frozen `LocalImageExecutionProfile` binds lane, exact model components, license, ComfyUI commit, node inventory, workflow/binding digests, reference contract, generation parameters and profile hash. `ComfyLocalImageProvider` implements the existing `ImageAssetProvider` signature and has no state-writer callback。

**RED:** Add tests with exact behaviors before implementation:

- reject profile content-hash mismatch；
- reject mutable model revision such as `main`；
- reject missing component size/SHA-256/license source；
- reject `base`, 9B, API or third-party quantization under the FLUX distilled 4B lane；
- reject Qwen optional LoRA/precision not declared by the profile；
- reject non-loopback IPv4/IPv6/hostname, redirect and proxy routing before any HTTP call；
- require request `provider_kind="comfyui_local"` and `model_id` equal exact profile ID；
- deterministic fake returns one PNG, consumes one permit and records one call；
- fake/no-network test patches `socket.socket.connect` and `socket.create_connection` and asserts zero calls。

Run RED:

```bash
python -m pytest -p no:cacheprovider tests/test_production_comfy_image.py -q
```

Expected: import/contract failures because the adapter does not exist。

**Implementation Notes:** Implement pure models, canonical hash, loopback URL validation and a transport protocol injected into the adapter. The first GREEN transport is a fake; do not contact `ComfyClient` or filesystem model paths yet. `ImageGenerationRequest` schema remains unchanged; `model_id` is the canonical profile content-addressed ID。

**Acceptance:** All pure/fake tests pass; network count, filesystem state writes and real Provider calls are zero outside the injected fake call。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_image.py \
  tests/test_production_image.py -q
```

---

### Milestone 2: Reuse Workflow and Comfy Transport Boundaries Without Copying Legacy

**Files:**

- Modify `src/ai_video/comfy_client.py`
- Modify `src/ai_video/workflow_renderer.py` or create `src/ai_video/workflow_binding.py` only if required by RED
- Modify `src/ai_video/production/comfy_image.py`
- Modify `tests/test_comfy_client.py`、`tests/test_workflow_loader.py`、`tests/test_workflow_renderer.py`
- Modify `tests/test_production_comfy_image.py`

**Contract:** Use `load_workflow_template()` for API/UI JSON, a focused image binding for prompt/negative prompt/seed/width/height/reference image names/output prefix, existing `ComfyClient` upload/submit/poll/history/view operations, and a PNG-specific output selector. Do not call `PipelineRunner` or `collect_clip_artifact()`。

**RED:**

- API-format and UI-format workflow both load through `load_workflow_template()`；
- binding changes only declared JSON paths and rejects a missing/ambiguous path；
- exact reference upload order equals request order；
- exactly one configured `SaveImage` output is selected；
- multiple candidates, wrong output node, `.jpg`, missing history and malformed metadata fail closed；
- `httpx.MockTransport` proves upload → prompt → history/queue → view sequence and exact request count；
- Legacy clip workflow/render/client tests remain unchanged。

Run RED:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_image.py \
  tests/test_comfy_client.py \
  tests/test_workflow_loader.py \
  tests/test_workflow_renderer.py -q
```

**Implementation Notes:** Prefer a small `fetch_artifact_bytes()` addition to `ComfyClient` over writing a Project path. If generic JSON-path helpers must be extracted, preserve old signatures and prove Legacy output equality. The adapter may use an attempt-scoped temporary upload/download directory, but it cannot write `state/`, `assets/`, Project or Registry files。

**Acceptance:** One fake Comfy job produces exact PNG bytes and a real sanitized fake `prompt_id`; no transport implementation is duplicated。

**Verification:** Command above plus:

```bash
git diff -- src/ai_video/pipeline.py src/ai_video/manifest.py
```

Expected: empty。

---

### Milestone 3: Bind the Profile into Existing P7 Durable Evidence

**Files:**

- Modify `src/ai_video/production/_state_commit_image_intent.py`
- Modify `src/ai_video/production/_state_commit_image_activation.py` only if necessary
- Modify `src/ai_video/production/_image_project_reader.py`
- Modify `src/ai_video/production/paths.py`
- Modify `src/ai_video/production/state_commit.py`
- Modify `tests/test_production_state_commit.py`、`tests/test_production_project.py`、`tests/test_production_p7_1_local_image_e2e.py`

**Contract:** For `provider_kind="comfyui_local"`, exact profile bytes at `state/images/execution-profiles/{profile_content_hash}.json` are part of R+1 candidate evidence and are reopened before R+2 permit minting. Existing fake P7 request chronology and bytes remain compatible。

**RED:**

- profile absent/tampered/model-ID mismatch gives zero Provider/Comfy/Manifest-submit calls；
- R+1 durable evidence includes exact profile file and aggregate hash；
- R+2 cannot mint a permit after profile bytes change；
- selected success reader reopens request, profile, result, PNG and receipt by exact identities；
- exact replay after success gives counters `provider=0`, `comfy_prompt=0`, `materializer=0`, `manifest=0`；
- old fake P7 requests without local profiles still replay exactly；
- no new Manifest or Registry field appears。

Run RED:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_commit.py \
  tests/test_production_project.py \
  tests/test_production_p7_1_local_image_e2e.py -q
```

**Implementation Notes:** Extend the existing conditional evidence set, not `ImageGenerationRequest`, `ImageProvenanceReceipt`, `StateCommitAttempt` or Asset Registry schemas. The request binds the profile through `model_id`; the adapter instance validates the same profile. If exact reopen cannot be proven with this contract, stop and produce an independent schema proposal instead of overloading unrelated fields。

**Acceptance:** First generation performs exactly one Provider call and one Comfy prompt submission; exact replay performs zero. Final activation still uses one existing Project/Registry/Graph Manifest replace。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_image.py \
  tests/test_production_image_e2e.py \
  tests/test_production_p7_1_local_image_e2e.py \
  tests/test_production_state_commit.py \
  tests/test_production_project.py -q
git diff -- src/ai_video/production/dependency.py src/ai_video/production/models.py
```

Expected final diff command: empty。

---

### Milestone 4: Add Truthful Human ChatGPT Web Import

**Files:**

- Create `src/ai_video/production/image_import.py`
- Create `tests/test_production_image_import.py`
- Modify existing `commit_project_registry` transaction owner and façade only as required
- Modify `src/ai_video/production/_image_project_reader.py`
- Modify `src/ai_video/production/paths.py`
- Modify `tests/test_production_state_commit.py`、`tests/test_production_project.py`、`tests/test_production_selective_rebuild.py`

**Contract:** `HumanImageImportReceipt` records `chatgpt_images_2_web`, human declaration/approval, exact prompt/reference/output identities, and explicit absence of backend model/provider request/durable submit/browser automation. The AssetRecord is `IMPORTED`, not `GENERATED`。

**RED:**

- reject any receipt with invented backend model ID, provider request ID or submit evidence；
- reject missing human actor/approval/source note；
- reject non-PNG/tampered bytes/dimension mismatch；
- exact receipt hash becomes `creation_receipt_id`；
- import appends one Registry record and changes only the declared Character/Scene/Shot binding；
- P5 computes exact invalidation and no P7 auto-regeneration occurs；
- reader ignores decoy/latest receipt and reopens only the selected content hash；
- exact import replay performs zero writes。

Run RED:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_image_import.py \
  tests/test_production_state_commit.py \
  tests/test_production_project.py \
  tests/test_production_selective_rebuild.py -q
```

**Implementation Notes:** Reuse existing `commit_project_registry`/P5 transition where possible. A test helper may prepare the exact candidate, but only `ProductionStateCommitter` writes/promotes/activates it. Do not create `operation="chatgpt_generation"` or any Provider permit。

**Acceptance:** Manual PNG import has honest, content-addressed provenance and atomic activation without any network or browser call in repository code。

**Verification:** Command above plus no-network socket assertions and:

```bash
rg -n "provider_request_id|durable_submit|automated_browser|source_surface" \
  src/ai_video/production/image_import.py tests/test_production_image_import.py
```

---

### Milestone 5: Prove Unknown Outcome, Recovery and No-Network Defaults

**Files:**

- Modify `src/ai_video/production/_state_commit_image_recovery.py` only if profile evidence requires classification
- Modify `tests/test_production_state_recovery.py`
- Modify `tests/helpers/p2a_crash_worker.py`
- Modify `tests/test_production_p7_1_local_image_e2e.py`

**Contract:** The existing P7 crash windows remain authoritative. Comfy prompt submission is the external execution boundary; timeout/lost history after submit is outcome unknown. Recovery never invokes ComfyUI, Provider, browser or model load。

**RED:** Add crash cases around:

```text
profile temp write / promote / reopen
R+1 Manifest replace
R+2 submit-intent replace
before and after permit consume
before and after POST /prompt
history completed but PNG not fetched
PNG/result/receipt promotion
candidate Manifest replace
final active Manifest replace
```

Assertions:

- pre-submit deterministic failure can end without a Provider call；
- after-submit ambiguity is `IMAGE_PROVIDER_OUTCOME_UNKNOWN`；
- recovery call counts are `provider=0`, `comfy_prompt=0`, `browser=0`；
- no permit is reminted；
- exact old/new Project/Registry/Graph tuples are the only accepted states；
- complete unselected evidence is preserved/reported, bounded incomplete temp may be cleaned only by explicit recovery。

Run RED then GREEN:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_state_recovery.py \
  tests/test_production_p7_1_local_image_e2e.py \
  tests/test_production_image_e2e.py -q
```

**Acceptance:** All deterministic fake/default tests pass while socket access is forbidden and ComfyUI is not running。

**Verification:** Command above with the shared socket-denial fixture enabled explicitly in the new test module。

---

### Milestone 6: Pin Official Components and Pass Compatibility, Disk and VRAM Gates

**Files:**

- Create the two real profile JSON files and reviewed workflow/binding files listed in File Map
- Create `scripts/check_p7_1_comfy_compatibility.py`
- Create `scripts/smoke_p7_1_local_image.py`
- Create or modify `tests/test_production_comfy_image.py` for real-profile static validation

**Owner / Dependencies:** The six selected model components and the PyTorch `cu130` repair were separately authorized and completed on 2026-08-18. Their dated evidence must be reverified, not treated as implementation acceptance. Any additional download, optional LoRA, dependency change or ComfyUI update still requires new explicit authorization and cannot be inferred from runtime implementation authorization。

**Contract:** Every model component and workflow is immutable, licensed, digest-verified and compatible with exact local ComfyUI/node inventory before GPU submit。

**Dated preflight evidence, not runtime truth:** `/home/reggie/ComfyUI` remained at `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`; the dedicated environment reported `torch/torchvision/torchaudio` as `2.11.0+cu130` / `0.26.0+cu130` / `2.11.0+cu130`; `pip check`, CUDA visibility and a minimal CUDA tensor operation passed. Installed `comfyui_workflow_templates 0.11.43` supplied Qwen template SHA-256 `d561a38c15bd7d08758a5e6773d467142244d5b83fc5d3aecdf6d8df9fe881b6` and distilled FLUX template SHA-256 `e0388a8870495802314d58fa61616ddcdb7064dac5f85a8787c9e08180b8a560`. No service/model inference was run。

**Implementation Notes:**

1. Refresh official evidence. Discovery pins are:

```text
Qwen/Qwen-Image-Edit-2511
  repo revision 6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9
  license Apache-2.0

black-forest-labs/FLUX.2-klein-4B
  repo revision e7b7dc27f91deacad38e78976d1f2b499d76a294
  license Apache-2.0
```

Do not assume these are still current; pin by immutable revision and record source URLs. Pin each Comfy split component separately. Do not treat a model-repository revision as the file digest。

2. Reopen the installed official templates as the normative graph sources:

```text
comfyui_workflow_templates 0.11.43
  image_qwen_image_edit_2511.json
  sha256 d561a38c15bd7d08758a5e6773d467142244d5b83fc5d3aecdf6d8df9fe881b6

  image_flux2_klein_image_edit_4b_distilled.json
  sha256 e0388a8870495802314d58fa61616ddcdb7064dac5f85a8787c9e08180b8a560
```

Generate the reviewed API-format derivatives through the existing loader/conversion path. The Qwen binding selects `qwen_image_edit_2511_bf16.safetensors` instead of the template's FP8 default; the FLUX binding selects `flux-2-klein-4b.safetensors` instead of its FP8 default. Keep `Enable 4steps LoRA? = false`; the absent optional LoRA must neither block validation nor execute the lazy branch. Require a machine-readable graph diff proving that every other change is deterministic conversion or a declared binding placeholder。

3. Recheck disk before any further authorized download:

```bash
df -BG /home/reggie /home/reggie/ComfyUI
```

Require `>=200 GiB` free and enforce `160 GiB` total hard cap with lane budgets `90/40/30 GiB` from the spec. Download to a path-resolved staging directory, verify size/SHA-256, then promote. No partial file may be treated as installed。

4. Inspect current ComfyUI `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` and its node inventory without modifying it. Validate workflow through API-format loader and local `/object_info`/system capability response before submit. If incompatible, stop and request separate ComfyUI update authorization; do not update automatically。

5. Run the read-only all-local-model regression before any live P7.1 submit. It must enumerate ComfyUI's effective `folder_paths` rather than only filenames known to P7.1, record every diffusion/text-encoder/VAE/LoRA filename, and header-detect every local diffusion weight. The 2026-08-18 baseline was eight diffusion models, four text encoders, six VAEs and zero LoRAs; all eight diffusion files detected as their existing Wan 2.2, MiniMax H3, Qwen or FLUX classes. Inventory drift is allowed only when fully reported; a previously recognized model becoming unknown is a blocker。

Planned command shape:

```bash
/home/reggie/micromamba/envs/comfyui/bin/python \
  scripts/check_p7_1_comfy_compatibility.py \
  --comfy-root /home/reggie/ComfyUI \
  --qwen-official-template image_qwen_image_edit_2511.json \
  --flux-official-template image_flux2_klein_image_edit_4b_distilled.json \
  --output /absolute/scratch/p7-1-comfy-compatibility.json
```

The command is no-network and must not start ComfyUI, allocate CUDA tensors or load model tensor bytes. This static shared-environment regression does not claim live Wan/MiniMax inference and does not expand P7.1 into those product lanes。

6. VRAM/RAM preflight records GPU identity, driver/CUDA/Torch, free/total VRAM and RAM. FLUX's official ~13 GB statement is only upstream guidance. Qwen BF16/offload on 32 GB is unproven and must pass measured load/inference. OOM fails the profile; no silent FP8/GGUF/LoRA substitution。

**RED:** Static profile tests fail until all real source revisions, component digests, workflow/binding hashes and node versions are complete and exact。

**Acceptance:** Both real profiles pass static/offline validation; official-template lineage and the binding-only graph diff are exact; Qwen's disabled optional LoRA is not required; every currently discoverable local diffusion model remains recognized; global model paths and existing Wan/MiniMax/Legacy workflows are unchanged; model files are present only if explicitly authorized; no GPU generation has occurred yet。

**Verification:**

```bash
python -m pytest -p no:cacheprovider tests/test_production_comfy_image.py -q
/home/reggie/micromamba/envs/comfyui/bin/python \
  scripts/check_p7_1_comfy_compatibility.py \
  --comfy-root /home/reggie/ComfyUI \
  --qwen-official-template image_qwen_image_edit_2511.json \
  --flux-official-template image_flux2_klein_image_edit_4b_distilled.json \
  --output /absolute/scratch/p7-1-comfy-compatibility.json
sha256sum \
  workflows/profiles/p7_1_qwen_image_edit_2511.json \
  workflows/profiles/p7_1_flux2_klein_4b.json \
  workflows/templates/p7_1_*_api.json \
  workflows/bindings/p7_1_*_binding.yaml
```

Use this exact read-only loader check; do not add a public CLI merely for verification:

```bash
python -c 'from ai_video.workflow_loader import load_workflow_template; load_workflow_template("workflows/templates/p7_1_qwen_image_edit_2511_api.json"); load_workflow_template("workflows/templates/p7_1_flux2_klein_4b_api.json")'
```

---

### Milestone 7: Run One Explicit Local Smoke Session

**Files:** No code changes during the smoke; output goes to an isolated, path-resolved scratch Production Project outside committed fixtures。

**Owner / Dependencies:** Requires explicit live-local-smoke authorization after Milestone 6. No authorization means this milestone remains blocked and P7.1 cannot be called live-accepted。

**Contract:** One command performs exactly one Qwen and one FLUX first execution, then exact replay of both. Maximum Provider/Comfy prompt calls are `2`; replay adds `0`. Endpoint is literal loopback; no browser or remote traffic。

**Single command design:**

```bash
python -m scripts.smoke_p7_1_local_image \
  --project-root /absolute/scratch/p7-1-local-smoke \
  --comfy-url http://127.0.0.1:8188 \
  --profiles qwen_image_edit_2511,flux2_klein_4b \
  --max-provider-calls 2 \
  --max-output-count-per-profile 1 \
  --replay-once \
  --require-loopback \
  --confirm-live-local-generation
```

The script must fail unless `--confirm-live-local-generation` is explicit. It prints sanitized profile IDs, ComfyUI commit, model/workflow digests, prompt IDs, elapsed time, peak VRAM/RAM, output hashes and replay counters; it never prints prompt reference bytes or secrets。

**Failure behavior:** A failure after either `/prompt` submission stops the session. Do not retry the failed profile or proceed to another submit when outcome is unknown. Run explicit recovery and report the state。

**Acceptance:** Exactly two first-run submits at most, two valid PNG activations, and replay counters all zero. No non-loopback socket, API key or browser is used。

**Verification:** The smoke's own structured report plus:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_p7_1_local_image_e2e.py \
  tests/test_production_state_recovery.py -q
```

---

### Milestone 8: Execute the Same-Input Blind Quality Benchmark

**Files:**

- Create `docs/benchmarks/p7-1-hybrid-image-inputs.json`
- Create `docs/benchmarks/p7-1-hybrid-image-results.json` only after results exist
- Do not modify runtime routing based on unreviewed results

**Owner / Dependencies:** Requires human-supervised ChatGPT web outputs and approved local live outputs. ChatGPT activity remains manual and outside repository automation。

**Contract:** At least 18 frozen bundles; same visible prompt/reference/output spec across lanes; fixed local seeds; ChatGPT seed recorded as unavailable; blinded opaque IDs; two reviewers plus tie-break; all seven requested quality dimensions and human acceptance rate reported。

**RED:** Before scoring, validation must reject:

- missing reference/prompt hash；
- lane-revealing filename or metadata；
- duplicate candidate bytes presented as different lanes；
- missing reviewer identity/rubric；
- missing ChatGPT source/import receipt；
- aggregate claims without per-case scores。

**Implementation Notes:** Compute lane-specific gates exactly as specified in the spec. Report failures, confidence/denominator and exclusions. Do not rewrite a failed gate as “subjectively close.” Text accuracy is reported for every lane even if the lane is not assigned text-heavy work。

**Acceptance:** Qwen and FLUX responsibilities are enabled only for the benchmark categories whose gates pass. No broad local-vs-ChatGPT equivalence claim is permitted from a role-specific pass。

**Verification:** A deterministic report validator command must be added with the benchmark tooling; planned shape:

```bash
python -m scripts.validate_p7_1_image_benchmark \
  --manifest docs/benchmarks/p7-1-hybrid-image-inputs.json \
  --results docs/benchmarks/p7-1-hybrid-image-results.json
```

If the validator is not implemented, benchmark acceptance is blocked rather than judged from prose alone。

---

### Milestone 9: Final Verification, Independent Review and Runtime Truth

**Files:** Runtime files/tests from Milestones 1-8; runtime-truth docs only after GREEN。

**Contract:** Parent agent owns final diff review and verifies reviewer claims. Documentation distinguishes fake acceptance, local smoke, benchmark acceptance, local merge, push and release。

**Verification:** Run focused P7.1:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_image.py \
  tests/test_production_image_import.py \
  tests/test_production_p7_1_local_image_e2e.py \
  tests/test_comfy_client.py \
  tests/test_workflow_loader.py \
  tests/test_workflow_renderer.py \
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

Run Base E2E and Legacy isolation:

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_base_ai_comic_e2e.py \
  tests/test_config.py \
  tests/test_cli.py \
  tests/test_pipeline.py \
  tests/test_resume_e2e.py \
  tests/test_manifest.py -q
```

Run full and architecture gates:

```bash
python -m pytest -p no:cacheprovider -q
python -m scripts.architecture_gate check
git diff --check
git status --short --branch
git diff --name-status "$P7_1_IMPLEMENTATION_BASE"...HEAD
git diff "$P7_1_IMPLEMENTATION_BASE"...HEAD -- \
  src/ai_video/production/dependency.py \
  src/ai_video/production/models.py \
  src/ai_video/cli.py
```

Expected last diff: empty unless an independently approved schema/CLI gate changed scope, in which case this plan is no longer sufficient and must be revised first。

**Independent Review Scope:**

- loopback enforcement and proxy/redirect bypass resistance；
- exact profile/model/workflow/license binding；
- no transport duplication or second writer；
- ChatGPT import truthfulness；
- permit consumption, provider call counts, replay and unknown outcome；
- P5/P6 ownership and precise invalidation；
- old P7 and Legacy compatibility；
- benchmark blinding and claim discipline。

Reviewer verdict must be `accept | accept with concerns | reject`, with blockers, evidence and minimal follow-up. Parent directly verifies every blocking claim and reruns affected commands。

**Runtime-truth docs:** Only after all applicable gates pass, update current behavior docs with actual ComfyUI/profile hashes, exact test outputs, smoke scope and benchmark verdict. If the benchmark fails, document the lane as disabled or narrowed. Do not record planned behavior as implemented。

**Acceptance:** Clean known tree, no unresolved reviewer blocker, fresh executable evidence, truthful docs and explicit local-vs-origin/push/release state。

## Final Non-Authorization

Completion of this plan document does not authorize any implementation step. Even after future implementation, completion does not imply model redistribution, ComfyUI update, merge, push, release, P8/P9, remote Provider, OpenAI API or unattended ChatGPT automation.
