# Seedance AI Portrait Input Admission Audit

Date: 2026-10-13

Status: `advisory_research`

## Current Scope

下文原 PNG 的 `InputImageSensitiveContentDetected.PrivacyInformation` 是历史输入失败。
最新已授权 T2V attempt 已被接受后以 `OutputVideoSensitiveContentDetected.PolicyViolation`
终止，没有 MP4；实际状态见[当前实测记录](../record_for_agent/2026-10-13-canvas-two-shot-continuity-preflight.md)。
用户已经拒绝私域库开通；后文较早的入库建议保留为历史，不是当前必要步骤。
本轮补查社区 AI drama 制作法及官方素材契约，结论在末尾；没有授权或执行新一轮生成。

## Finding

本次《界蚀》HTTP400的公开错误码是`InputImageSensitiveContentDetected.PrivacyInformation`。
没有发现当前请求的endpoint/model/role/JSON/Base64构造错误；存在明确的接入准备缺口：
本地fictional identity/egress声明被用于inline提交，未取得Provider认可的受信素材身份。
此前只解释“AI图也可能被拦截”，没有查全自有虚拟人像入库路径，结论不完整。
应优先保留原人物、原图与写实风格，核验私域AIGC素材路线，不因拒绝而改画风或降低逐镜验收。
准入错误不证明PNG是真人，也不证明Harness或模型连续性已通过。

## Official And Community Sources

