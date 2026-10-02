---
record_kind: media_experiment
topic_id: coco-nosha-metaso-h3-cut-continuity-repair
learning_eligibility: eligible
evidence_index_version: "1"
---

# METASO H3 Cut Continuity Repair Record

Date: 2026-10-03

## Goal And Boundary

用户拒绝旧三段拼接的无关联转场，并澄清不要求一镜到底，随后授权“再生成一轮或者修改我看看”。本轮保留原 S01，封存最多两个 METASO MiniMax-H3 新提交，重做 S02/S03，再以现有素材剪接。没有新增图片、配音、其他 Provider、UI、fallback、Production source change 或大 spec/plan。

Run：`runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/`。下文 run 内路径相对此目录。旧 [character continuity record](2026-10-02-metaso-h3-character-continuity.md) 的主角可辨结论不能证明跨镜切换成立；原 [canvas-method S01 FAIL](2026-10-02-metaso-h3-canvas-method.md) 保留。

## Authoring And Exact Inputs

先检查原片真实末态，再选择镜头：S01 的 D 木箱近景 → S02 从同一 D 近景拉回同一房间 → Nosha 接触并解除 C、放下、恢复 → 两人向右移动 → S03 换机位继续行进、停下看手机。保持 COCO 左前、Nosha 右后、手机属于 COCO、倾倒推车与地上水果；没有要求逐帧同一步态。

三张原 PNG exact bytes 继续绑定，不取 Vidu 失败帧或新增第四张图：

| Reference | Responsibility | SHA256 |
| --- | --- | --- |
| Image1 / a-scene | 原木质收容处、窗、光线、场景尺度和材质 | 66f13af336408a826dd17b7c8df68048592ca23bbf99dca312539dd8f2674b62 |
| Image2 / b-COCO | 单一 COCO：奶油白/黑机器人、黄色灯条、机械臂、轮底座；多视图不是多个角色 | 5f3996fbe878d848d0ee6d71f689114f944677b9e739ab816a5e06b048e41920 |
| Image3 / c-Nosha | 单一 Nosha：高大黑长外套、白手套、透明盛水头及内部生物；保持尺度关系 | 5d73df034a0b2a6637f29f8406fbd9f08a54f1636f34c03aea7a239239b134e6 |

S02 Video1 为原 S01 source 6–15s 的 9s 静音参考，SHA `98d5db9fed96b53c856a53671bd0bf6bb64fb4dd67292608469c171b4a2a5d0d`。S03 Video1 为本轮 S02 `edited.mp4` source 7.25–11.25s 的 4s 静音参考，SHA `e4b07e3c51ea7235858e6400a692b815fe025341f5dbcf2c2a7f5b5678fa2ff7`；该窗口在修正 split 的 `edited-v2.mp4` 中继续保留，前序 gate 实际绑定 v2。文件级 provenance 不改写成 v2 源。

用户确认的 source WAV SHA `52975f4a3df74a4ec294f712d6afdc563d1da770323bc59f912dba2d58fffb77` 仍登记且未改；两个新镜不提交 audio_url、不重复对白。最终保留原 S01 完整图像和内嵌对白来源，composition 会重新编码，不能称最终 AAC 与原 WAV exact bytes 相同。

## Actual API And Consumption

沿用既有 `metaso_h3` adapter 与 canonical paid seam；base `https://metaso.cn/api/minimax`，Bearer injected `METASO_API_KEY`，POST `/v2/video_generation`，GET `/v2/query/video_generation/{task_id}`。公开 Ref2VA video reference 是软参考，不能描述为精确首帧或 extension conditioning。本轮实际 JSON 为 `model=MiniMax-H3`、text + 3 `reference_image` + 1 `reference_video`，`resolution=768P`、`ratio=16:9`、`context_ir_enabled=true`。Context IR 内部文本未返回、未伪造保存。

| Shot | Task | Requested duration | Request SHA256 | Success / fetched latency | Usage input / output / total seconds |
| --- | --- | --- | --- | --- | --- |
| S02 | 2106047316655992832 | 12s | a4b9d75be612a766840c7dca23d1bd1fc0a0235acfeae68476a8b1bf3cde9ad2 | 96.853s / 104.730s | 9 / 12 / 21 |
| S03 | 2106049831727788032 | 8s | 0b5c2ab28410346c3dbc4ac6ef156999e3d2f4de2205fa1613a6fb02fae6add9 | 63.724s / 71.806s | 4 / 8 / 12 |

