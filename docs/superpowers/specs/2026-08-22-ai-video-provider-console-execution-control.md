# AI-VIDEO Provider Console Execution Control Specification

## Status

Proposed for acceptance。本文定义 Provider Console 从只读 observer 进入本机 operator execution control
的下一条 runtime slice；在本 Spec 被用户接受前，不授权实现、live Provider submit、付费调用或
Manifest mutation。

现有只读契约继续由
`docs/superpowers/specs/2026-08-22-ai-video-provider-console-runs-integration.md` 管理。本文只增加显式
execution path，不把原有 `GET/HEAD` projection 改造成隐式 writer。

## Goal

让操作员从真实 Shot 出发，查看每条已配置 Provider lane 的 exact readiness，手动选择且仅选择一条
lane，并通过可审计的单步操作完成：

`start -> preflight -> submit -> poll -> settle -> fetch -> validate -> activate`

异常结果只能进入显式 `recover`。任何步骤都不得自动选择 Provider、自动 fallback、自动 retry、自动
poll、自动激活 candidate 或把生成成功冒充最终交付。

终极产品方向不是“为 Seedance 做一个按钮”，而是建立 provider-neutral 的 operator control surface：
Seedance 2.0 Mini 是第一条 live-submit-capable remote lane；Local H3、Hailuo 与后续 Provider 通过同一 lane、
readiness、lifecycle 和 evidence contract 接入。

## Problem Boundary

当前 Provider Console 已能只读显示 `runs/` 的真实 Project、Shot、attempt、输入、prompt、输出和 evidence，
但没有 production execution assembly：

- Browser 没有经过授权的 mutation gateway；现有 `runs-api.mjs` 必须保持只读。
- `VideoGenerationService` 与 `ProductionStateCommitter` 已提供大部分 one-action lifecycle primitive，
  但尚无 operator-facing production assembly。
- `fetch_and_activate()` 把多个 lifecycle 阶段连在一个调用中，不适合显式 UI；validate 与 activate 必须
  分离。
- candidate preparer 当前只有 test factory，production path 没有可复用 assembly。
- Seedance adapter 依赖 profile、transport、credential supplier 与 input resolver，但缺少稳定、allowlisted
  runtime factory。
- 对一个尚无 attempt 的 Shot，Console 还不能用 exact capability selection 建立 durable attempt。

本 slice 的 single mutation orchestration owner 是新的 local operator gateway。它只编排现有 canonical owners，不拥有
第二份 Manifest lifecycle、Provider state 或 activation truth。

## Scope

### In Scope

1. 对真实 Project/Shot 生成 configured lane projection，并逐条执行现有 Planner、Readiness、Router 与 adapter
   compiler 的 exact validation。
2. 操作员手动选择一个 exact `provider + model + profile + capability_id`；无 fallback。
3. 为 ready lane 创建一个 durable video generation attempt，并绑定 exact request、inputs、prompt、source
   content hash 与 selected capability。
4. 对新 attempt 或既有 attempt 执行严格的一次一动作：preflight、submit、poll、settle、fetch、validate、
   activate、recover。
5. Seedance 2.0 Mini 的 production runtime assembly、Secret Service lookup 和 paid execution gates。
6. production candidate preparation，以及 continuity-bound candidate 的既有 review coordinator routing。
7. loopback-only、default-off、explicitly armed 的 local mutation API 与中文 operator UI。
8. fake Provider 的完整 offline E2E、crash/replay/recovery tests，以及 gated live Seedance smoke。

### Out Of Scope

- automatic Provider ranking、selection、fallback、retry、polling 或 recovery；
- queue、scheduler、daemon、multi-user auth、remote control plane 或 Sites execution；
- 新 Manifest/schema/layout migration；
- 修改 `ProductionStateCommitter`、Registry、Dependency Graph、ResolvedTimeline 或 HyperFrames 的 canonical
  ownership；
- 用 MiniMax Speech credential 调用 Hailuo/H3，或建立任意 credential fallback；
- 自动 QA acceptance、自动 candidate activation、自动 delivery；
- Provider benchmark、质量优劣结论或生产发布声明。

