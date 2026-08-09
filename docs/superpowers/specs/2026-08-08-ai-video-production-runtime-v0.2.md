# AI-VIDEO v0.2 — Production Runtime Specification

Status: Superseded on 2026-08-09 after local P1 legacy-runtime stabilization; retained as a historical provider-centric design and safety-contract source.
Target Repository: `Reggie-sun/AI-VIDEO`
Target Version: `0.2.0`
Document Role: 历史规格。不得再作为 v0.2 主线 implementation authority；仍可复用其 paid Provider、Budget Guard、Cloud Egress、Take/Attempt 和 crash-safety 设计。
P0 Baseline: `docs/v0.2-runtime-baseline.md`
P0 Plan: `docs/superpowers/plans/2026-08-08-ai-video-production-runtime-p0-contract-baseline.md`
Primary Goal: Historical — 在保留本地 Wan + ComfyUI 工作流的前提下，将当前单 Provider、单 Take、last-frame 链式生成 CLI 演进为 local-first、provider-agnostic、可审计、可恢复的视频生产运行时。

Successor Spec: `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`

Supersession Note: 本文件第 3 节的 current-state gaps 是 2026-08-08 P0 快照。terminal failed Attempt persistence、direct last-frame dependency invalidation、Legacy FPS semantics 和 artifact promotion rollback 已在本地 `main` 的四个 P1 commits 中实现；Provider abstraction、Manifest v2、Take、Timeline v2、Audio、Budget Guard、Human Review、Semantic Evaluation 和 Seedance 仍未实现。

---

# 1. Document Authority and Scope

本文件定义 v0.2 的目标行为、数据契约、不变量、失败语义和验收标准。

本文件不授权：

* 直接开始编码。
* 一次性实现全文。
* 自动修改当前仓库契约。
* 自动启用云端 Provider。
* 创建或执行 implementation plan。

实施前必须另行编写并审查 plan。每个 plan 只能覆盖本文件后部定义的一个可验证 planning slice。

在 plan 明确更新以下文件并获得批准前，当前仓库契约继续有效：

* `AGENTS.md`
* `docs/agent-primary-contract-matrix.md`
* `README.md`
* 对应源码和测试

因此，本文件中的云 Provider、新 CLI、Manifest v2、新产物布局和 Audio 都是 proposed contract，不是当前 runtime truth。

---

# 2. Product Decision

v0.2 的目标定位是：

`Local-first, model-agnostic AI Video Production Runtime`

该定位包含以下不可分割的约束：

1. 本地 Wan + ComfyUI 仍是默认路径。
2. 云 Provider 必须显式启用，不得成为隐式依赖或默认 fallback。
3. Legacy config、CLI 和 run 必须继续可用。
4. Manifest 仍是执行与恢复状态的持久化真相源。
5. Pipeline 仍按确定性规则运行，不引入自动导演 Agent。
6. Human review 优先于无限自动 quality retry。
7. 任何付费提交必须先经过 Budget Guard。
8. 任何远程数据上传必须可预览、可审计并获得显式 opt-in。

---

# 3. Verified Current State

以下状态以 2026-08-08 的代码为准。后续 plan 必须重新验证，不能只引用本节。

## 3.1 What Exists

当前仓库已经具备：

* Python CLI：`validate`、`run`、`resume`。
* 本地 ComfyUI workflow 加载、UI graph 转 API prompt、binding 渲染。
* 顺序执行 Shot。
* 首镜头显式 `init_image` 校验。
* 上一镜头 last frame 传递给下一镜头。
* 有边界的 infrastructure retry。
* Manifest 原子写入。
* 成功 Shot 的 clip、last frame、normalized clip 和 hash 记录。
* ffmpeg / ffprobe 校验、抽帧、normalize 和 stitch。
* `video-analysis` MCP 的 probe、抽帧、场景检测、转录和启发式 review。
* `CharacterProfile`、多张 `reference_images`、IPAdapter 配置和 Shot character ID 校验。

## 3.2 Current Gaps That Must Not Be Described as Existing Behavior

当前代码尚未完整实现：

* `mark_downstream_stale()` 已定义，但没有接入真实 resume 流程。
* `successful_shot_is_valid()` 只校验 clip 和 last-frame hash。
* `chain_input_hash` 和 `character_ref_hashes` 被记录，但没有参与有效性判断。
* 上游 Shot 重跑后，下游 Shot 仍可能因为自身文件 hash 有效而被错误跳过。
* 终态失败的 Attempt 不会完整落入 Manifest；Attempt history 目前主要在 Shot 最终成功时完整保留。
* Pipeline 没有硬编码 Wan node ID，但依赖单一 ComfyUI transport、单一 template/binding 和 concrete `ComfyClient` 分支。
* `defaults.fps` 同时承担 generation FPS 和 delivery FPS，语义未分离。
* 当前 `video-analysis` review 主要覆盖技术和启发式指标，不等同于 character identity、scene continuity 或 prompt adherence evaluator。

P0 的 plan 必须把这些项目当作 runtime truth gap，而不是已完成能力。

---

# 4. Problem Statement

当前系统能完成：

```text
shot
  -> render one ComfyUI workflow
  -> generate one clip
  -> extract last frame
  -> next shot
  -> normalize
  -> stitch
```

它不足以稳定支持中长视频生产，原因包括：

1. 连续性主要依赖 last-frame chaining。
2. Scene、Style、Object 等 Reference 尚未成为正式 domain。
3. Provider lifecycle 没有统一、可恢复的 contract。
4. Attempt 与创意 Candidate Take 没有分离。
5. 生成成功但质量不合格没有正式状态。
6. source media 与 delivery media contract 没有分离。
7. 没有显式 Video Timeline 和 Audio Timeline。
8. 云调用没有预算预留、结算和数据出站安全边界。
9. 当前 stale 判断不是 artifact dependency graph。
10. 最终视频尚不能由 Manifest 和保留产物确定性重组。

---

# 5. Goals

v0.2 完成后，系统必须支持：

* Legacy Wan 项目无回归运行和 resume。
* Core Pipeline 通过统一 Provider contract 调用本地或显式启用的远程 Provider。
* Reference-first continuity，last frame 只是可选 context。
* 一个 Shot 拥有多个 Take，每个 Take 拥有多个 Attempt。
* Technical Gate、Human Review 和可选语义报告。
* 生成、评价、合成三类独立 invalidation。
* 付费提交前预算检查和预留。
* 每次远程数据上传的显式审计记录。
* 独立 Video Timeline 和 Audio Timeline。
* 只重做真正失效的阶段。
* 从 Manifest 和保留产物重组 `final.mp4`，不重新生成已接受视频。

---

# 6. Non-goals

v0.2 明确不做：

* Web 视频编辑器。
* Premiere 或 DaVinci 替代品。
* 自动导演 Agent。
* 自动拆完整剧本。
* 自动生成所有 Dialogue、Voice、SFX 或 BGM。
* TTS 服务集成。
* 无限 quality retry。
* 自动购买云额度。
* 默认启用云 Provider。
* 一开始接入所有视频模型。
* 自研视频基础模型或 diffusion pipeline。
* ComfyUI 进程管理。
* Celery、Redis、数据库或分布式 worker。
* Callback server；v0.2 云任务恢复以 polling 为准。
* 并行付费生成；v0.2 默认串行 submit，以降低预算和恢复复杂度。

---

# 7. Contract Migration Gate

任何 implementation plan 只要包含以下任一变化，必须先通过 Contract Migration Gate：

* 云端视频 API。
* 新公共 CLI 命令或 flag。
* Manifest schema 变化。
* `runs/<run_id>/` 产物布局变化。
* Audio subsystem。
* 新 runtime dependency。

Gate 的通过条件：

1. 用户明确批准对应 contract 变化。
2. plan 列出需要同步修改的契约、README 和测试。
3. 默认本地行为保持不变。
4. Legacy config 和 run 的兼容策略已经写明。
5. rollback 路径已经写明。
6. 该变化拥有独立、可判定的 acceptance criteria。

未通过 Gate 的 plan 只能实现内部、无 observable regression 的重构。

---

# 8. Architecture and Ownership

