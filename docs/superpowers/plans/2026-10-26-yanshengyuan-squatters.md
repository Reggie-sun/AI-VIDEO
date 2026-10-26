# Yanshengyuan Squatters Film Production Plan

## Human Review Update — 2026-10-26

用户明确认可6.5秒720p诊断片的画面和声音，绑定 `cumulative-review-003` MP4 SHA-256 `0dc52da4df8211f56687e4ca7d27dab6aa014971c08ee06c3d532d52a8ce3e6a`。本节取代下文“正常速度人审未发生”的当前解释；后续保留这版已认可效果。该认可不扩大为完整广告验收，也不抹去MC-01包装比对、raw Gate FAIL与消费历史。广告固定720p规则见 `16390fd`；18次/A12上限已耗尽，未获新增次数授权前不得submit。精确人审范围与证据见主记录 `Human Review Update`。

**Goal:** 将用户已确认的《斑点钉子户》做成约50秒、40–60秒范围内的单条颜生源广告，以人物主动护理、镜中租客的反应及同份续住合同回扣形成因果。

**Scope:** 只推进本片，使用 Jimeng / Seedance 2.0 VIP、9:16；前三秒商品可见，完整品名入声，真实商品落版及“栖澜百货商贸”低存在感慢水印。旧全城警报稿已被用户否决，不作为新剧情基础。

**Authority:** 用户对上一轮完整五段故事回复“可以”。50秒为导演排布：S01 10s、S02 8s、S03 10s、S04 10s、S05 8s、真实产品卡4s。实际成片按动作与完整对白剪辑，最终保持40–60秒。

**Owners:** 新输入及媒体仅写 `runs/yanshengyuan-three-concepts-seedance20-20261025-001/squatters-001/`；creative writer 独占 `creative/`，Parent独占实际Provider调用、预算及交付；独立概念复核只读。保留其他窗口所有dirty/index内容。

## Story And Continuity

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

用户40–60秒、夸张、前三秒产品、完整品名、低存在感慢水印均映射到具体段落或全片处理；人物主动决定与反派状态/合同回扣明确。新路线未获得媒体质量PASS；镜面/微缩角色可读性及音义通道是首要真实验证项。旧失败和UNKNOWN保持独立，预算不重置，无新增Provider或renderer。
