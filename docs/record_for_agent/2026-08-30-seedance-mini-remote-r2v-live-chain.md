---
record_kind: media_experiment
topic_id: seedance-mini-remote-r2v-epic-two-shot
learning_eligibility: eligible
evidence_index_version: "1"
---

# Seedance Mini Remote R2V Live Chain Record

Date: 2026-08-30

## Review Supersession Notice — 2026-08-30

用户对原 stream-copy review derivative
`output/epic-skyship-two-shot-30s.mp4` 给出明确 `FAIL`：跨 Shot seam 明显卡顿，且成片没有声音和字幕。
该文件继续保留为历史 derivative 与失败证据，但不再是 current review artifact；此前单靠 boundary
SSIM `0.903748` 的技术描述不能代表 seam 已获人工接受。

当前 review artifact 已由同一两份 exact Provider MP4 本地确定性重组为
`output/epic-skyship-two-shot-29p79s-captioned-sound-v2.mp4`。本次修复没有重新生成 Shot、没有
Provider call，也没有改变两次 live Provider attempts、remote R2V provenance 或 Manifest activation truth。

## Purpose

本文记录 `doubao-seedance-2-0-mini-260615` 首次由 AI-VIDEO canonical remote-output materialization lane 完成的真实两 Shot live chain：Shot 1 T2V 在 exact-byte Gate PASS 后 activation，Shot 2 不经 manual Ark Asset upload、不退化为 last-frame I2V，直接复用 Shot 1 的 current remote Provider output 执行 `VIDEO_EXTEND` / R2V。

本文证明本次 bounded Mini chain 的 API acceptance、exact remote identity continuity、两段技术输出与 Agent Per-Shot Gate。它不是其他 Seedance model qualification、Provider invoice、P6、Final Acceptance、publication 或市场质量结论。

## Current Runtime Truth

Implementation checkpoint `823280e` 保留完整 remote identity 分层：

- `RemoteMediaMaterializationReceipt` durable 保存 task/model、opaque file identity、locator hash/origin、exact downloaded SHA-256、bytes、MIME、accessibility 与 fetch lineage；完整 signed URL 不持久化。
- `VideoGenerationService.refresh_remote_reference_lease_once()` 只从 Manifest exact-active source 重开 request/submit/status/fetch，并签发 one-use refresh permit。
- source request 的 `nominal_seconds=15` 被 seal 为 `15,000ms` remote-reference timing proof；physical MP4 的 `15.042s` measurement 仍由 active artifact/probe 独占，二者不互相覆盖。
- `SeedanceRemoteReferenceResolver` 只有在 binding 使用 sealed nominal duration 且 SHA/bytes/MIME/materialization/lease 全部 exact-current 时才投影 HTTPS `reference_video`。
- historical Seedance profile 仍以原 official `15,000ms` capability strict reopen；没有为了通过本次媒体而把 capability matrix 改成 `15,042ms`。

Canonical runtime docs live status checkpoint 为 `07e8e13`。Authoritative implementation receipt：

`.agent/harness/runs/seedance-remote-nominal-proof-commit-823280e/receipt.json`

该 exact commit-range receipt 为 fresh PASS：Architecture Gate `0 errors / 0 warnings`，Harness tests `204 passed`，Production video provider tests `743 passed`，provider-neutral requirement tests `360 passed`。Live docs receipt：

`.agent/harness/runs/seedance-remote-r2v-live-docs-07e8e13/receipt.json`

## Live Execution Evidence

Run root：`runs/seedance-mini-r2v-epic-skyship-20260829-002/`。

### Shot 1 — Exact Active Source

- attempt：`epic-skyship-v2-shot-01-attempt`
- mode：`text_to_video`
- request fingerprint：`442b80460a921846900de4f2f69aebb26b2f5ec389c9770723764b24b369bf86`
- artifact：`output/shot-01-seedance-mini-15s.mp4`
- SHA-256：`aff994a4ebefb9a5fd3d65d824be4f4f290cae0272ff94fe6d4765aa3338afd8`
- size：`10,069,617` bytes
- H.264 High、`1280x720@24fps`、361 frames、15.042s、no audio
- live report SHA-256：`230746feb2cd3f3f26e3c71b132674e3f5621fa0cf6caeeda394aa7816f2aaeb`
- Gate SHA-256：`abd982fa7c90bacced2a52fa65a1d776c4d7c1d6555c8903fb045ea60ccc6083`

project-local `video-analysis` MCP 与 Agent Gate 对 technical output、single ship identity、continuous motion、extendable endpoint、cinematic scale 与 forbidden elements 全部 `PASS`。该 exact candidate 随后 activation，才获得 remote refresh authority。

refresh 重新 query source task，并对相同 locator 完整 GET；复核 artifact SHA/bytes/MIME 后签发 in-memory lease。Materialization receipt ID 为 `db45c51bb599cb05f1833f19bbafb9cb7282301112815c7060086f2fe8a21d29`，locator 只记录 SHA-256 `9620b14d7e240e9c9d41f6177bbc0d176fb907153ddc1ca68a2c130be00c8f43`，未记录 raw URL。

### Shot 2 — Direct Remote R2V

