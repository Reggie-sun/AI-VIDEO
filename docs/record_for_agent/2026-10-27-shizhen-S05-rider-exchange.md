---

## Recovery Pre-submit Verification — Latest

## S05-007 Delivered — Current

提交Gate与原006 UNKNOWN恢复已完成，007已通过normal committer/adapter、新preview/预算/quota/durable intent/one-use permit实际submit一次并fetch。原声单段为`outputs/shizhen-episode01/失帧-第一集-S05-Seedance2.5-007-固定人物参考-原声-20秒.mp4`，SHA `dca4ee9f8658778d43a2ff4de56d6741ee503a2f5838e27df29272d753495114`；1920×1080，video20.016667秒/481帧，container20.065秒，原生VFR/H264/AAC。仅exact copy，无拼接/后加字幕/变速/发布。

project-local `video_analyze`已显式调用，Parent及独立媒体复核已查看80帧采样、3.5秒林序近景、8.5秒骑手近景和20秒末帧，未见对白字幕或明确固定母图身份漂移，五段摄影可辨；16.5秒切回时仍看骑手、左手在低位，之后看饭→抬手→指认→收回身侧→回看，末帧完整头脸/双手/右手手机与骑手左托盒可见。采样不证明原速自然度或口型；默认scene detector的1scene不能覆盖实际五段观察。平台AI生成水印保留。

新007 exact audio-understand单次POST成功HTTP200，完整identity与盲观察已保存；旧S03/004音频UNKNOWN未重试。观察支持五轮/两声线，但整体被描述为relaxed/casual且首句识别为“后面呢”而原文“后边呢”；不能将其签作低声焦急与逐字对白PASS，也不能仅凭识别差异认定实际错词。当前canonical evaluation为EVIDENCE_GAP、无confirmed failed requirement、all_required_observed_pass=false，Per-Shot Gate NOT_EVALUATED、human NOT_EVALUATED，next S06 STOP_EVIDENCE_REPAIR_FIRST。原声听感、首句用词、正常速度接点/完整表演待用户审片；不追加同片重生成来补证。

本有限单元新增video1、image/audio生成0、独立音频分析POST1（一次本地授权reference格式失败发生在unit/credential/POST之前，known-no-effect0调用；已修字段而未触碰旧UNKNOWN）。全片28次video提交尝试=27 accepted/settled+1 known_no_effect，S05七次（含006无效果）；视频报价1280CRD，实际扣费仍PENDING，1500为内部guard。音频分析内部guardUSD0.05，实际费用待确认。工程round10 finding set为空，累计10/上限11；定向75通过、既有compiler82与provider/recovery263通过，关联202通过/2既有失败均原HEAD owner复现，docs33通过；不是full regression或媒体PASS。

证据主目录`L/S05-repair-007/`：`compiler-recovery-review-round10.json`、`clone-admission-result.json`、`accounting-after-submit.json`、`fetch-output.json`、`raw-delivery-receipt.json`、`exact-media-mcp-response.json`、`S05-007-audio-understanding.json`、`canonical-observation.json`、`post-media-gate-007.json`。按本任务成片优先边界，新改动待认可后完整验证再owned commit/push；之前独立Gate slice已push的`852b3b4098f095c0db91370935e6e3a55c9899bb`不改写。其他窗口dirty/staged保留。学习评估no_candidate，不把多证据层或混合变量的前后片升级为普遍模型质量结论。


2026-10-27最新完整关联回归202通过、2失败；两个失败分别为既有Seedance final-text QA fixture缺口与既有error-message匹配不一致，使用Git HEAD原`generation_execution`内存载入均复现同样失败，未修改工作树基线。新compiler/predicate定向75项通过，完整无付费clone grant→prepare→start→quota→strict reopen通过，真实Manifest仍82。

