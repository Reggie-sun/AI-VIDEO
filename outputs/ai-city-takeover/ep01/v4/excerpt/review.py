#!/usr/bin/env python3
"""Review page and QA reports of the excerpt. Run from the repository root after qa.py (v1) and qa.py --v2:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/review.py

Writes index.html: v4 round 2 first (the s012 close-up a PLACEHOLDER still), then v4 round 1 (a window, song 36.22-50.93; the judged part is 39.674-50.93), then v3, then v2 and v1 the same way, then the EV strip. Originally (v2): v2 first (the stills-first re-edit: the video, six of its frames each beside the ESCAPE VELOCITY
frame it is measured against, cropped from the EV sheets ev-1..ev-4.jpg, 8 x 5 tiles of 240 x 135), the EV strip
(review/compare/ev-strip.jpg), then v1 (rejected 2026-11-18, kept) the same way; review/*.jpg; qa/QA.md and
qa/v2/QA.md from their qa.json. The HyperFrames compositions are composition.html (v1) and composition-v2.html (v2).
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edl import EXC, FPS, OFFSET, V4, V4R1_F0, frame_of  # noqa: E402

EV = V4.parent / "v3/review/compare"
VIDEO = "renders/IRIS-EP01-v4-excerpt-026-059.mp4"
# (song time, our note, EV sheet, row, col, what the EV frame shows)
PAIRS = [
    (28.90, "s007 · her line printed on the billboard's lit face (the leaves cover it), the $6,000 / MONTH tag hung "
            "from the branch, sourced", "ev-1", 1, 4, "EV: THIS IS NOT AN AI BILLBOARD typed onto the billboard"),
    (30.70, "s008 · the classifier drawn from the blank name sticker (A.I. printed on it, rows on the beat), "
            "subtitle low centre", "ev-1", 2, 6, "EV: AGI. / CGI. / CSI. readouts with size tags beside her"),
    (35.40, "s009 · 2.5D: focus racked to the lightbox, the ad printed on the glass, the scratch light through NOT",
     "ev-3", 0, 5, "EV: UNDERCLASS pressed into the frame with a soft shadow"),
    (43.60, "s011 · rows snapped on, NIGHT! tucked behind her, the ON CALL gauge on the B2 pillar, lyric lower left",
     "ev-2", 1, 2, "EV: LOCK as one giant word on the hit"),
    (53.75, "s013 · cutaway under her chin (no sung take): the incoming call, CALL / YOU HAD TO TAKE, ALL on the bar "
            "line, the card stamped ALL HANDS", "ev-1", 4, 1, "EV: Sorry. / ENCORE. mass line with the small line above"),
    (59.10, "s014 · push to the pager on Ten: its LCD and the 10:02:11 P0 readout with its source, the PAGED stack "
            "top right", "ev-2", 0, 7, "EV: the persistent flap device, top right"),
]


def grab(t: float, dst: Path) -> None:
    f = frame_of(t)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(EXC / VIDEO), "-vf", f"select=eq(n\\,{f})", "-vsync", "0",
                    "-frames:v", "1", "-q:v", "3", str(dst)], check=True)


def ev_tile(sheet: str, r: int, c: int, dst: Path) -> None:
    im = Image.open(EV / f"{sheet}.jpg").convert("RGB")
    im.crop((c * 240, r * 135, c * 240 + 240, r * 135 + 135)).resize((960, 540), Image.LANCZOS).save(dst, quality=90)


def qa_md(q: dict) -> str:
    ok = lambda b: "PASS" if b else "FAIL"
    L = [f"# QA · IRIS EP01 v4 excerpt 026-059", "", f"Render: `{q['render']}`  ", f"Overall: **{ok(q['pass'])}**", ""]
    s = q["spec"]
    L += ["## Spec", f"{ok(s['pass'])} · {s['width']}x{s['height']} · {s['fps']} fps · {s['frames']} frames · {s['codec']} "
          f"{s['pix_fmt']} · colour {'/'.join(map(str, s['color']))} · audio {s['audio']}", ""]
    a = q["sound"]
    L += ["## Sound (master, no loudness change)", f"{ok(a['pass'])} · offset against the master slice {a['offset_samples']} "
          f"samples ({a['offset_ms']} ms) · RMS difference {a['rms_diff_db']} dB", ""]
    L += ["## Cuts on beats (every cut within 0.03 s of a beat; the picture changes on that frame)", "",
          "| cut | planned | nearest beat | planned-beat | frame | frame time | frame-beat | render changes on | result |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in q["cuts"]["cuts"]:
        L.append(f"| {c['shot']} | {c['planned_t']} | {c['nearest_beat']} | {c['cut_dt_beat']:+.4f} | {c['frame']} | {c['frame_t']} | "
                 f"{c['frame_dt_beat']:+.4f} | {c['render_change_frame']} | {ok(c['pass'])} |")
    L += ["", f"Other frames whose change passes 80% of the smallest cut: {q['cuts']['unplanned_changes_above_threshold']} "
          "(in-shot events, each on a beat: f181-182 the s009 rack to the lightbox at 33.437, f332 ALL slammed at 39.897, f355 the s011 rows snapping on, f433 EVERYBODY, at 44.077, f709 the s014 punch at 55.542, f786-788 the push to the pager at 58.726; checked on the contact sheet).", ""]
    ly = q["lyrics"]
    L += ["## Lyrics", f"{ok(ly['pass'])} · **{ly['on_time']}/{ly['words']}** words of words.json inside 26.0528-59.2341 drawn on "
          "their onset frame, held 8 frames (or to their end / the excerpt end), none early. Source: the engine's own word log "
          "(snap.mjs --marks), every frame.", "", "| line | word | onset (s) | onset frame | first frame drawn | frames on | result |",
          "|---|---|---|---|---|---|---|"]
    for r in ly["rows"]:
        L.append(f"| {r['line']} | {html.escape(r['word'])} | {r['start']} | {r['onset_frame']} | {r['first_frame']} | {r['held_frames']} | {ok(r['pass'])} |")
    fl = q["flash"]
    L += ["", "## Flashes and single-frame jumps", f"{ok(fl['pass'])} · worst cell {fl['max_flashes_per_second_any_cell']} "
          f"flashes in any second (limit 3, WCAG 2.3.1 general flash on a 4x4 grid) · single-frame jumps: {len(fl['single_frame_jumps'])}", ""]
    ch = q["chinese"]
    L += ["## No Chinese on screen", f"{ok(ch['pass'])} · CJK in drawn strings: {ch['cjk_in_drawn_sources'] or 'none'} · CJK glyphs "
          f"in the shipped fonts: {sum(ch['cjk_glyphs_in_fonts'].values())} (the fonts cannot draw Chinese)", ""]
    rd = q["red"]
    L += ["## Red", f"{ok(rd['pass'])} · {rd['frames_checked']} frames (every 4th), {rd['frames_with_red']} with saturated red, "
          f"{rd['frames_with_red_outside_her_or_p0_over_12px']} with more than 12 px (at 960x540) outside her matte or the "
          "P0 ALERT RAISED label. Worst frames: " + ", ".join(f"f{w['frame']} {w['outside_px']} px" for w in rd["worst"][:5]), ""]
    L += ["Sheets: `qa/contact-every-6-frames.jpg`" + (", `qa/red-outside-map.png`" if (EXC / "qa/red-outside-map.png").exists() else ""), ""]
    return "\n".join(L)


PAIRS_V2 = [
    (28.90, "s007 · X07a · her line printed on the lit billboard (the branches cover it), the $6,000 / MONTH tag from the "
            "branch she pulls", "ev-1", 1, 4, "EV: THIS IS NOT AN AI BILLBOARD typed onto the billboard"),
    (30.90, "s008 · X08a · punched in on the beat to the sticker: A.I. printed on it, the classifier in the dark street",
     "ev-1", 2, 6, "EV: AGI. / CGI. / CSI. readouts with size tags beside her"),
    (34.50, "s009 · X09a · cropped on the bar line to the lightbox: the ad printed on the glass, NOT on the real scratch",
     "ev-3", 0, 5, "EV: UNDERCLASS pressed into the frame with a soft shadow"),
    (43.60, "s011 · X11a · rows snapped on, NIGHT! in the dark ceiling, the ON CALL gauge, lyric lower left",
     "ev-2", 1, 2, "EV: LOCK as one giant word on the hit"),
    (54.00, "s013 · X13a · CALL / YOU HAD TO TAKE, the call taken on 'take', ALL on the bar line, the card stamped",
     "ev-1", 4, 1, "EV: Sorry. / ENCORE. mass line with the small line above"),
    (59.10, "s014 · X14a · cut in on 'Ten' to the pager at her waist: its LCD and the 10:02:11 P0 readout",
     "ev-2", 0, 7, "EV: the persistent flap device, top right"),
]
VIDEO_V2 = "renders/IRIS-EP01-v4-excerpt-026-059-v2.mp4"


def badges(q: dict, qa_dir: str) -> str:
    ok = lambda b: "PASS" if b else "FAIL"
    ly = q["lyrics"]
    return f"""<div class="qa"><span>cuts on beats {ok(q['cuts']['pass'])}</span><span>lyrics {ly['on_time']}/{ly['words']} {ok(ly['pass'])}</span>
