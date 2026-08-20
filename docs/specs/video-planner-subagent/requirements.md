# Video Planner Subagent — Requirements

Status: proposed v2 (contract repaired; runtime implementation pending)
Owner: AI-VIDEO planning intelligence layer
Target module path: `src/ai_video/planning/`

## Context

AI-VIDEO 已有 canonical owners：`ProductionProject` owns Character / Scene / Shot，Asset Registry owns identity/provenance，Production Manifest 与 `ProductionStateCommitter` own durable lifecycle，`ResolvedTimeline` owns timing，HyperFrames owns default composition execution，Provider adapters own provider-specific execution，Review / Repair 与 human Pilot Gate own quality acceptance。

`VideoPlanner` 只补一个前置问题：

> 当前 Shot 的语义意图、连续性与动作需求，是否和声明的视觉策略一致；若一致，后续 Production 应要求什么 strategy/capability/assets？

旧版 contract 无法阻止 static-first：它把 `Shot.visual_strategy` 当成已验证事实，形成 `STATIC_IMAGE -> MotionRequirement.NONE -> STATIC_IMAGE -> confidence=1.0` 的自证循环；`STATIC_IMAGE` 还不要求 final visual asset。bootstrap 若先把动作 Shot 写成 static，planner 会认证错误而不是发现错误。旧 integration 又把 planner/router bridge 延期，使 `BLOCKED` 没有 Main Agent executable STOP seam。

## Who is affected

| Role | Contract after this slice |
|---|---|
| Main Agent | 为每个准备生成/组合的 Shot 构造 current request，消费 plan，并执行 STOP semantics |
| VideoPlanner | 纯函数地审查 intent/strategy coherence，提出 provider-neutral strategy，声明 required assets/review warnings |
| Production | 只接收通过 preflight 的 proposal；继续拥有 Provider/Asset execution、composition 与 durable state |
| Review / human Pilot | 检测重复、长静止区间、frame diversity、完整观看与最终作品质量；不下放给 planner |
| External Skills | 仅提供 Shot/motion advisory；不拥有 Shot、Asset、Review 或 plan lifecycle |

## What this slice must deliver

1. `VideoPlanner.plan(VideoPlanningRequest) -> VideoGenerationPlan`，provider-neutral、pure、no IO。
2. 对 current Shot intent、open/close state projection、motion directives、continuity constraints 与 declared strategy 做 coherence preflight。
3. 明确区分 Reference Asset 与 Final Shot Visual；static/image-motion 不得在缺少合格 final visual 时继续。
4. `ProductionPolicyInput.accept_static_image_fallback` 必须真实参与决策。
5. 保留 `PlanOutcome.PROPOSED | BLOCKED` 两态，用 typed `ReasonCode` / `PlanWarning` 表达 mismatch、fallback 与 human review。
6. 定义 Main Agent 侧最小 executable consumer/STOP seam；不让 Production module 反向 import planner。
7. 保留 AC-1～AC-10，并加入真实 static-first incident regressions。

## Explicitly out of scope

- final visual repetition detection、长时间 frame diversity 或 long-static-region analysis；
- 30～60 秒 Pilot Reality Gate、human full-watch、Final Acceptance；
- multi-Shot aggregate planning；
- Provider selection/ranking/fallback、H3 whitelist、Provider/model prompt adaptation；
- Provider 调用、上传/下载、secret、budget/permit execution；
- Manifest / Registry lifecycle、new schema、new durable approval store；
- timeline、render、composition implementation、automatic repair/retry/fallback；
- `ShotVisualResolver` / `VideoGenerationResolver` / HyperFrames 重构；
- Studio UI、LoRA、LangGraph/MCP runtime。

## Functional requirements

### FR-1 — Plan-only output

`VideoGenerationPlan` 只描述 proposal，不描述 selected Provider 或 durable lifecycle。至少包含 sealed `source_request_content_hash`、target Shot identity/revision/content hash、`generation_mode`、`continuity_mode`、`motion_requirement`、`required_asset_roles`、capability requirements、typed reasons/warnings、confidence、outcome、rationale 与 sealed `plan_hash`。

