# Shot-to-Shot Editing Decisions

Codex 仍是现有 Director/Editor。先看选中素材，再决定切镜；将决策写回现有 Canvas
`cut_requirements[].editing_intent`，源裁切/音轨放回 CompositionSpec，沿唯一 ResolvedTimeline、
HyperFrames、cut packet 和原有 P6/final-film QA 执行。下列方法不是固定剪辑配方或新执行许可。

## Decide From The Event

先明确观众在此刻应看到/听到什么变化：跟随行动、理解结果、接收新信息、观察反应、维持悬念，
或有意重置时空。能靠当前表演承载时允许停留；空等与有意义的停顿须区分。先守住完整行动、
台词、理解和回应，再选最有效的视角。不要按每句对白、生成片段边界或平均镜长自动切镜。

| Type | Decision emphasis |
| --- | --- |
| 剧情 `drama` | 行动因果、人物接收信息的时机、情绪停顿与反应；悬念先建立预期，再控制揭示与后果 |
| 广告 `advertisement` | Hook 后保留产品识别、真实尺度、使用过程和反馈的可读时间；产品插入须有因果动机，遵720p合同 |
| 片头 `opening` | 先建立空间/基调/叙事承诺；信息与标题不能抢走决定性事件，不强制快切或踩每个节拍 |
| 其他 `other` | 写明当前形式与观众目标，由内容决定节奏，不从其他 recipe 借固定频率 |

## Choose And Explain The Cut

- **Cut on Action：** 对照实际动作阶段和支撑转移，选择可连续接续的运动节点；核对方向、速度、
  手/物体状态及动作是否重演。运动可掩护接点，不能补出从未发生的动作。剪掉必要因果或完整台词时换方案。
- **Hard Cut：** 直接换画面；可用于说话者/反应/信息变化或有意省略过程。明确是否连续动作或时间省略，
  不能把不同动作阶段硬标为匹配。无明确变化的近似机位易跳，先看改变景别/角度是否提供新信息。
- **Match Cut：** 写出跨镜对应的是构图、物体、运动、概念或声音，以及它建立的意义。构图相近不证明动作连续。
- **空间/180°/视线：** 用既有场景基准、行动轴线、摄影机工作侧、人物屏幕方位、视线对象和背景地标判断。
  同向脸朝向不能替代真实空间关系；反打不等于过轴。有意过轴要用观众可读的机位移动、人物过轴、
  中性镜或重新建立空间来交代。参考图角度、prompt 数字不是真实几何测量。
- **景别/反应：** 广角/全景交代关系，中景承载行为，近景或插入镜显露决定性信息；按当前需求选择。
  反应应改变观众对事件的理解，先让人物接收到触发，再给足可读反应。不要用一闪而过的反应掩盖失败表演。
- **停顿/悬念/揭示：** 写明此切是延迟答案、揭示事实、兑现预期或延续情绪。审查动作完成、呼吸和情绪尾部，
  不是只比较镜头长度。先确认背景、道具插入有叙事任务，避免以无关空镜填容量。

J-Cut 是下一镜/场的声音先进入，L-Cut 是前一镜声音留到新画面；环境声可独立桥接两镜。
将声音和画面切点分开考虑，记录真实来源、意图与应跨接的音轨；保护原句、尾音、呼吸、room tone、
人物口型和空间声。使用现有 AudioTrackSpec 的 start/trim/fade，经 resolver 确认实际 sample spans。
轨道跨切点只证明结构上可能桥接，不能证明声音来源、J/L方向或听感正确；不能用任意 BGM 冒充接话。
现有 source-audio/对白准入不支持的声音重排须报告缺口，不伪装素材类型或 direct mux。

## Record Through Existing Owners

`ShotEditingIntent` 定义在 `src/ai_video/production/junction_review.py`，直接供 Canvas cut requirement 使用：

- `narrative_type`、`technique`、`reason`、`expected_effect`：题材、切型、为什么切、观众应理解什么。
- `outgoing_phase`、`incoming_phase`：可观察的前镜出态/后镜入态；源帧/素材SHA从 cut packet 回读，
  不在 intent 另算 timeline。改切点须修改原 CompositionSpec 并重新 resolve/render。
- `axis_eyeline_space`、`scale_reaction`、`rhythm_reveal`、`continuity_risks`：本接点的空间、信息与节奏义务；
  不适用的项说明原因，不留空、不自动判PASS。
- `audio_treatment=sync|j_cut|l_cut|sound_bridge|silence`、`audio_reason`、`audio_track_ids`：
  声音目的与实际 resolved 轨道；`technique=hard_cut|cut_on_action|match_cut|reaction|reveal|scene_reset`
  是剪辑语法，不能据此新增转场效果。
- `pickup_requirement`：缺失覆盖的反馈；无缺口用 null。填写缺少的动作/反应/视线对象/空间建立或声音、
  所需入出态、景别及所缓解风险。先穷尽现有素材可用切点、合理重排和有依据的声音处理；
  未补足时不签当前接点PASS，更不自动提交付费重生成。

Canvas 将 intent 展开为 final-output requirements，并在现有 cut packet 携带 canonical 源帧、SHA、
音轨和导出 identity；使用原有 QA/evaluator、whole-playback human requirement 与 committer。
旧 direction 无该可选字段时保持兼容；不要把旧接点PASS宣称为已覆盖新增剪辑维度。

## Inspect The Actual Film

使用既有 [assembly entry](../../../../docs/visual-quality-gate.md#assembly-harness-entry) 准备模板，
当前输出为 `assembly-review/2`。除原 action/声画观察外，逐刀填写 `editing_intent`、
`source_selection` 与 `editing_review` 的动作匹配、轴线视线空间、景别反应、节奏揭示和声音桥观察。
模板只在前后各有一个 resolved visual span 时投影源窗口；多层/retime segments 需显式选择
实际边界 span，不猜主画面。`source_out_frame_exclusive` 是出镜源窗口的排他端点，
`source_in_frame` 是入镜源起点，二者单位沿用 resolved trim 的 delivery-frame grid；有变速时同时看真实映射。

`verify-assembly` 继续绑定 exact MP4、timeline、renderer report、inventory、回答原字节；
新维度缺失为 NOT_EVALUATED，错源入出点/未解析声桥/显式失败/未补足 coverage 为 FAIL。
旧 `/1` 可读取，不能通过删新字段或改版本绕过当前 Gate。结构匹配不证明自然度；原速完整动作和实际听验
不足时保留 NOT_EVALUATED。Development Gate 不写 Product state，也不代替人工最终验收。

除 Shot 级边界外还要扫看生成片内部摄影切镜；scene detector 只给候选，漏检/误检都可能。
对真实跨镜节奏至少回看接点前后完整事件，再看整段/整片，核对叙事效果与已满足目标未退步。
修剪建议不等于修复完成；更新成片后所有 exact-byte 证据重做。

## Sources

这是本项目现有 Director/Edit/QA seam 的适配，不复制第三方代码或提示词。参考方法、exact revisions、
许可歧义及不采用的固定时长配方见 [primary-source research](../../../../docs/research/2026-10-27-shot-to-shot-editing-reuse.md)。