<span>flashes / single-frame jumps {ok(q['flash']['pass'])}</span><span>no Chinese {ok(q['chinese']['pass'])}</span>
<span>red only her + P0 {ok(q['red']['pass'])}</span><span>sound {ok(q['sound']['pass'])}</span><span>spec {ok(q['spec']['pass'])}</span>
<span><a href="{qa_dir}/QA.md">QA report</a></span><span><a href="{qa_dir}/contact-every-6-frames.jpg">contact sheet</a></span></div>"""


def pairs(video: str, plist: list, prefix: str, rv: Path) -> str:
    cards = []
    for i, (t, ours, sheet, r, c, evnote) in enumerate(plist, 1):
        f = frame_of(t) - (V4R1_F0 if "v4r" in video else 0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(EXC / video), "-vf", f"select=eq(n\\,{f})", "-vsync", "0",
                        "-frames:v", "1", "-q:v", "3", str(rv / f"{prefix}ours-{i}.jpg")], check=True)
        ev_tile(sheet, r, c, rv / f"ev-{i}.jpg")
        cards.append(f"""<section class="pair"><figure><img src="review/{prefix}ours-{i}.jpg" alt=""><figcaption><b>IRIS</b> · song {t:.2f} s · {html.escape(ours)}</figcaption></figure>
