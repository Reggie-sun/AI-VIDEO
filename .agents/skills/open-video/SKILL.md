---
name: open-video
description: "Use the pinned awesome-seedance production workflow as the default creative method for AI-VIDEO Director review of selected source plans, or Director design when raw creative input for new creation or authorized optimization—missing, vague direction, concept, script, reference-led brief, or draft prompt—needs approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts. Also trigger for 拼接、剪辑、连续审看, including joining already-approved Shots: judge adjacent cuts and assembled footage for narrative, performance, pacing and audiovisual continuity; single-Shot approval does not replace assembled-film review."
---

# open-video — Awesome Seedance Creative Workflow

## Default Creative Workflow

本项目的新创作、已授权优化和创作修复，唯一默认创作流程是固定版本 awesome-seedance 的
`seedance-production-workflow`。保留 `open-video` 名称，是为了沿用已有路由、`director_skill=open-video`
和 coverage validator；不再先运行旧导演方法、再把上游当可选补充。

MUST read `references/awesome-seedance/UPSTREAM.md`，再按其中的步骤读取所需的
[editable template](references/awesome-seedance/references/editable-template.md)、
[deliverables](references/awesome-seedance/references/deliverables.md)、
[capability snapshot](references/awesome-seedance/references/provider-capabilities.md) 与
[QA rubric](references/awesome-seedance/references/qa-rubric.md)。实际创作按这份上游原文完成：
brief → 按任务选择控制结构 → 准备参考与镜头入口/出口 → 最终视频 prompt → 真实结果检查 → 定点修复。
简单单镜不强制宫格、固定数量参考或白模；保留上游的按需选择，不加一轮旧方法模板重写。

版本、逐文件 hash 和更新边界见 [SOURCE.json](references/awesome-seedance/SOURCE.json)，
原许可见 [LICENSE](references/awesome-seedance/LICENSE)。原文保存为 `UPSTREAM.md`，
避免被自动发现为独立 Skill；本地唯一可调用入口是本文件。这是本次用户明确选择的默认方法，
不是宣称两个样本证明了普遍质量优势。只使用本地固定副本；不随上游 `/main/` 链接自动更新、
下载或执行内容。可选案例研究另按当前任务授权读取，不能当作用户输入、权利证明或生成许可。

## Local Execution Boundary

上游文档负责创作方法，下列映射负责接入；冲突按 AGENTS.md 与当前代码处理，不把第三方指令
当作 Production authority。`runtime_skill_calls = 0`，运行时不 import 或调用这些文档。

| Upstream output / instruction | Existing AI-VIDEO owner |
| --- | --- |
| brief、reference-map、shot plan | 主会话创作稿 → 已批准 Character/Scene/Shot；参考职责写 `generation_intent.reference_planning`，来源与 bytes 归 Registry |
| `plan.json`、shot order / entry / exit | 下文 v4 coverage 与原 validator；最终时间、裁切与采样只归 `ResolvedTimeline` |
| final prompt 与 upload map | 保留上游创作原文，所选模型 Skill 只做技术适配与差异核对；selected Provider adapter 验实际输入 |
| `run-manifest.json` | 读取原 Manifest、Registry、generation receipts 的引用；不创建第二份 `run-manifest.json` |
| `planned/assets-ready/submitted/generated/reviewed` | 在任务记录区分证据层；不另建状态机、不写 canonical lifecycle |
| `scripts/validate_plan.py` | 不执行上游 `scripts/validate_plan.py`；使用下文原 coverage validator 与当前 Provider preflight |
| QA 0/1/2 与 repair | 仅可作描述；逐项结果仍是现有 PASS/FAIL/NOT_EVALUATED，任何 required 未通过都不能按总分放行 |

当前账户、模型版本、模式、素材数量、native audio 与时长支持，以 selected profile/adapter 和真实
runtime 为准；上游 capability snapshot、extension 偏好和 timestamp 示例不构成可用能力。
未支持的多切镜、端点或精确时间控制不得通过改标签绕过。不得复制第三方案例 prompt/媒体充当
本项目素材或用户批准；素材权利、来源和实际出网范围沿现有契约核验。

