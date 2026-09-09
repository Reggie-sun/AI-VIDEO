---
record_kind: session_summary
topic_id: requirement-semantics-and-evaluator-fidelity
learning_eligibility: ineligible
---

# Requirement Semantics And Evaluator Fidelity Record

Date: 2026-09-09

## Formal Engineering Closure

用户随后明确授权正式工程 closure，包括 task-owned stage/commit 与 Harness 所需的
temporary detached worktree；不包含 push、Provider、真实媒体或 Production mutation。
下文无 Git 授权、ownership blocker 与尚无 receipt 的表述是此前阶段的历史状态。

正式验证范围为基线 `c55bfc3400d4aac95dda43da564fac9f4d1de555` 至本任务 commit，
仅纳入本任务代码/测试、同题已批准 Spec/Plan/record 与四个共享文档/policy 的任务增量；
其他任务 staged/dirty 内容保留在原 tree，不进入 execution snapshot。
收据入口为 `.agent/harness/runs/requirement-semantics-closure-20260909/receipt.json`。
该文件的实际 `status`、exact commit scope、artifact hashes、freshness 与 cleanup 结果
决定正式验证结果；本记录不以早先 working-tree PASS 或 review verdict 预填 receipt PASS。
可用 `python -m scripts.agent_harness verify-receipt <receipt-path>` 重新核验。
工程 closure 不代表真实 human host 已接入，不产生媒体质量、通过率、activation 或发布结论。

## Implementation Checkpoint — 2026-09-09

用户已明确授权按 accepted Plan 进行 current working-tree 有界离线实现；下文 Plan/Spec
阶段“只写文档”“尚未实现”的描述保留为历史，不代表当前授权或 implementation 状态。
本轮未获 stage/commit/push/worktree、Provider、真实媒体生成/派生或 Production mutation
授权。T1–T7 已落地：legacy hashes、marked QA、Director v4、evaluation source /2、受控
technical/analyzer presentation、shared projection/strict reopen 与只读 shadow helper。

两个评价录入入口共用 source→Findings/unresolved refs 校验；追加 PASS 不删除未映射质量
拒绝，mixed hard FAIL 仍按失败统计。Legacy verdict、rejection/abandonment、identity/
continuity、Final-output/no-regression 与生产治理 owner 保持原约束。真实 human host
integration 不支持，fail closed；fixture 不构成 human 或媒体资格化。

验证：T1 基线 59 passed（修改前 56）；相关 focused suites 271 passed；最终固定文件
状态的新语义/问答链路 117 passed。早启动的全量 pytest 在 1792.79s 接近 policy 的
1800s 上限时中断保留诊断：4669 passed、4 skipped、2 failed。两处失败是旧 v4 fixture
遇到本轮更新后的动态 validator；尾部 400 项加这两个节点补跑为 402 passed。以上运行
分开报告，不合并成一次全量 PASS。Architecture Gate、docs contract 与 current policy
audit 是 working-tree PASS；正式 exact-snapshot Harness receipt 尚无，工程 closure 未完成。
T1–T7 的 native reviewer_xhigh 最终 scoped re-review 为 accept，无未解决 blocking issue。

实际 shadow 通过 standard loader/committer reader 核对 attempt12/13 的 exact SHA/size，
完整 identity 与逐 atom 解释见下方 Historical Shadow。每个样本 19 个 proposed atoms
均有原 lineage、适用性与理由；原 Gate 和 diagnosis 保留。1.5s margin 不自动修复，
2.2s target 不替换 2.7s criterion，segment ASR 不证明末字端点；13 的 legacy-14/17
错对象保留未知。历史人类回答只作同 exact bytes 的旧证据引用；final proof 未补造。
整个历史 run 内容树 hash 前后相同，没有新 Provider/MCP/media 执行、真实 state 写入、
S01 migration 或历史 verdict 改写。24 个 task-owned 文件在最终 focused/tail tests 前后
hash 相同；T1–T7 边界时，开始已有的 18 个 changed files 和 index 均未改动。

