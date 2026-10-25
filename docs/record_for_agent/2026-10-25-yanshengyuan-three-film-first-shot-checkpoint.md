---
record_kind: recovery_incident
topic_id: yanshengyuan-three-film-seedance20
learning_eligibility: eligible
evidence_index_version: "1"
---

# Yanshengyuan Three-Film Media Checkpoint

Date: 2026-10-25 (Asia/Hong_Kong)

## Current User Motion And Hook Rejection — 2026-10-26

用户否定当前15秒合片（SHA `0a5047f3f5446957deb30d87f09f7774c29ca4a5d240a05b083e9b5e503eb08b`），
补充指出8秒后两只动物像固定在屏幕上、不随人物移动，前三秒钩子弱，要求“浮夸”。此前对应
S02 raw的静帧space-camera PASS不覆盖该动态附着要求，不能据此放行后镜；旧技术测量与7秒
开场的人审各保留其原范围，不扩展为当前合片认可。设计要求及Skill修订见
[Ad Creative User Requirements](2026-10-26-ad-creative-user-design-requirements.md)。没有重生或重试媒体。

## Narrative Rejection — 2026-10-26

用户对前20秒exact副本 `3590a61eaf225efef05efae4366d60f751171984d893f6f8e4fc4fc44b42749c` 明确反馈：“这个故事不对,因果没有,灵盖之后就是一个警报?然后就介绍产品太牵强了”。当前叙事人审为 **FAIL**；下方空间/技术检查及旧Gate保留其原证明范围，不能代替剧情认可。反馈封存在 `single-a-rework-001/creative/user-review-story-rejection-001.json`。后续生成暂停，先讨论人物目标、产品介入动机和结尾兑现，新剧情方向未获确认；本轮没有新增Provider/媒体/音义调用，不推断声音通过，也不重试旧UNKNOWN。学习评估仍为 `no_candidate`：单次整体叙事反馈不能作为跨实验因果规律或自动修改Skill/Policy/Gate的证据。

## Single-Film Opening Repair Checkpoint — 2026-10-26

本节取代下文“三片同时继续/保留A原开头”的当前执行方向，历史计数、原sealed intent、FAIL/UNKNOWN和早先人审范围全部保留。用户反馈“我看了下这三个都有不足的地方.我们先做好一个”“第一个人物所处的环境没有交待清楚看的莫名其妙”；Parent按首条A「全城戒备」集中处理，B/C停止新提交。新稿目标44秒（A01/A02/A03/A04各10秒+真实产品落版4秒），仍满足40–60秒、产品3秒内可见、完整商品名、功效与“栖澜百货商贸”缓慢动态水印；这不是已完成/已验收影片。

### Exact Opening And Observation

新运行边界为 `single-a-rework-001/`。Parent实际调用一次 builtin imagegen，以旧A01真实末帧与商品PNG为参考，生成有左窗城市、窗边梳妆台、右后床/暖灯的卧室宽景；原图941×1672 SHA `8e26f0eaf86470090fcb46be0c5fc0adbbf7a0f753d7d3b3d190cba6f4dc55ab`。首尾帧严格尺寸校验要求相同像素；Parent显式将完整构图技术归一化为720×1280，不裁切、不改原图，派生PNG SHA `e0dced7b66219ab1b3d9a836cf214f54b354d1f7a0984949ba4da69439d71f5b`。r1/r2 endpoint manifests保留来源与派生操作，实际使用r2；尾帧为旧A01实际frame239的720×1280 PNG `ff86fc80413b02afe569f9ee5b5c60f82ccf5b472b8ae59cff532427a421968c`，不冒称新片已执行。

新A01经canonical Registry/Project/committer、router/compiler、exact native preflight和one-use paid submit/fetch，目标Jimeng `seedance_2.0_vip` / FLF /10s/720p9:16/native audio。native prompt3626/4000 UTF16，request `6caeaa6136dc9c47b8cfa4bb6d0501325b18cdc918c9a342f26d7de34fb21ff2`；新node `node_dd6k2ey6d1` 与旧媒体节点分开。实际新MP4 SHA `ccc6b91626b82ad75e6404ba6745adca049d977a1e519ae9ef8e5056a6035336`，21772424bytes；fetch UTC `2026-10-25T17:14:56.044990Z`。Provider成功仍为UNQUALIFIED，没有activation或Final Acceptance。

