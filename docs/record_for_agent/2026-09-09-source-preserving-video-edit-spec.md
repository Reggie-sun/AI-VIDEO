---
record_kind: session_summary
topic_id: s01-failure-recovery-strategy-regression
learning_eligibility: ineligible
---

# S01 Failure-Recovery Strategy Spec Record

Date: 2026-09-09

## Approved Admission Implementation — 2026-09-09

用户后续“可以”明确批准 development-only failed-source admission，取代下文等待批准的
历史状态。新增 `repair_input_admission.py` 与 `bootstrap_repair_input()`；仍由既有
`ProductionStateCommitter.bootstrap_initial_state()` 独占 atomic 写入及 exact replay。
没有 Manifest schema migration、第二 writer、通用 importer 或 Editorial subsystem。

接入 receipt 固定 `NOT_EVALUATED`，保存原 Manifest exact bytes、request、paid submit、
status/fetch、binding、quality rejection、原 QA、experience 和历史 budget snapshot。
预算仅为 captured evidence，不成为新 root 的 budget；history 不导入，旧 FAIL 不改写。
Reader 重验内部 semantic identities 与证据关联，输入绑定新 Project hash；保留路径和
tool marker 不一致、跨项目冒用和直接绑定 Production Shot 均拒绝。

采用 `test-driven-development` 的 bounded red/green 验证：marker-removal 和三个外层重封
负例（QA 旧 semantic hash、request generation ID、fetch size）均先实际失败，再修复通过。
接入与 bootstrap 共 20 passed。`reviewer_xhigh` 首轮拒绝的三项 provenance 问题均修复，
同 tier scoped re-review 为 accept；该 verdict 不替代真实 source 接入或媒体验收。
Docs contract、policy audit、runtime Skill boundary（2 passed）与 task-delta Architecture
Gate 已通过。按 policy 中 `repair_input_admission_tests`、`production_reader_tests`、
`production_state_tests`、`generation_feedback_tests`、`s01_strategy_regression_tests`、
`production_strategy_tests`、`harness_tests` 的 argv 提取并去重 test paths，执行
`.venv/bin/python -B -m pytest -p no:cacheprovider <exact union> -q --tb=short`：
**1563 passed in 431.29s**。它覆盖上述 20 项接入/bootstrap 测试，不重复累计计数。
测试基于当前已检查的 working tree，不是隔离 snapshot Harness receipt。

正式 Harness closure 尚未完成：本 task 没有非空 exact staged/commit snapshot，已有 index
属于两项 unrelated work；未创建 worktree、未 stage/commit，也未把 advisory inspect 或
working-tree tests 描述成 fresh passing receipt。原项目不写入，Provider/上传/生成或派生
媒体/commit/push 均不属于本批准范围。

### Actual S01 Development Admission

已实际调用同一 canonical API，新 root 为
`runs/jieshi-s01-repair-input-20260909-v1`，标准 loader 重开与 exact replay 均成功。

- source：`runs/jieshi-e01-i2v-20260907-attempt10/production-s01-v10`，Manifest r62；
  原 107 个文件的逐文件 SHA-256 map 在接入前后及 replay 后完全一致。
- source Manifest **文件 bytes SHA-256**：
  `d1a59f248ec07a7f9873e306a8fc5b9f41d20db4d5d9756fc00c69a8ccf05479`；
  与下文 driver 的 semantic `manifest_hash` 是不同哈希口径。
- exact attempt11 MP4：`cb73c70c1e935d6849b3a91f5fa7ff19d81966647afaf88a010cd00dc89be537`，
  3,297,401 bytes；完整复制包含原音轨，不转码、不提取、不编辑。
- target Project hash：`93b3013ea3283120085ba284307fbad9e4350fabce5a4efa3a6eceb93427eb83`；
  target Manifest r1，Registry 为原 3 PNG 加 1 个未绑定 repair input。
- admission receipt：新 root 下
  `state/repair-inputs/0e7d3bd9f31fb0cdd03160a669477ebc5de3898da9ff0d0a2162b02de3863b5c.json`。
