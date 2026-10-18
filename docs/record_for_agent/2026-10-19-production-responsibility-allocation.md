---
record_kind: architecture_implementation
topic_id: production-responsibility-allocation
learning_eligibility: ineligible
---

# Production Responsibility Allocation Record

Date: 2026-10-19

## Current Result

通用制作分工工程已实现并发布，源码 `d08200901d242de634c4ab82487726c75b87f747`，tree `725d90a14379b23ae5f0825cd523c646f7fe023f`；push 后核验远端 `main` 为同一 SHA。实现沿既有 QA、ProductionIntent、Planner、compiler 和最终验收 owner，不新增 timeline、renderer、状态库、依赖或故事执行脚本。

本轮只有工程、离线编译及只读预览，真实图片/视频/音频 POST 为 0；没有新的音频理解、实际成片听看或模型质量验证。既有消费和授权没有重置或挪用。《界蚀》S01 仍 STOP，S02 POST0；机器人旧开发预览的人工接受不变，也没有因此取得 Production qualification。

合同与操作分别归 [spec](../superpowers/specs/2026-10-18-production-responsibility-allocation.md)、[plan](../superpowers/plans/2026-10-18-production-responsibility-allocation.md)、[workflow owner](../canvas-production-harness.md#production-responsibility-allocation) 和 [matrix](../agent-primary-contract-matrix.md)。本文固定实现、证据与适用边界。

## Shared Runtime Changes

- 新 QA publication 和当前策略使用共用 `production_allocation_issues`。声明 raw 的硬目标始终有 component 承担，assembly 重叠不免除原片验收；生成 rubric 保留其 observable、proof、tolerance、measurement，不能用 hint、后期条目或同名的较宽结果代替。source-only 仍经既有 exact source-use owner 取得用途资格。
- assembly 绑定既有 FinalOutputContract 的同 ID、同 observable。post 目标保留原 final-owner proof 映射；raw 原证明由 component/source-use 保留后，可以另加不同的 final proof，例如原片技术检查加成片人工验收。两层证明不互相替代；marked final/source-reference 校验保持严格。
- `author/preflight`、可选制作准备报告及原生输入预览展示固定来源、允许变化、职责、缺项和实际选择。缺 intent/allocation 明确报告，不把全局 QA 自动套给每镜，不猜测放宽或改 stage。实际 source map 只投影原 owner 的数据。未实现的 MASK_COMPOSITE、TRACKING、LIP_SYNC 仍是 capability blocker。
- 默认 CLI/Python `prepare_production` 返回原 immutable Decision；显式 `include_control_report=true` 才返回 `{decision, production_control}`。旧 policy bytes/hash、反序列化和历史 lineage 重开保持兼容；不完整旧分工的新使用会阻断。材料化后的预览经 `production_parent_context` 读取 retained canonical parent。
- 非 raw/diagnostic 条目不再从 intent paths 派生模型文本。未标记的旧 diagnostic 不阻断编译，真正 raw 输入缺失仍拒绝。原用户 prompt 与 explicit input-control 合同不被自动删改。

这些是职责、输入与验收工程约束，不保证模型遵守；也不把原片 FAIL 改成编辑用途或成片 PASS。

## Verification And Review

以下是连续源码范围的适用 Harness；不把重复测试或多个 receipt 计为独立模型实验。每份 `source-freshness.json` 均在其绑定源码快照核验 integrity、freshness、complete_completion_proof 后保存，不能冒称旧 receipt 对后续 HEAD 仍 fresh。

| Source range | Receipt | Result |
| --- | --- | --- |
| `5057f0c..7720246` | [initial source](../../.agent/harness/runs/production-responsibility-20261018-r2/receipt.json) | 23/23 checks PASS；Architecture 0 findings |
| `7720246..1d05014` | [API compatibility](../../.agent/harness/runs/production-responsibility-compat-20261018-r1/receipt.json) | 7/7 PASS；Canvas 291 PASS |
| `1d05014..c823c05` | [first review fixes](../../.agent/harness/runs/production-responsibility-review-fixes-20261018-r1/receipt.json) | 18/18 PASS；Canvas 292 PASS |
| `c823c05..d082009` | [final raw/proof ownership](../../.agent/harness/runs/production-responsibility-raw-ownership-20261019-r2/receipt.json) | 17/17 PASS；Architecture 0 findings |

最终范围包含 generation 534 PASS / 1 SKIP、strategy 125 PASS、final-output 63 PASS、Provider 976 PASS、preserved-source 92 PASS、review 664 PASS、visual 69 PASS、neutral requirement 450 PASS。唯一 skip 因隔离 checkout 不带历史 run archive；自包含 fixture 仍执行，不把 skip 算成历史媒体通过。

专项最终组合 96 PASS，覆盖 publication 写入前拒绝、实际 Planner 无 attempt 拒绝、legacy 重开、raw/assembly 漏项、同 ID predicate 替换及两层独立 proof。H3 Max/Seedance 的实际离线 compiler 11 PASS；responsibility preview 13 PASS；Canvas data 29 PASS。三组人物/动作/空间文本用例走同一编译路径，底层 fixture 不是三个独立真实人物或媒体实验。

Risk Gate 为 NATIVE_REVIEW_REQUIRED：验收职责遗漏可丢失原硬目标，fixture 后仍需独立核对跨 owner 语义。只使用同一 read-only native `reviewer_xhigh`，实际 agent `/root/responsibility_review`，三轮 target 依次为 `1d05014`、`c823c05`、`d082009`，未重置轮次。第三轮 finding set 为空；Parent 结合当前源码、可执行回归和 Harness 关闭以下已 CONFIRMED 问题：

| Finding | Repair and closure evidence |
| --- | --- |
| PRA-001 | post 的同 ID 结果/proof 替换，以及 assembly 豁免 raw 的缺口均关闭；Parent 补测还封住组件 raw predicate 替换。真正 raw＋final 重叠与独立附加 proof 保持合法。 |
| PRA-002 | 旧 unmarked diagnostic 不再误拒编译；两个 compiler 的真实 raw fragment 缺失仍返回 unsupported。 |
| PRA-003 | revise→materialize→preflight 保留 canonical parent revision/hash、目标和分工；不向第二个无 intent 的 Shot 自动分配全局 QA。 |

审查与 Parent 裁决见 `runs/production-responsibility-20261018-001/native-review-round-001.json`、`native-review-round-002.json`、`native-review-round-003.json`。修复前 raw 回归 10 FAIL，附加 proof 过严回归 3 FAIL，日志和 hash 保留在同目录 `raw-proof-regression-evidence.json`。过严中间候选 `ad98523` 的 Harness 被显式中止；其 `parent-abort.json` 明确不是完成证明。早期 whitespace 失败 receipt 也保留。静态审查不构成实际运行或媒体接受。

## Existing Project Previews

《界蚀》实际共享 preflight 在源码 `7720246` 执行，证据为 `runs/production-responsibility-20261018-001/jieshi-preflight.json`、`operation-proof.json`、`readiness-summary.json`。全部 15 项仍在 selected QA，S01/S02 均为 REQUIRES_PRODUCTION_INTENT；S02 的 future accepted source 仍未绑定。Manifest SHA `1ece69263041eb06d345e5673f010a2b209e67a1e2fea82c2002e12a2b982e60` 前后相同，并在最终源码点再次只读核对一致。A 的 6 PASS / 2 FAIL / 7 NOT_EVALUATED、S01 STOP、S02 POST0 未变。

机器人既有 A/V 开发预览在最终源码 `d082009` 经标准 loader 只读投影，见同证据根 `robot-current-responsibility-preview.json`。该项目的 source-shot 也尚无 ProductionIntent，报告 allocation_count=0、selected candidate 为空，Manifest 前后相同、POST0。不能从已渲染画面反推一份获批分工；也不能将报告的 actual_quality=NOT_EVALUATED 解释为撤销旧人工接受。[原人工和工程证据](2026-10-17-edit-first-temporal-control.md#current-result) 保留其自身边界。

两次重开只是当前工程/authoring readiness 证据，不是新模型样本。现有字段和执行能力不等于具体项目已经正确声明、绑定并验收它们。

## Publication And Remaining Boundary

源码已按 owned paths commit/push main 并核验 SHA。八份 foreign staged/dirty/untracked 文件的 bytes 及原 staged diff hash 保持不变，没有纳入本任务提交。本文及《界蚀》直接关联 notice 的文档 checkpoint 使用 `.agent/harness/runs/production-responsibility-record-20261019-r1/receipt.json`，publication 以其绑定提交与 Git 远端核验为准。

通用工程成立不证明通用模型质量、单镜通过、连续镜、完整故事或新 human 验收。下一真实验证建议限定为一个不同场景的一镜、一次生成、零重抽：raw 核验身份/动作顺序/可用终态，现有剪辑承担显式成片时限，非固定手势作为允许变化，再逐层验收原声成片。开始前仍须准备并封存 exact model/mode、参考 bytes/职责、白模处理、native preview 和新的有限授权；本建议不是已批准输入或新许可，不沿用任何旧 grant。

## Learning Evaluation

按 `record-ai-video-session` 创建本主记录并更新直接关联旧记录，自动执行 `distill-ai-video-learning` 评估为 **no_candidate**。本轮是确定性工程回归和既有状态投影，不能把 fixture、不同 proof 层或同源旧预览拆成独立模型实验证据；没有创建占位 Learning Claim 或自动采纳模型经验。工程合同与 Harness routing 按本任务授权实施，媒体 Gate 未放宽。未执行独立 RAG index 重建或刷新。
