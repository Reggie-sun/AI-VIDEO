# Hotpatch Warm Holiday Production Plan

**Goal:** 用用户指定的Jimeng Seedance2.0标准版，实际制作58秒竖屏《人还在上班，腰已经入住总统套房》，开头问题与贴片同框，原声、对白/旁白和配乐共同进入成片。

**Approved Scope:** 用户先要求讨论剧情，逐步明确产品提前、先贴出来、问题与产品一起出现、夸张效果加强；批准最终55秒暖假套房剧本后明确“seedance2.0就够了开始吧”。最新使用确认：“按说明贴在衣物上”。原54秒纸浪版停止后续生成，保留两段已生成媒体和全部历史。

**Owners:** Parent拥有新run的creative/source/qa/profile/bound、图像制作、浏览器画布、真实Provider执行、逐镜审片和交付；native bounded_worker仅拥有新run的`execute_film.py`、`bootstrap_shot.py`、`transport_materials.py`等明确实现模块。旧run和其他dirty/index不覆盖，不新增共享引擎功能。

**Contract Surfaces:** `ProductionProject`、Registry、唯一`ProductionStateCommitter`，Jimeng qualification生成、paid reservation/permit、逐镜MCP Gate、qualification preview capture、AdCreativePlan→CompositionSpec→ResolvedTimeline→HyperFrames。默认Production仍拒绝UNQUALIFIED；不绕过Guard、复制Manifest或激活试验媒体。

**Files:** `runs/hotpatch-warmholiday-seedance20-20261024-001/`独占新制作输入、脚本、原片、诊断和媒体receipt；六个Shot独立trial root、同一新canvas六个node。旧run仅作为可核验参考来源，保持历史计数。

**Delivery:** 1080×1920、24fps、58秒；正常速度，不复制、慢放旧片凑时长。按实际2.0支持选择720p源，最终构图/字幕避免把放大当成原生1080p。O1 8s、F1 8s、O2 6s、F2 12s、F3 9s、O3 10s，真实产品HERO5s。内部切镜按动作设计，不机械等分。生成对白保留原声，收尾品牌声补充，音乐让位于对白；缺少音轨不得静音交付。

## Milestone 1 — Creative And References

保存原始任务与最新批准剧本、产品truth和隔衣贴敷确认，冻结六Shot动作/表演/对白/参考职责。主角沿用已生成虚构成人身份，办公室为冷色真实工作场景，想象空间为米白纤维与暖橙灯、沙发/绒毯/套房逐级展开。贴片保留实物米色长条圆端外形，不变成方形暖宝宝。准备空办公室及暖屋/展开套房参考。Parent自审plan；独立native concept review检查产品、问题和夸张动作是否清楚、58秒是否完整，不把review当作观众验收。

**Acceptance:** 第一秒可见贴片及冷环境/保暖困境，贴在衣物上；有下落接住、套房展开和绒毯变拖鞋三次清楚升级；无治疗、实际温度/时长或贴后能力突变。

## Milestone 2 — Bounded Sequential Generation

通过当前登录浏览器新建一部作品的专用画布，保留所有节点、版本与server snapshot。exact model=`seedance_2.0_vip`，4–15秒限制、4000 UTF-16 prompt限制及native audio按当前adapter检查；不换Fast/Mini/2.5。六个独立qualification slots，每次至多500CRD upper bound，整体3000CRD，六小时有限窗口，零自动重试；之前54秒制作的3次paid调用/2次实际生成留明确predecessor引用，不归零。实际报价执行前由Provider核验，金额结算不确认时据实标未结算。

**Acceptance:** 每Shot先exact preview/binding与Paid Gate，再单次submit。exact MP4落盘后显式MCP验动作、人物、空间、商品truth、音频；用户选择自行听音，音频语义不足时请求该段反馈，未PASS不提交下一段。UNKNOWN停止且保留history；known-no-effect只允许原canonical显式有界恢复，不自动重试。

## Milestone 3 — Film And Review

三类声音分别入Registry：exact生成原音轨、需要的本地收尾旁白、有来源音乐。沿原capture与独立审片Project，ResolvedTimeline独占timing，HyperFrames出片；真实产品照片用于末尾5秒，正确中文用后期图文。依每段已接受状态调整相邻剪辑，不改批准主线或弱化夸张动作。

**Acceptance:** exact最终58秒MP4含原声+对白/旁白+配乐；逐帧构图/字幕/接触检查及实际音轨保留检查，独立native媒体审查。正常速度观感与听感仍交用户确认，不把技术PASS当作完整验收。

## Completion Boundary

先交成片给用户审片。用户明确认可后再进行相称完整工程验证和owned-path commit/push、remote SHA核验。稳定checkpoint依`record-ai-video-session`记录并自动学习评估，未形成独立可归因模式不创建claim；不因记录调用额外Provider或测试。

## Pre-Generation Concept Repair

独立native concept review的WH-C01确认O3收尾7秒不足；Parent保留全部批准剧情、其余时长与5秒HERO，将O3增至10秒，总55→58秒，仍在用户45–60秒界内。WH-C02将幻想拉远/升高与结构摄影字段对齐。round2 targeted复查未解决finding为空；这些是文字输入闭合，不是实际媒体验收。所有修订发生于首个generation/paid effect前，旧输入保存在新run/preflight-history/，预算6次/3000CRD不变。
