---
record_kind: media_experiment
topic_id: jieshi-s01-first-frame-native-audio
learning_eligibility: eligible
evidence_index_version: "1"
---

# S01 Spatial Hand Repair Gate

## Current Runtime Truth

用户“继续生成测试”后新增一次 Vidu `viduq3-pro` I2V，4秒、1080p、原生声音，
同一已登记首图。真实左手抬起、右手手机留膝上，本次动作选手改善；仍有烧录字幕和
镜头移动，手掌朝镜头而不是玻璃。逐镜 **FAIL**，未激活、未推进S02。

## Identity And Execution

Attempt `jieshi-e01-s01-vidu-i2v-attempt03`，request
`4fefcd71bc735c6296f28fddd31cdb18c7dd0e127c253afc68e7b4260fd7631d`。
MP4 SHA-256 `0bf686d428e7af6e11b8f191bf389565e74ca31728ef1048d9942d674e42d42c`，
4,188,741 bytes。文件位于
`runs/jieshi-e01-i2v-20260906-attempt03/production-s01-v3/state/video-generation/fetch/files/0bf686d428e7af6e11b8f191bf389565e74ca31728ef1048d9942d674e42d42c.mp4`。
实测1080×1920、24fps、97 frames、4.042s、AAC stereo 48kHz。Metadata内部标识含720p，
因此只确认交付raster，不确认模型内部原生raster。

同一 PNG SHA `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`
通过原import receipt/Registry和actual POST bytes核验。沿用未过期profile原bytes，
没有续期或查价。新task quota=1，独立root/attempt/authorization/reservation03/intent/permit。
旧Manifest未复制或更改，canonical bootstrap只复用selected creative/registered素材。
07:36:54 UTC accepted，07:37:57 succeeded，首次fetch被既有直连检查拦截；
已审阅GET-only DNS recovery在07:38:07取回同一结果，没有第二POST。

## Verification And Gate

Canonical bootstrap/strict reopen、Planner/readiness→I2V、compiler/resolve、paid preview和AST通过。
原 `reviewer_xhigh` 对新exact submit scope复核accept。未改core实现。
下载后立即调用project-local `video_analyze`并查看九帧，详见
[逐项Gate](../../runs/jieshi-e01-i2v-20260906-attempt03/preparation-v1/shot-01-gate.md)。
2s出现名字样式白字，2.5–3.5s烧录广播字幕；镜头移动裁掉右侧倒影。
Whisper base给出0–4s粗segment，不能据此证明精确广播时点或名字发音。
全帧无倒影、2cm间距、完整工牌和最终字幕尚未闭合。

Harness inspect判runs scripts为fallback；用户禁止worktree，未执行需要detached worktree的
完整Harness，无fresh passing receipt。真实媒体证据不替代工程验收。
七个既有staged runs文件及其他会话工作保留，未push。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s01-spatial-repair-gate | request:4fefcd71bc735c6296f28fddd31cdb18c7dd0e127c253afc68e7b4260fd7631d | jieshi-s01-first-frame-repair | jieshi-e01-s01-vidu-i2v-attempt03 | N/A | 0bf686d428e7af6e11b8f191bf389565e74ca31728ef1048d9942d674e42d42c | AGENT_REVIEW_OF_MCP | FAIL | BURNED_CAPTIONS_AND_CAMERA_DRIFT | NEW_ATTEMPT | NONE | runs/jieshi-e01-i2v-20260906-attempt03/preparation-v1/shot-01-gate.md |

## Learning And Next Boundary

按 `record-ai-video-session` 记录并自动执行 `distill-ai-video-learning`。
两次独立native-audio请求均在要求纯摄影画面时出现烧录对白字幕，构成窄范围重复现象；
仅支持“这两个S01请求的文字禁止约束未可靠落实”，不能证明audio开关是原因。
Prompt改变且随机种子未控制；本次左手改善仅为观察，不晋升确定性规则。
自动评估结果 `pending_candidate`，见
[字幕重复现象候选](learning/vidu-s01-native-dialogue-burned-captions.md)。证据identity validator通过；
修正了前次记录proof_layer的大小写格式，不改变其Agent证据性质或FAIL结论。
候选单独保存，确认前不修改Provider Policy或Gate。
此次一次submit已用尽，额外paid试验需要新有界授权；没有自动再试。
记录阶段无Provider/media/网络调用。RAG搜索返回stale片段，本次未前台刷新索引。
