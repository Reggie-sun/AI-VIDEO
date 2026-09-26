---
record_kind: media_experiment
topic_id: qingyan-original-packshot-brand-film
learning_eligibility: eligible
evidence_index_version: "1"
---

# Qingyan Original Packshot Brand Film Record

Date: 2026-09-27

## Purpose

用户要求再次生成视频观看。此前六秒样片的生成包装有可见文字问题；本次选用用户提供的真实商品照片，创作 10 秒竖屏原图动态图文品牌短片。此选择不声称实现真人、物理喷雾演示或产品功效验证。

## Current Media Truth

- 本地观看文件：`runs/ecommerce-qingyan-packshot-20260927-001/final/青颜_10秒_原图品牌短片.mp4`。
- exact MP4 SHA-256：`25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6`，528097 bytes。
- 实测 H.264 High、1080×1920、24 fps、240 frames；视频时长 10 秒，container duration 10.022 秒；AAC、48000 Hz、双声道。
- 图文阶段：0–3 秒「近距离，更从容」、3–6.5 秒「抑汗｜净味」、6.5–10 秒「青颜」、7.5–10 秒「点击了解青颜」；产品名与 60ml 说明持续显示（首帧处于淡入起点）。

本次没有修改仓库业务源码、contracts 或 tests。新 authoring driver 与媒体均在 ignored run 内；记录是 tracked documentation。所有媒体仅在本地，没有 push、release 或新的 Video Provider submit。

## Source And Canonical Execution

原图为 `artifacts/qingyan-miao-ad-20260826-v8/assets/product-packshot.jpg`，1440×1440、93224 bytes，SHA-256 `03d27bd46be48082b6d5ac737fbbb1f6cdca68b891d6c7d7c58eaa2c1c14f078`；来源与允许文案重读了 2026-08-26 / 2026-08-27 青颜记录，未编造未知用法或量化功效。

照片等比缩放至 1080×1080，放在 1080×1920 白色画布 y=420；未裁切、拉伸或重画包装。保存的 silent source MP4 SHA-256 为 `1a7c7eabd4c29bd47665090b5ec7bcfec3bd933a1f31961703c81bedbbaa2538`。从其第 0 帧仅提取一次 1080×1920 PNG，434489 bytes，SHA-256 `8c13fa83198a7891c5b67032f03ecfe0cd5db51836ca3ba6eab625d33bb6adc2`，作为 IMAGE Hero layer；VIDEO 保留 primary layer。

BGM 从严格加载的 `runs/haokou-ninebot-visual-v11-20260914/composed-production-24s5/project.yaml` 复用 `mixkit-cat-walk-bgm`，SHA-256 `2c6471144a3273a58e978bad6e181f5529a0cc3afa5715036e67d0056ed26227`，登记 license 为 Mixkit Stock Music Free License。音频走现有 P4 timeline/mixer，未 direct mux。

新隔离 development bundle 在 `runs/ecommerce-qingyan-packshot-20260927-001/production-v2/`：`ProductionStateCommitter.bootstrap_initial_state`、strict loader、canonical ad compiler、`ResolvedTimeline` 与 pinned HyperFrames `0.7.103`。唯一 timeline 为 240 frames / 480000 samples，composition fingerprint `52e76fde12b77677ee7e69ef639b638e5ae1e9b49eee80bc490cd6c90d662d39`。未改变既有 live project、renderer 或 lifecycle owner。

## Known Failures And Bounded Corrections

准备脚本先后出现错误：FFprobe 指错尚不存在的目标；过早删除临时源和根目录；`EXISTING_VIDEO` 误用 DERIVED 分类；同一 Shot 重复进入多个 Storyboard beats；Hero layer 吃掉唯一 primary layer；随后发现 graphic layer 必须绑定 IMAGE。Parent 的同 VIDEO overlay 建议也被原 compositor 正确拒绝，之后改用 exact decoded frame。以上是本次脚本/判断错误，不是 canonical contracts 被损坏的证据。

source MP4 实际 FFmpeg 制作两次：第二次恢复被错误清理的已知成功源，之后只复用保留字节。PNG 提取一次。旧 `production/` 的 bootstrap evidence 保留，最终使用独立 `production-v2/`。

