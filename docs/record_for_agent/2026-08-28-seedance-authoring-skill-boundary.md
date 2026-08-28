# Seedance Authoring Skill Boundary Record

Date: 2026-08-28

## Purpose

本文记录 AI-VIDEO 第一版 repo-local `seedance-authoring` Skill 的拆分与 authority boundary。
目标不是建立完整 Seedance Skill OS，而是在最小 context、低 routing ambiguity 与单一 Production
architecture 下，为已批准 Shot 提供 Seedance prompt/reference authoring。

本记录描述 commit `2162d69` 的 developer-control-plane implementation。它不是 Seedance
Provider/runtime capability promotion，不证明 prompt 能提高真实媒体质量，也不授权 Provider、ComfyUI、
paid submit、media generation、P6 或 Final Acceptance。

## Implemented Decomposition

第一版只增加一个 primary Skill：

```text
.agents/skills/seedance-authoring/
├── SKILL.md
└── references/
    ├── authoring-common.md
    ├── seedance-2.0.md
    └── seedance-2.5.md
```

`SKILL.md` 只消费已经确定的：

- approved AI-VIDEO `Shot Contract` / `Generation Requirement`；
- exact selected model/profile identity；
- version family、generation mode 与 runtime surface；
- 每个 reference 的 semantic role、`transfers` 与 `must_not_transfer`。

T2V、I2V、R2V、FLF2V、edit 与 extend 保持为 injected mode profile，不拆成独立 Skill。
Prompt 与 reference planning 保持同一 authoring responsibility；troubleshooting 只处理 prompt ambiguity、
reference-role conflict 与 event-density 等 creative repair，不拥有 runtime diagnosis lifecycle。

Shared reference 保存跨 2.0/2.5 的 role-first authoring、chronology、direct edit/extend wording 与
accepted observed state。Version overlay 采用 exactly-one loading：2.0 family（含 exact Mini/variant
profile）只加载 `seedance-2.0.md`，2.5 只加载 `seedance-2.5.md`。1.5、1.0、future、mixed 或 stale
selection 在第一版 fail closed，不继承 2.0 guidance。

## Routing And Retirement

`AGENTS.md` 只保存 durable summary；`.agent/context/control-plane-playbook.md` 是 detailed routing
owner。当前 Seedance authoring path 为：

```text
approved Shot / Generation Requirement
-> seedance-authoring
-> existing AI-VIDEO Provider Request and runtime owners
```

Concept/ordered coverage 继续进入 `open-video`，semantic continuity 继续进入
`hell-grind-aigc-skill`，Non-Seedance prompting 继续进入 `higgsfield`，deterministic motion/
graphics 继续进入 `video-shotcraft`。

AI-VIDEO 内以下旧 direct dispatch targets 已 retirement：

- `higgsfield-seedance`；
- `higgsfield-seedance-2-5`；
- `higgsfield-seedance-vfx`；
- `higgsfield-troubleshoot` 的 Seedance branch。

它们的 global frontmatter 不覆盖 repo-local routing。只有 `seedance-authoring` 已经 selected 后，
Agent 才可按需把其中一段作为 non-authoritative advisory source；不得迁移 version/runtime/Provider
事实或扩大 Skill authority。

`docs/record_for_agent/2026-08-20-seedance-synthetic-continuity-and-skill-preflight.md`
中列出的 `higgsfield-seedance` 是当时 run 的历史实际调用，不是当前 direct routing 声明，因此本次
没有改写或 supersede 该媒体记录。

## Runtime And Production Boundary

以下 owner 保持不变：

- capability registry / Shot Router：exact model、profile、mode support、limits 与 selection；
- `Shot Contract` / `Generation Requirement`：creative/continuity intent 与 semantic bindings；
- Provider adapter：native expression、payload、parameter/cardinality 与 transport validation；
- `VideoGenerationService` / `ProductionStateCommitter`：submit/poll/fetch、lifecycle、activation、
  recovery 与 unknown-outcome handling；
- continuity engine / P6：exact-media evidence、continuity/quality verdict 与 acceptance；
- Harness：changed-path verification 与 receipt。