提交前stop fence发现其他窗口新增macro1080v3 accepted，strict reopen后累计27次（26 accepted/settled、1 known-no-effect，无video UNKNOWN），S05六次。旧26→27预备bound保留，新的有限单元为全片27→28、S05六→七、最多1次新video、retry0，9000CRD金额guard不增；旧音频/图像UNKNOWN不重试。`S05-repair-007`保存最终bound/inventory、clone、定向/关联日志及两个基线复现，round10独立审查未完成前不实际submit。学习评估no_candidate：此处为同一原attempt的运行故障证据与工程恢复，不把多个证据层计作独立媒体实验。
record_kind: media_experiment
topic_id: shizhen-S05-rider-exchange
learning_eligibility: needs_identity
evidence_index_version: "1"
---

# Shizhen S05 Rider Exchange

## Known No-effect Recovery — Current

用户再次“那你继续修复啊”后，原006的具体原因已查明并完成真实恢复。Canonical请求1007字符末尾有LF；同一native submit/resource登记保存的实际`o.params.video_params.prompt`为1006字符，SHA精确等于原文移除末尾LF。Native `resolveSubmitContext`执行`trim()`；Git原Worker在admission前的exact params校验必定拒绝。原Worker+同一prompt本地复现`native request changed`，原HTTP/dispatch均0，空resource查询仅旁证。完整证据、自足content-addressed bundle及复现归`L/S05-repair-006/verified-original-pretransport-evidence.json`。

先在完整项目副本沿唯一committer验证成功，再经同一native reviewer的total9只读证据/操作审查（finding set为空），实际调用既有`reconcile_paid_provider_no_effect`追加纠正。真实Manifest82 strict reader PASS；006现在`failed`/paid`known_no_effect`，原UNKNOWN receipt `5f6ed151...` bytes原样保留，新corrective receipt `d85a5322fb9a8a7071595679e821d7cecbe51e56819f6cfb57085ee2fc2dbfb4`。原reservation已released、actual cost0，不重发、不补造dispatch、不重铸permit、不重置消费。证据及结果归`reconciliation-result.json`；这不是把旧post-media gate签PASS。

原R lineage仍24次视频提交尝试、S05六次。全部roots重开补查另纳入其他窗口两个macro调用，全片当前26次（25 accepted/settled+1 known-no-effect、video UNKNOWN0），实际各片是否合格仍各归原owner；本单元新video/image/audio调用0。证据归`all-roots-accounting-after-reconciliation.json`，不把历史验证副本重复计费。S03/S05-004声音UNKNOWN及人物图UNKNOWN保留。当前继续修复显式compiler version2的native边界空白适配，version1历史bytes冻结，现有QA/Goal不降级；007尚未start/submit，S06仍等S05真实媒体验收。下方UNKNOWN停点已被本节取代，保留历史。record后learning评估no_candidate：单次真实故障的追加proof，不自动采纳新模型经验。

## Unknown Submit Stop — Historical

### Read-only Recovery Evidence — 2026-10-27 05:38 UTC

用户再次要求继续后，实际只读检查native失败getter、controller、历史登记和浏览器缓存日志，没有再次submit、permit、image或audio调用。getter的message/reason均为`null`（`typeof null === 'object'`不是保留了Error对象），failure count为1，pending与pending commerce均0；缓存1000条console记录未找到已知发送前fence错误。消费明细入口未返回可核对记录，不能由页面余额推定扣费。

新发现同一target节点的native历史登记：submit ID `cb3052c5-62e4-495a-86a7-5faa682ba19c`、预分配resource ID `cb51f7ba-695b-4284-9b3f-32204d7786e0`，登记时间`1793067158322`ms，与006的`2026-10-27T02:12:38.390360Z` UNKNOWN receipt相符。它们仅为客户端预分配登记，不是sealed dispatch或平台接收证明。对该exact ID执行一次resource lookup，HTTP200/ret0但resources为空；不把空查询改写为known-no-effect、不补造dispatch、不释放reservation。仍缺本次平台明确未受理/发送前失败证据，或可验证实际effect及canonical恢复支持，因此保持UNKNOWN，而非开始007。

