# Seedance 2.0 Authoring Overlay

This is an authoring-only overlay. The current AI-VIDEO capability/profile and selected adapter
remain authoritative for exact support, limits, modes, and surface behavior.

## Use This Dialect

- Prefer a clear visual sequence over dense timestamp choreography. Official 2.0 guidance has
  cautioned that precise timing may not be reliably followed; use relative beats unless the exact
  selected surface has current evidence for stronger control.
- Bind each supplied image/video/audio reference to one semantic job and state what must remain
  unchanged. Do not assume reference ordering alone communicates the job.
- For first/last-frame authoring, describe the start state, permitted transition, and endpoint
  state. Do not introduce a second continuity story between those endpoints.
- For edit or extend, name the operation directly and protect source properties that must survive.
  Only use those profiles when the current runtime selection already supports them.
- Treat native audio, reference ceilings, duration, resolution, file format, and surface syntax as
  current runtime facts; never infer them from the `2.0` label.

## Repair Bias

When a result misses intent, first reduce competing actions, clarify the reference job, or replace
fragile clock-time wording with ordered relative beats. Change one authoring variable per retry
proposal and compare with the exact accepted/failed output evidence.

## Source Boundary

- Official model overview: <https://seed.bytedance.com/en/seedance2_0>
- Current API/runtime facts must be reopened from AI-VIDEO code, sealed profiles, and the selected
  surface before execution.
- Community prompt recipes are useful vocabulary, not proof of capability or quality.
