# Official and Community Evidence for H3 Action-Timing and Reflection Repairs

Date: 2026-10-17

## Follow-up — Edit-First Temporal Control (2026-10-17)

后续[edit-first实现记录](../record_for_agent/2026-10-17-edit-first-temporal-control.md)显示，同一失败 robot 视频可经 `ResolvedTimeline` 整数帧映射制作静音本地预览；2.0s 手臂垂下和 3.5s 左臂水平只获得编辑后样帧级 PASS。这把“可否通过剪辑验证既有画面”从待探索问题推进为单源实现证明。它不改变原 H3 Max CN 在约 4s 才达到水平、原 QA 的 FAIL/NOT_EVALUATED 或已停止的 Provider attempt，也不证明精确时序可由模型稳定生成、整段动作自然、声音保留、人工完整 1x 或 Production 质量。

下文关于下一步输入表达检查的建议保留为历史方向；现行 [workflow](../canvas-production-harness.md#edit-first-temporal-control) 先评估既有素材与剪辑/变速，再决定是否生成。

## Generic Reference Timing Follow-up

后续[几何人物R2V单元](../record_for_agent/2026-10-17-generic-h3-robot-reference-pilot.md)已观察到：
白模3.5秒平举，H3 Max CN输出约4秒才平举。这个有界反例不要求从零探索全部工作流；
应先复用可追溯做法并核对适用性，真实调用只验证尚未解决的目标，不重复验证已知接口边界。
本节为资料核对，无新媒体调用，不改变该attempt的FAIL/NE、输入或STOP。

- **Official reference semantics.** 官方[full-reference指南](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)
  区分主体特征、具体帧锚点与视频整体时序来源，并要求说明各自保留、部分保留、转移或弱参考的关系。
  `reference generation`与直接编辑原视频的`video editing`不是同一意图；仅借用动作/摄影不自动成为原视频编辑。
  指南说明的是rewrite output格式；不能据此断言CN API原始prompt必须有六个英文段，
  也不能把`fully_preserved`这种意图声明当作原生逐帧控制或执行保证。
- **Exact API boundary.** [当前CN API](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)
  的H3 Max扩写选项为`disabled`、`balanced`、`quality`，当前单元已用默认`balanced`。
  没有取得该次服务端重写文本，不能声称其内部一定保留或改变了动作时间；
  官方H3 Base的Context-IR指南也不证明H3 Max服务内部实现。
  不凭“质量优先”名称断言切换`quality`会解决时序，不把关闭扩写当已经验证的修法。
- **Community delay counterexample.** [第一手视频输入讨论](https://www.reddit.com/r/StableDiffusion/comments/1vg20lv/some_tips_for_feeding_videos_in_to_minimax_h3/)
  建议输入/输出时长一致、强制24fps；同帖仍有人报告动作相同但输出变慢、延后，
  自述需要约1.2倍retime才能匹配。这是本地H3用户观察，没有H3 Max CN的受控修复证明；
  不能将1.2倍直接套用到其他镜头、声音或原采用切点。本次来源已为5秒/24fps，不能把再统一帧率当新修复。
- **Reusable positive practice and limits.** [Blender参考案例](https://www.reddit.com/r/StableDiffusion/comments/1wqydpg/blender_camera_motion_minimax_h3_ref2vid_in/)
  用白模负责摄影运动、人物图负责身份、背景图负责环境；作者仍要求检查构图与衔接。
  它提供制作方法，没有3.5秒动作deadline的误差测量，且为本地采样，不能代签CN API质量。
  [人物替换原帖](https://www.reddit.com/r/StableDiffusion/comments/1vojyye/minimax_h3_ref2v_character_replacement_prompting/)
  还报告整个人物替换时`reference generation`比`video editing`好，后者过度保留原人物；
  因此不能把“全部改成video editing”升级成通用答案。

对当前案例，图/视频职责、同5秒长度和24fps已经核对；接下来可在既有authoring owner内离线检查
保留/转移关系、主体与视频时序是否被明确表达，以及所选模式能提供的控制强度。
现有`input_control`与prose可表达这些关系，资料没有证明必须新增schema、Provider或另一执行链。
这类输入核对不证明改写有效。只有要承诺某个model/mode在目标场景中稳定达到精确动作时点时，
才还需要有明确问题、通过标准和停止条件的有限真实验证；未取得新授权不执行。

## Scope and Current Evidence

本记录只评估离线提示表达，不修改 Production、不调用媒体服务，也不为下一次付费调用背书。当前 A 是官方 MiniMax H3 Max CN，标称 5 秒、768P，以原 PNG 作为唯一 `first_frame`，没有 `reference_video`；原采用合同仍为 S01 的 0–3 秒，最终 timing 归 ResolvedTimeline。最新 QA 为 6 PASS / 2 FAIL / 7 NOT_EVALUATED，`s01-reflections` 和 `s01-close-gap` 失败：约 1.5 秒起出现林砚抬手的玻璃幽影，解码的 frame 71（约 2.958 秒）仍在抬手，未在采用切点前落定。15 项原 QA 与 STOP 保留，详见[当前 S01 记录](../record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md#current-official-h3-max-first-frame-result--2026-10-17)。

现有生成文本已写“左手距窗约2cm停住”“保持到切出”，所以缺口不是没有终点状态，而是没有把该状态明确绑定到 3.000 秒采用切点。一次失败只能证明这组输入没有通过，不能证明缺少数字时点是唯一原因。

## Official API and Prompt Guidance

MiniMax CN V2 文档列出 H3 Max 时长为 5–15 秒整数；首帧图生视频请求使用 `text + first_frame`，且与 `reference_video` / 多模态参考角色互斥。公开 schema 中 `duration` 是整段时长字段，没有逐动作定时字段。因此 5 秒只是原生输出时长，不代表模型承诺在 3 秒前完成某个动作；3 秒采用点仍由既有 ResolvedTimeline 决定。[官方 API](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)

MiniMax 官方 H3 Base 提示指南将 I2VA 描述为从 0 秒首帧向前发展，并推荐“首帧锚定→动作起始→连续发展→结果或反应”。它规定 `[Shot N] At ...` 时间用于后续镜头切点，Shot 1 不写时间戳。故可在当前单镜自然文字中明确“3.000 秒前到位”，但这是待验证的提示表达，不是 API 定时控制；不应为了时间提示虚构 `[Shot 2]` 或真实剪辑点。指南中的示例正向描述“她的倒影在玻璃上移动”，但没有选择性移除单个人物倒影的开关或保证。[官方 H3 Base I2VA 与镜头时序指南](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md)

上述提示写法来自官方 H3 Base 指南，不等于官方证明 H3 Max CN 具有相同提示遵循质量；API 约束仅针对该 CN V2 文档所述接口。

## Traceable Community Evidence

- 一位本地 MiniMax H3 用户报告，将提示写成 `[0s–2.5s]` / `[2.5s–10s]` 后，首段实际占了约 6–7 秒；另一位用户建议按官方格式在后续镜头写 `[Shot 2] At 00:03.000`，原作者自述修正后解决。它支持先遵循官方镜头语法，但属于单个用户报告，运行模型变体未说明，也不能证明镜头切点语法会精确控制同一镜头内的手部动作。[原始时序故障讨论](https://www.reddit.com/r/StableDiffusion/comments/1vff69w/minimax_h3_ignoring_time_stamps_in_prompts/)
- 另一位公开本地 Full BF16 MiniMax H3 用户称，15 秒三段视频的场景大致落在提示时间窗，但一个要求精确时点的水滴音效没有出现。它是可追溯的正向但有限反例：时间顺序和场景窗口有时可用，精确事件时点仍会偏离；这是本地 H3，不是 H3 Max CN API。[原始生成与时间反馈](https://www.reddit.com/r/StableDiffusion/comments/1veofu3/minimax_h3_full_bf16_1920x1088_15s_single/)
- 一个独立社区 H3 仓库保留了相同 prompt 的 Native H3 与实验性 Semantic Bridge 视频。其作者报告 Native H3 将“右手平放在玻璃桌面”变成移动手部，而实验版本保持静止；作者将其明确限定为定性单对观察。该 bridge 面向标准 H3 Base FL2VA，仓库明确不支持 Ref2VA，并报告参考音频测试出现歌唱/口型退化；它也未验证 H3 Max CN API，因此不能移植到本次请求。[社区仓库及受限 A/B 说明](https://huggingface.co/speach1sdef178/MiniMax-H3-Semantic-Bridge/blame/1e4f878d5999b1655c095540a05a154f676bdfbb/README.md)
- 本地 H3 的另一条用户讨论报告，同一提示的多次生成中，玻璃戒指倒影有时继续缩放；另一个用户观察到桌面物件倒影能随手部动作对应变化。这些相反的单例只能说明反射既可能表现良好，也可能漂移，不能证明当前场景可稳定选择性保留或排除某个反射。[倒影漂移讨论](https://www.reddit.com/r/StableDiffusion/comments/1virhsf/doc_ock_transitions_of_various_kinds_using/)；[正向倒影观察](https://www.reddit.com/r/StableDiffusion/comments/1vejrb3/we_are_cooking_folks_h3_full_precision_weights/)

截至本次检索，未找到可信、可复核的社区证据证明单靠提示即可稳定保留七位乘客倒影、同时排除林砚身体和左手的反射。不要把社区对负向词的经验升级成模型保证，也不要把上述本地 H3 案例外推为 H3 Max CN 质量结论。

## Bounded Offline Revision Candidate

可在既有 Canvas authoring 文本 owner 内保留当前两段约 1202 字符原文和 15 项 QA 原样，再追加一个清楚标记的技术修订段；不替换剧情，不改模式、不新增素材/参考，不引入第二主动作：

1. 从首帧的坐姿、固定摄影和空座异常开始，只描述原有左手靠近玻璃这一主动作，按起因、过程、落定顺序表达；手不接触玻璃。在 3.000 秒采用切点前到达原定约 2 cm 悬停状态，并保持至该切点。
2. 为满足 H3 Max 的 5 秒技术时长，3–5 秒只延续同一已落定姿势、构图和空间状态，不增加剧情、动作或视线事件；生产采用范围仍为 0–3 秒，由 ResolvedTimeline 裁切/定帧规则拥有。
3. 将倒影写成局部、正向且可观察的关系：保留六名乘客与苏遥各自一次、完整的倒影；林砚对应的玻璃区域持续显示可见的空座/车厢视图，不出现林砚身体倒影或抬起左手的幽影。不能用“没有任何倒影”这种全局描述覆盖七个必须保留的倒影。

此候选利用官方 I2VA 的首帧锚定和动作顺序建议，并把既有 end state、采用切点与选择性异常表达得更明确；这只能改善输入的可解释性，不能保证精确 3 秒落点或反射抑制。若未来有新的有限媒体授权，仍须在精确输出上重验全部 15 项 QA 和逐帧时点；工程/离线检查不能解除当前 STOP，也不能证明通用质量、连续镜或完整故事通过。

本项目的 preserved-source 路径要求新增段先进入新 inspected snapshot，原生成图 selection 证据也必须经既有 import owner 绑定新 snapshot；不能只在 direction 或 compiled request 里附加文字。纯 author bundle/preflight 可验证这些输入，但不提供该候选的执行 binding、额度或 Provider 编译证明。当前可执行步骤和证据边界归[共享 workflow](../canvas-production-harness.md#action-timing-and-selective-effects)，不把社区经验采纳为新 Gate 或已证明的质量规则。
