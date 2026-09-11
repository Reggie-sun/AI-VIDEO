---
record_kind: session_summary
topic_id: jieshi-s06-first-frame-preparation
learning_eligibility: ineligible
---

# S06 First-Frame Preparation

## Superseding Generation Result

用户随后回复“可以”，批准本记录所述首帧用于 S06。已通过既有 Planner/Router/compiler、paid gates 与 canonical lifecycle，以 `viduq3-pro` I2V、6秒、1080p、`audio=true` 完成一次 submit 和一次 fetch；task ceiling1/used1。本节取代下文历史 checkpoint 的“尚未提交”和“待首帧确认”状态。

Exact MP4：`runs/jieshi-e01-i2v-20260907-attempt10/production-s06-v1/state/video-generation/fetch/files/62edbc87c2df450292832ce446dfa4e749c67cc908ffe43f7bd7576ffb5659cd.mp4`；SHA-256 同文件名，5,050,079 bytes。project-local `video-analysis` MCP probe 检出6.042秒、1080×1920、24fps、145帧、H264及AAC 48kHz stereo音轨。音轨存在不等于广播要求通过。

Post-media Gate **FAIL**：exact MP4 的 MCP 抽帧在3秒和6秒显示模型生成的屏幕文字；3秒另出现未要求的屏幕图形，违反 `s06-no-generated-text` 的干净屏幕要求。不是仅仅“精确文字尚待合成”，不能当作合格原始素材交付。Whisper base 与 small 均只转写出两段，未证实三次完整报站及指定时窗；同音转写差异本身不证明发音错误。其余需要连续正常速度声画人审的要求为 `NOT_EVALUATED`，holistic human verdict 为 `UNDECIDED`，不得以抽帧代替整体人审。下一 Shot 被阻断，未 activation、未 P4/Final Acceptance、未追加 submit。

Evidence 位于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s06-v1/`：`s06-task-authorization.json`、`s06-live-events.jsonl`、`fetch-dns-evidence.json`、`s06-attempt01-probe.json`、`s06-attempt01-review.json`、`s06-attempt01-frames.json`、两份 `s06-attempt01-transcript-*.json` 和 `s06-attempt01-post-media-gate.json`。Gate 绑定 QA hash `197b9ef7b9f6b8faeca91a384da4c9576d28953e6da28389ec7beb6df959a361`，并引用 S05 已接受的前序 Gate。下载沿用有界 GET-only 公开 DNS 解析，保留原 hostname、SNI 与 TLS 校验。

通过 standard loader 重开当前项目并校验 exact MP4 SHA；S03/S04/S05 Manifest 实测 hash 均未改变。准备时 focused tests 为106 passed（命令与 helper hashes 见 `s06-preparation-verification.json`，其中 `PREVIEW_READY_NO_SUBMIT` 是提交前历史快照）；native `reviewer_xhigh` pre-submit verdict 为 accept with concerns，未替代当前媒体 Gate。无产品 source change；无 fresh exact Harness closure，policy audit 仍受已有 unmapped paths 阻断。自动 `distill-ai-video-learning` 评估 `no_candidate`：单次失败样本不足以建立跨实验或 Provider-wide claim。已耗尽本次有限付费提交授权；进一步生成需要新增有界授权。

## Outcome

用户要求生成 S06，随后明确确认 S05“通过”。本轮保存 S05 exact raw human acceptance，完成 S06 新机位首帧候选；尚未导入 S06 图片或提交视频。

S06 为6秒“报站重复”：林砚放下左手看屏幕，前两次画外广播“下一站，临江路。”，第三次“下一站……林砚。”；笑意消失，末态视线滑向陈立。依创作包 Audio Production Policy，准备优先生成原生广播与环境声。逐字、同音色、时窗和表演仍需实际 MP4 验证，不以打开音轨代替。

## Evidence

- 使用 strict `load_production_project()` 重开 `production-s05-v1`，定位 approved registered S05 first-frame：`image-import-b3b83fba68d003a4374f8daaf482a5fad6cd9479356d8dbf29fa91061e8eda51`、SHA-256 `d3be37aed9166fa06b7df968c3f8ce76ad63d273feff4040131604b167c5c23f`；参考 Shot `jieshi-e01-S05` revision2、hash `a0a7774dac865ec314fc7a65413915da0b5fb9343c76771fd4c6f04c4d1f34af`。参考为 registered image，不是视频截图。
- 一次内置 `image_gen.imagegen` 编辑，用新机位显示林砚侧脸与门上电子屏。屏幕有意留白，遵守原分镜的精确文字独立图层路线；此候选不等于已完成“下一站：临江路”的成片屏幕效果。未声明该层已 materialize/render。
- Prompt、`source-reference.json`、`first-frame-result.json` 与 `s06-first-frame-candidate-v1.png` 保存于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s06-v1/`；result 记录实测 SHA/尺寸及三段广播窗口。无 Provider POST、ceiling1/used0。
- `retrieve-ai-video-memory` experience 查询返回 stale advisory fragments，未用历史结果授予当前质量 PASS。当前事实来自分镜、Audio Production Policy、exact S05 MP4 hash 与用户人审原话。

## Remaining Boundary

新 S06 PNG 仍需用户确认后才能满足 `HumanImageImportReceipt` 的 human approval/time ordering；S05 人审不自动覆盖之后才生成的图片。后续沿现有 Planner/Router/compiler/Provider seam 封装，不声称已运行 Router 或本轮已生成 S06 视频。

## Verification And Learning

已检查图片可读性、实测尺寸与 SHA、S05 exact MP4 和 source standard loader。无产品 source 改动；不声称 fresh Harness closure、音频或成片验收。按 `record-ai-video-session` 保存稳定准备 checkpoint；`distill-ai-video-learning` 评估 `no_candidate`：单张未获人审的候选不满足跨实验 claim 阈值，不创建 placeholder。保留其他 staged/dirty work。
