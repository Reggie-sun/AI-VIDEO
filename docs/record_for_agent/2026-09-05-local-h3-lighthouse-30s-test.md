---
record_kind: media_experiment
topic_id: local-h3-lighthouse-30s
learning_eligibility: eligible
evidence_index_version: "1"
---

# Local H3 Lighthouse 30s Test — Budget Stop

Date: 2026-09-05

## Current Status

用户要求真实本地 H3 30s 视频。本次封存的 9 次生成全部完成并 fetched，但只完成五个 Shot 的 required Gate：
`shot-01-repair-01 → shot-02 → shot-03 → shot-04-repair-01 → shot-05-repair-01`。
这五段可各取 5s，即 25s 素材；尚未生成最终 30s composition。

Shot 06 的拉远、灯光和基本塔型可读，但起始与终止画面主要是灯塔上半部，未达到 sealed
`shot_scale=extreme_wide`，Gate 为 `FAIL`。不放宽原 requirement，不把五段 PASS 或第六段技术成功称为成片成功。
本 checkpoint 是 `BUDGET_EXHAUSTED / STOP_BEFORE_FINAL_COMPOSITION`，不是 Provider unknown outcome。

Run root：`runs/director-h3-lighthouse-30s-20260905-001/`。本轮 task artifacts、脚本与视频为 local ignored outputs，不进入产品源码。
旧 5.167s 测试记录 `2026-09-05-local-h3-lighthouse-director-test.md` 的独立 artifact FAIL / NOT_EVALUATED
仍有效；本次新 run 不覆盖其历史判定。

## Director And Runtime Boundary

`open-video` schema3 coverage 已实际验证：`direction`、`agent_directed`、六个 units、30s、`multi_shot`。
分镜依据因果信息与视角变化选择：暗塔与海浪、手轮动作、灯亮、雨窗扫光、海面扫光、远景收尾；
不是按“超过15s”或有无 prompt 强制拆分。

已批准的 viewpoint cuts 使用六个独立 T2VA sources，保持 bounded semantic/color/object-archetype continuity；
不声称 exact tower geometry、terminal-frame continuity 或连续单 take。没有自动切换 I2V/Ref2VA。

