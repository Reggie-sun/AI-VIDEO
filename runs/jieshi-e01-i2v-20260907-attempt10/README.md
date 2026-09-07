# S01 Endpoint Repair Preparation

## Current State

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
