# Event-Led Timing

## Scope And Authority

用于尚未确定的对白节奏、动作时间和镜头时长决策。沿 `open-video` 的任务分类与原有
Story/Scene/Shot、coverage、selected authoring 和 QA 交接；不是第二套时间线、schema、
自动定长器或执行入口。既定来源复刻、局部修复和用户硬时间要求保持原范围。

## Direct The Event Before Allocating Seconds

先说明观众何时能读懂变化，再决定需要多少时间。在当前镜头说明里写清必要的内容即可：

- 人物接收什么可见/可听触发，此前知道什么；反应来自接收到的信息，不能来自观众的全知。
- 行动怎样造成下一事件：接近、接触、承重转移、释放有先后条件；不能用“同时”消除这些条件。
- 哪些通道可自然并行：说话时看向对方、倾听时停手、摄影跟随同一动作；同一只手不能执行冲突任务。
- 停顿让谁处理、试探、隐瞒或等待什么；反应可以迟疑、迅速、克制或强烈，取决于角色和作品。
- 镜头何时完成任务：观众读到决定/后果、注意交接、动作仍在继续的接点，或有意保留的不确定。
  由此选择继续停留或切出，不要求每镜都落定、每句说完都切镜，或每镜增加运动。

写“听见警告后收手，确认对方让开才接住”，优于为了填表写固定的几个秒段。
相对顺序不等于拖慢表演；无依据的漫长凝视、全员同步反应和把头身锁死也不能代表自然。
已经有意义的静止和留白应保留，不用增加动作凑满镜长。

## Plan Generation Groups Separately

先按叙事与表演确定摄影镜头，再独立判断哪些连续内容适合放进同一生成片段。一个生成片段可以包含
多个有动机的摄影切镜；剧情节点、coverage unit 和生成任务不默认一一对应。优先保住完整的行动、
倾听、回应与情绪变化，不为逐句、逐动作或逐摄影镜头生成而切碎连续表演。

选择分组与时长时，实际考虑当前模型可用的完整时长范围、参考条件、声画连续性与事件容量；不能把
旧的8–10秒分段、试片长度或API默认值当作常规上限，也不为用满模型上限增加空镜、拖慢表演或填充动作。
短插入镜头与较长的连续戏都可以成立，理由应来自内容及实际能力，不是固定长短偏好。

在原有作者稿说明每个生成片段覆盖的完整戏剧过程、摄影切镜、输入交接与时长选择理由，再沿现有
Shot / authoring 与Provider设置封存，核对实际请求时长确实反映该决定；不能只重写Prompt而保留旧时长。
已批准素材、固定用户时长、现有schema与QA边界仍有效，必要改组走原作者修订，不擅自重生成旧片、
拼接互不兼容的请求或建立第二时间线。

## Choose A Feasible Duration

由 Director 在授权的创作范围内选择时长，不等待用户逐句排秒，也不把时长决策全部交给模型。
按完整原句、表演方式、必要的顺序动作、理解/反应及声音尾部估计容量；可并行部分共享时间，
互为前提的事件仍需依次完成。没有实际测量时明确是文本估计，保留不确定范围；不能声称已经朗读或听验。
有同句、同表演的可靠录音或既有 exact 实片时优先参考实际发声与动作区间。
将估算范围、依据、未确定项与选择该镜长的理由留在既有 authoring notes / 镜头说明，
不为它新增状态字段，不把估算说明粘进 native prompt，也不将它计为数值验收证据。
不要默认每秒固定字数、每镜固定动作数、统一反应延迟、统一镜头长度或统一生成 handles。

再核对当前 selected model/provider/mode/profile 的合法时长、声音和参考能力：

- 未封存前，可在当前授权范围内调整镜长或 coverage，让必要事件自然完成；固定交付时长仍须满足。
- 放不下时先移除无叙事职责的竞争动作，或采用确实可并行的调度；仍不足则延长、按语义拆镜，
  并同步原 owner 的作者稿和设置。不能删改批准台词、用异常语速、冻结尾帧或重复对白解决超载。
- 明确的固定单镜/对白/交付时间若与容量冲突，报告具体冲突；不能悄悄拆镜、拉长或改成软目标。
- `provider_selected` / `duration=-1` 仅在当前 adapter/profile 明确支持且任务选择时使用，
  并保留实际时长证据；它不解除预算、交付约束或导演判断，也不是所有 2.5 surface 的能力。

保留既有 coverage 的具体 `duration_seconds` 和总时长校验；它们是这版方案的镜头预算，
不能直接翻译成每个内部动作的硬 deadline。区分 QA owner 批准的交付约束、导演节奏选择与
`generation_margin`；后者不是验收条件。调整已经批准/封存的输入须经原 authoring revision
和依赖失效路径，不能原地改 receipt、request 或历史时长。

