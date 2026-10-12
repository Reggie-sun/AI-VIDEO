---
record_kind: session_summary
topic_id: canvas-original-multishot-preflight
learning_eligibility: ineligible
---

# Original Canvas Multi-Shot Preflight

Date: 2026-10-12

## Partial Supersession Notice — 2026-10-12

用户随后选择补齐入口并实测。[新原文多镜与时长恢复记录](2026-10-12-canvas-original-sequence-and-nominal-timing.md)
证明 staged implementation 已通过完整 Harness；新第一镜已生成、逐镜 Gate、完整听看及 canonical activation，
第二镜无调用准备已通过，随后按原文生成并取回，连续观看页可用，完整听看和 Gate 尚待完成。
下文 source capability blocker 和等待方向选择是当时事实；
Kimi HTTP403 后已按用户明确授权改用原生只读审查；第一轮发现修复后的新快照通过完整 Harness，
第二轮语义入口修复后52项 focused tests 通过，最新完整 Harness 与第三轮只读复核已完成，
特殊 literal-hash 输入差异保留为非阻塞限制；实现 `a545090` 已 push 至 `main` 并核对 remote SHA。
两镜成片与完整 spec 仍未验收。
原修剪 timebase 未证明的限制及本记录的零调用历史保持不变。

## Goal And Current Result

用户要求实际制作原画布的连续段来观看，延续 Fast 2.0、480p、保留原文与参考素材的约束。
本次已核对《机魂觉醒》的真实时间线和生成来源；结果为 `SOURCE_CAPABILITY_BLOCKED`，
没有新 Seedance submit、poll、fetch，没有生成、拼接、render 或 activation。
这不是模型质量失败、余额错误，也不是画布缺少多镜；目前没有新视频可以审片。

## Selected Source And Continuity Boundary

来源为 `runs/reusable-canvas-production-20261011-001/mecha-document.json`。
`node_v79w4jnbrv` 的视觉轨有17个片段，另一时间线 `node_m83mt9f6jb` 有12个；各有一条音轨。
第一时间线开头5个片段的生成来源是视频7一次、视频2四次，不能把四份不同修剪当成四次生成。
视频7的修剪节点 `node_2wezyggyma` 来源于 `node_dzjqb2reg0`；接着四个修剪节点来源于
`node_44chrfmntz`。选段的叙事关系为怪物悬浮后机甲开始托举，不能用视频节点编号推断顺序。
视频2保留两份图片引用和“机械人零一”主体包 `node_nen56m0q6f`；主体包含原主图与辅图。
来源里的 `sourceRange` ticks 尚无已验证 timebase，不猜测换算或声称复现原裁切。

两个历史原文单镜的人工接受仍有效于各自原片，但没有证明这个相邻段落的接点，
也没有自动进入 canonical accepted-source 状态。不能将共享素材或原文计划末态充当实际末态证明。

## Executable Evidence

证据根为 `runs/canvas-mecha-multishot-fast20-20261012-001/`：

- `source-facts.json`：原时间线前五次 occurrence、实际父节点及原引用的有限投影。
- `inspection-timeline.json`：实际 `inspect_canvas_source` 选择完整第一时间线，结果 `BLOCKED`。
- `inspection-generators.json`：显式选择两份父生成节点，仍为 `BLOCKED`，包括
  `unsupported_subject_capability` 和 `unsupported_or_unbound_selected_source`。
- `kimi-receipt.json`、`kimi-report.json`、`parent-adjudication.json`：独立只读映射与 Parent 裁决。

`scripts/canvas_sequence_packet.py::_unit_source` 不解析 subject 扩展，也要求所选视频自身有
`generationDraft`；当前入口不能把修剪节点的父 draft 冒充已经证明的历史编辑输入。
`seedance_native_prompt.py::SeedanceNativePromptBinding.compile_source` 的现有原文入口明确拒绝
v4、conditioned intent 和 typed-hash continuity。它能生成独立原文单镜，不证明可以原文多镜交接。

为核对能力边界运行 `tests/test_seedance_source_prompt.py` 与 `tests/test_canvas_sequence_handoff.py`：
24 passed。该验证发生在保留既有 dirty 工作的当前树，相关源码与测试未被本次修改；
它证明所测边界，不能冒充已发布树的完整验证或真实媒体通过。
`make harness-inspect` 已使用项目 `.venv` 与正确 `PYTHONPATH` 执行；最初系统 Python 的依赖错误为
零副作用环境问题，未改变规则或降级检查。

受管 Kimi invocation 为 `a7e0a35c-c71e-4471-bab0-a85507a8fd06`，deep/max，
qualification 为 `4f2d5dc8-4234-4665-b382-e82f1ad6cc00`；3次实际 wire requests，
零 orchestration retry，内部 retry 未知。封存源码、actual Read 与 artifact hashes 已核对。
Parent 确认主体、修剪来源和原文 continuity 的能力边界；报告从有限投影推出完整图缺引用，
以及声称显式 generator selection 总是不合法的推断，被当前完整来源与代码反证，未采用。
该映射不是 implementation review，也不拥有媒体接受或新调用授权。

## Next Scope And Completion Boundary

用户此前强调模型复刻以便验证，本次没有自行把该请求改成新一轮代码实现。
已提出明确选择：补齐所需接入口再实测，保持模型验证并换合法连续来源，或保留证据停止。
选择前不进行依赖该答案的实现或 paid 提交；不是请求再次授权已确认的模型、分辨率或凭据。
实际视频复刻仍未完成；需要先解决主体输入、来源投影和前镜 accepted-state 的可执行接缝，
然后逐镜显式 MCP Gate，最终以正常速度完整听看片段，不用单镜接受替代连续性。

## Record And Learning Evaluation

`record-ai-video-session` 保存这个稳定的 preflight 阻断，前序 readiness 记录增加范围澄清。
`distill-ai-video-learning` 为 `no_candidate`：同一来源的两种选择检查不是两份独立媒体实验，
没有模型比较或新媒体结果，不创建泛化 Learning Claim、不采用 Skill/Policy/Gate 变更。
其他 dirty/staged 工作保持不变。记录按 exact staged documentation-only Harness 验证，
receipt 为 `.agent/harness/runs/canvas-multishot-preflight-20261012-final/receipt.json`；
commit、push 与 remote-main SHA 以实际 publication proof 为准。
