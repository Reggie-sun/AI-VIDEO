---
record_kind: media_experiment
topic_id: drama-m6-d-shot-01-first-generation
learning_eligibility: eligible
evidence_index_version: "1"
---

# Drama M6-D Shot 01 First Generation Record

Date: 2026-09-06

## Purpose

本文封存canonical `Key at the Waiting Room` Shot 01首次真实local H3/T8 generation、exact fetched MP4与紧随其后的
project-local `video-analysis` evidence repair。它取代request-readiness记录中`STOP_BEFORE_SUBMIT`的current-facing状态，
但不产生HUMAN Drama verdict、Shot 02 authorization、candidate activation、P6或Final Acceptance。

## Current Runtime Truth

Versioned v5 invocation通过current canonical source-binding、Router/profile/workflow、runtime checkout与
`VideoGenerationService` lifecycle只提交一次：

- attempt：`drama-shot01-first-20260906-v5`；
- first-submit approval：
  `docs/superpowers/artifacts/drama/b-d0/first-submit/key-at-the-waiting-room-shot-01-v5.accepted.json`，SHA-256
  `163324e9530bbb4c44f6b9401f5fdda1fbebf5fa1b1b10c6cfd08a0c040e3630`；
- driver：`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_first_submit_v5.py`，SHA-256
  `56d0754be372d9cedd7b3521aeae12cad5aba655b74315b973ff9ff984c38a97`；
- Provider/model：`comfy-local-h3-t8` / `minimax-h3-t8-t2va-quality`；profile
  `4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`；workflow
  `6a508f8522694297c2e3ce1157dd1b235cd34514d85bf3c2908f55020cd990a5`；binding
  `3af2ab9928d832253e22aaf14f47bf70ef80949f56a1664817accb8acacfd564`；
- runtime：ComfyUI `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`、T8
  `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`、VideoHelperSuite
  `4ee72c065db22c9d96c2427954dc69e7b908444b`、SageAttention `2.2.0`；
- exact compiled prompt SHA-256：`e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47`；
- Provider request ID：`3f56e4f0-c8d1-447d-9e25-020498756cf1`；terminal state `succeeded`；
- exact media：
  `runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/production-project/state/video-generation/fetch/files/264a4857ed7bd279c9fc528b78d59d55fc8747c128bdf9b2f68ff6e9ea745c36.mp4`，
  SHA-256 `264a4857ed7bd279c9fc528b78d59d55fc8747c128bdf9b2f68ff6e9ea745c36`，`1,724,778` bytes。

The output is `5.167s`, H.264 High `1344x768`, `24fps`, `124` frames, `yuv420p`, with AAC `32kHz` stereo native
audio。本attempt使用1次Provider submit、1个GPU job、0 retry；没有remote egress、Shot 02 submit或activation。

## Per-Shot Gate Evidence

综合`video_analyze`首次返回在client context boundary被截断；按`EVIDENCE_REPAIR_FIRST`只对相同exact MP4执行分拆
`video_probe`、`video_extract_frames`、`video_scene_detect`、`video_transcribe`与`video_review`，没有重生成媒体。
Run-local raw evidence：
`runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-first-20260906-v5-media-gate-v1.json`，
SHA-256 `0cce35bfeb7098fd620c0020ca061af8406fdd3b8ea0ab9108e79d34f43f1e3f`。

Current supporting evidence：

- probe与independent `ffprobe`一致；exact bytes可解码并包含预期video/audio streams；
- scene detection只观察到一个`5.167s` scene；`video_review`报告audio present、estimated speaking duration `2.4s`且
  没有tool-reported issue；它同时报告`166/166` unique sampled frames，与probe的`124` encoded frames矛盾，故该metric只保留为
  raw tool output，不进入Gate结论；
- 0.000–4.550s的8个MCP sampled frames保持locked medium-wide、林岚screen-left seated、林峻screen-right、
  单一钥匙举起并在终点可见；
- exact `0.000s` sample在screen-right doorway极边缘已出现林峻部分身体/面部，而sealed open要求doorway empty；这是
  HUMAN blocking review必须判断的material concern；
- Whisper识别为`要是还在 / 回去 / 一起开门`，语义覆盖目标三段，但同音词不能证明逐字“钥匙”，分段从
  `0.000s`延伸到`5.080s`，也不能证明speaker/lip-sync或sealed `1.700–3.900s` delivery window。