<figure><img src="review/ev-{i}.jpg" alt=""><figcaption><b>ESCAPE VELOCITY</b> · {sheet} r{r + 1} c{c + 1} (tile upscaled 4x) · {html.escape(evnote)}</figcaption></figure></section>""")
    return "".join(cards)


VIDEO_V3 = "renders/IRIS-EP01-v4-excerpt-026-059-v3.mp4"
VIDEO_V4R1 = "renders/IRIS-EP01-v4-excerpt-v4r1-036-051.mp4"
VIDEO_V4R2 = "renders/IRIS-EP01-v4-excerpt-v4r2-036-051.mp4"
VIDEO_V4R3 = "renders/IRIS-EP01-v4-excerpt-v4r3-036-051.mp4"
VIDEO_V4R4 = "renders/IRIS-EP01-v4-excerpt-v4r4-036-051.mp4"
VIDEO_V4R5 = "renders/IRIS-EP01-v4-excerpt-v4r5-036-051.mp4"
VIDEO_V4R6 = "renders/IRIS-EP01-v4-excerpt-v4r6-036-051.mp4"
VIDEO_V4R7 = "renders/IRIS-EP01-v4-excerpt-v4r7-036-059.mp4"
VIDEO_V4R8 = "renders/IRIS-EP01-v4-excerpt-v4r8-036-059.mp4"
VIDEO_V4R9 = "renders/IRIS-EP01-v4-excerpt-v4r9-036-059.mp4"
VIDEO_V4R10 = "renders/IRIS-EP01-v4-excerpt-v4r10-036-059.mp4"
VIDEO_V4R10B = "renders/IRIS-EP01-v4-excerpt-v4r10b-036-059.mp4"
VIDEO_V4R10C = "renders/IRIS-EP01-v4-excerpt-v4r10c-036-059.mp4"


def grad_table(tag: str = "v4r8") -> str:
    p = EXC / f"qa/{tag}/grad.json"
    if not p.exists():
        return ""
    g = json.loads(p.read_text())
    keys = [k for k in g if k != "ev"]
    rows = "".join(f"<tr><td>{m}</td><td>{g['ev']['median'][m]}</td>" + "".join(
        f"<td>{g[k]['median'][m]} <small>({g[k]['median'][m] / g['ev']['median'][m]:.2f}×)</small></td>" for k in keys) + "</tr>"
        for m in ("grad240", "grad160", "sat", "warm", "p2", "p10", "p50", "p90") if m in g["ev"]["median"] and all(m in g[k]["median"] for k in keys))
    return f"""<h3>Viewing-scale structure (qa/grad.py: grey, BOX to 240 / 160 px wide, 1/24 edges off, mean|∇|/std; median of 17 frames)</h3>
