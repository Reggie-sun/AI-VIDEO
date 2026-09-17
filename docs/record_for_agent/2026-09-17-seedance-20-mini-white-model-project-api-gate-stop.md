---
record_kind: media_experiment
topic_id: seedance-20-mini-white-model-motion-reference
learning_eligibility: eligible
evidence_index_version: "1"
---

# Seedance 2.0 Mini White-Model Project API Gate Stop Record

Date: 2026-09-17

## Purpose

本文记录用户将白模动作参考测试的 selected model 从 Seedance 2.5 改为
`doubao-seedance-2-0-mini-260615` 后，AI-VIDEO project API 的一次真实 paid/cloud
development experiment。目标仍是先生成受控白色关节人偶动作源，只有 exact-byte Per-Shot
Gate 全部 required findings 为 `PASS`，才允许以该 Source 执行
`reference_to_video` 真人动作迁移。

本记录证明 Mini 接受了本次 T2V project request 并返回白模 MP4，也记录该 exact Source
为何没有获准进入第二次 R2V submit。它不是 Seedance Mini 白模 R2V acceptance、motion-transfer
quality、Provider qualification、P6、Final Acceptance 或 publication evidence。

## Frozen Execution Contract

- Provider/model：`volcengine_ark_seedance` / `doubao-seedance-2-0-mini-260615`。
- Source：`text_to_video`；一个 matte-white articulated geometric mannequin。
- Target：只有 Source Gate 全部 required findings 为 `PASS` 后，才允许
  `reference_to_video` + one `reference_video`。
- Geometry/audio：`720p`、`1280x720`、`16:9`、24fps、MP4、`native_audio=false`。
- Mini timing：current capability/profile 只提供 `nominal_seconds` 与 `provider_selected`；当前
  decision binding 使用 `provider_selected`，payload `duration=-1`。创作目标仍为约 5 秒，但没有
  把它伪装成 exact-duration runtime control。
- Action：opening still hold -> subject-right arm lateral raise to shoulder height -> only then rotate
  the torso about twenty degrees to the subject's right and hold。
- Camera：locked、wide、head-to-toe；头、手、脚、全部肢体及脚下地面持续可见。
- Task submit ceiling：最多两个 POST；Source 与 Target 各一个；无 blind retry、Provider
  fallback 或 browser-console bypass。
- Runtime monetary fields 使用 sealed operator upper bound：每次 `10,000,000 micro-CNY`、project
  `20,000,000 micro-CNY`。它们不是官方价格、实际账单或市场报价。

Source/Target 均先进入 `ProviderNeutralVideoRequirement/4`，再由
`GenerationFeedbackOrchestrator`、Router、`seedance-video-compiler/2` 与
`GenerationDecisionExecutionBinding` 进入 canonical Provider lifecycle。Mini-only profile 使用
current `select_seedance_capabilities()` exact subset；没有把 default active base model 或 capability
catalog 当作 implicit selection。

## Preflight And Provider Evidence

正式 run 为 `runs/seedance-white-model-api-test-20260917-003/`。

零 POST preflight 同时完成 Source T2V 与 hypothetical Target R2V binding：

- Source mode：`text_to_video`；execution binding hash
  `fa9408d88d66c8e021d12e69006eeb6fb9696361d4fd686ef84960b8441a5c2f`。
- Target mode：`reference_to_video`；exactly one `reference_video`；execution binding hash
  `5735bda942c1fa8f6dbfe73e6b54bacac6f664e97f9d8111d5aa9746df9a2bce`。
- `submit_posts=0`。

Current live Source binding：

- attempt：`white-model-mini-source-attempt`
- requirement hash：`194039c5e432087a14088bb2589716a39b0b432a58ff259c5c79e76c3d14cb11`
- resolved request fingerprint：
  `5ed92a6e3b6cd041a7958337c2d4a0cc87fbeb7e3650017f7c07b8d35ccbdb38`
- execution binding hash：
  `cd886bffeed528eadc193dc74c8ef68382939781be1d76292e72df602135872f`
- compiled prompt SHA-256：
  `e47513aaa0005c1365406ebca88390847df3d758c28b29ec98dfab8f1adf12bc`
- media bindings：none

Ark 接受唯一一次 Source POST。第 11 次 read-only status query 观察到 `succeeded`，随后下载一次
exact result。没有 retry、fallback 或第二次 submit。

