# Decision C-lite Composition Strategy Shadow — When To Do

## Status

Decision C-lite Stage 1 and Stage 2 are implemented locally on `main` as a
Development-Governance-only shadow capability. No live Provider, paid/cloud execution,
push, or release was performed.

The next step is a 20–50 Shot real shadow Pilot. Do not promote the proposal into
canonical Production planning before that evidence exists.

## Governing Artifacts

- User-approved Decision C-lite implementation contract from the 2026-08-22 task.
- Existing planner contract:
  `docs/superpowers/specs/2026-08-21-ai-video-video-planner-subagent.md`
- Existing provider-neutral requirement contract:
  `docs/superpowers/specs/2026-08-21-ai-video-provider-neutral-generation-requirement.md`
- Existing readiness contract:
  `docs/superpowers/specs/2026-08-21-ai-video-shot-readiness-gate-v3.md`
- Existing Quality Intelligence contract:
  `docs/superpowers/specs/2026-08-21-ai-video-quality-experience-record-v1.md`
- Roadmap status:
  `docs/v0.2-agentic-production-roadmap.md`

No separate durable Decision C-lite spec or plan was created. The user task contract,
repository constitution, and existing canonical contracts were sufficient for this
bounded implementation.

## Delivered

### Stage 1 — Composition Playbooks

Added the Development-Governance-owned directory:

```text
.agent/playbooks/composition/
├── README.md
├── schema.json
├── hard_cut_continuation.yaml
├── character_consistent_dialogue_scene.yaml
└── narration_ai_comic.yaml
```

The Playbooks are declarative advisory knowledge. They may describe applicability,
preferred strategies, forbidden fallbacks, required evidence, limitations, failure
modes, review requirements, and repair suggestions.

They do not own or record Production Manifest state, Asset Registry identity, Provider
task state, budget, permit, active output, QA verdict, Final Acceptance, ResolvedTimeline,
or Dependency Graph state. Product Runtime does not read `.agent/playbooks`.

Validation is deterministic, no-network, and strict:

- YAML duplicate keys are rejected.
- Unknown fields are rejected.
- Required collections are non-empty and unique where required.
- Version, strategy, continuity, and playbook identity values are typed.
- Absolute paths, credential fields, Provider task state, and runtime lifecycle fields
  are rejected.
- The checked-in JSON Schema is checked against the strict Python model.

### Stage 2 — Typed Shadow Proposal

Added development-side tooling in:

- `scripts/composition_playbooks.py`
- `scripts/composition_shadow.py`

`CompositionStrategyProposal` contains complete Shot identity, playbook identity/version,
proposed strategy, continuity preference, typed rationale, rejected strategies,
uncertainty, required evidence, expected failure modes, and a deterministic semantic hash.

Diagnostic `notes` and `proposal_id` do not alter the semantic hash.

`compare_strategy_proposal(proposal, current_plan)` returns typed:

```text
MATCH
DIFFERENT
NOT_COMPARABLE
```

The comparison is pure. It does not modify the current plan, call a Provider, write
Manifest state, access network or credentials, or create Production side effects.

### Harness And Architecture Protection

Added the `composition_strategy_shadow` Harness category and focused checks for:

- Playbook schema tests;
- proposal/comparison tests;
- Product Runtime isolation tests;
- task Architecture Gate.

The architecture tests explicitly protect against `src/ai_video/**` importing or reading
the composition tooling or `.agent/playbooks`.

## Ownership Boundary

```text
Codex / Composition Playbook
        ↓
Shadow Strategy Proposal
        ↓
compare only
        ↓
Existing VideoPlanner
        ↓
ShotReadinessGate
        ↓
Shot Router
        ↓
Provider
```

The canonical owners remain:

- Agent: propose;
- Playbook: advisory knowledge;
- `VideoPlanner`: current canonical strategy decision;
- `ShotReadinessGate`: structural readiness;
- Shot Router: Provider/profile/capability binding;
- `ProductionStateCommitter`: durable lifecycle, activation, and recovery.

No Product Runtime Strategy Validator, generic LLM runtime, `CompositionSkillLibrary`,
`ExecutionTrace`, or Skill Evolution was introduced.

## Problems And Resolutions

- Independent review found five boundary defects: absolute-path bypasses, an overly broad
  identity reason, permissive playbook IDs, an incomplete architecture import scanner,
  and incorrect `VIDEO_EDIT`/`VIDEO_EXTEND` comparison handling. These were corrected and
  covered by regression tests.
- A concurrent docs/Harness writer owned shared Harness files for part of the window.
  The work was left untouched until its checkpoint was committed.
- A concurrent staged index caused commit `f018e4a` to include the composition Harness test
  together with eight unrelated Production files. The local history was not rewritten by
  decision; the mixed checkpoint is intentionally disclosed here.
- Direct Architecture Gate execution in the shared checkout reported an `ARCH002` error
  from another writer's staged `shot_router.py` change. The exact detached Decision C-lite
  snapshot passed its own Architecture Gate with zero findings.

## Verification

Focused verification:

- Playbook/proposal suites: `38 passed`.
- Architecture isolation and Harness routing: `5 passed`.
- `make harness-audit`: passed with no unmapped or unverified paths.
- `python -m scripts.docs_contract_gate check`: passed.

Exact detached Harness receipt:

```text
.agent/harness/runs/decision-c-lite-final-20260822/receipt.json
```

Receipt status was `passed` with `fresh=true`, `snapshot_matches=true`,
`scope_worktree_clean=true`, and `workspace_stable=true`. It ran Playbook tests,
proposal/comparison tests, architecture isolation tests, docs contract validation, and
the task Architecture Gate.

The shared checkout still contains unrelated dirty/staged work. Therefore this note does
not claim that the entire shared checkout's current Architecture Gate is green.

## Pilot And Stage 3 Gate

Run a 20–50 Shot shadow Pilot. For each Shot, record at minimum:

```text
selected playbook
agent proposed strategy
current planner strategy
comparison result and reason codes
final human or Production selection
provider
result
human quality result
retry count
manual intervention
```

Reuse an existing Quality Intelligence exact-record pointer/hash when useful. Do not add
a new database for this Pilot.

Only consider Stage 3 when fixed-rubric evidence shows one or more of:

- proposal improves outcomes;
- proposal finds a repeatable Planner blind spot;
- a Playbook is repeatedly reused;
- Playbook fields become stable;
- shadow disagreement correlates with real quality outcomes.

## Keep Deferred

The following are intentionally deferred until Pilot evidence justifies them:

- Product Planning Validator;
- Planner schema or semantic-hash integration;
- proposal identity/staleness rules;
- formal `CompositionSkillLibrary`;
- `ExecutionTrace` runtime;
- Promotion Gate implementation;
- Skill Evolution;
- Agent proposal as a canonical Production decision input.

## Publication State

The implementation remains local on `main`. No push or release was performed. This file
is a durable recap and scheduling note; it is not a new Product Runtime specification or
state owner.
