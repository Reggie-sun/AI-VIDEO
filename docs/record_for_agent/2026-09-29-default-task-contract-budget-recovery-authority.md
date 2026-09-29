---
record_kind: session_summary
topic_id: default-task-contract-budget-recovery-authority
learning_eligibility: ineligible
---

# Default Task Contract, Budget And Recovery Authority

Date: 2026-09-29

## User Decision And Scope

用户明确要求任务内“改变共享契约、预算或恢复规则”默认授权，不再逐项请求批准。本次修改 authorization routing，未修改 generation runtime、Manifest、模型或媒体，未开始新的视频 attempt。

## Applied Rules

- `/home/reggie/.codex/AGENTS.md`：任务内 shared contract、有限次数/时间窗口/repair ceiling和 recovery规则由 Parent自主评估、self-review、实现、验证及记录；written spec的默认任务授权不再要求用户逐份批准。
- `AGENTS.md` 的 `Decision Gates`及 spec/plan、paid-ceiling说明：同一任务目标内有依据的有限扩展默认授权；必须保存 predecessor、old/new bounds、真实消费和停止条件，不能删除历史或重置 consumed grant/permit。扩大 Provider/inputs/egress、发布、真实目标扩张或 destructive/irreversible操作仍需对应授权。
- `.agent/context/control-plane-playbook.md`：指向唯一规则 owner，移除旧 spec机械审批及 ceiling耗尽后仅因预算变更停止询问的路径。
- `/home/reggie/.codex/SUBAGENTS.md`：默认三轮 review耗尽后先调查，再自主记录有依据的新有限预算；保持历史轮次、失败 receipts和连续两次运行故障后的 native fallback，不通过加预算循环故障调用。

保护语义仍保留：local-first、secret/crash safety、Budget Guard、Cloud Egress、canonical ownership、provenance、replay、one-use、unknown-outcome fail-closed以及真实媒体质量验收。规则修改不能代替 canonical runtime contract实现。

全局 owner是 `/home/reggie/.codex/AGENTS.md`，SHA-256 `638ab0e04593c071d025736907bf9f20f0786081ddbe460360abb42d9b932153`；`/home/reggie/AGENTS.md`是不同的 workspace pointer，不能将二者 hash不同当作 source drift。修改后的 global `SUBAGENTS.md` SHA-256为 `d716328df2bb7c990a71fef8336560fc4844a7f7dafc46fecb47838542a5e5e6`。这两个仓库外文件已实际落盘，但不属于 AI-VIDEO Git commit。

## Verification And Review Evidence

Evidence root：`runs/default-task-authority-20260929-001/`。

初始 exact staged tree `e10a21eaf9e7027ae5a8d6c3343d3bf249df4eb9`的8项 routed checks通过，见 `policy-verification.json`。安全保护措辞补充后的 staged候选及 source hashes见 `policy-verification-round2.json`：documentation gate、policy audit、diff checks通过；runtime-skill tests 2、harness tests 261、open-video tests 48、seedance tests 8均通过，合计319个 tests。

默认 `architecture_gate check`报告历史基线上的1 error、26 warnings、15 infos；此次没有任何 `src/`变化，task delta `--base-ref HEAD`为0 findings/PASS。两种结果均保留，没有刷新 baseline或把历史问题当作本次新增 regression。明确禁止 worktree，故使用 direct checks，`canonical_harness_receipt=null`，不声称取得 canonical Harness receipt。

受管 Kimi review invocation `c4186d11-c6a1-420c-a41c-ebe95dfb11ac`、seal `9347ad9c6637a09606ceb338a799411581734b1b3f02f9d91e20b073c40d8f2e`实际 PARSED；392.105 s、4 wire requests、k3/max，qualified Docker route与 artifact hashes、完整 Read均已核验。`review-round-1-receipt.json`、`review-round-1-report.json`、`review-round-1-adjudication.json`保存 evidence和 Parent裁决。F1安全保护措辞已补齐；F2指出的全局路径混淆已由不同真实 owner及 hashes纠正。报告未审查后来补充的 global review预算段落，不宣称旧审查覆盖新 bytes。

窗口随后切换为 restricted filesystem/network，宿主机 state写入不在 writable roots，新的受管 Kimi seal/复核未执行。Final independent re-review尚未完成；这是当前环境限制，不是等待用户批准变更。初轮报告不升级为修改后全部 bytes的 Kimi acceptance。

受限环境里的最终复测：diff、documentation、policy及 task-delta Architecture Gate仍通过；runtime-skill 2、open-video 48、seedance 8通过。Harness组为260 PASS/1 FAIL，`test_network_guard_installation_blocks_external_dns`在创建 UDP socket时被OS拒绝（`PermissionError: [Errno 1] Operation not permitted`），尚未运行到该socket的 guard断言；之前同一组261 PASS保留，不能将最终复测描述为全PASS。Exact logs见 `final-*.log`。受限复测脚本的 `git write-tree`及一次 `git add`也因 `index.lock`只读失败；之后普通独立 `git commit`实际成功为 `41b02d9`，6个 owned repository files已提交，unrelated config未纳入。Git结论以该实际结果为准，不把部分命令的沙箱拒绝当作宿主机Git损坏；本记录随后同步这些真实边界。

## Media Boundary And Supersession

[COCO / Nosha当前记录](2026-09-28-reference-capabilities-and-local-canvas-method.md)及[第四份repair技术草稿](../superpowers/specs/2026-09-29-coco-nosha-fourth-runtime-repair.md)里的人工 approval blocker被本次 standing authorization取代；旧授权 chronology保留。技术候选仍需 Parent完成 source核对、self-review、plan、实现、GPU验证与适用审查，不能仅凭规则文件签发 cap4 grant或重用 consumed permit。

本次未增加视频 submit/fetch/activation。上一已验证 checkpoint仍为4个 known FAILED physical submits、0 MP4、3份 consumed repair grants，MLP GPU OOM尚未修复；不能把治理记录当作视频完成。

## Learning And Publication

`distill-ai-video-learning`评估为 `no_candidate`：这是用户设定的默认授权决策，不是独立重复实验或 controlled comparison，不创建经验 claim、不制造再次确认步骤。没有为了记录新增 Provider/media、网络或测试；上述 Kimi及 checks用于实际规则变更验证。未更新 RAG index，未写 memory folder，未 push/release；unrelated `.codex/config.toml`保持原样。
