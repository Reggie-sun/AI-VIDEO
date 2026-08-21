# AI-VIDEO Local H3 T8 Quality/Turbo Provider Family Implementation Plan

## Status

Proposed completion and acceptance plan；本窗口只写Plan，不执行implementation、test adoption或
live generation。

Current working tree已经包含一组并发Turbo/family draft。未来执行本Plan时必须先inspect、review并
adopt或修正该exact draft，不能假定它已完成，也不能为了“按Plan实现”而覆盖、重写或reset他人
in-progress work。

Implementation start gate：

1. 配套Spec
   `docs/superpowers/specs/2026-08-21-ai-video-local-h3-t8-provider-family.md`
   被接受；
2. 重新检查current `main`、dirty state、live ownership与exact target-file overlap；
3. 对current draft做independent native review并由parent核验blocking claims；
4. 用户明确要求开始implementation/execution，而不是仅写docs；
5. 开始前重新读取current profile/workflow/tests、contract matrix、Harness policy与runtime baseline。

本Plan不授权Provider/ComfyUI/network/credential、media generation、push或release。

## Goal and Boundary

完成一个additive、fail-closed的Local H3 T8 provider family：

```text
Quality child (existing, preserved)
                           \
                            -> LocalH3VideoProviderFamily -> one registered LocalVideoProvider
                           /
Turbo child (new, explicit)

Router-selected exact identity -> family pass-through -> exact child action -> ProductionStateCommitter
```

Problem boundary：Quality与Turbo需要在一个provider family下被Router显式区分，同时保持既有
local-video lifecycle唯一。

Single owners：Router selects；family statelessly dispatches the full local-provider seam；selected child
performsProvider actions；
`ProductionStateCommitter` persists/activates/recovers。

Old assumption to retire：`comfy-local-h3-t8`只有一个capability，因此provider object本身就能代表
唯一lane。Retirement只发生在capability exposure/wiring层，不删除Quality adapter或historical path。

Unchanged contracts：Quality bytes、provider-neutral requirement、request/resolved lineage、Manifest、
Registry、P5、`ResolvedTimeline`、HyperFrames、Review/Repair、local permit、unknown-outcome、replay、
recovery、Legacy CLI与no-fallback。

## Planned Change Surface

以下是future implementation/adoption的expected ownership surface，不是本轮allowed writes：

| Area | Expected files | Purpose |
| --- | --- | --- |
| Existing child | `src/ai_video/production/comfy_t8_video.py` | preserve Quality contract；只允许必要shared helper correction |
| Turbo child | `src/ai_video/production/comfy_t8_turbo_video.py` | sealed Turbo profile、workflow render、preflight与selected-child execution |
| Family | `src/ai_video/production/local_h3_provider_family.py` | one registered full `LocalVideoProvider` façade；exact action dispatch、no durable state |
| Public surface | `src/ai_video/production/__init__.py` | additive exports；保留Quality exports |
| Workflow artifacts | `workflows/{templates,bindings,profiles}/minimax_h3_t8_t2va_turbo*` | exact Turbo graph/binding/profile seals |
| Focused tests | `tests/test_production_comfy_t8_turbo_video.py`, `tests/test_production_local_h3_provider_family.py` | Turbo/family contract and fail-closed cases |
| Integration tests | `tests/test_production_shot_router.py`, existing T8/local-video suites | explicit selection、family-to-`VideoGenerationService` handoff、node 13 negative matrix、lifecycle regression |
| Routing/docs | `.agent/harness/policy.yaml`, contract matrix、runtime baseline | exact path routing与accepted truth after receipt |

`src/ai_video/production/seedance_asset.py`及其它unrelated dirty files不属于本Plan，必须保留且不得
stage/commit。若future writer与上述任一exact file发生same-file overlap，写入前停止并由用户决定
ownership/顺序；disjoint paths按repository rules继续。

## Contract Checkpoint Before Code

Parent在任何future edit前必须记录：

- **Problem boundary:** one provider name, two explicit T2VA capabilities, one existing lifecycle；
- **Single owner:** family owns onlyin-memory identity dispatch for the complete provider seam；selected
  child performs the action；committer ownsdurable lifecycle；
