# Local Unmetered Generation Limits Correction

## Authority And Goal

用户明确纠正“本地的额度应该是无限的”。该当前要求取代 COCO／诺萨旧 operator 设置的累计两次上限及未批准的 local renewal-ledger proposal。目标是严格 local/unmetered 的 ComfyUI 不设固定累计次数额度，同时继续有界执行和生成原 17 s 完整片段；不是取消 finite batch、repair policy、unknown-outcome、intent/permit 或 QA。

## Verified Boundary And Owner

`ExecutionLimits.local_total_limit` 已支持 `None`，pure decision 已表示无累计上限；真实 blocker 是 `ProductionStateCommitter._require_persisted_generation_limits` 把 prior local limits 作为永久不可扩张 quota。CodeGraph 与源码确认该检查由 `_require_submit_execution_binding` 在 side effect 前调用。sole committer 保持唯一 owner，不新增 schema、Manifest pointer、ledger、dependency、API 或 CLI。

## Contract

只有当前 selected sealed capability 同时 `execution_kind=local` 与 `billing_kind=local_unmetered`，才允许下一次 exact request 使用新的 finite batch bound 或 `local_total_limit=None`，不再因旧 local ceiling 被拒绝。所有真实 local submit intent / receipts 继续计入原 same-task counters，不能 reset 或换 task 名隐藏历史。finite batch bound 按累计 used + 本轮有限 allowance 表达；本任务当前只放行下一次请求，batch limit=3、used=2、total limit=None，active prompt wall=5400 s、elapsed=7200 s。

当前 request 显式提供非 None local total limit 时仍执行该限制；batch 达到上限仍停止。remote/metered variants 不获得本例外；所有 paid ceiling 扩张仍只经既有 paid quota-extension contract。adapter preflight / LocalVideoSubmitIntent 继续验证 strict loopback、local/unmetered、exact bytes 与 permits；不能根据 caller 标签把 remote call 变为 local。

同 Shot 的 resample/repeated-failure policy、runtime-repair cap、完整历史/最新结果、unknown outcome、QA/rubric/lineage、one-use consume/replay、activation 和最终验收保持。新 request 使用已经登记而未消费的 exact runtime repair grant，不改旧 attempt-03 binding，不 remint grant 或 permit。

## Verification And Delivery

回归先在 real project / canonical orchestrator / scripted local transport 复现旧 batch=1/total=1 后，same-task 新 finite batch=2/total=None 的 submit 被拒绝，再验证可执行一次、计数/history 保留、grant 与 permit one-use。不运行真实 Provider 的测试还需覆盖 explicit finite current limit、reset counter、pending intent reservation、paid quota、remote/metered limits 和 unknown recovery。

完成 actual changed-path policy commands、exact snapshot independent T2 implementation review 与 Parent adjudication 后，沿既有 canonical local seam 使用隔离且已 GPU 验证的 Triton runtime 生成。每个 MP4 立即调用 project-local video-analysis，逐项报告真实动作/身份/声线与完整观看/聆听边界；没有 MP4 不伪造结果。任务服务按 known terminal / empty queue 恢复，保留未知任务。无 worktree、push 或 release。

## Self Review

修复只改变 unmetered local ceiling 的永久单调限制，仍保留当前有界 batch 与所有非额度安全门。旧 schema bytes、pure decision和持久化 layout 可复用，无需新 local renewal subsystem。用户的不限累计次数不被解释成无限自动重试；原 17 s creative scope 不变。
