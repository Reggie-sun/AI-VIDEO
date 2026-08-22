# AI-VIDEO Provider Console Execution Control Implementation Plan

## Status

Executable。governing spec 已由用户接受，本文可以按 sequence 执行。

当前 continuation target 仅执行 T0/T1 offline core seam；不得提前进入 T2+、调用 live Provider、读取 raw
secret、修改 `runs/**` 或进入 T6 frontend。后续阶段继续受 governing spec 的 technical gates、Decision Gates
与 task-scoped authorization 约束。本计划覆盖 provider-neutral execution control，不把 Seedance live proof当成
终点；live call 位于所有 offline contracts、review 与 Harness closure 之后。

## Contract Checkpoint Before Code

- **Problem boundary:** 现有 Console 只能观察真实 `runs/`，不能安全建立或推进 generation attempt。
- **Single execution owner:** new `ai_video.provider_console_execution` local operator gateway。
- **Canonical state owner:** `ProductionStateCommitter`；Console、Node 和 Provider adapter 不拥有第二份 lifecycle。
- **Old path to reject:** UI 直接调用 `fetch_and_activate()`、Browser 自造 paid authorization、Node 读取 secret、
  自动 Provider fallback/retry/poll/activation。
- **Unchanged contracts:** Legacy CLI、Manifest/schema/layout、Registry、Dependency Graph、ResolvedTimeline、
  HyperFrames、read-only `runs-api.mjs` 与 Sites observer。
- **Focused verification seam:** fake Provider + deterministic exact-cost resolver + temporary Production workspace +
  exact one-action state assertions。

在 implementation 写入前，必须重新检查 `git status`、live agents 与下列 target files。当前
`src/ai_video/production/video_generation.py` 若仍存在其他 writer 的 same-file uncommitted change，必须先停下让
用户决定 ownership/order；不得覆盖或串改。

## Planned Change Surface

精确 filenames 可在 T0 architecture checkpoint 中按现有 module size/style收敛，但责任边界不得合并。

### New Owners

- `src/ai_video/provider_console_execution.py`：strict local operator gateway / CLI。
- `src/ai_video/production/video_candidate.py`：production candidate preparer assembly。
- `src/ai_video/production/video_provider_runtime.py`：allowlisted provider runtime factories，或等价的 cohesive
  production module。
- `tests/test_provider_console_execution.py`
- `tests/test_video_candidate.py`
- `tests/test_video_provider_runtime.py`
- `provider-console/scripts/execution-api.mjs`
- `provider-console/tests/execution-api.test.mjs`

### Expected Modifications

- `src/ai_video/production/video_generation.py`：增加显式 `validate_once()` / `activate_once()`，不改变现有 public
  lifecycle semantics。
- `src/ai_video/production/continuity_review_coordinator.py`：增加接受 exact-bound
  `HumanReviewDecisionV1` model 的 validate-only seam；保留 existing path/combined API compatibility。
- minimum existing production wiring/tests required to reuse canonical Paid Provider、Seedance、continuity and
  recovery owners。
- `provider-console/vite.config.mjs`：只有 explicit local execution mode 才挂载 mutation bridge。
- `provider-console/src/App.jsx`、`provider-console/src/styles.css`：configured lane readiness 与 single-action
  operator controls。
- `provider-console/AGENTS.md`：必须把现有 absolute read-only constitution收敛为“default observer-only；仅 explicit
  local execution mode 可使用 sibling mutation owner”，并保留 Sites/static绝对只读。
- canonical runtime docs、Harness policy：仅在 public/runtime routing 确实变化且 target-file ownership无冲突时同步。

### Must Not Modify

`runs/**` existing artifacts、Legacy pipeline/CLI、Manifest schema/layout、canonical renderer/timeline owner、
`.workflow/**`、secret storage、其它 Agent 拥有的 files。

## Implementation Sequence

### T0 — Acceptance, Ownership And RED Baseline

用户接受 governing spec 后才进入代码。重新读取 current runtime baseline、contract matrix、Harness routing，
检查 live writers 与 exact file overlap。记录：problem boundary、single owners、被拒绝的旧 shortcut、unchanged
contracts、focused commands。用 fake Provider 写出 one-action、stale revision、unknown outcome、exact-cost
settlement、continuity validate-only 和 validate/activate separation 的 failing tests。

### T1 — Core One-Action Lifecycle Seams

