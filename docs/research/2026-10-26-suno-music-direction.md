# Suno Music Direction Assessment

## Scope And Evidence

2026-10-26 核对当前源码、测试、Music Director/声音方案、Provider、P4 mixer、音频理解及历史记录，
研究两个指定项目的实际文件。本次不生成/上传音乐、不登录/刷新凭据、不查账号余额、不调用付费识音。
没有安装新 Skill、依赖或 Suno Prompt Craft。代码/提示词验证不证明专业听感。

项目历史通过 `retrieve-ai-video-memory --scope all` 检索；current_docs/superpowers 部分结果为
stale advisory，已直接重开相关源码与当前文档。CodeGraph 查询因并发源码变化返回
`Source changed during indexing`，未将索引结果当事实，改以当前 imports/call sites/tests 判断。

## Upstream Findings

### Suno CLI

检查 [paperfoot/suno-cli](https://github.com/paperfoot/suno-cli/tree/6d28c67a733b32183a80d81306bf0013f46b00b7)，
本机二进制 `0.10.1`；读取 README、`src/commands/prompt.rs`、`src/commands/generation.rs`、
`LICENSE`，本地运行 `agent-info --command prompt` 与 `guide prompting`。

它已有相当完整的操作能力：文本生成、模型/账户查询、状态恢复、签名下载、extend/cover/remaster/
stems、声线 persona 和歌曲管理。`prompt` 是本地参数拼接/校验器：合并 JSON presets 与显式
输入，按维度形成 tags/exclude，报告 missing directions，返回 argv；不是理解剧本或听音乐的模型。
`write` 提供歌词结构脚手架；prompting guide 已讲配器分工、节拍单位、表演、排除项、sliders 和
逐次审听，不能把这些算作新 Songwriter 独有能力。`generation.rs` 负责等待/下载与携带 IDs 的
恢复输出，不会判断音乐是否服务镜头。

[MIT LICENSE](https://github.com/paperfoot/suno-cli/blob/6d28c67a733b32183a80d81306bf0013f46b00b7/LICENSE)
允许复用，保留版权与许可声明；本次继续调用独立二进制，没有复制其 Rust 或 composer。
上游默认验证码自动化策略不导入本项目，继续使用已有 no-browser/no-captcha 边界。

### Suno v6 Songwriter

检查 [MJorgin/suno-v6-cookbook](https://github.com/MJorgin/suno-v6-cookbook/tree/c8e40ff0b10636a7719cbc88bc5f58443ad19907/agents/skills/suno-v6-songwriter)
的 `SKILL.md` 和全部五个 references：model-router、prompt-patterns、edit-and-mashup、
chinese-lyrics、quality-checklist。它是 Markdown-only advisory，没有代码、音频模型、CLI transport、
实际评分或自动修复执行。产物是供用户粘贴的风格、排除项、唱词/编辑指令和迭代建议。

价值集中在分开创作意图/音乐/演唱/唱词、具体音色与能量发展、中文可唱性、局部替换时保留周围
已成立部分、区分官方事实和假设。所谓图/视频到音乐、局部改词、mashup 是对 Suno 产品的操作
建议，不是这个 Skill 自己实现了接口。默认七段输出、三个实验、小乐器组、主副歌倾向属于
写歌工作法，不能直接成为影视配乐契约。

其 [LICENSE](https://github.com/MJorgin/suno-v6-cookbook/blob/c8e40ff0b10636a7719cbc88bc5f58443ad19907/LICENSE)
为 CC BY 4.0，作者 MJorgin 与 contributors；允许适配，需署名、许可链接与修改说明。
本地 Music Direction 参考已提供归因与差异，没有整包安装或复制为第二 Skill。
这两种代码/文档许可证均不能证明生成音乐的商用权利。

### Official Cross-check

[v6 FAQ](https://help.suno.com/en/articles/13924481) 确认 v6 的精确/成品导向、wild 的探索导向、
mini 的快速路线，并列出网页 Simple Mode 多模态、多源、局部编辑等能力；不是逐帧同步或
保留旋律的保证。Songwriter 的“视觉默认 wild”是社区推荐，不能压过本项目已确定的叙事需求。
[Sliders](https://help.suno.com/en/articles/6141377) 与 [Exclude](https://help.suno.com/en/articles/3161921)
支持参数的基本语义，但不支持固定最佳 slider 数值，也不证明本项目某一 prompt 听感更好。

## Existing Coverage And Gaps

| Concern | Before | Enhancement / remaining boundary |
| --- | --- | --- |
| 剧情、人物、情绪、画面 | brief 有剧本/场景/情绪，函数主要看关键词；没有实际推理剧本 | Codex 先作音乐叙事选择，显式 design 优先于关键词；不是自动作曲推理模型 |
| 风格、乐器、节奏、结构 | 常见用途硬编码通用 tags | 以自由文字表达配器职责、脉冲、发展、混音，不按题材固定模板 |
| v6 prompt | 已有 tags/exclude/lyrics、UTF-16 上限和离线 argv | 复用原编译/identity，把导演具体设计送入同一生成入口 |
| 音画匹配 | qa_findings 与未评估 QA；音频 MCP 返回观察 | 加入 cue 的叙事/发展/延续问题与 exact 成片审听方法；没有自动审美评分 |
| 定向调整 | 保护 unknown/replay，但缺音乐诊断工作法 | 区分混音问题、时点问题、作曲问题；保留已满足项后单一变量修订 |
| 主题、过渡、延续、静默 | 主题/转场/留白有简单 role；P4 有 trim/fade/ducking | 增加跨镜 spotting 和主题变奏方法；真正 source-conditioned 延续尚未接通 |
| 不同作品类型 | 通用底乐/悬疑/片内歌为主 | 以题材提问启发导演，最终按具体剧情与表演选择 |
| 执行 | 独立 Suno CLI + opt-in service、本地恢复 receipt、WAV 候选/绑定 | 保持原路径，无新 submit 操作；不是已打通完整 Production 自动配乐 |

现有 `AudioTrackSpec`、`ResolvedTimeline`、`_hyperframes_audio.py` 已拥有 sample placement、trim、
gain、fade、ducking 和同一混音链。原声 KEEP/MUTE/REPLACE 与后期轨可并存。历史
[native audio/P4](../record_for_agent/2026-08-19-seedance-native-audio-and-p4-mixing.md) 和
[Canvas 原声/后期](../record_for_agent/2026-10-23-canvas-native-post-audio-composition.md) 的关键经验是：
有音轨/有后期 BGM 不证明原声实际进入成片；音乐增强不得丢掉已有对白、动作声或环境声。
本次不重建混音器、时间线、音频识别服务、素材 lifecycle 或新音乐导演。

## Implementation Decision

原音乐类型与 `direct_music` 移到 `music_direction.py`，Suno model 留在 adapter；旧 import/
输出 schema、fallback tags、generation hash、request ID 与调用保护保留兼容。
`SceneMusicBrief.musical_design` 可选，承载 Codex 自主创作结果；显式 role 不会再被情绪关键词劫持。
沉默不接受发声设计，唱词用途不能偷换，角色主题需要明确角色，器乐不能声明歌手方向。
不为工程一致性规定固定结构、节拍或每镜一曲；不把音乐风格名单当自动创作。

未引入：独立 Songwriter Skill、Prompt Craft、歌曲总流程、固定三次 A/B、模型自动轮换、
新依赖、自动上传/编辑 API、生成即激活、听感分数。当前适配器只封装文本 generate；CLI 的
其他命令仍是独立工具，不冒称已通过项目 Budget Guard/permit/ProductionStateCommitter 编排。

## Acceptance Boundary

现在 Codex 可以在现有 Music Director 中自主设计影视音乐，并用明确设计经 Suno adapter 做
离线准备；真实文本生成仍须当前任务授权、账户/模型/预算/permit 等原约束。
“独立完成专业影视配乐并实际验收”尚无音乐实测证据：本次没有新 paid submit，没有验证
下载、主题旋律保持、实际音画审听或 Production activation。质量项保持 `NOT_EVALUATED`。
下一有意义的验证是在单独授权后，用一段有对白、情绪变化和静默的 actual 场景验证候选与
exact 混音成片；不需要先建更多模块。本次实际成本/积分为零。
