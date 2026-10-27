---
record_kind: session_summary
topic_id: shizhen-macro-opening-reference-preparation
learning_eligibility: ineligible
---

# Shizhen Macro Reference Preparation

Date: 2026-10-27

> **Current Update:** 用户已明确认可720p试片02并要求同方案1080p，本轮1080p版03已真实生成、可播放。新片约4.5–5.5秒出现基线没有的叠化，已标注新片未通过项，待用户审看；旧AI意见与720p用户认可分别保留。另按用户指令改为Seedance2.0默认1080p，2.5保持480p先审。未提交下一Shot、未改B6或签Production验收。

## Initial Scope And Result

用户说明referces角色图已存在后，直接复用character-packs-20261027中的董文慧身份底图，不重新造脸或扩已有视角；罗敏、高峥延续既有雨站原片。不改六镜剧情、B6、字体或音乐。此次是参考图准备的部分交付／已知质量阻断检查点，不是完整图包或视频验收。

已有角色身份包与E02/E05场次层分别归原记录；董文慧E02的灰蓝外套、包、本与日光入口不自动移植到本开场。本轮早先一张灰褐外套母图只保留历史，用户澄清后未选作身份锚点。新楼梯图实际绑定已有董文慧身份图，身份SHA为`53075b370bc0dd00285d4384e74cd521d8672243a417801f177f807776e69458`。

## Artifacts And Findings

审看入口：`outputs/shizhen-episode01/opening-A-revision-20261026/production-inputs/macro-reference-review-20261027/index.html`；独立板`index-board.png`，来源／用途`preparation-report.json`，核验receipt `verification.json`，浏览器证据`browser-verification.json`。单图、实际引用顺序、输入输出SHA及逐次裁决见`referces/shizhen/macro-opening-20261027/state-attempts.json`。

| State | Current assessment |
| --- | --- |
| L01-r1 | 浅凹已封闭、原身份与本场服装保留；静态候选 |
| L01-X | 下行转向与更低平台可定位；远处凹痕细节不足，非动作连续性证明 |
| L02 | 低平台右手接触门把、门关闭、人物门槛外；静态候选 |
| L02-O-r1 | 几何引导后向内半开、右手接触可辨；重复凹痕轮廓匹配仍未证明 |
| T01 | 双人在同站棚的较远定位候选；动态接点与时钟推进未验 |
| M01-v0/r1/r2 | 全FAIL：从左绞盘直连门的钢索仍在，不能证明向右牵引；M02/M03与受力细节不延展 |
| L01-v0、L02-O | 分别为裂口代凹痕、门向外开，均FAIL并保留 |
| L03 | 门继续内开后右手／把手未随门，FAIL；L04不延展 |

正常态、形变、同凹痕对比、右手接触及反应尚未全部覆盖，不把局部成立称为完整参考PASS。两个独立几何SVG只承担输入结构示意，不是Blender、ControlNet或视频服从证据。参考方法核对官方指南：https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide ，当前exact输出仍逐图判断。

## Bounded Calls And Source Evidence

共12次内置image_gen.imagegen：早先未选母图1、新状态尝试7、known质量修复4。第一单元修复上限2已消耗；随后保留旧界与计数，封存每项各1次的几何引导修复单元，详见generation-intent.json。无UNKNOWN、无自动重试、无新增付费Provider／视频／音乐调用；工具未暴露结算金额。停止失败依赖，不提交视频。

reference-manifest四张图和三份去重原片均可访问，SHA匹配；入口两人在场与事后空位已逐图区分，来源AI标识保留。原清单station-entry不是B6精确首帧；本轮另外抽取B6第0帧，实见时钟03:16:53，T01据此保留静态模板数字，不证明前置视频的时钟时序。B6 SHA前后均为`d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a`。其他窗口更新了角色包的静态审看元数据，原身份bytes未变，本轮未改角色包。

## Verification And Checkpoint

11个状态输出PNG解码、尺寸/通道、source exact copy、实际参考SHA与prompt SHA已核验。独立headless Chromium实际加载审看页16张图，无page error，原图链接可打开，保存完整截图；Chrome MCP因共享profile占用未启动，未改动共享浏览器。docs_contract_gate通过。生成参考metadata没有focused Harness映射，不静默跑全套；本轮不改软件行为，不声称软件完整回归或视频通过。

Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：仅隔离候选素材与记录，无核心行为、凭据或Production持久状态更改，Parent完成逐图判断。使用record-ai-video-session记录本检查点；distill-ai-video-learning为no_candidate：同一修复链的有界个案，缺少独立多实验支持，不改Skill/Policy/Gate。项目RAG返回stale advisory，未等待重建，当前结论按实际图像及来源核验。

