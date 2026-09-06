---
record_kind: media_experiment
topic_id: jieshi-s01-vidu-first-frame
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi S01 Vidu V2 Live Gate

Date: 2026-09-06

## Result

用户“继续生成”后，完成一次新的 Vidu Q3 Pro S01 首帧 I2V，compiler2、
`is_rec=false`、4秒、1080p、native audio true。**逐镜 Gate FAIL，未激活，S02 阻断。**
本记录补充 [compiler v2 implementation](2026-09-06-vidu-native-prompt-v2.md) 的真实媒体证据；
离线封装正确没有转化为本次画面质量通过。

## Execution And Identity

Run：`runs/jieshi-e01-i2v-20260906-attempt04`；project `production-s01-v4`。
Canonical bootstrap → strict reopen → Planner/readiness → Router → compiler2 → preview →
新 authorization/reservation04/intent/one-use permit → `submit_once()`，提交前 native
reviewer_xhigh `accept`。Registry PNG 与旧素材精确相同，未制造 human attestation。

- Request `b66d3b87c97390eacddd01140785d1702d6f566e82881908123ac576700f55c3`。
- Actual POST SHA `d504b3aefe6d3f1ac8d8b50c4c53df76d73fb31c6a9c94ca006e834bed13c1d6`，与离线审计一致。
- First-frame PNG `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`，2,064,319 bytes。
- MP4 `934f7498223dc6545396b868c7c6d31ea7dbd3015a80d34f19950087bb697bec`，3,517,773 bytes。
  文件位于 run 的 `production-s01-v4/state/video-generation/fetch/files/<SHA>.mp4`。

沿仓库已批准 operator-ceiling renewal 创建新 immutable profile，仅续期旧内部上限，
不查询官方价格；证据见 run `operator-ceiling-renewal.json`。用户本次新 quota=1，
08:32:55 UTC 开始 POST，HTTP200 accepted；08:33:59 observed succeeded。
初次 fetch 被 public HTTPS/DNS guard 拒绝，沿旧 GET-only 恢复流程解决本机 fake-IP，
08:34:24 exact fetch 成功，不重试 POST、不放宽原域名TLS或public-IP校验。

## Post-Media Evidence

落盘后立即调用 project-local `video_analyze`：1080×1920、H.264、24fps、97帧、4.042s，
AAC48kHz stereo；一镜。Codex 查看九个0.5s样本。

左手真实抬起，右手持机留在腿上；但掌心朝镜头、机位漂移、右边倒影人物出框。
1.5–3.5s 仍有错误姓名与广播白色字幕。Whisper base “零雁在終點站下車”是粗粒度
识别，不能证明准确广播及前三秒时序。完整 required verdict 表见
run `preparation-v1/shot-01-gate.md`；metadata/transcript 见同目录 `video-analysis-summary.json`。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-v2-live-gate | request:b66d3b87c97390eacddd01140785d1702d6f566e82881908123ac576700f55c3 | jieshi-s01-first-frame-repair | jieshi-e01-s01-vidu-i2v-attempt04 | N/A | 934f7498223dc6545396b868c7c6d31ea7dbd3015a80d34f19950087bb697bec | AGENT_REVIEW_OF_MCP | FAIL | BURNED_CAPTIONS_AND_CAMERA_DRIFT | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt04/preparation-v1/shot-01-gate.md |

## Assessment And Boundary

新 prose 与 `is_rec=false` 下仍出现同类问题，支持缩小后的重复观察，不能证明音频导致字幕，
也不能证明官方推荐提示是旧失败原因。随机种子未控制，不归因某一句提示或单个参数。
本次额度已消费，outcome known；保留全部历史和本次 evidence，未 push、未生成 S02。
本 run 脚本 AST及canonical离线准备通过，Harness inspect 为 fallback；因用户禁止worktree，
未运行隔离 full Harness，无 fresh receipt，也不以旧core receipt冒充。

按 `record-ai-video-session` 记录，自动 `distill-ai-video-learning` 更新既有同范围候选，
结果 `pending_candidate`；仅加入第三次独立证据及compiler版本边界，未采用 Provider Policy。
记录阶段不触发新的 Provider/media/网络工作。检索 stale 结果只作定位，未前台刷新索引。
