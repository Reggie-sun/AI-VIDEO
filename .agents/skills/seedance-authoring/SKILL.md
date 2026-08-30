---
name: seedance-authoring
description: Use when an approved AI-VIDEO Shot and preselected Seedance target need prompt and reference authoring or creative repair; consumes exact version, mode, runtime surface, and semantic reference roles without owning runtime dispatch or production state.
---

# Seedance Authoring

将已经批准的 AI-VIDEO Shot 转换为面向 Seedance 的创作指导。该 Skill 是 Agent-side
prompt/reference 专家，不是 Seedance workflow、router、Provider adapter 或 validator。

## Trigger Boundary

仅当以下输入全部存在时使用该 Skill：

- 已批准的 AI-VIDEO `Shot Contract`，或语义完全等价的创作 contract；
- exact selected Seedance model/profile identity，以及对应 version family（`2.0` 或 `2.5`）；
- 已预选的 generation mode 和当前 runtime/provider surface；
- 每个输入 asset 的 semantic reference role 与 transfer intent。

如果缺失事项属于其他 owner，先按以下规则 route：

- concept、coverage 或 ordered multi-Shot design -> `open-video`；
- semantic open/close state 或 cross-Shot continuity -> `hell-grind-aigc-skill`；
- non-Seedance generative target -> `higgsfield`；
- deterministic motion graphics、pacing 或 composition -> `video-shotcraft`；
- capability selection、execution、activation 或 QA -> 当前 AI-VIDEO code 与 contracts。

任何尚未形成 approved Shot / ordered coverage 的请求都不是该 Skill 可消费的 Shot。无论用户给出
空白、模糊方向、concept/script、reference-led brief 或完整 draft prompt，都必须先作为
`DIRECTOR_PREFLIGHT_REQUEST` route 到 `open-video` 做 Director optimization；prompt presence 不等于
approval。只有已经批准且本次不修改 creative intent/coverage 的 Shot 才可直接进入本 Skill。
`open-video` 必须保留用户明确的 subject、action、style、product facts、references 与 exclusions，
不得以“优化”为名覆盖 hard constraints；其 validator 只验证 declared constraint inventory 的结构、
verbatim source anchoring 与 coverage binding，不证明 raw input 的约束已提全或语义保真。进入本 Skill
前必须由 Agent 依次 review `raw evidence -> inventory` 与 `inventory -> coverage`。
Agent 必须在 Director 层根据 narrative beats、action/space progression、camera/blocking trajectory、
pacing 与 continuity 风险选择 `coverage_strategy=single_take|multi_shot`，不得按时长阈值选择。
Seedance 2.5 技术性支持单次 `30s` 既不自动证明应当 single-take，也不强制 multi-shot；它只影响
downstream feasibility。Director validator 不证明 Provider duration/mode capability；这些 exact facts
仍由 current selected profile owner 校验，若 selected strategy 不可执行则返回 Director 重新判断。
MUST NOT 为填补空 brief 自动起草 `one uninterrupted shot`、重复慢运镜、`no cut` 或
`VIDEO_EXTEND` prompt；这些 expression 只能来自已经批准的 `single_take` coverage 与明确 continuity intent。

不得猜测 version、mode、surface、asset identity 或 reference job。输入为 unknown, future,
mixed, or stale 时必须 fail closed，并报告缺失的 deterministic selection。

## Progressive Loading

1. Load `references/authoring-common.md`，获取共享 prompt 与 reference-role knowledge。
2. 只加载 exactly one version overlay：
   - 已选择 Seedance 2.0 family（包括 exact Mini/variant profile）->
     `references/seedance-2.0.md`;
   - 已选择 Seedance 2.5 -> `references/seedance-2.5.md`。
3. 禁止合并两个 overlay。第一版 authoring package 有意不支持 Seedance 1.5/1.0，且 MUST NOT
   继承 2.0 guidance。遇到其他或 ambiguous version 时停止，
   请求当前 AI-VIDEO capability/profile decision。

当前 AI-VIDEO capability registry 与 selected profile 中的 runtime/surface facts 优先于这些
authoring references。Community observations 只能作为提示。

