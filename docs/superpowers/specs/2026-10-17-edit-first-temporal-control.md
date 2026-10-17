# Edit-First Temporal Control

## Goal And Authority

用户明确要求将剪辑/变速对齐纳入上层通用制作控制，先检查已有素材能否满足最终目标，再决定是否生成。
本任务授权共享实现、离线预览与必要契约修复，无新付费POST、Provider或依赖范围。Parent自主裁决并继续执行。

## Current Gaps

ProductionStrategyResolver已有复用/裁切候选，但可在源用途缺证时直接选可行生成；EDIT_EXISTING_VIDEO仅有enum。
Canvas质量修复直接进入generation-only feedback。P3契约仅trim、强制源帧数等于目标帧数；pinned HyperFrames虽然runtime可读rate，实际导出不消费该属性。

## Contract

- 生产手段选择仍归ProductionStrategyResolver，新默认policy `/2`在qualified_reuse下优先处理具有更少生成次数、且仅缺用途评估的可行源候选。显式FAIL不伪称NE；旧显式policy `/1`保持旧语义。
- Source option、用途证据及CompositionLayerSpec共用可选VideoTimeMap；有序整数锚点(source_frame, output_frame)，相对所选源trim，起点(0,0)，终点精确等于源/目标帧数；两轴严格递增，无反转、插帧、冻结或跳跃。首版逐段倍率范围0.1–5。
- 新CompositionSpec/ResolvedTimeline 2.3表达变速；旧2.0–2.2空字段序列化/hash不变，旧schema拒绝非一比一时间映射。
- ResolvedTimeline唯一解析映射：每段有精确source trim、output frame/sample起止，并编译成顺序visual spans；同Shot不创造切镜或第二timeline。非一比一段按每个输出帧取floor(source coordinate)展开为1帧spans，HyperFrames消费现有一比一source window；不依赖该版本导出会忽略的data-playback-rate。
- 首个范围只支持显式muted视觉变速。源声音保留/口型同步、同Shot音轨/字幕/voice source不能静默沿用，缺样本级映射时明确拒绝。独立声音及所有最终要求继续由原P4/QA拥有。
- 用途证据绑定exact time map、bytes/window/role/transform及原要求；未变速PASS不能资格化变速用途。原始生成失败不被改写为PASS，编辑成片仍须新证据及最终验收。
- Canvas暴露现有ProductionPlanningService的薄prepare/materialize入口；闭合quality失败的再次生成先过上层重评，缺ProductionIntent返回明确authoring缺口。known-no-effect、unsubmitted、runtime recovery和unknown边界保留。
- 材料化后的source-backed族从已验证lineage和当前用途资格重开CompositionSpec，续接标准Canvas position/compose/render；不反造未持久化的原Decision或hash。与普通镜头合并后核验完整P4，外部occurrence剪辑边界从实际首/末子镜的ResolvedTimeline取证。首版不自动推进仍需原generation owner处理的动态组件；unknown优先STOP。
- 已失败MP4进入编辑候选须保留可重开的原request/fetch/rejection与qualification状态，不通过普通导入隐藏已知失败；开发preview与Production qualification分开。

## Acceptance And Limits

至少两种不同源/时长的normal、boundary和failure用例验证整数映射、用途证据失配、Planner编辑优先、source FAIL与NE分流、错误audio组合、旧hash重开及无POST。
实际pinned HyperFrames对可识别帧源证明源帧选择，并对本次已生成几何人物提供离线剪辑预览与显式MCP观察；不声称human完整1x或通用模型质量PASS。
不修改原《界蚀》或几何人物失败attempt、原消费/额度、原采用窗口和required findings。禁止故事专属分支、直接mux最终交付或自动activation。
