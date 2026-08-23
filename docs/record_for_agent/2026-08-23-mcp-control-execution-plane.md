# MCP Control And Execution Plane Architecture Record

Date: 2026-08-23

## Purpose

本文记录AI-VIDEO对Comfy MCP与Seedance MCP的只读架构审计、accepted spec/plan checkpoint及明确的
Development Governance / Product Runtime边界，避免后续Agent把“Agent调用MCP更方便”误解为“Product
Runtime应依赖MCP”。

本文不是MCP installation、ComfyUI live、workflow submit、Provider调用、paid smoke、Product Runtime
implementation、push或release授权。代码、测试、canonical docs与当前runtime evidence仍是source of truth。

## Stable Checkpoint

本窗口创建并提交：

- `docs/superpowers/specs/2026-08-23-ai-video-mcp-control-execution-plane.md`
- `docs/superpowers/plans/2026-08-23-ai-video-mcp-control-execution-plane.md`

Local commit：

```text
59016d8ed8ed59dd4a0bb70b43f641f673822ba1
docs: specify MCP control execution plane
```

该commit已进入local `main`，尚未进入`origin/main`，未push/release。创建spec/plan时local `main`相对
`origin/main`为ahead状态；不得仅由local ancestry推断remote publication。

## Execution Timing Follow-Up

用户随后要求plan必须明确记录“什么时候应该开始、做到什么程度算完成”。Plan已从
`Ready for explicit implementation authorization`更新为：

```text
Deferred
Current answer: DO NOT START NOW
```

对应local commit：

```text
717f81c7f7331de33c75d12b21b0585050a89616
docs: define MCP adoption gates
```

该commit只修改：

```text
docs/superpowers/plans/2026-08-23-ai-video-mcp-control-execution-plane.md
```

当前没有证据证明ComfyUI discovery或临时HTTP/Python实验摩擦正在阻塞后续工作，因此不得仅因plan存在、
MCP看起来更先进或希望减少Production adapter代码而开始实施。

Start gate要求全部满足：

1. 新的current task明确授权开始实现Comfy MCP Agent control plane；
2. 两个独立Local Comfy开发任务均出现重复手工discovery/临时HTTP/Python/output定位摩擦，或一个当前任务
   因缺Agent-readable discovery surface而真实blocked；
3. 收益仍限定为Development discovery/experiment ergonomics；
4. existing Local ComfyUI与direct AI-VIDEO path已独立可用；
5. adoption不会延迟更高优先级continuity、quality、Provider lifecycle或Pilot acceptance；
6. `.codex/config.toml`与playbook没有same-file ownership conflict；
7. pinned source、entrypoint、license、`comfy-cli` compatibility、tools、retry与single-loopback配置重新审计通过；
8. scope可以停在Milestone 0-2，不需要Product Runtime、Seedance、remote/Partner、paid或schema/layout change。

推荐最小完成点是Milestone 0-2：pinned isolated installation、project routing、真实MCP handshake与read-only
discovery、zero submit/upload/queue/Product mutation、Product Runtime zero dependency、exact staged/commit-range
Harness及local/publication truth分层报告。达到该点必须停止；Milestone 3 generation不是minimal adoption的完成
条件。

Milestone 3只可由新的task单独授权一次`development_experiment`。Plan可以在Agent-only retained、adoption
rejected/rolled back、experiment not needed或future executor gate failed四种结果下正常closure；MCP-backed
Product executor与Seedance MCP不属于本plan的completion definition。

本follow-up只更新durable plan/status，没有安装或启动MCP、运行ComfyUI、调用Provider、生成媒体或改变
Production Runtime。

## Architecture Decision

Accepted direction是：

```text
Development / Experiment Control Plane

Codex / Agent
    -> Comfy MCP
    -> local ComfyUI discovery or bounded development experiment
    -> non-authoritative development evidence


AI-VIDEO Product Runtime

VideoGenerationRequest
    -> Router + exact capability/profile
    -> VideoGenerationService
    -> ProductionStateCommitter intent/permit/receipts
    -> sealed direct ComfyUI or Ark adapter
    -> candidate/activation/recovery/replay
    -> P6 / human acceptance
```

Decision mapping：

- Comfy MCP experimentation：`RECOMMEND`；
- Comfy MCP Production Runtime：`DO NOT RECOMMEND`；
- Seedance MCP experimentation：`CONDITIONAL`，只允许另行授权的disposable experiment；
- Seedance MCP Production Runtime：`DO NOT RECOMMEND`；
- selected option：MCP只用于Agent/实验控制面，Production Runtime继续direct/sealed adapters。