媒体本体按仓库约定保留本机；Git只记录本轮说明、提示词、HTML/SVG与来源／核验metadata。提交与推送状态以最终实际回读为准，不夹带并行工作。


## Continuation 02

用户明确要求继续，新增有界单元最多12次，实际8次，全部known output；累计内置图像调用20次，无新增付费Provider、视频或音乐。新意图与逐次实际引用／SHA见`referces/shizhen/macro-opening-20261027/repair-02/continuation-intent.json`、`attempts.json`。

L03-r2允许自然侧移前倾随把手，撤回Agent附加的脚位冻结和固定七十度，保留原剧情、右手接触、内开与门槛外。L04继承同次持门停步。M01-r3只删除第三条直连索，随后M02/M03继承同场设备；M03-D0/D1-r1给出同机位平直／有限弯曲对照。D1首版主要改变反光，明确FAIL不采用。旧FAIL不改写，当前选用映射归`repair-02/current-reference-usage.json`，不建立Production/Registry状态。

当前六镜12项静态职责都有对应图，仍不证明持续运动、声音因果、渐进形变、步速、跨镜接点、Provider输入准入或人工接受。B6 exact SHA保持`d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a`，未改B6、字体、音乐、Registry或Manifest。当前板只列选用图，原部分交付页和receipt分别保留为initial-partial-review.html、verification-initial.json。

本轮为同一修复链的继续，不足以当独立多实验；distill-ai-video-learning为no_candidate，不改Skill/Policy/Gate。Risk Gate仍NATIVE_REVIEW_NOT_REQUIRED，无代码或Production持久状态变化。核验结果与publication以当前verification.json及最终回读为准。


## Initial Video Start Readiness — Superseded Version Choice

用户再次询问能否开始视频后，只完成MC01–MC02首个完整事件的可审看输入草稿：Seedance 2.5／建议multimodal／8秒／1080p／16:9，五张actual参考文件SHA已重验；提示词与验收项位于production-inputs/macro-video-preflight-20261027。当前代码支持的模型与模式不证明当前session/profile已就绪，native request preview、execution binding、预算、permit均未封存。

旧“未经授权不新增付费生成”仍有效。本轮无付费调用、上传或视频提交，旧1500 CRD历史profile未复用。等待用户明确首段一次付费授权及本次积分上限，之后仍走既有runtime owner与fresh preview/permit。preparation.json保留旧准备快照并更新当前缺口；execute_ready保持false，不能把静态参考齐全表述成可直接扣费提交。此次为同主题准备状态，learning继续no_candidate。


## Duration-Based Seedance Selection

用户明确要求“8s就用seedance2.0”，并要求将规则改为“15s内的shot就用2.0”。选模原则写入现有seedance-authoring入口：按实际单次生成时长，15秒及以内（含15秒）用2.0，超过15秒用2.5，用户另有明确指定时优先；先按完整事件定时长，不为阈值拆戏。此为用户直接选择规则，不是从媒体单例归纳出的学习Claim，不改运行时router或profile schema。

当前首段草稿由2.5改为seedance_2.0_vip，仍为8秒／multimodal／1080p／16:9，五张参考不变。当前code registry的时长、图片数、总素材数、尺寸、字节上限与原图SHA已核验；2.0 overlay替代2.5 overlay，未混用30秒能力。实际runtime profile/native preview/permit仍未封存，无视频提交或新付费调用。


## Rule Verification

seedance-authoring现有8项检查通过；8秒2.0 VIP的五张原图SHA、时长／图片数／字节／尺寸与1080p能力检查通过。exact Skill commit为8cf1c000eab2c28e2c2c66f2b22f68230391e365。初次staged Harness纳入并行暂存路径而缺映射；改用精确Skill commit range后，docs_contract与Skill检查通过，但Harness自身测试319 passed／2 failed，失败为complete-cross-check coverage和unmapped-owned-files。涉及本任务未修改的policy/source映射，不改动其并行工作、不冒充Harness通过或完整回归。

