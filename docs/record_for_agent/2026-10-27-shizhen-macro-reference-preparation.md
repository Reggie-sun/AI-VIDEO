---
record_kind: session_summary
topic_id: shizhen-macro-opening-reference-preparation
learning_eligibility: ineligible
---

# Shizhen Macro Reference Preparation

Date: 2026-10-27

> **Current Update:** 用户要求继续后，本轮补齐六镜12项静态状态职责。L03/L04与市政组旧阻断已有替代图；下文原检查点保留为历史，最新事实见末尾Continuation 02。视频/平台/人工仍未评估。

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
