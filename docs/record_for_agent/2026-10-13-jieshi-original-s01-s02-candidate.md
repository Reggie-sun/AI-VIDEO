---
record_kind: media_experiment
topic_id: jieshi-original-s01-s02-fidelity
learning_eligibility: eligible
evidence_index_version: "1"
---

# Jieshi Original S01–S02 Candidate Record

Date: 2026-10-13

## Supersession Notice — 2026-10-15

最新checkpoint见 **Codex Direct Image And Authoring Workflow Rule — 2026-10-15**：用户明确改用Codex内置工具，独立1次实际生成并exact copy落盘；老人坐下/放开扶杆，target static 5 PASS/1 NOT_EVALUATED。原图944×1672、输出943×1668，精确像素保护及完整原S01仍未通过，未导入/激活、Manifest33不变。用户随后明确要求把默认生图规则写入现有工作流，并批准只改playbook生图小节、独立提交且保留原暂存修改；无新增Provider调用或产品adapter。

上一尝试见 **Pose Reference Trial And MCP Execution Stop — 2026-10-15**：先前1次 `chatgpt-web` MCP 300秒超时，页面空白/入口未就绪，未取回 exact 图片；原remote outcome UNKNOWN继续保留，没有重发、退款消费或伪称outcome已关闭。后来的内置调用来自用户新的明确路线指示，不是自动fallback。下段为仍有效的上一媒体/工程 checkpoint。

最新checkpoint见 **Registry Retention Repair And Actual Targeted Z**。共享历史链修复已发布 `a45fa113b2ffb10bbd071bfa51753849aa82c911` 并核验remote main；原生审查两条blocker均由标准loader RED复现、修复后41项focused PASS和fresh exact Harness验证，原reviewer复审finding set为空，Parent关闭两条问题。标准metadata authoring恢复Registry原P7前缀，所有旧records/媒体/history保留。随后真实新增1次本地Z局部修复，exact PNG `102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557` 技术SUCCEEDED但老人仍站立扶杆，target QA 3 PASS/1 FAIL。遮罩外1,536,514 RGB像素变化0，不能替代坐姿成功。Z单元按FAIL STOP，H未提交；当前Manifest33，累计原准备paid图片2、本地模型图片2、原视频0、历史视频11。本窗口新增paid0，无accepted S01、实际handoff或HyperFrames声画交付；声音仍EVIDENCE_REPAIR_FIRST，human1.0x/完整故事AC-7均NOT_EVALUATED。自有ComfyUI unit已停止。

## Historical Supersession Notice — 2026-10-14

当前最新checkpoint为下文 **Actual Local Masked Generation And Targeted Repair**：本地三引用蒙版作图已真实执行1次，exact PNG技术准入成功但静态QA为2 PASS/4 FAIL/1 NOT_EVALUATED。蒙版外1,096,780像素RGB完全相同，窗内人物/道具/空间没有通过。累计原准备paid图片2、本地模型图片1、原视频0，Manifest25；没有accepted S01、handoff或成片。已封存最多再2次针对具体人物的本地修复，未提交；不挪旧edit/B、不重抽旧单元。共享工程 `d37d0482e4a0d6205b2c546ba010e24433dccd8c` 及输入准备 `49485ee5bfff539e4ebb9a5902a37c0dd501e0e3` 已push/remote核验。此前“只读runtime/无模型推理/Manifest19”是保留的历史checkpoint；技术准入、工程与素材QA仍分开。

用户已明确授权最多2 Seedream PNG+2原S01/S02 Fast4s、480p/native audio、零重抽的200 CNY内部上限单元。下文此前“新单元未授权/新增POST=0/Manifest revision3”为历史checkpoint，已被文末真实执行取代：新增1图片POST、0视频POST，exact底图视觉QA FAIL，未进入第二张或视频。paid receipt ACCEPTED与本地materialize `outcome_unknown`分开保留；不是Provider结果未知，也不是原S01成功。

## Current Goal And Boundary

用户明确纠正：旧抬手机/起身两镜为 Agent 简化测试，不是原开场。本次从已发布 shared inspect/author/preflight 继续，准备原 S01→S02 候选及逐项忠实度矩阵，不重建执行链。原开场两镜采用0–3/3–7秒；S03/S04才补足7–15秒，当前只保留映射、不扩4次生成。

当前广域masked候选为素材 `QUALITY_FAILURE`，本地unit1已用1/1并停止该attempt；已诊断后封存targeted repair有限unit，不推进视频。旧本地candidate materialization阻断已解除。source/identity crop/binary mask已按当前Scene/Character职责经canonical revision准入并真实推理，缺的仍是合格剧情画面。声音语义仍缺合格听音/登记路线的 `EVIDENCE_REPAIR_FIRST`。对原文“clean plate必须最终视频overlay”的过早解读已撤回：原文只要求几何一致且只删除林砚映像，可以先准备首帧。已补同一Seedream adapter的单PNG参考，但前两次实际使用T2I；准备图失败不能签实际plate或raw video成功。没有激活QA或qualified视频runtime。未生成新的原剧本MP4、没有前镜accepted source、没有state handoff/后镜submit、没有HyperFrames成片；human1.0x及故事AC-7 `NOT_EVALUATED`。

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

## Generation Workflow Research And Input Gap — 2026-10-14

用户要求核查社区是否用类似 ComfyUI 的生成工作流，重点为即梦。新增
[研究报告](../research/2026-10-14-jimeng-community-workflows.md)，区分创作者自述、对别人作品的复盘、教程目录、官方 UI/API/工作流文档和本项目当前代码；没有因研究提交任何图片/视频或改变 Production 状态。

### Verified Findings

