---
record_kind: media_experiment
topic_id: fanxiang-transom-metaso-h3-replication
learning_eligibility: eligible
evidence_index_version: "1"
---

# Fanxiang Transom — METASO MiniMax-H3 Replication Test

Date: 2026-10-02 UTC / Asia/Hong_Kong

## Result And Scope

在[作品拆解](2026-10-02-fanxiang-episode-one-canvas-analysis.md)完成并提交 `9211e82` 后，按用户授权执行 **一次 METASO MiniMax-H3 多参考图生成**，复现《反相之地第一集》V36“补镜头10C”：小龙从606门上气窗观察狗哥，狗哥抬头微笑、脖子伸长、贴玻璃叫“龙哥”。

**执行成功，创作复现 FAIL。** exact MP4已下载，人物反应、微笑、靠近玻璃和末段一句“龙哥”成立；长颈异化没有达到原片清晰程度，门上气窗的空间关系也偏离。不是接口报错，也不能据任务 `succeeded` 判镜头成功。没有第二次生成或付费修复，没有推进下一Shot。

本实验是 Development 观察，不构成 Production qualification、P6、Final Acceptance、activation、整集剪辑或发布。只测试本段、本次三个输入与这份编译后的提示词，不概括为“Seedance普遍优于H3”。

## Evidence Locations

实验根目录：`runs/fanxiang-transom-metaso-h3-20261002-001/`，下称 `T/`；原画布证据为 `runs/jimeng-fanxiang-analysis-20261002-001/`，下称 `S/`。这些目录为 ignored local evidence，不随文档commit分发。

| Artifact | Purpose |
| --- | --- |
| `T/output.mp4` | 唯一生成结果，13,235,186 bytes |
| `T/source-normal-speed-sheet.jpg` / `T/output-normal-speed-sheet.jpg` | 原片与H3各9个播放时点的对照板，标签含实际video clock |
| `T/source-normal-speed.json` / `T/output-normal-speed.json` | 各32次Chrome 1x播放截图与前后clock、wall time、exact hash、ended证据 |
| `T/mcp-probe.json` / `T/mcp-frames-index.json` | project-local metadata与31个0.5秒抽帧的索引；图片直接供Parent观察，另保存播放截图 |
| `T/mcp-transcript.json` / `T/mcp-scenes.json` | Whisper small zh与切镜检测结果 |
| `T/media-evaluation.json` | exact输入/输出hash绑定的七项Parent裁决；不是Product QA receipt |
| `T/exact-input-proof.json` / `T/request.json` | native request body与逐图bytes核对 |
| `T/physical-submit-consumption.json` / `T/response.json` / `T/status-012.json` | 一次POST fence、accepted task与首次succeeded观察 |
| `T/production-v2/state/manifest.json` | canonical Development attempt：revision22、phase `validate`、fetch pointer存在 |
| `T/production-v2/state/video-generation/fetch/receipts/1b02c9e732c7f2ca7b889ff22ac74b5acd9d612935509838a0cfe555e0e990be.json` | canonical fetch receipt |

输出 SHA-256：`1e8afdd40ae515bda9e817c1a3ad386d3c39674005f77794238c0e44e4e106d4`。对照V36 SHA-256：`e970276b5ef1df451375c571350d617e7b6445788786a17a68ae80961429d9e9`。

## Input Selection And Reference Responsibilities

沿用画布已存在的图片，未另造人物或场景。捕获的是canvas提供的 **720×405 WebP**，不是用户上传前的原始高分辨率bytes。所有人物sheet均明确解释为同一人的不同视图，不是多人出场。