先把 test-only candidate preparation收敛为 production owner，并为 `VideoGenerationService` 增加独立的
`validate_once()` 与 `activate_once()`。为 `ContinuityReviewCoordinator` 增加 validate-only method：接收已经
strict validated 的 `HumanReviewDecisionV1` model，执行 current snapshot/reviewer/axes stale checks并只调用
service `validate_once()`。不得删除现有 `fetch_and_activate()` 或 `validate_and_activate()` public compatibility，
但 Console 不得调用它们。

Focused verification：

```bash
python -m pytest -p no:cacheprovider tests/test_video_candidate.py tests/test_video_generation.py tests/test_production_continuity_review_coordinator.py -q
```

### T2 — Allowlisted Provider Runtime Assembly

实现 provider-neutral factory contract、fake Provider和 allowlisted cost resolver protocol。fake resolver 返回绑定
exact attempt/request/external effect/currency 的 deterministic actual cost。Seedance 2.0 Mini factory 只注入 stable
profile、transport、input resolver、clock 和 Secret Service credential supplier；secret lookup 延迟到 Python
submit。Seedance 未有可信 exact cost source时返回 settlement-gated，不得用 pricing upper bound代替 actual cost。
Local H3/Hailuo 尚未满足 runtime/credential contract时只返回 typed gated state。

Focused verification：

```bash
python -m pytest -p no:cacheprovider tests/test_video_provider_runtime.py tests/test_seedance.py -q
```

### T3 — Lane Projection And Attempt Start

为每个真实 Shot × configured lane 独立运行 Planner v3、Readiness、Router 与 adapter compiler，投影 exact
mode/inputs/prompt/capability/gates。start 必须重新 strict reopen、验证 expected revision与preview fingerprint，
并只调用 `begin_video_generation`。

Tests覆盖 T2V、I2V、R2V、FL2V、missing bindings、stale preview、disabled lane、manual selection、no fallback
与“start 不 submit”。

### T4 — Python Operator Gateway

实现 JSON stdin/stdout gateway：`lanes`、`start`、`preflight`、`submit`、`poll`、`settle`、`fetch`、`validate`、
`activate`、`recovery-preview`、`recover-workspace`。每个 invocation strict reopen一次 current state，验证
expected next action/hash/revision，最多调用一个 lifecycle action并返回 sanitized projection。`preflight`只生成
read-only submit preview；`recover-workspace` 必须绑定并展示整个 workspace 的 recovery scope，不能冒充
attempt-local mutation。

operator next-action projector 必须组合 canonical video phase与paid phase：`poll` 优先直到 video next=`fetch`；
remote 未 `SETTLED` 时只返回 `settle` 或 `settlement-gated`，并拒绝 `fetch`；settled remote或local lane才返回
`fetch`。tests覆盖 simultaneous paid/video states、unsettled remote fetch rejection、settlement unavailable、settled
fetch与local no-settlement。

Paid submit 在 server-side trusted authorizer 中绑定 exact preview、actor、budget/egress policy、durable intent
与 one-use permit。`settle` 只消费 allowlisted resolver 的 exact cost并调用 current committer；Browser不能提供
amount。client action ID仅做同进程 duplicate-click suppression，跨重启 replay/crash/unknown outcome/recovery
只沿用 canonical revision/phase/intent/permit/receipt contract。

continuity `validate` body 只接受 bounded `HumanReviewDecisionV1` JSON，验证 exact
`review_request_content_hash`、reviewer identity、complete axes 与 current snapshot；不得接受 decision path。
validated model交给 T1 validate-only seam。

Focused verification：

```bash
python -m pytest -p no:cacheprovider tests/test_provider_console_execution.py -q
```

### T5 — Secure Loopback Mutation Bridge

新增 sibling `execution-api.mjs`；observer-only 默认下不加载。测试 loopback/Origin/nonce、JSON/body cap、405、
arbitrary path/lane/action rejection、subprocess protocol、no-store、secret/raw response sanitization、single inflight
action与 Sites absence。额外覆盖 human decision strict JSON intake、stale hash/reviewer/axes rejection，以及 Browser
不能提交 settlement amount。Node 不接收 key，也不构造 Provider payload。

Focused verification：

```bash
node --test provider-console/tests/execution-api.test.mjs provider-console/tests/runs-api.test.mjs
npm --prefix provider-console run test:sites
```