Source artifact：

- path：`runs/seedance-white-model-api-test-20260917-003/output/source-white-model-5s.mp4`
- SHA-256：`ee621b59ebe5da1852edf3ba54eac86eee566e1da775b198e5815c7845ef6e3e`
- size：`1,700,256` bytes
- H.264 High、`1280x720`、`yuv420p`、24fps、121 frames
- container duration：`5.042s`
- audio stream：none
- project-local `video-analysis`：11 个 0.5 秒间隔 frames、1 scene

Prepared contract、live report 与 Gate receipt 分别为：

- `evidence/attempt-01-prepared-contract.json`，SHA-256
  `0891678b31a07fb8af39037f2d545d8348b554db1b137a5eed3060ceb1d70bda`
- `evidence/attempt-01-live-report.json`，SHA-256
  `19db7f275c3c799b33d245b6b29fac0eeadcf9aaedfe4e9d9802896eaaaed699`
- `evidence/attempt-01-gate.json`，SHA-256
  `dcec5231a69bfeda9dbd71c3979dd618f543182bd21bebe13da87685a60c7df9`

## Per-Shot Gate Verdict

| Required finding | Verdict | Exact evidence |
| --- | --- | --- |
| `technical_output` | `PASS` | Exact MP4 可解码；H.264 High、`1280x720`、24fps、121 frames、`5.042s`、无音轨。 |
| `white_model_subject` | `PASS` | 11 个 sampled frames 均为单个稳定的 matte-white articulated mannequin 与纯灰 studio。 |
| `motion_sequence` | `FAIL` | Opening hold、subject-right arm raise、subsequent torso/head turn 的顺序可见；但 3.5s 与 4.5s exact frames 显示人物朝 viewer-right，即 subject-left 旋转，与 sealed subject-right turn 相反。 |
| `fixed_full_body_camera` | `PASS` | Camera 固定；头、双手、双脚、全部肢体、脚下地面与 headroom 在抽样中持续可见。 |
| `no_text_or_cuts` | `PASS` | Scene detection 为 1 scene；抽样未见文字、字幕或 logo。 |
| `reference_readiness` | `FAIL` | Source 技术上干净、全身 framing 合格，但动作方向不符合 sealed intent，不能作为本 attempt 的 activated motion reference。 |

Contact sheet：
`runs/seedance-white-model-api-test-20260917-003/evidence/source-contact-sheet.jpg`，SHA-256
`2adffc308e22ff9700d8e21bd34aeb264143b5b32301c9b2146be15eb6366408`。

Gate 总 verdict 为 `FAIL`，`next_submit_authorized=false`。Driver 读取 exact Gate 后以
`RuntimeError: required post-media finding did not PASS` 停止；`live-failure.json` 记录
`outcome_unknown=false`、`blind_retry_performed=false`、`submit_posts=1`。这是预期的 fail-closed
control flow，不是 Provider unknown outcome。

## Lifecycle Boundary

当前 Manifest revision 为 `23`：

- `white-model-mini-source-attempt.status = running`
- `video_generation_state.phase = validate`
- `paid_provider_state.phase = settled`
- `candidate_video_asset_ids = null`
- `active_video_asset_id = null`
- Source 未 validate/activate，未刷新 remote reference lease
- `white-model-mini-motion-transfer-attempt` 不存在
- Target R2V submit count：`0`

本次唯一 Source reservation 按 frozen operator upper bound `10,000,000 micro-CNY` settled。该值只
说明 internal budget receipt basis，不是 Provider invoice 或 actual billing evidence。

## Assessment

对“Seedance 2.0 Mini 是否接受白模”只能分层回答：

1. **白模 T2V API acceptance 为 PASS**：Mini 接受了 decision-bound project request，并生成
   exact white-mannequin MP4。
2. **白模 source framing 明显改善并 PASS**：相对 2.5 前一 attempt 的 feet/lower-leg crop，本次
   全身与四肢持续可见；这不是等 prompt、等 model 的 controlled comparison。
3. **作为本次 sealed motion reference 的 readiness 为 FAIL**：动作顺序正确，但 torso turn
   direction 相反。
4. **白模 reference input / Mini R2V acceptance 仍为 NOT TESTED**：Target 从未 submit，不能由
   capability matrix、历史 Mini R2V 或本次 T2V success 推断该 exact white-model reference 已被
   接受或正确迁移。