| Native Order | Registered Input | Responsibility | SHA-256 |
| --- | --- | --- | --- |
| Image 1 | `a-transom` | 绿框横向气窗、完整脏玻璃、藤蔓走廊、对面607门的方向；607不是当前606门牌 | `e2e7dff1ddd241fba0725a3b35f6b44c2c831bba329bffab414021f300f689f9` |
| Image 2 | `b-Gouge` | 狗哥苍白脸、黑眼圈、短黑发、黑衣；正常颈长身份基线 | `b558f65e85381bcf8264efb08b9a9366c2a7a005bcc39cc5127875552aacfdd0` |
| Image 3 | `d-Xiaolong` | 小龙黑T恤、发型与耳饰；门内反应镜头 | `7e8636d2499b9612d7f895bdfc931fbd3176b26adfaf26cea15a33f8ce23e2bf` |

离线第一版还想送“狗哥长颈状态”第四张图；当前 canonical planner 的 character reference role按唯一owner计数，重复Gouge owner不满足四个角色引用的要求，因而在POST前拒绝。Parent核对 `available_role → asset_matches_role → required_role_is_available` 与当前源码，没有把狗哥拆为两个虚构人物或修改共享契约。第一版零Provider effects，证据保存在 `preparation-v1-*` / `production/`；第二版三输入位于 `production-v2/`，整个用户任务仍只有一次POST预算。

**实际没有发送长颈状态图、原片视频或参考音频。** 长颈要求保留为mandatory文本，长颈图片仅用于本地观察。这个输入限制是实验的明确confounder：本例失败不能区分“变形状态图未被输入”“文字适配不充分”与模型本身能力，也不能证明追加图片必然改善。

## Shot Intent And Prompt Adaptation

首次创意编写前实际读取 `open-video`、`hell-grind-aigc-skill` 与 `h3-video`。`open-video`负责覆盖与source-bound intent；semantic guidance负责身份、玻璃和首尾状态；H3 guidance只取适用的镜头表达与输入边界。METASO远程接口使用当前 prose compiler，未把本地ComfyUI的三字段格式冒充远程接口格式。

保留原composer的五个节拍，以 **三个剪辑镜头** 覆盖，不把长颈改为静态人像：

| Time Target | Camera Unit | Required Information |
| --- | --- | --- |
| 0–4s | 门内POV，经气窗看走廊 | 狗哥正常颈长、身体在窗下，建立玻璃与空间关系 |
| 4–6s | 小龙脸部反应 | 小龙察觉异常，无对白，视点仍在门内 |
| 6–9s | 回到同一POV，第三镜开始 | 狗哥抬头，微笑从正常变得诡异 |
| 9–13s | 第三镜连续 | 同一狗哥的颈部明确拉长，身体留在窗下；相机推近不能代替变形 |
| 13–15s | 第三镜连续 | 脸贴近完整玻璃，只说一次“龙哥”；不破窗、不入室、不变灯笼怪 |

第三镜内保持同一观察方向和动作接续；门窗、玻璃和身体位置是handoff约束，没有额外角色或反向越轴。预提交 `director-coverage.json` schema4 validator **PASS**：3units、15秒、7条source-bound intent atoms。相邻镜头重复close-up分类只产生允许的warning，未为了消除warning改变剧情。

中文master为1110字符；实际compiler输出为2869字符，包含按职责排序的三图引用、人物/场景与动作/镜头/对白约束。送出的不是master文件本身，`exact-input-proof.json`逐一验证native body的图像解码bytes与Registry一致。compiled prompt SHA-256：`3336274c4d6b2a25087b5dae335aa9a82713bec7a286df630f296a0aec40fc2a`；native body SHA-256：`2a4fee6ea953dbde5d6e323827b255784f98dc1b369c7c0c5a5507483d711b2e`。

## Execution And Recovery

用户明确选择 METASO MiniMax-H3、多参考图、先做一次。封存Provider/model/inputs、remaining count、exact paid preview、Budget Guard/reservation、egress、durable intent和one-use permit，经既有 `GenerationFeedbackOrchestrator → VideoPlanner/Router → MetasoH3VideoProvider → VideoGenerationService → ProductionStateCommitter` 路径提交，没有直接POST旁路。

