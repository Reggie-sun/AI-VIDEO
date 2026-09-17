---
record_kind: media_experiment
topic_id: blender-mcp-white-model-seedance-mini-reference
learning_eligibility: eligible
evidence_index_version: "1"
---

# Blender MCP White-Model To Seedance Mini Reference Runtime Record

Date: 2026-09-17

## Supersession Notice — 2026-09-17 Live Completion

下文两个 materialization blocker checkpoint 已被同日 `live-r2v-005` 的真实 cloud evidence 取代。
用户在 Volcengine Console 开通 TOS 后，browser session 为 private versioned bucket 中的 exact object
签发短期、method-specific presigned PUT/GET；项目的 canonical materializer 完成 upload 与 exact-byte
readback，随后 AI-VIDEO project API 对 `doubao-seedance-2-0-mini-260615` 执行了唯一一次
`reference_to_video` POST。Provider task 成功、exact MP4 已 fetch、project-local `video-analysis` post-media
Gate 全部 required findings 为 `PASS`，并由 `ProductionStateCommitter` 激活同一 SHA-256 candidate。

当前结论不再是 pre-submit blocked：本次 exact Blender white-model reference 已被 Seedance Mini 接受并
完成动作迁移。旧 blocker、`POST = 0` 与“需要 grant”的文字仅保留为历史 chronology，不代表 current
runtime state。本次证据仍只是 task-scoped Development live proof，不是 P6、Final Acceptance、release
或普遍 Provider capability qualification。

## Supersession Notice — 2026-09-17

下文 `Project API Materialization Blocker` 对“current runtime 没有 local MP4 materializer”的结论已被
本记录后续 `Materialization Implementation Checkpoint` 取代。现在 working tree 已实现受控对象存储
presigned PUT/GET、TOS version identity、exact-byte readback 与 request-bound短租约，但 host/repository
仍没有可用的受控 storage grant/presigner。因此 blocker 已从 `LOCAL_VIDEO_MATERIALIZER_NOT_IMPLEMENTED`
缩小为 `CONTROLLED_OBJECT_STORAGE_GRANT_MISSING`；Seedance generation POST 仍为 `0`。

## Purpose

本文记录用户纠正测试意图后的一次 bounded execution：白模不是由 Seedance 生成，而是由
`blender-mcp 1.8.7` 控制本地 Blender 5.2.1 LTS 制作；只有 exact local MP4 通过 Gate 后，才准备
交给 `doubao-seedance-2-0-mini-260615` 的 AI-VIDEO project API
`reference_to_video` path。

本记录证明本地 MCP authoring、render、asset validation 与 exact-byte source Gate 已完成，也记录
为什么项目在 paid Provider submit 前 fail closed。它不证明 Seedance 已接受本次白模 reference，
不构成 Provider capability PASS、candidate activation、P6、Final Acceptance 或 publication evidence。

## Corrected Execution Contract

- Source owner：local Blender MCP；Seedance 不生成白模。
- Blender transport：`blender-mcp 1.8.7`，addon protocol `4`，Blender `5.2.1 LTS`；telemetry disabled。
- Source action：opening hold -> subject-right arm lateral raise to shoulder height -> torso/head turn
  subject-right while the arm remains raised。
- Camera/scene：locked orthographic camera、head-to-toe framing、neutral studio floor、single matte-white
  articulated geometric mannequin、无文字、无音频。
- Target Provider/model/mode：`volcengine_ark_seedance` /
  `doubao-seedance-2-0-mini-260615` / `reference_to_video`。
- Reference job：只 transfer 动作节奏、肢体轨迹、站位与固定机位；不得 transfer 白模材质、方块
  比例、neutral background 或 silence。
- Remote submit ceiling：本 corrected task 最多一个 target POST；没有 retry 或 fallback。由于
  materialization preflight 未通过，实际 POST 为 `0`。

## Blender MCP Execution

正式 run 为 `runs/seedance-blender-white-model-r2v-20260917-001/`。

MCP status 证据确认 addon 与 server protocol 一致，并暴露 `execute_blender_code`、
`get_scene_info`、`get_object_info` 与 viewport screenshot 等能力。建模与渲染代码通过
`execute_blender_code` 进入 Blender，不是以 headless CLI authoring 冒充 MCP control。

