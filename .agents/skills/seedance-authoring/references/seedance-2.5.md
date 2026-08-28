# Seedance 2.5 Authoring Overlay

This is an authoring-only overlay. The current AI-VIDEO capability/profile and selected adapter
remain authoritative for exact support, limits, modes, and surface behavior.

## Use This Dialect

- Complex multi-reference prompts still require explicit roles. Assign identity, scene, style,
  motion, camera, voice, ambience, and edit-source jobs separately; add `must_not_transfer` when a
  reference contains unwanted salient properties.
- Timestamp or interval language may be used only when the exact selected surface and current
  evidence support it. Keep the same event-density discipline; timestamp syntax is an authoring
  aid, not a guarantee that every event will be rendered exactly.
- State edit operations directly, including what changes and what remains protected.
- For extension, begin from the accepted observed source endpoint and specify the next beat; do
  not reconstruct the endpoint from the original prompt.
- Treat audio behavior, reference ceilings, duration, resolution, file format, and surface syntax
  as current runtime facts; never infer them from the `2.5` label.

## Repair Bias

When a result blends references, narrow each asset to one job and strengthen
`must_not_transfer`. When timing drifts, simplify competing beats before adding more timestamps.
Change one authoring variable per retry proposal and bind diagnosis to the exact observed output.

## Source Boundary

- Official model overview: <https://seed.bytedance.com/en/seedance2_5>
- Official launch guidance: <https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5>
- Current API/runtime facts must be reopened from AI-VIDEO code, sealed profiles, and the selected
  surface before execution.
- Community prompt recipes are useful vocabulary, not proof of capability or quality.
