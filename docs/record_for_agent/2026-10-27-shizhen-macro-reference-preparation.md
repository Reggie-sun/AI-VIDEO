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