```text
Project Sources
    |
    v
Config / Shot / Reference Loader
    |
    v
Resolved Input Snapshot
    |
    +------------------------------+
    |                              |
    v                              v
Prompt + Continuity Resolver   Audio Resolver
    |                              |
    v                              |
Provider Router                    |
    |                              |
    v                              |
Generation Runtime <---------------+
    |
    +--> Attempt lifecycle
    +--> Take lifecycle
    +--> Budget reservation
    +--> Manifest transition
    |
    v
Technical Gate -> Human Review -> Selected Take
    |
    v
Video Timeline + Audio Timeline
    |
    v
Final Composer
```

## 8.1 Single Owners

| Responsibility | Single Owner | Must Not Own |
| --- | --- | --- |
| CLI parsing and user-facing command orchestration | `cli.py` | Provider SDK details、Manifest internals |
| YAML parsing、schema validation、local policy、path resolution | `config.py` | Generation lifecycle |
| Comfy UI graph loading and conversion | `workflow_loader.py` | Provider routing |
| Pure template + binding rendering | `workflow_renderer.py` | Network、Manifest mutation |
| Comfy HTTP/upload/poll/download | `comfy_client.py` | Shot ordering、retry policy |
| Provider request mapping and transport composition | Provider adapter | Manifest mutation、retry decision、Shot ordering |
| Shot/Take/Attempt ordering、retry、resume、state transitions | Generation Runtime / `pipeline.py` | SDK-specific payload construction |
| Atomic persistence、hash、fingerprint helpers | `manifest.py` | Provider calls |
| Media primitives | `ffmpeg_tools.py` | Timeline policy |
| Timeline resolution and composition policy | Timeline / Composer layer | Video generation |

`WanComfyProvider` 必须组合现有 loader、renderer 和 client，不得复制或迁移这些模块的既有实现。

---

# 9. Versioning and Compatibility

## 9.1 Config Version

v2 Project 和 Shot config 必须显式包含：

```yaml
schema_version: 2
```

缺少 `schema_version` 的现有文件按 v1 parser 读取。

禁止通过字段猜测版本。禁止在一个文件中混用 v1 和 v2 顶层结构。v2 schema 对未知字段使用 fail-fast，而不是静默忽略。

## 9.2 Legacy Behavior

Legacy config 必须继续保持：

* `ai-video validate --project ... --shots ...`
* `ai-video run --project ... --shots ...`
* `ai-video resume --manifest ...`
* 单 Take 自动 technical-pass 后选中并 compose。
* flat legacy artifact paths。
* 本地 ComfyUI 默认和 non-local opt-in 规则。

v2 功能不得通过解析 Legacy config 被隐式打开。

## 9.3 Manifest Version

* 缺少 `schema_version` 的 Manifest 视为 v1。
* v1 Manifest 必须继续由 legacy resume path 读取和恢复。
* v1 文件不得在普通 `resume` 中被自动原地改写为 v2。
* v2 reader 可以为 inspect 构造 synthetic view，但不能移动旧文件。
* synthetic view 将每个 v1 `ShotRecord` 映射为一个 `take_001`。
* v1 `succeeded` Shot 可映射为 `generation=succeeded`、`technical=passed`、`review=accepted`，并记录 `selection_reason=legacy_auto_accept`、`compatibility_assumption=true`；该映射不声称 v2 Technical Gate 已实际运行。
* synthetic view 只能保留 v1 已记录的 Attempt；不得补造当前 runtime 没有落盘的 terminal-failure history，且必须用 `history_completeness=legacy_partial` 标明。
* 任何持久化迁移必须写到新文件并保留原 v1 Manifest；具体迁移命令属于后续 plan 决策。

---

# 10. ProjectConfig v2

建议结构：

```yaml
schema_version: 2
project_name: demo

output:
  root: ../runs
  min_free_gb: 1

delivery:
  width: 1024
  height: 576
  fps: 24
  pixel_format: yuv420p
  video_codec: h264
  container: mp4
  audio_sample_rate: 48000
  audio_channels: 2
  audio_loudness_lufs: -16

generation:
  default_provider: wan
  default_model: wan2.2-i2v
  default_width: 1024
  default_height: 576
  default_fps: 24
  default_duration_seconds: 6
  default_seed: 1
  seed_policy: derived
  max_attempts_per_take: 2
  max_takes_per_shot: 3

runtime:
  poll_interval_seconds: 2
  job_timeout_seconds: 1800

prompt:
  default_negative_prompt: ""
  style_prompt: ""

providers:
  wan:
    type: comfyui
    enabled: true
    base_url: http://127.0.0.1:8188
    allow_non_local: false
    workflow:
      template: ../workflows/templates/wan22_i2v_api.json
      binding: ../workflows/bindings/wan22_i2v_binding.yaml

  seedance:
    type: seedance
    enabled: false
    allow_remote: false
    model: dreamina-seedance-2-0-<version>
    api_key_env: SEEDANCE_API_KEY

budget:
  enabled: false
  currency: USD
  max_run_cost: "20.00"
  max_shot_cost: "5.00"
  max_take_cost: "3.00"

references:
  root: ../references

review:
  mode: manual

audio:
  enabled: false
```

规则：

* `output` 只描述产物位置和磁盘保护。
* `delivery` 描述最终媒体 contract。
* Provider native media 参数属于 resolved Provider request，不得覆盖 delivery contract。
* Provider config 使用 discriminated model，不能把 SDK-specific 字段塞进 Core Domain 的任意 `dict`。
* API key 只能从命名的 environment variable 读取。
* `allow_remote: true` 只是启用资格，不等于允许 silent fallback。
* v1 `defaults.width/height/fps` 在 compatibility view 中同时映射为 generation defaults 和 delivery defaults，但必须记录这是 legacy-derived value。
* v1 `output.min_free_gb` 必须保留，不能在 v2 schema 中丢失。
* 所有 config、workflow、Reference、output 和 audio 文件路径在 resolved config / Manifest 中都必须是干净绝对路径；content fingerprint 使用内容身份，不使用机器相关路径。

## 10.1 Legacy Project Mapping

v1 Project 通过 compatibility view 运行，不要求用户先改文件。映射必须覆盖全部现有字段：

| v1 Field | v2 Compatibility Mapping |
| --- | --- |
| `project_name` | `project_name` |
| `comfy.base_url` / `allow_non_local` | `providers.wan.base_url` / `allow_non_local` |
| `workflow.template` / `binding` | `providers.wan.workflow.template` / `binding` |
| `output.root` / `min_free_gb` | `output.root` / `min_free_gb` |
| `defaults.width` / `height` / `fps` | generation defaults，并同时作为 legacy-derived delivery defaults |
| `defaults.clip_seconds` | `generation.default_duration_seconds` |
| `defaults.seed` / `seed_policy` | `generation.default_seed` / `seed_policy` |
| `defaults.negative_prompt` / `style_prompt` | `prompt.default_negative_prompt` / `style_prompt` |
| `defaults.max_attempts` | `generation.max_attempts_per_take`；Legacy `max_takes_per_shot=1` |
| `defaults.poll_interval_seconds` / `job_timeout_seconds` | `runtime.poll_interval_seconds` / `job_timeout_seconds` |
| `characters[]` | compatibility Character records；保留 `id`、`name`、string `description` 和全部 `reference_images` |
| `characters[].ipadapter` / `future_lora` | Wan typed provider options；字段和值原样保留 |

Compatibility view 不得把 v1 默认值写回 source config，也不得丢弃当前 parser 已接受的字段。

---

# 11. Reference Domain

## 11.1 Static ReferenceAsset

静态 Reference 是项目输入，不包含 previous frame/video 等运行时产物。

```yaml
references:
  - id: character_alice_front
    type: character
    source:
      kind: local_file
      path: characters/alice_front.png
    description: Alice front identity reference
    allowed_providers: [wan, seedance]
```

支持类型：

```text
character
scene
style
object
camera_motion
audio
```

Resolved Reference 必须记录：

* reference ID 和 type。
* source kind。
* 干净绝对路径或 provider asset ID。
* content hash。
* MIME type、size 和基础 media metadata。
* Provider eligibility。
* 是否会发生 remote egress。

## 11.2 Runtime ArtifactReference

以下内容属于 Runtime Artifact，不属于静态 Reference Library：

```text
previous_video
previous_first_frame
previous_last_frame
selected_take_clip
provider_native_audio
```

Runtime ArtifactReference 必须包含 source Shot、source Take、artifact hash 和 dependency reason。

## 11.3 Character and Scene

