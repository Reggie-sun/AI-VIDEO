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
9. `.agent/context/session-handoff.md`（若存在）和 `.agent/bug-memory/` 中与当前问题直接相关的记录，仅作为上下文或案例证据。
10. `.workflow/` 草稿或 brainstorming 产物，仅作为可选上下文。

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

AI-VIDEO remains the sole owner of production truth. External Skills provide advisory knowledge only unless an explicitly approved project contract says otherwise. Skill guidance MUST be translated into AI-VIDEO domain contracts before execution and MUST NOT mutate or own canonical state.

Use the minimum matching Skill set. Installation、description matching 或“本仓库生产视频”本身不构成触发条件。纯 production-state、asset、schema、dependency、timeline、render、activation、recovery 或 Provider-lifecycle 工作只使用 AI-VIDEO code 与 accepted contracts。

### `hell-grind-aigc-skill`

SHOULD proactively use for semantic Shot design、open/close state、cross-Shot continuity、identity/state/spatial/axis/action/light/environment/audio continuity、image/video prompt structure、generation failure diagnosis、iteration 与 candidate reasoning。

优先用于“Shots 之间什么必须保持或改变？”以及“generated Shot 为什么失败？”。AI-VIDEO Character、Scene、Shot 与 asset records 始终是 source of truth。MUST NOT 创建或维护平行的 Hell-Grind project schema、asset registry、generation ledger、review state 或 delivery truth。

### `higgsfield`

SHOULD proactively use for provider/model-specific prompt adaptation、Seedance/Hailuo/Kling/Veo guidance、T2V/I2V/reference/continuation/extension mode guidance、provider-specific camera vocabulary 与 generation troubleshooting。

只在 AI-VIDEO semantic Shot / continuity intent 已建立后使用。Model/mode 推荐不得选择或切换 active Provider、读取 credential、提交 generation，或绕过 AI-VIDEO Provider Router、Paid Provider Gate、budget、cloud egress、provenance、lifecycle、activation 与 recovery。Higgsfield CLI、MCP、account、workspace、memory 或 ledger 不是 AI-VIDEO owner。

### `video-shotcraft`

SHOULD proactively use for motion design、image motion、motion graphics、shot language、camera movement、pacing、transition、SFX、beat sync 与 visual QA ideas。

其 Remotion implementation、recipe、timeline 与 renderer 只作为 creative / implementation reference。选定方案必须翻译成 AI-VIDEO composition directives；不得创建第二套 canonical timeline/renderer、替代 `ResolvedTimeline` / HyperFrames，或绕过 AI-VIDEO QA / Repair lifecycle。

### Routing Precedence

- Semantic continuity / Shot-state problem -> `hell-grind-aigc-skill`。
- Specific generative model / Provider prompting problem -> `higgsfield`。
- Deterministic motion design / graphics / pacing problem -> `video-shotcraft`。
- Production state / assets / dependency / timeline / render / Provider execution / activation / recovery -> AI-VIDEO code and contracts。

多 Skill 组合必须按依赖顺序调用；后续 Skill 可以适配前序 advisory result，但不能重定义上游 semantic contract 或下游 production truth。

```text
generated-video continuity:
AI-VIDEO Shot intent
  -> hell-grind-aigc-skill: establish semantic continuity
  -> higgsfield: adapt the approved contract to Provider prompt/mode guidance
  -> AI-VIDEO Provider Request: provenance, lifecycle, activation, recovery

image motion / motion graphics:
AI-VIDEO Shot intent
  -> hell-grind-aigc-skill when semantic state needs clarification
  -> video-shotcraft: motion, pacing, transition, SFX, beat treatment
  -> AI-VIDEO CompositionSpec -> ResolvedTimeline -> HyperFrames
```

External Skills MUST NOT invent or own canonical Character/Scene/Shot truth、Asset Registry、Manifest、Dependency Graph、timeline、renderer selection、Provider lifecycle、review/repair 或 delivery state。

## Module Boundaries

- `src/ai_video/cli.py`：CLI parsing 与用户命令编排。
- `src/ai_video/config.py`：YAML/config validation、本地策略与路径解析。
- `src/ai_video/workflow_loader.py` / `workflow_renderer.py`：标准 workflow loading、UI-to-API conversion 与 pure binding/rendering。
- `src/ai_video/comfy_client.py`：ComfyUI transport、polling、artifact download 与 typed transport failure。
- `src/ai_video/pipeline.py` / `manifest.py`：Legacy Shot orchestration、resume 与 atomic Legacy Manifest persistence。
- `src/ai_video/ffmpeg_tools.py`：probe、clip validation、frame extraction、normalization 与 stitching。
- `src/ai_video/production/models.py` / `hashing.py` / `paths.py` / `validation.py`：strict schemas、sealing、containment 与 static validation。
- `src/ai_video/production/registry.py` / `project.py` / `_*project_reader.py`：read-only selected Asset Registry / Production Project evidence loading；不得写入、恢复或激活。
- `src/ai_video/production/state_commit.py` / `_state_commit_*`：唯一 public v2 writer、activation、commit 与 recovery boundary；private modules不得形成第二 writer。
- `src/ai_video/production/dependency.py`：pure immutable graph、desired fingerprint、precise invalidation 与 rebuild decisions；不得写文件、Manifest、Registry 或 runtime status。
- `src/ai_video/production/composition.py` / `hyperframes.py` / `visual_media.py`：canonical composition resolution、media validation 与 selected HyperFrames execution；不得另造 timeline。
- `src/ai_video/production/audio.py` / `captions.py` / voice adapters：audio、voice、caption contracts；timing仍归 `ResolvedTimeline`，durable mutation仍归 committer。
- `src/ai_video/production/review.py` 与 `src/ai_video_mcp/**`：pure review contracts或 raw analysis evidence；不得自判或写入 Production acceptance。
- `src/ai_video/production/image.py` / `video.py` / Provider adapters：provider-neutral contracts与显式 adapter execution；不得成为 writer、resolver、Provider selector 或 activation owner。
- `src/ai_video/production/__init__.py`：只暴露 approved public imports，不承载 implementation。

