---
record_kind: session_summary
topic_id: hotpatch-warmholiday-continuity-repair
learning_eligibility: ineligible
---

# Hotpatch Warm Holiday Continuity Repair

Date: 2026-10-24 (Asia/Hong_Kong)

## Supersession — Vidu Comparison And Source-Audit Closure

后续实际结果见[Vidu同稿原片记录](2026-10-24-hotpatch-vidu-same-script-source.md)：用户取消旧片尺寸修复，确认8×7厘米指橙盒，并要求原稿仅换Vidu；已生成一次47秒对照原片、官方返回1363积分，发现贴皮肤及末镜被子变马甲的问题，未当作广告定稿或发布。本文下方工程等待状态也已取代：source-audit修复的适用staged Harness经native依赖环境修正后PASS，三个owned paths已commit/push为`0734ee6be99a235f62a438bd3f87860b39248486`；详细receipt与旧失败历史保留在新记录中。此notice不改变旧47秒MP4或其尺寸缺陷。

## Human-Held Product And Moving Watermark — 2026-10-24

### Later User Decision And Engineering Verification

用户先回复“可以,vidu再做一条”，随后指出末镜橙色包装盒过大，并明确盒子实物长8厘米、宽7厘米（不是贴片尺寸）。之后又明确“用vidu再做一下吧,这不管了,大小你记住就好”：旧47秒成片不再修，保留原文件，不能再把它记为尺寸准确；新Vidu片必须采用此事实。旧片尺寸修复未提交新的Jimeng视频，一次内置imagegen调用被用户中断、未收到结果，outcome/cost UNKNOWN，不重试，见`box-scale-repair/cancelled.json`。按用户“记住”要求仅写一条memory extension note，未直接修改全局memory registry。

已有source-audit修复随后跑完整相关HyperFrames模块：`python -m pytest -p no:cacheprovider tests/test_production_hyperframes.py -q`，结果204 passed / 3 skipped / 52.29s；跳过项未算真实render通过，本次已另有真实47秒HyperFrames lint/check/render证据。此检查只覆盖相关模块，不冒充全仓Harness。下方deferred描述为当时历史，当前owned-path提交与push状态以后续实际receipt为准。

用户要求将静态包装尾卡改为人物手持宣传，并添加动态“乐喜呵护商贸”。已实际输出47秒审片副本：`/home/reggie/电商/热敷贴/成片/给腰放个暖假-47秒-真人产品收尾-乐喜呵护商贸.mp4`，SHA=`7df16787d4a2f32e538bdcbdc5b206bc3c737104baa760c7fb737019a4d798e5`，54,329,346 bytes，1080×1920/24fps/1128帧，AAC48kHz stereo。副本与HyperFrames verified staging逐SHA一致；仍NOT_PUBLISHED、未声明用户整片视觉或混音验收。下方旧静态卡片与O3声音待确认状态为历史，已由本节相应证据取代。

本次证据根为`runs/hotpatch-warmholiday-seedance20-20261024-001/held-product-close/`。`film-preparation.json`、`film-composition.json`、`film-timeline.json`、`film-render-output.json`、`final-mcp-analysis.json`、`final-audio-technical-review.json`、`delivery-copy-receipt.json`绑定实际成片。前42秒visual和native source windows/gain均与r4相同，42–47秒改为H1R手持包装；旧静态卡片图层和旧品牌TTS均不再入片。前42秒混音PCM与旧r4逐字节相同；最终AAC在42秒边界因新末段编码并非逐字节相同，未把它误记为全音轨相同。各对白窗口非静音，全轨解码无NaN/Inf，峰值约-1.80dBFS；新末段RMS约-18.37dBFS、peak约-2.42dBFS。完整混音听感仍交用户审片，不调用Gemini或音频理解Provider。

O3声音由用户“声音正常”关闭；`O3-canonical-diagnosis.json`现六项PASS，旧pending答案保留在`preflight-history/O3-audio-confirmation/`。H1五秒原片SHA=`e843ae6a214a1ae9b656f41f36a890d677f5c8c15f0b9a032b094f1d115a2b8f`，用户确认“台词和声音正常，保留”，但actual MCP与独立review均发现肩背被子消失，identity/space-camera FAIL，未采用且消费未重置。单次受控内置imagegen参考编辑被HTTP400 moderation_blocked拒绝，无可用图像，未换API重试或伪造图像。其失败记录为`H1R-image-edit-failure.json`，费用未知。