`qingyan-packshot-render-01` 在 source materialization 前置检查因漏传 audio asset 而 failed，未启动最终 renderer；strict reload 确认 failed、无 active render state。补齐 visual/audio asset map 后，以新 identity `qingyan-packshot-render-02` 成功，实际完成一次最终 render。不是 exact replay、blind retry 或 unknown-outcome recovery。

详细本地诊断：run 内 `source-preparation/failure-history.json` 与 `preflight/execution-adjudication.md`。旧六秒 MP4 的历史包装 FAIL 不因这次不同格式的新片而被改成 PASS。

## Review And Verification

执行前完整要求在 run 内 `preflight/contract.json` 封存，11 项 requirements；原视觉方向、Director coverage 和 creative brief 同时保留。managed Kimi worker 只做 bounded read-only preflight：invocation `7bc71e69-b1d5-4b74-a17d-97e531cef6f9`，PARSED、2 次已验证 k3-256k/high 请求；这不等于媒体或人类验收。

最终 exact MP4 显式调用 project-local `video-analysis.video_analyze`，抽取 20 帧、interval 0.5s，无 transcription/model download。完整开发报告为 `preflight/review/packet.json` 与 `result.json`，绑定同一 MP4；报告 subject hash `260dfe2308b7f6c30fb80de0e2739f0b2a7f80e4f382a259a31ddabc982e5116`。

Parent 与独立 read-only Native `reviewer_high` 都实际查看 12 个封存抽样帧。未发现可证实的包装错字、变形、遮挡或失真；独立报告在 `preflight/independent-review.md`。0–2.75、3.25–6.25、6.75–9.75 秒覆盖三阶段；3.00、6.50 秒是淡入样本。

exact MP4 全量 decode 完成 240 帧，无错误；响度 -19.3 LUFS，true peak -4.9 dBFS，LRA 1.1 LU；-60 dB / 150 ms silence detection 无检出区间。相邻 `decoded-audio-measurement.log` 与 `audio-silence-check.log` 保存实际测量。

开发侧 full-contract verdict 仍为 `NOT_EVALUATED`：8 项 evaluator PASS；`motion.integrity`、human `visual.advertising.holistic`、human `audio.listening` 保留未评估。`visual_quality_report check` 的 exit 1 表示此未完成 verdict，不是工具崩溃。抽帧、解码、音轨与响度不能替代原速完整观看/聆听；没有 P6 / Final Acceptance 或正式交付验收。

Exact documentation verification receipt location：`.agent/harness/runs/qingyan-packshot-record-20260927-01/receipt.json`；验证状态与完整性以该 machine receipt 及复验为准。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qingyan-packshot-technical | nonq0:qingyan-packshot-render-02:52e76fde12b77677ee7e69ef639b638e5ae1e9b49eee80bc490cd6c90d662d39 | qingyan-original-packshot-brand-film-20260927 | qingyan-packshot-render-02 | N/A | 25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6 | TECHNICAL | PASS | NONE | NEW_ATTEMPT | NONE | runs/ecommerce-qingyan-packshot-20260927-001/production-v2/state/render/render-receipts/fb8d04e5dcd3d5c0b75ab1071bd7c8b4216182641014a2dc9b4ecdb0ba7256dc.json |
| qingyan-packshot-full-contract | nonq0:qingyan-packshot-render-02:52e76fde12b77677ee7e69ef639b638e5ae1e9b49eee80bc490cd6c90d662d39 | qingyan-original-packshot-brand-film-20260927 | qingyan-packshot-render-02 | N/A | 25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6 | EXPLICIT_EVALUATOR | NOT_EVALUATED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | qingyan-packshot-technical | runs/ecommerce-qingyan-packshot-20260927-001/preflight/review/result.json |

## Learning Evaluation And Boundaries

自动 `distill-ai-video-learning` 评估：`no_candidate`。本次只有一个成片 attempt 的多个 proof layers，准备错误与原六秒生成包装案例不构成隔离变量的控制比较。现有 learning claims 没有本次可实质更新的匹配 claim，不把单例推广为 Provider/导演默认规则。

`.codex/config.toml` 的既有 unrelated dirty change 保留。记录阶段没有额外 Provider/media generation；只按 documentation policy 核验与 checkpoint。AOCI observe 收尾按当前官方 Guide 处理；独立 experience RAG 未人工 rebuild，检索时使用其 last-good snapshot，不声明新记录已进入该索引。
