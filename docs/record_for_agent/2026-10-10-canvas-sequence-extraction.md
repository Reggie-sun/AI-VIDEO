---
record_kind: architecture_implementation
topic_id: continuous-canvas-preparation
learning_eligibility: ineligible
---

# Continuous Canvas Workflow Extraction

## Scope And Evidence

用户要求把反向之地与白带子共用方法提入Harness，并明确包含整张画布的连续制作，默认480p。
本轮无Provider视频生成、无媒体改动。只读核对原始画布/正文和现有continuity owner。
反向之地沿用2026-10-09保存件：94节点、272边、39个生成节点，没有生成节点之间的直接reference边；
不将其称为本轮实时刷新。白带子从已登录画布只读获取：296节点、162边、66视频节点、1条8片段timeline。
原节点中的五段框架、六份导演合同、连续性锁定，以及前后生物遮挡/前冲连接都有直接文字证据。

## Implemented Boundary

新增`scripts/canvas_sequence_packet.py`，保留原始parts/参数/slot/node/resource、共享资产、
明确顺序、重复clip身份、timeline trim/speed/volume/mute原数据；新准备默认480p，原720p证据不改。
原rich packet对source_composers重建核对，raw draft对reference边/slot/resource核验。
逐边界复用现有BoundaryKind/ContinuityObligation/CausalEdgeSemantics/CausalStateChange，
full_continuity要求完整十维；两侧原文quote精确匹配，缺边界显式BLOCKED。
不从文字自动提取并签署实际状态，不按画布坐标/标题推断顺序，不另建生产timeline或writer。

共用制作步骤已进入[Continuous Canvas Production](../canvas-continuous-production.md)及现有playbook路由；
保留同空间连续、换场承接、单条内部一镜到底/切镜的区别。现有sequence adapter仍负责accepted source、
实际末态、QA与route，不声称本轮新增完整画布→ProductionProject自动编译或通用连续生成driver。

## Verification

Focused checks：`tests/test_canvas_sequence_packet.py`与`tests/test_canvas_reference_packet.py`共27 passed。
先记录缺模块失败，再实现；真实离线提取白带子8段/13份共享素材/7边界，反向24–27组4段/5份共享素材/3边界。
这些实际selection未新写承接状态，所以10个边界保持BLOCKED_MISSING_AUTHORING，不伪造accepted source。
证据目录：`runs/canvas-sequence-extraction-20261010-001/`，包含两份完整源快照、selection与sequence packet。
工程最终receipt：`.agent/harness/runs/canvas-sequence-extraction-20261010-003/receipt.json`；状态以该实际receipt为准。
前两次Harness在guide原有文档预算上停止，新增说明已压缩为现有行中的链接，未提高预算；失败receipt保留。

受管Kimi只读对照原prompt/原脚本：invocation 43425e2a-8cfc-4f78-b55f-06609fd7a614，
PARSED、六份实际读取、receipt已核验；它的任务封存早于用户强调整图，因此不冒充审过新增sequence实现。
Parent补查整图与现有sequence API，采用共享框架建议；音频由新raw-document入口保留身份，旧rich入口兼容不扩张。
CodeGraph确认旧build_packet的reader/测试关系，当前源码确认sequence adapter是既有唯一typed edge owner。

## Acceptance And Learning

用户此前对两条Seedance效果给出正面反馈：反向之地表情动作清楚，白带子效果可以；
这是人类观看意见，不能覆盖逐项造型/布局等已知偏差，也不把旧反击任务改为完成。
本轮没有重新审听视频，没有媒体质量结论。distill-ai-video-learning评估no_candidate：
沉淀的是用户明确要求的制作组织与确定性准备能力，不是经过受控对照证明的模型规律或token节省比例。
RAG返回stale advisory片段后直接查当前文件，未等待索引刷新。