- attempt：`epic-skyship-v2-shot-02-attempt`
- mode：`video_extend`
- request fingerprint：`53da0af907a055e9b807a637866b4d1edfd26d6a636bb5d85fe27d5a251f5507`
- 唯一 input：上述 lease 投影的 HTTPS `reference_video`
- artifact：`output/shot-02-seedance-mini-15s.mp4`
- SHA-256：`e33f18bc09c178703af5abfd534982d2c15ce5c48a2135dc7f4be3101eb68029`
- size：`8,582,158` bytes
- H.264 High、`1280x720@24fps`、361 frames、15.042s、no audio
- live report SHA-256：`155327b936105ed35e041563c9d7e861110eee5e35b7fa28ca33c75fa6f8f35a`
- submit audit SHA-256：`bf74e7490b4e1068e38af4f45193d4f1950c7314c430d1ddf090efae4321c4f5`
- Gate SHA-256：`2dd64751085dea8ace4d3801e835df908f6dc8ff67db5ab8249f3b0e22192e6c`

submit payload 的 sanitized audit 证明 mode 为 `video_extend`，含 exactly one `reference_video`，其 URL hash 与 source locator hash 相同；没有 Ark Asset、I2V 或 alternate Provider input。project-local `video-analysis` MCP 返回单 scene；Agent Gate 对 technical output、source identity continuity、motion continuity、cinematic scale 与 forbidden elements 全部 `PASS`。Shot 1 exact last frame 与 Shot 2 exact first frame SSIM 为 `0.903748`，视觉检查保留同一 dark-bronze crescent-prow sailship、sail silhouette、hull geometry 与 cyan-white stern light system。Shot 2 随后 activation。

### Combined Review Derivative

两份 original Provider MP4 以 stream copy 形成便于人工播放的 `output/epic-skyship-two-shot-30s.mp4`：

- SHA-256：`734ba67809b9a7036ac98ac650870da66ebefac80ac7ac59de254a3e51a57b9c`
- size：`18,607,685` bytes
- H.264 High、`1280x720@24fps`、722 frames、30.084s、no audio

该文件是 review derivative，不是第三个 Provider artifact、Manifest active asset、P6 或 final delivery activation。

用户实际播放后将其判为 `FAIL`：无声、无字幕，且硬切处明显卡顿。该 verdict 只否决这个 combined
review derivative，不回写为 Shot 1 / Shot 2 Provider artifact 或 remote R2V API execution failure。

### Review V2 — Local Seam, Audio And Caption Repair

current main review artifact：

- path：`output/epic-skyship-two-shot-29p79s-captioned-sound-v2.mp4`
- SHA-256：`5a34bf149a739959ccaa1b0953cda9f6fcf6b3275818960a104814b1f47774fa`
- size：`20,232,859` bytes
- H.264 High、`1280x720@24fps`、715 frames、29.813s
- AAC LC、48 kHz、stereo、约 255 kbps
- `volumedetect`：mean `-14.0 dB`、max `-1.0 dB`
- `silencedetect=noise=-40dB:d=0.5`：未检出连续 0.5s 以上静音

视觉 seam 使用 6 frames / 0.25s xfade，offset 为 `14.791666667s`。旧硬切 exact frame-pair
luma MAD 为 `9.893455`；修复版 encoded overlap 最大值为 `3.761`，峰值下降约 62%。移除
pre-xfade `fps=24` 后，exact 715-frame 输出的 near-duplicate frame count 为 `0`。15-frame seam
sheet 未见 double-ship ghosting：

`evidence/review-v2/seam-sheet.jpg`

音频由本地、可归因的 Mixkit BGM / ambience / whoosh / impact / shimmer assets 确定性混合；它不是
Seedance native audio，也不声称存在 Provider dialogue。字幕是四组手工编写的中文叙事字幕，以
Noto Sans CJK SC 48px、白字黑边烧录在 bottom safe area；它不是 Whisper transcription 或对白同步证明。
字幕 visual sheet：

`evidence/review-v2/caption-sheet.jpg`

project-local `video-analysis` MCP 绑定 current exact SHA-256，以 2.5s interval 采样 12 frames，返回
`has_audio=true`、threshold `0.3` 下 `scene_count=1`。Agent-side requirements 对 seam continuity、
audio presence/continuity、caption presence/legibility/safe-area 给出 `PASS`；current artifact 的用户主观
验收仍为 `NOT_EVALUATED`。完整本地 receipt：

`evidence/review-v2/gate.json`

另保留一个无 BGM、仅 ambience / SFX 的选择版本：

- path：`output/epic-skyship-two-shot-29p79s-captioned-sfx-only-v2.mp4`
- SHA-256：`c81a0f132359806676b3b39d4beb3e219baba780dcc554fec6b3a8492c418c2e`

V2 derivative 与 Gate 是同一两次 Provider evidence 的本地新 proof layer，不是独立 Provider attempt，
因此不增加下方 `Evidence Index` 的 independent evidence 数量。

## Provider And Budget Boundary

