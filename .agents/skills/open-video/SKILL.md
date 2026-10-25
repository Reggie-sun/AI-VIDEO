---
name: open-video
description: "Use for AI-VIDEO Director review of selected source plans, or Director design when raw creative input for new creation or authorized optimization—missing, vague direction, concept, script, reference-led brief, or draft prompt—needs approved Shots and ordered coverage; guidance is advisory and must return to AI-VIDEO contracts. Also trigger for 拼接、剪辑、连续审看, including joining already-approved Shots: judge adjacent cuts and assembled footage for narrative, performance, pacing and audiovisual continuity; single-Shot approval does not replace assembled-film review."
---

# open-video — autonomous director skill

> **AI-VIDEO routing:** Classify the task purpose before deciding whether to optimize raw creative input.
> Selected-source reproduction uses source-preserving review; new creation or authorized optimization
> uses Director design, even for one short clip. Missing project artifacts alone do not authorize redesign.
> Model-specific authoring follows an approved Shot and a selected production route;
> no model recipe chooses the creative strategy or grants execution authority.

> **Creative completion:** For new creation or a creative re-edit, including reused footage,
> read [Creative Completion Practice](references/creative-completion.md) before authoring.
> Preserve relevant cross-turn intent, check the concept independently, and use the practice's
> exact goal binding and review packet before bounded repair,
> and delivery. A technically valid preview with known defects does not complete the work.
> Faithful source reproduction is distinct from creative re-editing; retaining the source does
> not remove exact media review or delivery gates.

## 1. What open-video does