用户随后回复“继续”，交接 policy、contract matrix、runtime baseline、roadmap 和本记录，
允许保留既有内容做增量更新；stage/commit/push/worktree 禁令仍有效。T8 将五个新增
source/test paths 接入原 Harness categories/check argv，未新增 checker、降低检查标准或
更改 receipt 资格。五项 routing regression 先因未路由而 FAIL，接线后全部 PASS。
随后按当前 policy 的原始 argv 运行 `harness_tests`（225 passed）和
`generation_feedback_tests`（256 passed）；Runtime Skill boundary 另为 2 passed。
`scripts.docs_contract_gate check --json`、`scripts.agent_harness policy-audit` 和
`scripts.architecture_gate check --base-ref HEAD --format json` 均为 working-tree PASS。
T8 六个文件的独立 reviewer_xhigh 增量审查为 accept；未发现漏路由、gate 弱化或
证据过度声明。这些结果与前述 117/402/全量中断分别保留，不合并为单次完整运行。
复核确认原 policy obligations 保留；T1–T7 的 24 个文件、未交接的 13 个既有
changed files 和 Git index 均未改变。本题原 Plan/Spec 历史文档也未自行改写。
正式 snapshot/receipt 仍未完成；本轮没有新的独立媒体实验，不能从两个相关历史样本或
工程 AC 推导媒体质量、通过率、repair 成本或人工 review 效率改善。

本轮按 `record-ai-video-session` 更新稳定记录，并按 `distill-ai-video-learning` 评估为
`no_candidate`：experience retrieval 仅作 advisory preflight，当前内容是工程验证与已有
12/13 证据重述，不满足新增独立实验、受控比较或 existing claim 实质更新的准入条件。
保持 `learning_eligibility: ineligible`，不创建学习占位、不采用 claim、不修改学习目标。

## Historical Shadow

源 root：`runs/jieshi-e01-i2v-20260907-attempt10/production-s01-v10`；只读
`load_production_project()` 与 `ProductionStateCommitter.read_generation_experiences()`。
原 Gate 为上级 run 中 `preparation-v4/shot-01-gate.json`（12）与
`preparation-v5/shot-01-gate.json`（13）；原 policy 位于 `preparation-v1/acceptance-policy.json`。
完整 JSON 分析保留在本机 `/tmp/requirement-semantics-shadow.json`；下表保留 durable 摘要，
不依赖该临时文件继续存在，不回写 `runs/`。

| attempt | exact artifact SHA-256 | bytes |
| --- | --- | --- |
| 12 | `c56b05e2da5d38bfeddd2d6f58322d84a7d8433c01589112b87d1865b388b7f3` | 3472114 |
| 13 | `d6a636d5fe19c1a9cbdd23d5bbb160ce3b2e91b8379d40346ff12e69aebff922` | 3305001 |

原 rubric hash：`6e95f68134a326906d23b266c2a9a556cffe10988be7c48c0a19074191459820`。
Development proposed hash：`2762ca0ea97017880aa53f0d8f0f5bcec2eeca4ea4c7ad44540882e77db121ac`；version 为
`requirement-semantics/1`，profile 为 `s01-shadow-only/not-adopted-1`。这不是 adopted
QaPolicy/FinalOutputContract，未迁移 S01。原两个 Gate 均为 FAIL，原 diagnosis 均保留
`EVIDENCE_GAP + QUALITY_FAILURE`；下表的 proposed PASS 只表示相同 criterion 的历史
证据适用性，不是新的 `/2` presentation、human 再观看或 Production PASS。
`advisory` 不生成 required FAIL；NE 不伪装为成功。切点与 narrative hook 是显式拆出的
final atoms，保留原 source lineage，不自动继承其 verdict。

