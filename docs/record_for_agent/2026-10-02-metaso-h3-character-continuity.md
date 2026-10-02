---
record_kind: media_experiment
topic_id: coco-nosha-metaso-h3-character-continuity
learning_eligibility: eligible
evidence_index_version: "1"
---

# METASO H3 Character Continuity Record

Date: 2026-10-02

## Goal And Boundary

用户在首段视觉FAIL、声音接受之后明确要求：“这个不重要我觉得关键是后面能不能保持一致性,角色你再做两个shot看看”。本轮以S01实际外观为连续性基准，验证COCO/Nosha后续转头、互动和移动；不修原宠物解剖，不改写[S01 FAIL](2026-10-02-metaso-h3-canvas-method.md)。独立封存最多两个新提交，每镜一个候选，未重抽。未调用其他Provider、新增图片、重新配音或重构架构。

初始HEAD `b844bd3`。现有METASO adapter及canonical paid/Registry/committer seam保持；新增代码仅在任务授权的ignored run内：`prepare.py`、`execute.py`、`verify-experiment.py`和只读观看server。未改Production source。Run为 `runs/coco-nosha-metaso-h3-continuity-20261002-001/`，下文路径相对此目录。

## Exact Inputs And Requests

三张原PNG继续按原字节使用：Image1场景 `a-scene`，Image2单一COCO `b-COCO`，Image3单一Nosha `c-Nosha`。SHA分别为 `66f13af336408a826dd17b7c8df68048592ca23bbf99dca312539dd8f2674b62`、`5f3996fbe878d848d0ee6d71f689114f944677b9e739ab816a5e06b048e41920`、`5d73df034a0b2a6637f29f8406fbd9f08a54f1636f34c03aea7a239239b134e6`。

Video1负责前段实际主角外观、相对尺度、道具和动作状态；不是第四张图，也不重演原事故。S01原片15.083秒超过API15秒参考上限，stream-copy前348帧并去音轨，实际video14.5秒/container14.542秒，SHA `20b8d54170b2a2417b62e0d4ece578a26e47f6a21c4932c2a68362e83cc88821`。S03再使用S02的完整静音stream-copy参考。两次派生均保存source/output hash、命令和probe于 `s0{1,2}-reference-derivation.json`，没有生成新帧或声音。

每个请求均为 `MiniMax-H3`、8秒、768P、16:9、`context_ir_enabled=true`，content为text + 3 image_url + 1 video_url。没有audio_url；用户接受的原5秒对白仍只在S01，不重复。Context IR文本未由API返回，内部转换NOT_EVALUATED。S02取下C、站稳、看手机；S03沿货架行进、避让、停稳。完整prompt与实际body分别在 `shot0{2,3}/{compiled-prompt.txt,request.json}`。使用已有官方prose compiler，没有新H3 DSL或旧Vidu repair文本。

## Consumption And Exact Outputs

| Shot | Provider task | Request bytes | Success observation / complete fetch | Usage input / output / total seconds | Exact output SHA256 |
| --- | --- | --- | --- | --- | --- |
| S02 | 2106028625392300032 | 29948310 | 98.200s / 105.409s | 15 / 8 / 23 | 9b602ef313cba93193039ce4d120ee8a0ed198c8e806022e61f62c84561784c9 |
| S03 | 2106030735566172160 | 20344119 | 89.873s / 97.055s | 8 / 8 / 16 | 40d68b6eab3d2d5f92403d73a716089496e24d7e02ce2f706dbeb2f5c91a6b75 |

本轮 **2 physical POST / 2 candidates / remaining0**，连同历史S01共3个H3请求；原Vidu计数不变。Provider每次确认input_image_count3，合计usage total_seconds39；这不是credits或账单。响应未提供actual credits/cost，均null。内部每call5,000,000、总10,000,000 CNY microunits仅operator bound，不是实际费用。

MP4分别为 `shot02/output.mp4`（9,720,388 bytes）和 `shot03/output.mp4`（10,026,759 bytes）。两片均H264、8.000秒、192帧/24fps、1344×768、AAC32kHz stereo；实际ratio7:4偏离requested16:9，不裁切掩盖。标准fetch receipt落盘，Manifest保持VALIDATE，未activation/P6/Final Acceptance。Key仅stdin进入进程环境/injected supplier，未进入run、source、log、receipt或git。

## Media Findings

两镜明确调用project-local video-analysis MCP的probe、每0.5秒抽帧、scene detect和ASR，raw保存 `shot0{2,3}/mcp-*.json`。Parent另用只服务exact MP4的loopback endpoint完整1x播放并采样：S02 wall8.6135秒、S03 wall8.6566秒，均rate1/ended/17样本，保存 `normal-speed-{capture,playback}.json`和JPEG。只读server已停止；不把浏览器播放或ASR当作人工听音。

| Concern | Result | Evidence and limit |
| --- | --- | --- |
| COCO/Nosha broad identity | PASS for these two Shots | 奶油白/黑机器人、黄色头灯、机械臂/圆轮底座，与高大黑长外套/马甲/领带、白手套、透明盛水头及内部生物保持；无明显互换或克隆，高矮关系稳定。 |
| Pose and movement | PASS limited coverage | S02俯身/抱取/站直/转头，S03约2–5秒侧向行走与COCO滚动、6–8秒回正；未取得Nosha完整背面、极近景或换环境验证。 |
| Main phone and shelter appearance | PASS broad | COCO持续持相同黑竖屏/蓝界面；同木质日光收容处。手机有可读UI，精细prop忠实性不成立。 |
| Camera | PASS observed continuity | 两片MCP threshold.25各一个scene，原速没有明显硬切；轨迹没有完整实现预计换角度，S03回到近似旧前景，不能证明稳定房间floorplan。 |
| Secondary pets/props/causality | Imperfect; not character proof | S02约0.5–1.8秒推车自行回正，C抬起时拉长/变大、落地再胖圆，水果/箱旁宠物位置承接有偏差；不把主角PASS扩大为全场景或原解剖PASS。 |
| S02 speech | PASS human | 用户随后明确“没有人声，只有音效”，exact MP4绑定 `output-audio-user-feedback.json`。 |
| S03 speech | PASS analyzer observation | large-v3零segments/空text，未识别原句或新对白；无人类听音/声线或整体音质验收。 |

