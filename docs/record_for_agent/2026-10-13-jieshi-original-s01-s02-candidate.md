---
record_kind: media_experiment
topic_id: jieshi-original-s01-s02-fidelity
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi Original S01–S02 Candidate Record

Date: 2026-10-13

## Supersession Notice — 2026-10-14

当前最新checkpoint为下文 **Bounded Image Repair And Stop**：共享修复已发布 `0234fc55e3be9bb188db1ab8ca7a5ec12acd0066`，旧本地unknown在保留全部paid/原图后封存FAILED，随后修正图真实POST一次。累计图片2、原单元视频0，Manifest19，修正图canonical技术准入成功但实际QA仍FAIL；无edit、原S01 MP4、handoff或成片。此前“Manifest12/图片1/共享code未改”为保留的历史checkpoint，不是当前状态。

用户已明确授权最多2 Seedream PNG+2原S01/S02 Fast4s、480p/native audio、零重抽的200 CNY内部上限单元。下文此前“新单元未授权/新增POST=0/Manifest revision3”为历史checkpoint，已被文末真实执行取代：新增1图片POST、0视频POST，exact底图视觉QA FAIL，未进入第二张或视频。paid receipt ACCEPTED与本地materialize `outcome_unknown`分开保留；不是Provider结果未知，也不是原S01成功。

## Current Goal And Boundary

用户明确纠正：旧抬手机/起身两镜为 Agent 简化测试，不是原开场。本次从已发布 shared inspect/author/preflight 继续，准备原 S01→S02 候选及逐项忠实度矩阵，不重建执行链。原开场两镜采用0–3/3–7秒；S03/S04才补足7–15秒，当前只保留映射、不扩4次生成。

当前真实停止点为已授权底图的 `QUALITY_FAILURE`，并有本地candidate materialization阻断；声音语义仍缺合格听音/登记路线的 `EVIDENCE_REPAIR_FIRST`。对原文“clean plate必须最终视频overlay”的过早解读已撤回：原文只要求几何一致且只删除林砚映像，可以先准备首帧。已补同一Seedream adapter的单PNG参考；本轮底图失败不能签实际plate或raw video成功。没有激活QA或qualified视频runtime。未生成新的原剧本MP4、没有前镜accepted source、没有state handoff/后镜submit、没有HyperFrames成片；human1.0x及故事AC-7 `NOT_EVALUATED`。

## Owned Work

- [原候选与忠实度矩阵](../canvas-projects/jieshi-original-s01-s02/README.md)：原文出处→project/参考职责→exact source-native文本或canonical composition职责→required实际QA；显式列出原S01 Next/Risk clean plate、字幕与声音缺口，没有删剧情要求过检查。
- 原 `project.json/source.json/source-mapping.json` 沿共享数据入口；所有原Shot动作、对白、窗口、摄影与当前人物外观/道具/空间进入source；原字幕分配canonical caption职责。历史PNG同bytes仅用于审阅绑定，S02引用为future state placeholder，不是实际状态。
- 复现source compiler的typed对白6paths未表达。新增小型通用 `seedance_source_dialogue.py`，只有same-line exact语音约束才能声明时间/画内外/口型控制；既有逐字中文只表达mode/language。拒绝silent output、超request窗口和未表达fields；不改source text、schema、permit、QA或renderer。
- Self-reviewed spec/plan：`docs/superpowers/specs/2026-10-13-preserved-source-dialogue.md`、对应plans同名。默认Native Codex串行，当前main，无development worktree。
- 续执行共享修复：`seedream_reference.py` 负责单scene PNG测量/版本/preview accounting，`seedream.py` 显式 opt-in profile + injected byte resolver + 原字节 inline image/egress；`image.py` 区分新reference request `/5`与原T2I `/4`。旧profile序列化/hash及original PNG result版本不变。复用现有paid image committer、Registry、P5 activation，不新增Provider/model/timeline/renderer。
- 单参考的self-reviewed spec/plan：`docs/superpowers/specs/2026-10-13-seedream-single-reference.md`、对应plans同名。README与project adaptation_reason同步首帧准备职责；source/native输入和原剧本bytes未改，不编造bbox或实际plate。现有video+PNG generic overlay仍不宣称支持。

## Previous Published Candidate Evidence