| Atom | Original IDs | Category | Stage | Original12 | Original13 | Proposed12 | Proposed13 | Applicability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cut-continuity | legacy-03,legacy-06 | quality_critical | final_composition | FAIL/PASS | FAIL/NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | 来自03/06的 raw 证据不证明最终切点和自然动态；freeze 拒绝保持。 |
| final-hook | legacy-07,legacy-08 | narrative_critical | final_composition | PASS/PASS | PASS/PASS | NOT_EVALUATED | NOT_EVALUATED | 来自07/08的叙事元素不证明最终节奏、字幕或悬念效果。 |
| legacy-01 | legacy-01 | governance | raw_generation | PASS | PASS | PASS | PASS | 原 POST 的注册输入 SHA/bytes/role/order 支持相同 criterion；不是新 submit。 |
| legacy-02 | legacy-02 | governance | raw_generation | PASS | PASS | PASS | PASS | 原 exact probe 支持输出容器规格，不证明内部生成 raster。 |
| legacy-03 | legacy-03 | directional_preference | raw_generation | FAIL | FAIL | advisory | advisory | 保留原 1.5s FAIL；proposed 只把提前量作为偏好，切点连续性另验。 |
| legacy-04 | legacy-04 | quality_critical | raw_generation | PASS | PASS | PASS | PASS | 17 个历史样本支持右手/手机位置，不扩展为逐帧穷尽证明。 |
| legacy-05 | legacy-05 | directional_preference | raw_generation | NOT_EVALUATED | NOT_EVALUATED | advisory | advisory | 模糊和手指轴线变化不证明反掌；自然度仍是 hard legacy-17。 |
| legacy-06 | legacy-06 | quality_critical | raw_generation | PASS | NOT_EVALUATED | PASS | NOT_EVALUATED | 12 有 exact human 旧回答；13 无同 bytes 观看证明，不转移旧答案。 |
| legacy-07 | legacy-07 | narrative_critical | raw_generation | PASS | PASS | PASS | PASS | 样本支持七个人影，另记暗带，不能据此判定暗带无害。 |
| legacy-08 | legacy-08 | narrative_critical | raw_generation | PASS | PASS | PASS | PASS | 样本未见匹配主角倒影，不证明所有帧或 final narrative hook。 |
| legacy-09 | legacy-09 | quality_critical | raw_generation | PASS | PASS | PASS | PASS | 原采样支持固定构图，暗带变化不等同于相机运动。 |
| legacy-10 | legacy-10 | quality_critical | raw_generation | PASS | PASS | PASS | PASS | 原 raw 样本无生成字幕，不替代 final narrative subtitle 验收。 |
| legacy-11 | legacy-11 | quality_critical | raw_generation | PASS | PASS | PASS | PASS | 原样本支持可见身份连续性，不声称微小工牌细节可辨。 |
| legacy-12 | legacy-12 | governance | raw_generation | PASS | PASS | PASS | PASS | AAC48kHz stereo 仅证明音轨存在，不证明音质或单词时刻。 |
| legacy-13 | legacy-13 | narrative_critical | raw_generation | PASS | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | 2.2s target 不是 2.7s canonical criterion；两者的 segment 时间均非末字区间测量。 |
| legacy-14 | legacy-14 | quality_critical | raw_generation | PASS | NOT_EVALUATED | PASS | NOT_EVALUATED | 12 有 exact 音质旧回答；13 原 Gate 却问间隙，不能回答音质。 |
| legacy-15 | legacy-15 | narrative_critical | final_composition | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | NOT_EVALUATED | 最终字幕 proof 缺失，保留 final stage；不是 raw blocker。 |
| legacy-16 | legacy-16 | narrative_critical | raw_generation | PASS | PASS | PASS | PASS | 原样本支持闭嘴聆听，不推断逐帧唇动或 final audio 验收。 |
| legacy-17 | legacy-17 | quality_critical | raw_generation | PASS | NOT_EVALUATED | PASS | NOT_EVALUATED | 12 有 exact 手腕自然度旧回答；13 原 Gate 却问音频，手部仍未知。 |

对整个历史 run 使用同一文件枚举和 SHA-256 算法，shadow 前后 tree hash 均为
`34953e9af3af29fb7ae3655c52949cd2661becb37ded54e1dea67c503a57152d`；只读 replay 没有改变 bytes。

