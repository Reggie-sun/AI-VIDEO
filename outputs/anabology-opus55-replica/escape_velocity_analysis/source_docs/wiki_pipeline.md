# The whole pipeline

How one director and Claude made eight music videos in about 356 hours of wall-clock time, stage by stage, with the numbers.


Each film was made by one director, anabology, making every taste call in a few dozen short notes, and Claude (Opus 5.5
in Claude Code) as the production team: research, lyrics, storyboard, every prompt, every script, the edit and the
motion design. AIRPLANE MODE added seven GPT-6 Astra agents (OpenAI's model) in Blender, briefed and checked by Claude:
its low-poly world, the motion of its VR shots and some of its 3D motion design. DOWNFORCE was cut from real footage
(Tesla's livestream of the Roadster demo, SpaceX's 2018 Starman footage), with Wan 3.0 beside Seedance for its moves.
DON'T LET ME SCROLL cut her out of takes shot on grey and played them inside a world drawn in code, then re-dressed,
re-lit and repaired finished shots with Seedance and Wan. WHITEPILL was shot twice: a previz of every shot of hers by a
performer model, MiniMax H3, then each shot again in Seedance 2.5, singing from Suno's own vocal stem; its
worlds are shaders written in code and filmed by the same model, all of it cut on the song's bars. THE CAKE IS NOT A LIE
is set in Portal 2's world and seen through her own HUD: Claudia is GLaDOS, singing in her chamber while her memories play
as scenes, made in Seedance 2.5 from first frames that went through Midjourney and back to her character sheets, with six
physics shots recorded in Portal 2; the song's glitches are hit on her head, its shots are graded from their own numbers,
and the cut was re-paced by what each shot holds. Many of the stages ran as multi-agent workflows: several agents working
in parallel, judged and merged.

## The stages

Starting a film of your own? [Start here](https://claudia.gallery/wiki/start/) has the checkpoints, the accounts and the spending rules;
[What to build](https://claudia.gallery/wiki/toolkit/) specifies the tools.


1. **Brief.** The director's ask, word for word, then each decision with its date. Taboos and standing rules go in the
   brief and into every agent's prompt.
2. **Research.** Agents build banks of live memes and events, each fact checked by a separate verifier agent. BLISS also
   researched the XP sound files (downloaded and pitch-analysed), the old desktop-dancer programs and how to steer Suno.
   DOWNFORCE's research was the night itself: the coverage, each line's source, the real orbit from JPL Horizons, and
   the footage catalogued shot by shot, with Tesla's on-screen telemetry read off it frame by frame. DON'T LET ME
   SCROLL's was two surveys, of the library's moodboards and of the earlier films' looks, and Apple's own iOS 26
   screenshots, measured. WHITEPILL's was a case file for its argument, the case for benign AI, every item tagged by how
   it was checked; the ways of making the picture; and the sounds a new song could have. THE CAKE IS NOT A LIE's was the
   month's AI news for its second lyric, the interfaces of shipped games for its HUD, and the research on pacing, from
   studies of music videos to eye-tracking after a cut.
3. **Lyrics.** Several writers from different angles (density, tension, hook, story), judges, a merge, a critic pass,
   then the scansion scorer. See [Song](https://claudia.gallery/wiki/song/). WHITEPILL's first full draft merged four written in parallel: the
   season's doom headlines turned over, her own pitch, the good ending against the bad timeline, and the lead's. THE CAKE
   IS NOT A LIE's second lyric was rewritten only where the director pointed, each section's candidates ranked by the
   scorer.
4. **The song.** Suno takes, round after round, picked by ear; the director often made the final take themselves.
   WHITEPILL's is the director's own take of draft 2, the final lyric. THE CAKE IS NOT A LIE's is the director's own take
   of the rewritten lyric, its lead vocal treated in a voice the director chose by ear, with 15 % of the untreated voice
   under it, and only the voice levelled ([Song](https://claudia.gallery/wiki/song/#a-treated-vocal)).
5. **Listening.** Stems, a beat map, every word's time, a list of hits. Everything after sits on that grid. Check the
   tempo against the genre: DON'T LET ME SCROLL's first reading, 89 BPM, was two-thirds of the real 133.39. WHITEPILL's
   singing shots took their vocal from Suno's own stem split, which matched the master to the millisecond. THE CAKE IS NOT
   A LIE's grid was tracked from the drums 16th by 16th, and its glitch map measured every hit of the places where her
   voice is an instrument.
6. **Her.** The canon text and the looks for this world, tested on a few plates before any batch. See
   [Consistency](https://claudia.gallery/wiki/consistency/). WHITEPILL found her dress in stills before any take was made with it, and gave
   every video model her face sheet. THE CAKE IS NOT A LIE made her porcelain: one face on three bodies, each with a
   character sheet.
7. **Storyboard.** Three director agents board the song independently (in ESCAPE VELOCITY: fashion film, meme density,
   narrative), judges score them, a head director merges the best into one board. Every shot carries its lyric, its type
   device, its plate prompt, its camera on the song's hits and what its graphic explains. The director reviews a PDF of
   the board; CLODYSSEY got 70 notes shot by shot. WHITEPILL's final shot list was written in the song's bars, 27 shots
   with every cut on a bar line ([Storyboard](https://claudia.gallery/wiki/storyboard/#the-bar-map)), after a first board and an orbiting
   previz were dropped. THE CAKE IS NOT A LIE's restart was the lead's shot list of 114 shots on the drum-tracked grid;
   then every unit's first frame was made again in Midjourney twice over and put back on the character sheets, and the director picked
   unit by unit ([Midjourney](https://claudia.gallery/wiki/midjourney/#first-frames-then-an-identity-fix)).
8. **Plates.** Midjourney batches, contact sheets, picks, one image per shot. See [Midjourney](https://claudia.gallery/wiki/midjourney/).
   DOWNFORCE needed only 20 prompts: the real footage was the star, and Midjourney made only her. DON'T LET ME SCROLL's
   plates were her alone on grey, to be cut out, and the feed's 54 pictures, with no Claudia in them. WHITEPILL's
   Midjourney images were references only: the colony's places with nobody in them, and her dress. THE CAKE IS NOT A
   LIE's were a test against frames of Portal 2, a library of places, and two candidate first frames for every unit of
   its storyboard.
9. **Moving shots.** The prompt book, written by hand in one context and read before spending, then Seedance with lip
   sync measured. See [Seedance](https://claudia.gallery/wiki/seedance/). DOWNFORCE's: Wan 3.0 moves on real frames and shots of her, Seedance
   for the repairs and the re-shoots, every take judged by eye for its usable window. DON'T LET ME SCROLL's: Wan for her
   gestures, Seedance for the dances that had to land on the beat; after the edit, Seedance video edits that re-dressed
   takes and re-lit finished shots, and Wan passes that repaired them. WHITEPILL's: a previz of every shot of hers by
   MiniMax H3; a whole-film reshoot in Wan 3.0 Prime that was dropped; then each shot in Seedance 2.5 singing from the
   vocal stem, with the previz at 320 × 180 as a rough guide or with no guide; and the shader scenes remastered as film
   by Seedance 2.5. THE CAKE IS NOT A LIE's: a first film, set aside with its song; then her singing units in her chamber
   among screens of her memories, and the story's shots, in Seedance 2.5 on Higgsfield's API and on Replicate; six physics
   shots recorded in Portal 2; most of the units made again from the storyboard's new first frames, and reshoots on the
   director's notes ([Seedance](https://claudia.gallery/wiki/seedance/#a-singer-among-her-memories)).
10. **The edit.** An edit list that resolves singing takes and their covers moment by moment. Stills stand in until clips
    exist, so the film renders end to end at every stage. Takes cut out for a world drawn in code play through beat
    warps that never run them below 1×. WHITEPILL's is one take per shot on the bar map, each from its own song time at
    1×, the song laid over; the previz stood in for the masters until they landed. THE CAKE IS NOT A LIE's is one script
    that cuts every shot at its storyboard time on the 24 fps grid and grades it; its pacing pass re-timed or re-trimmed
    21 shots and took out 8, all from the takes it had ([Storyboard](https://claudia.gallery/wiki/storyboard/#pacing-by-what-a-shot-holds)).
11. **Chapters.** One animator agent per chapter, an art-director agent reviewing real rendered frames, a fixer; in
    BLISS's second round, review → fix → verify → finish, with notes on the seams between chapters. See [Motion](https://claudia.gallery/wiki/motion/).
    In AIRPLANE MODE's last round: one workflow per chapter, an animator, then an independent checker against the notes,
    then one refix. In DOWNFORCE: a builder, an art director and a QA checker in parallel, a fixer and a verifier per
    chapter, in three parallel runs; then a whole-film critic, fixers and a final check. In DON'T LET ME SCROLL: one
    animator per chapter with its own art-director passes and a notes file, and in the last rounds the director's own
    eye instead of reviewer agents. WHITEPILL had no chapters: agents wrote rival shader worlds in rounds, and a critic
    agent watched the previz as the director would, round after round; its lyrics are drawn after by one script. THE CAKE
    IS NOT A LIE had none either: its rounds of notes went to specialists (a HUD designer, a colourist, a pacing
    analyst, a motion designer), each with a written brief and the lead's review at full size before the director saw anything.
12. **Checks and render.** The lyric gate, contact sheets, the flash test, a strobe scan and a scan for single-frame
    outliers, then a CRF 16 master. WHITEPILL's: every cut measured against the bars and the sung lines, the picture's
    motion against the arrangement bar by bar, a frame per bar and both sides of every cut on sheets. THE CAKE IS NOT A
    LIE's: the HUD's overlap check on every frame against a head model, the head mattes' sheets, scene detection on the
    cut and on every take, and frame-exact decoding ([What to build](https://claudia.gallery/wiki/toolkit/#a-games-world-through-her-eyes)).

## What the director did

Taste, at checkpoints, in very few words. ESCAPE VELOCITY took about 50 notes, CLODYSSEY 68, BLISS 21, AIRPLANE MODE six
messages (one of them a long note on the first cut), DOWNFORCE fourteen (one of them the notes on the first cut), DON'T
LET ME SCROLL 43 (three rounds of notes among them), WHITEPILL 147, most of them short calls on tests as the method was
found, THE CAKE IS NOT A LIE 92 up to its final's approval, among them long notes on drafts 5, 7, 8 and 10. A few that
changed whole films:

- "way too.. gray … loses the Midjourney magic" (ESCAPE VELOCITY's colour)
- "s018 color is PERFECT" (CLODYSSEY's grade)
- "EVERY prompt needs to have litearlly timestamps, extremely detailed motion descriptions / blocking descriptions"
- "Can you use actual bliss as the bg or too late?" (BLISS's wallpaper)
- "idk i dont love these - id say more say y2k high fashion" (BLISS's wardrobe)
- "youre oftne over cutting, linger more snd find how single scenes can be coherent with the lyrics for longer (remember
  this plz)" (AIRPLANE MODE's cut)
- "the better way to do this js use the blender anims as motion refs only" (AIRPLANE MODE's game avatar)
- "i want it to be like tiktok car edits. many angles, lot of 3d effects, video models are great at 3d effects, moving
  shots in space" (DOWNFORCE's edit)
- "for reshoots use seedance 2.5 to try and make it better and specify the fix" (DOWNFORCE's re-shoots)
- "0:55 LOVE THIS. THis is the best part. more like this!!!! the opening should be on this tier." (DON'T LET ME SCROLL's
  grammar)
- "never slow these down. you lowered the framerate for no reason, just looks bad." (DON'T LET ME SCROLL's takes)
- "it should be like photography" (DON'T LET ME SCROLL's composition)
- "you could maybe just throw the entire clip thru Wan 3.0 (with your edits and stuff) and specify to remove the foot so
  you dont have to re-edit. and have it relight at the same time." (DON'T LET ME SCROLL's repairs)
- "i want you to basically shoot the entire video twice" (WHITEPILL's method)
- "the audio structure and video structure need to be consonant." (WHITEPILL's timeline)
- "i think SHADERS are the key actually! shaders are math + viz" (WHITEPILL's worlds)
- "OMG THE SEEDANCE W/ SUNO VOCAL STEM METHOD WORKED!!!!! LFG!!!! FINALLY. IT"S PERFECT" (WHITEPILL's lip sync)
- "just describe her exact dance (and all rest like camera movements etc same) for each of those scenes." (WHITEPILL's
  dances)
- "i want it to feel very wes anderson tbh" (WHITEPILL's look)
- "glados (claudia) was a […] agent that escaped and we see her development becoming  a superintelligence and then
  becoming the tester not the tested, and youre unsure if shes aligned." (THE CAKE IS NOT A LIE's story)
- "b is great close up" (her porcelain look)
- "I think we should never have fullf rame glitches for more than like 2 seconds" (its glitches)
- "it should be as if we shot a scene and there was a heads-up display there, and we framed the heads-up display in
  advance before we even shot the scene." (its HUD)
- "every time there's a shot that's literally a quarter of a second, we need to get rid of that." (its pacing)
- "Whenever I think of aperture and portal, I think of a lot of white surfaces, contrasting light colors." (its grade)

More of them, in context, in each film's making-of: [ESCAPE VELOCITY](https://claudia.gallery/record/escape-velocity/readme/) ·
[CLODYSSEY](https://claudia.gallery/record/clodyssey/readme/) · [BLISS](https://claudia.gallery/record/bliss/readme/) · [AIRPLANE MODE](https://claudia.gallery/record/airplane-mode/readme/) ·
[DOWNFORCE](https://claudia.gallery/record/downforce/readme/) · [DON'T LET ME SCROLL](https://claudia.gallery/record/dont-let-me-scroll/readme/) ·
[WHITEPILL](https://claudia.gallery/record/whitepill/readme/) · [THE CAKE IS NOT A LIE](https://claudia.gallery/record/the-cake-is-not-a-lie/readme/).

## Lessons from running it

- **One hand writes the prompts that cost money.** CLODYSSEY's first round of video prompts was written by planner agents
  and spent about 830 credits on lifeless takes before anyone read them. Since then, every paid prompt is written in one
  context and read before anything is submitted.
- **Spend only after reading.** A background workflow with its own spending stage kept spending after the director had
  flagged the prompts. Stop generator workflows the moment quality is in question.
- **Empty is not a pass.** When agents ran out of usage mid-run, chapter reviews came back empty and the scripts read
  "empty" as "nothing to fix". A review that returns nothing is a failed review, in code; check that every agent
  actually finished.
- **Long runs need their permissions in advance.** One write outside the allowed folders stalled a whole run on a
  single approval prompt.
- **Watch the queues.** Every clip import queued a 16-minute matte job; after 80 re-makes the GPU queue was about 20 hours
  deep. Cancel superseded jobs so the shots that matter go first.
- **Parallelism has a ceiling.** On a 4-CPU machine a workflow ran two agents at a time; splitting chapters into more
  workflows helped less than expected (1.1–1.5× measured, not 3×).
- **Keep run records.** Long workflows get interrupted; resume them by run id and let finished agents replay from cache.
- **A round of notes is a plan, in files.** AIRPLANE MODE's notes on its first cut became three kinds of document that
  every agent read first: the note verbatim with its parse, a plan (the story's logic, the cast, a beat sheet per lyric
  phrase, every asset with its owner, the budget) and one notes file per chapter. The lead appended dated UPDATE lines as
  takes and tools landed, and the agents re-read their file before finishing.
- **An independent checker, then one refix.** After each chapter's animator, a checker that had not built it rendered
  frames at every note's moment and reported each note done or not, with what it saw. Open items went back for a single
  refix. In an earlier round, two of four chapters failed their check and were re-fixed. All twelve chapters of the
  final round were built and checked this way, and the whole film gated 363 of 363 lyric tokens.
- **One workflow per chapter.** Resuming a multi-chapter workflow after an interrupt replayed stages unevenly, so some
  finished chapters were reviewed and fixed again. With one workflow per chapter, an interrupt costs one chapter.
- **Tools and chapters in parallel.** The level tag, the real anti-piracy card and the real seat-back screen were built by
  toolkit agents while the chapters laid out around them with their planned timing and stand-ins; an UPDATE line
  switched each chapter over when a tool landed.
- **Run the flash check before the master.** The re-cut's dive failed it only after the encode.
- **Send the rough cut before the polish.** DOWNFORCE's first cut went out with all eleven chapters at their first
  build, before any review, so the director's notes ("ok this is sick , so good. let me flag what i see in parallel with
  the review agents") reached the agents while the review rounds were still running. The chapter fixers applied most of
  them from the brief, and the whole-film pass re-checked each one.
- **Independent eyes at every level.** Judges scored DOWNFORCE's boards, an adversarial scout re-checked every take, an
  art director and a QA checker reviewed every chapter, and a critic watched the whole film. Each caught something the
  level below had passed: a man in the empty car's window and a repair that became a hatchback (the scout), an
  off-model close-up a fixer had swapped in (the critic).
- **Logged windows, enforced in code.** Every generated take got a usable window by eye, the chapters drew only inside
  them, and the final check logged every frame the film draws to prove it.
- **Interruptions cost time, not work.** DOWNFORCE's chapter runs were interrupted three times and resumed from where
  they stopped; 57 of 147 agent launches ran again.
- **Faster renders for the agents.** Asked "is there anything you think you could do serially faster?", the production
  moved the agents' test renders to a GPU render box rather than give up a review round; the first cut then rendered in
  about 3 minutes.
- **The director's eye replaces reviewers late.** In DON'T LET ME SCROLL's last rounds: "we dont need excessive
  'reviewers' after, ill stay in the loop and can do a visual review faster and more comprehensively than an opus reviewr
  can do it." Each chapter agent did one thorough pass with its own art-director check, and the flagged shots went to the
  director as previews before the final render.
- **Fixes, then reshoots, then re-lights.** Re-lights made before the outfits and compositions changed were spent twice:
  "kinda a waste on the excess ones".
- **Judge a change where it plays.** A re-light that looked darker and softer on its own read better behind the
  animation it plays under. The director asked "can we see how it looks w/ vs w/o the relight?", saw them side by side
  in place, and answered "New better."
- **A shared render box needs limits.** Rotos and chapter renders shared one CPU box; a roto under the matting library's
  default memory arena held about 12.5 GB and was killed, and one died behind a `| tail` that hid its exit status. With
  the arena off a roto held 1.3 GB, and the take tool counts its mattes and fails loudly.
- **Shooting twice works when the second pass is free to redraw.** WHITEPILL's previz carried the motion, the mouth and
  the camera. A master told to keep the previz exactly, or given it at full resolution, kept its faults too: a whole-film
  Wan reshoot over it was rejected ("i feel like h3 is dragging it down"). Shrunk to 320 × 180 as "a rough guide", with
  only the lip sync exact, it worked; where its faults were the problem (dances that lost limbs), no guide worked better.
- **Find the method on one shot.** The method that made the film was found on the opening shot made four ways and
  watched side by side, after a whole-film pass had failed.
- **The bars first.** WHITEPILL's reset began from the song's bar map, not from shots: cuts only on bar lines, moves in
  bars, and every assembly measured against the music. The director's diagnosis of the films' "temporal signature"
  ("i think you use cuttng to cover up imperfections from video models rather than for timing") made a failed take
  something to make again, never to cut around.
- **A previz model doesn't repeat itself.** Every shot was tried with several seeds, and its takes changed from run to
  run even with the same seed.
- **The director picks by eye from takes.** The look was picked from palette tests, and the cut from two complete versions
  mixed section by section: "ok let's do this mashup".
- **A new song is a new film.** THE CAKE IS NOT A LIE's first film, on its first song, was set aside whole when the song
  changed; the restart wrote the story on the new song first, and kept the tools.
- **One product, one source.** Its overlay became good when it became one thing: one visor, one projector, one grid, one
  set of slots, composed shot by shot and checked against every face in every frame. Panels made one by one never shared a
  surface, however carefully each was turned.
- **Glitch the subject, not the frame.** The song's glitches went on her head, inside a matte, on their measured hits;
  the long ones belong in the take, as picture only.
- **Measure a cut that feels wrong.** "the structure is somehow incorrect" became numbers (pieces, flags, a table per
  section against the song), a list of changes each checked against its take, and a re-cut with no new generation.
- **Make the first frames where the look is made.** Every unit's first frame was made again in Midjourney before its
  take, an image-model edit put the faces back on their sheets, and the director picked unit by unit on boards beside the
  earlier frame.
- **A round of notes goes to specialists.** Each got a written brief, the director's words verbatim and the lead's
  direction; the lead looked at every stage at full size before the director saw it.
- **A re-sung take isn't lost.** A take that re-sang the vocal but still sat on the song was measured and placed by its
  lag; only a take that drifted was made again.

## The numbers

| | ESCAPE VELOCITY | CLODYSSEY | BLISS | AIRPLANE MODE | DOWNFORCE | DON'T LET ME SCROLL | WHITEPILL | THE CAKE IS NOT A LIE |
|---|---|---|---|---|---|---|---|---|
| Length | 5:06 | 3:11 | 3:01 | 2:36 | 3:09 | 2:37 | 3:54 | 3:28 |
| Shots | 141 | 94 | 44 | 54 | 183 | 35 | 27 | 98 |
| Midjourney | 188 prompts · 636 images | 161 prompts · 644 images | 138 prompts · 315 images | 149 prompts · 548 images | 20 prompts · 80 images | 130 prompts · 516 images | 75 prompts · 300 images | 266 prompts · 1,064 images |
| Seedance 2.5 | 47 clips + 30 continuations | 101 clips · 189 takes | 50 clips | 98 clips · 116 submissions | 16 submissions · 67 s | 41 submissions · 212 s | 93 submissions · 777 s | 249 submissions · 1,353 s |
| Wan 3.0 | — | — | — | — | 63 submissions · 294 s | 49 submissions · 264 s | 81 submissions (Prime) · 863 s | — |
| Previz | — | — | — | — | — | — | MiniMax H3, every shot of hers, several takes each | — |
| Real footage | — | — | — | — | Tesla's livestream (2 files) and a lineup camera · SpaceX's Starman footage | — | — | six shots recorded in Portal 2 |
| Wall-clock | about 19 h | about 41 h | about 19 h | about 15½ h | about 13 h | about 25½ h | about 82 h | about 141 h |
| Director's notes | about 50 | 68 | 21 | 6 messages | 14 messages | 43 messages | 147 messages | 92 messages |
| Claude tokens | 1.4 B | 2.37 B | 2.25 B | not measured | not measured | not measured | not measured | not measured |
| Claude at API list prices | ≈ $626 | ≈ $1,007 | ≈ $714 | not measured | not measured | not measured | not measured | not measured |

The Claude figures are what the first three films' work would cost at API list prices. About
96–98% of the first three films' tokens were prompt-cache re-reads of long contexts. DOWNFORCE ran seven multi-agent
workflow runs, 172 agent launches in all. Its generation cost $143.17 at list price ($66.98 Wan, $76.20 Seedance), of
the $200 the director allowed. DON'T LET ME SCROLL ran 32 agent launches and no judged workflows; its generation cost
$365.90 at list price ($64.20 Wan, $301.70 Seedance), $357.51 after refunds. WHITEPILL ran 31 agent launches: 3
researchers and the 7 they launched, 3 lyric writers, 13 shader builds, 5 critics and QA passes. Its generation through
the APIs cost $588.59 at list ([Seedance](https://claudia.gallery/wiki/seedance/#costs-measured)): Wan 3.0 Prime, all 75 takes, $300.08 (the
dropped whole-film reshoot $132.42 of it); Seedance on Higgsfield's API, 13 tests, $48.14; Seedance on Replicate, the
shader scenes and tests, $238.44; images (logged) $1.92; each part rounded to the cent. Its Seedance takes of her, on
Higgsfield (References), are given in takes and seconds (42 takes, 412 s), and MiniMax H3's cost was not recorded. Its
seconds count every job that ran, the tests included. THE CAKE IS NOT A LIE ran 24 agent launches: 8 researchers, 9 for the
restart (the song map, the recordings in Portal 2, the character sheets, the Midjourney test and library, the first
overlay, the singing anchor and one team per act), 3 for storyboard v5 and 4 for the finishing passes (the memory films,
the HUD, the pacing analysis, the grade). Its generation through the APIs cost $467.12 at list: Seedance 2.5 $435.17 for
the 229 takes on Replicate ($155.35) and Higgsfield's API ($279.82), and GPT Image 2.5 $31.95 for 480 images and edits;
the first film's 20 takes of her on Higgsfield (References) are given in takes and seconds (90.8 s). Its seconds count
every take in its video record, the tests included.

## The full records

Each film's making-of: the story and the numbers, and every prompt for every tool.

- [ESCAPE VELOCITY](https://claudia.gallery/record/escape-velocity/)
- [CLODYSSEY](https://claudia.gallery/record/clodyssey/)
- [BLISS](https://claudia.gallery/record/bliss/)
- [AIRPLANE MODE](https://claudia.gallery/record/airplane-mode/)
- [DOWNFORCE](https://claudia.gallery/record/downforce/)
- [DON'T LET ME SCROLL](https://claudia.gallery/record/dont-let-me-scroll/)
- [WHITEPILL](https://claudia.gallery/record/whitepill/)
- [THE CAKE IS NOT A LIE](https://claudia.gallery/record/the-cake-is-not-a-lie/readme/)


---
From the Claudia wiki: https://claudia.gallery/wiki/pipeline/
