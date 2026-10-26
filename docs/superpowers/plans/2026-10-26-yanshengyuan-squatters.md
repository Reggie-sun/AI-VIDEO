# Yanshengyuan Squatters Film Production Plan

## Human Review Update — 2026-10-26

用户明确认可6.5秒720p诊断片的画面和声音，绑定 `cumulative-review-003` MP4 SHA-256 `0dc52da4df8211f56687e4ca7d27dab6aa014971c08ee06c3d532d52a8ce3e6a`。本节取代下文“正常速度人审未发生”的当前解释；后续保留这版已认可效果。该认可不扩大为完整广告验收，也不抹去MC-01包装比对、raw Gate FAIL与消费历史。广告固定720p规则见 `16390fd`；18次/A12上限已耗尽，未获新增次数授权前不得submit。精确人审范围与证据见主记录 `Human Review Update`。

**Goal:** 将用户已确认的《斑点钉子户》做成约50秒、40–60秒范围内的单条颜生源广告，以人物主动护理、镜中租客的反应及同份续住合同回扣形成因果。

**Scope:** 只推进本片，使用 Jimeng / Seedance 2.0 VIP、9:16；前三秒商品可见，完整品名入声，真实商品落版及“栖澜百货商贸”低存在感慢水印。旧全城警报稿已被用户否决，不作为新剧情基础。

**Authority:** 用户对上一轮完整五段故事回复“可以”。50秒为导演排布：S01 10s、S02 8s、S03 10s、S04 10s、S05 8s、真实产品卡4s。实际成片按动作与完整对白剪辑，最终保持40–60秒。

**Owners:** 新输入及媒体仅写 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/squatters-001/`；creative writer 独占 `creative/`，Parent独占实际Provider调用、预算及交付；独立概念复核只读。保留其他窗口所有dirty/index内容。

## Story And Continuity

### Active Hyperbole Rebuild — 2026-10-26

用户否定旧15秒片的动态附着与钩子强度，明确要求“重新做,做浮夸的,人物语气要浮夸,表情也是”。
当前执行转到 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/hyperbole-001/`，旧稿与FAIL/NE不覆盖。
暂排44秒：H01十秒建立卧室、前三秒脸颊三层违建弹起、女主浮夸语气表情与明确转头；H02/H03各15秒
让完整品名、主动使用、多次护理与租客收拾/合同回扣成立；真实产品卡4秒。产品前三秒可辨、水印与truth不变。
这是新创作授权内的Director排布，不把Agent选择记成用户逐镜指定；Seedance 2.0 VIP保持原选，不自动换2.5。

先完成H01，实测房屋展开、女主爆发喜剧表演与房屋随脸颊移动/透视/遮挡，再交exact带水印原速审片。
逐项Gate非全PASS仍不提交下一单元；不能静态营地、轻微微笑、冻结头部或静帧PASS替代浮夸与动态要求。
Parent负责新scene图、native空节点、真实付费和最终审片；creative/runtime/P4 writer各自只写新目录归属。
保留累计14个durable paid槽位（A8/B3/C3，含一次known-no-effect），旧9次历史另计；新内部有限单元
最多3个首次及1个有据repair，task18/9000CRD与单次500CRD不重置，A仅有据分配至12/6000CRD。
当前仅H01首次一次获执行，auto retry0，unknown停；新90分钟窗口沿实际clock及旧hash封存，不改原窗口。
出片所需最小prepare/render/检查先行，用户效果认可后再完成适用工程验证与owned-path commit/push。

- S01：夜间卧室梳妆台、真实前景产品、镜内同侧面颊斑点区域的微缩营地同框。两个明显幻想玩偶租客已搭营，女主看见后问“你们还打算住多久？”。镜外皮肤保持自然，避免将租客拍成与皮肤无关的镜中住户。
- S02：同一营地展开超长续住合同，女主看合同后明确回应“还想一直住？那我就天天认真护理。”并主动拿瓶。每个生成单元只有一个主要说话人。
- S03：商品操作/质地与租客识别精华形成直接关系，完整说“颜生源美白祛斑精华液？她这回来真的！”。画外声音若选用须沿当前typed voice route明确表达，不混成多人对话。旧手部镜头仅在视觉用途及原声/替换路线均获证时复用，否则新制对应镜头。
- S04：多次日常护理以时间跳切表达，租客逐步慌乱收拾铺盖，保留一个抱行李未离开的人。不能拿瓶即搬光、一滴见效、即刻美白，不宣称见效天数或百分比。
- S05：同一未离开租客举开场那份长合同试图续住；女主放瓶说“不续了”。镜内举合同即可，不要求玩偶穿镜向真人递物。商品卡收束“淡斑焕亮、匀净肤色”。

