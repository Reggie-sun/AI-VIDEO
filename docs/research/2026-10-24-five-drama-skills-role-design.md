# Five Drama Skills Role Design

## Implementation Update — 2026-10-24

用户随后授权执行并补充广告 `ad-creative`，本方案的advisory方法和路由已在
`4118931` / `a168f8d` 实施；已同步删除冲突、过时状态和重复说明。具体实现、验证与未验证
边界见[实施记录](../record_for_agent/2026-10-24-director-skill-integration.md)。下方保留原讨论方案，
其中“尚未安装/实施”属于此前讨论检查点；不表示整套上游安装、Drama Runtime或媒体质量已验证。

## Status And Scope

本轮是用户要求的原生团队讨论和接入设计，不是安装或 Runtime 实现。用户随后明确：五个仓库先用于 **Drama / 剧情与短剧层**，广告层暂不动；可识别共用能力。本文是 advisory proposal，不变更 accepted contract、Skill 路由、Production state 或验收状态。

已核对五库的固定 commit、实际 SKILL 与相关 references；版本和许可见[源码审计](2026-10-24-five-drama-skills-source-audit.md)。检查范围是下载的 Markdown 与许可文本，未执行上游安装器、脚本、Dashboard 或生成工具。

## Decision

五个仓库各取其强项，形成五组专责能力；Native Codex 结合现有 `open-video` 保持唯一导演整合入口。不是每个请求都加载五库，也不让五库分别重写同一份剧本、分镜或时间线。

| Source | Adapted responsibility | Input | Output | Authority boundary |
| --- | --- | --- | --- | --- |
| `zenstory-ai/drama-skills` | 编剧与剧情开发：系列承诺、改编、分集、场景因果、人物动机、对白、信息揭示和伏笔回收 | 用户要求、已有原作/剧本、已接受故事事实 | 单一故事稿与逐场戏剧目标；发展稿审读建议 | 不独立重排最终镜头、不持有第二项目状态；review 不签媒体验收 |
| `eternityspring/shuohao-skills` | 制作设定：角色、场景与叙事道具 bible，空间锚点和按需开场站位提案 | 已接受的角色名单、剧情事实、场景目标、可用视觉参考 | 角色/服装/场景/道具一致性锚点，场景几何与可占位说明 | 不另起 outline→script→storyboard 全流程；开场站位只是 Director 调度方案的输入 |
| `wuwangzhang1216/DirectorSKILL` | 场面调度与摄影剪接：潜台词如何可见、动态 blocking、视线/轴线、覆盖与揭示顺序、剪辑意图 | 剧本、空间设定、人物/道具事实、已接受前镜状态 | 单一完整调度与 coverage；镜头起止状态、切镜理由及接续义务 | 由 `open-video` 消费其方法；不成为第二导演入口或第二实际剪辑时间线 |
| `kangarooking/director-skills` | 表演与动作专项：听说反应、潜台词表现；按需动作接触、受力及后果 | 已接受动机、对白、blocking、目标表演强度 | 可观察的表演过程或动作因果链，含反应与声音意图 | 只选 emotion / action 子技能；不改人物动机、台词、机位或剧情；不接 Miora、文旅、品牌总流程 |
| `liyue-aigc/seedance-2-5-video-director` | Seedance 2.5 专项表达参考：素材职责、模式适配、保护范围、声画与时序表达 | 已批准 Shot、已选 exact 2.5 profile/mode、实际素材 | 对既定意图的 2.5 提示词草案与矛盾诊断 | 由现有 `seedance-authoring` 适配；不能选模型或提交；2.0 不加载 2.5 控制与限制 |

以上是本地接入建议，不是五库作者共同承诺的分工。源仓库中的其他能力不删除，可按本地职责作为参考按需读取；不能因源仓库声称全流程就引入第二控制路径。

## One Story And One Handoff

按现有 accepted [Drama authoring contract](../superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md) 表达 Story / Scene / Character / Shot；不在本轮发明新的平行 schema。

一次正常创作的职责交接是：

1. 编剧明确角色此刻想做什么、知道什么、为什么行动，及本场结尾发生了什么变化。
2. 制作设定补充可以保持一致的身份、服装、物件状态和空间锚点；不能通过美术设定增写剧情事实。
3. Director 形成唯一调度与镜头覆盖，接受或修订开场站位，写清动作/对白/视线的前后承接。已有场景只需要部分处理时，直接路由相应职责。
4. 表演与动作专项细化既定事件怎样可见、可听。发现动机或空间矛盾时退回相应作者，不能靠增加微表情、特效或 Prompt 形容词补洞。
5. 选定模型的 authoring 适配表达和素材映射，不重新创作场景。无法表达的目标返回 Director 比较可行处理，不能静默删掉关键行动。

子模块只提出其职责内的修改，Native Codex 汇总到同一修订。剧情动机由剧情作者处理，动态站位和镜头覆盖由 Director 处理，模型语法由选定 authoring owner 处理；修改影响上游事实时回到上游稿修订并重新核对受影响下游内容。

## Continuity Across Cuts

连续性不等于固定场地，也不等于必须换景。判断依据是观众能否跟随同一个事件与人物变化：

- 人物身份、当前目标、已知信息和关系状态接得上；反应发生在角色能获知触发信息之后。
- 上一镜动作、道具持有/状态、身体位置、视线及音频尾部，对应下一镜开场；省略、跳时、场景重置或主观转换要有明确且可理解的语义。
- 情绪和决定有触发、过程和后果；同一演员或相同画风不能单独证明叙事连续。
- 下一镜续接已接受的实际媒体状态，不从旧 Prompt 猜测前镜已经完成；单镜通过后仍需相邻镜与整场检查。