<table class="tx"><tr><th></th><th>EV 70–94 s</th>{"".join(f"<th>{k.replace('IRIS-EP01-v4-excerpt-', '')}</th>" for k in keys)}</tr>{rows}</table>
<p class="sub">At the user's viewing size, EV top / ours bottom, 640 px each:</p><img src="review/compare3/view640-{tag}.png" alt="">
{'<p class="sub">Same frames (song 44.0 / 49.5 / 53.5 / 56.0), v4r8 top, v4r9 bottom:</p><img src="review/compare3/v4r8-vs-v4r9.png" alt="">' if tag == "v4r9" else ""}
{'<p class="sub">Same frames (song 44.0 / 49.5 / 53.5 / 56.0), v4r9 top, v4r10 bottom:</p><img src="review/compare3/v4r9-vs-v4r10.png" alt="">' if tag == "v4r10" else ""}
{'<p class="sub">Same frames (render frames 368 / 200 / 500 = song 51.553 / 44.386 / 57.553), v4r10 top, v4r10c bottom: the skin under the red cap</p><img src="review/compare3/v4r10-vs-v4r10c.png" alt="">' if tag == "v4r10c" else ""}
{'<p class="sub">Same frames (render frames 368 / 200 / 500 = song 51.553 / 44.386 / 57.553), v4r10 top, v4r10b bottom: the skin under the red cap</p><img src="review/compare3/v4r10-vs-v4r10b.png" alt="">' if tag == "v4r10b" else ""}"""
PAIRS_V4R5 = [
    (39.75, "s010 · X10a · the graffiti read once off the billboard; the bottom event stream and the left scale", "ev-2", 0, 2, "EV: the billboard read as a joke"),
    (40.90, "s011 · the walk: HANDS! on the footfall; the roster lighting far to near", "ev-2", 1, 2, "EV: LOCK as one giant word on the hit"),
    (44.40, "s011 · 'Everybody': the engineer's seat picked out; the line as a mono annotation", "ev-3", 0, 5, "EV: UNDERCLASS pressed into the frame"),
    (45.72, "s012a · insert: her hand on the chair back", "ev-1", 0, 6, "EV: a tag read off the thing in frame"),
    (49.60, "s012b · SG03-w1 sings the whole line to him", "ev-1", 4, 1, "EV: Sorry. / ENCORE."),
    (50.70, "s012b · held from 50.32, cropped into him on the 50.469 beat: the sleep line leaps from his laptop to AWAKE", "ev-2", 1, 4, "EV: the face carries the line"),
]

PAIRS_V4R7 = PAIRS_V4R5[:2] + [
    (50.50, "s012 · SG03C-d1: closed eyes, 'you're awake'", "ev-2", 1, 4, "EV: the face carries the line"),
    (52.00, "s013a · INS13-a: the phone held out, her mouth out of frame; the call lit on 'call'", "ev-1", 0, 6, "EV: a tag read off the thing in frame"),
    (53.90, "s013b · SG04-r2-1: 'had to take', ALL lands right of her face", "ev-1", 4, 1, "EV: Sorry. / ENCORE."),
    (59.00, "s014c · INS14-b: the pager's LCD lit, 10:02 on 'Ten oh two'", "ev-2", 0, 7, "EV: the persistent flap device"),
]


def ticker_list() -> str:
    p = EXC / "data/edl-v4r5.json"
    if not p.exists():
        return ""
    items = json.loads(p.read_text()).get("ticker", [])
    rows = "".join(f"<tr><td>{html.escape(i['text'])}</td><td>{html.escape(i['source'])}</td></tr>" for i in items)
    return f"""<h3>Bottom event stream: every item and its source in the board</h3><table class="tx"><tr><th>text on screen</th><th>source</th></tr>{rows}</table>