## Canonical Ownership And Dependency Direction

| Concern | Owner | Console responsibility |
| --- | --- | --- |
| Project/Shot/request truth | `ProductionProject` | strict reopen and select |
| Exact capability selection | Planner + Readiness + Router | request one configured lane; never rank/fallback |
| Provider execution | selected `VideoProvider` adapter | call exactly one current action |
| Durable attempt/intent/status/evidence | `ProductionStateCommitter` | invoke owner with expected revision |
| Paid cost settlement | trusted provider cost resolver + `ProductionStateCommitter` | resolve exact cost, then request explicit settlement |
| Candidate preparation | production `VideoCandidatePreparer` | request explicit validation |
| Continuity review | split `ContinuityReviewCoordinator` validate-only seam | route exact-bound decision; never bypass or activate |
| Candidate activation/recovery | `ProductionStateCommitter` | explicit user action only |
| UI read projection | `ai_video.provider_console` | remain read-only |
| UI mutation orchestration | new `ai_video.provider_console_execution` | validate policy and compose canonical owners |

Dependency direction必须是：

`Browser -> loopback execution bridge -> Python operator gateway -> existing production owners`

Node/Browser 不得直接读取 secret、构造 Provider payload、编辑 Manifest、解释 remote response 或拥有 lifecycle。

## Lane Discovery And Start Contract

### Configured Lane Catalog

lane catalog 是 server-side allowlist，不是自动 Provider registry。每个 lane 必须绑定：

- stable lane ID；
- provider kind、model、profile、execution kind 与 billing kind；
- exact capability ID 或可被 Router 精确解析的 capability selector；
- runtime factory ID；
- budget policy ID、cloud-egress policy ID 与 stable credential reference（如需要）；
- enabled/disabled 状态和 operator-visible reason。

catalog 不保存 raw credential，不允许 Browser 提交 arbitrary module/class/URL/model/profile。未知 lane fail closed。

### Per-Shot Readiness

Console 必须对每条 configured lane 独立运行当前 `video-planner/3` generation requirement、Readiness、Router
与 adapter compiler；不得把一个 lane 的结果推断给另一个 lane。readiness 至少返回：

- exact Shot、request content hash、mode（`T2V / I2V / R2V / FL2V`）与 required bindings；
- selected capability/profile、fixed/adaptive limits 与 execution boundary；
- local asset/runtime、cloud egress、budget、credential reference availability 等 gate 状态；
- `ready`、`blocked` 或 `gated`，以及稳定、sanitized reason codes。

T2V 必须显示 sealed prompt；I2V/R2V 必须显示 prompt 与所有 required image/reference bindings；FL2V 必须
显示 prompt、first frame 与 last frame。缺失 required binding 时 lane 不可 start。

### Manual Start

操作员只能对一条 `ready` lane 点击 start。request 必须绑定 exact Project/Manifest revision、Shot、lane、
request content hash、capability、inputs 与 preview fingerprint。server 重新 strict reopen 并 recompute；任何 stale
或 mismatch 返回 conflict，不创建 attempt。

start 只调用 canonical `begin_video_generation` 建立 durable attempt，不 submit Provider。一个新 attempt 的
创建不能隐式执行 preflight 或付费调用。

## One-Action Execution Contract

每个 HTTP mutation 与 Python invocation最多推进一个 lifecycle action。gateway 必须先读取 canonical
`video_resume_next_action()`，再与 paid-provider phase 和 exact-cost resolver availability组合成唯一 operator next
action；Browser 不得自行猜测。`preflight` 是 submit 前必须由操作员单独触发的 read-only preview，不推进
Manifest；`recover` 是 `video_resume_next_action() == "stop"` 时另行确认的 workspace-scoped canonical recovery，
不是普通 attempt next action。

