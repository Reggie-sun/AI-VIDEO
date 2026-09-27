# Creative Goal Preservation And Completion Implementation Plan

Date: 2026-09-27
Status: Approved for offline implementation — 2026-09-27

## Goal And Authority

执行配套 [spec](../specs/2026-09-27-creative-goal-preservation-and-completion.md)，减少跨轮目标丢失、避险式创作降级及交出文件后提前结束任务。用户于 2026-09-27 后续明确要求实现本 plan，批准 M1–M4 offline engineering；不授权业务媒体、Provider、Production activation、push 或 release。实际工程 closure 与 evidence limits 由 [implementation record](../../record_for_agent/2026-09-27-creative-goal-preservation-implementation.md) 记录，plan 本身不替代实证。

Native Codex 是 lifecycle owner，后续获准后在当前 working tree 串行执行。当前基线为 `2e70a3a`；开始每个阶段前重新检查 target ownership。当前 `.codex/config.toml` 为 unrelated dirty，保留。同文件发生新的未知改动时停止该文件写入并报告，不创建 worktree 规避 ownership。

## Current And Target Behavior

当前 Director v4 能检查所提供文本的 quote/hash 与 coverage 结构；完整开发报告 packet `/2` 能保留 `FinalOutputContract`。两者之间没有本文定义的 intent→constraint→unit→requirement 校验输入。原 adjudicator 返回 aggregate verdict，报告保存的逐项 findings 仍是 evaluator 原始回答。

目标是接通可重开的目标引用链，在原 adjudicator 内给出有效逐项结果，并在现有审片入口呈现真实缺口。导演方案充分性、完整观看与用户满意仍须真实判断，不由 hash、镜头数或技术测试推断。

## File And Owner Map

| Paths | Responsibility |
| --- | --- |
| 新 `scripts/creative_goal_binding.py`、`tests/test_creative_goal_binding.py` | Development-only、只读的 binding loader / validator；唯一新增工具，不拥有创意或 QA 状态 |
| `.agents/skills/open-video/scripts/validate_director_coverage.py` | 调用其现有 `validate_director_coverage`，不复制算法、不改变 v3/v4 必填字段；预计无需改动 |
| `src/ai_video/production/final_output_review.py`、`tests/test_production_final_output.py` | 提取共用详细裁决结果，保持现有 aggregate API 与 verdict 行为 |
| `scripts/visual_quality_report.py`、`tests/test_visual_quality_report.py` | 新 packet `/3`、binding preflight、有效逐项摘要，兼容 `/1`、`/2` |
| `.agents/skills/open-video/references/creative-completion.md` | 跨轮意图、独立 concept 检查、实际观看与继续修复的详细操作 owner |
| `.agents/skills/open-video/SKILL.md`、`.agent/context/control-plane-playbook.md` | 仅更新进入上述流程的最小 routing pointer，不复制第二份细则 |
| `docs/visual-quality-gate.md`、`docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md` | 报告范围、工具 owner 与实现后实证边界；只在对应阶段完成后更新 runtime truth |
| `.agent/harness/policy.yaml`、`tests/test_agent_harness.py` | 新工具/test 的明确路由、mandatory checks 与路由回归 |
| `tests/test_open_video_skill.py`、`tests/test_runtime_skill_boundary.py` | 既有 authoring 兼容、入口约束、Product Runtime 不依赖 Development / Skill |

新工具留在 `scripts/`，可用与现有 skill tests 相同的显式文件加载方式调用 Director validator。不能让 `src/ai_video/production` 反向 import 它。现有文件达到体量阈值时按新增职责局部拆分，禁止顺带重构其他 owner。

## Stable Contracts

### Binding Input

`creative-goal-binding/1` 是只包含文件引用和关系的不可变开发输入：`schema_version`、`authority=development_only`、`creative_input`、`coverage`、`final_output_contract`、`bindings`。三个 file references 各含相对 `path` 与 exact bytes `sha256`；paths 相对于 binding 文件所在目录，必须在该目录内、为 regular files、不得通过 symlink 或 `..` 逃逸，不自动搜索其他来源。

`bindings` 行含唯一 `intent_item_id`、不重复的 `constraint_ids`、`unit_ids`、`requirement_ids`。ID 来自现有 artifacts。所有 active `explicit_user` intent 恰有一行，至少一个 constraint 和一个 requirement；director choice 可以映射，但不得替代用户意图。global 行可无专属 unit；beat-specific 行必须覆盖既有 coverage 中引用相关 constraint 的所有 units。未知字段/ID、重复、漏项、scope 无法从既有 constraint 确定时拒绝。