<p class="sub">Sept 20 countdown: not made — the board gives this section no story date (INC-0804 / INC-0902 are the source articles' dates,
AUG 4 / SEP 2 2026; INCIDENT WEEK has no date), so "days to SEP 20" cannot be derived.</p>
<p class="sub">Whole frames, ours beside EV: <a href="review/compare3/fullframe-v4r5.png">fullframe-v4r5.png</a></p><img src="review/compare3/fullframe-v4r5.png" alt="">"""


def texture_table(tag: str = "v4r3") -> str:
    """qa/<tag>/texture.json (qa/texture.py on EV 70-94 s and on v4r2 / v4r3 frames) and the same-box crop numbers."""
    p = EXC / f"qa/{tag}/texture.json"
    if not p.exists():
        return ""
    t = json.loads(p.read_text())
    cols = [c for c in ("ev", "v4r2", "v4r3", "v4r4") if c in t]
    keys = [("screen_prominence", "screen (2-D peak prominence; pitch 4.0 px)"), ("lap", "sharpness: Laplacian variance after sigma-2 low-pass (gate)"),
            ("crisp", "base sharpness, var(G2-G4)/var(G4-G8)"),
            ("sat", "mean saturation"), ("warm", "warm balance (R-B)")]
    rows = "".join(f"<tr><td>{lab}</td>" + "".join(
        f"<td>{t[k]['summary'][key]['median']} <small>({t[k]['summary'][key].get('p10', '')}–{t[k]['summary'][key].get('p90', '')})</small></td>"
        for k in cols) + "</tr>" for key, lab in keys if key in t["ev"]["summary"])
    gate = t.get("gate", {})
    grow_ = "".join(f"<tr><td>gate · {k}</td><td colspan='{len(cols)}'>ours/EV = {v['ratio']} → {'PASS' if v['within_20pct'] else 'outside ±20%'}</td></tr>"
                    for k, v in gate.items() if k in ("lap", "sat", "warm"))
    crop = t.get("crops", {})
    crow = "".join(f"<tr><td>crop {i + 1} · {name}</td>" + "".join(f"<td>{crop[side][i][name]}</td>" for side in ("ev", "v4r2", "v4r3")) + "</tr>"
                   for i in range(2) for name in ("crisp", "sat", "warm")) if crop and all(s_ in crop for s_ in ("ev", "v4r2", "v4r3")) else ""
    return f"""<h3>Texture, measured (qa/texture.py): median (p10–p90) over 13 EV frames 70–94 s and 12 frames of ours</h3>