| Durable state / phase | Allowed action | Required result |
| --- | --- | --- |
| no attempt + ready lane | `start` | durable request/attempt only |
| `REQUEST` | `preflight` (read-only), then `submit` | current preview/hash, then durable paid intent and one Provider POST |
| `SUBMIT_INTENT` / `OUTCOME_UNKNOWN` | `stop`; optional explicit workspace `recover` | seal/reconcile only what canonical recovery supports; never repeat submit |
| `SUBMITTED` / `POLLING` + video next=`poll` | `poll` | one Provider status read |
| video next=`fetch` + remote paid state not `SETTLED` + exact cost available | `settle` | one canonical budget settlement; no Provider generation call |
| video next=`fetch` + remote paid state not `SETTLED` + no exact cost | `settlement-gated` | no mutation; explain missing trusted cost source |
| video next=`fetch` + local lane or remote paid state=`SETTLED` | `fetch` | one fetch plus registered immutable result evidence |
| validation-ready | `validate` | candidate/evidence prepared; no activation |
| `CANDIDATE` | `activate` | atomic canonical activation only |
| interrupted/failed recoverable state | `recover-workspace` | explicit workspace-scoped canonical recovery action |
| activated/succeeded/done | none | read-only replay response |

`fetch_and_activate()` 不得被 Console 调用。Service 必须提供或由 bounded façade 组合独立的
`validate_once()` 和 `activate_once()`；每个方法仍把 mutation 委托给 canonical committer。

remote composite precedence 固定为：持续 `poll`，直到 canonical video next action 成为 `fetch`；此时如果 paid
state 尚未 `SETTLED`，只暴露 `settle` 或只读 `settlement-gated`，不得提前暴露 `fetch`。只有 settlement 完成后
才暴露 `fetch`。Local lane 完全跳过 settlement。gateway 不修改 `video_resume_next_action()` 的 canonical video
phase semantics，只负责安全地组合两个既有 durable state surfaces。

每个 attempt action request 必须包含：workspace key、attempt/Shot ID、expected Manifest revision、expected next
action、preview/action-context hash 与 diagnostic client action ID。workspace recovery 则绑定 workspace key、
expected Manifest revision、recovery preview hash 与 diagnostic client action ID；它必须明确展示可能影响的全部
interrupted attempts/artifacts。server 必须重新计算；revision/action/hash 不一致返回 `409`，不得调用 Provider。

client action ID 只用于本次 local session 的日志关联和 duplicate-click suppression，不是 durable idempotency owner，
也不进入 Manifest/schema。跨 process restart 的 replay safety 只能来自 canonical revision、phase、intent、permit、
receipt、external effect identity 与 content fingerprints。

## Paid Execution And Credential Contract

### Explicit Arming

execution server 默认关闭。只有 local operator 以明确 configuration 启动 execution bridge 时，mutation routes
才存在；普通 Vite observer 与 Sites/static deployment 始终只读。

server-side policy 文件必须是 local、regular、no-follow、owner-only readable，且只包含：actor identity、允许的
lane、单次/项目 budget ceiling、egress policy ID 和 stable credential reference。Browser 不能创建受信任的
`PaidProviderAuthorizationDecision`。

### Trusted Authorization

`submit` 前，Python gateway 必须用当前 exact preview 和 server policy 构造 trusted task-scoped authorization，
并依序执行现有 Paid Provider Gate、Budget Guard、Cloud Egress、durable intent、one-use permit 与 submit receipt。
budget settlement 是 submit 后的独立显式 action，不能在尚无 exact actual cost 时伪造。用户点击只表达对当前
preview/action 的确认，不能扩大 allowlist 或预算。

### Cost Settlement

remote candidate validation 已要求 exact settled budget evidence，因此 Console 必须有独立 `settle` action：

- actual cost 只能来自 server-side allowlisted provider cost resolver，绑定 exact attempt、external effect、request、
  currency 与 current pricing/billing evidence；Browser 不得提交 arbitrary amount。
- resolver 返回 exact `actual_cost_microunits` 后，gateway 才调用现有
  `settle_paid_provider_reservation()`；settle 不重放 generation/fetch。
- fake Provider 必须提供 deterministic exact cost，用于完整 offline E2E。
- 若 Seedance 当前 API/profile 没有可验证的 exact cost source，live attempt 必须停在 `settlement gated`，不得把
  pricing upper bound 冒充 actual cost，也不得继续 validate/activate。
