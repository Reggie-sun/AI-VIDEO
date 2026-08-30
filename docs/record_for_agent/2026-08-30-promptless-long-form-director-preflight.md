---
record_kind: architecture_implementation
topic_id: promptless-long-form-director-preflight
learning_eligibility: ineligible
---

# Promptless Long-Form Director Preflight Record

Date: 2026-08-30

## Purpose

本文记录 `PROMPTLESS_REQUEST` / `PROMPTLESS_LONG_FORM` Director preflight 修复。目标是阻止
“用户只给时长和 Seedance target、没有 creative brief”时，Agent 直接把空 brief 降级为一个重复慢运镜，
再用 `VIDEO_EXTEND`、`no cut` 或 `uninterrupted` 补足时长。

本记录描述 Development control-plane implementation，不是 Provider/runtime capability promotion，
不证明 Seedance 的真实媒体复杂度、prompt adherence、P6 或 Final Acceptance。

## Root Cause

修复前虽然 `.agent/context/control-plane-playbook.md` 已要求 Creative Skill Preflight，
但 `open-video` 的 discovery description 只覆盖 concept、script 和 reference-led input，且 Gate 没有
对 duration-only / promptless request 建立可执行的 coverage contract。Agent 因此可以先自行写一个
保守 Shot Contract，再由 `seedance-authoring` 忠实适配该简单 Shot。

初版修复曾把 `PROMPTLESS_LONG_FORM` 绑定到 selected Provider 的单 Shot 技术上限。独立
`reviewer_xhigh` 指出 `doubao-seedance-2-5-260628` 当前 capability 支持单次 `30s`，这会让 exact
“Seedance 2.5 + 30s + no creative brief”继续绕过 Director coverage。最终 contract 将 creative
threshold 与 Provider ceiling 分离。

## Implemented Contract

Implementation commit `a9b0dc0522e995573a2a6f706b637d075c531d2e` 与 final wording alignment
commit `01c9d306526d7fd75d6e244988821734965a98fa` 实现以下边界：

- 所有缺少 user creative brief 的 request 都是 `PROMPTLESS_REQUEST`，必须先进入 `open-video`；
- duration `>15s` 使用固定 creative threshold 分类为 `PROMPTLESS_LONG_FORM`，Seedance 2.5 单次支持
  `30s` 不构成豁免；
- `.agents/skills/open-video/scripts/validate_director_coverage.py` 只验证 Agent-side coverage 结构，
  不接收或声称证明 Provider duration/mode capability；exact capability 仍由 current profile owner 校验；
- long-form coverage 必须包含多个 ordered units，并为相邻 units 改变 finite `beat_function`、
  `shot_scale` 与 `camera_treatment`；`objective` 与 `visible_change` 不得通过标点变化伪造差异；
- 普通 promptless long-form 不允许用 `VIDEO_EXTEND` / no-cut treatment 代替 coverage；只有用户明确
  要求 single take、且保留直接 user-request evidence 时才允许 continuous transition；
- finite category 只要求 adjacent diversity，允许 120s 等长片在不相邻 units 合理复用镜头语言；
- `runtime_skill_calls = 0` 保持不变，Product Runtime 不 import 或调用 Agent Skill/validator；
- canonical playbook path 已加入 focused Harness routing，后续修改 Gate owner 会自动选择 OpenVideo、
  Seedance authoring、runtime-boundary、Architecture Gate 与 Harness checks。

## Verification And Review

Focused working-tree verification：

```text
193 passed
Documentation contract gate passed
Harness policy audit: no unmapped, unverified, missing, or unreferenced paths
skill-creator quick_validate: Skill is valid!
```

最终 `reviewer_xhigh` scoped re-review verdict 为 `accept`，无 blocking 或 non-blocking concern。
Reviewer 特别复核了 native-30s bypass、caller-supplied capability spoof、重复 camera treatment、长片
non-adjacent reuse、transition failure branches、Harness routing 与 Product Runtime isolation。

Exact commit-range Harness：

- scope: `bab9560ddd507be0a7e8400b9b350b3d3d40e322..a9b0dc0522e995573a2a6f706b637d075c531d2e`
- receipt: `.agent/harness/runs/promptless-director-20260830-v1/receipt.json`
- selected checks: `scope_diff_check`、`docs_contract_check`、`policy_audit_check`、
  `product_runtime_skill_boundary_tests`、`task_architecture_gate`、`harness_tests`、
  `seedance_authoring_skill_tests`、`open_video_skill_tests`
- result: all 8 checks passed
- receipt verification: `passed=true`、`fresh=true`、`complete_completion_proof=true`、
  `snapshot_matches=true`、`workspace_cleanup_confirmed=true`

Final canonical-wording alignment 另以 exact range
`ef7d6de50912836fdfe1e7924a618e7e39a1aa31..01c9d306526d7fd75d6e244988821734965a98fa`
验证，receipt 为
`.agent/harness/runs/promptless-director-threshold-20260830-v1/receipt.json`；全部 selected checks
通过，receipt verification 同样满足 `fresh=true` 与 `complete_completion_proof=true`。

## Evidence Boundary

本次没有调用 Provider、没有生成媒体、没有修改 Manifest / Registry / P6 / Final Acceptance，也没有
声称 validator 能判断真实镜头是否“高级”或“好看”。它只阻断已知结构性退化：空 brief 直接进入
Provider prompt、重复同一 coverage category、或用连续扩展冒充普通 Director coverage。

真实生成后的镜头复杂度、构图、动作、camera adherence 与观感仍属于 empirical uncertainty，必须由
现有 per-Shot media Gate 和 human/visual review 判断。

## Repository State

- implementation commits: `a9b0dc0522e995573a2a6f706b637d075c531d2e`、
  `01c9d306526d7fd75d6e244988821734965a98fa`
- publication: local `main` only；本次未 push、未 release
- unrelated `.codex/config.toml`、既有 staged H3 record、untracked artifacts/plans 与 `uv.lock` 均未修改、
  未 stage、未 commit
- Agent Memory retrieval preflight 因当前环境缺少 `langchain_core` 未运行成功；本次判断以 current
  code、contracts、tests、review 和 exact Harness receipt 为准，未刷新 RAG index

## Learning Evaluation

本记录是一个已验证的 deterministic control-plane regression fix，不是两次独立媒体实验、controlled
multi-arm comparison，也没有对既有 Learning Claim 提供 material empirical update。因此 automatic
`distill-ai-video-learning` evaluation 为 `no_candidate`，不创建 placeholder claim。
