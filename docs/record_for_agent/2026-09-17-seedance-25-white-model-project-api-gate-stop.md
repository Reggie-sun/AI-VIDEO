---
record_kind: media_experiment
topic_id: seedance-25-white-model-motion-reference
learning_eligibility: eligible
evidence_index_version: "1"
---

# Seedance 2.5 White-Model Project API Gate Stop Record

Date: 2026-09-17

## Purpose

本文记录一次用户明确要求的 Seedance 白模测试如何改走 AI-VIDEO project API，并冻结该次
真实 paid/cloud development experiment 的能力边界。实验目标是先生成一个受控白色关节人偶
动作源，通过 exact-byte Per-Shot Gate 后，再以 Seedance 2.5 `reference_to_video` 生成不同
外观的写实人物并继承动作。

本记录只证明一次 exact Seedance 2.5 T2V request 被接受并生成白模 MP4，以及该 MP4 为何未获
source activation。它不是 R2V motion-transfer PASS、Provider qualification、P6、Final
Acceptance 或 publication evidence。

## Frozen Execution Contract

- Provider/model：`volcengine_ark_seedance` / `doubao-seedance-2-5-260628`。
- Source：`text_to_video`，生成单个 matte-white articulated mannequin。
- Target：只有 Source Gate 全部 required findings 为 `PASS` 后，才允许
  `reference_to_video` + one `reference_video`。
- 每个 output：5 秒、`720p`、`1280x720`、`16:9`、24fps、MP4、
  `native_audio=false`。
- Source action：0–2 秒双臂下垂；2–3.5 秒把人物右臂侧抬至肩高；3.5–5 秒保持右臂水平并将
  躯干向人物右侧旋转约 20 度。
- Camera：固定、眼平、single continuous take、完整全身与所有肢体可见。
- Task submit ceiling：最多两个 POST；source 与 target 各一个，不允许 blind retry、Provider
  fallback 或 browser-console bypass。
- Runtime monetary fields 使用 repository 内 sealed operator upper bound：每次
  `10,000,000 micro-CNY`、project `20,000,000 micro-CNY`。这些是内部安全上限，不是官方价格、
  实际账单或市场报价。

Source/target creative intent 先进入 `ProviderNeutralVideoRequirement/4`，再由
`GenerationFeedbackOrchestrator` 与 `seedance-video-compiler/2` 生成 request；submit 必须携带可
重开的 `GenerationDecisionExecutionBinding`。没有直接把手写 prompt/request 绕过当前 decision
owner。

## Current Runtime Truth

正式 run 为 `runs/seedance-white-model-api-test-20260917-002/`。Source request 绑定：

- attempt：`white-model-source-attempt`
- mode：`text_to_video`
- resolved request fingerprint：
  `51cbd95776cb91be8215c5fe7cc39767f1b54a1854ebf2f1ceca437a03ce411c`
- execution binding hash：
  `a9de628de5514855bd818b96777bf49a1f9b5633bf977186b6d621d00d5a5af5`
- compiled prompt SHA-256：
  `b2163cb622eed4c117d2a08a818fc1d41204e4beaa2e3babba96df1f13f1308f`

Ark 接受唯一一次 Source POST，task 在 45 次 read-only status query 后返回 `succeeded`，随后
下载一次 exact result。没有 retry、fallback 或第二次 submit。

Source artifact：

- path：`runs/seedance-white-model-api-test-20260917-002/output/source-white-model-5s.mp4`
- SHA-256：`52b0db2a54d202cb89c823ebc1592d768f0170300b8cfc53bb3e6768abc1c7ef`
- size：`1,943,612` bytes
- H.264 High、`1280x720`、`yuv420p`、24fps、121 frames
- container duration：`5.042s`
- audio stream：none
- project-local `video-analysis`：11 个 0.5 秒间隔抽帧、1 scene

当前 Manifest 保持 truthful Gate-stop boundary：