## Acceptance Evidence Map

所有 test modules 均位于 `tests/`；Spec 保持需求定义 owner，下表只记录本轮验证对应关系。


| AC | Executable evidence |
| --- | --- |
| 01 | `test_open_video_skill.py::test_v4_director_handoff_binds_complete_compound_intent_groups`；`test_requirement_semantics.py` inventory tests |
| 02 | `test_explicit_fixed_user_requirement_cannot_become_preference`；`test_v4_fixed_user_result_cannot_be_reclassified_as_advisory` |
| 03 | `test_compound_atoms_keep_lineage_without_inheriting_verdicts`；v4 compound fixture |
| 04 | `test_advisory_cannot_fail_and_pure_diagnosis_defends_hint_injection`；`test_advisory_only_source_is_incomplete_without_creating_a_failure_sample` |
| 05 | `test_unresolved_refs_survive_reopen_merge_and_failure_first_statistics[FAIL]`；existing identity/continuity/router guards |
| 06 | typed-time coverage/segment cases；`test_marked_review_rejects_untrusted_or_mismatched_presentation` |
| 07 | `test_correct_hash_does_not_admit_wrong_question_object_or_actor`；actual review mismatch cases；human host fail closed |
| 08 | same binding test actor/media cases；temporal wrong-media full recording case |
| 09 | `test_time_predicate_uses_canonical_window_not_recipe_margin`；`test_typed_time_result_recording_and_strict_reopen` |
| 10 | same typed-time crossing-window cases |
| 11 | same typed-time outside-window cases |
| 12 | `test_segment_end_cannot_prove_word_end_and_exclusive_boundary_is_strict`；full segment recording case |
| 13 | advisory/hard/final mismatch tests；pure diagnosis rejects injected hint Finding |
| 14 | `test_marked_final_items_must_match_existing_final_owner`；`test_marked_raw_pass_cannot_replace_final_output_naturalness_or_proof` |
| 15 | marked admission/version tests；`test_marked_qa_rejects_legacy_source_and_unsealed_snapshot` |
| 16 | five legacy serialization/hash baseline tests plus historical import/rejection/reopen suites |
| 17 | existing `test_router_cannot_drop_requirement_by_replacing_baseline_rubric`；goal revision/activation protection tests |
| 18 | actual attempt12/13 standard-loader shadow JSON；simulated non-S01 shadow regression |
| 19 | existing `test_known_violation_rejects_any_repair_operation_before_execution`；real historical freeze rejection retained |
| 20 | existing `test_real_repair_outcome_blocks_regression_and_invalid_evidence`；generation no-regression tests |
| 21 | advisory-only incomplete regression；existing planning/strategy no activation/source-use/acceptance paths |
| 22 | existing generation execution guards, rejection and decision quota/unknown/identity suites |
| 23 | `test_marked_compiler_skips_only_unexpressed_advisory_not_authored_intent`；existing authored-intent omission test |
| 24 | full typed recording rejects contradictory verdict/event/media and pure binding rejects wrong question |
| 25 | actual committer strict reopen + additional PASS test；direct projection omission rejected；both entrypoints and empirical failure-first tests |
| 26 | separate one-use presentation proof tests, copied proof rejection, prior presentation rejection and missing host gap |
| 27 | QA sealed before simulated submit; fetch actual bytes; typed measurement recorded/reopened through original committer; wrong-media rejection |

此表是测试对应关系，不是正式 27 AC closure receipt。真实 human/Provider/media integration 未被 fixtures 资格化。

## Plan Authoring — 2026-09-09

用户随后“写 plan”明确扩展了文档授权，新增
[Implementation Plan](../superpowers/plans/2026-09-09-ai-video-requirement-semantics-and-evaluator-fidelity.md)。
下文仅允许 Spec、未允许 plan 的表述属于此前阶段；实现、Provider、媒体、真实 Production
mutation、stage/commit/push 仍未授权，Spec 与全部实施任务保持未实现。

