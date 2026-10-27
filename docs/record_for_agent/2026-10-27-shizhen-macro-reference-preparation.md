---
record_kind: session_summary
topic_id: shizhen-macro-opening-reference-preparation
learning_eligibility: ineligible
---

# Shizhen Macro Reference Preparation

Date: 2026-10-27

> **Current Update — City Reveal Move Confirmed:** 用户追问运镜质感后认可“屋檐滴雨→横移揭示城市→沿路网下降→减速交给钢索、工人与控制盒”的方向，回复“可以”。两稿已据此修订MC00，保留六镜及B6。确认仅限运镜方向，不冒充真实连续运动、最终Production Shot或全段事件一镜到底的批准；本轮没有生成媒体。详见 City Reveal Move Revision。

> **Historical Update — City Long Take Draft:** 初版MC00从城市大全景沿主路下降，辨认住宅与公交路线所在纵深，再减速落至市政现场外。该版及其范围待定状态归提交c3f637f；后续由用户确认的屋檐揭示版本取代其起幅与移动设计，旧核验保留。

> **Previous Update — Isolated Stair Reference:** 用户用两张截图指出先前露出的梯级本身弯曲，明确要求“把楼梯作为一个单独的白底图作为referces”。已生成一张独立白底直梯结构候选，包含上下平台与单侧栏杆，归 `referces/shizhen/macro-opening-20261027/stair-structure-white-20261027/`。这纠正了Parent此前将需求理解为尾部补片、随后又交原片截图的偏离；既有补片不能解决前段结构错误，不记为视频通过。该轮新增内置生图1次、视频0次，尚未绑定新视频。详见 Isolated Stair Geometry Reference。

> **Historical Update — Static Stair Image:** 用户“那個樓梯你就不能給一個image嗎”后，Parent曾以同源台阶PNG覆盖末两秒背景并导出8秒／1080p全景修订04。该方案保留人物、全景和原声，但并未处理用户随后指出的前段梯级弯曲，不能作为结构修复通过；未提交推门源。该阶段新增生成／远程音频调用均为0，只有1次本地HyperFrames渲染。详见 Static Stair Image Repair。

> **Historical Update — Arrival Reframe:** 用户“開始吧”后已生成8秒2.0／1080p下楼到达源，方向与到达在取帧中成立；用户指出尾段右下台阶抖动并确认原像素仍抖，原片按FAIL保留。同源近景修订03曾为8秒审看候选；未获用户声画认可，不将“给一个image”的后续要求记为接受。详见 Descent Source And Local Arrival Reframe。

> **Historical Update — Reference Regrouping:** 市政6.833秒剪辑版已获用户完整看听认可。第二事件楼梯原片及首尾帧修订02均已实际生成，修订02消除提前揭示，但仍反向上楼、门动作反复且短暂脱离右手接触，Post-Media Gate FAIL。宏观视频累计5次，本修复单元上限1次已用，停止本单元与下一Shot，未改B6或签Production/最终验收。最新参考重整已补4张并复用3张，七张静态候选审看板已可访问；本轮没有新视频提交。详见 Action Reference Sequence Regrouping、First/Last Stair Repair 及对应 verification.json。

> **Historical Update — HD Regeneration:** 用户已明确认可720p试片02并要求同方案1080p，本轮1080p版03已真实生成、可播放。新片约4.5–5.5秒出现基线没有的叠化，已标注新片未通过项，待用户审看；旧AI意见与720p用户认可分别保留。另按用户指令改为Seedance2.0默认1080p，2.5保持480p先审。未提交下一Shot、未改B6或签Production验收。

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

## Second Generation Unit — Stair Event

后续状态：本节原片FAIL及当时“未生成repair”为历史；用户随后“繼續”授权的首尾帧修复见下文 First/Last Stair Repair，旧失败与计数均保留。

用户“开始第二个shot”对应原分镜第二个完整事件组MC03–MC05，不是重做已包含MC02的市政组。既有scenario-identity-library、scenario-seedance-storyboard及seedance-authoring用于来源保留的准备：逐张查看董文慧identity-v1及L01-r1、L01-X、L02、L02-O-r1、L03-r2、L04，SHA／PNG尺寸1672×941均核验。实际视频仅绑定六张干净场景图，L01承担人物锚点，L04补侧脸；原四视身份板只作审查/父来源，不作为多人拼格输入。身份父SHA53075b370bc0dd00285d4384e74cd521d8672243a417801f177f807776e69458保持；本场灰褐外套、深灰裤，不移入第二集场次的包本。没有补图、改剧情、B6、字体或音乐。六图顺序、hash、职责归MC03-05/reference-input-plan.json，实际compiled/resolved image_bindings再次逐项一致。

起先严格保留前段剪辑片NOT_EVALUATED并仅准备，不以“开始下一镜”冒充完整听验。用户随后在本次明确回答“已完整看听，可以保留”，针对exact6.83秒剪辑版及其切镜/动作/声音。新predecessor-media-clearance.json封存原片SHAb3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d、原video-analysis字节SHA、逐项Parent/人工证据和用户原话；原raw及剪辑NE记录不覆盖，不重新资格化原始1080p v3。predecessor-assembly-user-accepted.json保留这一真实human证据，verify-assembly最终PASS；最初仍用explicit_evaluator强度时返回NE，随后按实际用户证据使用human，未把Agent播放/取帧冒充用户。start曾在assembly强度核对完成前创建request，尚无外部submit；修正caller再要求assembly PASS后才发唯一POST。只认可本exact片，不代表全开场Final Acceptance。