证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/`：

| Evidence | What it proves / limit |
| --- | --- |
| `inspection.json`、`author.json`、`preflight.json` | 已实际调用三个共享入口，generation/composition_order均S01→S02，production_acceptance NOT_EVALUATED；Production目录没有文件 |
| `native-dialogue-gap.json` | 修复前两镜各6typed dialogue paths未表达；是纯native-expression诊断，不冒充Planner/Router prepare |
| `native-expression-preview.json` | 当前author后的source-native文本与hash；两个原镜无未表达authored paths；完整qualifiedruntime prepare仍NOT_EVALUATED。S02仍是placeholder，不是final video-reference payload |
| `audio-capability-probe.json` | 本窗口实际音频输入被平台拒绝，Whisper只有转写证据；声音语义、时序和声线没有听音验收 |
| `kimi-receipt.json`、`kimi-report.json` | 受管read-only capability mapping，exact旧snapshot；不是implementation review或mediaQA |
| `.agent/harness/runs/jieshi-original-source-20261013-r1/receipt.json` | 第一轮真实FAIL：新helper/test未注册policy route，policy_audit_check阻断；其他suite未执行，保留失败历史 |
| `.agent/harness/runs/jieshi-original-source-20261013-r2/receipt.json` | 新helper/test接入已有preserved-source suite与routing后的非空exact staged验证；发布前必须fresh verify，不签模型/连续性成功 |

有效red evidence：`/tmp/jieshi-source-dialogue-red.txt` 的4 failed /7 passed（正确完整typed数据下重现，不把更早测试构造错误算产品回归）。随后13项新测试通过，含T2V与Fast I2V public common compiler；首轮61项source/native/compiler相关tests通过，扩大focused suite91项通过。最终Harness以实际receipt为准，不能从计划宣称PASS。policy修订只增加注册新测试/helper，保留全部旧检查，直接保护原对白、窗口和嘴部表演的输入表达，没有降低观看验收。

## Single Reference Engineering Evidence

| Evidence | What it proves / limit |
| --- | --- |
| `single-reference-current/{inspection,author,preflight}.json` | 当前project改动后重新调用共享三个入口；纯候选，不是qualified paid preview或Production acceptance |
| `clean-plate-capability/{task,run,receipt,report,parent-adjudication}.json` | 新一轮read-only Kimi mechanism mapping与Parent逐条裁决；冻结source hash在编辑前核验，修改后不把旧snapshot冒充final implementation review |
| `clean-plate-capability/audio-capability-current.json` | 当前再次实际audio input unsupported；medium/zh转写及当前verifier能力检查，见下文 |
| `/tmp/jieshi-reference-red.txt` | 原adapter/reference request拒绝的红测：6 failed、12 passed；没有Provider POST |
| `/tmp/jieshi-reference-final.txt` | 最终22项Seedream测试通过：public committer exact egress/native image、activation/reopen/replay、旧profile、错误role/count/bytes/PNG/geometry、credential lookup期间reference drift拒绝及known_no_effect |
| `/tmp/jieshi-reference-related-final.txt` | 此前19项版本加image/Grok remote lifecycle/state commit/Canvas project相关suite，280 passed；随后仅补3项reference geometry测试及清理新测试unused locals，不把旧测试数写为最新全套 |
| `.agent/harness/runs/jieshi-single-reference-20261013-r1/receipt.json` | 非空exact owned staged snapshot的当前工程验证；状态/selected tree和freshness以实际receipt为准，不预签PASS |

通过标准 `load_production_project` 重开旧asset-first Production：Manifest revision72，旧图片 `image-3bb276475a7f90384e8ca653d0bfa8a51f022c882746c0ccfa9ead26621fff64`，SHA `24c6636f075d9428b51216e2e34dfb70995a7da87acc81e753274e7d5383f602`，tool仍为 `seedream-original-png/1`。这是实际旧Registry兼容性证据，不把旧抬手机片提升为原accepted S01。

policy仅把新leaf helper加入existing seedream_image suite路由，没有删除checks、刷新Architecture baseline或降低验收。最终publication必须exact receipt fresh verify后owned commit/push，并核对远端main；foreign dirty不属于本轮证据scope。

## Sound Capability Probe

使用历史原S01 Vidu attempt09 exact MP4，SHA `7b249ddc7c535b36447b0804909059f2e54a74d0a73328dafe409db16a759302`，project-local video-analysis probe报告1080×1920、24fps、97帧、4.042秒、AAC48kHz2ch。局部诊断WAV派生至新run目录，未覆盖历史视频或receipt。

实际audio input返回 `audio content omitted because you do not support audio input`。MCP Whisper base返回0–2.0秒 `零燕請在終點站下車`，不能当原姓名发音正确、0.1–2.7窗口正确或实际听音证据。本窗口没有说听过原片；不是为补证重新生成视频。历史媒体质量没有重分类，本证据只说明当前分析能力缺口。

续执行再次读同源WAV仍返回unsupported；实际project-local MCP medium、zh、word_timestamps=true得到0–2.24秒 `林燕請在終點站下車`，但没有返回逐字timestamps。相近音转写既不能证明原姓名念对，也不能据此断言念错；没证明原窗口/停顿/女声/广播空间。`ControlledPresentationVerifier` 明确只支持technical/analyzer，并以 `EVIDENCE_GAP: no human presentation host integration` 拒绝human；现有Console continuity七项不含audio。网页正常播放、文本答复和ASR/AAC/decode均不能代签可信human或听音语义。此真实缺口需要合格可听音分析环境/selected authority，或接通真实exact-bound human presentation host后再实际听判；不新增虚假verifier绕Gate。

## Managed Mapping And Parent Adjudication

Kimi invocation `ea1727fb-280f-4baa-8eaf-4843245a5881`，sealed deep profile、qualified Docker containment，actual k3/max共3次authenticated requests、PARSED、exit0、未截断；report SHA `69c7fcd94a7b420be4a44a4cfc7af773a38cf02f9b1e29f9948b8dd906c14ba1`。Parent完成7个冻结read文件hash核对后才修改source。Standing Kimi授权不代表image/video授权。

| Finding | Parent disposition |
| --- | --- |
| source prose机械保留 | CONFIRMED，当前shared author+native-expression实测；不是完整qualified请求或模型理解证明 |
| clean plate / mask runtime gap | CONFIRMED限原S01路径；canonical已有多层结构不等于mixed video+局部plate已接通。不能只靠新增enum或模型随机缺人代替真实几何修复 |
| same physical Scene阻断handoff | FALSE_POSITIVE for this candidate；两个明确reference owner IDs共享原SC01地点，既有guard可满足，无需削弱guard或新story bypass |
| 建议新增reflection CausalDimension | 不采纳：当前boundary是声明的partial character carry；实际左手/倒影/空间由source与selected Gate/handoff七维观察核验。新增枚举不能证明缺席；若后续确需typed动态事实再按owner适配 |
| caption/audio existing seam及窗口不保证执行 | CONFIRMED；hook是非口述subtitle，需要authored provenance和actual native clock。拒绝mute/replace fallback，不能把source mapping代为听音验收 |

续执行mapping invocation `c9a84203-5470-4726-864b-8ae69ce8dc75`，sealed deep、qualified Docker、actual k3/max共4次authenticated requests，PARSED/exit0/未截断；report SHA `dbc92968dfb2f1dbac5bd5c00c6e53ec1253508a2946a0f137c4c93bc2760dce`。冻结9个文件；实际7个read hashes在编辑前全部核对。它是旧snapshot调查，不是新implementation review。

| New mapping finding | Parent disposition |
| --- | --- |
| 原clean plate没有强制最终overlay | CONFIRMED；选同源首帧准备，保留raw video全部要求 |
| 原Seedream adapter拒绝reference | CONFIRMED于修复前；本轮已补显式opt-in单PNG，不代表编辑质量 |
| static PNG可以generic叠video | FALSE_POSITIVE；现有classifier/graphic契约需要graphic_layer_id和AdCreativePlan；不能把原剧情plate标成广告graphic绕契约 |
| raw Gate不能由composition签 | CONFIRMED，不改Gate、验收顺序或历史media verdict |

## Historical Authorization And Finite Proposal

新增image/video POST=0。旧asset-first单元仍为图片1/1、视频1/2；历史10视频+旧A1=11，旧cap12保留，未挪用B。前次1原图+2原S01/S02 Fast4s/150 CNY为未批准的历史提案，不提供同源base与plate两阶段证据。本轮可审阅新提案为最多2 Seedream PNG（1152×2048），先准备正常八人/八倒影的技术base，再单参考只编辑林砚反射区域；技术base不能冒充原S01首帧。actual base后才可测/审bbox，不能先伪造exact edit payload。最多2原S01/S02 Fast4s、480p、native audio、零重抽；若以后批准，累计视频最多13而非重置历史。每素材50、总200 CNY只为operator upper bound，不是价或账单。本次没有发出新paid permit或付费批准请求；可听音且可登记的Gate路线与qualified exact previews补齐后集中提出唯一新单元决定。

## Previous Source Mapping Risk Decision

最终stable snapshot以exact staged Harness和`runs/.../review-risk.json`为准。当前diff是纯prose mapping+tests+原候选/证明文档，不涉及凭据、跨项目authority、mutable state、预算/permit或recovery。新映射要求精确声明，未表达值仍拒绝，raw/后镜/最终Gate均保留；已有failure-path及common-compiler测试覆盖确定性变更。真实音义/clean plate缺口显式阻断媒体推进，adversarial读代码不能补听音/几何实测。按SUBAGENTS Risk Gate未触发required final Kimi reviewer；mapping调用不冒充review，parent最终裁决。

## Single Reference Review Risk Boundary

本轮涉及remote image adapter，必须在新exact staged Harness后重新判断；上段不能沿用为新snapshot的final risk decision。新的decision写入 `runs/canvas-jieshi-original-s01-s02-20261013-001/single-reference-review-risk.json`，绑定selected tree、owned paths/hashes、spec/plan和receipt，并逐项记录explicit review mandate、critical consequence及重大后果/实质native gap/reviewer增益条件。当前实际plate/听音缺证仍是media推进blocker，不能靠代码review解除。

## Record And Learning

使用 `record-ai-video-session` 达成substantial候选/工程及真实声音blocker checkpoint。自动按 `distill-ai-video-learning` 评估为 `no_candidate`：没有新的原剧本媒体attempt或controlled comparison；历史同bytes的能力复查是同证据新proof layer，不能算独立实验或更新Vidu质量claim。memory查询已因incompatible library exit3停止，没有重建或刷新RAG。

保持用户列明foreign dirty五个tracked文件和untracked retarget plan；只stage/commit owned paths。Publication由完成后的main commit/push及remote SHA核验报告，技术receipt不构成publisher/human/media acceptance。

## Original First Request Checkpoint — 2026-10-14

用户继续要求原剧情真实视频。沿已发布asset-first准备路线，S01仅添加单个已bound `first_frame` image role，使用同字节historical PNG作准备槽；其usage仍review-only。没有新增制作镜头、第二timeline/state owner、故事执行脚本或Provider。技术base不算原S01首帧，不能发送到视频生成；必须另做clean plate并独立验收。原S01/S02 source-native原句、动作、摄影、声音和subtitle职责未删改。

初次新增pending image roles被strict bootstrap拒绝：generated_video只允许一个pending video role。这是known-no-effect，Production目录当时无文件；撤回该candidate，未改validator。随后复用现有bound first_frame角色，`CanvasAuthoringBundle.bootstrap`→唯一committer→`initialize_canvas_graph`→标准`load_production_project`真实重开成功，Manifest revision3。只是项目数据/graph；没有QA policy或媒体acceptance，不再沿用此前“Production为空”的current描述。

证据在 `runs/canvas-jieshi-original-s01-s02-20261013-001/original-input-preview-20261014/`：

| Evidence | Actual conclusion / boundary |
| --- | --- |
| `rejected-pending-image-roles.json` | 拒绝原因、候选撤回、known-no-effect；没有POST或Production write |
| `inspect.json`、`author.json`、`preflight.json` | 当前数据重新运行共享三个入口；不签真实图片/video Gate |
| `request.json`、`preview.json`、`native-body.json` | `SeedreamImageProvider.preview`实际生成首张exact candidate；1152×2048 PNG、固定model、无reference，禁止transport/credential回调未调用 |
| `operator-bound-proposal.json`、`receipt.json` | 实际决定时间起一小时的拟议内部上限；不是qualified profile、调用授权、reservation、intent或permit；过期必须重新prepare |

当前project data SHA `cbc4682c543529d07297205f01e6af4df19016d80677599d1d48a88fa0b8b74f`；base prompt SHA `ce6fcc5ee93f034dcf2385bffb936d2e088fbf0663f0659b1860bf0bc1a264d7`；native body SHA `d48502a7bd27fd80786e7f54cf8e56a06b26e08dbddd54a10cf24695f5812e1d`，2819 bytes。Parent实际校验三项current snapshot pointer、native body/settings/完整prompt、无reference egress、未active QA，均PASS。后续edit的actual base identity/bbox以及视频first-frame/source_video依赖仍未产生；不把source-native诊断写成完整qualified视频request。

本次只有ordinary data/prose修改，无共享code或Gate变更。适用Harness receipt为 `.agent/harness/runs/jieshi-original-first-preview-20261014-r1/receipt.json`，以实际receipt及fresh verify为准。Risk Gate在最终exact snapshot验证后判断；mapping不冒充implementation review。原新图片/视频POST继续为0；旧B额度、历史11视频计数及全部receipt未改。

## Raw Listening Route Checkpoint — 2026-10-14

受管只读Kimi invocation `c2d12ad7-8593-420d-bfac-e0fd970b0f1d`，sealed deep、qualified Docker containment，actual k3/max三次authenticated requests，PARSED/exit0/未截断；worker report SHA `80ed564df93412ea19b1c998d39ed6327498b23dbd60f4c0468562d9b72e5bb9`。九个冻结source当前hash全部一致，六个source实际Read完整；原canonical报告按hash复制。证据 `audio-review-route-20261014/{receipt,report,parent-adjudication}.json`。Standing Kimi授权不授予图片/视频POST。

Parent确认raw `CanvasProductionService.evaluate`→`review_generation_attempt`的controlled verifier与marked source validator均拒绝human；缺可信真人host/实际听音环境。最终 `review_canvas_delivery` 已有独立human whole-playback、full_playback/1000要求及exact render/one-use permit验证，不能补签raw Gate。最小共享接点已存在于presentation_verifier/VerifiedEvaluationBinding/one-use recording proof；缺实际presentation→answer和selected actor的可信采集，而不是缺一个允许任意JSON填写PASS的enum。本候选尚未active QA，不能声称真实音义profile/measurement方法已sealed。

未新增假human verifier、未声称听过、未把ASR或网页播放当semantic PASS，未重分类历史attempt09。声音恢复条件为qualified可听音analyzer/selected authority，或实际集成并验证exact-bound真人presentation host后由真实人听判。未满足前不提交视频；图片准备成功或新预算授权都不能解除这条依赖。

完整新单元仍是最多2 PNG+2 Fast4s/480p原生声音、零重抽，内部各50/合计200 CNY；非价格/账单。首张输入已可审阅，可集中请求新单元授权；之后也只在实际前序依赖及逐次fresh gates满足时执行，不消费旧B、不提交声音证据仍不可验的镜头。这是授权缺失与能力Gate分离的真实阻断，不宣称只要授权就一定有合格视频。自动learning再次为 `no_candidate`：新增只读mapping与candidate request，零新媒体，不构成独立质量实验。

## Authorized Base Execution And Stop — 2026-10-14

用户随后明确回复“授权”，沿已发布共享image owner实际执行上述有限单元。证据根为 `runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/`，`unit-authorization.json` 的 scope SHA `14458924df070bd0c71fcfee9c4f6959d3aff73121eb46cf587909c7e8597e5c`。边界保持2图片、2视频、各50/总200 CNY内部 upper bound、零重抽；旧图片/视频单元和历史11视频不重分类、不重置、不挪旧B。

初次 exact supplier lookup 因进程未接同用户D-Bus session而失败，transport调用0，canonical receipt `6935f89d86475dce2075f8d1d96e03f8b448ac2b4a90c660f5dab6d1c1c4eca9` 为 `KNOWN_NO_EFFECT`，原reservation已释放为actual cost0。只修复已核实的session注入，仍用原exact injected supplier；readiness实际通过，没有查替代secret source。封存一次 task-necessary known-no-effect runtime恢复，保留旧attempt/receipt，gen_revision1→2仅区分新request identity，native模型输入2819 bytes及SHA `d48502a7bd27fd80786e7f54cf8e56a06b26e08dbddd54a10cf24695f5812e1d`不变，未扩额度或复用permit。这不是重抽已生成素材。

恢复attempt `original-preparation-base-20261014-qualified-001`、request fingerprint `4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801` 经 `generate_remote_image_asset` 真实POST一次。fresh exact profile/window、preview、budget reservation、egress、durable submit intent和one-use permit均沿现有owner核验。Provider receipt `aa2c38927dace8d98eddd50dc005e9748a56b70764b9ca755827caf369ff1469` 是 **ACCEPTED**；原PNG与wire PNG均已落盘：`production/assets/files/14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73.png`，SHA同文件名，1152×2048，4,265,121 bytes。标准result/provenance validation及wire/local同bytes实际PASS。

本地activation随后失败：Manifest revision12，image attempt `outcome_unknown`、phase `materialize`；paid phase仍 `accepted`。Registry没有准入新图，candidate pointers为空。write-free重建同一持久result并调用shared preparer/validator，实际重现 `IMAGE_REQUEST_INVALID: Image candidate resolution contains an unrelated dependency node.`，位置 `production/image.py:1212`；Manifest bytes前后不变。没有放宽guard、手写candidate pointers、猜mixed state或再POST。已保存的PNG必须保留，不能把本地unknown误报为Provider未知、未返回图片或预算被冻结：budget revision5、blocked=false，50 CNY upper-bound reservation为reserved，actual cost尚null；不是实际账单。

`runtime-repair-001/execution-receipt.json` 保留原错误码；首次 `current-unknown-boundary.json` 的外部结果恢复建议被 `current-state-reconciled.json` 明确纠正为paid ACCEPTED/本地materialize失败，不覆盖历史。`materialization-diagnosis.json` 绑定exact PNG/result/provenance和无mutation复现。现有 `paid_provider_no_effect_reconciliation` 仅支持video的verified pre-transport failure，不能用于此已POST且ACCEPTED的image释放预算；本轮没有执行该reconciliation。

## Exact Base Visual Review

在同一已封存 `base-review-contract.json` 下，Parent经 `view_image(detail=original)` 实际查看exact PNG，并独立测PNG bytes/尺寸。`base-image-review.json`保存每个required ID和观察；这属于技术准备图的实际审查，不是canonical raw-shot QA、human正常速度视频验收或后镜准入。

| Required finding | Verdict | Actual observation |
| --- | --- | --- |
| base-eight-entities | PASS | 七名坐姿人物加门边苏遥，共八名实体，角色服装可辨 |
| base-eight-matched-reflections | FAIL | 上方八人反射倒置在车顶平面，不是原要求的对应侧窗几何，不能认定完整正确窗内倒影 |
| base-linyan-identity-props-hands | FAIL | 林砚坐姿/工牌/黑手机可见，但双手接触手机，左手未为空 |
| base-other-identities-props | FAIL | 正面苏遥用解剖右手持乳白手机，左手垂下，违反左手职责 |
| base-camera-space | FAIL | 倒置车顶映像替代本人/侧窗对应关系，林砚后方实际侧窗没有所需映像 |
| base-isolated-editable-reflection | NOT_EVALUATED | 几何未通过，不制作猜测bbox或宣称可保护七倒影 |
| base-png-and-unburned-caption | PASS | exact 1152×2048 PNG，无故事字幕/说明或拼图，保留预先声明的厂商watermark |

全项不PASS，结论 **QUALITY_FAILURE / STOP**。没有第二张edit、重抽、video submit或自动fallback；剩余图片为后续同源编辑，不能挪为换底图。新增实际图片POST1/2、视频0/2，历史视频仍11；S01/S02 raw QA、实际状态交接、原生音轨/字幕、canonical trim、HyperFrames及human1.0x均NOT_EVALUATED，完整前15秒和故事AC-7仍未交付。原source/native输入未删改；没有继续生成旧抬手机B。

恢复需要可忠实准入的准备素材与可审阅新输入；本单元零重抽不能自动扩大。shared candidate需按P5精确比较查明无关dependency frontier，并通过唯一owner显式处理本地materialization；不能白名单无关节点或为了准入删S02。视频之前仍需qualified可听音且可登记的真实证据路线。修正输入/有限新调用必须有适用明确授权；已有授权不再次请求，当前失败不以“继续”或授权文本代签PASS。

## Bounded Image Repair And Stop — 2026-10-14

用户最新“继续做图啊”对应明确有界修复，未自动转用旧edit/B额度：保留已POST1图片，最多再一次修正base和一次只有全项PASS后同源edit，累计图片上限3；单调用50、总200 CNY内部operator上限保持，非价格/账单。scope SHA `341f81647cfb85e8eb09c32d0110389d87bf3afcf7d3cebdc05371f626cd9a5a`，证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/`。实际只新增1 POST，没有自动重抽/fallback、没有edit或视频。

