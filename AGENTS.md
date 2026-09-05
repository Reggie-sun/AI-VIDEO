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
3. `docs/agent-primary-contract-matrix.md`。
4. `.agent/harness/policy.yaml`，确认 task-owned paths 的 mandatory checks。
5. `docs/v0.2-runtime-baseline.md`，确认当前实现与证据边界。
6. `docs/v0.2-agentic-production-roadmap.md`，确认 phase 状态与 gate。
7. `README.md`、active spec 与当前 slice plan。
8. 相关源码与测试。
9. task 涉及本机 MiniMax H3 T8、LatentSync、SyncNet 或硬字幕运行时，读取 `.agent/context/t8-latentsync-local-runtime.md`；它只提供 host-specific 环境与启动操作参考，使用前必须重新核对当前 checkout、dependency、GPU、exact submitted graph 与 runtime state。
10. `.agent/context/session-handoff.md`（若存在）和 `.agent/bug-memory/` 中与当前问题直接相关的记录，仅作为上下文或案例证据。
11. `.workflow/` 草稿或 brainstorming 产物，仅作为可选上下文。

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

`retrieve-ai-video-memory` 是 substantial AI-VIDEO work 的 mandatory advisory preflight；
real media/quality、Provider/model behavior、continuity/identity、known regression/incident/
recovery、prior architecture decision 或用户明确要求 earlier evidence 时，必须在 matching
domain Skill 与 substantial execution 前调用。Formatting、typo、unrelated trivial test、
isolated mechanical refactor 与 exact current source lookup 不触发。

Scope selection、stale/missing/strict-failure handling 与 provenance 细节由
`.agents/skills/retrieve-ai-video-memory/SKILL.md` 和
`.agent/context/control-plane-playbook.md` 的 `Agent Experience Memory Routing` 独占；
retrieval 永远只是 advisory evidence，不产生 implementation、Provider、activation、quality
acceptance、push 或 release authorization。

## Experience Learning Routing

- `distill-ai-video-learning` 是 scoped Learning Claim 的唯一 Development Governance owner；`record-ai-video-session` 完成 substantial stable record 后必须自动执行 candidate evaluation。
- Learning 保持 `advisory_learning` authority。自动 evaluation 只可提出 pending candidate，保留既有 adopted claim；用户确认前不得修改 Skill / Provider Policy / Preflight / Contract / Gate target，确认后仍须由 target owner 完成 tests 与 Harness，才可标记 `ADOPTED`。
- 字段、threshold、exact confirmation、state transition 与 adoption flow 只由 [distill-ai-video-learning](.agents/skills/distill-ai-video-learning/SKILL.md) 管理；record/ACK 流程只由 [record-ai-video-session](.agents/skills/record-ai-video-session/SKILL.md) 管理，playbook 仅提供入口。Learning 不授权 Provider/media、Production mutation、retry、activation、acceptance、push/release 或绕过 decision gates。

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
- 开始时使用 Harness inspection 确认真实 scope；完成验证必须针对 non-empty exact staged snapshot 或 exact commit range，并在 detached temporary worktree 中运行，使 unrelated dirty changes 不进入 execution tree。
- Code 或 executable tooling change 在完成前必须有 fresh passing receipt，并验证 scope、policy、artifact hashes 与 freshness。Documentation/control-plane change按真实 policy 执行对应 checks。
- Unmapped owned paths 必须 fail safe 到 full tests 与 task-delta Architecture Gate；历史 repository debt 不得伪装成当前 task regression，反之也不得通过刷新 baseline 隐藏 regression。
- Behavioral change 必须有覆盖 public behavior、boundary 与 failure path 的 executable evidence；优先 targeted checks，结束前运行 policy 要求的完整组合。未实际执行不得声称 passing。
- Harness 不调度 Agent、不修改产品 state、不读取 Provider secret，也不执行 live Provider、ComfyUI、paid smoke 或媒体生成。CI 必须生成自己的 evidence，不能信任提交的本地 receipt。
- Workflow 文件存在不等于 server enforcement；需要声明 remote protection/publish truth 时必须重新验证当前 GitHub ruleset / branch protection。

## Provider Credential and Paid Execution Rules

