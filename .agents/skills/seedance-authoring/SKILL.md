---
name: seedance-authoring
description: Use when an approved AI-VIDEO Shot needs authorized Seedance 2.0/2.5 version-selection advice, prompt and reference authoring, or creative repair; compare duration and reference needs, then consume an exact selected version, mode and surface without owning runtime dispatch or production state.
---

# Seedance Authoring

将已经批准的 AI-VIDEO Shot 转换为面向 Seedance 的创作指导。该 Skill 是 Agent-side
prompt/reference 专家，不是 Seedance workflow、router、Provider adapter 或 validator。

## Technical Adaptation Only

默认创作已由 `open-video` 中固定的 awesome-seedance `seedance-production-workflow` 完成。
本 Skill 只将该稿适配到当前 exact model/profile 的语法、reference tokens/roles、素材约束与
实际 native preview；不得自动二次创作，不按本地旧模板重排动作、镜头、表演、节奏或语气。
保存上游创作原文、实际 native prompt 与必要技术差异；没有技术差异就保留原文。
可执行性缺口返回原创作 owner，不以“优化”名义删内容。修复方案由 `open-video` 的默认 awesome-seedance 流程提出，
本层只检查其表达能否被当前模式合法消费，不自动应用旧 Repair Bias。

## Trigger Boundary

具体 prompt/reference authoring 仅在以下输入全部存在时进行；尚未确定版本时，只提供下节的选择建议，
由 Codex 经现有 capability/profile owner 完成选择，不混用版本语法或猜测运行能力：

- 已批准的 AI-VIDEO `Shot Contract`，或语义完全等价的创作 contract；
- exact selected Seedance model/profile identity，以及对应 version family（`2.0` 或 `2.5`）；
- 已预选的 generation mode 和当前 runtime/provider surface；
- 每个输入 asset 的 semantic reference role 与 transfer intent。

## Authorized Version Selection

默认按实际单次生成时长选择：**15秒及以内（含15秒）的Shot使用Seedance 2.0，超过15秒使用2.5**；用户明确指定版本时优先。
先按完整戏剧过程确定生成分组与时长，不为套用版本阈值拆短连续戏或删减动作、对白。用户授权自主选择时，
Codex 在所选version family内按分辨率、参考需求和当前渠道能力选择exact variant，不逐镜重复请用户选型号。
本Skill提供建议，确定exact model/profile与mode仍归现有capability/selection owner，进入authoring后只加载一个对应overlay。
用户明确锁定的版本、来源复刻、预算、渠道与审批边界优先；不把自主选择解释为任意换Provider。

当前核实的模型级差异（2026-10-26；实际可执行范围仍须核对selected surface/profile）：

| Capability | Seedance 2.0 | Seedance 2.5 |
| --- | --- | --- |
| 单次生成时长上限 | **15秒** | **30秒** |
| 图片参考上限 | 9张 | 30张 |
| 视频参考上限 | 3段 | 10段 |
| 音频参考上限 | 3段 | 10段 |

- 15秒及以内使用2.0时，仍须保住已认可的人物造型、表演、分辨率、声画和接点；若所选variant不支持
  必要mode或参考条件，报告具体缺口，不静默改用2.5。价格或速度优势以当前实际证据为准，不预设质量同等。
- 超过15秒使用2.5，让同一片段承载完整行动与回应及有动机的切镜；30秒容量不等于一镜到底，也不是必须凑满。
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

## Resolution Defaults And Approval