### Shared Engineering And Actual Old-State Closure

真实frontier diagnosis发现bootstrap未投影的两个既有asset节点，不是本次新增素材变更。新 `image_candidate_frontier.py` 通过同一P5的write-free baseline projection，仅排除desired未变的既有nonfresh/registered asset节点；已变无关节点仍拒绝，不删除S02、不造第二timeline。canonical `close_remote_image_materialization_failure` 只处理完整retained result且paid ACCEPTED/SETTLED的本地失败；typed receipt/reader/recovery均绑定原request/result/provenance/PNG/wire/paid/base。真正paid unknown、mixed、stale、缺证/tamper拒绝；不POST、不激活、不释放原reservation。

`state_commit_attempt_contracts.py` 承接新增optional pointer/validator和既有serializer，避免继续扩张大型models。旧None字段完全省略，旧hash/serialization兼容。共享工程提交 `0234fc55e3be9bb188db1ab8ca7a5ec12acd0066` 已push，`git ls-remote origin refs/heads/main` 实际核验相同SHA。

受管read-only Kimi mapping invocation `9b900f46-66fc-458b-b08b-1f21b3fe79f9`，sealed deep/qualified Docker、actual k3/max、3 authenticated requests、PARSED/exit0/未截断。canonical redacted report SHA `550c9cc41018ab37ff1548fafe08239048f4408dc49614ee7e0635af91fc0453` 保留，冻结read hashes在编辑前核验；不还原redacted内容。Parent确认frontier问题，驳回“现有recover能关闭unknown”和“Registry activation即accepted S01”；mapping不冒充implementation review。native bounded worker只负责failure leaf/test，Parent接回ownership并完成集成与最终diff裁决。