独立概念检查 SC-01/02/03 已由 Parent采纳：对应面颊斑点、可见主动决定、同租客/合同/行李状态连续。该文字复核不是媒体验收。

## Contract Surfaces

Project / Registry / authoring revision / mutable lifecycle 经当前 `ProductionStateCommitter`；生成走selected adapter、router/compiler、exact preview、预算、one-use permit及 `VideoGenerationService`。首尾帧用于确有起止约束的镜头；连续镜取前序实际accepted末态，换景按语义职责选择soft reference，禁止把镜头类型强行统一。全片剪辑/帧/样本/混音只由 `CompositionSpec → ResolvedTimeline → HyperFrames` 决定。

旧video task提交已使用10次（A4/B3/C3），task前另有9次历史；新片最多五个首次native提交，每镜一次、自动重试0。Parent在首个新POST前封存有限重分配：保留task18次/9000 CRD总内部ceiling，A上限由6至9次/4500 CRD，B/C冻结不新增；所有旧计数与UNKNOWN原样保存。单次500 CRD为已有内部upper bound，不能当实际报价或收费。实际金额/积分按receipt汇报，未结算注明待核账。

## Milestones

### 1. Freeze Story And Reference Inputs

在新creative目录保存逐字用户反馈、确认范围、Director v4、FinalOutputContract、goal binding和必要rich intent。以内置imagegen制作并实际查看首镜参考，明确真人/倒影/镜内玩偶/商品各自位置；只有清楚可读后接入标准image import。首镜仅一主动作与一句女主对白，避免十秒里同时搭营、展合同、取精华及搬家。

验证：Director/goal/rich intent局部校验、逐项人工比对原始约束；actual input尺寸/SHA及引用职责。使用现有run-local实现与canonical seam，只有实际输入证明缺能力时才做出片必需修正。

### 2. Execute And Review Sequential Shots

Parent核验全局真实计数和既有outcome、新native空节点及exact profile。提交前报告起止状态/参考handoff/轴线动作机位/prompt适配与lint；每Shot MP4落盘后显式video-analysis，按封存要求及前序实际状态裁决。只有全PASS才下一Shot submit。

音义路径使用现有qualified operator。新source/PCM才可建立新的一次性unit；task-local transport若为排障而注入，只能记录异常class、阶段与elapsed，仍单POST、凭据经既定supplier、不写message/headers/body/key。旧A02及其他consumed UNKNOWN没有同源POST补证/重试权限。缺可靠声音证据时先补证，不因出片压力签PASS或越过barrier。

### 3. Edit And Deliver The Exact Film

保留完整对白和动作因果，按实际in/out点删除重复动作/停顿，接缝画面与声音分别检查；水印跨镜连续且移动约0.9px/s级。用真实商品PNG收束，原生成AI披露保留清楚。正常速度看听exact成片，另做独立只读创意审片，明确无法观察的范围。

验证：出片必要的P4 lint/render/probe、所有切点/原声/商品/文字核验及真实人审；技术通过不等于叙事/声音/Final Acceptance。用户认可效果后再做影响相称工程验证与owned-path commit/push，不提前扩全工程阻塞交片。稳定checkpoint更新既有主记录并评估learning，不将单次修复升级通用规则。

## Self Review

### Performance-Preserving Editorial Repair — 2026-10-26

新motion variant原片SHA `f11aad0d4164edc9b61306ee0e672fac513e6fb97a61bff0aa96e9c2eb6246ef` 的原生Gate仍FAIL：角色短暂复制、侧转时立面透视不足、后段裁瓶。用户已正常速度看听其10秒慢水印诊断片（SHA `035cb943dcbc24631888e1448bce4523a9265e17eb3a02e1bb44178819a7cec1`），明确接受“语气和表情都够浮夸”。此反馈锁定表演方向，不覆盖画面FAIL。

