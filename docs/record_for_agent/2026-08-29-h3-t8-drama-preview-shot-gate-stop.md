---
record_kind: media_experiment
topic_id: h3-t8-drama-prompt-audio-adherence
learning_eligibility: eligible
evidence_index_version: "1"
---

# H3 T8 Drama Preview Shot Gate Stop Record

Date: 2026-08-29

Updated: 2026-08-30

## Supersession Notice — 2026-08-30 Six-Shot Repair Sequence

下方 v1/v2 停止结果继续作为 historical evidence，但“30 秒成片不存在”和“最新可查看
artifact 是 V2 Shot 1”已经被后续 bounded repair sequence 取代。当前已取得 Shot 1–5
逐镜 `PASS`，并生成一个 exact `30.000s` Development assembly；但该 assembly 使用了随后
被 corrected Gate 判为 `NOT_EVALUATED` 的 Shot 6 v21，因此只能作为 invalidated development
preview 观看，不能声称 technical PASS、P6、Final Acceptance、candidate activation 或 release。

Shot 6 v21–v24 共执行 4 个新 exact attempt。四次视觉 finding 均通过，但 sealed 台词
`等你开门。` 的首音节在 Whisper `base` / `small` / `medium` 间持续冲突；v24 的 `large`
复核又因本机缓存 `large-v3.pt` SHA-256 mismatch 无法加载。4/4 task-scoped submit budget
已耗尽，current task 在 Shot 6 dialogue evidence 上形成 genuine blocker，且未开始新的 final
assembly。

## Current Runtime Truth — 2026-08-30

- accepted Shot 1 v6：`4e2775d2cdc143823c44f00ed1f276cfe62060f74239ca88312bc262d01d1315`。
- accepted Shot 2 v8：`db80d6bd0e8ec38dc9c20491a1774c3677ed5e759432cb68a70dfce5aee5f54e`。
- accepted Shot 3 v9：`ea2e5ef20342bc8a5b411efcb28509b12fc6c705b292465ef74760fadd2b2ad6`。
- accepted Shot 4 v15：`c4aea79c553b8126f69343009075ad85880ea3a82e99cf1ee71c4dc15fa321c4`。
- accepted Shot 5 v20：`f12e1b54299dc2a7c137e138b57d831ab9525d95e43766a683d8c37441b3e637`。
- latest Shot 6 v24：`runs/drama-h3-t8-30s-preview-20260830-v24/outputs/shot-06.mp4`，
  SHA-256 `28b2817a023863ba9b0553f42f14867435bf323a84b58f54d0146724d7f58ff1`；Gate
  `NOT_EVALUATED`，Gate SHA-256 `c88963427004bf21529f590d2c704c5d6a8b137fd4cce00e5b733c680b372249`。
- development preview：`runs/drama-h3-t8-30s-preview-20260830-final/outputs/key-at-the-waiting-room-development-preview-30.000s.mp4`，
  SHA-256 `8e0274db4a7f607de22cd44d435eefebe426a58d828c9401f37ac1476207f81a`。
- preview exact media facts：H.264、`1344x768`、`24 fps`、720 frames、container/video
  `30.000s`；AAC `32000 Hz` stereo、audio `29.968s`。
- final assembly Gate：`runs/drama-h3-t8-30s-preview-20260830-final/sidecars/gates/final-assembly-gate.json`，
  SHA-256 `cb73cbad091b5e82357b0a54330bec78f55785b3a4306be7e527b6cf5c75d484`，verdict
  `INVALIDATED_DEVELOPMENT_PREVIEW_ONLY`。
- 全部 generation 均为 loopback local ComfyUI，无 remote/cloud egress、无 paid Provider call。
  queue 清空后 service 已停止，`127.0.0.1:8188` 不再监听；`/home/reggie/ComfyUI`
  已恢复到 clean detached checkout `e01fb4c56b7a88149d469b99cbbfe3223d715054`。

## Current Shot 6 Evidence Boundary

v21–v24 每个 attempt 仅修改一个可归因变量：dialogue boundary timing、首字符/四音节约束、
以及首音节 `deng3` 的 phonetic anchor。四个 exact MP4 均重新调用 project-local
`video-analysis` MCP，并在提交下一 attempt 前写入 requirement-level Gate；没有把单一 ASR
总分或 tool success 当成 PASS。

v24 visually maintains the accepted state：姐姐 screen-left、弟弟 screen-right、姐姐只持一把
黄铜钥匙、长椅中央空置、locked medium two-shot 与最后两秒静止均为 `PASS`。native AAC
audio 也存在且只有一段短句。但 exact-byte transcription 分别为：

- `base`：`你開門`
- `small`：`等你开门`
- `medium`：`讓你開門`
- `large`：缓存 `large-v3.pt` checksum mismatch，model load fail closed

