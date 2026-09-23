# AI-VIDEO Agent Guide

适用于在本仓库中工作的 Codex、Claude 以及其他编码 Agent。本文件只保存长期稳定的 repository constitution、routing policy、canonical ownership、change rules 与 verification contract；不作为 runtime status dashboard、phase ledger、live-provider evidence log、commit history 或 benchmark report。

## Purpose

- 保持 Legacy `0.1.x` local-first CLI 与 v0.2 Production Python APIs 的边界清晰。
- 维护 manifest-first、content-addressed evidence、explicit recovery、precise invalidation 与 deterministic composition 等长期产品契约。
- 让每项变更先找到唯一 owner，再按真实 changed paths 完成可复现验证。
- 默认使用中文沟通；`command`、`path`、API、schema、class 与 Skill 名保持原文。过程更新应简短、具体、基于当前仓库证据；review 先报告问题与风险。

## Runtime Truth Sources

| Concern | Canonical Source |
| --- | --- |
| Agent authority、routing、ownership、change 与 completion rules | `AGENTS.md` |
| Surface owner、invariant、禁止旁路与 focused verification | `docs/agent-primary-contract-matrix.md` |
| Changed-path category、mandatory checks 与 receipt routing | `.agent/harness/policy.yaml`、`scripts/agent_harness.py` |
| 当前已实现行为、local/origin/release truth、已验证与未验证边界 | `docs/v0.2-runtime-baseline.md` |
| Phase dependency、status、future gates 与 slice direction | `docs/v0.2-agentic-production-roadmap.md` |
| 单个 slice 的 accepted scope、tradeoff 与 implementation detail | active spec / plan |
| Executable truth | source code、tests 与本轮实际 runtime evidence |

Plans、specs、roadmaps、console text、Agent memory 或历史 receipts 本身都不能证明 runtime 已实现、当前仍有效或已获执行授权。若状态可能变化，必须重新核对当前 code、tests、Git 与 runtime evidence。

## Read Order

