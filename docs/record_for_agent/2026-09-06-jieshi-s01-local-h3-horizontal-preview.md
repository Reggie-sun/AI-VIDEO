---
record_kind: media_experiment
topic_id: jieshi-s01-local-h3-horizontal-preview
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi S01 Local H3 Horizontal Preview

Date: 2026-09-06

## Scope And Result

用户要求用本地 H3 试做既有《界蚀》，并批准 S01 横版试片及展示首帧的使用。复用完整剧本 `docs/superpowers/artifacts/drama/jieshi-episode-01/episode-01.md` 的首镜；本次不是 52 Shot / 300 秒竖屏全集交付。

唯一一次 local/unmetered I2VA 提交已成功取回 raw MP4，逐项 Gate 为 `NOT_EVALUATED`。七个其他人物倒影、林砚本人倒影缺席、左手抬起和右手手机在抽样画面中成立；广播逐字内容与时间窗未可靠验证，悬停的精确 2cm 无法从单视角测量。不提交 S02，不 activation，不签发 P6 / Final Acceptance。

## Exact Runtime Evidence

所有文件位于 `runs/jieshi-s01-h3-horizontal-20260906-001/`。本地媒体及 Production state 保留，Git 只保存选定的脚本和证据索引。

| Identity | Value |
| --- | --- |
| Attempt | `jieshi-s01-h3-horizontal-video-001` |
| Resolved request | `3a4ad6f82bc9ac67ae14220a1066647351b3e3564f1b930e6ab046781bc52367` |
| First frame SHA-256 | `1ea65e808a44444bd162185e9bacf299f5ff02ebe49556fc147b7a261b7b0061` |
| Import receipt content hash | `ef33d6769ca82f8eecfd38cea18a81a7e476e09c9c739c8a38351e99483a90d3` |
| Profile | `workflows/profiles/minimax_h3_t8_i2va_turbo_native_v2.json` |
| Profile hash | `f73fe4a9adef3275ba4b6c9b3bd0307bed39a40542f80747867f2cb46df3e667` |
| ComfyUI request | `92dfd32d-571f-43ec-8013-43ae8ae54165` |
| MP4 SHA-256 | `6126e68df217ce9a859c5de904b99ea294437fb48f10444eff3bccc52706492a` |
| MP4 bytes | `1419435` |

Canonical fetched path：`production/state/video-generation/fetch/files/6126e68df217ce9a859c5de904b99ea294437fb48f10444eff3bccc52706492a.mp4`。实际 1344×768、124 frames、24fps、5.167s、H.264 High/yuv420p、AAC stereo/32000Hz。完整 A/V decode exit 0。ComfyUI 日志记录生成 104.17 秒；提交时间 `2026-09-06T06:48:51.976110Z`，成功观测 `06:50:38.484481Z`，fetch `06:50:54.315029Z`。

输入 receipt 只表示 exact image 的使用许可，不伪造人类画质验收。所有 mutable state 经 `ProductionStateCommitter`；视频经 `VideoGenerationService.start/submit_local_once/refresh_local_once/fetch_local_once`，没有裸 transport submit。Provider preflight 核对模型、LoRA、节点和 runtime bytes 后消费独立 local intent/permit。生成前后 queue 均已核查；由本任务启动的 loopback ComfyUI 已在空队列下停止。没有 remote video / paid call。

## Compiler Fix And Verification

`6f5c0a1` 修复 native V2 完整 `/4` requirement 未接入 shared H3 prompt 的确定性缺口：`comfy_t8_native_turbo_video.py::compile_request()` 复用 `_h3_prompt.py`，对白按 sealed zh/en language 发射原生 tag；缺失或不支持 language typed fail closed。历史 `/1` 路径、profile identity、native-control rejection、唯一 writer 和 activation 边界保持不变。

独立 `reviewer_xhigh` 曾发现 worker 添加的 `supports_native_control=True` 绕过；该项已移除，`/1` 与 `/4` 均有真实 typed 拒绝回归。最终 verdict `accept`，无 blocking issue。parent 重开真实请求，与封存 hash 一致。

