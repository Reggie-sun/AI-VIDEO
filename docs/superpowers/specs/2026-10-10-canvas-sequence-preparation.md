# Canvas Sequence Preparation

## Goal

将《反向之地》和《白带子》整张画布共用的连续制作方法纳入现有 Harness，减少每次重读和单节点临时拼装。
本轮无媒体生成，默认未来准备分辨率480p；旧输入、生成结果及验收事实不变。

## Evidence And Scope

反向之地保存件有39个生成节点，以原文的上一组状态、共享角色/宿舍/视频参考维持关系。
白带子当前完整图有296节点，66个视频节点，并有8片段原时间线；另有素材锁定、动作结果、承接方式的母版文本。
连续性不能简化成生成节点连线：reference边只证明引用，timeline只证明编排，正文只证明创作意图。
采用现有源码pattern，不需要外部方案研究或A/B；仅新增离线准备工具，不扩通用执行架构。

## Ownership And Contract

`scripts/canvas_sequence_packet.py`是development-only准备工具，接受现有canvas packet或原始canvas document，
按明确节点顺序或唯一选定timeline导出连续准备包。保留原文/parts、parameters、引用slot/node/resource及原trim/speed/audio设置；
共享素材去重，出现次序不去重。既有`canvas_reference_packet.py`的旧CLI兼容且不迁移历史文件。
相邻边界显式填写已有`BoundaryKind`、`ContinuityObligation`、`CausalEdgeSemantics`和`CausalStateChange`，
引用两侧正文原句作为authoring证据；缺项保持BLOCKED，不推断生产状态或自动降为独立镜。
默认480p只用于新generation_defaults，不改observed_parameters，不自动选Provider或升分辨率。

Storyboard、accepted source、Manifest、Registry、ResolvedTimeline仍归既有owners；准备包无执行授权，
不将画布timeline另建为生产timeline，不把原文计划末态当实际视频末态。
后续生产仍必须调用`planning/sequence_continuity.py::build_sequence_video_planning_request`，
由该owner重开真实accepted source、QA和route。新工具不读凭据、不上传、不生成、不activation。

## Acceptance And Verification

验证两种输入结构、多片段顺序、同节点重复出现、引用身份、缺失/错序/越界拒绝、source quote绑定、
缺边界显式阻断、480p默认与显式override、输入不变及CLI独占创建。
用两套真实本地捕获件进行离线提取；不将成功提取称为整片连续性验证。
Focused pytest与staged Harness必须通过；Parent review后按risk gate判断。Self-review：范围明确、owner不变，可实施。