因此 `required_action_dialogue=NOT_EVALUATED`，v24 overall
`technical_gate=NOT_EVALUATED`。同一 failure boundary 已在 v21–v24 重复，且 4/4 submit
budget 已耗尽；继续生成需要新的明确 bounded budget，或先修复/重取 `large` evidence。缓存
文件没有被删除，canonical MCP 的 leaked worker lock 也没有通过杀进程强行清理。

## Supersession Notice — 2026-08-29 V2 Repair Attempt

下方 v1 结果继续作为 historical evidence，但其“下一步隔离剧情背景文本泄漏”已由新的
`runs/drama-h3-t8-30s-preview-20260829-v2/` attempt 执行。V2 使用 committed compiler
version `2`，排除 internal scene mood/objective/continuity bookkeeping，并让每句 typed
dialogue 在 exact native prompt 中只出现一次。V2 Shot 1 不再出现 v1 的中文硬字幕或相符
中文旁白，但 `video-analysis` Whisper `small` 仍在 no-dialogue Shot 的后段检测到一段可辨
人声样片，因此 `required_action_dialogue` 与 `native_audio` 继续为 `FAIL`，当前 batch 仍在
Shot 2 submit 前停止。

## Historical Purpose — Initial V1/V2 Checkpoint

记录一次本地 MiniMax H3 T8 30 秒剧情预览的真实执行边界。该任务从先前仅完成 authoring、没有媒体输出的 `Key at the Waiting Room` 场景派生出 6 个 Development Shot；逐 Shot Gate 在第一个 5.17 秒 MP4 上发现明确音频与硬字幕违约，因此按顺序执行契约在 Shot 2 submit 前停止。

本记录证明一次 local Provider 输出与一次 exact-bytes Gate 结果，不证明 30 秒成片已生成，不产生 P6、Final Acceptance、candidate activation、release 或 Production quality truth。

## Historical V1 Runtime Truth

- Run root：`runs/drama-h3-t8-30s-preview-20260829-v1/`。
- 计划为 6 个 `124 / 24 = 5.1667s` Shot，raw concat 31 秒后 trim 至 30 秒；由于 Shot 1 Gate 为 `FAIL`，Shot 2–6 均未 submit，final assembly 不存在。
- Shot 1 exact output：`runs/drama-h3-t8-30s-preview-20260829-v1/outputs/shot-01.mp4`。
- Shot 1 SHA-256：`d33a3de37ecccb369dd13cd0f043a80a2700882cf4428b16c89543a67d222cc9`。
- Shot 1 request 仅 submit 一次；`provider_submit_count_for_shot=1`，后续 Shot submit count 为零。
- Execution 为严格 loopback local ComfyUI，无 remote/cloud egress、无 paid Provider call。
- ComfyUI 在执行后停止，`127.0.0.1:8188` 不再监听；checkout 已恢复到启动前的 `e01fb4c56b7a88149d469b99cbbfe3223d715054`。

## Historical V1 Exact Request And Runtime Boundary

`runs/drama-h3-t8-30s-preview-20260829-v1/sidecars/exact-preview.json` sealed 以下 Development execution identity：

- profile：`minimax_h3_t8_t2va_quality`
- profile content hash：`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`
- workflow SHA-256：`6a508f8522694297c2e3ce1157dd1b235cd34514d85bf3c2908f55020cd990a5`
- binding SHA-256：`3af2ab9928d832253e22aaf14f47bf70ef80949f56a1664817accb8acacfd564`
- ComfyUI commit：`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`
- Shot 1 requirement hash：`91f6e7b3cd64b17232933ca2c07b2ded9b6668f375e91fd8c5d109f5bad41f47`
- Shot 1 resolved generation hash：`2e96cce84eaddf5536596a2d0aa74bc5db6856f41ef2b7b6f38f1dc9a3988602`

Exact preview 同时绑定了本次实际加载的 Production source hashes。当前 repository 的 unrelated dirty changes 不是该媒体证据的隐式组成部分；后续重放必须重新 seal current source/runtime identity，不能只复用文件名或本记录。

## Historical V1 Verification And Evidence

Fetched MP4 与 copied output 的 bytes identity 一致。`ffprobe` / project-local `video-analysis` MCP 对 exact output 测得：

- container：MP4；video codec：H.264 High；pixel format：`yuv420p`
- resolution：`1344x768`
- frame rate：`24 fps`；frame count：`124`
- duration：`5.167s`
- audio：AAC、`32000 Hz`、stereo
- scene detection：1 个连续 scene
- analysis：0.4 秒 interval、13 帧、Whisper `small`

Shot 1 sealed intent 要求：姐姐始终 screen-left；弟弟从 screen-right 进入并停下；钥匙不出现；locked medium-wide；无 spoken dialogue；只有稳定雨声；不得生成字幕。

