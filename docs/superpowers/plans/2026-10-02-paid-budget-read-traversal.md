# Paid Budget Read Traversal Repair Plan

**Goal / Scope:** 关闭Source3fd上实测的同一budget DAG反复展开，恢复COCO/Nosha canonical反馈和下一有限真实实验。Parent单writer，current main/no worktree；只修改reader、focused新tests、matrix/baseline/spec/plan/record及新focused test的既有policy route，保留`.codex/config.toml`。绑定[spec](../specs/2026-10-02-paid-budget-read-traversal.md)，不扩大media Provider、素材或QA。

## Major Milestones

### 1. Reproduce Without Production Effects

**Files:** 新`tests/test_paid_budget_read_traversal.py`复用`test_production_paid_budget_extension._ledger/_entry`与`test_production_paid_submit_quota._pending`的标准committer/loader fixtures；profiling/mapping原数据保持在run。

**Contract / Verification:** Setup后计数一次canonical预算/Manifest读取的历史验证，mixed ceiling/quota或多ceiling shared-prefix下应出现重复，新增bounded-node断言在旧Source RED。新测试同时约束跨call/currentpointer/历史base或binding/derived字节漂移、同遍历漂移、cycle拒绝，不通过mock绕过真实历史创建/读取。所有effects限pytest tmp_path/fake transport，无实际project/credential/Provider mutation。

### 2. Deduplicate Only A Complete Read Traversal

**Files:** `src/ai_video/production/_paid_provider_project_reader.py`；`docs/agent-primary-contract-matrix.md`的paid evidence owner说明与`docs/v0.2-runtime-baseline.md`实际证据边界。

**Contract:** 私有读取上下文保存active ancestry与completed budget identities；每次public budget/content-hash读取新建，Manifest paid verifier内部只分享本次root上下文。每个入口访问依旧先做canonical containment/nofollow/raw-byte pointer验证，完成全部两类extension验证后才能标completed；失败不标记。派生snapshot与base递归走原root scope，保留所有prefix/reservation/binding/Gate checks。无跨call或global缓存、无public可注入scope、无registry/lifecycle/schema变更。

**Verification:** 新tests GREEN，再运行paid/quota/budget/no-effect/production-reader最接近测试；检查拒绝typed error和state bytes不变。按实际staged paths运行policy checks、精确snapshot/source hashes、canonical Harness=null。AOCI在最终稳定时只评一次maintenance，原治理debt不冒充已对齐；不得修改无关正式索引内容。

### 3. Review Exact Source Then Resume Media Work

**Contract / Verification:** 新Source/spec/plan/tests/真实verification同immutable target双独立read-only审查，确认无验证缺口/隐藏历史/跨call stale replay，Parent裁决所有findings。记录原Kimi故障、native profiles/target及有限review轮次；旧Source review不覆盖新bytes。稳定checkpoint只commit owned paths，不push/release。

**Execution:** 旧technical优先自然结束。满足spec的known zero-feedback-write条件时才能显式停止owned旧读取，保存Gate未seal与durable bytes不变证据，然后fresh新Source标准loader重开同一fetch和QA。新loader测实际耗时/完整通过及输入恒等；若失败先修reader，不重复Provider。随后technical checkpoint→analyzer→真实mixed FAIL/NE canonical abandon；准备并执行[glancing contact单次修复](2026-10-02-coco-nosha-glancing-contact-repair.md)，每Shot Gate、其余Shot/唯一原WAV/HyperFrames成片继续，不在工程commit处停止。

## Self-Review

三里程碑覆盖可信RED、唯一owner修复、GREEN/真实policy/适用review及受限恢复到媒体。所有memo使用前字节和identity仍检查，跨call完全fresh，unknown结果不重复；可归因性能修复不改变验收阈值。标准fixture验证行为，partial cProfile不当loader PASS；暂无新Source或真实速度改善证据，完成后按实际记录。
