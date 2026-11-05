# FINDINGS: ESCAPE VELOCITY (anabology), author's published production documentation

Scope: claudia.gallery pages saved in this folder (see INDEX.md). Fetched 2026-11-03. Everything below is either a verbatim quote (in quotation marks, with source) or labelled as a gap. No inference is presented as fact. "Source file" names are local files in this folder; the URL for each is in INDEX.md.

Short URL key: R = https://claudia.gallery/record/escape-velocity/readme.md ; SD = .../record/escape-velocity/prompts-seedance.md ; SU = .../record/escape-velocity/prompts-suno.md ; MJ = .../record/escape-velocity/prompts-midjourney.md ; W-motion = https://claudia.gallery/wiki/motion.md ; W-story = .../wiki/storyboard.md ; W-tool = .../wiki/toolkit.md ; W-fmt = .../wiki/formats.md ; W-seed = .../wiki/seedance.md ; W-fail = .../wiki/failures.md ; W-start = .../wiki/start.md ; W-pipe = .../wiki/pipeline.md ; W-song = .../wiki/song.md ; W-mj = .../wiki/midjourney.md ; EV = https://claudia.gallery/escape-velocity.md ; CL = https://claudia.gallery/claudia.md.

Important caveats up front
1. The wiki pages (W-*) cover eight films. Only statements that name ESCAPE VELOCITY are attributed to it below. Where a rule is stated generically (for example the renderer contract in W-tool section 18), the page says it is the toolkit spec, and the EV-specific constants it names are quoted separately.
2. Several published numbers disagree between pages; these are listed in section G.
3. NOT published for EV: the board (`shots.json`), chapter names, the 141-shot list, word-level lyric timestamps, the beat map, the hits file, the edit list, the engine source, the print-pass/halftone shader parameters, the countdown-board code, the Midjourney personal profile code. Section F lists the gaps.

## A. Chapters (9) and shot ranges

NOT PUBLISHED. The 9 chapter names and their shot ranges appear nowhere in the saved documents.

What is stated:
- R: "Three director agents boarded the song independently: fashion film, meme density and narrative. Judges scored them, and a head director merged the best into one board: 141 shots across 9 chapters."
- R: "One animator agent per chapter wrote that chapter's code."
- W-story ("The board review"): "ESCAPE VELOCITY's sheet ran 13 pages of 12 cards, with a cover page showing the chapter map." (the map itself is not published)
- W-fmt (schema): "A chapter is `{id, name, t0, t1, sections, accent, set}`." and the board design list says "**The chapter map:** the song's sections grouped into chapters, each with its set, its light and its accent." (W-story "Design before shots")
- W-story: "Three judges scored the boards, which came in between 70 and 81; the narrative board won." "A head director merged the best of the three and checked the merge itself." "It took about 1.5 hours."
- W-story checks: "the shots tile the song; the cuts land on beats; every line is typed; she is on screen enough; the clips fit the budget and their windows; no image repeats."
- R/W-motion: 40 chapter agent runs: "(40 agent runs, 3,145 tool calls)", "an animator, an art director and a fixer agent per chapter, plus a first attempt that was restarted".

Song sections that ARE published (these are lyric tags, not the 9 chapters). From SU lyrics field tags in order: Intro (spoken) / Verse 1 (spoken, deadpan) / Pre-Chorus (spoken, strings swell) / Chorus (sung, trance lift) / Verse 2 (spoken, deadpan, darker) / Pre-Chorus (spoken, strings higher) / Chorus (sung) / Bridge (spoken, kick and strings only) / Drop (chanted, stacked voices) / Final Chorus (sung, key change up, euphoric) / Outro (spoken, deadpan, music falls away). Mean shot length per section (W-story "Cut rhythm"): intro, no vocal 1.33 s; spoken verse 1.62 s; sung chorus 2.69 s; second verse 2.63 s; bridge 2.25 s ("the countdown"); drop 1.58 s ("plus eighth-note strobes inside shots"); outro 4.40 s ("the ring-out"). Overall: "141 shots in 306 s, mean 2.17 s, median 1.83 s, about one bar at 131.5 BPM."

Known shot-id anchors (storyboard ids tied to song seconds) are in section C table (the only per-shot timecode data published): they cover s001 to s140 sparsely. Note: s140 is the last id mentioned (SD35: "storyboard shots s139, s140"), while the board has 141 shots, so s141 exists but is never referenced.

## B. How specific looks, shots, graphics were made (author statements)

### B1. Look / print pass / halftone
- R step 9: "**v1 to v2.** anabology on v1: "way too.. gray … loses the Midjourney magic." The print pass became a colour halftone."
- R: "Seedance clips made from monochrome start frames had come back grey. They were recoloured with exemplar-based video colourization (Deep Exemplar, CVPR 2019), using each shot's own Midjourney image as the colour exemplar." / "The lesson: keep generation inputs in colour, and apply the look in post."
- W-motion "Colour and texture": "Keep Midjourney's colour. ESCAPE VELOCITY's first cut ran a monochrome xerox look over everything, and the director's note was "way too.. gray … loses the Midjourney magic". The print pass became a colour halftone." and "**ESCAPE VELOCITY:** colour halftone and line screens, grain, dither transitions, misregistration; clay orange `#D97757` as the graphics accent."
- W-fail: "v1 "way too gray … loses the Midjourney magic" | a mono print pass, and chapters desaturating the footage | Colour halftone or native colour; never desaturate the footage."
- W-seed "Inputs": "**Colour in, look in post.** ESCAPE VELOCITY's references were pre-graded to monochrome and 32 of 59 clips came back grey. Generate from the plate's own colour and apply any look in the edit."
- SD header: "`@Image1`: the Midjourney plate for the shot, graded in the video's print look." (so the v1 inputs were pre-graded; conflicts in detail with the v2 "keep inputs in colour" lesson, see G)
- R stack row: "Headless Chromium: canvas plus a WebGL print pass. Every frame is a pure function of time."
- EV (film world text): "Blue-black night and steel blue, one red lamp as the only warm light, a colour halftone over everything, garment tags, split-flap boards and computer-vision boxes tracked to her."
- W-tool 18: "Two canvases. The base holds footage and anything graded with it. The overlay holds type and chrome, composited crisp on top." (generic renderer contract)
- No halftone cell size, angle, screen frequency, dither algorithm, misregistration offset or grain amount is published. Only the accent hex `#D97757` and plate palette `#0f1216` (R typical prompt) are given.