```yaml
characters:
  - id: alice
    name: Alice
    description:
      age_group: adult
      hair: long black hair
      outfit: white shirt and black coat
    references:
      - character_alice_front
      - character_alice_side
    continuity:
      identity: strict
      outfit: strict

scenes:
  - id: coffee_shop
    description: warm modern coffee shop at night
    references:
      - coffee_shop_wide
      - coffee_shop_counter
    continuity:
      lighting: strict
      environment: medium
```

`strict`、`medium` 等值只是 review policy 输入，不能被当成 Provider 保证。

## 11.4 Provider Eligibility

Provider 不支持某类素材、素材数量、尺寸、格式或人物资格时，必须在 static validate 或 explicit provider probe 中失败。

禁止：

* 静默丢弃 Reference。
* 静默裁剪 Reference 而不记录 requested/effective 差异。
* 把 local path 当成已经上传的 provider asset。
* 将不符合远程 Provider 人物素材规则的文件自动改投其它 Provider。

---

# 12. ShotSpec v2

```yaml
schema_version: 2
shots:
  - id: shot_001
    scene: coffee_shop
    characters: [alice]

    action: alice walks toward the entrance
    prompt: null
    negative_prompt: null

    camera:
      framing: medium
      movement: slow dolly forward

    requested_media:
      duration_seconds: 6
      width: 1024
      height: 576
      fps: 24

    continuity:
      strategy: reference_only
      previous_shot_id: null
      allow_downgrade: false

    references:
      - character_alice_front
      - coffee_shop_wide

    provider:
      preferred: wan
      fallback: null
      allow_fallback: false

    generation:
      takes: 2
      seed: null

    audio:
      native_provider_audio: disabled
      ambience_reference: coffee_shop_ambience
      sfx: []
```

`action` 是结构化意图；`prompt` 是可选人工 override。最终提交文本由 Prompt Builder 生成，并在 Manifest 中持久化。

`native_provider_audio` 的允许值是 `disabled | optional | required`。`required` 遇到不支持 native audio 的 Provider 必须在 submit 前失败；`optional` 可以解析为 `effective_native_audio=disabled`，但 requested/effective 差异和原因必须持久化。Provider 返回的 native audio 仍只是 Audio Timeline 的 source track。

## 12.1 Legacy Shot Mapping

Legacy parser 必须显式保留所有当前字段：

| v1 Field | v2 Compatibility Mapping |
| --- | --- |
| `id` | `id` |
| `prompt` | `prompt` override |
| `negative_prompt` | `negative_prompt` |
| `characters` | `characters` |
| `seed` | `generation.seed` |
| `clip_seconds` | `requested_media.duration_seconds` |
| `fps` | `requested_media.fps` |
| `width` / `height` | `requested_media.width` / `height` |
| `init_image` | explicit first-frame Runtime input |
| `continuity_note` | semantic continuity note |
| `metadata` | preserved legacy metadata namespace |

禁止只按 `id/prompt` 转换并丢弃其它字段。

---

# 13. Prompt and Resolution Contract

Prompt Builder 必须是纯逻辑：

```text
resolved Character / Scene / Style descriptions
    + Shot action
    + Camera intent
    + continuity note
    + explicit prompt override policy
    -> ComposedPrompt
```

Manifest 必须同时保存：

* source fields。
* composed positive prompt。
* composed negative prompt。
* Prompt Builder version。
* requested Provider/model。
* effective Provider/model。

相同 resolved inputs 和 builder version 必须生成相同 ComposedPrompt。

---

# 14. Continuity and Dependency Contract

支持策略：

```text
independent
reference_only
previous_frame
previous_video
reference_plus_previous_frame
reference_plus_previous_video
```

规则：

1. Global References 是 identity/world anchors。
2. Previous Take 是可选 continuity context。
3. Last frame 不再是唯一策略，但 legacy mode 继续支持。
4. `previous_shot_id` 必须指向已存在的上游 Shot。
5. Dependency graph 必须无环。
6. 未显式声明 previous dependency 的 Shot 不因前序 Shot 变化而 generation-stale。
7. 选择新的上游 Take 时，只使真正引用旧 Take artifact 的下游 generation-stale。
8. Provider capability 不满足请求时，默认 validation error。
9. 只有 `allow_downgrade: true` 时才能选择声明过的降级策略。
10. requested/effective strategy 和降级原因必须持久化。

Router 不得根据“看起来差不多”静默降级。

---

# 15. Provider Contract

## 15.1 Serializable Types

```python
class Money(BaseModel):
    amount: Decimal
    currency: str


class ProviderErrorRecord(BaseModel):
    code: str
    message: str
    retryable: bool
    sanitized_detail: str | None


class ArtifactDescriptor(BaseModel):
    artifact_id: str
    kind: Literal["source_video", "native_audio"]
    path: Path
    sha256: str
    size_bytes: int
    mime_type: str


class ProviderJobHandle(BaseModel):
    provider: str
    model: str
    job_id: str
    idempotency_key: str
    created_at: datetime
    job_lookup_expires_at: datetime | None


class CostEstimate(BaseModel):
    expected: Money | None
    upper_bound: Money | None
    pricing_source: str
    quoted_at: datetime
    expires_at: datetime | None


class ProviderJobStatus(BaseModel):
    state: Literal["queued", "running", "succeeded", "failed", "cancelled", "expired"]
    checked_at: datetime
    provider_updated_at: datetime | None
    progress: Decimal | None
    result_expires_at: datetime | None
    actual_cost: Money | None
    error: ProviderErrorRecord | None


class GenerationResult(BaseModel):
    source_video: ArtifactDescriptor
    native_audio: ArtifactDescriptor | None
    actual_cost: Money | None
    provider_metadata: ProviderResultMetadata


class ProviderCapabilities(BaseModel):
    billing_mode: Literal["local_unmetered", "estimated", "metered"]
    text_to_video: bool
    first_frame_image: bool
    last_frame_image: bool
    reference_images: bool
    max_reference_images: int
    reference_video: bool
    max_reference_videos: int
    reference_audio: bool
    max_reference_audio: int
    native_audio: bool
    seed: bool
    idempotent_submit: bool
    idempotency_retention_seconds: int | None
    lookup_by_idempotency_key: bool
    cancellable_jobs: bool
    supported_durations_seconds: list[int] | None
    min_duration_seconds: int | None
    max_duration_seconds: int | None
    supported_resolutions: list[str]
    supported_fps: list[int]


class GenerationRequest(BaseModel):
    request_id: str
    shot_id: str
    take_id: str
    prompt: str
    negative_prompt: str | None
    requested_duration_seconds: int
    requested_width: int
    requested_height: int
    requested_fps: int | None
    native_audio_policy: Literal["disabled", "optional", "required"]
    seed: int | None
    image_references: list[ResolvedReference]
    video_references: list[ArtifactReference]
    audio_references: list[ResolvedReference]
    provider_options: ProviderOptions
```

`ProviderOptions` 必须是按 Provider 类型区分的 typed model。禁止用无约束 `metadata: dict` 作为 Provider-specific backdoor。

`ProviderResultMetadata` 同样必须是按 Provider 类型区分、经过 allowlist 和 secret redaction 的 typed model；原始 SDK response 不是 Core contract。

Capability 中的 `None` 表示静态 adapter 无法枚举、需要在显式 probe 或 submit 前 resolution 中确认，不表示“不受限制”。`supported_durations_seconds` 与 min/max range 不能给出互相冲突的约束；任何未验证能力都不得被 Router 当作已支持。`idempotent_submit=true` 时必须同时给出可验证的 retention window；超出该窗口后不得 replay。

`GenerationRequest` 是用户请求语义。Provider 完成 capability resolution 后产生 `ResolvedGenerationRequest`，其中必须包含 requested/effective media、continuity、audio、Provider/model 参数。Runtime 再对该 resolved form、依赖 artifact 和 adapter/template 版本做 canonical serialization，计算最终 `generation_fingerprint` 和 Attempt `request_fingerprint`；不得在 resolution 前计算一个不完整 fingerprint。

## 15.2 Interface

```python
class VideoProvider(Protocol):
    name: str

    def capabilities(self) -> ProviderCapabilities: ...

    def validate_request(
        self,
        request: GenerationRequest,
    ) -> ResolvedGenerationRequest: ...

    def estimate_cost(
        self,
        request: ResolvedGenerationRequest,
    ) -> CostEstimate: ...

    def submit(
        self,
        request: ResolvedGenerationRequest,
        *,
        idempotency_key: str,
    ) -> ProviderJobHandle: ...

    def get_job(
        self,
        job: ProviderJobHandle,
    ) -> ProviderJobStatus: ...

    def find_job_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> ProviderJobHandle | None: ...

    def materialize(
        self,
        job: ProviderJobHandle,
        target_dir: Path,
    ) -> GenerationResult: ...

    def cancel(self, job: ProviderJobHandle) -> None: ...
```

