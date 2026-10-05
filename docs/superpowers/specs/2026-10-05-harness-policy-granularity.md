# Harness Policy Granularity Spec

## Goal And Authority

用户要求执行 Harness policy 细化，并明确由本 session 接管 `policy.yaml`，保留已有 staged
修改，旧验证自然结束。只改 Development Governance；缩短反馈周期，使媒体修复能更快获得
相关工程回归结果，不改变观看质量、授权、预算、unknown outcome 或媒体 Gate。

## Current Evidence

新增 `typed_causal_native_expression` 类别直接选择 `full_tests`；相同两个路径同时已有
`generation_feedback` 映射，其 check 显式包含新增 causal-expression 回归。第二轮 receipt
记录前置检查约 5 秒、full suite 1800.170 秒后 timeout。完整 pytest stdout 使用静默进度，
子进程结束前 receipt 没有当前检查记录；不将这一历史失败改写为 PASS。

## Contract

- causal-expression helper/test 路径选择独立 `typed_causal_native_expression_tests` 及既有
  Planner、neutral requirement、Router、Provider、Vidu 和 final-output 边界回归；不选完整
  feedback/repair 或仓库 suite。修改 feedback owner 仍选择完整 `generation_feedback_tests`。
- `generation_feedback_tests` 仍包含该专用 test file，只有同 run 该完整 suite 实际 PASS
  才覆盖并跳过专用 check；不把局部 expression 回归反向当作整个 repair suite 的证明。
- shared Production schema/reader/writer 保留 `production_contract_tests`；Python toolchain、
  test infrastructure 与未知路径保留 `full_tests` 和原 architecture/fail-safe 语义。
- 复用现有 `covers_check_ids` 与同 run 实际 PASS 后跳过的规则。只添加明确完整包含的关系，
  不按文件名相似、历史 PASS 或不完整测试交集跳过。
- pytest argv 添加内建 slow-duration 报告。完整 suite 输出 test node ID，并采用 pytest
  内建 faulthandler stack dump 辅助定位长时间 test；stack dump 不终止测试、不改变预算。
- 每 check 执行前打印 check ID 与 timeout 并立即 flush；执行后打印 status 与 duration。
  stdout/stderr/JUnit、receipt 哈希、freshness、coverage 与 process timeout 语义保持。
- 不新增依赖、test skip、cache acceptance、跨 run 复用、并行调度或 Production mutation。

## Acceptance And Verification

新增路由回归明确证明 causal-expression 无 full suite、相关边界仍被选中、未知/基础设施
仍 full fallback；完整覆盖去重必须在本 run PASS 后才成立。真实 pytest 验证 duration 输出、
full argv 的 node-ID/stack 诊断与 check-start 日志先于 runner。运行 project-native focused
suites、policy audit、agent rules、Architecture Gate 和 exact snapshot Harness；保存实际耗时。
结果只证明离线工程，不宣称全仓库健康或媒体通过。

## Ownership And Publication

owned paths：`policy.yaml` 的细化、`scripts/agent_harness.py` 的 argv/logging glue、新增专用
Harness policy tests、本 spec/plan/research/record。已有其他 Product/source/docs/index 修改
不属于本 session，保持不变。提交不得引入对尚未提交 source/test 的悬空引用；若 producer
尚未完成，其依赖是明确 publication blocker，不夹带其 source 或未经许可终止旧验证。

## Self-Review

完整 suite 的历史成本来自真实 receipt；聚焦检查通过选择真实 test files 保护 compiler、
sequence、feedback 和 routing 行为。未知路径安全兜底及媒体/paid/recovery 不变；没有依据
降低 timeout、删除 E2E 或全局接受历史结果。parent 在实现后调查并裁决 independent review。
