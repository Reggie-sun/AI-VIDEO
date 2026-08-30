---
record_kind: architecture_implementation
topic_id: promptless-long-form-director-preflight
learning_eligibility: ineligible
---

# Raw Creative Input Director Strategy Preflight Record

Date: 2026-08-30

## Current Supersession Notice — Raw Creative Input Boundary

Implementation commit `107e025bf27216bff90db760620adb540d5caf77` supersedes the
promptless-only routing contract from `f83f42ac7981aba0caa634c2a4c38a4362dee117`.
Prompt presence、detail 或格式不再构成 Director preflight bypass：只要输入尚未形成 approved
AI-VIDEO Shot / ordered coverage，无论是 missing、模糊方向、concept/script、reference-led brief 还是
详细 draft prompt，都必须先进入 `open-video` 优化。只有 already-approved 且本次不改变 creative
intent / coverage 的 Shot 可以跳过。

本文件名与 `topic_id` 保留历史身份；下方 promptless-only 与 fixed-threshold contracts 仅作为
regression chronology，不再代表 current boundary。

## Historical Supersession Notice — Fixed Threshold

本记录下方由 commits `a9b0dc0522e995573a2a6f706b637d075c531d2e` 与
`01c9d306526d7fd75d6e244988821734965a98fa` 实现的固定 `>15s` creative threshold，以及
“只有用户明确要求时才允许 single take”的结论，已被
`f83f42ac7981aba0caa634c2a4c38a4362dee117` supersede。旧段落保留为发生过的 regression
chronology，不再代表 current contract。

该次修复对所有 `PROMPTLESS_REQUEST` 都先 route 到 `open-video`，由 Agent 根据叙事 beat、
动作/空间变化、camera/blocking trajectory、pacing、continuity risk 与用户明确偏好选择
`coverage_strategy=single_take|multi_shot`。时长与 Seedance 2.5 native `30s` capability 只属于 pacing /
downstream feasibility，不能直接选择 creative strategy。

## Purpose

本文记录 Director preflight 从 fixed-duration、promptless-only 规则收敛到 raw creative input boundary
的过程。目标是阻止 Agent 在用户不给 prompt 时自行降级为简单镜头，也阻止 Agent 因用户已经给出一段
prompt 或模糊方向，就绕过 Director optimization 直接交给 Provider-specific authoring。

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

后续检查发现 promptless-only 仍是错误边界：用户给出的 prompt 可能只是一句模糊方向，也可能是需要
保真重构的 draft；它们都不是 approved Shot。若以 prompt presence 作为 bypass，简单镜头问题仍会在
“有 prompt 但没有 Director coverage”时复现。Current implementation 因此改用 approved Shot ownership
作为唯一 routing boundary。

## Current Corrected Contract

Implementation commit `107e025bf27216bff90db760620adb540d5caf77` 实现以下 current boundary：

- 所有尚未形成 approved Shot / ordered coverage 的输入都是 `DIRECTOR_PREFLIGHT_REQUEST`；missing、
  vague direction、concept/script、reference-led brief 与 draft prompt 一律先进入 `open-video`；
- schema v3 将 raw input 分类为 `creative_input_kind=missing|direction|draft_prompt`。Supplied input 必须
  绑定 exact `creative_input_evidence`；missing 必须使用 `null`，不得伪造 user prompt；
- supplied input 必须声明 structured `creative_constraints`。每个 `source_text` 必须是 input evidence
  的 verbatim substring；global constraint 必须绑定所有 coverage units，beat-specific constraint 至少
  绑定一个 unit，unknown 或 duplicate ID fail closed；
- validator 只证明 declared inventory 的结构、verbatim source anchoring 与 binding，不证明 raw input
  的约束已经提全，也不理解语义。Agent 必须依次 review `raw evidence -> inventory` 是否漏提 explicit
  constraints，以及 `inventory -> coverage` 是否遗漏、反转或擅自改写；
- Agent 必须显式选择 `coverage_strategy=single_take|multi_shot`，并以
  `director_decision_rationale` 说明基于内容的判断；没有 prompt-presence、duration threshold 或
  Provider-capability creative branch；