- `qualification=NOT_EVALUATED`；attempts=0、imported history=0、budget=null、QA=null。
  target 全文件 SHA map 在 exact replay 后不变，source 全文件也不变。

这是真实失败来源接入通过，不是 reuse qualification、Production Strategy workflow PASS、
局部修复执行或 S01 成片 PASS。下一层仍缺被批准的用途/requirement authoring 与相应真实
证据，不能把该未完成接线说成已验证的 localized edit executor gap。

按 `record-ai-video-session` 更新同一主记录；`distill-ai-video-learning` 自动评估为
`no_candidate`：本轮是接入工程验证与原素材复制，不是新的独立媒体实验，不创建学习占位。

## Continuation Finding — Registration Is Not Provenance Qualification

本节为批准实现前的调查记录；“等待批准/没有 runtime code”的状态已由上节取代。

用户要求继续后，主线程与独立只读 `code_mapper` 重新检查 admission，而不是默认
上一轮“不能注册失败素材”的泛化表述正确。本轮未增加 runtime code 或新 project。

- `ProductionStateCommitter.bootstrap_initial_state()` 的既有 generic bundle 可登记
  `AssetSourceKind.IMPORTED` VIDEO，Registry 重验 contained path、exact SHA 与 size。
  因而 FAILED MP4 作为未合格输入被登记在技术上并非全面禁止。
- 但 `_state_commit_bootstrap.py:126` 的专属 import-receipt 重开分支只覆盖特定 IMAGE
  imports；未有 imported-video 的原 Manifest/fetch/terminal-disposition provenance
  重开契约。`AssetRecord.creation_receipt_id` 与 video metadata receipt ID 本身只是字段，
  不能把填写旧 ID 描述成已验证原生成来源。Bootstrap 同时拒绝未被 required bundle
  引用的任意附加 artifact，不能顺手塞入一份 source history 就声称链路闭合。
- `generation_history_import.py:137–156` 另行拒绝多 attempt、已 binding、重复导入与
  FAILED source；这是 Feedback history admission，不是 Registry registration，不能混用。
- `source_use_evidence.py::SourceUseEvidence/assess_source_use` 仍要求当前 parent hash、
  task、component、window、transform、asset、proof/evaluator 匹配。新用途必须有真实
  evaluator response；旧 human PASS 不能自动升级。登记本身不是 qualified reuse。
- `planning/generation_feedback_context.py::require_feedback_context` 比较 selected Shot、
  Registry 和 lifecycle pointers；给旧 S01 补 intent 会改变身份，原 binding 不能直接复用。
  `ProductionUnit` 仍是 sequential Shot，不是独立共时手部区域。解决 admission 也不会
  顺带获得 hand replacement、完整历史映射或原音轨的合法独立使用能力。

建议的下一个批准边界是 development-only failed-result repair-input admission：
限 attempt11 exact bytes、新开发 root、可重开的原 request/fetch/FAILED 证据，由既有
committer 独占写入；不修改旧 root、FAIL、used count 或预算，不自动产生 SourceUseEvidence
PASS、activation 或历史导入。该入口需要新的有界 provenance artifact/validation 契约，
不是纯配置补全；当前没有将“继续”解释为允许这个新持久化契约或开始 Production mutation。
先确认这个范围，不新增通用 import framework、编辑 subsystem 或新的 Gate/Resolver。

本轮 source/codegraph 核对属于只读证据，不重算上一轮测试/真实 S01 运行结果。
`retrieve-ai-video-memory` 返回 stale advisory fragments，CLI 排队本地 derived-index
refresh；未等待、重试或启动 foreground rebuild。记录更新后按
`distill-ai-video-learning` 评估 `no_candidate`：没有新的独立媒体实验或可采用学习结论。
Provider、上传、媒体生成/派生、真实 Production mutation、stage、commit/push 均为零；
已有 task changes 和两项 unrelated staged changes 均保留。
本轮 documentation contract gate、policy audit、record whitespace 检查通过，
`tests/test_runtime_skill_boundary.py` 为 2 passed；advisory path inspection 无 fallback，
不产生正式 exact-snapshot Harness closure receipt。