<table class="tx"><tr><th></th>{"".join(f"<th>{c}</th>" for c in cols)}</tr>{rows}{grow_}{crow if tag == "v4r3" else ""}</table>
<p class="sub">Same-box crops (review/compare3, EV left, ours right): <a href="review/compare3/crop-compare.png">v4r2</a> · <a href="review/compare3/crop-compare-v4r3.png">v4r3</a>{f' · <a href="review/compare3/crop-compare-{tag}.png">{tag}</a>' if tag != "v4r3" else ""}</p>
<img src="review/compare3/crop-compare-{tag}.png" alt="">
{f'<p class="sub">Whole frames, ours 1080p beside EV 1080p, with 1:1 strips of the interface: <a href="review/compare3/fullframe-{tag}.png">fullframe-{tag}.png</a></p><img src="review/compare3/fullframe-{tag}.png" alt="">' if (EXC / f"review/compare3/fullframe-{tag}.png").exists() else ""}"""
PAIRS_V4R2 = [
    (39.75, "s010 · X10a · the graffiti read once off the billboard; 'IGNORED' on Forgot.", "ev-2", 0, 2, "EV: the billboard read as a joke"),
    (41.40, "s011 · the walk: HANDS! toned; the roster expanded, groups lit far to near from 40.786", "ev-2", 1, 2, "EV: LOCK as one giant word on the hit"),
    (44.40, "s011 · 'Everybody': the engineer's seat picked out", "ev-3", 0, 5, "EV: UNDERCLASS pressed into the frame"),
    (45.72, "s012a · insert: her hand on the chair back; no label, the hand says it", "ev-1", 0, 6, "EV: a tag read off the thing in frame"),
    (47.90, "s012b · SG03-w1: she leans in, he looks up; his sleep line starts at his laptop edge", "ev-1", 4, 1, "EV: Sorry. / ENCORE."),
    (50.20, "s012c · PLACEHOLDER still D1-b (closed-eye close-up, clip to come): the line leapt on 'you're', AWAKE locked", "ev-2", 1, 4, "EV: the face carries the line"),
]
# v4 round 1 renders song 36.2195-50.928 (frames 244..596 of the excerpt); the moments are song times
PAIRS_V4R1 = [
    (39.75, "s010 · X10a · the spell-check: IGNORE on 'Forgot.', the field and the billboard", "ev-2", 0, 2, "EV: the billboard read as a joke"),
    (40.90, "s011 · the walk take (MO06-w1b, in 0.215 s): the boot lands on HANDS!, the rows snap on", "ev-2", 1, 2, "EV: LOCK as one giant word on the hit"),
    (42.80, "s011 · NIGHT! as the long sleeve swings back; laptop logos blotted", "ev-3", 0, 5, "EV: UNDERCLASS pressed into the frame"),
    (45.72, "s012a · insert 1 (p012-w1): her hand on the chair back on 'hold', classified WHITE-KNUCKLED", "ev-1", 0, 6, "EV: a tag read off the thing in frame"),
    (46.55, "s012a · insert 2 (p012-w1): the engineer looking up on 'on tight'", "ev-1", 4, 1, "EV: Sorry. / ENCORE. mass line"),
    (49.60, "s012b · the sung take (SG03-w1, lag +0.0251): 'you're awake' on her mouth, his night climbs to AWAKE", "ev-2", 1, 4, "EV: the face carries the line"),
]
PAIRS_V3 = PAIRS_V2                                       # same moments, same EV tiles


def main() -> int:
    rv = EXC / "review"
    rv.mkdir(exist_ok=True)
    sections = [
        ("v4 round 10c · v4r10b with a tighter red cap on the phone insert's skin (s013a, INS13-a) · song 36.22-59.23 · "
         "JUDGE 39.674-59.234", VIDEO_V4R10C, "qa/v4r10c", "renders/render-provenance-v4r10c.json", PAIRS_V4R7, "v4r10c-", "auto"),
        ("v4 round 10b · v4r10 (approved look) with the red cap applied again after the tone curve, so skin stays out of the "
         "signal-red test; only her ear lamp keeps signal red · song 36.22-59.23 · JUDGE 39.674-59.234", VIDEO_V4R10B, "qa/v4r10b",
         "renders/render-provenance-v4r10b.json", PAIRS_V4R7, "v4r10b-", "none"),
        ("v4 round 10 · v4r9 with EV's tonal range: a tone curve before the interface and the screen (deeper blacks, brighter "
         "lights), the veil kept to the mid tones and lights · song 36.22-59.23 · JUDGE 39.674-59.234", VIDEO_V4R10, "qa/v4r10",
         "renders/render-provenance-v4r10.json", PAIRS_V4R7, "v4r10-", "none"),
        ("v4 round 9 · v4r8's depth of field cut to a third (background sigma 7 px), the engineers, the nearest front rows and "
         "the inserts' hands and props kept as subjects; the softness made up uniformly (structure softening and veil) · "
         "song 36.22-59.23 · JUDGE 39.674-59.234", VIDEO_V4R9, "qa/v4r9", "renders/render-provenance-v4r9.json",
         PAIRS_V4R7, "v4r9-", "none"),
        ("v4 round 8 · v4r7 with the texture softened at viewing scale: depth of field on every picture (background blurred "
         "round the figure's matte, the figure lightly softened), warm highlight bloom and a veil; the interface crisp under the "
         "screen · song 36.22-59.23 · JUDGE 39.674-59.234", VIDEO_V4R8, "qa/v4r8", "renders/render-provenance-v4r8.json",
         PAIRS_V4R7, "v4r8-", "none"),
        ("v4 round 7 · v4r6 to the end of the chorus: s011 on MO06-s-1, s013 = INS13-a phone insert (the call lit on 'call') then "
         "SG04-r2-1 (held from 54.95), s014 = MO07-s-2 with a jump on 57.377, then the INS14-b pager insert (LCD 10:02) · cut pairs: "
         "review/compare3/cuts-v4r7.png · song 36.22-59.23 · JUDGE 39.674-59.234",
         VIDEO_V4R7, "qa/v4r7", "renders/render-provenance-v4r7.json", PAIRS_V4R7, "v4r7-", "none"),
        ("v4 round 6 · v4r5 with the closed-eye close-up (SG03C-d1) cut into s012: SG03-w1 to the 49.087 beat, d1 sings "
         "'you're awake' to the 50.469 beat, then the crop into the engineer and the leap to AWAKE; everything else as v4r5 · "
         "the 49.087 cut, frame before / after: review/compare3/cut-49087-v4r6.png · song 36.22-50.93 · JUDGE 39.674-50.93",
         VIDEO_V4R6, "qa/v4r6", "renders/render-provenance-v4r6.json", PAIRS_V4R5, "v4r6-", "none"),
        ("v4 round 5 · s012 is the SG03-w1 take for the whole line (the closed-eye close-up dropped), held from 50.32 and cropped "
         "into the engineer on the 50.469 beat for the sleep line's leap to AWAKE; the console: EV-size small type, a bottom event "
         "stream from the board, a left scale; lyrics as mono annotations with DINish only on the masthead words; v4r4's texture "
         "unchanged · song 36.22-50.93 · JUDGE 39.674-50.93", VIDEO_V4R5, "qa/v4r5", "renders/render-provenance-v4r5.json",
         PAIRS_V4R5, "v4r5-", "none"),
        ("v4 round 4 · only the base texture and the grade changed from v4r3: the base from half/quarter-resolution copies (a low-res "
         "photo upscaled) under a sharp AM line screen deepest in the mid tones, peach/cream whites, warm brown blacks, saturation at EV's; "
         "the interface crisp under the screen; cold screens kept cold; s012 close-up still the PLACEHOLDER D1-b · song 36.22-50.93 · "
         "JUDGE 39.674-50.93", VIDEO_V4R4, "qa/v4r4", "renders/render-provenance-v4r4.json", PAIRS_V4R2, "v4r4-", "none"),
        ("v4 round 3 · v4r2 with the picture texture matched to EV by measurement: a softened base, EV's 4.0 px line screen at "
         "its angle, misregistration, grain, warmer and more saturated; interface and type under the same print · s012 close-up still the "
         "PLACEHOLDER D1-b · song 36.22-50.93 · JUDGE 39.674-50.93", VIDEO_V4R3, "qa/v4r3", "renders/render-provenance-v4r3.json",
         PAIRS_V4R2, "v4r3-", "none"),
        ("v4 round 2 · round 1 rebuilt in the approved design-v2 interface language and grade · s012: SG03-w1 to the 48.17 bar line, "
         "then the closed-eye close-up — PLACEHOLDER: the still D1-b stands in for its clip (not generated yet), light change only · "
         "song 36.22-50.93 · JUDGE 39.674-50.93", VIDEO_V4R2, "qa/v4r2", "renders/render-provenance-v4r2.json", PAIRS_V4R2, "v4r2-", "none"),
        ("v4 round 1 · the still -> motion -> singing junction (s010 still, s011 walk take, s012a two inserts, s012b sung take) · "
         "song 36.22-50.93 · JUDGE 39.674-50.93", VIDEO_V4R1, "qa/v4r1", "renders/render-provenance-v4r1.json", PAIRS_V4R1, "v4r1-", "none"),
        ("v3 · v2's edit on the stills remade in wardrobe W1 (the on-call hoodie couture)", VIDEO_V3, "qa/v3",
         "renders/render-provenance-v3.json", PAIRS_V3, "v3-", "none"),
        ("v2 · stills first (flash snapshots, first wardrobe): hard crops on beats, stills swapped on beats and bar lines",
         VIDEO_V2, "qa/v2", "renders/render-provenance-v2.json", PAIRS_V2, "v2-", "none"),
        ("v1 · rejected 2026-11-18 (generated clips + 2.5D cut-outs), kept for comparison", VIDEO, "qa",
         "renders/render-provenance.json", PAIRS, "", "none"),
    ]
    body = []
    for title, video, qa_dir, prov, plist, prefix, preload in sections:
        q = json.loads((EXC / qa_dir / "qa.json").read_text())
        (EXC / qa_dir / "QA.md").write_text(qa_md(q), encoding="utf-8")
        sha = json.loads((EXC / prov).read_text())["final"]["sha256"]
        body.append(f"""<h2>{html.escape(title)}</h2>
