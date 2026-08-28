# Drama Authoring And Acceptance Prerequisite Record

Date: 2026-08-29

## Purpose

本文记录dual-domain Shot-to-H3 continuity plan的`B-D0 — Drama owner prerequisite` docs-only checkpoint。
本轮只建立独立proposed Drama authoring/acceptance spec；没有选择fixture、baseline或Provider，没有编写
Provider prompt，没有调用ComfyUI、H3、`video-analysis`或生成媒体，也没有进入`M6-D` empirical execution。

## Current Status Truth

Canonical continuity plan与supersession record的当前状态没有被本轮改变：

- `B-D0 = BLOCKED_BEFORE_MEDIA`；
- `M6-D Drama = NOT_EVALUATED`；
- `M6-C Commercial = HUMAN_FAIL`，old Qingyan `15.5s` assembly不得repair、retry或扩成`30s`；
- Drama与Commercial的fixture、baseline、requirement coverage与verdict互不继承；
- M7–M9继续deferred，直到两条lane分别取得其exact HUMAN PASS并完成dual-domain closure。

新Spec当前metadata为`canonical: false`、`spec_status: proposed`、`implementation_status: not_started`、
`quality_status: not_evaluated`。Spec、review、Harness与commit都不能自我产生explicit acceptance或B-D0 PASS。

## Session Work And Decisions

新增：

- `docs/superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md`

该Spec独立拥有candidate Drama contract，不把continuity plan写成Drama truth owner。它定义：

- Story / Scene / Character / Shot authoring boundaries；
- permanent `DRAMA-AUTH-*`与`DRAMA-MEDIA-*` stable requirement IDs；
- narrative、relationship causality、motivation、dialogue、performance、blocking/eyeline、emotional progression、
  payoff/continuation与whole-scene readability rubric；
- eligible `2–3` generated-Shot、至少两个persistent characters的fixture selection contract；
- content-addressed baseline selection与dimension-floor contract；
- exact per-Shot、pairwise、whole-scene uninterrupted `1.0x` full-speed/full-audio HUMAN evidence；
- required `FAIL` / `NOT_EVALUATED` fail-closed、new SHA重新验收与cross-lane no-inheritance rules。

Independent `reviewer_xhigh`首轮发现HUMAN evidence没有完整绑定sealed Drama truth：相同media bytes可能在
authoring package或fixture selection变化后错误复用旧verdict。Spec随后补齐content-addressed authoring
package/profile/rubric、fixture/baseline accepted record与HUMAN authorization bindings，并声明任一bound
identity变化使旧evidence stale。Scoped same-tier re-review最终`accept`，无blocking或non-blocking concern。

`distill-ai-video-learning` automatic evaluation结果为`no_candidate`：本轮只有一个docs-only prerequisite
contract checkpoint，没有两次独立真实attempt、controlled multi-arm comparison或改变existing Learning Claim的
new exact empirical evidence，因此不创建placeholder Learning Claim，也不进入confirmation/adoption flow。

## Ownership Boundary

- Shared Continuity Core继续只拥有physical/perceptual continuity，不拥有motivation、relationship causality、
  dialogue semantics、emotion或payoff。
- Ecommerce继续独占Product Truth/claims、Hook、demo/proof、CTA、brand closure与commercial baseline。
- Router/adapter/Provider继续独占capability selection、native compilation与execution lifecycle；Spec不授权effects。
- Registry/media validators、`ResolvedTimeline`、renderer、P6 lifecycle与`ProductionStateCommitter`继续拥有
  Production correctness、durable review/activation/recovery与Final Acceptance。
- Drama development HUMAN PASS即使未来取得，也不等于Production candidate、P6、Final Acceptance、publication、
  release或audience success。

## Verification And Evidence

Spec checkpoint commit：

```text
b546142289071b801a34ddab7e48f257f2235666
docs: define proposed drama acceptance prerequisite
```

Focused verification：

- `python -m scripts.docs_contract_gate check`：PASS；
- `python -m scripts.agent_harness policy-audit`：PASS，`unmapped/unverified/missing/unreferenced=0`；
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_runtime_skill_boundary.py -q`：
  `2 passed`；
- stable requirement ID uniqueness check：28个catalog IDs，各定义一次；
- `reviewer_xhigh` scoped re-review：`accept`。

Authoritative exact-range Harness：

```text
base: 5bb78637abeb6f41ef4b56a7ce50eba39a9d54a4
head: b546142289071b801a34ddab7e48f257f2235666
receipt: .agent/harness/runs/drama-authoring-prerequisite-spec-20260829-v2/receipt.json
```

Receipt只覆盖新增Spec，selected checks为`scope_diff_check`、`docs_contract_check`、`policy_audit_check`与
`product_runtime_skill_boundary_tests`；status=`passed`。`verify-receipt`确认artifact integrity、policy/scope/
snapshot match、freshness、same-run coverage closure与workspace cleanup均为true。

`.agent/harness/runs/drama-authoring-prerequisite-spec-20260829/receipt.json`不是本任务completion evidence：
Harness intentionally ignores/clears `GIT_INDEX_FILE`，该首次run读取了真实index并混入用户原先staged的
`docs/record_for_agent/2026-08-27-h3-conditioning-attribution-gate-stop.md`。它虽执行通过，但scope不属于本任务，
不得引用为spec-only proof。上方`-v2` exact commit-range receipt是唯一authoritative receipt。

## Remaining Blockers And Next Work

只有用户对exact current Spec bytes给出明确acceptance，并按repository contract更新metadata/registration
（如适用）后，Spec才可成为accepted Drama owner/rubric contract。即使Spec被接受，B-D0仍至少需要：

1. separate explicit selection/acceptance/seal的exact bounded fixture；
2. separate explicit selection/acceptance/seal的exact Drama baseline；
3. 无required authoring `BLOCKER`的sealed authoring package；
4. current execution gates与exact evidence path可用。

本checkpoint不授权上述next work。Next action必须停在用户对proposed Spec的accept/revise decision；不得提前
选择fixture、写Provider prompt、生成media或进入M6-D。

## Agent Guardrails

- Proposed Spec不等于accepted owner；accepted Spec也不自动等于B-D0 PASS。
- HUMAN evidence必须同时绑定exact media与sealed authoring/profile/rubric/fixture/baseline/authorization identity。
- Repair、rerender、re-encode、recomposition、retime、transition、audio replacement或任何bytes变化产生new SHA，
  old verdict不得继承。
- Commercial、Base AI Comic、technical、model/analyzer或historical PASS不得填充Drama finding。
- 本轮publication state仅为local `main` commit；未push、未release、未publish。