标准reader重新打开PASS，Manifest81 SHA仍为`82c92c39593d416a1996bdf8a86389ddb68cd6e1ae9e3bea3e3d94ed1f9aeb59`，与此前canonical query-only recovery完全相同，006仍`outcome_unknown`/paid`outcome_unknown`/video`submit_intent`。本轮新生成调用0；累计仍24次提交尝试、23known+1UNKNOWN，本次1280credits报价的实际扣费未结算。没有新MP4，S06及拼接/字幕/发布均未执行。证据索引与校验归`L/S05-repair-006/unknown-recovery-evidence-review.json`；本轮无软件行为修改，未重跑工程测试。record/learning评估`no_candidate`：同一UNKNOWN的追加只读proof layer不是独立实验；没有修改Skill/Policy/Gate。媒体/source相关提交仍受原成片认可后验证边界限制，未新增commit/push。

用户再次“继续”后，引用归属恢复已经实现并实际应用，旧“未修复登记”阻断已解除。新增 `unsubmitted_retarget_references.py` 沿唯一committer补回原exact source同角色拥有的五张动作/摄影图，保留三张固定身份母图、旧Project6、旧target、所有其他Project/Shot字段、native输入、完整QA/Goal、profile、预算和计数；`previous_supersession` 保留一次一跳Project7，reader和submit锁重开两者。原timing correction不冒用，原direct /5仍source+1；第二Project修订只是候选，不能脱离canonical correction获得submit资格。添加完整source hash匹配和同owner校验，不允许换脸、移除引用、改剧情、后继request后修订或无限链。exact replay零写入。

软件验证：当前精准81passed（1个既有刻意坏model warning）、关联qualification/public generated-video E2E/historical replay72passed；新fresh actual-state clone沿public committer应用成功并strict-reader重开，normal prepare与真实locked predecessor给出GENERATE_ONCE、9图、exact纯中文1007字符。原工程3轮+中文2轮total5保留，本次新恢复语义有据最多追加2轮到total7；实际native xhigh round6 finding set为空，未启动第7轮。真实root已同样恢复到Project7 `d6c388d9063d27c64f67d255161696823b63234f751b55577ce79e5eaa6249e0`，Manifest77 strict reader PASS。完整回归未跑；whole-repository architecture49基线findings无本task路径，policy9个unrelated unmapped未隐藏，不冒充full Harness。证明及source snapshots归 `S05-repair-006/owner-recovery-*.json`、`owner-focused-tests.txt`、`owner-related-tests.txt`。

本次已经实际进入正常提交流程：fresh platform检查仍23个完成视频、target空；本次quote1280credits、内部1500CRD/call与S05累计9000CRD只为guard。normal exact preview/lint全通过（9图、1007中文原文、原五句、同轴五镜/完整收手、KEEP/1080p/20s），实际start、quota5→6、预算/reservation `shizhen-S05-reservation-006`、durable intent、新one-use permit均经原owners完成。第006次 `submit_once` 返回 `video_provider_outcome_unknown`，已停止，没有重发或remint。

当前canonical attempt006 `outcome_unknown`、paid phase `outcome_unknown`、video phase `submit_intent`；标准reader仍PASS。没有sealed Jimeng dispatch/resource ID，亦无exact新MP4。只读平台回查：target节点failed、resource ID为null、acceptedResourceIds空；同scoped画布仍23个status1000视频资源。该观察不证明没有扣费/没有脱离画布的effect，不能改写为known_no_effect。显式沿 `VideoGenerationService.recover_jimeng_unknown_once` 调用唯一恢复owner一次，返回“Jimeng has no sealed resource to query; keep UNKNOWN.”；Manifest SHA核对未变，new submits/permits均0。未裸调Provider、补造dispatch、退reservation、删除节点或另开root。

真实累计为24次视频提交尝试：23次结果已知，1次新UNKNOWN；S05共6次尝试，旧S03/S05-004音频UNKNOWN及人物制图UNKNOWN全保留。原生报价1280credits；本次实际生成数/扣费未确认，reservation保留，不得将内部1500或9000说成价格。新image/audio调用0。`attempt-outcome-receipt.json`、`canonical-unknown-recovery.json`、`unknown-platform-observation.json`为当前唯一scope事实；旧metadata阻断receipt原样保留作历史。

