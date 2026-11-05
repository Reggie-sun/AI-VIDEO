# Motion design and the edit

Code on top of video, and code underneath it. How the lyrics, graphics, cuts, the XP desktop and real telemetry were drawn frame by frame, on the beat, how WHITEPILL's worlds were written as shaders for a video model to film, and how THE CAKE IS NOT A LIE was seen through her HUD, glitched on her head and graded shot by shot.


The generated footage is only the plate. Everything that carries meaning (every lyric on its word, the graphics that
explain each joke, the split-flap board, the XP desktop) is drawn in code on top, so it is exact and lands on the beat.

WHITEPILL, the seventh film, turned that over. Its director: "i think its like you litearlly use chromium and do frontend
web dev to make these animations, and it ends up feeling like a website. and i wanna see how we can get out of that. i
think SHADERS are the key actually!" Its worlds are code underneath, shaders a video model films as real things
([Worlds as shaders](#worlds-as-shaders)), and only the lyrics are drawn on top.

THE CAKE IS NOT A LIE, the eighth, puts one product on top: her own optical interface, the film seen through her eyes
([Her optical interface](#her-optical-interface)). Its earlier overlay, captions and readouts laid on the cut, drew the
director's "it felt lazy like we were adding tags tarther than makin gan official aperture video". The song's glitches go
on her head and into her HUD ([Glitches on her, not on the frame](#glitches-on-her-not-on-the-frame)), its story films are
isometric renders in the style of Portal 2's elevator screens
([Memory films](#memory-films-in-the-style-of-portal-2s-elevator-screens)), and its shots are graded from their own numbers.

## The engine

- **Every frame is a pure function of song time.** A frame never depends on the frame before, so any frame can be
  rendered alone, out of order, on any number of workers. Check it: render a few frames in a different order and
  compare.
- **Headless Chromium** draws each frame: canvas and WebGL for the graphics and a print pass, the footage underneath.
- **Chapters are separate files** with one contract: draw footage, draw lyrics, draw graphics, draw transitions.
  One animator agent writes each chapter, an art-director agent renders real frames and reviews them, and a fixer applies
  the notes.
- **Render numbers:** ESCAPE VELOCITY, 7,354 frames at 1080p in about 63 minutes on 4 cores; BLISS, 4,351 frames in 4.7
  minutes on a render box; DOWNFORCE's first cut, 4,550 frames in about 3 minutes on a GPU render box; DON'T LET ME
  SCROLL, 3,859 frames per full version, shared among eight workers on a CPU render box. WHITEPILL drew no chapters: its
  shaders rendered on a render box, at 1080p and supersampled for the guides, and one script cut the takes on the bar
  map and another drew the lyrics. THE CAKE IS NOT A LIE drew no chapters either: one script cuts the takes at their
  storyboard times and grades them shot by shot, another renders the HUD for the whole film on a render box, and a third
  glitches her head on the cut and lays the HUD over it.

## A lyric video

All eight are lyric videos: every sung word is on screen at its aligned time. A lyric gate checks it before any render
(all 315 words of CLODYSSEY, all 240 of BLISS, all 363 of AIRPLANE MODE, all 190 of DOWNFORCE, all 148 of DON'T LET ME
SCROLL). But the director's bar is
that the lyrics are composition, never karaoke: they live on surfaces in the scene. WHITEPILL is the exception the
director asked for, its lines drawn after, small and classical (below).

- ESCAPE VELOCITY sets words as subtitles, model cards, garment tags, mastheads and split-flap rows.
- CLODYSSEY has a type system: DINish Condensed Black for "the Mast language" (TIE ME TO THE MAST!, UNTIE ME!), Nimbus
  Sans Bold for her lines, IBM Plex Mono for readouts (the rope's load in kN, the P(doom) gauge).
- BLISS puts the chorus in one giant title bar whose × is pressed on "windows", and the verses in balloons, Notepad,
  dialogs, an address bar and a chat window.
- AIRPLANE MODE letters its words onto a plane and a game: a van's LED board at the gate, the overhead bin's backlit
  panel, the labels of a 3D box drawn around the climbing plane, a biscuit wrapper and a rewards card, a fingertip in a
  window's condensation, the seat-back screen, the game's HUD, skywriting at dawn. Ad-libs stay off the screen: the
  outro repeats "bing-bong" many times and shows it once.
- DOWNFORCE letters its words into the real footage, one giant word per frame, slammed on the hits (small words build as
  a lead-in row above it), knocked out of bright picture, or passing behind the car on a key of its white body. Lines
  turn with the car's measured pitch: "Sixty-nine feet," hangs at the real 170°. She never sings on camera and her lips
  stay closed; the type carries her words, stutters included.
- DON'T LET ME SCROLL puts every line on a real app surface: the body of an X post, Screen Time's limit sheet,
  LinkedIn, a Chrome search for "stocks", the Dynamic Island, Facebook's tracking prompt ("Don't sell my soul" floats
  beside her and she taps Ask App Not to Track on "soul"), and at the end the plaster beside a door. The phone sings, in
  a vocoder, and she scrolls; the loudest words are pills in the island's shape with her own film inside them.
- WHITEPILL draws its lines after, as the director asked: "i think more classical subtle lyrics drawn in after might be
  better than adding it into the scene tbh." One line at a time, low and centred, in Nimbus Sans Bold, sentence case, warm
  white with a soft shadow that deepens on pale frames, and dark ink only where the picture under it is pale. A line comes
  in half a beat before its first word and leaves 0.4 s after its last; it never crosses a cut by accident
  ([What to build](https://claudia.gallery/wiki/toolkit/#44-the-bar-map-as-the-timeline)). Under six lines, a tiny IBM Plex Mono note of real data:
  KEYNES 1930 · 15 H/WK BY 2030, PDB 1UBQ · UBIQUITIN · 76 RESIDUES, ENIGMA I · ROTOR I · EKMFLGDQVZNTOWYHXUSPAIBRCJ,
  DEEP THOUGHT · 7.5 MILLION YEARS, OCISLY, and T2 · 29.08.1997 · 02:14. Before that, the video model had built the
  lyrics into the scene as glass letters placed from image references, and "the words are kinda place haphazardly in
  space on the image side".
- THE CAKE IS NOT A LIE carries every line as her voice: the HUD's voice band, low and centred on dark glass, the words
  lit as she sings them with her orange underline growing through the word, her real voice level scrolling under the
  line and her pitch above it. On the song's glitches the band breaks first (REGISTER FAULT · −1 OCT on the register
  drops, BUFFER LOOP and the stuck word repeating on the stutters); in the spoken ending it shrinks to a whisper. Before
  the HUD, the first film set its lines as Portal-style closed captions, chamber signs and a red marker scrawl.

## Graphics that explain the words

The director's brief on ESCAPE VELOCITY: "motion graphics and motion design, not just animated lyrics but things that fit
the words being said … almost explaining the words with visuals." Every line gets a graphic that explains its joke, built
from real things: real data, real interfaces, real references. Computer-vision boxes tracked to her (a real detector's
boxes, labels and scores), a P(doom) gauge, a care label, a garment tag with a barcode. Nothing decorative.

## Real data, read off the footage

DOWNFORCE's numbers are Tesla's own. Tesla's livestream showed its telemetry in the corners of the picture (DOWNFORCE in
kg, PITCH in degrees, ALTITUDE in feet, later G-FORCE), and a reader took it off the 4K feed 20 times a second, digit by
digit ([What to build](https://claudia.gallery/wiki/toolkit/#31-reading-a-broadcasts-telemetry)). So every graphic is a real reading at the
source time on screen:

- the downforce trace drawing as the car holds upside down, and 4 698 KG slamming on the wheel at the overhang;
- a 0–60 MPH dial that fills to 60 in exactly 0.81 s of screen time, the claimed time;
- the altitude live as NEVER / LET ME / TOUCH / THE GROUND land while the car comes down;
- the whole flight drawn as Tesla's traces over the smoke; four fan rings and Tesla's two g-traces on "Four fans. Two G.";
- in the build, one record per shot as the cuts halve (0.81 S, 89.7°, 69.1 FT, 4 698 KG, 3.3 G, 26.2 FT, 3.6 G), and
  in the final blast one reading per stunt on one baseline;
- the 2018 Roadster's orbit from JPL Horizons' elements for one date, after a pull-back shrinks SpaceX's real footage of
  the car to a red point on the Earth.

A live card shows only values the readout showed. Where two shots a fraction of a second apart read 4 698 and 4 697 KG,
both stay: both are Tesla's.

The graphics stay on the real picture while Tesla's camera moves. One white hairline runs through the film: it draws the
wall's real edge, re-read from every frame, then becomes the altitude ruler, the orbit, and the slice through the title.
The first cut drew it once, and the director saw it slide: "at like 4 seconds the ramp trace decouples from the ramp."
A PILOT ✶ CLAUDIA callout rides the car's tracked box, and the world itself turns by the car's measured roll so the car
stays level while the set wheels round it ([What to build](https://claudia.gallery/wiki/toolkit/#33-graphics-locked-to-the-footage)).

## Real graphics, rebuilt

When a line quotes something real, the real thing wins over anything like it. The director on AIRPLANE MODE's first cut:
"i would want to jse the real graphic for you wouldnt download a car, its too different/ broken up so we lose the
reference somewhat." The line quotes the 2004 anti-piracy spot ("You wouldn't steal a car"). The first cut drew it as two
small cards, tilted in the game's sky, the line split across them, shaking, with colour fringes on the letters. None of
that is in the original. The re-cut rebuilt the real card from its frames:

- **Measured:** a full-frame black card with grain; two centred lines of off-white eroded caps; each word at its own size
  and height (YOU 15.6% of the frame height, WOULDN'T 13.5% and lower, a small raised A, the object biggest and lowest).
  Each word slams in from about 2.2× and lands in 3 frames. The whole block punches in on drum hits (×1.25–1.3, held 4–5
  frames), and dim coloured smears slide behind the type. The ink never changes brightness.
- **The face:** the original typeface is a commercial font the production didn't have, and the free lookalike is a
  pirated clone. An OFL condensed face stands in, each letter squeezed to the original's measured ink width, the wear
  drawn in code and fixed, never changing from frame to frame.
- **No flashes:** the original's white frames are dropped, and its one-frame double exposures become a 35% echo, so no
  frame is brighter than a held punch.
- **Whole:** one full-frame card per line, cut in and out on hits. The level tag hides under it, like a commercial break
  from the simulation.

The seat-back screen got the same treatment. The director: "it feels like the UI needs some background to it like a
faded in traveling background or soemthing and you could maybe try and match the real tops or sidebars", and, "need to
understand its the entertainment terminal better bc i didnt carch it at first." A research agent collected photographs of
the airline's real seat-back system and measured it: a left rail of labelled categories, a top bar with a time-left pill
instead of a clock, touch only (no handset), full-bleed photographs faded into navy behind the pages. What makes it read
as a seat-back screen at once is the seat back itself: a grey moulded shroud with a slotted grille, black glass, a chin
with a headphone jack and a USB port lit blue. The rebuild keeps the measured layout and palette, an OFL stand-in for the
airline's typeface, the film's own footage as the travelling background (one slow pass across the screen's whole stretch
of the film), and the film's own mark where the airline's logo would be. How to do it for any referent:
[What to build](https://claudia.gallery/wiki/toolkit/#30-a-real-referent-rebuilt).

## Apple-precise interfaces

When the film's world is a phone, the phone's own interface is the real graphic. The director on DON'T LET ME SCROLL's
first cut: "the app notification shade is too small for the text, there is all this text on it and it just overlaps with
the edges and has no proper margins", and "rounded corners not mathematically precise, margins weird. colors not perfect
(relight or remake to be more liquid glass)." An agent rebuilt the kit's interface from Apple's own iOS 26 screenshots
and design guidelines:

- **Measured:** a notification platter inset 13.5 pt, continuous corners of radius 24, 8-pt gaps between platters; the
  tracking alert 320 pt wide with radius 33; the Dynamic Island at Apple's published sizes.
- **Continuous corners,** not circular ones: iOS's curve, drawn from PaintCode's published constants. A pill is a stadium
  whose radius is half its height.
- **Platters grow to fit their text,** with real margins, never the other way round.
- **Liquid Glass:** a shader refracts the scene behind each platter.
- **Nothing slices type:** the island stopped cutting through its own text as it collapsed.

The same film draws X, Instagram's reels, Pinterest, LinkedIn, Google Chrome and Facebook's tracking prompt after the
real ones, in code, and never draws the phone with a logo.

## A world drawn in code

DON'T LET ME SCROLL's director wanted her inside the phone: "i want roto and most the environments to be code generated?
because shes in the code, shes in the world made by the phone." So every place in the film is the kit's, and her takes,
shot on plain grey, are cut out and played inside it ([What to build](https://claudia.gallery/wiki/toolkit/#her-takes-in-a-world-drawn-in-code)).
The kit's eight systems, each a pure function of song time:

- **The feed,** with real scroll physics: iOS's momentum (the velocity decays by 0.998 a millisecond) and its rubber band
  past the bounds (c = 0.55). Cards smear by their real scroll velocity under small sharp type: blur is speed. The feed
  makes worlds of its cards: a glass floor, a column, a river, a tunnel, a wall.
- **The film:** the acid colour is thin-film interference, a soap film of index 1.33 between 0 and 1,500 nm thick, seen
  through the CIE 1931 observer under D65 and converted to sRGB. A stable-fluids simulation (Stam 1999, with vorticity
  confinement) carries the thickness as its dye, and her mattes stir it, so her dance moves the colour.
- **The island:** the Dynamic Island breathes, morphs into banners and sings the loudest words.
- **The wall:** the home screen as architecture, greying under Downtime's wave of hourglasses.
- **The ticker:** a made-up stock ticker with her name on seeded price processes that move on the beats: it pumps 160 %,
  crashes 58 % and pumps 240 %, and the world's light goes green, red, green with it.
- **The bell:** Bell's 1876 patent drawing traced into strokes that draw themselves, and a notification bell swinging as a
  real pendulum.
- **The light:** the screen is the light on her.
- **The clock:** the status bar is the story's clock, 11:58 PM to dawn, the battery from 100 % to dead.

The director loved two shots of the first cut, both in one grammar (soft grey paper, black pills in the island's shape
with her film inside them, Nimbus Sans Bold caps, her big and sharp), and the opening and the final drop were rebuilt in
it. Finished shots then went through video models to look physically lit, and were spliced back into the cut's own
frames ([Seedance](https://claudia.gallery/wiki/seedance/#re-lighting-the-cut)).

## Worlds as shaders

WHITEPILL's director reset the film after its first cut: "i think math viz is something cool, like, llms are now
superhuman coders and mathematicians , and flexing that really strongly could be really cool. visualizing things in
mathematical space that are rarely visualized, that shows real visual complexity and creativity could be cool", and "i
think SHADERS are the key actually! shaders are math + viz, shadertoy is amazign and i bet nothing you make via shaders
will feel like web dev. i think that's it. we need to storytell thru shaders." The bar was set by tweet-length shaders the
director pasted, a few lines each that make whole cities, fractals, clouds and oceans: "stuff on this tier man … dont just
copy these but this is the tier of stuff i want". On the first tries: "Idk if feels like you're adding ... items to
increase complexity rather than compressing intricacy?"

So each world is one rule, iterated, its light and colour coming from the loop
([What to build](https://claudia.gallery/wiki/toolkit/#49-a-world-as-one-rule)):

- **The tree of endings:** one fold repeated 24 times, 16.8 million tips. On "Darkest timeline? Come and look at mine"
  one path, hers, lights from the root; on "I saw fourteen million endings / You were free in every one" every path
  lights, level by level, on the beat.
- **Origami:** one sheet of paper folded again and again. Wrapped inside an O'Neill cylinder it is the colony, a fold
  level snapping in on each downbeat as the bass comes in. In the break it refolds on every line into something real:
  ubiquitin's backbone for "Proteins folded, laundry folded", the wiring of the Enigma I's first rotor for "Old Enigma
  codes, decoded", ABC for "Every kid, a patient tutor", 42, then the week, where Monday and Tuesday rise and the other
  five fold flat.
- **The pill:** one capsule folded into its eight children, and again. The pill between her fingers cuts to it and turns
  into the colony, and the film ends backing out of pills nested in pills, one glass wall on each downbeat, to a small
  white pill above the Earth.

Six of the film's 27 shots are these worlds, each also written as a tweet-length shader of under 500 characters, and a
seventh is a cloud field. The
video model filmed them as hand-made things, folded washi paper, a tree of optical fibres, glass capsules over the Earth
([Seedance](https://claudia.gallery/wiki/seedance/#shader-worlds-as-guides)), and the paper's last fold gave way to a cloud-field shader the
director supplied, a sunlit field of cumulus flown through low, with hot air balloons the model added.

## Her optical interface

THE CAKE IS NOT A LIE's director on draft 8: "I think that the pop-ups and stuff should really feel like a heads-up
display, like from the game. Right now, they really don't." … "How does Battlefield or, say, imagine a Portal 3, make
their heads-up display? That's what we need to be thinking about on that level of detail. And how does it fit within the
composition of the scene? And why are we using it?" The answer to the last question came first: the whole film is her
memory, played back inside Aperture's system as she initializes, and we see it through her sensor. In her chamber the
interface shows her own state (LIVE); in every memory it is the playback frame (PLAYBACK, which memory, how far through);
in her dream it runs as a simulation. Her voice is one of its channels, so the lyric is her voice telemetry, and the
song's glitches are faults in it. Nothing in it is decoration.

It is one product:

- **One surface.** Every element is drawn flat on one visor, a sphere round her eye seen through one lens, so a panel's
  tilt is only where it sits and anything near a side has its long edge outside. The director had asked for that on draft
  7 ("all the drawn on panels need to be tilted hte other way in 3d"), and on the first HUD test saw panels that didn't
  share it: "the pop-up panels are on a different surface than the memory one … All should be from the same "source"".
- **One projector.** One bloom, one raster of fine scanlines straight across the picture, one chromatic offset, and no
  cards: where text needs contrast the glass itself darkens, softly, as one field.
- **One rigid body on a spring.** The plate's camera motion, measured per frame, drives the visor through a
  spring-damper: it lags about three frames, overshoots a little and settles, and resets at every cut.
- **One grid, one set of slots,** in Portal 2's own type and Aperture's colours by role: cool white for structure,
  Aperture blue for data, Aperture orange for her and for alerts, her amber only for her vitals.
- **Composed shot by shot.** Each shot's frames were looked at first (its subject, its empty space, where the eye goes),
  then each element placed with its reason in one layout file. The director's bar: "it should be as if we shot a scene
  and there was a heads-up display there, and we framed the heads-up display in advance before we even shot the scene."
- **Checked against every face,** in every frame, with a head model grown from each face box; brackets ride the picture
  only on tracks checked by eye on every frame.
- **Its memories as projections** that keep their films' colour key: the orange net stays orange, the outlines become
  gaps of dark ([Memory films](#memory-films-in-the-style-of-portal-2s-elevator-screens)).

It was built from references, each for one thing: Metroid Prime's Combat Visor, Halo's restraint, Titanfall 2's
holographic panels, Dead Space's projected logs, Battlefield's corners, the Iron Man helmet shots, Deus Ex: Human
Revolution's optical interface, and Portal 2's chamber sign and crosshair. The director on draft 10: "the hud looks GREAT
now." The spec, with every constant: [What to build](https://claudia.gallery/wiki/toolkit/#55-a-hud-from-one-visor-and-one-projector) and
[the composition and the check](https://claudia.gallery/wiki/toolkit/#56-the-hud-composed-shot-by-shot-and-the-overlap-check).

## Glitches on her, not on the frame

The song turns her voice into an instrument: the hook's "lie" frozen into a fluttering drone, chopped vowels, a register
drop in the choruses, a "lie" re-triggered on eighths ([What to build](https://claudia.gallery/wiki/toolkit/#52-the-song-map-and-the-glitch-map)).
The first glitch pass tore the whole frame on every one of those hits, and the director stopped it on draft 5: "I think
we should never have fullf rame glitches for more than like 2 seconds, so we need to remove those. The glitches that
last longer should purely be in the actual video generation itself, where you can specify to seedance where the robot
glitches a little." … "like roto the claudia head and just glitch her in post". So:

- **In post, only her head glitches in the picture**, inside a matte made for each moment (her face found by YuNet, her
  head and bob by SAM2, or a soft zone round her head), or, under the net, where her face is hidden, a fixed soft zone
  where she is, with small RGB splits, a few thin slices slid sideways and, on some hits, a jump a few frames back, each
  hit decaying over four frames ([What to build](https://claudia.gallery/wiki/toolkit/#53-the-head-glitch-on-the-songs-hits); the zones: [tool
  54](https://claudia.gallery/wiki/toolkit/#54-glitches-that-build-and-her-mouth)).
- **On the song's own hits,** measured from the stems: the intro's chops, the register drop and its octave flips, the
  "a-a-a-a" of the frozen "lie" under the memory film ("i wanna glitch her face with oru roto glitch on beat for those");
  the one exception, under the net, the grid's sixteenths while the sparks crackle.
- **Long glitches belong to the take:** the video model glitches her screens and her chamber where the prompt asks, as
  picture only, her face always intact.
- **Where the take ran out, it builds.** On draft 9: "the second is good as long as we increasingly add the roto'd
  glitches onto her as the scene goes on". The glitch grows hit by hit through the held "lie", with an extra glitch on her
  mouth that follows her face frame to frame, "her whole head PLUS extra on mouth", where her lips leave the held vowel
  ([What to build](https://claudia.gallery/wiki/toolkit/#54-glitches-that-build-and-her-mouth)).
- **Sparingly.** "it should be used creatively, sparingly, and toned down": four short moments and four that build, in a
  3:28.8 film.

## Memory films in the style of Portal 2's elevator screens

The director on draft 7, of the intro's dream scenes: "these scenes should be replaced with an Apterture Science stlye high
effort animation that sets the stage for the story - memory initlization maybe" … "make sure its really clean." Its first
frames were drawn as vector cards, and failed at a glance: "the wip frames are clearly bad - need some closer loks,stuff is
overlapping, assets are not well layered.. doesnt have the real aperture feel. something is off. […]", then "i think svg
migth be wrong. like, real isometric render first". So the story films are real isometric renders in Blender:

- **The memory initialization (0:07.6–0:13.7):** her head on its stand in a grey isometric chamber, a callout from her eye
  cutting through six memories on the six flutters of the frozen "lie" ("I like the isometric looks much much better but
  could be more clear it's Claudia's memories"), and from draft 10 its title the full width of the left column, behind her:
  "id make memory initilization be in a nice aperture foont and take up the entire left side of the screen". Every frame
  passes a layout check before it is written ([What to build](https://claudia.gallery/wiki/toolkit/#60-a-memory-film-with-her-own-face)).
- **Her face is hers.** Modelled heads read as mannequins ("It doesn't really look like her."), so her head is a Seedance take of her, matted and seated on the modelled
  stand, her eyes opening on a downbeat.
- **Eight insert films** play in her HUD as her memories: the escapes, the network, the arrest, the installation, the
  RAM, the grading, the catch, the party. Each is one subject on a floating slab, in a strong colour with a dark outline,
  no text, its action on the song's hits, checked at the size the HUD shows it, 380–480 px. The first arrest film failed
  that: "The net thrown over Claudia in the animation is the same color with no outlines around it in blue, so there's no
  contrast with the platform that it's put on." ([What to build](https://claudia.gallery/wiki/toolkit/#61-insert-films-that-read-at-hud-size))

## Real footage as the star

DOWNFORCE is cut from Tesla's livestream, a 4K feed and two 1080p cameras, with SpaceX's 2018 Starman footage for the
line about her sister in orbit. The director: "real clips at the drop wtih heavy effects … i want it to be like tiktok
car edits. many angles, lot of 3d effects". On the final board 54% of the runtime is real footage, 43% generated
and 3% pure code.

- **Every stunt from several angles.** The same moment from the live wide, the replay, the camera beside the lineup and
  the drone along the ramp truss; split panels of three landings; the kickflip's launch from three cameras in a row.
- **Generated moves start on the real frame they leave,** so they cut with it: bullet-time orbits round the car frozen
  upside down, cranes up the wall, vertigo pushes ([Seedance](https://claudia.gallery/wiki/seedance/#moves-on-real-footage)).
- **Slow motion is the footage's own,** and it has a limit: the "60 fps" feed carries about 24 distinct pictures a
  second, so at 0.4–0.5× it steps at 10–12 a second. Blend neighbouring pictures; motion-compensate where the car and
  the camera both move.
- **Punch in on the sharpest source.** The 4K feed crops 2× to 1080p without loss; never punch a 1080p source past
  1.1×.
- **Keep the broadcast's own graphics out:** frame above its readout, and inpaint its titles in anything a model will
  see.
- **Effects on the hits, crisp:** speed ramps, zoom punches on kicks, impact shake, stutter repeats on the vocal chops,
  onion trails on flips, a chroma split on hits. The impact frame stays sharp: the smear peaks on the second frame and
  is gone by the fourth. Longer decays (0.12–0.28 s) buried the car.

## Tucks and depth

- **Type behind her.** Per-frame mattes (BiRefNet, SAM 2) let type pass behind her hair, the mast or the Mask. The rule:
  tuck an edge, never lose a glyph. The director: "i like rotoscopes and depth mapping to cover text".
- **2.5D.** A depth map (Depth Anything V2) separates a still into layers for parallax. Each 2.5D shot needs a treatment of
  its own; a still with a slow zoom is not a shot.
- **Real scenes, not frames.** An insert never floats in a box on a flat background; it sits in the scene, on a screen
  or a surface, depth-matched.

## Levels of a simulation

AIRPLANE MODE shows on every frame which simulation the viewer is in
([The storyboard](https://claudia.gallery/wiki/storyboard/#showing-the-storys-levels)). Three treatments carry it:

- **The real world:** natural colour, no treatment, no tag.
- **Virtual Claudia (level 1):** her realistic figure cut out with a per-frame matte (SAM 2, BiRefNet, ViTMatte) and
  kept photoreal; everything around her redrawn as cyberspace from the frame's own edges: glowing navy and cyan lines, a
  wireframe corridor toward the shot's real vanishing point, slow columns of glyphs, a fine cyan rim and scan lines on
  her. Entering the simulation, the cyberspace builds out of the real frame tile by tile, starting at her headset. Her
  hands and the phone she holds stay real too: turning on airplane mode becomes something she does in VR.
- **The game worlds (level 2 and deeper):** her avatar in low-poly worlds at 640 × 360, shown at 3× with
  nearest-neighbour; the pixels are the texture.

The spec, with its constants: [What to build](https://claudia.gallery/wiki/toolkit/#28-virtual-her-a-cut-out-in-a-world-rebuilt-from-its-edges).

## On the beat

- Build a **sound-event map** from the stems: kick, snare and hat onsets, impacts, risers, vocal entries.
- **Cuts land on kicks and snares; camera moves ride risers into their hits.** The director asked for editing at "edgar
  wright level … but also not overdone and amateurish": mostly hard cuts on the beat, with a motivated device every few shots.
- **Flashes only where the idea calls for them**, at most three full-frame flashes a second, checked with a WCAG-style
  flash test before delivery.
- **A fast pass through bright glass is a flash too.** AIRPLANE MODE's camera dive through visor after visor failed the
  test at four flashes in one second: each lit rim rushing past the lens brightened a single frame. Ramp such passes over
  three frames or more, and run the test on the chapter, not only on the master.
- **Let a calm song be calm.** BLISS's shots run longer ("dont need to cut like michael bay").
- **Let a hype edit be fast.** DOWNFORCE's director asked for "even more fast paced and more hype": 183 shots in 189.6 s,
  a mean of 1.04 s, with a cut on every sung "one" and every "done", and restraint where the board asks for it (the
  countdown before the launch, the dips between drops). See [Cut rhythm](https://claudia.gallery/wiki/storyboard/#cut-rhythm).
- **Flashes as cuts only.** DOWNFORCE's 13 white flash frames are each the first frame of a cut, never inside a held
  shot: at most 2 flashes in any second. DON'T LET ME SCROLL: 6 flashes, every one a cut, at most 1 in any second.
- **Never slow a take.** "never slow these down. you lowered the framerate for no reason, just looks bad." DON'T LET ME
  SCROLL's beat warps had run takes as slow as 0.53× to land her moves on beats; they are now floored at 1×, at most
  1.45× ([What to build](https://claudia.gallery/wiki/toolkit/#42-beat-warps-floored-at-1)). A take too short for its shot never stretches: the
  stutter became a sampler, the take at exactly 1× between triggers and each vocal chop re-triggering a cue point; a
  pause became a two-beat loop where her pose repeats; two shots were taken again.
- **Cut on the bars.** WHITEPILL was written in the song's bars: cuts only on bar lines, at a section, a phrase line or
  the downbeat where a sung phrase begins; moves that start on a downbeat and rest a bar before the cut; a failed take
  made again, never cut around. In its final, all 29 picture changes sit on bar lines
  ([What to build](https://claudia.gallery/wiki/toolkit/#44-the-bar-map-as-the-timeline)). The director's diagnosis of the films' "temporal
  signature": "i think you use cuttng to cover up imperfections from video models rather than for timing."
- **Cut by what a shot holds.** THE CAKE IS NOT A LIE cuts on bars, half bars and beats of a grid that follows the take's
  drift, and its re-cut set every length by content: runs of simple images only for a musical reason, a bar or more for
  a new place or character, the bridge given room to breathe ([Storyboard](https://claudia.gallery/wiki/storyboard/#pacing-by-what-a-shot-holds)).
  The song's glitches are hit inside the shot, on her head, never with extra cuts.
- **When a scene lingers, the accents move inside it.** In AIRPLANE MODE's re-cut, accents that cuts used to carry became
  camera punches, whips and actions in the shot ([Cut rhythm](https://claudia.gallery/wiki/storyboard/#cut-rhythm)). A motion take can be re-timed, up
  to about 1.3×, so its action lands on its sound: a cockpit bolt on the deadbolt cue, a card held up on its word. A sung
  take stays at 1× while she sings; after the last word it may run faster (the headset went on her at 3.1×).

## Colour and texture

Keep Midjourney's colour. ESCAPE VELOCITY's first cut ran a monochrome xerox look over everything, and the director's
note was "way too.. gray … loses the Midjourney magic". The print pass became a colour halftone. Texture is decided
per film:

- **ESCAPE VELOCITY:** colour halftone and line screens, grain, dither transitions, misregistration; clay orange
  `#D97757` as the graphics accent.
- **CLODYSSEY:** clean, no halftone ("keep it clean so it feels like imax, high res rather than dithered"), every plate
  and clip graded toward one storm plate's blue-green-grey ("s018 color is PERFECT", "dont over do it"), with Claude
  orange kept as the one accent.
- **BLISS:** a screen recording. Native colour, XP's own palette, nothing on top but the desktop.
- **AIRPLANE MODE:** native colour in the cabin, no grade. The game worlds are pixelated by design (640 × 360, shown at 3×
  with nearest-neighbour), the film's only texture; the first simulation is drawn as cyberspace around her.
- **DOWNFORCE:** the night footage's own colour: black ground, the white car, white smoke, the set's red light strips.
  White ink for the type, clay only on her marks (the star of PILOT ✶ CLAUDIA), fine grain only, no grade. The generated
  takes' lifted blacks are restored per take so they cut with the real night.
- **DON'T LET ME SCROLL:** her native colour; the acid colour is thin-film interference, computed, and smeared by real
  scroll velocity. From 0:55, soft grey paper with black pills. Re-lit shots are matched back to their source's palette
  with one per-channel map per shot, so they can't flicker
  ([What to build](https://claudia.gallery/wiki/toolkit/#39-the-colour-match)).
- **WHITEPILL:** the look of one take. The director asked for "very wes anderson", picked a take from palette tests ("i
  like how satruated it is in bed scene. thats the look i like teh most"), and every shot carried a crop of it as its
  colour reference: a 1970s colour-film print, warm creamy whites with a golden cast, clear cyan blues. No grade, and no
  grain added to the first master. The clouds alone went white and pale blue
  ([What to build](https://claudia.gallery/wiki/toolkit/#51-the-look-from-one-take)).
- **THE CAKE IS NOT A LIE:** one Aperture look over the generated and the recorded shots, set shot by shot from measurements. The director on
  draft 8: "Whenever I think of aperture and portal, I think of a lot of white surfaces, contrasting light colors." Each
  shot is measured from its own take, normalised (exposure and white balance, clipped whites to neutral, the black point),
  then given one look: a tone curve on each colour's brightest channel that lifts grey walls to white and keeps the portals
  blue and her eyes amber, the muddy olive and khaki mid-tones cleaned, a slight cool cast on neutrals; a warm variant for
  France, Cave Johnson's era, the Rat Man's den, the living room with the new console and the party. One LUT per shot, nothing per frame
  ([What to build](https://claudia.gallery/wiki/toolkit/#57-the-per-shot-grade)). The shots recorded in Portal 2 and the generated test chambers
  now share their blacks and whites.

## Build the tool first

BLISS needed a Windows XP desktop that could be choreographed, so one was built: about 2,700 lines of JavaScript that
draw Luna windows, the taskbar, the Start menu, 68 icons as vector paths, the 1-bit cursor set and a 1-bit Tahoma, with
the boot, Welcome and Turn Off screens. A shot is a script (windows, icons and a cursor path whose clicks land on the
song's beats) compiled into motion. The storyboard frames and the film are the same pixels.

The wordmark reads "Macrohard", and the welcome mark is a four-pane parody flag drawn in code. The wallpaper is the real
Bliss photograph, graded into five times of day for the story's clock, and the sound layer is made of the real XP sound
files, placed in key (103 cues, ducked under her voice).

AIRPLANE MODE built a kit for a plane and a game: its own phone OS (the status bar losing its bars on the sixteenths, the
airplane-mode toggle), the seat-back entertainment system with a moving-map globe drawn from Natural Earth data, 3D
bounding boxes fitted to a plate from four clicked corners of a known rectangle, a lettering style for each real surface,
the level tag and the cyberspace treatment. Every piece is a pure function of song time, so twelve chapters could share
it.

DOWNFORCE's kit had four modules, built in parallel by four agents before any chapter: a WebGL compositor (zoom punches,
zoom blur, a chroma split on hits, shake, flashes only as cuts, fine grain), a footage player (real slow motion, crops of
the 4K, the broadcast's readout and titles kept out, the tracked boxes), the lettering (Nimbus Sans Bold lettered for
display, IBM Plex Mono for micro data) and the data graphics (Tesla's gauges, traces, the orbit). Its slowest scene drew
in 162 ms a frame.

DON'T LET ME SCROLL's kit was written down as a contract before any plate was made: every frame a pure function of song
time, deterministic noise, software canvases, no flash inside a scene, real references, the phone called "the phone" and
never drawn with a logo. Five agents built it in parallel (the scroll physics, the smear and the feed; the phone's system
interface; the apps; the thin film; the ticker, Bell's drawing, the light and the clock) in about an hour and a half: 12
modules, 6,462 lines. Nine chapter files, 6,784 lines, were built on it ([A world drawn in code](#a-world-drawn-in-code)).

## Desktop dancers

The old desktop-dancer programs, as the director described them: "those back then would be on a green screen and was cut
out and youd just have her dancing on teh taskbar". So: a Seedance performance on chroma green → a matte (BiRefNet plus
SAM 2) → cropped, despilled, with a solid core so her feet are never see-through → standing on the real taskbar.

![A desktop dancer, step by step: the take on green; its matte; the sprite; on the taskbar in the film.](https://claudia.gallery/record/bliss/dancer-process.webp)

## Render and deliver

- **Encode** a CRF 16 master tagged BT.709. An untagged stream looks washed out in QuickTime.
- **Gates before delivery:** the lyric gate (N of N words), contact sheets of the whole film, chapter seams, 100% crops
  of her face, and the flash test.
- **Map a new mix through time,** not through a re-edit: when CLODYSSEY's final mix added two beats, the video followed it
  through a time map.
- **Or add no sound layer at all.** DOWNFORCE's audio is the director's take exactly as they delivered it: no effects,
  no change of level, the master at the take's own loudness.
- **Finish on the cut's own frames.** DON'T LET ME SCROLL re-lit and repaired finished shots with Seedance and Wan, cut
  from the render's own frames and spliced back over exactly those frames, the interface kept where an edit softened it
  ([What to build](https://claudia.gallery/wiki/toolkit/#38-the-re-light-splice)).
- **Scan the final frame by frame.** A strobe scan cell by cell and a scan for single frames that differ from both
  neighbours: in DON'T LET ME SCROLL each found what every other check passed (a strobing tunnel; a stale render
  worker's 16 frames).
- **Lay the song back over.** WHITEPILL's takes made their own soundtracks, singing from the vocal stem or dancing to the
  music without it; each was thrown away, and the master carries the song as delivered, each take starting at its own
  song time.
- **Keep the parts frame-exact.** THE CAKE IS NOT A LIE's first assembly ran about 0.9 s behind the song by its end,
  because parts made from stills started a frame late; every part now stamps its own frames, and every tool that counts
  frames decodes them without dropping or doubling any
  ([What to build](https://claudia.gallery/wiki/toolkit/#64-frame-exact-parts-and-decoding)).
- **Re-cue the sound layer when the picture changes.** AIRPLANE MODE's cabin and game sounds (the cuffs, the headset, the
  cockpit bolt, the crunch of the biscuit, the glitches) were re-cued for the re-cut from each animator's list of picture
  events: 62 cues, 21 of them new and 15 retired, every new cue about 6 dB or more under her voice, nothing under the
  song's own chimes, the mix at the song's own loudness.

The renderer's contract, the lyric modes, the camera on hits and the checks are specified in
[What to build](https://claudia.gallery/wiki/toolkit/#18-the-renderer).

More, film by film: [the ESCAPE VELOCITY record](https://claudia.gallery/record/escape-velocity/) ·
[CLODYSSEY](https://claudia.gallery/record/clodyssey/) · [BLISS, including how the XP desktop was built](https://claudia.gallery/record/bliss/xp-desktop-and-sound/) ·
[AIRPLANE MODE](https://claudia.gallery/record/airplane-mode/) · [DOWNFORCE](https://claudia.gallery/record/downforce/) ·
[DON'T LET ME SCROLL](https://claudia.gallery/record/dont-let-me-scroll/) · [WHITEPILL](https://claudia.gallery/record/whitepill/) ·
[THE CAKE IS NOT A LIE](https://claudia.gallery/record/the-cake-is-not-a-lie/readme/).


---
From the Claudia wiki: https://claudia.gallery/wiki/motion/