- `strategy_source=agent_directed|user_requested` 区分 Agent 判断与用户偏好；只有
  `user_requested` 可携带 `strategy_request_evidence`，不得伪造 user evidence；
- schema v3 validator 对 `multi_shot` 要求至少两个 ordered units 与 cut-class non-final transition，
  对 `single_take` 要求 continuous non-final transition；`30s` 单 unit single take 与 `10s` multi-shot
  都可在 coverage 自洽时通过；
- multiple units 仍须具有不同 `objective` 与 `visible_change`；只有 `multi_shot` 强制相邻 finite
  beat/scale/camera categories 不同，合法 `single_take` 可保持同一 camera language；
- 只有 already-approved 且本次不修改 creative intent / coverage 的 Shot 才能直接进入
  `seedance-authoring`；任意 raw prompt 都不能冒充 approval；
- Seedance 2.5 native `30s` capability 不选择 strategy。若已选 strategy 通过 downstream exact
  capability check 后发现不可执行，必须返回 Director 重新判断，Provider adapter 不得静默改写；
- `runtime_skill_calls = 0`、Product Runtime isolation、Provider authorization、per-Shot media Gate、
  Manifest/Registry/P6/Final Acceptance ownership 均保持不变。

## Current Verification And Review

Focused working-tree verification：

```text
183 passed
Documentation contract gate passed
Harness policy audit: no unmapped, unverified, missing, or unreferenced paths
Architecture Gate: PASS
skill-creator quick_validate: both Skills are valid
git diff --check: passed
```

本轮 `reviewer_xhigh` 首次 re-review verdict 为 `reject`：正向 fixture 没有保留 raw input 的
`red product` / `dark table` / `no people`，且旧措辞把 declared inventory completeness 冒充 raw input
constraint extraction completeness。修复 coherent fixture、verbatim substring gate 与两阶段 Agent review
后，同一 reviewer 的 scoped re-review verdict 为 `accept`，无 blocking 或 non-blocking concern。

Exact commit-range Harness：

- scope: `a45e00c8677db9c4b25e83037326e55662465412..107e025bf27216bff90db760620adb540d5caf77`
- receipt: `.agent/harness/runs/raw-creative-input-director-20260830-v1/receipt.json`
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
Acceptance，也没有声称 validator 能判断真实镜头是否“高级”或“好看”。schema v3 只验证 Agent 已
显式作出 strategy decision、declared constraints 的 source anchoring / binding 与 transition/coverage
结构内部一致；创意判断和 constraint extraction / semantic preservation 仍由 `open-video` routing 下的
Agent 承担，不能由 prompt presence、validator 或时长公式替代。

真实生成后的镜头复杂度、构图、动作、camera adherence 与观感仍属于 empirical uncertainty，必须由
现有 per-Shot media Gate 和 human/visual review 判断。

## Repository State

- current correction commit: `107e025bf27216bff90db760620adb540d5caf77`
- superseded implementation commits: `f83f42ac7981aba0caa634c2a4c38a4362dee117`、
  `a9b0dc0522e995573a2a6f706b637d075c531d2e`、`01c9d306526d7fd75d6e244988821734965a98fa`
- publication: local `main` only；本次未 push、未 release
- unrelated `.codex/config.toml`、既有 staged H3 record、untracked artifacts/plans 与 `uv.lock` 均未修改、
  未 stage、未 commit
- Agent Memory retrieval preflight 返回 stale last-good advisory fragments，并排队 background refresh；
  未把 stale RAG 作为 current truth。本次判断以 current code、contracts、tests、review 和 exact Harness
  receipt 为准，record 阶段未另行刷新 index

## Learning Evaluation

本记录是一个已验证的 deterministic control-plane regression fix，不是两次独立媒体实验、controlled
multi-arm comparison，也没有对既有 Learning Claim 提供 material empirical update。因此 automatic
`distill-ai-video-learning` evaluation 为 `no_candidate`，不创建 placeholder claim。
