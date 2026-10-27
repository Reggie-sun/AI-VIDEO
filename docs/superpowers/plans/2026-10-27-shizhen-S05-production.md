# Shizhen S05 Production

## S05-007 Delivered — Current

提交Gate与原006 UNKNOWN恢复已完成，007已通过normal committer/adapter、新preview/预算/quota/durable intent/one-use permit实际submit一次并fetch。原声单段为`outputs/shizhen-episode01/失帧-第一集-S05-Seedance2.5-007-固定人物参考-原声-20秒.mp4`，SHA `dca4ee9f8658778d43a2ff4de56d6741ee503a2f5838e27df29272d753495114`；1920×1080，video20.016667秒/481帧，container20.065秒，原生VFR/H264/AAC。仅exact copy，无拼接/后加字幕/变速/发布。

project-local `video_analyze`已显式调用，Parent及独立媒体复核已查看80帧采样、3.5秒林序近景、8.5秒骑手近景和20秒末帧，未见对白字幕或明确固定母图身份漂移，五段摄影可辨；16.5秒切回时仍看骑手、左手在低位，之后看饭→抬手→指认→收回身侧→回看，末帧完整头脸/双手/右手手机与骑手左托盒可见。采样不证明原速自然度或口型；默认scene detector的1scene不能覆盖实际五段观察。平台AI生成水印保留。

新007 exact audio-understand单次POST成功HTTP200，完整identity与盲观察已保存；旧S03/004音频UNKNOWN未重试。观察支持五轮/两声线，但整体被描述为relaxed/casual且首句识别为“后面呢”而原文“后边呢”；不能将其签作低声焦急与逐字对白PASS，也不能仅凭识别差异认定实际错词。当前canonical evaluation为EVIDENCE_GAP、无confirmed failed requirement、all_required_observed_pass=false，Per-Shot Gate NOT_EVALUATED、human NOT_EVALUATED，next S06 STOP_EVIDENCE_REPAIR_FIRST。原声听感、首句用词、正常速度接点/完整表演待用户审片；不追加同片重生成来补证。

本有限单元新增video1、image/audio生成0、独立音频分析POST1（一次本地授权reference格式失败发生在unit/credential/POST之前，known-no-effect0调用；已修字段而未触碰旧UNKNOWN）。全片28次video提交尝试=27 accepted/settled+1 known_no_effect，S05七次（含006无效果）；视频报价1280CRD，实际扣费仍PENDING，1500为内部guard。音频分析内部guardUSD0.05，实际费用待确认。工程round10 finding set为空，累计10/上限11；定向75通过、既有compiler82与provider/recovery263通过，关联202通过/2既有失败均原HEAD owner复现，docs33通过；不是full regression或媒体PASS。

证据主目录`L/S05-repair-007/`：`compiler-recovery-review-round10.json`、`clone-admission-result.json`、`accounting-after-submit.json`、`fetch-output.json`、`raw-delivery-receipt.json`、`exact-media-mcp-response.json`、`S05-007-audio-understanding.json`、`canonical-observation.json`、`post-media-gate-007.json`。按本任务成片优先边界，新改动待认可后完整验证再owned commit/push；之前独立Gate slice已push的`852b3b4098f095c0db91370935e6e3a55c9899bb`不改写。其他窗口dirty/staged保留。学习评估no_candidate，不把多证据层或混合变量的前后片升级为普遍模型质量结论。


## Current Recovered State

006已依据原始native body prompt的1007→1006末尾LF差异，经原Worker复现、项目副本验证及native审查round9后，沿唯一committer追加verified no-effect reconciliation。真实Manifest82重开PASS，006为known_no_effect、旧UNKNOWN receipt留存、原预留释放actual0；历史24次尝试不归零，新生成0。当前修显式compiler2的边界空白适配，保留compiler1 bytes与完整QA/Goal；007尚未start，S06未submit。实际证据与最新状态归S05 primary record及`L/S05-repair-006/reconciliation-result.json`，下方旧UNKNOWN停点为历史。

## Unknown Stop — Historical

引用归属恢复已应用到真实Project7，81精准/72关联与native工程round6（remaining findings为空）完成。006实际进入submit_once后返回UNKNOWN；没有sealed Jimeng dispatch/resource可查，canonical query-only recovery一次仍KEEP_UNKNOWN且Manifest未变。当前video24次尝试=23known+1UNKNOWN、S05六次；quote1280credits、扣费/是否产生新视频未确认，reservation保留。没有新MP4或媒体PASS，S06未submit；停止新付费尝试，不重发/remint/补造dispatch/新root归零。事实与恢复边界归S05 primary record最新段及 `S05-repair-006/attempt-outcome-receipt.json`。下方旧引用阻断和用户暂停均是历史状态。

