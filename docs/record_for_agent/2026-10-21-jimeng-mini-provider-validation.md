---
record_kind: recovery_incident
topic_id: jimeng-mini-production-provider-validation
learning_eligibility: ineligible
---

# Jimeng Mini Production Provider Validation

Date: 2026-10-21

## Outcome

用户批准 Seedance 2.0 Mini、720p、16:9、5 秒、复用现有参考图，最多一次真实生成、30 积分上限。正式 Provider 实际发出一次生成请求；即梦创建任务后返回 `status=1001`、`error_code=20010`，提示“生成失败，本次不消耗积分”。没有新 MP4，不能宣称 Mini 成功出片或 Shot QA 通过，不再次生成。

本次使用新画布 **AI-VIDEO · Seedance 2.0 Mini · Provider 验证 · 2026-10-21**，project `753f3322-7bc2-492f-95b3-a75bc64d3b84`，node `node_fhswnmh90n`；没有继续向《零号档案》的历史画布提交生成。参考图 SHA-256 为 `66f13af336408a826dd17b7c8df68048592ca23bbf99dca312539dd8f2674b62`，2,583,232 bytes、1672×941。样例仅验证固定机位、轻微活动的技术执行，不冒充原剧本验收。

## Changes And Owners

- `jimeng_contracts.py` / `jimeng.py`：显式 Mini profile、capability、compiler、原生参数与素材上限；旧 2.5 profile 序列化和 hash 保持兼容，不隐式换模型。
- `jimeng_browser.cjs`：只有视频参考才传入其计费与时长 context。原先纯图片调用传入 `inputVideoDurationMs=0`，被正常网页 owner 在商业执行、ID 分配和生成 HTTP 之前拒绝；只读运行原生 `68591.jR` 已复现该异常。
- `jimeng_browser.py`：读取最终 accepted ACK 后先关闭 stdin，再等待子进程退出。原 worker 的 readline 会等待 EOF，旧宿主却在等待 worker 退出，造成真实提交确认后超时；新增 subprocess 协议回归保留异常退出时的 UNKNOWN。
- `jimeng.py` / `paid_provider.py`：已校验身份、参数 hash 和数字 task ID 的 `1001` 资源可作为“提交已被接管、任务随后失败”的恢复证据；正常状态查询映射为现有 `VideoTaskState.FAILED`。不将未知状态视为 FAILED，不将失败任务视为免费或可重试授权。
- `_state_commit_jimeng.py` 沿用同一恢复 owner 支持两个显式模型。Paid、Manifest、Registry、素材字节验证与 QA owner 未复制。

## Paid Recovery And Current State

第一次正式调用在发送生成请求前确定失败，但旧 transport 统一封存 UNKNOWN。对 exact 原生校验器的无网络复现、旧 worker 源码、无 dispatch/resource 以及服务端空结果草稿取证后，一名 native reviewer 确认其满足既有 `verified_pre_transport_failure` 边界及原任务 recovery 授权。唯一 committer 追加 no-effect reconciliation，保留旧 UNKNOWN 回执，释放该预留为 0 成本，并登记 `not_submitted` evidence。

历史提交意图计数没有清零。既有 quota owner 将内部 intent ceiling 从 1 增至 2，保留 used=1、原 task、predecessor、old/new bounds 和 30 积分总上限，以容纳唯一替代意图；这不增加实际生成请求授权。替代 attempt `mini-reconciled-one-actual-submit` 发出本次唯一生成请求。之后没有再次 submit、重铸原 permit、充值或购买。

真实任务身份：

| Field | Value |
| --- | --- |
| resource_id | `2850a248-63fd-4847-8cb3-263d9259b677` |
| submit_id | `b33f42f7-bd93-4a5b-b48c-108704aacce6` |
| task_id | `23694928965388` |
| request fingerprint | `2bcdbf39ec783086dcb83deed8100e74e30dcc6074a6be3673440eb2004ab72f` |

宿主超时后，新独立进程经 `recover_jimeng_unknown_once` 只读找回该任务，核对身份及原生参数 hash，并由 committer 协调 accepted 回执。再经 `refresh_once` 将 Manifest16 的 attempt 记为 `failed`；Paid phase 为 `accepted`。原生费用提示为不消耗积分，查询前后显示余额均为 96383；资源的 `credits_amount=30` 是报价信息，不能当作实际扣费。尚无独立结算字段证明，实际成本仍为 null，保留 30 积分预留，不凭提示自动结算或释放。

## Canvas Evidence

服务端 draft2/head2 已包含本次 node/resource ID。本地完整快照已通过 Provider 和 committer 保存至有效项目根 `.codex/tmp/jimeng-mini-validation/project-ready/` 下：

`artifacts/provider-canvas/jimeng/50af0b9935d90d2919b0a2be044fcf40e4bda098aaada18eab5f4aa006f8ddcb.json`

其原始 `draft_json` SHA-256 为 `19011211368c702d457c626d51f52e3fc973346df0e32284f7e0e519f6d2968d`。标准项目 reader 重开成功，accepted 回执锚定 dispatch 与快照；任务失败没有丢失画布。画布节点的编辑器 `generationDraft` 仍保留原默认设置；实际 Mini 请求以资源 `video.gen`、封存 request/dispatch 及其 hash 为准，不能将编辑器默认值冒称为实际生成参数。

## Verification

- `tests/test_production_jimeng.py`：最终 56 PASS / 61.46 秒，含两个模型的正常/UNKNOWN/失败任务、strict reader、素材及画布替换拒绝、预算和 permit，以及真实 subprocess ACK/EOF/异常退出协议。新增缺陷回归均先复现失败。JUnit：`.codex/tmp/jimeng-mini-validation/pytest-jimeng.xml`。
- `node --check src/ai_video/production/jimeng_browser.cjs` 与 task diff whitespace 检查通过。
- 实际平台证据：一次生成请求、失败状态、精确资源找回、完整画布本地保存和服务端草稿确认。综合本地 receipt：`.codex/tmp/jimeng-mini-validation/validation-receipt.json`。该 receipt 和运行项目位于忽略目录，不随 Git 发布。
- 独立审查 round1 检查初始 Mini 接线；round2 检查无视频 context 修复及 no-effect 证据；最终 round3 的候选 tree 为 `6f5ff981996c4c903ea95285ddd0d91adf9d2262`，检查失败状态恢复、预算保留和子进程 EOF 协议，finding set 为空。Parent 核对真实恢复与上述回归；文档由 Parent 自审，不冒称 reviewer 已审文档。
- 本次 exact staged Harness 的 receipt 位置为 `.agent/harness/runs/jimeng-mini-20261021/receipt.json`，选测、结果和快照证明以该 receipt 为准；56 项专项 PASS 不能替代整组 Harness 结果。此前 P0 的全仓已知失败仍见原记录。

## Remaining Boundaries

失败原因尚不能由 `20010` 推断，未绕过平台权限、计费或审核。没有新 MP4，因此未调用逐 Shot 媒体 Gate，状态为 `NOT_EVALUATED`；旧三模态成功研究任务不能替代本次 Mini 成功证据。浏览器整体重启后的活动任务恢复、登录失效恢复，以及 Mini 的其他素材组合仍未实测。纯 HTTP 提交和服务端硬积分上限也未证明。

本次真实验证使失败路径、UNKNOWN 接管及画布保存得到运行证据，但 Mini 成功生成链路与无条件 Production qualification 未达到。自动 learning evaluation 为 `no_candidate`：这是同一有界技术验证及其恢复，不升级为跨实验质量规则，不修改 Skill/Policy/Gate。