新单位outputs/shizhen-episode01/macro-opening-video-20261027/MC03-05与runs/shizhen-macro-opening-20261027/MC03-05。按完整下行、开门显露、停步核对定12秒，依用户≤15秒用2.0、2.0默认1080p规则，选seedance_2.0_vip／multimodal4／16:9／native audio。当前native config现场核验12000ms和1080p支持；新空节点node_746f5r0dr5，不复用上轮aborted空节点。纯中文实际正文526字、六个image markers、右手门槛/开门/无对白配乐/不叠化约束均经编译与lint核验；526字符包含六个素材引用语法，去掉引用后460字符；官方500字为创作建议，当前现场4000字符为输入上限，不将两种口径混为超限或宣称长度保证质量。Typed主运镜改为向下短跟随并与正文一致，不沿用市政locked定义。新bootstrap首次因Storyboard残留市政scene_id在strict preflight拒绝，无发布/付费副作用；修正本任务数据后由committer正常bootstrap、graph、schema2.14、QA封存，未改共享源码或放宽检查。

operator-bound封存前三宏观known fetched attempt/Manifest/原片SHA及前一bound，单次内部1500CRD上限（非报价），累计由3→最多4、内部上限4500→6000CRD，本轮最多1次、零自动重抽。2026-10-27T08:40:02.855743Z唯一canonical VideoGenerationService.submit_once提交被接受，正常查询同一任务直至成功后fetch，不重试、不重铸permit；宏观真实累计4次。原S05 UNKNOWN保持隔离，不用其历史permit/消费或尝试恢复。付费已执行1次，实际积分/金额未取得结算，不能用预算或native quote充账单。

落盘原片SHA43584ba80ad0fc3beaaadfd8cc55c2748f4f3169b667a61d0655787e2e2b5528，33,005,511bytes，1920×1080，container12.065秒，video12.016667秒／289帧，AAC44.1k双声道。r_frame_rate60/1仅nominal metadata，avg17340/721，按actual PTS观察、不当60fps或retime。原样副本为失帧-楼梯异常-1080p-2.0-原片01.mp4；播放页index-stairs-v1.html已交用户并标已知失败。服务沿既有8883user systemd Range托管；exact copy/SHA、全声画decode、Range206、独立Chromium1x原声开启播至结尾均通过，无pageerror，仍非媒体验收。

显式project-local video-analysis MCP绑定本exact片、25张实际PTS帧及额外本地scene候选。MCP漏报内部切镜、scene_count1；实际顺序是0–1.4秒先见门已开与异常结果，1.5–2.5秒下行，约3–4秒反向上楼，再于4.5秒到关门前；不能拿scene_count当单镜证明。5–7秒实际把门拉向人物/摄影机，身体后退，和指定向内推门相反。仅删头不能改变拉门方向或证明完整下行到达，故没有制造“纯剪辑已修好”的成片。

同一只读native reviewer /root/macro720_review、reviewer_high完成新楼梯组一次actual-media审查，宏观累计第5轮／本次有据扩展上限5，前4轮保留；新用户任务/不同事件支持仅一轮扩展，不设机械resample。Reviewer核验SHA及全部25帧，独立提出SHZ-STAIR-R05提前揭示、R06下行变上行、R07拉代推三个blocking_candidate，Parent全部CONFIRMED；未连续原速看听，不签human接受。qa/independent-media-review.json及qa/post-media-gate.json保存：action/camera/space FAIL、performance/sound NE，identity/art仅对应已查看有限属性。当前单位STOP，无下一Shot、自动重抽、Production activation/P6/Final Acceptance；尚不把本段并入“全部合格镜头”的正式连续版。

完整音轨一次盲audio-understand、fresh一用operatorunit、source/audio SHA绑定、HTTP200，观察硬地脚步、门开/把手、微弱室内环境，无语音片段；不能证明定位滴水、门前后声场差异或逐动作同步。内部0.05USD上限非报价，实际结算待确认，不重复分析换取通过。旧原片认可不继承到新12秒片。

核验receipt为MC03-05/verification.json；任务脚本py_compile与docs_contract_gate通过，没改共享engine，未跑完整工程回归。Implementation Risk Gate NATIVE_REVIEW_NOT_REQUIRED；适用Skill要求的单名实际媒体复核已完成且blocker诚实保留。两次任务相关经验检索只得部分stale/无适用精确解法，未等待重建或把其他Mini/Ark白模案例移植成Jimeng保证；核对官方2.0来源只支持多模态/多镜能力边界，不以宣传签动作通过。当前实际六图、正文及失败链已保存，可供后续Director重新判断，未生成付费repair。record-ai-video-session记录这一有界首片交付/质量阻断，distill-ai-video-learning评估no_candidate：不同事件的单次结果与前组修复不能隔离多参考、长度、分辨率等变量，不据此改Skill/Policy/Gate或建立普遍模型结论。源媒体按ignore本地保存，Git仅推任务说明、caller、审看页和来源/QA metadata，不夹带并行修改。


## First/Last Stair Repair

用户“繼續”后，仅修复同一MC03–MC05事件，不改剧情、角色、B6、字体或音乐。复用retrieve-ai-video-memory、scenario身份/分镜和seedance-authoring既有入口；open-video独立概念检查由同一native只读reviewer执行累计第6轮。其SHZ-STAIR-R08指出原片真正下行只有约1.4–2.5秒，2.65秒已转上行、正常线索完整展示过短且无低平台到达，Parent确认不能将其裁剪后充当完整MC03。另确认原L03-r2自由门边投影缩短与向内推相容，不能把上次拉门归因为参考已画错。