<p class="sub">HyperFrames render, 1920×1080, 24 fps, AAC from the master · {video} · sha256 {sha}</p>
<video src="{video}" controls preload="{preload}"></video>
{badges(q, qa_dir)}
{texture_table(prefix[:-1]) if prefix in ("v4r3-", "v4r4-") else ""}
{ticker_list() if prefix == "v4r5-" else ""}
{grad_table(prefix[:-1]) if prefix in ("v4r8-", "v4r9-", "v4r10-", "v4r10b-", "v4r10c-") else ""}
{pairs(video, plist, prefix, rv)}""")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>IRIS EP01 v4 · excerpt 026-059 · review</title>
<style>
body{{margin:0;background:#0b0c0d;color:#e8e4da;font:15px/1.5 "IBM Plex Mono",ui-monospace,monospace}}
main{{max-width:1960px;margin:0 auto;padding:28px}}
h1{{font:700 26px/1.2 "Nimbus Sans",Helvetica,Arial,sans-serif;margin:0 0 6px}} h2{{font:700 21px/1.2 "Nimbus Sans",Helvetica,Arial,sans-serif;margin:46px 0 6px}}
.sub{{opacity:.7;margin:0 0 18px}}
video{{width:100%;max-width:1920px;display:block;background:#000}}
.qa{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 28px}} .qa span{{border:1px solid #444;padding:4px 10px}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:0 0 22px}} figure{{margin:0}} img{{width:100%;display:block}}
figcaption{{font-size:13px;opacity:.82;margin-top:6px}} a{{color:#f2b134}}
.tx{{border-collapse:collapse;margin:8px 0 14px}} .tx td,.tx th{{border:1px solid #333;padding:4px 10px;text-align:left}}
</style></head><body><main>
<h1>IRIS EP01 v4 · excerpt · song 26.05–59.23 s (Verse 1 + Chorus 1)</h1>
{''.join(body)}
<h2>ESCAPE VELOCITY reference strip</h2>
<img src="review/compare/ev-strip.jpg" alt="ESCAPE VELOCITY frames">
</main></body></html>
"""
    (EXC / "index.html").write_text(page, encoding="utf-8")
    print("review written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