### B2. Countdown board (split-flap)
- EV/R: "A split-flap board counts down "18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS" until it flips to "THERE IS NO UNDERCLASS" and the catwalk lifts off."
- W-story "Design before shots": "ESCAPE VELOCITY: a split-flap board that clatters onto "18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS", and a LOOK counter for the show's looks."
- W-story "The hook": "In ESCAPE VELOCITY's first frame, her face is in a dark back seat with her eyes closed, a red lamp crosses the clay streak, and a full-width split-flap row clatters onto its line and locks on the 1.20 s beat. Her eyes open into the lens on the 1.12 s hit." Also: "ESCAPE VELOCITY's intro cut once per bar: face, scale, profile, destination, a gesture, the arrival."
- W-fmt shot s001 JSON device: `{"kind": "flap", "anchor": {"slot": "bottom"}, "key": "F", "params": {"rows": [{"text": "18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS", "prev": "", "at": 0.0}], "cw": 36, "gap": 3}}` and `"chrome": "the split-flap board across the lower third; clatters from frame 1, settles by 1.5 s"`. Timing key F = "a fixed song time".
- Lyric countdown in SU (the number changes with the choruses): chorus 1 "Eighteen months to escape the underclass", chorus 2 "Six months to escape the underclass", bridge "Permanent underclass: three. Two. One. Zero.", final chorus "Zero months, there is no underclass". W-story cut-rhythm table calls the bridge "the countdown". The exact times the board changes to 6 / 0 / "THERE IS NO UNDERCLASS" on screen are NOT published.
- Plate evidence for the board: MJ `set-splitflap` ("a huge mechanical split-flap departures board hanging in a dark concrete hall, all flaps blank ... room for large typography"), `paper-board` (final shot: "a small black split-flap board with blank flaps alone on a seamless white paper wall"). SD35/SX12 prompts: "beneath the small board on the wall", "toward a small black board on the white wall". The text on boards is drawn in code (W-mj: "every word, title bar, split-flap and label in the films is drawn in code on top of the plate, in real fonts.").
- W-fail: "Tags never finish typing on short shots | the default typing speed | Type at 16-40 characters a second, and finish 6 frames before the cut." (generic)