失败receipt：`.agent/harness/runs/seedance-duration-rule-range-20261027/receipt.json`；本次输入核验记录：`outputs/shizhen-episode01/opening-A-revision-20261026/production-inputs/macro-video-preflight-20261027/verification.json`。这是用户明确规则更改，不是学习Claim adoption；learning为no_candidate，未产生视频或付费调用。

## First Video Generation — Current Checkpoint

用户随后明确要求“生成視頻”，取代上方旧的等待执行授权状态。本轮实际完成MC01–MC02首个8秒事件的一次Jimeng `seedance_2.0_vip`／multimodal／1080p／16:9资格试片提交。新画布`e09b617d-5af1-40ee-9136-d36a7422d40c`，新空视频节点；实际五张参考按M01、M02、M03、D0、D1顺序绑定，最终544字纯中文正文只加入必要image引用语法。引用SHA、模型实际配置、适配、lint、intent与exact request见`outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02/`。

通过既有`ProductionStateCommitter` bootstrap/QA激活、`GenerationFeedbackOrchestrator`、`VideoGenerationService`与`JimengBrowserTransport`完成start→一次submit→poll→fetch。没有裸POST、Production activation、P6或伪造正式资格。准备时修补缺失的audio/output字段、逐人物表演声明和非连续字符串片段映射；这些是submit前的输入修正，零额外付费尝试，旧QA revision及prepare阻断记录保留。首次新建画布按钮被遮挡，读回确认无变化；卡片随后进入本地画布。加节点后ensureProject无参数调用报错，但节点和画布已正常自动持久化；按实际project/node读回继续，没有再建第二节点或生成重试。

实际受理时间2026-10-27T06:03:25.800592Z。输出SHA `bae96d85f72179cae23aa3535180d851946f16b4676e138542b0147ec212a3d4`，24,508,531字节，1920×1080，容器约8.065秒，193帧，AAC双声道。MCP报告60fps取自r_frame_rate，真实avg_frame_rate为11580/481，未按60fps重定时。原始候选和审看副本逐字节相同，副本`outputs/shizhen-episode01/macro-opening-video-20261027/失帧-市政异常-8秒-Seedance2.0-候选01.mp4`；审看入口`http://127.0.0.1:8883/outputs/shizhen-episode01/macro-opening-video-20261027/index.html`。

当前逐镜Gate为**FAIL**：停灯后门继续向右滑动、正确两段索路、同侧切近景和工人保持安全距离已出现；连接底板在近景里仍大致平直，未清楚表现逐渐有限拱起。`video-analysis` MCP已显式调用；末段原尺寸帧与正常1.0x浏览器播放记录已保存。自动scene阈值漏掉了实际切镜，Parent按序列辨认，不伪造MCP结论。

声音盲分析另外消费一个development operator unit，exact MP4和完整PCM派生SHA绑定，Gemini3.8Flash HTTP200。分析器返回保龄球滚动／碰撞等描述；这与创作目标不吻合，也不足以断言原片真实存在保龄球声音。声音语义为`NOT_EVALUATED`，走`EVIDENCE_REPAIR_FIRST`，不以重新生成视频来修补听音证据。未进行human listening/acceptance。

`MC01-02/qa/post-media-gate.json`按全部七项要求裁决，当前attempt执行STOP，未提交任何后续Shot。完整冷开场尚未完成，本片只作为未通过的首段候选供审看。原B6、字体、配乐、人物剧情均未修改，B6 SHA仍为`d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a`。

当前有限单元为1次视频，已消费1次；预配置内部单次1500CRD上限不是报价，未取得实际结算金额。声音分析内部0.05USD上限同样不是报价，实际费用待确认。严格reader审计先前24个视频attempt；原S05 UNKNOWN保持不动，不重试、不清零、不退款或复用旧permit。本次为独立宏观首段的新任务，观察cohort累计25个，不声称这是账单统计。

核验receipt：`outputs/shizhen-episode01/macro-opening-video-20261027/verification.json`；含exact copy/SHA、全片声画decode、Range206、浏览器原速播放到结尾、B6保护核验。docs_contract_gate通过，任务脚本py_compile通过；未改共享源码，不额外跑全套或把技术检查当作质量通过。旧规则Harness的并行policy映射失败仍按上节保留。Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：只新增任务数据及调用既有owner，无修改凭据、权限、恢复或共享执行行为，Parent已核验实际证据。record-ai-video-session记录本稳定质量阻断；distill-ai-video-learning评估no_candidate，一次新片及其音频观察不构成独立多实验，不改Skill/Policy/Gate。

