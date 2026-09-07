---
record_kind: architecture_implementation
topic_id: generation-feedback-orchestration
learning_eligibility: ineligible
---

# Generation Feedback Orchestration Checkpoint

Date: 2026-09-07

## Status And Authority

这是 working-tree engineering checkpoint，不是 release 或媒体质量 acceptance。
执行范围来自用户对 [accepted spec](../superpowers/specs/2026-09-07-generation-feedback-orchestration.md)
的“实现／继续”；禁止 Provider、ComfyUI、真实媒体生成和 commit/push 仍然有效。
本轮仅执行离线源码修改与测试。记录时 HEAD 为 `4a5dc29`，本任务没有 main commit。
用户后续“OK”明确允许接管七个 staged driver 文件，并允许 Harness 专用 temporary worktree
和 synthetic snapshot commit；这不授权 main commit、push 或 Provider/media action。
当前行为与未验证边界由 [runtime baseline](../v0.2-runtime-baseline.md) 维护。

## Implemented Boundaries

- `generation_feedback.py` 从 canonical context、已注册 adapter variants 与 committer-owned
  experiences 制造 `DecisionInputs`，提供 conditioning conflict、有界 resample 与 feasibility
  建议；Router 保持唯一 selection owner。真实 run driver 与 video-analysis bridge 的后续迁移见下文。
- `generation_execution.py` 将 decision 与实际 native compiled request 绑定；video committer
  在 permit 前重开当前 project、QA、完整历史、累计 submit 与 policy 上限。更换 task 名称、
  注入／遗漏 experience、挑选更早的结果或 prepared-only attempt 不能重置失败历史。
- `generation_evaluation.py` 保存原始 typed evaluator document；QA 显式绑定 evaluator/proof
  kind，committer 核对 exact request/artifact/rubric/current policy 与 Finding 投影。
  这是证据契约，不能证明真实 analyzer 或 human 已执行。
- `generation_experience.py` 提供 Provider/model/mode/rubric/结构特征 cohort 的观察统计。
  整体 artifact 的 PASS/FAIL 不由跨 artifact 局部 proof 拼接；未知动作／手部特征仍为 unknown。
  Wilson interval 是有限样本描述，不是已校准的 Provider 成功率或因果改善证据。
- intervention 的 seed-only repair 必须计入 resample，空 delta 或改写说明不能构造新实验；
  声明的 target variable hashes 必须由 compiler 对照实际值验证。
- Source/M0 qualification 使用 owner 重开后发出的 immutable request-bound、一次性 proof。
  本轮独立复审接受了 mutation/copy/replace/换 request/重复消费的有界修复。
  后续已迁移 runtime/operator fixtures，保留原 UNKNOWN、failure、activation/reopen/replay
  断言。外部 preflight 被 mock，实际执行 inherited owner proof、caller、committer 与 permit；
  增加 owner 第二次 reopen 漂移时在 effect/attempt write 前拒绝的反例，不声称 live closure。
- 同一 `QaPolicy` 新增可选 `generation_acceptance`，显式区分 raw-generation 与 whole-ad
  rubric；保留旧 sealed inventory 兼容和未配置字段的旧序列化，核验当前 rubric identity。
- P7 retained first-frame 经 `_image_video_lineage.py` 证明 exact successor；复用 video reader
  的完整 candidate/probe/provenance/terminal 验证，原 P7 检查与当前 activation pointer gate
  保留。增强 hardcut E2E 覆盖后续 Project/Registry 变化、sealed terminal 与篡改拒绝。
- 商品 fixture 采用独立登记来源并经 standard loader/dependency resolver 建立合法前驱，
  不手工写入 FRESH；commercial positive tests 同时保留 whole-ad 与 raw-generation policy。

## Initial Checkpoint Verification

以下保留首次 checkpoint 的历史结果；后续修复与最新验证见下一节，不代表当前失败状态。

测试统一使用 `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider`。

| Scope | Observed result |
| --- | --- |
| `test_production_generation_decision`、`test_generation_feedback`、`test_generation_execution`、`test_generation_execution_guards`、`test_agent_harness` | 225 passed |
| historical replay、Local/Cloud wiring、evaluation、Vidu、Seedance、MiniMax H3/Hailuo、video service/pre-generation | 440 passed |
| local state、video recovery、generated-video E2E、product-interaction E2E | 20 failed / 55 passed |
| source runtime、source operator、source qualification、M0 caller | 10 failed / 89 passed |
| Harness `policy-audit` | 630 paths；missing/unmapped/unreferenced/unverified 均为空 |
| `git diff --check` | 通过 |

以上不是 full suite 或 exact-snapshot Harness receipt。当前 index 含其他会话的七个 Seedance
run-driver 文件；本任务没有 stage 它们。未建立 Harness 要求的 detached execution snapshot，
没有 fresh passing full Harness receipt，也没有把普通 pytest 结果伪装为该 receipt。

native `reviewer_xhigh` 分别接受历史推导和 qualification proof 修复；后续另接受 QA/lineage
修复。这些是 scoped review，不是整体 implementation approval。历史 H3/Vidu fixture replay 只
证明策略响应，不能声称实际避免了历史提交或提高了媒体成功率。

## Follow-up Verification

本轮修复下述前四项兼容性问题，保留原有 positive lifecycle 断言。最新结果：