| Source | Verified Claim | Limit |
| --- | --- | --- |
| [方舟私域虚拟人像库指南](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview?lang=zh) | 自有虚拟人像可创建AIGC素材组、上传并审核；只有`Active`资产可用于推理，以`asset://<asset_ID>`引用。需高级创作权益；Assets API用AK/SK及IAM；素材与推理key的`ProjectName`须一致。 | 未核验当前账号权益、AK/SK或实际入库。没有查询价格、购买权益或调用Assets API。 |
| [方舟肖像素材指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh) | 同账号30天内指定Seedream 5.0文生图原始产物、Seedance原始视频及其返回尾帧可走信任产物路径；跨平台产物不在这条路径。另有预置虚拟人像、授权真人素材。 | 不是“所有AI图都可以直传”；也不是“自有跨平台AI图永远无法使用”，私域AIGC入库是另一条路线。 |
| [方舟Create Video API](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh) | 图片可用标准Base64或素材URI；2.0参考图1–9张、`reference_image`；Fast支持480p，2.0 duration4–15秒；显式原生声音字段。 | 格式支持不等于人像准入，不等于账号可调用或输出质量。 |
| [ArcReel Issue #2249](https://github.com/ArcReel/ArcReel/issues/2249) | 2026-08-31 reporter提供同错误码：AI生成的人像作为图片输入被拒，提出asset库接入需求。 | issue仍为enhancement/needs-info；triage回复注明AI生成。只使用reporter的拒绝事实，不能将建议或bot回复视为已验证修复。 |
| [ComfyUI官方Seedance节点源码](https://github.com/Comfy-Org/ComfyUI/blob/14c553159994b626738c392eb99d295ea3d683c1/comfy_api_nodes/nodes_bytedance.py) | image helper上传虚拟库、等待`Active`、返回`asset://`；first/last-frame及reference-image调用点实际使用该helper。 | 经ComfyAPI proxy，是其平台/账号的素材处理链；不能把proxy权限移植到我们的ARK_API_KEY，也没有执行该外部源码。 |
| [社区Seedream使用反馈](https://www.reddit.com/r/generativeAI/comments/1se1e69/anyone_else_getting_reference_images_rejected_in/) | 有用户报告AI写实参考被拦，也有用户报告在平台内先用Seedream生图再做视频。 | anecdotal、自报参数不完整且渠道不同；不外推为本账号、所有图或所有平台的成功保证。 |

别人能制作写实AI人物视频，可能使用已入库人物、受信模型原始产物、预置虚拟人像或不同平台包装的
素材处理链。仅看到成片无法判断其模型版本、时间、账号权益或实际传输，不能据展示片判定我们的准入条件。

## Exact Local Request Audit

当前源码snapshot为`cb79ef2a95052f614e63931075a4f090b886367c`。通过共享reader重开failed新attempt
`canvas-293bebb27dd2322c484e104df678ac97ff5bbd4f`及exact sealed request，重新核对execution binding。
纯重建请求并构造HTTPX request，未send、未lookup credential，Manifest仍revision29。

| Surface | Actual Value / Evidence |
| --- | --- |
| URL / method | `https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks` / POST |
| Settings | `doubao-seedance-2-0-fast-260128`、480p、16:9、duration15、generate_audio=true |
| Images | 两个`reference_image`，分别为`door-layout`和`linyan-reference`，均为`data:image/png;base64,...` |
| Decoded image | 两项均解码到原SHA `1a21ac10047cab19b441bfefd84ab91fef8de4b6787b7a5c558794903ff18b55`，941×1672、1,801,377 bytes |
| Body | 4,804,956 bytes；SHA `845b3a3cb825334e086a8a804acced5ea36f06546352cc796882fd14b052e2ad`，低于64 MB；HTTPX保持body原bytes |
| Prompt | 原950 UTF8 bytes，SHA `f0bea858c193c474299df4314f31f7d3b59054ba90807b9f7695753b01a51748` |
| Projection | `seedance_rejection.py`只读取server `error.code`的known literal，不根据图片或prompt自行分类 |

同PNG被两个职责引用有冗余，但没有找到官方SHA唯一性规则或重复图片导致PrivacyInformation的证据。
不得仅为“修复”在adapter去重、删除scene/identity职责或重写已批准prompt。
这份audit是当前exact request的deterministic reconstruction，不是当时network wire capture；
历史raw server body未保留，所以不能声称排除了所有可能的代码问题。

本机证据位于`runs/canvas-jieshi-two-shot-20261013-001/input-admission-audit/`：
`exact-request-audit.json`、`comfyui-reference-identity.json`、`kimi-receipt.json`、`kimi-report.json`、
`parent-adjudication.json`。ComfyUI pin `14c553159994b626738c392eb99d295ea3d683c1`的源码SHA为
`e277456ff9cc959c52ce05b440d4368cffef3e4e411f208b826b8fce2011c7da`；只下载文本作分析。

focused既有tests：active Ark receipt、hash/evidence mismatch、inline I2V/R2V、Fast nominal payload，
8 PASS / 117 deselected。受管Kimi只读调用`97b75bad-471d-4a89-9495-838549ef4fe6`为PARSED，
deep/k3/max/Docker、2 wire requests、124.010秒；report SHA
`8a39ad23f837be6cf62e88329596ae03fee681691010e1716bcb9327d829b416`已核验。
Parent用官方资料及actual decoder裁决：重复图强制去重建议无因果证据；唯一真人路径说法不适用于本虚构图。
不自动采用其patch建议，不将PARSED/离线tests当成Provider准入或视频质量验收。

## Existing Owner And Minimum Recovery

### Historical Counterexamples And No-Opening Decision

本节修正下面较早的“最小方向”：原 PNG 精确面貌若保持，入库仍是一个候选；
用户已拒绝开通，并批准首次文字选角的新面貌，所以入库不再是当前单元必要条件。
账号 `aigc_writable=false` 只证明当前虚拟库写入路径受阻，不证明全部 Seedance 调用受阻。

通过 canonical reader 重开并实际核对输入与输出文件，历史有两个不同反例：
`qingyan-seedance2-fast-dialogue-benefit-20260828-002` 用同一 Fast 2.0，仅发送无人物瓶图，
人物由文字生成；真实 MP4 SHA `309b919c00fc86bfd9540802c445a2fca2b1db36ebf44f87c94db3c14c65ff5b`。
`t8-h3-seedance-3shot-continuity-20260822-v7` 的 Mini I2V 实际接受 H3 生成的写实女性首帧，
输入 SHA `b49071d0cd7009d2880aedf5ad3c972e837d6dccfc451641478e1e301b076446`；
真实 MP4 SHA `24f4c0c307480ab1b44057b7ad7ca7782ee3eee1975404a28c28ba4e1a7f683f`。
后者被用户否决身份/摄影连续性；前者也没有完整 QA acceptance。
它们证明历史存在未入库生成，不保证本次 Fast 接受普通中间帧，也不构成连续性 PASS。

本次额外受管 Kimi audit invocation `8cfabf74-ace4-4810-bae9-ed5bfc304349` 为 PARSED；
报告 SHA `c5765d4de3b8069d99a4c73ca5347aacc1c792a87a9f29bff394280168f1d577`。
其“所给五例没有写实人物参考成功”只在所给 scope 内成立；Parent 找到上述 scope 外反例。
旧 local inline retirement 阻断结论已被当前 runtime 和两个实际 POST supersede。
详细 reader/input/hash 对比与 Parent 裁决保存在
`runs/canvas-jieshi-two-shot-20261013-001/historical-input-audit/`。

用户 A 已接受 `no-opening-preflight.md` 的换貌差异及最多两次新 submit，零重抽/repair，
50 CNY/次与100 CNY/单元为原预配置内部 upper bound，累计9保留、上限11。
授权不证明当前首镜生成、参考准入、后镜接续或最终声画结果；以下旧研究 checkpoint 保留。

`SeedanceAssetMaterializationReceipt -> SeedanceAssetReferenceResolver -> SeedanceVideoProvider`已有
exact source PNG/confirmation/Active identity绑定与`asset://`输出，不需要第二生成链。
它导入的是已实际入库的human-observed素材；没有自动CreateAssetGroup/CreateAsset owner。
`ARK_API_KEY`不替代Assets API的AK/SK权限；账号高级权益、素材ProjectName与入库结果目前NOT_EVALUATED。

最小方向是把原exact PNG入AIGC组，取得actual Active asset/确认，再通过原共享入口绑定已有resolver。
本次同图两个local aliases对应同一provider asset时还需核对既有resolver的唯一ID约束；可先在source/data owner
表达真实alias与职责，不伪造第二Provider资产或Active receipt，不宣称当前已prepare成功。
后镜仍只在新前镜MP4全PASS后提取approved实际状态；若该中间帧需要入库，按其自己的exact bytes办理，
不机械改为尾帧。官方受信尾帧路线只能在actual状态及原单元契约匹配时作为候选。

本轮无新增视频Provider POST/poll/fetch、无Assets调用/云发布/购买，无Production mutation。
项目POST实际2、历史7、累计9保留；当前剩余一次不能覆盖fresh A+B。
后续调用须保留历史并明确下一有限单元、exact inputs、上限与permit，不能把本次研究当作新执行许可。
两镜视频、MCP、状态绑定、声音/trim/HyperFrames、human完整听看及完整故事AC-7仍未完成。

## Community AI Drama Workflows

2026-10-13 用户追问“该怎么办，别人社区是怎么做这种 AI drama”。Parent 核对了实际
`no-opening-A-native-prompt.txt`：只有原创成年男子在地铁抬手机的描述，未见明确作品、明星或品牌引用。
这不足以诊断输出版权拦截的具体触发点，也不足以证明误判；没有被拒视频，删角色名或增加原创声明
都不能被宣称为已证实修复。前次零重抽边界保持。

| First-Hand Source | Reported Practice | Applicability Limit |
| --- | --- | --- |
| [12-minute film creator](https://www.reddit.com/r/Seedance_AI/comments/1w675bp/i_used_seedance_for_most_of_a_12minute_ai_film_a/) | 固定角色和场景参考；明确每份素材负责身份还是布景；同场景保持光线；复杂调度先做构图静帧；480p检查。 | 作者自报的动画长片经验，未独立复核成片、成功率、账号或请求。其多视图拼板技巧不应机械套用所有模式。 |
| [Chris & Saleem / Zapters creator](https://www.reddit.com/r/generativeAI/comments/1wo3r8j/my_ai_animation_workflow_cheaper_draft_takes/) | 角色/场景资产复用，短剧情段分镜，多take挑选，前片或filmstrip提供接续参考，保留好镜头、替换坏镜头，最后处理声线与剪辑。 | 作者披露自有工具，属于商业一手经验；评论区自动bot的“二次重抽法”等不采纳为实测证据。filmstrip不证明方舟人脸准入。 |
| [Dreamina creator rejection report](https://www.reddit.com/r/Seedance_AI/comments/1sfp3ag/seedance_20_is_becoming_unusable_for_filmmaking/) | 作者报告AI人物以及从前片抽出的尾帧仍被拒。 | 不同时间/产品，不能归因本次Fast任务，也不能证明我们需要购买权益。 |
| [Copyright rejection discussion](https://www.reddit.com/r/Seedance_AI/comments/1vk47ts/sudden_copyright_problems/) | 有用户自报原创参考遭版权提示；涉及不同平台/模型。 | 原帖/回复有平台营销、法律猜测及已知IP案例；不能合并成统一误判率，更不能把“uncensored”广告当作解决方案。 |

可采用的制作结构是：剧本与镜头表 → 固定角色/场景/道具资产 → 每镜构图与动作设计 →
逐镜生成/验收 → 实际状态交接 → 剪辑/声音。社区的多take与换模型属于其自身预算与取舍，
不扩充我们的零重抽授权。一般短剧可用短镜头组织节奏，当前各15秒nominal契约没有因此改变。
声音有原生联合生成与后期表演/配音两条做法；本单元保持原生声音，后配音不能冒充原生音频验收。

[Runway References官方文档](https://help.runwayml.com/hc/en-us/articles/40042718905875-Creating-with-Gen-4-Image-References)
说明角色/场景参考先用于一致静帧；[Act-Two对话示例](https://help.runwayml.com/hc/en-us/articles/41748090660499-Creating-Multi-Character-Dialogues-with-Act-Two)
再组织场景运动、表演和合成。这支持资产与镜头分阶段的工作法，不证明当前repo已支持该后端或原生音频组合。

## Official Input Paths And Current Contract Gap

[Seedance 2.0提示词指南](https://docs.volcengine.com/docs/ark/seedance-2-0-prompt-guide?lang=zh)
区分素材参考、视频编辑、视频延长，要求明确各素材职责。它建议人物参考优先单人独立图，
提醒多视图可能导致人物重复，并承认多次续写会积累画质退化。
因此不能把“加更多参考/一直续写/不断重抽”当作稳定制作法。

[方舟肖像素材指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh)
列出的受信路径为同账号、同方舟平台、30天内指定模型的原始产物：Seedream5文生图，
Seedance原始视频及模型返回尾帧。编辑、压缩或转发可能破坏受信资格，输出仍经过审核。
用户拒绝私域库开通并不排除这些公开路径；但模型可用性、素材实际来源和适配器支持仍须逐项核验。

关键缺口：**任意本地提取的中间PNG没有被列入官方受信集合**。
“新A成功 → 中间帧自动能提交B”没有充分依据。历史Mini接受H3首帧仅是旧个案。
身份参考解决外貌；实际中间状态还必须表达持物、动作相位、人物与门的相对位置、运动方向、摄影及声音。
二者职责不能互相替代。首镜普通中间帧、Provider尾帧与原始视频是三种不同输入契约。

## Recommended Next Candidate

优先准备资产先行、逐镜验收的项目数据方案，复用既有Harness与renderer。
若继续Seedance且不开私域库，先核对同账号指定Seedream原始角色/场景图的可用路径，
生成A并验收后，保留原始MP4及Provider返回素材的精确身份。
后镜使用原始视频作状态参考、或在真实接点恰为片尾时使用Provider尾帧，是有官方依据的候选。
这需要新的exact输入、能力/素材准入核验及有限授权；目前没有可直接执行的封存新单元。

**原始视频参考不等价于已经批准的“仅用普通中间状态帧”输入；不能静默替换并声称原测试通过。**
若普通中间PNG是本轮不可变条件，应先为该exact输入找到并核验允许它的现有Provider路径；
不能以共享角色图、模拟状态图、尾帧或整段参考冒充该要求。目前尚未取得这样的当前准入证明。
无论选哪种，仍按A全PASS → approved实际state → B输入绑定 → B自身MCP全PASS →
canonical trim/native audio/接点 → HyperFrames → 正常速度完整听看执行。

本轮建议不把现有错误码解释为确定的prompt问题，不为碰碰运气再投原T2V请求。
下一实测问题应是“所选合规素材链能否保留要求的接点状态并被后镜实际消费”，
前提为exact source/mode可用、新有限单元和输入差异已明确；本研究不提供这些条件已满足的证明。

## Independent Evidence Check

受管 Kimi invocation `92a648cd-f139-436e-9481-51c157ebf5fa`，sealed deep/k3/max/Docker，
2 wire requests、70.977秒、PARSED；report SHA
`3b02f9c911117c51ea794d54ed876bf891d3c830707362e2ceea6552555959a8`已核验。
只读parent封存的来源摘要、exact prompt和STOP证据，未独立联网；primary网页由Parent直接核验。
Parent裁决：F1输出侧审核分类有证据，但“不是workflow缺陷”不足以排除整个制作方案的问题；
F2中间帧不在官方列举集合是证据缺口，不能说官方明确禁止一切中间帧，更不能强制改成尾帧；
F3当前未授权重抽成立，所谓后镜“永久blocked”不成立，未来仍可由新明确单元解除。
不采纳其再次提交同一prompt的建议，当前没有能提高成功率的可归因修复依据。
receipt/report/Parent裁决位于`runs/canvas-jieshi-two-shot-20261013-001/community-research/`。
