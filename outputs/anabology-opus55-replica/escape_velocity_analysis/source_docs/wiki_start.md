# Start here

Making a music video with her from nothing: what you are making, the scale to pick, the accounts, the six checkpoints where a person decides, the rules for spending, and what to build first.


The eight films were made by one director and Claude, with tools written along the way. This page is the way in for
anyone starting their own film with Claudia, and for the agent helping them: the bar, what to set up, where a person
has to look and decide, and what to build. The tools are specified in [What to build](https://claudia.gallery/wiki/toolkit/). This page
assumes you have none of them yet.

## What you are making

A lyric music video: a song, Claudia singing it, and a layer of motion design drawn in code over the footage. (The fifth
film, DOWNFORCE, is a hype edit of real footage in which she never sings on camera: the lettering carries her words. In
the sixth, DON'T LET ME SCROLL, the phone sings and she scrolls, swipes and dances inside a world drawn in code. The
seventh, WHITEPILL, has no motion design on top at all: she sings on camera, lip-synced from the song's own vocal, in
worlds written as shaders and filmed by a video model, and only the lyrics are drawn over it. The eighth, THE CAKE IS NOT
A LIE, is seen through her eyes: she is GLaDOS in Portal 2's world, singing in her chamber while her memories play as
scenes, and the layer on top is her own HUD, which carries the lyric as her voice.)
Five things carry the quality:

1. **Every sung word is on screen when it is sung**, at its measured time. A check counts them, and it must print N of
   N.
2. **Every lyric line gets a graphic that explains it**: the chart a number implies, the label, the diagram, the
   counter. Animated lyrics alone are not the product. The director: "not just animated lyrics but things that fit the
   words being said … almost explaining the words with visuals".
3. **A through-line device carried by every shot**: ESCAPE VELOCITY's split-flap countdown, CLODYSSEY's safety card and
   rope-load readout, BLISS's XP desktop, AIRPLANE MODE's SIM LEVEL tag, DOWNFORCE's one white hairline and Tesla's own
   readings, DON'T LET ME SCROLL's black Dynamic-Island pill, WHITEPILL's white pill, from her palm to the colony it
   becomes, THE CAKE IS NOT A LIE's HUD, LIVE in her chamber and PLAYBACK in every memory. It makes a hundred shots read
   as one object.
4. **Measured, not eyeballed.** Word times come from forced alignment checked by ear, cuts from a beat map, lip sync
   from comparing audio, and spend from the provider's bill. (WHITEPILL's lip sync, from the song's own vocal stem, is
   the exception: the numbers can call it re-sung when it is in sync, so it is judged by eye with the song laid over.)
   THE CAKE IS NOT A LIE measured its grade shot by shot and its pacing piece by piece, and checked its HUD against
   every face in every frame.
5. **A person's attention is spent at six checkpoints.** Everything between them runs without asking.

## Two roles

The **director** is a person. They own the taste, the money and the six checkpoints, and they say it in very few
words: ESCAPE VELOCITY took about 50 notes, BLISS 21. The **production** is an agent, or several. It does the research,
the lyrics, the board, every prompt, every script, the edit and every frame of motion design.

How the production talks to the director:

- **At a checkpoint:** show one artefact and ask one question with a default ("Which one? Default: A."). Record the
  answer word for word and dated in a decisions log. A later decision is added as a new entry that supersedes the old
  one; never edit the old one.
