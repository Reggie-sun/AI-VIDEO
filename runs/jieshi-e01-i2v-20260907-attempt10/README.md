# S01 Endpoint Repair Preparation

## Current State

### Latest Continuation — Attempt 12 Generated, Timing FAIL

既有一次追加授权已用于新的肘部屈曲动作方案，原首末帧、seed、广播与QA保留。
2026-09-08 10:45 UTC唯一POST成功；10:47 UTC通过原下载保护下的同任务DNS恢复取回。
MP4 SHA-256 `c56b05e2da5d38bfeddd2d6f58322d84a7d8433c01589112b87d1865b388b7f3`，
3,472,114 bytes。实际 project-local MCP 检查仍为 legacy-03 FAIL：约1.25秒起手，
1.5秒未到位；legacy-05因运动模糊无法可靠判定，NOT_EVALUATED。
其他11项技术/analyzer项PASS，human06/14/17待本片答复，不继承旧片确认。
证据在 `preparation-v4/`；次数 ceiling3/used3，不自动重试，无激活或S02。
下方“追加授权未消费”和 attempt11状态均为历史；以本节及当前记录为准。

### Historical Continuation — Human PASS, Attempt 11 Quality Closed

用户对 exact attempt11 的三项观感问题回复“正常”，真实 MCP bridge 已补齐
human06/14/17 PASS；legacy-03/05 仍 FAIL，诊断只剩 QUALITY_FAILURE。
唯一 committer 已将 attempt11 终结为 FAILED / `video_quality_rejected`，Manifest r38；
Project/Shot r6、旧预留与 paid 文件保留，原参数 replay 零写入。
证据见 `preparation-v4/attempt11-closure.json` 与
`preparation-v3/attempt11-human-confirmation.json`。

此前追加一次的授权仍未消费。onset-only 草稿尚不能解决掌向变化，未形成新
submit-ready intervention；没有新 POST、MP4、candidate activation 或 S02。
下方 human pending、EVIDENCE_GAP 与 r36 是已被本节取代的历史状态。

### Historical Continuation — Attempt 11 Generated, Gate FAIL

金额扩容与同 task 次数追加代码已通过独立 review 和正式 Harness（`7dd8237`）。
在保留旧预留和已用次数后，唯一追加 POST 已于2026-09-08 09:24 UTC被接受，随后成功fetch。
MP4 SHA-256 `cb73c70c1e935d6849b3a91f5fa7ff19d81966647afaf88a010cd00dc89be537`，
3,297,401 bytes。原首末帧、seed20260907和点名广播保留。

17帧/0.25秒检验仍为 legacy-03/05 FAIL：约1.25秒起手、2.5秒近目标，途中仍翻掌。
human06/14/17待新exact观看答复；没有质量通过、激活或S02。正式反馈诊断为
EVIDENCE_GAP+QUALITY_FAILURE，Manifest r36 / Project和Shot r6。
同 task ceiling2/used2、budget available0；不能自动再次POST。
详见 `preparation-v3/attempt11-runtime-checkpoint.json` 与
[当前记录](../../docs/record_for_agent/2026-09-08-jieshi-s01-human-gap-history-boundary.md)。
以下旧pending状态已被本节取代。

### Historical Continuation — Quality Closed, Budget Extension Pending

`6017eed` 的显式质量终结已通过独立复审和正式 Harness。真实 attempt10 已标记为
FAILED / `video_quality_rejected`，原 legacy-03/05 FAIL 保留；下一次 pre-generation
graph 已通过原 committer 提交，Manifest r26 / Project 与 Shot r6。
`preparation-v3/quality-close-runtime-checkpoint.json` 保存 receipt、graph 与不变性核验。
原参数重放无写入，paid-provider 文件和 source09 保持不变；没有新 Provider call 或 MP4。

下一次生成次数尚未使用，但原 ledger available 为 0；旧预留不得伪造结算/释放。
新增有界预算扩容契约尚待明确授权。Planner/graph 准备不等于可提交请求。

### Historical Continuation — Human Evidence Repaired, Runtime Blocked

以下入口缺失与 r23 状态已由上述 checkpoint 取代。

用户授权一次追加修复，并对 exact attempt10 的手部自然、间隙清楚与广播完整清晰
三项观看问题回复“确认”。真实 MCP bridge 已在原视频上追加 human06/14/17 PASS；
legacy-03/05 仍 FAIL。Manifest r23，Project/Shot r6，完整历史三条 experience。
补证与下一版时序草稿在 `preparation-v3/`，新额度尚未消费。

下一版 graph transition 在任何写入前被正式 committer 拒绝：attempt10 仍处于
RUNNING/VALIDATE，现有 runtime 缺少质量 FAIL 的无激活终结入口。不能把质量失败
伪装为 Provider failure 或虚构结算。没有 attempt11 submit、新媒体或下一 Shot。
所需最小 lifecycle contract 见
[当前记录](../../docs/record_for_agent/2026-09-08-jieshi-s01-human-gap-history-boundary.md)。
以下人类待答、r22 与额度耗尽均是上一 checkpoint 的历史状态。

### Latest Result — 2026-09-08

用户授权“解决之后再生成”已执行：legacy history兼容修复通过独立review与正式Harness，
旧16项评价已canonical导入，原四项FAIL保留；当前2.3 QA已选择。一次Vidu提交成功，
经原public-IP下载保护下的进程内DNS修复取回MP4，SHA-256
`94e7480dfce4374f9b3a4de3006797aae033526a8fc36faa8f9ac19ae0406954`，3,325,775 bytes。