## Preview-First Rule And Rejected Internal Cut

用户明确修订“统一先用480p，我点头再用1080p”，并指出“5s这个切镜头太奇怪了”。本次只改规则和切镜依据，零新增视频／图像／声音调用；不把此反馈当1080p认可或自动换型号授权。横版叙事/短剧的canonical规格`docs/canvas-continuous-production.md`删除“方法稳定后直接1080p”的豁免，改为统一480p试片、用户明确认可适用方案并授权后才1080p，CLI/表格同步；seedance-authoring只增加该owner的入口与能力缺口处理。

实际只读核验当前同一即梦账号与画布的全模态配置：`seedance_2.0_vip`只有720p/1080p/4k，`seedance_2.5`支持480p/720p/1080p。这个结论限当前渠道，不宣称2.0整个模型家族不支持480p。Parent提出2.5/480p选项后，用户追问为何不用2.0，没有批准换型；当前仍保留2.0，480p能力缺口未解除，不擅自用720p、1080p或先高分辨率再缩小冒充。15秒及以内选2.0的规则保留；新480p规则与当前渠道不可同时满足时报告，不静默择一。

原片SHA不变。按解码PTS确认实际切镜为5.2166667秒，切前5.16667秒工人手仍在停止控制上，连接耳位于画面右侧；切后连接耳跳到偏左，工人缩成远处左边背景，近景又未兑现新的形变动作。旧Gate的camera PASS只核对“有同侧近景”等结构，不能代表剪辑自然；当前camera判断由用户反馈及实际前后帧复核为FAIL。旧receipt保留，supersession见`outputs/shizhen-episode01/macro-opening-video-20261027/cut-repair-02/cut-review.json`，不把原片或旧PASS改成新片通过。

MC01/MC02镜头依据已修订：停机与继续滑移同镜不变；待手收回、目光交到牵引点、门到限位后再切，不硬钉第5秒；近景继承中右连接耳、朝右索向、门边限位与同一次受力阶段，在镜内从平直到有限拱起，不接静止细节图等到结束。D0/D1只承担形变前后职责，不自动批准旧构图。此为repair authoring，尚无新媒体，修订效果NOT_EVALUATED；不以转场、变速或冻结假装修复。

现有preparation和审看页同步当前480p要求、切镜失败与能力阻断。seedance-authoring精准测试8项通过，docs_contract_gate通过；切点按exact原片SHA/实际PTS与前后全尺寸帧核对，无新增共享代码行为，不运行完整工程套件。现有Harness policy的并行映射问题仍按旧段保留。record-ai-video-session更新本稳定规则/阻断检查点；distill-ai-video-learning为no_candidate：本次是用户直接规则和同片新观察，不是独立多实验或Skill学习adoption。Risk Gate仍NATIVE_REVIEW_NOT_REQUIRED，由Parent核验规则diff与实际帧；不改并行dirty AGENTS、Provider源码/文档或他人暂存。


## User-Selected 720p Seedance 2.0 Preview

用户明确选择“那你就用720p,2.0”，解除前段480p与当前即梦2.0渠道的规格冲突；只覆盖当前试片规格，不构成1080p认可。沿用Seedance2.0指导，生成首段8秒／720p／16:9／multimodal／原生环境声音轨，五张exact参考不换脸或设备。修订重点为收手与视线后的动机切镜、连接耳位置继承、底板固定端与中部曲率；不改剧情、B6、字体或配乐。

当前显式720p规格作为一个新的有界qualification试片单元保存，root为`runs/shizhen-macro-opening-20261027/MC01-02-720p-v2`，任务输入和工具调用器位于`outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-720p-v2`。经既有bootstrap/committer、GenerationFeedbackOrchestrator、VideoGenerationService、Paid Gate、独立reservation与一用permit执行；没有更改共享源码或模型Production资格。旧1080proot、paid receipt、failed Gate、原片及历史UNKNOWN不变；新封套绑定旧Manifest／原片／预算上限SHA、旧宏观调用1次与新有限单元1次，宏观累计上限2次，未重用旧permit或把历史消费清零。预配置内部上限仍单次1500CRD，宏观两个单元累计上限3000CRD，均非报价；真实扣费尚未结算确认。本轮无自动retry。