Forbidden fields 包括 Provider/profile/selected capability、Manifest revision、timeline position、artifact path、output asset、Review acceptance、activation/lock/final-acceptance state。

### FR-2 — Pure determinism

- 相同 sealed semantic request 必须产生相同 plan payload/hash；diagnostic `request_id` 明确排除在 semantic request hash 之外。
- planner 不读取 filesystem、network、secret、clock、Manifest 或 Registry。
- `available_assets`、intent evidence 与 approval/reuse evidence 只作为 Main Agent 提供的 immutable request projection；planner 不持久化它们。

### FR-3 — Continuity decision is required

所有 plan 都必须明确 `continuity_mode`：

| Mode | Semantics |
|---|---|
| `exact_terminal` | 同一动作继续，必须使用真实 upstream terminal evidence |
| `reference` | 换角度但保持角色/场景/状态；reference 仅作 guidance |
| `semantic` | 时间、场景或状态语义发生跳变 |
| `none` | 首 Shot、独立 Shot 或 explicit reset |

`reference` 不能被解释为 `needs_terminal_reference=true`；只有 `exact_terminal` 需要 terminal。

### FR-4 — Motion requirement comes from intent evidence

至少支持 `none`、`light_transform`、`graphic`、`character_action`、`free_complex`、`hero_or_repair`。

Motion classification 的证据优先级：

1. Main Agent 从 approved Shot/Storyboard/continuity/open-close state 投影出的 typed `ShotIntentEvidence`；
2. `Shot.motion_directives` 与现有 typed continuity constraints；
3. `Shot.visual_strategy`，仅作为需要审查的 declared strategy；
4. `Shot.intent` natural language 只可触发 “evidence unresolved / human review”，不得靠关键词直接选择 static/dynamic mode。

存在 character action、continuous action、空间移动、明确 subject animation directive，或 open/close state 必须发生视觉变化时，motion requirement 不能是 `none`。只有 `pan` / `zoom` / `parallax` / `zoompan` 这类 camera/image transform 不等于角色或主体动作。

### FR-5 — Intent and strategy coherence

- `STATIC_IMAGE` / camera-only `IMAGE_MOTION` 与 required character/continuous/spatial/state-changing action 冲突时，必须给出 typed mismatch；默认 `BLOCKED` + `REQUIRES_HUMAN_REVIEW`。
- 不能先由 `visual_strategy` 推导 motion，再用 motion 证明原 strategy。
- intentional static 仍可用，但必须有 explicit director/static rationale、合格 Final Shot Visual、可审计 reason，以及需要时的 current human review evidence。
- mismatch/fallback path 不得获得无条件 `confidence=1.0`。

### FR-6 — Reference Asset is not Final Shot Visual

定义：

- `Reference Asset`：提供 Character、Scene、state、identity、space、style 或 continuity guidance。
- `Final Shot Visual`：观众最终看到的、绑定 target Shot visual intent 的 Shot-specific visual，或被明确批准复用到该 Shot 的 plate。

`CHARACTER_REFERENCE` / `SCENE_REFERENCE` 永远不能单独满足 final visual readiness。

static/image-motion plan 至少要求二者之一：

1. `APPROVED_KEYFRAME`：`canonical_owner_id == target_shot.shot_id`，且 exact asset id 被 target Shot 的 canonical final-visual `required_asset_roles` 绑定；或
2. `APPROVED_REUSABLE_PLATE`：exact asset id 同样被 target Shot final-visual role 显式绑定，并有 current AI-VIDEO Review/director reuse rationale projection。

Planner-local role 只描述 request snapshot，不新增 Manifest/Registry/schema 或第二套 approval truth。

### FR-7 — Static fallback policy is executable