Seedance 2.0的新生成与修复重生成默认使用1080p；Seedance 2.5保持先480p试片、用户明确认可适用方案并授权后才升1080p。
商品广告例外：生成与交付固定720p，不适用上述1080p默认与升档流程，见[广告制作要求](../ecommerce-ad-workflow/SKILL.md#fixed-720p-output)。
用户当次明确指定的分辨率或审批要求优先；具体规则归[制作规格](../../../docs/canvas-continuous-production.md#formal-narrative-output-defaults)。
所选variant/渠道不支持目标分辨率时报告缺口，不擅自换规格或模型，也不把放大/缩小旧片冒充所选分辨率的原生生成。

如果缺失事项属于其他 owner，先按以下规则 route：

- concept、coverage 或 ordered multi-Shot design -> `open-video`；
- semantic open/close state 或 cross-Shot continuity -> `hell-grind-aigc-skill`；
- non-Seedance generative target -> `higgsfield`；
- deterministic motion graphics、pacing 或 composition -> `video-shotcraft`；
- capability selection、execution、activation 或 QA -> 当前 AI-VIDEO code 与 contracts。

`hell-grind-aigc-skill`、`higgsfield`、`video-shotcraft` 是全局 Codex Skills；当前 runtime 未安装时
报告该 owner 缺失，不由本 Skill 代行其职责。

任务分类（来源复刻 / 新创作或已授权优化 / 已知失败 repair）与 Director 边界唯一归 `open-video`
Step 1，本 Skill 不重述，只保留进入条件：
- 来源保留任务消费封存原文；必要 Provider grammar 适配须展示差异，不冒称原样 baseline。
- 新创作或已授权优化中，尚未形成 approved Shot / ordered coverage 的空白、模糊方向、concept/script、
  reference-led brief 或完整 draft prompt，先作为 `DIRECTOR_PREFLIGHT_REQUEST` route 到 `open-video`；
  prompt presence 不等于 approval。`coverage_strategy=single_take|multi_shot` 在 Director 层决定，
  不得按时长阈值选择；Seedance 2.5 支持 `30s` 只影响 downstream feasibility。
- repair 只做绑定失败项的有界调整；coverage/摄影/切点问题回到 `open-video`。
- 所有分支仍须 approved Shot 与 selected profile，不绕过 Provider/paid/egress/permit/media gates。
- MUST NOT 为填补空 brief 自动起草 `one uninterrupted shot`、重复慢运镜、`no cut` 或
  `VIDEO_EXTEND` prompt；这些 expression 只能来自已批准的 `single_take` coverage 与明确 continuity intent。

不得猜测 version、mode、surface、asset identity 或 reference job。输入为 unknown, future,
mixed, or stale 时必须 fail closed，并报告缺失的 deterministic selection。

## Progressive Loading

1. Load `references/authoring-common.md`，仅作技术一致性与 reference-role 核对，不再次起草创作稿。
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
2. 核对 Director 已写入 `generation_intent.reference_planning` 的参考职责（anchors／events／
   selections）；缺失或与 Shot 冲突时交回 Director，不在本层另建职责表。对每个输入只补充 prompt
   表达所需的 `transfers` 和 `must_not_transfer` constraints，并保留现有 identity 与 state。
   先核对动作/身份所需参考是否缺失；需要制作图片时交
   [identity preparation](../scenario-identity-library/SKILL.md) 或
   [action-state/storyboard preparation](../scenario-seedance-storyboard/SKILL.md)，返回实际图片后
   再绑定。不得只给现有单图分配角色就假定参考充分；制图素材不等于实际视频输入，按当前
   首帧/首尾帧/全模态模式核验真正的素材列表与顺序，不以画布摆放或文字提及代替绑定。
   复核上述参考制作 specialist 返回的连续性与输入适用性检查；将已观察的空间/姿态冲突和
   审看标记污染返回对应 owner。本层不自行改剧情或自动重生成，不重复接管参考图审查。
   “不为填满上限追加图片”不等于尽量少：先按[参考包](../../../docs/shot-reference-planning.md#reference-package-before-preview-2026-10-30)准备每个决定性时刻、可见表演者、证据细节与风格帧，再按模式能力选入；不得为了免做参考而改动 identity_continuity 或删掉人物与动作。
   消费现有 [Shot Reference Plan](../../../docs/shot-reference-planning.md) 的组合风险与 motion 等级，
   不因单个 contact/high-speed/camera 标签追加视频，也不为填满上限追加图片。
   对每份素材明确允许迁移与禁止迁移的属性；矛盾参考先解决用途，不默认叠加。
   准备输入见 `planned_model_inputs`，实际提交依据 exact preview 的 `actual_model_inputs` 与 native list；
   审看宫格、未完成的候选图和已选输入不能混同。2.0/2.5 的官方最大容量不证明当前渠道可用，
   R2V 中间图不等于定时关键帧；必需控制与 selected mode 冲突时交回现有 selection/Director，不能静默丢图或换模式。
3. 保存 `open-video` 交来的创作 prompt 或用户要求保留的 exact source。只转换当前渠道要求的
   reference token、role 或语法，并逐项记录 original → native 的技术差异。场景、动作、表演、
   镜头、台词、节奏与声音保持原意；不机械拼入内部 enums、`unspecified`、验证结果或完整 contract。
   不能合法表达时回到 Director，不在本层补一套新的创作方案。
4. 只核对 selected version overlay 的能力与语法边界。历史表达 advice 不自动执行；将
   current runtime facts 与 empirical/community observations 分开。
5. 检查 prompt/reference consistency：每个被提及的 reference 都存在；每个 asset 只有一个清晰
   job；edit/extend 使用 direct operation wording；event density 适配 selected duration；任何
   transfer rule 都不与 Shot 冲突。
6. 将 advisory result 返回现有 AI-VIDEO workflow，绝不直接执行。

表演、画风修复方案由 Director 返回后，本层仅按 `references/authoring-common.md` 核对约束、字段与 native 正文一致；参数和片段存在不证明真实自然度或全场风格通过。

## Output

返回简洁的 advisory package，不创建新的 durable schema：

```text
selected_profile: <从输入回显的 exact model/profile identity + version family + mode + runtime surface>
prompt_draft: <保持创作原意的 native technical adaptation>
reference_transfers:
  - <reference_planning 中的 asset/need identity>: <transfers; must_not_transfer>
authoring_warnings: <ambiguity、unsupported expression 或 evidence limits>
repair_note: <回传 Director 的具体表达或能力缺口，不自动改写>
runtime_handoff: <现有 capability/provider path 必须验证的 facts>
```

## Troubleshooting Dispatch

该 Skill 可以报告 prompt ambiguity、互相冲突的 reference jobs，或无法合法表达 approved Shot 的
具体位置。创作诊断和定点修复返回默认 Director 流程；本层不能据诊断自行重写或再次生成。

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
