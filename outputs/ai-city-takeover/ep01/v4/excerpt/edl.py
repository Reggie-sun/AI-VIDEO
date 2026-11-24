"""Edit decision list of the IRIS EP01 v4 excerpt (song time, seconds). Shared by prep_media.py, build.py and qa.py.

Comp time 0 is song time OFFSET. Output 24 fps (the clips' own cadence is about 24 pictures a second, so 24 fps shows
every picture once instead of repeating every fourth, and it is the author's ESCAPE VELOCITY rate). A time shows on the
nearest frame (frame_of rounds), so a cut lands within half a frame (0.0208 s) of its beat.
"""
from __future__ import annotations

from pathlib import Path

EXC = Path(__file__).resolve().parent
V4 = EXC.parent
REPO = EXC.parents[4]
FPS = 24
W, H = 1920, 1080
OFFSET = 26.0528                       # song time of comp frame 0 (the s007 cut, a downbeat)
END = 59.2341                          # song time of the s015 cut (excerpt end)
MASTER = V4 / "song/master/all-hands-r4-edc6c6bf.wav"
MASTER_SHA = "6dffe1d9022c960d7e0a67c834787131206707b02ca30ade67e04f82209c0350"

FETCH = "project/state/video-generation/fetch/files"
SHOTS = [
    {"id": "s007", "t0": 26.0528, "t1": 29.7448, "kind": "clip", "clip_song_start": 26.0528, "tail_lights_to_orange": True,
     "orange_thresholds": (0.12, 0.05),  # the dim red reflection in the wet pavement
     "clip": f"pilot/sd-MO04/MO04/{FETCH}/5cafae77b683083cd08389788178ff7c93c3018f45cdde43abc94354fb2b7b12.mp4"},
    {"id": "s008", "t0": 29.7448, "t1": 31.1263, "kind": "clip", "clip_song_start": 29.529, "lag": 0.0499,
     "track": "sticker", "lipsync_until": 31.39,
     "clip": f"pilot/sd-SG02-r2/SG02/{FETCH}/0c7a34119f4ab9aa3870eb03a2e6442393352ba312d31320b07679699d6c5425.mp4"},
    {"id": "s009", "t0": 31.1263, "t1": 36.1999, "kind": "plate", "plate": "p009"},
    {"id": "s010", "t0": 36.1999, "t1": 40.7859, "kind": "clip", "clip_song_start": 36.1999, "tail_lights_to_orange": True,
     "clip": f"pilot/sd-MO05/MO05/{FETCH}/ce47961f40bbaecda1eb8f9dc704bf9f10b4ed839d00a63da747121fd6b422e8.mp4"},
    {"id": "s011", "t0": 40.7859, "t1": 44.9422, "kind": "plate", "plate": "p011"},
    {"id": "s012", "t0": 44.9422, "t1": 50.933, "kind": "clip", "clip_song_start": 44.9422, "lag": 0.0385,
     "clip": f"pilot/sd-SG03/SG03/{FETCH}/fee974f046e8df07d582c7730b14ccf74c0accd496221244833608068a47cb02.mp4"},
    {"id": "s013", "t0": 50.933, "t1": 55.0777, "kind": "plate", "plate": "p013"},
    {"id": "s014", "t0": 55.0777, "t1": 59.2341, "kind": "plate", "plate": "p014"},
]


def frame_of(song_t: float) -> int:
    """Output frame on which a song time shows (nearest frame)."""
    return int(round((song_t - OFFSET) * FPS))


FRAMES = frame_of(END)                 # 796 frames = 33.1667 s