Parent显式调用project-local video-analysis，逐一实看21帧（0–10s、0.5s），观测与Gate在 `single-a-rework-001/source-acceptance/A01/`。0–3s卧室床/灯、左窗城市、台面及产品清楚；2–2.5s楼顶红灯亮、3s后看左窗；5.5–8s可见说话嘴部变化，9.5–10s瓶底落桌并保持左看末态。Gate为NOT_EVALUATED：空间/identity/truth采样PASS；精确旋松半圈与盖声因果、完整原速表演/唇音及声音缺可靠证据。Whisper只提供有同音字错误的近似文本与不可靠0–2s时间，不能签声音PASS。本轮没有音义Provider请求、没有重试旧UNKNOWN。约5s后源片左上AI披露发生重复重叠，另交P4做可见单一披露整理；不把源片判为无缺陷。

### Product Close-Up Recut And Local Delivery

旧A02原on-screen/lip-sync FAIL继续保留；新剪辑用途为产品/手部近景配原女声画外音，不宣称补做了原口播。`single-a-rework-001/post/render-r13/` 经P4 CompositionSpec→ResolvedTimeline→HyperFrames实际渲染10秒候选，SHA `f30bed309de7a06f08295f9640d6538bea262e2f9085ea285f8e0506ceb507ef`，1080×1920、24fps/240帧。画面连续源区间0–84、84–132、132–240帧，原声单条0–480000/48k samples，不在画面切点拆分；慢水印取44秒全片路径的10–20秒切片。r1–r11失败制备/路径/font checkpoints均保留，无Provider作用；r12实际渲染后发现末段瓶标签贴左边，修正为r13。

Parent另显式video-analysis并查看全片接触表/MCP关键帧：嘴部出画，取滴管/滴液/推开完整。瓶身第一段完整可见，约4–5s贴左边、末段瓶底出画；这是手部质地近景的实际取景限制，不宣称全程整瓶完整。AI披露与商户慢水印可见。音频技术对照 `audio-fidelity-check.json` 显示原声0–10s与候选均480000 mono samples，对齐差1024 samples、相关性0.9999015051；这仅证明保留区间的技术忠实性，不证明实际听感或声音语义。人类审片仍NOT_EVALUATED。

用户目录 `/home/reggie/电商/颜生源/广告试片/2026-10-26-A单条打磨/` 已放 `01-卧室开场参考.png` 与 `02-手部产品近景-原声旁白-10秒待审.mp4`，逐一核对复制前后hash相同。新A01+A02前20秒诊断合片已通过P4/HyperFrames实际渲染并交到同一用户目录：`00-A全城戒备-卧室开场与功效衔接-前20秒待审.mp4`，SHA `3590a61eaf225efef05efae4366d60f751171984d893f6f8e4fc4fc44b42749c`，24850208bytes，1080×1920、24fps/480帧、20.000s、48k stereo AAC；不是44秒完成片，A03/A04没有新提交。receipt为 `single-a-rework-001/post/review-20s/r7/delivery.json`，render report SHA `15832e2998a4fe97c6f64a4d5d4f9893e72ed4bc387b2aa2d5fa352a60ee76e1`，lint/check均0 errors/0 warnings。

Parent再次显式video-analysis（40帧/0.5s），实看开场、AI标识与9.5/10/10.5s等切点及末段：卧室宽景保留，10s切到瓶/手近景，单一清楚AI披露覆盖旧重复轮廓，商户水印沿0–20s全局慢轨迹连续。两段各原声0–10s在P4时间线各480000 samples连续排列；原源PCM串联与20s副本的对齐相关性0.9998451091、全局AAC对齐差1024 samples，技术上无拆词复用/意外重叠的时间线。此不签声音语义、原速自然度或人类听审，相关Gate仍NE/旧FAIL，`full_film_complete=false`、`next_shot_submit_authorized=false`、`NOT_PUBLISHED`。

合片制备中已查实旧r13 repair-input receipts绑定旧target project snapshot，不能直接复制到新Project；在新20s项目用原A02 source和相同trim/transform沿canonical owner重新制备，保留失败r1–r5与实际r6。r6覆盖层仍露源badge一小段，r7只扩大AI披露backplate并实际重渲染核验。没有为此修改共享代码或重新生成视频。

### Preserved Bounds And Implementation Limits