- `white-model-source-attempt.status = running`
- `video_generation_state.phase = validate`
- `paid_provider_state.phase = settled`
- `candidate_video_asset_ids = []`
- Source 未进入 candidate、未 activation、未刷新 remote reference lease
- `white-model-motion-transfer-attempt` 不存在
- Target R2V submit count：`0`

## Recovery Incident

Source fetch 后，local run driver 在报告字段中误用了不存在的
`GenerationDecisionExecutionBinding.content_hash`，正确字段应为 `binding_hash`。异常发生在
canonical fetch receipt 已持久化、exact MP4 已复制之后；Provider outcome 已知且 settled。

恢复过程没有重提 Provider task。它从 Manifest 重开 exact request、execution binding、status 与
fetch receipt，确认 canonical fetched bytes 与 copied output SHA-256 相同，再生成
`attempt-01-live-report.json` 并进入 Per-Shot Gate。该 incident 只属于本次 ignored run driver，
不是 Product Runtime capability failure，也不进入 `.agent/bug-memory/`。

先前 `runs/seedance-white-model-api-test-20260917-001/` 的 direct-request prototype 在
`VideoGenerationService.start()` 前因缺少 `execution_binding` 停止，submit count 为 `0`；它没有
Provider side effect，也不能作为当前 contract 的执行样例。

## Per-Shot Gate Verdict

Gate receipt：
`runs/seedance-white-model-api-test-20260917-002/evidence/attempt-01-gate.json`，SHA-256
`ea7b4bb201111f2bad1484e9f673cb5d29c8bd87d291c7b29c62775eec2b0469`。

| Required finding | Verdict | Exact evidence |
| --- | --- | --- |
| `technical_output` | `PASS` | Exact MP4 可解码；H.264 High、`1280x720`、24fps、121 frames、`5.042s`、无音轨。 |
| `white_model_subject` | `PASS` | 所有 sampled frames 均为单个稳定的 matte-white articulated geometric mannequin 与纯灰 studio。 |
| `motion_sequence` | `FAIL` | 右臂约 1.0 秒已开始抬、约 1.5 秒已水平，违反 0–2 秒保持下垂、2–3.5 秒抬臂的 sealed timing；后段虽有轻微 torso turn，但不能修复前段 mismatch。 |
| `fixed_full_body_camera` | `FAIL` | Camera 稳定且居中，但所有 sampled frames 都裁掉脚和部分 lower legs，不满足完整全身与全部肢体可见。 |
| `no_text_or_cuts` | `PASS` | scene detection 为 1 scene，sampled frames 未见文字、字幕或 logo。 |
| `reference_readiness` | `FAIL` | Timed action 与 full-body framing 两项 source contract 均失败，不能作为本次 sealed motion-transfer reference。 |

Contact sheet：
`runs/seedance-white-model-api-test-20260917-002/evidence/source-contact-sheet.jpg`，SHA-256
`283327c6453009d24b38db4ce3107e3def2e1952d567ffcc8982f3c911c76e5e`。

Gate 总 verdict 为 `FAIL`，`next_submit_authorized=false`。恢复 driver 读取 exact Gate 后以
`RuntimeError: required post-media finding did not PASS` 停止；这是预期的 fail-closed control
flow，不是 Provider unknown outcome。

## Provider And Project API Evidence

- prepared contract：
  `runs/seedance-white-model-api-test-20260917-002/evidence/attempt-01-prepared-contract.json`，
  SHA-256 `34bccf4d5cb6c3d9d415294844b50c77f54ccb3ee84aa3648b302e17969d9122`。
- recovered live report：
  `runs/seedance-white-model-api-test-20260917-002/evidence/attempt-01-live-report.json`，
  SHA-256 `413ee81edf33696d8e7dde0b7b6d777a8c0d3470dd719856bac7ea77ca3ddc12`。
- submit POST：1。
- status GET：45。
- result download GET：1。
- blind retry：0。
- Provider fallback：0。
- Target R2V submit：0。

Source paid reservation 已按 frozen operator upper bound `10,000,000 micro-CNY` settled。该数字只
说明 internal budget receipt 的 settlement basis，不说明 Provider invoice 或实际扣费。

