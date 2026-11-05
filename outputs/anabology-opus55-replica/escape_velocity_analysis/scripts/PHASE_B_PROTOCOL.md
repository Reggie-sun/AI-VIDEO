# Phase B protocol: per-shot reverse-engineering records

You write `shots/shot_NNNN.json` (one per assigned shot) that a different agent, who never saw the video, can use to rebuild the shot.
JSON is the only source of truth; markdown is generated later by script (do NOT write .md).

## Ground rules
- Analysis only. Never generate media, never call paid/cloud APIs, never touch git. Write ONLY: `<root>/shots/shot_NNNN.json` for your shots and
  `<root>/work/phaseB/notes_<your-batch>.md` (free-form notes, new-asset proposals, cross-shot observations).
- Frame convention: 0-based, 24 fps, 1920x1080. `end_frame` inclusive. Time = frame/24. Normalised coordinates are `frame_norm_top_left`
  (x,y,w,h in 0..1 of 1920x1080, origin top-left) — convert from pixels (pixels/1920, pixels/1080).
- Shot boundaries are already decided (work/shots.json, produced from verified boundaries). Do NOT change them. If you believe a boundary is wrong,
  keep the shot as is and record it in `uncertainties` and your notes file.
- You MUST view images. For every shot: open its filmstrip `<root>/contactsheets/<shot_id>.jpg` and the keyframes listed in
  `work/shot_stats.json[shot_id].keyframes` (960 px). For HUD text, small type, numbers and fine detail extract full-res crops:
  `python -I <root>/scripts/extract_full.py <root> work/full <frame> crop=x,y,w,h,scale` (scale 2-3 for small text) and look at the PNG.
  For fast animation (flap flips, counters, wipes, typed text) build dense sheets with `scripts/viz_frames.py` (step 1-3 frames).
- Measure, don't guess: positions from full-res crops/pixel coordinates; colours from the palette in `work/shot_stats.json` or by sampling
  pixels with PIL (`/home/reggie/miniconda3/bin/python -I`); motion from `work/shot_stats.json[shot].motion` and your own frame comparison.
  Label visual estimates as estimates (`method: visual_estimate`) and give confidence < 0.8.
- Production hypotheses must use evidence_level exactly: `confirmed` (the author's own published pages say it — cite the source file and quote in `source_refs`,
  files are in `<root>/source_docs/`), `inferred` (visual evidence + technical reasoning), `unknown`. Never upgrade an inference.
  Useful author facts (confirmed in source_docs/FINDINGS.md): plates = Midjourney v8.2; moving shots = Seedance 2.5 via OpenRouter (clip table in
  FINDINGS.md section C maps song second -> clip -> storyboard shot -> plate); all type/graphics/HUD are drawn in code by a custom JS engine
  (headless Chromium, canvas + WebGL print pass, every frame a pure function of time); colour halftone print pass; clay-orange accent #D97757;
  2.5D parallax from Depth Anything V2 depth maps; Grounding DINO boxes for CV brackets; Deep Exemplar recolouring of some clips.
  Use the Seedance clip table (song start second) to say whether a shot's footage is probably a Seedance clip: song_second = frame/24 (the video IS the song timeline).
  If a shot lies inside a clip window [start, start+len] that is `inferred` (not `confirmed`) unless the shot id is stated.