- 增加 provider cost resolver 不改变 budget snapshot/schema；若未来需要新的 durable billing receipt/layout，
  必须另行批准 migration。

### Secret Handling

Seedance 唯一稳定 credential reference 是 `ARK_API_KEY`。lookup 仅发生在 Python Provider submit 进程，使用
Secret Service exact attributes：

- `application ai-video`
- `provider seedance`
- `credential ARK_API_KEY`

raw key 不得进入 repository、policy file、Browser、Node、command argument、environment、prompt、fixture、log、
error、receipt 或 repr。MiniMax Speech 的 `MINIMAX_SPEECH_API_KEY` 与本 slice 无关，不得作为 Hailuo/H3
credential。

## Local Mutation API And Security Contract

mutation bridge 使用独立 sibling module，例如 `provider-console/scripts/execution-api.mjs`，不得把 write branch
塞进 `runs-api.mjs` 的 read projector。

最低安全边界：

- 仅监听 loopback；Sites/static build 不包含 execution capability；
- mutation route 仅接受 JSON `POST`，有 body size cap、exact content type 与 schema validation；
- 校验 local Origin、session nonce/CSRF token 与 explicit execution-mode handshake；
- workspace/lane/action 使用 allowlist identity，不接受 arbitrary filesystem path、URL、command 或 Provider payload；
- response 只返回 sanitized state、next action、evidence pointers 与 stable error code；
- `Cache-Control: no-store`，不回显 raw Provider response、credential、signed URL、absolute path 或 traceback；
- Python gateway 使用 JSON stdin/stdout；secret 不通过 Node，也不通过 process arguments/environment；
- mutation 同步执行一个 bounded action；不启动 background poller、queue 或 hidden retry。

现有 `GET /api/runs*` 与 media endpoints 的 read-only/no-network contract 不变。

## Replay, Unknown Outcome And Recovery

- 同一进程内相同 client action ID 可抑制 duplicate click；跨重启 replay 只按 reopened canonical state处理。
- stale expected revision/action/hash 返回 conflict；Browser 必须 refresh，不自动 retry。
- Provider POST 发出但 receipt 未稳定落盘时进入既有 unknown-outcome contract；禁止再次 submit 或 remint permit。
- recovery 必须由操作员在查看 workspace-scoped recovery preview 后显式点击，并调用 canonical
  `ProductionStateCommitter.recover()`；完整 orphan evidence 保留。它不得伪装为仅影响当前 attempt。
- recovery 不能猜测 remote outcome、自动激活 candidate 或删除 evidence。
- process crash、Browser refresh、Node restart 后 next action 必须完全由 reopened durable state 推导。

## Candidate Validation, Continuity And Activation

production candidate preparer 必须复用 current artifact/Registry/measurement/provenance contract，不复制 test-only
state writer。validation 只生成 candidate/evidence，不改变 active pointer。

如果 attempt 绑定 continuity terminal/reference contract，`validate` 必须路由到新增的
`ContinuityReviewCoordinator.validate_once()`（名称可按现有 style收敛）及其 human fallback，并只生成
candidate；不得调用 current `validate_and_activate()` 或 `fetch_and_activate()`。旧组合 API 为既有 caller保留
compatibility，但 Console 禁止使用。identity、axis、framing 等没有可信 evaluator 时保持 `NOT_EVALUATED`，
不得把 CUDA/model smoke 当 Final Acceptance。非 continuity attempt 才走普通 candidate preparer。

Browser 提交 human decision 时只能发送 bounded `HumanReviewDecisionV1` JSON，不发送 local path。Node/Python
必须执行 body cap、strict schema/content hash、required reviewer identity、complete axes 与 current snapshot stale
check；gateway 把 validated model传给 validate-only coordinator seam，不创建任意 path或接受任意 filesystem
reference。现有 `decision_path` API 可作为 compatibility wrapper继续 strict read，再委托现有组合 behavior；它不
作为 Console input seam。