Parent新90分钟窗口 `single-a-rework-001/operator-window-renewal.json` SHA `5e1698d5e91e5e6fee67296b3ec019d9d7af4eb270fb8a03cca207ecfde1b160`，真实issued16:46:29.850582UTC、expires18:16:29.850582UTC；保留task18次、6次/片、单次500/每片3000/task9000 CRD内部upper bound，不是市场价。续期时真实video submits9，A/B/C各3；本次唯一新A01 submit后task10、A4/B3/C3；加task前9次为累计19。实际扣点/金额待核账，builtin imagegen实际费用亦待确认，不以upper bound估账。

单镜runtime仅task-local新helper；Parent实审并要求修正budget创建后poll自拒、trial budget错误使用task9000而非film3000、已有attempt时不再重造candidate等问题，修后实际start/submit/poll/fetch成功。旧首轮空authoring因过长prompt(4312/4000)完整归档至 `runtime/A/runtime-authoring-incomplete-001/`，24文件逐项hash/size复核，0 generation/paid/no budget；不覆盖/清理/重计付费历史。新作者精简重复字段并同步coverage起止文本/hash，Director v4/goal binding/rich intent局部验证通过。notes→goal→coverage单向identity，未给goal添加反向notes hash造成循环。未做共享src扩展或全工程验证。

只读音义根因追踪进一步确认：A02 resume已启动固定venv并进入MCP transport；consume后transport.post异常映射UNKNOWN，未封存异常类别/阶段/HTTP status，不能判定请求到达Provider，更不能确定DNS/TLS/timeout等具体根因。旧UNKNOWN永久保留，不将先前gzip条件修复当作这次原因或服务恢复。此为只读结论，本轮无音义请求/凭据值读取/重试。

旧共享源码/文档dirty/index均保留；本轮媒体与task-local脚本在ignored run内。依film-first，未把工程验证/commit/push提前到用户效果认可之前。当前仍未发布/投放，下一步只做前20秒诊断审片与同bytes人类反馈，所有required findings PASS前停止后镜提交。自动学习评估 `no_candidate`：本轮同时改构图、参考与叙事表达，剪辑派生不增加独立实验计数；没有隔离变量或足够跨实验支持，不升级Skill/Policy/Gate。

## Benefit Continuation Checkpoint — 2026-10-25

本节保留2026-10-25三片续镜阶段历史；当前执行方向见上节Single-Film Opening Repair Checkpoint，后续首镜段落与计数亦为历史快照。用户已批准将功效写进三片后续剧情，保留已认可首镜；新稿位于主run的 `benefit-continuation/creative/`，三条目标仍为40–60s、当前54s设计。主卖点为“淡斑焕亮、匀净肤色”，有商品与质地/使用动作，不使用报告数字、见效期限或把30ml报告外推到15ml。

### Current Media And Barrier

A02/B02/C02 均已通过 selected Jimeng `seedance_2.0_vip`、10s、720p、9:16、first-frame + native audio 的 canonical prepare/start/submit/poll/fetch。实际输入为对应已获人审首镜的 raw frame239；从真实CFR审片末帧比对并以标准 video-frame binding 导入，不按 r_frame_rate=60 换算。各原request与fetch仍为 qualification/UNQUALIFIED，不是Production activation。

| Shot | Exact new MP4 SHA-256 | Original-intent Gate | Finding |
| --- | --- | --- | --- |
| A02 | `5d47d40b63b23c9d121e5b3399b4826966913fd5fbfff73376902452e35abc34` | FAIL | 滴液与推开、产品前景完成；采样见嘴部闭合/微笑而原声含完整台词，未满足原on-screen/lip-sync意图。已问用户是否采用产品/手部特写配原声旁白，尚无新反馈。 |
| B02 | `18fbc0ebac2b396c52aec5451c4fb79b3777115a57a244228a3fa26cf4173aa4` | NOT_EVALUATED | 四人、护瓶展示与单向摇镜可辨，女主嘴部自然变化；声音与完整声画同步待实际看听。 |
| C02 | `7242c94cbc46fc3f09b82d84f5bf6e3ed2b319d627a00f5d516e010257619cfb` | FAIL | 约1–4.5s巨瓶连人腾空、5–5.5s落岩柱，偏离原持续grounded/仅摄影机升高意图；双手抓盖保持。 |