Skill 不创建 asset manifest、provider tag compiler、capability registry、sequence state、continuity
ledger、retry workflow 或 validation subsystem。`runtime_skill_calls = 0` 保持为硬边界。

为避免该边界只停留在文档，commit 还增加 `tests/test_runtime_skill_boundary.py`，并通过
`.agent/harness/policy.yaml` 将 `product_runtime_skill_boundary_tests` 设为 always-selected check。
它检查 `src/ai_video/**` 是否引入 Agent Skill path、direct identity、snake_case/CamelCase loader/
registry identifier 或 Skill-like AST import；ordinary prose 中的 `skill` 单词不被 blanket 禁止。

## Verification And Review

Pre-commit focused verification：

```text
python -m pytest -p no:cacheprovider \
  tests/test_runtime_skill_boundary.py \
  tests/test_seedance_authoring_skill.py \
  tests/test_agent_harness.py \
  tests/test_docs_contract_gate.py -q

168 passed
```

另通过：

- `skill-creator/scripts/quick_validate.py`：`Skill is valid!`；
- `python -m scripts.agent_harness policy-audit`：无 unmapped/unverified/missing/unreferenced path；
- `python -m scripts.docs_contract_gate check`；
- `python -m scripts.architecture_gate check`：PASS。Shared dirty tree 中显示的历史/并发 warnings 不属于
  task-owned paths；exact commit-range Gate 为 0 warning。

Independent `reviewer_high` 首轮拒绝 old Seedance dispatch 未退役和 runtime guard 太弱；修复后 scoped
re-review 为 `accept with concerns`。随后两项 concern（CamelCase loader tokenization 与 explicit
`higgsfield-troubleshoot` identity）均已补齐，并由上述 168-test focused run 验证。没有把 reviewer
verdict替代 executable proof。

Implementation commit：

```text
2162d69 feat: add Seedance authoring skill boundary
```

Exact `HEAD^..HEAD` Harness receipt：

```text
.agent/harness/runs/seedance-authoring-skill-boundary-2162d69/receipt.json
```

Harness checks：

- Product Runtime Skill boundary：`2 passed`；
- Harness/docs/policy contracts：`193 passed`；
- Seedance authoring Skill：`7 passed`；
- task Architecture Gate：PASS，`0 error / 0 warning / 0 info`。

`verify-receipt` 确认 `passed=true`、`fresh=true`、`snapshot_matches=true`、
`scope_worktree_clean=true`、`policy_matches=true`、`artifact_integrity=true` 与
`complete_completion_proof=true`。

## Assessment And Remaining Evidence Boundary

第一版有意不支持 Seedance 1.5/1.0 authoring overlay，也没有创建 `seedance-core`、
`seedance-router`、`seedance-sequence`、mode-specific Skills、asset manifest、validator 或 runtime
adapter。新增 Skill 的条件应继续由独立 trigger、独立输入/输出和可验证 authority 证明，而不是为了
结构整齐。

本次没有 Provider/API/ComfyUI call、credential access、媒体生成、媒体分析、paid effect、Manifest/
Registry mutation、activation、P6、push 或 release。Static Skill/tests/Harness 只能证明 routing 与
architecture boundary，不能证明 Seedance prompt quality 或 media continuity quality。

## Agent Guardrails

- 未有 approved Shot、exact selected profile/mode/surface 或 semantic reference roles 时，
  `seedance-authoring` 必须 fail closed，不能自行选择或猜测。
- Version/runtime facts 必须重新从 current AI-VIDEO registry、sealed profile、adapter、tests 与 current
  runtime evidence打开；version overlay 不拥有数字 limits、node/API surface 或 Provider truth。
- Creative repair 只能隔离一个 authoring variable；不得自动 retry、fallback、remint permit 或继续
  multi-Shot batch。
- Skill output 必须回到 existing AI-VIDEO contracts；任何 Product Runtime → Agent Skill dependency
  都应被 always-selected boundary guard 拒绝。
- Unrelated staged/dirty Provider Console、H3 record、artifact 与 empirical-quality docs 在本任务中保持
  untouched；实现与记录均为 local-only，未 push/release。
