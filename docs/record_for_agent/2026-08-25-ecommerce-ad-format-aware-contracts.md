# Ecommerce Ad Format-Aware Contracts Record

Date: 2026-08-25

## Purpose

本文记录 `ecommerce-ad-workflow` 的 contract simplification checkpoint。该 Skill 继续只负责电商广告 authoring；本次没有增加 Provider execution、Production Runtime、Manifest / activation、Final Acceptance、广告效果预测或 AI comic ownership。

## Session Work And Decisions

Commit `93b6fa3f193ad3cc0ef5a1dd476e685c3c32521d` 将 package contract 升级为 `ecommerce-ad-workflow/package/2`，并完成以下收敛：

- master package 的 `creative_variant_matrix` 可缺省；只有显式 creative experiment 才验证 variant isolation。
- `prohibited_claims` 字段仍必须存在，但允许 `[]`，避免为通过 schema 编造商品级禁用 claim。
- package 保留 exact `ad_format`，由 shared gates 加 format-specific profile 验证六种广告格式。
- `motion_graphics_product` 等 talent-free authoring 允许空 `talent_plan`、空 `set_plan`、无 dialogue Hook；只有实际存在的 talent / set 才能投影 `Character` / `Scene` proposal。
- package validation 必须提供 exact `--source-input-file`，并绑定 canonical input SHA-256、Product Truth、format、duration、aspect ratio、audience、pain point 与 objective。
- `BLOCKED_BY_TRUTH_OR_RIGHTS` 自动阻止 authoring readiness；source input 在同一 validation 中只读取一次。

`SKILL.md` 与 references 保留 G0-G7：Product Truth -> Strategy -> Hook / Beats -> Product Presentation -> Copy / Audio -> Storyboard / Shots -> Runtime Handoff -> Ad QC。Runtime Handoff 仍只输出 proposals、requirements 与 classified gaps，不拥有 execution 或 acceptance。

## Verification And Evidence

对 exact task files 的验证结果：

- `ruff format --check`：4 files already formatted。
- `ruff check --ignore E402`：PASS；`E402` 仅用于保留 validator 现有 local import bootstrap。
- `python -m pytest -p no:cacheprovider tests/test_ecommerce_ad_workflow_skill.py -q`：`83 passed`。
- example input validator：`status=valid`。
- example package validator 携带 exact `--source-input-file`：`status=valid`。
- `git diff --check`：PASS。
- 独立 `reviewer_xhigh` scoped re-review：`accept`，无 blocking issue 或 non-blocking concern。
- 在固定 checkout `93b6fa3` 的隔离 clone 中，`python -m scripts.architecture_gate check --base-ref 7cc4ee6`：PASS。

Harness 对 exact range `7cc4ee6..93b6fa3` 生成 receipt：

`.agent/harness/runs/ecommerce-ad-workflow-format-gates-20260825/receipt.json`

该 receipt 为 `failed`，不能作为 completion proof。`scope_diff_check` 与 `docs_contract_check` 通过；`policy_audit_check` 因前一提交 `7cc4ee6` 已引入的 11 个 unmapped commercial production/test paths 失败，后续 checks 被 fail-fast 跳过。在同一 exact checkout 手动运行被跳过 checks 时：

- `task_architecture_gate`：PASS。
- `ecommerce_ad_workflow_skill_tests`：`83 passed`。
- `harness_tests`：`183 passed, 1 failed`；唯一失败仍是相同的 repository policy coverage debt。

本任务没有修改 `.agent/harness/policy.yaml`，也没有把并行 commercial Runtime 工作纳入本 Skill commit。

## Current Boundary And Remaining Risk

- `93b6fa3` 已提交在 local `main`；本记录创建时未 push 或 release。
- Contract tests、examples、architecture gate 与独立 review均通过，但 fresh passing Harness receipt 尚未闭合。
- 待 owning control-plane change 合法映射上述 commercial paths 后，应对 immutable commit range 重新运行 Harness；不得通过把无关 policy changes 并入本 Skill commit 来伪造 closure。
- 本次没有执行 live Provider、媒体生成、Runtime activation、P6 或 Final Acceptance，也没有刷新独立 RAG index。

## Agent Guardrails

- `package/2 valid` 只表示 Ecommerce authoring contract valid，不表示媒体已生成、可观看、已接受或可投放。
- `ad_format` profile 是 authoring Gate，不是 Provider 或 renderer routing。
- 空 `prohibited_claims` 表示已审查且没有商品级禁用项，不表示通用广告政策失效。
- optional creative variants 不得被解释为跳过 master strategy 或 Product Truth。
- 当前 failed receipt 必须如实保留；手动 focused checks 不能替代 fresh passing Harness receipt。