第一版 diagnostic render 暴露人物 framing 缺陷：抬臂后人物偏左，头顶和脚部被裁切。随后只调整
orthographic camera framing，并重新执行 MCP create/render。最终 source：

- `.blend`：`runs/seedance-blender-white-model-r2v-20260917-001/source/white-model-motion.blend`
- `.blend` SHA-256：
  `ae4d1cbd4416d0cb988020862ac43019ba82185c2edecc98b7501084b504113d`
- MP4：`runs/seedance-blender-white-model-r2v-20260917-001/source/white-model-motion.mp4`
- MP4 SHA-256：
  `b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1`
- measured bytes：`58,505`
- measured media：H.264 High、`1280x720`、`yuv420p`、24fps、120 frames、`5.000s`、无音轨
- source contact sheet：
  `runs/seedance-blender-white-model-r2v-20260917-001/evidence/source-contact-sheet.jpg`
- contact-sheet SHA-256：
  `ce826a425421c4e543510c0f47bd5e53a97cd643de8ffa8735e13fe94f5aaa2d`

Blender Agent Studio fresh-process inspection 报告 `hard_gate_pass=true`，没有 asset issue，并确认
`HeadTurnPivot`、`RightShoulderPivot`、`TorsoTurnPivot` 三条 action 覆盖 frame 1-120。标准 multiview
与 critical-frame evidence 位于 `evidence/multiview/`。

## Exact-Byte Source Gate

project-local `video-analysis` 对 exact MP4 的 probe、scene detection 与 sampled-frame review 均已执行。
`evidence/local-source-gate.json` 的 required findings：

| Required finding | Verdict | Exact evidence |
| --- | --- | --- |
| `technical_output` | `PASS` | exact MP4 可解码；H.264 High、`1280x720`、24fps、120 frames、`5.000s`、无音轨。 |
| `white_model_subject` | `PASS` | critical frames 均为单个 matte-white articulated geometric mannequin 与 neutral studio floor。 |
| `motion_sequence` | `PASS` | frame 1/48 hold；frame 84 完成 subject-right arm raise；frame 120 保持抬臂并完成 subject-right torso/head turn。 |
| `fixed_full_body_camera` | `PASS` | head、hands、feet、全部肢体、floor contact 与 headroom 在四个 critical frames 中持续可见。 |
| `no_text_or_cuts` | `PASS` | scene detection 为 1 scene；visual inspection 未见文字、字幕或 logo。 |
| `reference_readiness` | `PASS` | exact local MP4 可作为 motion-only reference；本结论不证明 Provider transport acceptance。 |

## Historical Project API Materialization Blocker

Current code 只实现两条 Seedance video-reference lane：

1. `SeedanceAssetMaterializationReceipt -> SeedanceAssetReferenceResolver -> asset://...`，要求 exact
   local binding 已由 Ark Console `Active` asset 和 human-observed confirmation evidence 封存。
2. `RemoteMediaMaterializationReceipt -> SeedanceRemoteReferenceLease -> exact HTTPS locator`，仅接受
   Seedance 自己已 fetch 的 provider output，并要求 current active source、one-use refresh permit、
   locator origin/expiry 与 exact bytes revalidation。

Current runtime 没有 local MP4 object-storage upload、Ark `CreateAsset` automation、general Files API、
presigned URL publisher 或另一条可把本次 Blender bytes 物化为受支持 identity 的 canonical path。
登录状态、Experience 临时上传、本地 path 或任意 public URL 都不能替代 receipt，也不能绕过
`SeedanceVideoProvider` 的 exact resolver type checks。

因此本轮以 `BLOCKED_BEFORE_PAID_SUBMIT` 停止：

- Ark/Seedance upload：`0`
- Seedance generation POST：`0`
- poll/fetch：`0`
- Provider MP4：`NONE`
- candidate/activation/P6/Final Acceptance：`NONE`
- outcome unknown：`false`
- blind retry/fallback/browser generation submit：`false`

