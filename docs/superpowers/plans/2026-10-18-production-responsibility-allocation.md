# Production Responsibility Allocation Implementation Plan

## Goal And Scope

实现[合同](../specs/2026-10-18-production-responsibility-allocation.md)规定的逐目标分工闭合与共享预览。当前基线 `5057f0cee4fc947e9278a53288258a386fd19863`；当前 working tree/main，保留八份 foreign dirty/index 文件，不建 development worktree。

流程 owner 为 `superpowers:writing-plans`；Parent 根据用户本轮实施授权自审，随后执行，无额外审批停点。参考资料核对已在[调研](../../research/2026-10-18-canvas-prompt-control-and-acceptance.md)完成。

## Milestone 1: Close Allocation Responsibilities

Owner：一名 native bounded worker；Parent 负责最终裁决。

文件：`production/domain_acceptance.py` 中统一纯校验，原 `_state_commit_review.py` publication、`planning/production_strategy.py`、`production_strategy_reader.py` 与 `production_strategy_materialization.py` 的 current-use seams 调用同一规则。测试 `tests/test_production_responsibility_admission.py` 及现有 allocation/planning/source-use 用例。

验收：声明 raw 的 hard IDs 始终有 component 承担；组件自身 raw 目标不因 assembly 重叠而免验，observable/proof/tolerance/measurement 保持。其他未分给 assembly 的 hard IDs 也须有 raw rubric；rubric required IDs 不能是 hint 或后期阶段；assembly 必须有既有 final-output 目标，所有已声明 hard goal 的 observable/proof 保持匹配。source-only 合法、重叠职责合法；旧 policy bytes/hash 和只读 lineage 继续可重开，不完整旧 policy 的新执行明确停止。新 publication 拒绝发生在 durable write 前，策略拒绝不开 attempt。

## Milestone 2: Expose The Same Division In Existing Previews

Owner：Parent，与 Milestone 1 文件互不交叉。

文件：新增只读 `production/production_responsibility.py` 投影既有 inventory/allocation；`canvas_preflight.py`、`scripts/canvas_production.py` 与 `production_planning.py`/`canvas_production.py` 接回既有 preflight/prepare；`video_reference_controls.py` 展示语义/自由度，`generation_feedback.py` 保持 raw/input fragments 与后期职责分离。新增 `tests/test_production_responsibility_preview.py`，复用现有 Canvas/Provider compiler fixtures。

不改变旧 API/CLI 默认 immutable decision 返回；显式 `include_control_report=True` 的制作准备报告附带只读分工信息，原 Decision/hash 不改。现有项目重开 selected QA，新项目可显式预览 candidate QA 并标明尚未批准；不实例化 Provider/runtime 或制造预算/permit。报告只呈现当前声明、证据与实际选择，不自动推断偏好、不改 prompt、不复制 timeline。

验收：三个不同场景与两个编译器显示相同通用分工；允许变化不计 required PASS；raw 内容、参考职责、editorial/final 目标和未支持修复分别可见。所有原目标保持且纯预览不写 Manifest，不调用凭据或 transport。

## Milestone 3: Verify And Publish

Parent 更新 `docs/canvas-production-harness.md` 与 matrix 的现有 owner 段，按新源码/测试路径补 Harness routing；不修改 foreign `AGENTS.md`、playbook、runtime baseline。

先 focused tests 得到正常/边界/失败证据，稳定 snapshot 再跑 applicable Harness 与 Architecture Gate。由于 publication/current-use 改动涉及持久化验收的语义缺口，按 Risk Gate 选择一名 read-only native `reviewer_xhigh`，绑定 exact commit/tree、测试与 receipt；Parent 修复 confirmed findings，遵守同任务有限轮次。

只读实际《界蚀》preflight 解释当前缺项，不运行 Provider/媒体；模型质量、连续镜、完整故事与 human 状态分别保留。稳定 checkpoint 使用既有 record owner，自动评估 distill；owned paths commit/push main，核验远端 SHA，不能在审计或单个测试后结束授权工作。

## Self Review

已逐项覆盖合同：单一 QA/Planner owner、缺项阻断、偏好/固定来源、后期结果与执行能力分离、历史兼容、无外部效果、多场景/编译器及 publication。没有新 timeline、repair engine、自动放宽 Gate 或付费许可。