S05-006 post-media gate为NOT_EVALUATED（NO_EXACT_MP4_OUTCOME_UNKNOWN）；无新MP4故不调用旧媒体冒充本次video-analysis，也未写媒体QA PASS。S05-005原caption FAIL等评价不变，S06未submit、不拼接/字幕/发布。当前恢复条件是可核验的本次effect/未接受证据及原canonical recovery，绝非再次“继续”或重复付款。source与媒体相关记录仍按用户要求待成片认可后的完整验证及owned commit/push；仅先前上层规则已推送。当前Goal未完成，停止所有新付费attempt，不把UNKNOWN当重试理由。record后learning评估no_candidate：一次未获输出的异常及同链软件验证，未隔离模型变量，不能得出中文消除字幕/身份保持或可重试的模型经验。

## Reference Owner Admission Block — Historical

用户已明确解除生图/视频暂停，要求继续视频；人物参考入口又明确写为 `referces/`，AGENTS规则提交 `d9bba1d07b69a6b0c896a1c9d62c36955954820a` 已push并核验。新林序正面/右侧45度与骑手正面已实际查看、核对原generation manifest SHA并经正常Registry/Project接入，不能继续沿用“找不到固定参考”的旧暂停状态。原有参考制图UNKNOWN均保留、不重试。

本次没有生成新视频。S05已正常封存Project6、Shot6、QA与含9图的authored target，并有一个已确认空的Canvas节点 `node_aw397g7bnb`；真实平台23个视频资源全部完成，历史video仍23/S05五次。新有限单元23→24、own5→6、内部S05 guard7500→9000CRD保留历史，本次原生报价1280credits，不是已扣费。尚未创建006 video request/reservation/permit/submit，无新增video/image/audio调用。

当前真实阻断是我登记时把Character.reference_asset_ids替换为三张固定身份图，未保留仍被director row选择的五张旧动作/摄影参考归属；`canvas_feedback_context` 在正常prepare直接拒绝“character reference needs one exact selected owner”。标准reader重开Project6通过、Manifest74，不能把可读取说成可生成。原六图实际输入保留、新三图仅追加，纯中文1007字草稿与全五句仍在，但无compiled preview或MP4。证据归 `S05-repair-006/reference-owner-blocker.json`，旧未提交草稿归 `pre-identity-draft/`；旧Project、FAIL、receipt和UNKNOWN不覆盖。

Project6和/5 target已经封存，target锁定exact Project6；不能覆盖旧Character/Project文件，也不能直接把Project7替入、裸发Provider或新root归零。既有未提交timing-only correction不适用于reference ownership，未冒用该入口。当前停止paid attempt；剩余工作是先沿唯一committer实现/验证保留旧封存目标与计数的最小未提交引用归属恢复，然后重新正常prepare、preview/new permit并实际生成。本段不声明该恢复已实现，也不放宽任何锁。S06继续受前序FAIL与本准入缺口阻断。

唐姐已有参考已实际查看并将原bytes集中到 `referces/shizhen/tang-jie/identity-20261027/01-work-medium.png`，明确低扎发、米色袖、灰蓝围裙、记货笔及普通工作神态；来源、SHA和不继承的构图/背景归同目录source-evidence，零新增生图，不伪称人类接受。当前不拼接、不后期字幕、不发布。代码/本次媒体相关记录仍未commit，按原用户成片认可后完整验证的边界保留；仅两条上层规则已独立提交推送。record后learning评估no_candidate：静态引用准备与一次准入登记失败，不是独立受控媒体验证。

## Generation Paused And Identity Audit — Historical

用户最新“先别生成了,主人公的referces都没有固定我发现...”，当前暂停所有视频/图像生成。真实video累计23、S05共5，无新video UNKNOWN；当前两次audio UNKNOWN为旧S03与S05-004，均保留不重试。006只有离线prospective Project6和923字中文稿，没有canonical authoring/new node/budget reservation/permit/submit，S05实际Project仍5；S06仍未提交。