本轮两次builtin-imagegen仅修改门状态参考，结果均已落盘、查看，保持董文慧原identity父SHA53075b370bc0dd00285d4384e74cd521d8672243a417801f177f807776e69458。新关门图L02-push-closed只供几何审看；实际输入为已有背向下行L01-X（SHA9a0be93cec6dbeaf460686c1d140156a7390bf1a200ffbfd45b8423d1e5b5f50）和新L03-push-open（SHAeca6dc03ff3869c9d9e0eb3cf7327b56771fd5d092ae8231f7dcf3d17c806648）。初选正面大人像L01-r1与尾帧景别不一致，提交前已退役该选择而保留预备记录，未伪报兼容。新图和审看板在referces/shizhen/macro-opening-20261027/door-push-repair-03/；可访问来源/用途与一份审看板归MC03-05-repair-v2/reference-input-plan.json、reference-review.html，三张PNG HTTP可达且哈希核验。静态图不是动作通过证据。

新资格实验单位outputs/shizhen-episode01/macro-opening-video-20261027/MC03-05-repair-v2/，canonical根runs/shizhen-macro-opening-20261027/MC03-05-repair-v2/。使用Seedance2.0 VIP／1080p／12秒／16:9／native audio，实际native mode3 first_last_frame而非原六图multimodal。提交前按真实API纠正Canvas approved_keyframe→native first_frame映射，沿committer封存兼容conditioning assessment、L01-X来源及Shot显式first_frame/last_frame角色，不绕过所需锚点准入。一次canonical项目修订后因immutable QA mapping赋值错误而停止准备，核对已完成的project revision后由独立completion caller完成QA更新，没有盲目重复已提交mutation或video POST。最终project revision3、Shot revision2、QA revision2由standard loader重开；实际编译466字纯中文正文、两图roles/order/hash、12秒1080p和原声lint全通过。

operator-bound保留前4个known fetched宏观调用与旧S05 UNKNOWN隔离，封存本单位新视频上限1、零自动重抽、宏观最多5；内部每次1500CRD、累计7500CRD为预配置保护上界而非价格。2026-10-27T09:57:36.737889Z唯一canonical submit_once受理，正常查询同一任务后成功fetch，没有重新提交或重铸permit。两次参考制图、一条视频、一次盲音频分析均outcome已知；实际积分/金额结算未取得，不能把预算充账单。

新MP4 SHAaecf88b4f06a005e5db32b11138dcc9b3db3700ab08c993187263e2ed21038c5，30,389,843bytes，1920×1080，container12.065秒、video12.016667秒／289帧、AAC44.1k双声道。保留actual PTS、不按nominal60fps重定时。全声画decode、exact副本、Range206、独立Chromium1x声音开启播至结尾通过；这些仅技术事实。审看入口index-stairs-v2.html、文件失帧-楼梯异常-1080p-2.0-修订02.mp4，沿原8883user systemd服务提供，页面明确失败诊断属性。

显式project-local video-analysis MCP绑定新exactMP4并抽25帧；MCP scene_count1仍漏切镜，本地actual PTS检出4.08333、6.55秒。开头提前揭示已消除，但约0.5秒开始转身、1–4秒向上行走，未到达指定较低平台；门前段开合反复，未完成一次连续推门。尾部约9.5–12秒可作为线索/停步候选，尚未完整source-use审查；剪掉错误门动作仍不能补出缺失的完整下行，因此没有把全片裁剪宣称修好，也未执行canonical salvage或新合成。后续须先重审动作覆盖和控制方案，不能再靠同类长事件反复抽样。

完整音轨只做一次盲audio-understand，fresh一用operatorunit及exact source/audio SHA绑定、HTTP200；观察为硬地脚步、门开与关门、空房回声，无可辨语音，不证明滴水、门前后声场差异或逐动作同步。保留sound/performance NOT_EVALUATED，未编造用户听验。qa/post-media-gate.json逐项裁决action/camera/space FAIL，identity/art限已见属性；STOP_CURRENT_UNIT.json阻止下一Shot。本轮不追加视频、不接入全部合格镜头、不继承市政human接受，不activation/P6/Final Acceptance/publication；B6 exact SHA仍d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a。

record-ai-video-session更新同一topic历史与当前阻断，distill-ai-video-learning评估no_candidate：同一目标下条件改变未隔离多个变量，两个结果不足以证明首尾帧无效或模型必然不能下楼/推门，不修改Skill/Policy/Gate。当前工作仅任务caller、参考用途、审看页和证据，无本任务共享工程变更；并行HEAD的footage-salvage功能不是本轮成果。具体技术与独立审查结论以MC03-05-repair-v2/verification.json为准，源PNG/MP4按既有ignore本地保留。


同一reviewer完成本单位唯一actual-media审查累计第7轮／封存上限7，核验SHA、查看25帧与技术元数据，未连续原速观看或聆听。独立确认SHZ-STAIR-R06反向上楼、R07门外摆回关后手脱离把手仍继续内开；Parent以原尺寸frame15、18、19、20再次核对，两个blocking_candidate全部CONFIRMED。8.5–9秒门无接触继续运动是新可见细节，不能仅删除外摆/关门就将尾部签为完整推门。qa/independent-media-review.json记录具体时段、影响、裁剪限制及Parent裁决，没有额外review或Provider调用。