## Admission Block — Historical

用户已解除暂停。固定林序/骑手参考已导入S05 Project6，1007字纯中文准备稿、9图与一个空节点已备；历史video23/S05五次，新有限单元24/六次尚未提交或消费permit。当前normal prepare因旧动作参考丢失Character归属而被拦截，不能覆盖封存Project6或绕过exact /5 target。必须先通过committer保留历史的未提交归属恢复；该恢复尚未实现，当前停止paid attempt，S06不提交。实证与剩余工作归S05 primary record最新段及 `S05-repair-006/reference-owner-blocker.json`。下方旧用户暂停是历史状态，不应重新索要“继续”。

## Hold — Historical

用户最新明确“先别生成了,主人公的referces都没有固定我发现...”。所有图像/视频生成暂停；累计video23、S05五次，006仅离线准备且未进入canonical state/预算/permit。S06继续阻断。先完成林序共同身份锚点及派生参考的核对，不按下方历史“下一步生成”自动执行；审计归 `runs/shizhen-episode01-jimeng25-20261025-001/live-action-regeneration-01/identity-reference-audit/README.md`，当前状态归S05 primary record。

## Junction Repair 005 — Historical

004已实际生成/fetch：SHA `34cfb8fdc2177657670b236acd7c63e0c72ebb2e856d584cfce7ffacf0ad7772`，1080p/20.016667秒视频/原生AAC，累计22次。完整头脸与左手落身侧已出现，但用户明确“16s的这个shot衔接很不自然”；exact decoder frame396@16.5仍看骑手，397@16.55已低头伸臂指饭，跳过动作起始。另有模型原片烧入对白字幕。004 canonical action/space-camera/coverage/story-scope FAIL，不改写成过关。

004新音频分析在exact004的独立development unit中实际consume一次后返回 `transport_unknown/UNKNOWN`，未取得声音观察、不重试；旧S03 UNKNOWN同样保留。第一次system Python缺mcp发生于operator准备前，known-no-effect；之后复用既有venv，未安装依赖。不要以MCP isError=false推定声音成功。

在004单元结束、22次结果全known核对后，按新用户接点拒绝封存下一有限005单元：最多1次video、own4→5、历史22→23、自动retry0、图片新增0，不重置任何旧消费/UNKNOWN。仅用现有6张exact图及原raw QA：第四镜切出仍看骑手、左手未抬，第五镜同态切入后才连续看饭、抬手、短指、收回、回看；约6秒末镜容量是生成余量，不是对白或验收时间戳。保留完整头脸双手、焦急近景、原五句、20秒/2.5/1080p原声；明确声音台词不渲染成画内字幕。仍先单段审看，不S06/拼接/后期字幕/发布。

## Ending Repair 004 — Authorized And In Progress

用户在S06被前序Gate阻断后明确“先处理失败”，本次先修S05-003已知末段裁脸及左臂未完整收回。此新授权用于一次有界S05修复，旧不自行追加S05的边界不解释成永久禁止用户后来要求的修复。保留全部旧FAIL、原五句、20秒、2.5、1080p原声、多镜近景及既有5张绑定；只新增一张已查看的完整头脸/双手/收手末态参考，修订第五镜表达，不降raw QA或改旧结果。

工作入口为 `L/S05-repair-004`，沿原 `R/trial-S05-v1` task使用现有 `/5` 和唯一committer。新有限单元最多1次video，own3→4、历史21→22、自动retry0；图片最多2次、已实际1次且结果known。平台21个已知video资源均完成，新空节点已单独创建；当前6图/20秒/1080p quote1280credits，仍须submit时由adapter重核。1500/call只是继承的内部operator guard，新累计budget4500→6000CRD，不是市价或实扣；无重置消费。旧S03声音UNKNOWN不重试。

先做prospective compile和最终native preflight，再正常封存supersession/Project+1/预算续期/start/quota/new permit并submit一次；exact新片后逐项MCP、实际视觉和声音观察，先交原声单段。若仍FAIL/NOT_EVALUATED如实记录并停止该单元，不以S06准备或ASR替代验收。当前未生成新片，不宣称修复通过，不拼接/字幕/发布；后续仍保留S06原目标。