UTF-8 source 文本须与 coverage 的 `request.creative_input_evidence` 精确相同，不 trim 或重写换行后冒充 exact bytes。JSON 文件 SHA 与 `FinalOutputContract.contract_hash` 分别校验文件身份和模型语义，不能混用。新 binding 只消费包含 intent inventory 的 Director v4；v3 继续供历史路径重开，不自动推导或迁移到新链。

loader / validator 输入为明确 binding path，输出 verified inputs 和 diagnostics，零网络/媒体/Production write。私有 `python -m scripts.creative_goal_binding --binding PATH` 输出 JSON：exit 0 表示结构完整；exit 2 表示非法或不完整输入。消息不打印文件全文或 secret，异常不得输出 raw traceback。该命令不是公共 `ai-video` CLI。

### Detailed Adjudication

在原 owner 内新增共用详细计算，返回 aggregate verdict、每个 requirement 的有效 verdict 与 evidence-gap diagnostics；既有 `adjudicate_final_output` 仅投影 aggregate。保持原顺序：有效 FAIL 优先；否则任何 incomplete 或缺失/非 PASS 观察导致 `NOT_EVALUATED`；只有全部原条件满足才 PASS。

保留 request/contract 身份、unknown/duplicate findings、visual finding eligibility 和 human proof 检查。不能因把循环拆成逐项计算而丢失原 `incomplete` 标记。对无法归属到某项的非法 evidence，返回全局证据缺口并维持原 aggregate NE；逐项结果不能被单独汇总来绕开这一标记。每项原始回答与有效结果分开，不合格 PASS 不能显示为已证明。

不得新增 Production persisted schema 或改变 `QaPolicy`、`FinalOutputObservation`、Manifest、Final Acceptance 条件。如果为完成重构需要改变这些语义，停止受影响实现、修订 spec 与 review tier，而不是用本计划授权变更。

### Review Packet And Compatibility

给 `prepare` 增加 keyword-only `goal_binding` 输入，给现有私有 `prepare` CLI 增加 `--goal-binding`；它要求同时提供完整合同，缺失/冲突在 probe、抽帧和 mkdir 前失败。旧调用未传新参数时仍产生原 `/1` 或 `/2`，保留原签名用法和 exit 语义，不悄悄升级历史 packet。

新 `/3` 在原 packet 基础上绑定 goal-binding 的 SHA 与依赖文件 identity，`subject_hash` 覆盖它们。准备时将已验证的 binding 与三个依赖按原字节放入 packet 内的 `creative/` 子目录，保持引用关系；这是 evidence snapshot，不是第二个可变目标 owner。更换目录以外的内容必须产生新 identity；reopen 只消费 packet 中封存文件，检查 containment/hash/validator，不能回退到已经改变的外部原路径。

prepare 校验后到复制完成之间必须重核字节或使用已读 immutable bytes，防止 copy 与校验目标不同。`reopen/check` 缺文件、换合同、改 quote 或映射都拒绝，且不能保留旧 PASS 派生展示。原始文件可在 packet 生成后移动，封存 snapshot 仍能重开；不能因此接受 snapshot 自身被篡改。

## Milestone 1: Preserve Intent At The Handoff

**Dependencies:** 无代码前置阶段；重新确认 source / target ownership。

**Files:** 新 helper / tests；policy 和 `test_agent_harness.py` 的最小路由修改。

**Red:** 用广告与剧情的确定性 fixture 先复现 A1–A3：删前轮要求映射、替换 source、unknown/duplicate ID、beat-specific 缺 unit、global 合法零专属 unit。加入 invalid UTF-8、引用越界、symlink、v3 被新链拒绝但旧 validator 仍支持、空或未完整绑定 inventory 等边界。所有无效输入断言零 subprocess / 网络 / 媒体及 Production write。

**Green:** 实现 Stable Contracts 的 loader 与精确 join，复用 v4 validator 和原 `FinalOutputContract`。diagnostics 覆盖 `source_identity_mismatch`、`stale_binding`、`unbound_user_intent`、`unresolved_intent_scope`、`unknown_requirement`，并为非法引用/版本/结构提供稳定类型。不要实现语义提取或把 context summary 当逐字原话。

**Acceptance:** A1–A3 通过；合法 single_take、multi_shot、global 禁止项均可成立；hash 正确但语义不充分只得到结构验证结果。A4 的 Director 兼容部分也在此验证：现有 v3 payload 仍由旧入口接受，新 binding 不自动升级它；v4 原始 required fields、quote/hash 与合法空 intent groups 的旧验证结果保持不变，新链可另行要求 inventory 完整。新文件在 policy audit 有明确 owner/check，不触发 unmapped fallback。

