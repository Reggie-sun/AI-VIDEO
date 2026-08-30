---
record_kind: architecture_implementation
topic_id: promptless-long-form-director-preflight
learning_eligibility: ineligible
---

# Promptless Director Strategy Preflight Record

Date: 2026-08-30

## Supersession Notice — 2026-08-30

本记录下方由 commits `a9b0dc0522e995573a2a6f706b637d075c531d2e` 与
`01c9d306526d7fd75d6e244988821734965a98fa` 实现的固定 `>15s` creative threshold，以及
“只有用户明确要求时才允许 single take”的结论，已被
`f83f42ac7981aba0caa634c2a4c38a4362dee117` supersede。旧段落保留为发生过的 regression
chronology，不再代表 current contract。

Current contract 对所有 `PROMPTLESS_REQUEST` 都先 route 到 `open-video`，由 Agent 根据叙事 beat、
动作/空间变化、camera/blocking trajectory、pacing、continuity risk 与用户明确偏好选择
`coverage_strategy=single_take|multi_shot`。时长与 Seedance 2.5 native `30s` capability 只属于 pacing /
downstream feasibility，不能直接选择 creative strategy。

## Purpose

本文记录 `PROMPTLESS_REQUEST` Director preflight 的初始修复及其后续 strategy-owner correction。目标是阻止
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
“Seedance 2.5 + 30s + no creative brief”继续绕过 Director coverage，因此当时将 creative threshold
与 Provider ceiling 分离。用户随后指出固定 creative threshold 本身仍然越权替代 Director 判断：
`30s` 可能适合一个完整 single take，而 `10s` 也可能需要 multi-shot。当前修复因此删除整个
duration-based creative classification，而不是调整 threshold 数值。

## Current Corrected Contract

Implementation commit `f83f42ac7981aba0caa634c2a4c38a4362dee117` 实现以下 current boundary：

- 所有缺少 user creative brief 的 request 都是 `PROMPTLESS_REQUEST`，必须先进入 `open-video`；
- Agent 必须显式选择 `coverage_strategy=single_take|multi_shot`，并以
  `director_decision_rationale` 说明基于内容的判断；没有 duration threshold 或 Provider-capability
  creative branch；
- `strategy_source=agent_directed|user_requested` 区分 Agent 判断与用户偏好；只有
  `user_requested` 可携带 `strategy_request_evidence`，不得伪造 user evidence；
- schema v2 validator 对 `multi_shot` 要求至少两个 ordered units 与 cut-class non-final transition，
  对 `single_take` 要求 continuous non-final transition；`30s` 单 unit single take 与 `10s` multi-shot
  都可在 coverage 自洽时通过；
- multiple units 仍须具有不同 `objective` 与 `visible_change`；只有 `multi_shot` 强制相邻 finite
  beat/scale/camera categories 不同，合法 `single_take` 可保持同一 camera language；
- Seedance 2.5 native `30s` capability 不选择 strategy。若已选 strategy 通过 downstream exact
  capability check 后发现不可执行，必须返回 Director 重新判断，Provider adapter 不得静默改写；
- `runtime_skill_calls = 0`、Product Runtime isolation、Provider authorization、per-Shot media Gate、
  Manifest/Registry/P6/Final Acceptance ownership 均保持不变。

## Current Verification And Review

Focused working-tree verification：

```text
168 passed
Documentation contract gate passed
Harness policy audit: no unmapped, unverified, missing, or unreferenced paths
Architecture Gate: PASS
skill-creator quick_validate: both Skills are valid
git diff --check: passed
```

首次 `reviewer_xhigh` verdict 为 `accept with concerns`，指出 validator 将 multi-shot 的相邻
beat/scale/camera diversity 规则错误套到了 multi-unit `single_take`。修复并新增 regression test 后，
同一 reviewer 的 scoped re-review verdict 为 `accept`，无 blocking 或 non-blocking concern。

Exact commit-range Harness：

- scope: `1cd07984ee1299cdc1479a0e96ec82d526c76aa7..f83f42ac7981aba0caa634c2a4c38a4362dee117`
- receipt: `.agent/harness/runs/promptless-director-strategy-20260830-v1/receipt.json`
- selected checks: `scope_diff_check`、`docs_contract_check`、`policy_audit_check`、
  `product_runtime_skill_boundary_tests`、`task_architecture_gate`、`harness_tests`、
  `seedance_authoring_skill_tests`、`open_video_skill_tests`
- result: all 8 checks passed
- receipt verification: `passed=true`、`fresh=true`、`complete_completion_proof=true`、
  `snapshot_matches=true`、`workspace_cleanup_confirmed=true`

## Historical Fixed-Threshold Contract (Superseded)

Implementation commit `a9b0dc0522e995573a2a6f706b637d075c531d2e` 与 final wording alignment
commit `01c9d306526d7fd75d6e244988821734965a98fa` 曾实现以下边界；这些条目只保留为历史：

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

## Historical Verification And Review

Focused working-tree verification：

```text
193 passed
Documentation contract gate passed
Harness policy audit: no unmapped, unverified, missing, or unreferenced paths
skill-creator quick_validate: Skill is valid!
```

该历史版本最终 `reviewer_xhigh` scoped re-review verdict 为 `accept`，无 blocking 或 non-blocking concern。
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

本次 correction 没有调用 Provider、没有生成媒体、没有修改 Manifest / Registry / P6 / Final
Acceptance，也没有声称 validator 能判断真实镜头是否“高级”或“好看”。schema v2 只验证 Agent 已
显式作出 strategy decision、evidence source 与 transition/coverage 结构内部一致；创意判断本身由
`open-video` routing 下的 Agent 承担，不能由 validator 的时长公式替代。

真实生成后的镜头复杂度、构图、动作、camera adherence 与观感仍属于 empirical uncertainty，必须由
现有 per-Shot media Gate 和 human/visual review 判断。

## Repository State

- current correction commit: `f83f42ac7981aba0caa634c2a4c38a4362dee117`
- superseded implementation commits: `a9b0dc0522e995573a2a6f706b637d075c531d2e`、
  `01c9d306526d7fd75d6e244988821734965a98fa`
- publication: local `main` only；本次未 push、未 release
- unrelated `.codex/config.toml`、既有 staged H3 record、untracked artifacts/plans 与 `uv.lock` 均未修改、
  未 stage、未 commit
- Agent Memory retrieval preflight 因 local index library version mismatch 未运行成功；按 Skill
  fail closed，未 rebuild 或刷新 RAG index。本次判断以 current code、contracts、tests、review 和
  exact Harness receipt 为准

## Learning Evaluation

本记录是一个已验证的 deterministic control-plane regression fix，不是两次独立媒体实验、controlled
multi-arm comparison，也没有对既有 Learning Claim 提供 material empirical update。因此 automatic
`distill-ai-video-learning` evaluation 为 `no_candidate`，不创建 placeholder claim。