| Field | Actual Value |
| --- | --- |
| Model / profile | `MiniMax-H3`；15s、`768P`、`16:9`、`context_ir_enabled=true` |
| Input | text + 3 image references；0 video / 0 audio references |
| Task authorization | `user-approved:fanxiang-transom-metaso-h3-20261002` |
| Attempt | `fanxiang-transom-h3-attempt01` |
| METASO task | `2106040002976804864` |
| Physical POST | 1；remaining0；repair0 |
| Submit / accepted | 2026-10-02 15:13:34.330 UTC / HTTP200 at15:13:37.439 UTC |
| First succeeded observation | 15:14:42.541 UTC，POST后约68.2秒 |
| Provider created→updated | 60秒；不是下载完成时间 |
| Usage | input_image_count3、input_seconds0、output_seconds15、total_seconds15 |
| Actual cost / credits | `null`，未获实际费用证据；2,000,000 CNY microunits为既有operator upper bound，不是市场价或账单 |
| Exact output | H.264 / AAC stereo，15.083s、362帧、24fps、1344×768 |

请求16:9，但实际dimensions约分为 **7:4**；文件未经裁切/缩放，记录规格差异，不将请求参数冒充成片规格。

用户指定 `.env` 的exact path只核对变量名与存在性，发现其中是 `MINIMAX_API_KEY`、没有 `METASO_API_KEY`；未拿另一Provider凭据代用。当前调用使用用户此前明确提供的METASO凭据，通过无回显进程输入注入exact supplier `METASO_API_KEY`，未写repo、`.env`、argv、日志、request、receipt或文档。signed result URL仅保留origin/hash。

首次下载被既有公网检查挡住：本机DNS提供fake-IP。保留succeeded task与消费记录，未重新生成。GET-only恢复先用两个HTTPS DNS resolver核对同一result host的共同公网A，再仅在该fetch进程中指定该host，保留public-IP pin、TLS/SNI、禁止redirect和结果GET无授权header；不修改全机DNS/VPN。

同一task下载成功并经committer持久化fetch pointer之后，本地helper把 `FetchedVideoCandidate` dataclass交给JSON serializer，触发 `TypeError`。不是远程失败或未知生成结果：重新用standard loader确认phase `validate`、fetch receipt和13,235,186字节hash，再从canonical pointer仅本地复制 `output.mp4`。没有再次fetch、POST或activation。`fetch-error.json`保留历史错误，`terminal.json`说明当前已落盘状态。

## Exact Media Review

exact MP4落盘后显式调用project-local `video-analysis`：probe、0.5秒抽31帧、Whisper small zh、scene detect。另在Chrome以 `playbackRate=1` 播放原V36与H3各一次，各32次截图，均到ended；播放是**静音**，没有人工聆听。Parent查看全部31个MCP样本及播放对照板、关键原片帧，不能由截图证明完整混音或精确口型同步。

| Required Finding | Verdict | Exact Observation |
| --- | --- | --- |
| Identity | PASS | 狗哥与小龙的脸、发型及黑衣类型可区分，未见身份交换、多视图sheet变多人；只是视觉对应，不是生物识别认证 |
| Geometry | FAIL | 0–4s、6–9s玻璃下横梁遮住狗哥部分脸，下方仍见胸口，呈开放下半区域；没有建立关闭门上气窗的完整关系。整门不在画面，门是否关闭单项为NOT_EVALUATED |
| Coverage | FAIL | 外侧观察→小龙反应→再观察顺序存在；必须出现的长颈节拍不充分，不能只因三镜顺序正确便PASS |
| Transformation | FAIL | 6–9.5s有颈部绷紧/有限伸展；10–15s主要是脸靠近变大及窗框/背景重构，未呈现原片那种持续、明确的长颈且身体留窗下 |
| End state | PASS | 13–15s狗哥脸在脏玻璃后贴近，窗框与玻璃保持；未见破窗、入室或灯笼怪转换 |
| Dialogue | PASS, bounded | ASR仅识别一次“龙哥”，12.66–14.30s，约在末段；存在原生AAC音轨。起点较13秒target早0.34秒，仅记估计差异；原声身份、听感、完整lip sync与无BGM为NOT_EVALUATED |
| Visual quality | PASS, bounded | 表情、反应与靠近动作可读，未见静帧替代、明显脸部崩坏或额外文字overlay；不替代geometry/transformation裁决 |

