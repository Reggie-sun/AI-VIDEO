---
record_kind: media_experiment
topic_id: coco-nosha-metaso-h3-canvas-method
learning_eligibility: eligible
evidence_index_version: "1"
---

# METASO H3 Canvas-Method Record

Date: 2026-10-02

## Purpose And Boundary

先读取任务初始HEAD `13cad76`（第八次Vidu quality rejection）、原画布记录及当前baseline，只接METASO MiniMax-H3并验证一次完整multimodal画布方法。用户明确排除新大Spec/Plan、Seedance、T8、本地H3、MiniMax官方API、新Vidu、新素材、UI、fallback与连续抽卡。原Vidu 8/8及旧local H3消费保持；本轮独立 **1 request / 1 candidate**。

原canvas `f0ed223b-090e-4ed6-b394-283f8b7dbd07` / selected `node_bq6wajb5xe` / `视频 10 (17)`，UI可见Seedance2.5/全能参考/17秒/三图/COCO声线参考。Composer不等于历史exact submit receipt。新实验按METASO真实15秒上限保留完整压缩事件序列，没有拆成五镜。

## Actual Public API Contract

2026-10-02核对[官方GitHub](https://github.com/meta-sota/ComfyUI-MiniMaxH3-API)的 `api_client.py`、`nodes.py`、README及[METASO公开页面](https://metaso.cn/minimax-h3)的API示例。完整限制与owner见[Provider contract](../metaso-h3-provider.md)。

- Base `https://metaso.cn/api/minimax`；Bearer `METASO_API_KEY`；model `MiniMax-H3`。
- Create `POST /v2/video_generation`，body `model/content/duration/resolution/ratio/context_ir_enabled`，ack `task_id`。Query `GET /v2/query/video_generation/{task_id}`，response `task.id/model/status/content.url`。
- 官方content类型text/image_url/audio_url/video_url，后三者role为reference_image/reference_audio/reference_video。Adapter发送Registry exact bytes的inline data URI；video reference已实现，本轮未使用。
- 输出duration整数4–15秒、768P/2K，ratio adaptive/21:9/16:9/4:3/1:1/3:4/9:16。README旧5秒下界落后于当前节点/页面4秒下界。不提交臆测的seed/fps字段。
- Context IR默认开启，可用 `context_ir_enabled: false` 关闭，请求优先于console global。旧插件client未发送此字段，METASO自身公开示例明确支持。本轮显式true；响应没有IR文本，内部转换仍不可检查。
- 成功URL通过同task重查，在内存以credential-free、public-IP-pinned、原host TLS/SNI、禁redirect HTTPS GET下载。持久化response/status对签名URL只留origin/hash，不保存完整签名URL或API key。

## Exact Inputs And Reference Responsibilities

Run：`runs/coco-nosha-metaso-h3-canvas-method-20261002-001/`（下文evidence文件均相对该目录）。Ordinal来自原 `reference-provenance.json` 与 `reference-ordinal-join-proof.json`，职责来自实际图像inspection及canonical creative evidence。复用已认证恢复的 **canvas-served exact PNG bytes**；原始上传前bytes身份仍NE。

| H3 binding | Exact source | SHA-256 | Responsibility |
| --- | --- | --- | --- |
| Image 1 / a-scene | `runs/coco-nosha-host-recovery-20260928-001/reference-source/reference-01.served.png` | `66f13af336408a826dd17b7c8df68048592ca23bbf99dca312539dd8f2674b62` | 日光木质收容处、材质、尺度、宠物群与道具关系；图中为中段扑脸受力，不作为第一帧，不平均混合宠物。 |
| Image 2 / b-COCO | 同目录 `reference-02.served.png` | `5f3996fbe878d848d0ee6d71f689114f944677b9e739ab816a5e06b048e41920` | 一个奶油白/黑色轮式COCO、横向黄灯、机械臂；多视图不是多个机器人；剧情使用手机。 |
| Image 3 / c-Nosha | 同目录 `reference-03.served.png` | `5d73df034a0b2a6637f29f8406fbd9f08a54f1636f34c03aea7a239239b134e6` | 一个高大黑长外套/西装Nosha、白手套、透明圆柱水容器头与内部生物；多视图不是多个Nosha。 |
| Audio 1 | `runs/coco-nosha-vidu-voice-recovery-20260930-001/source/selected-canvas-dialogue-48k.wav` | `52975f4a3df74a4ec294f712d6afdc563d1da770323bc59f912dba2d58fffb77` | 已获用户源声线/完整对白/只一次确认的5秒48kHz stereo PCM WAV，不重新配音。 |

三PNG分别2,583,232 / 1,622,654 / 1,461,375 bytes，WAV960,124 bytes。原完整 `production/creative/shot.yaml`、canonical角色/场景与导演文字保留，run内通过标准loader/Registry创建等价单段creative input。职责→global shooting rules→timeline→预备/发起/接触/受力/反馈/恢复进入普通导演prose；采用官方Image/Audio ordinal grammar，无自创DSL，无历史Vidu budget/gate/seed/transport repair文字。

`compiled-prompt.txt` 为实际3910字符，SHA `ec932a720e307e9230aeb8ba11331067ff080e67896ef4cf56547a7f04a7a61e`。`request.json` 8,845,663 bytes，SHA `185b7519da1f62d3b0f2521bc4ac32b20d6fcf38404d52074e7fa9d3f5fb7400`；MiniMax-H3、15秒、768P、16:9、context_ir_enabled true、3 image / 1 audio / 0 video。`exact-input-proof.json`绑定decoded body素材bytes/hash与对白一次。

## Implementation And Verification

`69f99c2`新增 `src/ai_video/production/metaso_h3.py`、离线tests及最小contract/policy routing；`9110c69`补same-task/credential-free fetch tests；`b425ac6`修复http.client Title-Case response headers与继承httpx式consumer的lookup差异。Adapter复用既有remote prose compiler、typed receipt、paid quota/Budget Guard/egress/one-use permit、generation service与唯一committer，不重构框架/default/fallback。

Header缺陷有可靠RED `header-case-red.log`；修复后133 focused PASS，包括20项METASO tests。`direct-policy-verification.json`绑定exact HEAD `b425ac600a97ff0fd8912fe0aee729f41c2ec069`与base `ac5b1de`，10项checks全部PASS，Provider suite860 PASS，snapshot unchanged。既有多Provider离线回归不代表其他Provider真实调用。Canonical isolated Harness receipt **null**，不以direct checks冒称隔离Harness。

受管Kimi mapping与review均经sealed合同/qualified Docker route。首次review `60e40ca6-250b-4d55-adb7-44a43056c90b`为connection error/OUTCOME_UNKNOWN，partial隔离；round2 `44a16d6e-fd9b-4af7-88e0-c08314c3a586`绑定 `9110c69`，无blocking finding，Parent保留2xx异常ack fail-closed。Round3 `cd35a0a4-6458-4dbe-911e-7244b3f3ac91`仅审 `b425ac6` header fix，3 wire requests、完整实际Reads/identity/hash核验，无blocking defect，Parent接受工程修复，非媒体acceptance。

另session随后修改AGENTS/Harness/context/matrix/baseline/tooling，保留其dirty/staged/untracked文件，不覆盖或commit。本轮review于13:19:39.585886 UTC完成，AGENTS修改mtime13:19:40.251422 UTC；reviewed source/tests仍match。Baseline更新遇到另一writer同文件改动时停止写入，本任务事实由独立record与已提交Provider contract保存。AOCI维护blocked、6 stale managed entries/79 observed pending，未改正式索引或宣称对齐。Agent Memory experience retrieval exit3/library-incompatible按Skill排队，未前台重建/重试。

## One Real Submission And Recovery

`physical-submit-consumption.json` fsynced fence与canonical paid receipt证明一个物理POST。无POST preflight发现Manifest2.4不支持既有paid feature，sole committer显式升级2.8；零效果preflight证据保留。

12:56:53.796199 UTC唯一POST，ack task `2106005640266379264`且canonical接受receipt落盘。随后run-local日志误用不存在的submission property；恢复只允许GET重查同task，禁止第二POST。DNS fake-IP198.18.2.178被原public-address检查正确拒绝；两独立DoH一致证明files.metaso.cn真实A为39.107.127.154，run-only exact-host解析使用该public地址，原pin/TLS/SNI/noauth/noredirect保留，无系统VPN修改。Header修复后canonical fetch成功；run-local dataclass JSON错误发生在fetch receipt落盘之后，标准loader核验exact artifact后复制 `output.mp4`，无重生成。

Provider task created→updated **70秒**；首次success观察 **128.212秒**；POST→canonical fetch **557.976秒**（含本地日志/query/DNS/header恢复）；POST→最终copy观察625.283秒。`actual-consumption.json` / `status-000.json` / `response.json` / `fetch-receipt.json`保存receipt/task/usage/latency。Usage：input_audio_seconds5、input_image_count3、input_seconds0、output_seconds15、total_seconds15。**actual_cost / actual_credits=null**；内部2,000,000 CNY microunits仅operator bound，不是实际费用。Key仅经进程环境 injected supplier，不存source/log/manifest/receipt/git。

## Exact Output And Media Assessment

`runs/coco-nosha-metaso-h3-canvas-method-20261002-001/output.mp4`：SHA `7ff47f55bbf19e9014aa7443d37f3a45a1a56bea62a0565707b583469046aba4`，17,448,770 bytes、H264/15.083秒/362帧/24fps/1344×768、AAC32kHz stereo。实际pixel ratio **7:4** 偏离请求16:9，不裁切隐藏。Manifest10/VALIDATE，fetch已记录，未activation/P6/Final Acceptance。

明确调用project-local video-analysis MCP probe、每0.5秒31帧、scene检测、整段zh ASR，保存 `mcp-{probe,frames,scenes,transcript}.json`。另用Chrome原生MP4 player、仅服务exact MP4的loopback只读endpoint完整1×播放，每0.5秒capture共30样本，保存 `normal-speed-{capture,playback,viewing}.json` / JPEG；服务已停止。Parent基于实际播放时间戳/样本判读，没有声称人工输出聆听。

| Concern | Verdict | Exact result |
| --- | --- | --- |
| Identity vs Vidu | NOT_EVALUATED comparative | 本片COCO/Nosha大体外观持续可辨，无多视图克隆；历史Vidu duration/authoring不同，不能作受控优越性结论。 |
| A/B/C/D swapping | PASS | 颜色与剧情职责大体可区分，未见明显互换；正确形态另行FAIL。 |
| Action / causality | FAIL | B→A→容器/C→Nosha→推车/果篮→D主链可读，但B跟A坠落；C多次整体跳跃并用肢体抱头，偏离指定吸附/受力动作。 |
| Reference responsibility comprehension | NOT_EVALUATED | 场景/COCO/Nosha broad作用可见，pet细节不忠实；无IR文本，不能检查内部理解。 |
| Morphology / props | FAIL | A兔样爪足；B鱼形爪足而非无足腹褶滑行；C四肢软宠而非六瓣吸盘；D蛙/蜥蜴爪足、头口而非指定软壳/五足/腹口；水果橘/南瓜状。Nosha白手套符合Image3，不是失败。 |
| Camera continuity | PASS | 正常速度低→高→低→木箱运动自然连续，MCP threshold.25为一个scene；不证明精确逆时针轨迹或排除所有隐蔽转场。 |
| Dialogue text / count | PASS | 目标句ASR完整一次，0–4.74秒，无额外transcribed speech。 |
| Audio placement | FAIL observation | 对白从片头开始，早于约3–5秒手机展示；此项描述音画节奏偏差，不否定用户对声音的接受。 |
| Audio quality / voice | PASS user | 用户随后确认本H3输出“声音可以”。取代此前机器层声线NOT_EVALUATED；5秒PCM correlation.6543/lag.00025秒仍只为客观对照，不是人工验收依据。 |
| Added cuts / roles / dialogue | PASS observation | 未见乱切镜/串角色或额外ASR对白；手机有可见UI/text，违反不可读屏幕要求。 |

Overall creative goal **FAIL**：形态、角色动作与音画职责偏差，非API未跑通。Raw findings在 `evaluation.json`，第一轮止步，不自动第二次，不降低标准或激活失败成片。

### User Audio Acceptance — 2026-10-02

用户明确反馈“fail主要体现在哪里,声音可以”。Exact task/MP4绑定在 `output-audio-user-feedback.json`；`evaluation-after-user-audio-feedback.json`只补充用户声音PASS，原 `evaluation.json`及音画时间戳完整保留。当前主要失败依据是宠物/果实形态、B跟随A坠落及C附着动作；声音本身不再是未验收项。用户未另行确认手机展示同步或整体画面，不据此激活、改写视觉FAIL或生成第二次。

## Evidence Index

同provider/task/body/output anchor只算一个independence unit；technical/analyzer/Parent视觉不增加实验计数。Runtime边界为 `metaso_h3 / MiniMax-H3 / remote Ref2VA / context_ir_enabled true`。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H3-FETCH | metaso:2106005640266379264 | coco-nosha-metaso-h3-canvas-method | metaso-h3-canvas-attempt01 | N/A | 7ff47f55bbf19e9014aa7443d37f3a45a1a56bea62a0565707b583469046aba4 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | runs/coco-nosha-metaso-h3-canvas-method-20261002-001/fetch-receipt.json |
| H3-MEDIA | metaso:2106005640266379264 | coco-nosha-metaso-h3-canvas-method | metaso-h3-canvas-attempt01 | N/A | 7ff47f55bbf19e9014aa7443d37f3a45a1a56bea62a0565707b583469046aba4 | AGENT_VISUAL | FAIL | MORPHOLOGY_ACTION_AUDIO_PLACEMENT | SAME_EVIDENCE_NEW_PROOF_LAYER | H3-FETCH | runs/coco-nosha-metaso-h3-canvas-method-20261002-001/evaluation.json |
| H3-ASR | metaso:2106005640266379264 | coco-nosha-metaso-h3-canvas-method | metaso-h3-canvas-attempt01 | N/A | 7ff47f55bbf19e9014aa7443d37f3a45a1a56bea62a0565707b583469046aba4 | ANALYZER | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | H3-FETCH | runs/coco-nosha-metaso-h3-canvas-method-20261002-001/mcp-transcript.json |
| H3-AUDIO-USER | metaso:2106005640266379264 | coco-nosha-metaso-h3-canvas-method | metaso-h3-canvas-attempt01 | N/A | 7ff47f55bbf19e9014aa7443d37f3a45a1a56bea62a0565707b583469046aba4 | HUMAN_AUDIO | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | H3-FETCH | runs/coco-nosha-metaso-h3-canvas-method-20261002-001/output-audio-user-feedback.json |

## Learning Evaluation And Next Experiment

`distill-ai-video-learning`：**no_candidate**。只有一个METASO whole-sequence attempt，无Context IR开关或prompt职责受控多arm；与历史Vidu/local H3同时改变provider、duration、authoring，不能隔离原因。既有 `h3-shot-local-visible-context` 为灯塔T2VA跨字段冲突，`h3-i2v-first-frame-condition-renders-at-head` 为local fl2va literal first-frame，不属于本Ref2VA case，不更改其active/pending状态。

第二次H3实验有条件值得：完整连续镜头与主连锁事件已有可观察能力，适合只检验“scene reference形态与canonical文字职责优先级”的一个authoring假设；保持三exact PNG、source WAV、完整剧情、15秒/768P/16:9/Context IRtrue，不换图/配音/拆镜或同时改多个变量。仅建议，未证明能修复，不授权自动POST，本轮停止于第一exact FAIL。

## Publication And Remaining Boundaries

代码与记录仅local commits，无push/release。Run/media为任务授权的ignored evidence。Unrelated staged `.codex/config.toml`及另session文件保持，不stage/commit。记录及声音反馈补证期间零Provider/media生成，未前台刷新RAG或解决AOCI历史debt。输出声音已获用户接受；原画布成片受控比较、Production qualification及整体成片验收仍未完成。新增human proof仍为同一个attempt，automatic learning evaluation继续no_candidate。