## Current Runtime Ownership Truth

当前HEAD中的Production ownership保持：

- `VideoGenerationService`拥有provider-neutral generation lifecycle orchestration；
- `ProductionStateCommitter`是唯一durable lifecycle、activation与recovery writer；
- `ComfyUIVideoProvider`及Local H3/T8/Turbo/native-Turbo child adapters拥有deterministic workflow、profile
  preflight与native ComfyUI mapping；
- `LocalVideoTransport`只抽象server/node discovery、asset upload、prompt submit、status poll与artifact fetch五类
  I/O primitive；
- Seedance Production使用direct Ark adapter，保留exact model/profile、pricing、Cloud Egress、Paid Provider
  Gate、materialization、native task ID、status/fetch、response model、one-use permit、unknown-outcome、activation
  与replay；
- candidate、activation、provenance、explicit recovery、exact replay、P6与Final Acceptance均不属于MCP。

MCP不得成为second Manifest、Registry、lifecycle、recovery、retry、Provider router或quality owner。

## Comfy MCP Audit Result

审计snapshot固定为Comfy MCP commit：

```text
b3766a0baa456deda5944b9e3f549228eecf7985
```

该snapshot支持Agent-friendly server/node/model/workflow discovery、workflow submit、prompt ID、status与output
fetch，但存在以下Production blockers：

- MCP server实际委托`comfy-cli`调用ComfyUI，不是AI-VIDEO transaction owner；
- model discovery主要提供filename/inventory，不提供AI-VIDEO要求的bytes/SHA/license seal；
- workflow run不回显AI-VIDEO-owned exact request/workflow seal；
- error surface经过normalized/compact处理，不等同于完整raw ComfyUI response；
- 存在tool-side credential retry policy，不能满足strict zero-secondary-retry；
- 没有caller-supplied durable effect token、idempotency key或按该token查回唯一prompt ID的contract；
- request已发送但prompt ID response丢失时无法canonical reconcile，可能留下orphan Comfy job；
- comfy-cli prompt/output/recent-run state不能成为Production lifecycle truth。

因此Comfy MCP当前是Agent-friendly wrapper，不是可直接替换AI-VIDEO Production submit/status/fetch contract的
transport。

即使未来在`LocalVideoTransport`后接入MCP，AI-VIDEO仍必须保留workflow/profile/compiler/model seals、input
reopen、permit、status/fetch receipts、output probe/SHA、provenance、candidate、activation、recovery与replay。
静态估算是Production Local Comfy responsibility complexity只减少约`5-8%`，扣除MCP bridge/version/error/
state handling后tracked-code净减少约`0-3%`；Agent临时HTTP/Python与手工找output的实验成本才是主要收益。

## Seedance Audit Result

当前可验证路线必须区分：

1. direct Ark API：保留native model/request/task ID/status/output/error/usage surface，继续是Production选择；
2. third-party Seedance MCP：审计reference commit
   `0e54bb1c28e90a7c30520922a4c1adae14630c3b`使用broker API，不是AI-VIDEO direct Ark identity；
3. Comfy MCP -> ComfyUI Partner node：使用Comfy account/credits，外层主要是Comfy prompt identity，会改变
   credential、billing、Provider与materialization path；
4. provider-native MCP：本次未找到可验证的成熟官方Seedance Production MCP；不得把“未找到”扩写成永久
   不存在。

任何MCP若隐藏或降级native task ID、exact model/profile、billing、materialization、raw error、one-use submit或
unknown-outcome semantics，只适合experiment control plane，不适合Production executor。

## Replay And Recovery Boundary

Production exact replay必须在调用任何MCP/Provider之前由AI-VIDEO canonical state short-circuit：

```text
same desired exact replay
    -> zero MCP invocation
    -> zero ComfyUI submit
    -> zero fetch/activation effect
```

Agent直接调用MCP不能提供该保证。

若MCP request已发送但response/prompt ID丢失，当前Comfy MCP没有caller effect token lookup，不能证明submit
是否发生，也不能找回唯一canonical job。正确行为只能是保留unknown outcome并停止，不能blind retry。

当前direct Comfy/Ark adapters在“Provider已接受但native ID response丢失”的窗口也采用fail closed/no
resubmit，并非完整自动reconciliation。MCP没有修复这个已知限制，反而会增加一层timeout、retry和secondary
state。

## Recommended Development Workflow

后续获得implementation authorization后，最小adoption顺序是：