valid red包含public Canvas bootstrap frontier失败和closure API尚未实现时6 failed/1 passed；更早fixture/import错误不当产品回归。相关旧candidate回归341 PASS；serializer迁移后的模型/新boundary suite309 PASS。最终 `.agent/harness/runs/jieshi-image-materialization-20261014-r2/receipt.json` 对非空15 owned paths、tree `90419835fe0b4846e2af2aea71e711e05a4c0eda` 实际通过：20 selected checks，15 executed PASS、5按同轮full Production覆盖跳过；full Production **4007 passed/3 skipped/2608 deselected**，final image136 PASS、Seedream/shared remote-image38 PASS。首次r1因models增长触发Architecture FAIL，保留未覆盖的后续checks，不伪称r1完整通过；移出serializer后r2 Architecture PASS，reader仅7行delegated integration的WARN保留，未改baseline。

fresh receipt命令首次误传RUN_ID，提交后原staged receipt在当前main自然stale。未覆盖receipt或伪造fresh stamp；通过一次仅验证用disposable checkout重建原HEAD+exact staged tree，canonical `receipt_freshness` 全项fresh=true，且已提交tree等于已测试index tree。`snapshot-revalidation.json` 保存对应关系、原receipt hash与真实diagnostic；验证checkout不用于开发，没有重复长回归或Provider调用。Risk Gate在final native verification后为 `KIMI_REVIEW_NOT_REQUIRED`，理由和精确snapshot/hashes见 `implementation-review-risk.json`：变更不能改active tuple、退款、重放paid POST或关闭真正paid unknown；无remaining重大implementation gap。素材质量仍由实际QA，不能以mapping/reviewer代签。