### B3. HUD / computer-vision boxes
- W-motion: "Computer-vision boxes tracked to her (a real detector's boxes, labels and scores), a P(doom) gauge, a care label, a garment tag with a barcode. Nothing decorative."
- R: "computer-vision boxes tracked to her"; R GPU box row: "object and face tracking (Grounding DINO)"; W-tool 12: "**Boxes:** face and person boxes from Grounding DINO. Graphics anchor to them, and the camera keeps the face in frame through pushes and shakes."
- W-fmt s001 devices: `{"kind": "sheet", "anchor": {"box": "a face"}, "key": "B", "params": {"title": "EXPRESSION · MODEL 01 · LIVE", "rows": [["CALM", ".98"], ["WORRY", ".02"], ["THRESHOLD · WORRY > 0.50", "NOT MET", "hot"]]}}` and `{"kind": "cv.bracket", "anchor": {"box": "a face"}, "key": "B", "params": {"label": "FACE · MODEL 01", "conf": 0.99}}`. Author's explanation: "a face that is not worried under the year's most-quoted threat, and an expression meter that says so in numbers."
- W-story graphics-per-line examples that are EV-specific: "Ladies. Gentlemen. Agents. | a guest list: LADIES 0% · GENTLEMEN 0% · AGENTS 100%, then a front row of open laptops and no people, each detected as AGENT"; "This is not an AI billboard. | a classifier tag on the billboard flips from BILLBOARD · 0.99 to AI BILLBOARD · 0.97 on "billboard""; "+25% = -17% | a bar chart drawn on the beat: the weekly limit falls from 150 to 125, "+25%" is struck through, "= -17%" lands in the accent"; "Sorry. Encore. | an APOLOGY METER · VIA BOW gauge read off her actual bow (0° upright, 30° sorry, 60° deep)"; "Feel the AGI | a seismograph: M 9.0 · "FEEL THE AGI" · OFF SCALE"; "Escape velocity: 11.2 KM/S | Newton's cannonball: falls at 7.0, orbits at 7.9, escapes at 11.2 km/s". (The page lists these as "Line, as read | Its graphic" for several films; these six lines are from EV's lyric, see SU.)
- W-story rules: "It enters on the word that names it." "Counters roll on sixteenths, rows type one per sixteenth, detections land on thirty-seconds, crops cut on eighths." "Use at least six kinds in a film, and never the same kind on three lines in a row."

### B4. Parallax / 2.5D
- R: "2.5D parallax from depth maps"; R GPU row: "depth maps for 2.5D"; R: "It draws 2.5D depth parallax, kinetic lyrics on each word's time, and all the explaining graphics".
- W-motion "Tucks and depth": "**2.5D.** A depth map (Depth Anything V2) separates a still into layers for parallax. Each 2.5D shot needs a treatment of its own; a still with a slow zoom is not a shot."
- W-tool 12: "**Depth:** Depth Anything V2 Small, which is Apache-2.0; the Large model is non-commercial." W-tool 18: "The 64-step parallax shader costs 0.5-1.1 s, and a full-resolution canvas blur about 0.5 s. Use depth slices (about 30 ms) and blur by resampling instead." W-fail: "0.5-1.1 s a frame on 2.5D shots | the 64-step parallax shader | Depth slices or multiplanes." and "Frames differ depending on what rendered before | a WebGL canvas drawn into a 2D canvas switches it to GPU rasterisation | Read 2.5D pixels back through the CPU."
- W-story "What moves": tiers "still", "2.5D", "motion", "sung". "A 2.5D treatment never repeats on two shots in a row. It is never a still with a slow zoom." Director quote: ""that's where we'll have to shine and be creative. depth to separate layers ofc, motion graphics galore, diversity so its not repetitive"." R: director notes "two clips must never start from the same frame, and repetitive 2.5D panels become pure motion design."
- Names/parameters of the individual 2.5D "treatments" used in EV are NOT published (schema field `treatment` is "a 2.5D family").
- These pages say which shots are 2.5D vs clips only indirectly: clips cover 47 shot-groups (section C); everything else is still / 2.5D / pure code. Per-shot tier labels are not published.

### B5. Type modes (subtitle / coverline / masthead / strobe)
- W-tool 18 "Lyric modes" table (renderer contract): "subtitle | sung lines; the sung word lit in the accent"; "coverline | spoken lines set beside her in the plate's empty field, with tracking collapsing word by word"; "masthead | payoff words, numerals, the answer in a call and response"; "stack | short emphatic lines, one word per row"; "mass | a declared wall of micro text in a drop, with the sung line still drawn"; "title | the title knocked out of black".
- "strobe" is NOT a lyric mode in W-tool 18; W-fmt `type.mode` lists "subtitle · coverline · masthead · stack · mass". R says shots carry "a type mode (subtitle, coverline, masthead or strobe)". The only EV-specific strobe statement: W-story cut-rhythm table "drop | 1.58 s | plus eighth-note strobes inside shots". Definition of strobe type mode is a GAP.
- Type rules (generic renderer contract): "One lyric block per frame; a line keeps one mode and one position across cuts." "At least 40 px, and never over her face." "Margins are left 72, top 56, right 96 and bottom 84 at 1920 x 1080." "Hang type from the left axis or from a feature in the frame." "Nothing may cover the lyric: the renderer measures it every frame and moves the other layers off it."
- W-motion (EV-specific): "ESCAPE VELOCITY sets words as subtitles, model cards, garment tags, mastheads and split-flap rows." R: "look cards set as model cards and garment tags".
- Timing: W-tool 18: "A lyric token appears at its aligned start exactly, never snapped to a beat: "the motion syncs to the beat, the word to the voice"." "An entrance takes at most an eighth of a beat." Timing keys W (word), B (beat grid), H (track event), F (fixed song time), T (take-frame keyframe). Lyric gate for EV: "ESCAPE VELOCITY: 417/417." (W-tool 19)
- Display tokens format (W-fmt/W-tool 8): `TEXT|n` shows TEXT for n sung words; markers `*x*` accent, `~x~` strike-through, `_x_` mono. Example `+25%|3 =|1 −17%|2`.
- Fonts: static assets on the site are `dinishcn-900.woff2`, `heros-700.woff2`, `plexmono-500.woff2` (site CSS, not stated as EV's film fonts). W-motion states Nimbus Sans Bold / IBM Plex Mono / DINish Condensed for OTHER films. EV's font list is a GAP; W-fail says "Ship OFL fonts only".

### B6. Camera / beat behaviour (generic renderer contract, W-tool 18; not labelled EV-specific)
"punch on kicks: amp 0.01-0.03, gated by the drum envelope; shake with the drums: none in screen or UI shots; ride a riser into the hit it lands on; impact on real hits: strength at least 0.6, zoom kick 0.06; whip on fills." "Hold still where the song breathes. A move never cuts the face." Density options: "dense: three or more layers, five or six as the norm; budgeted: ...; sparse: ...". EV's chosen density is not stated. W-fail: "Five accent-coloured elements in one frame | ... | The accent goes on at most two elements."

### B7. Her (character) and plates
- R step 4: canon "a black blunt jaw-length bob, one clay-orange streak, an eight-pointed clay spark hair clip, a headset microphone, a white cropped puff-sleeve shirt, a black pleated coated-nylon skirt with a harness belt and a garment tag, and knee boots."
- R: "Midjourney v8.2 has no `--oref`, so identity was tried three ways: GPT-image identity passes, face-sheet image prompts, and plain prompt text. Identity passes drifted ... Face sheets over-conditioned ... **What worked:** the canon written into every prompt, plus an explicit descriptor ("a young Caucasian American woman with pale skin and light freckles"). Without it, Midjourney drifted her ethnicity from shot to shot."
- R plate style words: "the palette and light: "blue-black and steel blue, one small red status lamp as the only warm light""; "the grain: "fine silver grain""; "the finish: "cinematic 35mm film still""; "always: "no text, no letters, no logos"". Parameters "`--ar 16:9 --v 8.2 --raw --hd`" plus the director's personal profile; "A few were image-weighted face-sheet tests (`--iw 0.5`), and one early `--oref` test was rejected by v8.2."
- R: "Every prompt is a concrete scene, usually with a declared empty area for type."
- R counts: "188 prompts in 15 batches; 159 ran to completion, four images each (636 images)." / "130 plates".
- Full identity text and Look 00 wardrobe: CL (claudia.md). Full 188 prompts: MJ. Example of one final-form plate prompt (verbatim, W-fmt s001) is quoted in `wiki_formats.md` lines 193-195.

### B8. Moving shots, lip sync
- See section C for the prompt template and the per-clip table.
- R: "Each clip gets the plate as `@Image1` and the exact window of the vocal as `@Audio1`. The prompt quotes the words sung in that window: `@Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in time: "…"`."
- R: "anabology spotted the key fact: "its perfectly synced while in seedance, but the audio changes when it desyncs." Seedance copies the reference audio into its own soundtrack, and the mouth follows that soundtrack. So a script compares the clip's soundtrack with the real vocal to find the point where it drifts. The edit cuts on the last eighth note before it, and a continuation clip starting from that frame covers the rest."
- R/SD: "About 86% of sung seconds were verified in sync" ; "Cost: about $93 for 91 submissions and 421 seconds of 720p."
- SD header: "Endpoint: **bytedance/seedance-2.5** through OpenRouter, 720p, 16:9, 4-8 s per clip, `generate_audio: true`." "`@Audio1`, for sung shots: the exact window of the vocal it must lip-sync, cut from the song in a word gap. Motion clips get the full mix instead, for timing and energy."
- SD: "**Totals:** 47 storyboard clips (SD = sung or hero shots, SX = extra motion), 30 covers, 7 early tests; 91 submissions, 421 s generated, ≈ $97.28. The dollar figure is the local ledger's estimate; OpenRouter billing was the source of truth, at about $93."
- W-story: "She sings on camera for most sung words, in chains of lip-sync windows. In ESCAPE VELOCITY that was 62% of sung words, plus 17% of spoken words said straight into the lens." "She is on screen at least 70% of the runtime. ESCAPE VELOCITY reached 83%." "ESCAPE VELOCITY planned 47 clips (224 s) and generated 421 s."
- Clean vocal window constants (generic, W-tool 14) and the sync check constants (W-tool 15): 16 kHz mono, 10 ms frames, 1024 FFT, 80 mel bands 50-7,600 Hz; copy if NCC > 0.2; cut on the last eighth at or before `synced_until`; cover window `clamp(ceil(end - start + 0.3), 4, 8)` s; at most two covers per root. W-tool 16 measured: "ESCAPE VELOCITY | 41% of sung takes copied; with covers, about 86% of sung seconds verified".
- W-seed: "**Short prompts copy, long ones re-sing.** A later test on seven singing windows found that prompt length was the biggest lever" (a later test, not EV; EV prompts are the short form shown in SD).
- OpenRouter note: W-seed "**On OpenRouter, a first frame drops the audio.** When a request carries `frame_images`, the audio reference is silently ignored ... Singing windows and covers go in reference mode ... First frames are for motion clips." (EV used OpenRouter; whether EV motion clips used first-frame mode is not stated.)
- Lip-sync fallback conflict: R lists "LatentSync as a lip-sync fallback" and "with LatentSync as the fallback"; W-seed/W-tool say "No lip-sync models ... Sync, LatentSync and Wav2Lip were tried as fallbacks and dropped". See G.

### B9. Song / beat facts
See section E.

### B10. Render / delivery
- R: "7,354 frames at 1920×1080, rendered in about 63 minutes on a 4-core machine, then encoded as a CRF 16 master." W-tool 18: "one frame per 1/24 s", "ESCAPE VELOCITY's 7,354 frames took about 63 minutes with three workers on 4 CPUs; at 1080p one cut's frames take about 9.6 GB." W-motion: "Encode a CRF 16 master tagged BT.709. An untagged stream looks washed out in QuickTime."
- 7,354 frames at 24 fps = 306.4 s (arithmetic check by this researcher: 7354/24 = 306.42; consistent with the published "duration": 306.4 in W-fmt).
- R: "Time: ~19 h from the first message to the v2 master · about 50 messages from anabology". Claude cost: "≈ $626 at API prices, 1.4B tokens" etc. (R "What it cost in Claude tokens").

## C. Seedance prompt template and per-shot prompt-to-timecode mapping

### C1. The EV prompt templates (verbatim from SD)
Sung clip (pattern used by every SD sung clip and cover):
```
@Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in time: "<words>". <framing sentence about the woman from @Image1 and her expression/action>. <camera: Locked camera / very slight push in>, no cuts, no head turns.
```
Real example (SD05): `@Image1 sings @Audio1. She lip-syncs to @Audio1 exactly, every word in time: "Our Waymo just drove into a firework. Are we on fire, dude?". Medium close-up of the woman from @Image1 sitting upright in the back seat of the car, facing the camera, saying the words flatly with no expression. Locked camera, no cuts, no head turns.`

Motion clip pattern (SD03):
`The scene from @Image1, moving in time with @Audio1. <action sentence(s)>. <camera sentence>. No cuts. Her mouth stays closed, face expressionless.`
Some motion clips (SD02) use `@Image1` as the car and `@Image2` as the woman, and no "Her mouth stays closed" tail.

Early tests (SD "Early tests"): test-sing-a: `@Image1 is the young woman with the black bob, the clay-orange streak and the headset microphone. She sings the vocal in @Audio1: her mouth lip-syncs exactly to @Audio1, every syllable and every held vowel in time, her jaw opening wide on the long notes. She sings: "Eighteen months to escape the underclass." Locked medium close-up, she faces the camera with her eyes half closed, no head turns, the camera does not move, the light stays the same.` (This test, per R, is where the method was found; the later `@Image1 sings @Audio1. She lip-syncs ...` form replaced it.)

Generic (all-film) labelled-section template with 【Audio Policy】/【Generation Goal】/... is in W-seed "Template: a singing window" and is NOT what the EV clips used (EV prompts are the short form above). W-seed says the labelled-section structure follows "BytePlus's published Seedance 2.5 prompt guide".

### C2. Per-clip table (generated mechanically from prompts-seedance.md headings, meta lines and quoted words; "Storyboard shots" are the author's ids)
The song start is the Seedance audio window start in song seconds. There is no end time and no word-level timestamp; the quoted words are what the clip's window contains. Clips with empty "quoted words" are motion clips (no lyric in prompt) or the `-ls` entries (which have no prompt text in the source).

| Clip | Song start | Len | Kind | Plate | Storyboard shots | Quoted sung words (verbatim from prompt) |
|---|---|---|---|---|---|---|
| SD01 | 0.00 | 6 | motion | waymo-cu | s001, s003 |  |
| SD02 | 8.30 | 4 | motion | waymo-arrive | s006 |  |
| SD03 | 18.90 | 6 | motion | hall-ms | s011, s013 |  |
| SD04 | 32.95 | 4 | motion | hacker-house | s019 |  |
| SD05 | 56.16 | 4 | sung | waymo-seat | s031 | Our Waymo just drove into a firework. Are we on fire, dude? |
| SD06 | 62.14 | 4 | sung | podcast | s033 | Look six. Like, the singularity. How's the temperature? Mild. |
| SD06-c1 (cover of SD06) | 63.63 | 4 | sung | podcast | s033 | singularity. How's the temperature? Mild. No grades, no tests. |
| SD07 | 80.44 | 5 | sung | hero-walk | s045 | Eighteen months to escape the underclass. Lock in, |
| SD08 | 84.10 | 6 | sung | hero-cu | s046, s048 | Lock in, baby, foot down on the gas. Feel the A G I, feel it |
| SD09 | 89.52 | 5 | sung | hero-profile | s049 | feel it coming fast. Escape velocity... |
| SD09-c1 (cover of SD09) | 91.49 | 4 | sung | hero-profile | s049 | Escape velocity... |
| SD09-c2 (cover of SD09) | 91.49 | 4 | sung | hero-profile | s049 | Escape velocity... |
| SD09-c3 (cover of SD09) | 91.49 | 4 | sung | hero-profile | s049 | Escape velocity... |
| SD09-c4 (cover of SD09) | 91.49 | 4 | sung | hero-profile | s049 | Escape velocity... |
| SD09-ls1 (cover of SD09) | 91.62 | 1.92 | sung |  |  |  |
| SD10 | 93.30 | 5 | motion | hall-turn | s050, s051 |  |
| SD11 | 100.81 | 4 | sung | n-P33~2 | s053 | WE'RE SO BACK! |
| SD12 | 108.06 | 4 | sung | flap-cu-b~1 | s056 | WE'RE SO BACK! Look |
| SD13 | 127.55 | 4 | motion | sheer-walk | s065 |  |
| SD14 | 131.04 | 4 | motion | arena | s067 |  |
| SD15 | 138.41 | 7 | sung | hoodie | s071, s072 | Not A I. S I. It sounds much better. Trust us. Cashmere. |
| SD15-c1 (cover of SD15) | 139.64 | 6 | sung | hoodie | s071, s072 | I. It sounds much better. Trust us. Cashmere. |
| SD16 | 148.95 | 5 | sung | golden-pool | s074 | Lower me into the golden light. |
| SD16-c1 (cover of SD16) | 147.78 | 7 | sung | golden-pool | s074 | seats. Lower me into the golden light. You have six months |
| SD16-c2 (cover of SD16) | 150.54 | 4 | sung | golden-pool | s074 | into the golden light. You have six |
| SD17 | 159.98 | 8 | sung | freeway-dawn | s079, s081 | Six months to escape the underclass. They say hit the brakes, we say hit the gas. Feel the |
| SD17-c1 (cover of SD17) | 161.01 | 4 | sung | freeway-dawn | s079, s081 | months to escape the underclass. They say hit the |
| SD18 | 162.10 | 4 | sung | wind-cu | s080 | escape the underclass. They say hit the brakes, we say |
| SD19 | 167.26 | 4 | sung | n-P58~2 | s083 | Feel the A G I, feel it coming fast. |
| SD20 | 174.39 | 4 | sung | rail-mcu | s086 | WE'RE SO BACK! (It's so |
| SD20-c1 (cover of SD20) | 174.57 | 4 | sung | rail-mcu | s086 | SO BACK! (It's so |
| SD20-c2 (cover of SD20) | 174.57 | 4 | sung | rail-mcu | s086 | SO BACK! (It's so |
| SD20-c3 (cover of SD20) | 174.57 | 4 | sung | rail-mcu | s086 | SO BACK! (It's so |
| SD20-ls1 (cover of SD20) | 174.68 | 3.76 | sung |  |  |  |
| SD21 | 180.23 | 4 | sung | rail-mcu~1 | s088 | WE'RE SO BACK! |
| SD21-c1 (cover of SD21) | 181.62 | 4 | sung | rail-mcu~1 | s088 | SO BACK! Escape velocity: |
| SD22 | 190.40 | 4 | motion | gantries~4 | s092 |  |
| SD23 | 209.94 | 4 | sung | white-mcu | s100 | Did we make it? |
| SD23-c1 (cover of SD23) | 209.21 | 4 | sung | white-mcu | s100 | Did we make it? |
| SD23-c2 (cover of SD23) | 209.21 | 4 | sung | white-mcu | s100 | Did we make it? |
| SD23-c3 (cover of SD23) | 209.21 | 4 | sung | white-mcu | s100 | Did we make it? |
| SD24 | 217.00 | 6 | motion | ramp-white | s103, s104 |  |
| SD25 | 222.78 | 4 | sung | white-cu | s105, s107 | Lock in. Lock in. Feel the A G I. |
| SD25-c1 (cover of SD25) | 219.86 | 6 | sung | white-cu | s105, s107 | Lock in. Lock in. Feel the A |
| SD25-c2 (cover of SD25) | 219.86 | 6 | sung | white-cu | s105, s107 | Lock in. Lock in. Feel the A |
| SD26 | 224.70 | 4 | motion | ramp-white~1 | s108 |  |
| SD27 | 228.61 | 6 | sung | float-ms | s111 | in a datacenter. Lean proofs. Phages. Enzymes. Kidneys. Good boys. |
| SD27-c1 (cover of SD27) | 229.22 | 4 | sung | float-ms | s111 | datacenter. Lean proofs. Phages. Enzymes. Kidneys. |
| SD27-c2 (cover of SD27) | 229.22 | 4 | sung | float-ms | s111 | datacenter. Lean proofs. Phages. Enzymes. Kidneys. |
| SD27-c3 (cover of SD27) | 230.22 | 4 | sung | float-ms | s111 | Lean proofs. Phages. Enzymes. Kidneys. Good boys. |
| SD28 | 239.56 | 6 | sung | float-ms~1 | s116, s118 | We're So Back region. Slash loop: make me happier. Slopacolypse? Not ours. |
| SD29 | 250.30 | 5 | sung | white-cu~3 | s122, s123 | WE'RE SO BACK! WE'RE SO BACK! Zero months, there is no underclass. |
| SD29-c1 (cover of SD29) | 251.65 | 4 | sung | white-cu~3 | s122, s123 | SO BACK! Zero months, there is no underclass. One |
| SD30 | 253.46 | 4 | sung | white-catwalk | s124 | there is no underclass. One year back for every |
| SD30-c1 (cover of SD30) | 253.42 | 4 | sung | white-catwalk | s124 | there is no underclass. One year back for every |
| SD31 | 255.22 | 4 | sung | white-cu~4 | s125 | One year back for every year that passed. Feel the |
| SD31-c1 (cover of SD31) | 254.22 | 5 | sung | white-cu~4 | s125 | underclass. One year back for every year that passed. Feel the |
| SD32 | 260.62 | 4 | sung | white-cu-b | s127 | feel it coming fast. Escape velocity... |
| SD33 | 266.42 | 5 | sung | white-cu-b~1 | s130, s131 | It was never over! WE'RE SO BACK! |
| SD33-c1 (cover of SD33) | 269.87 | 4 | sung | white-cu-b~1 | s130, s131 | BACK! |
| SD33-c2 (cover of SD33) | 266.59 | 4 | sung | white-cu-b~1 | s130, s131 | It was never over! WE'RE SO BACK! |
| SD34 | 283.00 | 8 | sung | tag-to-lens~1 | s137, s138 | Do not iron. Do not nerf. Made in San Francisco. |
| SD34-c1 (cover of SD34) | 287.21 | 4 | sung | tag-to-lens~1 | s137, s138 | Made in San Francisco. |
| SD34-c2 (cover of SD34) | 287.21 | 4 | sung | tag-to-lens~1 | s137, s138 | Made in San Francisco. |
| SD35 | 290.20 | 11 | motion | paper-board~1 | s139, s140 |  |
| SX01 | 50.89 | 4 | motion | billboard-catwalk | s028 |  |
| SX02 | 53.17 | 4 | motion | n-P20~1 | s029 |  |
| SX03 | 54.99 | 4 | motion | mission-fire | s030 |  |
| SX04 | 65.93 | 4 | motion | answer-sheet | s035 |  |
| SX05 | 67.75 | 4 | motion | moat | s036 |  |
| SX06 | 110.42 | 4 | motion | cage | s057 |  |
| SX07 | 120.38 | 4 | motion | envelope-ms | s062 |  |
| SX08 | 124.45 | 4 | motion | leather-jacket | s064 |  |
| SX09 | 194.25 | 4 | motion | gantry2-ms | s093 |  |
| SX10 | 201.00 | 4 | motion | n-P63 | s095 |  |
| SX11 | 231.96 | 4 | motion | dog-walk | s112 |  |
| SX12 | 271.41 | 4 | motion | paper-board | s132 |  |
| test-sing-a | 0.00 | 5 | motion |  |  |  |
| test-sing-b | 0.00 | 5 | motion |  |  |  |
| test-sing-cover | 82.45 | 5 | sung |  |  |  |
| test-sing-ref | 80.54 | 5 | sung |  |  |  |
| test-sing | 0.00 | 5 | motion |  |  |  |
| test-walk | 18.96 | 6 | motion | hall-ms |  |  |
| test-waymo | 0.00 | 5 | motion |  |  |  |

Other per-shot facts from the same sources:
- SD01 (s001, s003, motion, `waymo-cu`) full prompt: "The scene from @Image1, moving in time with @Audio1. Close-up. The woman from @Image1 sits still in the back seat of the moving car at night, eyes closed. A red light slides slowly across her face from left to right. At one second she opens her eyes and looks straight into the lens. At four seconds she turns her head slowly to the side window as a white light sweeps across the glass and her face. The car rocks slightly. Locked camera, very slow push in. No cuts. Her mouth stays closed, face expressionless."
- Shot s001 (W-fmt): t0 0.0, t1 2.111, section "intro", framing CU, clip SD01, plate `waymo-cu`, "motion_tier": "motion", camera "locked, very slow push in (3%)", accent "#D97757".
- Plate-to-shot mapping is published only for the 60 distinct shot ids that appear in the table (counted mechanically from prompts-seedance.md); the other 81 of 141 shots have no published plate or shot-id mapping (MJ gives plate names and batch notes such as "ESCAPE VELOCITY plates from shots.json", never shot ids).
- Pose/camera vocabulary used repeatedly by the author in clip prompts: "Locked camera, no cuts, no head turns."; "very slow push in"; "The camera moves back at her walking speed so she ends at medium shot."; "Her mouth stays closed, face expressionless." (motion); "The camera moves slowly around her by a few degrees."

## D. Lyrics with timestamps

NOT PUBLISHED with word- or line-level timestamps.

Published:
- The full lyric as generated (SU, "Lyrics field (draft 3, as generated)"), section-tagged but untimed. Saved verbatim in prompts-suno.md lines 26-114.
- Partial timing evidence: the Seedance table above (song start of each window plus the words inside it). Example: SD07 starts at 80.44 s with "Eighteen months to escape the underclass. Lock in,"; SD11 at 100.81 s "WE'RE SO BACK!"; SD23 at 209.94 s "Did we make it?"; SD34 at 283.00 s "Do not iron. Do not nerf. Made in San Francisco."; SD29 at 250.30 s "WE'RE SO BACK! WE'RE SO BACK! Zero months, there is no underclass."
- Format of the author's (unpublished) word-timing file, W-fmt "Timed words": `{"words": [{"i": 0, "w": "ladies", "line": 0, "t0": 9.32, "t1": 9.64, "conf": 0.91, "src": "w2v"}], "lines": [{"line": 0, "text": "Ladies. Gentlemen. Agents.", "t0": 9.32, "t1": 10.72}], "gaps": [{"t0": 18.8, "t1": 26.3, "after_word": 12}]}`. The page does not label this as EV's data, but the text, the 18.8 s gap before the SD03 start (18.90) and the beat-map example duration 306.4 match EV. This is an observation, not a stated fact; treat the values as unconfirmed.
- W-start: "In ESCAPE VELOCITY the word "Look" was aligned 2.6 s early, onto a delay throw. Only one chapter's own lyric check caught it." and W-song: "A delay throw got aligned as a word in ESCAPE VELOCITY, 2.6 s early."
- W-tool 5 (forced alignment on EV): "Re-run on ESCAPE VELOCITY, it reproduced the shipped times exactly for 78.6% of words, and within 0.10 s for 92.5%." "Singing aligns worse than speech: mean confidence 0.64 on ESCAPE VELOCITY". Lyric gate result for EV (W-tool 19): "ESCAPE VELOCITY: 417/417."
- Number words / acronym spelling in lyrics field: SU "Numbers and acronyms are spelled out in the lyrics field (A G I, C S I) so Suno pronounces them." Display text on screen differs from the sung spelling via display tokens (e.g. `AGI|3`).

## E. BPM / beat / section facts

- R: "Song 5:06.4 · Suno v6 · 131.5 → 133.9 BPM"; "the song accelerates from 131.5 to 133.9 BPM". SU: "The song accelerates from 131.5 to 133.9 BPM, so the engine always uses the beat map, never a fixed tempo."
- SU style field requested "128 BPM, 4/4" ("fashion show electroclash techno, 128 BPM, 4/4, ..."); the delivered take measured 131.5 to 133.9.
- W-fmt beat map example (not labelled EV): `"duration": 306.4`, tempo `131.55` at t=0 and `131.6` at t=5, "sections" example `{"name": "intro", "t0": 0.0, "t1": 18.96, "energy": 0.31, "bar0": 0, "bar1": 9}`. First beat in the example 0.452; downbeats 0.452, 2.276 (= 1.824 s per bar = 4 beats at 131.6 BPM).
- W-tool 6 (EV-specific parts): "ESCAPE VELOCITY went from 131.5 to 133.9 BPM ... so a fixed grid is more than a beat off by the end." "On ESCAPE VELOCITY the kick vote was split 36% while the chord vote held 77%." (downbeat phase decided by chord vote). Method: onset strength of drum stem, local tempos on 20 s windows every 5 s, beats snapped to drum onsets within ±30 ms.
- W-story hook: first hit at 1.12 s, split-flap row locks "on the 1.20 s beat"; "Every cut lands within 0.03 s of a beat or a declared hit." W-story audit gate "cuts | a cut more than 0.03 s from a beat, and not a declared hit".
- W-story: "1.20 s beat" is the only absolute beat time stated for EV other than the Seedance window starts and the example above.
- Stems: R "Stems (htdemucs)", "beat tracking (librosa), then a fitted map" (SU "After Suno").
- Section order and spoken/sung roles: see section A and SU.
- W-song "Two numbers" scansion/assonance for EV: "ESCAPE VELOCITY | 75 | 39". W-tool 2: "Suno gives each spoken line its own two-bar slot. The line enters on the "and" of beat 2 of the first bar, its last word lands on beat 4 of the second bar ... verse lines 0.8-1.5x, median 1.12" (delivery model "measured by laying ESCAPE VELOCITY's real take, forced-aligned, on its beat map").
- Song structure with times: only the Seedance window starts. No section start times (verse 1, chorus 1, drop, etc.) are published for EV.

## F. Confirmed vs gaps

### Confirmed (author states explicitly; quote + URL above)
1. Film is 5:06 (306.4 s), 141 shots, 9 chapters, lyric video with every word on screen. (R, EV)
2. Tools: Midjourney v8.2 `--raw --hd` + personal profile, Suno v6, Seedance 2.5 via OpenRouter at 720p, custom JS engine in headless Chromium (canvas + WebGL print pass), GPU box tasks (htdemucs, librosa beat map, wav2vec2 forced alignment, depth maps, Grounding DINO, LatentSync listed, Deep Exemplar colourisation). (R)
3. Lyrics full text and Suno style/exclude fields. (SU)
4. All 47 Seedance clip prompts + 30 covers + early tests with song start times and shot ids. (SD)
5. All 188 Midjourney prompts by batch. (MJ)
6. The v1 look (mono xerox) was rejected; v2 = colour halftone; Seedance inputs that were pre-graded mono came back grey (32 of 59 clips) and were recoloured with exemplar-based colourisation. (R, W-motion, W-seed)
7. Type modes list and renderer contract; the countdown board device, CV bracket and expression sheet device for shot s001 with their parameters. (W-tool 18, W-fmt)
8. Beat map drifts 131.5 to 133.9 BPM; engine uses the beat map; every frame is a pure function of song time; 24 fps; 7,354 frames; CRF 16. (R, W-tool 18, W-motion)
9. Cut-rhythm table per section; she is on screen 83%; sings on camera 62% of sung words. (W-story)
10. Lip-sync method: reference audio copied into the soundtrack; detect divergence by spectrogram/NCC; cut on last eighth; cover clip; ~86% of sung seconds verified. (R, W-tool 15-16)

### Gaps (not published for ESCAPE VELOCITY; do not fill by inference)
1. The 9 chapter names, their time ranges and shot ranges; chapter-level accent/set/light.
2. The 141-shot board (`shots.json`) and per-shot: type mode, tier (still / 2.5D / motion / sung), 2.5D treatment name, devices, transitions. Only s001 is shown in full (W-fmt).
3. Word-level or line-level lyric timestamps (`words.json`), the beat map (`beats.json`), the hits file, section start times, bar numbers.
4. Halftone / line-screen / dither / misregistration / grain shader parameters; print-pass colour pipeline; transition (dither) design.
5. The countdown board's flip times (18 to 6 to 0 to "THERE IS NO UNDERCLASS"), glyph set, flap animation timing beyond "clatters from frame 1, settles by 1.5 s", font, `cw: 36, gap: 3` units.
6. The LOOK counter and model-card / garment-tag layouts, fonts used in EV, tracked CV box detector prompts/threshold values (only "Grounding DINO" and the example labels).
7. Definition of the "strobe" type mode (named in R, absent from the renderer's mode table).
8. Exact mapping of which shots are 2.5D vs clips vs pure code (only the clip-bearing shot ids are known).
9. The Midjourney personal profile code; 130 plates list with shot mapping (only 92 flagged `plate:true` in the API; see G).
10. The final edit list; which covers/takes appear at which times; the lip-sync fallback usage (LatentSync) details.
11. Whether any sound design or mix processing was added after Suno for EV (not stated in R or SU).
12. Exact prompts sent for the `-ls` entries (SD09-ls1, SD20-ls1) which have an empty prompt in the source ("song 91.62 s · 1.92 s · sung" with no text).

## G. Inconsistencies in the author's own documents (for the replicator)
- Plate count: R and api_index "130 plates used"; EV page and api_films "92 of them plates in the film" and the API item field `plate` = "EV: recovered by matching the cut". 92 items have `plate:true` in api_films_escape-velocity.json. Both numbers are published.
- Seedance cost: SD "≈ $97.28" local ledger vs "about $93" OpenRouter; W-start confirms "one said $97.28 for a $93.15 bill".
- Clip counts: R "91 submissions"; SD "47 storyboard clips, 30 covers, 7 early tests" (= 84 listed clips; the remaining 7 of 91 are not listed in SD). W-seed: "32 of 59 clips came back grey" (59 is a different count from 47; not reconciled).
- LatentSync: R says it was the fallback ("About 86% ... verified in sync, with LatentSync as the fallback"); W-seed/W-tool say lip-sync models were tried and dropped ("No lip-sync models"). Unreconciled; the wiki text is generic across films.
- Inputs colour: SD says plates were "graded in the video's print look" (mono) for @Image1; R/W-seed say that monochrome inputs came back grey and the lesson is colour in, look in post. SD describes the v1 batch; whether covers/new clips in v2 used colour plates is not stated beyond the recolourisation step.
- Style BPM: SU asks Suno for "128 BPM"; delivered take 131.5 to 133.9.
- Identity descriptor drift: R canon "young Caucasian American woman" vs W-consistency: ""young" makes it worse. ESCAPE VELOCITY's text said "young"" (the later canon uses "28-year-old ... grown-up angular face", see W-fmt s001 prompt and CL).

## H. Ten-line reconstruction digest
See the final reply message; the same facts with sources.