## Implementation Checkpoint — Read-only Foundation

用户随后以“实现”授权有界工程工作；spec 现为 accepted / foundation_only。
本次新增 `scripts/s01_strategy_regression.py` 与对应测试，同步 Harness routing、
contract matrix、baseline 和 roadmap；没有新增 Resolver、Gate、schema 或编辑子系统。

driver 通过 strict loader 重开 exact source bytes 与 canonical experience，分别观察
source attempt 和当前 Feedback history。原 Strategy 接口仅在 authoring 存在时执行，
缺失输入明确返回 `integration_incomplete`；不造 source-use PASS，不将历史 FAIL 素材
假激活。实际 CLI 使用拒绝 transport、credentials、media access 的 Vidu adapter。
报告保留原 verdict/candidate blockers，`workflow_acceptance` 恒为 `not_evaluated`。
旧 context binding 的 limits/policy/routing 来源与当前 budget observation 分开标注，
`current_authorization_verified=false`；不会续期或把观察转换成执行授权。

首次真实只读 CLI 已 exit 0：Manifest r62，hash
`f3a4ba6ae0e516721fc6874b51c38d52107f0ebeba22d486fae558d8168b1323`；
attempt11 source SHA 为上方 spec 固定值，状态 failed，registered asset IDs 为空，
用途 qualification 为 null。原 diagnosis 保留 legacy-03/05 FAIL；selected S01
没有 production intent，QA allocation/source-use evidence 均为零。
结果 `integration_incomplete`，不能据此判定 localized executor capability-gap PASS。

最终代码复跑也 exit 0，Manifest r62/hash 与首轮一致。source 仍为 attempt11，
Feedback latest 明确为 attempt13（evidence hash
`4d08d92a81e7d13a80dddc58790dc698024c3feadce002fd30e7dda054cc461f`），
baseline request hash 为
`edd3eab9bdcdb961ade2fd75da21f024833fbe2efd0e521de43e150072de1130`。
完整输入保留 8 个 evidence hashes，原 owner 返回 `EVIDENCE_GAP`，同时保留
`QUALITY_FAILURE` / legacy-03 FAIL。used=4、旧 binding ceiling=4、
generation_forbidden=false；当前 budget available=0 且 authorization 未验证。
Strategy generation_available=true，但 missing_production_intent 导致未作策略选择。
这证明 driver 未用 source11 替代 latest13 或人为禁用 generation；不证明已改变
production responsibility，也不产生任何新 submit、验收或 activation。

只读复现入口（不携带 secret，不执行 Provider）：

```bash
.venv/bin/python -B -m scripts.s01_strategy_regression \
  --project-root runs/jieshi-e01-i2v-20260907-attempt10/production-s01-v10 \
  --source-attempt jieshi-e01-s01-vidu-i2v-attempt11 \
  --source-sha256 cb73c70c1e935d6849b3a91f5fa7ff19d81966647afaf88a010cd00dc89be537 \
  --context-attempt jieshi-e01-s01-vidu-i2v-attempt13 \
  --planning-request runs/jieshi-e01-i2v-20260907-attempt10/preparation-v5/planning-request.json \
  --provider-profile runs/jieshi-e01-i2v-20260907-attempt10/preparation-v5/provider-profile.json
```

### Verification And Remaining Boundaries

- 初始 missing-module 测试 RED，新增 Harness 路由检查 RED，随后实现。
- 最近组合验证：driver/Harness/Feedback/Planning/quality-rejection 为 205 passed；
  Production Strategy 全 focused suite 为 63 passed；最后 driver/runtime Skill boundary
  为 12 passed（包括强化后的最终 Manifest 漂移拒绝）。这些结果有重叠，不相加计数。
