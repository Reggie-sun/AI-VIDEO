# AI-VIDEO Agent Guide

适用于在本仓库中工作的 Codex、Claude 以及其他编码 Agent。本文件只保存长期稳定的 repository constitution、routing policy、canonical ownership、change rules 与 verification contract；不作为 runtime status dashboard、phase ledger、live-provider evidence log、commit history 或 benchmark report。

## Purpose

- 保持 Legacy `0.1.x` local-first CLI 与 v0.2 Production Python APIs 的边界清晰。
- 维护 manifest-first、content-addressed evidence、explicit recovery、precise invalidation 与 deterministic composition 等长期产品契约。
- 让每项变更先找到唯一 owner，再按真实 changed paths 完成可复现验证。
- 默认使用中文沟通；`command`、`path`、API、schema、class 与 Skill 名保持原文。过程更新应简短、具体、基于当前仓库证据；review 先报告问题与风险。

## Rule Layers

`AGENTS.md` 是入口合同，负责长期 constitution、ownership、不可绕过的 gates 与 completion contract。低频执行细节下沉到 `.agent/context/control-plane-playbook.md`；该 playbook 只补充执行方法，不定义新的 workflow 或 canonical state。`.agent/harness/policy.yaml` 是 changed-path routing 与 mandatory checks 的 machine-readable truth。

下位文档不得静默覆盖用户指令、当前 code/tests/runtime evidence、`AGENTS.md`、`docs/agent-primary-contract-matrix.md` 或 Harness policy。发现职责重复时，优先收敛到现有 owner，不新增平行 control plane。

## Runtime Truth Sources

| Concern | Canonical Source |
| --- | --- |
| Agent authority、routing、ownership、change 与 completion rules | `AGENTS.md` |
| Surface owner、invariant、禁止旁路与 focused verification | `docs/agent-primary-contract-matrix.md` |
| Changed-path category、mandatory checks 与 receipt routing | `.agent/harness/policy.yaml`、`scripts/agent_harness.py` |
| Low-frequency creative、provider、module、pilot 与 memory execution details | `.agent/context/control-plane-playbook.md` |
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
5. `.agent/context/control-plane-playbook.md`，仅在 task 命中其低频执行主题时按需读取；命中 creative、Provider、media quality 或历史 failure 时必须读取相关章节。
6. `docs/v0.2-runtime-baseline.md`，确认当前实现与证据边界。
7. `docs/v0.2-agentic-production-roadmap.md`，确认 phase 状态与 gate。
8. `README.md`、active spec 与当前 slice plan。
9. 相关源码与测试。
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

## Spec And Plan Routing

Agent 必须根据当前 task 的 uncertainty、contract impact、execution complexity、handoff need 与 verification risk，自主选择 `neither`、`spec only`、`plan only` 或 `spec + plan`。除非用户明确限定 artifact scope，否则不得仅为询问“是否需要写 spec / plan”而暂停；应在过程更新中简短说明选择及依据，然后继续到自然停止点。用户明确要求或禁止 spec / plan 时，以用户指令为准。

- `neither`：需求、owner、边界和验证方式已清晰，且工作是 narrow bug fix、局部 documentation/configuration、mechanical change 或可在单次连续执行中安全完成的 bounded implementation。此类 task 使用 thread 内的 lightweight contract / plan 即可，不创建重复 artifact。
- `spec only`：目标行为、public contract、schema/data model、canonical owner、lifecycle/state、compatibility、safety gate 或关键 tradeoff 尚需形成 durable target，但尚未获准实施、暂不需要 execution sequencing，或 implementation plan 会过早固化未知细节。
- `plan only`：已有 accepted spec、canonical contract 或足够明确的用户要求，但 implementation 跨多个 modules/milestones、存在 ordering/migration/recovery concern、需要 delegated handoff、预计跨 session，或 verification matrix 需要 durable sequencing。
- `spec + plan`：既需要稳定新的或显著变化的 target contract，又需要组织 non-trivial execution。必须先收敛 spec，再让 plan 引用该 spec；不得用 plan 偷带未解决的 product/architecture 决策。

下列情况默认提高到 durable spec：开始新的 runtime slice；改变 public API/CLI、schema、Manifest、artifact layout、canonical owner、Provider/renderer/timeline selection、activation/recovery、paid/cloud/secret/safety contract；或存在多个合理方案且选择会影响 compatibility 或后续 slices。下列情况默认提高到 durable plan：改动跨越多个 canonical owners、需要 migration 或 rollback、包含多个有依赖关系的 implementation units、需要跨 session / agent handoff，或无法用一个 focused verification command可信覆盖。

