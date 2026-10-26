---
name: seedance-authoring
description: Use when an approved AI-VIDEO Shot needs authorized Seedance 2.0/2.5 version-selection advice, prompt and reference authoring, or creative repair; compare duration and reference needs, then consume an exact selected version, mode and surface without owning runtime dispatch or production state.
---

# Seedance Authoring

将已经批准的 AI-VIDEO Shot 转换为面向 Seedance 的创作指导。该 Skill 是 Agent-side
prompt/reference 专家，不是 Seedance workflow、router、Provider adapter 或 validator。

## Trigger Boundary

具体 prompt/reference authoring 仅在以下输入全部存在时进行；尚未确定版本时，只提供下节的选择建议，
由 Codex 经现有 capability/profile owner 完成选择，不混用版本语法或猜测运行能力：

- 已批准的 AI-VIDEO `Shot Contract`，或语义完全等价的创作 contract；
- exact selected Seedance model/profile identity，以及对应 version family（`2.0` 或 `2.5`）；
- 已预选的 generation mode 和当前 runtime/provider surface；
- 每个输入 asset 的 semantic reference role 与 transfer intent。

## Authorized Version Selection

用户授权自主选择时，Codex 应根据完整戏剧过程、表演/连续性目标、参考需求、实际质量证据和当前渠道
能力，在允许的Seedance版本中自行择优；不逐镜重复请用户选型号。本Skill提供建议，确定exact
model/profile与mode仍归现有capability/selection owner，进入authoring后只加载一个对应overlay。
用户明确锁定的版本、来源复刻、预算、渠道与审批边界优先；不把自主选择解释为任意换Provider。

当前核实的模型级差异（2026-10-26；实际可执行范围仍须核对selected surface/profile）：

| Capability | Seedance 2.0 | Seedance 2.5 |
| --- | --- | --- |
| 单次生成时长上限 | **15秒** | **30秒** |
| 图片参考上限 | 9张 | 30张 |
| 视频参考上限 | 3段 | 10段 |
| 音频参考上限 | 3段 | 10段 |

- 需要15秒以上连续戏、多轮人物互动、复杂多参考、白模/动作参考、连续叙事或局部编辑时，优先评估2.5，
  让同一片段承载完整行动与回应及有动机的切镜；30秒容量不等于一镜到底，也不是必须凑满。
- 15秒以内的简单、独立内容可评估2.0，但不能只因片段短就自动降级；必须保住已认可的人物造型、
  表演、分辨率、声画和接点。价格或速度优势以当前实际证据为准，不预设2.0一定更便宜或短片一定同质。
- 官方将2.5的长叙事、转场连续性、白模/动作参考及时间戳编辑列为增强方向；这不是精确动作、
  时间点或物理效果必定成功的承诺，也不取消本任务“不逐句分配对白时间戳”的要求。
- 分辨率不按版本一概推断：当前Jimeng注册的2.5为480p/720p/1080p，2.0 VIP有720p/1080p/4k，
  Mini/Fast为720p；不能把渠道输出档位说成全系列原生分辨率，也不只为更大像素牺牲剧情与表演。

版本改变发生在新请求封存前：同步核对模型、mode、时长、分辨率、参考数量/格式/时长、声音与
compiler表达，再沿原authoring revision、preview、预算和permit执行。不原地改已提交请求、不重置
累计消费；UNKNOWN不允许借换模型盲重试。当前渠道不支持目标时，保留原目标，重新选择可行版本或
返回Director调整，不截断到15秒、不隐式换Provider或把原生能力宣传当作渠道已实现。

依据：[2.0官方发布](https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0)、
[2.5官方发布](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)，
以及当前`src/ai_video/production/jimeng_models.py`。没有实际A/B证据时，不将版本宣传差异当作本项目质量结论。

如果缺失事项属于其他 owner，先按以下规则 route：