| Scope | Observed result |
| --- | --- |
| feedback、execution guards、historical replay、Local/Cloud wiring、decision、Provider/service、Harness tests | 653 passed |
| evaluator/execution、local state/recovery、generated-video/product E2E、commercial source、image、source runtime/operator/qualification、M0 | 237 passed，210.25s |
| enhanced hardcut E2E，含 terminal、后续 Registry 及篡改反例 | 1 passed |
| source runtime/operator，外部 preflight mocked，实际 owner/caller/committer | 18 passed |
| source/M0 qualification focused tests | 82 passed |
| fresh Harness `policy-audit` | 630 paths；全部 diagnostics 为空 |
| `git diff --check` | 通过 |

各行存在覆盖重叠，不累计为独立测试总数。组合测试上一轮的 1 failed / 236 passed 是 fixture
将完整 Registry 反转，触发原 P7 prefix guard；已改为只交换后继新增的末尾 output/terminal
记录，保留原 P7 prefix。增强 hardcut 单项与最终 237 项组合均已重跑通过，原 30 项失败已关闭。
reviewer 的最终 verdict 为 `accept`，范围限于本轮 QA/lineage 与对应兼容性迁移；不替代
完整 Harness、真实 driver 接线或媒体质量验证。

## Initial Failure Findings And Resolution

1. Commercial whole-ad policy 没有新 recipe 所需的 raw-generation requirement inventory。
   当前入口 fail closed，导致原本的 commercial positive lifecycle 测试无法进入后续检查。
   后续通过独立 `generation_acceptance` 解决，保留原整片要求。
2. 商品 source fixture 在 preauthor generated Shot 后留下非 fresh 的 product-reference 前驱；
   commercial approval 即使写入 keyframe FRESH，通用 dependency resolver 仍会按前驱状态
   将其降级。后续以独立登记的 fixture 输入恢复合法来源，未手写 FRESH 或放宽 reader。
3. hard-cut 的 P7 first-frame 被视频 activation 保留，但 Shot creation receipt 更新为 video
   provenance；image reader 仍要求原 image receipt，最终 reopen 拒绝。后续增加精确后继
   lineage 验证和 output/probe/provenance 篡改反例，未移除原 provenance guard。
4. Source qualification 原三个 real-committer regression 的断言必须保留；其旧 `service.start`
   fixture 尚无合法的新 qualification binding。Operator 的手写 preflight snapshot 也不能被
   宣称为实际 owner closure integration。此覆盖缺口不能靠删除测试关闭。
   后续迁移保留这些断言，使用继承的真实 `execution_proof` owner；外部 preflight 是明确的
   mock 边界。Runtime/operator 18 项与 Source/M0 proof-focused 82 项已通过。
5. 初始 checkpoint 的 driver ownership 曾阻断接线；用户随后明确交接，后续已迁移四个
   prepare/live wrappers，保留两个历史 bootstrap 和原预算/媒体记录。

## Driver And Evaluation Closure

`scripts/generation_feedback_driver.py` 从显式 typed configuration 经真实 Planner/current Project
进入共同 caller，不再依靠固定 selected capability、旧 request hash 或自制授权。
reference receipt 在 intent 前解析；当前 paid preview/authorization、service、permit 仍为执行边界。
`ai_video_mcp/generation_feedback.py` 重开并双重测量 exact fetched bytes，调用 project-local
MCP，再要求 selected evaluator 显式绑定不可变 raw response。首次写入需要 exact、一次性
进程内 proof；copy/deepcopy/reuse/换 attempt 或仅导入自称 MCP 的 JSON 均被拒绝。
已有 canonical evidence 的正常重启 replay 不重复分析/生成/Manifest write。
评估后由 durable experience 驱动下一 decision；semantic authoring 与 human judgement
仍有明确外部 owner，不伪造自动 PASS、自动 creative revision 或质量收益。

首轮全量 working-tree 测试为 `4655 passed, 6 failed, 4 skipped`；这保留为修复前历史结果。
六项失败分别来自 oversized reader/models、Planning import boundary、committer MRO expectation、
两个 compiler identity assertions 和 M0 负向 guard fixture。通过职责提取、公开类型 alias 兼容
和合法 fixture 迁移修复，没有刷新 Architecture baseline 或移除安全断言。
修复后的第一组 targeted verification 为 `28 passed, 49 deselected`；配置入口新增测试通过
真实 current Project + Planner + registered Seedance compiler，并拒绝篡改 plan。
最终修复组合为 `317 passed`（driver/review、committer structure、quality capture、M0 validation、
Planner 与 Architecture Gate）。随后补齐畸形 MCP nested JSON 的 typed validation，driver/review
组合为 `21 passed`。独立 reviewer 已确认 recording proof 和 reader/type extraction 无阻塞问题；
畸形 JSON concern 已修复，原 `reviewer_xhigh` scoped re-review 为 `accept`；独立检查
5 个畸形输入、2 个有效 structured/text 文档与不可变视图，未执行任何外部分析。

最终 exact staged snapshot 的验证 owner 为 Harness；对应路径
`.agent/harness/runs/generation-feedback-closure-20260907/receipt.json`。
必须读取 receipt 并核验 freshness / snapshot / policy / artifact hashes 才能判断通过；
上述历史 pytest 结果不能代替它。未运行真实 MCP、Provider、ComfyUI 或质量实验。

## Learning Evaluation

`distill-ai-video-learning` 自动评估结果：`no_candidate`。本记录没有新增独立媒体实验或受控
quality comparison，代码反例与 scripted transports 不能支持 Provider 质量经验采纳。
没有创建 placeholder claim、没有 adoption、没有修改历史媒体 verdict 或 RAG index。

## Next Boundary

完成 policy 要求的精确快照验证后，质量收益仍是 `not established`。
离线 qualification 分层覆盖不能替代本机真实 preflight closure。任何 live Local/Cloud quality 实验仍需
另行遵守当时授权与冻结的 empirical protocol；本记录不授予执行权限。
