# Shot Continuity QA Gate And Evaluator Boundary Record

Date: 2026-08-21

## Purpose

本文记录 continuity-bound generated Shot 在 P8 candidate activation 前的 QA gate
实现，以及自动视觉 evaluator 的当前边界。它是 architecture/runtime record，不是
新的 Provider、live generation、paid execution 或 quality-acceptance 授权。

本记录补充但不替代既有的 `2026-08-20-h3-shot-continuity-and-vscode-playback.md`；
旧记录关注 Local H3 terminal-frame technical continuity 与 playback，本记录关注
semantic continuity evidence、P6 adjudication 与 activation fail-closed boundary。

## Current Runtime Truth

Commit `a09ec45`（`fix: gate shot continuity on qa evidence`）已把 continuity review
接入现有 Provider-neutral video candidate seam：

- `GeneratedShotContinuityEvidence` 位于 `src/ai_video/production/review.py`，绑定
  source/target Shot、target Shot hash、resolved generation hash、MP4 SHA-256、
  continuity constraints hash、active QA policy hash 与 evaluator identity。
- `src/ai_video/production/video_artifact.py` 在 held-FD measured validation 后调用
  explicit reviewer，并恢复原始 FD offset；evidence 必须来自
  `explicit_evaluator` 或 `human`，且 evaluator 必须属于 active policy 的
  `semantic_authorities`。
- P6 deterministic adjudicator 派生 `PASS`、`FAIL` 或 `NOT_EVALUATED`；evidence
  没有 evaluator 自报 verdict 字段。
- `VideoGenerationService.fetch_and_activate()` 通过唯一 committer path 传入
  reviewer；缺 active policy、semantic authority、reviewer、完整 evidence 或
  passing verdict 时，candidate 停在 `VALIDATE`，不会写入 candidate/activation。
- 非 continuity request 与历史无 evidence 的 `VideoProbeReceipt` 保持 reopen/
  serialization 兼容。

当前 branch 后续又包含相邻的 Quality Intelligence commit `7e3266a`；该 commit
不是本 record 的实现来源，且本 record 没有修改其 files。

## Session Work And Decisions

### Diagnosis

此前 multi-Shot 检查中，第二个 Shot 的画面方向与前一 Shot 不合理，但 generic
`video-analysis` 没有报告 structural issue。原因不是单纯 prompt：analysis 只提供
raw technical/heuristic evidence，Provider fetch path 也没有把 P6 semantic review
作为 activation 前的强制 gate。直接 H3 smoke 因此可以生成并继续，而不是在 per-Shot
continuity failure 处停止。

### Contract Decision

本次采用 fail-closed evidence gate，而不是让 analyzer 或 prompt 自己升级为 semantic
PASS。最低要求覆盖：

- identity、camera axis、framing；
- motion direction；
- entrance 与 exit state；
- unexpected re-entry；
- complete coverage 与 exact policy/request/artifact binding。

这保持 `ProductionStateCommitter` 为唯一 activation owner，也不创建第二条 QA
control path 或第二套 lifecycle truth。

## Verification And Evidence

Task-owned implementation files：

- `src/ai_video/production/review.py`
- `src/ai_video/production/video_artifact.py`
- `src/ai_video/production/_state_commit_video_candidate.py`
- `src/ai_video/production/video_generation.py`
- `tests/test_production_review.py`
- `tests/test_production_video.py`
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`

Evidence:

- Native reviewer：`accept with concerns`，无 blocking issue；指出的 non-blocking
  gap 是尚未有完整 `VideoGenerationService -> committer -> active QaPolicy ->
  VALIDATE/CANDIDATE/ACTIVATE` lifecycle regression。
- Focused review/video suite：`76 passed`。
- Exact staged Harness 在 commit 前通过：`62` harness tests、`949` production state
  tests、`515` review tests、`907` video/provider tests、`249` provider-neutral tests；
  Architecture Gate 为 PASS。
- Commit-range receipt：
  `.agent/harness/runs/20260821T142425114636Z/receipt.json`，运行时
  `status=passed`、`closure_eligible=true`、`snapshot_matches=true`、policy matched。
  后续 HEAD 前进到 `7e3266a` 后，该旧 range receipt 当前不再 fresh，这是 receipt
  scope 已过期，不是 continuity gate 测试失败。
- 本 slice 没有 Provider submit/poll/fetch、ComfyUI media generation、remote/paid
  call、upload 或 Final Acceptance；验证仅证明 code/state contract 与 tests。

## Automatic Evaluator Boundary

当前实现需要显式注入 `GeneratedShotContinuityReviewer`，尚未提供通用自动视觉
evaluator。这是有意的安全边界：没有可信 evaluator 时，系统宁可停在
`NOT_EVALUATED`/`VALIDATE`，也不能猜测 semantic PASS。

当前可行的后续 v1 是 hybrid evaluator：

1. 使用 exact source/target MP4 frame sampling 生成可复现的 boundary/contact evidence；
2. 用 deterministic measurements 覆盖 motion direction、entrance、exit 与 re-entry；
3. 对 identity、axis、framing 使用真正支持 image/video input 的 vision backend；
4. backend 只返回 raw measurements、confidence 与 frame indices，最终 verdict 仍由
   P6 adjudicator 派生；低置信度必须进入 human fallback。

`gpt_image_2` MCP 当前是 `prompt -> generate_image` 的图像生成接口，不接受图片或
视频输入，不能直接承担 evaluator。`video-analysis` 可以用于抽帧，但不能未经明确
adapter contract 变成 Production runtime 的第二 reviewer/activation owner。

## Assessment

本次修复解决了“第二个 Shot 明显不连续却继续 activation”的 silent failure：现在
continuity-bound candidate 必须有 policy-selected、exact-bound evidence，并由 P6
派生通过结果。

它不等于已经完成通用视觉质量评估，也不等于实现了自动 repair、自动 Provider 选择或
Final Acceptance。技术 continuity、semantic review、subjective human acceptance 和
最终 composition 仍是不同层级。

## Remaining Risks Or Next Work

- 后续 evaluator v1 应保持 no-new-dependency、no-remote-default、no-MCP-runtime-
  coupling；若需要新视觉 Provider、credential、budget 或 cloud-egress，必须另行
  取得 scope 授权并更新对应 contract。
- 应补一条完整 lifecycle regression，证明 continuity failure 保持 `VALIDATE`、
  candidate pointers 为空、passing reviewer 才能 activation，且 replay 不重复
  reviewer side effect。
- 在自动 evaluator 获得代表性样本和人工校准前，不得将其结果外推为通用 identity、
  motion、quality 或 Final Acceptance 结论。

## Agent Guardrails

- Analyzer/reviewer 只能提交 raw evidence；不得自报 Production PASS。
- Exact MP4、Shot、request、constraints、policy 与 evaluator identity 必须进入
  evidence binding；stale/tampered/incomplete evidence 必须 fail closed。
- `ProductionStateCommitter` 独占 candidate、activation 与 recovery；不得在 analyzer、
  Provider adapter 或 MCP tool 中创建第二 writer。
- `video-analysis` technical output、Local H3 proof、单次 Provider success 和
  playback success 都不等于 semantic quality acceptance。
- 本 record 没有包含 secret、raw prompt、signed URL、Provider response 或 private
  environment values。