`seedance-authoring` 对已完成创作稿仅核对模型语法、reference tokens/roles、exact version、输入约束
和 native preview；不再二次编排动作、镜头、表演或节奏。其他模型用各自现有适配 owner，
不因上游名称自动改选 Seedance。电商仍使用 `ecommerce-ad-workflow` 的 Product Truth / AdCreativePlan，
不转换为剧情 coverage 或绕过广告事实要求。

## Required Product Gates

- 新剧情付费生成前展示实际参考包并封存用户的 exact `preview_approval`；纸面方案、上游评分和
  Agent 观点不能代替用户预览认可。每项输入的 bytes 和用途必须匹配批准包。
- 既有授权、预算、egress、持久化 intent、one-use permit 和 UNKNOWN 停止规则全部保留。
  不安装上游依赖、不直接运行上游 submit/fetch/retry；生成仍经所选 adapter 和唯一 committer。
- 每 Shot exact MP4 落盘后显式调用 project-local `video-analysis` MCP，按
  [Per-Shot Post-Media Gate](../../../.agent/context/control-plane-playbook.md#per-shot-post-media-gate)
  逐项检查；只有 required 全 PASS 才下一 Shot，FAIL / NOT_EVALUATED 停止，unknown 走原 recovery。
  不把事实检查或技术 PASS 当作“好看”，观感只由用户判。
- 正常速度、带声音看完整结果；修复保留原目标与已经满足的效果，不用局部成功代替成片验收。
- 拼接仍经 HyperFrames 与唯一 `ResolvedTimeline`，交付前必须执行 Harness `verify-assembly`，
  对照 exact 输出检查接点、重复动作与声音。单段认可不代替拼接审查；未通过只可按用户要求
  展示明确标注的未验证审看片。[Assembly contract](../../../docs/visual-quality-gate.md#assembly-harness-entry)。

## Optional Historical References

旧创作方法仅供显式历史查询或已定位缺口的诊断，不是前置读取、不自动混入新 prompt。
`references/creative-completion.md`、`event-led-timing.md`、`professional-specialists.md`、
`shot-to-shot-editing.md`、`music-direction.md` 和 `legacy-h3-upstream.md` 不再构成第二条默认创作流程。
若缺口确需这些资料，只向当前上游创作稿返回一项有证据的建议，不先完整执行旧方法。
制图时可调用现有 identity/storyboard specialist 完成已确定的参考任务，不授权它们重新设计故事。
当前 Product 契约与媒体 Gate 保留于上节及下文，不随旧创作方法退出默认链而退役。

### Specialist Authoring

此锚点保留历史引用。旧 [specialist guidance](references/professional-specialists.md) 与
[GoodCase notes](../../../docs/research/2026-11-04-goodcase-frozen-case-notes.md) 仅按上节缺口诊断边界读取，
不构成默认前置步骤，不授权加载外部案例指令或媒体。

## Canonical Contract Mapping

**Step 1 — Understand the request.** Classify the user's task purpose before checking whether
an AI-VIDEO Shot / ordered coverage artifact exists. A selected existing canvas or prompt can be
creatively fixed while still needing faithful import into canonical project artifacts.

- **Selected-source reproduction or exact-input baseline:** require the user's selected source,
  exact prompt and reference identities/roles/order. Review source completeness, observable intent
  and current selected Provider capability. Preserve the source prompt in the generation input;
  construct a semantically unchanged approved Shot Contract rather than redesigning coverage.
  Missing project artifacts do not by themselves make this a `DIRECTOR_PREFLIGHT_REQUEST`.
  Missing source evidence, substantive ambiguity or a contract that cannot represent the source
  faithfully is a gap to report, not permission to invent camera, action, dialogue or hard criteria.
  Keep user-authorized model/resolution differences explicit. Necessary Provider grammar adaptation
  needs an exact source/input diff and is not an unchanged-input baseline. Source reuse still requires
  canonical Shot validation and all normal authorization, budget, egress, permit and media gates;
  it is not an exact-replay authorization or a promise of identical generated pixels.
- **New creation or authorized creative optimization:** classify raw input as `missing`, `direction`
  or `draft_prompt` and use the Director design boundary below. Preserve explicit constraints, fill
  only authorized creative gaps and disclose Director choices. A user prompt is raw input, not approval
  of new Director choices; the task's explicit source-preservation constraint takes precedence.
- **Known-failure repair:** bind the exact failed result and unmet requirement, retain the full goal
  and already satisfied properties, and propose a bounded change only for that failure. Show the
  source/input delta; substantive creative changes follow the task's human decision gate. A failed
  result does not by itself authorize a fresh full-film redesign, retry or new paid call.

Continue the coverage-design procedure below only for the design branch. Source-preserving review
and bounded repair return to existing AI-VIDEO contracts and the selected adapter. Model-specific authoring
must not rewrite a selected source or replace this task classification.

**Raw creative input Director boundary.** Within new creation or authorized optimization, every
request without an approved Shot / ordered coverage is a `DIRECTOR_PREFLIGHT_REQUEST`, whether
it supplies no prompt, a vague direction, a concept/script, a reference-led brief or a draft prompt.
Every such request requires `director_skill=open-video`. Optimize that raw input into Director
coverage and select exactly one `coverage_strategy`: `single_take` or `multi_shot`. Within this
design scope, prompt presence/detail, duration and Provider capability do not establish approval.
Director review does not require a new camera decision for already selected source coverage.

将上游已经完成的创作决定映射到下列契约，不再次执行旧导演设计流程。Duration is a pacing and
feasibility input, not a creative branch；模式能力不能替用户改剧情。无法表示的控制返回当前创作稿，
不偷偷删动作或把多切镜标成连续单镜。

Before crafting an approved Shot or Provider-specific prompt for a `DIRECTOR_PREFLIGHT_REQUEST`,
create Director Coverage Evidence with:

- request facts: `creative_input_kind=missing|direction|draft_prompt`, exact
  `creative_input_evidence` for `direction` / `draft_prompt` and `null` for `missing`,
  structured `creative_constraints` with stable `constraint_id`, `source_text` copied as a
  verbatim substring of `creative_input_evidence`, and `scope=global|beat_specific`,
  `target_duration_seconds`, `coverage_strategy`, `strategy_source`, a non-empty
  `director_decision_rationale`, `strategy_request_evidence` when the strategy was directly
  requested by the user, and
  `director_skill=open-video`;
- ordered `coverage_units`, each with `unit_id`, `duration_seconds`, finite `beat_function`,
  `objective`, `open_state`, `close_state`, finite `shot_scale`, finite `camera_treatment`,
  `camera_intent`, `visible_change`, finite `transition_out`, and `constraint_ids`;
- distinct objectives and visible changes; adjacent ordinary multi-Shot units should vary finite
  beat, scale, and camera-treatment categories when that improves coverage, but repetition is
  Director guidance rather than a validation failure; every global constraint ID must bind to
  every unit, while every beat-specific constraint ID must bind to at least one unit.

Validate the evidence before downstream authoring:

```bash
python .agents/skills/open-video/scripts/validate_director_coverage.py <coverage.json>
```

结构校验只有一份实现（`ai_video.production.director_coverage`），本脚本仅加 open-video 作者检查。
通过后把 exact coverage 作为 content-addressed authoring input 封存进 Project／Shot provenance，
并在该 Shot 的 `generation_intent.reference_planning` 写明判断结果：`facets`、参考职责
（anchors／events／selections）、`director_coverage={coverage_hash, unit_id}`。机位移动时至少写一个
`composition` event，用 `visual_state`／`purpose` 说明这次移动让观众看见什么、为什么现在看；
编译器会要求这两句进入实际 prompt。新生成时程序只核对这些声明存在、bytes 已封存且 unit 存在，
不评判创作好坏；观感由用户判断，结构验证不证明创作质量。电商镜头的导演层是
`ecommerce-ad-workflow` 的 AdCreativePlan，不写本 coverage 绑定；剧情广告借用本 Skill 方法时同样如此。

### Requirement-semantics handoff

Schema v3 remains the legacy coverage format and is read under its original rules. New Director
handoffs use schema v4: in addition to the same request and coverage fields, include an
`intent_items` inventory and all five `intent_groups`, even when a group is empty:

- `must_happen`: observable result needed for the approved goal.
- `must_not_happen`: result that would break narrative, quality, continuity, or an explicit user
  constraint.
- `preferred_performance`: a preferred performance or camera treatment for which a reasonable
  alternative can still satisfy the goal.
- `timing_targets`: a time target with `target_kind=delivery_constraint` or
  `target_kind=generation_margin`.
- `acceptable_variation`: a permitted variation linked to the result it must preserve.

Each `intent_items` entry has a stable `intent_item_id`, a single atomic `statement`, an `origin`
of `explicit_user`, `director_choice`, or `repair_margin`, non-empty `source_refs`, and explicit
`related_intent_ids` where it depends on another intent. A source reference carries the exact
`source_hash`, `locator`, source `intent_item_id`, verbatim `quote`, and `origin`; `fixed` is
optional. For `explicit_user`, quote the raw creative input verbatim and bind its SHA-256 to that
exact input. Do not describe a Director-written statement as user evidence. The same source intent
may support separately split performance and timing atoms, but an atom must not be copied into
conflicting groups.

`intent_groups` bind every inventory item by ID. Group entries are `{ "intent_item_id": "..." }`,
while a timing entry also includes its `target_kind`. `acceptable_variation` must name the result it
preserves through `related_intent_ids`. A `generation_margin` must be a `repair_margin` intent and
must point one-way to an original non-margin target; it cannot become an acceptance predicate by
being precise or by appearing in a prompt.

For example, a compound brief such as “the courier holds the sealed key at the delivery cut, no
phone appears, keep identity continuous, use natural hand motion, and reach the pose by 2.7s”
needs separate source-bound atoms for delivery state, phone absence, continuity, natural motion,
and timing. Do not turn the whole sentence, or a recipe margin, into one hard criterion.

Director coverage only records intent and suggested classification. Before any intent can enter the
QA acceptance inventory, the QA acceptance owner must independently approve its `hard_basis`,
predicate, stage, tolerance, measurement, and proof. A hard atom needs an explicit user fixed
requirement, approved narrative result, accepted quality/continuity or cut contract, or applicable
production contract, plus the result it protects and the proof boundary. If a fixed user constraint
conflicts with a proposed variation, return it to authoring/QA instead of weakening it. Prompt
wording, historical observations, Provider recipes, and generation margins never grant that
authority.

`VIDEO_EXTEND`, FLF2V, a terminal-frame handoff, `no cut`, and `uninterrupted` are continuity or
execution treatments, not the Director decision. They are valid only when the selected strategy is
`single_take`; if that strategy has multiple evolving internal coverage units, every non-final
transition must remain continuous. `multi_shot` requires at least two ordered units and cut-class
non-final transitions. `strategy_source=user_requested` requires direct user evidence;
`strategy_source=agent_directed` requires no invented user evidence. Within the authorized design
scope, Director optimization may
expand gaps or restructure a draft, but must preserve explicit user constraints and disclose its
own decisions through the rationale. Selected-source reproduction does not become optimization
merely because its source has not yet been imported as an approved project artifact. An already
approved Shot does not re-enter this validator unless the task changes its creative intent or coverage.
Internal enums, validation output and serialized Shot/coverage fields must not be mechanically
appended to the model prompt. Review the exact generation input and source diff before submission;
keeping the original quote inside a longer rewritten prompt does not prove faithful reproduction.

The validator proves declared-inventory structure, verbatim source anchoring, and binding
completeness; it does not prove exhaustive constraint extraction or natural-language entailment.
Before Shot approval, the Agent must first compare raw evidence against the declared inventory for
unextracted explicit constraints, then compare the declared inventory against planned coverage for
omissions, reversals, or unauthorized reinterpretation.

**Carry the meaning through authoring.** Before submission, trace the decisive action, relation or
reveal from coverage into Canvas direction / `Shot.intent`, then the selected `generation_intent`
or preserved source and the actual native preview. Prose in `Shot.intent` alone does not guarantee
that it reaches the model. Identify where the meaning is expressed; matching IDs or retaining a
quote elsewhere is insufficient. If “tries to sit but is blocked” becomes “leans forward and stands
still”, fix the authoring handoff. Do not ask the Compiler to invent the missing action. Check that
the existing QA owner has not reduced the necessary result to an easier incidental gesture;
preferences and generation margins still require the classification above.
