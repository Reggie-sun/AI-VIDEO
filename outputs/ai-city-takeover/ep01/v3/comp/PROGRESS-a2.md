# IRIS EP01 v3 · animatic a2 · progress (handoff file)

Task: revise the full-length animatic to a2 per `../animatic-spec.md` section "a2 修订" and
`../../reviews/2026-11-04-codex-animatic-a1-review.md`. Work from the repository root (never `cd` into subfolders).

Write scope: `ep01/v3/comp/`, `ep01/v3/renders/`, `ep01/v3/review/`, `ep01/v3/qa/animatic-a2/` only.
Never touch: `motion-kit/`, `ep01/v2/`, `src/ai_video/`, `tests/`, `shots-map.json`, `animatic-spec.md`, `ep01/v3/build_*.py`,
`.env`. No generation, no paid services, no git add/commit/push. a1 outputs stay as they are
(`renders/IRIS-EP01-v3-animatic-a1*.mp4`, `review/animatic-a1.html`, `review/thumbs/frames/`, `qa/animatic-a1/`).

## Status

- [x] 1. build.py for board v2-a2 (chrome, plate luminance, lights-off plates, wall, cue rule, narrow face)
- [x] 2. engine: chrome layer, typography roles, new components, fixes
- [x] 3. still checks (snap.mjs) of every unit type
- [x] 4. three sample renders (0-12, 44-60, 205-226 s) + frame checks
- [x] 5. full render a2 + CRF 20 proxy
- [x] 6. review page animatic-a2.html
- [x] 7. QA qa/animatic-a2
- [x] 8. review-notes.json for a2

## Commands (from the repo root)

```bash
# build (data, plates, fonts, engine.js, index.html, sample pages)
uv run python outputs/ai-city-takeover/ep01/v3/comp/build.py --samples 0:12,44:60,205:226
# quick stills without a render (dev check)
node outputs/ai-city-takeover/ep01/v3/comp/snap.mjs --out /tmp/iris-a2-snaps --t 5.5,7.0 [--gpu]
# sample renders
npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v3/comp -c sample-0000-0012.html \
  -o outputs/ai-city-takeover/ep01/v3/renders/samples/IRIS-EP01-v3-a2-sample-0000-0012.mp4 -f 30 -w 4 --browser-gpu --quality high
# full render (about 10 min on this machine for a1)
npx --no-install hyperframes render outputs/ai-city-takeover/ep01/v3/comp \
  -o outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a2.mp4 -f 30 -w 4 --browser-gpu --quality high
# review proxy (CRF 20), page, QA
ffmpeg -y -i outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a2.mp4 -c:v libx264 -crf 20 -preset medium \
  -pix_fmt yuv420p -c:a copy -movflags +faststart outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a2-review.mp4
uv run python outputs/ai-city-takeover/ep01/v3/comp/review.py \
  --video /home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a2-review.mp4 \
  --out /home/reggie/vscode_folder/AI-VIDEO/outputs/ai-city-takeover/ep01/v3/review/animatic-a2.html
uv run python motion-kit/tools/qa.py --video outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a2.mp4 \
  --comp outputs/ai-city-takeover/ep01/v3/comp --dur 261.56 --out outputs/ai-city-takeover/ep01/v3/qa/animatic-a2
```

## Log

