---
record_kind: session_summary
topic_id: jieshi-s01-first-last-repair
learning_eligibility: ineligible
---

# S01 Composition Repair Capability Boundary

Date: 2026-09-06

## Current Evidence

用户在attempt09失败后要求继续。本次没有新增Provider提交或生成媒体；只检查替代修复路径。07和08经canonical strict reader复核仍为validate，exact MP4 SHA及bytes保持：

- 07：`88d3a8ed59550c706e176da88e1d7ef89c02a1e60a5f6e1546b112507d0cd93e`，3,350,152 bytes；历史视觉约2秒到位，但广播结束晚。
- 08：`cc522e481994be961e585a95b618887a4f06b192fa9ae85b1c359e87474c194e`，3,232,566 bytes；历史ASR广播约2.14秒结束，动作晚到位。

两者都不是accepted S01或已激活素材。组合可用部分只能产生新的待验收目标，不能改变旧Gate结论。

## Confirmed Runtime Blocker

Native code_mapper只读检查composition/audio/visual_media/captions及相邻测试。Parent直接复核关键源码：

- `src/ai_video/production/visual_media.py::resolved_video_trim_duration`只有裁切，要求源帧覆盖Shot区间；没有速度重映射入口。
- `src/ai_video/production/visual_media.py::render_visual_element`及`_hyperframes_source.py`将源视频静音，独立mixed_audio拥有最终声音。
- `src/ai_video/production/audio.py::AudioImportRequest`只接受WAV输入，并显式拒绝`AssetSourceKind.GENERATED`，不能把Provider原生音频伪装为普通导入音频。
- 没有现成canonical generated-MP4 embedded-audio extraction/registration入口。

因此“07原前3秒视觉＋08原生广播＋既有字幕”仍为`REQUIRES_RUNTIME_CAPABILITY`。视觉注册本身也必须经过既有generated-video owner，不能仅凭fetch把07变成active或accepted；本次未尝试任何activation。

## Concrete Proposed Scope — Not Authorized Or Implemented

最小后续范围是补齐生成视频原生音轨的派生入口，不建立新音频系统或时间轴：

1. 新的cohesive generated-video-audio模块读取exact fetched MP4，严格绑定其SHA、原Provider request/task、提取工具及派生PCM WAV hash；缺失/身份不符fail closed。
2. 派生音频沿用既有P4 metadata和`ProductionStateCommitter`登记，保留generated provenance。不得放宽`AudioImportRequest`来掩盖来源，不引入新writer。
3. 在既有素材生命周期允许的条件下，构建新的repair composition：07视觉前三秒、08广播音轨、既有narrative caption；`ResolvedTimeline`与HyperFrames仍是唯一时间轴/renderer。
4. 最小验证覆盖exact-byte provenance、源变化拒绝、重复执行不重复副作用、音轨sample映射和新输出Gate。是否允许未接受源进入repair composition必须按现有owner验证，不能自行降低Gate。

这不是已完成设计或实现。当前用户明确限定沿用workflow、不开架构改造；`AGENTS.md::Decision Gates`要求新runtime slice先确认，因此停在此范围决定，不执行direct mux或另一次付费重抽。

## Record And Learning

使用retrieve-ai-video-memory的experience新query发现旧native-audio记录，返回stale advisory并排队后台刷新；未重试或主动重建。当前blocker来自源码，非旧记录推断。record-ai-video-session评估稳定blocker并记录；distill-ai-video-learning结果`no_candidate`：本轮是已存在capability缺口的当前确认，无新媒体实验或新的可采纳行为结论。

只读source/strict loader/SHA和文档diff检查；未运行测试、Provider、media或网络研究。保留全部unrelated staged work，未push。
