---
record_kind: architecture_implementation
topic_id: character-performance-control
learning_eligibility: ineligible
---

# Character Performance Control Record

Date: 2026-10-20

## Purpose And Current Status

用户要求由原生 subagent 完善通用人物表演模块，并明确要求 Agent 在制作时写入参数。
共享实现已完成并发布到 `main`：`0f2d09d218b6363e91cd516c286e698ff2958a89`，实际 remote SHA 匹配。
范围与 Parent self-review 见[实施计划](../superpowers/plans/2026-10-19-character-performance-control.md)。
具体作品仅作为验证案例；本轮没有生成图片、视频、音频或调用付费理解，不改变原 S01 的 STOP。

## Authored Contract And Existing Owners

- Agent 准备新生成人物镜头时，必须明确填写
  `generation.generation_intent.performance_intent.character_directions`，覆盖 Shot 的全部 canonical Character IDs。
  主角、配角、背景人物各有 `screen_identity`、`role`、`visibility`；镜外人物必须说明原因。
- 可见人物按 `opening/response/settle` 的有序子集，或单独的 `throughout`，填写 trigger、emotion、
  intensity、facial_expression、gaze_target、breathing、body_behavior。机械、遮挡和静止状态按真实可观察部位说明。
  相对表演阶段不创建第二 timeline；frame/sample/trim/timing 仍归 `ResolvedTimeline`。
- `PerformanceIntent` 和新增类型归 `production/performance_direction.py`；原 `video_requirement` public import 保留。
  旧六字段及无新方向时的 JSON/hash/prompt shape 保持；历史 reader/replay 不要求补写。
- fresh `GenerationFeedbackOrchestrator.prepare` 与新 execution binding creation 检查参数及 selected raw QA。
  必须有 required `acceptance/raw_generation` analyzer/human 条目覆盖表演；technical、diagnostic、later-stage
  或仅手/视线覆盖不足。按组件生成时，映射必须进入所选组件的 generation acceptance。
- rich remote 与 local H3 沿既有 compiler 表达同一表演方向。preserved-source 路线要求 Agent 先把完整确定性
  表演段落及 coarse 六字段写入封存作者原文，compiler 只核对；缺表达即拒绝。
  表演文本仍受 exact model/mode 提示词长度限制，作者精炼表达，不能静默删角色或目标。
- `preflight.performance_control` 与 prepared reference-control 显示人物、缺项、native 段落、字面表达和验收映射。
  `LEXICALLY_EXPRESSED` / `DECLARED` 只证明输入及映射；机制为 `MODEL_PROMPT_GUIDANCE`，实际质量保持 `NOT_EVALUATED`。

Agent 操作与限制已写入既有[工作流](../canvas-production-harness.md#character-performance-authoring)，
owner 写回[contract matrix](../agent-primary-contract-matrix.md)。没有新状态库、writer、renderer、Provider 或依赖。

## Verification And Publication

完整源码证明绑定 `51cff9f47dbf350eeb703e828720d2cc69b527cf..0f2d09d218b6363e91cd516c286e698ff2958a89`：

`.agent/harness/runs/character-performance-control-20261020-r4/receipt.json`

21 checks PASS；另 2 checks 由同轮通过检查覆盖。发布前实际核验
`integrity/artifact_integrity/fresh/complete_completion_proof/coverage_closed_same_run=true`。
Architecture Gate 为 0 error、0 warning。关键组包括 generation feedback 589 PASS/1 skip、Planner 201 PASS、
Provider 982 PASS、Vidu 204 PASS、no-regression 63 PASS、voice 47 PASS；各组有共享用例，不合计成独立质量样本。
Provider suite 的 23 个 Pydantic warnings 来自合成 legacy/tamper fixture，不是实际 Provider 或媒体观察。

测试通过标准 author → reader → prepare/selected compiler 路径，覆盖不同人物、动作、空间的 Seedance/H3 Max
离线案例、多人物/镜外/阶段/绑定失败、缺参数/缺 raw QA/源文未表达、旧 bytes/hash、恢复与拒绝路径。
新增用例的 transport/credential 调用在离线编译时禁止。Vidu 多主体换人拒绝、旧模型长度限制、原生声音及一次性提交断言保留。

R1 因旧大文件增加 LOC warning 中断，随后将完整 PerformanceIntent 收敛到独立 owner；R2 有 65 个旧夹具
缺少新参数/验收及预期 hash 的失败；R3 有 5 个新目标夹具 QA 缺项和 1 个旧 H3 长度失败。
历史 receipt 保留，只有 R4 是最终完整源码证明。其后仅记录文档另做 scoped 验证，不重跑源码组。
源码、测试和工作流通过 `b886f0b`、`8c2c68c`、`ec46c3a`、`0f2d09d` 四次 owned commit 发布。

原生 `bounded_worker` 完成类型/编译与分组夹具实施，`test_analyzer` 做失败归因，Parent 负责共享接入、
最终 diff、Harness、发布与裁决；worker 参与不计作独立 review。
最终候选 `0f2d09d` 的 Risk Gate 为 `NATIVE_REVIEW_NOT_REQUIRED`：无新 durable writer、授权扩张或具体关键损坏路径；
完整验证已覆盖 fresh 准入、兼容、拒绝、恢复与效果计数，未发现能由独立静态审查补足的重大运行语义缺口。
模型自然度未知仍须实际媒体观察，不能由 review 替代。

## Production And Quality Boundary

原工程 Manifest hash 仍为 `06b50a94afcbc6d130b24db609dde4513172db8b83447dd0d6392ee04c3bd80a`；
本轮没有修改《界蚀》作者输入、QA、要求、消费、失败或 accepted state，没有新媒体 POST，S02 POST0。
旧 S01 STOP、实际交接状态缺失与 75a 局部修补人工观感 PENDING 保持。
本模块不追认旧视频表演通过，也不证明已去掉“僵尸感”。

`next_empirical_question`：当前选定 model/mode 能否在保留原叙事与动作的同时落实逐人物表演。
`cheapest_valid_experiment`：先完成可审阅 exact 作者输入/模式/参考与 QA，获得新的有限授权后，仅 1 条代表性短镜头、
最多 1 次 submit、零重抽，结合正常速度完整听看逐项裁决。单例只能证明该候选，不能证明跨项目模型质量。
`blocking_prerequisite`：新的当前有效有限调用单元及 exact preview/permit；旧已消费单元不能复用。
这是后续验证边界，不是本记录授予调用许可或已封存可执行请求。

## Record And Learning Evaluation

`record-ai-video-session` 建立本主记录，并在原 S01 与 cleanup 记录添加直接 supersession notice。
自动 `distill-ai-video-learning=no_candidate`：本轮为确定性实现、合成 fixture 与输入表达验证，没有新的独立真实媒体
尝试或受控模型对照，不创建 Learning Claim、不采纳 Skill/Policy/Gate。此前同一 raw 链的反馈仍不增加独立实验数量。
检索保持 advisory；没有重建 RAG index。