run `...-002` 只发生两个 submit POST：Shot 1 T2V 一次、Shot 2 R2V 一次。Shot 2 resume 在 local profile compatibility preflight 曾 fail closed 一次，位于 credential/network/POST 之前；修正后只消费剩余一次授权 POST。全程 blind retry `0`、Provider fallback `0`、I2V fallback `0`、manual Ark Asset upload `0`。

两个 attempts 各以 conservative upper bound `7,452,000 micro-CNY` settled，run-local total 为 `14,904,000 micro-CNY`；连同历史 run `...-001` 的一次 settled attempt，用户授权范围内累计 upper-bound basis 为 `22,356,000 micro-CNY`。这些是 local Budget Guard settlement values，不是 Provider invoice 或最终实际账单。

Manifest revision `56` 中两 attempts 均为 `status=succeeded`、`video_generation_state.phase=activate`、`paid_provider_state.phase=settled`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| epic-v2-shot01-provider-fetch | seedance-mini:442b80460a921846900de4f2f69aebb26b2f5ec389c9770723764b24b369bf86 | seedance-mini-r2v-epic-skyship-20260829-002 | epic-skyship-v2-shot-01-attempt | shot-01-t2v | aff994a4ebefb9a5fd3d65d824be4f4f290cae0272ff94fe6d4765aa3338afd8 | PAID_PROVIDER_SUBMIT_POLL_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-mini-r2v-epic-skyship-20260829-002/evidence/shot-01-live-report.json |
| epic-v2-shot01-agent-gate | seedance-mini:442b80460a921846900de4f2f69aebb26b2f5ec389c9770723764b24b369bf86 | seedance-mini-r2v-epic-skyship-20260829-002 | epic-skyship-v2-shot-01-attempt | shot-01-t2v | aff994a4ebefb9a5fd3d65d824be4f4f290cae0272ff94fe6d4765aa3338afd8 | AGENT_PER_SHOT_POST_MEDIA_GATE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | epic-v2-shot01-provider-fetch | runs/seedance-mini-r2v-epic-skyship-20260829-002/evidence/shot-01-gate.json |
| epic-v2-shot02-provider-fetch | seedance-mini:53da0af907a055e9b807a637866b4d1edfd26d6a636bb5d85fe27d5a251f5507 | seedance-mini-r2v-epic-skyship-20260829-002 | epic-skyship-v2-shot-02-attempt | shot-02-r2v | e33f18bc09c178703af5abfd534982d2c15ce5c48a2135dc7f4be3101eb68029 | PAID_PROVIDER_SUBMIT_POLL_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/seedance-mini-r2v-epic-skyship-20260829-002/evidence/shot-02-live-report.json |
| epic-v2-shot02-agent-gate | seedance-mini:53da0af907a055e9b807a637866b4d1edfd26d6a636bb5d85fe27d5a251f5507 | seedance-mini-r2v-epic-skyship-20260829-002 | epic-skyship-v2-shot-02-attempt | shot-02-r2v | e33f18bc09c178703af5abfd534982d2c15ce5c48a2135dc7f4be3101eb68029 | AGENT_PER_SHOT_POST_MEDIA_GATE | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | epic-v2-shot02-provider-fetch | runs/seedance-mini-r2v-epic-skyship-20260829-002/evidence/shot-02-gate.json |

## Assessment

这次 live evidence 支持用户的核心判断：`Ark Active asset + human confirmation` 不是 Seedance 自身生成 Shot 之间 R2V 串联的 API 硬限制；保存 remote materialization identity 并由 canonical active source 自动刷新 short-lived locator，可以直接完成 Shot N -> Shot N+1。

它同时表明 duration 需要分层，而不是二选一：physical `15.042s` 属于 exact artifact/probe truth，Provider family allowance 使用 source request sealed nominal `15.000s`；把 capability matrix 改为 `15.042s` 会破坏 historical profile strict reopen，因此已在任何 Provider effect 前拒绝并撤销。

## Remaining Risks And Next Work

- local H3/T8 output 自动上传受控 object storage、presigned URL lifecycle、cloud-egress approval 与 provider-neutral materialization proof 尚未实现；不得把 Seedance-output refresh permit 泛化为 uploader authority。
- 本次只有一个真实 Mini R2V attempt，不能自动形成 Provider-wide Learning Claim，也不能外推 Seedance 2.0 base/fast/2.5。
- Agent Per-Shot Gate、boundary SSIM 与 Review V2 local Gate 都不是独立 human P6 / Final Acceptance；用户仍需对 current V2 的电影感、配乐、字幕文案与 seam 作最终取舍。
- RAG index 未刷新；committed record bytes 不等于 retrieval index 已包含本次 evidence。

## Agent Guardrails

- `remote URL available` 不等于 durable identity；必须保留 exact hash/bytes/accessibility/provenance 并重新验证 current locator。
- nominal duration 不能覆盖 physical probe measurement；physical measurement 也不能直接改写 sealed official profile capability。
- source Provider success/fetch 不授权下一 Shot；必须先 exact-byte Gate PASS并 activation。
- combined 30s MP4 是 review derivative，不得冒充 Provider output、P6 或 final active deliverable。
- 本次记录过程没有新的 Provider call、media generation、Production mutation、push 或 release。
