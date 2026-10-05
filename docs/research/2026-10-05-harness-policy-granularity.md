# Harness Policy Granularity Research

## Question And Boundaries

减少局部修改的 Harness 验证成本，同时保留完整受影响契约、exact snapshot 与同 run
覆盖证明。不调查 Provider 价格，不修改媒体 Gate，不因历史测试失败隐藏或跳过 E2E。

## Verified Repository Evidence

- `typed-causal-native-expression-20261005-final-2/receipt.json` 的 `full_tests` 为
  `timed_out`，`duration_ms=1800170`；前置检查合计约 5 秒。后续两轮还有 source drift /
  SIGTERM，不能归因成相同 timeout，也不能将它们视为 PASS。
- `agent_harness_policy.py::inspect_paths` 使用 categories 的 union；未知路径选 fallback。
  新 causal-expression 路径既有 generation-feedback 回归，重复添加 `full_tests` 会扩展
  至整个 repository，而不是只补充必要边界。
- `coverage_groups`、`verify_inspection` 与 `validate_execution_records` 已实现同 run
  PASS 后的 coverage skip，复用该机制。`quality_intelligence_tests` 的 literal file selectors
  完整包含 `agent_memory_tests`，无 `-k`/marker 过滤；其他有限测试组没有新的完整包含关系。
- `agent_harness_runtime.py::run_command` 使用 `communicate(timeout=...)`，结束后才交付
  captured streams；本轮只添加 START/result 日志，明确不宣称逐 test 实时流式日志。

## Prior Art And Compatibility

pytest 的 [official usage](https://docs.pytest.org/en/stable/how-to/usage.html#profiling-test-execution-duration)
支持 `--durations` 与 `--durations-min`，可以复用内建报告，不需新增 profiler。
[official failure guide](https://docs.pytest.org/en/stable/how-to/failures.html#fault-handler)
说明 `faulthandler_timeout` 可在长时间测试中打印线程 stack；它是诊断，不是终止预算。

参数写入相关大测试组的 policy argv，full suite 用 `-v` 保留 node IDs；不在 argv builder
无条件追加，因此历史 policy 的 argv 重建不变。JUnit artifact 与原 proof owner 保持。

## Independent Investigation

受管 Kimi deep read-only investigation：invocation `34d8195e-4a4e-405b-9778-d25cebeea4ef`，
三次 wire requests，process exit 0，完整 worker report。实际 Read evidence 绑定 Harness
source hashes；parent 核对其 buffered capture、coverage ordering 与 proof argv reconstruction
结论。report 不构成 implementation review 或 acceptance。

## Decision

采用独立 causal-expression test file 与现有 compiler/planning/routing/Provider/final-output
边界；feedback owner 修改仍保留完整 repair suite。共享 schema 与未知路径保留广泛检查。
优先消除选集扩大，不改变 scheduler、不添加
cache acceptance、pytest-xdist、skip 或自动重试。完整 suite 的总性能仍需其独立实测，
本轮 duration/node-ID/stack 诊断用于后续定位，不虚构已找到所有慢测试根因。

## Measured Refinement

首轮新 exact snapshot 的 `generation_feedback_tests` 为 395 PASS / 1 skip，pytest 报告
590.29 秒；最大 call 是 ceiling-6 extended local repair 的 16.52 秒。只读 native
`test_analyzer` 核对这些 local fixture 没有 `continuity_routing`，不会进入 helper 的 eligible
causal-expression 分支。因此 helper/test delta 单独路由专用 suite，feedback owner delta
继续完整修复回归；保留 real history、replay 与 one-use 保护，不优化 Product reader 或 fixture。