# ---------------------------------------------------------------- v2 (2026-11-18): stills first
# The user rejected v1 (pace, edit, the clips and the 2.5D cut-outs); v2 is cut from the flash-snapshot stills only
# (flash/stills, X07a..X14a), the author's `still` tier: a plate moved in code - hard crops landing on beats, a still
# swapped on a beat or a bar line, a slight handheld drift - no clip, no cut-out, no parallax, no slow zoom.
# Cuts keep the board's places: section starts on downbeats (26.0528, 40.7859, the end 59.2341); 29.7448 a bar line;
# 31.1263 the user's decision; 36.1999, 44.9422, 50.933, 55.0777 beats a line's pickup before its first word (the image
# arrives with its line). Still swaps: 35.2827 (bar line, the scratch light lands), 39.8454 (beat after "Forgot.",
# carrying ALL), 48.1698 (bar line).
STILLS = EXC / "flash/stills"
SHOTS_V2 = [
    {"id": "s007", "t0": 26.0528, "t1": 29.7448, "stills": [["X07a", 26.0528]]},
    {"id": "s008", "t0": 29.7448, "t1": 31.1263, "stills": [["X08a", 29.7448]]},
    {"id": "s009", "t0": 31.1263, "t1": 36.1999, "stills": [["X09a", 31.1263], ["X09b", 35.2827]]},
    {"id": "s010", "t0": 36.1999, "t1": 40.7859, "stills": [["X10a", 36.1999], ["X10b", 39.8454]]},
    {"id": "s011", "t0": 40.7859, "t1": 44.9422, "stills": [["X11a", 40.7859]]},
    {"id": "s012", "t0": 44.9422, "t1": 50.933, "stills": [["X12a", 44.9422], ["X12b", 48.1698]]},
    {"id": "s013", "t0": 50.933, "t1": 55.0777, "stills": [["X13a", 50.933]]},
    {"id": "s014", "t0": 55.0777, "t1": 59.2341, "stills": [["X14a", 55.0777]]},
]

# ---------------------------------------------------------------- v3 (2026-11-18): v2's edit on the stills remade in
# wardrobe W1 (the on-call hoodie couture: grey hoodie crop jacket, one long sleeve and one bare shoulder, leather
# cross-body strap, waist chain with the old black pager and a blank badge, black mini skirt, knee boots). Same names,
# same cuts and swaps; the places on each still are re-read in src/shots2.js (GEO[3]).
STILLS_W1 = EXC / "flash/stills-w1"
SHOTS_V3 = SHOTS_V2
# her ear lamp on each W1 still (plate px centre, radius): the only red kept (prep_media.py --v3)
W1_LAMP = {"X07a": (1050, 150, 60), "X08a": (1110, 210, 70), "X09a": (748, 266, 50), "X09b": (1235, 240, 90),
           "X10a": (925, 268, 55), "X10b": (935, 95, 40), "X11a": (895, 95, 40), "X12a": (825, 185, 50), "X12b": (1188, 203, 55),
           "X13a": (902, 176, 55), "X14a": (935, 135, 40)}