## Action Reference Sequence Regrouping

用户问“是不是referces沒做好”，Parent重开实际输入、两张端点及失败帧后承认准备/使用缺口：整个12秒从楼梯到门后仅绑定首尾，中途到达和接触缺乏约束；新关门图仅审看未送模型。该诊断不证明参考是唯一原因，也不把向内终态静态图本身说成已画错。用户“可以”批准分别建立下楼到达和接触推门参考。本新单位封存参考图上限4、视频提交上限0、一次静态独立复核；没有自动恢复旧视频attempt或更改旧预算/消费/UNKNOWN。

使用已有scenario-identity-library、scenario-seedance-storyboard及builtin imagegen，先实际查看董文慧identity-v1、L01-X、关门和开门参考并按各自职责绑定；原身份SHA53075b370bc0dd00285d4384e74cd521d8672243a417801f177f807776e69458与灰褐外套/深灰裤保留，不继承身份图灰背景、多人排版或E02服装。新图归referces/shizhen/macro-opening-20261027/action-sequences-04/：A1-descent逐级向下的中途状态，A2-arrival关门前低平台手空终态，B1-contact-push右手持续接触的向内半开态。观察三张输出后发现A2手空而旧关门图已握把，故在既定第四次上限内补B0-before-contact关门前未伸手起态，避免把缺失的伸手直接交给接镜跳过。四次调用均known outcome，没有自动重抽或fallback；宏观builtin制图计数22→26，宏观视频仍5，图像真实结算待确认，本轮视频费用为零。

审看板的review IDs与实际文件名明确映射在reference-sequences-v4/reference-input-plan.json：A0旧L01-X→A1新下降→A2新到达；B0新未接触→B1旧关门接触→B2新半开接触→B3旧开门扶住，共7张。两组分别承担下行到达和接触推门，拟用途不冒充actual image bindings。A2→B0换机位保留门关闭、右手空着、人物在平台门外，不预设五秒剪点；未来需选择真正可容纳选用状态图的已核验2.0模式，核对actual request，不能把审看板上的中间态等同送入模型。没有在本轮修改Production Shot、Registry或Manifest，没有视频submit/activation/P6/final acceptance。

七张PNG全部逐张查看、完整性/SHA与HTTP200字节核验；四条实际制图提示词为纯中文。实测新B0-before-contact原宽1671，其余宽1672，均高941；未暗中resize/crop或声明像素保护。A组人物因走远变小，不能把这种设计硬填成同subject-scale匹配。独立Chromium桌面与手机布局载入七图、点击原图链接成功，无pageerror；board.png和board-mobile.png为真实网页截图，不是模型合板或视频首帧。审看入口http://127.0.0.1:8883/outputs/shizhen-episode01/macro-opening-video-20261027/reference-sequences-v4/index.html，沿原Range服务提供；干净单图不包含审看编号或箭头。

同一native只读reviewer /root/macro720_review、reviewer_high完成新用户批准静态包的一次独立复核，宏观累计第8轮／本单位有限上限8，前7轮保留。查看并核验7张图，finding为空，未发现A2→B0或B组可明确证实的空间、手别、接触状态或门扇方向矛盾。Parent对照同一门/窗/栏杆、电箱、手空到接触及门自由边后，保留为REVIEWED_CANDIDATE；不将此写成自然下楼、持续握把、一次推门或细微听辨的动态PASS。动态、声音和human接受均NOT_EVALUATED，原两条楼梯失败视频与Gate字节/FAIL状态不变，B6 exact SHA仍d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a。

新单位来源/用途、图片意图与结果、独立复核、浏览器和核验receipt均归outputs/shizhen-episode01/macro-opening-video-20261027/reference-sequences-v4/，主receipt verification.json。没有共享工程变更；任务脚本py_compile、docs_contract_gate和diff检查为对应验证，未跑完整工程测试或新增验收规则。record-ai-video-session继续同一topic记录，distill-ai-video-learning评估no_candidate：本轮是静态准备改善，没有新的受控动态实验或可提升为普遍模型结论的证据。PNG和网页截图本地保留，Git推送提示词、来源/用途及核验metadata，未发布影片。


## Descent Source And Local Arrival Reframe

用户“開始吧”授权按新参考分别动态验证下楼到达和接触推门，Parent封存最多两源、每源一次、零自动重抽，宏观5→最多7；先A、仅媒体Gate通过才B。时长按完整行动分别预留8秒，不把5秒或clip边界作为强制剪点。选seedance_2.0_vip／multimodal4／1080p／16:9／native audio，实际画布核验8000ms、1080p与三图支持，A新空节点node_hpjhj0pbj1。输入为新参考包A0旧L01-X、A1新下降、A2新低平台到达，实际三条reference角色、顺序、hash、三个markers与443字符正文（去除markers为410）均通过lint；没有把中间态留在审看板，也没有新增图片生成。原完整楼梯目标和未完成的B推门显露/反应保留在unit-intent、source-preservation-diff和brief中，不以A源通过替代完整MC03–MC05。

准备阶段恰逢另一窗口reference-planning修改暂时引用尚未加入的ShotFacet，standard loader报AttributeError，尚无生成POST。该次只写本任务data/row/三条图片观察，Parent没有修改对方源码；依赖导入恢复后通过独立completion caller完成尚未执行的准备尾段，没有重复已写exclusive文件。一次自写lint误把当前native reference角色叫reference_image，当前adapter实际为reference，原失败lint保留为initial-role-name，核对源码后修正技术别名，不放宽图数量或顺序。canonical bootstrap／strict loader／compiler及Budget/egress/durable intent/一用permit沿原owner执行，未改共享规则。

