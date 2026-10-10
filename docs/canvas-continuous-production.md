# Continuous Canvas Production

## Reusable Production Entry

先从 exact source 和显式 selection 生成 inspection；未选链、selected source gaps、unsupported subject/edge/track
均定位报告，其他未选择单元的失败不禁止当前合法链。

```bash
PYTHONPATH=src:. .venv/bin/python -m scripts.canvas_production_source \
  --source canvas-document.json --selection selection.json --output inspection.json
```

Product application 不 import `scripts`。固定一次现有 runtime 配置后，各故事仅替换 inspection、导演数据与素材选择：
`CanvasProductionService.from_inspection(inspection=..., direction=..., committer=..., targets=...,
routing_policy=..., decision_policy=..., execution_stack=..., handoff_preparer=...)`。
targets 使用既有 `RegisteredGenerationTarget`，profile/compiler/credential supplier/预算/permit 保持原 owner；
不从画布模型名自动授权、换 Provider 或访问 credential。handoff_preparer 只供应既有 owner 已 materialize 的
C2/C4 conditioning，不在只读 prepare 中生成素材；当前共享 caller 支持 same-stack 交接，cross-stack 不推断或 fallback。

导演输入的 `brief/story/characters/scenes/storyboard/shots` 内容直接使用既有 models，省略内部
`artifact_id/revision/content_hash/creation_receipt_id/source_provenance`。`shots` 以 occurrence_id 逐一绑定、保持
Storyboard 顺序；同节点重复 clip 使用不同 Shot ID。source_text 原文和适配 diff/reason 可审查，显式 source_dialogue
变化拒绝。每个后续 Shot 必填 typed boundary；有意独立可填 `{"independent": true, "reason": "..."}`，
但不能覆盖 source 已声明的 continuity。完整 causal columns 是导演目标，hash 由 helper 计算，不构成实际末态 PASS。

`author()` 只准备 bundle；`approve_authoring(bundle=..., attempt_id=..., qa_policy=...)` 才经 committer 批准。
可消费已有 qualified Registry/PreparedArtifact，或通过 `png_selections` 和 `allowed_asset_root` 选择本地 PNG；每项填写
asset_id label、node_id、resource_id、path、usage_license，不填写 hash。PNG bytes 经现有 measurement/no-follow seam，
Registry identity 自动计算。node/resource 声明与 source snapshot 一致，但本地文件不自动证明来自平台或被原用户采用。
其他视频/音频导入使用现有 Registry owners，不能把 resourceId 或 URL 当作已获取 bytes。

`prepare(limits=...)` 重开 actual Project/Registry 并返回现有 decision、compiled request 和 typed capability exits；
`start(limits=...)` 仅开始当前 durable attempt，`execute(action=...)` 最多做一个 next action。
缺 selected voice 时可用 `generate_voice(prepared=..., **authorized_runtime)` 委托既有 selected voice handoff，再 reprepare；
voice candidate/preparer、authorization 和 dependency transition 由既有 runtime 配置提供。
fetch 后显式 `await evaluate(session=project_local_video_analysis_session, adjudicate=...)`，逐项 PASS 才允许 validate/activate；
`position()` 从 Manifest/request/adoption 重开。unknown 返回 stop，不新建 attempt、不 remint 或重放 submit。

`register_native_audio(shot_id=..., audio_kind=..., usage_license=..., toolchain=...)` 从 exact accepted video 提取 WAV；
对白/旁白另填真实 speaker_id/voice_id/language，script hash 从批准 Shot 原文计算。composition 用实际 registered AudioTrackSpec
绑定 Shot，native sound 没有 exact WAV 时必须显式 mute 或停止；BGM 不充当原对白。
`compose(audio_tracks=..., caption_tracks=..., voice_sources=...)` → `render(attempt_id=..., toolchain=...)` → `deliver()`
均沿现有 owners。trim 以 Production frame/sample 表达；source tick timebase 不猜测，speed/gain 非支持值停止。
默认新项目以480像素短边、24fps保持来源显式 aspectRatio（16:9为854×480，竖版9:16为480×854）；
来源未声明比例时使用640×480。混合或未支持比例要求明确 delivery_profile；capability 不支持时停止。
已成功 render 的同 attempt replay 不再次执行 renderer。相同 bytes 的不同 visual asset IDs 遇现有 renderer bundle duplicate-path
检查时停止，不自动改 identity；可由导演选择同一已准入 asset 的正常复用策略。