- Native/compiler focused suites：60 passed；扩展 Provider/neutral requirement/skill-boundary suites：1184 passed。
- `docs_contract_gate check` PASS；`agent_harness policy-audit` 无 diagnostics。
- `architecture_gate check --base-ref HEAD` 在实现提交前 PASS，仅有 native adapter fan-out 达到 14 的 INFO；新增 import 均用于同一 compiler 责任。
- 完整 suite：4453 passed、2 failed、4 skipped、2 warnings，1389.53 秒。失败均为 `tests/test_mcp_transcribe.py` 的 no-audio / invalid-model 测试，独立重跑仍失败；当前测试 Python 缺少 `whisper`，未修改的 `transcribe.py` 在 typed 检查前 import 导致 `ModuleNotFoundError`。实际 MCP 在其独立环境中已完成转写。未新增 dependency 或越界修复该模块；详见 `verification.json` 和 `full-tests.log`。
- 当前用户规则禁止未明确请求的 worktree；标准 Harness 必须创建 detached worktree，因此本轮没有 fresh Harness receipt。上述普通检查不冒充 exact-snapshot Harness，代码 checkpoint 不代表完整 Harness 验收。

## Media Gate And Repair Assessment

已显式调用 project-local `video-analysis` MCP：0.5 秒间隔 11 帧、probe、scene detection 和 Whisper base；又对 exact MP4 用中文 base、medium 各做一次转写。原始英文自动识别甚至给出超过 5.167 秒的 timestamp，不能作为台词证据；中文输出分别为“你”和“看到些”，均无法支持完整广播。音轨 mean -47.8dB、max -23.6dB；有音轨和非静音不等于正确台词或可交付声音。

另外对分析用副本增加 20dB 后用同一 MCP/medium 再识别，返回空文本，仍无法支持广播验收。MCP 拒绝 audio-only WAV，因此使用视频流 copy 的独立诊断 MP4；`analysis-video-derivative.json` 绑定源文件和副本 hash。该副本不用于交付、不替换原生音轨，源 MP4 bytes 未变。

缩略图初看漏数一人，parent 使用原分辨率 `frame-3s.png` 核对为 2 站立 + 5 坐姿，共 7 个，已更正过程说明；没有把计数误判保存为模型失败。`media-gate.json` 是当前逐项判定的唯一 run 记录。

`EVIDENCE_REPAIR_FIRST` 已执行。封存上限为 2 次生成、7200 秒 task、3600 秒 GPU，本轮使用 1 次。当前正确台词、中文 tag、画外声源和原时间窗都已进入 exact graph，现有证据未隔离出可归因的 prompt 缺陷；不以随机改写耗尽第二次机会。保留未接受 raw preview，停止当前 attempt。没有将低音量或 ASR 结果单独外推为 H3 通用能力结论。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-fetch | h3:3a4ad6f82bc9ac67ae14220a1066647351b3e3564f1b930e6ab046781bc52367 | jieshi-s01-h3-horizontal-20260906 | jieshi-s01-h3-horizontal-video-001 | N/A | 6126e68df217ce9a859c5de904b99ea294437fb48f10444eff3bccc52706492a | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/jieshi-s01-h3-horizontal-20260906-001/fetch-receipt.json |
| s01-gate | h3:3a4ad6f82bc9ac67ae14220a1066647351b3e3564f1b930e6ab046781bc52367 | jieshi-s01-h3-horizontal-20260906 | jieshi-s01-h3-horizontal-video-001 | N/A | 6126e68df217ce9a859c5de904b99ea294437fb48f10444eff3bccc52706492a | AGENT_VISUAL_AUDIO | NOT_EVALUATED | AUDIO_EVIDENCE_INSUFFICIENT | SAME_EVIDENCE_NEW_PROOF_LAYER | s01-fetch | runs/jieshi-s01-h3-horizontal-20260906-001/media-gate.json |

## Learning And Publication Boundary

已按 `record-ai-video-session` 保存稳定记录，再按 `distill-ai-video-learning` 评估为 `no_candidate`：只有一个独立媒体 attempt，且没有受控音频对照或对既有 visible-context claim 的明确材料更新。再次 experience 检索得到 advisory 历史材料，不用其替代当前 MP4，不修改 adopted claim，不刷新 RAG index。

本任务的代码、脚本和记录为 local-only checkpoint，无 push/release。无直接受本次 H3 证据取代的旧 H3 记录；旧 Vidu/Seedance 结果仍属不同 attempt。原七个 staged run 文件未修改，提交前后 staged patch SHA-256 均为 `5e6c24dd5a82a3e9f66a79781d234e63491b97293e28716ddbda3f7db611a639`。
