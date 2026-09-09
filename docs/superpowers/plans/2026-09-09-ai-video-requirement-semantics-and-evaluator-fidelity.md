---
surface_id: requirement_semantics_and_evaluator_fidelity_plan
canonical: false
plan_status: proposed
implementation_status: not_started
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
---

# Requirement Semantics And Evaluator Fidelity Implementation Plan

Date: 2026-09-09

## Goal And Authority

实现 [Requirement Semantics And Evaluator Fidelity Spec](../specs/2026-09-09-ai-video-requirement-semantics-and-evaluator-fidelity.md)
的通用契约：必要结果、质量底线、导演偏好、诊断观察和生产约束产生不同运行后果，
使 evaluator 忠于 selected QA，保留旧历史与 Final-output/no-regression。

用户本轮“写 plan”只授权编写本计划和更新同题记录；不授权执行下列 implementation tasks。
当前不修改 Spec、代码、QA 或真实 Production state，不调用 Provider、不生成或派生媒体，
不 stage、commit、push 或创建 worktree。Spec 仍为 proposed，implementation 尚未开始。
后续实施范围为离线工程契约与 development shadow replay；不包含真实 S01 policy adoption。

本计划引用 Spec 的规则与 AC 编号，不建立第二份可独立修改的语义规范。
Spec 决定 what/why，本计划只决定 implementation sequence、owner、验证与退出条件。

## Baseline And Change Boundary

基线为 HEAD `c55bfc3400d4aac95dda43da564fac9f4d1de555` 加当前 working-tree changes。
规划开始时已有 17 个 dirty/untracked 文件，其中包括本题 Spec/记录以及独立的
recovery/admission、Harness、runtime 文档与测试工作。后续写入前必须重新核对 ownership；
不得覆盖或将这些 changes 算成本题实现。

| Concern | Current Owner / Entry | Required Change Boundary |
| --- | --- | --- |
| Director handoff | `.agents/skills/open-video/SKILL.md`、`scripts/validate_director_coverage.py` | 在原 handoff 增加可辨后续版本，保留 v3 读取，不成为 runtime import |
| QA semantics | `production/domain_acceptance.py`、`generation_recipe.py` | 单一 inventory、marker、source metadata、compound atoms 与按 level 的 compiler coverage |
| Raw evaluator | `production/generation_evaluation.py`、`ai_video_mcp/generation_feedback.py` | QA-derived item、source /2、实际 presentation/answer 绑定、typed time measurement |
| Evidence projection | `production/generation_feedback.py::record_attempt_evaluation` | source → Findings / unresolved refs 的唯一可复核投影 |
| Durable evidence | `_state_commit_generation_feedback.py`、`_generation_feedback_reader.py` | 原 committer/reader 持久化与重开；不增加 writer 或 Manifest lifecycle |
| Diagnosis and statistics | `generation_diagnosis.py`、`generation_experience.py`、`generation_decision.py` | 区分 QUALITY_FAILURE、EVIDENCE_GAP、rubric conflict 与 advisory |
| History import | `generation_history_import.py` 与现有 import reader | 保留旧资格、attribution、原 QA 和 hash；不增加 retrospective proof 权限 |
| Final output | `final_output_contracts.py`、`final_output_review.py` 与既有 repair owner | 保持全部底线；新 raw /2 不替代 Final Acceptance |
| Production method | `planning/production_strategy.py::ProductionStrategyResolver` | 消费原 authoring/QA，不重新分类、不增加 sampling policy |
| Engineering verification | `.agent/harness/policy.yaml`、contract matrix | 路由真实 changed paths 和新增测试，不新增 Harness subsystem |

上表 `production/` 为 `src/ai_video/production/`，MCP 路径位于 `src/ai_video_mcp/`。
Skill 行的 script 相对 `.agents/skills/open-video/`；详细 owner 继续由
[contract matrix](../../agent-primary-contract-matrix.md) 独占。

### Paths To Replace And Paths To Preserve

在 **marked QA 新记录** 中替换：自由拼接 question/criterion、无语义检查地 flatten source、
任意 human hint FAIL 的兜底、把所有 raw level 强制投进 prompt 的检查。
旧 unmarked QA + /1 的 exact replay 保留原路径及原 verdict；以 selected QA version
分流，不能加 caller flag 选择较宽旧模式。

不修改历史 Gate/run scripts 以使其产生新 verdict，不让它们成为 /2 的准入旁路。
不修改真实 S01 authoring/QA/Manifest，不恢复 attempt12，不替 attempt13 补 human proof。
既有 admission/regression slice、VIDEO_EDIT 和实际媒体修复不在本计划实现范围。

