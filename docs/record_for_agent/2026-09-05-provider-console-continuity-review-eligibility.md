---
record_kind: recovery_incident
topic_id: provider-console-continuity-review-eligibility
learning_eligibility: ineligible
---

# Provider Console Continuity Review Eligibility Record

Date: 2026-09-05

## Root Cause

用户报告 `Human continuity review 不可用 / continuity review 投影不可用`。
本机 `127.0.0.1:5173` 的 review endpoint 实际返回
`503 / CONTINUITY_REVIEW_CONFIG_UNAVAILABLE`；服务未配置四项审核身份字段。
前端原先只检查 `continuity_role + validate`，因此还会把不适用该审核协议的
attempt 当作可审核对象。

通过 canonical Project reader 和真实 detail API 检查
`runs/drama-h3-t8-30s-preview-20260905-v72/production-project/project.yaml`：
`drama-preview-v9-attempt-05` 为 running/validate，绑定类型为
`ContinuityReferenceBinding`，包含有效 `terminal_frame`，但无 active QA policy。
该 workspace 因缺 policy 不满足人工 review 前提；binding 类型本身不构成排除条件。
截图本身未标识 workspace；上述 workspace 是本轮验证的实际复现对象。

## Repair And Ownership

`provider_console_continuity.continuity_review_eligible()` 统一投影审核请求的已知前提，
detail 新增 `continuity_review_eligible`，App 仅消费明确的 `true`。
检查 lifecycle、未 evaluation、terminal binding/target、唯一 fetch pointer 和
active QA policy；缺 policy、terminal/evaluated attempt 不触发错误表单。
review endpoint 仍独立重开 exact media、request、QA policy 和身份，不把 eligibility
视为 bytes verification、审核授权或 acceptance。缺身份配置现在给出明确提示，
不填充默认 evaluator/reviewer，不写任何 Production state。

## Verification And Evidence

- Regression RED：缺资格字段/函数导致 Python 11 项失败；Node 缺配置提示测试失败。
- Focused Python：`tests/test_provider_console.py`，46 passed。
- Node API/contract/panel：`runs-api.test.mjs`、`continuity-review-contract.test.mjs`、
  `continuity-review.test.mjs`，56 passed。并行 SSR 测试曾输出已有 HMR port 占用提示，
  所有测试结束成功；该提示不是实际页面 console error。
- Chrome DevTools MCP 的共享 profile 被其他实例占用，使用独立 headless MCP 实例。
  真实选择上述 v72 workspace 后，review requests 为零、错误框为零；视频
  `readyState=4`、duration `5.166667`，媒体请求 HTTP 206，console warning/error 为零。
- Canonical detail API 输出 `continuity_review_eligible=false`；直接访问 review endpoint
  仍以 503 返回明确身份配置提示，不伪造成功。
- 最终 exact staged snapshot 的 Harness receipt：
  `.agent/harness/runs/20260905-continuity-review-eligibility-v2/receipt.json`。
  该 receipt 的实际 checks、status 和 freshness 是最终验证依据。

## Remaining Boundaries

本轮修复 UI 误判和配置错误说明，保留符合全部前提的 reference-binding 人工审核路径，
没有配置 evaluator/reviewer，也没有执行人工 review、Provider、媒体生成或 activation。
本地代码 checkpoint；未 push/release。项目 RAG 返回 tagged stale advisory fragments，
检索工具自动排队刷新，未等待刷新或主动重建 index；根因来自本轮代码和运行时。

`distill-ai-video-learning`：`no_candidate`。这是单个 deterministic regression，
不具备跨独立媒体实验的 Learning Claim admission evidence。