H1R使用既有实拍式办公室状态参考13-O1-office取代旧人物参考，产品02-carton保留；先封新有限单元，保留旧bounds与七次实际消费，最多一次修复、零自动重试。H1R canonical prepare/start/submit/poll/fetch已知成功，request=`9a19e28e8a6063ee046d1f20139197a4e70003ca0b60e5c34da0cda7e577fdac`，原片SHA=`46b2075691639f4fd2ba16f26718446c8ca19906bf082013126eb6a1088e22f9`，6,344,896 bytes，video5.016667秒/121帧、AAC5.088005秒。显式project-local MCP逐0.25秒21帧检查，肩背/腿被保留，双手承托纸盒、前递后收回可读；用户另对这份exact H1R原片确认“台词和声音正常，保留”，没有沿用H1听音结论。`H1R-canonical-diagnosis.json`六项PASS，旧pending答案/诊断保留`H1R-audio-pending-history/`。包装主版式可读，不宣称生成细字逐像素准确；硬切至已持盒的商业收尾，不虚称拍到取盒动作。

同一画布全部历史节点保留，H1为第8节点，H1R为第9节点`node_32jcvjwnb1`，未覆盖旧生成。当前总实际视频submit为8：O1/F1/O2/F2/F3/O3/H1/H1R；F4仍未提交。新增H1/H1R两次使用Seedance2.0 standard，未调用Vidu或新视频Provider。500CRD是内部上限，不是市场价或实际花费，实际扣分未取得可归因结算证据，标待确认。

动态水印通过同一CompositionSpec→ResolvedTimeline→HyperFrames输出，10段TextDesign共享全片clock，x约64→264px、y微动，嵌入Noto CJK SC六字子集、43%透明度，无底板；Parent实际MP4抽查0/3/…45秒可见且位置变化，没有复活“想象画面”字条，原生AI来源标记保留。隔离Chromium computed-opacity检查证明各cut只显示一个水印容器；早先怀疑的TextDesign NONE跨镜泄漏是分支混淆，实际step-end分支正确，未修改该CSS分支。

实际导出另触发了真实共享source-audit错误：legacy percent兼容分支只看commercial_graphics、未看text_layers，默认商业字与自定义水印font_weight组合会在构造本不适用的legacy候选时抛错。Parent只将兼容资格检查扩大至两类实际图层，与现有render拒绝条件对齐，未放松source一致性审计或加fallback。两例回归测试先真实失败，再与旧版可读/改字拒绝检查共5项通过，证据`/tmp/hotpatch-watermark-regression-red.log`及`/tmp/hotpatch-watermark-regression-green.log`；实际HyperFrames0.7.103 lint/check均exit0，check保留2warnings，最终1128帧已导出。必要局部修复为`src/ai_video/production/hyperframes.py`及`tests/test_production_hyperframes.py`，此前两文件无foreign dirty；Risk Gate为NOT_REQUIRED（局部可逆、无授权/凭据/持久化语义变化，实际失败路径被测试与成片覆盖），Parent自审。

post prepare还修复了作者证据闭包：H1R继承的authoring-input不都位于新root，content_hash也不是文件raw SHA；改用canonical require_authoring_input从限定来源根验证并原样捕获，未改源实体/媒体或杜撰provenance。首次失败发生目标bootstrap前，记录保留；成功后经committer建立独立review Project，未复制付费Manifest。render入口一次LoadedProductionProject.project_id误取在副作用前失败，已改为project.project.project_id；后续真实审计失败的staging r1保留，成功r2独立输出。

按film-first规则先交实际成片，暂未扩跑完整工程套件或commit/push这些制作及必要修复；待用户认可效果后补适用工程验证并提交owned paths，保留其他窗口dirty/index。record-ai-video-session更新本唯一主记录；distill-ai-video-learning评估为no_candidate：H1/H1R的参考与prompt同时改变、seed未控，不构成隔离变量比较，没有足够证据将单次修复推广为通用模型规律。未新增学习claim或修改Skill/Policy/Gate、全局memory。

最终独立reviewer_high核验同一SHA，抽查16时点及42秒接点、12/26/44秒放大，finding set为空；水印在白百叶上偏淡但仍可读，未遮脸/商品，未发现新的视觉blocker。范围仅视觉抽样，不代称正常速度整片声画或用户验收。Parent保存`held-product-close/final-review-receipt.json`，含exact source/test hashes、局部验证与未commit/push边界。

## Current Composite Review — 2026-10-24