## Handoff To The Selected Model

用现有 `SubjectAction.progression`、`MotionEnvelope.onset/peak/settle`、`Pacing.cadence/tempo_class`
和逐人物表演的 trigger/response/settle 表达相对阶段；没有必要就不添加秒数或新字段。
`shot_duration_seconds` / output 设置承载片段预算，最终帧、sample、trim 仍只归 `ResolvedTimeline`。
把关键动作和说话者绑定到实际人物/参考中的可见身份，再检查 exact native preview；只在
`Shot.intent` 写到、或声明路径覆盖，并不证明模型收到该语义。

| Selected route | Expression and boundary |
| --- | --- |
| Seedance | 读 `seedance-authoring` 及一个 exact version overlay；中文叙述触发、动作和反应，按现有 reference jobs 绑定素材。时间戳只是所选 surface 支持时的表达，不能承诺遵从。 |
| Jimeng / `seedance_2.5` 原生顺序对白 | 若当前 runtime 已明确适配 `DialogueIntent(mode=conversation)`，有序 turns 可封存逐字台词、speaker、画内外、口型与反应义务，不填台词时间。复核 native audio 与人物绑定；本次只在尚未发布的其他任务工作树中检查到此适配，本文不发布该能力或证明质量，不支持时返回缺口。 |
| Local H3 | 读 `h3-video`，按 selected compiler 的三字段、对白标记及真实切镜语法表达。`[Shot N] At ...` 是后续镜头切点，不能拿它给同一镜头的每个手势定时。当前 H3 compiler 拒绝 `conversation`，不能借本方法开放该模式。 |
| Remote H3 / other providers | 核对 exact adapter 的原生语法与 supported contract；不从 Local H3、另一型号或上游示例外推。未适配的无时码对白返回缺口，不静音、不走 neutral fallback、不伪造台词时间来过 schema。 |

当前 `conversation` 表达的是顺序接话；不能声称已经支持任意多人重叠、打断或独立声线控制。
如果批准剧情必须抢话或打断，保留事实并报告当前表达缺口，不能反写成“所有人等对方说完”。
原有 timed `dialogue` 和 preserved-source 输入继续沿其合同，不自动迁移或重写。

## Observe Then Decide The Cut

对 exact MP4 沿既有 Per-Shot Gate 取得正常速度声画证据，分别看触发是否先被接收、动作是否完成、
说话者/原句/口型是否一致、反应是否可读，以及后果与声音尾部是否被剪掉。
文本顺序检查、抽帧或 ASR 不能证明自然度；“未指定秒数”既不是数值时序 PASS，也不是质量豁免。
没有相应观看/聆听证据保留 `NOT_EVALUATED`。

在批准的可变范围内，可依据实际表演向原剪辑 owner 提出入出点与镜长修订，再生成新的
`ResolvedTimeline` / exact 成片证据。不能把真实失败重新命名为“弹性”、改验收标准，或沿用旧
hash 的 PASS。已有素材的变速/裁切只在保留动作自然、对白、接缝与已满足目标时成立；有声片
不能只比较关键帧。失败与 unknown 仍沿原 recovery/预算/验收规则，不授权任何新生成。

## Worked Authoring Choices

以下是独立虚构的作者示例，未生成媒体，不是时长或效果保证：

**生活对白。** 店员说“还烫，等一下。”顾客听到后缩手；店员垫好纸再递近，顾客确认托稳后说
“谢谢。”顾客收手与抬眼可重叠，垫纸与承重转移有先后。镜长先容纳完整原句、服务动作和反应，
再选合法设置；不按两句平均分配秒数。切在交接后或批准的动作接点，取决于下一镜义务。

**固定落点。** 若用户明确要求 3.5 秒前举臂至水平，该 deadline 仍须实际验证；
只写“随后抬臂”或让模型自行定长不能解除它。参考视频只是控制证据，不能保证精确时点；
后期时间映射也必须重新验证完整声画自然度。放不下就报告能力/容量缺口，保留原要求。

## Sources And Adaptation

本方法为本地中文改写，局部参考 Zenstory 的
[performance-action-timing](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-video-prompts/references/performance-action-timing.md)
（[MIT notice](../../drama-authoring/licenses/zenstory-MIT.txt)）及 DirectorSKILL 的
[editing-and-assembly](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/references/editing-and-assembly.md)
（[MIT notice](../licenses/DirectorSKILL-MIT.txt)）。只采用相对节奏、容量判断和按事件选择切点的适用方法，
不采用其固定语速、反应时限、裁头尾配方或并行生产控制面。
完整许可、差异及历史实片反例见[本次研究](../../../../docs/research/2026-10-26-director-skills-and-event-led-timing.md)。