同一画布新空视频节点`node_qd3b1733rt`；当前native model config、profile、compiled与resolved输出均明确720p。07:02:51.951138Z接受一次submit，随后poll成功、fetch落盘，视频SHA `d427e9eeee1cdd17d181fc76055984997637ce9b916e78dcd7b7077523d72424`，16,125,077字节，1280×720，约8.097秒，193帧，AAC44.1kHz双声道。审看副本`outputs/shizhen-episode01/macro-opening-video-20261027/失帧-市政异常-720p-2.0-试片02.mp4`逐字节一致。播放入口`http://127.0.0.1:8883/outputs/shizhen-episode01/macro-opening-video-20261027/index-720p-v2.html`；保留旧版入口，无直接mux、retime或假装为完整冷开场。

显式project-local video-analysis MCP已调用。精确PTS取帧与本地scene检测定位切点3.71667秒；MCP scene列表依然只报1场，未把工具漏检冒充无切镜。新片工人收手更完整，灯灭后门继续向右、两段索路及同一设备仍可辨；但近景仍把连接耳从约70%画宽跳到41%，未落实中右位置继承。4–8秒有渐进几何变化，因此不再写成“静止底板”；画面更像整块底板右缘翘离，未清楚表现螺栓固定而中部独立拱曲。七项Gate中action/camera FAIL、sound NOT_EVALUATED；后续Shot不提交，1080p未生成。

按当前open-video Creative Completion要求启用一个native只读`reviewer_high`，任务`/root/macro720_review`，无nested delegation。先独立检查五张参考和意图，再检查actual MP4 SHA与17张exact PTS帧；没有把Parent结论或工具成功当输入。R1提出参考可能导致整板翘离；actual R2提出SHZ720-R01（4–8秒整板翘离）与SHZ720-R02（3.71667秒位置重置），Parent均CONFIRMED。其能力限制是静态序列，未完成原速连续观看／听音；不宣称human或独立正常速度验收，记录归qa/independent-concept-review.json、independent-media-review.json。

当前新MP4另外执行一次带exact SHA的盲音频理解development unit，HTTP200，Gemini3.8Flash实际返回持续风／气流、金属碰撞和低环境轰鸣，无语音片段。观察不能可靠证明雨／交通／马达停声及持续摩擦的因果时序，human listening仍未完成，sound保留NOT_EVALUATED。只对新源分析一次，未重复旧UNKNOWN或旧音频unit；0.05USD为内部保护上限，非报价，实际结算待确认。

验证包括源／副本SHA、1280×720输出、全声画decode、17张实际源PTS帧、Range206、独立Chromium1.0x原声开启播放到结尾、B6保护SHA不变。receipt为`outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-720p-v2/verification.json`，逐项裁决为`qa/post-media-gate.json`。任务调用脚本py_compile、docs_contract_gate通过，无共享实现变更，不追加完整工程回归，也不把技术成功当媒体PASS。候选仍FAIL，Production activation/P6/Final Acceptance均无。下一修复应先解决参考主导的近景构图及固定端几何，声音走EVIDENCE_REPAIR_FIRST，不再仅改秒点或重复同Prompt。

record-ai-video-session记录本稳定交付／失败检查点；distill-ai-video-learning评估no_candidate：同一来源修复链中同时改变了分辨率与创作表达，不能归因于版本或分辨率，也没有足够独立证据采纳通用规则。代码Implementation Risk Gate为NATIVE_REVIEW_NOT_REQUIRED；媒体所需独立只读复核已完成，但未解决blocker，不能称镜头或完整开场已完成验收。


## Approved 720p Source To 1080p And New Model Defaults

用户对试片02明确说“这个没问题,用1080p再做一次”，将该exact720p成片作为本轮视觉、表演、接镜对照。用户认可属于创作选择，不以旧AI构图／底板偏好继续改片；旧FAIL/NE和独立意见保留，未倒写成技术PASS或伪造听音证据。新的认可封套位于`MC01-02-1080p-v3/accepted-720p-source.json`，绑定源SHA `d427e9eeee1cdd17d181fc76055984997637ce9b916e78dcd7b7077523d72424`及原话，新1080p本身仍须重新审看。