In AI-VIDEO, Codex uses this advisory Skill to make creative decisions: translate the brief into
audience experience, design action and visual expression, direct performance, choose coverage,
and judge whether the result serves the work. Use the
[directorial choices and diagnosis practice](references/creative-completion.md#directorial-choices)
to reason about these decisions before filling the existing coverage fields.

The project-local Skill contains guidance and a coverage validator. Model-specific grammar,
parameters and commands belong to the selected model Skill. Creative reasoning may describe
emotion and motivation; express the observable performance through that selected authoring owner.

Return authoring to the existing Canvas/Shot owners, generation to the selected adapter, timing to
`ResolvedTimeline`, composition to HyperFrames, and acceptance to the existing media/QA owners.
No upstream command, automatic score or PASS stub substitutes for those owners or for watching
and hearing the exact film.

### Specialist Authoring

For story development or production design, read the local [Drama authoring specialist](../drama-authoring/SKILL.md).
For product advertising, use [ad creative](../ad-creative/SKILL.md) with the existing
`ecommerce-ad-workflow` Product Truth and authoring contract. A narrative ad retains its advertising
objective and may borrow Drama craft; it does not become an episodic-fiction request.
For staging, performance or physical action, load only the relevant section of
[Professional Specialists](references/professional-specialists.md). These specialists return advice
to the same approved story and coverage; they do not dispatch one another or execute production.
Skip upstream development for an already approved source or a bounded local repair.

For music spotting, thematic development, score prompts or music repair, read
[Music Direction](references/music-direction.md). Codex acts as the existing Music Director;
choose music from the narrative and actual performance before using a selected music tool.
This does not install another Skill, select a Provider, or authorize generation.

When dialogue rhythm, action timing or shot length is undecided, read
[Event-Led Timing](references/event-led-timing.md). Direct the causal performance and the reason
to hold or cut before choosing a feasible generation duration; an allocated clip duration does not
assign a timestamp to every gesture or line. Preserve fixed user timing and approved source facts.

## 2. Director Task And Coverage

**Step 1 — Understand the request.** Classify the user's task purpose before checking whether
an AI-VIDEO Shot / ordered coverage artifact exists. A selected existing canvas or prompt can be
creatively fixed while still needing faithful import into canonical project artifacts.

- **Selected-source reproduction or exact-input baseline:** require the user's selected source,
  exact prompt and reference identities/roles/order. Review source completeness, observable intent
  and current selected Provider capability. Preserve the source prompt in the generation input;
  construct a semantically unchanged approved Shot Contract rather than redesigning coverage.
  Missing project artifacts do not by themselves make this a `DIRECTOR_PREFLIGHT_REQUEST`.
  Missing source evidence, substantive ambiguity or a contract that cannot represent the source
  faithfully is a gap to report, not permission to invent camera, action, dialogue or hard criteria.
  Keep user-authorized model/resolution differences explicit. Necessary Provider grammar adaptation
  needs an exact source/input diff and is not an unchanged-input baseline. Source reuse still requires
  canonical Shot validation and all normal authorization, budget, egress, permit and media gates;
  it is not an exact-replay authorization or a promise of identical generated pixels.
- **New creation or authorized creative optimization:** classify raw input as `missing`, `direction`
  or `draft_prompt` and use the Director design boundary below. Preserve explicit constraints, fill
  only authorized creative gaps and disclose Director choices. A user prompt is raw input, not approval
  of new Director choices; the task's explicit source-preservation constraint takes precedence.
- **Known-failure repair:** bind the exact failed result and unmet requirement, retain the full goal
  and already satisfied properties, and propose a bounded change only for that failure. Show the
  source/input delta; substantive creative changes follow the task's human decision gate. A failed
  result does not by itself authorize a fresh full-film redesign, retry or new paid call.

Continue the coverage-design procedure below only for the design branch. Source-preserving review
and bounded repair return to existing AI-VIDEO contracts and the selected adapter. Model-specific authoring
must not rewrite a selected source or replace this task classification.

**Raw creative input Director boundary.** Within new creation or authorized optimization, every
request without an approved Shot / ordered coverage is a `DIRECTOR_PREFLIGHT_REQUEST`, whether
it supplies no prompt, a vague direction, a concept/script, a reference-led brief or a draft prompt.
Every such request requires `director_skill=open-video`. Optimize that raw input into Director
coverage and select exactly one `coverage_strategy`: `single_take` or `multi_shot`. Within this
design scope, prompt presence/detail, duration and Provider capability do not establish approval.
Director review does not require a new camera decision for already selected source coverage.

Choose the strategy from the ordered narrative beats, whether action/space/time changes need a
viewpoint reset, whether one camera/blocking trajectory can carry every visible change, pacing and
information reveal, identity/continuity risk, and any explicit user single-take/cut preference.
These considerations are not a fixed score or duration formula. Duration is a pacing and
feasibility input, not a creative branch: a rich `30s` single take and a tightly cut `10s`
multi-shot plan are both valid when the Director rationale and coverage agree. Consider production
feasibility with the production owner while choosing the strategy, using the practice below;
the selected adapter still validates exact capability. Capability limits cannot silently rewrite
approved creative facts. An infeasible strategy returns to Director planning or an explicit gap,
rather than proceeding on the strength of a well-formed prompt.

先按戏剧关注点、信息揭示、动作因果与人物反应决定摄影镜头和切点，再适配模型的生成片段；剧情段落、摄影镜头、一次生成不默认一一对应。选择固定单镜时须说明该机位与人物调度怎样承载整段戏，不能只以保留完整表演、减少身份漂移或生成方便作为理由；也不按每句对白机械切镜。

修复须保留已经满足的叙事、表演与连续性效果，不能据此自动冻结旧景别、机位、镜长或剪辑。若问题涉及镜头覆盖或动作可读性，回到 Director 在已有授权范围内修订 coverage，再走原 authoring revision、依赖失效与执行准入；局部修复入口只准修改哪些变量，不是不可改变的创作要求，也不授权绕过该入口。

Before crafting an approved Shot or Provider-specific prompt for a `DIRECTOR_PREFLIGHT_REQUEST`,
create Director Coverage Evidence with:

- request facts: `creative_input_kind=missing|direction|draft_prompt`, exact
  `creative_input_evidence` for `direction` / `draft_prompt` and `null` for `missing`,
  structured `creative_constraints` with stable `constraint_id`, `source_text` copied as a
  verbatim substring of `creative_input_evidence`, and `scope=global|beat_specific`,
  `target_duration_seconds`, `coverage_strategy`, `strategy_source`, a non-empty
  `director_decision_rationale`, `strategy_request_evidence` when the strategy was directly
  requested by the user, and
  `director_skill=open-video`;
- ordered `coverage_units`, each with `unit_id`, `duration_seconds`, finite `beat_function`,
  `objective`, `open_state`, `close_state`, finite `shot_scale`, finite `camera_treatment`,
  `camera_intent`, `visible_change`, finite `transition_out`, and `constraint_ids`;
- distinct objectives and visible changes; adjacent ordinary multi-Shot units should vary finite
  beat, scale, and camera-treatment categories when that improves coverage, but repetition is
  Director guidance rather than a validation failure; every global constraint ID must bind to
  every unit, while every beat-specific constraint ID must bind to at least one unit.

Validate the evidence before downstream authoring:

```bash
python .agents/skills/open-video/scripts/validate_director_coverage.py <coverage.json>
```

### Requirement-semantics handoff

Schema v3 remains the legacy coverage format and is read under its original rules. New Director
handoffs use schema v4: in addition to the same request and coverage fields, include an
`intent_items` inventory and all five `intent_groups`, even when a group is empty:

- `must_happen`: observable result needed for the approved goal.
- `must_not_happen`: result that would break narrative, quality, continuity, or an explicit user
  constraint.
- `preferred_performance`: a preferred performance or camera treatment for which a reasonable
  alternative can still satisfy the goal.
- `timing_targets`: a time target with `target_kind=delivery_constraint` or
  `target_kind=generation_margin`.
- `acceptable_variation`: a permitted variation linked to the result it must preserve.

Each `intent_items` entry has a stable `intent_item_id`, a single atomic `statement`, an `origin`
of `explicit_user`, `director_choice`, or `repair_margin`, non-empty `source_refs`, and explicit
`related_intent_ids` where it depends on another intent. A source reference carries the exact
`source_hash`, `locator`, source `intent_item_id`, verbatim `quote`, and `origin`; `fixed` is
optional. For `explicit_user`, quote the raw creative input verbatim and bind its SHA-256 to that
exact input. Do not describe a Director-written statement as user evidence. The same source intent
may support separately split performance and timing atoms, but an atom must not be copied into
conflicting groups.

`intent_groups` bind every inventory item by ID. Group entries are `{ "intent_item_id": "..." }`,
while a timing entry also includes its `target_kind`. `acceptable_variation` must name the result it
preserves through `related_intent_ids`. A `generation_margin` must be a `repair_margin` intent and
must point one-way to an original non-margin target; it cannot become an acceptance predicate by
being precise or by appearing in a prompt.

For example, a compound brief such as “the courier holds the sealed key at the delivery cut, no
phone appears, keep identity continuous, use natural hand motion, and reach the pose by 2.7s”
needs separate source-bound atoms for delivery state, phone absence, continuity, natural motion,
and timing. Do not turn the whole sentence, or a recipe margin, into one hard criterion.

Director coverage only records intent and suggested classification. Before any intent can enter the
QA acceptance inventory, the QA acceptance owner must independently approve its `hard_basis`,
predicate, stage, tolerance, measurement, and proof. A hard atom needs an explicit user fixed
requirement, approved narrative result, accepted quality/continuity or cut contract, or applicable
production contract, plus the result it protects and the proof boundary. If a fixed user constraint
conflicts with a proposed variation, return it to authoring/QA instead of weakening it. Prompt
wording, historical observations, Provider recipes, and generation margins never grant that
authority.

`VIDEO_EXTEND`, FLF2V, a terminal-frame handoff, `no cut`, and `uninterrupted` are continuity or
execution treatments, not the Director decision. They are valid only when the selected strategy is
`single_take`; if that strategy has multiple evolving internal coverage units, every non-final
transition must remain continuous. `multi_shot` requires at least two ordered units and cut-class
non-final transitions. `strategy_source=user_requested` requires direct user evidence;
`strategy_source=agent_directed` requires no invented user evidence. Within the authorized design
scope, Director optimization may
expand gaps or restructure a draft, but must preserve explicit user constraints and disclose its
own decisions through the rationale. Selected-source reproduction does not become optimization
merely because its source has not yet been imported as an approved project artifact. An already
approved Shot does not re-enter this validator unless the task changes its creative intent or coverage.
Internal enums, validation output and serialized Shot/coverage fields must not be mechanically
appended to the model prompt. Review the exact generation input and source diff before submission;
keeping the original quote inside a longer rewritten prompt does not prove faithful reproduction.

The validator proves declared-inventory structure, verbatim source anchoring, and binding
completeness; it does not prove exhaustive constraint extraction or natural-language entailment.
Before Shot approval, the Agent must first compare raw evidence against the declared inventory for
unextracted explicit constraints, then compare the declared inventory against planned coverage for
omissions, reversals, or unauthorized reinterpretation.

**Carry the meaning through authoring.** Before submission, trace the decisive action, relation or
reveal from coverage into Canvas direction / `Shot.intent`, then the selected `generation_intent`
or preserved source and the actual native preview. Prose in `Shot.intent` alone does not guarantee
that it reaches the model. Identify where the meaning is expressed; matching IDs or retaining a
quote elsewhere is insufficient. If “tries to sit but is blocked” becomes “leans forward and stands
still”, fix the authoring handoff. Do not ask the Compiler to invent the missing action. Check that
the existing QA owner has not reduced the necessary result to an easier incidental gesture;
preferences and generation margins still require the classification above.

For known-quality failures, use
[failure attribution](references/creative-completion.md#failure-attribution) before selecting a fix,
including during source-preserving review. Diagnosis does not authorize redesigning approved
content or another generation attempt.

## 3. Production Feasibility And Handoff

While choosing coverage, use [Production Feasibility](references/creative-completion.md#production-feasibility)
to identify the decisive event and its implementation risk with the production owner. Compare routes
against current model/adapter evidence and available assets before committing to a design. A supported
mode, reference slot or valid prompt does not establish that the required performance or contact will work.
Preserve approved creative facts; choose an expressive solution within scope or report the exact capability gap.

Use the existing [Production Strategy owner](../../../docs/agent-primary-contract-matrix.md#production-strategy)
for executable allocation and route selection; Director proposals do not select active Product state,
qualify assets or bypass readiness. Once the Shot and selected route are established:

- H3 authoring uses [h3-video](../h3-video/SKILL.md); selected Seedance authoring uses
  [seedance-authoring](../seedance-authoring/SKILL.md); selected Vidu models/services use
  [vidu-authoring](../vidu-authoring/SKILL.md), including dialogue versus automated TTS service matching.
  Other selected models use their matching owner.
- Generation uses the selected adapter and existing authorization, budget, egress and permit gates.
  Rendering uses HyperFrames and timing uses the single `ResolvedTimeline`.
- After each exact MP4, explicitly use project-local `video-analysis` MCP and the
  [Per-Shot Post-Media Gate](../../../.agent/context/control-plane-playbook.md#per-shot-post-media-gate).
  Only all-required `PASS` permits the next Shot; `FAIL` / `NOT_EVALUATED` stops the attempt,
  unknown stops for recovery. Scores and automatic PASS stubs do not replace media evidence.
- Review the actual film using [Creative Completion Practice](references/creative-completion.md);
  a paper comparison or successful technical check does not establish natural performance or audience appeal.

[Legacy H3 upstream text](references/legacy-h3-upstream.md) is archived for explicit historical lookup,
not part of this Director procedure and not required reading for ordinary directing.
