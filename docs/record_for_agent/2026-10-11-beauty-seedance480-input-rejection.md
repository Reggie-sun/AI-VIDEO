---
record_kind: media_experiment
topic_id: seedance-canvas-fictional-reference-admission
learning_eligibility: eligible
evidence_index_version: "1"
---

# Beauty Canvas Seedance 480p Input Rejection

Date: 2026-10-11

## Purpose And Current Status

推进[reusable canvas spec](../superpowers/specs/2026-10-11-reusable-canvas-production-harness.md)的真实制作验证。
用户明确授权Seedance480p，声明人物为虚构生成角色且有素材使用权，并选择保留原对白/音效、无配乐/字幕。
本单元先验证平台是否接收《美丑》原timeline index1的五图参考；完整目标仍是indices1–4的60秒Pilot。

一次真实POST返回HTTP400 / `InputImageSensitiveContentDetected.PrivacyInformation`。
无task ID、无生成MP4；canonical `KNOWN_NO_EFFECT`，重开仍为`stop`。
媒体、逐镜Gate、handoff、composition、renderer、完整人类听看均NOT_EVALUATED。
不声明spec完成、质量FAIL、平台指出具体哪张图，或全部虚构写真参考必然被拒。

## Exact Inputs And Preflight

运行证据根：`runs/canvas-beauty-seedance480-20261011-001/`；历史失败不覆盖或删除。
原source node `node_y8q933qdhx`，原timeline occurrence `dd364df9-1a03-4fe3-b290-5b8dcd6c9f6c`。
显式node选择由source adapter生成occurrence `node_y8q933qdhx`；两种身份分别保留，不伪造timeline采用。

- Model：`doubao-seedance-2-0-260128`；mode `reference_to_video`；15秒、480p、native audio。
- 原画布720p只留在观察值；实际native payload为`resolution=480p`、`duration=15`、`generate_audio=true`。
- 所选profile的native raster为864×496、24fps；最终854×480需正常Composition，未渲染或交付。
- 五张实际PNG依序为卧房、赵老爷正面、赵老爷三视图、东施正面、东施三视图；每份有独立semantic job。
  原bytes、source node/resource、measured hash/size、Registry与human声明分别封存。
  `jimeng-canvas-export` provenance只证明只读导出，明确原始generator receipt不可用；没有补造生成记录。
- 原文两个摄影段落保留：固定拍摄位置的呼吸晃动/转焦/踹门晃灯，切侧前手持跟拍/喝酒滴领/摔杯。
  一次15秒生成包含两段摄影，8/7秒仅是相对节奏目标，不是两次submit或硬timestamp控制。
- 盖头全段不揭；杯从半满到喝完摔碎、最后空手；灯从剧烈晃荡到微晃。
  两句原对白、声音/乡音、门轴/碎杯/酒嗝、无BGM/字幕均保留，待exact媒体逐项验证。

`Director v4`和goal-binding实际validator通过；Parent核对raw→inventory→coverage。
受管只读Kimi concept check invocation `f756ffb3-50da-467a-969a-347c450de880`，
contract `0562a847-1cf3-4e44-85f5-80716ab8ee96`、qualified deep route
`4f2d5dc8-4234-4665-b382-e82f1ad6cc00`；receipt核验PARSED/exit0、5个实际Read。
Parent裁决其720p疑问为观察值与执行值分离，实际wire证明480p；不是修改源参数或额外授权。
此审查只核对创作，不代签API准入、完整spec或媒体质量。

完整intent补齐performance、visual treatment和camera metadata，exact Compiler2 recipe覆盖检查通过。
辅助quality最低raster字段不是所选compiler的能力，尺寸约束通过其支持的exact output字段保留；没有升档。
这些均为正常导演/配置数据，未改共享code、v2冻结或Gate。

## Authorization And Execution Boundary

用户指定本repository `.env`为本单元exact私密来源；injected supplier只读`SEEDANCE_API_KEY`，
不插值、不输出、不持久化value。原Secret Service查找无可用值、零Provider网络；当前例外不成为其他任务默认。
credential presence不是授权；本次用户明确Seedance480p指令独立封存为opt-in。

封存物理submit上限1、自动resample0。monetary guard沿预配置operator内部上限
`TASK_BOUND_MICROCNY=50_000_000`创建本任务新immutable profile与preview；不是市场价格或实际账单，
旧task/profile不授权本次调用，不重置其历史消费。实际POST前重开exact request、human attestation、
request-level egress、预算、durable intent与one-use permit；所有副作用经既有owner。

