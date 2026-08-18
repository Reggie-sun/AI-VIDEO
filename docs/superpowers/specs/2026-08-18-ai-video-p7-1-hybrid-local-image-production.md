# AI-VIDEO P7.1 Hybrid Local Image Production Specification

Status: Approved product direction；docs-only design。P7.1 runtime implementation remains unauthorized and must wait for accepted Base AI Comic E2E plus a new explicit implementation authorization.

## 1. Goal

在不改变 P7 durable image lifecycle、不引入 remote image API、也不把网页操作伪装成 Provider 的前提下，定义一个质量优先的 hybrid image production profile：

```text
human-supervised ChatGPT Images web lane
  -> imported Character masters / complex key shots / last-resort repairs

loopback ComfyUI + Qwen/Qwen-Image-Edit-2511 lane
  -> Character-consistent, multi-reference production storyboard images

loopback ComfyUI + black-forest-labs/FLUX.2-klein-4B lane
  -> backgrounds, sketches, layout exploration and fast candidates

all selected assets
  -> existing P7 request / permit / result / PNG / provenance / activation
  -> existing P5 exact invalidation
  -> existing P6 review and Base AI Comic composition path
```

P7.1 的目标是为 P7 增加受控的真实本地 execution adapter 与诚实的人工导入边界，不是宣称本地模型质量已经达到 ChatGPT，也不是扩展到 P8 video generation。

## 2. Problem Boundary

### 2.1 Included

- 一个显式 opt-in、loopback-only 的 local ComfyUI `ImageAssetProvider` adapter。
- 两个 sealed local execution profiles：Qwen production storyboard lane 与 FLUX candidate/background lane。
- 精确绑定 model repository/revision/file digests、ComfyUI commit、workflow/binding digests、seed、references、license 和 output PNG 的 provenance。
- ChatGPT 网页图片的 human-supervised import receipt 与 imported/reference activation path。
- deterministic fake/no-network acceptance、一次显式 local live smoke，以及同输入 blind quality benchmark。

### 2.2 Excluded

- ChatGPT browser automation、无人值守网页操作或 browser session persistence。
- OpenAI Image API、API key、remote image Provider 或 remote fallback。
- 自动模型下载、自动安装依赖、自动更新 `/home/reggie/ComfyUI`。
- 新 public CLI、通用 Agent runtime、queue/server/frontend、P8/P9、video Provider 或 renderer redesign。
- Character/Scene/reference 变化后自动触发 image regeneration。
- 在 benchmark 通过前声称 Qwen 或 FLUX 与 ChatGPT quality equivalent、better 或 production-substitutable。

## 3. Ownership and Existing Boundaries

### 3.1 Single Owner

- Pure local adapter/profile/workflow contract owner: proposed `src/ai_video/production/comfy_image.py`。
- Human import receipt contract owner: proposed `src/ai_video/production/image_import.py`。
- Durable write/permit/activation/recovery owner: existing `ProductionStateCommitter` façade and its private `_state_commit_*` modules。不得出现第二 Manifest、Registry、graph 或 receipt writer。
- Transport owner: existing `src/ai_video/comfy_client.py`。P7.1 只能组合或最小扩展它，不能复制 upload/submit/poll/history/view transport。
- Workflow loading owner: existing `load_workflow_template()`。image-specific binding/rendering 可以新增 focused owner，但 UI-to-API conversion 不得复制。
- Dependency owner: unchanged P5 `dependency.py` builder/resolver。
- QA/repair owner: unchanged P6 review/repair contracts。

### 3.2 Old Path to Replace

P7 当前只有 injected deterministic `ImageAssetProvider`，没有 concrete/live adapter。Legacy `PipelineRunner` 直接组合 `ComfyClient`、video-oriented `WorkflowBinding`、`render_workflow()` 与 clip collector；它是 Legacy video path，不是 P7 image generation path。

P7.1 replaces only the missing concrete local image execution seam. It must not route Production Project image generation through Legacy `PipelineRunner`, `Manifest v1`, clip collection, last-frame chaining, or Legacy `allow_non_local` behavior.

### 3.3 Unchanged Contracts

