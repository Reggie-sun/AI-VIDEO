---
name: seedance-authoring
description: Use when an approved AI-VIDEO Shot and preselected Seedance target need prompt and reference authoring or creative repair; consumes exact version, mode, runtime surface, and semantic reference roles without owning runtime dispatch or production state.
---

# Seedance Authoring

Adapt an already-approved AI-VIDEO Shot into Seedance-facing authoring guidance. This Skill is
an Agent-side prompt/reference specialist, not a Seedance workflow, router, Provider adapter, or
validator.

## Trigger Boundary

Use this Skill only when all of these inputs exist:

- an approved AI-VIDEO `Shot Contract` or exact equivalent creative contract;
- an exact selected Seedance model/profile identity and its version family (`2.0` or `2.5`);
- a preselected generation mode and current runtime/provider surface;
- semantic reference roles and transfer intent for every supplied asset.

Route elsewhere first when the missing concern belongs to another owner:

- concept, coverage, or ordered multi-Shot design -> `open-video`;
- semantic open/close state or cross-Shot continuity -> `hell-grind-aigc-skill`;
- a non-Seedance generative target -> `higgsfield`;
- deterministic motion graphics, pacing, or composition -> `video-shotcraft`;
- capability selection, execution, activation, or QA -> current AI-VIDEO code and contracts.

Do not guess a version, mode, surface, asset identity, or reference job. If an input is unknown,
future, mixed, or stale, fail closed and report the missing deterministic selection.

## Progressive Loading

1. Load `references/authoring-common.md` for shared prompt and reference-role knowledge.
2. Load exactly one version overlay:
   - selected Seedance 2.0 family (including an exact Mini/variant profile) ->
     `references/seedance-2.0.md`;
   - selected Seedance 2.5 -> `references/seedance-2.5.md`.
3. Never merge both overlays. Seedance 1.5/1.0 are intentionally unsupported in this first
   authoring package and MUST NOT inherit 2.0 guidance. For any other or ambiguous version, stop
   and request a current AI-VIDEO capability/profile decision.

Runtime or surface facts from the current AI-VIDEO capability registry and selected profile win
over these authoring references. Community observations are hints only.

## Mode Profile

Consume, but do not independently select, one mode profile:

| Profile | Authoring concern |
| --- | --- |
| `T2V` | Express the approved Shot without invented asset bindings. |
| `I2V` | State what the first-frame image anchors and what may change. |
| `R2V` | Give every image/video/audio reference one explicit semantic job. |
| `FLF2V` | Treat first and last frames as start/end constraints, not two generic references. |
| `edit` | Name the exact operation and protected source properties. |
| `extend` | Continue from the accepted observed source state and specify the new beat. |

These are mode profiles, not separate Skills. MUST NOT dispatch a mode-specific Skill or invent a
new provider mode token. Exact mode support, role cardinality, and transport mapping remain
deterministic runtime facts.

## Authoring Procedure

1. Echo the exact selected model/profile identity, version family, mode, surface, Shot identity,
   and supplied semantic roles. Mark any missing field instead of filling it heuristically.
2. Build a reference-role map. For each input, preserve its existing identity and state:
   `primary_role`, allowed `transfers`, and `must_not_transfer` constraints.
3. Draft the prompt from the approved Shot: subject, visible action, scene, spatial relation,
   camera, lighting, audio intent, chronology, and negative constraints. Do not add new story or
   continuity facts.
4. Apply only the selected version overlay. Separate authoring advice from current runtime facts
   and empirical/community observations.
5. Check prompt/reference consistency: every mentioned reference exists, each asset has one clear
   job, edit/extend uses direct operation wording, event density fits the selected duration, and
   no transfer rule contradicts the Shot.
6. Return the advisory result to the existing AI-VIDEO workflow. Never execute it directly.

## Output

Return a concise advisory package, not a new durable schema:

```text
selected_profile: <exact model/profile identity + version family + mode + runtime surface echoed from input>
prompt_draft: <Seedance-facing authoring draft>
reference_roles:
  - <existing asset identity>: <primary role; transfers; must_not_transfer>
authoring_warnings: <ambiguity, unsupported expression, or evidence limits>
repair_note: <one isolated authoring change when diagnosing a failed result>
runtime_handoff: <facts the existing capability/provider path must validate>
```

## Troubleshooting Dispatch

This Skill may diagnose prompt ambiguity, conflicting reference jobs, excessive event density,
or wording that fails to express the approved Shot. Repair one authoring variable at a time and
compare against the accepted observed result.

Runtime/API/ComfyUI/node/credential/budget/egress/task/container errors belong to the selected
AI-VIDEO Provider adapter and typed failure path. Cross-Shot identity/state/axis problems belong
to the continuity engine and review gates. Do not relabel those failures as prompt failures.

## Authority Boundary

- `runtime_skill_calls = 0`; `src/ai_video/**` MUST NOT import or invoke this Skill.
- The AI-VIDEO capability registry owns exact model/version/mode support and parameter limits.
- The AI-VIDEO `Shot Contract` owns creative and continuity intent.
- The selected `Provider adapter` owns native request expression and transport validation.
- `ProductionStateCommitter` owns lifecycle mutation, activation, and recovery.
- The continuity engine and P6 review owners decide evidence-backed continuity/quality outcomes.
- The Harness owns changed-path verification and receipts.
- MUST NOT select a Provider or create a second router/capability registry.
- MUST NOT submit, poll, fetch, retry, or recover a generation task.
- MUST NOT create an asset manifest, duplicate Registry identity, or compile provider transport
  tags as durable truth.
- MUST NOT activate or accept media, write Manifest state, issue P6 / Final Acceptance, or claim
  empirical quality from static authoring checks.
