# Vidu Reaffirmed Profile Resample Implementation Plan

**Goal:** 让纯时间续期后的 Vidu profile 与一次有界 seed resample 经 canonical feedback/decision/compiler seam 合法且可审计地执行。

**Scope:** typed profile proof、反馈输入、决策 delta admission、历史重采样计数、测试与对应 canonical 文档。

**Contract Surfaces:** `DecisionInputs` 新增兼容的可选 proof；既有 `Intervention`、compiled request、paid permit 与 Manifest 格式不改。Proof 无值时旧序列化/hash 不变。

**Invariants:** exact old/new pointer、非时间字段相等、最多一小时新窗口；仅 Vidu；`max_resamples` 跨续期计数；unknown outcome fail closed；不改变任何外部执行 gate。

**Spec / ADR:** [Vidu Reaffirmed Profile Resample Spec](../specs/2026-09-30-vidu-reaffirmed-profile-resample.md)

## Major Milestones

### Milestone 1: Typed proof and admission

**Files:** `src/ai_video/production/vidu_profile.py`、`src/ai_video/production/generation_decision.py`、`tests/test_production_generation_decision.py`。

**Contract:** `ViduProfileReaffirmation` 验证完整 profile 非时间相等和新窗口；`DecisionInputs` 只在 baseline、候选与 proof 的 computed pointers 精确相符时接纳；resample 允许声明实际的 `provider_profile` 加 `seed`，历史已提交次数按同一策略累计。

**Verification:** proof 正反例、历史 hash、未知结果与旧计数测试。

### Milestone 2: Common feedback producer

**Files:** `src/ai_video/production/generation_feedback.py`、`src/ai_video/production_planning.py`、`tests/test_generation_feedback.py`、`tests/test_production_planning_generation.py`。

**Contract:** 标准 orchestrator 从显式 proof 产生两变量 resample；应用层 `prepare_generation()` 透传 proof；canonical baseline 到达 proof 当前 pointer 后复用 orchestrator 不再注入过期 proof；compiler 仍拒绝任何额外 native request delta；无 proof 路径不变。

**Verification:** 原反馈集成用例及续期正反例。

### Milestone 3: Canonical documentation and live checkpoint

**Files:** `docs/agent-primary-contract-matrix.md`、`docs/v0.2-runtime-baseline.md`、`.agent/harness/policy.yaml`（仅新路径确需路由时）。

**Contract:** 文档记录唯一 owner、兼容边界和实际验证；完成 changed-path checks 和 T3 独立审查后，重新封存 Shot 1 repair exact preview、paid gates，并只调用一次。Exact MP4 到位后先执行本地 video-analysis 与 required findings，失败时停止下一 Shot。

**Verification:** focused pytest、policy receipt、相同 snapshot 的 review evidence；live media 与质量单独报告。

## Self-Review

三个里程碑覆盖 spec 的 typed binding、旧 hash 兼容、有限计数、standard producer、验证及 live stop gate；没有未定义接口、额外 Provider 或自动质量放行。实现先由测试确认旧失败，再运行 targeted suite 与 policy checks。
