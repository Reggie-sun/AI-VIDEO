# Shared Seedance Authoring Knowledge

This file contains version-portable authoring guidance. It does not define runtime capability,
provider parameters, asset identity, production validation, or lifecycle state.

## Evidence Order

When facts conflict, preserve their authority instead of blending them:

1. Approved AI-VIDEO Character / Scene / Shot facts own creative intent.
2. Current AI-VIDEO capability/profile and selected adapter own executable support and surface
   semantics.
3. Official model guidance may inform authoring language for the exact selected version.
4. Community recipes and observed heuristics remain advisory and must be labelled as such.

Never promote a successful lint, an upstream template, or one observed clip into current runtime
or Production acceptance truth.

## Prompt Grammar

Write in observable terms and keep the chronology readable:

```text
subject and stable identity
-> visible action and state change
-> scene and spatial relations
-> one primary camera treatment
-> lighting and visual treatment
-> audible action / dialogue / ambience when required
-> constraints and protected properties
```

- Describe what can be seen or heard. Do not replace actions with mood labels.
- Keep one primary camera intent per Shot unless the approved Shot explicitly contains a cut.
- Order events as start state -> action -> resulting state. Reduce event density when the selected
  duration cannot express every beat clearly.
- Preserve approved names, appearance, wardrobe, objects, screen axis, direction, and causal
  anchors. Do not invent missing story facts.
- Treat audio as authoring intent only. Exact native-audio support and final mix ownership remain
  current AI-VIDEO runtime facts.

## Reference Role Map

Every supplied asset needs one primary semantic job before it appears in the prompt:

| Role | Authoring meaning | Typical protection |
| --- | --- | --- |
| `first_frame` | Exact visual start state for I2V/FLF2V. | Preserve anchored identity, composition, and starting state unless the Shot changes them. |
| `last_frame` | Exact intended endpoint for FLF2V. | Preserve endpoint identity/state; do not describe it as a generic style image. |
| `reference_image` | Identity, object, scene, or style evidence that is not the start frame. | Transfer only the named properties. |
| `motion reference` | Action rhythm, camera path, physical motion, or timing example. | Do not transfer identity, wardrobe, location, or audio unless explicitly authorized. |
| `reference_video` | Motion/style/source video for R2V, edit, or extend. | State the operation and protected source properties. |
| `reference_audio` | Voice, dialogue, ambience, music, or timing evidence. | Transfer only the named audio property; do not infer visual identity. |

For each asset, record:

- `primary_role`: exactly one dominant job;
- `transfers`: properties the prompt is allowed to inherit;
- `must_not_transfer`: properties that must remain excluded;
- `target`: the approved subject, object, scene, action, camera, or audio intent receiving the
  transfer.

`must_not_transfer` is required whenever a reference contains salient but unwanted identity,
wardrobe, location, composition, motion, text, branding, or audio. If one asset is asked to do
conflicting jobs, split the intent or return an ambiguity instead of silently merging roles.

## Mode-Specific Expression

- `T2V`: use no implicit asset binding.
- `I2V`: say what `first_frame` anchors and describe the permitted change from it.
- `FLF2V`: distinguish the starting `first_frame` from the endpoint `last_frame`; do not call both
  generic references.
- `R2V`: name the job of every image, video, and audio reference in prose.
- `edit`: use direct operation wording such as replace, remove, preserve, recolor, relight, or
  restage, plus the exact protected properties.
- `extend`: use direct operation wording, begin from the accepted observed state of the exact
  source output, then describe only the continuation beat. A prior prompt is not evidence of the
  actual source endpoint.

## Authoring Consistency Check

Before handoff, confirm:

- every referenced asset is present in the input contract;
- first/last/reference roles are not conflated;
- every transfer and `must_not_transfer` rule is traceable to approved intent;
- prompt chronology has no impossible overlap or contradictory state;
- edit/extend states the operation directly;
- runtime limits, file formats, reference counts, mode tokens, and node/API fields are not guessed;
- any community-derived heuristic is marked advisory.

This is an authoring check only. It is not a provider validator, continuity verdict, media lint,
Harness receipt, or Production acceptance gate.
