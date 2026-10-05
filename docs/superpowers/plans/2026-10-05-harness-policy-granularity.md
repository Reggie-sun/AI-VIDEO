# Harness Policy Granularity Implementation Plan

## Goal And Scope

按 [spec](../specs/2026-10-05-harness-policy-granularity.md) 细化 causal-expression 的测试路由，
复用可证明完整的覆盖去重，并增加 pytest 慢测试与 Harness 进度诊断。Native Codex 是唯一
lifecycle owner；只读 Kimi 调查与 exact snapshot independent review 不拥有 acceptance。

## Contract Surfaces And Invariants

policy version 2、receipt version 2、public CLI 与 Runner 接口不变。未知路径 full fallback、
同 snapshot PASS 后覆盖跳过、artifact hashes/freshness、network/secret guards、timeout
process-group cleanup、Production/媒体/付费授权保持。旧验证自然结束，历史 receipt 不改写。

## Milestone 1: Focused Routing And Evidence

修改 `policy.yaml`，新增 `tests/test_agent_harness_policy.py` 并接入 `harness_tests` 与 category。
先用真实 policy inspect 建立 RED：causal-expression 不应 full、边界必须选中、未知/共享
与 test infrastructure 不降范围；只添加 argv 明确完整包含的 coverage 关系。保留现有 staged
Product 任务引用，记录并处理 publication dependency。

## Milestone 2: Slow-Test Diagnostics

修改 `scripts/agent_harness.py::_check_argv` 与执行日志的 bounded glue；不扩展 scheduler 或
subprocess runner。使用 pytest 内建 durations、full-suite verbose node ID 与 stack dump。
专用 tests 检查前置日志可见、argv/reopen 相同、真实 pytest duration 输出与失败状态。

## Milestone 3: Verify, Review And Publish

运行 focused Harness/policy/invariant tests、policy audit、agent rules 与 Architecture Gate；
在 nonempty exact snapshot 跑 Harness 并核验 receipt。验证之后按仓库 T3 verification
contract 执行同一 snapshot 的两次独立只读 review；parent 裁决 findings，语义修复后重验。
记录实测选集和耗时边界，评估 record/learning，仅提交 owned paths 并 push `main`；
若仍依赖 producer 的未提交 source，报告明确 blocker，不夹带 unrelated work。

## Self-Review

三个 milestone 对应 routing、diagnostics 与 completion；不包含 Provider/media、重新生成、
隐式预算扩大、test skip、dedicated development worktree 或旧验证终止。结构关系已用
CodeGraph 检查 `verify_inspection` 与 `_check_argv` 的 caller；源码与 tests 是最终事实。