先做约6.5秒三段剪辑：原片2–4.5秒直接进入展开与反应；真实产品特写1.5秒遮掉坏转头，并用原声6–7.5秒形成Jcut；回到原片7.5–10秒的吐槽，构图去掉半截瓶且不伤主要表情。完整对白原声6–10秒、语气、重音和1x速度保留，不新生成。具体帧/样本、裁切和排序只归ResolvedTimeline。检查所有cut两侧声画及新encoded，商户水印跨三段缓慢连续，AI披露清楚一次；不能以隐藏坏区间声称原片所有运动附着PASS。必要时使用专业产品卡布局修复末尾半瓶，而不牺牲眼口表情。

新用途先独立核验并交用户审片，通过后才评估后镜。原始FAIL、既有paid/fetch/NE历史保留，不弃掉已认可表演重抽人物。后续约15+15+4秒，完整目标约40.5秒，仍在用户40–60秒范围；完整品名口播、使用/效果因果及结尾回扣继续归后段。此计划不授权绕过下一Shot自己的exact preview、预算、egress、permit或source-use barrier。

用户40–60秒、夸张、前三秒产品、完整品名、低存在感慢水印均映射到具体段落或全片处理；人物主动决定与反派状态/合同回扣明确。新路线未获得媒体质量PASS；镜面/微缩角色可读性及音义通道是首要真实验证项。旧失败和UNKNOWN保持独立，预算不重置，无新增Provider或renderer。

## Execution Checkpoint — 2026-10-26

S01原I2V终态20008/no artifact；一次有界4图R2V修复取得raw10秒，后段商品出画FAIL原样保留。P4只用前7秒，已由用户正常速度看听明确接受环境/反应/完整问句与口型；当前全片剪辑目标47秒。人审与原FAIL的精确身份见主记录Squatters节。

S02沿accepted7秒用途与真实rawframe167的qualification source proof接镜，不冒充Production accepted sequence或raw10PASS；SourceUse Gate只批准此用途。新8秒first-last-frame endpoint已实看封存：boss长合同与女主拿起同一瓶，原托盘空。截止此checkpoint S02尚未提交，当前task12/A6，续期窗口只允许后续S02–S05各1次，task18/A10/9000CRD总体上限不增加、零自动重试。


## S02 Recovery Checkpoint — 2026-10-26

S02端点现都720×1280，实际r3编译3767/4000 UTF16。唯一首次canonical submit在参考上传阶段FAILED/known_no_effect，无generation dispatch/MP4，reservation释放actualcost0；旧attempt/receipt/permit保留，保守task durable paid槽位13/A7，native accepted generation仍12/A6。两张exact参考后来分别确认上传commit，已封存hash/profile/诊断证据及严格本地复用transport，无隐式重传或替换。当前只实施一次同Project/task/Shot successor的canonical no-effect recovery与quota1→2，不新建trial来隐藏失败；尚未恢复submit，不宣称S02通过。后续先显式媒体Gate，再交7+8秒接缝审片，最后推进S03。磁盘缓存清理已按用户仅pip的范围完成，原片/模型/已安装依赖保留。

恢复已在同Project/task/Shot完成唯一successor submit/fetch，exact raw SHA `936aa6ab66e1492e7adec8eec30823a21ef9509ffeb5dc138c0863af5d8af2b3`。旧失败与quota1→2历史保留；durable槽位14/A8，native accepted generation13/A7。新显式MCP Gate视觉五项PASS、performance/sound NE，S03仍禁止提交；现在先做约15秒带慢水印DIAGNOSTIC接缝审片，S02双AI标识沿P4清楚整理，S01已认可前7不变。

## Active Editorial Revision — 2026-10-26