## Dependency Order

`T1 → T2 → T4 → T5 → T6 → T7 → T8`，另有 `T2 → T3 → T7`。
默认由一个 writer 串行推进；T3 的 Agent-side 文件虽可独立划界，也不要求并行或 worktree。
每个任务先覆盖真实失败模式，再实现最小行为，最后运行其 focused tests。
T1 的 legacy baseline 应先 PASS；面向新行为的 regression 应先 RED，不能更新旧 golden 值掩盖差异。

所有任务当前均为 `not_started`。中间 schema/unit test PASS 不产生新 QA qualification；
marked runtime 路径必须完成 T2/T4/T5/T6 的完整接线后才可声明工程可用。

## T1 — Lock Historical Baseline And Regression Inputs

**Owner / Files：** 原 tests 与 fixture owners；
`tests/test_generation_evaluation.py`、`tests/test_generation_historical_replay.py`、
`tests/test_generation_history_import_receipt.py`、`tests/test_generation_quality_rejection.py`、
`tests/test_generation_no_regression.py`。新增语义测试集中放在
`tests/test_requirement_semantics.py`；必要的小型 JSON fixtures 放在 `tests/fixtures/`。

**Work：**

- 固定 legacy QA/recipe/source/experience 的原字段、嵌套 serialization、hash 与 diagnosis。
  覆盖当前 human FAIL 兜底、原 rejection/abandonment、旧 final_output_goal=None。
- 增加后续应修复的边界案例：margin 被提升、同 ID 问错问题、hint Finding、跨时间容差边界。
  不把历史错误 verdict 改成新预期；旧重放与新语义测试使用不同 contract identity。
- S01 exact MP4、原 source/Gate/QA 只作为只读引用。普通 CI 使用可公开的显式 fixtures，
  不要求 clone 包含未跟踪的 runs 或下载真实媒体。
- 准备至少一个非 S01、非 Vidu 的 fixture，证明实现不依赖 legacy-N、特定阈值或 Provider。

**Exit：** legacy baseline 可复现；新行为 regression 指向具体缺口；fixture 明确标注模拟证据。
**Spec coverage：** AC-07、13、16–18 的 baseline，后续任务补齐 new-contract assertions。

## T2 — Add Versioned Semantics At The Existing QA Owner

**Owner / Files：** `domain_acceptance.py`、`generation_recipe.py`、
`generation_feedback.py::_expressions`，及 T1 的语义测试。

**Work：**

- 在原 profile_payload 接纳 `requirement-semantics/1` marker；添加 Spec 定义的
  semantics/measurement_spec，强制 category/level、来源、hard_basis 和完整 inventory 一致。
- 对单镜和 component allocation 都走同一 validation helper；current selected QA 是版本 owner。
  未知版本、部分 metadata、移除 marker、遗漏 hard ID 必须拒绝。
- 处理 `generation_recipe → domain_acceptance` 已有依赖方向。若共享 typed definitions
  会造成反向 import，允许一个无 I/O 的 `production/requirement_semantics.py` 叶模块；
  它仅容纳同一契约的类型/校验，不拥有第二 inventory、选择或 lifecycle。
- 可选字段在最内层 legacy serialization 中省略，不能默认补 null/category 或改变旧 hash。
  不升级整个 recipe/Manifest，不自动迁移旧 policy。
- 按 Spec 调整 `expression_errors()` 与 native_text projection：raw hard 保持 coverage；
  有 path 的 hint 保持表达检查；仅供排名的 hint 和 diagnostic 不强制进入 prompt。
  全量 authored intent 遗漏保护继续执行。
- 实现 compound atom 的独立 ID/source lineage 和 stage/proof 校验；不自动用 NLP 拆句或定性。
- marked final_composition acceptance 必须引用原 FinalOutputContract，并校验
  ID/observable/proof 一致；纯 final 项不因本次分类被复制成更严格的 raw 条件。

**Exit：** 同一 QA inventory 能表示五类，且编译行为按 level 分离，旧 serialization 完全不变。
**Focused tests：** `test_requirement_semantics.py`、`test_production_generation_decision.py`、
`test_generation_provider_wiring.py`、`test_generation_local_wiring.py`、
`test_production_requirement_allocation.py`。
**Spec coverage：** AC-01–03、13、15–16、23、27。

## T3 — Version The Director Handoff And QA Admission Guidance

**Depends on：** T2 的字段和映射稳定。

**Owner / Files：** 原 `open-video/SKILL.md`、`validate_director_coverage.py`、
`tests/test_open_video_skill.py`。