这不是“Seedance Mini 拒绝白模”的 empirical verdict；它是当前项目缺少 exact local-video
materialization seam 的 deterministic blocker。

## Historical Materialization Implementation Checkpoint

`src/ai_video/production/seedance_local_video.py` 已增加显式的非身份视频 lane：

- exact preview 绑定 source asset/revision/SHA/size/MP4 metadata、目标 Provider/model/request hash、
  对象存储 scope/bucket/object-key hash、credential reference 与有限 expiry；
- human actor 只授权本次 upload/cloud egress，不是人物身份、liveness 或 trusted-person attestation；
- durable-intent validator 签发一次性 materialization permit，PUT 前立即消费；
- Volcengine TOS PUT 必须返回 ETag 与 `x-tos-version-id`；GET readback 逐字节重验
  SHA/size/MIME/ISO-BMFF，上传后不确定结果 fail closed 且不能复用 permit；
- HTTP transport 只接收已经校验并保留的 exact bytes，不按 pathname 二次打开，避免 permit 后
  source swap；durable receipt 只保存 URL/ETag hash，raw presigned URL 不进入 model/repr；
- 最多五分钟的 process-local lease 精确绑定同一 receipt，`SeedanceVideoProvider` 在 resolve 与
  paid permit 消费前都重验 request/model/input hash 与 lease freshness。

离线 focused verification 为 `129 passed`：

```text
python -m pytest -p no:cacheprovider \
  tests/test_production_seedance.py \
  tests/test_production_seedance_local_video.py -q
```

覆盖 Mini `reference_video` payload、source drift 在 upload 前阻断且不消费 permit、permit 后 path swap
不能改变 upload bytes、readback mismatch 进入 unknown 并阻断 retry、跨 request materialization 在
Provider effect 前拒绝，以及 signed URL 不进入 durable receipt/repr。以上均为 fake transport；没有
发生 object-storage PUT/GET 或 Seedance POST。

当时唯一 live pre-submit blocker 是缺少与 exact preview 一致的受控对象存储 presigned PUT/GET grant：
repository/host 没有 TOS/S3 credential reference、presigner 配置或可调用的 materialization MCP。
登录状态不能补足该 grant；匿名临时 host、browser upload、local path 与伪造 URL 继续禁止。

## Live Materialization And Seedance Execution

用户开通 TOS 后，browser-authenticated Volcengine Console 只负责签发短期 private-object grant；signed
URLs 与 browser STS credential 均未写入 repository、receipt、日志或 prompt。项目 materializer 在
Provider submit 前完成：

- Registry source asset：`blender-white-model-motion`，active Registry revision
  `c47af7a288979faf733aadc3a3c4defe70bc6c2c13ea4530d57e2eedc15d4540`；
- materialization receipt：
  `runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/materialization-receipt.json`；
- receipt content hash：
  `bd8ff5cf6fccdaae1f0f0a745d7ddeb2cbab70c269ef95c037600108cd2ef25c`；
- TOS version ID：`5607A80F01B0F42D3C43`；
- uploaded/read-back bytes：`58,505`；readback SHA-256 与 source 同为
  `b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1`。

Sealed execution identity：

- model：`doubao-seedance-2-0-mini-260615`；
- mode：`reference_to_video`；
- request fingerprint：
  `9c5eb5b2af4a74c2d2d64b5335a145983729574342b640ea15660011903ea8d2`；
- paid preview fingerprint：
  `5d834cbcccc3a116572d753c2c587b58f90f679bb63645064d6507bef3050a2a`；
- submission fingerprint：
  `7be0f3b40db00492beb892754e6291a5bb32574da83aedfb6b5e88b64a917fb3`；
- exact counters：`submit_posts = 1`、`query_gets = 12`、`download_gets = 1`、
  `blind_retries = 0`、`provider_fallbacks = 0`。

Provider output：

- path：
  `runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/output/seedance-mini-stylized-robot-motion-transfer.mp4`；
- SHA-256：
  `127b435cef282fe2b297929013e813e667f1b30b50d1046da0cc043eb2bfc674`；
- size：`1,762,880` bytes；
- measured media：H.264 High、`1280x720`、24fps、121 frames、`5.042s`、无音轨。