1. 用户请求。
2. 本 `AGENTS.md`。
3. 按 task concern 读取 `docs/agent-primary-contract-matrix.md`、`.agent/harness/policy.yaml`、runtime baseline、roadmap、active spec / plan 与相关源码、测试；不得以文档状态替代 executable truth。
4. `.agent/context/` 是 advisory operational reference；按需读取匹配章节并重新核对当前环境与 runtime。`session-handoff`、`.agent/bug-memory/` 和 `.workflow/` 仅提供次级上下文。详细入口见 [Task Context Loading](.agent/context/control-plane-playbook.md#task-context-loading)。

## Conflict Resolution

当信息冲突时，按以下优先级处理：

1. 用户的明确指令。
2. 当前代码、测试与已验证 runtime behavior。
3. 本 `AGENTS.md` 的长期规则和 ownership contract。
4. runtime baseline、contract matrix、README、roadmap、active spec / plan。
5. handoff、bug-memory、`.workflow/` 与其他草稿。

如果用户请求有意改变既有契约，必须在同一任务中同步更新代码、测试与对应 canonical 文档。不得只改文档就把 proposed behavior 描述成 runtime truth。

## Product Invariants

### Legacy `0.1.x`

- 保持 local-first、CLI-first；默认 ComfyUI 必须为本地，非本地主机需要 explicit opt-in，且不得成为 fallback。
- 公共命令保持 `ai-video validate`、`ai-video run`、`ai-video resume`，除非独立批准并同步 CLI tests、README 与退出码契约。
- `validate` 必须无副作用：不创建 run、不联网、不上传素材、不提交生成任务。
- `run` 创建 `runs/<run_id>/`，按 Shot 顺序执行并原子持久化 Manifest；`resume` 必须从既有 Manifest 恢复，不能通过再次调用同一 `run_id` 的 `run()` 模拟。
- Legacy Manifest、flat artifact layout 与既有 config/workflow/ffmpeg semantics 保持兼容，除非明确批准 migration。
- Workflow 保持 template + binding，不得在 CLI、pipeline 或 transport 中写死 node IDs。

### v0.2 Production Harness

- `ProductionProject` 与 Asset Registry 读取必须 strict、read-only、no-network，并验证 selected revision、semantic/content identity、path containment 与 registered bytes。
- `ProductionStateCommitter` 是唯一 v2 write、activation 与 explicit recovery owner；mutation 不得扩散到 reader、registry、validation、dependency 或 Legacy Manifest/pipeline。
- `ResolvedTimeline` 是唯一 order/frame/sample/timing owner；audio、captions、generated media 与 render adapter 只能消费同一 canonical timeline。
- Dependency Graph 独占 dependency、desired fingerprint、precise invalidation 与 rebuild frontier；immutable graph 不保存 mutable lifecycle，也不推导 timeline。
- HyperFrames 是默认 Production renderer。只有显式批准的 adapter contract 才能改变 renderer selection；不得出现隐式 fallback 或第二条 canonical timeline。
- Image、video、voice 与其他 Providers 是 optional capabilities。基础 Production path 在没有 Video Provider 时仍必须能够完成 image、motion graphics、voice、captions 与 deterministic composition。
- Remote/paid execution 必须 explicit opt-in，并通过 finite task-level submit quota、既有 runtime Budget Guard、cloud-egress、secret、durable intent、one-use permit、provenance、activation 与 recovery gates。正常 task authorization 不要求 Agent 或用户查询、推导或确认 Provider 官方价格。

### Cross-Cutting Safety

- Immutable evidence 必须 content-addressed，并绑定 exact selected inputs、actor/tool identity 与 measured artifact bytes。
- Mutable lifecycle 只存在于 canonical Manifest owner；immutable graph、receipt 或 Registry record 不得偷带第二套 lifecycle truth。
- Exact replay 不重复 Provider、renderer、analyzer、materializer 或 Manifest write 等外部副作用，也不得无证据推进 state。
- Unknown outcome 必须 fail closed；recovery 必须显式，不能 blind retry、remint permit、猜测 mixed state、自动激活或删除完整 orphan evidence。
- Typed cross-module failures使用 `AiVideoError` 与 `ErrorCode`；retryability 由 typed metadata 决定，常规 CLI 输出不得泄露 raw traceback。

### Final-output-first / No-regression

所有生成、修复、后处理和验收均以用户实际会看到的成片为最终判断对象。局部修复不得破坏已满足的视觉、动作、连续性、节奏、音频或叙事要求；已知会降低整体观看质量的方案必须否决，不能用 preview、技术 PASS、成本或避免重生成放行。

测试、schema、receipt 或单项指标只证明其覆盖的条件，不能替代对成片的观看检查，也不得因追求未来工程完整性长期阻滞当前出片。Gate 阻断时说明其保护的具体要求和失败证据，在已授权范围内修复或补证；确无可行路径时说明恢复出片的最小条件。不得因此绕过安全、授权、预算、数据完整性或质量底线，也不得伪造验收。修复前的具体 preflight 见 [Final-output-first Repair Preflight](.agent/context/control-plane-playbook.md#final-output-first-repair-preflight)。

### Empirical Validation Priority

- 对不能仅由 code/tests/Harness 证明的媒体能力，必须区分 Engineering / Deterministic Uncertainty 与 Empirical / Model-Quality Uncertainty。后者占主导且存在安全、有界、满足适用授权或 local exemption、可负担且可执行、可隔离归因的最小真实实验时，下一关键动作 SHOULD 优先取证，再扩大仅服务未来验证的 engineering。
- Development experiment evidence 不产生 Production qualification、activation、P6 / Final Acceptance、live-ready、release 或 replay truth；PASS/FAIL 均不授权降低 contract、改变 frozen rubric 或绕过现有 safety、budget、egress、permit、lifecycle、recovery gates。
- 触发场景、前置条件、用户要求先完成 contract 的优先权、pure deterministic work 排除项与操作顺序，由 [Empirical Uncertainty Triage](.agent/context/control-plane-playbook.md#empirical-uncertainty-triage) 维护；本规则不要求所有任务先生成媒体。

### Per-Shot Post-Media Gate

- Sequential multi-Shot generation 必须在每个 Shot 的 exact MP4 落盘后、下一 Shot submit 前显式调用 project-local `video-analysis` MCP，按 sealed intent、applicable requirements 与前序已接受状态逐项给出 `PASS` / `FAIL` / `NOT_EVALUATED`。只有全部 required findings 为 `PASS` 才可推进。
- MCP 不可用、证据缺失/陈旧、identity 不匹配或 required finding 无法判定均为 `NOT_EVALUATED`，阻断下一 Shot；不得等待 batch 完成或用户提醒，也不得以 background hook、tool success、总分或自动 VLM stub 代替 Gate。
- `FAIL` / `NOT_EVALUATED` 停止当前 attempt，不默认结束未完成的任务。适用 local exemption 且 outcome known 时，orchestration 必须执行有界 `LOCAL_BOUNDED_REPAIR_LOOP`；证据问题先执行 `EVIDENCE_REPAIR_FIRST`。Unknown outcome 必须停止，禁止 blind retry、fallback、permit 复用或越过 Gate。
- MCP 只提供 exact-bytes raw evidence；Gate 不写 Manifest、不激活 candidate、不签发 P6 / Final Acceptance，也不自行重试。独立 repair attempt、有限预算、单变量诊断、新 identity/intent/permit、完整重验与任务停止条件，由 [Per-Shot Post-Media Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate) 独占。

## Canonical Ownership

| Concern | Canonical Owner |
| --- | --- |
| Creative intent | Codex + approved AI-VIDEO Character / Scene / Shot artifacts |
| Project schema and selected revision | AI-VIDEO `ProductionProject` |
| Asset identity and provenance | Asset Registry |
| Mutable lifecycle and active pointers | Production Manifest |
| v2 writes, activation, and recovery | `ProductionStateCommitter` |
| Dependency, desired state, invalidation, rebuild frontier | Dependency Graph / resolver |
| Timing, order, frame, sample, and source trim | `ResolvedTimeline` |
| Default render execution | HyperFrames adapter |
| Provider-specific generation | Selected AI-VIDEO Provider adapter behind AI-VIDEO gates |
| QA, repair, and final-acceptance evidence | AI-VIDEO Review / Repair receipts and Manifest lifecycle |
| External Skills | Advisory knowledge only |

Reader、registry、validation、dependency、Provider adapter、renderer 与 analyzer 可以验证或消费 canonical state，但不得直接决定 durable activation。Fetch、render、analysis 或 generation success 本身不等于 candidate activation、QA acceptance 或 delivery truth。

## Agent Memory Retrieval Routing

`retrieve-ai-video-memory` 是 substantial AI-VIDEO work 的 mandatory advisory preflight：real media/quality、Provider/model behavior、continuity/identity、known regression/incident/recovery、prior architecture decision 或明确要求 earlier evidence 时，在 matching domain Skill 与 substantial execution 前调用；trivial formatting/test 与 exact current source lookup 不触发。Scope、失败处理与 provenance 由 [Skill](.agents/skills/retrieve-ai-video-memory/SKILL.md) 和 [Agent Experience Memory Routing](.agent/context/control-plane-playbook.md#6-agent-experience-memory-routing) 独占。检索不授权 implementation、Provider、activation、quality acceptance、push 或 release。

## Experience Learning Routing

- `record-ai-video-session` 完成 substantial stable record 后，必须由唯一 owner [distill-ai-video-learning](.agents/skills/distill-ai-video-learning/SKILL.md) 自动评估 scoped Learning Claim；record/ACK 由 [record-ai-video-session](.agents/skills/record-ai-video-session/SKILL.md) 独占。
- Learning 仅有 `advisory_learning` authority：自动评估只可提出 pending candidate 并保留既有 adopted claim；用户确认及 target owner 的 tests/Harness 前不得修改 Skill、Provider Policy、Preflight、Contract、Gate 或标记 `ADOPTED`；不授权 Provider/media、Production mutation、retry、activation、acceptance、push/release 或绕过 decision gates。

## Creative Skill Routing

AI-VIDEO remains the sole owner of production truth. External Skills are advisory only；
use the minimum matching set and translate guidance into AI-VIDEO contracts。

| Concern | Route |
| --- | --- |
| Prior experience / decision trigger | `retrieve-ai-video-memory` first |
| Cross-experiment learning / adoption proposal | `distill-ai-video-learning` after stable record |
| Ecommerce / SKU / product advertising authoring | `ecommerce-ad-workflow` |
| Director coverage / ordered multi-Shot planning | `open-video` |
| Semantic continuity / Shot-state problem | `hell-grind-aigc-skill` |
| Approved Shot + selected MiniMax H3 guidance | `h3-video` |
| Approved Shot + selected Seedance target | `seedance-authoring` |
| Non-Seedance model / Provider prompt adaptation | `higgsfield` |
| Deterministic motion / graphics / pacing | `video-shotcraft` |
| Production state / assets / timeline / execution / activation / recovery | AI-VIDEO code and contracts |

Detailed trigger、preflight evidence、ordering、provider preference 与 forbidden Skill runtime
behavior 只在 `.agent/context/control-plane-playbook.md` 的 `Creative Skill Routing And
Preflight` 维护。External Skills MUST NOT invent or own canonical Character/Scene/Shot truth、
Asset Registry、Manifest、Dependency Graph、timeline、renderer、Provider lifecycle、review、
repair 或 delivery state。

## Agent Workflow Routing

本节是 Codex、Claude Code 等 runtime 选择 Skill、spec、plan、review 与 verification 深度的共享契约。Runtime adapter 仅接线，不复制规则；操作细节见 [Agent Workflow Operations](.agent/context/control-plane-playbook.md#agent-workflow-operations)。

### Instruction Hierarchy

冲突时依次以用户当前明确指令、当前 code/tests/runtime evidence、本 `AGENTS.md` 及委托的 matrix/policy/playbook、accepted spec / approved plan、Skill instructions、reviewer feedback、runtime defaults 为准。低位阶不得推翻高位阶；Skill 默认门控不得覆盖本节 routing。Reviewer 只提供 advisory evidence，由 Parent 裁决。

### Task Tiers And Skill Routing

按 semantic risk / blast radius 分级，不按代码行数：

| Tier | 判据 | 必需流程 |
| --- | --- | --- |
| T0 局部低风险 | 单文件、可逆、无契约面变化 | implement + targeted validation |
| T1 中等 | 多文件、边界清晰、无 shared contract 变化 | （必要时 research）→ plan → implement → verify |
| T2 高风险 | architecture / workflow state machine / Provider contract / Harness 行为 / shared schema / acceptance criteria / cross-module 变化 | research → specs → plan → implement → verification → implementation review |
| T3 关键契约 | canonical ownership、verification contract、paid/credential/recovery/QA acceptance 语义变化 | T2 全部 + final dual independent review |
| Bug | 任意 tier 的 bug | 先 systematic-debugging 做 root-cause，再按 tier 走流程，末做 regression validation |

Skill 按需触发、不预载：设计不清用 brainstorming，写 plan 用 writing-plans（`docs/superpowers/plans/`），执行 approved plan 用 executing-plans / subagent-driven-development，bug 用 systematic-debugging，完成前用 verification-before-completion，review 按本节边界；项目与 creative Skill 按上方 routing。

### Specs / Plan / Review Triggers

- Specs：architecture、workflow state machine、Provider/Harness contract、acceptance criteria、Shot generation/regeneration policy、shared schema、persistent project rule、cross-module behavior 变化或用户明确要求时触发；普通小修复不触发。
- Plan：多文件且顺序不明显、多阶段、T2/T3、architecture/Provider/workflow 修改或迁移/回滚/兼容性时触发；复用 writing-plans。简单 T0/T1 不产 plan artifact。
- Review：仅在完整稳定 target 上触发 T2/T3 spec、plan、implementation review；T3 完成前 final dual review。T0/T1 无独立 review；禁止碎片化循环，`PARSED` 或 review 执行不等于 acceptance。

### Dual Independent Review

T3（及 Parent 判定的高风险 spec/plan）对同一 immutable exact commit 或 staged snapshot 进行双独立审查并记录 target ID；reviewer 互不先看结论，均无 blocking issue 才可进入 Parent acceptance。冲突由 Parent 按证据裁决，不投票、不改 acceptance criteria；修复后两者重审同一新 target。可用时优先跨 runtime 的独立 context；派发和裁决步骤见 playbook。

### Verification Levels And Evidence

完成前区分 execution success、structural validity、functional correctness、acceptance criteria、final review acceptance 五级；下位或局部指标不能替代上位或成片目标。PASS / DONE / ACCEPTED 必须有 evidence，无法验证标 `NOT_EVALUATED`。

### Roles

Parent 独占最终 routing、分派、冲突裁决与 acceptance；Worker 不得降低 criteria；Reviewer 独立、read-only 优先，只报告 evidence + severity，不以通过任务为职责。

### Context Control

常驻 context 只含全局规则、runtime adapter 与 canonical 规则；Skill、spec、plan 和 Provider/workflow 文档按需加载。

## Module Boundaries

`docs/agent-primary-contract-matrix.md` 是 detailed surface owner、module boundary、forbidden
alternate path 与 focused verification 的唯一 human-readable owner。实现必须遵守上方
`Canonical Ownership`，不得在 `AGENTS.md` 或 `.agent/context/` 复制第二份 file-to-owner catalog。

## Coding Standards

- 遵循现有 Python style、naming、imports、dependency injection 与 module boundaries；优先 simple、stable、verifiable implementation。
- 只做用户要求的最小 scoped change；不要顺带清理 unrelated code、formatting、docs 或 generated artifacts。
- Architecture boundary 优先于局部最小 diff。新责任应进入合适模块，不得继续扩张 oversized multi-responsibility module；correctness-critical transaction lifecycle 不得为减行数机械拆散。
- 在可行时 non-test code file SHOULD 不超过 800 行；新增 distinct responsibility 前先复用或建立 cohesive boundary。
- 修改 public behavior、schema、layout、CLI 或 lifecycle 时，必须同步 tests 与 canonical docs。
- 优先使用 `rg` / `rg --files` 做搜索与发现、`apply_patch` 做 routine edits、shell 执行 Git/tests/build；structural dependency 问题使用可用的 codegraph tooling。
- Frontend design/behavior change 除非明显 trivial，默认进行 integrated browser verification。

## Change Rules

- 默认在当前 working tree 串行工作；本仓库单 writer 通常直接使用 `main`。只有用户明确要求或存在 concurrent writers 时才使用对应 branch/worktree isolation。
- 写入前检查 `git status`。Unrelated user changes 是真实 in-progress work：不得 reset、checkout、clean、revert、overwrite、stage 或 commit；若目标文件冲突，停止并报告。
- 只修改 task-owned files；每一处 changed line 都应可追溯到用户请求。只使用 `git add <specific-files>`。
- 除非用户明确批准或任务本身要求，不新增 runtime dependency，不改变 local-first default，不扩大 Provider/cloud scope。
- Schema、Manifest、artifact layout、CLI public contract 或 exit-code semantic 变化必须包含 migration/compatibility、tests 与 docs；禁止仅靠文档声明完成。
- 不编辑 `.workflow/`、`runs/`、生成媒体或其他产物，除非任务明确涉及。测试必须走标准 production loading/execution seam，不能通过裸解析或旁路伪造通过。
- 自身 change 产生的 orphan imports、variables、functions 或 files 必须清理；pre-existing cleanup 只报告，不顺手删除。

## Verification Contract

- `.agent/harness/policy.yaml` 是 changed-path routing 与 mandatory checks 的 machine-readable truth；`docs/agent-primary-contract-matrix.md` 提供 human-readable focused verification。两者的 routing 变更必须同步并测试。
- 开始时 inspect scope；完成时在 detached temporary worktree 对 non-empty exact staged snapshot 或 exact commit range 运行 policy checks。Code / executable tooling change 要有 fresh passing receipt 并验证 scope、policy、artifact hash 与 freshness；documentation/control-plane change 同样按真实 policy 验证。
- Unmapped owned paths fail safe 到 full tests 与 task-delta Architecture Gate；behavioral change 要有 public behavior、boundary、failure path 的 executable evidence。历史 debt 不能冒充 task regression，也不能刷新 baseline 隐藏 regression；未运行不得声称通过。
- Harness 不调度 Agent、变更 Product state、读取 secret 或执行 live Provider/media；CI 自行生成 evidence。Workflow 文件不证明 server enforcement。具体执行与远端核验见 [Verification, Pilot And Delivery Details](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details)。

## Provider Credential and Paid Execution Rules

- Raw credential 不得进入 repository、`.env`、artifact、prompt、argument、fixture、log、error、repr 或 receipt；lookup 只经 injected supplier，失败时 fail closed，不搜索其他 secret source。本机引用与查找步骤见 [Provider Credential And Paid Execution Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)。Credential 存在不证明 access、余额或授权。
- 用户明确要求完成必含 remote/paid call 的任务，即授权该 accepted Provider/model、inputs 与最少有限 submit count，不因付费重复询问；docs-only、plan、review、可行性分析、历史执行或旧 run 不授权 live call，也不得复用于 benchmark、额外 variants 或扩大后的 scope。未指定 count 时按已接受输出与 Shot 数封存最小 ceiling，不为此询价、查价、计算预计账单或刷新 pricing snapshot。
- 每次 submit 仍须 remaining-count check、exact preview、既有 Budget Guard/reservation、cloud-egress approval、secret reference、durable intent 与 one-use permit；现有 monetary ledger 不因此变成 count-based schema。Runtime monetary fields 仅消费预先配置并 sealed 的 operator upper bound，不代表官方实际价格。
- Ceiling 耗尽、scope/Provider/egress 变化、确需新增调用或上次 outcome unknown 时停止报告，禁止 blind retry、remint permit 或扩大授权。纯 operator upper bound 续期只按 [Operator Ceiling Renewal](.agent/context/control-plane-playbook.md#operator-ceiling-renewal)；缺失上限、真实市场报价过期或不符合续期条件仍是 compatibility blocker。

## Local ComfyUI Authorization Exemption

- 严格 loopback、完全 local/unmetered、无 cloud egress 的 ComfyUI `status` / `start` / `stop`、image/video generation、retry、variant 与 benchmark 不需要额外 user/task authorization。用户明确的 read-only 或禁止 media effects 仍优先；非 loopback、remote、metered、paid 或可能 cloud egress 不适用。
- 豁免只移除 authorization gate，不扩大 task scope；exact identity、sealed profile、preflight、local intent/one-use permit、canonical seam、唯一 committer、provenance、recovery 与 media verification 均保留。Retry/variant/benchmark 必须是 bounded、task-relevant 的新 exact attempt；unknown outcome 禁止 blind retry、fallback、permit remint 或重复 side effect。Per-Shot `FAIL` / `NOT_EVALUATED` 阻断下一 Shot，outcome known 时按 `LOCAL_BOUNDED_REPAIR_LOOP` 处理。Exact preview 是 readiness evidence，不是 user approval。操作细节见 [Provider Credential And Paid Execution Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)。

## Decision Gates

除非用户的当前明确请求已经批准对应 scope，否则以下变更必须先暂停并确认：

- 引入新 dependency、公共 CLI command/argument/exit semantics，或 schema / Manifest / artifact layout migration。
- 改变 local-first default、允许 remote fallback、引入新的 Provider selection path，或更改 canonical renderer/timeline/activation owner。
- 引入新的 v2 writer、自动 recovery、automatic candidate activation，或把 mutation 移入 reader/registry/dependency/adapter。
- 引入 frontend、API server、queue manager 或其他新的 product subsystem。
- 引入超出已验收 P4 audio/caption contract 的新音频子系统，或改变 canonical audio / timeline ownership。
- 开始新的 runtime slice、非 local-ComfyUI live smoke / benchmark、remote/paid Provider submit 或 quality-acceptance claim。符合 `Local ComfyUI Authorization Exemption` 的 lifecycle、generation、retry、variant 与 benchmark 无需暂停确认，但仍必须执行全部适用技术 gates。
- 放宽 crash safety、secret handling、Budget Guard、Cloud Egress、provenance、replay、recovery 或 QA acceptance contract。

## Repository-Specific Don't Repeat This

具体 implementation pitfalls、standard loader、resume/path、media-analysis tool 与交付案例只在
`.agent/context/control-plane-playbook.md` 的同名 section 维护；已经真实发生且可复现的 regression
才进入 `.agent/bug-memory/`。任何实现仍不得绕过 canonical owner、standard loader、atomic
state write、typed dependency、`ResolvedTimeline` 或 truthful delivery boundary。

## Completion Standard

在宣称完成前确认：

- Substantial AI-VIDEO work 到 stable checkpoint、completion、genuine blocker、handoff 或 compaction boundary 时，按 [record-ai-video-session](.agents/skills/record-ai-video-session/SKILL.md) 主动评估；repository 外的 effects 也计入，缺少 diff/hook/request 不免除。Unfinished/trivial work 按 Skill 判为 `no_record`。
- Diff 仅含 task-owned changes，canonical owner 与禁止旁路已复核；行为或公共契约变化同步 code、tests 与 canonical docs。
- 对 exact staged snapshot 或 commit range 完成 policy checks；code/tooling change 有 fresh verified passing Harness receipt，documentation/control-plane change 也按 policy 验证。
- 交付报告 changed files、验证证据、receipt 相对路径、publication state、风险及未验证区域。未执行的 live/provider/media/quality 验证不能由历史证据推断。

<!-- aoci:begin -->
## AOCI-CODE 与 CodeGraph

跨模块修改、架构理解、影响分析、复杂 bug、重构或重要功能开发时，按需先用 AOCI 获取职责、语义关系、API 与约束，再用 CodeGraph 核对 symbol、reference、dependency/call graph，以源码/LSP 为具体事实、tests 为最终验证。简单局部任务没有实际 AOCI 认知需求时，禁止仅为流程完整机械调用 AOCI。

AOCI cognition 永远不是 source of truth；Overview、Entry 与检索结果只作 advisory context，不能代替当前源码、tests、已验证 runtime evidence 或 canonical contracts。AOCI 正式认知位于 `aoci.txt`、`aoci.meta.txt`、`aoci.code.txt`；当前状态、维护顺序和安全停点以项目 AOCI MCP 的 `aoci_rules`、实时 Guide、工具返回及官方文档为准。索引语义必须基于当前源码和契约证据由模型编写；若认知与源码或 CodeGraph 不符，应修正认知，不能覆盖源码事实。受管理对象在最终稳定状态后按 AOCI 官方流程维护，不能把未对齐索引称为完整认知。
<!-- aoci:end -->
