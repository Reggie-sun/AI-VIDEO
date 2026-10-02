# Full Continuity Capability Honesty

## Goal And Authority

基于 `b16ec55` 修复已声明 `FULL_CONTINUITY` 的 Shot edge 在 submit 前的语义退化。
用户授权离线分析、最小实现、测试和本地 commit；禁止真实 credential、Provider 请求、
远程生成、push、release/deploy。Parent self-review 后执行，无新增用户 approval gate。

## Root Cause

### A. Exact Execution Path

当前 HEAD `b16ec55` 是 replay evidence 文档；`b2ba4b3` 是原画布重试记录；
`bd30c787` 记录 cut repair/raw failures；`e62a0db7` 保留 multiple reference views。
后者没有引入 first-frame conditioning。

`runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/prepare.py:101-150`
构建 rich intent，再调用 `VideoPlanner.plan()`、`require_current_video_plan()` 和
`require_feedback_context()`，后续 canonical generation/paid seam 消费 execution binding。
该脚本是历史 local evidence，本任务不修改或执行它。

### B. Values At Each Boundary

| Layer | Actual S03 Value |
| --- | --- |
| Authoring | open text 声明 C 已解除/留在地上、继续向右；无 typed pairwise policy |
| Planning request | `previous_shot_state=None`，semantic roles 为 identity/scene/video_reference |
| Planner | `_decide_continuity()` 返回 `NONE` |
| Neutral requirement | `/4`，`REFERENCE_TO_VIDEO`，`continuity_mode=none` |
| CapabilityNeed | needs_first_frame/last_frame/terminal_reference/continuity_state 全为 false |
| Readiness | 无 policy，v1 readiness；NONE 跳过 causal validation |
| Router context | upstream_terminal/semantic_continuity_state 均为 null；continuity_mode=none |
| Execution binding | continuity_routing=null；GENERATE_ONCE；routing selected |
| Native request | 3 reference_image + 1 reference_video + text，无 first/last frame |

这些值来自实际 `shot03/planning.json`、`plan.json`、`execution-binding.json`，
不是由 prompt 推断 Provider capability。

### C. Semantic Degradation

第一次缺失发生于实验 authoring→planning：故事状态被写成 text/普通软视频 reference，
没有 distinct source/target Shot edge、previous state 或 `ContinuityTransitionPolicy v2`。
`VideoPlanner._decide_continuity` (`src/ai_video/planning/video_planner.py:61`) 只消费
coarse previous flags；`require_current_video_plan:834` 的 policy 是单独显式输入。
不能从 prompt 或仅有 reference_video 推断 FULL，否则会误封合法 Ref2VA。

另有两个 source-level gaps：`ShotReadinessGate.evaluate` 仅在 `/4 + mode!=NONE`
时检查 policy；`_video_requirement_routing.apply_continuity_transition` 仅在跨
execution stack 的 FULL edge 检查精确首帧，same-stack 缺少同一规则。Router 也未复用
readiness 的 v2 target intent/carry 校验。
离线复现进一步确认：same-stack FULL+软 reference 虽然走到 selected，末端
`ProviderBoundVideoRequest` 的 lifecycle validator 已因首帧不匹配拒绝，不能声称旧代码
一定可提交。P0 把它前移为稳定 capability blocked result；实验绕过的主要原因仍是未建 edge。

### D. Capability Honesty

`MetasoH3VideoProvider.capabilities` (`src/ai_video/production/metaso_h3.py:120`)
只声明 Ref2VA、allowed_image_roles=reference、required_first_frame=false。
reference_video 是软参考，不是 extension/exact first frame。四种 policy anchors
是 edge 的输入/证据集合；不意味着每个 I2V request 必须把四者全部直接提交。
C4 multi-anchor lane 的 complete grammar 仍按原专用 gate 验证。

### E. Existing Owners

`ContinuityTransitionPolicy` 已支持 HARD_CUT/FULL/DIRECT、四个 anchors 和 causal dimensions。
本案例 character_presence/prop_identity/prop_holder/prop_functional_state/action_phase/
screen_motion_axis 应为 CARRY：C detached、holder=floor、release completed、moving right。
其他 dimensions 仍依原 v2 完整校验，不弱化为仅六项。