A单位为outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-v1，canonical根runs/shizhen-macro-opening-20261027/MC03-descent-v1。唯一submit在2026-10-27T10:52:11.975569Z受理，查询同一任务至succeeded并fetch；真实宏观累计6次，旧S05 UNKNOWN仍隔离。内部每源1500CRD、A后累计9000CRD是预配置保护上界，不是价格；本轮视频1次，实际结算待确认，条件B尚未提交。

原MP4 SHA326e4fcb83b4bfcd232a3efefab44bd52f0caef6c7be2b3242a0042cca41e43e，14,440,394bytes，1920×1080，container8.065秒、video8.016667秒／193帧，AAC44.1k双声道。nominal60/1不是实测播放率；按actual PTS观察，不retime。显式project-local video-analysis MCP绑定exact片并取17帧，无local scene-change候选。取帧中人物持续背向下楼、走到低平台关门前、双手空，未重现反向上楼。一次盲audio-understand绑定exact source/audio SHA、HTTP200，仅识别规律硬地脚步与房间回声，无可辨语音；不证明衣料、滴水、逐步同步或人类听验。Range206、声画完整decode及独立Chromium1x原声开启播到结尾通过，仍非质量接受。

同一native只读reviewer／reviewer_high完成累计第9轮A实际媒体取帧复核，17帧finding为空；未连续原速观看/聆听，不能据此否决后来的用户反馈。用户对完整看听问题回复“最後的時候樓梯懂了正常嗎”，进一步定位“右下方台阶边缘在抖／变形”；没有回答“可以保留”，Parent不借此推进B。末段5–8秒墙窗栏杆及选定台阶区域的整数NCC位移最佳值均为0，但该测量不能排除局部/亚像素/纹理不稳定。另取6–8秒0.25秒原尺寸局部帧，并做同一MP4原像素／1x局部循环诊断页；用户明确回复“原像素回放仍然抖动”，因此不能只归因为整幅缩小显示，源片按human报告的局部观感缺陷FAIL保留，结构形变根因仍未确诊。相关证据在qa/human-quality-feedback.json、static-geometry-comparison.json与stair-edge-tail/，未把采样或NCC当human接受。

Parent先尝试不新增生成的静态背景补片：同源frame144／6秒、右下ROI1000,835,760,245，人物已在ROI上方。直接geq采RGB造成少量边缘像素变化，保留拒绝PNG；改为独立alpha加alphamerge后，所有RGB与同源帧逐字节相同，ROI外透明。该路线未实际用于出片：bootstrap先拒绝将captured开发VIDEO直接绑为Production角色，纠正为原preview-use后，又拒绝pending generated_video上任意绑定背景PNG角色；当前caller所需普通图片叠层未沿非广告语义接通，Parent未伪造ad plan、绕准入、普通import原FAIL视频或修改Gate。两次prepare拒绝均发生发布前、target核对为空；同源PNG补片仅保留为未采用试验，不宣称修复已执行。

随后改用现有FixedTransform的有动机到达近景：完整保留原源[0,144)全景和[144,192)同一次低平台到达，后者只重取景，原速原声、无倒放/重演/冻结/叠化。第一本地候选MC03-descent-edit-v2通过canonical capture→CompositionSpec→ResolvedTimeline→HyperFrames software导出，但Parent查到6秒后第一步脚边过紧、尾段原AI说明被裁，故保留FAIL候选，不交作通过；SHAefc254158826a4504263b019cd0633e4a91fb0f44b1a5436dd7a504f40ff2979，7,003,964bytes。一次render caller在input receipt不存在时即停止，实际renderer尚未启动，不算额外render或未知副作用。后续有限本地上限由1扩到2仅为已见脚部覆盖回归，旧候选/计数保留，没有新Video Provider调用。

最终候选MC03-descent-edit-v3放宽下沿：末两秒FixedTransform translate(-1223,-344)、scale1.637，约取原图747,210,1173,660，双脚与关门前平台完整入画；前六秒正常灭火器与管道保留。近景明确为数字放大，不冒称新生高清；原AI生成字样在全景源中可见，裁切尾段用现有text_layers的来源说明承接“AI生成”，没有改B6片名/字体/音乐。192帧8秒，独占CompositionSpec→ResolvedTimeline，usage_scope=development_audio_preview；source windows连续、48k样本窗0..288000后接288000..384000，0dB无fade/retime、无新增声音。选software沿已验证参数，没有改renderer或node_modules。源捕获保留qualification谱系，未把原片FAIL重新资格化或Production激活。

修订03 exact SHAbaecafca35d096811b8e544fda4944c5ce3e2f043afa0b185083ce31f27d9384，7,059,018bytes，1920×1080／24fps／192帧、8秒、AAC48k双声道。审看入口index-descent-edit-v3.html；原片和第一本地候选页面分别保留问题与替代提示。全decode、Range206、Chromium1x不静音播至结束、HyperFrames lint/check/render证据通过。显式video-analysis MCP绑定新MP4取16帧，另有32张0.25秒actualPTS帧；MCP仍漏报6秒cut，以local scene detector与直接边界为准。新exact片只做一次盲audio-understand，识别硬底鞋脚步与房间回声；两条音频观察对应raw和新片，未拿原片报告冒充新SHA听验，真实账单待确认。