因此当前 exact 结论是：Seedance 2.0 Mini 能通过项目 API 生成白模；这次白模比前次更适合做动作
参考，但仍未达到 sealed reference Gate，真人 R2V 没有执行。

## Verification And Publication

- `PYTHONPATH=.:tests python -m pytest -p no:cacheprovider tests/test_generation_execution.py tests/test_generation_provider_wiring.py tests/test_production_seedance.py -q`：`162 passed in 7.96s`。
- Mini Source/Target zero-POST binding preflight：`PASS`，Target reference count `1`。
- Live Provider lifecycle：1 POST、11 status GET、1 result download、0 retry、0 fallback。
- Exact Source 调用 project-local `video-analysis` MCP 并完成人工 contact-sheet / direction-frame
  inspection。

上述 focused tests 与 live run 来自当前 working tree；该 checkout 含 pre-existing unrelated
uncommitted product-source changes，因此 live evidence 绑定 run 内 exact contracts/artifacts，不冒充
clean-commit reproducibility。Run driver、media 与 receipts 位于 ignored `runs/`，不会随本记录 commit。

## Learning Evaluation

`distill-ai-video-learning`: `no_candidate`。本次 Mini Source 与同日 2.5 Source 是两个 distinct
independence units，但 selected model、timing mode、authoring expression 与 failure mode 均不同，不能
构成 framing、timing 或 direction repair 的 controlled comparison。两次都支持的窄结论只是“Provider
T2V success 不等于 motion-reference readiness”，该语义已由当前 Per-Shot Gate 与 repository
invariants 直接拥有，本轮没有新的 Skill、Provider Policy、Preflight、Contract 或 Gate behavior
需要 adoption。未创建 Learning Claim placeholder，也未把两个 proof layers 重复计数。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seedance20mini-white-source-fetch | seedance20mini:5ed92a6e3b6cd041a7958337c2d4a0cc87fbeb7e3650017f7c07b8d35ccbdb38 | seedance-white-model-api-test-20260917-003 | white-model-mini-source-attempt | source-t2v | ee621b59ebe5da1852edf3ba54eac86eee566e1da775b198e5815c7845ef6e3e | PAID_PROVIDER_SUBMIT_POLL_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-white-model-api-test-20260917-003/evidence/attempt-01-live-report.json |
| seedance20mini-white-source-gate | seedance20mini:5ed92a6e3b6cd041a7958337c2d4a0cc87fbeb7e3650017f7c07b8d35ccbdb38 | seedance-white-model-api-test-20260917-003 | white-model-mini-source-attempt | source-t2v | ee621b59ebe5da1852edf3ba54eac86eee566e1da775b198e5815c7845ef6e3e | AGENT_PER_SHOT_POST_MEDIA_GATE | FAIL | TORSO_TURN_DIRECTION_MISMATCH | SAME_EVIDENCE_NEW_PROOF_LAYER | seedance20mini-white-source-fetch | runs/seedance-white-model-api-test-20260917-003/evidence/attempt-01-gate.json |

## Remaining Risk And Next Work

- 用户授权的本轮 ceiling 是最多两次 submit，本轮实际使用 1 次；Gate FAIL 后未使用的第 2 次额度
  不构成 retry 或不同 attempt 的授权。
- 若要继续完成真人 R2V，必须由新的 task-scoped authority 创建新 Source attempt 或由用户明确接受
  当前相反 turn direction 作为新的 intent；不得事后改写本 Gate。
- 只有新的 Source exact Gate PASS 并 activation 后，才能刷新其 remote reference lease，再准备
  Target `reference_to_video`；Target 仍需自己的 exact-byte Per-Shot Gate。
- 本 run 贡献一个 independence unit；Provider fetch PASS 与 Agent Gate FAIL 是同一 attempt 的不同
  proof layers，不能计为两个独立实验。

## Agent Guardrails

- 不得激活本次 Gate-failed Source，也不得用它继续 Target R2V。
- 不得把 Mini capability registry、历史 remote R2V 或本次 T2V success 当作当前 white-model
  reference acceptance。
- 不得把 Provider `succeeded`、可解码、白模可见或全身 framing PASS 转换为 motion-transfer PASS。
- 不得从本次 development experiment 推导 P6、Final Acceptance、release 或 publication truth。
- 不得记录 raw credential、signed URL、完整 Provider response 或完整 compiled prompt。