这次 target 是明确非真人的 blue-orange mechanical service robot。结果保留 source 的动作轨迹与
固定全身机位，没有把 white material、blockout appearance 或 black studio 当成 target appearance。

## Post-Media Gate And Canonical Activation

project-local `video-analysis` MCP 对 exact output 执行 `video_probe`、`video_analyze`、
`video_review`、`video_scene_detect` 与 `video_extract_frames`。随后对 exact bytes 生成 4fps、20-frame
contact sheet，并逐项判定：

| Required finding | Verdict | Exact evidence |
| --- | --- | --- |
| `technical_output` | `PASS` | H.264 High、`1280x720`、24fps、121 frames、`5.042s`、无音轨。 |
| `non_human_robot_subject` | `PASS` | 全部 sampled frames 为 blue-orange mechanical robot；无 skin、human face 或 photorealistic person。 |
| `source_motion_transfer` | `PASS` | 双臂下垂起始，单臂连续抬升至水平，并保持终态；与 source motion sequence 一致。 |
| `fixed_full_body_camera` | `PASS` | camera 固定；head-to-feet 在 sampled frames 中持续可见。 |
| `source_appearance_not_inherited` | `PASS` | white block mannequin 与 black studio 被 robot/workshop target appearance 替换。 |
| `robot_geometry_integrity` | `PASS` | 20-frame sampling 中 head、torso、arms、hands、legs、feet 与 joints 稳定，无 duplication/disappearance/gross deformation。 |
| `no_text_or_cuts` | `PASS` | scene detection 为 1 scene；未见文字、字幕、logo 或 watermark。 |
| `audio_policy` | `PASS` | sealed request 禁用 generated audio；exact candidate 无 audio stream。 |

Gate receipt：
`runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/post-media-gate.json`，
SHA-256 `dae62a7112f4abc587e7bc97ec361c9072aa1121e825c687870b300e97eef2cd`。

Gate PASS 后，canonical committer 将同一 exact output 作为
`blender-white-model-mini-r2v-output` 激活。最终 state：

- Manifest revision：`27`；
- attempt：`blender-white-model-mini-r2v-attempt`；
- attempt status：`succeeded`；
- video phase：`activate`；
- active output SHA-256：
  `127b435cef282fe2b297929013e813e667f1b30b50d1046da0cc043eb2bfc674`；
- activation report：
  `runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/activation-report.json`。

Activation 没有新增 Provider POST。Post-media Gate 是 task-scoped Development evidence；其 4fps
sampling 与 MCP analysis 不构成 P6 或 Final Acceptance，也不代表所有白模、动作、prompt 或 Mini
request 都会获得同等结果。

## Assessment

用户纠正的 Blender-first path 已完整走通：Blender MCP authoring -> exact local source Gate -> private
TOS materialization/readback -> AI-VIDEO project API Seedance Mini R2V -> exact fetch -> post-media Gate ->
canonical activation。它直接回答了本次 bounded question：该 Provider/model path 可以接受这份 exact
synthetic white-model MP4 作为 motion reference，并产出非真人 stylized robot motion transfer。