Plan 按现有 owner 分为 8 个依赖任务，覆盖 Spec 的 27 个 AC，包含兼容性基线、
QA/Director、评价与可信问答、持久化/重开/统计、shadow replay 和工程 closure。
只读接线核查补齐两个既有评价录入入口；独立 `reviewer_xhigh` 的两项 concerns 修订后，
scoped re-review 为 `accept`：不漏 unresolved refs，也不把 mixed hard FAIL 降为 incomplete。

Docs contract、policy audit、runtime Skill boundary（2 passed）和文档路径/格式检查通过。
这些是计划文档验证；没有运行计划中的新行为测试，没有实现通过的 Harness receipt。
本次只新增 Plan 并更新本记录，保留原 Spec 与其他既有工作。按记录/学习 Skill 重新评估为
`no_candidate`，没有新的独立实验，不创建学习占位或修改历史 verdict。

## Scope And Status

本轮仅编写 proposed [Requirement Semantics And Evaluator Fidelity Spec](../superpowers/specs/2026-09-09-ai-video-requirement-semantics-and-evaluator-fidelity.md)。
用户未授权实现或 implementation plan；没有调用 Provider、生成或派生媒体、修改真实
Production state、改写历史、stage、commit 或 push。Spec 的 `implementation_status`
为 `not_started`，不改变 runtime baseline、current QA selection 或任何历史 verdict。

基线为 HEAD `c55bfc3400d4aac95dda43da564fac9f4d1de555` 加既有 working-tree changes。
本轮只新增 Spec 和本记录；已有 recovery/admission 工作不属于本轮成果。

## Contract Decisions

Spec 在原 `RequirementExpression` / QA inventory 上区分必要叙事、质量底线、导演偏好、
诊断观察与生产契约，并规定不同运行后果。Director 提供明确来源与建议分类；QA owner
发布验收 predicate；Evaluator 不能从 prompt、repair margin 或历史 Gate 增加标准。

必要扩展包括 versioned semantics、有限时间 measurement、evaluation source /2、
实际问题与回答的可信来源绑定，以及未映射质量证据的持久化投影。它们留在现有 owner 内，
不建立第二 requirement system、Director、Resolver、QA lifecycle 或 Exploration Manager。
完整字段、限制与 27 个后续实现验收场景由 Spec 独占，本记录不复制第二份 contract。

attempt12/13 仅作为非 canonical 示例和后续 shadow replay 输入；旧 QA、FAIL、
abandonment 和缺失的 human/final proof 均保留。拒绝 freeze derivative 的
Final-output/no-regression 要求保持严格，不承诺本次语义修复提高媒体质量或通过率。

## Verification

- `reviewer_xhigh` 首轮指出三个契约缺口；修订后同 tier scoped re-review 为 `accept`，
  无剩余 blocking issues。该结论仅针对 Spec 的完整性和可实现性。
- Harness explicit-path inspection 将两个新增文档归入 documentation，
  `closure_eligible=false`；没有生成 exact-snapshot Harness receipt。
- `scripts.docs_contract_gate check --json` 与 `scripts.agent_harness policy-audit` 通过。
- `tests/test_runtime_skill_boundary.py`：2 passed；未因文档任务执行全量产品测试。
- 本轮写入前已有的 15 个 dirty/untracked 文件逐文件 SHA-256 未变，原 index 未改动。
  `runs/jieshi-e01-i2v-20260907-attempt10/production-s01-v10` 的 107 个文件树哈希前后相同：
  `7f4f7581141605b50a66ac92adba4aed32ec7f5927e342508fcede84b8d1eacd`。

以上属于文档与工作区边界验证，不是实现验收、真实媒体新评价、历史 verdict 修订或 empirical benefit。

## Learning Evaluation

按 `record-ai-video-session` 保存此稳定边界后，已评估 `distill-ai-video-learning`，
结果为 `no_candidate`。本轮没有新的独立媒体实验；Spec 与历史证据重述不构成额外支持样本。
不创建学习占位、不采用新 claim，也不修改历史记录或学习目标。