Independent native `reviewer_xhigh`重开final raw evidence、execution sidecars、Manifest、exact MP4、blocked envelope与
current-facing docs后给出`accept`，无blocking issue或non-blocking concern；review未重放Provider、media或`video-analysis`。

因此mandatory technical barrier保持`NOT_EVALUATED`：identity/decode/single-scene层已通过，但generated-audio route要求的
dialogue semantics、speaker binding与lip-sync没有credible complete evidence。五项required
`DRAMA-MEDIA-SHOT-*`均由HUMAN authority判定；当前没有full-length `1.0x` full-audio playback attestation，全部保持
`NOT_EVALUATED`。Gate envelope：
`docs/superpowers/artifacts/drama/b-d0/per-shot-media-gate/key-at-the-waiting-room-shot-01-v1.blocked.json`，SHA-256
`675b81d59ca60f1551a493523327dea454892772537f9fac6fd59e41a6054bd5`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drama-shot01-v5-provider-result | drama-shot01-first-20260906-v5 | drama-m6-d-shot01-first-generation | drama-shot01-first-20260906-v5 | N/A | 264a4857ed7bd279c9fc528b78d59d55fc8747c128bdf9b2f68ff6e9ea745c36 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-first-20260906-v5-fetched.json |
| drama-shot01-v5-technical-gate | drama-shot01-first-20260906-v5 | drama-m6-d-shot01-first-generation | drama-shot01-first-20260906-v5 | N/A | 264a4857ed7bd279c9fc528b78d59d55fc8747c128bdf9b2f68ff6e9ea745c36 | ANALYZER | NOT_EVALUATED | REQUIRED_AUDIO_SEMANTICS_SPEAKER_LIPSYNC_NOT_ESTABLISHED | SAME_EVIDENCE_NEW_PROOF_LAYER | drama-shot01-v5-provider-result | runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/drama-shot01-first-20260906-v5-media-gate-v1.json |
| drama-shot01-v5-human-gate | drama-shot01-first-20260906-v5 | drama-m6-d-shot01-first-generation | drama-shot01-first-20260906-v5 | N/A | 264a4857ed7bd279c9fc528b78d59d55fc8747c128bdf9b2f68ff6e9ea745c36 | HUMAN | NOT_EVALUATED | HUMAN_PLAYBACK_ATTESTATION_MISSING | SAME_EVIDENCE_NEW_PROOF_LAYER | drama-shot01-v5-provider-result | docs/superpowers/artifacts/drama/b-d0/per-shot-media-gate/key-at-the-waiting-room-shot-01-v1.blocked.json |

## Assessment And Next Work

Current boundary是`M6-D=NOT_EVALUATED / STOP_AFTER_SHOT_01_GATE`，不是`STOP_BEFORE_SUBMIT`。下一唯一动作是由当前用户或
playback前明确授权的HUMAN designee，以exact MP4全长、`1.0x`、full audio、primary verdict期间不scrub的方式，对以下五项
逐项给出`PASS` / `FAIL` / `NOT_EVALUATED`与简洁rationale：

- `DRAMA-MEDIA-SHOT-NARRATIVE-001`；
- `DRAMA-MEDIA-SHOT-DIALOGUE-001`；
- `DRAMA-MEDIA-SHOT-PERFORMANCE-001`；
- `DRAMA-MEDIA-SHOT-BLOCKING-001`；
- `DRAMA-MEDIA-SHOT-EMOTION-001`。

五项HUMAN finding与mandatory technical barrier未全部PASS前，`next_shot_submit_allowed=false`。Sealed v5 budget为
`retry_count=0`，当前task不得自动生成repair attempt；不得提交Shot 02、激活candidate、进入pairwise/whole-scene Gate、
P6或Final Acceptance。

## Agent Guardrails

本记录不把Provider success、MCP metrics或sampled frames转写为HUMAN Drama verdict，也不复用Commercial verdict。
Recording阶段不运行Provider、ComfyUI lifecycle、媒体生成、网络或额外tests。Session内unrelated staged Jieshi files保持未修改、
未stage到本task commit、未reset或清理。Agent Memory retrieval此前strict失败
`index library version mismatch; rebuild required`；本task未重试、rebuild或fallback，current repository/runtime evidence仍为
authoritative。Automatic `distill-ai-video-learning`评估结果为`no_candidate`：本记录只有一个
`independence_key`、没有controlled multi-arm，且本Drama attempt不构成对已采纳且明确限于lighthouse场景的
`h3-shot-local-visible-context` claim之material update；未创建placeholder或修改既有Learning Claim。
