# Five Drama Skills Source Audit

## Scope and Evidence

本审计只看五个公开仓库固定 commit 下的 Markdown（包括技能、README、references）及 LICENSE／NOTICE；没有下载或审阅上游 scripts、二进制／图片，也不运行脚本、不安装技能、不生成媒体，因此不构成代码安全审计。GitHub API 返回的默认分支快照及本地 Markdown／许可证下载清单位于 `/tmp/ai-video-five-skills-20261024/snapshot-index.json`；五份许可证文件和 Shuohao 的 NOTICE 均完整落盘且 SHA-256 与下载清单一致，下载错误数为零。下表 commit SHA 是本审计所依据的版本；仓库后续更新不自动纳入结论。

| 仓库与固定版本 | 仓库实际形态 | 许可证 |
|---|---|---|
| [eternityspring/shuohao-skills](https://github.com/eternityspring/shuohao-skills/tree/d28a9c539b40523d081794b25ff9113016bd98e0) · `d28a9c539b40523d081794b25ff9113016bd98e0` | 7 个技能：6 个短剧阶段技能与独立的 `character-refs` | Apache-2.0；仓库含 `NOTICE` |
| [zenstory-ai/drama-skills](https://github.com/zenstory-ai/drama-skills/tree/fdb7b7c58017e3eae64eca382c2a85ede368dab0) · `fdb7b7c58017e3eae64eca382c2a85ede368dab0` | README 称 11 个日常技能；树上另有一个只供维护者使用的 `short-drama-knowhow`，共 12 个 `SKILL.md` | MIT |
| [liyue-aigc/seedance-2-5-video-director](https://github.com/liyue-aigc/seedance-2-5-video-director/tree/ad0e68ba6ce24fb9ae9c67c9276061cef37663f1) · `ad0e68ba6ce24fb9ae9c67c9276061cef37663f1` | 单一 Seedance 2.5 专用导演／提示词技能 | MIT |
| [wuwangzhang1216/DirectorSKILL](https://github.com/wuwangzhang1216/DirectorSKILL/tree/c65ae0d14457053efb1e354c7e7f7e120d97fad1) · `c65ae0d14457053efb1e354c7e7f7e120d97fad1` | 一个覆盖开发、预演、镜头、提示词、剪辑、连续性与诊断的通用导演技能 | MIT |
| [kangarooking/director-skills](https://github.com/kangarooking/director-skills/tree/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5) · `301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5` | 7 个专项技能，含动作、表演、视觉资产、Seedance、Miora 与文旅 | MIT |

## Candidate Roles and Reusable Methods

| 来源 | 剧情／短剧层最适合承担的工作 | 值得吸收的做法 | 保留边界 |
|---|---|---|---|
| **Shuohao** | 最适合只取人物／场景／道具 bible 与按需的每场开场站位。仓库也有大纲、剧本和故事板技能，但这些与 Drama Skills 及本地导演覆盖重叠，首轮不应整条管线并入。 | `novel-characters` 与 `novel-art` 把身份、可见锚点、道具状态、光照状态从戏里提取出来；`novel-staging` 把剧本开场转成站位和空间锚点。开场站位给分镜一个具体空间起点。[novel-characters](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/skills/novel-characters/SKILL.md) · [novel-art](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/skills/novel-art/SKILL.md) · [novel-staging](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/skills/novel-staging/SKILL.md) | 多项硬门、时长估算、场景数量和爽点间距是该套件的项目假设，不能作为普遍戏剧定律；场景、角色、道具提示词强制英文也是其图像资产字段约定，不能推出对白或 Seedance 视频提示词必须英文。`novel-art` 还要求时代未明时推成一个具体朝代，适合来源本就有历史依据的项目，不适合让它替原创、架空或现代故事补造时代。它采用 Node 本地脚本、JSON/HTML 报告和自有目录契约；只借创作方法，不搬入第二套创作真相或目录/schema。H3 提示词约定也不应跨模型照搬。[novel-outline](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/skills/novel-outline/SKILL.md) · [novel-storyboard](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/skills/novel-storyboard/SKILL.md) |
| **Drama Skills** | 故事引擎、系列承诺、分集地图和单集剧本；承担剧情与集间叙事的候选 owner。`short-drama-develop` 定义故事引擎与分集地图；`short-drama-write` 管剧本；`short-drama-assets`、`short-drama-storyboard`、`short-drama-review` 可为下游连续性方法提供参考，但这些阶段不应与 Shuohao 及本地 owner 同时维护平行真相。 | 连续性表达具体到“谁／物处于什么状态、相对什么锚点、变化由哪个动作完成”，明确区分同一连续时空内可续接的相邻生成段与通过剪接／换机位进入的独立镜头；时间或地点跳变可以重新起链。分镜与视频提示词分别负责意图和执行措辞，审查者只提有证据的修订要求。[short-drama-develop](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-develop/SKILL.md) · [short-drama-assets](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-assets/SKILL.md) · [short-drama-storyboard](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-storyboard/SKILL.md) · [short-drama-review](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama-review/SKILL.md) | `short-drama` 中心路由强绑定本仓库的五份 Markdown、Dashboard、项目工具及生产生命周期；不可和 AI-VIDEO 的项目、镜头、生产状态或媒体 Gate 并行成为第二 owner。作者所设的固定文本字段、阈值及“何时可续接”可作为设计参考，仍需由本地导演和已选模型能力裁决。[short-drama 路由](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/skills/short-drama/SKILL.md) |
| **Seedance 2.5 Director** | 当且仅当目标生产档案选定 Seedance 2.5 时，作为镜头计划到该版本提示词语法的末端适配参考。它自身说明不代替题材／类型导演的故事发展，也不提交生成任务。 | 按一个主模式选语法；为参考素材写清绑定职责；把连续性锁与动作、时间、声音一并审计；诊断与改写遵守用户要求的交付范围。[SKILL.md](https://github.com/liyue-aigc/seedance-2-5-video-director/blob/ad0e68ba6ce24fb9ae9c67c9276061cef37663f1/SKILL.md) · [README](https://github.com/liyue-aigc/seedance-2-5-video-director/blob/ad0e68ba6ce24fb9ae9c67c9276061cef37663f1/README.md) | 它明确限定 Seedance 2.5。模式、时长、参考槽位、长视频、续写和术语不能套到 Seedance 2.0。当前使用 2.0 时最多借模型无关的检查思路，提示词仍交本地 `seedance-authoring` 与能力档案。 |
| **DirectorSKILL** | 镜头覆盖、动态调度和剪接设计的导演工艺参考：戏剧目的、动作／站位先于构图、coverage、关键帧、视听连续性，以及失败定位。它覆盖 A–J 多种模式与 13 步总流程，并非单一窄技能。[模式与流程路由](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/SKILL.md) | 用可见的动作和空间说明替换抽象形容词；镜头要改变观众理解；按具体症状定位故障并做最小修复；镜头数量／风格变化需服务叙事。[SKILL.md](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/SKILL.md) | 与本地 `open-video` 的全片导演和镜头覆盖职责高度重叠。不能再完整注册一个会因“任何 AI 视频”触发的第二总导演；如吸收动态调度、coverage、转场／剪接方法，应并入唯一导演 owner。源的 `editing-and-assembly.md` 固定用 24 fps、ASL/镜头数分布与生成 handles 的成本式；这些是该技能的计划模型，不是本地 timeline 或 Seedance 参数。它也提出用 cutaway、blur 或 dissolve 掩饰画面连续性缺口；它们最多能遮住一处视觉接缝，不能修复剧情因果断裂或前后事件不搭，需避免被误作用户所说的“连续性”修复。源中列出的导演风格镜片应作为用户点名时的可选分析方式，避免默认风格化或复刻具体作品。 |
| **Director Skills** | 可按需调用的微表演、动作因果和视觉资产分析方法参考；它不是一个统一的剧情导演。 | `emotion-performance-director` 把潜台词译成少量、按时间排序的眼神／呼吸／脸／身体／声音信号；`action-fight-prompt` 要求动作有前因后果与可见环境反馈；`cinematic-asset-prompts` 先定视觉基调、再从剧本清点角色／场景／道具。[emotion-performance-director](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/emotion-performance-director/SKILL.md) · [action-fight-prompt](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/action-fight-prompt/SKILL.md) · [cinematic-asset-prompts](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/cinematic-asset-prompts/SKILL.md) | `action-fight-prompt` 的≤15秒单次生成假设、每2–3秒一个动作段、每段必须环境反馈、运镜须变化及结尾铺垫下一轮，都是其打戏配方；可取“动作有前因后果”的原则，不把其时长、镜头变化和尘土声响硬套到所有剧情。`seedance-motion-studio` 是品牌、产品、新闻、科普导向的制作工作流，`miora-video-studio` 是特定生成通道的操作／状态处理，`travel-*` 面向文旅；它们不应变成此处短剧剧情 owner，也不应把广告或供应商能力引进剧情规范。[仓库职责表](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/README.md) |

## Team Discussion: Non-Overlapping Responsibilities

五个仓库不是五个同等层级的“导演”。按源文件边界推导，较稳妥的讨论起点是：

1. **故事／分集／剧本**：Drama Skills 作此层候选 owner，吸收故事引擎与集间状态承诺；Shuohao 的小说大纲／剧本阶段只作对照，避免两套分集地图分别改写。
2. **人物／场景／道具资产和开场站位**：优先参考 Shuohao 对资产 bible 和按需场次 staging 的拆分，不采用它的全套独立文件、默认配方和英文提示词硬门。
3. **动态调度／coverage／剪接**：DirectorSKILL 只提供导演工艺参考；本地 `open-video` 继续拥有全片导演、场次意图、镜头职责和最终连续性判断，不另建常驻总导演。
4. **表演／动作专项**：Kangaroo 的微表演和动作因果按需提供微指令；不要把武打模板套到日常戏。
5. **模型提示词**：只由选定版本的 authoring owner 承担。当前 Seedance 2.0 走本地 `seedance-authoring`；Liyue 仓库只作 2.5 版本专用参考，不提前混入 2.0。

分工是从仓库技能边界推导的设计建议，不表示已安装或已通过运行／成片验证。

连续性原则应写成“跨段状态与因果连得上”，而不是固定场地规则：场景可保持也可改变。场景变化需能由剪接、时间跳跃或新动作起因解释；人物身份、衣着／道具状态、动作前后因果、空间关系、情绪意图与声音交接按具体镜头继续、重置或明确变化。此结论是跨仓库内容与创作者反馈的综合建议，不是任一上游仓库的原文定律。

## License and Adaptation Notes

五个仓库都提供了根目录 LICENSE：Shuohao 为 Apache-2.0，并附 `NOTICE`；其余四个为 MIT。[Shuohao LICENSE](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/LICENSE) · [Shuohao NOTICE](https://github.com/eternityspring/shuohao-skills/blob/d28a9c539b40523d081794b25ff9113016bd98e0/NOTICE) · [Drama Skills LICENSE](https://github.com/zenstory-ai/drama-skills/blob/fdb7b7c58017e3eae64eca382c2a85ede368dab0/LICENSE) · [Seedance Director LICENSE](https://github.com/liyue-aigc/seedance-2-5-video-director/blob/ad0e68ba6ce24fb9ae9c67c9276061cef37663f1/LICENSE) · [DirectorSKILL LICENSE](https://github.com/wuwangzhang1216/DirectorSKILL/blob/c65ae0d14457053efb1e354c7e7f7e120d97fad1/LICENSE) · [Director Skills LICENSE](https://github.com/kangarooking/director-skills/blob/301e6e72199f28b8ea82cd48ff06ab9ae49d0ee5/LICENSE)。若后续逐字复制或改编文件，MIT 文件须随附版权和许可声明；Shuohao 的 Apache-2.0 文件须随附许可证、保留适用 NOTICE，并对修改文件附上显著修改说明。本节核对的是上游许可证文本及改编时须保留的声明；一般思想与职责分工的借鉴不等于已复制源文本。

## Unverified Areas

本审计没有运行上游脚本、evals 或媒体流程，没有判断其输出审美、实拍／生成表现或质量门的实际预测力，也没有检查各仓库最新版本是否已变化。Markdown 宣称的确定性检查与作者自报测试，只描述仓库设计或作者主张，不构成本地技能采用或真实成片验收证据。