Parent 对A/B、独立native reviewer对C显式调用project-local `video-analysis`，各21帧/0.5s实际查看。Gate与观测在 `benefit-continuation/source-acceptance/{A02,B02,C02}/`；原request intent不回写。后镜source/predecessor共享同一Gate路径。实际调用executor `_prior_gate` 对A03/B03/C03均拒绝，三片均没有提交Shot03。B/C音义unit均未创建。

### Local Review Files

三条10s审片片段已经P4 `CompositionSpec → ResolvedTimeline → HyperFrames`，1080×1920、24fps/240帧，原声选0–10s、1x。基于本地转写的末句结束A9.72s、B7.72s、C9.56s与尾部测量，Parent明确允许剪无词尾音，不把保留每个AAC padding sample当作完整对白。无拉速、无为凑时长补freeze。水印“栖澜百货商贸”取全54s路径的10–20s切片，未把全路径压进10s。

用户目录：`/home/reggie/电商/颜生源/广告试片/2026-10-25-三条夸张剧情/功效续镜待审/`。文件分别为 `01-A02-全城戒备-功效续镜-10秒慢水印-待审.mp4`、`02-B02-三界抢瓶-功效续镜-10秒慢水印-待审.mp4`、`03-C02-巨瓶峡谷-功效续镜-10秒慢水印-待审.mp4`。

源/渲染/用户副本映射、各SHA及音轨技术对照在 `benefit-continuation/post/review-02-delivery.json`，SHA `79e16ca1cc878ab9a8b6f8b52c5e4a06e2deb251c61d3483b4ce0ca774490667`。三条源0–10s与P4副本的对齐音频相关性均>0.9997，解码对齐差1024个48k样本；这只证保留区间的技术忠实性，不签听感、发音、唇音或人工验收。Parent查看A0/9秒及B/C9秒实际输出，水印名正确、低存在感，原声实际看听仍待用户。

### Audio Outcome And Safe Recovery

新A02第一次外层driver使用system Python，缺`mcp`依赖，在派发前KNOWN_NO_EFFECT；原unit只有intent/reservation，没有consume/outcome。其本地异常处理还缺`AiVideoError` import，已补。Parent封单源、短时恢复授权，固定video-mcp venv；原失败/授权r1/r2/r3均保留。两次恢复admission因授权枚举大小写与preview嵌套字段读取错误停止，均未派发/消耗。第二处修正为读取 `preview.request.audio_sha256`，没有放宽源/PCM/request/原unit检查。

最后一次通过admission后只复用原未消费unit，未调用prepare_operator_unit、未重铸permit，真正音义调用发生一次。其 `operator/outcome.json` 为UNKNOWN且consume=true；`resume-001/resume-summary.json`为EVIDENCE_GAP/operator_status UNKNOWN，phase停止。旧失败记录、旧四个UNKNOWN与旧STOP未动，新B/C均无音义调用。当前累计可核对为旧6个consumed audio units加本次1个，UNKNOWN旧4加本次1；实际收费未结算，不能将内部USD0.05 reservation当实际价。

新证据证明声音服务尚未恢复；不把先前gzip条件修复当作服务恢复或实际旧UNKNOWN根因。后续只能据当前缺口做人类实际听审或经canonical owner修复新source能力，不重试本次/旧UNKNOWN。

### Execution And Verification Boundary

90分钟新窗口 `benefit-continuation/operator-window-renewal.json`（SHA `e11ada076795443f03fe7773d0ecb34f9962ea6d464399fe0641412b32aed9de`）保留18次task、6次/片、9000 CRD内部ceiling与历史，不增额度、不重置。当前task paid video invocation=9（原3+repair3+本次3），每片3；加task之前历史9为总18。实际积分/费用仍待核账，不按ceiling估算。

本地作者输入缺rich projection字段与B02相机orientation冲突均在start/submit前发现；三份零generation/零paid的初稿完整存档为 `runtime-authoring-incomplete-001/`，另B的零效果修订存为 `runtime-authoring-incomplete-002-B/`，没有覆盖任何已开始attempt。当前bootstrap在写入前使用真实 `ProviderNeutralGenerationIntentProjection`，不以GenerationIntent单体parse冒充router-ready。A/B/C实际exact native preflight均PASS；Parent executor独立read-only review的初始snapshot无findings，未来Gate路径/shot-specific输入路径作局部对齐，实际后镜拒绝已复核。