## Multi-Shot And Readable Performance Repair — Current

003实际结果已取回并交原声审看，SHA `760c14af792e466e88a9ac427e1ee2abb3c47ff5f0de35ec4fa183c654a5b801`。五段摄影画面与林序近景已出现；末段取景过低、脸被裁掉且未完成封存收手末态，action/coverage FAIL。语气/自然度/逐字听感未获人工接受，仍NOT_EVALUATED；未把多镜改善当完整成功。当前21次video全部known，本有限单元1次已用尽，报价1280credits实际扣费待结算；只交单段原片，不自动重试或推进后续。实际证据归primary record与 `L/S05-repair-003/raw-delivery-receipt.json`。

用户已观看002并明确“首先我没看出来很焦急,面部表情控制看不到,然后这个镜头不应该是一镜到底”；002当前performance/coverage为用户拒绝，旧NOT_EVALUATED记录与技术观察保留。此指令明确取代旧固定双人中景，不能把旧摄影形式当不可改的修复限制。

003沿同root/task仅新增一次2.5/20秒/1080p原声生成，own2→3、全历史20→21、零自动retry。摄影按普通指路→急切纠正→普通困惑→具体作证受阻→指饭收手组织5个机位，重点用林序正面近景看眉眼嘴、短促呼吸和急于求承认；末句骑手画外，林序听到即在近景内反应，再切含台面手势的中近景。对白逐字不变且不分配时间戳，持物/轴线/身份/场景和前镜认可末态保留。2.5的20秒由用户继续保留，一次生成包含这些摄影镜头，不将Shot ID等同摄影单镜。

原4张exact参考保留，补1张已实际查看的林序焦急近景（新05）；两张新后段手势图分别错换手与指向手机，均known outcome、保留而不绑定，不以负面词掩盖错误。此次image共3次、只选1；视频实绑目标为5图，新近景只控制脸/摄影/求证表演，不把骑手肩前景复制到每镜。影像成本未暴露。