- 按 policy 展开的 Generation Feedback 与 Harness 全 focused suites 为
  420 passed in 89.60s；没有执行真实 Provider/media。
- Documentation contract gate、policy audit 与 task diff whitespace 通过；
  八个 task-owned paths 的 advisory Harness inspection 无 fallback，closure_eligible=false。
- `reviewer_xhigh` scoped re-review 为 accept with concerns，无 blocking issue，
  仅接受 foundation。CLI profile/binding/request 错配、多 attempt 与 unknown-state
  的自动反例仍不足；真实案例观察不能替代这些长期回归控制。
- 没有正式 exact snapshot Harness receipt：未 stage/commit，保留两个 unrelated staged
  paths；未创建用户未要求的隔离 worktree，未以 working-tree tests 伪称完整 Harness closure。
- 未调用 Provider、上传、生成/派生媒体、写真实 Production state、commit 或 push。
  尚未形成合法的 S01 production intent/source-use/history projection，未 materialize
  hand component，未做 composition 或 whole-shot revalidation，未开始 S02。

这不是完整 spec 的完成记录。下一个实质边界是合法的案例 authoring 与用途资格取证，
而不是用更多 enum 或强制禁用 generation 制造预设 capability gap。
按 `record-ai-video-session` 更新同一记录；`distill-ai-video-learning` 为 `no_candidate`：
本次只有工程/历史复读，没有新的独立媒体实验，不创建 Learning Claim 或 adoption。

## Historical Scope — Decision Regression Spec Revision

用户明确调整目标：用 Shot1 验证 failure recovery / editorial strategy，之后再评估
Shot2 fresh-shot authoring；本轮不再预选 Seedance VIDEO_EDIT，也不要求 Shot1 成片必须过。
[同一 spec](../superpowers/specs/2026-09-09-ai-video-source-preserving-video-edit.md)
已修订为 proposed `/0.2`，保留旧路径。下方 `/0.1` 单次 edit 目标及审查为历史，
不再代表下一步 scope；没有新增 implementation plan 或 runtime 授权。

核对 exact attempt11 human confirmation，只有 legacy-06/14/17 为用户认可；
legacy-03/05 的正式 FAIL、后续掌向解释不确定性和窗内暗影 concern 都保留。
attempt12/13 作为独立后续证据，不混用源片、human PASS 或 quality verdict。

当前源码同时暴露 decision/integration 限制：ProductionUnit 是 sequential Shot，
不是 co-visible hand subcomponent；prepare 不直接消费 failed intervention history；
required_operations 会影响同 unit 的 full-generation 选项。因此不能仅给 fixture 加
MASK_COMPOSITE、移除 Provider 或检查顶层 capability_gap 就宣布新 workflow 成功。

修订后的 acceptance 要求真实输入/历史、实际入口与候选级 blocker、用途责任分配、
原 owner 对重复 intervention 的判断和零副作用证据。有依据的 localized capability gap
可以使 decision regression PASS，但不产生 Shot/media/activation/P6/Final Acceptance。
缺少 authoring/history projection 只能标 integration incomplete，不包装成局部 executor gap。

attempt11 仅作为素材/失败事实基底。当前 Feedback 的 latest/baseline 仍由原 history owner
选择，可能是 attempt13；不得截断后续历史伪装 attempt11 时点回放。

本轮补查 retrieve-ai-video-memory 返回 stale advisory fragments，CLI 自动排队本地
derived-index refresh；未等待或手工 rebuild。重要结论均重开当前源码/原始记录核对。
record-ai-video-session 更新本主记录并保留历史；distill-ai-video-learning 为 no_candidate，
因为没有新的独立媒体实验或可采用的质量结论。

## Latest Verification — Version 0.2

标准 load_production_project 只读重开真实 production-s01-v10：selected S01 无
production_intent/production_lineage，production_allocations 与 production_source_evidence
均为 0，Registry 无 attempt11 exact MP4 绑定。未修改 snapshot 或补造 source evidence。
初次诊断打印误用了不存在的 Manifest.revision 字段；修正打印后成功取得上述结果，
不是 Production loader 故障。本次仅验证输入现状，未运行完整 Strategy regression。

