---
record_kind: architecture_implementation
topic_id: creative-goal-preservation-and-completion
learning_eligibility: ineligible
---

# Creative Goal Preservation Implementation Record

Date: 2026-09-27

## Authority And Scope

用户明确要求实现 [plan](../superpowers/plans/2026-09-27-creative-goal-preservation-and-completion.md)，
批准对应 spec 的 M1–M4 offline engineering。Native Codex 在当前 `main` 串行执行，
保留 unrelated dirty `.codex/config.toml`；没有开发 worktree、push/release 或业务媒体执行。
Harness 自有的 detached verification workspace 仅用于 exact checks。

本记录承接 [spec record](2026-09-27-creative-goal-preservation-spec.md) 的待批准设计。
工程改进不解除旧青颜单图方案的用户拒绝，不签发 Production/人类/创作质量 acceptance。

## Implemented Behavior

- `scripts.creative_goal_binding` 只读重开四份 exact inputs，调用原 Director v4 validator；
  校验每个 explicit_user intent 的 constraint/requirement，以及 beat-specific 的所有相关 units。
  global 可无专属 unit，director choice 不替代用户意图。来源 bytes、UTF-8、目录 containment、
  symlink、schema/unknown/duplicate/missing IDs 均有边界测试，不做语义提取或 Production write。
- `final_output_review.py::adjudicate_final_output_details` 产生 ephemeral aggregate/逐项结果和
  全局 evidence gaps；原 aggregate API 投影同一计算。有效 FAIL 优先、incomplete 阻断、
  identity/visual/human proof 规则与既有 no-regression/repair 行为保持不变。
- `visual_quality_report.prepare(..., goal_binding=PATH)` 与 `--goal-binding` 消费相同 preflight，
  无效输入在媒体操作前拒绝。新 `/3` 将封套与三份依赖按预检 retained bytes 封存于 `creative/`，
  reopen 只读此 snapshot。源文件移动可重开，snapshot 换字节/引用/合同不可复用旧 PASS。
  `/1`、`/2` 和旧 positional API 保留范围/身份，并明确目标链未核对。
- JSON/HTML 分开展示 raw answers 与有效 results，摘要列出 exact identity、scope、待修/补证项
  和当前反馈来源。机器不解释用户是否撤回拒绝；Parent 必须披露未决反馈并继续处理已知缺陷。
- open-video 原 reference 承接跨轮意图、独立 concept、实际观看、有限修复与广告/剧情案例。
  routing pointers 保持薄；Runtime boundary guard 禁止 `src/ai_video` import `scripts`。

新增 check/path routes 与 matrix 同步，不新增 Runtime dependency、Manifest/QA persisted schema、
Provider、timeline、renderer、writer、activation owner 或 accepted 状态。

## Verification Evidence

M1 初始 helper 缺失使新增 suite RED；随后 targeted 40 tests PASS。M2 详细 API 缺失使新增
11 tests RED，最终 M2 focused suites 92 PASS，旧 oracle 未改。M3 `goal_binding` 不被接受及
旧结果缺目标链状态已 RED，接线后 focused suites 111 PASS。

Parent 最终发现 Director normalization 边界：`Explicit User` 可被旧 validator 识别但原新 helper
漏绑检测未识别；两项新增测试确实 FAIL 后，改为复用原 `_enum/_normalized`。相关新 helper/
report/Director/runtime/Harness suites 314 PASS；后续 exact verification 以最终 receipt 为准。
另一次合并 suite 在此修正前启动；受影响文件重新验证，不把正在运行的旧加载状态冒充新 bytes。

Chrome MCP 返回 `Missing X server`，没有改动 browser/MCP config。使用已安装本机 Chrome
headless 实际渲染 2 秒 lavfi fixture 的 `/3` 报告，DOM 与截图复核：raw PASS 与有效
NOT_EVALUATED 分开，补证要求和 Production acceptance 边界清晰。输出位于
`/tmp/creative-goal-browser-_mp03q98/`；此 fixture 只证明报告显示，不是业务成片或人类观看。

最终 exact Harness 与 T2 implementation review 在本 checkpoint 仍待完成，不能以当前记录
代替最终 receipt/Parent adjudication。完成后在本节追加 exact identities 和结果。

## Acceptance Boundaries

A1–A3、A8 的结构部分由 binding suite 验证；A4/A7/A10 由 Python/CLI `/3` round-trip、
旧版本与新反馈 revision 独立封存测试验证；A5/A6 使用原裁决器及有效摘要；A9 复用
`test_qa_activation_cannot_rewrite_or_remove_same_goal_requirements` 的 remove 分支、
`test_router_cannot_drop_requirement_by_replacing_baseline_rubric` 与
`test_real_repair_outcome_blocks_regression_and_invalid_evidence` 的 stale 分支。

青颜案例只判断真实包装修复不能自动满足有效广告目标；单镜头剧情案例以递物、迟疑、拒接、
放下与靠近解释行动/关系变化；能力不足案例保留动作要求并提出实际素材/授权选项。
这些 paper cases 不证明已生成有效表演或声音。广告与剧情各一次的真实 empirical acceptance
尚未执行，用户满意与 full human playback 保持 NOT_EVALUATED。

## Learning Evaluation

按 `record-ai-video-session` 自动调用 `distill-ai-video-learning` 的 admission 判断为
`no_candidate`。当前只有同一 engineering slice 的确定性 fixtures、文档案例及旧失败的既有
反馈，没有两次独立实际媒体尝试、controlled comparison 或同范围 adopted claim 的新实证。
不创建占位 Learning Claim，不修改任何 adoption target，不主动 rebuild Agent Memory。
本轮检索曾返回 tagged stale fragments，当前实现判断基于直接重开的源码、tests 和 contracts。