用户随后要求去掉截图中的“想象画面”。已在原composition移除F1/F2A/F2B三处对应graphic，由同一HyperFrames重新导出r4，交付`/home/reggie/电商/热敷贴/成片/给腰放个暖假-47秒-去提示字审片版.mp4`，SHA=`4d20606fdaf953520f5eb4995a75d66ea081e9bcffe189ba46f7dd09888fec1f`。1128帧/47秒保持，visual/audio spans与r3完全一致，其余graphics完全一致；新旧MP4完整解码PCM SHA相同。显式project-local MCP抽16帧，Parent核对9/21/30秒三处均无该字条；原生AI来源标记保留。证据见同run的`current-cut-47/remove-label-review.json`、`remove-label-mcp-analysis.json`与`remove-label-delivery-receipt.json`。r3及其输入保存，0新Provider submit；仍为审片、NOT_PUBLISHED，用户整片验收未声明。此更新仅补充同一剪辑链版本，无独立实验，learning=`no_candidate`；继续按film-first等待审片，不扩跑工程或commit/push。

用户最新要求“拼接合成看下”，本次已实际交付47秒当前素材审片版；下文未出整片的结论仅保留为此检查点之前的历史。文件：`/home/reggie/电商/热敷贴/成片/给腰放个暖假-47秒-当前素材合成预览.mp4`。exact SHA=`6596e5863634344215667c305f9b23a88ad3196a90ffb3585de6facf48833396`，49,983,714 bytes，1080×1920 H.264、24fps、1128帧、47.000秒，AAC48kHz stereo。尚未生成的F4不在这一版；55秒计划保留，本次新增Provider submit=0。

相对证据均位于`runs/hotpatch-warmholiday-seedance20-20261024-001/current-cut-47/`：`film-preparation.json`、`film-composition.json`、`film-timeline.json`、`film-render-output.json`、`final-mcp-analysis.json`、`final-audio-technical-review.json`、`delivery-copy-receipt.json`。外部观看副本与`finished-film-render-r3/verified.mp4`逐SHA一致。唯一ResolvedTimeline顺序为O1 0–8 / F1 8–16 / P1 16–18 / F2A 18–25 / P2 25–27 / F2B 27–32 / P3-P4 32–36 / O3END 36–42 / HERO 42–47；P1-P4来自同一O3原片0–8秒，电话对白完整保留在F2B，源音画按同一秒数原速截取。

每个生成视频源的完整原声先解码为48kHz stereo WAV，按editorial alias精确source window进入显式P4轨；visual REPLACE只避免重复播放，不删除原对白/SFX。O3END按实测提升5dB，其余native轨0dB；42秒接既有本地品牌旁白“医健树护腰贴，给腰留点暖意”。实际成片各对白窗口非静音，peak约-1.80至-4.19dBFS；品牌窗口RMS约-16.16dBFS，末尾配乐RMS约-35.87dBFS。完整解码无NaN/Inf；这些仅是技术音频证据，未调用Gemini或音频语义Provider，用户听审仍NOT_EVALUATED。

本地准备适配修正：保留源实际VFR测量（193/289/361帧与名义8/12/15秒），使用既有development preview原速output clock；原声全长保留AAC尾部而不伪造24fps或提前截断。派生原声的input asset绑定目标已捕获MP4别名，不引用目标Registry中不存在的原Provider asset ID。收尾图先用严格bootstrap创建原始creative/Registry项目，再由committer原子提交完整派生图及其receipts和最终Project v2，未修改共享bootstrap合同或直接写Product state。

首个本地render在check阶段因提示重叠/对比度失败，无成片；改为分区提示与淡入。r2已完成，但实际看图发现袋装小图挡住包装，且配乐原截段尾部近静音；保留r2输入/MP4/分析，将r3收尾改为单张完整实物包装与有乐声的既有CC0片段。r3 HyperFrames0.7.103 lint/check均exit0、0errors，check保留1warning，不声称零警告。显式project-local video-analysis MCP对exact r3 MP4提取16帧，禁用ASR/understand_audio；Parent结合原速剪辑窗口、r2联系表与r3实物收尾逐项核对。最终审美和正常速度完整听审由用户裁决。

本次为用户明确要求的当前素材连贯看听副本，不改变O3 sound NOT_EVALUATED、不写source六PASS、不允许据此提交F4。没有Production activation、P6或Final Acceptance，publication=`NOT_PUBLISHED`。按film-first先交审片，未启动完整工程套件或commit/push本次制作记录；foreign dirty/index保持原样。`record-ai-video-session`更新此唯一主记录，`distill-ai-video-learning`评估=`no_candidate`：同一剪辑链的r1/r2/r3不构成独立实验，未新增claim、修改Skill/Policy/Gate或全局memory；未为记录执行Provider、媒体或额外测试。

