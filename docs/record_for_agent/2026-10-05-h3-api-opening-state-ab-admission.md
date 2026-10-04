---
record_kind: research_note
topic_id: h3-api-opening-state-ab-admission
learning_eligibility: ineligible
evidence_index_version: "1"
---

# H3 API Opening-State A/B Admission Record

Date: 2026-10-05

## Baseline And Scope

初始干净 `main` / `HEAD` / remote `origin/main` 均为
`c16b2d9528c6a57f41edd3b2fd9d88a137b409bd`，已实际执行 `git ls-remote` 核实远端。
最近 continuity commits 为 `c16b2d9`、`30a312e`、`ac9dfa5`、`76790a8`、`e733d46`、`d234233`。
本任务要求 raw H3 A/B，默认每 arm 一个 attempt；后续用户明确限定 **API_ONLY**。
未启动本地 H3、未调用 generation API、未编辑 continuity contract / Production source。

本轮 observation ID 为 `h3-opening-state-ab-20261005-001`；证据目录
`runs/h3-opening-state-ab-20261005-001/`。它是 admission audit，**不是完成的媒体实验**。
不存在本轮 A/B request hashes、task IDs、raw MP4、fetch receipts 或媒体 verdict。

## Source Admission

使用当前标准 `load_production_project()` 重开历史 S02 的 `production-final` / `production-sealed-v3`
及 S03 的 `production-sealed-v3`，再调用
`accepted_sequence_source(..., require_causal_close=True)`；三者均以
`source Shot requires one exact activated generation` 拒绝。Manifest / active project / Registry
identities 和 bytes hashes 保存在 `source-admission.json`。这是 fixture evidence 缺失及正确
fail-closed，没有证明 implementation regression。

历史 S02 的 durable intent 为 `close_state.kind=typed_text`、`state_hash=null`；execution stack hash
缺失。raw terminal 为 `FETCHED_UNACTIVATED`，raw gate 为 `FAIL`。现有 recipe 不包含针对
`generation_intent.close_state.state_hash` 的 exact semantic acceptance criterion。
不能补写历史 intent、激活失败 source、把 edited derivative 或 prompt 升格为 accepted causal truth。

当前完整 `CausalDimension` 为 `character_presence`、`prop_identity`、`prop_holder`、`hand_contact`、
`prop_functional_state`、`action_phase`、`gaze_target`、`dialogue_turn`、`screen_motion_axis`、`audio_bridge`。
本轮未声明任何一维为已 accepted；未生成 `PreviousShotState`、C2 target keyframe 或 B request。
恢复必须先取得满足当前 accepted-sequence owner 的真实 raw source：activated exact generation、
execution binding / stack、完整 typed close column、raw exact semantic PASS、terminal evidence 和
current source activation Registry；然后由既有 C2 owner 准备合法 target FIRST_FRAME。

## API Capability Research

当前 `MetasoH3VideoProvider` 的 capability / resolve 只表达并接受 `REFERENCE_TO_VIDEO`，
`MiniMaxH3VideoProvider` 只开放 `TEXT_TO_VIDEO`。当前正式 API adapters 没有可选的 H3 I2V / FL2VA
capability，因此即使补齐 source，也不能在本 HEAD 通过 canonical Planner / Router 执行 B。
这是当前 capability coverage gap，不是已证实的 regression；用户禁止新增 Provider capability，
本轮没有扩展 adapter 或直接 POST 绕过 owners。