Agent 不得仅因 file count、task 被称为 feature、使用了 Skill、存在历史 spec/plan，或“先写文档更完整”而创建 artifact。Root cause 尚未确定的 diagnosis 应先收集 evidence；除非 investigation 本身需要 durable multi-session coordination，否则不得用 prospective spec / plan 代替 diagnosis。已有 active artifact 能被安全更新时，优先更新唯一 owner，不创建并行 spec / plan。

Durable specs 写入 `docs/superpowers/specs/YYYY-MM-DD-<slug>.md`，durable plans 写入 `docs/superpowers/plans/YYYY-MM-DD-<slug>.md`；这些路径只是 artifact storage，不会自动启用 Superpowers 或其他 workflow。Artifact 必须记录 `Status`、accepted scope、out-of-scope、contracts/invariants、acceptance criteria、verification，以及 relevant assumptions / unresolved decisions；plan 还必须引用 governing spec 或明确写明其直接依据的 canonical contract。若关键选择会扩大用户 scope、触发 `Decision Gates` 或产生 materially different outcomes，必须先向用户提问，不能由 Agent 借写 spec / plan 自行批准。

创建或更新 spec / plan 属于 task preparation，不代表 implementation、remote/paid call、quality acceptance、push 或 release 已获授权，也不改变 Runtime Truth Sources。若用户请求 implementation 且上述关键选择均已解决，Agent 可在同一 task 内先写必要 artifact 再继续实施，无需为 lifecycle transition 重复请求确认。

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
- Remote/paid execution 必须 explicit opt-in，并通过既有 budget、cloud-egress、secret、durable intent、one-use permit、provenance、activation 与 recovery gates。

### Cross-Cutting Safety

- Immutable evidence 必须 content-addressed，并绑定 exact selected inputs、actor/tool identity 与 measured artifact bytes。
- Mutable lifecycle 只存在于 canonical Manifest owner；immutable graph、receipt 或 Registry record 不得偷带第二套 lifecycle truth。
- Exact replay 不重复 Provider、renderer、analyzer、materializer 或 Manifest write 等外部副作用，也不得无证据推进 state。
- Unknown outcome 必须 fail closed；recovery 必须显式，不能 blind retry、remint permit、猜测 mixed state、自动激活或删除完整 orphan evidence。
- Typed cross-module failures使用 `AiVideoError` 与 `ErrorCode`；retryability 由 typed metadata 决定，常规 CLI 输出不得泄露 raw traceback。

## Canonical Ownership

| Concern | Canonical Owner |
| --- | --- |
| Creative intent | Codex + approved AI-VIDEO Character / Scene / Shot artifacts |
| Project schema and canonical Character / Scene / Shot artifacts | AI-VIDEO `ProductionProject` |
| Asset identity and provenance | Asset Registry |
| v2 mutable lifecycle and active pointers | Production Manifest |
| v2 writes, activation, and recovery | `ProductionStateCommitter` |
| Dependency semantics, desired fingerprint computation, invalidation, rebuild frontier | Dependency Graph / resolver |
| Timing, order, frame, sample, and source trim | `ResolvedTimeline` |
| Default render execution | HyperFrames adapter |
| Provider-specific generation | Selected AI-VIDEO Provider adapter behind AI-VIDEO gates |
| QA, repair, and final-acceptance evidence | AI-VIDEO Review / Repair receipts and Manifest lifecycle |
| External Skills | Advisory knowledge only |

Reader、registry、validation、dependency、Provider adapter、renderer 与 analyzer 可以验证或消费 canonical state，但不得直接决定 durable activation。Fetch、render、analysis 或 generation success 本身不等于 candidate activation、QA acceptance 或 delivery truth。

## Creative Skill Routing

Creative skill selection、Agent-side image generation preference、mandatory preflight evidence、Skill routing precedence 与 `runtime_skill_calls = 0` boundary 见 `.agent/context/control-plane-playbook.md` 第 1 节。

这些规则在命中对应 creative task 时是 mandatory，但 playbook 只承接低频执行细节；AI-VIDEO、其 canonical artifacts、Manifest、Registry、Dependency Graph、ResolvedTimeline、HyperFrames、Provider lifecycle、review/repair 与 delivery truth 的 ownership 仍由本文件和 `docs/agent-primary-contract-matrix.md` 定义。

## Module Boundaries