Visual evidence 对人物左右位置、单一入场方向、locked framing 与钥匙不提前出现均为 `PASS`。但 exact frames 直接显示烧录字幕“林峻想证明自己会留下”与“由她决定”；Whisper 同时在约 0–4 秒转录出相符中文旁白。因此：

- `required_action_dialogue=FAIL`
- `native_audio=FAIL`
- overall `technical_gate=FAIL`
- `batch_decision=STOP_BEFORE_NEXT_SUBMIT`

逐项 finding、output hash、requirement hash 与停止决定保存在 `runs/drama-h3-t8-30s-preview-20260829-v1/sidecars/gates/shot-01-gate.json`。这不是仅由 ASR hallucination 推导的失败：硬字幕在 extracted frames 中可直接观察。

## Historical V2 Repair Attempt

- Run root：`runs/drama-h3-t8-30s-preview-20260829-v2/`。
- exact output：`runs/drama-h3-t8-30s-preview-20260829-v2/outputs/shot-01.mp4`。
- SHA-256：`139ed00ca11e9e2aca1701d13162814486cbc41982a90fea5286cbf5d9ef7a20`。
- requirement hash：`1eaccd8105cf0975745ae8194910e6c5fb27585df97ae022c87751eaee59d8d3`。
- resolved generation hash：`e280c0062d98697935727df622bfbe0187c7d16757a65a1af657716226d64266`。
- compiler version：`2`；compiled request hash：`88f9d7691e9d8ad57e689a2f11003bb7d1e37f9bbbbda027b9cb0ccdea80fe29`。
- submit count：Shot 1 一次；Shot 2–6 零次；final assembly 不存在。

Exact MP4 仍为 `1344x768`、H.264 High、`24 fps`、`124` frames、`5.167s`，并含
AAC `32000 Hz` stereo 音轨。0.4 秒 interval 的 13 帧 contact sheet 显示：女性持续
screen-left，男性从 screen-right 进入并停下，钥匙保持不可见，locked medium-wide 单镜头
稳定，画面未见硬字幕。这五类视觉 finding 均通过。

同一 `video-analysis` 调用把音轨识别为 `fr`，在 `3.88–5.52s` 返回
`Mais ahji, de ce côté même donné xan.`。这不匹配任何 sealed dialogue，且 Shot 1 明确要求
`no speech, no dialogue, no narration, and no voices`。因此 exact Gate 记录：

- `identity_wardrobe=PASS`
- `single_brass_key=PASS`
- `axis_screen_direction=PASS`
- `camera_readability=PASS`
- `required_action_dialogue=FAIL`
- `native_audio=FAIL`
- `technical_gate=FAIL`
- `batch_decision=STOP_BEFORE_NEXT_SUBMIT`