# ---------------------------------------------------------------- v4 round 1 (2026-11-18, PLAN-v4.md): the still ->
# motion -> singing junction, rendered for song 36.1999-50.933 (frames 244..596 of the excerpt; judged 39.674-50.93).
# s010 as v3; s011 the new W1 walk (MO06-w1b): in-point 0.215 s so the raised boot (planted on picture 7, 0.29 s) lands
# on HANDS (40.861), 1x, clip audio unused, laptop logos tracked and blotted; s012a two still inserts cropped from
# p012-w1 on "hold on tight" (her hand on the chair back on "hold", the engineer looking up on "on tight"), cut on
# beats; s012b the new W1 sung take (SG03-w1) placed by its lag (clip_time = song - 44.9422 + 0.0251), from clip 1.87 s
# to its end, one shot for "I'm the reason you're awake".
V4R1_F0 = frame_of(36.1999)            # 244: the window starts on s010's own first frame
V4R1_F1 = frame_of(50.933)             # 597: s013's cut (exclusive)
FETCH_W1 = "project/state/video-generation/fetch/files"
SHOTS_V4R1 = [
    {"id": "s010", "t0": 36.1999, "t1": 40.7859, "stills": [["X10a", 36.1999], ["X10b", 39.8454]]},
    {"id": "s011", "t0": 40.7859, "t1": 44.9422, "kind": "clip", "clip_song_start": 40.7859 - 0.215, "tail_lights_to_orange": True,
     "clip": f"pilot/sd-MO06-w1b/MO06/{FETCH_W1}/63c54845fc17046e0c5d7a0213e113a4cfc20936a1548ee1cc8603ee6951bed2.mp4",
     # keyframes (clip time, x, y in 1920 px) read off the footage; sign: the logo's contrast with its lid
     "logos": [{"name": "held-laptop-right", "sign": -1, "r": 12, "lid": (0.35, 0.95),
                "keys": [(0.25, 1556, 722), (1.0, 1545, 720), (1.5, 1527, 712), (1.9, 1515, 705), (2.94, 1498, 686), (3.23, 1496, 682),
                         (3.98, 1494, 668), (4.33, 1495, 660)]},
               {"name": "small-laptop-right", "sign": 1, "r": 9, "lid": (0.08, 0.5), "keys": [(0.25, 1410, 772), (4.33, 1410, 771)]},
               {"name": "laptop-left-blue", "sign": 1, "r": 9, "lid": (0.08, 0.5), "keys": [(0.25, 277, 653), (1.0, 277, 657), (4.33, 263, 657)]},
               {"name": "held-laptop-left", "sign": -1, "r": 11, "lid": (0.3, 0.95), "keys": [(0.25, 412, 640), (1.0, 408, 640), (4.33, 460, 640)]}]},
    {"id": "s012a", "t0": 44.9422, "t1": 46.7882, "stills": [["p012w1-hand", 44.9422], ["p012w1-engineer", 45.8594]]},
    {"id": "s012b", "t0": 46.7882, "t1": 50.933, "kind": "clip", "clip_song_start": 44.9422, "lag": -0.0251, "tail_lights_to_orange": True,
     "clip": f"pilot/sd-SG03-w1/SG03/{FETCH_W1}/02169f1ebff05dc4700e37c6baa361adee2a24de2ad1cdd4460c8395063c0bbd.mp4"},
]

# ---------------------------------------------------------------- v4 round 2 (2026-11-19): round 1 rebuilt in the
# approved design-v2 interface language and grade (src/shots5.js, console2.js), the same window (frames 244..596).
# Edit change: SG03-w1 only to the 48.170 bar line, then the closed-eye close-up for "reason you're awake" - its clip
# is not made yet: the still flash/design/D1-b.png stands in (PLACEHOLDER, light change only).
SHOTS_V4R2 = [
    SHOTS_V4R1[0], SHOTS_V4R1[1], SHOTS_V4R1[2],
    {**SHOTS_V4R1[3], "t1": 48.1698},
    {"id": "s012c", "t0": 48.1698, "t1": 50.933, "stills": [["D1-b", 48.1698]], "placeholder": True},
]

# ---------------------------------------------------------------- v4 round 5 (2026-11-19): the user dropped the
# closed-eye close-up (SG03C-c failed its gate; option B). s012b is the SG03-w1 take singing "I'm the reason you're
# awake" in one shot (song = clip + 44.917; usable to clip 5.4 = song 50.32); from 50.32 its picture holds (the
# engineer looking up), and on the 50.4686 beat a hard crop into him and his laptop carries the sleep line's leap to
# AWAKE through the 50.933 cut. v4r4's texture and grade are kept as they are.
SHOTS_V4R5 = [
    SHOTS_V4R1[0], SHOTS_V4R1[1], SHOTS_V4R1[2],
    {**SHOTS_V4R1[3], "t1": 50.933, "freeze": 50.32, "punch": 50.4686},
]

# ---------------------------------------------------------------- v4 round 6 (2026-11-19): v4r5 with the closed-eye
# close-up cut into s012 (SG03C-d1, its gate PASS; song = clip + 46.93 - 0.018, usable clip 2.168-3.538 = song
# 49.08-50.45). SG03-w1 sings to the 49.087 beat (after "reason", before "you're"); d1 sings "you're awake" to the
# 50.4686 beat (its last frame shows clip 3.516, inside the usable range: no hold needed); then v4r5's crop into the
# engineer (SG03-w1's picture at song 50.303, the frame v4r5 held) carries the sleep line's leap to AWAKE to 50.933.
# v4r5's hold of SG03-w1 from 50.32 is gone.
FETCH_D1 = "project/state/video-generation/fetch/files"
SHOTS_V4R6 = [
    SHOTS_V4R1[0], SHOTS_V4R1[1], SHOTS_V4R1[2],
    {**SHOTS_V4R1[3], "t1": 49.087},
    {"id": "s012c", "t0": 49.087, "t1": 50.4686, "kind": "clip", "clip_song_start": 46.93 - 0.018, "tail_lights_to_orange": True,
     "clip": f"pilot/sd-SG03C-d1/SG03C/{FETCH_D1}/2de73f901d83839f23b9e3004e8271c1597fbacc91ce85fee5842ba51f76fb09.mp4"},
    {"id": "s012d", "t0": 50.4686, "t1": 50.933, "kind": "clip", "seq_from": "s012b", "fixed_pic": 84, "punch": 50.4686},
]