- 创作者案例先做角色/场景参考和构图示意，再逐镜生成、检查、局部修正；也承认多人、空间镜像和精确手部动作失败。少数案例不证明普遍做法，更不证明该地铁七倒影关系可解。
- 即梦/Dreamina UI、Ark API、ComfyUI 本地模型与 ComfyUI 云 API 节点为不同执行面。ComfyUI 官方 Seedream Pro 节点需要账号/网络，把同一远端请求搬入节点不会添加本地 ControlNet 条件。
- `seedream.py` 实际只发送 prompt 与可选一张 scene PNG；当前未暴露多角色参考、mask/区域保护或分层输出。前两次原准备生成使用纯文本，已有单参考能力未用起来，不能用 Skill 数量或工程 PASS 解释素材成功。
- `comfy_image.py` 的两条 sealed edit lane 各有两个参考槽，但拓扑没有 mask/inpaint、pose/depth ControlNet。代码存在不证明当前 host 模型/service live-ready；本次未安装或运行。
- Ark 官方文档列出多图、坐标交互与图层拆分，不能推导二值保护 mask 或 clean plate 质量。动态正文抓取受限；Chrome MCP 因已有 profile 占用未能打开，没有接管/关闭用户浏览器。实际界面及新增 API exact wire 仍未验证。

### Parent Adjudication And Recovery Direction

受管只读 Kimi invocation `fd9a2ab6-88ed-423f-9d94-f55f5c880fa8`，sealed contract
`63534dc0c3a1a3467ea6a3ff9c4defff130e4a779253731a6031d23056b5543a`；Parent 核验
route qualification、k3 model identity、containment、四个 artifacts 与全部 observed-read SHA，均匹配。
receipt/reduced adjudication 见
`runs/canvas-jieshi-original-s01-s02-20261013-001/jimeng-workflow-research-20261014/`。
它是能力映射，不是 implementation review 或 media acceptance；`PARSED` 不代签质量。

Parent 不采纳“必须再生成八个实体全部可见、八个正常倒影的底图”的推导。原镜构图含八名角色，七个倒影可承担其中角色的可见职责；原首帧始终是林砚映像缺席。两次旧技术base仍按各自sealed contract保持FAIL，不倒改历史。

本窗口实际查看历史 `historical-opening-review` PNG
`4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`，其侧窗与本人构图接近原目标；只可用于布局审阅/准备参考，尚非 accepted S01，也未在 Scene 注册为新的视觉职责或发送 Provider。

下一输入应把地铁布局、镜头构图、角色/道具、窗面与七倒影对应关系及 clean plate 准备成可审阅资产，再经现有 inspect/author/preflight。必须实际确认只处理林砚映像并保护其余七个；不能把坐标prompt当保护遮罩、把未准入旧底图当 accepted 前镜。若确需多参考、mask或分层，先做目标必要的共享 contract 适配及验证；不新增故事执行脚本/第二timeline/renderer，不直接复制社区无限重抽流程。

### Verification And Learning Boundary

本次为 research/record 文档修改，无 Provider/committer/schema/Gate 变更；Parent 风险判断为无需 implementation Kimi review，不叠加 reviewer。最初 `make harness-inspect` 使用系统Python因缺PyYAML失败；按现有 `.venv` 与 `PYTHONPATH=src:.` 重跑inspect成功，未新增依赖。文档最终exact staged验证由
`.agent/harness/runs/jieshi-jimeng-workflow-research-20261014-r1/receipt.json`
记录，不能据此宣称生成效果。

`record-ai-video-session` 在研究稳定checkpoint更新当前record；`distill-ai-video-learning`
评估为 `no_candidate`：没有新增媒体对照或候选工作流实测，外部案例与代码能力映射不构成本项目的新独立实验。没有采用/修改 Skill、Policy 或 Gate。原本声音缺口、逐镜QA、human1.0x、0–7秒与原0–15秒边界及完整故事AC-7保持。

## Native Masked Image Workflow Implementation — 2026-10-14

用户明确要求直接用原生subagent实现作图工作流。Native Codex继续拥有集成、最终裁决与publication；三个原生任务职责不重叠，`image_workflow_seam`只读核对消费者，`image_mask_contract`实现输入/输出保护校验并追加core-only supervisor切片，`comfy_masked_workflow`实现sealed Comfy图与adapter。worker均完成并归还ownership后Parent接回修改；无第二timeline/state库、故事执行脚本或新依赖。spec/plan完成Parent self-review，按 `superpowers:writing-plans` 持久化既有授权范围。

### Shared Contract And Workflow

- 新 `edit_mask` reference仍归当前Scene/Registry，只有local mask请求采用 `ai-video-image-request/6`；旧request/profile/workflow字节及hash兼容。input职责固定为Character身份参考、Scene待编辑原图、同Scene binary mask；mask白编辑、黑保护，不自动推断bbox或生成mask。
- 新profile `workflows/profiles/p7_1_qwen_masked_edit.json`，lane `qwen_image_edit_2511_masked_local`，sealed profile hash `d9179d4f83a5572d09a14778587f9cb836eb603dc0ade6aacfe27650bfbf35b7`。Scene进入Qwen image1与latent，Character进入image2；mask进入latent noise mask和最终 `ImageCompositeMasked`，目标仍是原Scene。请求尺寸须为8的倍数，source/mask尺寸一致、PNG不透明且mask仅0/255。
- `image_edit_mask.py`在input、candidate activation及standard reader复验registered bytes/identity/geometry；output所有mask=0的RGB像素必须逐像素相同。保护承诺是像素，不是整PNG文件hash相同；mask内正确性仍靠真实QA，不能由composite签七倒影或原剧情PASS。
- 共享 `CanvasProductionService.prepare_image_workflow` 与既有CLI同名action仅做无副作用准备，输出exact request/preview/profile。该action不加载operator runtime。真实生成仍通过现有注入provider、authorization与 `ProductionStateCommitter.generate_image_asset`，candidate沿 `canvas_image_candidate_preparer`，P5/Registry/provenance/replay保留唯一owner。
- Supervisor新增显式 `--core-only`，禁用custom/API nodes并设置HF/Transformers offline；默认启动行为不改。没有增加ControlNet权重、pose/depth路线、多层renderer或Seedream云mask能力。

