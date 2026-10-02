# Full Continuity Capability Honesty Implementation Plan

## Goal

在 ProviderBoundVideoRequest 创建前阻止 FULL edge 退化到 soft Ref2VA，接通现有 C2/I2V。

## Scope And Contract Surfaces

绑定 [Spec](../specs/2026-10-03-full-continuity-capability-honesty.md)。Parent 是唯一 writer；
在当前 main 串行实施。保持现有 public schema、serialization/hash、Provider 能力、
Registry/Manifest/committer、历史 evidence 和 unknown-outcome guards。

## Current And Target Behavior

显式 FULL same-stack 请求目前会走到 soft selected 并被末端 lifecycle validator 拒绝；readiness 的 NONE
会跳过 policy。修复后 FULL 无真实首帧/派生 keyframe conditioning 即阻断。
兼容 C2 复用 HardCutKeyframeBinding，交给原 compiler/lifecycle seam；不自动改 Provider。
没有 typed edge 的 independent Ref2VA 保持合法，不能用 prompt 推断 continuity truth。

## File Ownership

| File | Responsibility |
| --- | --- |
| src/ai_video/production/_video_intent_validation.py | 共用 v2 target/causal consistency 和 readiness obligation 检查 |
| src/ai_video/quality_gates/shot_readiness_gate.py | 显式 policy 始终验证 |
| src/ai_video/production/_video_requirement_routing.py | universal FULL conditioning gate、exact C2 lineage |
| src/ai_video/production/shot_router.py | 原两个 apply call sites 传入 lifecycle |
| src/ai_video/planning/_asset_readiness.py | 复用既有目标 Shot 首帧的精确绑定判定 |
| src/ai_video/planning/video_planner.py | angle change 首帧进入现有 I2V 分支 |
| tests/test_production_shot_router.py | same-stack METASO/causal/C2 regression |
| tests/test_shot_readiness_gate.py | NONE downgrade、义务不匹配及标准 C2 Planner/readiness regression |
| docs/v0.2-runtime-baseline.md | 当前实现边界短条目 |
| docs/record_for_agent/2026-10-03-full-continuity-capability-root-cause.md | 实际结果与证据分层 |

## Major Milestones

### 1. Reproduce And Bind The Existing Contract

添加真 METASO capability 的离线 fixture：canonical image 代表旧状态，source close 为
C detached/floor/release completed/moving right；HARD_CUT/FULL/DIRECT 与完整 v2 causality。
先证明 same-stack soft route 和显式 policy/NONE 检查缺口。补回 identity/reset 正向 controls。

### 2. Close Existing Validation Gaps

复用 causal validator，Router 验证 v2 target intent 与 carry；readiness 检查显式 policy，
按 policy version 验证，保留 legacy v1 readiness；原 `/4` continuity 仍要求 v2。
不新增 continuity owner。FULL 首帧条件应用于所有 stacks，复用现有 reason code。
合法 C4 grammar、exact terminal I2V 不变；不修改 ProviderNative capability 描述。

### 3. Reuse C2 And Complete Verification

只在 HARD_CUT/FULL + 现有 binding 精确匹配时允许派生 first_frame/I2V。
该 C2 lane 使用 `REFERENCE`；EXACT_TERMINAL 不可重绘首帧。
测试 mutated target/keyframe/terminal metadata 和 continuous-take misuse 均阻断。
将非 Commercial、非 semantic-jump 的 angle change + 单 FIRST_FRAME 请求纳入现有首帧分支，
保留当前 Shot owner/hash/role guards；通过标准当前计划校验验证 REFERENCE + I2V。
不扩展到 angle change first/last 双帧、不从粗粒度 flags 推断 FULL policy。
运行 focused suites、changed-path Harness、同 snapshot 双独立 read-only review。
按 findings 做有界修复和必要复核，最终 exact-owned paths commit，不 push。

## Verification

`python -m pytest tests/test_production_shot_router.py tests/test_shot_readiness_gate.py
tests/test_production_video_transition.py tests/test_production_metaso_h3.py
tests/test_planning_video_planner.py tests/test_production_video.py
tests/test_production_comfy_video.py tests/test_production_local_h3_provider_family.py -q`。
其后 `make harness-inspect` 按 exact staged snapshot 执行 policy；不跑 live experiment。

## Self Review And Limitations

P0/P1/P2、七项回归及 evidence mismatch 均有明确 owner/seam。已有软 Ref2VA 功能、multiple
views 和旧 hashes 保持；媒体 state correctness 仍要逐 Shot exact-media gate 验证。
Planner coarse flags 不承载完整 policy，标准 handoff 必须显式传入 policy；本 slice 不做
默认 inference 或新的状态 owner。真实 H3 A/B 需后续另行授权，离线 PASS 不代替它。
