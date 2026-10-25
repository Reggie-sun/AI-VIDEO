# Shared Seedance Authoring Knowledge

本文件保存可跨 version 使用的 authoring guidance，不定义 runtime capability、provider parameters、
asset identity、production validation 或 lifecycle state。

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

表演修订先辨明用户明确约束、已批准叙事事实、导演选择和旧 repair margin；保留构图/坐姿不能自行扩张为头身全锁。让可读的动机连接脸部、目光、呼吸、平衡与主动作，按景别说明可见范围；不强制每镜增加动作，不用全员同步眨眼或摆动代替背景生活状态。有来源的静止、`subtle`、`none`、`throughout` 均可保留，遮挡及微表演不可辨认时明确缺证。

author/revise 后逐项核对 canonical directions → selected QA 的人物/beat 表达职责 → exact 最终 native 正文。普通精简 binding 的片段可共同表达多个明确列出的字段；在现有 QA 表达里绑定具体路径及片段，不继承被替换长文的覆盖声明，不凭父路径或泛泛的“自然一些”豁免全员。当前新普通 Seedance binding 使用已封存 compiler/4；preserved-source 原有逐字契约独立，不把整个渲染表演模板强塞进普通正文。程序核验片段、路径和绑定；作者另审片段是否确实表达意图、有无反向语句矛盾，不将字面检查当作 NLP 等义证明。

实际查看每张 exact 参考，分别检查主要人物、背景人物、头身比例、肤质/发丝/衣物材质和环境光照。只报告有局部证据的风格结论及未确定项，不以主角 CG、人数或覆盖完整证明全场统一；合法混合参考须使用既有 scope 声明。换图沿现有 Registry/authoring/review owner，不默认增加白模、参考或模型调用。

实际结果另沿现有 Per-Shot Gate 以 project-local `video-analysis` 观察 exact MP4；表演须正常速度观看，声音语义和反应时机须可靠的同 bytes 声画证据。分别保留基础连续性、表演/观感、完整剧情/声音结论；FAIL/NOT_EVALUATED 停止，缺证先同 bytes 补证。工程接通、参考覆盖或静态表达通过均不能签发自然度、activation 或最终验收。

## Prompt Grammar

以下起草 guidance 适用于已授权创作/优化或对应 repair；来源保留沿 Generation Input Boundary，
发现 event density 或 grammar 不适配时报告缺口，不静默缩减原动作或重写原文。起草使用可观察的表达，
并保持 chronology 清晰：

```text
subject 与 stable identity
-> visible action 与 state change
-> scene 与 spatial relations
-> 一个 primary camera treatment
-> lighting 与 visual treatment
-> 必要时加入 audible action / dialogue / ambience
-> constraints 与 protected properties
```

- 描述可见或可听的内容，不要用 mood label 取代 action。
- 每个摄影镜头保留清楚的 primary camera intent；一段戏的镜头数与切点先由 Director 按关注点和反应决定，再组织有序 coverage 与生成片段。本条不把一段戏或一次生成限制为单镜，完整表演也不等于不切镜；明确包含 cut 的 approved coverage 保留其切镜意图。
- 按 start state -> action -> resulting state 排列事件。Selected duration 无法清晰表达所有 beat
  时，降低 event density。
- 保留 approved names、appearance、wardrobe、objects、screen axis、direction 与 causal anchors，
  不得虚构缺失的 story facts。
- Audio 仅作为 authoring intent。Exact native-audio support 与 final mix ownership 仍属于 current
  AI-VIDEO runtime facts。

### Prompt Length Guidance

Seedance 2.0、2.0 Fast 和 2.5 的[官方 API 文档](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)
建议中文提示词不超过 500 字、英文提示词不超过 1000 词；文字过长可能使信息分散，模型遗漏细节、仅关注重点，
导致视频缺少部分元素。这是创作建议，不是已核实的 API 硬上限，也不意味着长 Prompt 必然失败。

优先精简重复场景描述、泛化形容词和互相竞争的指令，保留决定含义的动机、动作因果、人物反应、表情变化、
关键声音及参考职责。不能为凑字数自动截断或删除批准内容；来源保留任务仍按 Generation Input Boundary
保留原文，创作性改写需有当前任务授权。实际本地编译边界见[运行说明](../../../../docs/seedance-prompt-length.md)，
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

对每个 asset 记录：

- `primary_role`：只能有一个 dominant job；
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
- edit/extend 直接说明 operation；
- 未猜测 runtime limits、file formats、reference counts、mode tokens 或 node/API fields；
- 所有来自 community 的 heuristic 都标注为 advisory。

这只是 authoring check，不是 provider validator、continuity verdict、media lint、Harness receipt
或 Production acceptance gate。