用户指出的问题已由canonical Character与实际request核对：林序身份引用逐镜更换，没有固定一套各镜共同的身份母图。S05近景的实际imagegen输入是S05-002生成帧；S06近景再从该S05近景派生。S05双人入口制图曾绑定S01原图，但S05/S06最终绑定均未直接保留S01母图，不能把间接来源误称共同身份锚点。实际查看S01、S03、S05、S06参考图，可见面貌比例和发量轮廓变化；不作生物识别判断，也不因服装相似、SHA正确或单段sampled identity PASS宣布跨镜同脸合格。审计与暂停计数见 `R/live-action-regeneration-01/identity-reference-audit/README.md`、`canonical-reference-inventory.json`、`generation-hold.json`。下一步是先明确同一林序身份母图、逐张排除漂移，再考虑恢复生成；本段不自动解除用户暂停，不追加生成。

此前004修复003裁脸/收手后出现16.55秒动作中态跳切，用户明确拒绝；005同态切入并在末镜完成看饭/抬手/指示/落手/回看，抽帧证据支持动作阶段修复，但仍烧入模型对白字幕，整体FAIL，声音/表演NOT_EVALUATED。005原片SHA `89497e155e872792dece88eb44db1e165bf44e0213bf04dc6c43dffe6c34b02b`，004为 `34cfb8fdc2177657670b236acd7c63e0c72ebb2e856d584cfce7ffacf0ad7772`；均1920×1080/481帧/native VFR/AAC，exact MCP/metadata与raw delivery receipt保留在各repair目录。两次新增视频quote各1280credits，实际结算待确认；新增收手参考图费用未暴露，004一次音频分析transport_unknown，不重试。没有拼接、后期字幕或发布。

实际005 native正文5734字符，英文模板、重复动作/表演字段和五轮脚本式对白同时存在。没有独立字幕开关，字幕已烧进原生视频；全部“字幕”文字均是禁止要求。因此确认输入质量有问题，但不能证明某一句、引号、英文或长度单独导致字幕。用户要求纯中文已写入AGENTS并单独commit/push `3e0ae8e360a6e5f27cc6cd5e038c07a00d95cc98`；未夹带并行AGENTS拼接规则。现有HEAD基线14185bytes已超14000byte文档预算，规则测试33pass/1fail与staged Harness拒绝未分离unstaged AGENTS hunk的限制均据实记录，不能宣称全PASS。

纯中文真实正文入口已做最小代码/QA mapping候选，旧无mapping行为不变，沿已有final-text scalar验证、recipe/compiler/committer；Jimeng相关286pass、关联84pass、新增输入/guard11pass，非完整验证。native工程review round4指出qualification调用漏传current intent（JCN-001），Parent已确认并作零Provider副作用的局部修复与回归，最终新增12项回归通过，native round5 remaining findings为空；旧84关联在最后一行callsite修复前，修复关联56pass/1个缺少prompt delta的测试夹具失败，经修正夹具后的12项确认，不冒充全量当前snapshot PASS。详情归006 `engineering-verification.json`。所有生产源码/媒体仍按成片优先待用户认可后的完整验证与owned commit/push。当前只已推送纯中文规则，未发布媒体。本record后learning评估no_candidate：同一失败修复链、未隔离字幕成因、未接受身份一致性，不能推导模型或prompt普遍规律。

## Multi-Shot Repair — Historical 003

用户实际看过002后明确“首先我没看出来很焦急,面部表情控制看不到,然后这个镜头不应该是一镜到底”。002当前不是等待认可，而是表演可读性与一镜到底被拒绝。最初一次调用review默认exact replay，返回旧EVIDENCE_GAP而没有执行新judge；后已用既有 `repair_evidence=True` 对同SHA正式追加新 `coverage/performance=FAIL`，旧评价与采样PASS均保留。canonical新证据见 `S05-repair-003/predecessor-rejection-observation-repaired.json`，不得只凭旁边手写FAIL gate当作已写入Production。