1. host-local isolated、pinned Comfy MCP；Product Runtime dependency保持不变；
2. Codex只做single loopback server/node/model/workflow metadata discovery；
3. 在新的明确授权下运行一次`development_experiment`，exactly one submit、no automatic retry、output留在
   temporary/non-Production location；
4. 只记录prompt ID、status、workflow/tool/server identity、output bytes/SHA与known unknown-outcome boundary；
5. 不写`runs/**`、Project、Registry、Manifest、candidate、P6或Final Acceptance；
6. 默认在Agent-only阶段结束。只有caller effect token、crash reconciliation、raw error、strict zero retry等
   spec gates全部满足，才另写MCP-backed Product executor spec。

MCP不得修改sealed Production workflow/profile/binding。Agent可以在temporary experimental directory修改
experimental workflow，但一次成功run不能把它提升为Production artifact。

## Verification And Evidence

Spec/plan commit range：

```text
c8eeb5110e475c762def1532128331734342f326
..
59016d8ed8ed59dd4a0bb70b43f641f673822ba1
```

Harness route只包含：

```text
category: documentation
checks: scope_diff_check, docs_contract_check
fallback_paths: []
sensitive_paths: []
```

Fresh commit-range receipt：

```text
.agent/harness/runs/20260823-mcp-control-execution-plane-commit/receipt.json
```

Execution timing follow-up的fresh commit-range receipt：

```text
.agent/harness/runs/20260823-mcp-plan-start-completion-gates-commit/receipt.json
```

Receipt verification结果：`passed=true`、`fresh=true`、`integrity=true`、`artifact_integrity=true`、
`policy_matches=true`、`snapshot_matches=true`、`scope_worktree_clean=true`、
`workspace_cleanup_confirmed=true`。

`scope_worktree_clean=true`只证明Harness detached execution tree，不代表共享checkout没有unrelated dirty work。

## MiniMax Investigation Evidence

Local Comfy/T8 mapping使用一次external read-only explorer：

```text
Role: explorer
Scope: Local Comfy/T8 production lane
Model: MiniMax-M3
Transport: external CLI
Status: DONE_WITH_CONCERNS
Exit: 0
External session: 7c56f4c7-9ce7-4a87-a99e-5e4cecf4c597
```

其核心finding是只有`LocalVideoTransport`五项底层I/O primitive可被MCP替换，Production seals、permit、
provenance、lifecycle、replay、recovery与activation均不能删除。其关于其它`ComfyClient` consumers的concern已由
主线程全仓search复核。

Sanitized diagnostic：

```text
/home/reggie/.codex/session-diagnostics/minimax/
01a02ed6-36fe-7923-bc1e-4f1aa6bc6d3d-d993211f222de29e.md
```

该capture只证明subagent invocation/activity与sanitized terminal status，不单独证明architecture correctness。

## Workspace Safety Note

架构审计开始时`index.json`已是unrelated dirty file。按repository structural-discovery规则调用codegraph
indexing时，该工具意外重写了该文件；没有调用前backup，不能在不覆盖未知用户内容的情况下安全恢复，因此
没有revert、stage或commit。后续工作保留该dirty/index state。

创建spec/plan与本record期间还存在其它unrelated dirty/untracked work；task commit只包含明确的task-owned
documentation paths。不得把这些现有changes归入本窗口，也不得reset、clean、overwrite、stage或commit。

## Unverified Boundaries

本窗口没有：

- 安装或启动Comfy MCP；
- 启动ComfyUI或submit workflow；
- 调用Local/remote Provider或Seedance；
- 读取credential、产生cloud egress或付费行为；
- 生成、fetch或分析新媒体；
- 验证真实MCP handshake、live node/model discovery、prompt ID或output fetch；
- 证明MCP-backed Production transport、creative quality、P6或Final Acceptance。

这些状态不得从spec、plan、external source audit、Harness receipt或subagent status推断。

## Agent Guardrails

后续Agent必须保持：

- `Codex -> MCP -> ComfyUI`属于Development / Experiment Control Plane；
- `AI-VIDEO Runtime -> MCP`不是由前者自动推出的结论；
- Production attempt必须经过`VideoGenerationService`、canonical intent/permit与selected sealed adapter；
- MCP output默认是`development_experiment`，不能直接注册、activation或P6 accept；
- Comfy MCP version变化后必须重新审计source、retry、error、state、license与effect-identity contract；
- Seedance Production继续direct Ark API；不得因third-party/Partner MCP减少adapter代码就替换paid lane；
- technical PASS、MCP success、hash或Harness PASS均不等于creative/human/Final Acceptance；
- implementation必须由新的明确授权开始，spec/plan本身不授权installation、live、Provider、paid、push或release。