# ---------------------------------------------------------------- v4 round 7 (2026-11-19): v4r6 extended to the end of
# the chorus (song 36.1999-59.2341, frames 244..795; judged 39.674-59.234). Every take passed its gate or was approved by
# the user. s011 is MO06-s-1 (the strap the right way round; clip 0.417-4.573, the footfall at clip 0.500 on HANDS
# 40.861); s012 as v4r6; s013 = the INS13-a still (the phone held out, her mouth cropped out, a slow push; the call lights
# on 'call' 51.76) to the 52.3146 beat, then SG04-r2-1 (clip = song - 50.933 + 0.947) held at clip 4.958 from song 54.95
# (its lips drift after clip 4.98); s014 = MO07-s-2 clip 0-2.299 (the turn, the sleeve out), a jump on the 57.3765 beat
# to clip 3.0-4.393 (the sleeve down, she walks off right; the red light on her hip near clip 2.5 is skipped), then the
# INS14-b still on the 58.7697 beat (her hand on the pager; its LCD reads 10:02 for "Ten oh two"). Media ids keep the
# earlier rounds' prepared pictures untouched (seq dirs s011s, s013b, s014a, s014b).
V4R7_F1 = frame_of(59.2341)            # 796 (exclusive)
FETCH7 = "project/state/video-generation/fetch/files"
MO06S = f"pilot/sd-MO06-s-1/MO06/{FETCH7}/234b4a7ef49dd1fa74ac71399bcb0d946cf645c94e3441bcbe81a2ba84f9d40c.mp4"
SG04R = f"pilot/sd-SG04-r2-1/SG04/{FETCH7}/e18949ce2639bdce058609c34bfb9b9926f98768420a52133237261f6d45ec29.mp4"
MO07S = f"pilot/sd-MO07-s-2/MO07/{FETCH7}/9a08bc46eebb59fc0d430cdd07044f4a754c4bc48afd9bc835179b5167ea256d.mp4"
SHOTS_V4R7 = [
    SHOTS_V4R6[0],
    {"id": "s011", "media_id": "s011s", "t0": 40.7859, "t1": 44.9422, "kind": "clip", "clip_song_start": 40.7859 - 0.417,
     "tail_lights_to_orange": True, "clip": MO06S,
     "logos": [{"name": "held-laptop-right", "sign": -1, "r": 10,  "lid": (0, 1),
                "keys": [(0.45, 1570, 729), (1.2, 1539, 717), (2.0, 1502, 702), (2.8, 1476, 682), (4.5, 1458, 650)]},
               {"name": "small-laptop-right", "sign": 1, "r": 9, "lid": (0, 1), "keys": [(0.45, 1415, 770), (4.5, 1408, 765)]},
               {"name": "laptop-left-blue", "sign": 1, "r": 9, "lid": (0, 1), "keys": [(0.45, 277, 662), (4.5, 275, 662)]},
               {"name": "held-laptop-left", "sign": -1, "r": 12, "lid": (0, 1),
                "keys": [(0.45, 415, 642), (1.5, 425, 640), (2.5, 433, 636), (3.5, 445, 634), (4.5, 472, 624)]}]},
    SHOTS_V4R6[2], SHOTS_V4R6[3], SHOTS_V4R6[4], SHOTS_V4R6[5],
    {"id": "s013a", "t0": 50.933, "t1": 52.3146, "stills": [["INS13-a", 50.933]]},
    {"id": "s013b", "t0": 52.3146, "t1": 55.0777, "kind": "clip", "clip_song_start": 50.933 - 0.947, "tail_lights_to_orange": True,
     "clip": SG04R, "freeze": 54.93},     # frame 693 on: picture 119 (clip 4.958), the last before 4.98
    {"id": "s014a", "t0": 55.0777, "t1": 57.3765, "kind": "clip", "clip_song_start": 55.0777, "tail_lights_to_orange": True,
     "clip": MO07S, "logos": [{"name": "laptop-right", "sign": -1, "r": 11, "lid": (0, 1), "keys": [(0.0, 1690, 569), (4.4, 1690, 570)]}]},
    {"id": "s014b", "t0": 57.3765, "t1": 58.7697, "kind": "clip", "clip_song_start": 57.3765 - 3.0, "tail_lights_to_orange": True,
     "clip": MO07S, "logos": [{"name": "laptop-right", "sign": -1, "r": 11, "lid": (0, 1), "keys": [(0.0, 1690, 569), (4.4, 1690, 570)]}]},
    {"id": "s014c", "t0": 58.7697, "t1": 59.2341, "stills": [["INS14-b", 58.7697]]},
]