worker局部验证包括audio operator24项、qualification preview3项及P4 lint/check；未运行全工程套件，不宣称fresh Harness全回归。新A03 draft已移除2.5-only conversation，使用团长单句，灰雾幻想角色/场景仍是draft，不是已执行Shot。原完整片仍未完成/未验收/未投放；这三条是明确标记的非PASS诊断审片，不是最终40–60秒广告。

当前HEAD `1c53e61` 为其他窗口已有进度，index为空；本任务新run输出gitignored，源码/记录尚未commit/push。遵守film-first边界，不能因记录或局部技术PASS提前发布/夹带共享dirty改动。当前自动学习评估 `no_candidate`：多媒体实验动作/参考/内容不同，没有隔离变量；单次pre-dispatch修复与新UNKNOWN不能泛化为服务已修复或一种接镜策略更优。

## User Review And Benefit Revision — 2026-10-25

用户后续明确反馈“已看听，A/B声音正常，C动作接受”，随后提出“没问题,但是我们要讨论下产品的功效在哪,现在只是有了开局夸张”。exact交付/原始MP4映射及原话在 `creative/user-review-20261025-002.json`。这补充A/B的人类实际声音观察，并接受C当前先跳再抓的动作变体；不宣称旧C已执行原先抓后升意图，也不结算任何UNKNOWN。下文“未收到反馈”属于此反馈之前的历史checkpoint。

三条完整片仍未完成。当前先讨论功效如何进入后续剧情，保留已认可首镜，不在卖点主线尚未敲定前提交后镜。新发现：现有Product Truth曾只用商品PNG与品名，遗漏用户所给详情和检测资料；详情主打淡斑焕亮、均匀肤色及润泽肤感。检验报告包含紫外线诱导人体皮肤黑化模型的祛斑美白项目，但受检样品标30ml，当前SKU为15ml；规格/配方承接及任何量化广告claim尚未闭合。此为讨论依据，不是新功效承诺、数值或见效期限；尚未修改原sealed Product Truth、Director coverage或正式Gate。

## Goal And Current Status

用户批准三条夸张剧情广告，每条40–60秒、Seedance 2.0，3秒内出现产品、至少完整说出“颜生源美白祛斑精华液”，并要求“栖澜百货商贸”低存在感缓慢动态水印。当前方案为每片5个10秒生成单元加4秒真实商品落版，目标54秒。三条完整成片**未完成、未验收、未投放**；用户提出的30分钟交付目标没有达到。

