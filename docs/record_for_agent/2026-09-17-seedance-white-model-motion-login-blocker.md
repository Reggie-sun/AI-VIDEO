---
record_kind: session_summary
topic_id: seedance-white-model-motion-reference-test
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Seedance White-Model Motion Reference Test Blocker Record

Date: 2026-09-17

## Supersession Notice — 2026-09-17

本记录的 browser authentication blocker 已被同日的项目 API 实验
[`2026-09-17-seedance-25-white-model-project-api-gate-stop.md`](2026-09-17-seedance-25-white-model-project-api-gate-stop.md)
取代。用户登录后明确要求不得使用网页 Experience submit，后续改走 AI-VIDEO 的
`GenerationDecisionExecutionBinding -> VideoGenerationService -> SeedanceVideoProvider`
canonical API path。该路径完成一次 Seedance 2.5 T2V submit/poll/fetch，但白模源因动作时序和
全身 framing 不满足 sealed Gate 而保持 `VALIDATE`、未激活，R2V target submit 为 `0`。

下文 local Blender reference 的 exact bytes、最初 browser 上传/登录 chronology 与当时
submit count `0` 仍是历史事实；“登录后重新走 browser submit”的 Remaining Work 已失效，
不得再作为当前 continuation 指令。

## Purpose

本文记录一次用户明确要求的 Seedance 白模动作参考测试在正式 submit 前的准备证据与真实 blocker，供后续 Agent 从同一边界继续。本文不构成 Seedance 动作迁移能力 PASS，也不构成新的 Provider 调用授权。

## Current Runtime Truth

本次目标是验证 Seedance 2.5 是否能从白色三维人偶参考视频中继承动作与固定机位，同时生成不同外观的写实虚构人物。

已准备 exact local reference：

- path: `runs/seedance-white-model-motion-test-20260917-001/white-model-motion-720p.mp4`
- SHA-256: `036c33c9bf2ae75e35e5d25d8f1c122dc026ee10369a8a86f9e57baeac62575b`
- measured format: H.264、`1280x720`、`yuv420p`、`24 fps`、`5.000 s`
- measured bytes: `298528`
- intended motion: 自然站立，逐步抬起右臂至肩高，随后躯干向右转约 20 度并保持

对应 preparation evidence 位于：

- `runs/seedance-white-model-motion-test-20260917-001/preparation/create_white_model.py`
- `runs/seedance-white-model-motion-test-20260917-001/preparation/white-model-motion.blend`
- `runs/seedance-white-model-motion-test-20260917-001/preparation/contact-sheet.png`

这些文件仅证明 reference 素材的本地 identity、格式与可视动作，不证明 Seedance 已接收、生成或成功迁移动作。

## Session Work And Decisions

1. 使用 Blender 生成中性白色关节人偶动作，并在 contact sheet 中确认全身、固定机位和动作阶段可见。
2. 初始 `768x432` MP4 在 Ark Experience 上传 UI 被客户端拒绝为不支持的分辨率；该阶段未发生 Provider generation submit。
3. 将同一动作转码为 `1280x720` H.264 后重新尝试上传。
4. Ark Experience 的 presigned-upload 请求返回 HTTP 403，同时 account metadata 请求显示未认证。页面随后停在登录 modal。
5. 未绕过 canonical Provider/console authentication，也未把素材临时公开托管以规避现有 asset/materialization boundary。

Prompt/reference authoring 已把参考视频的角色限定为 motion-only：允许继承动作节奏、肢体轨迹、站位与固定机位；明确禁止继承白色人偶外观、方块比例、材质、灰色背景与声音。本文不保存完整 raw prompt。

## Verification And Evidence

- `ffprobe` fresh measurement confirmed H.264、`1280x720`、`24 fps`、`5.000 s` and `298528` bytes for the exact SHA above.
- Final contact sheet was visually inspected after correcting the shoulder rotation axis and camera framing.
- Browser runtime selected `Doubao-Seedance-2.5` / `260628`、reference generation、`16:9`、`720P`、MP4.
- Network evidence showed the 720p reference upload stopped at unauthenticated presigned-upload acquisition with HTTP 403.
- Seedance generation submit count: `0`.
- Provider output artifact: `NONE`.
- Paid/cloud generation result: `NONE`.
- Per-Shot post-media Gate: `NOT_APPLICABLE` because no Provider MP4 exists.

## Assessment

当前 blocker 是浏览器控制台 authentication，不是已证实的 Seedance capability failure，也不是 reference MP4 的 measured codec/duration failure。登录完成后仍需重新上传 exact 720p bytes，并在仅一次 submit 的边界内生成、下载、测量和执行 project-local `video-analysis` Gate，才能回答白模动作参考是否在本次 exact attempt 中成立。

## Remaining Work

1. 用户在已打开的 Ark Experience 登录 modal 完成认证。
2. 重新上传 exact SHA-256 为 `036c33c9bf2ae75e35e5d25d8f1c122dc026ee10369a8a86f9e57baeac62575b` 的 720p MP4。
3. 复核 model/mode、reference attachment、5 秒时长、静音与 prompt role mapping 后只 submit 一次。
4. 若 outcome known 且成功，下载 exact Provider MP4，运行 `ffprobe` 并调用 project-local `video-analysis`，逐项判定动作轨迹、机位、人物外观替换、几何完整性、无额外剪辑/文字与音频要求。
5. 若 submit outcome unknown，fail closed；不得 blind retry。若单次 ceiling 已消耗且结果 FAIL，不得自行追加 paid attempt。

## Agent Guardrails

- 本记录是 blocked handoff，不是 capability PASS、candidate activation、P6 或 Final Acceptance。
- 登录态存在不等于允许扩大 Provider、model、input 或 submit count。
- 不得把 reference upload 成功等同于 generation submit 成功。
- 不得在没有 exact Provider MP4 与 post-media Gate 的情况下回答“Seedance 已能接受并正确使用白模动作”。
