---
record_kind: media_experiment
topic_id: h3-t8-drama-prompt-audio-adherence
learning_eligibility: eligible
evidence_index_version: "1"
---

# H3 T8 Drama Preview Shot Gate Stop Record

Date: 2026-08-29

## Purpose

记录一次本地 MiniMax H3 T8 30 秒剧情预览的真实执行边界。该任务从先前仅完成 authoring、没有媒体输出的 `Key at the Waiting Room` 场景派生出 6 个 Development Shot；逐 Shot Gate 在第一个 5.17 秒 MP4 上发现明确音频与硬字幕违约，因此按顺序执行契约在 Shot 2 submit 前停止。

本记录证明一次 local Provider 输出与一次 exact-bytes Gate 结果，不证明 30 秒成片已生成，不产生 P6、Final Acceptance、candidate activation、release 或 Production quality truth。

## Current Runtime Truth

- Run root：`runs/drama-h3-t8-30s-preview-20260829-v1/`。
- 计划为 6 个 `124 / 24 = 5.1667s` Shot，raw concat 31 秒后 trim 至 30 秒；由于 Shot 1 Gate 为 `FAIL`，Shot 2–6 均未 submit，final assembly 不存在。
- Shot 1 exact output：`runs/drama-h3-t8-30s-preview-20260829-v1/outputs/shot-01.mp4`。
- Shot 1 SHA-256：`d33a3de37ecccb369dd13cd0f043a80a2700882cf4428b16c89543a67d222cc9`。
- Shot 1 request 仅 submit 一次；`provider_submit_count_for_shot=1`，后续 Shot submit count 为零。
- Execution 为严格 loopback local ComfyUI，无 remote/cloud egress、无 paid Provider call。
- ComfyUI 在执行后停止，`127.0.0.1:8188` 不再监听；checkout 已恢复到启动前的 `e01fb4c56b7a88149d469b99cbbfe3223d715054`。

## Exact Request And Runtime Boundary

`runs/drama-h3-t8-30s-preview-20260829-v1/sidecars/exact-preview.json` sealed 以下 Development execution identity：

- profile：`minimax_h3_t8_t2va_quality`
- profile content hash：`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`
- workflow SHA-256：`6a508f8522694297c2e3ce1157dd1b235cd34514d85bf3c2908f55020cd990a5`
- binding SHA-256：`3af2ab9928d832253e22aaf14f47bf70ef80949f56a1664817accb8acacfd564`
- ComfyUI commit：`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`
- Shot 1 requirement hash：`91f6e7b3cd64b17232933ca2c07b2ded9b6668f375e91fd8c5d109f5bad41f47`
- Shot 1 resolved generation hash：`2e96cce84eaddf5536596a2d0aa74bc5db6856f41ef2b7b6f38f1dc9a3988602`

Exact preview 同时绑定了本次实际加载的 Production source hashes。当前 repository 的 unrelated dirty changes 不是该媒体证据的隐式组成部分；后续重放必须重新 seal current source/runtime identity，不能只复用文件名或本记录。

## Verification And Evidence

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

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| h3-t8-drama-shot01-gate-20260829 | local-comfyui:h3-t8:drama-prompt-audio-adherence:20260829 | drama-h3-t8-30s-preview-20260829-v1 | drama-preview-shot-01-entry-submit-1 | t2va-quality | d33a3de37ecccb369dd13cd0f043a80a2700882cf4428b16c89543a67d222cc9 | EXACT_MEDIA_GATE | FAIL | UNINTENDED_NARRATION_AND_BURNED_SUBTITLES | NEW_ATTEMPT | NONE | `runs/drama-h3-t8-30s-preview-20260829-v1/sidecars/gates/shot-01-gate.json` |

## Assessment

该输出在基础画面可读性上有效：两个人物、左右轴线与入场动作清楚，画面稳定，适合作为失败样片查看。但它不满足本镜最关键的 audio/dialogue/字幕 contract，也不能作为后续连续性判断的已接受前序状态。

现有 evidence 支持的最窄结论是：在该 exact T2VA request 中，传入 H3 的剧情/目标说明泄漏为模型生成的中文旁白和硬字幕。仅凭一次 output 不能判定这是模型固定行为、prompt compiler 的普遍缺陷，或所有 H3 T8 drama request 都会失败；任何修复或重试都必须作为新的、单变量、exact attempt，并重新经过 Shot 1 Gate。

## Remaining Risks Or Next Work

- 用户要求的 30 秒视频未完成；当前可查看 artifact 只有失败的 Shot 1。
- 不得自动提交 Shot 2，也不得将 6 个未 Gate 的片段拼成伪 30 秒结果。
- 若继续，最小 repair target 应隔离“剧情背景文本进入 native speech / burned subtitle”的变量，并保留现有画面、轴线、时长、profile 与本地执行边界；repair 仍需新的 exact preview、one-use submit 与逐 Shot Gate。
- 当前没有人类 subjective acceptance；本记录只保存 exact technical/media evidence。

## Agent Guardrails

- `video-analysis` tool success 不等于 Gate PASS；必须映射每个 required finding。
- `AAC stream exists` 不等于 `rain-only native audio`。
- 一个可观看的 5.17 秒 Shot 不等于 30 秒 composition，也不等于 Production candidate。
- Gate `FAIL` 后不得自动 retry、remint permit 或提交下一 Shot。
- `runs/` 下 artifact 为 local-only、ignored evidence；本记录被 checkpoint 也不发布媒体 bytes。