同一reviewer累计第10轮，仅一次最终本地候选复核；有据有限上限11保留未来B一次，前9轮不重置。查看32帧并直接解码143/144/147帧（5.958/6.000/6.125秒），未见源阶段倒退/重演或脚被裁，末段右下原前景梯级已出画，finding为空。Parent接受该有限视觉观察；未签剩余区域时间性抖动、原速景别跳变或声音连续性通过。prepare-assembly-review与verify-assembly绑定exact新MP4/timeline/render report，显式evaluator为sampled_frames、未听验，真实verdict NOT_EVALUATED；没有用技术结果或renderer成功冒充human。修订03Post-Media Gate保持NOT_EVALUATED，完整8秒看听问题已发用户，B尚未submit，原raw FAIL不覆盖。主receipt MC03-descent-edit-v3/verification.json，A源receipt MC03-descent-v1/verification.json。

本任务新增1条生成视频、2次有界本地render、0次imagegen、2次exact盲音频观察；宏观视频累计6，条件B预算未消费。B6 exact SHA仍d64aef43ddb97df8387adc03bd2a6ec71d6f1d5d901942a1d97082abc84a532a。无本任务共享工程改动；并行aa10dee reference-risk功能与audio修改不归本任务，不stage或代签。任务脚本py_compile、docs_contract_gate及diff检查为对应验证，非完整工程回归。record-ai-video-session更新同一topic，distill-ai-video-learning评估no_candidate：新A与原完整事件同时改变覆盖、机位、参考和动作密度；单条改善不能孤立证明某个变量或普遍模型能力，局部观感反馈也不由单一相关指标推导根因。媒体本地保留，Git只推caller／来源／审看页与核验资料；未发布、未签Production/P6/Final Acceptance。

## Static Stair Image Repair

用户随后要求“那個樓梯你就不能給一個image嗎”。本轮选择实际以固定图片覆盖背景，保留原8秒全景与人物运动，不再用切近避开问题；没有新剧情、换人、重新生成视频、修改B6、字体或音乐。新单元为`outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-image-v4/`，审看入口`index-descent-image-v4.html`。Macro真实视频计数仍6，B推门未submit；旧raw FAIL与修订02/03历史不覆盖。

补片像素取同一raw的第144帧／6秒，来源PNG SHA `019d2a89114271d91d70827269ba7b4ae97bf1250c618c59b6cafb6f6c1e556c`。新`stair-lock-rgba.png` SHA `09590726eff3c4758ebe885cf253db020c82297af73cbb4438697c4455a46106`，1920×1080 RGBA，RGB全部与来源帧逐字节相同。Alpha外框1000,835–1760,1080、8px羽化；比旧矩形更保守地将脚部范围1290,835–1581,899完全透明。旧版“人物在ROI上方”仅来自较疏采样，不能作为足够避让证据；本轮另取6–8秒每0.125秒16帧并核对脚部，旧矩形不使用。没有用imagegen重绘台阶或改人物；补片只在源帧144..192生效，原AI标识保持。

现有Composition入口拒绝普通PNG-only叠层，因为`graphic_layer_ids`此前与AdCreativePlan一并要求绑定；captured原声布局也把图片误算作第二主视频。最小共享修复位于`composition_contracts.py`和`_composition_visual.py`：普通registered raster image沿已有graphic层、asset role/type、同一ResolvedTimeline与HyperFrames解析；仅从captured主视频数量/连续音轨窗口检查中排除显式声明的图片层，继续核验每Shot确有主视频、原音频exact provenance/trim/gain/fade、Development隔离。商业图文和广告声音仍要求exact AdCreativePlan，未伪造广告计划，未改QA/paid/egress/permit/activation Gates；未新增renderer、timeline、依赖、Provider或自动动态遮罩。原source FAIL视频仅经`prepare_qualification_preview_input`捕获，仍不绑定Production主角色；PNG以现有reference IMAGE角色登记。

按TDD先观察普通PNG无广告计划测试因旧入口失败；最小修复后124项composition/ad测试通过。真实接入又暴露captured原声布局的限制，在修改该路径前先跑新测试观察有效叠层被拒绝，再修复并跑当前代码159项composition/caption-preview/repair-admission/source-audio测试全通过；错音频来源、短音轨、缺主视频仍拒绝。当前另跑原声/retime/subtitle回归73通过、17跳过；使用已有系统`libfreetype.so.6`的进程级`LD_PRELOAD`解决Conda libass链接冲突，没有安装依赖或修改系统环境。另有2项Runtime Skill边界测试、docs contract与task architecture检查通过。

正式Harness不标通过：初次focused封存较早3路径，后续staging新增captured音频路径导致snapshot不再覆盖最终delta；其中47项voice通过，composition/audio大组1074通过、23跳过、1项因原生libass依赖`FT_Get_Transform`缺失失败。上述进程级环境修正后的73项回归包括该字幕失败测试。最终5路径related入口在未改动的`AGENTS.md`篇幅预算检查即失败；独立policy audit还报告HEAD已有9个未映射路径／5个未引用测试，均非本轮新增，未改政策放行。完整工程回归未完成，相关receipt保留于`.agent/harness/runs/shizhen-raster-overlay-{focused,related}-20261027/receipt.json`，补充验证与限制见新单元`qa/engineering-checks.json`；不能将手动局部通过冒充正式related或full PASS。

