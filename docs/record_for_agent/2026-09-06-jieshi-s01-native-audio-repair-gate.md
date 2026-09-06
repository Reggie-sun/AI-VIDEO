---
record_kind: media_experiment
topic_id: jieshi-s01-first-frame-native-audio
learning_eligibility: eligible
evidence_index_version: "1"
---

# S01 Native Audio Repair Gate

## Current Runtime Truth

用户再次“授权”后，完成一个 Vidu `viduq3-pro` I2V submit；4 秒、1080p、原生音频开启。
真实首帧已进入 API payload，新视频下载成功，但逐镜 Gate **FAIL**，未激活，S02 阻断。
这不是已接受成片，也不是新的人类验收。全集目标仍未完成。

## Exact Evidence

Attempt: `jieshi-e01-s01-vidu-i2v-attempt02`。
Request: `cdf6a55c1d3586fbad30e5649306ef38f99d924afec645144d4daf5f9e96df9c`。
MP4: `runs/jieshi-e01-i2v-20260906-attempt02/production-s01-v2/state/video-generation/fetch/files/49e585e89585449627431e3fe7395d64c1fa4bd42c9d400a3863fdde06fcb5f8.mp4`。
SHA-256 同文件名，4,248,601 bytes。MCP 实测 1080×1920、24fps、97 frames、4.042s；AAC stereo 48kHz。
Provider metadata 的内部 ProduceID 含 `720p`，本记录只确认交付 raster，不能证明模型内部原生分辨率。

首帧复用已登记 PNG，SHA-256 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`。
Audited transport 校验了实际 POST 解码后的图片 bytes，未把 prompt 中提到 reference 当作实际输入。
旧项目 attempt 仍在 VALIDATE；未伪造 terminal failure 或复制旧 Manifest。
新 `production-s01-v2` 通过 canonical bootstrap 复用精确创作包、Registry、原 import receipt 和图片，strict loader 重开。

## Gate Findings

[逐项 Gate](../../runs/jieshi-e01-i2v-20260906-attempt02/preparation-v3/shot-01-gate.md)
绑定 exact MP4，下载后立即调用 project-local `video_analyze` 并查看九帧。
左手一直留在膝上，抬起的是拿手机的右手；0.5–2s 出现模型自带白字幕；镜头改变构图。
这三项已足够判 FAIL，不需要为了记录再生成或扩大分析。
广播 ASR 在 0–2.56s 转写“林燕,請在終點站下車”；同音字不能单独判定读错姓名。
精确语音质量、全帧无倒影、完整身份工牌和最终字幕仍未闭合。

## Execution And Verification

真实续期仅重新确认既有内部 operator ceiling，不增加上限，不是官方价格观察；新旧 profile
hash 与实际一小时窗口见 `runs/jieshi-e01-i2v-20260906-attempt02/renewal-evidence.json`。
新 preview、authorization、reservation02、durable intent、one-use permit 均按既有 seam 创建。
一次 POST 在 07:23:40 UTC accepted，07:24:53 Provider succeeded；首次 fetch 被直连安全检查拒绝。
已审阅的 GET-only DNS recovery 在 07:26:02 成功取回同一结果，未新增 submit，未削弱 TLS/redirect guards。
脚本 AST、真实 canonical dry preview 已通过；独立 `reviewer_xhigh` submit review accept。
Harness inspect 将新 runs scripts 判为 fallback，要求 full tests / architecture 等；用户明确禁止 worktree，
未运行必须 detached worktree 的完整 Harness，也没有 fresh passing receipt。上述 live proof 不替代 Harness。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-native-repair-gate | request:cdf6a55c1d3586fbad30e5649306ef38f99d924afec645144d4daf5f9e96df9c | jieshi-s01-first-frame-repair | jieshi-e01-s01-vidu-i2v-attempt02 | N/A | 49e585e89585449627431e3fe7395d64c1fa4bd42c9d400a3863fdde06fcb5f8 | agent_review_of_mcp | FAIL | WRONG_HAND_AND_BURNED_CAPTIONS | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt02/preparation-v3/shot-01-gate.md |

## Learning And Next Work

已按 `distill-ai-video-learning` 评估，`no_candidate`。新右手/手机动作与原生音频实例各只有本次
明确证据；prompt 和 audio 同时改变，不能将差异归因于声音开关。前次手影 FAIL 不能被本次
未完整判定的倒影状态算作第二个支持例。现有 learning 目录无同题 claim。
首帧能约束初始画面，不能把本次未通过的动作约束说成已解决。
单次 submit ceiling 已消费，进一步 paid repair 需新的有界授权和新 identity/intent/permit。
保留 exact MP4、本次各 preparation 版本和旧失败证据。其他 staged/dirty work 未处理。
本记录写入阶段没有 Provider/media/网络调用；未 push，未刷新 RAG index。