严格实际重开旧PNG/result/provenance/paid joins后，唯一owner显式封存旧attempt：Manifest12→13，local FAILED、paid仍ACCEPTED，closure hash `5e0e40ffa5ea45400898164f6745711c2b39a0ecb5930a52838f0584f14cfd57`。原PNG、active project/Registry/graph、dependency states、budget pointer/bytes全部前后相同，POST=0；证据 `preclose-evidence.json`、`closure-execution.json`。旧QA FAIL没有改为PASS，旧完整媒体和全部副作用历史保留。

### Exact New Input And Paid Execution

[修正文字](../canvas-projects/jieshi-original-s01-s02/S01-preparation-base-repair-input.txt)3015 bytes，只具体化竖直侧窗/正立反射/不反光车顶和左右手；人物服装与固定空间段同旧prompt逐字相同。原S01/S02 source/native输入未改，点名广播、对白、动作、摄影和字幕职责没有删减。技术base仍要求正常八倒影供后续定位，不是原S01首帧，也不送video。

`base-001/native-body.exact.json` 使用actual adapter settings/JSON顺序，3171 bytes、SHA `d35b1ba65447f436021f6b157a2c02ed6c0aeb5486d9535b383fac7f970c3c7f`；早先sorted-key body只为语义等价预览，`native-body-exactness.json` 明确纠正，未用该旧SHA声称真实wire。实际transport observation与exact body全bytes一致，headers/credential值未记录。