MCP scene detect在threshold0.25返回1个scene，漏掉可见的小龙切镜。它是自动切镜线索，不是镜头覆盖裁决；Parent以4.5–5.5s实际画面确认反应切镜存在。metadata与ASR、自动scene统计、Parent视觉分别保留，工具exit0不等于创作PASS。

原片约11.91s、12s附近能看到较长的颈部从黑衣领口接到高处的脸；H3同阶段已经将脸放大到近景，颈部仍短，窗下身体关系被裁掉。这个区别影响观众读到的是“熟人身体发生不可能的变化”，还是“熟人笑着靠近镜头”。后者保留诡异感，却丢失本段最关键的恐怖信息。

总体required findings非全PASS，故本次 attempt 到此停止。输出可供用户观看比较，不作为accepted reference、生产素材或下一Shot的accepted state。

## Evidence Index

非Q0 identity绑定同一 `metaso_h3 / MiniMax-H3 / remote Ref2VA / context_ir true`、task、request body和结果；各proof layer只计 **一个independence unit**。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FX-H3-FETCH | metaso-task:2106040002976804864 | fanxiang-transom-metaso-h3-20261002 | fanxiang-transom-h3-attempt01 | N/A | 1e8afdd40ae515bda9e817c1a3ad386d3c39674005f77794238c0e44e4e106d4 | PROVIDER_RECEIPT | PASS | NONE | NEW_ATTEMPT | NONE | `runs/fanxiang-transom-metaso-h3-20261002-001/terminal.json` |
| FX-H3-VISUAL | metaso-task:2106040002976804864 | fanxiang-transom-metaso-h3-20261002 | fanxiang-transom-h3-attempt01 | N/A | 1e8afdd40ae515bda9e817c1a3ad386d3c39674005f77794238c0e44e4e106d4 | PARENT_VISUAL | FAIL | GEOMETRY_AND_TRANSFORMATION | SAME_EVIDENCE_NEW_PROOF_LAYER | FX-H3-FETCH | `runs/fanxiang-transom-metaso-h3-20261002-001/media-evaluation.json` |
| FX-H3-ASR | metaso-task:2106040002976804864 | fanxiang-transom-metaso-h3-20261002 | fanxiang-transom-h3-attempt01 | N/A | 1e8afdd40ae515bda9e817c1a3ad386d3c39674005f77794238c0e44e4e106d4 | ANALYZER_TRANSCRIPT | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | FX-H3-FETCH | `runs/fanxiang-transom-metaso-h3-20261002-001/mcp-transcript.json` |

## Verification, Learning And Publication

当前接口测试 `python3 -m pytest tests/test_production_metaso_h3.py -q`：**20 PASS**。coverage validator PASS，只有允许的相邻scale重复warning。standard Production loader重新打开fetch pointer，bytes/hash相符。文档对exact committed range执行Harness并验证fresh receipt；该receipt覆盖文档checks，不认证real media质量。receipt为 `.agent/harness/runs/fanxiang-h3-record-20261002-01/receipt.json`，最终状态以该文件与integrity验证为准。

按 `record-ai-video-session`在真实测试稳定后记录；`distill-ai-video-learning`再次评估 **no_candidate**：只有一次attempt，无controlled multi-arm。既有H3 learning scope为local ComfyUI first-frame/open-state或shot-local prompt案例，与此METASO多图形变不是相同provider/input边界；没有足够依据修改这些claim或归纳新的模型能力规则。source V36不是本实验同输入/同请求的受控对照，不能充作第二个独立support arm。

本实验唯一新增durable项目记录为本文件；作品拆解只添加后续结果链接与V36播放补证。保留unrelated staged `.codex/config.toml`，不改共享Provider/paid/credential/QA契约；没有push、release、画布编辑、分享或发布。所有测试与失败素材保留，本次授权的一次生成已用完。
