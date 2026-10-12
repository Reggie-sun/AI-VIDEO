# Canvas Generated Source And Unsubmitted Continuation Plan

## Goal And Authority

用户2026-10-13回复A，允许《界蚀》两镜单元必要共享 provenance/unsubmitted recovery 修复，
并确认 exact PNG 为 project-owned fictional/no-protected-identity。修复后直接继续真实两镜，
不增加两次新增submit、零自动重抽或内部100 CNY上限，不重问是否开始。
本计划由 `superpowers:writing-plans` 组织，Native Codex执行；Parent self-review，无额外spec批准步骤。

## Scope And Owners

`canvas_assets` 接受 optional `generated_source`，只将明确外部生成来源的exact PNG形成
有源receipt的派生copy；默认选择保持imported。单独 `canvas_image_provenance` 验证contained
source record原bytes/hash、其image SHA/size/width/height及明确source tool，准备immutable evidence。
不推断人物class、human attestation、平台来源、商业许可或模型qualified状态。
Registry仍唯一拥有asset metadata，committer仍唯一写入。

`canvas_recovery` 重开committer已核验的closed-unsubmitted结果/evidence。
`CanvasProductionService.prepare_repair/start_repair`只允许该已关闭、未发生外部效果的同task
准备进入existing Orchestrator，绑定exact predecessor evidence、保留旧request/Registry/limits。
current attempt selector只接受完整、唯一、无fork lineage；不按日期猜版本。

Owned files：`src/ai_video/canvas_assets.py`、new `src/ai_video/canvas_image_provenance.py`、
`src/ai_video/canvas_authoring.py`（复用authoring-input绑定来源evidence）、
`src/ai_video/canvas_recovery.py`、`src/ai_video/canvas_production.py`、相关canvas tests、
`docs/canvas-production-harness.md`、`docs/agent-primary-contract-matrix.md`、本计划及本次owned record。
foreign spec/plan/baseline/record与untracked旧retarget plan保持不动，不创建worktree。

## Invariants And Compatibility

- 只做明确源record匹配的派生copy，不允许一个source_kind字段将imported冒充generated。
- optional来源字段缺失时，旧Registry和creative/source表达保持兼容。
- source evidence落盘经PreparedArtifact/唯一committer；没有新的state store/renderer/timeline。
- unsubmitted closure只由原committer核验：no paid state/reservation/intent/effect/receipt/fetch，
  exact not_submitted experience、typed actor/reason；Canvas不能制造或替代该proof。
- 未关闭、known-paid failure缺grant、unknown、wrong task、missing/tampered evidence、fork保持拒绝。
- 此准备恢复不消费付费submit，不授权新增paid repair；submit仍逐次exact preview/budget/egress/permit。
- Per-Shot MCP、required all-PASS、actual A reference、B own QA、native audio、trim、HyperFrames及human gate不削弱。

## Acceptance And Verification

真实pure Registry revise发现preserved-source校验只识别imported receipt；必要适配扩展到
`canvas_source_expression`：重开canonical copy/source evidence，对齐原snapshot、node/resource、asset
及实测bytes/尺寸，保持所有原文/引用角色检查。后续revise保留immutable source inputs。
该缺口先由标准author/reader/compiler回归复现；缺证、bytes损坏、重新seal的错误node/resource/image/source均拒绝。

1. 标准reader/committer重开generated-source evidence；图片hash/尺寸、source hash、路径containment任一不匹配拒绝。
2. 未关闭REQUEST拒绝repair；canonical closed-unsubmitted产生一个唯一新准备，paid_submits_used仍0，
   old evidence保留、task/ceiling不变，immutable resume选到同一successor；wrong task/fork/tampered closure拒绝。
3. focused `test_canvas_assets.py`、new provenance tests、`test_canvas_recovery.py`及project-data/source suites。
   complete exact staged Harness按policy补全部checks，按稳定snapshot判断Implementation Review Risk Gate。
4. 工程核验和适用受管review通过后owned commit/push并核验main SHA，然后actual Runtime接续同单元。
5. 真实生成A→MCP Gate→state reference→B→own Gate→canonical audio/trim/HyperFrames→完整听看。
   任一FAIL/NOT_EVALUATED/unknown停；两镜与完整故事AC-7分别报告。

## Major Milestones

### 1. Preserve Generated Image Provenance

源record输入是明确生成输出记录，必须携带与实测PNG一致的 `sha256/size_bytes/width/height`。
封存source record与派生copy selection observation，保留declared generator tool的证据边界。
修正本单元的精确license为project-owned-synthetic；不能用描述性后缀代替机器许可值。

### 2. Continue A Closed Zero-Effect Preparation

先记录原attempt的not_submitted experience，再由committer以superseded_before_submit显式关闭。
canonically revise authoring/Registry，保留完整历史；shared repair路径引用原exact closure evidence，
重新Planner/Router/compiler，且仅创建一个新待提交request。没有人工伪造paid failure或复用permit。

### 3. Verify, Publish And Execute

先工程tests/Harness/适用review，再commit/push。运行时核对新exact preview与remaining2，
封存PNG human attestation和request-level synthetic egress receipts，reserve仅已有内部上限。
source Gate之前不提交B，source-frame Gate不能代替B findings；最终human acceptance未回复保持NOT_EVALUATED。

## Self-Review

范围只补实际阻断，不新增故事执行链；所有写入仍经committer。
恢复与图片来源分离，Paid Provider和媒体质量Gate不降级。
Runtime验收仍是目标，完成plan/测试/commit不成为停止点。
