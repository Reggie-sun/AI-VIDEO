# Continuous Canvas Production

## Shared Method

本方法来自两套实际画布，目标是复用整段制作组织，而不是照搬某条prompt或保证模型质量。
《反向之地》原捕获件有39个生成节点；《白带子》当前完整图有296节点、66个视频节点和一条8片段时间线。
白带子图中的「固定框架」「锁定素材」「母版」「分镜提示词框架」明确写有素材职责、完整因果、动作结果与前后承接。

| 共用步骤 | 制作时保留什么 | Harness现有承接位置 |
| --- | --- | --- |
| 固定角色与资产职责 | 谁是谁、谁说话、每份参考只管身份/场景/动作/声线中的哪些方面；参考画面是起点、途经状态还是终点 | Character、Scene、Registry、semantic reference roles |
| 先讲清整段 | 开场状态→触发→行动与反应→转折→结束状态，不以镜头数量代替剧情 | Story、Storyboard、Shot intent |
| 空间和摄影有因果 | 人物左右/高低、门与桌、持物、光源、轴线；镜头因信息和动作变化而移动/切换 | space/lighting/camera intent、open/close state |
| 表演写过程和落点 | 谁先注意、为什么动、如何受影响、怎样落定；不同人物按处境反应，不用眨眼/呼吸数量替代自然表演 | action/performance/dialogue intent |
| 声音参与叙事 | 原对白、说话者、声线职责、声源、先听后反应；旁白/BGM/字幕是否允许按本段决定 | audio intent、existing source-audio policy |
| 前后段承接 | 前段实际结束状态、后段要求起始状态，以及允许发生的变化 | existing sequence_continuity adapter、typed causal state changes |
| 全片采用 | 原声原时序、连续观看、实际听辨、用户反馈与已知偏差分开保存 | per-Shot media Gate、human final acceptance |

不是所有画布都套一镜到底。反向之地一组内有切镜，组与组继承叙事状态；白带子既有独立长镜头，
也有跨世界的连续段落与遮挡剪接。时间轴里的顺序不证明连续性已经成立，reference边也不是剧情顺序。

## Sequence Before Individual Nodes

先选定明确的故事链或画布timeline，不能按画布坐标、节点名字的数字、共用图片或创建时间自动排序。
保留同节点在timeline中重复出现的每个clip身份。variant不是新的剧情段；不将全部候选排列成片。

每个相邻边界都明确说明：

1. 前段实际结尾与后段计划开场分别是什么，引用原文用于说明意图，引用实际视频用于证明结果。
2. 哪些人物、持物、接触、动作阶段、视线、对白轮次、画面运动轴与声音需要承接。
3. 哪些变化可见地发生，哪些在明确切镜/换场后允许释放；光源、场景与天气仍归各Shot对应状态。
4. 用首帧、尾帧、视频、共享资产中的哪种参考来帮助承接，具体角色由导演决定；不得默认每镜继承上一尾帧。

反向之地24→25→26→27组要保留小龙从上铺下来、空手、门口堵桌、手机照明，以及曾亮按肩后的关系。
白带子8段链后半部分用「生物贴镜遮满→下一异世界从遮挡中继续前冲」接续，
保留运动趋势和叙事目标，同时允许生态、场景和局部光源改变；不能误标成同一地点完整状态不变。
这些是原文里的制作安排，不是本轮重新审片得到的质量结论。

## Reusable Offline Entry

`scripts/canvas_sequence_packet.py`一次保存选定顺序、逐段原始prompt/parts、参数、素材身份、共享资产和边界。
接受已有`canvas_reference_packet`输出，或浏览器只读保存的canvas document（nodes/edges/generationDraft）。
原始parts中的引用slot保留，不用字符串替换猜引用，不省略未在正文出现的video/audio参考。

选择文件使用`{"node_ids": ["node-a", "node-b"]}`，或者`{"timeline_id": "timeline-node"}`。
默认480p；旧画布的720p/1080p仍留在observed_parameters，不自动覆盖用户默认。

```bash
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_sequence_packet \
  --source canvas-document.json --selection selection.json --output sequence-packet.json
```

可选`boundaries`以source_occurrence_id/target_occurrence_id绑定相邻段，timeline使用clipId，显式node列表使用nodeId。
每项包含两侧正文的source_close_quote/target_open_quote，以及现有BoundaryKind、ContinuityObligation、
CausalEdgeSemantics枚举值和causal_state_changes；full_continuity必须提供完整十维。
没有boundary时导出BLOCKED_MISSING_AUTHORING；完整时也只是AUTHORED_NOT_MEDIA_VERIFIED，不是READY或PASS。
`--resolution 720p`或`1080p`只在用户明确要求时使用；模型不支持480p时返回能力问题，不静默升级。

## Production Handoff And Cost Boundary

本包只是可复用的前置准备资料，不是第二套Production schema、Manifest或可付费执行计划。
将选定顺序写入既有Storyboard，逐段创作进入现有Director/Shot contracts；批准过且意图不变的Shot不重做创作。
保持原文与明确变更diff；换角、参考适配或剧情改写不能伪装成完全复刻。
跨段通过`build_sequence_video_planning_request`及`prepare_sequence_shot_for_existing_production`进入既有Planner/Router。
真实accepted source、实际末态、Registry bytes和route由这些owners重开，不以原prompt的结尾描述代替。
新工具未实现全自动画布→ProductionProject编译器，亦不声称已存在通用无人值守连续生成driver。

下一次同链修改只重新读取受影响节点、相邻边界和引用身份；输入未变时复用封存资料，
新提交仍必须核对当前源身份与用户授权。通过当前实际输入预览审查后，沿用现有单次执行与逐镜Gate。
不默认增加Team/Claude轮次，不重复造临时上传/提交脚本；明确要求Claude时只审本次输入与差异。
工程PASS、抽帧和ASR不代替完整听看；用户觉得可采用也不抹掉已知偏差。