- concept、coverage 或 ordered multi-Shot design -> `open-video`；
- semantic open/close state 或 cross-Shot continuity -> `hell-grind-aigc-skill`；
- non-Seedance generative target -> `higgsfield`；
- deterministic motion graphics、pacing 或 composition -> `video-shotcraft`；
- capability selection、execution、activation 或 QA -> 当前 AI-VIDEO code 与 contracts。

先按用户目标区分已选来源复刻/原样 baseline、新创作或已授权优化、已知失败 repair；详细边界归
`open-video` 的 Step 1。尚未导入 approved Shot 不等于创作方案尚未确定，也不自动授权改写。
已选画布/原 prompt 的来源保留任务先核对 exact source/reference，并构造语义不变的 approved
Shot Contract，再进入本 Skill；不因缺少项目格式就将其归成任意 draft optimization。
原样生成文本消费封存原文；必要 Provider grammar 技术适配须展示差异，不能冒称原样 baseline。
缺来源证据、实质歧义或 contract 无法无损表达时报告缺口，不新增机位/动作来填满制作字段。
新创作或已授权优化中，尚未形成 approved Shot / ordered coverage 的空白、模糊方向、concept/script、
reference-led brief 或完整 draft prompt，先作为 `DIRECTOR_PREFLIGHT_REQUEST` route 到 `open-video`
做 Director optimization；在该设计范围内 prompt presence 不等于 approval。已知失败 repair 绑定失败项、
完整目标与已满足部分，只做有界对应调整；保留表演不自动锁定机位与剪辑。覆盖、摄影或切点有问题时回到 `open-video`，在已有授权范围内修订 coverage 并走原 authoring revision 与执行准入，不把局部修复的变量限制当成导演要求；用户明确要求先审批或超出授权时仍遵从。
所有分支仍须 approved Shot 与 selected profile，且不能绕过 Provider/paid/egress/permit/media gates。
Director design 分支中，`open-video` 必须保留用户明确的 subject、action、style、product facts、references 与 exclusions，
不得以“优化”为名覆盖 hard constraints；其 validator 只验证 declared constraint inventory 的结构、
verbatim source anchoring 与 coverage binding，不证明 raw input 的约束已提全或语义保真。进入本 Skill
前，该 design 分支必须由 Agent 依次 review `raw evidence -> inventory` 与 `inventory -> coverage`。
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
   先核对动作/身份所需参考是否缺失；需要制作图片时交
   [identity preparation](../scenario-identity-library/SKILL.md) 或
   [action-state/storyboard preparation](../scenario-seedance-storyboard/SKILL.md)，返回实际图片后
   再绑定。不得只给现有单图分配角色就假定参考充分；制图素材不等于实际视频输入，按当前
   首帧/首尾帧/全模态模式核验真正的素材列表与顺序，不以画布摆放或文字提及代替绑定。
3. 来源保留任务输出封存原 prompt，按 `references/authoring-common.md` 的 Generation Input Boundary
   核对实际输入与差异；结构化 Shot 不自动授权扩写。仅已授权创作/优化才从 approved Shot 起草
   subject、visible action、scene、spatial relation、camera、lighting、audio intent、chronology 与
   negative constraints；repair 限于已声明失败项。不得新增 story 或 continuity facts，也不得机械
   拼入内部 enums、`unspecified`、验证结果或完整 contract 序列化。
4. 只应用 selected version overlay。将 authoring advice、current runtime facts 与
   empirical/community observations 分开。
5. 检查 prompt/reference consistency：每个被提及的 reference 都存在；每个 asset 只有一个清晰
   job；edit/extend 使用 direct operation wording；event density 适配 selected duration；任何
   transfer rule 都不与 Shot 冲突。
6. 将 advisory result 返回现有 AI-VIDEO workflow，绝不直接执行。

人物表演或画风 repair 还须按 `references/authoring-common.md` 的 Performance And Whole-Shot Review，核对约束来源、逐人物/beat 的最终文字职责、exact 参考的全场局部证据及正常速度声画审查。静止或细微表演不按关键词判错；完整参数、片段存在、人数及参考 SHA 均不能冒充真实自然度或全场风格通过。

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
