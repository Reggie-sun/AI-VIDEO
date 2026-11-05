# Shared Seedance Authoring Knowledge

本文件是技术核对清单，不是默认改写模板。它消费 `open-video` 已完成的 awesome-seedance 创作稿，
不定义 runtime capability、provider parameters、asset identity、production validation 或 lifecycle state，
也不自动应用旧创作或修复偏好。

## Evidence Order

facts 冲突时，保留各自的 authority，不得混合：

1. Approved AI-VIDEO Character / Scene / Shot facts 拥有 creative intent。
2. Current AI-VIDEO capability/profile 与 selected adapter 拥有 executable support 和 surface
   semantics。
3. Official model guidance 可以影响 exact selected version 的 authoring language。
4. Community recipes 与 observed heuristics 始终是 advisory，必须明确标注。

不得将一次成功 lint、一个 upstream template 或一个 observed clip 升级为 current runtime 或
Production acceptance truth。

## Generation Input Boundary

来源保留任务消费用户已选定并封存的原 prompt 与参考绑定，Shot Contract 的结构化不自动授权改写实际
生成文本。核对将要提交的 exact native prompt，而不只检查“保存了原文”或“包含了原文”。必要的
Provider grammar / reference-role 技术适配须展示原文与实际输入的差异，不标为原样 baseline；不得借
适配新增故事、机位、对白或验收要求。创作性调整沿当前 task 的授权与 human decision gate。

内部 enums、`unspecified`、验证结果、完整 Shot Contract / coverage 序列化不是给模型的创作指令，
不得机械拼入 prompt。已授权创作时，只表达该 Shot 需要的可观察内容与必要 reference jobs；不以
prompt 更长、lint PASS 或 source quote 仍存在来证明语义保真或模型遵从提高。

## Performance And Whole-Shot Review

核对原创作稿的表演约束是否在技术转换时丢失或反转；发现缺口返回 Director，
不自行增补呼吸、眨眼、手势或头身限制，也不将事实/语义检查升级为观感判定。

author/revise 后逐项核对 canonical directions → selected QA 的人物/beat 表达职责 → exact 最终 native 正文。普通精简 binding 的片段可共同表达多个明确列出的字段；在现有 QA 表达里绑定具体路径及片段，不继承被替换长文的覆盖声明，不凭父路径或泛泛的“自然一些”豁免全员。当前新普通 Seedance binding 使用已封存 compiler/4；preserved-source 原有逐字契约独立，不把整个渲染表演模板强塞进普通正文。程序核验片段、路径和绑定；作者另审片段是否确实表达意图、有无反向语句矛盾，不将字面检查当作 NLP 等义证明。

实际查看每张 exact 参考，分别检查主要人物、背景人物、头身比例、肤质/发丝/衣物材质和环境光照。只报告有局部证据的风格结论及未确定项，不以主角 CG、人数或覆盖完整证明全场统一；合法混合参考须使用既有 scope 声明。换图沿现有 Registry/authoring/review owner，不默认增加白模、参考或模型调用。

实际结果另沿现有 Per-Shot Gate 以 project-local `video-analysis` 观察 exact MP4；表演须正常速度观看，声音语义和反应时机须可靠的同 bytes 声画证据。分别保留基础连续性、表演/观感、完整剧情/声音结论；FAIL/NOT_EVALUATED 停止，缺证先同 bytes 补证。工程接通、参考覆盖或静态表达通过均不能签发自然度、activation 或最终验收。

## Prompt Compatibility

保持原创作稿的语言、叙事顺序、动作与声音。技术适配只处理当前 selected surface 要求的
reference tokens、roles、native grammar 和明确硬限制，并保存差异。不要把旧 subject → action
模板套到已有原文，不为让字段“看起来齐全”重复拼入完整 contract。需要实质改写时回到 Director。

### Prompt Length Guidance