本结论只绑定 source SHA、request fingerprint、model version、output SHA 与本次 one-POST evidence。
它不能扩张成“所有 provider 都接受白模”，也不能把 Development Gate PASS 提升为 production quality
qualification。TOS bucket/object 仍为 private live resource；本记录没有授权或执行删除。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blender-mcp-white-model-source | blender-mcp:white-model:b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | seedance-blender-white-model-r2v-20260917-001 | blender-mcp-white-model-source-attempt | local-source | b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | LOCAL_MCP_AUTHORING_AND_EXACT_MEDIA_GATE | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-blender-white-model-r2v-20260917-001/evidence/local-source-gate.json |
| seedance-mini-local-video-materialization | blender-mcp:white-model:b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | seedance-blender-white-model-r2v-20260917-001 | blender-mcp-white-model-source-attempt | local-source | b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | PROJECT_API_MATERIALIZATION_PREFLIGHT | BLOCKED | LOCAL_VIDEO_MATERIALIZER_NOT_IMPLEMENTED | SAME_EVIDENCE_NEW_PROOF_LAYER | blender-mcp-white-model-source | runs/seedance-blender-white-model-r2v-20260917-001/evidence/materialization-preflight.json |
| seedance-mini-local-video-materializer-checkpoint | blender-mcp:white-model:b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | seedance-blender-white-model-r2v-20260917-001 | blender-mcp-white-model-source-attempt | local-source | b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | PROJECT_API_MATERIALIZATION_IMPLEMENTATION | BLOCKED | CONTROLLED_OBJECT_STORAGE_GRANT_MISSING | CONCLUSION_SUPERSEDED | seedance-mini-local-video-materialization | tests/test_production_seedance_local_video.py |
| seedance-mini-live-materialization | tos-materialization:bd8ff5cf6fccdaae1f0f0a745d7ddeb2cbab70c269ef95c037600108cd2ef25c | seedance-blender-white-model-r2v-20260917-001 | blender-white-model-local-materialization | target-r2v | b4cdb2a778390599eeff069c215486105b34170935a1297e45cecc010361b0b1 | LIVE_TOS_PUT_EXACT_READBACK | PASS | NONE | CONCLUSION_SUPERSEDED | seedance-mini-local-video-materializer-checkpoint | runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/materialization-receipt.json |
| seedance-mini-r2v-fetch | seedance-mini-r2v:9c5eb5b2af4a74c2d2d64b5335a145983729574342b640ea15660011903ea8d2 | seedance-blender-white-model-r2v-20260917-001 | blender-white-model-mini-r2v-attempt | target-r2v | 127b435cef282fe2b297929013e813e667f1b30b50d1046da0cc043eb2bfc674 | PAID_PROVIDER_SUBMIT_POLL_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/live-report.json |
| seedance-mini-r2v-post-media-gate | seedance-mini-r2v:9c5eb5b2af4a74c2d2d64b5335a145983729574342b640ea15660011903ea8d2 | seedance-blender-white-model-r2v-20260917-001 | blender-white-model-mini-r2v-attempt | target-r2v | 127b435cef282fe2b297929013e813e667f1b30b50d1046da0cc043eb2bfc674 | AGENT_PER_SHOT_POST_MEDIA_GATE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | seedance-mini-r2v-fetch | runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/post-media-gate.json |
| seedance-mini-r2v-activation | seedance-mini-r2v:9c5eb5b2af4a74c2d2d64b5335a145983729574342b640ea15660011903ea8d2 | seedance-blender-white-model-r2v-20260917-001 | blender-white-model-mini-r2v-attempt | target-r2v | 127b435cef282fe2b297929013e813e667f1b30b50d1046da0cc043eb2bfc674 | CANONICAL_CANDIDATE_ACTIVATION | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | seedance-mini-r2v-post-media-gate | runs/seedance-blender-white-model-r2v-20260917-001/live-r2v-005/evidence/activation-report.json |

## Learning Evaluation

`distill-ai-video-learning`: `no_candidate`。本次 live materialization、Provider fetch、post-media
Gate 与 activation 是同一 bounded execution chain 的不同 proof layers，不是两个 independent Provider
attempts，也不是 controlled multi-arm comparison。历史 Mini/2.5 white-model runs 的 source owner、target、
prompt、mode 或失败阶段不同，无法隔离“Blender white-model reference 可稳定迁移动作”这一变量；因此
不把单次成功扩张成 model-wide、provider-wide 或 workflow-wide Learning Claim。

## Agent Guardrails

- 不得回到 Seedance T2V 生成白模；这不是用户当前 intent。
- 只有本次 exact live materialization + Provider receipt 证明 Seedance input acceptance；不得从 Blender
  MCP/local Gate 单独推导。
- 不得用 Experience page generation、匿名临时 host、local path 或 local Registry ID 绕过 project API
  materialization contract。
- 不得伪造 human-observed `Active` Ark asset receipt，或把 login state 当成 materialization evidence。
- Provider `succeeded` 不等于 quality acceptance；本次激活依赖 exact MP4 post-media Gate PASS。
- 本次 task-scoped submit ceiling 已耗尽；不得把授权复用于 retry、variant、benchmark 或其他 model。