- `accept_static_image_fallback=False`：动作 Shot 不得降级到 `STATIC_IMAGE` 或 camera-only `IMAGE_MOTION`；返回 `BLOCKED`。
- `accept_static_image_fallback=True`：只有同时存在 explicit fallback/director rationale、合格 Final Shot Visual、typed fallback reason/warning 与 current human review evidence，才可返回 `PROPOSED`。
- fallback `PROPOSED` 仍不是 creative PASS；缺任一 evidence 必须 `BLOCKED`。
- planner 不自动修改 Shot strategy，不执行 fallback，不生成 placeholder。

### FR-8 — Required capability, not selected capability

`CapabilityRequirements` 只能描述 required capability，例如 references、first/last frame、continuity state、local/remote eligibility；不能包含 Provider 名、model id、selected profile、ranking 或 fallback chain。

### FR-9 — Reasons, warnings, and confidence are auditable

至少支持这些新增 typed values：

- reasons: `ACTION_INTENT_REQUIRED`、`STRATEGY_MOTION_MISMATCH`、`CAMERA_MOTION_ONLY`、`FINAL_SHOT_VISUAL_REQUIRED`、`FINAL_SHOT_VISUAL_AVAILABLE`、`REUSABLE_PLATE_APPROVED`、`INTENTIONAL_STATIC`、`STATIC_FALLBACK_ACCEPTED`；
- warnings: `FINAL_SHOT_VISUAL_MISSING`、`CAMERA_MOTION_NOT_SUBJECT_MOTION`、`STATIC_FALLBACK_REQUIRES_REVIEW`、`REQUIRES_HUMAN_REVIEW`。

保留 v1 identity/continuity/reference/missing-anchor reason/warning。每个 plan 至少一个 reason。`confidence` 必须在 `[0,1]`，但 confidence 不能取消 typed STOP/review requirement。

### FR-10 — Inputs reuse AI-VIDEO truth

`VideoPlanningRequest` 复用现有 `Shot`、`Character`、`Scene`、`AssetType`、`AssetRoleRequirement` 语义，不建立新的 Story/Character/Scene/Shot schema。

`ShotIntentEvidence` 只能是 sealed ephemeral projection，引用 current Shot identity/hash，并表达诸如 `character_action_required`、`continuous_action_required`、`spatial_change_required`、`state_change_required`、open/close state evidence refs。它不拥有或改写 canonical creative intent。

### FR-11 — Production ownership boundary

Planner 不 import Production writer/Manifest/Registry/dependency/composition/hyperframes/Provider/secret，不读写文件，不选择 Provider，不生成 media，不写 Review acceptance。

### FR-12 — Mandatory current-plan preflight

每个准备进入 Provider/Asset execution 或 composition 的 Shot 必须先经过 Main Agent consumer：

1. Main Agent 从 current canonical Shot、asset binding、Review decision 与 policy 重新构造 sealed current request；plan 的 `source_request_content_hash` 必须与之完全一致；
2. plan target Shot id/revision/content hash 与 current Shot 完全一致；
3. `BLOCKED` → STOP；
4. required assets 缺失、owner/binding不匹配 → STOP；
5. unresolved `REQUIRES_HUMAN_REVIEW` → STOP；
6. STOP 后 router、Provider、placeholder/materializer、composition/render 调用次数必须为 0。

consumer 属于 Main Agent/run preflight，不由 Production module import planner。durable state 继续交给既有 owner。

### FR-13 — `PROPOSED` has narrow semantics

`PROPOSED` 只表示 strategy proposal 已通过当前 planner checks，可进入既有 Production gates。它不表示 generated、reviewed、selected、locked、activated、human creative PASS 或 Final Acceptance。

### FR-14 — Downstream quality ownership remains unchanged

正确路由为：

```text
VideoPlanner per-Shot preflight
  -> AI-VIDEO Provider / Asset execution
  -> Composition
  -> Review
  -> human Pilot Reality Gate
```

跨 Shot repetition、长静止区间、frame diversity、full-watch 与 final quality 由 Review/Pilot 负责，不能塞入 single-Shot planner。