S02早期base/small/auto-language ASR给出互不一致短句/重复乱码，先保存音频NOT_EVALUATED并停止推进；证据修复large-v3空text后才允许S03，用户之后补充无人声。原 `continuity-gate-pending-audio.json`、analyzer-only revision、全部raw transcript保留，没有改写旧证据。

独立read-only `/root/h3_character_continuity_review`（reviewer_high）未读取Parent verdict，核对原图/三段MP4抽帧和S03 hash；支持有限姿态下主角可辨、无交换/克隆，指出精细/完整背面NOT_EVALUATED与次要推车/宠物承接问题。Reviewer未播放/听音，Parent补原速视觉、S02用户补听音；详见 `independent-media-review.md`。主角可辨一致性两镜PASS不代表完整电影/长期Provider qualification。

## Engineering And Verification

20项现有METASO离线测试PASS；`exact-evidence-verification.json`核验两个physical fence、body/hash/content类型、MP4 hash、时长和S03前序gate，无网络或生成。Zero-submit preflight纠正empty dialogue、Registry containment、完整remote intent，以及graph/QA先于schema2.8升级的顺序。修改intent后旧graph被canonical lineage check正确拒绝，physical0；失败bundle保留，最终用fresh `production-final`先封存完整intent再建graph，未裸写Manifest或重试付费请求。

受管Kimi mapping invocation `7a84f051-6c27-4697-8d43-5889058a81e4`经过sealed/qualified Docker route，2 wire后response-body CONNECTION_ERROR/OUTCOME_UNKNOWN，无完整结果可依赖，未盲重试；Parent重新检查源码和标准loader。CodeGraph关系请求超时，未声称取得图证据。当前无Production源码变化，不触发新的implementation review；独立媒体验证另行完成。

文档最终exact commit range的policy checks见run内 `direct-policy-verification.json`，不以direct checks冒称isolated Harness receipt。Unrelated staged `.codex/config.toml`保持；后来观察到的AOCI改动由其他session自行提交为 `43d4a01`，本任务未stage/commit其文件。仅本记录与原记录的后续实验notice进入local commit，无push/release。

## Evidence Index

Runtime boundary: metaso_h3 / MiniMax-H3 / remote Ref2VA / Context IRtrue / original three PNGs + predecessor video. S02/S03为不同task但同一依赖连续参考链，不能机械当成独立重复实验。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H3-S02-FETCH | metaso:2106028625392300032 | coco-nosha-metaso-h3-character-continuity | metaso-h3-continuity-attempt02 | N/A | 9b602ef313cba93193039ce4d120ee8a0ed198c8e806022e61f62c84561784c9 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/coco-nosha-metaso-h3-continuity-20261002-001/shot02/fetch-receipt.json |
| H3-S02-CHAR | metaso:2106028625392300032 | coco-nosha-metaso-h3-character-continuity | metaso-h3-continuity-attempt02 | N/A | 9b602ef313cba93193039ce4d120ee8a0ed198c8e806022e61f62c84561784c9 | AGENT_VISUAL | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | H3-S02-FETCH | runs/coco-nosha-metaso-h3-continuity-20261002-001/shot02/continuity-gate.json |
| H3-S02-AUDIO | metaso:2106028625392300032 | coco-nosha-metaso-h3-character-continuity | metaso-h3-continuity-attempt02 | N/A | 9b602ef313cba93193039ce4d120ee8a0ed198c8e806022e61f62c84561784c9 | HUMAN_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | H3-S02-FETCH | runs/coco-nosha-metaso-h3-continuity-20261002-001/shot02/output-audio-user-feedback.json |
| H3-S03-FETCH | metaso:2106030735566172160 | coco-nosha-metaso-h3-character-continuity | metaso-h3-continuity-attempt03 | N/A | 40d68b6eab3d2d5f92403d73a716089496e24d7e02ce2f706dbeb2f5c91a6b75 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/coco-nosha-metaso-h3-continuity-20261002-001/shot03/fetch-receipt.json |
| H3-S03-CHAR | metaso:2106030735566172160 | coco-nosha-metaso-h3-character-continuity | metaso-h3-continuity-attempt03 | N/A | 40d68b6eab3d2d5f92403d73a716089496e24d7e02ce2f706dbeb2f5c91a6b75 | AGENT_VISUAL | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | H3-S03-FETCH | runs/coco-nosha-metaso-h3-continuity-20261002-001/shot03/continuity-gate.json |

## Learning Evaluation And Conclusion

`distill-ai-video-learning`: **no_candidate**。本次同一参考链的两个后续任务支持有限case的身份可辨，缺独立repeat/受控multi-arm，不能归因于视频参考或Context IR，也不更新local H3灯塔/T2VA与literal-first-frame既有claims。没有新placeholder或采纳target变更。

值得继续使用H3验证主角跨镜头一致性；当前证据比一次API跑通更具体，但不足以保证长片、完整背面、宠物/道具状态或整个场景一致。两个新submit已经耗尽，本轮停止，不自动追加。