**Work：**

- 为新 handoff 明确 must_happen、must_not_happen、preferred_performance、
  timing_targets、acceptable_variation 五组及 source/intent ID binding；旧 v3 仍按原规则读取。
- 加入 explicit_user / director_choice / repair_margin 来源，保留 verbatim 用户证据。
  coverage 输出中的“必须”不能自行获得 QA authority。
- 明确 QA admission 如何审核 hard_basis、stage、tolerance、measurement、proof；
  生成 margin 只单向引用原结果，不反向重定义 acceptance。
- 用一个通用 compound 示例与 S01 的非 canonical 示例检查 source→atom 的完整性。
  不改真实 episode authoring，不调整与本题无关的 coverage/camera 风格限制。

**Exit：** 新输出缺语义或引用错配会被 validator 拒绝；旧 v3 行为不变；
Product Runtime 没有 Skill import/dependency。
**Focused tests：** `test_open_video_skill.py`、`test_runtime_skill_boundary.py`。
**Spec coverage：** AC-01–03、23；固定用户要求仍严格。

## T4 — Bind Canonical Evaluation Items And Temporal Predicates

**Owner / Files：** `generation_evaluation.py`、原 review input；
按需要在其同层抽取无 I/O 的 criterion helper；新增
`tests/test_generation_evaluation_binding.py`。

**Work：**

- 从 selected QA、recipe 与 fetch 后 actual request/artifact 派生 immutable evaluation items。
  只使用 observable/tolerance/measurement/stage/proof；Provider prompt 和历史 note 不参与 predicate。
- 实现 source /1 与 /2 的严格 schema dispatch；/2 acceptance、advisory、
  unresolved-quality entries 分开，不允许 C/diagnostic 投影为 Finding。
- 时间窗仅支持 Spec 的 event_time_window。QA 预先封存 event、selection rule、边界和精度；
  fetch 后才绑定 SHA/size，避免生成前 criterion 依赖未来 MP4。
- 按实测区间与 canonical 窗口推导/复核时间 verdict：包含、相离、跨界分别处理。
  span_millis 保持位置语义；ASR segment 不能冒充末字测量。
- 错 ID/question/stage/proof/阈值为 contract admission error；合法缺证据为 EVIDENCE_GAP。
  源中既有非法条目不得通过静默过滤形成 PASS。

**Exit：** 2.2s recipe target 不能覆盖 2.7s canonical predicate；ID/hash 正确但对象或测量错仍拒绝。
本任务只完成结构与纯判定，不声称已有可信 presentation proof。
**Focused tests：** `test_generation_evaluation.py`、`test_generation_evaluation_binding.py`、
`test_requirement_semantics.py`。
**Spec coverage：** AC-06–15、24、27。

## T5 — Connect Trustworthy Presentation And Answer Evidence

**Owner / Files：** `ai_video_mcp/generation_feedback.py::GenerationReviewInput / review_generation_attempt`、
`generation_evaluation.py`、`tests/test_generation_feedback_review.py`。

**Work：**

- 在既有 review entrypoint 注入 Spec 要求的 presentation-evidence verifier；
  将 T4 的 canonical items 作为 adjudicate 的实际输入，保持旧调用的 legacy 分支。
- 明确接口输入为 actual presentation/answer evidence、expected items、selected authority、
  exact media/context；输出为验证后的绑定或 typed mismatch/evidence gap，不能只返回 caller boolean。
- verifier 核对可信来源 namespace、interaction/event references、实际内容、
  answer correlation、actor 和来源提供的事件顺序。不能以 caller 时间戳、任意 JSON、
  事后贴 hash 或已有 `_AnalysisRecordingProof` 证明“先提问后回答”。
- 将 evidence capture/核对留在既有 review host/adapter，Product 不依赖 Codex session path、
  Skill、外部消息平台 SDK 或新前端。不新增 review session state machine。
- 首个接入必须明确一个实际可验证的来源契约，例如受控 request/response 事件；
  human 只有在现有 host 能提供可复核呈现/回答记录时才支持。无此来源时保持 NE，
  不能以 fixture verifier 声称真实 human /2 已资格化。
- immutable source 保存足以离线重验的来源凭据；strict reopen 不重发问题、
  不调用 MCP/Provider，也不依赖重做真实观看。现有 one-use analysis proof 仍保护其原范围。