003改为双人建立、林序近景纠正、骑手中近景普通疑惑、林序更紧近景拿细节作证并承接画外反问、含台面/左手的中近景指饭收回。五个摄影镜头在一次2.5/20秒生成中，原五句逐字且无台词时间戳；最后一句骑手画外说，让观众直接看到林序当场受阻的脸部反应。镜头改变不复位持物、站位或情绪，原S04认可入口保持。

新生成近景参考3次、仅选05 `a97528f842d4f153bd64de7d1e871e0bd702bd101533749292d898629b213a44`；一张后段图换左右手，修复图又指向手机，均保留为REJECTED并排除，未继续无限重试。实际模型5图=原4exact bindings+1焦急近景；新图只控制同一林序的脸、摄影和表演，原04正确左手横身指饭/右手手机继续控制动作。图像真实费用未暴露。

既有 `/5` 显式封存 revised raw IDs（action/coverage/performance/sound/space-camera）和新增图ID，复用 `/4` QA字段边界，旧IDs/proof/stage/owner与完整Goal保留；Project/Shot3、林序仅追加近景reference及Registry5图已由committer实际接入。原固定双人中景和旧想笑QA不再冒充用户不可变要求；旧目标/receipt不覆盖。45精准、54关联用例通过；原native reviewer第2轮指出canonical拒绝未追加，第3轮核验explicit evidence repair、独立prepare和predecessor closure后剩余findings为空。原3轮历史不重置，见 `S05-repair-003/multishot-independent-review.json`。

全部20个已知视频及平台完成资源在提交前重验，新target为空；003经正常adapter、preview、budget/quota2→3、durable intent及新permit提交，历史20→21，自动retry0。平台本次quote1280credits，内部budget3000→4500CRD仅guard，实际扣费待结算。003已fetch并按原bytes交付 `outputs/shizhen-episode01/失帧-第一集-S05-Seedance2.5-003-多镜近景重做-原声-20秒.mp4`，SHA `760c14af792e466e88a9ac427e1ee2abb3c47ff5f0de35ec4fa183c654a5b801`，67,339,665bytes，1920×1080，video20.016667秒/481帧、container20.065秒、原生VFR `28860/1201`、AAC原声；是单段原片审看而非24CFR累计master。

exact project-local MCP、80张4fps采样及last decoded frame已实际核验：确实出现五段摄影画面，约3.25秒切林序近景、7.5秒骑手侧、11.25秒更紧林序脸、16.5秒手势镜。MCP默认0.4 scene detector却只返回1scene，不能用该启发式推翻肉眼切镜证据或签PASS。新近景可见眉间压力/抬眼/嘴部张力，但情绪与低声焦急尚无新片人工接受。base/small Whisper都得到五轮次序，对红围裙均有不同同音字，末尾语气词也不一致；没有把ASR当逐字/语气/口型PASS，未新调用远程audio understanding。

已发现新的明确不足：末段实际裁掉林序脸，末帧左臂仍抬在身前、手指仅弯曲，未达到封存的完整收手/回看末态。canonical action/coverage FAIL，performance/story/sound NOT_EVALUATED，身份/可见持物空间/摄影质感只有采样范围PASS。`S05-repair-003/post-media-gate-003.json` 和 `raw-delivery-receipt.json` 明确这是未过关原声审看片，未声称修复成功。当前一次call有限单元已用尽，不自动重试、不拼接/字幕/S06/发布，旧S03音频UNKNOWN仍不重试。用户听看后的反馈与后续有据有限修复仍是剩余工作；按成片优先规则尚无owned commit/push。本次record后learning评估no_candidate：未获新片人类接受，且完整目标仍FAIL，不从三次生成或测试数推导普遍模型结论。

## Historical Repair 002 — 2026-10-27

下方首次接收时的“等待exact视频”及“想笑未笑”是历史草稿，已被实际结果和用户表演要求取代。S05-001 已取回并交付，exact SHA `2155df692f9ae6fd2e72198f74a4dad53a33d8e70709c7505d7858e6d7231d31`；用户明确拒绝约12秒笑意与全段主角语气，canonical observation 已记录 performance/sound FAIL，旧片未获接受。