Runtime 拥有 polling、timeout、retry、Budget 和 Manifest transition。Provider adapter 不得拥有这些策略。

`wait()` 不作为唯一 Core API，因为阻塞式 wait 不能表达持久化 job、进程恢复和 `submit_unknown`。

若 `cancellable_jobs=false`，`cancel()` 必须抛出类型化 unsupported error；不得伪造远程任务已取消。若 `lookup_by_idempotency_key=false`，`find_job_by_idempotency_key()` 同样必须返回类型化 unsupported error，不能用全量 job 扫描猜测匹配。

---

# 16. Provider Implementations

## 16.1 WanComfyProvider

职责：

* 把 `GenerationRequest` 映射到现有 renderer 所需 context。
* 组合 `load_workflow_template()`、`render_workflow()` 和 `ComfyClient`。
* 使用 Comfy `prompt_id` 作为 provider job ID。
* 收集并 materialize clip。
* 把 Comfy failure 映射为 `AiVideoError` / `ErrorCode`。

不得：

* 复制 UI graph conversion。
* 复制 binding renderer。
* 决定 Shot 顺序。
* 决定 retry 或 fallback。
* 直接写 Manifest。

## 16.2 MockProvider

必须支持可编程场景：

* success。
* validation failure。
* submit failure before job creation。
* submit response lost / `submit_unknown`。
* queued/running/succeeded polling。
* terminal provider failure。
* timeout / expired。
* corrupt download。
* deterministic estimated and actual cost。

默认 CI 不得调用真实 ComfyUI 或云 Provider。

## 16.3 SeedanceProvider

Seedance 是 proposed opt-in Provider，不是 v0.2 前置默认依赖。

实现 plan 必须以当时官方 API 文档为准，并至少处理：

* 异步 task submit/query/cancel。
* Provider task ID 和结果 URL 的 TTL。
* image/video/audio reference 数量、格式、尺寸和资格限制。
* 模型是否支持 seed；不支持时必须 validation fail 或显式解析为 `effective_seed=null`，不得静默假装使用了 seed。
* remote asset upload / asset ID 生命周期。
* real-person reference 的授权和 trusted-asset 约束。
* actual usage 返回和成本结算。
* content safety / policy failure 不得自动 fallback。

Provider model ID 必须来自配置，不能把示例别名 `seedance-2` 硬编码为 API ID。

SeedanceProvider 只有在 Budget Guard、Cloud Data Egress 和 crash-safe Attempt persistence 完成后才能启用真实 submit。

---

# 17. Provider Routing

v0.2 Router 使用 deterministic rules，不使用 Agent。

Resolution 结果必须在 submit 前固定：

```text
Shot request
    -> preferred provider config
    -> capability validation
    -> explicit downgrade policy
    -> explicit fallback policy
    -> budget validation
    -> ResolvedExecutionPlan
```

规则：

* 默认 Provider 是本地 `wan`。
* `fallback` 只有在 Shot 和 Project 均显式允许时可用。
* auth、budget、invalid config、content safety、data-egress denial 不得 fallback。
* capability mismatch 默认在 validate 阶段失败。
* runtime failure 后跨 Provider fallback 会创建新 Take，而不是新 Attempt。
* fallback 前必须重新估算预算并重新确认数据出站资格。
* requested/effective provider、model、continuity strategy 和 fallback reason 必须持久化。

---

# 18. Attempt Lifecycle

Attempt 表示一次 Provider submission lifecycle，不表示新的创意候选。

```text
planned
  -> submitting
  -> submitted
  -> running
  -> materializing
  -> succeeded

submitting -> submit_failed
submitting -> submit_unknown
submit_unknown -> submitted
submit_unknown -> submit_failed
submitted/running -> provider_failed
submitted/running -> expired
submitted/running -> cancelled
materializing -> materialize_failed
materialize_failed -> materializing
```

恢复边的限制：

* `submit_unknown -> submitted` 只能在 lookup 或保证期内的 idempotent replay 返回同一个 billable job identity 后发生。
* `submit_unknown -> submit_failed` 只能在 Provider 明确证明没有创建 job 且没有费用后发生。
* 无法证明上述任一结果时，Attempt 必须停留在 `submit_unknown`，Run 进入 `recovery_required`。
* `materialize_failed -> materializing` 只能重试同一 job 的同一结果，不得调用 generation submit。

## 18.1 Required Attempt Fields

```text
attempt_id
attempt_number
request_id
request_fingerprint
idempotency_key
provider
model
status
provider_job_handle
cost_ledger_entry_id
started_at
updated_at
completed_at
error
```

这些 key 在每个 Attempt record 中都必须存在；尚未产生的 handle、completion timestamp 或 error 使用 `null`，不得靠字段缺失区分 lifecycle state。对应 ledger entry 同样保持固定 schema，未取得的 actual cost 使用 `null` 和 `unsettled`。

## 18.2 Atomic Persistence Order

每次付费 submit 必须遵守：

1. 生成稳定的 `attempt_id`、`request_fingerprint` 和 `idempotency_key`。
2. Budget Guard 创建 reservation。
3. Manifest 原子写入 `submitting` 和 reservation。
4. 调用 Provider `submit()`。
5. 收到 job ID 后立即原子写入 `submitted` 和 `provider_job_handle`。
6. 后续 poll 只使用已持久化 handle。
7. materialize 完成后写入 artifact hash。
8. Provider actual usage 可用时结算 reservation。

如果第 4 步可能成功但客户端没有收到响应：

* Attempt 进入 `submit_unknown`。
* Runtime 不得自动创建新 submission。
* Provider 支持 `lookup_by_idempotency_key` 时，Runtime 可以用原 key 查询并恢复 handle。
* Provider 明确保证 `idempotent_submit` 且保证期仍有效时，Runtime 可以重放完全相同的 resolved request 和 key 来取回同一个 job；这不是创建新 Attempt。
* 两种能力都不可用或保证期已过时，必须停下并要求 inspect/review。

本文把同一 request、同一 key、Provider 保证同一 billable job identity 的调用称为 `idempotent replay`，它属于 reconcile，不属于 resubmit。`resubmit` 指使用新 key、改变 request，或 Provider 可能创建第二个 job 的调用；`submit_unknown` 禁止 resubmit。

每条恢复边都必须先计算目标状态和 ledger action，再在同一次 Manifest 原子写中更新 Attempt、ledger entry 和 sanitized history。恢复出 `submitted` 后才允许继续 poll；恢复出 `materialize_failed` 时沿用原 handle 和 ledger entry。

---

# 19. Take and Review Lifecycle

Take 表示一个创意候选。Infrastructure retry 留在同一 Take；quality regeneration 创建新 Take。

为避免单一 enum 状态爆炸，Take 使用独立状态轴：

```text
generation_status: planned | running | succeeded | failed
technical_status: pending | passed | failed
review_status: pending | accepted | rejected
generation_freshness: fresh | stale
evaluations[<evaluator_id>].freshness: not_run | fresh | stale
```

`generation_freshness` 只表示 source generation inputs 和 dependency artifacts 是否仍匹配当前 generation fingerprint。每个可选 evaluator 拥有独立 record、fingerprint 和 freshness；一个 evaluator 的变化不得使其它 evaluator stale。它们都不得替代 Technical Gate。Composition freshness 属于 Run，不属于单个 Take。

## 19.1 Selection Invariants

`selected_take_id` 只能指向同时满足以下条件的 Take：

* `generation_status == succeeded`
* `technical_status == passed`
* `review_status == accepted`
* `generation_freshness == fresh`
* Technical Gate 记录的 source clip hash 和 gate-policy fingerprint 仍是当前值
* clip 和 required artifacts 的 hash 有效

v0.2 的语义 evaluator 默认 report-only，不阻断 selection。若 Project review policy 显式列出 required evaluator IDs，则这些 records 也必须存在、fresh 且满足该 policy；该要求不能通过一个聚合 overall score 隐式开启。

Manual selection 必须原子地执行：

1. 将目标 Take 标记为 accepted。
2. 写入 `selection_reason`、reviewer 和 timestamp。
3. 更新 `selected_take_id`。
4. 计算 downstream generation invalidation。
5. 标记 Video Timeline / Composition stale。
6. 原子写入 Manifest。