- 2026-11-04: read spec, Codex review, a1 project, new map (84 units, chrome) and words.json; plan written.
- 2026-11-04 (successor executor, after the 03:27 account cut): re-read spec a2, review, all of comp/ and the map.
  Step 1 check of build.py against the spec: board check, chrome resolved to frames (counter f2773, top_right f7496),
  dim/no-ticker flags, plate luminance zones (only P-lab-terminals-a is light), wall list, narrow face (MK-Narrow-Bold
  in fonts.json), CJK guard: present and right. words.json: same 47 lines and texts as words-ctc-v1, only lines 43/44
  moved (line 43 ends 211.85, line 44 starts 222.44), so lyric.js KEYS line indices stay valid.
  Problems found: (1) P-dark-hall-b--off is damaged: its `led` anchor sits on the collar glow (no ear device at that
  scale), so lights_off drew a dark lens disc and a straight dark strip on the collar, and the red spill on the
  shoulder stayed (r-max(g,b) up to 32 at 26-45 px). P-row-lit-a--off is clean (no px with r-max(g,b) > 4 within 80 px
  of the collar; LED core filled, dark lens). (2) U083 cue = first hit 256.27 s (3.8 s into the card): the card
  timing must not use u.cue. (3) wall: 5 of the 9 stills have no face anchor (boxes need one). (4) the engine
  (src/*.js) is still a1: nothing uses u.off, chrome, the new components or the a2 type roles yet.
- 2026-11-04 step 1 done: lights_off() rewritten (channel model: inside a 40 px collar band / 30 px LED disc,
  feathered 12 px, R is capped at the red its own G,B predict from a fit on the unlit ring; the light's hot core
  (r-max(g,b) > 30) takes the cloth's cool grey x0.8; a white-hot LED core is filled from the device). Verified on
  both --off plates: no px with r-max(g,b) > 4 within 52 px of the collar; the LED disc keeps only ear skin (max 8);
  every px outside the zones byte-identical to the still; crops look like an unlit strip / dark lens, no drawn
  artifacts (/tmp/iris-a2/proto/*-cmp3.png, scratch). Build: 12 s, 84 units, 7847 frames, 49 plates, no placeholders;
  unhandled graphics = the four new a2 components (engine step 2).
- 2026-11-04 step 2 done (engine, src/*.js; build 12 s, unhandled graphics none):
  new src/chrome.js (corner crosses, top-left IRIS · EP01 + DAY counter, top-right title + IRIS CLOCK, bottom ticker via
  motion-kit hud.js drawTicker at 90 px/s = 3 px/frame; MK Mono SC 15 px (caps 11 px) tracking 3 - IBM Plex Mono is not
  installed; light ink + 3 px shadow on dark, dark ink + pale pill on light grounds (P-lab-terminals-a, U070 white
  panel); 40% in dim units; no ticker in U083; switches are plain cuts: a flap showed made-up digits like DAY 76).
  main.js: lights-off still (u.off) whenever lights.js lightOn() is false (camera/anchors keep the base still); light
  ground = u.light or plates.json light; chrome drawn last on the overlay. util.js: OSD_IN = 72, NARROW, boardText /
  boardCaption. osd.js: OSD frame, label, clock, status row moved inside OSD_IN (they collided with the chrome rows and
  the ticker); camLabel takes graphic_text when it names a camera (U069 CAM 07); monitor wall 3x480x270 inside the
  frame, boxes lock one per half beat in order 4,0,8,2,6,1,7,3,5 from t0+0.3. anchors.js: face boxes for P-door-latch-a,
  P-headturn-b, P-spotlight-low-a, P-catwalk-b, P-hairflip-a (wall). lyric.js roles: headline = lyric_word on a unit
  with a still (Grotesk 88 px, caps 63, one row, faint->lit per CTC word, key red, x 76 / inside the OSD frame on
  system units); small = lyric_word on graphic units; stack = c15 + a long (>= 0.8 s) key word at the line end on its
  own row in MK Narrow Bold 190 px red (U022/U027/U044/U048/U072); chant = MK Narrow Bold caps 260 px, slam + kick
  pulse; whisper/tiny/flip unchanged; dark ink and no scrim on light grounds. boards.js: flip clock intro settles all
  digits together >= 0.2 s before the cue, the changed digit flips on the cue frame (settle 1), caption IRIS CLOCK
  under the board; photo flip: the new top shows on the switch frame, the bottom swings over 4 frames; flip wall 6
  rows above the chant word. labels.js: fact card = 4 lines, one per beat from t0+0.2, fact lines wrapped at 62 chars
  (mono 30 px), SOURCES 22 px dim, all up ~1.9 s after the cut, held ~3.8 s; red-team label mono bold 52 px (caps 38)
  steel tick; cache tags kept clear of the chrome. charts.js: nodegraph_control_gap (U013), nodegraph_single_endpoint
  (U017), timing-chart title mono bold 44 px (caps 32). lights.js: lightOn, spotlight_flicker (2 frames at gain 0.16,
  then over-bright decay), fade_out_end (uFade over the last 0.8 s; last frame black).
- 2026-11-04 step 3 done: ~170 snap.mjs stills (/tmp/iris-a2/snaps, scratch) over all 84 units. Seen: chrome on every
  unit type and readable at 1:1; OSD only on system units; no Chinese; U002 lit collar/LED only from frame 200 (6.667 s;
  before: max r-max(g,b) 25 = her lips), flicker on 200-201, 205-206, >= 209; U004 board with IRIS CLOCK; U013/U017 diagrams as specified; lab units dark ink, no red (labels steel, stamp dark steel); U053 two inverted
  frames 4889-4890 with dark chrome; U056 flips; U073 nine stills, boxes locking; U074 dip on frame 6570; U083 card 4
  lines held; U084 red only from the cue, black last frame. Known: CA fringes give r-max(g,b) up to ~96 on OSD text and
  rim edges in the corners of system units (print-grade CA, a1 too); rack status LEDs in some stills are small red dots.
- 2026-11-04 step 4 done: samples renders/samples/IRIS-EP01-v3-a2-sample-0000-0012.mp4 (33 s render, 360 frames),
  -0044-0060 (42 s, 480), -0205-0226 (58 s, 630); exact frames pulled with /tmp/iris-a2/frames_at.py. Found and fixed:
  on U004's cue frame the one-tick flap showed a random digit that read 03:48 (made-up time) -> one-step board changes
  are now hard (flip clock and day calendar), chrome switches too. Re-rendered sample 1 (33 s): whole-frame diff is flat
  on frames 298-303 and changes only on 304 (cue, 03:47), so qa.py's onset lands on the cue. Seen on sample frames:
  chrome on every unit, OSD only on U001/U003 (system), U002 no red before frame 200 (max r-max(g,b) 19 = lips) then
  lit; U017 line reaches EXTERNAL CHATBOT, LIMITED; U018 punch; U020 tiny whisper + switch at 58.233; U070 white
  panel dark chrome; U072 narrow OUTSIDE + switch at 211.067; nothing sung 212.30-222.44 (line 43 hold ends 212.30);
  U073 nine stills locking; U074 dip on 219.000-219.033; U076 headline in the CITY CAM frame. Not in a sample window
  (checked on snaps only): U013, U036-U040, U083, U084.
- 2026-11-04 04:31 step 5 started: full render (command above, -w 4 --browser-gpu --quality high) of the build after the
  U004 fix; review-notes draft for step 8 kept at /tmp/iris-a2/review-notes-draft.json (scratch; if lost, rewrite from
  this log). review.py now takes the label from --out (animatic-a2.html -> thumbs-a2/), a1 keeps thumbs/.
- 2026-11-04 step 5 done: full render 04:31-04:42 (697 s): renders/IRIS-EP01-v3-animatic-a2.mp4, 1920x1080, 30 fps,
  7847 frames, 261.588 s container, 1,944,661,119 bytes, SHA-256
  e487ab57d0a733a29647a43861207e75532b94c5ffbd5482a4c5670b59b5bca5. Proxy (CRF 20, 107 s):
  renders/IRIS-EP01-v3-animatic-a2-review.mp4, 408,562,039 bytes, SHA-256
  91ebc2a38be95b20fa779afbb6283d421457436880594ecfa54136c0c3fb5f50. Audio: the AAC stream of master and proxy is
  byte-identical to a1's (stream MD5 41ec48c6...) = the T4 master as HyperFrames encodes it; correlation with the WAV
  0.998. Frame checks on the master (exact frames): U002 no red before frame 200, lit on 200; U004 03:46 on 303 /
  03:47 on 304; U013 boundary, red resolver, MISCONFIGURED; DAY counter 11 from frame 2773; red-team units max
  r-max(g,b) 7; U053 inverted on 4889-4890; U056 switch frame shows the new top half; U073 wall; U082 03:47 on 7495 /
  03:48 on 7496 (chrome switches the same frame); U083 four lines readable at 1:1 (mono 30 px), held to 258.13;
  U084 unlit 7771, lit 7772; last frame black.
- 2026-11-04 step 7 done (157 s): qa/animatic-a2/report.md: verdicts all True; 100/100 sync events PASS (U004, U053,
  U056 x2 now 0 frames; cut_U083 and U001_cue +1); flash max 1/s; no pops, strobes or outliers.
- 2026-11-04 step 8 done: comp/review-notes.json rewritten for a2 (what it is, files + SHA, QA, changes vs a1, component
  status, known problems, how to view; no placeholder text).
- 2026-11-04 step 6 done (11 s): review.py --video <abs proxy> --out <abs>/review/animatic-a2.html -> page + its own
  review/thumbs-a2/{frames,plates} (84 + 47); a1 page and review/thumbs/ untouched. Headless Chrome check: 84 rows,
  164 images all load, video duration 261.567, a click on U083 seeks and plays; the a1 page still loads (85 rows, no
  broken images).

## a2.1 (fix batch after the user's approval of a2 at checkpoint B)

Task (team lead, 2026-11-04): (1) U012 lyric shows "One D N S resolver": join runs of >= 2 single capital-letter CTC
tokens into one display word (DNS), lit from the first letter's start to the last letter's end, in every lyric role;
words.json stays as it is. (2) map chrome.top_right is now 03:46 from 0.0 s, 03:47 from 10.133 s, 03:48 from
249.85 s: rebuild, the 03:47 switch must land on frame 304 (U004's board) and 03:48 on 7496. (3) U084: the OSD REC
dot grey for the whole unit (the only red: her light at the cue); other system units keep a red dot.
Outputs: renders/IRIS-EP01-v3-animatic-a2.1.mp4 + -a2.1-review.mp4 (CRF 20), qa/animatic-a2.1, review/animatic-a2.1.html
(own thumbs), an a2.1 section in comp/review-notes.json. Every a2 output stays untouched: SHA-256 of all 143 a2 files
(renders a2 + samples, review/animatic-a2.html, review/thumbs-a2, qa/animatic-a2) saved in /tmp/iris-a2/a2-guard.txt
(scratch) to re-check at the end.

- [x] 1. lyric.js: letter runs joined (DNS)
- [x] 2. rebuild with the new map; clock switch frames 304 / 7496
- [x] 3. osd.js: REC dot grey in U084
- [x] 4. snap checks U001-U004, U012, U084
- [x] 5. full render a2.1 + proxy
- [x] 6. QA qa/animatic-a2.1
- [x] 7. review page animatic-a2.1.html + review-notes a2.1 section
- [x] 8. a2 outputs re-checked untouched

Log a2.1:
- 2026-11-04: map now sha256 3c3a14a8e2ddd5c6... (board still v2-a2, 84 units); only one letter run in words.json
  (line 4 "D N S"); "A" and "I" only stand alone, never next to another single capital.
- step 1: lyric.js spelled(): a run of >= 2 tokens matching /^[A-Z][^\w\s]*$/ becomes one word (letters joined, the
  last letter's trailing punctuation kept), start = first letter's start, end = last letter's end; applied in segsOf, so
  every role (headline, small, stack, chant, flip) gets it. Checked with node on line 4: One | DNS 35.01-35.59 |
  resolver, ; a lone I stays.
- step 2: build (12 s, map sha 3c3a14a8...): chrome topRight frames 0 (03:46), 304 (03:47), 7496 (03:48); U004 cue
  frame 304, U082 cue frame 7496. 84 units, 49 plates, no placeholders, no unhandled graphics. (Built without
  --samples: the sample-*.html pages are gone from comp/; the a2 sample MP4s are untouched.)
- step 3: osd.js recColor: grey (150,156,162) also for a unit with light_flicker_on (only U084 among system units).
- step 4 (snap.mjs): top-right tag 03:46 on frames 60, 180, 255, 303; 03:47 on 304, 330. U012: "One DNS resolver",
  DNS faint on 1047, lit on 1056, resolver lit on 1080. U084: REC dot centre (140,140,142) grey on 7746, 7758, 7771,
  7772, 7800, 7830 (a2: (180,30,15) red); her light off on 7771, on from 7772. Left: the system look's chromatic
  aberration gives a 1-px warm/blue fringe round the grey dot and the white OSD type in the corners (r-max(g,b) up to
  ~60-96 on single edge pixels, also in every other system unit); not touched (outside the three fixes). Other system
  units keep the red dot (U001 frame 60: red).
- step 5: full render 17:09-17:23 (843 s): renders/IRIS-EP01-v3-animatic-a2.1.mp4, 7847 frames, 1,944,655,720 B,
  SHA-256 c3fb2aefc39730442e1f248b910ef061095e6e73bb8c63a5dcb7c7c18bacd2c9; proxy CRF 20 (141 s)
  renders/IRIS-EP01-v3-animatic-a2.1-review.mp4, 408,547,078 B, SHA-256
  1a050aa67b0a9a8917682b963e680e2be9de08844215f1a1f4d1b8f26cc68f0c. Audio stream MD5 41ec48c6... = a2 = a1.
  Master frames: tag 03:46 on 60/303, 03:47 on 304..7495, 03:48 from 7496; U012 DNS faint 1047, lit 1056, resolver lit
  1080; U084 REC dot grey (centre ~(140,145,137) after 4:2:0), no px with r-max(g,b) > 100 on 7758/7771, her light from
  7772; U001 dot still red. a2 vs a2.1 decoded frame diff (480x270 gray, > 12 levels): only frames 0-303 (tag digit),
  1042-1094 (U012 lyric box), 7764-7789 and 7811-7835 (REC dot), plus single-pixel encoder noise.
- step 6: QA (193 s) qa/animatic-a2.1: verdicts all True, 100/100 PASS (cut_U083, U001_cue +1), flash max 1/s, no pops,
  strobes or outliers.
- step 7: review-notes.json: new first section "a2.1 修订" (files + SHA, the three fixes, diff vs a2, QA); a2 sections
  kept as they were. review.py label pattern now takes dots (animatic-a2.1 -> thumbs-a2.1; before, \w+ would have
  fallen back to a1 and written into review/thumbs). review/animatic-a2.1.html (12 s) + review/thumbs-a2.1 (84 + 47);
  headless Chrome: 84 rows, 164 images, video 261.567 s, U083 click seeks and plays; a2 page still fine.
- step 8: all 143 a2 files byte-identical to the guard list; a1 files untouched; no render leftovers. (A
  docs/record_for_agent/2026-11-04-shizhen-dispatch-master-reference-preview.md changed at 17:31 is another session's
  file, not written here.)
