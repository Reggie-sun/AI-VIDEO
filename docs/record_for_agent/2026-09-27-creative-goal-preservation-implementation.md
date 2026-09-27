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

最终 code checkpoint 已完成 exact Harness 与 T2 implementation review；下面分别记录
机器验证、审查与 Parent adjudication，不以本记录替代原 receipts。

### Exact Code Checkpoint

`ce6ec9be2b6d0f890423ad57c4bc370974423a9a..6019f3969cb49e68f30c5f29f85c284c747f7a0e`
的 Harness 已完成，receipt 位于
`.agent/harness/runs/creative-goal-implementation-20260927-01/receipt.json`。
12 个执行 checks PASS，`open_video_skill_tests` 由同一 run 的完整覆盖 check 承接；
`verify-receipt` 在该 exact code checkpoint 返回 `fresh=true`、`integrity=true`、
`artifact_integrity=true`、`coverage_closed_same_run=true`。关键 suites 包含 Production Review
664 PASS、Final-output / No-regression 63 PASS、visual quality 69 PASS、goal binding 161 PASS；
无 unmapped/fallback paths。后续记录提交不改变该 code checkpoint 的测试字节或验收标准，
记录 closure 的 freshness 由其独立 exact receipt 核验，不把旧 HEAD receipt 描述为新 HEAD 的证明。

### Gstack Browser Verification

用户后续明确要求使用 gstack browser，按 `browse` Skill 实际打开同一 fixture 报告。
accessibility snapshot、console、media 与页面 JS 检查通过：无 console error、两张帧图
均加载；375px / 1280px 的 `scrollWidth` 等于 viewport width，没有横向溢出。
手机、平板、桌面截图已保存并复核，raw PASS 与有效 NOT_EVALUATED、补证项和当前来源
均可见。证据目录仍为 `/tmp/creative-goal-browser-_mp03q98/`，包括
`gstack-checks.json`、`gstack-{mobile,tablet,desktop}.png` 和 `gstack-snapshot.txt`。
`gstack-checks.json` SHA-256 为
`d82c9e0a802eb6282ca915aadbb4bac0de95c5f6fcd500bd261cd24f9956830b`。
这证明开发报告的实际显示；fixture 不证明任何广告或剧情内容质量。

### Independent Review And Parent Adjudication

本变更按 accepted plan 的 T2 contract 要求 stable implementation review；原 aggregate QA、
persisted schema、acceptance criteria 和 canonical owners 未变，不把详细计算升级为新验收语义。
采用一个受管、read-only Kimi `deep` reviewer，sealed inputs、Docker containment 和 matching
qualification `4f2d5dc8-4234-4665-b382-e82f1ad6cc00`。两轮均绑定同一 code commit；
过程中只更新本记录，不改 code/tests/Spec/Plan/criteria，未叠加 Native reviewer。

- Round 1 `ab33aa6b-f491-4dfe-88de-05c4d2e77dd5`：1200s 上限超时，15 wire requests，
  `OUTCOME_UNKNOWN`，无 terminal report；保留全部 consumed/receipt 与隔离 partial 输出，
  不视作完成的 review 或 acceptance。Parent 检查了 canonical receipt 和过滤后的事件计数：
  32 次 Read、0 tool errors、无 terminal。只读 containment 与未变 code bytes 确认后，
  用较小 context 发起独立有界 round 2，不重放该未知 response。
- Round 2 `bf2be738-db45-4fc3-bf71-f091676d19d1`：900s/16-request ceiling，实际 517.15s、
  7 wire requests，正常退出、`PARSED`；16 complete Native Reads，覆盖全部 13 required paths。
  所有 observed file hashes 与当前 bytes 一致，canonical artifacts 的 size/SHA 核验通过。
  request/response model 均由 authenticated endpoint 机械观察为 `k3`，effort 为 `max`，
  route 为 qualified `deep`；这与 fake containment 的 `live_identity=NOT_EVALUATED` 分开。
  `worker-report.json` SHA-256：
  `370b4125f8a213965e2a5699b3d68c388cc2b36280a59cf330a17908fde85b98`。

Latest report 的 findings/questions 均为空；Parent 未把 `PARSED` 自动当作 acceptance。
对其 uncertainties，Parent 从 exact base `ce6ec9b` 重开源码，确认提供给 reviewer 的原
aggregate algorithm 与 baseline bytes 相同，`--content-kind` 在基线已为 required；
直接读取 `StrictModel` 的 `extra="forbid"`，并复核 policy 的完整 check argv / covers_check_ids。
其余 freshness 与真实媒体范围的限制保留为本文明确边界，不构成 offline engineering blocker。

Paper cases 的独立判断引用原始拒绝与包装/广告表达差异、信件的行动/反应及关系变化、能力
不足时保留使用 requirement 的具体选项，未以镜头数或 template score 判断作品。
Parent 结合源代码、旧 oracle、fresh-at-code-checkpoint Harness 与可核验 review，裁决
`6019f3969cb49e68f30c5f29f85c284c747f7a0e` 的 M1–M4 offline engineering 为 KEEP。
没有 unresolved implementation blocker；广告/剧情 empirical 与人类验收仍未执行。

### Managed Cognition And Publication

最终 code 稳定后按 AOCI 当前流程更新四个受管理对象；Verify、Check 和 Guide 均确认 aligned。
记录收尾仅更新 observe fingerprint，不制造新的索引语义。压缩后的 Whole-Index 交付已确认，
attestation 输入两次未被 Schema 接受（含一次纯字段修正），未继续尝试；完整模型认知验证
仍未完成，不主张完整系统掌握。治理对齐与模型认知证明分开，业务结论基于实际 source/tests。

Task commits 为 `949a05a`、`beb8112`、`6019f39`；本记录及 observe metadata 的 closure 另行
提交，并以 `.agent/harness/runs/creative-goal-record-20260927-02/receipt.json` 独占该
closure 的执行结果/freshness。publication 为 local-only，未 push/release，unrelated
`.codex/config.toml` 未 stage/commit。

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