Reject 必须记录 reason。Regenerate 必须创建新的 Take ID，不得覆盖旧 Take、Attempt 或费用记录。

一个 Take 的 generation fingerprint 和成功 source artifact 是不可变审计记录。改变 prompt、Reference、Provider、model、seed 或其它 generation input 必须创建新 Take；同一 Take 内的新 Attempt 只允许重试完全相同的 resolved request。

Legacy mode 可以把唯一 technical-pass Take 自动标为 accepted，并记录 `legacy_auto_accept`。

---

# 20. Retry Contract

## 20.1 Infrastructure Retry

可以自动重试：

* 明确发生在 job 创建前的 transient submit failure。
* 对同一个 job 的 poll transient failure。
* 对同一个结果的可恢复 download failure。
* 明确 terminal 且 Provider 声明可安全重提的 failure。

不得自动重提：

* 对 `submit_unknown` 使用新 key 或任何可能创建新 job 的 resubmit；仅允许 18.2 定义的 lookup / idempotent replay reconcile。
* auth failure。
* budget denial。
* invalid request / unsupported capability。
* content safety / policy denial。
* remote egress 未授权。

## 20.2 Quality Retry

Quality retry 创建新 Take，并受以下全部限制：

* `max_takes_per_shot`。
* `max_run_cost`、`max_shot_cost`、`max_take_cost`。
* Human review policy。
* Provider availability 和 capability。

禁止任何无上限的 score-driven loop。

---

# 21. Budget and Cost Ledger

Budget Guard 是任何付费 Provider submit 的前置依赖。

## 21.1 Money Type

金额使用 15.1 定义的 `Money`。JSON 中 `amount` 必须编码为 decimal string，或由后续 plan 统一选择固定最小货币单位；禁止使用 binary float 作为持久化金额真相，同一 schema version 内不得混用两种编码。

## 21.2 Reservation Model

```text
CostEstimate
    -> reserve declared upper-bound amount
    -> persist reservation
    -> provider submit
    -> settle actual usage
    -> release unused reservation
```

如果 actual cost 尚不可用，ledger 状态必须保持 `unsettled`，不能写成 0。

Paid Provider 的 `CostEstimate` 必须提供有限、同币种的 reservation upper bound；只有 expected value 而没有可执行上界时不得 submit。若最终 actual cost 仍超过 reservation，必须如实结算、写入 `budget_status=exceeded`、使 Run 进入 `recovery_required` 或 `failed`，并阻断后续 paid submits，不能截断或篡改账本。

Ledger 是金额状态的 single owner；Attempt 只保存 `cost_ledger_entry_id`，不得再维护一份可独立变更的 cost 副本。Ledger 必须按 Attempt 记录，包括：

* accepted Take cost。
* rejected Take cost。
* failed Attempt cost。
* retry cost。
* reservation、settled、released、unsettled 状态。

每次 Budget Guard 判断必须把已结算支出和所有未释放 reservation 一并计入 Run、Shot 和 Take 上限。失败、被拒绝和 retry 已产生的实际费用仍计入预算，不得因未被选中而扣除。

`budget.enabled: false` 表示禁止任何 paid Provider submit，不表示绕过 Guard。若任一 `billing_mode != local_unmetered` 的 Provider 配置为 `enabled: true`，static validation 必须要求 Budget 启用、币种合法且 Run/Shot/Take 限额均为有效正数。本地 unmetered Provider 不受此开关阻断。

## 21.3 Attempt State to Reservation Action

| Attempt State | Required Ledger Action |
| --- | --- |
| `planned` | 不创建 reservation |
| `submitting` / `submitted` / `running` / `materializing` | 保持 reservation，占用 Run/Shot/Take 可用预算 |
| `submit_failed` 且 Provider 明确未创建 job | release 全部 reservation；actual cost 记录为 Provider 明确返回的 0 |
| `submit_unknown` | 保持 reserved 或 `unsettled`；禁止按 0 释放 |
| `provider_failed` / `expired` / `cancelled` | 查询并结算已产生费用；无法确认时保持 `unsettled` |
| `materialize_failed` | generation 费用照常 settled/unsettled；重试同一 artifact download 不创建新 generation reservation |
| `succeeded` | 结算 actual usage 并释放余额；actual usage 延迟时保持 `unsettled` |

人工放弃 `submit_unknown` 也不得静默释放 reservation。只有 Provider 证明确无 billable job，或后续 plan 定义了显式、带 reason/actor/timestamp 的管理型 adjustment，才能解除占用；adjustment 不能改写原 Attempt cost history。

## 21.4 Currency

Provider 原币和 Run budget 币种必须分别保存。

v0.2 允许两种策略：

1. Provider 原币与 Run budget 相同。
2. 配置一个固定 conversion rate，并将 rate、source label 和 timestamp 快照写入 Manifest。

没有可重现 conversion snapshot 时，不得跨币种聚合预算。

预算不足时必须在 Provider `submit()` 之前拒绝。v0.2 不提供 warn-only paid submit。

---

# 22. Evaluation Contract

## 22.1 Technical Gate

Technical Gate 是 Take 被接受前的必需步骤，检查：

* 文件存在且 hash 有效。
* ffprobe 可读取。
* duration 在容差内。
* width、height、FPS 和 pixel format 可 normalize。
* codec/container 可接受。
* corruption / blank output。
* `native_audio_policy=required` 时必须存在可读 audio；`optional` 且实际返回 audio 时同样必须校验。

Technical failure 不得通过 manual selection 绕过。

## 22.2 Semantic and Continuity Report

第一版为 report-only，至少允许输出：

```python
class EvaluationResult(BaseModel):
    evaluator_id: str
    evaluator_version: str
    evaluation_fingerprint: str
    freshness: Literal["fresh", "stale"]
    technical_score: float | None
    continuity_score: float | None
    prompt_adherence_score: float | None
    findings: list[EvaluationFinding]
    created_at: datetime
```

不得要求一个神奇的 overall score 自动决定所有镜头。

现有 `video-analysis` 代码可以通过内部 Python adapter 复用技术分析能力，但 Core Runtime 不得依赖 MCP server transport 才能工作。Character identity、scene continuity 和 prompt adherence 必须视为新增 evaluator 能力，不得把现有启发式 review 描述成已支持。

---

# 23. Media Contract

## 23.1 FPS

必须区分：

```text
requested_fps
effective_provider_fps
source_fps
delivery_fps
```

Provider 不支持 requested FPS 时，必须在 submit 前给出 validation error 或显式 resolved difference。

所有进入 Video Timeline 的 normalized clips 必须满足统一 delivery contract：

* width。
* height。
* FPS。
* pixel format。
* codec。
* container。

## 23.2 Duration

必须区分：

```text
requested_duration
effective_provider_duration
generated_duration
normalized_duration
timeline_duration
```

所有值必须来自实际 request、Provider response 或 ffprobe，不得互相覆盖。

---

# 24. Video Timeline

最终顺序必须来自显式 Timeline，不得从目录名或文件排序推断。

```python
class VideoTimelineEntry(BaseModel):
    shot_id: str
    take_id: str
    source_artifact_id: str
    normalized_artifact_id: str
    start_seconds: Decimal
    trim_start_seconds: Decimal
    trim_end_seconds: Decimal | None
    transition: TransitionSpec | None
```

Timeline resolver 必须从每个 Shot 的 valid selected Take 构造列表。缺少 selected Take、hash 无效或 generation-stale 时，compose 必须失败并列出具体 Shot。

---

# 25. Audio Timeline

Audio 与视频生成 Provider 解耦。Provider native audio 只是可选 source track，不是最终 mix。

## 25.1 Timebase and Delivery

* 配置时间以 decimal seconds 表示。
* 渲染时对齐到 48 kHz audio samples 和 delivery video frames。
* 默认输出 48 kHz、stereo、AAC。
* 默认 integrated loudness target 为 `-16 LUFS`。
* 默认 true peak 不高于 `-1.5 dBTP`。
* Final mux 的音视频时长差不得超过 `max(one video frame, 20 ms)`。

## 25.2 Track Model

```yaml
audio:
  tracks:
    - id: ambience_coffee_shop
      type: ambience
      source: audio/ambience/coffee_shop.wav
      lifecycle: scene
      scene: coffee_shop
      start_seconds: 0
      trim_start_seconds: 0
      trim_end_seconds: null
      loop: true
      gain_db: -12
      fade_in_seconds: 0.5
      fade_out_seconds: 0.5
```