`activate` 是单独按钮，只有 canonical state 已是 valid candidate 且 current evidence/revision仍匹配时才调用
`ProductionStateCommitter`。Provider success、fetch success、media playable 或 validation success 均不等于激活。

## Provider Rollout Contract

1. **Fake provider:** 先完成 offline lifecycle、replay、crash、unknown-outcome 和 UI E2E。
2. **Seedance 2.0 Mini:** 第一条 live-submit-capable remote lane；必须通过本 Spec 全部 pre-submit gates，live
   smoke 最多一次 submit。只有 exact cost resolver也可用时才能继续 settle/validate/activate；结果只证明该
   exact request 已实际完成的阶段与 evidence。
3. **Local H3:** 仅在 exact local runtime/profile/assets 的现有 readiness 与 sealed gate 均通过时启用；不以 fake
   fixture 声称 live-ready。
4. **Hailuo / cloud H3 / later providers:** 可以作为 disabled/gated lane 显示；只有建立各自稳定 credential、
   runtime factory、capability、budget/egress policy 与 tests 后才能启用。

所有 Provider 共用同一 lifecycle contract；不得为 Seedance 创建绕过 Planner、Readiness、Router、committer、
QA 或 recovery 的快捷路径。

## Compatibility And Migration

- 不改变 Legacy CLI、Production Manifest/schema/artifact layout、existing request receipt 或 Provider protocol。
- existing attempts 可在 strict reopen 后进入 execution gateway；缺失新 action hash 的旧 attempt只能先生成
  read-only preview，不能被 Browser 直接 submit。
- 现有 Provider Console observer 默认行为、read endpoints、static/Sites deployment 和真实 runs projection 保持
  兼容。
- execution config 是本机 operator input，不进入 repository 或 `runs/` canonical state。

## Acceptance Criteria

1. 未启用 execution mode 时，所有 mutation routes 不存在或 fail closed；observer/Sites仍严格只读。
2. UI 对真实 Shot 显示 configured lanes 及 exact readiness；T2V/I2V/R2V/FL2V inputs 与 prompt 正确。
3. 只能手动选择一条 ready lane；start 只创建 durable attempt，不 submit。
4. 每次 click 最多推进一个 canonical action；无 auto fallback/retry/poll/fetch/validate/activate/recover。
5. stale revision/action/hash、非法 Origin/nonce、unknown lane/path/payload 均在 Provider call 前 fail closed。
6. Paid submit 依序留下 preview、authorization、budget、egress、intent、one-use permit 与 submit receipt；
   settlement 是 exact cost resolver驱动的独立 action，unknown outcome不重复 POST。
7. validate 与 activate 可独立测试；continuity-bound attempt 使用 exact-bound decision JSON 和 validate-only
   coordinator seam，不绕过 review coordinator/human fallback。
8. raw secret 与 raw Provider response 不进入 Browser、Node、args/env、logs、errors、receipts 或 committed files。
9. fake Provider offline E2E 覆盖 exact cost settlement、success、failure、crash、replay、stale action 与 recovery。
10. focused Python/Node/frontend tests、Chrome integrated QA、independent review 和 exact Harness receipt 通过。
11. gated live Seedance 2.0 Mini smoke 只有在用户接受本 Spec、pre-live exact Harness closure 完成且本轮授权仍
    有效时才执行；若 exact cost source不可用，明确停在 settlement gate。报告包含 exact commit、attempt/evidence
    paths、已完成阶段与未证明的质量边界。

## Rollback

关闭 execution mode 或移除 execution bridge 即恢复 observer-only。代码 rollback 不删除 `runs/`、Manifest、
intent、receipt、candidate 或 evidence；已产生的 unknown outcome 必须继续通过 canonical recovery 处理，不能用
Git rollback 掩盖。

## Acceptance Gate

用户接受本文后，配套 implementation plan 才可执行。接受本文并不自动授权新的 Provider、超出配置预算、
自动 activation、production release 或后续 benchmark；live submit 仍须满足本 task 的 paid gate 与所有
runtime preconditions。
