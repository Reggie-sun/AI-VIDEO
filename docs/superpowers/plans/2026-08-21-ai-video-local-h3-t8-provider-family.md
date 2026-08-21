# AI-VIDEO Local H3 T8 Quality/Turbo Provider Family Implementation Plan

## Status

Target source/tests implemented in the current local change。Commit
`15ef1d510a59cc9d46445b1fafff2ac2b34a1473` 提供原始capability aggregation、
`compile_request()`与`resolve()`；本slice补全request-aware full family pass-through、restart-safe
status/fetch与pure Registry coexistence regression。Final closure仍取决于independent review与exact
commit-range Harness receipt。

本轮授权source、tests、focused Harness policy route与对应canonical docs；不授权
Provider/ComfyUI/network/credential/media、live quality acceptance、push或release。
Seedance dirty work保持独立，不由本slice覆盖或提交。

Implementation audit确认：

- family已实现capabilities/compiler/resolve及preview/preflight/submit/status/fetch完整pass-through；
- status/fetch seam显式携带committer重开的resolved request，不修改durable schema/hash，也不保存cache；
- Registry pure regression验证family与distinct-name remote objects并存、exact lookup、duplicate rejection
  与zero Provider calls；
- concrete product caller仍负责显式Registry lookup与Service injection；本slice不新增global coordinator；
- exact implementation snapshot必须取得fresh passing Harness receipt后才能声明offline closure。

## Goal and Boundary

```text
Global provider-neutral selection boundary
  ├── comfy-local-h3-t8 -> LocalH3VideoProviderFamily
  │    ├── Quality child
  │    └── Turbo child
  ├── seedance
  ├── minimax_hailuo
  ├── minimax_h3
  └── future distinct-name Providers

Within comfy-local-h3-t8 only:
Router exact selection -> full family identity dispatch -> selected child action -> committer lifecycle
```

Problem boundary：同一个local provider name下的Quality/Turbo需要一个deterministic、stateless、
完整local provider façade；它在same-name family内委托，但不得成为global registry、cross-provider
selector或durable lifecycle owner。

Single owners：

- Planner derives neutral requirement；
- Router selects Provider/profile/capability；
- family aggregates and identity-dispatches the full local provider seam；
- selected child implements each concrete local action；
- `ProductionStateCommitter` persists/activates/recovers。

Old paths to retire：single-capability assumption、partial family with no execution assembly、
“one registered provider”这种global wording，以及把remote Provider coexistence描述为future scope。

Unchanged：Seedance/Hailuo/MiniMax H3 identities与gates、request/resolved/Manifest/Registry/P5/
timeline/review schemas、local/paid seams、no-fallback、Base AI Comic no-Video-Provider path。

## Implemented Change Surface

| Area | Files | Current truth |
| --- | --- | --- |
| Quality child | `src/ai_video/production/comfy_t8_video.py` | existing sealed lane；full local execution |
| Turbo child | `src/ai_video/production/comfy_t8_turbo_video.py` | additive sealed lane；full local execution |
| Family | `src/ai_video/production/local_h3_provider_family.py` | implemented: capability aggregation、compile/resolve 与 full stateless local pass-through |
| Workflows | `workflows/{templates,bindings,profiles}/minimax_h3_t8_t2va_{quality,turbo}*` | exact Quality/Turbo seals |
| Tests | focused T8/family/Router/provider-neutral suites | offline source evidence |
| Canonical routing | policy、contract matrix、runtime baseline | current owner and claim boundaries |

本轮已修改表内明确列出的 implementation files，并同步 local protocol 与 Service 的 reopened-request 传递。
用户已明确授权将 `.agent/harness/policy.yaml` 的 focused-test route 纳入本 task；
`src/ai_video/production/seedance_asset.py` dirty change 仍不属于本 task，必须保留且不得 stage/commit。

## Contract Checkpoint