同轮用户另外要求“顺便把seedance 2.0的改了默认1080p,2.5不变”。Agent规则owner `seedance-authoring/SKILL.md`及canonical制作规格`docs/canvas-continuous-production.md`同步为：2.0新生成／修复默认1080p，当前用户另有规格或审批指令时优先；2.5维持480p试片、认可后才1080p。15秒及以内用2.0的选择原则不变。这是用户直接规则，不是媒体学习adoption；不改原生平台／API默认、历史sealed请求、型号能力或Product Gate。默认规格仍由每次exact selected profile显式落实，variant不支持时报告，不换型号或假放大。

本轮保留720p实际请求的751字纯中文正文、全部GenerationIntent、五张exact图片bytes／顺序／角色、模型2.0VIP、multimodal、8秒、16:9和原生环境声音。native prompt SHA、image_bindings逐字段相等；仅输出规格、commercial selector、新空节点及技术rationale变化，见`source-preservation-diff.json`和`pre-submit-preflight.json`。本轮eval context明确以用户认可基线核对回归，原plan的action/camera观察仍保存在data.json的original_720p_observations，不谎称旧AI逐项技术通过。B6、字体与配乐未改。

新1080p有界qualification单元root：`runs/shizhen-macro-opening-20261027/MC01-02-1080p-v3`；输出metadata/caller归`outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-1080p-v3`。沿既有committer bootstrap、feedback编译、VideoGenerationService、Paid Gate／reservation／一用permit执行，未改共享实现或模型资格。新节点`node_45y3tdf66j`，actual native config、compiled/resolved output均1080p。07:21:56.162074Z一次submit被接受，随后poll成功并fetch；没有retry、旧permit复用或scope外提交。封套保留前两宏观paid attempt／fetch／Manifest SHA，宏观计数由2增到3、本轮上限1；预配置单次内部保护上限1500CRD、三个单元累计4500CRD，均非报价，实际结算未确认。历史S05 UNKNOWN未动，没有清零历史或退款。

新原片SHA `88564a7f7399edc432dbe25778c762f48f65217524ddad67c913331628eb0e52`，30,452,488字节，1920×1080，约8.058秒，193帧，AAC44.1kHz双声道。审看副本`outputs/shizhen-episode01/macro-opening-video-20261027/失帧-市政异常-1080p-2.0-认可方案03.mp4`与fetched bytes完全一致。入口`http://127.0.0.1:8883/outputs/shizhen-episode01/macro-opening-video-20261027/index-1080p-v3.html`，另保留720p对照和全部旧片，不做本地升采样、retime或direct mux冒充1080p生成。

显式project-local video-analysis MCP、17张actual PTS帧和全声画decode已完成；独立Chromium1.0x原声开启播放到结尾、Range206、B6保护SHA不变。MCP与本地scene阈值未检测到hard cut，Parent实际序列见约4.5–5.5秒的远近景叠化，不能把漏报/无硬切当作无转场。新片保留停灯后门继续右移和用户认可的连接有限变化，但叠化出现双重人物与设备，和720p直接切换不同，属于新生成差异，未声称保留相同像素或自动合格。

沿同一个native只读`/root/macro720_review`、profile `reviewer_high`完成第3轮actual HD对照审查，无新增reviewer或nested delegation。提供用户新的认可与原片SHA，要求比较新增回归而不重开旧R01/R02。独立发现SHZ-HD-R03：4.5–5.5秒新增叠化、两处人物和两套受力连接重影；Parent CONFIRMED。限于17张取帧，reviewer未连续原速观看或听音，不签human或完整成片认可。七项Gate camera FAIL、sound NOT_EVALUATED，余项仅按用户已认可基线的有界观察；`qa/independent-media-review.json`及`qa/post-media-gate.json`保留。第3轮后没有自动第四轮或重复生成，下一Shot未提交，Production activation/P6/Final Acceptance均无。

同一新MP4完整音轨仅盲分析一次，source/audio SHA绑定独立development operator unit，Gemini3.8Flash HTTP200。返回风声、机械重响、低频撞击，无语音片段；不足以可靠证明完整声场及马达停声／受力摩擦时序，无human listening结论。内部0.05USD上限不是报价，结算待确认。旧音频unit与UNKNOWN无重试，声音仍走EVIDENCE_REPAIR_FIRST，不生成新视频来补声音证据。

核验receipt `MC01-02-1080p-v3/verification.json`、规则receipt `rule-verification.json`。8项seedance-authoring精准检查、docs_contract_gate和本轮operator脚本py_compile通过，无共享runtime行为变更，不宣称完整工程回归或媒体通过。record-ai-video-session记录本稳定原片交付／差异检查点；distill-ai-video-learning为no_candidate：单次1080p与720p对照仍受uncontrolled seed影响，不能归因为普遍分辨率或版本规律，且默认规格来自用户直接选择。Implementation Risk Gate为NATIVE_REVIEW_NOT_REQUIRED；实际媒体所需的单名独立复核已完成，新增blocker未解决，明确保留HD待审状态。

