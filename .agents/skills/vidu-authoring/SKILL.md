---
name: vidu-authoring
description: Adapt an approved script or Shot to a selected Vidu model or whole-ad service, preserving speaker dialogue, speech-free action beats and reference roles; diagnose narration drift before another call.
---

# Vidu Authoring

这是本地改写的 Provider 表达指导，不是 Vidu 官方导演 Skill。消费已批准的剧情、声音方案与预选
model/service/profile；返回原有 authoring owners，不生成、提交或改变 Production state。

## Match The Service To The Sound Intent

先核对当前 adapter、sealed profile 与官方文档，区分具体视频模型和 `ad-one-click` 整片服务。
Provider 名称相同不代表说话人、口型、对白时段、剪辑或静默控制能力相同。

- 用户需要角色对话、听者反应、动作留白或同期声时，默认采用经现有 Runtime 核实可表达这些要求的
  视频生成模式；不得仅凭“广告”“长视频”或一次可生成整片，就改走自动解说的整片服务。
- `ad-one-click` 提供自动营销编排及多语言 TTS；当前请求没有独立的逐镜说话人、精确对白时间表或
  禁止其它人声的结构化控制字段。Prompt 的“只说这句”“不要旁白”不是可靠执行保证。
  若这些缺失影响原稿的硬要求，回到现有 capability/production strategy owner 选择合适的同 Provider
  路径，不用整片服务冒充等价替换。未知能力保持 gap，不推测底层模型。
- 用户明确要广告解说/口播，或在知晓限制后要求该整片服务作效果对照时，可保留这条路线；表达
  差异与未验证项。不能把一次整片生成的内部镜头伪装为通过逐 Shot Gate 的序列。
- “稿子不改、只换 Provider”先比对实际传输内容与控制能力；不得默默新增卖点、解说、配音或
  自动创意改写。必要格式适配保留原句、说话人、叙事顺序和无口播段落，并说明技术差异。

## Preserve Speech And Its Absence

声音计划归 [Ecommerce G4](../ecommerce-ad-workflow/references/audio-pacing-and-coverage.md) 和既有
Shot/GenerationIntent；在这些 owner 中明确每个段落的可听内容：

- 对白或旁白：谁说、原句、对应动作与可说的窗口、是否出镜/需要口型同步。
- 无口播段：明确不出现对白、解说或额外人声，但继续保留需要的动作声、环境声、配乐及反应停顿；
  不把“声音覆盖完整”误解成从头到尾都有人说话，也不把无口播误解成整轨静音。
- 旁白是否需要由原稿的信息职责决定，不因生成视频带音轨就省掉必要旁白，也不因广告服务提供
  TTS 就自动增加旁白。说话时长由实际台词、语速和停顿判断，不把台词硬铺满片长。
- 在实际 native preview 中复核逐字台词、speaker/reference 角色和无口播段仍可表达；字段、参考槽
  或控制能力缺失时先解决能力匹配，不把“后期再补”当作提交依据。

不机械规定所有影片相同的人声占比、台词句数或固定秒数。允许原稿需要的连续口播；剧情广告
中保留已批准的安静动作与反应，不把它们补写成营销文案。

## Review The Actual Soundtrack

沿项目既有 exact-MP4 / Per-Shot Gate 检查实际声音，而非只查音轨存在。比对原稿中的对白、
说话人、无口播段和动作反馈；人物不说话却出现持续解说、额外文案或静默段被人声填满，属于
声音意图不符，不能记作全项通过或据此提交下一 Shot。

用户选择亲自听音时遵从，不擅自新增音频理解 Provider。波形/响度只能说明技术声音状态，ASR
只作辅助，不能独立证明说话人、口型、停顿和听感。用户反馈“像解说”“一直说话”须定位到
exact source，保留为声音样式失败，不能把旧片声音确认转移到新生成。

失败后先区分服务自动 TTS、原稿 VO 设计、模型额外人声和后期重复叠声。只保留实际证据支持的
归因，不能假称已听音或肯定服务内部如何实现。继续沿现有有界 repair/授权/成本和未知结果恢复
owner；不盲目重试 Prompt，也不直接删掉全部原声而丢失角色对白、拟音与环境声。

## Authority And Sources

`runtime_skill_calls = 0`。本 Skill 不选择 active Provider、不调用凭据/模型/字幕/音频服务，
不更改预算、Registry、Manifest、timeline、QA 或验收；P4/ResolvedTimeline/HyperFrames 仍为
声音与成片 owners。规则只约束 Agent 作者决策，不能保证模型结果，实际媒体验收继续执行。

- [Vidu 一键广告接口](https://platform.vidu.cn/docs/one-click-ad-film)：请求字段与服务范围。
- [Vidu 模型地图](https://platform.vidu.cn/docs/model-map)：整片广告服务的多语言 TTS 定位。
- [本地接口实现](../../../docs/vidu-ad-provider.md)：当前可执行合同，不从上游营销描述推断能力。

来源与职责为本地原创适配；一次失败只记录该服务/请求的观察，不推广为所有 Vidu 模型结论。