登录后的 browser Experience 页面曾成功临时上传 local white-model reference，但用户随后明确要求
使用项目 API，因此没有点击 browser generation submit。临时 Experience upload 不是 Asset
Registry/Manifest evidence，也没有被冒充为 project materialization。当前 account metadata 当时显示
`aigc_writable=false`，所以本次合法策略是让 Seedance 先生成 Provider-owned Source，再在 Gate PASS
后使用项目的 remote-output lease；后者因为 Gate FAIL 没有执行。

## Assessment

对“Seedance 是否接受白模”必须分层回答：

1. **本次 T2V acceptance 为 PASS**：Seedance 2.5 接受了 project API 的白色关节人偶语义请求，
   并返回确实可见的白模 MP4。
2. **作为受控动作源的质量为 FAIL**：该 exact artifact 没有遵守关键动作 timing，也没有完整全身
   framing，因此项目正确阻断后续 motion transfer。
3. **白模 reference input / R2V acceptance 为 NOT TESTED**：Target request 从未 submit，不能由
   Source T2V success、browser temporary upload 或 capability matrix 推断 Seedance 2.5 已接受并正确
   使用白模 reference video。

因此不能给出 Provider-wide 的“可以”结论；当前精确结论是“可以生成白模，但这一次生成的白模不够
合格，尚未实测它作为 R2V reference 的接受与动作迁移结果”。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seedance25-white-source-fetch | seedance25:51cbd95776cb91be8215c5fe7cc39767f1b54a1854ebf2f1ceca437a03ce411c | seedance-white-model-api-test-20260917-002 | white-model-source-attempt | source-t2v | 52b0db2a54d202cb89c823ebc1592d768f0170300b8cfc53bb3e6768abc1c7ef | PAID_PROVIDER_SUBMIT_POLL_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-white-model-api-test-20260917-002/evidence/attempt-01-live-report.json |
| seedance25-white-source-gate | seedance25:51cbd95776cb91be8215c5fe7cc39767f1b54a1854ebf2f1ceca437a03ce411c | seedance-white-model-api-test-20260917-002 | white-model-source-attempt | source-t2v | 52b0db2a54d202cb89c823ebc1592d768f0170300b8cfc53bb3e6768abc1c7ef | AGENT_PER_SHOT_POST_MEDIA_GATE | FAIL | MOTION_TIMING_AND_FULL_BODY_FRAMING | SAME_EVIDENCE_NEW_PROOF_LAYER | seedance25-white-source-fetch | runs/seedance-white-model-api-test-20260917-002/evidence/attempt-01-gate.json |

## Remaining Risk And Next Work

- 本次 task ceiling 已使用 1/2 submit，但修复 Source 后仍需另一个 Target submit；完成原两阶段目标至少
  还需要两个新的 paid calls，超出现有 ceiling，不能自行追加或把未用的单次额度解释成完整 repair
  authority。
- 若用户另行批准继续，应创建新 attempt identity，首先只修复 Source framing/timing；新的 Source 仍需
  完整 Per-Shot Gate，不能复用本次 Gate 或覆盖本次 artifact。
- 只有新 Source exact-active 后，才能刷新其短期 remote reference lease 并准备 R2V；Target 生成后仍
  必须执行自己的 exact-byte Gate。
- 单个 source artifact 只贡献一个 independence unit；不得把 Provider fetch PASS 与 Agent Gate FAIL
  当作两个独立实验，从而外推 Seedance 2.5 的一般白模能力。

## Agent Guardrails

- 不得激活本次 Gate-failed Source，也不得用它继续 Target R2V。
- 不得把 capability matrix、browser upload 或 remote URL availability 当作 live R2V acceptance。
- 不得把 `succeeded` task、技术可解码或白模可见转换成 motion-transfer quality PASS。
- 不得从本次 development experiment 推导 P6、Final Acceptance、release 或 publication truth。
- 不得记录 raw credential、cookie、signed URL、完整 Provider response 或完整 raw prompt。