每个 source 使用既有 `ProductionStateCommitter` bootstrap、正式 Planner/Router/compiler3、
`VideoGenerationService.submit_local_once`、poll/fetch。Profile：
`workflows/profiles/minimax_h3_t8_t2va_quality.json`，hash
`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`。
T8 `977df788fcf8b971dc3d0fc7d6baa79a0edfaf40` / `1.36.2`；
ComfyUI `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；
VHS `4ee72c065db22c9d96c2427954dc69e7b908444b`、SageAttention `2.2.0`。
Exact request 为 quality20，未使用 Turbo LoRA，严格 loopback、无 cloud/paid call。

9 次均由 canonical service 记录 known succeeded；第一 submit 为 09:22:06 UTC，
最后 succeeded 为 10:56:51 UTC。首个预提交 draft 保留在 `preflight-shot-01/`，没有 submit，不计生成次数。
`budget.json` 限制 total9、每Shot2、elapsed14400s、GPU10800s；总次数已耗尽。
共享 ComfyUI 曾被其他任务使用；本任务未取消其他 job。停止生成时队列空，但不因记录停止共享 service。

## Media Findings And Repairs

每段 exact MP4 均调用 project-local `video-analysis.video_probe` 与
`video_extract_frames`，0–5s 每秒抽样；按 source intent 分项 Gate。后续 submit 重新绑定前序
PASS Gate 与 exact MP4 SHA-256。Probe sidecar 移除了 embedded prompt metadata。

| Shot | Initial finding | Repair variable / result |
| --- | --- | --- |
| 01 | 应保持暗灯，但初始视频已亮灯：FAIL | 移除首段未来 amber 状态泄漏，明确未亮窗室；repair PASS |
| 02 | 手轮顺时针约四分之一圈并保持，固定近景：PASS | 无补拍 |
| 03 | 正面 Fresnel lens 暗到 amber 并稳定，推近：PASS | 无补拍 |
| 04 | 扫光完成，但右摇不明显：FAIL | 增强相邻窗格的 camera endpoints 与可读幅度；repair PASS |
| 05 | 扫光完成，但灯塔建筑占左侧，违背 sea-only：FAIL | 可见 context 只留海水/礁石，将光源放在画外；repair PASS |
| 06 | 灯塔/灯光/拉远通过，但构图未达 extreme-wide：FAIL | 总预算耗尽，未补拍 |

所有九个 raw MP4 技术 probe 为 H.264 High、1344×768、24fps、124frames、5.167s、AAC 32kHz stereo；
完整 AV decode 检查通过。技术 PASS 与上表语义 finding 分开，不证明逐帧 anatomy、human full-speed
perceptual quality、精确跨镜头建筑一致性、P6 或 Final Acceptance。

Repairs 保持同 profile/mode/duration，但新 exact request 派生了新 seed；
它们是 evidence-backed bounded attempts，不是固定 seed 的受控因果比较。

## Audio And Composition State

用户同意统一后期音轨，所有 source 声明 `GENERATED + REPLACE`，同时请求 native audio=true。
Raw Gate 只证明 native route 与显式 P4 0–30s coverage 已声明，不证明最终替换已经发生。

`soundtrack.wav` 是本地原创合成 wind/surf texture 与低音持续音，非 literal synchronized foley；
SHA-256 `d1dffdcf00fe8d9996ec9a331053843832dc073e7796c2d494f6a1b36f16181a`，
48kHz stereo PCM16、1440000samples。源测量 mean -34.4dBFS / peak -19.9dBFS；
task composer 声明 P4 +6000millidB gain。尚未混入成片，human listening 为 NOT_EVALUATED。

`compose_final.py` 已静态审查，要求显式六个全 PASS 的 `selected-sources.json`，
真实 imported video assets、唯一 `ResolvedTimeline`、720frames/1440000samples 与 HyperFrames。
当前没有 selection、final bootstrap 或 render，没有 P8 source activation、P6 或 Final Acceptance。
不能用 direct concat、重复片段、慢放或移除 source muted 绕过未关闭的 Gate。

## RAG And Learning Evaluation

真实项目 RAG 在开始时检索 `H3 30s multi shot canonical source audio replace P4 continuity`，
命中旧三镜头 run summary；随后针对 `H3 camera pan ignored locked camera endpoint repair` 检索。
后者包含 stale-tagged 旧 M6/V13 经验，已重开当前原文；没有可直接复用的当前 T8 T2VA 右摇修复配方。
历史材料仅为 advisory，不代替当前 Gate；未等待或手工重建 RAG index。

`distill-ai-video-learning` 自动评估：`no_candidate`。
已检索当前 learning 目录中的 lighthouse/灯塔/camera endpoint/画外/offscreen，未发现同范围 claim；
并核对旧灯塔测试及 M6 的失败/后续 supersession 作为 counter-context。
本次只有一个六段叙事链，各段目标不同，三次 repair 均混有 seed 变化；
不能据此提出“增强 prompt 必然修复”或 H3 model-wide quality/continuity 规则。未修改 adoption targets。

## Resume And Verification Boundary

如用户选择继续最小补拍，应先显式续封有限预算，仅重做 Shot06：
让 whole tower、base 与 coast 的可见 endpoints 明确，小尺寸塔体完整入画，保留 backward camera、
amber lamp 与 rainy coast；新 identity/intent/permit 后完整重验。不得修改现有 FAIL Gate 或旧预算 bytes
来伪装尚未耗尽；当前 driver 的预算来源需要明确续期方案。

只有第六段 PASS 后才能调用 task composer，经正式 import、timeline preview、render，再验最终30s
实际裁切与 P4替换音轨。当前 prepared composer 只有静态证据，不声称实际 runtime/render PASS。

本记录按 documentation 类别进行 exact staged Harness checks，receipt 位置：
`.agent/harness/runs/h3-lighthouse-30s-budget-stop-20260905-v1/receipt.json`；
只有实际 fresh PASS receipt 才构成验证证据。本次不为记录执行额外 Provider/media、network 或 full suite。
未改动其他窗口文件，未 push/release；其他窗口在本任务期间自行推进 main，不计入本次工作。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shot-01-media | h3:a213b70147300fda55b2d1f82913de72656a2154608b49267561cb7469619f22 | lighthouse-30s-20260905 | shot-01-video-30s | N/A | a2625cc547a90a3fa4e5d33da79060fcd7c195295fad13da09f07eed1b3a4f73 | AGENT_VISUAL | FAIL | DARK_LANTERN | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-01/media-gate.json |
| shot-01-repair-01-media | h3:44f92d833a47b5a175d491fd2dabcaa0049cc6ac0341b90e9e3b69d4e5875fc2 | lighthouse-30s-20260905 | shot-01-repair-01-video-30s | N/A | bf82c78ac79b9bec701e390494e03bd3f764079f98d92ed8c58baa6bb44c2fc9 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-01-repair-01/media-gate.json |
| shot-02-media | h3:2e04687f4023e53719350f5644a671a91ca3c8c591b2a5733582bc4294f106a9 | lighthouse-30s-20260905 | shot-02-video-30s | N/A | ecb88f58b8aef00affff61d7b3eae128783eab7cfa2e1e82d943316c4de0686c | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-02/media-gate.json |
| shot-03-media | h3:ec5d0b7e62510c90f44e89110d789fbdd81f092adb6984071007e30e2c13679c | lighthouse-30s-20260905 | shot-03-video-30s | N/A | 4f9e36c22cf19ce15a4a26d4487ef78c2b94fde88c52ed9681cc9a230cfd4ec6 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-03/media-gate.json |
| shot-04-media | h3:63184b05fb934bbf77ac778b1e54c6e1bf62b9263b3880fe2cf30f3f76f804a8 | lighthouse-30s-20260905 | shot-04-video-30s | N/A | 05fc29db6bffa334c34ef3730b82ed7729f4708553c367e4c249322f5a460e4f | AGENT_VISUAL | FAIL | CAMERA_PAN | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-04/media-gate.json |
| shot-04-repair-01-media | h3:06312e1b86960e8b1356bf8ee303acdfc35e762f5dbe50e163f5cbafb4e9dc57 | lighthouse-30s-20260905 | shot-04-repair-01-video-30s | N/A | 6cd8ac78ef1b4e311c0b8b9e418964bf7b2a74e3836e791cd029bdf07651b47d | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-04-repair-01/media-gate.json |
| shot-05-media | h3:04014045bb2758574974f1563ef9142763f5a23f10973296e137663d11b8b05b | lighthouse-30s-20260905 | shot-05-video-30s | N/A | 73937df49aaf0977c53e017849891245d957c8390cb61d0a550b6cb6413e1dfd | AGENT_VISUAL | FAIL | OFFSCREEN_ARCHITECTURE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-05/media-gate.json |
| shot-05-repair-01-media | h3:77bf42aeb183f2fadafa884ff18f88d7150dca6a075d10fc2197e0cb00bf9063 | lighthouse-30s-20260905 | shot-05-repair-01-video-30s | N/A | 0fe033bb5189ec4c339e27789fd84763826a90ace7e9daccda740f9021ca8476 | AGENT_VISUAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-05-repair-01/media-gate.json |
| shot-06-media | h3:2d7f875c2b2a2f4948e43c04b5332ce633f5af4ac3237dfe27ba730ced2975c3 | lighthouse-30s-20260905 | shot-06-video-30s | N/A | 272dd8b34ab8f0bd2bbb7a14394ffa708d7e72277f25dd1ef177b527dbb3c861 | AGENT_VISUAL | FAIL | SHOT_SCALE | NEW_ATTEMPT | NONE | runs/director-h3-lighthouse-30s-20260905-001/shot-06/media-gate.json |