## Playback Service Recovery

用户反馈“打不开”。现场证据：8883无监听，原播放页curl connection refused；HTML与30,452,488字节原片都存在，源SHA未变。旧一次性exec启动方式没有维持可用服务；本轮只恢复播放可达性，不修改媒体、质量Gate、默认规格或生成结果，无新增Provider／音频调用。

改用同一现有Range handler，由当前UID的独立user systemd transient unit `ai-video-shizhen-macro-review.service`托管，WorkingDirectory为本repository，Restart=on-failure／RestartSec=2，仍只绑定127.0.0.1:8883。当前exec环境缺少user bus变量，先核验`/run/user/1000`和bus属于当前UID，再对systemd命令显式接线；不读取凭据或扩大网络暴露。unit位于user manager的app.slice，MainPID966245，独立于启动exec；不是开机安装的永久服务。停止入口为`systemctl --user stop ai-video-shizhen-macro-review.service`。

原始地址恢复200，视频Range0–1023返回206／1024字节，越界Range返回416。独立Chromium原速、声音开启播放8.057秒到结尾，无page error；另行seek到5.0秒成功，readyState4、seekable[0,8.057007]、media error=null。原完整播放metadata保留，新证据为`MC01-02-1080p-v3/qa/service-recovery-playback.json`、`service-recovery-seek.json`及`review-service-recovery.json`。本地MP4可直接打开作为另一个入口，原文件SHA仍`88564a7f7399edc432dbe25778c762f48f65217524ddad67c913331628eb0e52`；已有叠化差异与人工待审状态未变，服务恢复不等于影片验收。

本轮无共享源码或媒体修改，不追加单元测试／完整回归；验证直接覆盖服务独立生命周期、HTTP、真实浏览器播放和拖动。Risk Gate为NATIVE_REVIEW_NOT_REQUIRED。record-ai-video-session记录本稳定恢复；distill-ai-video-learning为no_candidate：单次服务退出／恢复事件，不扩张为通用Skill或Gate规则。项目经验检索返回stale advisory，未等待后台刷新，结论按实际端口、HTTP、浏览器和exact bytes核验。

## HD Dissolve Editorial Repair

用户指出“这个5s的时候有问题”，Parent核对1080p-v3约4.5–5.5秒双重工人与设备叠化。最初准备同模型单变量重生成，但用户及时追问“这个不能剪辑吗”，遂改为直接剪已有原片；只已在原画布创建一个空video node `node_gm3a1rrn58`，未bootstrap generation、未prepare/start/submit、无paid reservation／POST。该空节点不删除或复用，`MC01-02-1080p-v4/aborted-before-generation.json`明确ABORTED_UNSUBMITTED；宏观实际视频消费仍3次，没有第四次视频提交。

本轮使用open-video既有剪辑方法，完整目标仍是停机后门持续受力、工人确认和连接近景，不改B6、字体、音乐、人物、参考或后续剧情。实际逐帧定位后，保留HD v3的24fps交付网格源[0,104)及[132,192)，删[104,132)即约4.333–5.500秒，原速直接切换，总164帧／6.833秒；不冻结、插帧、变速或补新素材。每段同源原声同步裁切，0dB无fade、无新配乐。标准prepare_qualification_preview_input捕获exact paid fetched qualification链，保留原源FAIL／sound NOT_EVALUATED，ProductionStateCommitter独占新开发bundle bootstrap，未将原片当普通import绕过qualification；两条捕获资产分别绑定各自Shot和trim，同一原MP4身份。source-native-48k.wav仅同源解码/重采样，AudioImportRequest绑定对应VIDEO与源SHA，不伪造语音。