更细的 surface owner、forbidden alternate path 与 focused tests 以 `docs/agent-primary-contract-matrix.md` 为准。

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
- 稳定 credential reference 是 `ARK_API_KEY`；本机 Secret Service exact attributes 为 `application ai-video`、`provider seedance`、`credential ARK_API_KEY`。不得改用 `SEEDANCE_API_KEY`、读取 MiniMax credential 或建立 environment/provider fallback。
- Secret lookup 必须封装在 injected credential supplier 中。不得在交互终端把 secret 输出到 stdout；presence check 必须不回显。Lookup失败、keyring locked、credential invalid/rotated 时 fail closed，不得搜索 repo、shell history 或替代 secret source。
- Credential 存在不证明 access、pricing、余额或当前 task authorization。
- 用户明确要求执行一个必然包含 remote/paid call 的任务时，该请求构成该 accepted scope 的 task-scoped authorization；不得仅因付费对同一任务重复询问。Docs-only、plan、review、可行性分析或“能否执行”不构成 live authorization。
- Authorization 仅覆盖 accepted Provider/model、inputs、budget 与完成目标所需的最少调用；不得复用于 benchmark、额外 variants、不同 Provider/model 或扩大后的 scope。
- Task-scoped authorization 不替代 Paid Provider Gate。调用前仍需 exact preview、finite budget ceiling/reservation、cloud-egress approval、secret reference、durable submit intent 与 one-use permit。
- 若费用超过 ceiling、scope/provider/egress 变化、需要更多调用，或上一次 outcome unknown，必须停止并报告；不得 blind retry、remint permit 或把授权解释为无限额度。
- 历史 live evidence、offline tests、现有 credential/余额或旧 run 不授权新的调用。

## Decision Gates

除非用户的当前明确请求已经批准对应 scope，否则以下变更必须先暂停并确认：

- 引入新 dependency、公共 CLI command/argument/exit semantics，或 schema / Manifest / artifact layout migration。
- 改变 local-first default、允许 remote fallback、引入新的 Provider selection path，或更改 canonical renderer/timeline/activation owner。
- 引入新的 v2 writer、自动 recovery、automatic candidate activation，或把 mutation 移入 reader/registry/dependency/adapter。
- 引入 frontend、API server、queue manager 或其他新的 product subsystem。
- 引入超出已验收 P4 audio/caption contract 的新音频子系统，或改变 canonical audio / timeline ownership。
- 开始新的 runtime slice、live smoke、benchmark、remote/paid Provider submit 或 quality-acceptance claim。当前 task 已满足 task-scoped authorization 时不要重复确认，但仍必须执行全部技术 gates。
- 放宽 crash safety、secret handling、Budget Guard、Cloud Egress、provenance、replay、recovery 或 QA acceptance contract。

## Repository-Specific Don't Repeat This

- 不要对同一 `run_id` 再次调用 `run()` 来实现 resume；从持久化 Manifest 恢复。
- 不要将包含 `..` 的相对 artifact path 写入 Manifest 或 resolved config；持久化路径必须是干净绝对路径。
- 不要在更新 `final_output` 等 terminal state 后绕过 atomic Manifest write。
- 不要在测试中用裸 YAML/JSON parsing 绕过标准 `load_workflow_template()` 或 Production loader。
- Production invalidation 不得退化为 Shot-order blanket stale；只沿 canonical typed dependency edges 传播。
- 不要让 native media audio 绕过 canonical P4 mixer，也不要让 graph、Provider 或 Skill 重算 `ResolvedTimeline`。
- Project-local `video-analysis` 是本仓库默认视频检查工具；全局 `videoscan` 只可作为 metadata/frame helper，不能成为 Production QA owner。
- 交付 generated-video 时只提供真实 live/fetched/validated output；不得把 preflight、fake fixture、smoke artifact、technical evidence 或 fetch success冒充 activated、quality-accepted 或 final delivery truth。

## Completion Standard

在宣称完成前确认：

- 最终 diff 仅包含 task-owned changes，且未覆盖 unrelated user work。
- Canonical owner、禁止旁路与 unchanged contracts 已复核。
- 行为变化已在代码和测试中体现；公共契约变化已同步 canonical docs。
- Policy 要求的验证已对 exact staged snapshot 或 exact commit range 实际运行。
- Code / executable tooling change 已生成并验证 fresh passing Harness receipt；文档/control-plane change已完成真实 policy 要求。
- Final delivery 报告 changed files、verification evidence、receipt repository-relative path（如适用）、publication state、remaining risk 与未验证区域。
- 未执行的 live/provider/media/quality 验证必须明确标注，不能由历史证据或计划推断。
