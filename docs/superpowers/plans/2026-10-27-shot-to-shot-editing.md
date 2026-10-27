# Shot-to-Shot Editing Implementation Plan

**Goal:** 在现有 Director、唯一 ResolvedTimeline 与逐接点 QA 中绑定剪辑动机、源入出点、叙事效果和连续性风险。

**Scope:** 当前能力审计、两个上游仓库研究、最小结构化决策与 QA 接入、《失帧》现存素材审计和可执行修复方案。Parent 拥有实现；只读 mapper/inventory 独立调查，research writer 仅拥有 research 文档。

**Invariants:** 不增加导演、timeline、renderer 或 Product state writer；不自动生成视频，不重试 UNKNOWN，不更改历史素材/验收，不接管其他 dirty 文件。决策不是自动语义判断、人工验收或执行许可。

**Current / Target Behavior:** 现有 cut packet 已提供 canonical 源时序，junction Gate 已要求声画与动作/状态/节奏证据；新增叙事类型、切镜原因/方法/效果、轴线视线空间、景别反应、节奏揭示、声音桥和补拍反馈。所有新 assembly 评审要求明确决策与精确源入出点，旧记录可读但缺新证据不签新 Gate PASS。

## Milestones

1. 审计已有 owners 与 current media，并研究上游 exact revisions/许可。优先复用方法，不复制执行控制面或固定切镜公式。
2. Parent 修改 `src/ai_video/production/junction_review.py`、`scripts/agent_harness_assembly.py`、`src/ai_video/canvas_review.py`。用现有测试文件先覆盖缺决策、错源入出点、声音桥未跨切点、显式失败/补拍阻断，以及 Canvas 意图成为真实最终成片 QA requirement；不改 CompositionSpec timing 算法。
3. 在 `open-video` 内加入剪辑决策参考并链接；保存 research、实现审计和《失帧》证据。原速听看不足保持 NOT_EVALUATED，抽帧不等于表演/声音验收。现存 S01–S03、S04、S05 分开核验；未拼接接点不冒充已渲染。
4. 精准测试后运行关联 Harness；检查 task-only diff、Risk Gate 与记录。按 owned paths 提交并 push/核验 main，若 source drift、既有 staged ownership 或验证阻断则如实报告，不夹带、不清理他人变更。

## Verification

精准：`tests/test_junction_review_gate.py`、`tests/test_agent_harness_assembly.py`、`tests/test_canvas_continuity.py`；关联增加 Composition/Canvas edit-first、visual quality/skill boundary。Harness 使用 task-only index snapshot；新文件映射缺失需明确处理，禁止静默全量替代。实际媒体通过 project-local video-analysis、exact frames、源SHA与现有 ResolvedTimeline 取证；完整人工 1x 声画验收继续单列。

## Self Review

用户七项目标分别对应上述能力、research、共享实现、题材区分、显式决策、成片 QA 和实片审计。无 paid submit，无第二控制面，无自动 acceptance；修复建议不自动成为已改善的成片。