- **Problem boundary:** one local provider name, two exact capabilities, one full stateless family façade。
- **Single owner:** Router selects；family identity-dispatches；selected child executes；committer persists。
- **Old path:** partial family without runtime assembly与global-only-provider wording。
- **Unchanged:** multi-provider coexistence、local/remote seams、request/state schemas、no-fallback。
- **Focused implementation command for later re-verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_shot_router.py -q
```

## Workstream Tasks

### T1 — Reconcile current implementation truth

**Status:** implemented; documentation correction in this task。

- pin commit `15ef1d5` as current local implementation snapshot；
- distinguish committed source from fresh passing Harness closure；
- remove stale “draft additions” and “future implementation” wording；
- preserve unverified live/media boundaries。

Exit：Spec/Plan no longer claim family methods absent from source。

### T2 — Preserve additive capability identities

**Status:** implemented in `15ef1d5`；requires future exact-range re-verification before closure claim。

- Quality identity/profile/workflow bytes remain unchanged；
- Turbo uses distinct capability/provider-kind/model/profile identity；
- both lanes remainlocal/unmetered/loopback-only；
- duplicate capability ID or identity fails closed；
- no default、ranking或fallback。

Exit：focused capability/profile tests pass on a fresh exact snapshot。

### T3 — Preserve implemented aggregation and compile/resolve

**Status:** implemented source contract；prior plan corrected here。

- `capabilities()` merges and sorts same-provider child variants；
- `compile_request()` dispatches by selected `capability_id`；
- `resolve()` dispatches by exact provider-kind/model/profile/mode identity；
- reject empty、foreign、duplicate或unknown child/identity；
- family MUST NOT retain last-selected child or runtime state。

Exit：原始three-method behavior保持兼容，T4在其上additive补全local seam。

### T4 — Complete full family seam and multi-provider coexistence

**Status:** source/tests implemented；exact Harness closure pending final acceptance。

- parent provider-neutral Spec/Plan must show Local H3、Seedance、Hailuo、MiniMax H3 and future
  distinct-name Providers as peers；
- “unique” must mean sole entry for provider name `comfy-local-h3-t8`，not sole global Provider；
- `VideoProviderRegistry` remains exact lookup with no selection/fallback；
- `VideoGenerationService` remains exact injected-provider lifecycle service，not Registry owner；
- family capability snapshot cannot contain remote Provider variants。

Implemented work：

- expand the family child protocol to the complete `LocalVideoProvider` seam；
- delegate `preview()`/`preflight()`/`submit_local()` by sealed resolved request identity；
- extend `LocalVideoProvider` status/fetch seam with the committer-reopened resolved request；
- delegate `get_local_status()`/`fetch_local()` by that exact identity and reject mismatched
  submission/observation seals before child effects；
- preserve inputs/outputs/permit/submission/observation/receipt byte-for-byte；
- reconstruct a fresh family after restart and prove the same durable identity reaches the same child；
- prove one `("comfy-local-h3-t8", family)` entry can coexist with distinct-name Providers and be the exact
  object an explicit caller injects into `VideoGenerationService`；
- prove family contains no attempt phase、permit、task ID、poll、artifact、activation或recovery state。

The pure regression constructs one Registry containing the Local H3 family object plus distinct-name fake remote
Providers，and asserts exact lookup、duplicate-name rejection and zero runtime/Provider calls。

Exit：one registered T8 family completes both Quality/Turbo local action paths；distinct-name Providers coexist；
no global selector、fallback or second lifecycle owner。

### T5 — Preserve selected-child lifecycle

**Status:** child actions and family request-aware pass-through implemented；live proof remains separate。

- Quality/Turbo child independently implements preview/preflight/submit_local/status/fetch；
- durable request identity and lifecycle receipts remain exact；
- selected child failure never selects sibling or remote Provider；
- node `11`/`13` output validation remains child-specific；
- committer remains the only intent/permit/state/activation/recovery owner。

Exit：existing child lifecycle regression suites remain green through the completed family façade。

### T6 — Synchronize docs and Harness routing

**Status:** source/tests、canonical docs与existing required family/Turbo Harness `argv` synchronized；用户已
明确授权把该pre-existing policy hunk纳入本implementation snapshot。

- Local H3 child docs link to provider-neutral parent owner；
- parent docs own cross-provider coexistence and assembly boundary；
- no new parallel control-plane document；
- docs-only delta routes to `documentation` / `scope_diff_check`。

Exit：Harness inspect maps exact four docs without fallback。

### T7 — Independent review and exact acceptance

**Status:** required for this implementation；pending independent review and exact Harness closure。

Docs review must confirm：

- no global-only-provider implication；
- full family façade behavior matches source/tests and does not imply live/media acceptance；
- Registry、Router、Service、child、committer ownership remains distinct；
- Seedance/Hailuo/MiniMax H3 coexistence is unchanged；
- no historical live evidence or committed code is promoted beyond available receipts。

This implementation task runs the policy-selected source/test checks and exact commit-range Harness before
claiming fresh offline closure。

### T8 — Optional local live technical proof

**Status:** not authorized by this docs task。

Future live execution may run one exact loopback selected child only after sealed preflight/local permit gates。
It must record exact profile、runtime inventory、submit/status/fetch、`ffprobe`、`video-analysis`、artifact hash、
reopen/replay and human verdict。Turbo failure must not trigger Quality or remote fallback。

## Requirements-to-Tasks Traceability

| Requirement | Tasks | Evidence |
| --- | --- | --- |
| Additive Quality/Turbo identities | T2 | profile/capability tests |
| Family aggregation/compile/resolve current surface | T3 | family source/tests + docs review |
| Full stateless family execution façade | T4–T5 | family-to-Service lifecycle/restart regressions |
| Multi-provider coexistence | T4 | parent docs；pure Registry regression |
| Selected child owns lifecycle | T5 | child/local lifecycle tests |
| No ranking/fallback | T2–T5 | Router/family/child negative tests |
| Exact docs correction | T6–T7 | diff check + Harness receipt |
| Live/media separation | T8 | separate execution record only |

## Focused Test Matrix

| Group | Must prove | Must not do |
| --- | --- | --- |
| Family pure | same-name aggregation、sort、compile/resolve dispatch、duplicate rejection | network、durable state |
| Family lifecycle | full identity pass-through、restart same-child、unchanged child receipts | global selection、fallback、second lifecycle |
| Router | explicit exact Quality/Turbo selection、blocked no-fallback | runtime inspection、submit |
| Registry coexistence | distinct names coexist、exact lookup、duplicate rejection | selection、fallback、Provider calls |
| Quality/Turbo children | sealed profile/preflight/output/lifecycle | sibling or remote fallback |
| Docs | parent-child ownership、accurate status/claims | runtime acceptance extrapolation |

## Exact Verification Commands

### Focused implementation re-verification

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_shot_router.py \
  tests/test_production_local_video_state.py \
  tests/test_production_video.py -q
```