调用方 `outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-edit-v4/{prepare.py,render.py}`，新独立development project在 `runs/shizhen-macro-opening-20261027/MC01-02-edit-v4/project`。首个bootstrap在写入前因origin共用可变windows、增加audio_id后hash不匹配而拒绝；保持目标空目录，改为深拷贝封存origin，核验已生成PCM与当前exact源一致后重跑通过，无Source/Manifest损坏或未知副作用。新唯一CompositionSpec→ResolvedTimeline为development_audio_preview，HyperFrames0.7.103完成实际导出。首次硬件check返回sweep_static，未出片；保留render-001失败证据，核对既有S03同类记录与当前公开browser_gpu_mode参数后，在相同timeline用software模式及新render-002-software staging完成lint/check零错误、真实render与adapter输出验证。未改renderer代码、node_modules、检查或隔离规则。

交付 `MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4`，SHA `b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d`，13,606,194bytes，1920×1080／24fps／164帧，AAC48k双声道。入口 `http://127.0.0.1:8883/outputs/shizhen-episode01/macro-opening-video-20261027/index-edit-v4.html`，继续由已有user systemd Range服务托管。原片/720p均保留。源B6 exact SHA仍d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a。

显式project-local video-analysis MCP绑定本次MP4，抽取14帧；另取28张actual PTS的0.25秒序列，实际输出4.25秒为干净远景、4.50秒为干净近景，叠化双影区间已排除。MCP scene detector仍漏报硬切，未用scene_count=1冒充单镜。全片声画decode、SHA、Range206和独立Chromium1x声音开启播放到结尾通过；这些技术事实不证明自然表演或human听验。原声只盲分析一次、HTTP200、exact source/audio SHA／一用operatorunit绑定，返回水声/海浪拟声、无语音，无法证明马达停声/金属摩擦时序和接点听感；不向分析器喂预期，不重复分析换取通过。内部音频保护上限0.05USD非报价，实际结算待确认；本轮视频生成费为零。

`prepare-assembly-review`与`verify-assembly`均显式执行，回答绑定当前exact视频/timeline/render report；实际取帧观察与源窗口写入，完整原速声画/听验不足仍NOT_EVALUATED、exit1，不伪造PASS。一次填写误用keep枚举导致exit2，改为当前typed retain_with_reason后返回有效NOT_EVALUATED，保留最终回答和verdict。`qa/post-media-gate.json`阻断下一Shot，未activation/P6/Final Acceptance/publication。review服务可达、影片有音轨、render检查通过均不用于签质量。

用户另问为何相同处理差异大：当前prepare.json核验720p-v2与HD-v3 actual native prompt及5个image_bindings完全相同，但模型进行了新一轮生成，分辨率与commercial selector不同，当前渠道seed_supported=false，无法固定采样对照；不是原片上采样，分辨率因果作用未隔离，不能断言差异全由分辨率造成。`source-comparison.json`保存直接输入对照。官方多镜/参考能力资料仅advisory，不宣称显式hard-cut prompt必定可控；最终采用已有片确定性剪辑而非追加模型试错。

本轮无共享工程修改，任务脚本py_compile、docs_contract_gate通过，实际canonical bootstrap/resolve/render、MCP、decode、HTTP/浏览器为对应验证，不宣称完整工程回归。Implementation Risk Gate NATIVE_REVIEW_NOT_REQUIRED，媒体按适用open-video独立review要求另取证。record-ai-video-session记录本稳定剪辑交付，distill-ai-video-learning评估no_candidate：仍是同一macro修复链、无controlled seed或多独立模型实验；software单例仅复用已有兼容参数，不升级默认配置或学习规则。

同一native只读reviewer `/root/macro720_review`、profile reviewer_high完成有据有限扩展第4轮／上限4；前三轮保留，扩展原因是用户新指认HD R03并改为一版确定性本地剪辑，不开启连续模型重试。Reviewer独立核验exact SHA、查看28帧并直接解码输出frame103/104：R03叠影在候选中未重现，未发现新增视觉问题；未连续原速观看或听验。SHZ-EDIT-R04 non_blocking指出boundary-index没有标明它是原片取帧，4.5秒源叠影可能被误认作输出；Parent CONFIRMED，补原片exact path/SHA、source_pts_seconds及显著ORIGINAL_HD_SOURCE_BOUNDARIES_NOT_EDITED_OUTPUT说明，另指输出frame-index。不改媒体bytes，证据标签修正无需新审查。Parent将原R03局部问题判为OBSOLETE_AFTER_CHANGE，整片节奏/声音仍NOT_EVALUATED；`qa/independent-media-review.json`记录闭合及范围。经验跟进检索返回fresh advisory，命中既有S03 sweep_static/software恢复，已重开当前记录与参数验证；未为此重建索引或扩建共享工程。
