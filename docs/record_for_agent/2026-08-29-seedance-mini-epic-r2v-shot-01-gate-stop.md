---
record_kind: media_experiment
topic_id: seedance-mini-remote-r2v-epic-two-shot
learning_eligibility: eligible
evidence_index_version: "1"
---

# Seedance Mini Epic R2V Shot 01 Gate Stop Record

Date: 2026-08-29

## Supersession Notice — 2026-08-30

本记录的 run `...-001` artifact、Gate FAIL、未激活状态与 Shot 2 未执行事实继续有效。其“用户要求的两段连续 15 秒未完成”与“没有 live remote-identity R2V evidence”的 project-wide current-facing 状态，已被独立 repair run `runs/seedance-mini-r2v-epic-skyship-20260829-002/` 及 `docs/record_for_agent/2026-08-30-seedance-mini-remote-r2v-live-chain.md` 取代。新 run 没有追认、覆盖或激活本记录失败的 Shot 1；它使用新的 request/artifact identities，完成两次独立 settled attempts 与两个 exact-byte Per-Shot Gates。

## Purpose

本文记录一次用户明确授权的 Seedance 2.0 Mini 两段连续 15 秒电影感视频执行。冻结目标为：Shot 1 使用 T2V，Shot 2 必须复用 Shot 1 完整 remote Provider output 执行 `VIDEO_EXTEND`，不得退化为尾帧 I2V。

该次执行在 Shot 1 的 exact-byte Per-Shot Post-Media Gate 停止。本文是 paid live development evidence，不是 Production qualification、P6、Final Acceptance 或可交付双 Shot 完成证明。

## Frozen Execution Contract

- Provider/model：`volcengine_ark_seedance` / `doubao-seedance-2-0-mini-260615`。
- Shot 1：`text_to_video`；Shot 2：`video_extend` + one `reference_video`。
- 每段 output：`720p`、`1280x720`、`16:9`、24fps、15 秒、MP4、`native_audio=false`。
- Paid ceiling：每次 `8 CNY`，project total `16 CNY`，最多两个 submit POST。
- 禁止 automatic retry、Provider fallback、I2V fallback 与第三次 submit。
- Shot 1 全部 required finding 必须 `PASS`，才能激活 source、刷新 short-lived remote lease 并提交 Shot 2。

创作与连续性契约位于：

- `runs/seedance-mini-r2v-epic-skyship-20260829-001/shot-contract.md`
- Shot 1 prompt SHA-256：`e411aeb3257aa158df3fcf27ce2740ec28a090c9b14feaad044188c150f29ed2`
- Shot 2 prompt SHA-256：`d17eb1627ad97a9a21bff6862f78c2c684f28a28b0ec151603863dc82c4807d5`

记录不复制 raw prompt、credential、signed result URL 或完整 Provider response。

## Current Runtime Truth

Shot 1 的唯一 submit 被 Ark 接受并最终返回 `succeeded`。随后 exact result URL 下载一次，得到：

- artifact：`runs/seedance-mini-r2v-epic-skyship-20260829-001/output/shot-01-seedance-mini-15s.mp4`
- SHA-256：`3f2f7966402427cda536810248b6dec4bfa61539333e8316908a258f4197d8dd`
- size：`10,105,009` bytes
- H.264、`1280x720`、24fps、361 frames
- video duration：`15.041667s`；container duration：`15.042s`
- audio stream：none
- project-local `video-analysis`：1 scene、sampled unique-frame ratio `1.0`、no generic review issue

Manifest 保持在 truthful unactivated boundary：

- attempt：`epic-skyship-shot-01-attempt`
- status：`running`
- `video_generation_state.phase`：`validate`
- `paid_provider_state.phase`：`settled`
- active Project/Registry 未切换到 generated Shot 1 candidate
- 没有 source activation、remote lease refresh、Shot 2 attempt 或 Shot 2 Provider submit

## Per-Shot Gate Verdict

Gate receipt：`runs/seedance-mini-r2v-epic-skyship-20260829-001/evidence/shot-01-gate.json`，SHA-256 `f7de4a99e01672be3092a3732b48b6968da97e6371507960f58a054641fd0f48`。

| Required finding | Verdict | Exact evidence |
| --- | --- | --- |
| `technical_output` | `FAIL` | 361 frames / `15.042s`，不等于冻结的 360 frames / `15.000s`；resolution、fps、container 与 mute policy 匹配。 |
| `single_ship_identity` | `FAIL` | 末段可见约七个 cyan-white ring engines，违反 `exactly three`，并出现 propulsion-layout drift。 |
| `continuous_motion` | `PASS` | scene detection 为单 scene；sampled frames 全部 unique，contact sheet 可见持续运动。 |
| `extendable_endpoint` | `PASS` | 尾帧仍保留 rear tracking、暖色云层与可继续的 forward motion。 |
| `cinematic_scale` | `PASS` | 山脉尺度、storm-to-gold 光线、volumetric clouds 与 cinematic contrast 明确成立。 |
| `forbidden_elements` | `FAIL` | 未见人物、文字、hard cut 或 duplicate foreground ship；但 engine-count/layout morph 违反 no-geometry-morphing。 |