实际渲染沿canonical bootstrap→strict loader→CompositionSpec 2.3→ResolvedTimeline→pinned HyperFrames 0.7.103 software；零至六秒源窗0..144及六至八秒144..192连续、identity transform，PNG仅随第二窗叠加，无新增摄影切镜或重定时。原声布局及静图trim的拒绝均发生在resolver阶段、实际renderer尚未启动前；静图沿Shot全窗不设置video trim，未放宽静图校验。本轮实际本地renderer只执行1次。192帧／24fps、8秒、384000音频samples，usage_scope仍development_audio_preview，源Manifest渲染前后相同，无Production激活。

新片`失帧-下楼到达-1080p-台阶静图修订04.mp4` SHA `76d27a534fe5e97e2dc39f4833cc1c9e9a6f89639e3fc240e20581e073a7c9b8`，7,533,163bytes。已显式调用project-local video-analysis MCP，另取32张actual PTS帧、全decode、HyperFrames lint/check零错误、Range206和Chromium1x不静音实际播至结束。补片不透明像素的平均时间标准差由raw 1.272降到output 0.093，只证明选定区域时变降低，不代表观众感知或整体空间通过。完整解码48k双声道PCM与修订03逐字节相同，SHA `e1355ff057289357dd2ecb5b485c8c15612e91941ad07e26ece95d2e98170fac`；只经同音频identity桥接旧盲观察，不把旧MP4报告或先前市政接受搬到新片。新增远程音频调用0，新增生成调用0，新增生成/分析费用0。

复用原native reviewer_high `/root/macro720_review`完成一次只读复核，宏观媒体第11轮／本单元上限11，旧10轮与计数保留，不因换候选重置。查看32帧、alpha和5个源码/测试/文档hash；未发现遮脚、静止人影、重复脚、明显补片接缝或具体准入旁路，finding set为空。Parent接受有限取帧和代码观察，仍不签原速时间性稳定、补片启用瞬间及声音通过。此为本次有界复核，未来B如需审查须先保留历史并合理封存新有限单元。

`prepare-assembly-review`和`verify-assembly`重新绑定exact新片/timeline/report，sampled_frames、未实际听验，实际结果NOT_EVALUATED。新Post-Media Gate身份/行动/固定全景仅按已看证据PASS，performance/space/art/sound保持NOT_EVALUATED；STOP_BEFORE_NEXT_SHOT，已向用户发完整8秒看听问题，不把静图、量化、空finding或播放器成功当视频通过。主receipt `verification.json`，分项`qa/post-media-gate.json`、`patch-verification.json`、`assembly-verdict.json`；B6 SHA仍为原`d64aef43...84a532a`。媒体/PNG留本地，影片NOT_PUBLISHED，无P6/Final Acceptance。当前代码及记录未commit/push：正式验证被上述既有文档预算／policy问题阻断，且用户原速声画认可尚待；保留本任务staged源码与其余本地owned资料，不把检查失败隐藏为通过后发布代码。

`record-ai-video-session`继续更新同一主题；`distill-ai-video-learning`评估no_candidate：同一源的单次固定补片尚缺原速human接受，局部像素变化也不能提升为跨模型稳定方法或下楼动作规律。不创建学习占位、不修改Skill/Policy/Gate。另一窗口audio-understanding及through-S05文件保持原状。

## Isolated Stair Geometry Reference

用户展示之前下楼时逐渐露出的台阶，指出“之前的暴露的楼梯是弯的，不对劲，你开始给的referces就有问题”，并指定将楼梯单独做成白底参考。Parent承认此前修补末两秒抖动、误交透明补片及随后只给原片全帧，没有解决这项结构准备问题；没有将用户追问记为修订04接受。用户截图作为独立反馈原件exact copy保留在新参考目录。它支持当前素材的几何问题反馈，不证明所有动态失败只有参考这一个原因。

沿scenario-seedance-storyboard与内置imagegen完成一个有界新单元：生图上限1、视频0、自动重试0。实际仅引用完整原片第144帧，职责限定为旧居民楼灰色石质台阶／黑色栏杆的材质与类型；提示词明确不继承弯曲、扇形、宽窄变化或原图人物/房间。两张用户截图仅用于审查，未伪称实际输入。纯中文正文已核对，要求独立直跑梯段、矩形踏步与上下平台、单侧栏杆、纯白不透明背景。此为独立物件几何参考，不将其作为人物动作首帧；未改人物、剧情、B6、字体或音乐。

唯一内置调用返回后，将输出exact copy保存为`referces/shizhen/macro-opening-20261027/stair-structure-white-20261027/stair-structure-white-v1.png`，SHA `8f877405bd8f8432779c42e113177279e1d060be8ebd946a7297509cae0efa1e`，1672×941 RGB、无resize/crop，白底无透明缺口。Parent实际看图核对独立梯段、笔直踏步、上下平台、无人物及房间；为STATIC_REFERENCE_CANDIDATE。生成光栅不能证明精确世界尺寸或施工参数，接回原场景还须重验上下行、栏杆物理侧、机位及门前平台；本次新视角不能靠图像左右直接判断原动作工作侧。没有将图片、长提示词或白底形式视为动态硬约束或验收。

当前图仅实际绑定本次制图输入，未绑定Seedance新请求、未提交新视频或激活Production。对旧片新增用户几何反馈，与已有抖动FAIL历史共同保留；尾部补片没有改变前六秒，因此不能作为该几何目标通过。主来源／用途与静态观察归新目录`generation-intent.json`、`verification.json`及README；审看图片已直接展示给用户。新增builtin生图1次，macro累计builtin图片26→27；macro真实视频仍6，UNKNOWN及旧计数不改。工具未提供本次图像结算金额，不推断为免费。

