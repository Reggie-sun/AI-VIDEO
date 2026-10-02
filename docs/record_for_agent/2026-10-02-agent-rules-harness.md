---
record_kind: architecture_implementation
topic_id: agent-rules-harness-migration
learning_eligibility: ineligible
---

# Agent Rules Harness Migration

Date: 2026-10-02

## Scope And Runtime Truth

用户要求精简 `AGENTS.md` 和 `.agent/context/`，把适合机械验证的规则迁到现有 Harness。
实现属于 Development Governance，不改变 Product lifecycle、Provider execution 或媒体验收语义。

| Document | Before lines / bytes | After lines / bytes |
| --- | --- | --- |
| `AGENTS.md` | 268 / 30425 | 176 / 13420 |
| `control-plane-playbook.md` | 513 / 55971 | 196 / 15197 |
| `t8-latentsync-local-runtime.md` | 268 / 10931 | 74 / 4571 |

Root UTF-8 bytes 减少约56%，context 合计减少约70%。重复 Skill/schema/catalog 回指现有 owner，
历史 T8 实验回指原记录，不移到新文档形成第二 owner。授权、安全、unknown outcome、
canonical ownership、逐 Shot MCP Gate、最终成片验收和 completion 边界保留。

`agent-rules.yaml` 只登记 rule → existing check IDs、offline proof boundary 与文档预算；
argv、changed-path routing 与 receipt 仍属于现有 policy/Harness。新只读 gate 检查 registry、
known/routed checks、context 注册和总量、bytes/lines 与 contained Markdown links/anchors。
`agent_rules_check` 每轮运行；control-plane/Harness delta 增加真实 CLI、resume、reader、timeline、
dependency、unknown-outcome 与 replay 测试。它们不拦截任意 Agent shell，也不代签 Product acceptance。

## Implementation And Verification

Task commits：`be175a4`、`fc1cce3`、`81bf3eb`。最后实现 target：
`81bf3eb50f99e320dfe96720117e84ecfc1c026b`。
Exact base `b425ac600a97ff0fd8912fe0aee729f41c2ec069` → target 的 Harness v3：
11 checks PASS；378 tests（boundary2、Harness261、invariants44、CLI15、open-video48、Seedance8）PASS；
Architecture Gate PASS / 0 findings；docs contract、policy audit 和 rule gate PASS。
Receipt：`.agent/harness/runs/agent-rules-20261002-v3/receipt.json`；checkpoint 时 scope、policy、
artifact integrity、freshness、snapshot 与 verification-checkout cleanup 均验证为 true。
该 range 含另一个 session 已提交的 Metaso record `085e0b4`；其内容不属于本任务，review owned diff 已排除。

## Review And Parent Adjudication

T3 两个 independent read-only contexts 审查同一 exact target，互不读取对方结论。
Native `reviewer_xhigh`：发现 titled/reference links 漏检和 validate test 的 side-effect proof不足，
修正后又发现 multiline inline links 漏检。Parent 独立复现三个 RED 用例再修正，加入合法链接回归。
最终 round3 finding set 为空；reviewer 没有执行测试，测试证据来自 Parent Harness。

Kimi live rounds 保留历史：round1 `80dca6ae-de3f-4acf-bc8c-85a62726f6f3` 发生 response-body
CONNECTION_ERROR，没有 terminal report，partial output 未用于 acceptance；round2
`62fa8a4d-5e9a-4761-98ab-1e14b0e19c3f` 完整 report 无 blocking candidate。
Parent 接受 F-01..F-04，恢复精简的 evidence levels、default-authority保护、artifact/standard seam与triage audit。
F-05 FALSE_POSITIVE：memory Skill lines30–34 已独占 derived run-summary authority/provenance，删除重复内容没有删除owner。
最终 round3 `b56bba8c-e238-4881-847f-d6f9465e9b58` 为 PARSED，7 次 wire requests 均 IDENTITY_VERIFIED，findings为空；Parent 逐一重算 report evidence_refs 的文件SHA并核对 owned patch，target均为81bf3eb。审查包旧commit/tree字段仅为前一轮元数据，head/base、sealed sources、receipt与补丁一致；原packet不追改，裁决另存final-adjudication.json。双review无unresolved blocker，Parent接受Development Governance变更。并发session随后提交8c4ce09，只更新其Metaso record；target至当前HEAD的全部owned paths diff为空，保留其提交。
PARSED、exit0、模型同意及 tests PASS 各自只证明其对应层，最终判断由 Parent 负责。

## Remaining Boundaries

AOCI maintenance 返回 stopped/blocked、aligned=false、零 authoring candidates；已有 observed evidence
要求 human review（范围内与范围外漂移并存）。未修改正式索引/Baseline、未冒称认知对齐；需要后续按官方治理停点处理。
本轮没有 Product Provider/media generation、activation、push 或 release。受管 Kimi 的外部审查请求按standing authorization执行。
既有 staged `.codex/config.toml` 的 index blob及工作内容保持，其他 session 的 commit保留。交付仅 local commits。
记录过程不运行 Provider/media、不刷新 RAG；之前 advisory retrieval 返回 stale last-good并由其自带队列触发background refresh，未以前台重建或旧hit冒充当前事实。

## Record And Learning Evaluation

采用 `record-ai-video-session` 保存单一稳定 implementation record。按
`distill-ai-video-learning` 搜索同题历史和反证后判定 `no_candidate`：这是一项确定性治理实现，
没有可归因的多次媒体实验、controlled arms 或可采用的模型质量 claim。不创建 placeholder、不修改Learning/Skill/Provider目标。
旧治理记录陈述历史layout/measurement，未留下本任务未解决status，不改写历史或无关record。
