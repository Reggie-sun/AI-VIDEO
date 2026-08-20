# Video Planner Subagent — Requirements

Status: proposed (slice draft, awaiting scope lock)
Owner: AI-VIDEO planning intelligence layer
Target module path: `src/ai_video/planning/` (new top-level package)

## Context

AI-VIDEO v0.2 Production Harness 已经拥有：

- `ProductionProject` — canonical schema owner of Character / Scene / Shot / Story
- Asset Registry — identity & provenance
- `ResolvedTimeline` — order / frame / sample / timing
- `HyperFrames` — default Production renderer
- `production.shot_router.ShotVisualResolver` + `VideoGenerationResolver` — provider-aware routing inside Production
- `production.video.VideoGenerationRequest` + `VideoGenerationMode` — sealed submission contract
- `production._video_continuity` — hard-cut continuity evidence

这些是 AI-VIDEO 的 canonical ownership。任何新增模块都必须**不取代**：

- Shot owner
- Asset owner
- Manifest owner
- Timeline owner
- Provider owner
- v2 writer / committer
- Continuity evidence owner

现有 `ShotVisualResolver` 已经是 production internal routing；它回答 “this Shot 应该被路由到**哪个** capability”，并接受 `VideoProviderCapabilities`。这是一个 provider-aware 的内部决策器。

Main Agent 现在缺一个**前置**、**provider-neutral** 的智能层，用来回答：

> “这个 Shot 应该采用什么生成策略？”

新模块就是用来补这个 gap。它必须在 Production 之上、独立于 Provider、调用方为 Main Agent。本文档锁定需求边界。

## Who is affected

| Role | Pain today | After this slice |
|---|---|---|
| Main Agent | 没有显式的“生成策略”抽象，只能猜或读 Shot 直觉判断 | 通过 `VideoPlanner.plan(request)` 拿到结构化的 `VideoGenerationPlan` |
| Production Harness | 必须自己重复决定 continuity mode / motion requirement / required bindings | 接收 plan 作为 hint；仍保留 final authority |
| External Skills (hell-grind / higgsfield / open-video / video-shotcraft) | 各自只能给创作建议，没有统一 plan 容器 | 都能消费/产出 `VideoGenerationPlan` 的字段（plan / craft / validate / judge / refine 思想） |

## What this slice must deliver

1. 一个 `VideoPlanner`（pure function / class），输入 `VideoPlanningRequest`，输出 `VideoGenerationPlan`。
2. `VideoPlanningRequest` 与 `VideoGenerationPlan` 是 `pydantic` frozen models，含 `content_hash` seal。
3. 支持至少 7 个 generation mode 候选：`static_image` / `image_motion` / `text_to_video` / `image_to_video` / `first_last_frame_video` / `reference_to_video` / `hybrid`。
4. 决策遵循**纯函数**：相同输入（含 content_hash）→ 相同 plan_hash。无 IO、无网络、无 secret、无 Provider 调用。
5. 至少 5 个 acceptance case（见 acceptance criteria）必须可重复执行。
6. 一份 Main Agent 调用契约文档 + 至少 1 个真实场景示例。

## Explicitly out of scope

- 调用任何 Provider（H3 / Hailuo / Seedance / ComfyUI / OpenAI / Anthropic）
- 选择 Provider；plan 必须只含 `required_capability`
- 上传 / 下载文件
- 读取 secret 或 `ARK_API_KEY`
- 修改 Manifest / Asset Registry / Shot revision
- 创建第二套 timeline
- 自动生成视频
- 自动 repair / retry
- LangGraph / 新 Agent runtime / MCP server
- 重写 `ShotVisualResolver` / `VideoGenerationResolver` / `HyperFrames`
- 新 Manifest schema / 新 Provider adapter
- 新 dependency graph schema

## Functional requirements

### FR-1 — Plan-only output

`VideoGenerationPlan` 必须只描述**应该被怎么生成**，不描述**由谁生成**。

