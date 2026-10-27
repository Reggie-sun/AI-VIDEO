# Shot-to-Shot Editing Decision Research

本研究检查了两个指定 GitHub 仓库在 2026-10-27 可见的 `main` 快照，并把可复用部分限定为指导方法和验证思路。`narrative-film-direction` 快照为 `4ee8b42484cb57407f4a7772216aa79e20b0971f`；`agent-video-editor` 快照为 `8e32c0aff64c445ef1e2b87bc04408a34d68c973`。外部 Skill 属于参考资料，不构成本项目运行时、媒体质量或验收证据。

## Findings

优先复用“每个 cut 必须有叙事理由”以及以事件、动作阶段和观众信息为依据选切点的方法；用清晰的镜头状态记录动作、空间、景别、视线、声音和情绪变化；把镜头切点落实到唯一的 `ResolvedTimeline`，再对 exact 导出成片的接点做声画审查。两份资料都提供了可参考的剪辑语法，但没有可直接接入 AI-VIDEO 的通用电影剪辑决策器，也没有证据表明其指导文字能自动改善生成素材或成片。

## Repository Comparison

| 项目 | 实际形态与可借鉴内容 | 证据边界 |
| --- | --- | --- |
| [narrative-film-direction](https://github.com/Nagacash/narrative-film-direction/tree/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction) | 面向 AI 生成剧情场景的导演方法文档：先锁定场景地理和行动轴线，再用 master shot/keyframe 固定空间关系，规划 coverage，先审 setup still 再动画；覆盖 180°、视线、30°、动作衔接、J/L cut 和节奏。 | 仓库快照只含 README、Skill 和 Markdown references，没有可执行剪辑程序或自动化测试。Worked example 是说明性案例，不是可重放的本项目成片证据。其 5–8 秒片段、4 帧头尾修剪和五组对话覆盖是标明为实践经验的参考值，不能固化为统一规则。 |
| [agent-video-editor](https://github.com/kmilo93sd/agent-video-editor/tree/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos) | 跨工具的剪辑 craft 指南，按 talking head、vlog、podcast、Shorts、screen tutorial 分 recipe；解释剪辑目的、J/L cut、声音、观看检查，且显式标注规则来源及证据强度。 | `evals.json` 是提示及期望答案样例，不等于媒体验收。仓库有可执行的 `edit-engine.mjs`，但它是 narrated screen tutorial 专用：检查素材时间单调、镜头/语音间隙/速度、冻结帧、图文锚点和缩放；不判断剧情表演、运动匹配、轴线、视线、悬念或反应镜头。没有跨题材电影 cut reviewer。 |

### Reusable Decision Methods

- **按事件而非按时钟切。** 每个 cut 至少做一件事：去除无效等待、改变观众获得的信息、跟随动作，或显露有意义的反应。vlog recipe 明确以事件决定节奏；podcast recipe 以说话者变化和有信息的反应切换，并说明没有可靠的统一切镜频率。由此应把题材节奏作为输入和参考范围，禁止把平均镜头长度变成硬门槛。
- **动作匹配与切点。** 先描述出点和入点的动作阶段（动作开始、遮挡/速度峰值、动作完成、反应落点）；同一动作跨镜时让方向、手/物体状态和动作进度可接续，并在可遮住 seam 的运动时刻 Cut on Action。若找不到可以保持动作意图的相邻阶段，标记素材缺口而不是靠转场掩盖。Motion-hide 是一种切点选择依据，不等于给每个接点加效果。
- **空间、轴线与视线。** 使用已批准的场景空间基准记录行动轴线、摄影机工作侧、人物屏幕方位和各自注视对象；反打镜头要能证明其背景空间与 master 相容。180° rule 应作为连续性默认约束，而不是不可跨越的硬禁令：剧情有意换边时，标出观众可读的中性重定位镜头或画面内人物过轴。30° rule 可作为同主体近似角度造成跳切的风险提示，实际以画面接点判断。视线方向应用人物之间的空间关系描述；角度数值只在镜头参考和机位定义足以支撑测量时使用，避免把提示词中的精确数字当成真实视线证据。
- **景别、反应和信息顺序。** 从建立空间的远景、承载行为/对话的中景、强调情绪或信息的近景、关键细节插入镜头中选择观众此刻需要的画面；反应镜头只有在改变观众对上一动作/台词的理解时才成立。Master/coverage 提供选择空间，不构成每场必须拍满指定数量景别的清单。
- **节奏、停顿和揭示。** 以“预期—行动—反应—信息兑现”的事件阶段决定镜头长短；在关键反应、悬念未解或信息将揭晓时允许停留，解释信息后再改变画面。不同题材可以有不同的开场钩子、节奏变化与 payoff，但广告要保持商品真实表现，剧情片服从表演和因果，片头优先建立承诺和观众定位。镜头频率只作诊断统计，不作自动剪切目标。
- **声音桥接与切型。** J-cut 先带入下一镜/场的声音以引出期待；L-cut 保留当前台词或环境声覆盖新画面以维持情绪或空间连续。偏好 room tone/环境声自然延续；桥接长度由台词、呼吸和画面决定。Hard cut 表示直接切换而不叠化，前后动作/空间是否连续仍须另行判断；Match Cut 建立画面、运动、构图或声音之间可辨识的对应关系；Cut on Action 选择运动中的接点。它们是不同决策，不能统一映射成 transition effect。Dissolve 留给时间、地点或段落的真实变化。
- **识别需要补拍的衔接镜头。** 若相邻素材无法提供必要的动作前后阶段、方向一致的入镜、可理解的视线对象、建立或重置空间的镜头、关键反应/信息镜头，或可用的环境声桥，则明确标记为缺少覆盖并反馈：缺少什么画面或声音、应承接哪个事件、建议景别和运动状态、所需入/出动作、连续性依据及所缓解的风险。仅当现有素材没有合格裁切点或允许的重排/声音桥时才建议补拍；禁止默认重新生成付费视频。

## Minimal Integration

把以上内容实现为现有导演与 Shot/Continuity 决策上的**逐接点记录**，而不是新增导演或时间线系统。每条决策至少包含：前后 shot 身份、剪辑类型及原因、源入点/出点（精确到源时间/帧）、承接的动作/情绪/信息事件、景别和屏幕方向/视线关系、声音桥方式和长度、预期观众效果、连续性风险/证据状态、缺失 coverage 与补拍请求。空值不得默认为通过；未知的动作阶段或空间关系进入风险项，交由实际成片审查。

时间点最后由 `ResolvedTimeline` 独占解析并输出；该记录解释为何切以及要观察什么，不另算一次时长、不复制 timeline 推导。QA 将决策中的预期效果和风险转成接点级观察项，绑定 exact rendered MP4 的 identity 与边界帧/短播放区间，实际看原速声画；自动场景检测、帧提取或结构检查只能提供线索，不能签署连续性/情绪节奏结论。若 QA 观察与计划不符，记录 `FAIL` 或 `NOT_EVALUATED` 和证据，并进入现有修复/补拍所有者。

## Licensing And Reuse Boundaries

`narrative-film-direction` 仓库有 MIT `LICENSE`，但 Skill frontmatter 标 `CC-BY-4.0`，`LICENSE-DOCS` 也称文档适用 CC BY 4.0；该文件的适用路径仍写作 `skills/prove-it/references/`，署名也指向 `prove-it`，与仓库名不一致。文档许可存在歧义：本次只综合方法，不复制其提示词或长段原文；若将其文字、示例或具体表达并入项目，应先核对作者/许可范围并履行正确署名。

`agent-video-editor` 将代码和文本列为 MIT，音效库与图形素材各自列 CC0。当前适配无需复制或引入其素材、脚本或完整 recipe；只概括剪辑原则和按题材区分决策的做法。第三方仓库的许可并不改变 AI-VIDEO 的 canonical owner、真实媒体验收或运行约束。

## Primary sources

- Naga Codex，`SKILL.md` 与 reference 文件，快照 `4ee8b42484cb57407f4a7772216aa79e20b0971f`： [导演流程](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction/SKILL.md)、[覆盖规划](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction/references/coverage-protocol.md)、[轴线和视线](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction/references/screen-direction.md)、[剪辑语法](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction/references/editing-grammar.md)、[镜头示例](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction/references/worked-example.md)、[来源强度说明](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/skills/narrative-film-direction/references/sources.md)、[仓库许可](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/LICENSE)、[文档许可](https://github.com/Nagacash/narrative-film-direction/blob/4ee8b42484cb57407f4a7772216aa79e20b0971f/LICENSE-DOCS)。
- kmilo93sd，`agent-video-editor`，快照 `8e32c0aff64c445ef1e2b87bc04408a34d68c973`： [Skill](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/SKILL.md)、[剪辑节奏与切点](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/references/pacing-and-cuts.md)、[成片检查清单](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/review-checklist.md)、[Vlog recipe](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/recipes/vlog.md)、[Podcast recipe](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/recipes/podcast-to-youtube.md)、[教程剪辑实现](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/recipes/narrated-screen-tutorial/templates/edit-engine.mjs)、[示例 evals](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/evals/evals.json)、[代码许可](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/LICENSE)、[音效许可](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/library/LICENSES.md)、[图形许可](https://github.com/kmilo93sd/agent-video-editor/blob/8e32c0aff64c445ef1e2b87bc04408a34d68c973/skills/editing-videos/graphics/LICENSES.md)。