上游 [METASO nodes.py](https://raw.githubusercontent.com/meta-sota/ComfyUI-MiniMaxH3-API/main/nodes.py)
实际存在 `MiniMaxH3FirstLastFrameNode`，发送 `first_frame` 及可选 `last_frame`；
[api_client.py](https://raw.githubusercontent.com/meta-sota/ComfyUI-MiniMaxH3-API/main/api_client.py)
使用同一 H3 endpoint 和 `MiniMax-H3` model 字符串。原始抓取 bytes / SHA256 在
`upstream-sources.json`；这不证明项目 capability、账号 live acceptance 或内部 checkpoint 相同。
不能把“当前 adapter 仅 Ref2VA”解释成“远端 API 永远不支持首帧”。

用户限定 API 前只读检查了 local profiles：Ref2VA diffusion SHA 为
`9eef934046a0671bc8a5daf87100705e1478419c574cfde70c50fbe6885f76a9`，I2VA / FL2VA 为
`7ad4c73e6e378b822ffd1629f27f632d3787d95f5e468e3af958f98c58df96a5`；共享 runtime 不能消除 checkpoint
confound。该本地候选已被后续用户指令排除，不构成本轮 execution strategy。

## Comparison And Consumption

A 的预期 API strategy 是独立 non-FULL soft Ref2VA：canonical identity / scene references 和 preceding
video soft reference。B 的预期 strategy 是 accepted source → typed HARD_CUT / FULL_CONTINUITY →
DIRECT_CONTINUITY → C2 FIRST_FRAME → canonical I2V。二者均未形成 selected final execution binding。

预期 conditioning 差异可以描述，实际 prompt / native request / reference equivalence 无法证明；
`prompt-diff-proof.json` 明确为 `NOT_EVALUATED`。本次没有完成 controlled 或 quasi-controlled
comparison；结论为 **Level 1 — No evidence**。每 arm `NOT_EVALUATED`，
`OPENING_STATE_CONTINUITY=NOT_EVALUATED`。不能断言新 A 复现 reset 或 B 消除 reset。

本轮 H3 physical submits **0**、新 raw artifacts **0**、H3 usage **0**；没有产生 H3 generation charge。
用户当前明确要求 API execution，历史两份已消费且过期的 preview-bound authorization 不复用；
在 source / B capability 阻断时没有伪造 preview、reservation、authorization、permit 或 start fence。
Kimi investigation 是独立受管研究调用，不能计作 H3 submit 或媒体 evidence。

## Historical Evidence Preservation

重新计算 exact bytes，历史 S02 raw SHA 仍为
`44715c6a44a9ad357abfac34e38db02053b9a7bfa0fa2d82c6705f9bec590b3a`，13,108,563 bytes；
历史 S03 raw SHA 仍为
`fa3d8abc7ad2fbde4be48683800161d53581d7df0fd2c381d274d3fe962b52f4`，8,395,135 bytes。
二者匹配原 gate / terminal；`historical-byte-verification.json` 明确 `admitted_as_new_arm=false`。
历史 **S03 raw = FAIL / OPENING_STATE_RESET** 保留；旧 edited review 的有限结论和文件不改写，
也不进入本轮 continuity verdict。原 [repair record](2026-10-03-metaso-h3-cut-continuity-repair.md) 保留。

## Verification And Assessment

已执行 `make harness-inspect`。干净 baseline 的 targeted suites 共 **227 PASS**：sequence / transition /
METASO / local family / native adapter / Comfy 164，FULL-soft block / hard-cut Router 14，direct H3 API 49。
这是离线工程证明，不是媒体 PASS。命令、elapsed 和 proof boundary 在 `verification.json`；
Router / direct H3 stdout 在各自 `*-tests.log`。本轮文档的 exact staged Harness receipt 为
`.agent/harness/runs/h3-api-ab-admission-20261005-002/receipt.json`；`001` 是此前文档候选的 receipt。

父 Agent 保留 admission / finding adjudication / completion responsibility。受管 Kimi read-only audit
invocation `72e0ee49-4122-46a5-bb7c-f86a4944bf3b` 为 `PARSED` / exit 0、6 wire requests、348.828s；
authenticated `k3` / `max`、sealed `deep` / Docker route 及 required Reads 已核验，费用未返回。
`kimi-receipt.json` / `kimi-report.json` 保存 canonical evidence，`kimi-parent-adjudication.json` 保留裁决：
source admission 和 local checkpoint finding 确认；将“METASO 不支持首帧”限定为当前项目 adapter，
拒绝与最新 upstream source 冲突的 API-wide 外推，也拒绝用 development derivative 降低 B 的 source
要求。该研究调用不作为媒体判定。没有 Production implementation candidate，本轮不触发 implementation final review。

按用户“杀掉llm”指令，显式停止 `jianji-qwen3-vl.service`：`MainPID=0`、`inactive/dead`，GPU compute
process 为空，释放原 25,060 MiB 占用。`llm-stop-receipt.json` 保存真实操作；不自动重启该服务。

`distill-ai-video-learning` evaluation 为 **no_candidate**：没有新的媒体 attempt、controlled arms 或
足以 materially update 既有 claim 的结果；不创建 learning placeholder，不修改 adoption targets。
不需要第二 replicate；第一有效 comparison 尚未发生。generic Production sequence driver 暂缓，
先解决真实 source admission 和合法 API I2V execution，再取得 raw strategy evidence。