支持 track type：

```text
dialogue
voiceover
sfx
ambience
bgm
provider_native
```

规则：

* Dialogue / voiceover 在 v0.2 必须提供本地音频文件；文本只可作为 script metadata，不能触发隐式 TTS。
* Ambience 默认以 Scene 为生命周期，可跨多个 Shot 连续播放。
* BGM 默认以 Project 或 Scene 为生命周期。
* duck/fade/stop/resume 必须解析成显式 automation events。
* selected Take duration 变化后必须重新解析 Timeline。
* 只修改非 native audio 不得使视频 generation-stale。

---

# 26. Fingerprints and Invalidation

系统必须使用版本化 canonical serialization 生成 generation、evaluation 和 composition 三个独立 fingerprint family。Technical Gate 使用 evaluation family 下独立且必需的 gate fingerprint，不能与可选语义报告共用 freshness owner。

Canonical payload v1 规则：

* Domain prefix 固定为 `ai-video-fingerprint-v1`，并包含 fingerprint kind。
* 编码为 UTF-8 JSON；object key 按字典序；无非语义 whitespace。
* 有语义顺序的 array 保持顺序；无序集合先按稳定 ID 或 content hash 排序。
* File input 用 content hash、size 和 MIME 表示，不把机器相关的绝对路径当作内容身份。
* `Decimal` 使用规范十进制字符串；timestamp 使用 UTC RFC 3339；fingerprint payload 禁止 binary float。
* request ID、job ID、运行时间和 secret 等非语义字段不得进入 fingerprint。
* schema 规定的 `null` 不得因 serializer 实现差异随机省略。
* 最终值为 domain prefix 与 canonical JSON bytes 的 SHA-256。

## 26.1 Generation Fingerprint

至少包含：

* resolved Shot semantics。
* composed prompts 和 builder version。
* requested/effective Provider、model 和 adapter schema version。
* seed，仅在 Provider 支持且实际使用时。
* requested/effective duration、resolution、FPS。
* requested/effective native audio policy。
* Provider generation parameters。
* resolved static Reference content hashes。
* continuity Artifact hashes。
* Wan template 和 binding hashes。

变化后：Take `generation_freshness=stale`，需要 regenerate。

## 26.2 Evaluation Fingerprint Family

Required `technical_gate_fingerprint` 至少包含：

* source clip hash。
* Technical Gate implementation/version。
* gate policy、media tolerance 和 required native-audio policy。

每个 Optional semantic/continuity evaluator record 的 `evaluation_fingerprint` 至少包含：

* source clip hash。
* evaluator ID 和 version。
* evaluation policy/config。
* continuity evaluator 实际比较的 upstream/downstream Take IDs 和 clip hashes。
* Reference hashes 和 evaluation-context resolver version。

Technical Gate fingerprint 变化后：把 `technical_status` 重置为 `pending` 并只重跑 gate。可选语义 fingerprint 变化后：只把对应 `evaluations[evaluator_id].freshness` 标为 `stale` 并重跑该 evaluator。二者都不得使 generation stale。

## 26.3 Composition Fingerprint

至少包含：

* selected normalized clip hashes。
* trim / transition。
* delivery media contract。
* resolved Audio Timeline。
* audio source hashes。
* composer version 和 relevant ffmpeg settings。

变化后：Run `composition_freshness=stale`，只需 re-compose。

Manifest 中 `desired_composition_fingerprint` 表示按当前 selection、delivery 和 Audio Timeline 解析出的目标输入；`final_output.composition_fingerprint` 表示现有成品实际使用的输入。只有两者相等且 final artifact hash 有效时，`composition_freshness=fresh`。不得用一个可覆盖字段同时充当 desired 和 applied owner。

## 26.4 Invalidation Matrix

| Change | Required Action |
| --- | --- |
| Prompt、Reference、Provider、model、generation params | Regenerate affected Take and dependent downstream |
| Upstream selected Take changes | Regenerate only downstream that consumes its artifact; mark affected continuity evaluations stale; recompose timeline |
| Technical Gate version/policy/tolerance | Reset technical status and rerun Technical Gate only |
| Evaluator version/policy | Re-evaluate affected Take |
| Review note/status changes without changing `selected_take_id` | Update review state only |
| BGM、ambience、SFX、audio gain/fade | Re-compose audio/final only |
| Delivery codec/FPS/resolution | Re-normalize and re-compose; do not regenerate source video unless Provider request also changed |
| Missing normalized artifact | Re-normalize from retained accepted clip |
| Missing accepted source clip | Regenerate or fail; cannot silently compose |

---

# 27. Manifest v2

Manifest 必须保持稳定、可读 JSON，并在每次状态转换后原子写入。

最小结构：

```json
{
  "schema_version": 2,
  "run_id": "...",
  "status": "ready_to_compose",
  "composition_freshness": "stale",
  "history": [
    {
      "event_id": "event_001",
      "type": "run_status_changed",
      "from": "awaiting_review",
      "to": "ready_to_compose",
      "reason": "take_selected",
      "created_at": "2026-08-08T00:00:00Z"
    }
  ],
  "input_snapshot": {
    "project_source_path": "/absolute/source/project.yaml",
    "project_source_hash": "...",
    "shots_source_path": "/absolute/source/shots.yaml",
    "shots_source_hash": "...",
    "resolved_project_path": "/absolute/run/path/inputs/project.resolved.json",
    "resolved_shots_path": "/absolute/run/path/inputs/shots.resolved.json"
  },
  "shots": [
    {
      "shot_id": "shot_001",
      "resolved_references": [],
      "takes": [
        {
          "take_id": "take_001",
          "generation_status": "succeeded",
          "technical_status": "passed",
          "review_status": "accepted",
          "generation_freshness": "fresh",
          "requested_provider": "seedance",
          "effective_provider": "seedance",
          "model": "dreamina-seedance-2-0-<version>",
          "generation_fingerprint": "...",
          "technical_gate_fingerprint": "...",
          "technical_source_clip_hash": "...",
          "attempts": [
            {
              "attempt_id": "attempt_001",
              "attempt_number": 1,
              "request_id": "request_001",
              "request_fingerprint": "...",
              "status": "succeeded",
              "idempotency_key": "...",
              "provider": "seedance",
              "model": "dreamina-seedance-2-0-<version>",
              "cost_ledger_entry_id": "cost_001",
              "provider_job_handle": {
                "provider": "seedance",
                "model": "dreamina-seedance-2-0-<version>",
                "job_id": "...",
                "idempotency_key": "...",
                "created_at": "...",
                "job_lookup_expires_at": "..."
              },
              "started_at": "...",
              "updated_at": "...",
              "completed_at": "...",
              "error": null
            }
          ],
          "artifacts": {
            "source_clip": {
              "artifact_id": "artifact_001",
              "path": "/absolute/run/path/shots/shot_001/takes/take_001/clip.mp4",
              "sha256": "..."
            }
          },
          "technical_gate": {
            "status": "passed",
            "source_clip_hash": "...",
            "gate_fingerprint": "..."
          },
          "evaluations": {}
        }
      ],
      "selected_take_id": "take_001"
    }
  ],
  "video_timeline": [],
  "audio_timeline": [],
  "desired_composition_fingerprint": "...",
  "cost_ledger": [
    {
      "ledger_entry_id": "cost_001",
      "attempt_id": "attempt_001",
      "estimated": {"amount": "0.80", "currency": "USD"},
      "reserved": {"amount": "0.80", "currency": "USD"},
      "actual": {"amount": "0.72", "currency": "USD"},
      "settlement_status": "settled",
      "updated_at": "..."
    }
  ],
  "final_output": null
}
```

`final_output` 非空时必须包含 final artifact descriptor、`composition_fingerprint`、created timestamp 和 composer version；写入顺序是先校验并原子 materialize 成品，再在 Manifest 中绑定 applied fingerprint 和 output hash。

## 27.1 Run Lifecycle

Run 使用以下持久化状态：

```text
created -> running
running -> awaiting_review | ready_to_compose | recovery_required | succeeded | failed | cancelled
awaiting_review -> running | ready_to_compose | cancelled
recovery_required -> running | failed | cancelled
ready_to_compose -> composing | running | cancelled
composing -> succeeded | failed
failed -> running | cancelled
succeeded -> running | awaiting_review | ready_to_compose
```

规则：

