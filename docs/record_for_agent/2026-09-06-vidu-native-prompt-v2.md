---
record_kind: architecture_implementation
topic_id: vidu-native-prompt-v2
learning_eligibility: ineligible
evidence_index_version: "1"
---

# Vidu Native Prompt V2 Record

Date: 2026-09-06

## Subsequent Live Evidence

同日后续 [S01 compiler2 live attempt04](2026-09-06-jieshi-s01-vidu-v2-live-gate.md)
已生成并检查 exact MP4，Gate FAIL：烧入字幕、掌心朝镜头和机位漂移仍存在。
下方“尚无 version2 媒体证据”仅描述本实现 checkpoint 的历史边界。

## Purpose

用户在核对官方参数后要求“改进／继续”。本轮只改进 Vidu 请求编译和验证，
没有新 Provider submit、媒体生成或 Production state mutation。
依据 [S01 official parameter audit](2026-09-06-jieshi-s01-spatial-hand-repair-gate.md#official-parameter-audit)，
内部 neutral key-value 曾直接进入模型 prompt；没有证据证明服务端改写过历史 prompt。

## Ownership And Runtime Truth

`ViduVideoProvider.compile_request()` 继续通过 canonical common compiler 创建请求；
新 `_vidu_prompt.py` 独占 version `2` 的自然语言投影，替换新请求的旧 key-value 表达。
Planner/readiness、Router、Registry、Paid Provider Gate、committer 和逐镜 Gate 不变。

- 保留 `/1` 已编写的开场／收尾、动作终点、真实变化要求、人物允许变化、场景、空间／轴线、
  摄影机、节奏和参考角色；音频内容沿 authored scene constraints 保留。
- 未指定状态却要求变化、opaque state、rich `/4`、commercial 字段等无法表达的输入 typed reject；
  common compiler 的 lineage、版本与 native hard control 拒绝继续生效。
- 新编译只接受 version `2`。仅该版本 I2V／首尾帧 payload 加 `is_rec=false`；
  历史 version `1` 请求保留原始 payload bytes 与恢复能力，其他 endpoint 不加此字段。
- 不新增字幕开关、Q3 无效的 movement 参数或 seed schema。Native audio 仍显式传递。
  文字锁机位不是 API 硬控制，编译成功不证明画面服从要求。

## Verification And Review

已将 helper 和新测试纳入 `.agent/harness/policy.yaml` 的现有 Vidu 检查组；
新增 routing test 先复现 unmapped failure，再验证修正。Scoped inspect 无 fallback paths。

- 完整 Provider、neutral requirement、Vidu 三组去重运行：1187 passed，114.39 秒；
  此结果在最后 open/close 变化语义和两个 canonical I2V 测试补齐前取得。
- 修正后 Vidu 三文件组：154 passed。最后补充 audio/prose 断言后，
  canonical first-only / first-last 两个用例再次通过。
- Harness 自测：136 passed；docs-contract、record-hook 和 runtime-skill-boundary：73 passed。
- policy-audit 与 docs-contract check 通过；`git diff --check` 通过。
  最终 `architecture_gate check --base-ref HEAD` 通过，0 findings。
- native `reviewer_xhigh` 首轮指出状态变化标志遗漏及 canonical I2V 覆盖缺口；
  修复后同 reviewer scoped re-review：`accept`。双次纯编译仅为非阻断简化建议。

用户明确禁止 worktree；本轮未运行需要 detached worktree 的完整 Harness，
没有 fresh isolated Harness receipt。上述测试是当前工作树的离线证据，不冒充该 receipt。
其他会话的七个 staged runs 保留，不纳入本次提交；未 push/release。

## Remaining Work And Learning

S01 历史 MP4 Gate 仍为 FAIL，S02 不可推进。Version `2` 尚无真实生成和媒体质量证据；
新实验需要新 exact request、有效有界授权与完整 paid/egress/intent/permit，再逐镜验收。
本轮不复用已消费的 attempt03 quota。

按 `record-ai-video-session` 记录并自动执行 `distill-ai-video-learning` evaluation：
`no_candidate`。本轮只有确定性代码／测试，没有新增独立媒体实验；既有字幕现象的
pending learning claim 保持原样，不因本次实现而擅自采用或宣称其因果已确定。
此前 experience retrieval 的 stale 结果仅用于定位，未前台刷新索引。