### Architecture and policy-routed acceptance

```bash
python -m scripts.architecture_gate check
git diff --check
make harness-inspect
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
```

For this implementation，use the exact staged snapshot or exact commit range and require all task-owned
source、test与canonical doc paths to be present。

## Harness Changed-Path Routing

| Changed paths | Required checks |
| --- | --- |
| four `docs/superpowers/{specs,plans}/...` files | `documentation` + `scope_diff_check` |
| family/source/test change | `production_video_provider_tests` + provider-neutral/Router checks + Architecture Gate |
| policy change | `harness_tests` plus all categories matched by exact delta |

Path mapping alone is insufficient for test additions；the coexistence regression must be present in an
actually executed check `argv`。

## Acceptance Lane Separation

| Lane | Status | Boundary |
| --- | --- | --- |
| Source/test implementation | current task | offline only；no Provider/runtime/media calls |
| Existing partial implementation | superseded by additive full seam | historical `15ef1d5` behavior remains compatible |
| Pure coexistence regression | implemented | no Provider/runtime calls |
| Local live technical | separate task | one exact loopback child |
| Quality vs Turbo A/B | separate plan | no default ranking inference |
| Seedance/Hailuo/cloud live | separate paid task | full Provider-specific gates |

## Review Plan

Native reviewer must return `accept`、`accept with concerns` or `reject` and check：

- Local H3 spec is clearly a child slice；
- parent spec owns multi-provider coexistence；
- additive full family seam preserves the historical three methods and closes exact-name assembly；
- registry exact lookup is not described asselection；
- service injection and local/remote seams are not invented；
- claims distinguish committed、freshly verified、live and quality truth。

Parent verifies all material claims against current files and final diff。

## Rollback and Recovery

- implementation rollback reverts task-owned source/tests/docs together while preserving Quality and all other Providers；
- durable attempts useexisting explicit recovery，never convert to anotherlane/provider；
- rollback never createsfallback、second writer、second Registry or second lifecycle。

## Deferred and Explicitly Unauthorised

- further source/test/policy changes beyond this accepted family seam；
- global Provider catalog or automatic assembly；
- Provider ranking/fallback、multi-candidate generation；
- T8/Turbo/ComfyUI install or runtime mutation；
- any local live media、Hailuo/Seedance/cloud submit、credential or billing action；
- push、release or remote protection changes。