**Verification:** `PYTHONPATH=src:. .venv/bin/python -m pytest -p no:cacheprovider tests/test_creative_goal_binding.py tests/test_open_video_skill.py tests/test_runtime_skill_boundary.py tests/test_agent_harness.py -q`。

## Milestone 2: Expose Effective Requirement Results

**Dependencies:** 与 M1 代码独立，仍串行执行；不等待新媒体。

**Files:** `final_output_review.py`、`test_production_final_output.py`。

**Red:** 新增详细结果行为测试：所有 raw answers PASS 但 human strength 无效、sampled visual evidence、错 contract/request hash、未知/重复 finding、有效 FAIL 与无效 evidence 混合、有效 PASS 加额外 malformed evidence。明确断言有效逐项结果与 aggregate，锁住原 `incomplete` 和 FAIL 优先行为。

**Green:** 抽取一次共用裁决，原 public 函数变为等价投影；有效细项与全局 evidence gaps 由同一 owner 产生。不得在报告里复制这些规则。

**Acceptance:** A5/A6 的有效证据结果成立；旧 Production callers、repair/no-regression 行为不变。保留既有 tests 的期望，不能修改旧 oracle 配合新算法。对于未能证明等价的输入组合不宣布重构完成。

A9 明确复用并执行现有回归：`test_production_final_output.py::test_qa_activation_cannot_rewrite_or_remove_same_goal_requirements` 的 remove 分支、`test_generation_no_regression.py::test_router_cannot_drop_requirement_by_replacing_baseline_rubric` 验证不能丢掉原要求；`test_production_final_output.py::test_real_repair_outcome_blocks_regression_and_invalid_evidence` 的 `stale` 分支验证旧 baseline review 不可关闭新 repair。它们均包含在下面命令中，不只在文档声称 no-regression；发现实际缺口才补相应失败测试，不调整旧期待。

**Verification:** `PYTHONPATH=src:. .venv/bin/python -m pytest -p no:cacheprovider tests/test_production_final_output.py tests/test_production_visual_quality.py tests/test_generation_no_regression.py -q`。

## Milestone 3: Connect Preparation, Reopen And Reporting

**Dependencies:** M1、M2 完成。

**Files:** `visual_quality_report.py`、`test_visual_quality_report.py`，同步 `docs/visual-quality-gate.md`。

**Red:** 覆盖 A4–A7、A10：CLI 和 Python 入口消费同一 binding；缺合同/错 identity 在任何媒体 effect 前拒绝；`/3` round-trip、封存 source/coverage/binding 被替换、原文件移动不破坏封存 packet、copy 时输入漂移拒绝。保留旧 `/1`、`/2` fixtures，不批量更新为新版本来隐藏兼容问题。

**Green:** 按 Stable Contracts 接入 preflight 和 `/3` evidence snapshot，使用原报告的 check / subject identity 路径和 M2 结果。JSON/HTML 展示原始回答、有效结果、全局证据缺口与 `production_acceptance=not_evaluated`；旧 packet 明确说明没有新目标链证据，不能据此声称全任务完成。

用户反馈属于新 revision 的输入来源，仍写在 brief/creative-input/intent inventory 中；摘要引用这些来源及当前 requirement 缺口。工具不得用自由文本判断用户是否撤回拒绝，也不新建 `accepted` 状态。Parent 在交付说明中披露未解决拒绝及下一动作；正反 fixture 证明旧报告未被追溯改写，不能声称机器自动理解用户意见。

**Acceptance:** 真实开发入口从 binding 到 prepare/reopen/check/report 接线可运行；全 raw PASS 加无效 human evidence 时，摘要明确列出未评估项。没有仅测试 helper 而入口继续旁路的实现。

**Verification:** `PYTHONPATH=src:. .venv/bin/python -m pytest -p no:cacheprovider tests/test_creative_goal_binding.py tests/test_visual_quality_report.py tests/test_production_visual_quality.py tests/test_runtime_skill_boundary.py -q`。测试沿用仓库已有短 lavfi fixture / 明确 fake seams，只证明离线行为，不渲染业务广告或调用 Provider。

## Milestone 4: Use The Checks In Creative Work And Close Offline

**Dependencies:** M3 完成，完整实现达到稳定 candidate。