`revise_authoring(attempt_id=...)` 显式批准当前新导演输入，creative paths content-addressed，未变化 artifacts 复用；
既有 P5 owner 计算局部失效并保留历史。它不授权重生成，也不自动替换失败/unknown attempts 的恢复决定。
`deliver()` 只展示 exact final target；完整听看和 final acceptance 继续由既有 review/committer owner 与用户决定。
scripted Provider/renderer 测试证明控制流，不能签作品质量或原平台采用。

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

反向之地24→25→26→27组要保留门口堵桌、手机照明、人物上下铺/地面与曾亮按肩后的关系。
原文24末段和25写小龙持长杆，26却明确双手空着，没有放下长杆的过渡；此冲突必须保留并阻断，不能概括成全程空手。
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
CausalEdgeSemantics枚举值、causal_state_changes和required_carryover_dimensions；组合由production唯一owner校验。
full_continuity必须提供完整十维及所有carry项。source_analysis保留原句、计划开闭状态、继承项及gaps/conflicts；
冲突或缺证分别输出BLOCKED_SOURCE_CONFLICT/BLOCKED_SOURCE_GAPS，不因正文存在就放行。
有明确承接方法但尚未形成批准Shot状态列时为ANALYZED_PENDING_SHOT_AUTHORING，不能进入执行。
两链的原句、计划状态、参考职责与输出指针分别保存在[反向之地](canvas-sequences/fanxiang.json)与[白带子](canvas-sequences/baidaizi.json)；
文件含expected_source_snapshot_sha256，可直接作为selection重开对应源快照；源漂移拒绝。白带子后五边只继承遮挡/前冲，
明确释放世界身份；运动矢量、透光和音轨实际匹配属于media_checks，不把不同物种误当剧情冲突。
没有boundary时导出BLOCKED_MISSING_AUTHORING；完整时也只是AUTHORED_NOT_MEDIA_VERIFIED，不是READY或PASS。
`--resolution 720p`或`1080p`只在用户明确要求时使用；模型不支持480p时返回能力问题，不静默升级。

## Production Handoff And Cost Boundary

本包只是可复用的前置准备资料，不是第二套Production schema、Manifest或可付费执行计划。
将选定顺序写入既有Storyboard，逐段创作进入现有Director/Shot contracts；批准过且意图不变的Shot不重做创作。
保持原文与明确变更diff；换角、参考适配或剧情改写不能伪装成完全复刻。
跨段通过`build_sequence_video_planning_request`及`prepare_sequence_shot_for_existing_production`进入既有Planner/Router。
真实accepted source、实际末态、Registry bytes和route由这些owners重开，不以原prompt的结尾描述代替。
共享入口见下文；仍不推断创作歧义，也不提供无人值守创作/验收。

`scripts.canvas_sequence_handoff.build_canvas_sequence_planning_request`是实际可调用的只读交接入口：
传入原source/selection、target_occurrence_id、project_root、current_request、逐occurrence的当前Shot identity、
execution_evidence（source_shot采用时identity、source_generation_intent_hash、stack、anchors、lifecycle等）。
它重建准备包、拒绝有冲突/缺证的边界，核对已有Storyboard连续顺序与当前Shot修订，再调用canonical sequence adapter。
同canvas节点在timeline重复出现时仍需不同Shot身份；首单元走既有single-Shot入口。source adopted revision和当前revision分开核验。
原输出resourceId只作为快照指针保存，未读取MP4时不伪造SHA或验收。输出尺寸必须符合新准备默认480p（显式override除外）；
不会改写已批准request。这个入口不自动创建/批准Storyboard或Shot、不提交、不签媒体PASS。

下一次同链修改只重新读取受影响节点、相邻边界和引用身份；输入未变时复用封存资料，
新提交仍必须核对当前源身份与用户授权。通过当前实际输入预览审查后，沿用现有单次执行与逐镜Gate。
不默认增加Team/Claude轮次，不重复造临时上传/提交脚本；明确要求Claude时只审本次输入与差异。
工程PASS、抽帧和ASR不代替完整听看；用户觉得可采用也不抹掉已知偏差。