采用既有 `/5`、不新增执行链：sealed target显式列出被用户修订的raw required IDs，复用 `/4` 的QA身份/proof/owner保护；原图不变，只准封存新增图ID及其exact bindings。原Goal内容保留仅升版本、Project恰好+1、完整paid历史/quota/budget/permit/UNKNOWN保护保持。必要实现经针对性验证和原native reviewer核对；实际原声审看与完整工程验证分别取证，未获认可不拼接/字幕/下一镜。官方[2.5提示词指南](https://docs.volcengine.com/docs/ark/seedance-2-5-prompt-guide?lang=en)的景别/表演/参考职责说明仅作advisory，不能保证模型执行。

## Authorized Performance Repair

当前执行结果：attempt002 已经 canonical submit/fetch，原声MP4 SHA `67fac2bf925127b257486cf3f359aac56155c038b709e5d4b2da6b0b2a1f1ed0` 已交用户单镜审看。真实新增1次，全部已知video总数20、S05共2；native quote1280credits、实际扣费待结算。MCP、80张采样与local ASR已取得，但焦急语气/正常速度反应尚无新片人工认可，保持NOT_EVALUATED，不提前拼接、上字幕或推进S06。当前准入代码36精准/54关联通过、一次独立native reviewer findings为空，不等于媒体验收或完整工程验证；具体路径及边界归primary record。

S05-001 exact SHA `2155df692f9ae6fd2e72198f74a4dad53a33d8e70709c7505d7858e6d7231d31` 已实际fetch，用户拒绝约12秒笑意和主角全段语气。native prompt中“想笑”重复6次，且末段表情落在throughout字段；原对白只约束文字/说话者/口型，未明确逐句发声方式。已按真实用户反馈记录performance/sound FAIL，不重签旧片PASS。

用户最终明确“就用2.5吧,因为我忘了你做了20s”，并指定“焦急的,想证明自己”与“上一镜余惊未消、压低声音急着求证”同时存在。故本次保留2.5、20秒、原五句、4图和持物/空间，只修表演：嘴角平直、下颌张力、余惊的浅短气息、压住音量又急切地解释，分opening/response/settle；两句分别强调“刚才”与“热饭/红围裙”，结尾指饭收手仍焦急。取消先前拟议2.0/15秒选择，该选择未发生任何POST。

沿同root/task封存attempt002，一次新增video，历史19→20、own1→2、自动retry0；原1280credits quote重新核对，内部budget1500→3000CRD是两次guard累加，费用待结算。原FAIL/已fetch/所有旧permit和UNKNOWN保留，不另开root归零。

当前既有同模型authoring入口只支持单首帧，现有R2V retarget只支持换模型；实际四图同型号表演修复有确定性准入缺口。最小扩展原 `generation_authored_retarget.py`、`_generation_authored_prospect.py`、`_qualification_authoring_revision.py`：仅known fetched FAIL、同task/Shot/Provider/model/capability/compiler、同exact image/media/output、原QA和仅升版本的完整Goal、下一有限paid quota+1、零resample、原new permit允许改prompt及fresh profile/node。新分支不开放参考/分辨率/时长/模型重选，不绕过committer、封存目标或submit锁，不改旧schema/serialization。用现有retarget tests覆盖边界，再经一次read-only native independent review核对paid admission语义；缺失review不POST。其他窗口dirty/staged内容保留。

## Goal And Authority

用户“过关,开始shot5”接受S04接点修正版，授权实际制作真人S05原声单镜。前序exact SHA为 `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`；认可不改写原S04 raw FAIL、assembly crop warning或旧S03音频UNKNOWN。原剧本与S05已批准coverage继续拥有剧情，旧CG媒介已由用户真人要求取代。只生成S05，不生成S06、不发布；先给单镜审看，拼接与字幕停在既有审看边界。

## Complete Event And Continuity

承接林序已经看向右侧骑手、右手手机垂髋、左手自由的实际末态。骑手已取好自己的一个长方餐盒，左掌托底、盒靠腰腹，右手可扣头盔；手机已收进口袋。保持原白开放式头盔、黑雨衣和黑黄背包，补足此前未看清的普通成年男性脸。林序的三角饭团始终在原白纸上，咖啡瓶直立，枪横卧瓶左，不重扫或重掉。

原话按自然听说次序完整保留：骑手“你找老板？后边呢。”；林序“不是。刚才这个小伙子。”；骑手“什么小伙子？”；林序“给我热饭那个。红围裙。”；骑手“你不是自己热的？”。骑手听到“小伙子”才停扣头盔、看柜台再看林序；结尾林序想笑没笑出，用左手短指饭团又收回，右手手机不抬不换手，餐盒始终左掌托稳。店长下镜才出现。

摄影沿原S05顾客侧双人中景：林序左、骑手右，可互看且脸、盒底、手机与指示动作可读；稳定观察两人的认知分歧和同时发生的听说反应，完整事件不靠反打藏掉反应。选择这一个摄影机位有叙事理由，不由时长或生成方便默认。实际新的站位来自同场向右取景，不镜像或跨柜台。

## Reference And Execution Boundaries

四张planned模型图：1为S04 exact terminal（林序身份/已降低的手机，非旧单人构图控制）；2为新双人开场/骑手形象；3为骑手右手停扣、左掌托盒中态；4为林序左手指示、右手手机仍垂髋的后段动作。S01三人旧图仅给制图参考骑手衣物，不进入视频模型，防止旧店员/持物姿势回流。实际逐图核验后才绑定；参考不保证动作或口型。

五轮约四十字对白、拿稳餐盒/停扣/查看/指示收手及自然倾听呼吸按约20秒完整事件分组，选已实查的Seedance2.5 multimodal、1080p、native audio KEEP；2.0的15秒上限不通过赶词或删反应解决。原生quote1280credits，内部1500CRD只是guard，真实扣费待结算。18次已知video保留，新增S05最多1次，合并有限上限19，自动retry0；图像补充当前最多3次新图，费用未暴露。

L/S05负责当前入口、参考与执行辅助；R/trial-S05-v1为新逻辑镜头canonical root，task `shizhen-S05-qualification` / attempt `shizhen-S05-qualification-attempt-001`。不创建worktree，不覆盖sealed数据，不裸调Provider，不改其他窗口源码。经现有Registry、ProductionStateCommitter、compiler、preview、budget/quota、durable intent及一次性permit。提交前重查全部roots与平台已知状态，UNKNOWN不重试。

## Verification And Delivery

用户认可edited-S04的技术handoff仅绑定该新成片scope，旧raw和assembly技术结果保留。S05封存前检查四图实际顺序、每人物参考/表演与全五轮对白，时长/benefit/output一致。取回后explicit project-local MCP与实际画面/声音证据分别裁决，不用ASR或音轨存在冒充自然度与人工接受；不能预签PASS。先交原声单镜1080p审看片，记录实际成本状态、所有生成计数和未验证项。
