---
record_kind: architecture_implementation
topic_id: preview-approval-and-identity-waiver-gate
learning_eligibility: ineligible
---

# Preview Approval And Identity Waiver Gate

Date: 2026-10-30

Status: EXECUTION_PASSED_COMMIT_BLOCKED

## Scope And Continuation

接续 Claude session `d0b7629b-ae33-4ea5-8127-a46e3c11fe32` 最后尚未完成的工程分支。用户要求先修复反复跑偏的规则与程序；本次完成预览认可与人物身份门禁的审查修复和测试迁移，不继续付费生成，不认可或重做此前现场镜头。

`43c330bc` 已包含前一会话的预览认可模块与规则修改。本次从其未提交工作继续：只拥有参考规划、相关 fixture/tests、contract matrix、参考规划文档及 Harness policy；不接管并行 motion-kit、AI city、spec 或媒体改动。

## Implemented Behavior

- 可见表演者须声明身份延续、required identity anchor，或显式 `{character_id, reason}` 豁免。preferred anchor 不满足独立身份义务；已有 identity_continuity 的必需参考也不能被 preferred anchor 降级。
- 拒绝重复豁免和与 identity_continuity 矛盾的豁免。剧情执行绑定收到 Project 时，逐个角色核对其豁免是否列入同一份已封存的 preview approval `identity_waivers`。
- Preview payload 可省略无豁免的列表，旧内容/hash 不因此改写；错误类型的 identifier 列表确定性抛 PreviewApprovalError，不泄出 unhashable TypeError。
- 电商继续使用 AdCreativePlan 的独立导演层；本次不把剧情 coverage/preview 的程序核验强行复制到电商。
- Synthetic fixture 通过原 authoring/committer 封存相符的 approval；不为真实 Canvas 示例伪造用户认可。helper 只迁移可识别的 synthetic approval，保留 custom binding。
- Harness 补齐 preview 模块及既有 dotenv_source/test 的精确路径与测试映射，没有 exemption、baseline 刷新或凭据逻辑修改；policy audit 无遗漏。未读取真实 `.env`。

