---
record_kind: architecture_implementation
topic_id: jimeng-seedance-25-production-provider-p0
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Jimeng Provider P0 Engineering Record

Date: 2026-10-21

## Follow-up Runtime Boundary — 2026-10-21

下文“新 Provider 真实提交未实证”已由 [Mini 正式 Provider 验证](2026-10-21-jimeng-mini-provider-validation.md)部分取代：独立新画布中真实提交一次 Mini 任务，服务端生成失败；任务已由独立进程恢复并记为 FAILED，完整画布快照已保存。新增修复覆盖纯图片 commercial context、worker EOF 与失败任务恢复。没有新 MP4 或 Mini 成功出片证明，原全仓 Harness 与质量边界继续保留。

## Current Runtime Truth

即梦 Seedance 2.5 已作为可选 `JimengVideoProvider` 接入既有 `VideoGenerationService`、Paid Provider Gate、`ProductionStateCommitter`、Manifest 与标准项目 reader。`jimeng.py` 负责生成服务技术执行，`jimeng_browser.py` / `jimeng_browser.cjs` 隔离已登录浏览器内的原生提交，未建立第二套任务状态、付费授权、Registry 或 Shot QA。部署时仍须显式注入账号 profile、浏览器 transport、Registry 字节 resolver 和当前项目 committer；不存在隐式 Provider 切换。

每次付费提交前，既有 Paid Owner 先持久封存预算预留、一次性 permit 与 `SUBMIT_INTENT`，Jimeng dispatch 再封存账号/project、submit/resource 身份、原生参数 hash 和有序素材关系。图片、音频、视频素材按精确 Registry 字节核验并上传。提交经网页 `generationRuntime.actions.submitVideo`；本地与浏览器两处 fence 限制一次性请求，原生权限及 quote 先检查，但 quote 字段不被视为服务端积分硬上限。

提交后，Provider 读回服务端已保存的完整画布草稿，要求目标 node 绑定本次 `resource_id`，将草稿、版本、hash 保存为项目内不可变 `JimengCanvasSnapshot`。正常 accepted 回执锚定 dispatch 与快照。若响应丢失、草稿无法确认或进程退出，既有 Paid attempt 保持 UNKNOWN，预算预留不重置；标准 `recover()` 与 Jimeng 专用入口均封存当时已有证据，仅允许按封存的 resource 查询恢复，不签发新 permit、不重新付费提交。无 dispatch 时保持 UNKNOWN。

标准项目 reader 重开 accepted/UNKNOWN 证据时，核对回执、dispatch、画布快照、资源身份和有序素材 tuple 与原 `ResolvedVideoGenerationRequest`。后续查询、等待与下载仍走 Generation 服务与已有 artifact probe；导演判断、Shot QA、Review / Repair、再次付费决定留在上层。

## Verification And Evidence

- `tests/test_production_jimeng.py`：30 项通过，覆盖多模态映射、上传、正常提交、响应丢失、标准恢复入口、无 dispatch UNKNOWN、快照缺失或替换、标准 reader 重开、预算协调及下载边界。测试为 Mock/离线证据，不是真实付费执行。
- 原候选的 `production_video_provider_tests` 1009 项、`seedance_local_video_tests` 171 项、`provider_neutral_video_requirement_tests` 450 项通过；后续证据绑定改动后，相关 235 项 Paid/Video 选测通过。最新恢复修复后，另有 122 项 Paid/State 回归通过，随后停止该重复选测，交由完整 Harness 继续验证。
- `4ad6699` 修复独立 MRO 结构断言后，`tests/test_production_state_commit_structure.py` 与 Jimeng 专项合计 48 项通过。该提交的 commit-range Harness 前置文档、规则、策略和架构 Gate 通过；后续 4,252 项重复合同选测因下述已复现基线失败而停止，不记为 PASS。
- 完整 commit-range Harness receipt 为 `.agent/harness/runs/20261021T115902913309Z/receipt.json`：7,286 passed、48 skipped、13 failed；其中 1 项是新增 Jimeng mixin 的 MRO 预期遗漏，已由 `4ad6699` 修复。其余 12 项在未修改的 `16cf57c` 基线临时快照中逐一重跑，仍为同名 12 failed（涉及文档/电商夹具、libass 环境和 Seedream 旧流程）。因此不能宣称全仓 Harness PASS，也不能将这些 12 项归因于 Jimeng 变更。
- 一名 native 只读独立 reviewer 对最终候选 `4ad6699` 做最后一次有界复审，检查标准 Paid 恢复、UNKNOWN 证据、reader、非 Jimeng 回归及画布保存；finding set 为空。Parent 保留上述 Harness 限制，不以审查意见替代运行证明。
- 浏览器 worker 已核实进入 sdist、wheel 和实际安装目标。历史已付费三模态任务通过当前 transport 只读找回；历史 MP4 再下载为 29,222,147 字节，SHA-256 与原片一致。历史服务端画布草稿只读核对包含对应 `resource_id`。这不证明新 Provider 的真实提交或新任务的画布自动保存时序。
- 本次工程化未提交新的付费生成、充值或购买；2026-10-21 历史唯一真实任务实际结算 442 积分，其研究证据见 [Jimeng Interface Research](2026-10-21-jimeng-interface-research.md)。

## Assessment And Remaining Risks

代码与离线恢复契约已接入 P0 所需 canonical owners；工程 P0 的可管理、可恢复、可追踪路径已有专项验证和无 blocker 复审。全仓 Harness 仍非 PASS，且新 Provider 的真实付费提交、浏览器整体重启、登录失效、提交响应真实丢失、长期 UI 内部对象稳定性尚未实证，因此尚不能宣称无条件 Production qualification。操作人封存的积分上限是本地 Paid Guard；服务端接受 `quote_precondition` 不证明远端硬上限生效。生成结果也不构成 Shot QA 或成片验收。