本次修订的 documentation contract check、policy audit 通过，runtime skill boundary
tests 为 2 passed；spec 13 个本地链接存在，whitespace 检查通过。
独立 reviewer_xhigh 对 /0.2 审查为 accept，无遗留 blocking/non-blocking issue；
父代理核对并补明其指出的 source attempt 与 Feedback latest/baseline 区别。
该 verdict 仅接受 spec，不证明 workflow regression 已运行或通过。
仍无 staged/commit-range Harness closure receipt，未 stage/commit/push。
仅修改同一 spec/record；原有两份无关 staged 文件保持不变。没有 Provider/media、
新 fixture/project、Production mutation 或 S02 执行。

## Historical Scope And Decision — Version 0.1

用户在 S01 / Production Strategy 只读调查后要求写一个 spec。本轮新增
[proposed spec](../superpowers/specs/2026-09-09-ai-video-source-preserving-video-edit.md)，
未创建 implementation plan，未实现新代码或更改 runtime 状态。

范围是一次有界的 source-preserving `VIDEO_EDIT` 可行性实验，不是通用 Editorial
Execution Layer。现有 Provider edit/extend 并非全部缺失；S01 的关键问题还包括
exact input eligibility、原声独立保留、输出格式适配，以及真实完整音画质量。
先证明媒体价值，再考虑 Strategy 接线；不得以 spec、API 或测试通过宣称修复成功。

## Historical Runtime Boundary — Version 0.1 Context

依据当前 source、baseline 和
[S01 主记录](2026-09-08-jieshi-s01-human-gap-history-boundary.md)：

- attempt12 的质量放弃不使它满足 current exact-active remote source lease；
  不能假激活失败素材，也不能把“修复输入资格”等同于成片可用。
- 现有 generated-video audio derivation 要求 VALIDATE、SETTLED 及受限目标版本；
  仅结算不能消除 attempt12 的生命周期和目标 schema 限制。
- spec 将开发音画 review derivative 与 canonical Production composition 明确分开；
  开发证据不产生 Registry、activation、P6 或 Final Acceptance。
- Source-preserving 是待验证目标，不是现有 mask/tracking 或像素不变保证。
  若输入不具备合法可执行条件，停止并报告具体缺口，不扩建通用导入/编辑系统。

这些是 proposed scope 的约束，不修改旧实验 verdict，也不表示已具备 S01 submit readiness。

## Historical Verification And Publication — Version 0.1

当前 checkout 的 documentation contract check 与 Harness policy audit 通过；
`tests/test_runtime_skill_boundary.py` 为 2 passed。Spec 的 10 个本地证据链接均存在，
新增文档 whitespace 检查通过。

独立 `reviewer_xhigh` 首轮无 blocking issue，指出格式/组合阻断与质量失败归因重叠，
并建议明确 Ark materialization 的人工 Active 确认入口。父代理核对当前源码后修订；
同 tier scoped re-review 为 `accept`。审查没有产生新的 runtime 或媒体证据。

Harness explicit-path inspection 路由为 documentation，无 fallback；它不是
exact staged/commit-range closure proof。按用户不 commit/push 的限制，未 stage，
未生成正式隔离 snapshot receipt，不声明 Harness completion。

原有 staged `docs/record_for_agent/2026-09-08-production-strategy-harness-closure.md`
和 `tests/test_agent_memory.py` 未修改。仅新增本 spec 与本记录；没有 Provider 调用、
上传、媒体生成、Production mutation、commit 或 push。

## Historical Learning Evaluation — Version 0.1

按 `record-ai-video-session` 留存本边界，随后按 `distill-ai-video-learning` 评估为
`no_candidate`：本轮是 proposed 文档与当前能力核对，没有新增独立媒体实验，
不将同一 S01 历史的再次引用计作新证据，不创建 Learning Claim 或修改 adoption target。