## Mode Profile

消费但不得自行选择一个 mode profile：

| Profile | Authoring concern |
| --- | --- |
| `T2V` | 表达 approved Shot，不虚构 asset binding。 |
| `I2V` | 说明 first-frame image 锚定什么，以及允许改变什么。 |
| `R2V` | 为每个 image/video/audio reference 指定一个明确的 semantic job。 |
| `FLF2V` | 将 first/last frame 视为起点/终点约束，而不是两个 generic reference。 |
| `edit` | 明确 exact operation 与受保护的 source properties。 |
| `extend` | 从 accepted observed state 延续，并说明新增的 beat。 |

这些是 mode profile，不是独立 Skill。不得 dispatch mode-specific Skill
（MUST NOT dispatch a mode-specific Skill），也不得发明新的 provider mode token。Exact mode
support、role cardinality 与 transport mapping 仍是 deterministic runtime facts。

## Authoring Procedure

1. 回显 exact selected model/profile identity、version family、mode、surface、Shot identity 和
   输入的 semantic roles。缺少字段时显式标记，不得用 heuristic 补全。
2. 建立 reference-role map。对每个输入保留现有 identity 与 state：`primary_role`、允许的
   `transfers` 和 `must_not_transfer` constraints。
3. 从 approved Shot 起草 prompt：subject、visible action、scene、spatial relation、camera、
   lighting、audio intent、chronology 与 negative constraints。不得新增 story 或 continuity facts。
4. 只应用 selected version overlay。将 authoring advice、current runtime facts 与
   empirical/community observations 分开。
5. 检查 prompt/reference consistency：每个被提及的 reference 都存在；每个 asset 只有一个清晰
   job；edit/extend 使用 direct operation wording；event density 适配 selected duration；任何
   transfer rule 都不与 Shot 冲突。
6. 将 advisory result 返回现有 AI-VIDEO workflow，绝不直接执行。

## Output

返回简洁的 advisory package，不创建新的 durable schema：

```text
selected_profile: <从输入回显的 exact model/profile identity + version family + mode + runtime surface>
prompt_draft: <面向 Seedance 的 authoring draft>
reference_roles:
  - <现有 asset identity>: <primary role; transfers; must_not_transfer>
authoring_warnings: <ambiguity、unsupported expression 或 evidence limits>
repair_note: <诊断失败结果时仅隔离一个 authoring change>
runtime_handoff: <现有 capability/provider path 必须验证的 facts>
```

## Troubleshooting Dispatch

该 Skill 可以诊断 prompt ambiguity、互相冲突的 reference jobs、过高的 event density，或无法表达
approved Shot 的 wording。每次只修复一个 authoring variable，并与 accepted observed result 比较。

Runtime/API/ComfyUI/node/credential/budget/egress/task/container errors 属于 selected AI-VIDEO
Provider adapter 与 typed failure path。Cross-Shot identity/state/axis 问题属于 continuity engine
与 review gates。不得把这些失败重新标记为 prompt failure。

## Authority Boundary

- `runtime_skill_calls = 0`；`src/ai_video/**` MUST NOT import or invoke this Skill。
- AI-VIDEO capability registry 拥有 exact model/version/mode support 与 parameter limits。
- AI-VIDEO `Shot Contract` 拥有 creative 与 continuity intent。
- Selected `Provider adapter` 拥有 native request expression 与 transport validation。
- `ProductionStateCommitter` 拥有 lifecycle mutation、activation 与 recovery。
- Continuity engine 与 P6 review owners 决定 evidence-backed continuity/quality outcomes。
- Harness 拥有 changed-path verification 与 receipts。
- MUST NOT select a Provider，也不得创建第二个 router/capability registry。
- MUST NOT submit, poll, fetch, retry, or recover generation task。
- MUST NOT create an asset manifest、复制 Registry identity，或把 provider transport tags 编译为
  durable truth。
- MUST NOT activate or accept media、写入 Manifest state、签发 P6 / Final Acceptance，或从 static
  authoring check 声称 empirical quality。