本轮 **2 physical POST / 2 raw candidates / remaining0**；历史原 S01 + 旧 continuity 两镜共3次，本任务家族 H3 合计5次，未改 Vidu 消费。两次 response usage 均确认3张图，合计 total_seconds33；actual credits/cost 未返回，保持 null。Operator monetary bound 不是账单。Physical-start fence 的初始 UNKNOWN 原文保留，terminal/status/fetch 已补证 known outcome，不重写历史 fence 或重试 POST。

每镜保存 `request.json`、`response.json`、`status-*.json`、`compiled-prompt.txt`、`source-hashes.json`、`reference-mapping.json`、`physical-submit-consumption.json`、`fetch-receipt.json`、`terminal.json`。Credential 未写入这些文件；run 文本模式扫描为0。Durable intent、exact preview、Budget Guard/reservation、cloud-egress、one-use permit 继续经既有 seam，不裸写 Manifest；候选未 activation。

## Raw Failures And Local Edits

S02 原片 `shot02/output.mp4` SHA `44715c6a44a9ad357abfac34e38db02053b9a7bfa0fa2d82c6705f9bec590b3a`，13,108,563 bytes、12.25s/294帧。D 近景接点、主角身份、拉回房间和恢复可用，但解除 C 时短暂分裂，raw gate **FAIL**。

局部剪辑先失败：v1 从 frame141 才切走，独立检查 H3-EDIT-01 指出136–140已分裂。v2 在130–167（5.4167–7.0s）使用同一时段 COCO 近景 cutaway，保留此前手接触与之后单个 C 被降低、落地、恢复。`shot02/edited-v2.mp4` SHA `d994677a7d04283166eab5d8aa01cdb47ad36b4200852e14a5510a9897342937`；音频 packet hash 与 raw 相同。MCP125ms抽帧、整段1x和独立 finding 修正后 gate PASS，才提交 S03。没有宣称完整无省略的脱落物理过程。

S03 原片 `shot03/output.mp4` SHA `fa3d8abc7ad2fbde4be48683800161d53581d7df0fd2c381d274d3fe962b52f4`，8,395,135 bytes、8s/192帧。开头把已经解除的 C 再贴回 Nosha 头上并重复解除，raw gate **FAIL**。保留该原片，剪去前2s，派生 `shot03/edited.mp4` SHA `b6af272d1ddcbcbf484fa600d1d0706ba6a5cd9f3df9c2258ca58aea576eef86`，6s；随后最终剪接从 raw3s开始，只使用最后5s，不追加 Provider 请求。

第一次 composition SHA `21dca68061e65ab05f8aa0d8fb9ebdf34a5fcc796e0edddfcab569f16fe2163d` 在26.333s有明显位置回跳，独立 H3-CUT-01 **FAIL**，已保存为 `rejected-v1-review.mp4`。最终将 S02 endpoint 从11.25s前移到250/24=10.4167s，将 S03 start 从raw2s移到raw3s；切点25.5s，先起步再换机位向前，不返回较早窗边位置。原 raw、失败 edit、失败 composition、findings 和消费均保留。

## Exact Viewing Output And Assessment

最终 **`review.mp4`**（同 bytes `review-v2.mp4`），SHA **`753ab5285abba746f26c97e3162027a3f4d1d34bd0e0ab67b7f414d1fa555c8e`**，24,436,286 bytes，container30.569s、video30.500s/732帧、H2641344×768/24fps、AAC32kHz stereo。Requested16:9、actual7:4 deviation 保留，没有偷偷裁画幅。它是 development viewing derivative，不是 raw Provider 全目标 PASS、Production renderer交付或 P6/Final Acceptance。

| Concern | Current finding | Limit |
| --- | --- | --- |
| Main identity | Broad PASS | COCO/Nosha可辨、手机归属和高矮关系保留；不证明长期、背面或换场景一致性。 |
| Action / causality | Readable edited recovery | D近景→同房间恢复→接触/放下C→向右移动可读；移除中段用cutaway省略，raw两镜仍FAIL。 |
| Cuts / camera | Limited visual PASS | 最终25.458→25.500s继续向右，推车落到身后；换机位允许步态/间距变化。两个接点正常速度采样复核，无frame-exact或一镜到底要求。 |
| Pets / props | Imperfect | C形态/尺寸、水果堆和细小道具仍漂移；用户淡化此项不等于原画布精细目标已实现。 |
| Original dialogue | Single original source retained | 原S01只出现一次、新镜没有绑定对白参考，不重新配音。 |
| No extra speech / human viewing | NOT_EVALUATED | standalone新镜large-v3空text；完整edit另识别“谢谢大家”且时间30–59.98s超出30.569s成片，输出不可靠。保留raw，不伪造人工听音或无人声PASS；等待用户看听此 exact edit。 |