`HardCutKeyframeBinding` (`production/_video_continuity.py:631`) 已封存 previous terminal、
distinct derived keyframe、target、constraints 和 image request/provenance。
`validate_hard_cut_keyframe_binding_against_project:684` 已验证 activated image attempt 和
canonical character/scene lineage；标准 video request/committer 保持这项验证。
local H3 `ComfyUIVideoProvider.capabilities:577` 已声明 FL2VA first/last-frame；其他现有
H3 I2VA lane 也维持原能力。复用 binding/首帧，不新增 pipeline 或自动 fallback。

### F. Evidence Boundary

S03 generation reference 为 S02 edited.mp4 的 7.25–11.25s；最终 review 用
S02 edited-v2.mp4 至 frame250 exclusive=10.4167s，S03 从 raw3s 开始。
该边界不是同一个 exact boundary。保留 S03 raw FAIL/OPENING_STATE_RESET 与
edited limited visual PASS 分层；不修改历史结论。

## Minimal Repair Contract

1. 每条 FULL edge 都必须通过 Provider conditioning gate，复用
   `BLOCKED_CAPABILITY / CONTINUITY_FRAME_CONDITIONING_REQUIRED`，失败不产生 bound request。
2. 明确传入 readiness 的 policy 不得因 NONE 或旧 requirement version 被忽略。
   FULL 必须具备中立 I2V/FL conditioning evidence；reset 仍允许 NONE。
   v1 policy 保留 legacy requirement 的 target/obligation 校验，不要求契约不存在的 causal
   fields；原 `/4 + mode!=NONE` 的 v2 causality 要求不放宽。
3. Router 验证 v2 target intent hash、完整 causal dimensions 和 CARRY equality，
   不用 prompt 当 typed truth。旧 v1 serialization/hash 不变。
4. HARD_CUT/FULL 可以复用 distinct derived keyframe 首帧：必须提供现有
   HardCutKeyframeBinding，与当前 target、upstream terminal、keyframe bytes/metadata 精确一致。
   C2 使用 `REFERENCE` continuity mode；`EXACT_TERMINAL` 仍只能使用原末帧，不允许派生图替代。
   continuous take 不可走 derived-keyframe。最终 canonical activation/QA owner 不变。
5. 非 Commercial 的 AUTO + FIRST_FRAME 换机位请求复用现有 Shot-bound first-frame 分支：
   previous state 必须为 angle change 且非 semantic jump；首帧仍精确绑定当前 Shot/hash/role。
   标准 `VideoPlanner.plan → require_current_video_plan` 生成 REFERENCE + I2V，并显式验证 FULL
   policy；不将普通 VIDEO_REFERENCE 改作 first_frame，不扩展该 C2 lane 到 first/last 双帧。

## Scope And Non-Goals

生产修改限定现有 causal validator、readiness gate、requirement routing、Router call sites，
以及 Planner/asset-readiness 的既有首帧分支。
不新增 GenerationUnit/StateContract/ContinuityGroup/NarrativeState；不改 schema、hash 公式、
METASO capability、credential/transport/paid lifecycle、历史 runs/records、composition 或 media。
不重做 Planner：未声明 edge 的 NONE 不能自动升级；此限制必须报告。

## Acceptance And Review

回归证明 FULL+soft-only Ref2VA blocked；identity carryover/scene reset METASO 可 route；
exact terminal I2V 与 hard-cut derived-keyframe I2V 可 route；causal mismatch blocked；
标准换机位 first_frame handoff 对 legacy/rich intent 均可达，错误 asset owner/hash/role binding
和无 terminal 的 continuous-take 请求仍阻断；
旧 hash/serialization 和 multiple views 不回退。focused suites + exact staged Harness。
本任务触及 capability/readiness gate，按仓库 T3 在同一稳定 snapshot 做双独立只读 review；
远程 Kimi 被当前禁 credential/paid request 约束排除，使用 Native profiles，不声称 Kimi receipt。
工程结果不构成 H3 媒体质量或 Production qualification。

## Self Review

现有 owners 可以表达要求；四锚点、C4 与 C2 的职责分开，未将软参考改名为精确首帧。
修复针对显式 obligation 和具体遗漏的 validation，不通过 prose heuristics 猜状态。