```python
class VideoGenerationPlan(StrictModel):
    plan_hash: str                              # sha256 of canonical payload
    target_shot_id: str
    target_shot_revision: int
    target_shot_content_hash: str
    generation_mode: GenerationMode              # one of 7 enum values
    continuity_mode: ContinuityMode              # exact_terminal | reference | semantic | none
    required_asset_roles: tuple[AssetRole, ...]
    capability_requirements: CapabilityRequirements
    motion_requirement: MotionRequirement
    reason_codes: tuple[ReasonCode, ...]         # min_length=1
    confidence: float                            # 0.0 .. 1.0
    warnings: tuple[str, ...]
```

**Forbidden fields**（任何一项出现 → contract violation）：

- `provider_name`
- `provider_profile`
- `provider_kind`
- `selected_capability_id`
- `selected_mode`（与 `required_mode` 同义；本层只能给 required）
- `manifest_revision`
- `timeline_position`
- `asset_path` / `artifact_path`
- `output_asset_id`

### FR-2 — Pure determinism

- `plan_hash` = `canonical_sha256(plan.model_dump(mode="json", exclude={"plan_hash"}))`
- `create(**values)` classmethod 提供 sealed construction
- 任何 external state（filesystem / network / secret / clock）禁止进入函数
- 输入是 `Shot` 来自 `ProductionProject`，但 `VideoPlanner` 不直接 import registry — 通过传入的 `VideoPlanningRequest` 注入

### FR-3 — Continuity decision is required

`continuity_mode` 必须在所有 7 个 mode 都有定义；不能为 `None`。

| Continuity mode | 语义 | 典型 trigger |
|---|---|---|
| `exact_terminal` | 同一动作继续，同镜头延长 | 上游 Shot 同一动作链，未换角度 |
| `reference` | 换角度，保持角色与场景 | 上游 Shot 切轴 / 切距离，仍是同一语义时刻 |
| `semantic` | 时间跳跃 / 场景变化 | 状态语义（衣着 / 伤势 / 道具 / 场景身份）已变 |
| `none` | 完全独立 | 首 Shot / 无上游 / 显式标记 reset |

### FR-4 — Motion requirement granularity

至少 6 个 `MotionRequirement` 等级：

- `none` → `static_image`
- `light_transform` → `image_motion`
- `graphic` → `motion_graphics`（mapping 到 `hybrid` 或被 caller 翻译）
- `character_action` → 主要路径
- `free_complex` → 主要路径
- `hero_or_repair` → 默认 blocked（需要更上层策略）

### FR-5 — Required capability, not selected capability

`CapabilityRequirements` 描述 *needed* 能力，**不**绑定具体 provider。例：

```python
class CapabilityRequirements(StrictModel):
    needs_character_reference: bool = False
    needs_scene_reference: bool = False
    needs_first_frame: bool = False
    needs_last_frame: bool = False
    needs_terminal_reference: bool = False
    needs_audio_native: bool = False
    needs_continuity_state: bool = False
    max_reference_count: int | None = None       # ≥0
    min_output_duration_seconds: int | None = None
    accepts_local_execution: bool = True
    accepts_remote_execution: bool = True
```

错误形态（绝对禁止）：

```json
{ "provider": "H3", "model_id": "h3-local-7b" }
{ "selected_capability_id": "h3.reference_to_video.v1" }
```

正确形态：

```json
{ "required_capability": { "mode": "reference_to_video", "needs_character_reference": true, "needs_terminal_reference": false } }
```

### FR-6 — Reason codes are auditable

`reason_codes` 至少包括：

- `IMPORTANT_CHARACTER`
- `IDENTITY_REQUIRED`
- `CONTINUITY_REQUIRED`
- `REFERENCE_AVAILABLE`
- `TERMINAL_AVAILABLE`
- `NO_CHARACTER_REFERENCE`
- `NO_SCENE_REFERENCE`
- `NO_VISUAL_ANCHOR`
- `FREE_ENVIRONMENT`
- `FIRST_SHOT`
- `SEMANTIC_JUMP`
- `MOTION_NONE`
- `MOTION_LIGHT`
- `MOTION_GRAPHIC`
- `MOTION_HERO_REQUIRES_POLICY`
- `MISSING_TERMINAL`
- `MISSING_REFERENCES`

每个 plan 至少 1 个 reason code；reason code 与 chosen mode 必须逻辑一致（在 test 中验证）。