- Do not invent fonts: give a visual description + candidates; fonts named by the author (DINish Condensed 900, Heros/Nimbus Sans Bold 700, IBM Plex Mono 500) are
  `candidate` only (the author's pages name them for the site/other films).
- Persistent chrome ("always-on devices") is registered once in `<root>/visual_system.json` under `global_layers` with `asset_id` G-*. In every shot do NOT
  re-describe those layers as elements; record their per-shot STATE in `persistent_layer_state` keyed by asset_id (e.g. look counter value, months-counter value,
  ticker text visible, timecode start value, whether the left ruler / spectrum / months widget is hidden or restyled in this shot, any deviation such as a white pill background).
  If a persistent layer is hidden, moved, restyled, or does something special in this shot, say exactly what.
- Everything else visible is an element: background media (the plate/clip itself), people/props, CV brackets and their labels, panels, charts, gauges, flap boards,
  counters, big words, lyric/caption text (every word and its timing), icons/markers, light streaks, masks, flashes, glitch, overlays specific to this shot, etc.
  Split into independent elements by motion/timing/role. A text line whose words enter at different frames is ONE element with per-word keyframes.
- Typography: record exact visible text (UPPER/lower case as drawn), approximate cap/x-height in px at 1920x1080, line height, letter-spacing character
  (tight/normal/wide/mono), weight, colour hex, alignment, anchor position (px and normalised), stroke/shadow, entrance/exit, and relation to sung words if audible in the lyrics.
- Animation: for every element give `keyframes` as [{frame, ...property values}] using the properties actually observed (x,y,w,h,scale,opacity,rotation,
  progress,value,text_visible_chars,...). Give start/end frames of entrance and exit; identify easing by shape (linear, ease-out, snap/step, overshoot, spring, typewriter at N chars/s, flap clatter...).
  Sample densely enough (look at every 1-4 frames around entrances).
- Audio: read `<root>/audio_timeline.json` (if present) / `<root>/audio/` only to fill `audio_events` (audio_event_id + relation + frame). If the audio files are not ready,
  leave `audio_events` as [] and note it; the lead will link audio later by timestamp.
- Be specific. Banned phrases: "sci-fi feel", "cool transition", "cinematic look", "dynamic text" with no numbers. Say what/where/how big/how long/which colour.
- Time budget: a typical 1-3 s shot deserves ~8-20 elements. A strobe burst shot should list each constituent frame range and what each frame shows.
- Keep uncertainties honest and itemised.

## shot JSON skeleton (schema: <root>/schema/shot.schema.json; every key below is REQUIRED)
Copy the timing fields from work/shots.json exactly: shot_id, start_frame, end_frame, start_time, end_time, duration_frames, duration_s, start_tc, end_tc, boundary_in_id.
Also put `"schema": "ev-shot/v1"`.
- reference_frames: [{frame, path (relative to <root>, e.g. keyframes/S0007_f00123.jpg), role: first|middle|last|key_change|detail|transition, note}]
  (at least first, middle, last; key_change frames you inspect and rely on should also be listed; you may extract extra frames with extract_full.py and list them as detail with their work/full path).
- scene_type, narrative_role (what job the shot does in the film's story/rhythm), subject, visual_complexity{level,rationale}, scene_description (>=60 chars, concrete),
- composition{shot_size, subject_position, subject_bbox{x,y,w,h,space:"frame_norm_top_left"}|null, subject_screen_fraction, camera_angle, layers{foreground,midground,background}, empty_field_for_type},
- camera{movement, direction, speed_profile, dof_focus, parallax_kind (none|real_camera|generated_video_motion|2.5d_depth_parallax|crop_scale_only|unknown), evidence, estimated_zoom_start, estimated_zoom_end},
- lighting{key_direction, quality, effects[], temporal_change},
- colors{palette[{hex,role,fraction,method}] (>=3; start from measured k-means in work/shot_stats.json, give each a role like shadow base / skin midtone / accent), contrast, grain_halftone (describe the halftone dot size/visibility you see; measured pitch table in <root>/halftone_pitch.json), temporal_change},
- persistent_layer_state{G-asset: state},
- elements[] (see element schema; element_id = `<shot_id>-E01`, `-E02`...; shot_id; asset_id for reuse e.g. G-* or N-<slug> for new reusable assets you propose),
  per element: type (enum in schema), description, start_frame, end_frame, bounding_box (x,y,w,h normalised at its typical/max size; also keyframes may carry positions),
  z_index (convention: 0 background media; 5 plate-derived layers (cut-outs/parallax slices); 10-19 scene props/CV brackets; 20-29 typography; 30-39 panels/charts/boards; 40-49 persistent chrome; 50 halftone/grain pass; 60 flash/transition overlays),
  text{content,case,typography{...}} for text, appearance{color_hex,opacity,blend_mode,details}, motion{path,easing,entrance,exit}, keyframes[], effects[], reference_frames[] (ints), confidence, uncertainties[], reconstruction_hint,
- animations[] (choreography summary: {anim_id,target_element_ids,description,start_frame,end_frame,easing,audio_sync}),
- in_shot_events[] (flash/light leak/zoom punch/etc. frames; start from the hints in work/shots.json[shot].in_shot_events but verify them),
- transitions{in:{type,boundary_id,span,description,driver,recommended_technique}, out:{...}} (use work/boundaries_all.json for the in/out boundary records and look at the frames),
- audio_events[],
- production_hypothesis{layers:[{layer,technique,evidence_level,rationale,source_refs[]}]} — separate layers: base footage; 2.5D/cut-out layers; CV/HUD/type overlay layer; print pass; transition,
- source_references[] ({kind: author_url|author_clip_table|author_prompt|inference_only|none, ref, note}),
- confidence, uncertainties[], reconstruction_notes{recommended_method (concrete: tools, layers, order), dependencies[], difficulty 1-5, difficulty_notes, alternatives},
- strobe_constituents (only for strobe bursts), author_vocab (optional: framing ECU..EWS, motion_tier still|plate3d|motion|sung, type mode subtitle|coverline|masthead|stack|mass, devices kinds like flap|sheet|cv.bracket).

## Procedure per shot
1. Read the shot's entry in work/shots.json, work/shot_stats.json, the filmstrip and keyframes.
2. For anything animated, build dense sheets and look at them; for text and HUD numbers look at full-res crops.
3. Write the JSON. Validate: `/home/reggie/miniconda3/bin/python -I <root>/scripts/validate_shot.py <root> shots/shot_NNNN.json` and fix errors.
4. After finishing all shots do a second pass: re-open 3 random shots' keyframes and check that every visible thing is listed (text, small HUD, particles, masks, overlays). Fix omissions.
5. In your notes file list: new reusable assets proposed (asset_id, description, which shots), cross-shot patterns, boundaries you doubt, anything unresolved.

## Final reply (short)
Shots written, validator results, number of elements, top 5 uncertainties, proposals for global assets.