attempt `original-preparation-base-repair-20261014-001`，request FP `c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011`。submit前实际核验当前profile/window、current canonical count/state、exact injected supplier readiness、preview/opt-in/egress；shared committer逐次执行budget reservation、durable intent及one-use permit。实际transport调用1、HTTP200、零retry；09:37:31 UTC返回时Manifest19，local SUCCEEDED/activate、paid ACCEPTED，canonical技术素材已准入，不是QA acceptance。

原PNG SHA `ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f`，1152×2048、4,671,205 bytes，`production/assets/files/<SHA>.png`；result FP `b2fef9aac736035c4641f5c1fb946936223200bedbf306165424bae121111c78`，provenance receipt `9f098252dc0ec8c833690d2b4fce6f7a4615c6b08739dbf1ac72fb7ea3581462`。标准loader实际重开joins成功，wire/local原字节保留。

### Actual Image QA And Stopping Boundary

Parent通过 `view_image(detail=original)` 实际看图，沿submit前sealed七项review contract，不用Provider成功或coverage代签。`base-001/image-review.json`：**1 PASS/5 FAIL/1 NOT_EVALUATED**。

| Required finding | Verdict | Actual observation |
| --- | --- | --- |
| base-eight-entities | FAIL | 只见林砚、陈立、周伯祥、郭向东、沈嘉程、何静、苏遥七名实体；海军蓝风衣许雯缺失 |
| base-eight-matched-reflections | FAIL | 改为正立侧窗，但苏遥样貌的立姿映像在不同窗重复，不能逐人认定八个完整对应映像；若干坐姿反射暗/遮挡 |
| base-linyan-identity-props-hands | PASS | 静态林砚左手空、右手唯一黑手机分离，工牌/蓝挂绳及坐姿可见；不证明原S01动作 |
| base-other-identities-props | FAIL | 苏遥左手乳白手机与何静膝上袋改善，但许雯缺失、郭向东多出黑手机，完整inventory不通过 |
| base-camera-space | FAIL | 蓝椅/银杆/侧窗改善，但沿身体、膝腿及地面明显俯看；原坐姿眼高斜侧中广景及本人下方/窗上方构图未建立 |
| base-isolated-editable-reflection | NOT_EVALUATED | 不能可靠定位唯一完整林砚映像并保护另外七个；未编造bbox |
| base-png-and-unburned-caption | FAIL | PNG尺寸通过，但左上额外生成“界蚀”故事标题，超出预选原生watermark；canonical hook字幕仍未制作 |