## Current Direction

用户要求继续实际广告制作。先前“三段不搭边”的反馈针对连续性，同场/换景均可，产品开头与问题同框、隔衣使用、45–60秒、即梦 Seedance 2.0、保留原声及必要旁白的要求仍有效。

本轮将原58秒排法临时调整为52秒：O1 8 / F1 8 / F2 12 / F3 9 / O3 10 / HERO 5；排除提前回现实且隔衣细节缺证的O2，但保留其MP4、节点、未关闭finding和真实消费。这个排法随后又收到用户明确反馈：**“为什么这么久了没看到产品”**。按该排法8–37秒连续是幻想，真实贴片离开画面约29秒；不能把产品开头出现一次、结尾再放包装当作商业主线已满足。

用户随后明确选择“夸张剧情主导：保留套房，但每个笑点都切回真实贴片与使用动作”。Parent停止原F3重试，封存新的55秒产品贯穿coverage：O1/F1保留，F2拆为展开与电话两个完整语义单元，每单元回切同一办公室的真实腰侧贴片；取消偏离腰部的拖鞋，新增独立F4腰后靠垫单一笑点；O3改为15秒真实产品动作/结尾对白的源素材。见`product-intercuts-55/director-repair.md`及`delivery-selection.json`。实际O3产品窗口/对白时间仍待生成后核验，不能先声称剪辑已完成。

## Preserved Canvas And Calls

Run: `runs/hotpatch-warmholiday-seedance20-20261024-001/`。