V2 finding、output identity 与停止决定位于
`runs/drama-h3-t8-30s-preview-20260829-v2/sidecars/gates/shot-01-gate.json`。与 v1
不同，V2 没有 extracted-frame 硬字幕 corroboration，也没有 human audio verdict；因此当前
只能证明 analyzer-level no-dialogue/rain-only Gate 未通过，不能把该转写扩大为模型稳定生成法语
台词或确定的人类可辨语言内容。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| h3-t8-drama-shot01-gate-20260829 | local-comfyui:h3-t8:drama-prompt-audio-adherence:20260829 | drama-h3-t8-30s-preview-20260829-v1 | drama-preview-shot-01-entry-submit-1 | t2va-quality | d33a3de37ecccb369dd13cd0f043a80a2700882cf4428b16c89543a67d222cc9 | EXACT_MEDIA_GATE | FAIL | UNINTENDED_NARRATION_AND_BURNED_SUBTITLES | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260829-v1/sidecars/gates/shot-01-gate.json` |
| h3-t8-drama-shot01-v2-gate-20260829 | local-comfyui:h3-t8:drama-prompt-audio-adherence-v2:20260829 | drama-h3-t8-30s-preview-20260829-v2 | drama-preview-shot-01-entry-submit-2 | t2va-quality-compiler-v2 | 139ed00ca11e9e2aca1701d13162814486cbc41982a90fea5286cbf5d9ef7a20 | EXACT_MEDIA_GATE | FAIL | UNINTENDED_SPEECH_ASR_ONLY_NO_BURNED_SUBTITLES | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260829-v2/sidecars/gates/shot-01-gate.json` |
| h3-t8-drama-shot06-v21-gate-20260830 | local-comfyui:h3-t8:drama-shot06-dialogue-v21:20260830 | drama-h3-t8-30s-preview-20260830-shot06-dialogue | drama-preview-shot-06-submit-v21 | v21-boundary-retranscription | 84d5d9ce51d3027e6b4d2f04e48b606d7d0dd3b04bc5b3c930b29c1c0febc5dc | EXACT_MEDIA_GATE | NOT_EVALUATED | CONFLICTING_FIRST_SYLLABLE_TRANSCRIPTION | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260830-v21/sidecars/gates/shot-06-gate.json` |
| h3-t8-drama-shot06-v22-gate-20260830 | local-comfyui:h3-t8:drama-shot06-dialogue-v22:20260830 | drama-h3-t8-30s-preview-20260830-shot06-dialogue | drama-preview-shot-06-submit-v22 | v22-dialogue-timing | 82d48e32e033f45694e102f5b4767ba1030351da6513eff4c5faa90bc00d799b | EXACT_MEDIA_GATE | NOT_EVALUATED | CONFLICTING_FIRST_SYLLABLE_TRANSCRIPTION | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260830-v22/sidecars/gates/shot-06-gate.json` |
| h3-t8-drama-shot06-v23-gate-20260830 | local-comfyui:h3-t8:drama-shot06-dialogue-v23:20260830 | drama-h3-t8-30s-preview-20260830-shot06-dialogue | drama-preview-shot-06-submit-v23 | v23-four-syllable-anchor | bc62c5cb4f560a50cf0397b24696bd644e501fdf50302b29c1d809c0575b6ab6 | EXACT_MEDIA_GATE | NOT_EVALUATED | CONFLICTING_FIRST_SYLLABLE_TRANSCRIPTION | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260830-v23/sidecars/gates/shot-06-gate.json` |
| h3-t8-drama-shot06-v24-gate-20260830 | local-comfyui:h3-t8:drama-shot06-dialogue-v24:20260830 | drama-h3-t8-30s-preview-20260830-shot06-dialogue | drama-preview-shot-06-submit-v24 | v24-deng3-phonetic-anchor | 28b2817a023863ba9b0553f42f14867435bf323a84b58f54d0146724d7f58ff1 | EXACT_MEDIA_GATE | NOT_EVALUATED | CONFLICTING_FIRST_SYLLABLE_AND_LARGE_MODEL_UNAVAILABLE | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260830-v24/sidecars/gates/shot-06-gate.json` |

## Historical Assessment Before 2026-08-30

该输出在基础画面可读性上有效：两个人物、左右轴线与入场动作清楚，画面稳定，适合作为失败样片查看。但它不满足本镜最关键的 audio/dialogue/字幕 contract，也不能作为后续连续性判断的已接受前序状态。

V2 证明 compiler-side background/objective leakage repair 消除了 v1 可见的中文硬字幕症状，但没有获得
rain-only audio PASS。由于 V2 的 residual speech finding 只有 ASR proof layer、缺少 human audio
corroboration，当前 evidence 不能证明同一 failure mechanism 仍存在，也不能把两个 attempt 合并成
“H3/T8 必然生成旁白”的 general claim。

现有 evidence 支持的最窄结论是：在该 exact T2VA request 中，传入 H3 的剧情/目标说明泄漏为模型生成的中文旁白和硬字幕。仅凭一次 output 不能判定这是模型固定行为、prompt compiler 的普遍缺陷，或所有 H3 T8 drama request 都会失败；任何修复或重试都必须作为新的、单变量、exact attempt，并重新经过 Shot 1 Gate。

## Historical Remaining Risks Before 2026-08-30

- 用户要求的 30 秒视频未完成；当前最新可查看 artifact 是 V2 失败的 Shot 1。
- 不得自动提交 Shot 2，也不得将 6 个未 Gate 的片段拼成伪 30 秒结果。
- 若继续，最小 repair target 应先对 V2 音轨取得 human-audible 或更强的 speech/non-speech corroboration，再决定是 native-audio prompt adherence 问题、ASR 对雨声的 hallucination，还是需要 separate no-dialogue audio strategy。后续仍须新的 exact preview、one-use submit 与逐 Shot Gate。
- 当前没有人类 subjective acceptance；本记录只保存 exact technical/media evidence。

## Agent Guardrails

- `video-analysis` tool success 不等于 Gate PASS；必须映射每个 required finding。
- `AAC stream exists` 不等于 `rain-only native audio`。
- 一个可观看的 5.17 秒 Shot 不等于 30 秒 composition，也不等于 Production candidate。
- Gate `FAIL` 后不得自动 retry、remint permit 或提交下一 Shot。
- `runs/` 下 artifact 为 local-only、ignored evidence；本记录被 checkpoint 也不发布媒体 bytes。
- invalidated 30 秒 Development preview 可以供人观看，但不能倒推出 Shot 6 Gate PASS；新的 final
  assembly 必须等待 Shot 6 exact current attempt 的六项 required findings 全部 `PASS`。