Seedance 2.0、2.0 Fast 和 2.5 的[官方 API 文档](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)
建议中文提示词不超过 500 字、英文提示词不超过 1000 词；文字过长可能使信息分散，模型遗漏细节、仅关注重点，
导致视频缺少部分元素。这是创作建议，不是已核实的 API 硬上限，也不意味着长 Prompt 必然失败。

长度建议只触发可读性提示，不触发自动精简。不能为凑字数截断或删除批准内容；仍按 Generation Input Boundary
保留原文，创作性改写交回默认 Director，需有当前任务授权。实际本地编译边界见[运行说明](../../../../docs/seedance-prompt-length.md)，
不得将中文“字”、英文“词”、字符、UTF-8 字节和 token 当作同一单位。

## Reference Role Map

每个输入 asset 在进入 prompt 前都必须有一个 primary semantic job：

| Role | Authoring meaning | Typical protection |
| --- | --- | --- |
| `first_frame` | I2V/FLF2V 的 exact visual start state。 | 除非 Shot 明确改变，否则保留被锚定的 identity、composition 与 starting state。 |
| `last_frame` | FLF2V 的 exact intended endpoint。 | 保留 endpoint identity/state；不得把它描述为 generic style image。 |
| `reference_image` | 不作为 start frame 的 identity、object、scene 或 style evidence。 | 只 transfer 被点名的 properties。 |
| `motion reference` | Action rhythm、camera path、physical motion 或 timing example。 | 未明确授权时不得 transfer identity、wardrobe、location 或 audio。 |
| `reference_video` | 用于 R2V、edit 或 extend 的 motion/style/source video。 | 明确 operation 与 protected source properties。 |
| `reference_audio` | Voice、dialogue、ambience、music 或 timing evidence。 | 只 transfer 被点名的 audio property；不得推断 visual identity。 |

每个 asset 的 dominant job（只能有一个）是 Director 判断，只写入
`generation_intent.reference_planning` 的 `anchors`／`events`／`selections`，由程序校验数量、
角色、模式与实际绑定；本 Skill 不另维护第二份职责表。本 Skill 只核对已有表达是否包含：

- `transfers`：允许 prompt 继承的 properties；
- `must_not_transfer`：必须排除的 properties；
- `target`：接收 transfer 的 approved subject、object、scene、action、camera 或 audio intent。

Reference 含有显著但不需要的 identity、wardrobe、location、composition、motion、text、branding
或 audio 时，必须提供 `must_not_transfer`。如果一个 asset 被要求承担冲突的 jobs，应拆分 intent
或返回 ambiguity，不得静默合并 roles。

## Mode-Specific Expression

- `T2V`：不得使用 implicit asset binding。
- `I2V`：说明 `first_frame` 锚定什么，并描述从该状态开始允许的变化。
- `FLF2V`：区分起点 `first_frame` 与终点 `last_frame`；不得把两者都称为 generic reference。
- `R2V`：在正文中说明每个 image、video 与 audio reference 的 job。
- `edit`：使用 direct operation wording，例如 replace、remove、preserve、recolor、relight 或
  restage，并给出 exact protected properties。
- `extend`：使用 direct operation wording；从 exact source output 的 accepted observed state
  开始，只描述 continuation beat。此前的 prompt 不是 actual source endpoint 的证据。

## Authoring Consistency Check

handoff 前确认：

- 每个 referenced asset 都存在于 input contract；
- first/last/reference roles 未被混淆；
- 每条 transfer 与 `must_not_transfer` rule 都可追溯到 approved intent；
- prompt chronology 不存在 impossible overlap 或 contradictory state；
- 动作前提、接触、释放、落点等在创作稿中已确定的关系不能在技术转换时丢失或反转；
  有疑义交回默认 Director，不自动载入旧动作方法或追加负面词；
- edit/extend 直接说明 operation；
- 未猜测 runtime limits、file formats、reference counts、mode tokens 或 node/API fields；
- 所有来自 community 的 heuristic 都标注为 advisory。

这只是 authoring check，不是 provider validator、continuity verdict、media lint、Harness receipt
或 Production acceptance gate。
