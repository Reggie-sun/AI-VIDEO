# Seedance AI Portrait Input Admission Audit

Date: 2026-10-13
Last updated: 2026-10-16 (official sources and authenticated web observation)

Status: `advisory_research`

## Latest Correction — Free Entry And Account Eligibility — 2026-10-16

**Free-entry follow-up:** 用户选择继续找免费Seedance入口后，当前即梦免费版账号实际检查Mini、2.5样片与2.5，均出现各自“升级以使用”提示。官方新用户任务提供3次Mini限免是有条件活动，未证实属于本账号；40赠送积分不作为这些新模型可用次数。字节官方列豆包App的Seedance2.0入口，但当前豆包网页未登录且未显示视频功能，App免费次数/图片输入待用户核对。详见[当前免费候选矩阵](../record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md#free-seedance-alternatives-and-account-specific-readiness--2026-10-16)。没有新生成或上传，未购买/充值，原图和Fast网页草稿保持；没有证明免费路线已可执行，也不由本账号阻断推出所有平台都必须付费。

**Current account update:** 用户保留个人账号并选择核对即梦个人网页，随后已完成登录。当前`积分详情`实测40赠送积分（订阅0/充值0，本次“每日免费积分 +40”）；同一原PNG已正常选入首帧，local blob的SHA/size/dimensions与canonical完全相同。但`Seedance 2.0 Fast VIP`生成按钮悬停明确“此功能为VIP专属”；网页可选4s，分辨率菜单仅720P，未观察到原生音频的独立证明。未点击生成、购买或充值，素材服务端审核仍`NOT_EVALUATED`。见[登录后实测](../record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md#authenticated-jimeng-credits-exact-frame-selection-and-vip-boundary--2026-10-16)；此前[未登录观察](../record_for_agent/2026-10-13-jieshi-original-s01-s02-candidate.md#jimeng-personal-web-readiness-and-login-boundary--2026-10-16)、免费Entry企业条件及Ark单次输入拒绝保留，网页免费积分不推用于Ark或VIP资格。此选择仅核验路线，不授权新生成或付费。

上一轮将“本账号尚无已证明可用的免费准入”归纳成当前仅能咨询，遗漏了应具体核对的免费Entry。
这不是新上线能力：[官方权益表](https://docs.volcengine.com/docs/ark/seedance-2-0-purchase-guide?lang=zh)（页面更新2026-08-13，本轮重新打开）明确列出免费`高级创作权益（Entry）`，支持虚拟人像素材入库、控制台及Assets API，50素材/50组、CreateAsset最大3QPM。基础免费档与Entry不同，前者的虚拟人像入库列为不支持。高级权益不等于必须购买付费套餐。

该页同时要求企业实名认证、合规风险评测、协议及手机号安全校验。沿[免费权益入口](https://console.volcengine.com/ark/region:cn-beijing/openManagement?LLM=%7B%7D&advancedActiveKey=mediaAsset)核对；不以网页存在、API key存在或50个quota推定本账号已具备AIGC写权限，不代签协议/身份、购买、充值或擅自开通。

此前已有[本账号实测记录](../record_for_agent/2026-10-13-canvas-two-shot-continuity-preflight.md#current-account-entitlement-blocker--2026-10-13)及`runs/canvas-jieshi-two-shot-20261013-001/asset-entitlement-check-20261013.json`：观察时间为2026-10-12T20:21:11.115298+00:00，AIGC readable=true/writable=false、免费Entry未开通，按钮因仅限企业账号而disabled。该历史证据已知道免费档，不能解释成欠费或需要付费订阅；重新读到不等于当前权限刷新。核对Entry时Chrome MCP因既有profile占用未取得控制台新页面；后续即梦核验使用独立浏览器，没有停止其他浏览器、读取cookie或代做认证。用户随后确认仍是个人账号；live console权限与quota保持`NOT_EVALUATED`。

正规候选为：保留当前`13c83ce4…76923`整张PNG → 企业资格与免费Entry就绪 → 虚拟人像入库并实际审核 → human-observed `Active`与exact来源确认 → 既有`SeedanceAssetMaterializationReceipt / SeedanceAssetReferenceResolver` → 原Canvas生成链。共享loader重开Manifest45/Project10及exact PNG成功；尚无Provider asset ID、Active receipt或新生成请求。是否接受“本人加七个倒影”的整张图仍未证，不能把免费权益代签素材审核。

社区确有外部AI图经其他Seedance入口生成的自报案例：[GPT Image 2分镜→Dreamina/CapCut Omni Reference](https://www.reddit.com/r/Seedance_AI/comments/1stq5q7/gpts_images2_seedance20_is_the_best_workflow/)是动画式多格分镜，不能代当前写实首帧；[Seedance2.5写实参考测试](https://www.reddit.com/r/Seedance_AI/comments/1wg61g5/seedance_25_accepts_a_photoreal_reference_face/)自报5次仅1次接受，非稳定准入或本账号证明。没有证据支持“创作者都购买人物库”，也不把生成用量订阅等同人物库订阅。不采用遮脸、叠网格或更换角色的审核规避建议，不自动换平台或扩大次数。

用户最新限定只用Seedance，已停止METASO/H3方向；没有读取所指`.env`或新credential lookup。免费入库与后续视频生成授权/计费分开，旧原S01 POST1与S02剩余次数不重置/互挪。当前恢复候选与官方观察保存在`runs/canvas-jieshi-original-s01-s02-20261013-001/seedance-free-entry-20261016-001/`，仅advisory准备，无上传、模型调用或Production写入。下文“免费路径未证实”仍描述当前exact图未实际准入的边界，但不能再省略已明确存在的免费Entry及具体账号条件。

个人账号下的候选仍须明确改变哪个输入面：保留当前图，可先核对即梦/Dreamina个人网页的正常参考上传、实际审核与已有额度；其[官方制作说明](https://dreamina.capcut.com/resource/about-dreamina-terms-of-service)展示静帧到Seedance的制作能力，不证明当前账号/这张跨平台多人图可用。保持现有方舟API，则官方受信原产物路线要求另有合格Seedream原始首帧，不能把当前Codex图改标签；重新制作会改变图片身份，不自动授权，也不是免费复用。若现图和API都不变，只能保留现有证据向官方核实，不能以换输入格式或模型版本保证放行。以上均不是新Provider默认选路；不降版、删除动作/声音或新增调用来碰运气。

## Current Scope

2026-10-16 当前原图 S01 attempt 使用 `doubao-seedance-2-0-fast-260128`，4 秒请求以 HTTP 400
`InputImageSensitiveContentDetected.PrivacyInformation` 在 submit 阶段被拒。精确输入 SHA-256 为
`13c83ce47482f81da436d6b1d43e3b49a09b09f93250c6f10e647eafb8776923`；记录显示 1 次 POST、无任务/MP4、S02 未提交、无 retry。
本次累计 POST 计数为 12（历史 11 + 本次 1），没有查询或推断账单。见[实际拒绝审计](../../runs/canvas-jieshi-original-s01-s02-20261013-001/original-S01-live-20261016-001/actual-rejection-audit.json)
与[停止状态](../../runs/canvas-jieshi-original-s01-s02-20261013-001/original-S01-live-20261016-001/final-stop-state.json)。
项目记录将该 exact frame 保持为原始整张首帧；静态首帧 authoring 检查为 `PASS`，人类成片验收为 `NOT_EVALUATED`。
当前 SHA 的来源已由 native Codex generation record 确认；它不是官方列明的 Seedream 5.0 文生图或 Seedance 原始视频/尾帧产物。
方舟[错误码目录](https://docs.volcengine.com/docs/ark/error-codes?lang=en) 将该 code 解释为输入图像可能含真人。
这表示平台作出了“可能含真人”的判断，不证明图中实际有真人；也没有指出具体哪张脸、倒影、文字或其他局部触发。
“没有命中受信人像来源路径”仍是结合素材政策和同类报告得出的可能解释，不是分类器根因证明。

较早的原 PNG 拒绝、T2V 输出侧 `OutputVideoSensitiveContentDetected.PolicyViolation` 与私域库建议都保留为历史，不覆盖本次当前状态。
用户于 2026-10-16 明确要求“别找那种付费的途径”并保留当前原图；这使下文较早的“开通私域库”及“新生成 Seedream 原图”建议不再是当前恢复方案。
本轮研究没有新图生成、素材上传、新增视频 submit/重试、购买/开通或对外工单；上文记录的单次 S01 POST 保持为当前既有 attempt。

## Finding

本次《界蚀》HTTP400的公开错误码是`InputImageSensitiveContentDetected.PrivacyInformation`；官方释义为平台判输入图像可能含真人。
当前 original S01 有实际 submit-wire observation，并将 wire body 与解码图像 SHA 绑定到这次拒绝；此分类不证明 PNG 是真人，也没有定位某张脸、倒影、工牌/OCR 或其他局部。
“当前写实人像没有命中受信输入来源”与官方信任规则和同类社区报告相符，但仍只是解释该失败的工作假设。
没有证据表明改 prompt、裁切、重绘或换渠道会解决问题。
首帧静态质量与 Provider 准入是两个独立 verdict；拒绝不使静态 authoring `PASS` 自动变成失败，也不证明视频连续性或成片验收。

## Official And Community Sources

| Source | Verified Claim | Limit |
| --- | --- | --- |
| [方舟私域虚拟人像素材指南](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview?lang=zh) | 单个 Asset 是一个图像/视频/音频文件；AIGC 组可管理自有虚拟形象。图像须为虚拟人像，合法拥有且不得与自然人形象雷同；审核后仅 `Active` 可推理。文档要求开通“高级创作权益包”，Assets API 用 AK/SK / IAM，素材与推理项目须一致。 | API 层面可上传一个图像文件，不代表当前含林砚与七个倒影的完整场景会被归类或审核为合格虚拟人像。AIGC 指南没有在已核验内容中明确禁止多人脸；真人库的多人脸规则不能移植到 AIGC 库。账号是否已有该权益、或可否无新增付费使用，均未知；按最新约束不购买、不申请开通、不调用。 |
| [方舟肖像素材指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh) | 同账号30天内指定Seedream 5.0文生图原始产物、Seedance原始视频及其返回尾帧可走信任产物路径；跨平台产物不在这条路径。另有预置虚拟人像、授权真人素材。 | 不是“所有AI图都可以直传”；也不是“自有跨平台AI图永远无法使用”，私域AIGC入库是另一条路线。 |
| [方舟错误码目录](https://docs.volcengine.com/docs/ark/error-codes?lang=en) | `InputImageSensitiveContentDetected.PrivacyInformation` 的官方解释为 “The request failed because the input image may contain real person.” | “may”是平台判定，不证明真人身份或具体触发局部；本次 request 的 error body 没有额外标签定位原因。 |
| [方舟创建视频任务 API](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh) | `content.image_url.url` 接受 `asset://<ASSET_ID>`；同一 image object 对 `role` 定义了 `first_frame`、`last_frame`、`reference_image`，故 asset-backed image + `first_frame` 的字段组合有 API schema 依据。 | 私域 AIGC 专属示例只演示 `reference_image`；schema 不证明当前图像内容能入库、能通过输入审核，亦不证明当前账号可用。格式支持不等于人像准入或账号授权。 |
| [ArcReel Issue #2249](https://github.com/ArcReel/ArcReel/issues/2249) | 2026-08-31 reporter 自述 AI 生成的人像作为首帧/参考图片被同一错误码拒绝，并请求素材库支持。 | issue 为 `enhancement` / `needs-info`；后续详细根因与替代方案标记为 AI triage 内容，不是官方答复或成功修复。仅作为相似失败报告。 |
| [Brut 的 Seedream/Seedance 实测说明](https://getbrut.app/docs/providers/seedream.html) | 该工具作者自述真实请求中，Seedream 文生图原图（含多视图角色表）及 Seedance 片段帧被接受；Seedream 编辑图、裁图和其他来源的肖像被拒。 | 商业工具的一手自报，没有随附可独立核对的请求/receipt；多视图角色表不等于当前多人场景。其“resize/re-export 保持信任”与方舟官方对压缩/转发可能丢失信任的警告不同，不据此指导重编码当前原图。 |
| [ComfyUI官方Seedance节点源码](https://github.com/Comfy-Org/ComfyUI/blob/14c553159994b626738c392eb99d295ea3d683c1/comfy_api_nodes/nodes_bytedance.py) | image helper上传虚拟库、等待`Active`、返回`asset://`；first/last-frame及reference-image调用点实际使用该helper。 | 经ComfyAPI proxy，是其平台/账号的素材处理链；不能把proxy权限移植到我们的ARK_API_KEY，也没有执行该外部源码。 |
| [社区Seedream使用反馈](https://www.reddit.com/r/generativeAI/comments/1se1e69/anyone_else_getting_reference_images_rejected_in/) | 有用户报告AI写实参考被拦，也有用户报告在平台内先用Seedream生图再做视频。 | anecdotal、自报参数不完整且渠道不同；不外推为本账号、所有图或所有平台的成功保证。 |

别人能制作写实AI人物视频，可能使用已入库人物、受信模型原始产物、预置虚拟人像或不同平台包装的
素材处理链。仅看到成片无法判断其模型版本、时间、账号权益或实际传输，不能据展示片判定我们的准入条件。

## Historical Exact Local Request Reconstruction

本节记录较早的 two-shot 简化 attempt，不是 2026-10-16 当前 original S01 attempt。下述 deterministic reconstruction / no-wire-capture 限制仅适用于这个历史请求；当前 original S01 有独立的实际 submit-wire observation。

该历史源码snapshot为`cb79ef2a95052f614e63931075a4f090b886367c`。通过共享reader重开failed attempt
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
这份历史 audit 是该 attempt 的 deterministic reconstruction，不是当时 network wire capture；
其 raw server body 未保留，因而不能用来判断当前 original S01 的请求绑定或失败原因。

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

**2026-10-16 无付费 supersession。** AIGC 私域库官方指南明确要求高级创作权益包；当前没有证据证明本账号已具备可零新增付费使用的权益。
因此既有的私域入库候选现仅作历史记录，当前不得购买、开通、上传或以“免费 Entry”名义推定可用；本轮未查询购买页或价格。
官方可信原始产物路线仅能复用已经存在、仍在 30 天有效期内、且字节确认为同一 Ark 账号指定模型原始产物的输入；不建议新跑 Seedream 文生图，也不把 Seedance 视频 submit 说成免费。
当前 SHA 已知来自 native Codex generation，不符合官方指定 Seedream / Seedance 受信原始产物来源，因此当前图不能走这条已公开路径。保留当前图的免费放行方式未证实；可整理已知错误码、模型、wire observation 与 decoded SHA 供用户自行向官方询问原因，但不承诺免费白名单或豁免，也不代发。

对于当前整张首帧，资产 API 允许单文件 Image、视频 API 字段允许 `asset://` 与 `first_frame` 的 schema 组合；但素材内容必须属于合格虚拟人像并通过审核。
该图有一名主体及七个倒影，私域虚拟人像文档未证明此场景可作为一个 AIGC portrait Asset 通过审核；能否入库及之后是否免于人像输入拦截均为 `UNKNOWN`。
真人素材库明确的多人脸限制绑定真人认证/真人组，不足以推出 AIGC 库也必拒；不得反向宣称它一定可入库。

关键缺口：**任意本地提取的中间PNG没有被列入官方受信集合**。
“新A成功 → 中间帧自动能提交B”没有充分依据。历史Mini接受H3首帧仅是旧个案。
身份参考解决外貌；实际中间状态还必须表达持物、动作相位、人物与门的相对位置、运动方向、摄影及声音。
二者职责不能互相替代。首镜普通中间帧、Provider尾帧与原始视频是三种不同输入契约。

## Former Recommendation — Superseded 2026-10-16

以下是此前允许付费权益研究时提出的候选方向，现为历史，不是本次执行建议。用户已要求不找付费途径并保留当前原图，因此不再推荐开通私域库、生成新的 Seedream 人像、裁切/重绘当前图或换用可能收费的 Provider。
尚未证实有保留当前图的免费放行路径；可整理已知证据供用户自行向官方核验解释，不承诺免费白名单或豁免，也不代发。AIGC 入库审核与账号是否有可无新增付费使用的权益仍为 `UNKNOWN`。

### Historical Candidate Text

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