- **Old path:** single-capability provider assumption；Quality implementation itself remains；
- **Unchanged:** request/resolved/Manifest/Registry/P5/timeline/review schemas and no-fallback；
- **First focused command:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py -q
```

## Execution Tasks

### T1 — Inspect and classify the current draft

**Goal:** 在写入前把current working-tree draft分成adopt、correct或out-of-scope。

Required work：

- inspect exact diff and live ownership for all planned paths；
- confirm Quality adapter/profile/workflow/binding bytes没有被Turbo lane改写；
- compare Turbo profile hashes with exact workflow/binding/component/LoRA declarations；
- confirm family只提供capability aggregation与full protocol identity dispatch，不保存durable state；
- confirm public exports、policy、contract matrix和baseline changes来自同一lane；
- classify unrelated `seedance_asset.py` and any later dirty paths aspreserve-only。

Exit：parent记录exact owned files、existing changes adopted、known gaps与first verification command。
不得通过file presence宣布实现完成。

### T2 — Lock additive profile and capability identities

**Goal:** Turbo addition不能改变Quality seal，两个capability必须显式且互不歧义。

Required work：

- keep Quality capability/profile identity byte-stable；
- seal Turbo upstream/T8/ComfyUI/VHS/SageAttention/model/LoRA/workflow/binding/node-schema
  identities；
- fix Turbo capability to LOCAL + LOCAL_UNMETERED + TEXT_TO_VIDEO；
- fix exact `capability_id`、`provider_kind`、`model_id`、`profile_version`；
- assertremote/fallback disabled；
- test that Quality child rejectsTurbo identity and Turbo child rejectsQuality identity。

RED cases first：Quality profile file SHA drift、duplicate identity、LoRA size/hash drift、workflow or
binding reseal without profile update、remote endpoint、wrong output geometry。

Exit：profile/capability focused tests pass，Quality regression remains green。

### T3 — Complete Turbo workflow and preflight contract

**Goal:** selected Turbo child在任何prompt effect前验证exact runtime并render唯一six-step graph。

Required work：

- validate exact workflow topology and binding aliases；
- bind prompt、seed、width/height、frame count、steps、scheduler、LoRA fields和output prefix；
- preflight exact runtime commits/versions、launch capability、four H3 components、Turbo LoRA、
  required nodes与custom-node input schema；
- render 6 steps、`simple`、denoise 1.0、Turbo sampler、native audio、CRF 17、node `13`；
- keep loopback-only transport with `trust_env=False` and redirects disabled；
- consume exact durable local permit immediately before one submit；
- map pre-effect validation failure vs outcome-unknown submit failure toexisting typed semantics。

RED cases first：runtime drift、missing node、input schema drift、LoRA drift、wrong task/audio mode、
wrong node wiring、invalid permit、submit exception。

Exit：Turbo preflight/submit tests pass，zero submit effect is proven for all preflight failures。

### T4 — Complete family aggregation, full-provider dispatch and Router wiring

**Goal:** Router看到一个deterministic two-capability snapshot；同一个family作为唯一registered
`LocalVideoProvider`把durable identity路由到exact child，且无fallback。

Required work：

- reject empty/foreign/duplicate children；
- sort variants bycapability ID；
- dispatch compile byselected `capability_id`；
- dispatch resolve by `(provider_kind, model_id, profile_version, mode)`；
- implement `preview`、`preflight`、`submit_local`、`get_local_status`与`fetch_local` as
  identity-based pass-through to the same child instance；
- register only one `comfy-local-h3-t8` family in`VideoProviderRegistry`，不重复注册两个child；
- pass family to`VideoGenerationService` and prove Router-selected Quality/Turbo each complete the
  expected local action path；
- reconstruct a fresh family forrestart and prove durable resolved identity routes status/fetch to the
  same profile without process-local last-selection state；
- prove unknown/ambiguous identity typed fails closed；
- update Router integration test to selectQuality andTurbo independently；
- proveRouter selection performsno runtime inspection、no preflight、no submit；
- provemissing/wrong capability remains `BLOCKED_CAPABILITY` without choosing the other lane。

Exit：family + Router + `VideoGenerationService` handoff tests pass；family source contains no attempt
phase、permit、task ID、poll result、artifact locator或activation/recovery state。

### T5 — Prove selected-child lifecycle completeness

**Goal:** 保留current positive Turbo status/fetch proof，并补齐selected-child与output artifact的
fail-closed negative matrix。

Required work：

- retain the current fake terminal history atoutput node `"13"` with exactly one final
  `*-audio.mp4`；
- retainpositive `get_local_status()` observation and exact `fetch_local()` measured receipt；
- add rejection for non-MP4/empty fetched bytes；
- reject Quality node `"11"`-only history forTurbo；
- reject video-only sibling、zero final AV、duplicate final AV、wrong suffix和ambiguous locator；
- retain existing local intent/status/fetch/recovery tests forQuality/local providers；
- ensure exact replay produces zero provider/Manifest effects and unknown outcome never switches child。

Source inspection confirms `_final_av_artifact(history, self.profile)` is dynamic，且current focused test
已把positive node 13 path变成executable proof。本task只补当前缺少的negative matrix与family-level
same-child handoff proof。

Exit：Turbo node 13 status/fetch regression and existing local lifecycle suite pass。

### T6 — Public surface, policy and canonical docs

**Goal:** 新paths被正确路由，canonical docs只陈述receipt支持的truth。

Required work：

- additive export Turbo/family types without removingQuality exports；
- mapTurbo/family source/tests/workflow/profile/binding to`production_video_provider` Harness category；
- add `tests/test_production_comfy_t8_turbo_video.py` and
  `tests/test_production_local_h3_provider_family.py` to the actual
  `checks.production_video_provider_tests.argv` command；path mapping alone is insufficient；
- keep contract matrix focused test list aligned withpolicy；
- update runtime baseline only afteroffline implementation acceptance；
- state explicitly: no live Turbo media、no host compatibility proof、no subjective quality claim；
- run Harness policy tests ifpolicy changed。

Exit：policy audit maps everyowned path；docs claim boundary matches tests/receipt。

### T7 — Independent review and exact acceptance

**Goal:** 用independent semantic review与exact snapshot evidence决定accept/reject。

Reviewer必须检查：

- Quality seal是否真正未变；
- Turbo是不是additive explicit lane而不是replacement/fallback；
- family是否错误拥有execution/lifecycle；
- identity dispatch是否可歧义；
- preflight是否在permit/submit前完成；
- node `13` status/fetch是否真实被tests覆盖；
- policy/docs是否把offline acceptance夸大为live/quality；
- unrelated dirty work是否被stage或commit。

Reviewer输出`Verdict`、`Blocking issues`、`Non-blocking concerns`、file/test evidence和minimal
follow-up。Parent必须复核重要claims、final diff与staged file list。

Exit：no blocking review issue；exact staged Harness receipt fresh and self-valid；task-only checkpoint
commit created。

### T8 — Optional local live technical proof

**Not part of this docs-only request or default implementation acceptance.**

只有用户后续明确要求实际执行时才进入。Local loopback unmetered generation不需要paid
authorization，但仍必须：

- useexact isolated/pinned ComfyUI/T8/Turbo runtime and profile-listed component bytes；
- avoid upstream Long Video/Studio/Repair/Reel/Context IR/external-provider routes；
- submit exactly theuser-scoped number of attempts；no retry/fallback unless separately authorized；
- record durable intent、permit、status/fetch、activation、reopen、replay/recovery；
- verify exact output with`ffprobe`、project-local `video-analysis`、audio inspection and human review；
- distinguish technical success fromQuality-vs-Turbo oruniversal subjective acceptance。

Quality vs Turbo controlled A/B is anotherexplicit task：fixed Shot/requirement/prompt/seed/assets/
dimensions/frames/fps/encoder and one changed sampling lane at a time。

## Requirements-to-Tasks Traceability

| Requirement | Tasks | Primary evidence |
| --- | --- | --- |
| Preserve Quality seal | T1–T2 | Quality profile SHA + existing suite |
| Add distinct Turbo capability | T2–T3 | profile/capability/workflow tests |
| One family, exact full-provider dispatch | T4 | family uniqueness + Router -> service handoff/restart tests |
| Router explicit selection/no fallback | T4 | Quality/Turbo/missing capability matrix |
| Existing lifecycle unchanged | T3, T5 | permit/status/fetch/replay/recovery tests |
| Turbo node 13 output correctness | T5 | retained positive path + negative artifact matrix |
| No remote/credential/second truth | T2–T7 | profile invariants、search/review、policy |
| Exact acceptance evidence | T6–T7 | Harness inspect/verify/receipt |
| Live/quality separation | T8 | separate execution record only |

## Focused Test Matrix

| Test group | Must prove | Must not do |
| --- | --- | --- |
| Quality adapter | old profile/workflow seal、preflight、status/fetch | Turbo selection、network |
| Turbo adapter | exact profile/LoRA/schema、six-step render、node 13 lifecycle | fallback、quality verdict |
| Family | deterministic aggregation、snapshot-unique IDs/identities、full seam same-child dispatch | durable state、fallback |
| Router | explicit Quality/Turbo selection and typed denial | runtime inspection、IO |
| Local lifecycle | permit、status/fetch、unknown outcome、replay/recovery | second committer、blind retry |
| Architecture/policy | imports、path routing、no second truth | baseline refresh hiding debt |

## Exact Verification Commands

使用repository-standard `python -m pytest`，不得用裸`pytest`。

### Turbo and family first

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py -q
```

