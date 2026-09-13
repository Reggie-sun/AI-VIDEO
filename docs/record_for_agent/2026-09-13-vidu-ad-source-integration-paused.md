---
record_kind: architecture_implementation
topic_id: vidu-ad-source-integration
learning_eligibility: ineligible
---

# Vidu Ad Source Integration Record

Date: 2026-09-13

## Resumed Completion

用户随后要求“继续”，本轮恢复收尾。代码已提交至本地 `main`：
`61c05f443fedb988eaaaa66f8f612eff1d0fed25`；没有 push 或 release。
提交内容与通过验证的 exact snapshot 相同，原有 staged patch 与其余 working-tree
内容保持不变。以下原暂停记录保留为历史，原 ownership 等待与 policy audit 阻断已解除。

本轮只补齐 policy 与 matrix 的缺失路由：原始视频帧 import 归既有 image tests，
既有 paid video reconciliation 使用专属16项测试及原 provider tests；未修改这三个
文件的 runtime 实现，也未把 video reconciliation 扩展到广告请求。

完整 Harness receipt：`.agent/harness/runs/vidu-ad-source-20260913-v5/receipt.json`。
在 detached exact-commit 验证环境中执行 `verify-receipt`，`fresh`、`integrity`、
`artifact_integrity`、`coverage_closed_same_run` 和 `complete_completion_proof` 均为 true。
共享脏工作区不是该隔离快照，不将其剩余 voice 修改描述为已通过本次验证。

- Production contract suite：3408 passed、3 skipped、1651 deselected。
- 广告测试51 passed；既有 Vidu tests154 passed；Harness tests225 passed。
- 其余 policy-required checks、Architecture Gate 与 policy audit 全部通过。
- 独立 `reviewer_xhigh` 对本轮路由补齐复审为 accept。
- 补充执行 reconciliation tests：16 passed。

记录使用 `record-ai-video-session` 更新，自动 `distill-ai-video-learning` 评估仍为
`no_candidate`：本轮只有确定性的实现与离线验证，没有新真实广告实验。
后续仍需使用已接受的素材与 task authorization 完成真实 Provider 生成和成片验收；
本次没有 live/paid submit，没有可交付广告视频。RAG 索引未主动刷新。

## Historical Paused Checkpoint

以下内容描述恢复收尾前的状态，不代表当前阻断或最新验证结果。

## Scope And Ownership

用户要求接入官方 `ad-one-click`，服务于“潜江市浩口9号电动车”广告。
实现范围为显式 prepare / submit / query / fetch，输出待验收整段广告素材。
没有新增 CLI、自动激活、第二 timeline、renderer 或 Provider fallback。
官方接口没有 `model` 选择字段，不能宣称请求明确指定了 Q3。

用户批准保留现有改动接手相关共享文件；随后发现新的并发 voice 修改，用户明确要求
先让其他会话完成，暂停修改 `_state_commit_paid_provider.py`。收到此指令后未再写入
该文件。当前任务没有正式 commit、push 或 release；验证使用 unattached Git snapshot，
没有移动 `main`，原有 index 和无关 working-tree 改动保持不变。

## Implementation Boundary

`vidu_ad_wire.py` / `vidu_ad_provider.py` 复用既有 Vidu transport、credential supplier
和下载校验。`_StateCommitAdMixin` 仍属于唯一 writer `ProductionStateCommitter`，
复用既有 paid reservation、durable intent 和 one-use permit。

`vidu_ad_contracts.py` 保存 sealed request、有限 task submit ceiling 与待验收素材身份。
`_provider_manifest_fields.py` 负责 explicit Provider 字段的版本准入；广告状态要求
Manifest 2.16，旧版本 typed/mapping 输入均拒绝，旧序列化不新增空字段。
`vidu_ad_reader.py` 从既有 paid reader 入口重验 request/profile、registered inputs、
paid joins 和下载 bytes，包含尚无 paid budget 的 prepared request。

下载成功只表示未验收 MP4 source bytes；未证明解码、内容质量、真实车型一致性、
品牌优势、地点文字或成片可交付。`outcome_unknown` 保留预算并禁止自动重试，当前广告
没有 reconciliation / 恢复提交入口，既有 paid video reconciliation 不适用于广告。
完整用法与限制见 [Vidu ad provider](../vidu-ad-provider.md)。

## Verification And Evidence

基线：`651c8809a16220862ccfe0b196539a5b6a5f9eb6`。
最终 task-only verification snapshot：`5e97e04de26a667a7f89d10a2607f0abdddc2605`。
快照从 HEAD 加本任务 delta 构建，排除同文件中的既有及并发 voice 修改。

- 最新 production code snapshot 的 focused tests：462 passed，覆盖广告协议/lifecycle、
  Vidu、paid-provider E2E、Manifest models 与 committer 结构。
- Architecture Gate 相对基线：PASS；通过责任拆分消除本次 models/project 增长问题。
- 随后修复 policy、统一广告测试文件为 `test_production_vidu_ad_*.py`。最终快照的
  Harness tests 与广告测试：204 passed / 1 deselected；明确排除已单独执行且失败的
  baseline unmapped policy audit，没有将排除后的结果描述为完整 Harness PASS。
- native `reviewer_xhigh` 独立检查发现旧 schema typed-input 漏检，主线程修复后复审接受。
- 旧快照的广泛检查主动停止于 1410 passed / 4 failed；其中3项本次 policy 问题已修复，
  其余是基线 policy audit 缺口。这不是完整测试套件 PASS。
- 最终 Harness：FAILED，停止于 policy audit；不存在 fresh passing receipt。

失败 receipt 与测试/架构证据保存于
`.agent/harness/runs/vidu-ad-source-20260913-v4/`。
其中 `task-clean.patch` SHA256：
`e2f66bf4284b41124e3ab780697a5011b4f0be75b3a48fea80f6be785b543381`。
这些为本地 ignored evidence，不是发布或质量验收证明。

## Remaining Blockers

1. 等待用户确认其他会话完成后，才能恢复共享 paid 文件的写入与最终 task commit。
2. 基线已有3个未映射路径：`src/ai_video/production/image_import_video_frame.py`、
   `src/ai_video/production/paid_provider_no_effect_reconciliation.py`、
   `tests/test_paid_provider_no_effect_reconciliation.py`。当前任务未修改这些文件；
   不能通过刷新 baseline 或删检查伪造 Harness 通过。
3. 解除阻断后重新核对所有 target-file ownership，按届时精确任务快照完成 Harness、
   task-only commit。当前共享工作区的结果不能替代该快照证明。

本次没有执行 live/paid Provider 调用、广告视频生成或 Production activation。
本记录未更新 RAG 索引；自动 learning evaluation 为 `no_candidate`，没有足够的独立
真实广告实验支持新的跨实验规则。
