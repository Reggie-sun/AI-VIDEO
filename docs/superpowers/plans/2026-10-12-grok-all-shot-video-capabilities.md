# Grok All-Shot Video Capabilities Implementation Plan

**Goal:** 扩展 Grok 全部公开视频操作与所有适用 generated-video Shot 路由。

**Spec:** [Grok All-Shot Video Capabilities](../specs/2026-10-12-grok-all-shot-video-capabilities.md)。

**Invariants:** exact profile/input identity、唯一 StateCommitter、总输出时长、one-use permit、
unknown fail closed、zero-extra-cash default blocked、deterministic composition 和旧缺省 hash 保持。

## Major Milestones

### Milestone 1: Model Inventory And Sealed Controls

**Files:** `production/grok_profile.py`、`production/grok_video_controls.py`、
`tests/test_grok_video_capabilities.py`；Parent 修改 `production/video_contracts.py` 的新增 ratio Literal。
实现三个精确模型及所有适用五种模式；profile keyframes/voices 不成为隐藏输入。
定义 legacy-omitting serializer、static C4 exact grammar、model/mode/control bounds 和拒绝证据。

### Milestone 2: Canonical Wire Operations

**Files:** `production/grok.py`、`production/grok_video_request.py`、
`tests/test_production_grok.py`、`tests/test_grok_video_operations.py`。
抽出 payload/input responsibility，新增 edit/extend 固定 paths、exact media supplier、所有图片角色、
reference index/voice/keyframe表达；保留 existing status/download/auth/budget/permit seam。
每 operation 的目标 identity 必须绑定 model + profile + endpoint；total/added duration 不混淆。

### Milestone 3: Shot Integration And Delivery

**Files:** Parent 独占 `tests/test_generation_provider_wiring.py`、必要 leaf Router capability fixes、
policy、matrix、guide、baseline 和同主题 primary session record。
实际 common caller 覆盖所有适用 mode、motion/continuity/商业 Shot；不改 deterministic commercial
lane 或 qualification guards。Native tests → exact staged/range 全部 policy checks → Risk Gate →
必要的 managed review → Parent adjudication → owned commit/push/SHA。
登录/真实 media 不作为本 slice engineering completion 的虚构证据。
Commercial v4 连接涉及现有 `_commercial_video_planning.py`、`_video_requirement_routing.py`、
`_remote_video_native_prompt.py` 与 product-fidelity leaf；使用原 standard project loading/approval/
Planner/Router seam 验证，保留 legacy v3。`video_geometry.py` 与 Grok measurement leaf 在 artifact
落盘和 reader reopening 中执行相同输出验证；C4 exact endpoint 不降级为 nominal。

## Ownership And Execution

已有 development worktree 与 branch 继续使用；原工作区 dirty paths 不接管。
profile/controls worker、adapter/wire worker、Parent integration/docs 的 allowed_paths 完全不相交。
mapping seal 覆盖的 source 在 canonical receipt 检查前冻结，writers 只进入 seal 集合外文件。
任何 scope 调整保留同 task 计数和 exact snapshot，不为未知结果重试。

## Self-Review

Spec 的协议、Shot、授权、compatibility、input、timing、verification 各有对应 owner。
选择 profile hard-control seam 是已有 architecture 的延伸；不引入 speculative generic schema。
Parent 负责最终 diff、风险裁决、完整验证和 publication；workers 不 commit/push 或签 acceptance。