本轮 **QUALITY_FAILURE / STOP**，不edit、不生成video，不把剩余edit次数挪作重抽。累计原准备图片POST2，当前修复用1/2，余1只能全PASS后的edit；原单元video0、历史video11全部保留。没有原S01/S02 exact MP4、accepted前镜、actual state、后镜QA、原生音轨/caption/trim/HyperFrames成片；human1.0x和完整故事AC-7 NOT_EVALUATED。两镜7秒与原前15秒S01–S04映射始终分开，声音路线仍有独立EVIDENCE_REPAIR_FIRST，未伪称听过。

最小恢复条件是能保全完整cast/映像/摄影、无标题污染的可审阅新输入与有界attempt决定，然后实际base全部required PASS；本次失败不能直接晋级edit或video，不能删人物/倒影/原对白来通过。共享materialization确定性阻断已解除，当前剩余是实际素材质量，不再以缺Skill或engineer PASS解释为媒体成功。

## Evidence Index

此表只为本次原开场准备单元建立identity；历史其他实验不并入。本次remote boundary为Seedream/`doubao-seedream-5-0-pro-260628`、Ark shared image owner、1152×2048 PNG。同一图片的receipt、bytes、materialization和visual proof使用同一request fingerprint independence_key，只贡献一个图片样本；预transport失败不是第二个视觉样本。

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| credential-before-post | native-image:463e47e5d7b07c89d5db8f82db5d06f06867b08d7eac9d2066acb860adf74ac3 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-candidate | N/A | NO_ARTIFACT:PRE_TRANSPORT_CREDENTIAL_FAILURE | PROVIDER_RECEIPT | KNOWN_NO_EFFECT | CREDENTIAL_READINESS | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/base-known-no-effect-current.json |
| base-submit | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | PROVIDER_RECEIPT | ACCEPTED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/production/state/paid-provider/submits/aa2c38927dace8d98eddd50dc005e9748a56b70764b9ca755827caf369ff1469.json |
| base-bytes | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | TECHNICAL_BYTES | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/runtime-repair-001/materialization-diagnosis.json |
| base-materialization | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | LOCAL_MATERIALIZATION | OUTCOME_UNKNOWN | CANDIDATE_VALIDATION | SAME_EVIDENCE_NEW_PROOF_LAYER | base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/runtime-repair-001/current-state-reconciled.json |
| base-visual | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/authorized-unit-20261014-001/base-image-review.json |
| base-closure | native-image:4225a10af7b88649f33bbfa08f8df705363780f78b07abae1847dcd230845801 | jieshi-original-preparation-20261014 | original-preparation-base-20261014-qualified-001 | N/A | 14ce8688fd567c1d2ff7518a1de112cd505e5dec395bf22299219a00fed3ec73 | LOCAL_MATERIALIZATION | FAILED | CANDIDATE_VALIDATION | CONCLUSION_SUPERSEDED | base-materialization | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/closure-execution.json |
| repair-base-submit | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | PROVIDER_RECEIPT | ACCEPTED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/execution-receipt.json |
| repair-base-bytes | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | TECHNICAL_BYTES | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | repair-base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/image-review.json |
| repair-base-materialization | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | LOCAL_MATERIALIZATION | SUCCEEDED | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | repair-base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/stop-state.json |
| repair-base-visual | native-image:c5e32912fd1bd00b8bf0afc26d40133305cc95a5bfea9d1c3a0523d633c03011 | jieshi-original-preparation-20261014 | original-preparation-base-repair-20261014-001 | N/A | ba9eb952c5606333727198800fa593abce806b3c239188425ebb7b27087cab4f | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | repair-base-submit | runs/canvas-jieshi-original-s01-s02-20261013-001/image-repair-20261014/base-001/image-review.json |