此轮不改共享工程，不追加工程测试；核验PNG解码、RGB/尺寸/SHA、exact copy和实际图像几何，未作动态质量、真实视频输入或human接受结论。沿同一record-ai-video-session记录检查点；distill-ai-video-learning评估no_candidate，单个静态候选及同源失败链不能升级为模型通用规律或自动采用新的Skill/Gate。本轮Git提交范围仅新白底参考的说明、提示词、来源核验与本记录；PNG和用户截图留本地。前轮共享合成源码及其staged测试不纳入本次提交，既有工程验证阻断及原速声画未验收状态保留。

## City Long Take Draft

本节记录提交c3f637f时的初稿与未决范围；后续运镜方向确认见 City Reveal Move Revision。

用户读宏观剧本后提出“還少一個那種鏡頭串連起來，就是一個鏡頭到底，這個鏡頭覆蓋城市”。本轮只补创作稿，不因这句话直接提交新视频、改写既有事件或重做B6。已询问这是新增城市长镜头还是将三处事件本身也合并为一条摄影轨迹，当前未收到选择；先按可审查的新增MC00候选展开，明确标记范围未定，不把沉默记为批准。

逐镜内容仍归`MACRO-SHOTBOARD-20261027.md`，讨论依据归`MACRO-CREATIVE-DISCUSSION-20261027.md`，没有再建第三份脚本。MC00候选从城市大全景沿主路连续下降，途中用住宅与公交线路所在纵深建立空间记忆，最后在市政正常作业阶段减速落到街侧观察方向，再明确切入MC01；城市镜头内部不插六镜，不预演停控或复制工人反应。视野覆盖城区不等于短时间飞遍全城，新增外部位置关系是美术地理设计，不声称既有源片已经证明地点相邻。楼梯仍按独立白底结构修复，MC06/B6精确入点、两人在场、原声和片名保护不变。

城市镜头暂估12–18秒仅表示移动／理解容量；未测飞行、未选模型／提交时长。旧35–45秒总长不再压缩新增内容，结合既有市政6.833秒、下楼8秒候选及尚未完成的事件，整段先按约一分钟上下讨论。路线过长先收敛距离或调整单镜时长，不偷偷加速、插切、冻结或删B6对白。城市总图、同城起幅／沿途／末态与连续相机预演是待补参考职责，不承诺静图、文字或白模必然控制生成。

本轮没有图像／视频／音乐生成、没有新付费调用、Production mutation或媒体Gate通过；原楼梯几何FAIL及前轮staged工程阻断保留。本文仍是草稿，没有编造approved Shot、Provider prompt、封存输入或实际绑定。工程Risk Gate为NATIVE_REVIEW_NOT_REQUIRED；匹配open-video所需的独立concept check另派原native reviewer_high进行一次只读审查，具体结果归同目录`macro-city-shot-review-20261027.json`。单次文本审查不记为新媒体审看，不重置历史11轮媒体复核，不把文档校验当成运动、接点或human接受。

沿record-ai-video-session更新同一topic，distill-ai-video-learning评估no_candidate：这是用户直接新增的创作要求及候选文字，没有新的受控媒体实验或跨尝试结论，不创建学习占位、不修改Skill/Policy/Gate。

## City Reveal Move Revision

用户询问“运镜高级吗”，Parent说明原高空直接下降偏常规，并提出“近处屋檐滴雨→横移，城市从楼体遮挡后展开→沿道路纵深下降，住宅和站棚依次显露→逐渐减速，钢索进入前景，最后看清工人和控制盒”；用户回复“可以”。本轮将这项认可落实到既有分镜稿MC00与讨论稿，按新增独立城市镜头继续，不把运镜认可扩写为全片无切镜、城市地图细节确认、媒体验收或本轮生成请求。

相机从建筑外侧屋檐近景开始，保持部分远景可见，横移越过外转角才展开城市；沿同一主路缓弧下降，以前景视差和地标显露建立联系，街面附近逐渐减速，由钢索入画交给工人与控制盒。稿中明确不拍极端微距、不借满屏屋檐／墙面掩切、不穿墙或跨牵引线／翻轴；末态仍正常作业，异常与停控动作留给MC01。近处滴水退远、交通声接管、马达渐清，B6原声与音乐不改。

原12–18秒仍仅为文本容量估计，须预演检查屋檐揭示、地标可认、下降速度和末态接戏；人物及实际素材的旧FAIL没有因此关闭。起幅建筑、屋檐转角及相关空间参考尚未制作或绑定，无图像／视频／音乐生成、付费调用或Production mutation。旧核验`macro-city-shot-review-20261027.json`保留，当前修订核验归`macro-city-shot-review-20261027-v2.json`，分别绑定旧／新文件hash与审批范围。

工程Risk Gate仍NATIVE_REVIEW_NOT_REQUIRED：只改创作文本与记录。复用原native reviewer_high进行城市文本概念第2次、仅针对本轮实质运镜修订的只读检查，保留初审1次及既有11轮媒体复核历史，不增加媒体review或重置计数。文档、链接、diff与B6字节身份为本轮验证范围；运动、质量与最终声画仍NOT_EVALUATED。既有staged合成源码／测试和其他窗口audio文件不纳入本轮提交。

record-ai-video-session继续同一主题；distill-ai-video-learning为no_candidate：这是用户直接选定的运镜方向，没有新增媒体或跨尝试对照，不把文字改进升级为已验证的模型规律或Skill/Gate adoption。