* `awaiting_review` 和 `recovery_required` 是持久化暂停状态，不是 completed run。
* `failed` 表示最近一次命令以类型化失败结束；只要 Manifest 中存在安全恢复路径，它仍可由 `resume` 转回活动状态。
* `cancelled` 只有在所引用的 Provider jobs 已取消或明确记录无法取消时才能写入。
* `succeeded` 只有在 selected Take invariants、required artifact hashes 有效，且 desired/applied composition fingerprints 相等时成立。
* `succeeded` 只能在 source/snapshot comparison、fingerprint 或 artifact invariant 发现新失效后 reopen：generation invalidation 进入 `running` 或 `awaiting_review`，composition-only invalidation 进入 `ready_to_compose`，evaluation-only invalidation 进入 `running`。无变化时 `resume` 必须保持 `succeeded` 并无副作用。
* `running -> succeeded` 只允许用于不需要 generation 或 composition 的恢复路径，例如 evaluation-only refresh；转换前必须重新验证 generation freshness、所有 required evaluator records、selected Take invariants、desired/applied composition fingerprints 和 final output hash。
* 每次状态变化都必须追加 sanitized history event；不得只覆盖当前字符串而丢失原因。
* Shot-level status 从 Take、selection 和 dependency state 推导。若为查询性能缓存，resume 时必须重算，不能成为第二个状态 owner。

## 27.2 Provenance

每个最终 Artifact 必须可追溯到：

* source Shot、Take 和 Attempt。
* requested/effective Provider 和 model。
* sanitized request snapshot。
* Reference IDs 和 content hashes。
* input fingerprints。
* output hash。
* created timestamp。
* tool/adapter version。

Manifest 和 request snapshot 不得包含 API key、Authorization header、signed download query、cookie 或原始敏感 Provider response。

## 27.3 Input Snapshots

Run 创建时必须在 run 目录保存 secrets-redacted resolved inputs。

`resume` 规则：

* 原 source files 存在时，重新解析并与 snapshot 比较，计算 stage-specific invalidation。
* source files 缺失时，可以使用 snapshot 恢复未完成的已知 job 和 compose，但不能导入新修改。
* 任何 source change 和 resulting stale decision 必须记录在 Manifest event/history 中。

---

# 28. Artifact Layout v2

新 v2 Run 使用：

```text
runs/<run_id>/
├── manifest.json
├── inputs/
│   ├── project.resolved.json
│   ├── shots.resolved.json
│   └── references.resolved.json
├── shots/
│   └── <shot_id>/
│       └── takes/
│           └── <take_id>/
│               ├── request.json
│               ├── provider_response.sanitized.json
│               ├── clip.mp4
│               ├── first_frame.png
│               ├── last_frame.png
│               ├── evaluation.json
│               └── attempts/
│                   └── <attempt_id>/
│                       └── diagnostics.json
├── normalized/
│   └── <shot_id>/
│       └── <take_id>.mp4
├── audio/
│   ├── sources/
│   ├── normalized/
│   └── mix/
├── timeline/
│   ├── video_timeline.json
│   └── audio_timeline.json
└── final/
    └── final.mp4
```

规则：

* normalized path 必须包含 Shot 和 Take，避免切换 Take 时覆盖。
* Manifest path 是真相源，Runtime 不得通过扫描目录推断状态。
* Legacy run 保留原 flat layout，不移动文件。
* 下载和 compose 使用临时文件，校验成功后原子 rename。
* 所有写入 Manifest 的路径必须是干净绝对路径。

---

# 29. CLI Contract v2

## 29.1 Preserved Commands

```bash
ai-video validate --project ... --shots ...
ai-video run --project ... --shots ...
ai-video resume --manifest ...
```

Legacy 调用行为保持兼容。

## 29.2 Proposed Commands

```bash
ai-video inspect --manifest ...
ai-video review --manifest ...
ai-video regenerate --manifest ... --shot ...
ai-video compose --manifest ...
ai-video cost --manifest ...
```

这些命令只有通过 Contract Migration Gate 后才能加入公共 CLI。

## 29.3 Command Semantics

### `validate`

默认必须无副作用：

* 不创建 run 目录。
* 不写 Manifest。
* 不上传素材。
* 不发起付费请求。
* 不做默认网络 availability probe。

它必须完成 schema、path、Reference、adapter 声明的静态 capability snapshot、workflow binding、media 和 budget config 校验。需要远程 discovery 才能确认的能力必须明确标为 `unverified`，不能在默认 `validate` 中偷偷联网。

如后续 plan 增加 `--probe-providers`，该 flag 必须显式触发只读网络检查，并且仍禁止上传或付费 submit。

### `run`

* 创建新 Run 和 Manifest。
* Legacy mode 保持单 Take 自动完成并 compose。
* v2 manual review mode 在 candidates 生成并通过 Technical Gate 后进入 `awaiting_review`，不得伪装为 final success。

### `resume`

* 从 Manifest 启动，不创建新 Run。
* 对持久化 job handle 继续 poll，不盲目 resubmit。
* 按 stage fingerprint 只重做失效阶段。

### `inspect`

只读输出 Run、Shot、Take、Attempt、stale reason、cost、audio 和 composition 状态。

### `review`

支持 accept、reject、select 和请求 regenerate。所有 mutation 必须原子写 Manifest。

### `regenerate`

创建新 Take；只传播真实 dependency invalidation；不得覆盖旧 Take。

### `compose`

只执行 normalize、Video Timeline、Audio Timeline、mix 和 final mux。不得调用视频 Provider。

### `cost`

只读输出 reservation、settled、unsettled、accepted、rejected 和 retry cost。

## 29.4 Exit Codes

保持现有语义：

* `0`：命令成功完成其声明的阶段，包括明确进入 `awaiting_review`。
* `1`：类型化、可解释的用户输入、Provider、budget 或 runtime failure。
* `2`：未预期内部错误。

---

# 30. Cloud Data Egress and Security

任何远程 Provider plan 必须实现：

1. Project-level `enabled` 和 `allow_remote` 双重显式启用。
2. submit 前生成将上传的文件、hash、size、MIME 和目标 Provider 清单。
3. Reference eligibility validation。
4. Secret、header、cookie、signed URL 和 account identifier redaction。
5. HTTPS-only download，除非 Provider adapter 有明确测试过的例外。
6. 受限 host / redirect policy。
7. 最大下载大小、content type 和 media probe 校验。
8. 临时文件下载、hash 校验和原子 rename。
9. partial file 清理。
10. sanitized Provider response allowlist；默认不落盘原始 response。
11. 远程上传、任务创建和下载的审计事件。

Provider 不得通过异常 detail 或 debug log 泄露 secret。

---

# 31. Resume and Recovery Semantics

Resume 必须处理：

```text
valid accepted Take             -> skip generation
pending/submitted/running job   -> poll existing job
submit_unknown                  -> reconcile or stop; never blind resubmit
provider terminal failure       -> apply typed retry policy
generation_freshness=stale      -> regenerate affected Take/downstream
one or more evaluator records stale -> re-run only those evaluators
composition_freshness=stale     -> re-normalize/re-compose as required
rejected Take                   -> retain; do not regenerate unless requested
missing normalized artifact     -> rebuild from accepted source clip
missing accepted source clip    -> fail or regenerate according to policy
audio-only change               -> re-compose without video generation
```

Run 的 terminal status 不能只依据 `manifest.status` 字符串；必须重新验证 required artifact hashes 和 selected Take invariants。

---

# 32. Acceptance Criteria

以下标准是后续 plans 的共同上限。每个 plan 只选择与其 slice 对应的子集，但不得降低语义。