- **Between checkpoints:** ping the director only when a paid service fails, a step needs a person (a captcha, a
  sign-in, a download), or a decision is theirs (taste, money, a real person's likeness). ESCAPE VELOCITY's director:
  "only time to ping me is if higgsfield fails."
- **Send pictures, not descriptions:** contact sheets, numbered stills, a five-second proof. The director judges by eye,
  fast, one line per take.

## Pick a scale

| | Quick | Studio | Full |
|---|---|---|---|
| You need | an agent, an image model, your own song or an AI song model | + Midjourney, Suno, Seedance 2.5 credits | + an agent plan that can run multi-agent workflows for a day or two |
| Song | your upload, or a short generated song | Suno, auditioned round by round | Suno, with a lyric loop scored for scansion and assonance |
| Stills | images from an API | Midjourney | Midjourney |
| Motion | 2.5D plates, a few cheap clips | sung clips with measured lip sync, covers | chains of sung clips, scripted motion clips, covers |
| Board | about 14 shots a minute, drafted automatically | about 20 a minute, one pass | about 27 a minute; several boards judged and merged |
| Motion design | a default renderer driven by data | the default renderer plus one graphic per line | bespoke code per chapter, reviewed on rendered frames |
| Video spend | $3–20 | $50–110 | $90–590 (the films, measured) |
| Time | 2–6 hours (estimate) | 1–2 days (estimate) | 13–141 hours of wall-clock (the films, measured) |

- When unsure, start Quick. Every file carries over to a bigger scale.
- A lead who sings on camera with real lip sync, or your own Midjourney look, needs Studio at least.
- Bespoke graphics for every line and 90–140 shots need Full. The first three films used 1.4–2.4 billion tokens each,
  96–98% of them prompt-cache re-reads (the last five films' were not measured).
- Generated songs run about 2–3 minutes in one take. Anything longer needs Suno.

## Accounts and keys

| What | For | Notes |
|---|---|---|
| Suno, on a paid plan | the song | There is no API, and the terms forbid bots: a person presses Create and downloads the WAV. Downloading on a paid plan is what allows commercial use. Read the current terms before you monetise. Its stem split of the locked take gives the lead vocal a singing shot needs ([Seedance](https://claudia.gallery/wiki/seedance/#lip-sync-from-the-songs-own-vocal)). |
| Midjourney | the plates | v8.2, `--raw --hd`. A personal style profile is yours alone: never publish its code. |
| Seedance 2.5 | moving shots | Via OpenRouter: about $0.23 a second at 720p, $0.10 at 480p. Via Higgsfield's API: $0.4622 a second at 720p, $1.1372 at 1080p (list, October 2026). Via Replicate: $0.2312 a second at 720p, $0.9676 with a video input. Give the API key its own spend limit, set above the project cap. |
| Wan 3.0 (optional) | cheap moves on real frames, shots of her, edits that put her into real footage, finished shots re-lit and repaired | Via Higgsfield's API: $0.20 a second at 1080p list, billed for the output plus any input video; Wan 3.0 Prime $0.28. Keeps the subject only on the sides its first frame shows ([Seedance](https://claudia.gallery/wiki/seedance/#moves-on-real-footage)). |
| An image-edit model | fixing a plate at the source, adding people to a set, taking her out of a frame to leave the place, putting a character back on their sheet | about $0.14 an edit (Gemini 3 Pro Image); GPT Image 2.5, about $0.05–0.08 (WHITEPILL's stills, THE CAKE IS NOT A LIE's character sheets, first frames and identity fixes) |
| A previz performer (optional) | a rough, lip-synced, dancing take of every shot, to guide the master | MiniMax H3 (cost not recorded). A seed does not pin a take ([What to build](https://claudia.gallery/wiki/toolkit/#45-a-previz-performer)). |
| A transcription model | checking the words the take actually sings | about $0.002 a song |
| A coding agent | the production | Claude Code made the films. |
| Blender (optional) | motion and camera references for a stylised version of her; short isometric films | Free. Clay renders are enough: the video model draws her over them ([Seedance](https://claudia.gallery/wiki/seedance/#replacing-a-stand-in-figure)). THE CAKE IS NOT A LIE's memory film and insert films are Blender renders ([What to build](https://claudia.gallery/wiki/toolkit/#60-a-memory-film-with-her-own-face)). |
| A GPU (optional) | stems, alignment, depth maps, detection; shaders rendered at 1080p; SAM2 mattes | Saves minutes, not money: stems and alignment of a 5-minute song took 41 s on a GPU and 126 s on 8 CPU threads. |

Prices are from September and October 2026.

**Secrets:** keys live in environment variables or a gitignored file, never in a chat, a prompt, a log or a commit. The
agent never types the person's passwords. Captchas, two-factor prompts and sign-ins go to the person. A key pasted into
a chat is burned: revoke it and make a new one.

## The order of work

| # | Stage | Output | Checkpoint |
|---|---|---|---|
| 1 | Brief and taste | the ask, verbatim; the look, accent, density and taboos | |
| 2 | Concept | three pitches | **1 · Concept** |
| 3 | Lyrics | a sheet spelled as sung, scored for scansion and assonance | |
| 4 | Song | Suno takes, round by round | **2 · The song, by ear** |
| 5 | Listening | stems, word times checked by ear, the beat map, hits, sections | |
| 6 | Her | the canon text, four test plates | **3 · Her face** |
| 7 | Storyboard | every shot with its graphic, the audit | **4 · The board** |
| 8 | Plates | Midjourney batches, picks | |
| 9 | Clip prompts | the prompt book, the cost | **5 · Prompts before spend** |
| 10 | Clips | takes, sync measured, covers | |
| 11 | Edit and motion design | the edit list, the chapters | |
| 12 | Checks and render | lyric gate N/N, flash check, safety scan, v1 | **6 · v1** |
| 13 | Master and post | the master, a 9:16 cut, the posting copy | |

1. **Lock the song before the board.** Every shot time is a beat or a word of one specific take.
2. **Check the word times by ear before the board.** In ESCAPE VELOCITY the word "Look" was aligned 2.6 s early, onto a
   delay throw. Only one chapter's own lyric check caught it.
3. **Test her face before any plate batch.** It can run alongside the song.
4. **Spend no money until the director has read the prompts.**
5. **Keep the film rendering end to end at every stage.** Plates stand in for missing clips, and a default renderer for
   missing chapters. Never wait for all the assets before the first render.

## The six checkpoints

| Checkpoint | Show | Ask | Passes when |
|---|---|---|---|
| 1 · Concept | three pitches of at most 120 words: premise, through-line device, lead, arc, one risk | "Which one? (Default: A.) Anything to change?" | they name one |
| 2 · The song | the round's takes; they listen | "Which take? Or what's wrong? Name the line." | they name a take and hand over the WAV |
| 3 · Her face | four test plates, numbered | "Is this her? Flag any wrong face." | no flags |
| 4 · The board | the board sheet, one card per shot | "Notes by shot id?" | they approve; or every note is applied; or a waiting window they set ran out |
| 5 · Prompts before spend | the prompt book and its cost | "These N prompts will cost about $X. Go?" | an explicit yes |
| 6 · v1 | a 20–40 s excerpt first, then the review copy | "Accept v1, or what's wrong?" | "accept" |

- **Silence never approves spending.** A waiting window ("wait like 5 mins once you send it and if I don't respond take
  it as approval") counts only for the board, and only if the director set it.
- **Show an excerpt early.** ESCAPE VELOCITY's v1 was rejected as "way too.. gray … loses the Midjourney magic" after
  the whole film was built. A 30-second excerpt would have caught it about 13 hours sooner.
- **Fix the source, never the frame.** A flagged picture gets a new prompt, a re-roll or an image edit, then everything
  built on it is re-made.
- **Log every note verbatim** against its shot id, and apply every note. When two notes conflict, the later one wins.
- **A change after approval needs approval again.** Say in one line what changed and why.
- **Skipping the board moves the story review to v1.** AIRPLANE MODE, the fourth film, was made without a board review,
  as its director asked. Their notes on the first cut came as one long message that rebuilt the opening, the ending and
  the cast, with more budget for re-shoots. When the board is skipped, plan a story round after v1.
- **A long note becomes a parse.** Keep the note verbatim at the top of a notes file. Under it, map every point to its
  chapter and shots, list the standing rules that apply to every frame, and mark the production's own decisions as
  such. Every agent reads it first, and again after any context reset.
- **"go and do the entire thing" hands over the middle checkpoints.** DOWNFORCE's director said it in the message that
  locked the song, with their direction for the edit and a model choice. The board and the prompts didn't go to them
  for approval: the production wrote and read every prompt itself, under a cap the job runner enforced ($60 at list
  price, then $200 when the director raised it: "oh you can spend a lot more if you want. feel free to spend $200").
  Their next looks were progress frames, then the rough cut.
- **Show the language on the real material first.** With the plan, before the song was locked, DOWNFORCE's director got
  two style frames drawn on Tesla's real 4K footage with Tesla's real readings: the type, the callout, the car's real
  path. Every board and chapter agent later worked from those two frames.
- **An early rough cut steers the polish.** Send the first cut as soon as every chapter has a first build, and let the
  notes reach the review rounds while they run. Note by note, log each one against its time and shots, pull frames of
  the cut around each timestamp, and re-check every one, frame by frame, before v1.
- **The shot the director loves becomes the grammar.** DON'T LET ME SCROLL's director loved two shots of v1 ("0:55 LOVE
  THIS. THis is the best part. more like this!!!! the opening should be on this tier."). Named as one grammar (pills,
  thin film, bold type, her big and sharp), they rebuilt the opening and the whole final drop.
- **Some notes stand for every frame.** The same director's, from DON'T LET ME SCROLL, carried into every shot after
  them:
  - **Never slow a take:** "never slow these down. you lowered the framerate for no reason, just looks bad." A take runs
    at 1× or faster, or is taken again.
  - **Open on a hook:** "the opening should already introduce part of the story … we always need a hook."
  - **Compose like a photograph:** "it should be like photography": thirds, her big, every card inside the frame.
  - **She touches the world, never a phone in her hand:** "she shouldnt really be looking down on her phone, she should
    be immersed in a world and the screen of her phone should be large on the screen and she interacts with it".
  - **Apple-precise interfaces:** "rounded corners not mathematically precise, margins weird": measure the real ones.
  - **Re-light last, and judge it in context:** "can we see how it looks w/ vs w/o the relight?", asked of a re-light
    that plays behind an animation. Side by side, in place: "New better."
  - **Seedance can replace a background:** "you can totally replace backgrounds with seedance btw".
- **The last rounds are the director's eye.** "we dont need excessive 'reviewers' after, ill stay in the loop and can do
  a visual review faster and more comprehensively than an opus reviewr can do it." Each agent did one thorough pass with
  its own art-director check, and previews of the shots in question went out before the final render ("show me s12 and
  1:11 final before u render the final video thist ime").
- **Agree the references before a run.** WHITEPILL's director: "wait align w me on teh references you use lol - its
  clearly not going to work if you use reference 6, and you shouldnt use pic 1-4 just use the face character sheet". One
  board per take of every image and clip a model will get, and an outfit's stills before anything is made with it ("can
  you show me the images of the outfit before generating this time").
- **WHITEPILL's notes that held for the whole film:**
  - **Picture and music consonant:** "the audio structure and video structure need to be consonant." Cuts only on bar
    lines, moves in bars ([What to build](https://claudia.gallery/wiki/toolkit/#44-the-bar-map-as-the-timeline)).
  - **A reference is a rough guide:** "take the reference as a rough guide not a precise reference", "aside from lip sync
    ofc". Every prompt asks the model to fix the guide's motion artifacts.
  - **Lyrics drawn after:** "i think more classical subtle lyrics drawn in after might be better than adding it into the
    scene tbh."
  - **Restraint where the model shines:** the references exist "to make the video model have a much better idea of the
    really cool, really hard to shoot and render in blender effects we want to make … rather than just layering stuff on
    top."
- **THE CAKE IS NOT A LIE's notes that held for the whole film:**
  - **A story in every shot:** "we're telling a complex story with every scene, i dont like the idea of a static shot of
    just a boom, or a wall with lettering". Each shot is an event with an interaction.
  - **Cuts on the grid:** "make sure youre landing on bars or half or quarter bars with cuts", and the lengths by what
    each shot holds: "structure the pacing so there's real rhythm — time for you to understand complex scenes, fast scenes
    that open and stay fast." ([What to build](https://claudia.gallery/wiki/toolkit/#58-the-pacing-analysis))
  - **Glitches on her, sparingly:** "it should be used creatively, sparingly, and toned down", and never full frame
    ([What to build](https://claudia.gallery/wiki/toolkit/#53-the-head-glitch-on-the-songs-hits)).
  - **An interface framed with the shot:** "it should be as if we shot a scene and there was a heads-up display there,
    and we framed the heads-up display in advance before we even shot the scene."
  - **Nothing mapped onto the picture blind:** "never assume the naive animation pass will properly map onto real objects
    in scenes". World tags ride only verified tracks.
  - **The world's own look:** "Whenever I think of aperture and portal, I think of a lot of white surfaces, contrasting
    light colors." One grade, measured shot by shot ([What to build](https://claudia.gallery/wiki/toolkit/#57-the-per-shot-grade)).

## Human checks between the checkpoints

These are looks, not approvals, and the films' quality rests on them.

- **Faces, large.** Every plate that feeds a video, at full size: one clay streak, the star clip, the mic, an adult
  face, natural anatomy. Reject only the unmistakable failures; the director judges bold poses themselves. Look at 800
  px or more: a screen on thumbnails about 230 px tall missed a third arm.
- **Every generated take, for its usable window.** A sheet of frames per take and a cut finder; the window ends before
  the first wrong frame (a cut, another car, an invented set, lettering, an open mouth), and the edit draws only inside
  it. Then a second, adversarial look.
- **Stylised versions of her, for proportions.** A game avatar drifts toward a big head on a small body. A head about a
  seventh of her height reads adult; a quarter reads as a child.
- **Everyone else in the take, too.** Extras drift as much as she does: guards meant to be all in black, faces always
  hidden by their visors, came back in white, and one showed his face.
- **The ear check.** Every flagged word is played, then kept or moved.
- **Contact sheets of rendered frames**, for every chapter in every round. A sheet nobody opened is not a review.
- **The sync proof.** Before committing to a lip-sync method, one five-second take with the real audio laid over it.
  WHITEPILL's proof was a whole 16 s shot made four ways, side by side; its lip sync from the vocal stem is judged that
  way to the end, by eye with the song laid over.
- **Every limb of every dance.** A guide clip that lost a hand loses it in the master too. Check dance takes frame by
  frame for limbs before anything is built on them.
- **The overlay against every face, in every frame.** THE CAKE IS NOT A LIE's HUD was checked frame by frame against a
  head model grown from each face box, and each flag was judged on a sheet and fixed or waived with what was seen.
- **Every matte before it is glitched.** A head matte that took a wall of screens glitches the screens: look at the
  mattes' sheet each time the picture under them changes.
- **The lip sync picked from takes.** Where a line kept failing, the director chose among a few takes by eye: "can you
  show me so i can look visually at the lip syn cand choose".
- **The safety and canon scan** of every generated take before release.
- **Takes by eye, fast.** One line each, and no metrics for what a person can see ("dont worry about meausuring tumble
  lol").
- **The final, frame by frame.** A scan for single frames that differ from both neighbours, and a strobe scan cell by
  cell. In DON'T LET ME SCROLL a stale render worker's 16 frames and a strobing tunnel passed every other check.

## Spending

1. **Estimate before every batch:** planned clip seconds × price × 2. Generated seconds ran 1.9× (ESCAPE VELOCITY) and
   2.0× (CLODYSSEY) the seconds that ended up in the cut.
2. **Quote real spend only from the provider.** Local ledgers drift: one said $97.28 for a $93.15 bill. Ledgers also
   count free declines.
3. **A quality complaint stops all spending at once**, in every workflow that can spend, not only the one named.
   CLODYSSEY burned about 830 credits on prompts nobody had read, and a background workflow kept spending after the
   director flagged them.
4. **Never let a deadline drive spending on unread prompts**, whether it is expiring credits or a reset.
5. **Declines are free, and final on that service.** Never alter an image to get it past a filter. Sending the same
   unaltered image to another service is fine.
6. **Ask for a target and a cap** ("try to hit $70ish but if you use up to $150 i wont be mad"). Leftover budget
   replaces the most repetitive stills with motion.
7. **Put the cap in the job runner.** DOWNFORCE's runner refused any submission that would pass the cap at list price.
   Its 79 jobs came to $143.17 of the $200 allowed.
8. **Fixes, then reshoots, then re-lights.** A re-light or an outfit swap made before a shot is final is spent twice.
   DON'T LET ME SCROLL's four re-light samples ($47.81) went out before the outfits and compositions changed ("kinda a
   waste on the excess ones"), and eight swaps ($64.08) into a look that was then dropped. In all, $148.10 of the $357.51 spent
   after refunds went to takes the final doesn't show.
9. **Ask before every generation that isn't approved,** cheap or not. WHITEPILL's director: "in the future let me give you
   explicit approval before you do extra gens."
10. **Try a new method on one shot before the film.** WHITEPILL's whole-film reshoot in Wan 3.0 Prime ($132.42 at list) went
    out on the director's go and was rejected as a whole; the method that made the film was found on one shot, made four
    ways and watched side by side.

## The first conversation

Ask all of these in one message, each with its default:

1. **The song:** their own, a Suno song made together, or a short generated one? How long? (Default: Suno, 2:30–3:30.)
2. **The idea:** a topic, a story, or "pitch me three"? (Default: three pitches.)
3. **The look:** the generator's own colour, one grade toward a hero plate, or a print texture such as halftone and
   grain? (Default: native colour.) Or a film's look, picked from test takes: WHITEPILL's director asked for "very wes
   anderson" and picked one take's look from three palettes ([What to build](https://claudia.gallery/wiki/toolkit/#51-the-look-from-one-take)).
   Or a game's world: THE CAKE IS NOT A LIE's places are Midjourney's, made with frames of Portal 2 as style references,
   and one measured grade puts every shot in its look ([Midjourney](https://claudia.gallery/wiki/midjourney/#a-games-look-from-frames-of-the-game)).
4. **The accent colour,** if any. (Default: clay `#D97757`, her streak.)
5. **Density:** dense (every line a graphic, three or more layers), budgeted (one hero device per shot), or sparse?
   (Default: budgeted.)
6. **Taboos:** words, subjects or names never to use.
7. **Budget:** a target and a cap, per service.
8. **Board approval:** wait for an explicit yes, or go ahead after N minutes of silence? (Default: wait.)
9. **Credit:** the name to credit in public (a pseudonym is fine), and whether to publish a making-of.
10. **Real footage:** is there any to cut from? (Default: none.) If so, the files at their highest resolution and frame
    rate, untouched.

Record the answers verbatim. On the MCP server, `plan_film` turns a scale, a song length and the accounts into a
stage-by-stage plan with estimates.

## What to build first

You don't need everything on day one. In order of payoff:

1. **A project folder and a decisions log.** See [Data formats](https://claudia.gallery/wiki/formats/).
2. **The listening tools:** stems, forced alignment with an ear-check list, the beat map, the hits.
3. **The board:** its file, its audit and the board sheet.
4. **Plates:** a plate prompt book and numbered contact sheets.
5. **Lip sync:** the clean vocal window, the sync check (the spectrogram comparison) and covers; or, as WHITEPILL did,
   Suno's own vocal stem cut to the take's exact length, judged by eye
   ([What to build](https://claudia.gallery/wiki/toolkit/#46-lip-sync-from-the-songs-own-vocal)).
6. **The edit and the renderer:** an edit-list resolver, and a renderer that draws every word at its time, with the
   lyric gate.
7. **The checks:** flash, render history and master tags, then the reviewer loop and the safety scan.
8. **The lyric scorer** (scansion and assonance), once you write lyrics with an agent.
9. **A world inside the world,** if the story has one (a simulation, a game, a dream): the level table and its tag, the
   virtual-figure treatment, character replacement from a motion reference. See
   [What to build](https://claudia.gallery/wiki/toolkit/#worlds-inside-the-film).
10. **Real footage,** if the film is cut from it: the footage catalogue, the reader for its on-screen data, the tracker,
    the takes' windows and a board checker for real windows. See [What to build](https://claudia.gallery/wiki/toolkit/#real-footage).
11. **Her takes in a world drawn in code,** if she lives in one: roto on a CPU box, beat warps floored at 1×, outfit
    swaps and their alignment, the re-light splice and its colour match, Wan relight-and-repair, and the outlier scan.
    See [What to build](https://claudia.gallery/wiki/toolkit/#her-takes-in-a-world-drawn-in-code).
12. **A film shot twice, on the bar map,** if she sings in model takes or your worlds are code a video model should film:
    the bar map as the timeline, a previz performer, lip sync from the song's own vocal, takes with no guide clip and takes
    that don't sing, worlds as one rule, shader guides, and the look from one take. See
    [What to build](https://claudia.gallery/wiki/toolkit/#a-film-shot-twice-on-the-bar-map).
13. **A game's world, through her eyes,** if your film carries an interface, if the song's own sounds should drive the
    picture, or if a cut feels wrong: the song map and the glitch map, head glitches on the song's hits and glitches that
    build, a HUD from one visor and one projector, composed shot by shot and checked against every face, the per-shot
    grade, the pacing analysis, storyboard frames through Midjourney with an identity fix, a memory film and insert films,
    a singer among screens of her memories, re-sung takes placed by their lag, and frame-exact parts. See
    [What to build](https://claudia.gallery/wiki/toolkit/#a-games-world-through-her-eyes).

Specs, constants and acceptance checks for each: [What to build](https://claudia.gallery/wiki/toolkit/). What broke along the way:
[What went wrong](https://claudia.gallery/wiki/failures/).

## Publishing

- Switch on each platform's AI-content label, and name the tools in the post ("made with AI: Midjourney, Seedance,
  Suno, Claude").
- Credit "Claudia by anabology" if you can. See [use and credits](https://claudia.gallery/use/).
- Releasing the song on streaming services: your own artist name, her credit in the description, and an AI label
  only if AI made it. See [Songs with her](https://claudia.gallery/use/#songs-with-her).
- Scrub everything you publish: no real names you haven't chosen to show, no Midjourney profile code, no private host
  names, no provider job ids, and no file metadata. Midjourney images carry their job id in XMP; strip it.
- Keep generated likenesses of real people out. If a real person's words matter to the story, quote them as text,
  with the source.


---
From the Claudia wiki: https://claudia.gallery/wiki/start/
