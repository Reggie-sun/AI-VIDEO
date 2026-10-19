# Character Performance Control Implementation Plan

## Goal And Authorized Scope

完善现有 `PerformanceIntent`，让 Agent 制作有人物的镜头时必须明确填写逐人物表演参数，实际输入与既有验收条目能够核对。用户已授权原生 subagent 实施，并明确要求制作时必填；Parent 在现有 owners 内确定合同与分工，不新增执行链或付费媒体调用。

## Contract And Compatibility

- 唯一意图仍归 `GenerationIntent.performance_intent`。新增 `character_directions`，绑定当前 Shot 的 exact Character IDs；native 文本只使用作者提供的可见身份，不泄漏内部 IDs。
- 每个人物声明 `principal/supporting/background` 与 `visible/offscreen`。可见人物必须有明确阶段；不在画面者必须给出原因，不能自动省略。阶段为 `opening/response/settle` 的有序子集，或单独的 `throughout`，表达相对表演进程，不建立第二时间线。
- 每阶段明确 trigger、emotion、intensity、facial_expression、gaze_target、breathing、body_behavior。自然中性、静止、机械角色及镜外声音都必须按当前镜头说明，不强迫所有人做同一动作，不从人物Bible自动编造表演。
- 新鲜生成准备与新 execution binding creation 检查完整人物覆盖和 selected QA 的 `acceptance/raw_generation`、analyzer/human 条目映射；字段缺失不能靠旧六字段、默认值或 diagnostic/technical 条目满足。历史 reader、hash、replay 与已消费授权不变。
- rich remote 与 local H3 按既有 grammar 机械表达新字段。preserved-source 路线仅在全部 coarse 字段及完整确定性表演段落已经由 Agent 写入并封存到原文时承认表达；编译器不擅自增写源文，不静默丢参数。unsupported 保持原 typed error 路径。
- 无新字段时，旧序列化、prompt 和 expressed paths 保持。新参数进入既有 requirement/request hash；输入覆盖不证明模型服从或成片自然。
- preflight/reference-control 展示人物覆盖、输入表达、验收映射和缺项；Agent 制作操作写回既有 workflow owner。原 S01/全部要求、failed state、S02 POST0及消费历史不变。

## Ownership And Milestones

### 1. Typed Direction And Exact Native Expression

Owner：native `bounded_worker` `/root/performance_core_impl`。唯一写入 `production/performance_direction.py`、`video_requirement.py` 的 PerformanceIntent 部分、`_remote_video_native_prompt.py`、`_h3_prompt.py`、`seedance_source_expression.py` 和 `tests/test_performance_direction.py`。

验收：结构及人物绑定、阶段顺序和 offscreen 失败路径；old bytes/hash；rich 编译包含作者表演；preserved-source 缺原文表达拒绝。无外部效果。

最终 owner 收敛：完整 `PerformanceIntent` 类型与新增逐人物类型同归 `performance_direction.py`，
`video_requirement.py` 保留原 public import。避免扩张已有大模型文件；历史 JSON、hash 与旧 prompt 的兼容通过固定 golden 验证。

### 2. Mandatory Authoring And Acceptance Integration

Owner：Parent。新增小型 preparation guard，接入现有 `GenerationFeedbackOrchestrator.prepare` 与 `GenerationDecisionExecutionBinding.create` 的 fresh creation 边界；不修改 historical validation。现有 Canvas preflight 和 reference-control 展示同一 sealed 数据与缺项。测试覆盖公共 author→standard reader→prepare seam、多场景、缺少人物/参数/验收、未表达与成功编译；只迁移受影响的共享 fixtures，不能放宽新规则来保持旧 fixture。

### 3. Verification And Publication

Owner：Parent。先 focused tests，稳定后 exact owned snapshot 的适用 Harness 和 Architecture Gate；按 `/home/reggie/.codex/SUBAGENTS.md` 判断一次 Risk Gate，必要时仅一名原生 read-only reviewer，有限复审不重置历史。更新既有 workflow/matrix、主记录，评估 record/learning。只提交本任务路径，push main 并核验远端 SHA；保护全部 foreign dirty/index。

## Verification And Evidence Boundary

多场景使用不同人物、动作、空间的离线 fixture，证明参数必填、身份绑定、源文保留、输入表达、验收联接和失败无 Provider 调用，不证明模型质量。实际表情、动态自然度和 human 体验仍需后续有界且当前有效的媒体授权与 exact 成片验收。本任务不生成/修剪媒体，不读凭据，不解锁 S01 STOP。

## Parent Self-review

用户目标已覆盖参数必填、逐人物/阶段、实际输入、既有验收及跨项目复用；兼容边界与 source 保留分别明确。计划无独立质量状态库、第二 renderer/timeline 或自动表演合成。实现如发现必需 seam 超出分工，先由 Parent 调整 ownership 并保留同一授权范围。