Contact sheet：`runs/seedance-mini-r2v-epic-skyship-20260829-001/evidence/shot-01-contact-sheet.jpg`，SHA-256 `6a48b7604c4d05e98835a34b821d2acf205f45ecb80ead1fbfdb87d936849971`。

Gate 总 verdict 为 `FAIL`，`provider_submit_authority_for_next_shot=false`。driver 在读取 exact Gate 后以 `RuntimeError: Shot 1 required finding did not PASS` 停止；这是预期的 fail-closed control flow，不是 Provider unknown outcome。

## Provider And Budget Evidence

`runs/seedance-mini-r2v-epic-skyship-20260829-001/evidence/shot-01-live-report.json` 绑定 request fingerprint `dced056b820d95839914dbd05f2e83cbad8ddcaac1fc53bbb79b3975580e9a24` 与 exact MP4，文件 SHA-256 为 `a2474e6e60fb00ebf9fe81f569582e1b5fa08e9f73a391efe63f4452358fb60b`。

本次可验证 counters：

- submit POST：1
- status GET：25
- result download GET：1
- blind retry：0
- Provider fallback：0
- Shot 2 submit：0

settled amount 使用冻结的 conservative upper bound `7,452,000 micro-CNY`；它是 local budget receipt 的 settlement basis，不是 Provider invoice 或最终账单声明。

generic `live-failure.json` 的 `submit_posts=0` 来自 failure wrapper 未保留 transport local variable，不能覆盖 `events.jsonl`、durable paid submit receipt 与 `shot-01-live-report.json` 所共同证明的一次 submit。后续 Agent 不得把该 wrapper counter 单独当作 paid-effect truth。

## Architecture Assessment

本次结果没有否定已经实现的 Seedance remote-output R2V lease path。该路径只有在 source Shot exact-active 后才允许刷新 lease；Shot 1 Gate 已失败，因此没有合法 activation authority，也没有调用 `refresh_remote_reference_lease_once()`。

换言之，这次 STOP 是 continuity/technical acceptance contract 的结果，不是基础设施再次把 R2V 退化成 I2V，也不是 Ark 要求人工上传 `Active asset`。Shot 2 未执行，所以当前没有新的 live evidence 可以证明或反驳 remote identity R2V 在该具体媒体上的生成质量。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| epic-shot01-provider-fetch | seedance-mini:dced056b820d95839914dbd05f2e83cbad8ddcaac1fc53bbb79b3975580e9a24 | seedance-mini-r2v-epic-skyship-20260829-001 | epic-skyship-shot-01-attempt | shot-01-t2v | 3f2f7966402427cda536810248b6dec4bfa61539333e8316908a258f4197d8dd | PAID_PROVIDER_SUBMIT_POLL_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-mini-r2v-epic-skyship-20260829-001/evidence/shot-01-live-report.json |
| epic-shot01-agent-gate | seedance-mini:dced056b820d95839914dbd05f2e83cbad8ddcaac1fc53bbb79b3975580e9a24 | seedance-mini-r2v-epic-skyship-20260829-001 | epic-skyship-shot-01-attempt | shot-01-t2v | 3f2f7966402427cda536810248b6dec4bfa61539333e8316908a258f4197d8dd | AGENT_PER_SHOT_POST_MEDIA_GATE | FAIL | TECHNICAL_DURATION_AND_GEOMETRY_IDENTITY_DRIFT | SAME_EVIDENCE_NEW_PROOF_LAYER | epic-shot01-provider-fetch | runs/seedance-mini-r2v-epic-skyship-20260829-001/evidence/shot-01-gate.json |

## Remaining Risk And Next Work

- 用户要求的“两段连续 15 秒”未完成；当前只有一个 Gate-failed Shot 1 development artifact。
- 继续生成需要新的 paid attempt 与至少一次新的 Shot 1 submit；现有授权冻结为本次最多两 POST，但 Gate stop 后不得自动把未用额度解释为 retry authority。
- 如果未来批准 repair attempt，应重新冻结能更稳地保持 engine topology 的 subject contract，同时必须保留新 attempt identity；不得覆盖本次 artifact 或 receipt。
- 即使新 Shot 1 通过 Agent Gate，Shot 2 仍需自己的 exact-byte Per-Shot Gate；R2V transport success 不能替代 continuity/quality verdict。
- `15s` Seedance Mini output 再次出现 361 frames / `15.042s`，但本记录只贡献一个 independence unit；是否形成可采用的 cross-experiment Learning Claim 由 `distill-ai-video-learning` 依据 eligible identity evidence 单独决定。

## Agent Guardrails

- 不得激活该 Shot 1 candidate，也不得用尾帧 I2V 或 manual Ark upload 绕过 Gate。
- 不得从 signed URL、Provider success 或 remote materialization 推导 P6 / Final Acceptance。
- 不得把没有发生的 Shot 2 描述为 R2V failure；它是 `NOT_EXECUTED_AFTER_REQUIRED_GATE_FAIL`。
- 后续任何 paid repair、variant 或额外 submit 需要新的明确执行 scope；不得 blind retry。