# ---------------------------------------------------------------- opening v2c (2026-11-21): s014 reshot. MO07 r6-2
# (per-shot gate PASS; the audience heads down throughout) replaces s014a + s014b (MO07-s-2 with its jump on the
# 57.3765 beat): ONE span of the take for song 55.0777-58.7697, no jump cut, then s014c (INS14-b) unchanged as an
# insert. Material offset 0.035 s (clip_song_start 55.0427): picture 56 (clip 2.333 s, the sleeve flung out, the
# take's largest picture change) lands on the 57.3765 beat (song frame 1377); the turn runs pictures 49-54 before it.
# The shot keeps the id s014a (the engine's v8 shot functions and levels are keyed by id) on its own prepared pictures
# media/seq/s014r6. One laptop mark is blotted: the light apple-like mark on the lid right of her (1598.5, 507.5 at
# 1920; 4K DoG +18). The other lids carry marks at DoG 7-8 (the old take's dark apple was -47) next to the lids'
# bright rims: left as they are (a blot there would smear the rim). Search window 3 px (prep_media.remove_logos "win").
MO07R6 = f"pilot/sd-MO07-r6-2/MO07/{FETCH7}/f8ea9ac669f8db68315817e8d2ed845f24d9c6dd52ee31cdcc24d11bc0195950.mp4"
S014_OFFSET = 0.035
S014_V2C = {"id": "s014a", "media_id": "s014r6", "t0": 55.0777, "t1": 58.7697, "kind": "clip",
            "clip_song_start": 55.0777 - S014_OFFSET, "tail_lights_to_orange": True, "clip": MO07R6,
            "logos": [{"name": "laptop-right-lid", "sign": 1, "r": 4, "win": 3, "lid": (0, 1),
                       "keys": [(0.0, 1598.5, 507.5), (5.1, 1598.5, 507.5)]}]}

# ---------------------------------------------------------------- opening v3 (2026-11-21, v2d review: "56s那里那个动作我没
# 看懂"): s014 r6-2 split on the 56.9237 beat (song frame 1366) into two pieces of the same take, no new generation. The
# pager press (her right hand on the pager on the front waist chain, head down; take pictures 12-44 = song frames
# 1334-1366) is the punch-in s014p, 55.0777-56.9237, prepared from the take's own 3840x2160 pictures (the author's rule:
# "Punch in on the sharpest source. The 4K feed crops 2x to 1080p without loss"), shown at 2x of the wide (1:1 of the
# 4K picture); 56.9237-58.7697 back to the wide (s014a, media/seq/s014r6 from its picture 44) for the turn, the single
# sleeve swing and the walk away. Same placement (material offset S014_OFFSET), same red repair, same lid blot.
S014_SPLIT = 56.9237
S014P_V3 = {**S014_V2C, "id": "s014p", "media_id": "s014p", "t1": S014_SPLIT}