Canonical contract 见 [reference planning](../shot-reference-planning.md#reference-package-before-preview-2026-10-30) 和 [contract matrix](../agent-primary-contract-matrix.md)。

## Verification Checkpoint

- 独立 code-reviewer 已审目标 tree `8d3bfcd181c529fc8dedfd2082a463e0becf65e5`（相对 `43c330bc`，22 files），结论 APPROVE；先前唯一新增 LOW unused import 已移除。
- 定向 reference authoring/planning/integration 119 passed；reviewer 的 authoring/planning/integration/performance 组合 144 passed。这些是重叠验证，不能相加为独立证据。
- 调用方组合首轮 145 passed、1 failed：voice identity helper 未封存请求所绑定的 waiver approval。修复后与 fresh quality-rejection golden、原样保留的 legacy evaluator/evidence frozen-hash 测试一起验证，3 passed。
- 修正快照的 focused 首轮实际执行生成反馈组：656 passed、1 skipped、1 failed；失败为 fresh history-import fixture 的三处固定 hash 尚未迁移，单独重算确认相同 approval/provenance 因果后修复，history-import 与 legacy no-regression 组合 22 passed。失败 receipt `preview-approval-focused-r2-20261030/receipt.json` 保留。
- 初次 focused receipt `preview-approval-focused-20261030/receipt.json` 保留于 `.agent/harness/runs/`：发现迁移遗漏后终止过时快照的本任务测试，exit -15；不是通过证据。修正快照重新逐级验证，结果另记于后续验证节点。

- 最终快照 focused-r3 整级通过：generation_feedback 657 passed/1 skipped，reference_planning 119 passed，voice 47 passed，Harness 324 passed，Canvas 366 passed，Provider 1299 passed；typed causal 由同轮 generation_feedback 覆盖。receipt `.agent/harness/runs/preview-approval-focused-r3-20261030/receipt.json`；完整性、snapshot identity、coverage 与隔离清理均确认。focused 不构成 completion/full 证据。

- Related 整级通过，receipt `.agent/harness/runs/preview-approval-related-20261030/receipt.json`；verify-receipt 确认 fresh、complete_completion_proof、coverage closure、exact snapshot 与隔离清理均为 true。最终 source tree 仍为 `8d3bfcd181c529fc8dedfd2082a463e0becf65e5`。

## Full Execution And Concurrent Writer Blocker

Full execution status passed：Python 8482 passed、43 skipped、43 warnings（4733.80s）；前端 tests/build 与 repository architecture check 也通过，整轮 13 checks passed、65 checks 按同轮覆盖关系 skipped。receipt `.agent/harness/runs/preview-approval-full-20261030/receipt.json` 的 integrity、artifact integrity、execution records 和 snapshot identity 均为 true。

提交前发现 `tests/reference_authoring_fixture.py` 另有并行 unstaged 改动：默认 preview approval 加入八个固定人物的 waiver（本地修改时间 2026-10-30 20:16:23 -0400）。它不属于被审查/测试的 tree，导致当前 `scope_worktree_clean=false`、`fresh=false`，不能把 execution PASS 当成当前工作树的完整 closure。新增改动备份为 `.agent/harness/runs/preview-approval-full-20261030/concurrent-fixture.patch`；没有覆盖、stage 或提交这份并行改动。按 AGENTS.md 的 same-file conflict 规则等待用户确认最终版本归属。当前未 commit/push。

## Fresh Fixture Hash Migration

`test_abandon_preserves_mixed_diagnosis_paid_state_and_exact_replay` 构造的是 fresh fixture。新增 approval provenance、preview binding 与 hero waiver 改变 Shot/requirement/request identity，进一步改变 source → findings → evidence/experience hash。生产序列化模块未因本次迁移修改，legacy frozen-hash 测试保持原值。

| Fresh Fixture Field | Previous Expected Hash | Current Expected Hash |
| --- | --- | --- |
| technical source | e95ebdf7eada31349c79d87a16a904948efa23d3df47ab9bd5ef27ab3976ce17 | 3e6a0ae1f86d12850545a1eef472f2461230541e4870dd62c3ea8961bc546229 |
| human source | 17b3229ff6ebcc773b509d41f3d93e0a947060abcb28c02fd5c9ac1ece81c4bf | b49d0b54d62ee464d2c09d64d51d54371537ddc341895aa7c151347655cd03ff |
| analyzer source | 010273e2b71a8610d7fa7571e93886b90a0a4f770407f1d8cc8afb2b1841dd8a | 3691ae8f75147e785102229e4c077e66cc3f12d99c7d8c2068f1c55db91bf309 |
| evidence | b82648ecefb9bf04b5cf252cdc08b2aecbae9c51f72eca7057909565404f7669 | 3da2e100242cd9cbe3b78c25b96b4c168482de851fbd1262c9342ee6865df959 |
| experience | 92251603ca9dd55e6defa94096cf46c338798398c1c190b131eb85373c27d784 | aa6b4bde74c6b98ff737f5758949779789a277143524ecf4adcdb21d331465d9 |

fresh history-import 的三项同因变更：

| Fresh Import Field | Previous Expected Hash | Current Expected Hash |
| --- | --- | --- |
| source | 9c8d3314f7809cb9707676a00d3bbc0baf530b7a38fc29f17664f278094e20ee | 2f8536a33511852c29b0d76e56daed90c7c98602e666d7fe1262f20c7351f0e5 |
| evidence | c8c3caac8757db1583c74960bc7f8b37eb4cd0660c4c3deb047e6802ba76793c | a6d933045ade09568c07bd120536c659ddbd3c6fc3751e9fc429fef5b60ad61a |
| experience | e6fd410572e83d1d5007dcdd41e188dcfb4d16f0d57ccf0326e006f429776a92 | c9d33e08a303b4934aa2849dadb956f28fce8ef4e4e609d4cc57bda72ab1599a |

## Remaining Boundaries

人物义务目前只看 performance 的 visible 声明；preview artifacts 尚未逐一绑定实际 Provider 输入；无 source_project 时仅做结构检查。M2/M3/M4 是明确保留的缺口，不是本次已修成果，也不允许作者利用它们跳过实际预览或隐藏人物。

没有 Production 媒体生成、付费调用、激活、发布或人工验收证据。旧现场镜头的历史 Agent PASS 不代表用户认可；声音、反应、连续性及完整审片问题不能由离线工程 PASS 关闭。

自动评估 `distill-ai-video-learning`：no_candidate；本次为单个工程实现/回归分支，没有新的独立媒体实验，不创建 Learning Claim 或改写全局记忆。

RAG 索引没有另行刷新；当前 freshness 未验证。
