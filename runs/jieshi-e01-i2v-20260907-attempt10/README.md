# S01 Endpoint Repair Preparation

## Current State

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