Parent在浏览器以1x完整播放，exact browser SHA一致、ended=true、wall30.8396s、123个250ms样本；证据 `final-v2-normal-speed-{capture,playback}.json`、`mcp-final-v2-{probe,frames,transcript}.json`、`final-review.json`。播放采样只证明播放和所查视觉，不能替代人工听音。全片FFmpeg decode无错误，`composition-evidence-v2.json`记录exact sources、trims、命令与probe。

独立 reviewer_high `/root/h3_character_continuity_review` 对最终SHA检查25.250–26.500s，finding set为空；它只用MCP/帧证据，没有连续播放或听音。此前blocking findings已由Parent调查、本地修改并在新SHA重验，未追改旧结论。受管Kimi concept审查 invocation `21607acd-9d96-4635-8d8a-a0e735335bb7`、contract `c640f85e-fdac-4f7b-ad13-8205f0e8b2f5` 经sealed qualified Docker route，PARSED/exit0；其10s过载意见促成实际12s，不把text-only审查当媒体通过。

## Evidence Index

Boundary：METASO MiniMax-H3 / remote Ref2VA / Context IRtrue / original 3 PNGs + preceding H3 video。两个任务是依赖参考链，edited derivatives与不同proof layers不是额外独立实验。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CUT-S02-FETCH | metaso:2106047316655992832 | coco-nosha-metaso-h3-cut-continuity-repair | metaso-h3-cut-repair-attempt02 | N/A | 44715c6a44a9ad357abfac34e38db02053b9a7bfa0fa2d82c6705f9bec590b3a | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/shot02/fetch-receipt.json |
| CUT-S02-RAW | metaso:2106047316655992832 | coco-nosha-metaso-h3-cut-continuity-repair | metaso-h3-cut-repair-attempt02 | N/A | 44715c6a44a9ad357abfac34e38db02053b9a7bfa0fa2d82c6705f9bec590b3a | AGENT_VISUAL | FAIL | C_SPLIT | SAME_EVIDENCE_NEW_PROOF_LAYER | CUT-S02-FETCH | runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/shot02/continuity-gate-raw.json |
| CUT-S03-FETCH | metaso:2106049831727788032 | coco-nosha-metaso-h3-cut-continuity-repair | metaso-h3-cut-repair-attempt03 | N/A | fa3d8abc7ad2fbde4be48683800161d53581d7df0fd2c381d274d3fe962b52f4 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/shot03/fetch-receipt.json |
| CUT-S03-RAW | metaso:2106049831727788032 | coco-nosha-metaso-h3-cut-continuity-repair | metaso-h3-cut-repair-attempt03 | N/A | fa3d8abc7ad2fbde4be48683800161d53581d7df0fd2c381d274d3fe962b52f4 | AGENT_VISUAL | FAIL | OPENING_STATE_RESET | SAME_EVIDENCE_NEW_PROOF_LAYER | CUT-S03-FETCH | runs/coco-nosha-metaso-h3-continuity-repair-20261002-001/shot03/continuity-gate-raw.json |

## Verification And Publication

`exact-evidence-verification.json`核对request/native-body hash、3 PNG/video实际data bytes、两个physical fences、known terminal/fetch、raw与edited gate exact hashes和credential模式零命中。未修改Production code，不把其他窗口的改动归为本任务：开始HEAD `4b13712`，期间观察`fc4388e`，最后其他窗口提交`e62a0db`。仅本记录和旧记录supersession notice进入本轮local documentation commit；`.codex/config.toml`既有staged变更保持，不push/release。

文档exact commit range由标准Harness隔离验证，run ID `metaso-h3-cut-repair-20261003-docs-001`；它不执行Provider/media，不构成观看验收。RAG experience检索因shard incompatible返回exit3，未foreground rebuild/index刷新；后续Agent应直接读此exact record/run。

## Learning Evaluation And Stop

`distill-ai-video-learning`: **no_candidate**。同一依赖链中两镜有不同失败，authoring、时长、video参考和local editing同时变化，没有受控归因；也不构成既有local H3/first-frame claim的新独立验证。没有placeholder、adoption或Skill/Policy/Gate变更。

本轮两个submit已耗尽。当前交付让用户看听剪接版；原片失败说明H3不能仅靠参考与prompt保证状态连续。是否继续实验应先依据此版实际观看反馈，不自动提交第三个候选。