## Acceptance criteria

1. AC-1 — 重要角色 + character/scene references + coherent generated-video intent + reference continuity → `REFERENCE_TO_VIDEO` proposal；`continuity_mode=REFERENCE`，reference capability/reasons 正确。
2. AC-2 — exact same-action continuation + previous terminal + 无 character reference → `IMAGE_TO_VIDEO` 或 `FIRST_LAST_FRAME_VIDEO`；terminal/first-frame capability 正确。
3. AC-3 — 无角色且无 explicit action/motion requirement 的 establishing Shot → `TEXT_TO_VIDEO`、continuity `NONE`。
4. AC-4 — 重要角色且无 character/scene/terminal visual anchor → `BLOCKED`；禁止 silent T2V downgrade。
5. AC-5 — 换角度的 reference continuity → `REFERENCE_TO_VIDEO`；禁止强制 `EXACT_TERMINAL`，`needs_terminal_reference=false`。
6. AC-6 — 相同 sealed request 两次 plan payload/hash 完全相同。
7. AC-7 — forbidden fields 由 `extra="forbid"` 捕获。
8. AC-8 — planner 无 Production writer / Provider / secret / IO imports。
9. AC-9 — AC-1～AC-18 全部有 executable pytest coverage；new planning module line coverage target ≥95%。
10. AC-10 — `integration.md` 至少包含 current-plan Main Agent consumer、plan JSON、STOP example 与 downstream route。
11. AC-11 — character-action Shot 被 bootstrap 为 `STATIC_IMAGE` 时，返回 `BLOCKED`/review mismatch；不得返回高置信度 static proposal。
12. AC-12 — action Shot 只有 `pan`/`zoom`/`zoompan`/`parallax` directive 时，记录 camera-only mismatch；不得把它当真实 character motion。
13. AC-13 — `accept_static_image_fallback=False` 时禁止 action Shot static/image-motion downgrade。
14. AC-14 — Character/Scene reference 不得满足 Final Shot Visual/keyframe requirement。
15. AC-15 — intentional static Shot 有 approved Shot-specific keyframe、explicit director rationale 且无 action mismatch时可 `PROPOSED`。
16. AC-16 — `accept_static_image_fallback=True` 的动作 fallback 只有在 final visual、rationale、current review evidence齐全时可 `PROPOSED`，并必须带 fallback reason/warning；否则 `BLOCKED`。
17. AC-17 — Main Agent consumer 收到 `BLOCKED`、missing required assets、stale Shot id/revision/hash、stale source request（含 Review/policy/asset binding change）或 unresolved review warning 时 STOP；router/Provider/placeholder-materializer/composition/render spies 均为 0 calls。
18. AC-18 — `PROPOSED` 不等于 human creative PASS、Review acceptance、activation 或 Final Acceptance；integration/test 必须明确断言。

## Verification plan

- RED-first unit/contract/integration tests：见 `test-spec.md`。
- Architecture gate：planning import blacklist + Production 不反向 import planning。
- Determinism：相同 sealed request 两次结果/hash相同。
- STOP spies：blocked path 后 router/Provider/placeholder-materializer/composition/render 均未调用。
- Policy-routed validation：对 exact staged snapshot 运行 `.agent/harness/policy.yaml` 要求的 checks。

## Risk & rollback

- Risk: planner 与 Router 重叠。Mitigation: planner 只提 required strategy；Main Agent preflight owns STOP consumption，Production 继续选择 exact capability。
- Risk: ephemeral approval projection 被误当 durable truth。Mitigation: plan 不存 receipt/activation/Review state；每次都绑定 current Shot/hash并由 canonical owner重新提供。
- Risk: static fallback 变成自动 fallback。Mitigation: false 默认、true 仍需 final asset+rationale+review evidence，且无 planner-side mutation/execution。
- Rollback: 未来实现可删除 `src/ai_video/planning/` 与 tests，不涉及 Production schema/Manifest migration。