用户最终保留 Seedance2.5、20秒，并要求“焦急的,想证明自己”和余惊未消、压低声音急着求证同时存在。原 native prompt 的“想笑”出现6次，且一处放进 throughout 人物表情；原对白未逐句明确这种发声方式。这是 exact 输入与用户反馈支持的诊断，尚非隔离变量 A/B 的模型因果结论。

同 root/task 的 attempt002 已由平台接收：原4张 exact 图、原5句、20秒、1080p、持物/构图不变，仅改分阶段表情与发声文字。林序短促纠正、重读“刚才”，再更急地把“热饭”“红围裙”当证据；末句反问后卡气、左手指饭收回，下颌和嘴角仍紧。骑手保持普通疑惑。完整文本与绑定见 `R/live-action-regeneration-01/S05-repair-002/native-prompt.txt`、`prepare.json` 和 `prompt-lint.json`，R为本次 run。

修复沿原 authored retarget `/5` 扩展同型号 exact-reference R2V 窄分支，未新建执行链；canonical supersession、Project/Shot revision2、budget extension、quota1→2、new reservation/one-use permit 已实际通过。针对性测试36 passed，独立 native reviewer round1 findings为空，冻结 source hashes 与 review packet 见 `S05-repair-002/same-model-repair-independent-review.json`；不是媒体质量PASS。内部 guard1500→3000CRD，平台本次quote1280credits，实际扣费待结算。

全部旧root与平台19个已完成资源在POST前重新核验；本次新增1，历史总数19→20、S05 own1→2、自动retry0。旧S03远程音频UNKNOWN未重试。修复已实际fetch并交付原bytes：`outputs/shizhen-episode01/失帧-第一集-S05-Seedance2.5-002-焦急求证重做-原声-20秒.mp4`，SHA `67fac2bf925127b257486cf3f359aac56155c038b709e5d4b2da6b0b2a1f1ed0`，60,149,057bytes，1920×1080、video20.016667秒/481帧、container20.065秒，原生VFR `28860/1201`，AAC原声；这是一镜原片审看，不是24CFR累计master。

project-local MCP 已显式分析exact MP4；80张4fps samples和12/13/14秒原分辨率画面已查看，局部未见明显笑开，不能据此签全段焦急语气PASS。local Whisper得到原五轮次序，红围裙仍为同音识别不确定，未用ASR替代听音。左手指饭约16.25–17.75秒、18.25秒前收回，末句ASR约12.32–13.44秒；中间呼吸/反应是否自然保持未验。Gate/action/performance/story/sound/coverage均 NOT_EVALUATED，不推进下一镜；身份、空间持物和摄影质感只有采样可见范围内的PASS。证据与独立准入核对均不证明人工认可。

关联 guard 测试另54 passed，详见 `S05-repair-002/bounded-engineering-verification.json`，无 full suite/Harness completion receipt。当前等待用户对新片原声语气的认可，不拼接、不做字幕、不提交S06、不发布；按成片优先规则保留当前任务改动待认可后的完整验证及owned commit/push。record后 learning 评估 `no_candidate`：修复尚无人类接受，不能将prompt诊断或准入测试升级为普遍模型经验。

## Scope And Accepted Entry

用户“过关,开始shot5”接受S04原声接点修正版 `e40d40218902300f5bde4c9365fbc5a09a06e5e893f97378f1f917b182125fa4`。实际末帧236@24fps已提取并查看：林序看向右侧骑手，右手手机垂右髋、左手自由；瓶直立、扫码枪卧瓶左、饭团在白纸。S05只执行原剧本五轮与指饭收手，不扩展至店长出场或S06、不发布。当前用户已认可的是S04，不是尚未取回的S05。旧S04 raw FAIL、assembly crop warning/NOT_EVALUATED和S03音频UNKNOWN仍保留。

## Complete Event And Selected Route