**Exit：** 标准 review seam 能在离线受控 fixture 下完成正确绑定并拒绝事后补贴；
缺真实 host integration 的 proof kind 明确 fail closed，不宣称 live integration 已通过。
**Focused tests：** `test_generation_feedback_review.py`、`test_generation_evaluation_binding.py`。
**Spec coverage：** AC-07–08、15、26；覆盖 replay 零副作用与凭据不可冒用。

## T6 — Preserve Semantics Through Persistence, Reopen And Feedback

**Owner / Files：** `generation_feedback.py`、`generation_diagnosis.py`、
`generation_experience.py`、`_state_commit_generation_feedback.py`、
`_generation_feedback_reader.py`；检查 `generation_decision.py`、
`generation_history_import.py`、`generation_rejection.py` 的既有消费者。

**Work：**

- `record_attempt_evaluation` 与现有 `GenerationFeedbackOrchestrator.record_evaluation`
  都必须委托同一 source→Findings / unresolved_quality_refs 投影与校验，移除各自无条件 flatten。
  direct committer 准入、experience 重开和 import 验证复用同一个 exact projection invariant，
  直接提交遗漏 refs 的 experience 也必须拒绝，不能只保护 MCP bridge。
- 新 AttemptEvidence 字段进入新 hash，旧缺失仍省略；引用必须解析到同媒体/QA 的完整 source entry。
  拒绝 source 有拒绝但 projection 为空、孤立 hash、跨 source/bytes/QA 拼接等旁路。
- 纯 diagnosis 对 marked C/hint 非法 Finding 防御，保留 legacy human FAIL 原行为。
  未映射真实质量拒绝变为 rubric conflict，保留 exact refs；不伪造 requirement FAIL。
- `diagnose_exact_result` 合并全部 unresolved refs；后加 PASS、遗漏旧 source 或重新命名候选
  不能解除阻断。原 history/Feedback 重开仍交 acceptance owner，不自动 repair。
- `empirical_assessment` 和 decision assessment 对没有真实 hard FAIL 的 unresolved/incomplete
  视为未完成，不计作成功或虚构 QUALITY_FAILURE。若同 exact 媒体同时有真实 hard FAIL 与
  unresolved refs，保留 QUALITY_FAILURE、failed IDs 和 rubric conflict；按原 failure 优先
  统计为失败，不能降成 incomplete。加入这类 mixed-evidence regression。
  advisory 不能改变成功率分母、failed IDs 或保护集。
- 当前准入使用 selected QA；历史重开使用原 sealed QA/context，不能用 current QA 重解释旧 source。
  旧 history import /1 保持资格与 attribution；/2 若不满足既有合法导入前提必须明确拒绝，
  不新增无 binding 媒体的 retrospective presentation proof 或受控 MCP 冒认权限。
- 不新增 conflict 清除/FAIL 撤销机制；全部适用 hard proof PASS 仍不能压过 unresolved refs。
  rejection、abandonment、permit、activation 与 frozen-goal 规则保持原 owner 严格执行。

**Exit：** source→evidence→receipt→strict reopen→diagnosis→decision/statistics 后果一致；
旧 QA/goal/Manifest exact reopen 不变；新 source 不存在只在 bridge 有效的校验旁路。
**Focused tests：** `test_generation_feedback.py`、`test_generation_evaluation.py`、
`test_generation_historical_replay.py`、`test_generation_history_import.py`、
`test_generation_history_import_receipt.py`、`test_generation_quality_rejection.py`、
`test_production_generation_decision.py`、`test_generation_execution_guards.py`。
**Spec coverage：** AC-04–06、13、15–17、21–22、25。

## T7 — Run Shadow Replay And Final-Output Integration Regressions

**Owner / Files：** 新 `tests/test_requirement_semantics_replay.py`；
原 `tests/test_generation_no_regression.py`、`tests/test_production_final_output.py`、
`tests/test_production_planning_generation.py` 和 `tests/test_production_strategy_reader.py`。

**Work：**

- 将 shadow replay 放在 development/test helper 内，输入为显式历史 evidence root 与
  proposed QA；不创建 Production replay API、public CLI 或新 manager。
  如需单独脚本，仅包装同一 helper，以只读 stdout 返回结果，不默认写入。
- 本地实际验证 attempt12/13 的 exact SHA/size 与原 QA/Gate/evaluator evidence。
  完整 inventory 按来源拆分，保留 original verdict 与 proposed assessment 的并列结果；
  旧回答只能注明历史引用，不伪装为 /2 新提问。
- 不因 1.5s margin 自动 repair attempt12；不把13起手更早当作整体更好；
  纠正2.2/2.7标准和legacy-14/17对象错配，所有缺失 human/final proof 保持未知。