主运行目录 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/`，下文相对证据路径均以此目录为根。旧影片、旧原始首镜、原FAILED/UNKNOWN、预算和消费记录均保留。

## Exact Media And Review

三次原始首镜：A整盖拔离且缺少可见滴管结构，B标签蓝胶囊改成ESSENCE，均为exact MP4视觉FAIL；C平台终态FAILED、错误码20008，无MP4。该数字码没有已核实的语义解释，不推断为审查、质量或输入类型错误。

有界repair-001使用新节点：A/B真实first/last-frame，C使用开场布局、期望巨瓶构图、女主身份三张软参考。修复素材均已canonical submit/poll/fetch，并由Parent显式调用project-local video-analysis；独立TUI另作逐0.25秒采样和局部加密核对。

| Film | Exact repair MP4 SHA-256 | Current raw Gate | Evidence boundary |
| --- | --- | --- | --- |
| A | `30fca882f55646c35f809431dcbd298c681df9e40aa74ed841590d6719f3ec32` | NOT_EVALUATED | 可见时段盖附着、先稳瓶后旋拧、惊吓转窗改善；中段连接处出画，精确半松与声音未完整证实。 |
| B | `91dfb788b949de9357fd5e291075f2a2d95d5ad83adfc4ed47f630d7efb9ea25` | NOT_EVALUATED | 入场、受惊、接触后拿瓶可见，未重现ESSENCE；闪电/震窗及声音仍有缺口。 |
| C | `9bdc9577ba5679a87a03a57da4f6d49a85576d83be54a041c1840b3f2bedc5a0` | FAIL | 巨化、破顶、悬挂末态可见，但6.5秒已先跳离地、7.083–7.25秒才抓盖，不符合先抓盖再由增长带起的因果。 |

实际Gate在 `repair-001/runtime/{A,B,C}/{film}01-post-media-gate.json`；分项复查在 `ref-audit/{shot}-repair-001-review.json/.md`。可辨认身份与无法逐字核准的微小fineprint分开，不把小字看不清擅自升级为身份FAIL，也不宣称所有印刷字已精确通过。

## Local Review Delivery

三个10秒首镜经P4 `CompositionSpec → ResolvedTimeline → HyperFrames` 渲染为1080×1920、24fps、240帧、单AAC原声音轨。水印只取完整54秒轨迹的0–10秒切片，不将整条路径压缩到10秒；保留AI生成标识。源视频是VFR，241个解码帧、1/20与1/30秒间隔交替；没有按容器r_frame_rate=60重解释播放速度。

本地目录：`/home/reggie/电商/颜生源/广告试片/2026-10-25-三条夸张剧情/修复候选/`。

| File | Delivered SHA-256 |
| --- | --- |
| `01-A01-全城戒备-修复候选-10秒慢水印-未通过质检.mp4` | `0fbe4fe81f5263a2043c223b45143bbf01a030dff088aca5e7c9b83ebf2665f3` |
| `02-B01-三界抢瓶-修复候选-10秒慢水印-未通过质检.mp4` | `0bb762ecdfeb16d32f0a045fc081742d19005f1618746945c12592d89f3e6348` |
| `03-C01-巨瓶破顶-修复候选-10秒慢水印-未通过质检.mp4` | `f646327fdbb076b17758dcf32704e37abf99740448d1db0d69db7452a81ddb84` |

逐项源/副本hash、渲染报告、raw Gate在 `post/repair-001-delivery.json`；用户目录有 `新片状态说明.txt`。Parent实际查看三份水印衍生片0/9秒帧，不把静帧核对当成完整听看。另已渲染4秒真实产品PNG落版：`post/product-hero/r1/render/output/颜生源-美白祛斑精华液-4秒产品落版-50秒轨迹慢水印-候选.mp4`，SHA `0386c03b25e555c0e0f7725c7ba3ebe4b1d04a3a7f2160a7c832834088860c2b`；仅素材，不是完整广告。

## Audio Blocker And Conditional Transport Fix

原A首镜得到一次盲声音观察，但广播含混；原B分析consumed后transport_unknown。旧S02/S04 UNKNOWN继续封存。Parent对独立视觉FAIL/平台FAILED后产生的三份新修复媒体建立有限准入，核对不同full-track PCM、exact fetch、原失败依据、旧STOP及消费hash；最多3个新源，每源1次，无自动重试。不是重试旧音轨，也不释放旧reservation。

repair A声音分析单次consume于04:10:50.483579 UTC，04:10:51.304220 UTC返回 `UNKNOWN/transport_unknown`，没有observations。准入phase立即停止，repair B/C没有创建新unit或发送声音请求。证据为 `audio-evidence/A01-repair-001-review.json`、`repair-001-execution-stop.json`、`repair-001-audio-disposition.json`；新旧UNKNOWN仍未结算，不用转写或静帧签听感PASS。

只读排查和纯内存复现确认一个条件性代码缺陷：httpx 0.28.1的 `iter_bytes()` 已解码gzip，原transport重建Response仍携Content-Encoding，可能二次解码抛DecodingError，被归为UNKNOWN。已在 `src/ai_video_mcp/audio_understanding.py` 重建前移除失效的Content-Encoding/Content-Length；保留解码后1MB限制、45秒timeout、禁重定向、trust_env=False、单次POST、注入凭据和permit/outcome合同。

相关回归4项、完整 `tests/test_mcp_audio_understanding.py` 29项通过；Parent审核完整diff，并仅清理一处新测试unused import。证据 `network-evidence/diagnosis.md`、`transport-fix-review.json`。历史响应未记录异常class/encoding，**不能断言该缺陷就是旧UNKNOWN的实际原因**，也未用旧请求做live重试。无凭据公开HEAD和2.4MB合成body OPTIONS连通探测有响应，只证明对应公开探测可完成，不证明真实分析服务恢复。

## Continuation Preparation And Counts

`operator-bound-extension.json` 保留旧v2与原9次调用/6次native/644积分历史，新增范围上限15→18次、每片5→6次、内部credit ceiling7500→9000，仍每槽1次、自动重试0。实际新片当前共6次视频paid invocation：原首镜3次加repair3次，每片各2次；FAILED不自动回收slot。积分ceiling不是市场报价，本次新增调用实际扣点未完整核账。新run声音已consume3个unit，内部单次USD0.05是reservation上界，实际费用待确认。

run-local续镜loader已覆盖Shot02–05：02参考对应repair01；后续按实际accepted来源取帧。A03指挥中心cutaway与A04回切保持multimodal软参考，A04画面参考A02，提交顺序仍要求A03完整Gate PASS；不从指挥官硬首帧变形回女主。所有原PENDING输入和master不覆盖，新单镜通过唯一committer接入。

已接入 `continuation-readiness/authoring_adaptation.py`：保留完整动作和逐字台词，移除重复终态与套语，角色只写本人的动作；B03不重演B02入场，C04/C05明确微型成年女主。12镜纯内存native compiler投影均≤4000，最大3922；实际reference-duty仍可能增加长度，必须以fresh canonical prepare为准。Parent另核12行schema、幂等、首尾态/完整progression/参考计划保留。没有真实PASS帧包、没有创建后续trial或提交后续Shot。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original-A | jimeng:0e3811ae4a6f3890b67a7039a2a3169385e657117f11696a8f29b7b1084c0def | ysy-three-first-shots | yanshengyuan-three-v5-A-A01-qualification-attempt-001 | N/A | 634e2a0f9ec121cc93c0b5d4952f6f75139d3dc0f016a8a35eb2efb1e419dc9f | ANALYZER | FAIL | CAP_PROP_STATE | NEW_ATTEMPT | NONE | runtime-v5/A/A01-post-media-gate.json |
| original-B | jimeng:29895ce2de05ee04ac089a604634a18c81073b4503e6e6b194bc312a2ad1304f | ysy-three-first-shots | yanshengyuan-three-v5-B-B01-qualification-attempt-001 | N/A | de15d6e3e534e86c250836b0d0b64dd532dc63eb46c92837e0b77df5b9c7782a | ANALYZER | FAIL | PACKAGING_TEXT_DRIFT | NEW_ATTEMPT | NONE | runtime-v5/B/B01-post-media-gate.json |
| original-C | jimeng:50a79064ad6b50a62be936feab221c663acf81144517fabb1657db87227ceafa | ysy-three-first-shots | yanshengyuan-three-v5-C-C01-qualification-attempt-001 | N/A | NO_ARTIFACT:PROVIDER_FAILED_20008 | PROVIDER_RECEIPT | FAIL | PROVIDER_FAILED_20008 | NEW_ATTEMPT | NONE | runtime-v5/C/C01-poll-001.json |
| repair-A | jimeng:699301551db8f9e3f168b28e7573913894b3f5881bd3924ff10835be8206907c | ysy-three-repair-001 | yanshengyuan-three-repair-001-A01-attempt-001 | N/A | 30fca882f55646c35f809431dcbd298c681df9e40aa74ed841590d6719f3ec32 | ANALYZER | NOT_EVALUATED | AUDIO_AND_OBSERVATION_GAPS | NEW_ATTEMPT | NONE | repair-001/runtime/A/A01-post-media-gate.json |
| repair-B | jimeng:6b0b650edc40f06a18559dc001b6b77ae32dc719d48f8607c0f7d5166cf21e43 | ysy-three-repair-001 | yanshengyuan-three-repair-001-B01-attempt-001 | N/A | 91dfb788b949de9357fd5e291075f2a2d95d5ad83adfc4ed47f630d7efb9ea25 | ANALYZER | NOT_EVALUATED | AUDIO_AND_ACTION_EVIDENCE_GAPS | NEW_ATTEMPT | NONE | repair-001/runtime/B/B01-post-media-gate.json |
| repair-C | jimeng:6d604cc68cdb641edd53e3f833942134d8c5f88f5c327fc1acd30f3cd0cdf1f3 | ysy-three-repair-001 | yanshengyuan-three-repair-001-C01-attempt-001 | N/A | 9bdc9577ba5679a87a03a57da4f6d49a85576d83be54a041c1840b3f2bedc5a0 | ANALYZER | FAIL | CONTACT_LIFT_CAUSAL_ORDER | NEW_ATTEMPT | NONE | repair-001/runtime/C/C01-post-media-gate.json |
| repair-A-audio | audio:ba84ce63dbc8255c2d4194a6418b14f1a0bf6b0725bb48f99e1e6f682b760a20 | ysy-three-repair-audio | A01-repair-001--30fca882f55646c35f809431dcbd298c681df9e40aa74ed841590d6719f3ec32 | N/A | NO_ARTIFACT:TRANSPORT_UNKNOWN | ANALYZER_RECEIPT | UNKNOWN | TRANSPORT_UNKNOWN | NEW_ATTEMPT | NONE | audio-evidence/A01-repair-001-review.json |
| benefit-A | jimeng:22dd0b9cca7599191014a1d48b94782e41f81304e6869872d37d56c46bea8c4d | ysy-benefit-shot02 | yanshengyuan-benefit-v2-A-A02-qualification-attempt-001 | N/A | 5d47d40b63b23c9d121e5b3399b4826966913fd5fbfff73376902452e35abc34 | ANALYZER | FAIL | ONSCR_DIALOGUE_MISMATCH | NEW_ATTEMPT | NONE | benefit-continuation/source-acceptance/A02/post-media-gate.json |
| benefit-B | jimeng:611d480aced78f26ebf9355cf4b2682ea1d024f3b9d3399ae29851b23bc1dab8 | ysy-benefit-shot02 | yanshengyuan-benefit-v2-B-B02-qualification-attempt-001 | N/A | 18fbc0ebac2b396c52aec5451c4fb79b3777115a57a244228a3fa26cf4173aa4 | ANALYZER | NOT_EVALUATED | AUDIO_EVIDENCE_GAP | NEW_ATTEMPT | NONE | benefit-continuation/source-acceptance/B02/post-media-gate.json |
| benefit-C | jimeng:912bf57971fb931dfb5b3462a6ffdc276f5a2ecadbae70c5d77b6a416f6913f9 | ysy-benefit-shot02 | yanshengyuan-benefit-v2-C-C02-qualification-attempt-001 | N/A | 7242c94cbc46fc3f09b82d84f5bf6e3ed2b319d627a00f5d516e010257619cfb | ANALYZER | FAIL | UNREQUESTED_PROP_FLIGHT | NEW_ATTEMPT | NONE | benefit-continuation/source-acceptance/C02/post-media-gate.json |
| benefit-A-audio | audio:8f0d8d01c7ff555522b6558068288ebdbe71d32043bd0bfb83020ffba7ace63b | ysy-benefit-audio | yanshengyuan-benefit-A02-audio-001 | N/A | NO_ARTIFACT:UNKNOWN | ANALYZER_RECEIPT | UNKNOWN | AUDIO_OBSERVATION_UNAVAILABLE | NEW_ATTEMPT | NONE | benefit-continuation/audio/attempts/A02--5d47d40b63b23c9d121e5b3399b4826966913fd5fbfff73376902452e35abc34/resume-001/resume-summary.json |
| single-A-opening | jimeng:6caeaa6136dc9c47b8cfa4bb6d0501325b18cdc918c9a342f26d7de34fb21ff2 | ysy-single-a-opening-rework | yanshengyuan-single-a-rework-001-A-A01-qualification-attempt-001 | N/A | ccc6b91626b82ad75e6404ba6745adca049d977a1e519ae9ef8e5056a6035336 | ANALYZER | NOT_EVALUATED | AUDIO_AND_FULL_PERFORMANCE_REVIEW_GAP | NEW_ATTEMPT | NONE | single-a-rework-001/source-acceptance/A01/post-media-gate.json |

## Completion And Publication Boundary

下段保留三片阶段的历史状态；当前以Single-Film Opening Repair Checkpoint为准。

当时的阻断是声音证据缺失与C确定的动作因果失败，不能提交下一镜。已向用户提供三段实际候选并请求真实原速听看反馈；未收到反馈前不假定接受，也不自行改变C的原动作要求。下一步先补证/按真实要求修复，所有必需finding PASS再续镜；不能借重建素材重试音频UNKNOWN。

本次共享decoder小修及既有Jimeng/Gate改动均未commit/push；Git index保持空，未夹带其他窗口修改。依项目film-first规则，完整工程验证和发布不冒充媒体完成。HEAD为另一窗口已有的136038a，本地origin/main跟踪ref在2d17c49；未为本记录查询远端服务器，不将本地跟踪ref当作服务器最新状态。本次不推送这些未验收或受阻变更。

自动 `distill-ai-video-learning` 评估：`no_candidate`。gzip为单个离线条件复现，历史响应原因不明；镜头修复同时改变prompt、构图和参考条件，没有隔离变量，不能泛化首尾帧的成功率或把多个证明层算独立实验。未修改Skill/Policy/Gate学习目标，没有创建占位claim。