实现与接口见 [共享Harness文档](../canvas-production-harness.md)、[spec](../superpowers/specs/2026-10-14-canvas-masked-image-workflow.md)、[plan](../superpowers/plans/2026-10-14-canvas-masked-image-workflow.md)。研究报告顶部同步当前supersession；旧“无本地mask”事实保留为历史，不改两次base的sealed QA。

### Actual Verification And Runtime Boundary

工程证据 `.agent/harness/runs/canvas-masked-image-workflow-20261014-r1/receipt.json` 绑定非空23 owned paths、base `0765a404a046cd59c3adcb03112e7304e360e439`、index tree `a60c3027934ba7c62013027320a21900b3438cf4`。18 selected checks中16实际执行PASS，2由同轮reader/state覆盖跳过；无unmapped fallback。包括Production reader569、state962、Canvas218、image172、Seedream38、supervisor18项测试；不同suite的重叠测试不计为独立质量证据。新增测试覆盖selected mask拒绝、三引用lineage/readback、fake provider坏保护像素不激活、exact replay、CLI禁止加载runtime、核心拓扑篡改及旧profile字节。

Architecture PASS保留两个已有大文件增长WARN（image有效行+10、reader+4），没有刷新baseline或增加例外；拓扑独占新module，Comfy adapter缩减。提交前canonical `verify-receipt` 实际 `fresh=true/closure_eligible=true`；提交tree与该index tree完全相同。共享工程 `d37d0482e4a0d6205b2c546ba010e24433dccd8c` 已push，`git ls-remote origin refs/heads/main` 实际返回相同SHA。提交后不把旧staged receipt冒充当前fresh，而是保留已验证snapshot→commit tree对应关系。

`runs/canvas-masked-image-workflow-20261014-001/runtime-readiness.json` 为本机**只读**profile preflight实际PASS，耗时36.312秒；完整测三模型bytes/SHA、ComfyUI commit `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` 和所需14个node/input。已有Qwen diffusion40,861,031,560 bytes、text encoder9,384,670,680 bytes、VAE253,806,246 bytes均匹配sealed profile；未安装/下载模型。预检使用明确标记technical fixture，非原S01 source，不新增媒体样本；`generation_calls=0/model_inference=NOT_EVALUATED`。

Supervisor实际启动任务自有unit `ai-video-comfyui-6970131d868d4c7faec099f4894ee27c.service`、invocation `2638eaeb66c94102bb7a113174d8bf15`，strict loopback/core-only；完成只读核验后先验证同unit/invocation再停止，实际inactive/not-found。`runtime-supervisor-binding.json`、`runtime-stop.json`保存实际所有权和停止结果，没有接管foreign service。本预检只证明该次readiness，不是持续在线或GPU推理成功。

最终Risk Gate为 `KIMI_REVIEW_NOT_REQUIRED`，exact snapshot、owned hashes、spec/plan与fresh receipt以及三个trigger逐项判断写入 `implementation-review-risk.json`。未改credentials、paid ledger、egress或unknown恢复规则；existing intent/permit/committer仍独占，protected-pixel failure在激活前拒绝。剩余实测画质缺口需真实模型/媒体QA，不能以code reviewer代签。原生delegation结果不是独立implementation review或acceptance。

### Original Story And Learning Boundary

本实现新增真实图片/视频调用均0，原Production/paid budget未变，两次旧FAIL不重判。原场景尚未按新route注册source/mask；历史review PNG宽941不满足新lane尺寸契约，任何准备必须显式保留原bytes并形成新asset/revision，不能偷偷改图或把review图改为accepted S01。原首帧七完整倒影、林砚缺席及左手/右手机职责均保留；不重引入“必须八实体全可见/正常八倒影底图”的额外要求。

后续仍须实际准入可审阅输入、local generation及原S01专属QA；S01/S02逐镜MP4、actual handoff、声音语义/时序/口型、canonical字幕/trim与HyperFrames、human1.0x均未完成。两镜7秒不代表原15秒S01–S04或完整故事AC-7；声音路线仍有独立 `EVIDENCE_REPAIR_FIRST`。

本稳定checkpoint按 `record-ai-video-session` 更新同一主record，自动按 `distill-ai-video-learning` 评估为 **no_candidate**。技术fixture、scripted tests、runtime预检及多个proof层不是新独立画质实验；没有实测本地workflow与Seedream的可控对照，也没有更新既有Vidu claim的exact媒体证据。原Evidence Index不添加假媒体attempt，不修改Skill/Policy/Gate、不刷新RAG或全局memory；record没有触发新的媒体、Provider、research或额外全套测试。foreign dirty/staged均保留，只提交当前owned路径。

## Actual Local Masked Generation And Targeted Repair — 2026-10-14

用户继续后，原生mapping确认新mask/crop/padding没有合法原node/human-web import接点。共享 `production/image_preparation.py` 复用Registry/PreparedArtifact，独占显式最小8倍数padding、crop、binary region mask与source/operation receipt；标准reader重放同一leaf验证。Native worker18项unit测试，Parent补APNG拒绝、如实 `local_pixel_preparation` origin与typed loader错误；真实标准loader/revise的tamper测试先RED后GREEN。focused suite61 PASS，工程 `49485ee5bfff539e4ebb9a5902a37c0dd501e0e3` 已push并核验remote main。

`.agent/harness/runs/canvas-image-preparation-20261014-r1/receipt.json` 绑定exact12 owned-path commit range：16 selected checks中15实际PASS、1同轮reader覆盖skip，提交后fresh=true；Canvas238、reader569、image172、image-state118、Seedream38项通过。Architecture PASS，reader薄delegation有效行+5 WARN保留。另一个writer已暂存AGENTS/playbook，采用path-limited commit保留其index，未夹带。final Risk Gate按最新native-only规则为 `NATIVE_REVIEW_NOT_REQUIRED`，source hashes/snapshot及三个trigger见 `local-masked-20261014-001/input-preparation-review-risk.json`；不调用或探测Kimi，原历史route保留。

