# Phase A protocol: shot-boundary verification (per chunk)

Goal: turn auto-detected "disturbances" (work/disturbances.json) into a frame-accurate, visually verified
list of shot boundaries and in-shot transition/flash events for one time chunk of the video.

Frame convention: 0-based frame index, 24 fps, time = frame/24. A boundary is the FIRST frame of the new
shot. work/f960/NNNNN.jpg is frame NNNNN at 960x540 (use these, never re-decode the video).
Disturbance "step i" = change between frame i and i+1; `first_frame_after` = peak_step+1 (a hint, not truth).

Make sheets with:  /home/reggie/miniconda3/bin/python -I <root>/scripts/viz_frames.py <root> <out.jpg> <cols> <tile_w> <spec>
spec = comma list of frame indices or a:b:step ranges (b inclusive). 6 cols x 320px tiles x 6 rows is a good sheet.
Write sheets to <root>/work/phaseA/chunk<k>/ . View them with the Read tool (image). You MUST look; metrics alone are not evidence.

Procedure
1. Coarse pass: view the whole chunk at ~1 frame/s (step 24) to understand what content appears, in order.
2. For EVERY disturbance in your chunk (see work/disturbances.json, field chunk==k) view frames peak-4 .. peak+4 (or wider for gradual
   ones: whole span +-4) and decide: is it a shot boundary (new source image/clip) or something inside one shot?
3. Look for MISSED boundaries: view dense strips (step 3-6) of any stretch longer than ~3 s with no boundary, and any "minor_change"
   disturbances; slow dissolves and cross-fades have low per-frame metrics.
4. For each boundary give the exact first frame of the new shot (for dissolves/wipes: the first frame where the incoming
   picture covers >=50% of the frame; also give the span of the whole transition).
5. Classify using ONLY these types:
   hard_cut | flash_cut (cut hidden by 1-3 white/colour flash frames) | whip_cut (motion-blur whip/push hides the cut) |
   dissolve | fade_black | fade_white | shape_wipe (vector cut-out/blob/star/geometric mask reveal) | light_wipe (light-leak/streak sweep revealing next image) |
   glitch_cut (datamosh/RGB-split/scanline tear) | match_cut | zoom_punch_cut | strobe_burst (a rapid run of 1-2-frame images; list each
   constituent frame range) | other (explain)
6. In-shot events that are NOT boundaries (flash pulse, light leak sweep over the same picture, grain/glitch burst, snap zoom,
   graphic/HUD/text swap, speed ramp, camera whip inside the same take): record under in_shot_events with frame_range and type from
   flash | light_leak | glitch | hud_swap | text_swap | zoom_punch | camera_whip | speed_ramp | strobe_pulse | other.
7. Sub-3-frame segments: if the new shot lasts < 3 frames, do not make a boundary per frame; make ONE strobe_burst boundary with
   `constituent_frames`.
8. Be honest. If uncertain mark confidence < 0.6 and say why in `uncertainty`. Never invent; never merge two different cuts.

Output file: <root>/work/phaseA/boundaries_chunk<k>.json
{
 "schema":"ev-phaseA/v1","chunk":k,"frame_range":[start,end_exclusive],
 "chunk_content_summary":"3-6 sentences in order of what the chunk shows (for sanity)",
 "boundaries":[
  {"boundary_id":"B<k>-001","dist_ids":["D0012"],"first_frame_of_new_shot":int,"type":"...",
   "transition_span":[start_frame,end_frame],        // [f,f] for a clean hard cut
   "constituent_frames":[[s,e],...],                 // only for strobe_burst
   "prev_shot_last_frame_desc":"...","next_shot_first_frame_desc":"...",
   "evidence":"what you saw in which frames","confidence":0.0-1.0,"uncertainty":"..."}
 ],
 "in_shot_events":[{"dist_ids":[...],"frame_range":[s,e],"type":"...","description":"...","confidence":0.0-1.0}],
 "rejected_disturbances":[{"dist_id":"D0007","reason":"..."}],
 "missed_cut_search":{"method":"what stretches you re-checked and at what step","found":[boundary_ids]},
 "unresolved":["..."]
}
Every dist_id in your chunk must appear in exactly one of boundaries / in_shot_events / rejected_disturbances.
Boundaries you own: first_frame_of_new_shot within [start, end_exclusive). The first shot of the whole video starts at frame 0 (chunk 0 does not need a boundary at 0).
Then run:  /home/reggie/miniconda3/bin/python -I <root>/scripts/validate_phaseA.py <root> <k>   and fix errors.