## Record And Learning Update

前一次checkpoint的no_candidate基于一个视觉样本，为历史结论。本次按 `record-ai-video-session` 更新同一主记录和README，原文/媒体/receipt及foreign dirty保留。按 `distill-ai-video-learning` 自动重新评估仍为 **no_candidate**，但不再声称只有一个视觉样本：已有两个独立实际图片attempt，proof层和旧closure不另计样本。旧图错误为倒置车顶映像/双手持机，新图侧窗/手改善却少人物/重复反射/新增标题；多项输入同时变化，不是isolated-variable comparison。不能由这些输出断言模型不具该能力、添加禁用人物/倒影规则或证明改Skill会解决。现有完整image QA/FAIL STOP已覆盖观察，未形成需要新adoption target的有界机制结论；既有Vidu对白/burned-caption claim明确排除人物/倒影与其他Provider，不构成material update。没有制造重复claim、修改Skill/Policy/Gate、刷新RAG或全局memory。

共享工程已发布0234fc5并核验remote，当前文档checkpoint的receipt/commit/push另列实际结果；工程证明不代图片QA、raw连续镜或正常速度human声画验收。原hook `ai-video-record-6104c772eca8de88` 已在前一record checkpoint以recorded/no_candidate ACKED；本更新不重复ACK旧request或猜新ID。