同一作品[即梦画布](https://jimeng.jianying.com/ai-tool/ai-canvas/b0d2c76f-5f9a-4fd1-9d9b-cfaf55221f37)及原六节点保留；native UI一次增加F4空video节点`node_m1q1r46xk9`，server draft18核验共7节点、旧6未删、F4无resource，0新增生成。模型仍为`seedance_2.0_vip`，没有Fast/Mini/2.5或隐式fallback。

原`operator-bound.json`6初始调用/3000 CRD总上限保持原字节。Parent依据新的用户创意方向，在`product-intercuts-55/operator-bound.json`封存七独立Shot slot/3500 CRD总upper的有限单元，链接旧封套SHA及5次已知真实消费anchor；每次500 CRD、0自动重试和原expiry不变。新增最多为未提交O3一次15秒及独立F4一次8秒；不复制F3 Manifest、不将F3失败改成PASS，不重置任何历史。这是task必要续单元，不是实际市场价或已结算花费。

当前共6次已接受视频调用：O1、F1、O2、F2、F3、O3；F4尚无视频调用。此次新增F2/F3/O3三次，实际扣分尚未取得可归因结算证据，标待确认，不用500 CRD上限冒充花费。历史前三段记录报价合计308 CRD不代表本轮总实际结算。新封套中`known_new_video_submits=5`是续单元时的不可改历史anchor，不是当前实际计数；当前实际6由全部原root Manifest重读得出。

## Exact New Media

| Shot | Exact media | Findings |
| --- | --- | --- |
| F2 | `86bd72c23f769c83a21d53ce09db2d88c4dbd1c26595698ed9f1871b65a2fcfc`；12.097秒，18,550,199 bytes，720×1280，289帧；AAC44.1kHz stereo | 显式project-local MCP分析；Parent逐0.5秒看图，面板按下→墙顶展开→右侧边几电话露出→拿放听筒可见。用户对SHA相同原片明确回复“台词和原声正常，继续保留”。canonical六项PASS。不是整片审美/最终混音验收。 |
| F3 | `0a59203f567c700a8d2bdeac6af4c1b48078ffca44c4c5517fdbf4c87095d93e`；9.089秒，12,041,455 bytes，720×1280，217帧；AAC44.1kHz stereo | 显式MCP逐0.25秒分析。块状物先悬在膝前再变拖鞋，抬袜脚发生在拖鞋形成后；靠垫由人物从右侧搬到左侧，没有清楚自动滑至腰后；末尾不满足原定升高长圆端全景。action、space-camera FAIL；identity/performance/truth保留；sound NOT_EVALUATED。 |
| O3 | `caa9153385c9ada67296f56ad4fa6618c39c36f71c3af5b613a958df0e3188d4`；15.105秒，19,951,966 bytes，720×1280，361帧；AAC44.1kHz stereo | 新现实产品主线，显式MCP逐0.5秒分析。0–8秒白衣上的单片持续可读，轻按/手指滑动，平稳后撤至原办公室双人景；9秒后同事口部动作，女子11秒回头/说话至14秒。五个视觉finding PASS（analyzer），sound等待用户个人听音，未写canonical all-PASS。 |

F2观看副本：`/home/reggie/电商/热敷贴/成片/给腰放个暖假-F2-12秒套房展开-原声核对.mp4`。F3问题副本：`/home/reggie/电商/热敷贴/成片/给腰放个暖假-F3-9秒动作问题样片.mp4`。副本SHA均核对相同。

O3新观看副本：`/home/reggie/电商/热敷贴/成片/给腰放个暖假-15秒真实贴片主线-原声核对.mp4`，SHA与原fetch相同。已发出绑定这份exact源的听音问题，未收到回复前保留NOT_EVALUATED。source观察见`O3-mcp-analysis.json`、`O3-parent-answers.json`。原计划女子拿杯未发生，按片/回头应答的核心产品与叙事目标可用；记录为nonblocking道具动作变化，不宣称全部prompt动作逐字执行。人物/现实办公室影像仍是生成影像，不是实际消费者见证。

F2音轨全解码成功，RMS -21.967782 dBFS、peak -1.948269 dBFS、NaN/Inf为0；声音语义和适用性结论来自用户听音，不来自波形或ASR。未调用Gemini或`audio_understand`。F3听音问题的用户回复是产品曝光质疑，不是声音确认，不能据此写sound PASS。

相对receipt：`F2-mcp-analysis.json`、`F2-parent-answers.json`、`F2-canonical-diagnosis.json`、`F3-mcp-analysis.json`、`F3-parent-answers.json`、`F3-canonical-diagnosis.json`。F3 diagnosis=`EVIDENCE_GAP + QUALITY_FAILURE`，next_owner=`evidence_owner`。没有执行quality rejection、abandon或新attempt。

## Authoring And Recovery Evidence

F2开场以F1实际末帧为准：画面右扶手的米白矩形物件是服务面板，电话从打开的墙后露出在边几，不把面板变成电话。移除冲突的旧暖屋图，明确人物/展开建筑/实际末帧三个参考职责；经committer保存authoring与依赖变更。native prompt由重复压缩后为3584 UTF-16 units，完整动作/原台词保留。request hash=`0274db25f914a2713b6161e18229238724e5bbca16aab9b429a2291e8e7b994a`。

一次新07-suite上传没有可确认结果，`upload-recovery/F2-52-07-suite-receipt.json`仍为`unknown_upload_outcome_stop`，没有重传或改写成known-no-effect。改用先前已committed的07-suite/10-F1-terminal，通过当前同账户同画布的native `assetLibrary.getOriginalImageUrl`只读读取；PNG编码不同，但完整RGBA像素和尺寸逐一完全相同。新readback receipt显式链接旧commit与当前验证，仅重封一小时task-use窗口，不冒充Provider TTL或把未知上传变成成功。随后F2正常canonical start/submit/poll/fetch，generation UNKNOWN=0。

F3通过committer登记F2实际末帧/宽景，删去无来源的普通鞋/脱鞋描述。按实际native binding顺序01-woman / 04-patch / 11-F2-terminal / 12-F2-wide写素材职责，native prompt3503 UTF-16 units；request=`e9fc370970412b779a7cac6c26cfd45ccd0cd57c6a9c573ccfb9c861cb89c9f7`。四个首次素材上传均committed；真实生成仍未执行全部动作，因此不把authoring/preflight成功当媒体PASS。

O3仅完成未提交authoring：使用O1实际办公室frame，保留橙开衫女子、蓝短袖同事、被子搭肩盖腿、白衣隔衣单片与左右关系；改为同事看见她笑而问“你笑什么？”，女子答“人还在上班，腰先放个暖假”，不再插回幻想。首次本地事务误复用immutable Scene v2路径失败，原因不是并发writer；失败attempt001、已写v2/orphan均保留。逐路径核对后，attempt002以新Shot/Scene v3成功，manifest rev11；native纯离线编译3547 units。此输入也必须按最新产品主线重新判断，不能直接以旧台词执行。见`preflight-history/O3-authoring/O3-authoring-receipt-002.json`。

## Product55 Source And Audio Checkpoint

O3后续authoring已改为15秒产品主线，保留既有所有事务；15秒profile一度误留`benefit_amount=10`，标准pure prepare在任何副作用前按typed`video_capability_unsupported`拒绝。作者经committer与新immutable Shot v5修为15/15，同benefit_type、同500 upper；Manifest rev15、Project=`d0f1e52917bbb55d500dc68718f2c2fd0efee413d4bad943c8fefacd10706f46`。新prepare request=`9e60ba85b7eaa12a3127ffe7679b73552fab76156b059d2a954a247418380905`、binding=`2d38c4a6600af53f955d58ba95dea746d0736e30598bbefac86f445f58e2e041`、native3763 units。之后首次O3 start/submit/poll/fetch已知成功；未隐式更换模型。

O3素材阶段01-woman首次上传committed，04-patch新上传UNKNOWN，未重传/改旧结果。用F3已committed的同款04与O2已committed的08，在当前O3账户/画布只读取native原图并逐RGBA像素核对完全一致；13-O1-office是首次上传committed。新`product55-reference-readback-receipt/1`明确链接旧commit、当前owner、实际readback文件/完整像素与一小时task-use窗口，Transport重新读字节/像素验证；不是伪称新的upload成功，也不是Provider TTL保证。原UNKNOWN保持未选择、未解决状态。材料四份验证后才submit。

F4已独立bootstrap：`trial-F4` Project=`b9bd764296c74228b0e33c8b3e57f9fc1c246897a014740ec9830854b53bcd99`，Registry=`141400baf1d087d4a8a2c097187247200de0f9d4701f5475b2e55d69f92c4ac6`，Manifest rev5，无video/paid attempts、active budget null。新根只复制验证过的creative/Registry字节，不复制旧Manifest/尝试/付款状态；旧O2/F3仍在原root与全局七slot库存计数。F4参考01/11/12已预先native只读读取、全RGBA像素一致，0新上传。复制读图helper一处本地locator误写O3前缀，原proof保留，`F4-readback-local-locator-correction.json`以原proof SHA和实际returned byte SHA修正定位，未重取远程或改原证据。F4仍必须等O3六PASS与用户音频确认后才prepare/submit。

O3完整音轨解码RMS -28.963905 dBFS、peak -7.287077 dBFS，NaN/Inf为0。比较实际对白窗口：F2 7.5–11秒mean -18.8 dB/peak -1.9；O3 9–15秒mean -25.3/peak -7.6。Parent据此仅将最终P4的`native-O3END`设+5dB，其余native轨0dB，原内容不替换，预期该窗口peak仍约-2.6 dB；这是测量后的混音意图，不是已听完最终混音。证据`product-intercuts-55/dialogue-window-level-check.json`，实际render与用户整片听审仍待完成。

## Historical Completion Boundary Before Current Composite

独立concept reviewer识别的道具职责、笑点丢失、同事知识依据问题已在F2真实输入及F3/O3 authoring中处理；共保留旧三轮与本轮两次targeted检查历史，不新开第六轮。F3密度/实际效果不确定性现在被真实失败证据证实，不能因文字已补齐而关闭。

`continuity-repair-52/prepare_film.py`、`compose_film.py`、`render_film.py`只完成准备。新55秒edition需用唯一editorial Shot aliases与各自source trim，重复捕获同一exact source时去重媒体artifact、保留每份use receipt；同一MP4派生48k原声以显式P4轨匹配每个alias的source window。visual REPLACE不等于删除听到的原声，不能将静音visual误当成必须改用新音效/TTS的理由。计划中的native P4轨0dB/精确trim与5ms边缘淡化、结尾本地品牌VO、压低配乐、幻想提示仍须由exact新成片验证；尚未执行整片capture/compose/render。没有52/55秒成片，publication=`NOT_PUBLISHED`，model仍UNQUALIFIED，没有Production activation/P6/Final Acceptance。

Native子代理限定run-local authoring/postproduction或只读repair API定位；没有Provider代理、nested delegation或Git writer。Parent保留所有foreign dirty/index工作。HEAD仍`f5849ddff73ffffbc9ba74a6bdba8e55a43259ed`，index为空；本任务按film-first规则尚未运行完整工程套件或提交新制作修改，不把先前skill-integration Harness receipt冒充此次影片验收。

本记录按`record-ai-video-session`保存已知媒体结果与新的创意分歧；自动`distill-ai-video-learning`结果=`no_candidate`。这些不同动作/参考/时长的镜头没有隔离变量，尚无完整广告认可；未新增学习claim、修改Skill/Policy/Gate或全局memory，也没有为记录新增Provider、媒体、网络或额外测试。