project-local `video_analyze`实测1080×1920、24fps、97帧、4.042秒，AAC48kHz stereo；
medium转写原点名广播为0–2秒。17帧/0.25秒检查发现1.5秒才开始抬手、约3秒接近
目标，且途中掌向仍改变：legacy-03/05 FAIL。新片human06/14/17待答，不能继承旧片批准。
Gate为FAIL，未激活、未推进S02；一次提交额度已用完，禁止自动再次POST。

strict reopen：Manifest r22 / Project r6 / Shot r6，attempt RUNNING/VALIDATE，
一条imported history与一条新generation experience；原attempt09 Manifest完全未改变。
`preparation-v2/`保存exact preview/binding、POST审计、fetch结果、MCP原始响应、Gate、
canonical反馈诊断与runtime checkpoint。下方是本次生成前的历史准备状态。

### Supersession — 2026-09-08

用户对 exact attempt09 明确反馈“手部出现明显变型”，并对前3秒的小间隙可读性
回答“看不清”。`human-visual-review-attempt09-20260908.json` 保存原话和媒体 identity；
legacy-17 / legacy-06 均为 human FAIL，不推断物理接触或厘米深度。
`historical-human-supplement-20260908.json` 与旧证据在原2.1 rubric 下合并，
`historical-diagnosis-after-visual-20260908.json` 实跑仅 QUALITY_FAILURE，
不再有 EVIDENCE_GAP；原始证据和旧 NOT_EVALUATED 不覆盖。
`historical-decision-after-visual-20260908.json` 的纯历史 Router 重放为
REASSESS_FEASIBILITY，不是当前2.3 rubric 的可提交决定。

当前 strict reopen 仍为 Manifest r4 / Project r6 / Shot r6，active_qa_policy=None。
旧attempt09没有新版execution binding，v10没有durable generation experience。
当前committer要求新binding的历史与Manifest完全一致，且没有旧无binding历史的
导入入口；不能清空失败历史、伪造旧binding或绕过提交校验。需先解决这个明确的
兼容性边界，再绑定已有2.3 rubric/evaluator并重新规划。没有新Provider提交，
单次修复额度未消费。详细当前记录见
[S01 history boundary](../../docs/record_for_agent/2026-09-08-jieshi-s01-human-gap-history-boundary.md)。

下方2026-09-07状态为历史准备记录，其中“待补真实间隙答复”已被上文取代。

2026-09-07 最新用户指令：“那我的判断出问题了,你就修复手的问题就好了”。
原点名广播保留；普通报站改稿撤回，未进入 runtime。旧片手部 human FAIL 保留。
`preparation-v1/` 已保存 strict planner/context/lifecycle、同额续期 profile 和完整
candidate/acceptance projection。当前 acceptance version 2.3；所有 measurement
面向被评价 exact artifact，新生成音频不继承旧片批准。早期未通过表达/measurement
检查的草稿另存为 `*draft*.json`，不是 active candidate。

public Router 已实跑 `decision-awaiting-visual.json` 为 EVIDENCE_GAP；该历史评价与
decision 使用早期 rubric 2.1，不能作为 2.3 的最终 decision。真实间隙可读性答复
到达后须按当前 rubric 重算；没有已提交任务，不需要恢复 Provider outcome。
此处待补的是旧片前 3 秒小间隙的观看结论，不是厘米标定或旧手势接受。
native 表达检查已通过，不代表 compiled request 或 submit readiness。
尚无 compiled/resolved request、paid preview、authorization、intent、permit、POST 或新 MP4。

用户在 2026-09-07 对已展示的 `endpoint-repair-03.png` 回复“确认”。输入 SHA-256
`d9a21860e91cadc7cf4cfe0ce74a44b57c2aa6d600b8c8cc06dc17e4fb4cd1da`，
2,051,993 bytes，941×1672。该确认只批准新图作为 S01 末帧，不是旧视频或新视频质量验收。

`bootstrap_and_import.py` 已执行成功，经 `ProductionStateCommitter` bootstrap、
HumanImageImportReceipt、project/registry/dependency transition 正式登记到
`production-s01-v10/project.yaml`；strict reopen 为 S01 revision 6。
receipt hash `c08cf7784be9dd5bbc3cd5454f70e56a15f3a3efb504908a13ad62aecaecced0`。
不要重跑 bootstrap；已有项目必须使用显式后续事务或 recovery。

## Evidence And Remaining Work

`diagnose_previous.py` 是只读旧媒体/旧 Gate、写本目录诊断投影的 offline helper。
它保留旧表全部 15 项；原生源中的字幕不冒充 final composition，原 FAIL/NOT_EVALUATED
不改写。JSON 是本次回溯投影，不声称旧请求当时已经封存新的 recipe schema。
当前已实跑为 `EVIDENCE_GAP + QUALITY_FAILURE`，`next_owner=evidence_owner`。
该投影没有为新请求准备完整 native expression coverage，不能拿来提交。

旧片手部动作/掌向 FAIL 保留；原表仍有约 2cm 深度、身份/胸牌及人工试听缺口。
应对同一 exact MP4 补证；若尺度或阶段解释错误，由 acceptance owner 显式版本纠错，
不能篡改旧表、移除 required item 或以新图审批代替证据。

`planning.py` 与 `request-draft.json` 绑定新图和侧向微曲手势，尚无可提交的 compiled request。
下一次是最多一次同 Vidu Q3 Pro 的 `production_repair`：新 endpoint、动作措辞、
新固定 seed 与同额 operator ceiling profile 续期均须逐项记录 actual delta。
历史 seed 未控制，不声称单变量因果。保留 native audio、原首帧、4 秒源/3 秒成片目标。
补证后仍须 public Router、完整 recipe/native coverage、fresh exact profile/preview、
Budget Guard、egress、durable intent、one-use permit；不得调用旧 public API 或跳过 Gate。

本目录尚无 Provider submit/poll/fetch、permit、付费预留或新 MP4；没有激活 candidate 或推进 S02。