同一`CanvasProductionService`完成author/approve/revise/prepare/start/execute。
`ProductionStateCommitter`持久化请求、paid状态及failure experience，client没有另写Manifest/Registry。
下次从既有canonical request/outcome重开；没有自动换模型、UI入口、删人像或重铸permit。

## Verification And Exact Evidence

| Item | Verified identity or outcome |
| --- | --- |
| Attempt | `canvas-3647b1dc420c18befeb57c24106f46561604021b` |
| Request input hash | `bca7f1d5399145cca95eb22cc7078b07c6c2fb2653bfbf53a506b3da15cdd696` |
| Resolved request hash | `36dce716104a4d2926906d4c12dfedd6380c092ae90ce64d0529a85b73fa04ee` |
| Provider-bound hash | `6f9144358f609684411b1358686850b7590c81b58402d52fb49b43cb32f2459b` |
| Native prompt hash | `e853ac63804a22c3cb0cff6184957088cc10f4eddcccfd12bd93c50547b6066e` |
| Profile hash | `3de1cd56cd415e255dc47c34274727534477ed4d765389975b14b52fe077005b` |
| Native POST body | 9724384 bytes; SHA `9ed937b200817aa39a15f4fc9e417d0bdfc04745140d5bc4a41b3e745d6f46d0` |
| Response | HTTP400; 290 bytes; SHA `e1bdf825893b462bbcaae9898d9fb22c2bf08146c7725832d48da3c352d1b9ec` |
| Canonical paid receipt | `production/state/paid-provider/submits/12f408444bd8e30a19759194940e25a614cbbedb55975da7624f3561f30f1758.json` |
| Receipt file hash | `711d0be90bca59dbc4155888dde73e37b40cd325f747cdb05ce6bfe4fb94acf5` |
| Outcome | paid `known_no_effect`; attempt `failed`; resume `stop`; no external effect ID |
| Counts | 1 physical POST; 0 task IDs/MP4/Gates/activations/renders; 0 retries/next-Shot submits |

原始响应、HTTP headers、inline payload与credential值未进入record；wire observation仅保留safe code/hash/count。
`runtime-failure-experience.json`及Manifest中的experience pointer由正常feedback owner形成，
标记`runtime_failure`，不把未生成的视频评价为差或合格。
工程原11-check/1475-test receipt仍只证明其exact已发布snapshot，本次没有重跑全套来代替上游结果。
本次owned文档按policy验证，receipt入口为
`.agent/harness/runs/reusable-canvas-production-20261011-live-rejection/receipt.json`；publication以实际receipt/remote SHA为准。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| beauty-input-rejection | provider-request:36dce716104a4d2926906d4c12dfedd6380c092ae90ce64d0529a85b73fa04ee | canvas-beauty-first-unit-20261011 | canvas-3647b1dc420c18befeb57c24106f46561604021b | N/A | NO_ARTIFACT:VIDEO_PROVIDER_FAILED | PROVIDER_RECEIPT | FAIL | INPUT_IMAGE_PRIVACY_REJECTED | NEW_ATTEMPT | NONE | runs/canvas-beauty-seedance480-20261011-001/submit-wire-observation.json |

该非Q0身份绑定Ark Seedance2.0 R2V、exact resolved request及native POST/response hashes。
一份attempt的source、preview、wire、paid receipt和failure experience只计一个独立单元。

## Remaining Work And Learning Outcome

当前不是画布数量或凭据不足。继续《美丑》须有该入口可接收且保持原角色意图的合法素材/参考方式，
再按新有限单元重新取证；不能复用旧permit或把用户虚构声明当成Provider接收证明。
其他已保留画布可另选支持的单元验证流程：例如《机魂觉醒》蚂蚁段有完整prompt与一张参考，
但其音效/动作与完整Pilot仍须独立导演、素材和Gate验证，不因名称或本次人物拒绝自动合格。
已向用户呈现“换现有机甲样本 / 补兼容原角色素材 / 暂停新增媒体”的选择；本checkpoint不新增调用。

`record-ai-video-session`判定稳定真实blocker，更新初始implementation record的当前状态，保留其历史。
`distill-ai-video-learning`评估`no_candidate`：既有Group26拒绝提供相同error-family的历史观察，
但model/reference组合不同，未隔离具体触发素材，也不能推出全部人物或模型的准入规则。
“本地准入/声明不证明上游接收”已是现有边界；没有新的可采纳修复或Gate变更证据，
不创建placeholder、blanket禁止、Skill/Policy修改或自动fallback。
record不重建RAG，不为记录额外调用Provider、生成媒体或扩大测试。