### T6 — Product Design UI And Browser QA

使用 `product-design` plugin 的 `product-design:audit` / `product-design:image-to-code` guidance，把现有中文视觉
外壳扩展为真实 lane readiness 与 single-action control；不重做产品风格。UI 必须明确区分：blocked/gated、
preflight、paid submit confirmation、poll、settle、settlement-gated、fetch、validate、human review、activate、
recover、done。

Chrome integrated QA覆盖：observer mode、execution armed、四种 input mode、stale conflict、unknown outcome、
settle/settlement-gated precedence、keyboard/focus、responsive layout、console/page/network errors。live Provider网络
不得用于普通 UI QA。

Focused verification：

```bash
npm --prefix provider-console run build
```

### T7 — Offline End-To-End And Independent Review

在 temporary Production workspace 上用 fake Provider + exact-cost resolver走完整 success path；逐个注入 submit
crash、lost response、settlement unavailable/mismatch、poll failure、fetch failure、invalid candidate、continuity
decision stale/`NOT_EVALUATED`、stale activation 与 explicit recovery。
验证 process/browser restart 后 next action只来自 reopened durable state，且外部调用次数精确。

由 native `reviewer` 独立检查 paid gates、secret boundary、lifecycle owner、continuity routing、replay、tests与
final diff；parent复核所有 blocking claim。

### T8 — Pre-Live Exact Closure And Gated Seedance 2.0 Mini Smoke

先只 stage offline implementation-owned files，运行 exact staged Harness，commit checkpoint，再对 exact commit
range完成 detached verification并验证 fresh receipt。只有该 pre-live closure passing，且 governing spec accepted、
execution config有效、task-scoped authorization仍成立、Secret Service exact lookup成功、budget/egress/intent/
permit gates通过、用户明确选定 exact ready lane，才执行一次 live submit。

按单步 UI/API顺序执行 preflight -> submit -> poll -> settle -> fetch -> validate；activation 仍需单独显式动作。
如果 Seedance exact cost resolver不可用，停止在 settlement gate，不把 upper bound冒充 actual cost，也不继续
validate/activate。记录 exact commit、workspace/attempt、sanitized receipts、artifact hash与未验证质量边界。任何
unknown outcome立即停止并进入 recovery，不再次 POST。

### T9 — Post-Live Evidence Closure

如果 live smoke 产生 task-owned canonical docs/records updates，只 stage这些文件并再次运行 exact staged +
commit-range Harness；live `runs/` artifacts继续作为 runtime evidence，不纳入代码 commit。报告 offline implementation
commit、pre-live receipt、post-live docs commit/receipt（如有）、live smoke实际停止阶段、未 push/deploy与 remaining
provider lanes。

## Verification Matrix

| Risk | Executable evidence |
| --- | --- |
| Observer accidentally mutates | existing GET/HEAD tests + execution-disabled route tests |
| Start submits Provider | fake Provider call count remains zero after start |
| Double submit / lost response | durable intent/permit replay and exact POST count; client ID is non-durable |
| Stale Browser action | revision/action/hash conflict before adapter invocation |
| Secret crosses boundary | subprocess/response/log fixtures assert no raw sentinel |
| False cost settlement | resolver binding tests; Browser amount rejected; unavailable source gates validation |
| Validate auto-activates | candidate state and active pointer asserted separately |
| Continuity bypass | decision JSON binding + validate-only coordinator + `NOT_EVALUATED` tests |
| Automatic fallback/retry | exact selected capability and adapter call trace |
| Sites exposes execution | static worker route/build assertions |
| Provider-specific shortcut | same fake contract suite against runtime factory protocol |

## Natural Stop Points

- Governing spec not accepted：停在 docs checkpoint，不写 runtime code。
- same-file writer overlap：在写入前报告 exact file并请求 ownership/order。
- required runtime factory、credential reference、exact cost resolver或candidate owner缺失：保持 lane gated，不造
  fallback或伪造 settlement。
- offline test/review/Harness失败：不执行 live smoke。
- live unknown outcome：停止新动作，保留 evidence并只允许 explicit recovery。

## Rollback

关闭 explicit execution mode即可保留 observer-only。回滚代码时不删除任何 durable attempt、intent、permit、
receipt、candidate、artifact或evidence；由 canonical recovery处理已开始的外部事务。
