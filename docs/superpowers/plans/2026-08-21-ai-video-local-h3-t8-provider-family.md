# AI-VIDEO Local H3 T8 Quality/Turbo Provider Family Implementation Plan

## Status

Partial implementation已提交到local `main` commit
`15ef1d510a59cc9d46445b1fafff2ac2b34a1473`。该commit完成capability aggregation、
`compile_request()`与`resolve()`，但未实现完整family local execution pass-through或
Registry-to-Service runtime assembly。本Plan现同时记录implemented work与remaining blocker。

本轮用户只授权修订specs/plans。允许写入仅限本Plan、配套Local H3 Spec以及existing
provider-neutral parent Spec/Plan；不授权source/test/policy/runtime/Provider/ComfyUI/network/
credential/media、push或release。

Current audit发现：

- current code中的family只实现`capabilities()`、`compile_request()`、`resolve()`；
- canonical matrix描述current family只做compile/resolve，selected child继续实现具体action；
- 但exact-name Registry无法同时注册两个同名children，而partial family又不能注入
  `VideoGenerationService`；因此full stateless `LocalVideoProvider` pass-through仍是target contract，
  不是已经完成的current truth；
- workspace中未找到覆盖exact implementation snapshot且状态为`passed`的Harness receipt，故不能
  仅凭commit或canonical prose重申fresh offline closure。

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
| Family | `src/ai_video/production/local_h3_provider_family.py` | current: capability aggregation + compile/resolve；target: full stateless local pass-through |
| Workflows | `workflows/{templates,bindings,profiles}/minimax_h3_t8_t2va_{quality,turbo}*` | exact Quality/Turbo seals |
| Tests | focused T8/family/Router/provider-neutral suites | offline source evidence |
| Canonical routing | policy、contract matrix、runtime baseline | current owner and claim boundaries |

本轮不修改上述implementation files。Unrelated `.agent/harness/policy.yaml` 与
`src/ai_video/production/seedance_asset.py` dirty changes不属于本task，必须保留且不得stage/commit。

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

Exit：current implemented three-method surface remains stable while T4 completes the missing provider seam。

### T4 — Complete full family seam and multi-provider coexistence

**Status:** docs target in this task；source/tests/policy implementation remains future authorized work。

- parent provider-neutral Spec/Plan must show Local H3、Seedance、Hailuo、MiniMax H3 and future
  distinct-name Providers as peers；
- “unique” must mean sole entry for provider name `comfy-local-h3-t8`，not sole global Provider；
- `VideoProviderRegistry` remains exact lookup with no selection/fallback；
- `VideoGenerationService` remains exact injected-provider lifecycle service，not Registry owner；
- family capability snapshot cannot contain remote Provider variants。

Required future implementation：

- expand the family child protocol to the complete `LocalVideoProvider` seam；
- delegate `preview()`/`preflight()`/`submit_local()` by sealed resolved request identity；
- delegate `get_local_status()`/`fetch_local()` by durable submission resolved identity；
- preserve inputs/outputs/permit/submission/observation/receipt byte-for-byte；
- reconstruct a fresh family after restart and prove the same durable identity reaches the same child；
- register only one `("comfy-local-h3-t8", family)` entry and inject that family into
  `VideoGenerationService`；
- prove family contains no attempt phase、permit、task ID、poll、artifact、activation或recovery state。

Future pure regression should construct one Registry containing the Local H3 family object plus distinct-name
fake remote Providers，assert exact lookup、duplicate-name rejection and zero runtime/Provider calls。

Exit：one registered T8 family completes both Quality/Turbo local action paths；distinct-name Providers coexist；
no global selector、fallback or second lifecycle owner。

### T5 — Preserve selected-child lifecycle

**Status:** child action implementations exist；family pass-through/restart proof remains pending T4。

- Quality/Turbo child independently implements preview/preflight/submit_local/status/fetch；
- durable request identity and lifecycle receipts remain exact；
- selected child failure never selects sibling or remote Provider；
- node `11`/`13` output validation remains child-specific；
- committer remains the only intent/permit/state/activation/recovery owner。

Exit：existing child lifecycle regression suites remain green through the completed family façade。

### T6 — Synchronize docs and Harness routing

**Status:** current implementation changed canonical docs/policy；this task changes only four specs/plans。

- Local H3 child docs link to provider-neutral parent owner；
- parent docs own cross-provider coexistence and assembly boundary；
- no new parallel control-plane document；
- docs-only delta routes to `documentation` / `scope_diff_check`。

Exit：Harness inspect maps exact four docs without fallback。

### T7 — Independent review and exact acceptance

**Status:** required for this documentation correction；implementation closure remains separate。

Docs review must confirm：

- no global-only-provider implication；
- no claim that the full family façade is current or implemented；
- Registry、Router、Service、child、committer ownership remains distinct；
- Seedance/Hailuo/MiniMax H3 coexistence is unchanged；
- no historical live evidence or committed code is promoted beyond available receipts。

This docs task runs exact commit-range Harness for its four files. A separate implementation verification task
must rerun the policy-selected source/test range for `15ef1d5` before claiming fresh offline closure。

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
| Multi-provider coexistence | T4 | parent docs；future pure Registry regression |
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

For this docs-only correction，use exact staged snapshot or exact commit range and require
`changed_paths` to equal the four task-owned Spec/Plan files。

## Harness Changed-Path Routing

| Changed paths | Required checks |
| --- | --- |
| four `docs/superpowers/{specs,plans}/...` files | `documentation` + `scope_diff_check` |
| future family/source/test change | `production_video_provider_tests` + provider-neutral/Router checks + Architecture Gate |
| future policy change | `harness_tests` plus all categories matched by exact delta |

Path mapping alone is insufficient for future test additions；new coexistence regression must be present in an
actually executed check `argv`。

## Acceptance Lane Separation

| Lane | Status | Boundary |
| --- | --- | --- |
| Docs correction | current task | no code/runtime/media |
| Existing partial implementation | committed at `15ef1d5` | full family lifecycle and fresh passing exact-range receipt not confirmed |
| Pure coexistence regression | pending code scope | no Provider/runtime calls |
| Local live technical | separate task | one exact loopback child |
| Quality vs Turbo A/B | separate plan | no default ranking inference |
| Seedance/Hailuo/cloud live | separate paid task | full Provider-specific gates |

## Review Plan

Native reviewer must return `accept`、`accept with concerns` or `reject` and check：

- Local H3 spec is clearly a child slice；
- parent spec owns multi-provider coexistence；
- current three-method implementation is described as partial，while target full family seam closes exact-name assembly；
- registry exact lookup is not described asselection；
- service injection and local/remote seams are not invented；
- claims distinguish committed、freshly verified、live and quality truth。

Parent verifies all material claims against current files and final diff。

## Rollback and Recovery

- Docs correction rollback only reverts this task’s four files；
- implementation rollback preservesQuality and all other Providers；
- durable attempts useexisting explicit recovery，never convert to anotherlane/provider；
- rollback never createsfallback、second writer、second Registry or second lifecycle。

## Deferred and Explicitly Unauthorised

- source/test/policy changes，includingfull family seam and Registry coexistence tests；
- global Provider catalog or automatic assembly；
- Provider ranking/fallback、multi-candidate generation；
- T8/Turbo/ComfyUI install or runtime mutation；
- any local live media、Hailuo/Seedance/cloud submit、credential or billing action；
- push、release or remote protection changes。