### Quality preservation and Router integration

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_provider_neutral_adapters.py \
  tests/test_production_shot_router.py -q
```

### Local lifecycle invariants

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_local_video_state.py \
  tests/test_production_video_state_recovery.py \
  tests/test_production_generated_video_e2e.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

### Full mapped provider category and architecture

```bash
python -m pytest -p no:cacheprovider \
  tests/test_production_comfy_video.py \
  tests/test_production_comfy_t8_video.py \
  tests/test_production_comfy_t8_turbo_video.py \
  tests/test_production_local_h3_provider_family.py \
  tests/test_production_minimax_h3.py \
  tests/test_production_shot_router.py \
  tests/test_production_video.py \
  tests/test_production_video_state_recovery.py -q
python -m scripts.architecture_gate check
```

### Exact snapshot Harness

```bash
git diff --check
make harness-inspect
make harness-verify
make harness-receipt RECEIPT=<fresh-receipt-path>
```

若final acceptance使用commit range：

```bash
make harness-verify-range BASE_REF=<verified-base-commit>
make harness-receipt RECEIPT=<fresh-range-receipt-path>
```

## Harness Changed-Path Routing

| Changed paths | Required category/checks |
| --- | --- |
| `comfy_t8_turbo_video.py`, `local_h3_provider_family.py`, related tests | `production_video_provider_tests` + neutral requirement tests + Architecture Gate |
| Turbo workflow/profile/binding | same provider category + workflow seal tests |
| `tests/test_production_shot_router.py` | Router + neutral requirement + Architecture Gate |
| `src/ai_video/production/__init__.py` | shared Production + provider categories as exact policy resolves |
| `.agent/harness/policy.yaml` / contract matrix | Harness tests plus every category matched by same staged delta |
| canonical docs | `documentation` + always-on `scope_diff_check`；docs不替代code tests |

Implementation完成前运行`python scripts/agent_harness.py inspect --path <each owned path>`核对当前
policy output；本表是human-readable expectation，不能替代machine-readable routing truth。
同时必须直接检查`production_video_provider_tests.argv`确实列出Turbo与family focused test；仅有
category pattern匹配不能证明detached Harness执行了核心tests。

## Acceptance Lane Separation

### Fake/offline acceptance — T1–T7 default

可以证明：profile/workflow seals、identity、Router selection、dispatch、preflight order、permit、
node 13 status/fetch、typed failure、replay/recovery regression和path routing。

不能证明：installed runtime compatibility、GPU execution、wall time、VRAM、audio sync、motion、
visual quality、human GO、P6 Review或Final Acceptance。

### Local live technical proof — T8 separate execution task

可以证明一个exact pinned host/runtime/request的loopback execution chain与measured artifact。

不能证明Turbo普遍优于Quality、其它assets/prompts、cloud portability或universal quality。

### Controlled Quality vs Turbo A/B — separate plan/run record

只有fixed-input、one-variable-at-a-time、measured media + human review才可比较。不得用steps更少、
文件更大或upstream“stable”claim代替AI-VIDEO evidence。

## Review Plan

Implementation review使用native named `reviewer`。Reviewer必须独立检查：

- stated bug/goal是否真正由exact selection + child-owned lifecycle解决；
- Quality behavior是否在scope外改变；
- family是否完整实现`LocalVideoProvider` same-child dispatch且没有hidden coupling、fallback或
  second durable state；
- Turbo tests是否覆盖真实terminal/fetch failure mode而不只是rendered dict；
- profile/license/source metadata是否准确且没有复制未审查upstream code；
- docs/runtime truth与actual receipt是否一致。

Parent负责解决contradictions、直接验证critical claims、review final diff、确认task-only staged files并
决定accept/reject。

## Rollback and Recovery

- T1–T7未开始durable attempt时，按task-owned commits反向撤销Turbo/family additive delta；保留
  Quality lane和historical evidence；
- 不允许rollback成single-provider implicit selection或automatic fallback；
- 任何已durable begin的Turbo attempt只走existing explicit recovery；不得改写成Quality、
  blind retry、remint permit或删除complete orphan evidence；
- docs/policy rollback必须同步，不能保留宣称accepted但source已删除的runtime baseline。

## Deferred and Explicitly Unauthorised

- T8/Turbo/ComfyUI install、upgrade或active-runtime mutation；
- Local Turbo generation、Quality-vs-Turbo A/B、VRAM/performance benchmark；
- Long Video、Studio、Repair、Reel、Context IR/external Provider routes；
- Provider ranking、default selection、fallback、multi-candidate generation；
- Manifest/Registry/request schema、second writer/resolver/timeline/renderer；
- remote/paid Provider、credential、cloud egress；
- push、release、publication或remote protection changes。

完成T1–T7只代表offline implementation acceptance，不代表live、media quality、P6 Review或Final
Acceptance。用户后续明确要求前不得开始T8。
