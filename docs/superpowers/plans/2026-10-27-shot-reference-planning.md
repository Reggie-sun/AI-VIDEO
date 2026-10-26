# Shot Reference Planning Implementation Plan

## Goal And Scope

在既有 Director → VideoPlanner → neutral requirement → Router → compiler → QA 链中增加按语义事件派生的参考规划，不新增 Registry、timeline、执行 Agent 或状态机。不调用真实 Provider。

## Architecture And Compatibility

- `GenerationIntent.reference_planning` 为可选、严格验证的导演声明，包含组合特征、镜头内部有序事件、持久参考职责和明确素材选择。缺省序列化省略，历史 sealed bytes 保持不变。
- `production/reference_planning_contracts.py` 独占声明与只读报告类型；`production/reference_planning.py` 由现有 intent 派生关键状态、风险、资产需求和自然生成范围，不解析关键词猜 Shot 边界。
- `planning/_reference_planning.py` 复用现有 asset readiness，精选执行素材并影响 Planner mode/outcome/requirement。计划图数量与上传数量分离。
- `production/reference_strategy.py` 在既有 Router 能力匹配边界检查当前 variant 和需求；复用 capability cardinality 和模式规则，不能生成第二份能力事实。QA 建议根据既有 diagnosis 与 rubric 的字段来源，不自动重试或拆镜。
- 现有参考报告展示规划与执行差异；Director 的原意、Storyboard 顺序、Registry identity、unique committer 与真实媒体 Gate 均保持原 owner。

## Milestones

1. 增加 typed facets/events/roles、语义规划及不编造秒数的关键状态报告。测试静态、对白、情绪、运镜、调度、动作、状态转换、产品、图形及多镜头结构。
2. 接入 VideoPlanner、现有 Router 与准备报告。测试选择最少必要素材、缺素材阻断、模式冲突、能力限制、精确时间不支持、旧 hash 与 canonical loader/Canvas 链。
3. 接入 QA 的来源绑定建议，保留已满足项，unknown/evidence gap 停止，连续镜头不得自动拆分。测试真实 diagnosis seam。
4. 更新 canonical matrix、Harness 映射、架构说明和工作记录。运行 focused、related 与发布前 full；已有失败须如实区分，不改 baseline 掩盖问题。

## Ownership And Verification

Parent 唯一 writer；只读 mapper 已完成 Canvas/sequence/feedback 调查。用户允许 policy/matrix 仅追加本任务条目并只提交 owned hunks。其他既有 dirty 文件不修改、不 stage。

使用标准 Production loader fixture 与真实 Planner/Router/compiler seams；单元案例只证明工程决策，不证明模型画面。候选稳定后依据 SUBAGENTS Risk Gate 决定是否需要独立 review。所有 task-owned 改动按项目规范提交、push main、核对远端 SHA；full 失败或共享源码漂移报告为限制。
