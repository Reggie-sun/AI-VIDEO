# Lost Frames Opening Reconstruction

## Goal And Scope

将方向C的静态概念包装改造成可观看的视听叙事预演：正常的城市运动逐步收束到两人关系，遮挡前后以空位改变观众记忆，人物继续生活，片名最后进入影像。保留剧本揭示边界和原Suno B录音，不新增付费视频生成。没有匹配素材的正式摄影镜头保留导演及生成输入，不冒充完成。

## Ownership And Decisions

Parent唯一写入 `outputs/shizhen-episode01/opening-reconstruction-20261026/`、本计划和独立session record；不改其他窗口文件、原片、旧FAIL/UNKNOWN或Production lifecycle。`open-video`为创作owner，Motion/Kinetic提供克制的运动及排字方法；现有CompositionSpec→ResolvedTimeline→HyperFrames拥有剪辑、样本及输出。独立只读concept reviewer已指出同构图空位后态过短，优先补真实运动观察时间。

比较三种机制：城市日常中的关系消失；日常照片中的关系缺席；连续建筑空间失去一段时间。选择第一条：已有真实动态素材能承载原因与结果，另两条缺关系源或连续摄影源，强做会再次成为海报或引入新机制。城市stock只作临时动态预演，正式版需匹配雨夜、地理与人物画风。

## Work And Verification

1. 固定当前C、海报、剧本、原设计、A1/A2/A3、S01及Suno B身份；研究参考片头并区分实际抽帧、创作者访谈与无法取得的媒体。
2. 在独立development project中经唯一committer准备来源；外部stock有作者/许可/原片与24fps无补帧derivative记录。重用generated源沿现有qualification preview capture；只改本次用途，不改历史判决。
3. 实际渲染视听预演。原片内对白在视觉片头中显式MUTE，以原音乐与真实环境源补声；不可用声音保留缺口。不得用静帧延长空位、循环对白、时间倒放或身体残影掩盖素材不足。
4. exact MP4经project-local video-analysis、密集接点抽帧、1x浏览器播放、音轨及原源身份核验；独立read-only审片，缺聆听/人工审美证据明确NOT_EVALUATED。制作可打开的审看页和可生产镜头包。

## Feedback Clarification And Handoff

用户后续指出候车本来是另一组人物，说“我觉得很好啊”“继续”。撤销将其对HTML的质疑扩大为整套候车创意被否决的判断；不据此自动签署R2艺术通过。原先静音原对白的R2保留用于比较，但下一连续版恢复“两位/就我一个”的声音关系，并衔接片名、翌夜与S01。另一制作窗口唯一写入 `outputs/shizhen-episode01/opening-narrative-integration-20261026/`；本窗口继续独占原重构目录、复核反馈与实际成片，避免重复剪辑或同时修改共享runtime。新生成两张共伞PNG归备选静帧设计，未启动视频生成，不强制替换候车段。

## Completion Boundary

本轮已有可观看交付：相邻制作目录 `focus-002/失帧-两位-关键事件重剪-002.mp4`，18.417秒442帧，SHA `f3c03c289bb770b209a355ffad5c59f732168d10d30553f249882c382a19faa9`。本窗口完成反馈纠正、两次实际接点缺陷发现及修复核验、一次既有reviewer最终复核、模型音频结果核对和唯一审看入口。明确仅候车事件预演，宏观至微观整段设计与艺术验收尚未完成；本地入口字节Range修复仅保证真实跳转，不代替艺术通过。详情归session record与 `qa/standalone-review/002/verdict.json`，不再追加本轮媒体。

后续范围同步：用户明确只要前面的开场，与S01无关。停止衔接版推进与展示；独立制作目录完成standalone候车关键事件重剪，本窗口只复核该最终候选。既有衔接测试保留为历史，不能将其当本轮交付或追加S01工作。

预演与最终成片明确分开；所有评价对exact媒体，不把渲染、字体或结构PASS当艺术PASS。遵守film-first：先交用户审片，用户认可后才完整工程验证、owned-path commit/push。当前不改共享引擎，不为本次作品扩建Skill或第二渲染器。
