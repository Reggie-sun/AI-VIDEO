# Planning Preflight Boundary Repair

## Scope

`9482f04d` 的 `architecture_gate.toml` 中，`_sequence_source.py` 读取 Planner 的 `ARCH103` 例外已于 2026-11-05 到期。序列读回仍须重算前序 neutral seed 和最终计划的完整投影。旧例外的来由和伪造投影复现见 [Sequence Destination Route Authority](2026-10-04-sequence-route-authority.md)。本次修复只调整该功能的依赖方向和验证归属。

## Implementation

1. 将原 `VideoPlanner`、输入与结果模型、资产和参考推导、`ShotReadinessGate` 与 exact projection 校验放到 `src/ai_video/production/generation_preflight/`。商业请求的加工仍由 planning 持有，共享目录仅接收其已封存 input 并推导纯 requirement。
2. `ai_video.planning` 与 `ai_video.quality_gates` 通过原公开入口提供同一组 types 和 functions。原有 handoff、sequence authoring 及 commercial project reopen 继续在 `planning/`。Production 的两个序列读回点调用共享实现，仍分别重开 neutral seed 和 sealed final request。
3. 删除 `ARCH103` 中列出的过期例外。共享实现位于现有 `production_runtime` 规则覆盖范围。保留到期拒绝、跨层依赖拒绝、单一 projection 校验定义及 requirements、Readiness、Router 的现有行为证据。配套更新矩阵、当前 baseline 文档、结构断言和 Harness 路径路由。

## Acceptance

- replay 时保持 request、plan、projection 与 readiness 的 schema、序列化和 hashes。合法跨栈链仍可读回，封存其他 seed、伪造投影、异常 causal continuity 继续拒绝。沿原公开 API 测试。
- Architecture Gate 在当前日期下直接运行，`ARCH103` 继续阻断 Production 和共享 preflight 到上层 planning、quality 包的引用。保留历史 baseline 文件和失败回执。
- 对 staged snapshot 执行 focused、related Harness 与仓库级 Architecture Gate。复刻示例的三份字节回归随同验证。保留当前并行改动，全部本地提交，继续离线。