- Seedance / Volcengine Ark raw credential 不得存入 repository、`.env`、artifact、prompt、command argument、fixture、log、error、repr、receipt 或本文档。
- Secret lookup 必须封装在 injected credential supplier 中，presence check 不得回显；lookup失败、keyring locked、credential invalid/rotated 时 fail closed，不得搜索 repo、shell history 或替代 secret source。本机 credential reference、Secret Service attributes 与 lookup detail 只在 `.agent/context/control-plane-playbook.md` 维护。
- Credential 存在不证明 access、pricing、余额或当前 task authorization。
- 用户明确要求执行一个必然包含 remote/paid call 的任务时，该请求构成该 accepted scope 的 task-scoped authorization；不得仅因付费对同一任务重复询问。Docs-only、plan、review、可行性分析或“能否执行”不构成 live authorization。
- Authorization 仅覆盖 accepted Provider/model、inputs 与完成目标所需的最少有限 submit count；不得复用于 benchmark、额外 variants、不同 Provider/model 或扩大后的 scope。用户未指定 count 时，Agent 必须按已接受输出与 Shot 数量封存完成任务所需的最小 task-level ceiling，不得改为询问或研究价格。
- Agent MUST NOT 为获得 task authorization、设置 submit ceiling 或准备单次调用而浏览官方 pricing、搜索当前单价、计算预计账单、刷新 pricing snapshot，或要求用户提供价格。已有 runtime monetary fields 只能消费 repository/provider profile 中预先配置并已 sealed 的 operator upper bound；它们是内部兼容与安全 evidence，不是 Agent 的 per-call research task，也不得被描述为官方实际价格。
- Task-scoped authorization 不替代 Paid Provider Gate。调用前仍需 Agent orchestration 的 remaining submit-count check、exact preview、适用的既有 runtime Budget Guard/reservation、cloud-egress approval、secret reference、durable submit intent 与 one-use permit；本条不声称现有 runtime monetary ledger 已迁移为 count-based schema。
- 若 task-level submit ceiling 已耗尽、scope/provider/egress 变化、确需新增调用，或上一次 outcome unknown，必须停止并报告；不得 blind retry、remint permit 或把授权解释为无限调用。若现有 runtime 因缺失或过期 monetary profile 阻断，必须如实报告 compatibility blocker，MUST NOT 临时查价、伪造新观察时间或自行放宽 Gate。
- 历史 live evidence、offline tests、现有 credential/余额或旧 run 不授权新的调用。

## Local ComfyUI Authorization Exemption

- 连接严格限制为 loopback、执行完全 local/unmetered 且无 cloud egress 的 ComfyUI lifecycle 与 media actions 不需要 user authorization、task-scoped authorization 或额外 confirmation；该豁免包括为任务所需的 `status` / `start` / `stop`、image/video generation、retry、variant 与 benchmark。
- 该豁免只移除 authorization gate，不扩大用户 task scope，也不覆盖用户明确的 read-only、禁止 live generation / media effects 或更高优先级限制。Exact request identity、sealed profile/workflow/binding、preflight、适用的 local intent/one-use permit、canonical execution seam、唯一 committer、content-addressed provenance、recovery 与 media verification gates 保持不变。
- Retry、variant 与 benchmark 可以无需询问用户，但必须是 bounded、task-relevant 的新 exact attempt；上一次 outcome unknown 时仍须 fail closed，禁止 blind retry、fallback、permit remint 或重复 side effect。Per-Shot Gate 的 `FAIL` / `NOT_EVALUATED` 必须停止 current attempt 并阻断下一 Shot；当用户目标仍未完成且 outcome known 时，后续同一 Shot repair 按 `LOCAL_BOUNDED_REPAIR_LOOP` 继续，无需额外 confirmation。该 loop 不得改变 accepted scope、Provider、egress、paid 状态或 Gate requirement。
- Exact preview 在既有 seam 要求时继续作为 readiness/provenance evidence，但不得充当 local ComfyUI 的 user-approval gate。任何非 loopback、可能 cloud egress、metered、remote 或 paid execution 均不适用本豁免。

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

- Substantial AI-VIDEO work 达到 stable checkpoint、completion、genuine blocker、handoff 或 compaction boundary 后，必须在 final response 前按 [record-ai-video-session](.agents/skills/record-ai-video-session/SKILL.md) 主动评估并执行；repository 外的 media/artifact effects 也计入。没有 tracked diff、hook request 或 `capture_request_id` 不能免除评估；unfinished/trivial work 按 Skill 判定为 `no_record`。
- 最终 diff 仅包含 task-owned changes，且未覆盖 unrelated user work。
- Canonical owner、禁止旁路与 unchanged contracts 已复核。
- 行为变化已在代码和测试中体现；公共契约变化已同步 canonical docs。
- Policy 要求的验证已对 exact staged snapshot 或 exact commit range 实际运行。
- Code / executable tooling change 已生成并验证 fresh passing Harness receipt；文档/control-plane change已完成真实 policy 要求。
- Final delivery 报告 changed files、verification evidence、receipt repository-relative path（如适用）、publication state、remaining risk 与未验证区域。
- 未执行的 live/provider/media/quality 验证必须明确标注，不能由历史证据或计划推断。