- Manifest remains `2.5`; Asset Registry schema and `AssetRecord` remain unchanged unless a separately approved schema gate proves an unavoidable gap.
- Public CLI remains `validate | run | resume`。
- P7 request → preview → authorization → durable submit intent → one-use permit → result → measured PNG/provenance → candidate → atomic activation remains mandatory。
- Exact replay occurs before any Provider call or durable write; unknown outcome never blind-resubmits or remints a permit。
- P5 graph stays immutable and does not gain Provider/workflow/model lifecycle nodes。
- P6 owns review and repair; P7.1 does not add a second quality adjudicator or make P6 approval automatically generate a new image。
- Base AI Comic E2E、CI 和 default tests remain deterministic fake/no-network。
- Legacy ComfyUI remains local-first/default-local and behavior-compatible。P7.1 is stricter: its adapter accepts loopback only and has no `allow_non_local` escape hatch。

## 4. Verified Source Snapshot

The following facts were checked on 2026-08-18 and are planning evidence, not runtime acceptance:

| Surface | Verified fact | Planning consequence |
| --- | --- | --- |
| Qwen | The official [`Qwen/Qwen-Image-Edit-2511` model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) identifies Apache 2.0, multi-image inputs, improved character consistency and multi-person consistency. The Hugging Face API reported repository revision `6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9`. | This exact revision is the discovery pin. Implementation must still pin every actual ComfyUI model component and measured SHA-256; repository revision alone is insufficient. |
| FLUX | The official [`black-forest-labs/FLUX.2-klein-4B` model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) states Apache 2.0, text/image generation and multi-reference editing, and approximately 13 GB VRAM. The Hugging Face API reported revision `e7b7dc27f91deacad38e78976d1f2b499d76a294`. | This exact distilled 4B model identity is required. A `base`, 9B, third-party quantization or API model is not an equivalent substitute. |
| Qwen + ComfyUI | The official ComfyUI documentation publishes a [Qwen-Image-Edit-2511 native workflow](https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511) and lists its split diffusion model, text encoder, optional LoRA and VAE. | The official workflow is the normative graph baseline, not merely an example. P7.1 must pin and vendor a reviewed API-format derivative with exact package/source revision and digest, then select the approved local model components through bindings rather than hand-authoring an unrelated graph or following mutable `main` at runtime. |
| FLUX + ComfyUI | The official ComfyUI organization publishes [FLUX.2 Klein workflow templates](https://github.com/Comfy-Org/workflow_templates) and the BFL card states ComfyUI availability. | The exact distilled 4B official template is the normative graph baseline. Its FP8 widget default is not a requirement to replace an approved BF16 checkpoint; the sealed binding selects the exact local component while preserving reviewed graph semantics. `base`, 9B and API variants remain non-equivalent lanes. |
| ComfyUI API | Official [ComfyUI developer documentation](https://docs.comfy.org/development/overview) describes local workflows and a local server API; workflows are node graphs that can generate images and save outputs. | Reuse API-format workflow submission and local transport; do not depend on UI automation. |
| ChatGPT | OpenAI documents [ChatGPT Images 2.0](https://openai.com/index/introducing-chatgpt-images-2-0/) as a ChatGPT product surface. | The repository records `chatgpt_images_2_web` as a human-declared source surface, not as an API model ID or runtime Provider identity. |

Current local inspection found `/home/reggie/ComfyUI` at `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`, with local branch `ahead 9, behind 19`. It must not be updated or modified without separate authorization.

### 4.1 Dated Local Host Compatibility Snapshot

After separately authorized model downloads and a separately authorized PyTorch build repair, the following was measured on 2026-08-18. This is host/preflight evidence, not P7.1 runtime acceptance or a quality claim:

- the dedicated ComfyUI environment is Python `3.12.13` with `torch 2.11.0+cu130`, `torchvision 0.26.0+cu130`, `torchaudio 2.11.0+cu130`, `comfy-kitchen 0.2.31` and `comfy-aimdo 0.4.13`；
- `pip check`, CUDA visibility on the RTX 5090 and a minimal CUDA tensor operation passed；
- installed `comfyui_workflow_templates 0.11.43` contains `image_qwen_image_edit_2511.json` with SHA-256 `d561a38c15bd7d08758a5e6773d467142244d5b83fc5d3aecdf6d8df9fe881b6` and `image_flux2_klein_image_edit_4b_distilled.json` with SHA-256 `e0388a8870495802314d58fa61616ddcdb7064dac5f85a8787c9e08180b8a560`；
- ComfyUI's actual filename inventory exposes eight diffusion models, four text encoders, six VAEs and zero installed LoRAs；
- header-only detection identified all eight local diffusion files: four existing Wan 2.2 files as `WAN21_T2V`, two existing MiniMax H3 files as `MiniMaxH3`, Qwen as `QwenImage`, and FLUX as `Flux2`；
- no ComfyUI server, full model load, image/video inference or P7 durable lifecycle was exercised, so live compatibility remains unproven。

The effective `folder_paths` inventory at that snapshot was:

```text
diffusion_models:
  Wan2_2-I2V-A14B-HIGH_fp8_e4m3fn_scaled_KJ.safetensors
  Wan2_2-I2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors
  flux-2-klein-4b.safetensors
  minimax_h3_fl2va_pruned_int8_convrot.safetensors
  minimax_h3_ref2va_pruned_int8_convrot.safetensors
  qwen_image_edit_2511_bf16.safetensors
  wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
  wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
text_encoders:
  qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
  qwen_2.5_vl_7b_fp8_scaled.safetensors
  qwen_3_4b.safetensors
  umt5-xxl-enc-bf16.safetensors
vae:
  Wan2_1_VAE_bf16.safetensors
  flux2-vae.safetensors
  minimax_h3_audio_vae_fp32.safetensors
  minimax_h3_video_vae_fp16.safetensors
  qwen_image_vae.safetensors
  wan_2.1_vae.safetensors
loras: none
checkpoints: none
```

This inventory is deliberately dated and must be regenerated rather than copied forward as current truth.

The downloaded P7.1 component evidence is:

| Role | Local filename | SHA-256 |
| --- | --- | --- |
| Qwen diffusion | `qwen_image_edit_2511_bf16.safetensors` | `ae42d927b5fac4f278b9a894554c727e619727a63622976f2d95625be4bce08c` |
| Qwen text encoder | `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `cb5636d852a0ea6a9075ab1bef496c0db7aef13c02350571e388aea959c5c0b4` |
| Qwen VAE | `qwen_image_vae.safetensors` | `a70580f0213e67967ee9c95f05bb400e8fb08307e017a924bf3441223e023d1f` |
| FLUX diffusion | `flux-2-klein-4b.safetensors` | `ec3d4e733a771f61c052fb4856c48b336c55eaf2c65487c2a1faeb9bbda7a343` |
| FLUX text encoder | `qwen_3_4b.safetensors` | `6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a` |
| FLUX VAE | `flux2-vae.safetensors` | `d64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5` |

The Qwen official template defaults `Enable 4steps LoRA?` to `false`, and its model switch uses a lazy branch. Therefore absence of the optional Lightning LoRA is not a compatibility blocker for the non-LoRA profile. Enabling that LoRA later requires its own licensed/digested component declaration, binding change, profile hash and benchmark reset.

## 5. Design Decision

Three approaches were considered:

1. **Selected: hybrid human-import + one loopback ComfyUI adapter driven by sealed per-model profiles.** This keeps P7 lifecycle and transport ownership intact, makes local execution reproducible, and preserves a truthful manual lane for the highest-value images.
2. **Rejected: model-specific independent Providers with duplicated HTTP/workflow code.** This creates duplicate transport, inconsistent replay handling and avoidable drift between Qwen and FLUX.
3. **Rejected: ChatGPT browser/API as a Provider.** Browser use has no repository-owned durable submit/outcome protocol, unattended automation is excluded, and no OpenAI Image API authorization exists.

The selected adapter is model-neutral at the transport boundary. Qwen and FLUX differ only through immutable execution profiles, workflows and bindings. The product routing remains explicit and quality-driven; there is no automatic fallback between lanes.

### 5.1 Official Template and Local Binding Rule

- Start from the exact installed official Qwen and distilled FLUX templates recorded in section 4.1; do not design replacement graphs from scratch while an applicable official graph exists。
- Convert/load the pinned official UI workflow through the existing `load_workflow_template()` path and review the resulting API graph. A vendored derivative must retain official graph lineage, source package/version and source SHA-256。
- Bind only declared widget/API paths to the sealed local filenames, prompt, seed, dimensions, references and output prefix. For the current host this means Qwen FP8-default filename to approved Qwen BF16 and FLUX FP8-default filename to approved FLUX BF16; it does not mean changing model identity or precision silently at runtime。
- Any topology change beyond deterministic UI-to-API conversion and explicit binding placeholders requires a reviewed graph diff, a new workflow digest and focused compatibility tests。
- P7.1 must not modify global ComfyUI model search paths, rename existing model files, overwrite official installed templates, or mutate existing Wan/MiniMax/Legacy workflows。

## 6. Hybrid Production Profile

| Lane | Exact responsibility | Inputs | Output admission | Must not do |
| --- | --- | --- | --- | --- |
| `chatgpt_images_2_web` | Character masters, difficult multi-character/key shots, required text-heavy shots, and last-resort repairs after local review failure | Human-entered prompt, human-uploaded Character/Scene/style references, target role and output requirement | Human downloads PNG, verifies it, records true web source and approval, then imports it as `AssetSourceKind.IMPORTED` or a reference asset | No Provider protocol, provider request ID, permit, durable submit intent, browser automation or claim about hidden backend model |
| `qwen_image_edit_2511_local` | Main Character-consistent and multi-reference batch storyboard lane | Exact Character + Scene references, optional style reference only if current P7 validation is separately extended, prompt/negative prompt, seed, dimensions, sealed Qwen profile | Existing P7 generated PNG validation, provenance and atomic target Shot activation | No remote inference, automatic upstream regeneration, unpinned LoRA/quantization or silent model substitution |
| `flux2_klein_4b_local` | Background plates, sketches, layout exploration and fast candidate generation | Exact Character + Scene references required by current P7 request, prompt/negative prompt, seed, dimensions, sealed FLUX profile | Existing P7 generated PNG validation and activation; candidate becomes production only after the same review/import selection gates | No claim that speed implies key-shot quality; no `base`, 9B or API fallback |

Routing is a Codex/human production decision outside repository automation. A local failure does not trigger ChatGPT or another model automatically.

## 7. Local Execution Profile Contract

Each local call consumes one immutable `LocalImageExecutionProfile` whose canonical content hash is the profile ID bound by `ImageGenerationRequest.model_id`. The profile must include:

- lane ID and adapter contract version；
- model repository ID and immutable repository revision；
- every required model component: canonical filename, source repository/revision, byte size and SHA-256；
- variant/precision/quantization identity; absence of quantization is explicit；
- license identifier and authoritative model-card URL；
- exact ComfyUI Git commit；
- required core/custom node names and versions；
- API-format workflow source URL/revision, vendored workflow path and SHA-256；
- binding file path/version/SHA-256；
- supported reference count/roles, dimensions, sampler/scheduler/steps/guidance and output-node contract；
- local loopback endpoint policy；
- profile content hash and schema version。

For P7.1 local requests:

```text
provider_kind = "comfyui_local"
model_id = "local-image-profile:sha256:{profile_content_hash}"
```

The exact profile bytes must be a durable R+1 artifact at `state/images/execution-profiles/{profile_content_hash}.json` and must be reopened before permit minting. The adapter instance must hold the same profile and reject any request/profile mismatch before contacting ComfyUI. Existing fake P7 requests remain compatible and do not acquire a local profile.

If implementation proves that conditional R+1 profile evidence cannot be added without changing existing request/replay semantics, it must stop at an independent request-schema design gate. It must not overload `provider_request_id`, `usage_license`, `policy_receipt_id` or `ToolIdentity.version` with hidden profile data.

## 8. Request, Reference, Output and Provenance Contract

### 8.1 Inputs

- Current P7 requirements remain exact: target Shot/role, prompt, negative prompt, seed, width/height, generation revision, base Project/Registry/Graph pointers, and canonical Character + Scene reference bindings。
- Adapter uploads only the referenced bytes listed by the request; no project directory scan or “latest file” selection。
- A workflow expecting more/fewer references than the sealed profile fails before submit。
- Seed is exact for local lanes. ChatGPT web seed is recorded as `not_exposed`, never invented。

### 8.2 Output

- Exactly one PNG is admitted per request。
- Comfy history must identify exactly one configured `SaveImage` output; ambiguous/multiple unexpected candidates fail closed。
- Adapter downloads bytes through the existing Comfy transport boundary and returns them in `ImageProviderResult`; it does not write Project/Registry/Manifest state。
- Existing P7 code measures PNG signature/chunks/hash/size/dimensions. Provider- or workflow-reported dimensions never override measured values。

### 8.3 Provenance

The durable evidence chain must allow a reader to recover:

```text
request fingerprint
  -> exact Character/Scene/reference identities
  -> local execution profile hash
  -> model repository + revision + component digests + license
  -> ComfyUI commit + workflow/binding digests
  -> seed and generation parameters
  -> sanitized Comfy prompt_id as provider_request_id
  -> measured resource evidence
  -> exact output PNG hash/size/dimensions
  -> existing provenance receipt and activated AssetRecord
```

`provider_request_id` may contain a sanitized real Comfy `prompt_id` only after a real durable submit. Fake tests use a deterministic fake ID. No identifier may be fabricated for a manual ChatGPT image.

## 9. Human ChatGPT Import Contract

ChatGPT web output enters through an immutable `HumanImageImportReceipt`, never `ImageProviderResult`. The receipt must contain:

- `source_surface="chatgpt_images_2_web"`；
- declared UI/product label visible to the human, while `backend_model_id=null`；
- original downloaded filename, exact PNG SHA-256/size/dimensions and import timestamp；
- exact prompt fingerprint and reference asset/creative identities supplied by the human；
- target asset role and whether the asset is Character master, Scene reference, key Shot or repair replacement；
- human actor identity, approval decision and approval timestamp；
- license/source note supplied by the human; no inferred ownership claim；
- `provider_request_id=null`、`durable_submit_intent_present=false`、`automated_browser=false`；
- receipt content hash。

The asset is registered as `AssetSourceKind.IMPORTED`. The existing `ProductionStateCommitter` must persist the receipt, imported PNG, candidate Project/Registry/Graph and final pointer transition. The preferred implementation reuses the existing `commit_project_registry` transaction rather than adding a new Manifest operation. P5 alone computes exact invalidation.

Character/Scene master import may revise the relevant creative artifact and Registry binding, but it does not automatically regenerate existing P7 images. Codex must submit explicit new image requests when desired.

## 10. Loopback ComfyUI Contract

- Accepted hosts are only literal loopback identities resolving to `localhost`, `127.0.0.1` or `::1`; redirects to non-loopback hosts are rejected。
- The adapter never reads or honors Legacy `allow_non_local`。
- `http://127.0.0.1:{port}` is the normal endpoint. HTTPS is not required for loopback, but no proxy environment may reroute the request。
- Upload, `/prompt`, `/history/{prompt_id}`, `/queue`, `/view` and cleanup reuse `ComfyClient` behavior. New byte-returning artifact retrieval may be added there while preserving `download_artifact()` behavior。
- UI automation, Comfy Cloud, partner API nodes and workflow nodes requiring browser/client-server interaction are forbidden。
- A workflow node inventory must be validated against the exact local ComfyUI checkout before submit。

## 11. Quality Benchmark and Admission Gate

### 11.1 Dataset

Use at least 18 frozen input bundles:

- 6 single-character consistency/pose/expression cases；
- 3 multi-character composition cases；
- 3 Scene/background cases；
- 3 required-text cases；
- 3 cross-shot style-continuity cases。

Each bundle fixes prompt, negative prompt, Character/Scene/reference bytes, requested dimensions and acceptance rubric. Qwen and FLUX use recorded fixed seeds. ChatGPT web receives the same visible prompt/reference bundle; its seed remains unavailable.

### 11.2 Blind Review

- Strip metadata and randomize opaque candidate IDs before review。
- At least two human reviewers score independently; disagreement on accept/reject receives a third tie-break review。
- Reviewers do not see lane/model identity, latency or file path。
- Record 1-5 scores for Character consistency, multi-character composition, prompt adherence, anatomy/artifacts, required text accuracy and style continuity, plus binary human acceptance。
- Severe identity break, severe anatomy defect, required-text failure or unsafe/unusable artifact is a hard reject for a production image。

### 11.3 Lane Gates

Qwen may become the batch storyboard lane only if, on its target cases:

- median Character consistency and prompt adherence are at least `4/5`；
- single-character acceptance is at least `80%` and multi-character acceptance at least `70%`；
- hard anatomy/artifact reject rate is at most `10%`；
- no required metric median is more than `0.5` below ChatGPT web, and total acceptance is within `10` percentage points of ChatGPT web。

FLUX may become the background/candidate lane only if:

- Scene/background prompt adherence and style continuity medians are at least `4/5`；
- background/candidate acceptance is at least `80%`；
- hard artifact reject rate is at most `10%`；
- its role-specific median generation time is lower than Qwen on the same host without trading away the above quality thresholds。

Text scores are always reported for all lanes. Passing a role-specific gate does not support a broad “quality equivalent to ChatGPT” claim. Failure keeps the affected lane disabled or narrows its responsibility; it never causes automatic remote fallback.

## 12. Failure, Unknown Outcome and Recovery

| Failure | Required behavior |
| --- | --- |
| Model/profile file missing or digest mismatch | Fail before durable submit; zero Provider call. |
| Local ComfyUI unavailable or incompatible node inventory | Typed fail before submit when possible; no update/fallback. |
| VRAM/RAM preflight insufficient | Fail before submit; report measured requirement and keep lane disabled. |
| OOM or Comfy job failure after prompt submit | Persist terminal/unknown state according to authoritative history; never blindly resubmit. |
| Timeout, lost history or transport ambiguity after submit | `IMAGE_PROVIDER_OUTCOME_UNKNOWN`; explicit recovery only. |
| Multiple/invalid/non-PNG outputs | Fail closed; do not activate any candidate. |
| Crash during candidate activation | Existing exact old/new Project/Registry/Graph recovery; no permit remint or Provider replay. |
| ChatGPT download/source uncertainty | Do not import until a human supplies the missing source/approval fields. |

Comfy cancellation or queue cleanup is best-effort operational cleanup, never authoritative proof that a submitted generation did not execute.

## 13. Compatibility, Disk and Rollback

### 13.1 Compatibility Gate

- First test the current local ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` read-only。
- Pin the exact commit and node inventory in each accepted profile。
- Re-enumerate every current ComfyUI diffusion model, text encoder, VAE and LoRA through `folder_paths`; a hard-coded P7-only directory listing is insufficient。
- Run header-level detection for every discoverable local diffusion model and require the previously supported Wan/MiniMax families plus Qwen/FLUX to remain recognized. This protects the shared ComfyUI environment but does not claim those pre-existing families passed live inference。
- Use the pinned official workflow graph as the source and prove that the vendored derivative differs only by reviewed UI-to-API conversion and declared bindings. Official default filenames that select a different precision are binding inputs, not automatic blockers or permission to download/substitute that precision。
- Keep Qwen Lightning LoRA disabled for the current non-LoRA profile. Its absence must not fail static validation or execute the lazy LoRA branch。
- If it is incompatible, stop. Updating/rebasing `/home/reggie/ComfyUI` requires separate authorization and a rollback plan; P7.1 implementation may not perform it implicitly。
- Qwen BF16/offload viability on RTX 5090 32 GB is unproven. No FP8/GGUF/LoRA substitution is permitted without a new profile, source/license verification and benchmark reset。

### 13.2 Storage Gate

Before any authorized download, require at least `200 GiB` free and reserve a hard maximum of `160 GiB`:

- Qwen profile, components and temporary download space: `90 GiB`；
- FLUX profile, components and temporary download space: `40 GiB`；
- Comfy caches, benchmark outputs and rollback copies: `30 GiB`。

The observed ~2.9 TB free space is context only; implementation must measure again. Exceeding a lane budget stops the download before another component starts.

### 13.3 Rollback

1. Disable P7.1 local profiles and human-import entrypoints。
2. Preserve readers, imported/generated assets, receipts and Manifest 2.5 recovery support。
3. Restore only P7.1-owned workflow/profile files and adapter code through normal Git revert; do not downgrade schemas or delete durable project evidence。
4. Models downloaded under separate authorization may be removed only by an explicit, path-resolved cleanup request; no cleanup is authorized by this spec。
5. Never fall back to remote ComfyUI, OpenAI API, ChatGPT automation or Legacy video generation。

## 14. Implementation and Acceptance Gates

P7.1 runtime work may start only after all are true:

1. Base AI Comic E2E is accepted in code/tests and its Git integration base is explicit。
2. The user grants a separate P7.1 runtime implementation authorization。
3. Target files have one writer and no conflicting dirty work。
4. Exact model/workflow/license evidence is refreshed from official sources。

P7.1 may be called accepted only when:

- deterministic fake/no-network tests cover both profiles, manual import, loopback rejection and error paths；
- model/profile/workflow/component digests are exact and reopenable；
- P7 provider call count is exactly one per first execution and zero on exact replay；
- recovery never calls ComfyUI or remints a permit；
- a separately authorized single local smoke session succeeds without remote traffic；
- blind benchmark results satisfy the lane-specific gates；
- focused, P7 canonical, Legacy isolation, full tests and Architecture Gate pass；
- independent review has no blocking issue；
- runtime-truth docs describe only evidence actually obtained。

This specification does not authorize downloads, dependency installation, ComfyUI changes, GPU execution, runtime implementation, merge, push or release.
