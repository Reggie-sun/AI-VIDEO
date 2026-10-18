---
record_kind: architecture_implementation
topic_id: staged-verification-boundaries
learning_eligibility: ineligible
---

# Staged Verification Boundaries Record

Date: 2026-10-19

## Current Result

用户要求在没有可用视频前减轻验证，随后明确“修改架构”。本轮在既有 owners 内落实取材、剪辑、交付与工程证明的边界，并合并一次确定的重复项目加载。源码 `a07b1ed030ad5942d44da91b7404ce87aac681df` 已 push main，远端 SHA 相同。新增外部 Provider/媒体/音频理解调用0，没有新 schema、状态库、timeline、renderer、依赖、试拍许可或跨调用缓存。

## Ownership And Behavior

- Harness 并非原有视频 submit 的运行时前置条件，问题之一是 Agent 把工程发布检查提前执行。CLI `inspect` 现在显式输出 `verification_purpose=engineering_completion`、`media_submit_authority=false`、`media_acceptance_authority=false`；help 同步说明用途。原 verify/receipt、完整路由与 completion-scope 拒绝规则保持，不新增 fast 模式或轻量 PASS。
- [Canvas workflow](../canvas-production-harness.md#verification-responsibilities) 编排三个阶段：取材前只补当前证据确认的确定性缺口和相关回归，保留所有提交安全条件；原片出来后按 raw QA 观察，可用但偏慢先沿现有剪辑/原声映射处理；工程完成和最终交付再分别取得完整工程、P6/final-output/human 证明。FAIL/NOT_EVALUATED 不推进下一 Shot。通用 workflow 不再固定历史 Seedance7/7计数，当前次数/outcome只归 canonical state及当前授权。
- `ProductionStateCommitter` 的原锁内 submit guard 已严格加载当前 project、核对 Manifest/current QA，并从原 `production_family_shot_ids` 派生 family tuple；limits helper 现在必需接收这个同次 tuple，删除其第二次完整加载/重复派生。paid/local 两条调用均在同一 exclusive lock 内。新动作仍重验，公共入口不能提交自证快照；history、predecessor、任务/额度/策略限制、budget、actual clock、egress、permit 与 unknown 行为没有删减。

canonical paid-intent 回归在修复前观察到两次项目加载而 RED；修复后为一次加载、一次 family 派生，reservation/gate/submit intent仍真实持久化。此为离线工程行为，不是对此前约9分钟耗时的完整归因，也未测量真实项目 wall-clock 改善。

## Verification And Proof Boundary

稳定 owned bytes 的直接检查证据根为 `.agent/harness/runs/staged-verification-boundaries-20261019-r1/`。`focused-checks.json` 保存全部八份 owned source hashes、policy hash、原 policy argv、结果与前后 source_stable=true；明确 `engineering_completion_proof=false`。它不是 canonical full Harness receipt。

| Evidence | Result |
| --- | --- |
| Worker focused canonical/history/unknown/quota/unsubmitted cases | 33 PASS；一项既有 Pydantic fixture serializer warning。命令为 guards 全文件加 quota、unsubmitted、imported-history 的针对性 nodes；worker tool output，未伪造 JUnit |
| Parent single-snapshot canonical paid-intent check | 1 PASS；`single-snapshot-check.json`、`single-snapshot.junit.xml`及stdout，验证正常 intent/reservation 与一次加载/派生 |
| Parent stale current-QA check | 1 PASS；精确匹配 current QA final-output owner mismatch，完整 bytes不变且无 intent/reservation；`stale-current-qa-focused.log` |
| Harness CLI purpose/no-execution and old completion/receipt boundary | 初始缺用途字段 RED；focused3 PASS；随后原 policy `harness_tests` 307 PASS |
| Original policy rule invariants | 44 PASS，含 unknown reservation不可释放及 unsubmitted replay |
| Runtime Skill isolation | 2 PASS |
| Architecture/policy/docs/rules | Architecture PASS，0 errors /27 WARN /18 INFO；policy audit、docs contract、agent rules通过，未刷新 Architecture baseline |

Parent 自审确认本改动只传递同锁内既有纯投影，未增加 authority、cache 或未覆盖的高后果语义路径，Risk Gate为 `NATIVE_REVIEW_NOT_REQUIRED`，见 `parent-risk-gate.json`。早先 component CGB审查仍绑定其原候选，不冒称审过本次新源码。只读调查使用 native mapper/auditor，writer为 native bounded_worker；无 nested/external delegation。CodeGraph结构查询未及时返回后停止，结论以当前源码/调用点和可执行回归为准，不宣称索引完成。

按用户本轮先取可用视频、减轻验证的要求，未再运行已知耗时的大范围完整发布套件；没有制造或复用一份“完整 PASS”。源码发布是 Git事实，完整工程 completion proof仍为 DEFERRED。将来宣称工程完整完成前须取得适用 exact-scope 全检查证明，它不成为每次取材的前置条件。当前任务的文档检查 receipt 为 `.agent/harness/runs/staged-verification-boundaries-record-20261019-r1/receipt.json`，只证明文档范围，不补签源码全量证明。

## Existing Media And Publication Boundary

本轮未启动 Provider、读取凭据或修改实际 Production state。原项目仍 Manifest133；Manifest SHA `914aa7b92d14ea7c9d192535b9c1548e6be9722dfca6ce61f9f3f42ab852b726`。S01最后一次提交的 HTTP402/known_no_effect 和无新MP4状态见[媒体主记录](2026-10-13-jieshi-original-s01-s02-candidate.md#current-finite-s01-submit--2026-10-19)；无 accepted-state/activation，S02 POST0。恢复真实生成仍需解决当前接口拒绝及下一次有效有限授权。

八份源码/合同按 owned paths提交，foreign staged diff SHA `c727828e0ef6aebc8033b71b3842d44668105948aafd9dd6363db47254b90b82` 保留；AGENTS/playbook及其余未知修改未纳入。本文和旧工程记录的直接关联 notice另作文档 checkpoint，publication以Git及文档 receipt为准。

## Learning Evaluation

通过 `record-ai-video-session` 记录当前稳定工程边界，自动 `distill-ai-video-learning=no_candidate`。本轮没有新的模型质量样本、受控比较或 existing model claim更新；fixtures、重复检查及同一源码不同证明层不算独立媒体实验。执行次序修订来自用户当前指令和已确认代码职责，不自动升级为模型质量经验，不修改 Skill/Policy/Gate的质量条件，不刷新RAG/全局memory。