### Exact Input And One Actual Submit

证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/local-masked-20261014-001/`。历史布局PNG仅作未accepted准备source，右补3px到944×1672，不缩放；Lin头肩crop352×480；binary mask覆盖三个玻璃内部区域。三资产原始来源、操作、RGB、SHA及content-addressed receipts已实际检查，`canonical-input-binding.json`记Manifest19→21；旧Registry/assets/attempts全部保留，Shot原intent字节不变。Lin Character revision2、opening Scene revision2按唯一committer准入；不是原S01 accepted state。

Actual request `2d5994083367b056436bd7bb98b2cccd33216de31cb9d4caa5a6054ea07c85ec`，seed2026101401、profile d9179d4f…，exact `request/preview/execution-profile/authorization/workflow` 和静态rubric均在submit前封存。operator误用不存在的budget字段在进入Provider前失败，Canonical attempt/permit未创建、transport0；核对Manifest21和空event目录后重开同一request/authorization，改用已存在 `active_paid_provider_budget`。`operator-setup-known-no-effect.json`保留错误，不视为一次图片生成、不复用permit或重抽。

Supervisor actual core-only unit `ai-video-comfyui-9d02303789fd4e1f99c54cb545464a2a.service` / invocation `8e76c619228a4deca7fd3cfc027da36a`，loopback-only/offline。fresh profile/model/refs预检、durable intent与one-use permit沿原owner通过；Observer只记录exact transport事件，不替代Production state。实际3次local上传与1次prompt submit，job `96d42b33-96dc-49fd-b359-d727da96d727`，无remote/paid/重试；执行214.693秒含fresh preflight。exact PNG `62a4414bdc72f1409c88a2fd145ad4bd06d7c85156f6051d7fb0bc2955d982e9`，944×1672、2,101,450 bytes，技术SUCCEEDED/Registry准入，Manifest25，paid budget pointer不变。

### Actual Image Review And Bounded Next Unit

Parent实际 `view_image(detail=original)` 看exact输出，复验1,096,780 black-mask像素，RGB变化0。`static-image-review.json`：2 PASS（保护像素、无文字单PNG）、4 FAIL（他人身份、七完整坐姿/站姿倒影、道具、车厢几何）、1 NOT_EVALUATED（窗内新增未能归属的深外套浅灰衣男子，不能签Lin映像缺席）。广域编辑换了脸/服装，把暗门换成白墙，保护条旁残留旧人物片段；不称“保护PASS=原剧本PASS”。首个local unit1/1用完且STOP，视频0，没有原native音轨、字幕/trim、handoff或HyperFrames。

新有限修复证据 `local-targeted-repair-20261014-001/bounded-local-repair-unit.json` 保留该predecessor与精确FAIL图。最多再2次local submit、每次1200秒、blind retry0，本地累计cap3、paid0：恢复历史布局source，先只处理Zhou站姿并用Zhou自己的身份crop；该target/preservation证据PASS后才只处理He截断并用He身份crop。所有完整首帧要求保持，中间修复图仍不是accepted S01，不推进后镜。unknown或target FAIL/NE、缺新可归因变量或预算耗尽停止；不会由原paid剩余额度、旧B或新agent名字重置消费。

`record-ai-video-session`在首个真实local FAIL checkpoint更新此主record；`distill-ai-video-learning`评估仍为 **no_candidate**。现在有一个新的Qwen实测，source/ref/mask/model/目标合同与旧Seedream技术base同时不同，不能当isolated对照、推断所有工作流无效或外推既有Vidu声音claim。工程保护属性有真实证据，mask内剧情质量仍FAIL；不修改/采用Skill/Policy/Gate、不刷新RAG或全局memory。后续修复状态另经真实新receipt取代本planned段。

## Registry Retention Repair And Actual Targeted Z

### Shared Regression And Native Review

Z输入已经经唯一committer成功authoring到Manifest27，但随后标准loader报 `selected image candidate history is not retained`，未发Z POST。根因是新像素准备合并全Registry时按asset ID排序，移动了此前P7生成图，破坏其精确历史前缀。当前source/PNG/receipt没有损坏；原生 `image_workflow_seam` 只读确认现有recover只处理未完attempt，没有成功commit回滚API。Parent没有改Manifest或绕过loader手工拼状态。

工程先以standard generation→prepare→author→reopen测试复现两个RED，再把准备合并改为保留旧tuple并追加新records。已提交旧排序仅由标准reader的最窄只读successor证明重开：连续hash-bound成功authoring边、所有旧AssetRecord全字段保留、新增限candidate明确引用的IMPORTED/DERIVED IMAGE；原P7 base→candidate append-one、receipt/placement/activation/bytes仍独立验证。普通membership、删改旧record、未引用新增、missing/non-authoring边仍拒绝。matrix/spec/plan同步该边界，没有第二writer、timeline或renderer。

首个候选 `725f2fa81d2dc4d7e514826e4637dcbed367d672` 的exact7路径Harness通过；Risk Gate基于新历史准入可能影响后续canonical effects的后果、branch/chronology剩余语义缺口及对抗审查增益，选择一名read-only native `reviewer_xhigh`（实际 `/root/registry_retention_review`，profile TOML选定，不override、不Kimi）。round1发现REG-001缺原P7 activation下界、REG-002先过滤时间隐藏匹配分支。Parent源码确认并新增完整standard-loader RED，两个非法历史均被旧代码接受。修复后每边base≥原activation且base+2≤后继revision；先检全部匹配成功边唯一再检时间。activation计算保持reader单owner。

最终候选 `a45fa113b2ffb10bbd071bfa51753849aa82c911` focused41 PASS；exact chronology-fix range Harness通过并fresh，reader569、Canvas251、Seedream38项及所有mapped controls通过；Architecture PASS，reader有效LOC +3 WARN保留。原7路径候选的image172、image-state118与其他proof保留为历史，不虚称其receipt对新HEAD fresh。同一native reviewer round2完整有界复审finding set为空；Parent用RED→GREEN和source hashes关闭REG-001/002，不以空findings代签媒体。两owned commits已push，remote main exact SHA已核验；foreign staged AGENTS/playbook和旧dirty docs未夹带。

当前证据根 `runs/canvas-jieshi-original-s01-s02-20261013-001/local-targeted-repair-20261014-001/`：`registry-retention-review-package.json`、`registry-retention-review-r1-adjudication.json`、`registry-retention-review-r2-package.json`、`registry-retention-review-r2-adjudication.json`。工程receipt：`.agent/harness/runs/canvas-image-registry-retention-20261015-r1/receipt.json` 与 `.agent/harness/runs/canvas-image-registry-chronology-20261015-r2/receipt.json`，snapshot范围各自独立。

### Canonical Metadata Restoration

先完整只读重开真实Manifest27，其文件SHA `d342ebd4004631c64676dc31c0800b18f79d138584c2dc83cfba2ccf89d4816c` 未变；不重放Z输入authoring。随后用既有 `revise_authoring` 独立metadata repair attempt `original-s01-registry-order-repair-20261015-001` 提交原最后P7候选tuple前缀＋现有额外records，Manifest27→29、Project5→6。九个AssetRecord、Shot/Character/Scene、旧attempts及paid budget pointer全部相同，只有新Registry顺序/快照与project pointer改变；原坏排序成功历史完整保留。标准reopen PASS，模型调用0。`registry-order-repair.preview.json` / `registry-order-repair.execution.json`提供exact指针及证明；后续生成沿原严格append路径，不扩大只读例外跨非authoring效果。

### Exact Local Generation And Quality Stop

原Z单元上限最多2新submit（Z通过才H）、每次1200秒、本地累计cap3；恢复后新请求 `a6175b8930d3e7bd84ae3bff8bdc6beacc9c73be3973fd6bc1110e5dd6149455`，attempt `original-s01-targeted-Z-generation-20261015-001`，seed2026101501。Character为Zhou本人128×144 crop `4669a45199bacf80ad99ffc4409f8986fe95dee845010695aa92fb2f017a403e`，Scene为原944×1672 padded布局 `1c36a9ea7600c0d5cbc73848f6ffd1731307478027f53937cb8731502fa7e6d8`，binary mask为已注册r2 `06af95640e884cce000773daffc43f2e8024e778d83800e972b7af2f90b930bb`。r1候选遮罩未经注册/submit；本次不以旧广域FAIL图作source，不改原S01/S02动作、广播、对白、字幕或机位要求。

fresh supervisor核对exact unit/invocation、sealed模型full hashes/checkout/core nodes、当前source/registry bytes与三引用；exact request/preview/profile/authorization和实际workflow已落盘 `Z-*.exact.json`。既有committer创建durable intent/one-use permit；实际local上传3次、prompt submit1次，job `cb5464e5-3f42-44b3-b8d0-6931d784d98a`，无paid/remote/retry。端到端202.188秒含fresh preflight，Comfy prompt执行154.22秒。exact PNG `102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557`，944×1672、2,099,914 bytes，creation receipt `a0e7eb163b43e31f02973453bff1a8b5b1be982a5ea12e71eedf65cbfc8cb943`；技术SUCCEEDED/Registry准入，Manifest29→33，paid budget pointer不变。这不是原S01素材质量acceptance。

Parent实际original-resolution `view_image`：Zhou身份/衣物与原图对应、空间保持，但仍在原高度站立并扶杆，没有坐姿、膝上双手。target findings为identity PASS、seated-complete FAIL、geography PASS、preservation PASS。独立像素复验：1,536,514黑mask保护像素变化0；41,854白mask像素中40,439 RGB发生变化，不能解释为“没有运行模型”，也不能解释为动作执行成功。完整static要求仍为4 PASS/1 FAIL/2 NOT_EVALUATED：Z站姿与He右边截断导致七完整倒影FAIL，Lin对应空位几何及全部道具未取得完整证明。

`Z-execution-receipt.json`、`Z-static-rubric.sealed.json`、`Z-static-image-review.json`与`unit-stop-receipt.json`封存已知输出及FAIL STOP。新单元用1/2，剩余H slot没有挪给再次Z；累计local模型2、原paid准备图2、原视频0、历史视频11。无unknown、重抽、remint或重分类旧失败。自有 `ai-video-comfyui-9d02303789fd4e1f99c54cb545464a2a.service` / invocation `8e76c619228a4deca7fd3cfc027da36a` 经supervisor停止，其他进程未动。

### Minimum Recovery And Proof Boundaries

下一有效输入路线须能明确约束Zhou坐姿/几何，同时保持其身份和非目标像素；不能继续依靠相同输入重抽。当前workflow已证明区域保护，不证明pose遵循或原S01 clean plate成功。完整七倒影、对应空位、道具和摄影的静态证据仍全部需要，之后才有资格开始原MP4→project-local video-analysis全PASS→actual state→S02自身QA。普通两镜约7秒、原前15秒S01–S04覆盖、完整故事AC-7与离线工程proof继续分开。

原生声音语义仍EVIDENCE_REPAIR_FIRST；本次没有音视频，未声称听过或正常速度验收。native audio/caption/ResolvedTimeline trim/接点/HyperFrames exact声画和用户完整1.0x听看均未交付。required target FAIL是本单元真实停止条件，不能删坐姿要求或用保护区PASS推进。

`record-ai-video-session`在此真实Gate失败的stable checkpoint更新同一主record。`distill-ai-video-learning`自动评估仍为 **no_candidate**：两个local attempt共用未accepted synthetic底图但编辑目标/角色参考/mask/prompt/seed不同，不是隔离变量对照；技术硬合成保护已由当前contract拥有，不能由两次不同质量失败推导通用Qwen能力结论或修改Skill/Policy/Gate。未找到需material update的相关existing claim，旧Vidu对白claim不在本scope；工程测试/派生crop/mask/多proof层不另计独立媒体。RAG prior failure不重试、不刷新，全局memory未写。

## Community Pose Repair Research — 2026-10-15

针对 Z 仍站立的已知 FAIL，完成 [研究续记](../research/2026-10-14-jimeng-community-workflows.md#pose-repair-follow-up--2026-10-15)：社区有只改姿势却改身份/背景、局部修改不遵循目标和 DWPose 参考失效案例；AnyPose 作者也公开多人/背景失效边界。它们是公开自述与产品/模型作者指导，不是本项目成功证据。

重开 exact `Z-workflow.exact.json` 与 pinned ComfyUI node：实际语义输入只有原场景＋脸 crop，mask 负责 noise/composite，没有坐姿参考或适配 Pose/Depth。40 steps/denoise 1 已实际使用。节点内部 reference latent 缩放与采样 latent 尺寸不同，是待审查的对齐风险，未证明为姿势失败原因。建议隔离目标单人、补明确坐姿/接触几何、通过共享 reference/profile/authoring 接入后再按原位置合成；不能以全图多人 AnyPose、增加 prompt 或盲抽替代。

本轮是资料研究与已有 evidence 核对，新增模型/图片/视频 submit、模型下载、ComfyUI 启动和 Production mutation 均为 0；旧 FAIL、剩余 H slot、原剧情及视频/声音验收边界不变。`record-ai-video-session` 更新同一主 record；`distill-ai-video-learning` 评估 **no_candidate**：公开案例未在本项目受控复现，现有不同目标 local attempts 不隔离变量，未形成可采用的新 bounded claim。无 Skill/Policy/Gate 或 global memory/RAG index 更新。文档研究不触发 implementation Risk Gate，不新增 reviewer；foreign staged/dirty 保留。

## Pose Reference Trial And MCP Execution Stop — 2026-10-15

用户要求先尝试修图、成功后再接工作流。Parent 按当前 playbook 的 Agent-side preference 选择 project-local `gpt-image-2` MCP、显式 `backend=chatgpt-web`，不是 Kimi/外部工程 subagent 或 API fallback。使用 `imagegen` 的身份/编辑底图/姿态参考职责指导，以及 `open-video` 的 known-failure repair 边界；没有改变原剧情或把先试后接变成先建新 adapter。此前 RAG layout mismatch 沿同一任务不重试/刷新，当前标准 loader、源码、原角色/Shot 与 exact receipts重新核对。

试验目录 `runs/canvas-jieshi-original-s01-s02-20261013-001/pose-reference-trial-20261015-001/`。原场景 `1c36a9ea7600c0d5cbc73848f6ffd1731307478027f53937cb8731502fa7e6d8` 和身份脸 crop `4669a45199bacf80ad99ffc4409f8986fe95dee845010695aa92fb2f017a403e` 保持原 bytes；新增944×1672技术坐姿图 `zhou-seated-pose-guide.png`，SHA `61a696b7001f2e778ef8411b2d681e176b79295e3a5dc81946a4b3c127a4363d`、11,440 bytes。它从空白画布按显式 joints/seat anchors绘制，不是模型输出、人物身份或镜面几何成功证据，未改写照片；`pose-guide.geometry.json`保留坐标。初稿膝部弯曲不够清楚，在任何模型调用前修正并实际看图。原图/脸图/姿态图三引用顺序及 SHA 经 `reference-bindings.json`重验。

`request.exact.json` SHA `8811e001d70794f03f8d34edfcdf9d5ea26f20bd53fa907e41d09e84d537fc2b`；新身份 `original-s01-pose-reference-web-20261015-001`，new conversation、n=1、请求timeout600秒；先封存 `rubric.sealed.json` 与 `one-use-call-intent.json`，最多1次 generate invocation、禁止retry。prompt只改老人坐姿、保留身份/邻座/摄影/窗面/道具；原广播、动作、对白和字幕继续由原视频/composition执行。Provider路径与姿态输入均改变，因此即使产图也不是隔离变量的 Qwen 对照。本试验不挪旧 H slot、不改变旧 paid/local计数或假造 Product reservation/qualification。

`browser_visibility`从未启动状态开启专用浏览器；提交前 `backend_status`为ready=true，actual MCP `generate_image` 调用1次。客户端返回 `timed out awaiting tools/call after 300s`，**不证明未发生生成或可重试**。`mcp-call-timeout.json`保持原工具超时类别。仅通过既有 browserConnection owner/loopback校验连接现有页，对同一次完整请求只读取证，没有 Send/新请求/新tab/修改工具。请求在现有页不存在，user/assistant消息数0，因此匹配门拒绝继续collectImages/export；独立复验 document complete但body空白，无main/composer/file input，后续backend为ready=false、starting=true。没有取回图片或视觉裁决；`page-discovery.json`和`readiness-diagnosis.json`保存只含非敏感分类事实，未保存 session/browser URL/private diagnostics。

为阻止已超时的startup以后迟发，核验仅有本次从browser_open=false启动的专用空白ChatGPT tab，且仍无main/composer/messages后只关闭该tab；`startup-stop.json`保存动作/URL hash，不关闭其他浏览器或进程。这个动作不反证历史零POST，remote submit count/outcome仍 **NOT_EVALUATED / UNKNOWN**。`unit-stop-receipt.json`封存EXECUTION_EVIDENCE_GAP和STOP：observed output0、后续调用0、API0、Comfy0、workflow integration NOT_STARTED、全部visual findings NOT_EVALUATED。它是执行入口阻塞，不是坐姿方案或模型质量FAIL。

标准 `load_production_project`在试验前后均成功；`production-before.json` / `production-after.json` 的project bytes、Manifest/Registry规范模型hash及Manifest33完全相同。无Production writes、输入准入或activation，无新视频/音频/HyperFrames；原full S01、真实接续、human1.0x、完整故事AC-7均未通过。本单元1/1 invocation已用且不释放；原准备paid图片2、本地模型图片2、原视频0、历史视频11是已确认历史，不把未知web调用算成0或已完成图片。

最低恢复条件：先由同一次调用的可靠证据完成outcome reconciliation，再恢复并核验实际composer/upload readiness；unknown未关闭前不补发、不改用本地、不remint该intent。取得新bounded候选后，须完整验坐姿/身份/邻座/保护/尺寸，再决定共享工作流接入。

在真实blocker处按 `record-ai-video-session`更新同一主record和研究状态。`distill-ai-video-learning`评估 **no_candidate**：没有新可验媒体，不能验证姿态假设或自动采用社区方案；该工具超时与历史其他MCP问题边界不同，未建立可采用的重复机制。无Skill/Policy/Gate、global memory或RAG index更新。没有源码实现，implementation Risk Gate不触发；Parent完成artifact/状态核对，未新增reviewer。foreign staged/dirty保持，文档checkpoint的exact Harness/commit/push另由实际receipt与Git报告证明。

## Codex Direct Image And Authoring Workflow Rule — 2026-10-15

用户连续明确要求Codex直接接入、自带Generated Image参数和实际效果，随后要求将规则写入工作流。新的独立单元使用 `image_gen.imagegen`，不调用Qwen、ComfyUI、浏览器MCP或CLI/API fallback；原UNKNOWN单元没有重放/重分类。exact request `9cdd1fdf7ea2a660361cd3a5b145ccf9557924d74b31bcb9df1ba70c969610d2`，attempt `original-s01-codex-direct-image-20261015-001`，最多1调用、实际1、retry0。沿用原布局、老人身份crop与明确坐姿图三个角色分工；原图没有被直接编辑或覆盖。`image_gen`返回真实图片，底层模型/采样参数未暴露，不伪称具体model/profile qualification。

图片为 `runs/canvas-jieshi-original-s01-s02-20261013-001/codex-direct-image-trial-20261015-001/s01-zhou-seated-codex-candidate.png`，SHA `f9128ccfde3868ed8aaea420f953e306b37c003e139fd0d85943774eea057e93`，RGB PNG、943×1668、2,027,887 bytes。从工具原始文件exact copy入项目工作目录，原始文件保留，不resize/crop/重编码；`generation-record.json`实测绑定request/output事实，不保存私有session或假model设置。

Parent实际original-resolution看图，并在写规则时重新核对bytes/尺寸/标准项目状态。`static-image-review.json`：同一老人身份衣物、完整坐姿/屈膝/可见鞋、双手自然合放膝前且不握杆、可见邻座/机位关系、非目标人物及无新增文字五项有界PASS；身份不代human attestation，机位不代镜面/镜头标定。原图944×1672与输出943×1668不同，精确保护区等价为NOT_EVALUATED。原最右何静截断仍在，七完整倒影没有通过；林砚缺席对应几何和全部道具仍NOT_EVALUATED，音视频及human1.0x未验。局部效果成立不授权原S01 accepted source、后镜submit或完整故事AC-7。

`production-before.json` / `production-after-generation.json`和规则记录时标准loader复验：project bytes、Manifest bytes/Registry规范模型hash均一致，Manifest33；实际素材导入/activation NOT_STARTED。已确认历史原准备paid图片2、本地模型图片2、原视频0、历史视频11不改；新增内置图片1单独列出，旧web调用UNKNOWN不算作0或完成图片。写规则这一阶段新增媒体/模型/Provider调用为0。

默认规则由用户直接指定，写入 `.agent/context/control-plane-playbook.md` 的 **Agent-Side Image Generation Provider Preference**，详细流程只归 `docs/canvas-production-harness.md` 的 **Agent Image Authoring Workflow**：身份/场景/姿态职责→实际支持的prompt/参考/透明背景字段→有界尝试→图片及完整要求QA→现有generated_source/canonical committer导入。明确不接受ComfyUI JSON/seed/steps/CFG/sampler/latent mask/ControlNet参数，不把语义参考当硬节点、尺寸或像素保护；Qwen仅为已选择的可选路线，不新增Product backend/脚本/状态owner。已有mask路线、paid/unknown/逐镜视频/声音/剪辑验收合同保持。

写前发现playbook已有foreign暂存的native reviewer迁移，与当前生图小节同file；用户明确选择A，授权只改生图小节、独立提交，原暂存保留。原 `AGENTS.md` 及其他foreign paths不编辑/夹带；独立Git index仅用于本次owned patch的隔离提交，不是development worktree或Product状态库。提交后核对原foreign暂存路径、其他blob和playbook原暂存增删内容，不能把另一任务迁移声称为本次工作。

Native Codex Parent串行完成这一有界文档变更；没有源码/parser/lifecycle/credentials/budget/Gate改动，用户未要求independent review，未触发重大后果与验证缺口，Risk Gate为NATIVE_REVIEW_NOT_REQUIRED。前置规则budget检查曾暴露正文超限，仅精简本次生图summary、详细指导留唯一workflow owner后重新PASS，不增registry限额。exact最终commit range Harness必须另核验fresh receipt，工程/文档PASS不代媒体验收。

按 `record-ai-video-session`稳定checkpoint更新同一记录。`distill-ai-video-learning`为 **no_candidate**：单次内置图片能证明该次坐姿效果，不能由模型/姿态输入同时改变推导通用胜率；旧web超时无图片，不算视觉反例。规则属于用户明确的新偏好，不是自动采用Learning Claim；没有制造第二确认、改Skill/Policy/Gate、刷新RAG或写global memory。

## Evidence Index

此表只为本次原开场准备单元建立identity；历史其他实验不并入。remote boundary为Seedream/`doubao-seedream-5-0-pro-260628`、Ark shared image owner、1152×2048 PNG；新增local boundary为Qwen-Image-Edit-2511/三引用masked profile、944×1672 PNG，不与remote合同或计数合并。同一图片的receipt、bytes、materialization和visual proof使用同一request fingerprint independence_key，只贡献一个图片样本；预transport失败不是第二个视觉样本。

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
| local-masked-execution | native-image:2d5994083367b056436bd7bb98b2cccd33216de31cb9d4caa5a6054ea07c85ec | jieshi-original-local-masked-20261014 | original-s01-local-masked-20261014-001 | N/A | 62a4414bdc72f1409c88a2fd145ad4bd06d7c85156f6051d7fb0bc2955d982e9 | LOCAL_MODEL_EXECUTION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/local-masked-20261014-001/execution-receipt.json |
| local-masked-visual | native-image:2d5994083367b056436bd7bb98b2cccd33216de31cb9d4caa5a6054ea07c85ec | jieshi-original-local-masked-20261014 | original-s01-local-masked-20261014-001 | N/A | 62a4414bdc72f1409c88a2fd145ad4bd06d7c85156f6051d7fb0bc2955d982e9 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | local-masked-execution | runs/canvas-jieshi-original-s01-s02-20261013-001/local-masked-20261014-001/static-image-review.json |
| local-Z-execution | native-image:a6175b8930d3e7bd84ae3bff8bdc6beacc9c73be3973fd6bc1110e5dd6149455 | jieshi-original-local-targeted-repair-20261014 | original-s01-targeted-Z-generation-20261015-001 | N/A | 102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557 | LOCAL_MODEL_EXECUTION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/local-targeted-repair-20261014-001/Z-execution-receipt.json |
| local-Z-visual | native-image:a6175b8930d3e7bd84ae3bff8bdc6beacc9c73be3973fd6bc1110e5dd6149455 | jieshi-original-local-targeted-repair-20261014 | original-s01-targeted-Z-generation-20261015-001 | N/A | 102c1ec74f873a0de8297d2cf9de1477a9ae1cf0b0fc654836e6e8dc7e127557 | VISUAL_INSPECTION | FAIL | QUALITY_FAILURE | SAME_EVIDENCE_NEW_PROOF_LAYER | local-Z-execution | runs/canvas-jieshi-original-s01-s02-20261013-001/local-targeted-repair-20261014-001/Z-static-image-review.json |
| pose-web-invocation | external-authoring:8811e001d70794f03f8d34edfcdf9d5ea26f20bd53fa907e41d09e84d537fc2b | jieshi-original-pose-reference-trial-20261015 | original-s01-pose-reference-web-20261015-001 | N/A | NO_ARTIFACT:OUTCOME_UNKNOWN | LOCAL_TOOL_EXECUTION | OUTCOME_UNKNOWN | EXECUTION_EVIDENCE_GAP | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/pose-reference-trial-20261015-001/mcp-call-timeout.json |
| codex-direct-generation | native-image:9cdd1fdf7ea2a660361cd3a5b145ccf9557924d74b31bcb9df1ba70c969610d2 | jieshi-original-codex-direct-image-20261015 | original-s01-codex-direct-image-20261015-001 | N/A | f9128ccfde3868ed8aaea420f953e306b37c003e139fd0d85943774eea057e93 | TOOL_GENERATION | SUCCEEDED | NONE | NEW_ATTEMPT | NONE | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-direct-image-trial-20261015-001/generation-record.json |
| codex-direct-static | native-image:9cdd1fdf7ea2a660361cd3a5b145ccf9557924d74b31bcb9df1ba70c969610d2 | jieshi-original-codex-direct-image-20261015 | original-s01-codex-direct-image-20261015-001 | N/A | f9128ccfde3868ed8aaea420f953e306b37c003e139fd0d85943774eea057e93 | VISUAL_INSPECTION | NOT_EVALUATED | EVIDENCE_GAP | SAME_EVIDENCE_NEW_PROOF_LAYER | codex-direct-generation | runs/canvas-jieshi-original-s01-s02-20261013-001/codex-direct-image-trial-20261015-001/static-image-review.json |

## Historical Record And Learning Update

本节为此前第二张paid PNG checkpoint；最新local/engineering评估见上文，历史计数不改写。

前一次checkpoint的no_candidate基于一个视觉样本，为历史结论。本次按 `record-ai-video-session` 更新同一主记录和README，原文/媒体/receipt及foreign dirty保留。按 `distill-ai-video-learning` 自动重新评估仍为 **no_candidate**，但不再声称只有一个视觉样本：已有两个独立实际图片attempt，proof层和旧closure不另计样本。旧图错误为倒置车顶映像/双手持机，新图侧窗/手改善却少人物/重复反射/新增标题；多项输入同时变化，不是isolated-variable comparison。不能由这些输出断言模型不具该能力、添加禁用人物/倒影规则或证明改Skill会解决。现有完整image QA/FAIL STOP已覆盖观察，未形成需要新adoption target的有界机制结论；既有Vidu对白/burned-caption claim明确排除人物/倒影与其他Provider，不构成material update。没有制造重复claim、修改Skill/Policy/Gate、刷新RAG或全局memory。

共享工程已发布0234fc5并核验remote，当前文档checkpoint的receipt/commit/push另列实际结果；工程证明不代图片QA、raw连续镜或正常速度human声画验收。原hook `ai-video-record-6104c772eca8de88` 已在前一record checkpoint以recorded/no_candidate ACKED；本更新不重复ACK旧request或猜新ID。
