# Design QA

**Comparison target**

- Source visual truth: `design/provider-console-source.png`
- Final implementation screenshot: `design/implementation-main-final.png`
- Combined comparison evidence: `design/qa-comparison-final.png`
- Local evidence dialog: `design/implementation-evidence-final.png`
- Cloud gated state: `design/implementation-cloud-gated-final.png`
- Collapsed gates state: `design/implementation-gates-collapsed-final.png`
- Local intent success state: `design/implementation-interactions-final.png`
- Viewport and state: desktop, default Local H3 T8 Quality lane, gates expanded, `1487 × 1058` CSS px, `deviceScaleFactor = 1`
- Pixel normalization: source `1487 × 1058`; implementation `1487 × 1058`; no resizing or density conversion. The combined comparison is `2974 × 1058` with source on the left and implementation on the right.

**Findings**

- No actionable P0, P1, or P2 differences remain.
- Fonts and typography: the implementation uses the available Inter / CJK system stack with matching hierarchy, compact control text, and readable dense metadata. Minor platform rasterization and weight differences are acceptable P3 variation.
- Spacing and layout rhythm: the `160 px` global nav, `260 px` lane rail, project summary, readiness sequence, `352 px` identity column, action row, and other-lane gate panel preserve the source composition. The final `1487 × 1058` render has no document overflow.
- Colors and visual tokens: deep ink surfaces, violet selected/primary states, green readiness, amber authorization, and red blocked states match the source intent. No gradients were introduced.
- Image quality and asset fidelity: the supplied Alice Café image is used for both the project thumbnail and first-frame evidence card with source-appropriate crops. No placeholder image, custom SVG, CSS illustration, emoji, or div art replaces a visible asset.
- Copy and content: all product UI is Simplified Chinese while Provider/model identifiers remain original. The passive/no-network wording is explicit, and no automatic recommendation or fallback is implied.
- Icons: visible controls use one Phosphor icon family with consistent stroke/filled state treatment.
- Accessibility: semantic buttons with pressed state, dialog labeling, visible keyboard focus, a two-control dialog focus trap, Escape-to-close with opener-focus restoration, disabled cloud CTAs, and `prefers-reduced-motion` are present.
- Responsiveness: a second Chrome pass at `1180 × 820` reported `scrollWidth = clientWidth = 1180` and `scrollHeight = clientHeight = 820`; the desktop console remains usable without page-level overflow.

**Interaction and runtime evidence**

- Local Quality → Local Turbo selection: passed.
- Cloud Hailuo selection with non-executable primary CTA: passed.
- Evidence dialog open and Escape close: passed.
- Other-lane gates collapse and re-expand: passed.
- Local primary CTA produces a visible prototype-only intent success state: passed.
- Cloud evidence copy and dialog stay gated/lane-specific instead of showing Local H3 capability: passed.
- Browser console errors: none.
- Page errors: none.
- Failed HTTP responses: none.
- External network requests: none.

**Comparison history**

- Iteration 1 found a source-layout mismatch, cramped stage copy, a React `key` spread warning, a missing intent-success assertion, and a missing favicon response.
- Fixes: rebuilt the page around the source anatomy, removed the `key` spread path, added a local supplied favicon, restored the explicit intent state, and retained only local static behavior.
- Iteration 2 found the project label/title collision and action-note alignment drift.
- Fixes: made the project metadata a real vertical flex group and placed the manual-selection note beneath the primary action.
- Review iteration found insufficient state screenshots, an overly high right-column start, and contradictory Local H3 evidence when a cloud lane was selected.
- Fixes: added state-specific browser captures, aligned the right column with the readiness section, made evidence tone/content lane-specific, and added dialog focus containment/restoration.
- Final evidence: `design/qa-comparison-final.png` shows the corrected default state at equal pixels; the four state screenshots cover dialog, cloud-disabled, gates-collapsed, and local-success views. The final browser pass has no console, page, response, network, or interaction failures.

**Focused region comparison**

- A separate crop was not required because the equal-density combined image keeps the project summary, readiness labels, asset metadata, right-column facts, action controls, and gate rows legible at original height. Relevant non-default regions are captured as full-size, equal-density state screenshots: evidence dialog, cloud gate, collapsed gate panel, and local success.

**Follow-up Polish**

- P3: exact font antialiasing and a few label widths may vary by the user's installed CJK fonts.

final result: passed