- 无未跟踪真实资产的 CI 跑显式模拟 fixtures；本地 exact replay 为独立验证步骤。
  缺少真实 bytes 时报告该项未验证，不能用 fixture 成功声称 AC-18 的真实部分完成。
- 验证 final_composition 项不能成为 raw Finding，raw PASS 不代替最终字幕、叙事、自然度或切点。
  新 raw binding 不扩展为完整 final-question schema。
- 用已有 freeze rejection 证明：timing改善仍被已知自然度/no-regression拒绝；
  required/optional baseline 的 PASS→FAIL/NE 继续阻断。
- 在原 Strategy/Planning/Feedback seams 验证偏好保留不产生 activation、source-use、
  下一 Shot、batch submit 或额外 quota；不修改 Resolver 的职责和选择算法。

**Exit：** legacy replay 与 proposed shadow 两种解释隔离；真实可知和未知均保留；
Final-output 和 production gates 没有因新分类变弱。
**Spec coverage：** AC-14、16–22、25；与 T1 非 S01 fixture 一起验证泛化。

## T8 — Contract Documentation, Routing And Engineering Closure

**Owner / Files：** `docs/agent-primary-contract-matrix.md`、
`docs/v0.2-runtime-baseline.md`、`docs/v0.2-agentic-production-roadmap.md`、
`.agent/harness/policy.yaml`，必要的既有 Harness tests 与本题记录。

**Work：**

- 仅在对应代码/测试实际完成后同步 runtime truth、适用版本和未验证 proof integration。
  不因 plan/fixture 存在就写 implemented/live-ready；不扩张 root AGENTS。
- 给实际新增 modules/tests 加入现有 Harness categories/check argv，复用既有 checks；
  新测试不能成为未路由 orphan，新增 source 不能被错误归入 docs-only。
- 完成一个 native `reviewer_xhigh` 独立审查；修复 blockers 后同 tier scoped re-review。
  重点审查新旧版本分界、错证明对象、历史重开、统计误算和单 owner。
- 按实际 task-owned scope 执行 Harness 要求的测试和 Architecture Gate；
  正式 closure 需符合当时授权的 exact snapshot 与 fresh receipt。
  当前没有 stage/commit/worktree 授权，不预先执行这些动作；条件不具备时明确报告
  closure 未完成，不能用 explicit-path inspect 或 working-tree PASS 替代。
- 更新同题 session record；区分工程完成、shadow evidence、真实 human/Provider/media
  验证和 empirical benefit。学习评估不把原12/13重复引用计作新的独立实验。

**Exit：** AC-01–27 全部有明确 test/evidence 对应；所有失败路径与历史边界通过；
无未解决 reviewer blocker。任何未完成的实际 proof integration/exact replay/receipt 单独列出，
不得通过削减验收 scope 宣称整项完成。

## Verification Commands

以下均为 **未来实施时** 的 focused commands；本次写计划不执行新行为测试。

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_requirement_semantics.py tests/test_generation_evaluation_binding.py -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_open_video_skill.py tests/test_runtime_skill_boundary.py -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_generation_evaluation.py tests/test_generation_feedback_review.py tests/test_generation_feedback.py tests/test_production_generation_decision.py -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_generation_historical_replay.py tests/test_generation_history_import.py tests/test_generation_history_import_receipt.py tests/test_generation_quality_rejection.py tests/test_generation_execution_guards.py -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider tests/test_requirement_semantics_replay.py tests/test_generation_no_regression.py tests/test_production_final_output.py tests/test_production_planning_generation.py tests/test_production_strategy_reader.py -q
```

`test_requirement_semantics.py`、`test_generation_evaluation_binding.py`、
`test_requirement_semantics_replay.py` 是计划新增文件，当前不存在。
其他 T2 focused suites 及最终 mandatory 组合按真实 changed paths 从 policy 获取，
不要把上面的 focused list 当成固定完整 Harness 清单。

本次 plan 文档验证限于：docs contract、policy audit、runtime Skill boundary、
local links/whitespace、task scope，以及独立 plan review。不会生成实现通过 receipt。

## Completion And Non-Goals

完成工程 contract 不证明生成质量、通过率、repair成本或人工review效率改善。
这些收益需要另行有界实验；不能由27项工程 AC 或两个相关历史样本推出。

本计划不实现 best-of-N、Exploration Manager、第二 Director/Resolver/QA lifecycle、
Provider ranking、VIDEO_EDIT、新模型、自动审美 evaluator、整套 Harness 重设计，
也不批准真实 S01 migration、媒体继续生成、历史 verdict 修订或任何额外调用。