**Files:** 既有 creative-completion reference、最小 routing pointers、matrix、baseline；`test_open_video_skill.py` 仅在确有入口/示例契约变化时增加必要验证。继续使用原 record skill，不建第二套 handoff 文档体系。

**Behavior:** 将“相关原始上下文 → 提取 intent → 独立 concept 判断 → 保留有效 requirement → binding 检查 → 制作 → exact 成片复核 → 修复/补证/真实阻碍”写入已有实践。前置判断先看用户和内容，再看作者技术理由。指向可执行新命令与审片参数；引用旧入口时明确它只是局部检查。

**Paper Cases:** 青颜中区分包装修复与广告表达，否决把已被拒绝的单图方案再次当作完成；剧情中以固定镜位的递物/迟疑/反应证明单镜头可以承载发展。再给一个能力不足保留目标并提出具体选项的案例。独立 reviewer 必须引用内容证据，不以镜头数或模板打分。这里只审查设计与案例，不能称实际表演/声音已验收。

**Acceptance:** A8/A9 与前序 A1–A7/A10 全部有归属；runtime 不依赖新开发工具；坏片不能仅换成 candidate 就结束制作任务。报告区分结构检查、概念判断、实际观看和用户意见四类证据。

**Verification:** 合并一次前序 focused suites，随后按真实 paths 跑 Harness；不因文档新增机械关键词断言来冒充语义质量测试。T2 stable implementation review 按 repository contract 执行；如果实际变更进入 QA acceptance 等 T3 语义，先处理对应 approval/dual review，禁止在这里豁免。

## Acceptance Mapping

| Spec criteria | Milestones | Evidence limit |
| --- | --- | --- |
| A1–A3 | M1 | 检查已登记 intent 的关系，不证明原始提取完整 |
| A4 | M1、M3 | 历史版本兼容与新版本严格 reopen |
| A5–A6 | M2、M3 | 同一 QA 规则下的有效证据，不是自动审美 |
| A7 | M3、M4 | 新输入/旧证据分离；用户语义仍由 Parent 核对 |
| A8 | M1、M4 | 不施加固定镜头数，概念样例独立审查 |
| A9 | M2、M4 | 既有 no-regression/recovery 回归，不扩张权限 |
| A10 | M3、M4 | CLI / Python 实际接线和单向依赖 |

## Exact Verification And Checkpoints

每个 milestone 先记录可信 RED，再 GREEN；稳定代码 checkpoint 只 stage task-owned paths 并提交。测试 scope 来自已解释的 working-tree state，不能 stage 或清理他人内容。无需为每条测试或小编辑单独建计划步骤。

新 helper 与 test 显式加入 policy 的 focused check；`test_agent_harness.py` 验证新 paths、被改 caller 与 mandatory command 选择。完成检查使用非空 exact staged snapshot 或 exact commit range；Harness 自有 detached 验证机制，不授权手工创建开发 worktree。运行 `verify-receipt`，要求 passed、fresh、integrity、scope/policy/artifact hash 一致后才能关闭工程阶段。

按 `record-ai-video-session` 保存最终 exact implementation evidence，并自动评估 `distill-ai-video-learning`。AOCI 仅在受管理文件最终稳定后维护，保留 unrelated dirty；不手动 rebuild experience RAG。本轮文档的 receipt 不能替代将来的代码 receipt。

## Compatibility, Rollback And Stops

旧 packet 与 Director schema 不迁移；new path 缺 binding 应显式失败或保持旧局部 scope，不允许自动造映射。新报告可回退到旧工具只读取历史 `/1`、`/2`，但旧工具不支持 `/3` 时必须明确拒绝，不能 strip 新证据伪装兼容。保留所有新旧 immutable artifacts，不删除失败证据。

发现 aggregate verdict 改变、重复 QA owner、runtime→development import、同文件 ownership 冲突或 mandatory verification failure 时停止对应阶段，报告 exact 差异；不改 baseline、削弱 tests 或绕过 check 求通过。恢复使用明确修正或 task-owned follow-up commit，不 reset 共享工作区。

## Empirical Acceptance After Engineering

工程阶段完成后，用户授权的实际广告任务和剧情任务各验证一次：先封存相关目标与 concept，执行既有技术 gates，完整观看/聆听 exact 成片，并记录用户反馈。素材和模型按真实任务选择，不用同一机械模板证明两种类型都好看。

不在本轮或 offline tests 中运行上述媒体任务；实际执行仍需各任务具备授权、能力和有限预算。没有实际作品及相应反馈，只能声明 M1–M4 的 offline engineering closure。已知创作失败应改内容方案，不能以继续增加 schema 或评分器替代修片。