原文五轮依次为骑手“你找老板？后边呢。”、林序“不是。刚才这个小伙子。”、骑手“什么小伙子？”、林序“给我热饭那个。红围裙。”、骑手“你不是自己热的？”。骑手左掌稳托独立封闭餐盒，右手扣头盔，听到小伙子才停扣、看空柜台再看林序。林序右手手机全程垂髋，结尾用左手短指白纸上的饭团再收回，想笑未笑。头盔松带与餐盒各有真实支撑，不拿错三角饭团。

20秒容纳约四十字五轮、相互倾听、托稳餐盒、停扣、看柜台和短指收手。选现有Jimeng / Seedance2.5 / multimodal /1080p/native audio KEEP；不是为10秒的软件限制换版本，也不挤压2.0的15秒上限。沿原S05顾客侧稳定双人中景，同时看认知相反的听说反应；这个机位来自叙事和原coverage，不由时长默认一镜到底。原CG表现已按用户持续真人要求替换，原剧情与逐字对白不变、不加逐句时间戳。

## Exact Reference And Preflight Evidence

L/S05实际绑定4图：1是S04 actual terminal的林序身份/低持手机；2是新双人开场、同白头盔黑雨衣黑黄背包骑手的脸与造型；3是右手停扣/左掌托盒的中态；4是林序左手指饭团、右手手机仍垂髋的后段状态。2/3/4来自image_gen，已逐张实际查看；S01三人图仅用于制图时保留原骑手衣物，不进视频输入，避免旧店员和旧持物姿态回流。

本轮image调用4次、选用3张生成图。04-v1食指偏向手机，known outcome下封存一次有界gesture repair，04-v2纠正指示目标和眼神，保留原图且未盲重试UNKNOWN。费用未暴露。所有原PNG、完整prompt、input/output SHA与尺寸见 `S05/references/*.source.json`、`reference-evidence.json`。

封存前依次保留v1/v2/v3 intent及旧preview：v2把简写“黑有线枪”明确为“黑色有线扫码枪”；v3移除已消失店员的旧围裙材质，并把林序表演触发改为先询问、听否认后才不服。旧sealed数据不覆盖，时长、原话、参考与QA不变。最终 `prepare-v3.json` / `native-prompt-v3.txt`4083字符，四图顺序、五句原话、无台词时间戳、两人持物与支撑、KEEP、20秒/benefit/output和1080p lint全通过；2.5当前渠道上限15000，未套用2.0的4000。

## Real Submission And Finite Bounds

canonical `R/trial-S05-v1`，task `shizhen-S05-qualification`，attempt `shizhen-S05-qualification-attempt-001`。全部roots严格盘点得到此前18个唯一paid video，无video UNKNOWN；平台18个旧video资源均完成，新目标node为空，账号/project exact匹配。经现有ProductionStateCommitter、selected adapter、preview、budget/quota、durable intent和新one-use permit提交1次并被接收。历史消费不归零，合并有限上限18→19，自动resample/retry0。

native quote **1280credits**，1500CRD是内部每call guard，实际扣费待结算；图片费用未暴露，旧S03音频UNKNOWN未重试。本轮未新调远程声音理解。实际bindings、prompt SHA、原话、全计数归 `S05/actual-binding-receipt.json`；原平台/历史检查归 `platform-preflight.json`与`all-roots-before-submit.json`。

## Verification And Current Limit

当前已完成GenerationIntent模型校验、canonical reader/bootstrap/prepare/start、真实账户/平台只读核验和submit被接收；此处仍等待exact视频，不能把这些签成电影质量PASS。新run-local脚本已compileall，未扩建共享源码，未启动长全片/工程审核拖延交片。取回后须explicit project-local MCP，并区分逐字对白/口型、持物、自然度和用户接受；ASR或音轨存在不证明实际听感。

使用record-ai-video-session记录本稳定接收检查点，distill评估no_candidate：本次新单臂生成尚无媒体结果，参考修复也不是独立视频实验。S04原适配源码修改已通过此前277个关联用例但尚未完成完整工程验证；保留其他窗口dirty工作，不夹带commit。当前publication NOT_PUBLISHED，S05人工接受/媒体Gate NOT_EVALUATED。
