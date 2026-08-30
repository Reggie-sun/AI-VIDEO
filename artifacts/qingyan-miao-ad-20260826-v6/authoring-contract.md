# Authoring Contract V6

## Human Failure Correction

- V5 remains `HUMAN_VISUAL_FAIL` for opening seam, product duplication and still-image jitter.
- Remove the old `02_product_lift` segment entirely. Do not present an empty-hand close state and
  a product-in-hand open state as one continuous action.
- The presenter Shot may contain the generated bottle in her hands, but no source-packshot overlay
  may share that frame.
- The source packshot appears exactly once, in the dedicated product hero segment. The end card is
  text-only.
- Remove every `zoompan`, sinusoidal crop and artificial still-image motion. Product and text pixels
  remain geometrically fixed; only large background light bands may move once in a single direction.
- Do not cross-dissolve two different human poses. Every change of state passes through a brief
  white graphic endpoint, with no double-exposed face, hand or product state.

## Exact Timeline

The ten non-overlapping segments sum directly to `720` frames at `24fps`; there is no overlap,
clone padding or hidden extension.

| Segment | Frames | Time | Product state | Boundary |
| --- | ---: | ---: | --- | --- |
| 01 concern | 48 | 0.000-2.000 | none | fade to white |
| 02 neutral bridge | 24 | 2.000-3.000 | none | white graphic endpoint |
| 03 spoken presenter | 124 | 3.000-8.167 | one generated hand-held bottle; no overlay | fade through white |
| 04 benefit card | 84 | 8.167-11.667 | none | stable graphic |
| 05 walk forward | 56 | 11.667-14.000 | none | fade through white |
| 06 scenario bridge | 36 | 14.000-15.500 | none | stable graphic reset |
| 07 walk smile | 56 | 15.500-17.833 | none | fade through white |
| 08 social turn | 48 | 17.833-19.833 | none | skip the source's initial 8-frame still hold |
| 09 product hero | 144 | 19.833-25.833 | one exact source packshot | dedicated hero |
| 10 text end card | 100 | 25.833-30.000 | none | final brand closure |

Frame identity: `48 + 24 + 124 + 84 + 56 + 36 + 56 + 48 + 144 + 100 = 720`.

## Audio And Copy

- Exact spoken line: `出门前用青颜，抑汗净味，清爽舒适。`
- The native voice starts at exactly `3.000s` and remains the only dialogue.
- Allowed copy remains limited to product name, `抑汗净味`, `清爽舒适`, `帮助减少汗湿困扰`
  and non-absolute lifestyle wording.
- BGM remains beneath the voice; transition SFX never masks the dialogue.

## Acceptance Requirements

- No double-exposed face, hands or product at 1.75-2.25s or 3.75-4.25s.
- No source-packshot overlay in any presenter/live-action segment.
- Exactly one source-packshot presentation window in the final composition.
- No `xfade`, `zoompan`, `tpad`, clone, reverse or duplicated-frame extension in the compositor.
- Exact final: `1080x1920`, `24fps`, `720` frames, 30 seconds.
- Development evidence does not equal P6, Final Acceptance or publication approval.