本节按最新用户指令取代旧6.5秒商品卡方案。Parent接回builder与source-use ownership，原003不执行。新004封存A源2–4秒、B源4–4.5秒租客近景（3倍/−1500/−1650，排除女主口形）承接原声7–7.5秒“不是”、C源7.5–10秒质问，计划5秒。首尾静态已查，actual MP4与MCP/人审尚待执行；raw FAIL、r6拒绝和局部表演认可不变。独立concept reviewer `/root/opener_concept_check`/`reviewer_high` 的OC-01确认：旧5+15+15+4仅39秒；改为5+15+15+6暂排41秒，真实剪辑后仍须40–60秒。B必须连续正面租客，不定格、重复动作或硬插商品卡；后段产品特写由主动拿瓶护理引出。预算paid16/A10/B3/C3与18/A12上限不变，无新remote调用。

## Reaction Cut Feedback — 2026-10-26

r8半秒反切被用户明确拒绝。新006/r10改A1.5秒+B1秒+C2.5秒，原声与r8解码逐样本相同；视听节奏尚待该版原速人审，不能以时长变长或技术PASS关闭拒绝。r9仅准备失败无MP4，保留；r10用原r8 canonical mix经标准音频导入/Registry，未改共享REPLACE guard。全片41秒计划不变，后镜submit关闭，预算和raw FAIL不变。

## Native Closeup And Explicit 720p — 2026-10-26

最新r10模糊拒绝优先于上节待审状态。用户进一步明确720即可；Parent自行提高1080的准备没有submit或付费，经not_submitted evaluation及canonical close关闭并保留历史。当前仅执行 `hyperbole-001/sharp-repair-720-001/` 的720p/15秒五图R2V：原生清晰租客近景→中景续租合同→浮夸挑眉/主动拿瓶/完整品名→手部一滴护理。近景前合同藏起，中景才展开，避免插回旧C时合同跳状态；旧“不是”仅用原声，raw7.5–10正面段保留去半瓶构图。完整预算2.5旧A+15新素材+2.5旧C+15H03+7真实商品=42秒，实际剪后仍40–60秒。

新request `bd450e850f85fd7a3c89443ae6e5b51e252369f462302866232f7753f2c27f8b` 已accepted，3751/4000 UTF16，native只读报价210积分。paid17/A11/B3/C3，18/A12下剩1；总预算与单次上界不增加，实扣待结算。当前新媒体未fetch/未验收，先exact MCP Gate及累计连续版原速看听；H03禁止提前submit。获准后续H03仍须多次护理与租客收拾、同合同“不续了”回扣，不虚构见效天数或一滴即白。共享renderer旧修复与其他窗口dirty保留，用户效果认可后才完成适用验证及owned-path commit/push。

## Exhausted Bounded Repair — 2026-10-26

720p15秒已fetch并因合同/持物/镜像不一致封存FAIL。最后1次在同一失败主体分组内改25秒720pSeedance2.5完整主体修复（合同→拿瓶/完整品名→护理→晨夜日常护理→收椅/卷回合同→不续了），非在FAIL后另开H03；30秒报价600超500单次上界未执行，25秒报价500。实际request `43a9ff8d33baa7fe9c5e6a43573d387e35ae55c9b89ade743a75f00eddbeaa9d` accepted/fetched，source SHA `9b1b6c987463bfface25c0464218924079314b1deedb3efb6bfe3559ccb91880`。MCP和独立抽帧复核仍发现瓶签10ml/品名异常；正常速度声音/口型及肤色纹理保留NE，raw25也canonical封存FAIL。

实际6.5秒720p累计诊断片已通过P4编码并显式MCP检查，macro清晰且嘴出画、原不是/问句保留，旧C无半瓶；但MC-01确认A段包装错误，故整体仍FAIL。透明真实产品PNG局部覆盖的task-local尝试未满足当前canonical预览/AdCreativePlan合同，r4–r7无新片、无guard弱化；不能执行当前builder冒充已解决。已知错误诊断副本明确命名“瓶签错误未通过”，正常速度人审未发生。

实扫当前paid18/A12/B3/C3，accepted17/known_no_effect1，上限18/A12耗尽；本轮报价710积分，实际结算未知，1080零submit。当前全片40–60秒未完成、未发布、未验收；下一动作不得再submit或重置计数，须先解决正确包装/声画及支持能力或明确新的授权边界。记录与精确证据见主记录 `Final Bounded Media Results And Blocker`，receipt清单 `hyperbole-001/body-repair-25s720-001/final-budget-readback.json`。未commit/push，其他窗口dirty保留，learning=no_candidate。
