# Explicit Local Generation Budget Renewal Proposal

## Status And Authority

**SUPERSEDED — 2026-09-28**：用户明确纠正本地无累计额度。当前源码已有 `local_total_limit=None`，应按[local limits correction](2026-09-28-local-unmetered-generation-limits.md)修正 prior-local ceiling gate；不实施本文提出的新 ledger / Manifest migration。下文保留未批准 proposal 的历史，不再请求一次性 quota renewal 批准。

`PROPOSED — NOT APPROVED / NOT IMPLEMENTED`。此文只提出解除当前 canonical quota blocker 的具体 contract，不授权新的 submit。既有 17 s creative scope 已获批准，不需要重复批准；本次待批准的是 local submit quota 的显式续期与对应持久化 contract。

## Verified Problem

COCO／诺萨原 task `user-approved:coco-nosha-local-17s-20260928` 的 initial 1 + repair 1 已消耗，两次均 known terminal OOM，没有 MP4。2026-09-28 sampler recovery 已通过隔离 Triton kernel 的 GPU boundary tests；准备 `coco-nosha-attempt-03` 时，`GenerationFeedbackOrchestrator` 接受了 batch review hash，但 `ProductionStateCommitter._require_persisted_generation_limits` 在 local intent / permit 写入前拒绝：`Generation submit ceilings cannot expand within one task.`

当前执行代码还明确拒绝用 bare batch review hash 重置 durable counters。attempt-03 仅有 prepared generation state / execution binding，没有 local submit intent、permit、submit receipt 或 Provider job。旧两次 submit 和 failure evidence 保留；没有 unknown video outcome。

## Goal And Scope

在同一 task / Shot 下，通过 sole committer 持久化一次 exact、one-use 的 local renewal，让累计上限从 **2 到 3**，仅增加 **1 次**采用已验证 kernel 修复的真实本地生成。累计 counters 保持 **used=2**；batch 上限同样从 2 到 3，不做计数 reset。新增部分 elapsed ceiling=7200 s、active prompt wall ceiling=5400 s。若第三次仍为 runtime failure 或 unknown，停止；无额外 quality-repair submit。

这不是 paid quota、新的 Provider route、queue subsystem 或自动 recovery。原 17 s / 408 frames / 24fps、正常速度、一镜到底、完整因果、三图/原声线、profile/model/weights 与全部验收要求保持。

## Ownership And Durable Contract

`ProductionStateCommitter` 独占 renewal 写入和消费；receipt 只保存 immutable facts，Manifest pointer 保存 consumed lifecycle。复用既有 execution-binding / local intent / one-use permit 原子事务，不新增 writer。

不可变 renewal receipt 必须绑定：same task / project / registry / Shot / graph / rubric / profile identity；旧 execution bindings、两次 exact failure experiences 与完整 reviewed-batch evidence hash；旧 cumulative/batch ceilings=2、新 ceilings=3、durable used=2；actor、repair basis、隔离 runtime package manifest / launcher / kernel-verification hashes；新的 target attempt / exact execution binding、当前 Manifest revision、续期 wall bounds。

sole committer strict reopen 全部 evidence 和 registered bytes，确认旧 attempts terminal failed、queue/prompt outcome 已知、目标 attempt 尚无 intent/permit、remaining runtime repair grant 未消费，才可登记。提交时重验 identity/freshness/剩余额度，并在同一 atomic local-intent write 中将 renewal pointer 和 runtime-repair pointer 标为 consumed。没有 receipt、receipt 陈旧或不匹配、重复消费、unknown、扩大到非 loopback/remote/metered/paid，一律 fail closed。

当前全局 `MAX_RUNTIME_REPAIRS_PER_SHOT=2` 保持；已有一次 consumed，另一次已登记未消费，不重置或增加。当前 attempt-03 的旧 binding 保留为 blocked preparation evidence，不能改写为已执行；恢复提交应使用新的 attempt / request identity，并严格保留前序 history。不得通过换 task ID、清空 history、复用 permit 或直接 POST 绕过 gate。

## Compatibility And Rollback

Manifest / pointer / receipt 的 additive version 与 migration 必须走既有 schema capability registry、standard loader 和 sole committer；旧 schema 默认不接受新 pointer。旧 bytes、reader serialization 和既有无 renewal 的 submit 行为保持。由 implementation plan 核对当时 registry 的最新 version 并封存明确版本；批准此 proposal 前不迁移当前 project。

rollback 只停用新 renewal capability；保留已登记/已消费 receipts、prepared attempts 和旧失败，不能删除消费证据或反向恢复可用额度。不能把恢复后的原 ComfyUI 服务健康当作 media acceptance。

## Acceptance And Verification

先完成 executable tests：同 task exhausted 默认拒绝；完整 renewal 仅放行一次且 used 不归零；identity/hash/actor/revision mismatch、缺证、tamper、double-use、unknown、remote/paid、超过第三次均拒绝；intent crash/replay 不重复效果；Manifest migration/serialization 与旧 local/paid/Production family 行为不回归。exact snapshot policy verification 和适用 T3 dual independent review 完成后，才接通一个新 submit。

每次 exact MP4 落盘后显式调用 project-local `video-analysis`，保留 PASS / FAIL / NOT_EVALUATED 与完整观看/实际聆听边界。没有 MP4 不运行 analyzer。无 automatic activation / P6 / Final Acceptance，交付实际视频和真实缺项。known terminal / queue empty 后恢复临时服务。

## Self Review

本 proposal 修复的是 caller-side batch review 与 committer-side persistent ceiling 之间的缺口，不将一个 hash 当作已验证续期。它明确增加一个 submit，因此属于 repository Decision Gates 的 persistent contract / runtime slice 变更，不能从“继续”、local exemption 或此前时长批准自动推导 implementation approval。当前没有声称 receipt、migration、T3 review 或实际第三次生成已经完成。