1. Legacy Wan 3-shot fixture 继续使用当前三个 CLI 命令完成生成、resume 和 final compose。
2. Legacy config 不会隐式启用 v2、云端或 Audio。
3. 终态失败 Attempt 会在异常返回前原子持久化。
4. 上游 artifact 变化会使真实依赖它的下游 generation-stale。
5. 不依赖上游 artifact 的 Shot 不被过度 invalidation。
6. Pipeline 不再依赖 concrete `ComfyClient` 类型分支。
7. `WanComfyProvider` 复用现有 loader、renderer 和 client。
8. Provider job handle 可序列化并在 resume 后继续 poll。
9. `submit_unknown` 不会用新 key 或可能创建新 job 的方式自动 resubmit；若执行 idempotent replay，测试必须证明 job identity 不变且 billable job 数不增加。
10. Budget denial 时 Provider `submit()` 调用次数为 0。
11. 每个付费 Attempt 都有 reservation 和 settlement 状态。
12. 不支持 seed 的 Provider 不会把 requested seed 记录为 effective seed。
13. 未授权 remote egress 在上传前失败。
14. Manifest、request snapshot 和 logs 不包含 secret 或 signed URL。
15. 一个 Shot 可保留至少两个 Take 和各自 Attempt history。
16. selected Take 必须同时满足 generation、technical、review 和 hash invariants。
17. 切换 selected Take 不覆盖旧 Take 和费用记录。
18. Technical Gate 在 accept/select 前运行。
19. evaluator version 变化只使该 evaluator record stale，并只触发对应 re-evaluation。
20. BGM/ambience/SFX 变化只触发 re-compose。
21. delivery FPS 变化触发 normalize/compose，不自动重新生成 source clip。
22. v2 normalized artifact path 对不同 Take 唯一。
23. v1 Manifest 普通 resume 不发生原地 schema rewrite。
24. `validate` 默认不创建文件、不联网、不上传、不付费。
25. `compose` 永不调用视频 Provider。
26. Final MP4 音视频时长差满足 Audio Timeline 容差。
27. Manifest 能回答每个最终 Artifact 的 Shot、Take、Attempt、Provider、model、References、hash 和 cost provenance。
28. 从 Manifest 和 retained accepted artifacts 可以重组 final output，不调用视频 Provider。
29. `submit_unknown` 只有在同一 billable job 被证明或无 job 被证明时才能离开该状态；每条恢复边与 ledger/history 同次原子写入。
30. 已 `succeeded` Run 在输入无变化时 resume 无副作用；发生 stage-specific invalidation 时只 reopen 到对应活动状态。
31. 一个 evaluator 的版本或上下文变化不会使其它 evaluator record stale。
32. Attempt 只引用 cost ledger entry，金额状态不存在第二个可写 owner。
33. `composition_freshness=fresh` 必须同时满足 desired/applied fingerprint 相等和 final output hash 有效。

---

# 33. Testing Requirements

## 33.1 Required Test Layers

| Layer | Required Coverage |
| --- | --- |
| Unit | schema、fingerprint、state transition、budget arithmetic、routing、redaction、timeline resolution |
| Component | 每个 Provider adapter 使用 fake HTTP/transport；ffmpeg command construction |
| Integration | MockProvider + real Manifest persistence + crash injection + resume |
| Compatibility | Legacy config、Manifest v1、flat artifact layout、Legacy CLI |
| Optional Live | 本地 ComfyUI smoke；显式 opt-in Seedance smoke |

## 33.2 Mandatory Failure Tests

至少覆盖：

* Manifest 在每个 Attempt transition 后可恢复。
* submit 前崩溃。
* Provider 已创建 job 但响应丢失。
* unknown job 经 lookup 或 idempotent replay 恢复，job identity 和 billable job 数不变。
* unknown job 被 Provider 明确证明不存在后安全转为 `submit_failed`。
* job ID 持久化后崩溃。
* poll transient failure。
* job expired。
* download 中断、超限、错误 MIME、corrupt media。
* `materialize_failed` 重试不调用 generation submit、不创建新 reservation。
* Budget reservation 后 submit failure。
* actual cost 高于和低于 estimate。
* rejected Take 保留。
* selected Take 切换传播。
* succeeded Run 的 no-op resume，以及 generation/evaluation/composition 各自的受控 reopen。
* 多 evaluator fingerprint 独立 invalidation。
* v1 read/resume 不改写。
* remote egress denial。
* secret/signed URL redaction。
* Audio Timeline loop、fade、duck 和 duration tolerance。
* compose failure 不触发 generation。

## 33.3 Test Command Surfaces

后续 plan 必须按改动面至少包含：

```text
tests/test_config.py
tests/test_workflow_loader.py
tests/test_workflow_renderer.py
tests/test_comfy_client.py
tests/test_pipeline.py
tests/test_manifest.py
tests/test_resume_e2e.py
tests/test_ffmpeg_tools.py
tests/test_cli.py
```

新增模块必须有对应 test file。真实云调用不得进入默认 CI。

---

# 34. Future Plan Boundaries

本节只定义后续 plan 的边界和依赖，不是 implementation plan。

```text
P0 Contract decision + verified baseline
    |
    v
P1 Runtime truth fixes
    |  terminal failure persistence
    |  real stale propagation
    |  source/delivery media semantics
    v
P2 Provider abstraction, local only
    |  Provider DTOs
    |  MockProvider
    |  WanComfyProvider
    |  no public behavior change
    v
P3 Manifest v2 + crash-safe Attempt lifecycle
    |
    v
P4 Take + Technical Gate + Human Review + Video Timeline
    |  core selected-artifact dependency graph
    |  selection/regenerate invalidation
    |
    +----> P5 Reference domain + expanded dependency validation
    |          |
    |          +----> P6 Budget Guard + Cloud Egress Security
    |          |          |
    |          |          v
    |          |      P7 SeedanceProvider
    |          |
    |          +----> P8 Semantic Evaluation reports
    |
    +----> P9 Audio Timeline + Final Composer
```

约束：

* 每个边界必须生成独立 plan。
* P2 必须保持 CLI、Manifest v1 和 artifact layout 无 observable regression。
* P3 之前不得真实接入异步付费 Provider。
* P4 之前不得让用户选择未经 Technical Gate 的 Take。
* P4 的 user-visible select/regenerate 必须与最小 selected-artifact dependency graph 和精确传播测试一起交付；不能等到 P5 才补正确性。
* P6 之前不得真实提交云任务。
* P7 依赖 P3、P5 和 P6；P8 依赖 P4 和 P5。
* P9 依赖 P4，但不依赖 Seedance 或其它云 Provider。
* P7 和 P9 不应出现在同一个首轮 implementation plan。
* 每个 plan 必须列出 old path 如何退役或保留，不能形成双 owner。

---

# 35. Rollback and Compatibility Strategy

* P1/P2 内部重构必须可通过 revert 恢复，不改公共 schema。
* Manifest v2 初期只由显式 v2 config 创建。
* v1 reader/resume 在整个 v0.2 周期保留。
* 新 v2 artifacts 不覆盖或移动 legacy artifacts。
* 云 Provider 可以通过 config disable；disable 后本地 Wan 不受影响。
* Audio 可以独立 disable；disable 后 silent-video compose 继续工作。
* 如果某个新 Provider adapter 回滚，已有 accepted local artifacts 仍可 compose。
* schema rollback 不承诺把 v2 Manifest 降级写成 v1；因此 v1 原文件不得被自动覆盖。

---

# 36. Definition of Done

本规格只有在以下全部成立时才视为实现完成：

* 当前 Legacy Wan 示例仍可用。
* Core Pipeline 不包含 Wan-specific request assumptions。
* Provider abstraction 没有复制现有 workflow/client owners。
* Async job 可以 crash-safe resume，且不会 blind resubmit。
* Character、Scene、Style、Object References 是一等输入。
* Runtime Artifact 和静态 Reference 生命周期分离。
* Last frame 是可选 continuity context，不是唯一架构。
* Take 和 Attempt 语义、状态和成本记录完全分离。
* Technical Gate 先于 accept/select。
* generation、evaluation、composition invalidation 分离。
* source FPS 和 delivery FPS 明确记录。
* 云端保持 opt-in，所有付费请求受 Budget Guard 保护。
* 所有远程数据出站可审计且不泄露 secret。
* Audio 拥有独立 Timeline，非 native audio 修改不触发视频生成。
* Final output 支持连续 ambience/BGM 和明确 media contract。
* Manifest 完整记录 generation、review、cost 和 composition provenance。
* Resume 只重做真正 stale 或缺失的阶段。
* `final.mp4` 可由 Manifest 和 retained artifacts 重组，不重新生成 accepted video Takes。
* Unit、integration、compatibility 和 failure-injection tests 覆盖所有关键状态转换。

---

# 37. External References

后续 Seedance plan 必须重新检查当前官方文档。本文撰写时使用：

* BytePlus ModelArk Video Generation API: `https://docs.byteplus.com/en/docs/modelark/1520757`
* BytePlus ModelArk Billing: `https://docs.byteplus.com/docs/ModelArk/1099320`

外部 Provider capability、model ID、价格、素材规则和 TTL 都是会变化的运行时事实，不得只依赖本规格中的快照。