例如普通剧情《家里的钥匙》：女儿在厨房把家门钥匙放到桌上，说“我明天搬走”；母亲听完，将那把钥匙推回女儿面前，说“家里的钥匙，不用还”。女儿听完，收进右手，起身向门口走。随后切到门外走廊，女儿继续向外走，停下，摊开右手看那把钥匙。

在这个例子中，编剧负责离家决定、母亲挽留的表达及女儿的变化；制作设定负责同一钥匙和厨房通向走廊的空间关系；Director 决定怎样拍清钥匙放下、推回、收进右手以及向外行走的切换；表演专项负责母亲听完才回应、女儿收到回应后的停顿及走廊余韵；模型适配只表达既定事件。跨场景的持物、行走、声音和未结束的心理过程支持切换，不能突然换物、重置动作或让角色回应未听到的对白。该例只是文本分工推演，未生成、未证明成片可读性。

## Retain Useful Methods Without Duplicate Owners

团队对初版进行了交叉质疑，以下为采纳的修正：

| Question | Resolution |
| --- | --- |
| Shuohao 是否独占开场和中途所有站位？ | 不独占。其 `novel-staging` 本身只排开场；开场候选进入 Director 的整场调度同一稿，不保留与 Shot 不一致的第二份 active staging truth。没有明确场景重置时，续拍不能复位到最初开场。 |
| Zenstory 的 storyboard / review / edit 是否全丢？ | 不全丢。保留对白/来源追踪、信息揭示时机、起止状态、可用素材段和原声随 trim 等方法；分别由现有 Director、审读和剪辑 owner 使用。不导入独立项目工具、状态、渲染或验收链。 |
| 五库是否每次都必须参与？ | 不需要。无打戏不加载动作配方；无小说不强行改编；非 2.5 不用 2.5 模式；简单局部任务不走完整开发流程。 |
| 表演默认克制是否覆盖用户要的夸张？ | 不能。以已接受的表演强度为准，既允许静止和克制，也允许有动机的夸张；不把微表情当统一质量标准。 |
| 能否用 cutaway、模糊或转场解决断裂？ | 可以服务已设计的省略或过渡；不能据此掩盖未经解释的身份、动作、物件或因果错误并宣布通过。 |

## Upstream Rules To Adapt

不照搬以下源配方为普遍 Gate：

- Shuohao 的固定镜长/分段、数量限制和英文图片 Prompt；采用当前作品需要与选定模型的真实约束，默认即梦生成 Prompt 使用中文。
- Kangarooking 动作模板中的每段 2–3 秒、每段环境反馈、变化运镜及结尾下一轮。它们只作为相应动作类型的可选建议，安静收束或固定机位均可成立。
- DirectorSKILL 剪辑配方中的固定 ASL、24fps、handle 时长或用插入镜掩盖接续问题。最终节奏由实际观看决定，frame/sample/trim 归 `ResolvedTimeline`。
- Liyue 的 2.5 时长、Long Video、extension、edit、Clay Renderer 和素材语法。上游说明不是当前 Provider/profile 的可用性证据，更不是 2.0 能力。
- 上游自动生图、安装器、Dashboard、项目发布/接受工具、Miora watcher 和独立剪辑执行。不随知识参考接入本地 Runtime。

## Shared And Domain Specific

可跨 Drama 与广告共用的方法：身份/道具/空间连续、动态调度与镜头覆盖、动作受力、台词前中后反应、原声与后期声音规划、选定模型的表达适配。它们不自动改变任何通用 owner。

Drama 专属：故事承诺、角色动机与知识、关系变化、伏笔回收、分集与续看意图。广告的 Product Truth、功效证据、卖点/Hook、demo、CTA、品牌记忆与商业验收保持广告 owner 管辖，本轮不修改。上游品牌/文旅流程暂不接入。

## Minimal Adoption Sequence

1. 当前完成来源审计和职责讨论，保留分歧及选择理由；此步骤不是 Skill 安装完成。
2. 后续实施时，在现有 `open-video` 下接窄触发的 Drama authoring 知识/入口，沿 accepted Drama contract 汇总同一稿。保留来源、固定版本和许可；DirectorSKILL 已有吸收内容先复用，避免再加同义模块。
3. 以普通对话、跨场景因果、动作接触、局部修复四类文本案例核对：是否改动越权、重复写稿、强行加戏、泄漏 2.5 控制或新增状态。文本检查只证明职责表达。
4. 后续在已授权制作中验证 exact 媒体的逐镜、成对及整场连续性与声音；未做的范围保留 `NOT_EVALUATED`。既有媒体 Gate 和 HUMAN evidence 要求不因接入 Skill 而下降。
5. Typed Drama Runtime / Gate 2 若有必要另行界定实现范围；本轮不把 advisory skill 当作已实现的 Runtime seam 或 Production acceptance。

## Verification And Limits

本轮证据为固定源码/许可阅读、本地 owner 核对及四名原生子代理的讨论：来源审计、剧情分工、已有 owner 衔接、交接反例检查。前三者进行交叉质疑；第四者核对跨场景因果、夸张表演局部修复、2.0/2.5 错配和实际前镜状态与新开场提案冲突。检查发现原手机示例存在“扣屏未拒接却给对端忙音”的因果漏洞，已用上方更简单的钥匙场景替换，并限定无场景重置时的续拍承接。

Parent 裁定上述方案；这些角色不是四名审片者或独立工程验收。没有 Provider 调用、媒体生成、上游脚本执行或观众实验，未证明作品质量、留存或商业效果。

本地依据：`AGENTS.md`、[owner matrix](../agent-primary-contract-matrix.md)、[accepted Drama spec](../superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md)、现有 `open-video` / `seedance-authoring`。本地已有的广告文档漂移由审计识别为 deferred，本轮不修复。