### FR-7 — Confidence is required

`confidence: float ∈ [0.0, 1.0]`。

- `1.0` = 唯一明显策略
- `0.7–0.9` = 主导策略但有 alternatives
- `<0.5` = 需要 Main Agent 二次确认（必须伴随 `warnings` 非空）

### FR-8 — Warnings are typed

`warnings: tuple[str, ...]` 必须使用受控枚举字符串而非 free-form。允许：

- `MISSING_CHARACTER_REFERENCE`
- `MISSING_SCENE_REFERENCE`
- `MISSING_TERMINAL_FRAME`
- `LOW_CONFIDENCE`
- `REQUIRES_HUMAN_REVIEW`

### FR-9 — Inputs reuse AI-VIDEO models，不新建

`VideoPlanningRequest` 必须是 wrapper，**复用**：

- `Shot` （已有）
- `Character` （已有）
- `Scene` （已有）
- `AssetType` / `AssetRoleRequirement` 字段语义映射（不复制定义）

不创建新的 Story / Character / Shot schema。

### FR-10 — Production ownership boundary

`VideoPlanner` 必须：

- 不 import `state_commit` / `committer` / `manifest` / `dependency` / `hyperframes` / `composition`
- 不 import `comfy_client` / `ffmpeg_tools` / Provider adapter
- 不读 `os.environ` / `keyring`
- 不写任何文件

违反任一项 → 不通过 Architecture Gate。

## Acceptance criteria

1. AC-1 — 重要角色 + 有 reference asset → `reference_to_video`，`continuity_mode = reference`，`needs_character_reference = true`，`reason_codes` 包含 `IMPORTANT_CHARACTER` 与 `REFERENCE_AVAILABLE`。
2. AC-2 — 重要角色 + 有 previous shot terminal frame + 无 character reference → `first_last_frame_video`（或 `image_to_video`+reference；若实现 `first_last_frame_video` 优先），`needs_terminal_reference = true` 或 `needs_first_frame = true`。
3. AC-3 — 无角色环境镜头（establishing shot） → `text_to_video`，`continuity_mode = none`，`needs_character_reference = false`。
4. AC-4 — 重要角色 + 无 character reference + 无 scene reference + 无 terminal → `blocked` plan；`reason_codes` 必须包含 `MISSING_CHARACTER_REFERENCE` 或 `MISSING_VISUAL_ANCHOR`；**禁止降级到 `text_to_video`**。
5. AC-5 — 重要角色 + 有 reference 但仅换角度（reference continuity）→ `reference_to_video`，`continuity_mode = reference`；**禁止强制 `exact_terminal` chaining**。
6. AC-6 — Plan 是纯函数：相同 `VideoPlanningRequest.content_hash` → 相同 `plan_hash`，callable 两次无差异。
7. AC-7 — `VideoGenerationPlan` 中无任何 forbidden field；pydantic `extra="forbid"` 必须捕获。
8. AC-8 — `VideoPlanner` 不导入任何 production writer / provider / secret。
9. AC-9 — 5 个 AC 全部由 pytest unit test 覆盖；coverage ≥ 95% lines for new module.
10. AC-10 — 调用契约文档（integration.md）至少包含 1 个 Main Agent 调用示例与 1 个 plan JSON 输出示例。

## Verification plan

- Unit tests: `tests/test_planning_video_planner.py`
- Pure-function smoke: 相同 request 两次调用结果 hash 相等
- Architecture gate: 通过 `tests/test_architecture_gate.py` 的 import rules
- Negative tests: 故意构造 forbidden field → `ValidationError`
- Forbidden-call test: monkeypatch 禁止 import，`VideoPlanner` 不触发

## Risk & rollback

- Risk: 与 `ShotVisualResolver` 责任重叠。Mitigation: 本模块输出 `required_*`，Production 仍以 `ShotVisualResolver` 做最终 selection；二者通过 “plan is hint, not binding” 解耦。
- Risk: future evolution 让 `VideoPlanner` 想写 state。Mitigation: AC-10 + Architecture Gate import whitelist。
- Rollback: 删除 `src/ai_video/planning/` 包与对应 tests。无 Production 代码改动；no manifest 写入路径需要回滚。