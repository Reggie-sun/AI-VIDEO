---
record_kind: session_summary
topic_id: aoci-index-maintenance
learning_eligibility: ineligible
---

# AOCI Index Maintenance

Date: 2026-10-02

## Scope And Current Truth

用户要求维护 AOCI。任务开始于 `b844bd3`，沿既有 33 对象 managed scope，完整复核
87 个 observe 路径和 6 个 stale owner；没有扩大索引范围、修改业务源码或改变 Root、Meta、
scope、预算及 observe policy。既有 staged `.codex/config.toml` 不属于本任务。

AOCI `0.1.0-rc14` 官方事务更新 6 条 Entry，首轮 Verify、Check、Guide 均通过：
`governance_aligned=true`、`complete=true`、`next_action=none`；stale、missing、orphan、
unbaselined、observed pending、Recovery 与第三方冲突均为 0，budget 为 healthy。
此结果证明索引治理对齐，不证明 Provider、媒体质量或 Production acceptance。

## Source Review And Parent Decision

33/33 旧 Entry 完整交付、Host body 确认、Challenge 10/10；该认知绑定旧 index
`caec246602155339564f56a9ac79b0e615b9b26958a7581ae2d443fc86fbb6c8`，不冒充更新后 identity。
两个独立 read-only native mapper 分别全文复核 4 个文档 owner（3181 行），以及
48 个 observed source/tests 和 2 个 stale source owner。Parent 重验 93 个源文件的 exact bytes、
关键代码与当前契约；这些读取不等于执行了业务 tests。

受管 Kimi invocation `47fd551f-f01a-4882-b3e9-197fb3e99921` 使用 deep/k3/max，
11 次 wire requests 均为 `IDENTITY_VERIFIED`。Parent 核验 39/39 observed docs 的完整
Read 区间与 SHA。终态为 `EVIDENCE_INCOMPLETE`：26 个必读项没有逐项列入报告引用，
已有引用的 hash/range 有效；原 seal/receipt 不改写，没有 canonical accepted report。
Raw proposals 只作线索，修正由 current source、native 全文 mapping 和 Parent 裁决支持。
这是 advisory mapping，不是 required implementation acceptance review，没有为补齐报告追加调用。

## Index Changes And Official Evidence

更新 AGENTS、Harness policy、contract matrix、runtime baseline、generation execution 和
video requirement 的既有 Entry：同步 rule registry 的责任分割与离线证明边界；区分 dated
历史与当前 authority；补充 canonical subject 执行闭包及 reference-only/T2V conditioning 例外。
其余 27 条 Entry 没有发现必须修正的矛盾，新 helper 继续受既有 owner 约束，不新增索引 owner。

87 项 observe 经过 model review 后由官方 `scope acknowledge` 前移 fingerprints；事务
`60a7f69b6e2bf0222013d488`。随后一次提交完整 6 项机器批次
`2f434f42062648fee84e268307860d293a5a7cf2836a9a83c434aba8db6373c5`，
`applied=6`、`remaining=0`、findings 为空。正式 Code Volume SHA-256 为
`8bf047d147c9c6a064fbc66c382d821245a85084b225aa5227ba0212aff5bd6e`。
正式资产仅 `aoci.code.txt` 与官方 `.aoci/baseline.json` 有内容变化。

本地证据目录：`runs/aoci-maintenance-20261002/`，保存 source snapshot、读取核验、
Kimi 原 receipt 与 Parent adjudication、官方 acknowledgement、batch、apply、Verify/Check/Guide。
相关 portability/contained-path tests 实际运行：`tests/test_aoci_project_cognition.py`，2 passed。
最终 exact commit range 的 Harness 凭据位于
`.agent/harness/runs/aoci-maintenance-20261002-final/receipt.json`，以 `verify-receipt` 的
scope、policy、artifact integrity 和 freshness 核验为交付证据。

## Publication And Record Boundary

本任务只有 formal Code Volume、官方 Baseline、本记录和直接受影响旧记录的 supersession notice；
Root/Meta、AOCI config、业务源码和既有 staged config 内容/index 保持。仅本地 commit，不 push/release。
记录过程没有 Provider/media 调用。旧记录中的 AOCI blocker 由当前官方证据取代，保留原历史。
RAG 检索曾返回 stale last-good 并由其自身队列安排 background refresh；未以前台 rebuild
或旧检索结果证明当前事实，本记录不宣称 RAG 已刷新。

按 `record-ai-video-session` 保存稳定记录；按 `distill-ai-video-learning` 自动评估为
`no_candidate`：确定性索引维护没有新的独立媒体实验或 controlled arms，不创建占位 claim。