稳定 module owner、禁止旁路与 focused-test routing 见 `.agent/context/control-plane-playbook.md` 第 2 节；surface owner 与 invariant 以 `docs/agent-primary-contract-matrix.md` 为准。

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
- Harness inspection 后，完成验证必须针对 non-empty exact staged snapshot 或 exact commit range，并在 detached temporary worktree 中运行，使 unrelated dirty changes 不进入 execution tree。
- Code 或 executable tooling change 必须有 fresh passing receipt；documentation/control-plane change 也必须执行 policy 路由的真实 checks。详细 receipt、Pilot、media acceptance 与 delivery boundary 见 `.agent/context/control-plane-playbook.md` 第 4 节。
- Unmapped owned paths 必须 fail safe 到 full tests 与 task-delta Architecture Gate；未实际执行不得声称 passing。Harness 不调度 Agent、不修改产品 state、不读取 Provider secret，也不执行 live Provider、ComfyUI、paid smoke 或媒体生成。
- Workflow 文件存在不等于 server enforcement；需要声明 remote protection/publish truth 时必须重新验证当前 GitHub ruleset / branch protection。

## Provider Credential and Paid Execution Rules

- Seedance / Volcengine Ark raw credential 不得存入 repository、`.env`、artifact、prompt、command argument、fixture、log、error、repr、receipt 或本文档。
- 稳定 credential reference 是 `ARK_API_KEY`；本机 Secret Service exact attributes 为 `application ai-video`、`provider seedance`、`credential ARK_API_KEY`。不得改用 `SEEDANCE_API_KEY` 或建立 environment/provider fallback。
- MiniMax Speech credential 已存入本机 Secret Service；`secret-tool` label 为 `AI-VIDEO MiniMax Speech`，exact attributes 为 `application ai-video`、`provider minimax-speech`、`credential MINIMAX_SPEECH_API_KEY`。其稳定 credential reference 是 `MINIMAX_SPEECH_API_KEY`；除该明确 reference 外，不得读取其他 MiniMax credential 或建立 environment/provider fallback。
- 在当前 task scope 内调用已配置的 loopback local ComfyUI Provider 生成 media，不需要 task-scoped user authorization，也不得为该调用重复请求确认。此豁免只适用于 local、unmetered、no-cloud-egress execution；用户明确禁止 live generation 时仍必须遵守，且 sealed profile、preflight、local permit、唯一 committer、recovery 与 media verification gates 保持不变。
- Secret lookup、task-scoped authorization、Paid Provider Gate、budget、cloud-egress、durable intent、one-use permit 与 unknown outcome recovery 细节见 `.agent/context/control-plane-playbook.md` 第 3 节；这些 gates 在命中时仍是 mandatory。

## Decision Gates

除非用户的当前明确请求已经批准对应 scope，否则以下变更必须先暂停并确认：

- 引入新 dependency、公共 CLI command/argument/exit semantics，或 schema / Manifest / artifact layout migration。
- 改变 local-first default、允许 remote fallback、引入新的 Provider selection path，或更改 canonical renderer/timeline/activation owner。
- 引入新的 v2 writer、自动 recovery、automatic candidate activation，或把 mutation 移入 reader/registry/dependency/adapter。
- 引入 frontend、API server、queue manager 或其他新的 product subsystem。
- 引入超出已验收 P4 audio/caption contract 的新音频子系统，或改变 canonical audio / timeline ownership。
- 开始新的 runtime slice、benchmark、remote/paid Provider live smoke 或 submit，或提出 quality-acceptance claim。Loopback local ComfyUI generation/live smoke 按上述本地豁免执行；其他 task 在已满足 task-scoped authorization 时不要重复确认，但仍必须执行全部技术 gates。
- 放宽 crash safety、secret handling、Budget Guard、Cloud Egress、provenance、replay、recovery 或 QA acceptance contract。

## Operational Detail Routing

- Repository-specific failure boundaries、Legacy/Production 易错项与 generated-video delivery 约束见 `.agent/context/control-plane-playbook.md` 第 5 节。

## Agent Experience Memory (Advisory)

Agent Memory 的 scope、检索触发条件与 final relevant search 规则见 `.agent/context/control-plane-playbook.md` 第 6 节。Memory 始终是 advisory，不能覆盖当前 code、tests、runtime evidence 或 current architecture contracts。

## Completion Standard

在宣称完成前确认：

- 最终 diff 仅包含 task-owned changes，且未覆盖 unrelated user work。
- Canonical owner、禁止旁路与 unchanged contracts 已复核。
- 行为变化已在代码和测试中体现；公共契约变化已同步 canonical docs。
- Policy 要求的验证已对 exact staged snapshot 或 exact commit range 实际运行。
- Code / executable tooling change 已生成并验证 fresh passing Harness receipt；文档/control-plane change已完成真实 policy 要求。
- Final delivery 报告 changed files、verification evidence、receipt repository-relative path（如适用）、publication state、remaining risk 与未验证区域。
- 未执行的 live/provider/media/quality 验证必须明确标注，不能由历史证据或计划推断。
