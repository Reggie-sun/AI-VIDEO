#!/usr/bin/env python3
"""IRIS EP01 opening v2 (2026-11-21): the Agentcut layer of escape-velocity-replica rebuilt for the v2 picture
(opening_v2.py) and the v2 layout (pilot/opening/plan/index.html §3; texture_study/REPORT.md §3, §6):

- picture: pic-print plays renders/IRIS-EP01-v2-picture-000-1422.mp4 (copied to assets/video/iris/print-v2b-000-1422.mp4);
  the v4r11 picture clip moves to the hidden track pic-print-v4r11.
- ticket: the P0 card (track ticket, now hidden) becomes TicketChip, 230x83 under the top-right spectrum (EV's MONTHS
  widget, 0.92 %): one line (ticket id / SEV) and one count (PAGED); the top left keeps the HUD's one chapter line.
- event graphics: every clip ends on its own shot's cut (song cuts CUTS); clips that ran over a cut are split there
  (later pieces carry their words with negative frames, the pager stack an offset); positions spread over the frame,
  away from the x72 column where the shot allows; s001's pager label sits bottom right on a leader that follows the
  pager (Callout track). All words stay in props.

Run: uv run python outputs/ai-city-takeover/ep01/v4/excerpt/agentcut_v2_layers.py   (reads the pre-v2 backup, writes
layers.json; the backup is qa/opening-v2/layers.before-v2.json, also .studio/scratch/layers.before-v2-20261121.json)

v2c (--v2c, 2026-11-21, s014 reshot): pic-print plays renders/IRIS-EP01-v2c-picture-000-1422.mp4 (copied to
assets/video/iris/print-v2c-000-1422.mp4; opening_v2.py --join-c), the v2 picture moves to the hidden track pic-print-v2.
s014 is one shot (MO07 r6-2) from 1322 to 1410: the 1377 cut is gone, so nothing is split or ends there any more
(slam ALL HANDS! ALL NIGHT!, the pager stack, the sung lines run on to 1410); cls-s014a-frontrow ends on 1410.

v2d (--v2d = --v2c + two fixes, 2026-11-21): the pager stack's PAGED label sat on the HUD's SONG/BAR readout (top
1003 - cap, x ~1570-1824) and its lowest icons touched it: the stack's bottom moves from 990 to 950 (icons end at 946, PAGED
at 958-972, clear of the readout); the front-row box reads LOOKING AT / THEIR LAPTOP (r6-2's engineers look at laptops).

v3 (--v3 = --v2d + the v3 picture, 2026-11-21): pic-print plays renders/IRIS-EP01-v3-picture-000-1422.mp4 (copied to
assets/video/iris/print-v3-000-1422.mp4; opening_v2.py --join-3), the v2c picture moves to the hidden track pic-print-v2c.
s014 is cut on the 56.9237 beat (frame 1366): 1322-1365 the punch-in on the pager press, 1366-1409 the wide. As v2 did
on its 1377 cut, everything is split on the new cut (slam ALL HANDS! ALL NIGHT! continues as a second piece whose words
are already up, the pager stack continues by its offset, the sung lines continue); a pager callout PAGER · 10:02 ·
BUZZING tracks the pager in the punch-in (Callout.track, positions read off the v3 picture) and ends on 1366; the
front-row box moves into the wide (1372-1410: the punch-in shows no front row).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

PROJ = Path("/home/reggie/Agentcut/projects/escape-velocity-replica")
SRC = Path(__file__).resolve().parent / "qa/opening-v2/layers.before-v2.json"
V3 = "--v3" in sys.argv
V2D = "--v2d" in sys.argv or V3
V2C = "--v2c" in sys.argv or V2D
CUTS = [0, 99, 231, 307, 406, 493, 625, 714, 791, 869, 979, 1078, 1123, 1178, 1211, 1222, 1255, 1322, 1377, 1410, 1422]
if V2C:
    CUTS.remove(1377)                          # s014 r6-2: one shot 1322-1410
if V3:
    CUTS.insert(CUTS.index(1410), 1366)        # v3: the punch-in 1322-1365, the wide from 1366
BLACK_F = 956
# v3: the pager in the punch-in (song frame, x, y at 1920x1080), read off renders/IRIS-EP01-v3-picture-000-1422.mp4
PAGER_TRACK = [(1334, 1005, 860), (1342, 990, 875), (1350, 1000, 885), (1358, 1000, 885), (1365, 1005, 852)]
COL = {"color": "#EDEBE6", "ink": "#0A0A0A", "accent": "#F2B134"}


def shot_end(f: int) -> int:
    return next(c for c in CUTS if c > f)


def callout(cid, f, end, anchor, label, title, rows=(), note="", track=None, source=None):
    p = {"at": 0, "anchor": anchor, "label": label, "title": title, "rows": list(rows), **COL}
    if track:
        p["track"] = [{"at": a - f, "x": x, "y": y} for a, x, y in track]
    if source:
        p["source"] = source
    return {"id": cid, "name": cid, "from": f, "duration": end - f, "scene": "Callout", "note": note, "props": p}


def classifier(cid, f, end, targets, note=""):
    return {"id": cid, "name": cid, "from": f, "duration": end - f, "scene": "Classifier", "note": note,
            "props": {"targets": targets, **COL}}


def box(at, x, y, w, h, key, value, conf, side=None):
    t = {"at": at, "box": {"x": x, "y": y, "width": w, "height": h}, "rows": [{"at": at, "key": key, "value": value, "conf": conf}]}
    if side:
        t["side"] = side
    return t


def split_words(c: dict, f: int, end: int) -> dict:
    """A copy of a lyric / slam clip from song frame f to end, its frames re-based (earlier words keep negative frames)."""
    n = copy.deepcopy(c)
    d = f - c["from"]
    n.update({"from": f, "duration": end - f, "id": f"{c['id']}@{f}", "name": f"{c.get('name', c['id'])} @{f}"})
    for ln in n["props"].get("lines", []):
        ln["at"] -= d
        for w in ln.get("words", []):
            w["at"] -= d
    for r in n["props"].get("rows", []):
        r["at"] -= d
    lines = n["props"].get("lines")
    if lines is not None:
        keep = [ln for ln in lines if ln["at"] < end - f]
        n["props"]["lines"] = keep
    for s in n["props"].get("spots", []):
        s["at"] = max(0, s["at"] - d)
    return n


def per_shot(c: dict) -> list[dict]:
    """Split a clip at every cut it runs over."""
    a, z = c["from"], c["from"] + c["duration"]
    out, f = [], a
    while f < z:
        e = min(shot_end(f), z)
        out.append(c if (f == a and e == z) else split_words(c, f, e))
        f = e
    return out


def main() -> int:
    L = json.loads(SRC.read_text())
    T = {t["id"]: t for t in L["tracks"]}
    # picture
    old = T["pic-print"]["clips"][0]
    new = copy.deepcopy(old)
    new.update({"id": "print-v2-full", "name": "v2 picture (opening_v2.py)", "src": "assets/video/iris/print-v2b-000-1422.mp4",
                "note": "AI-VIDEO excerpt opening_v2.py: stills s003/s007/s009/s010, s004 hold, dot screen 0-955, black 956-978, "
                        "line screen 979-, one-offs K s005 / D s007 / C2 s011 / B s013a (renders/IRIS-EP01-v2-picture-000-1422.mp4)"})
    hidden_v2 = None
    if V2C:
        hidden_v2 = {"id": "pic-print-v2", "name": "画面·v2（旧 s014）", "kind": "video", "hidden": True, "clips": [copy.deepcopy(new)]}
        new.update({"id": "print-v2c-full", "name": "v2c picture (opening_v2.py --join-c)", "src": "assets/video/iris/print-v2c-000-1422.mp4",
                    "note": new["note"].replace("renders/IRIS-EP01-v2-picture-000-1422.mp4", "renders/IRIS-EP01-v2c-picture-000-1422.mp4")
                    + "; v2c: s014 = MO07 r6-2 in one span 1322-1410 (material offset 0.035 s), no jump on 1377"})
    hidden_v2c = None
    if V3:
        hidden_v2c = {"id": "pic-print-v2c", "name": "画面·v2c（统一模糊）", "kind": "video", "hidden": True, "clips": [copy.deepcopy(new)]}
        new.update({"id": "print-v3-full", "name": "v3 picture (opening_v2.py --join-3)", "src": "assets/video/iris/print-v3-000-1422.mp4",
                    "note": new["note"].replace("renders/IRIS-EP01-v2c-picture-000-1422.mp4", "renders/IRIS-EP01-v3-picture-000-1422.mp4")
                    + "; v3: s004 plays through (no hold); s014 punch-in 1322-1365 (4K source) / wide 1366-1409; per-shot blur classes A-E"})
    T["pic-print"]["clips"] = [new]
    T["pic-print"]["name"] = "画面·v2（静帧 + 网点/线网 + 一次性处理）"
    hidden_v4r11 = {"id": "pic-print-v4r11", "name": "画面·v4r11（旧）", "kind": "video", "hidden": True, "clips": [old]}
    # ticket -> chip
    T["ticket"]["hidden"] = True
    chip = {"id": "ticket-chip", "name": "P0 小组件（v2）", "kind": "scene", "clips": [{
        "id": "chip-p0", "name": "chip-p0", "from": 231, "duration": 1422 - 231, "scene": "TicketChip",
        "note": "v2: EV MONTHS-size widget (230x83) under the spectrum; one line + PAGED count; keys from the old ticket-p0",
        "props": {"countLabel": "PAGED", "right": 1824, "y": 124, "w": 230, "h": 83, **COL, "keys": [
            {"at": 0, "line": "INC-WEEK · SEV-LOW", "count": 1}, {"at": 307 - 231, "count": 2},
            {"at": 625 - 231, "line": "INC-0804 · SEV-MED"}, {"at": 791 - 231, "line": "INC-0902 · SEV-MED"},
            {"at": 958 - 231, "invert": True}, {"at": 979 - 231, "invert": False},
            {"at": 1014 - 231, "line": "INC-0902 · SEV-HIGH"},
            *({"at": a - 231, "count": n} for a, n in zip([1084, 1103, 1112, 1117, 1139, 1151, 1162, 1173, 1189, 1195, 1217], range(3, 14))),
            {"at": 1290 - 231, "stamp": "ALL HANDS"}]}}]}
    # slam
    S = {c["id"]: c for c in T["slam"]["clips"]}
    all1 = S["slam-allhands-1"]
    allA = copy.deepcopy(all1)
    allA.update({"id": "slam-all-black", "from": 958, "duration": 979 - 958,
                 "note": "v2: ALL slams on 39.897 (f958) on the black frames 956-978 (EV S0011/S0012), no screen"})
    allA["props"]["rows"] = [{"text": "ALL", "at": 0, "mode": "slam", "cap": 270, "baseline": 680}]
    allB = split_words(all1, 979, 1014)
    allB["props"]["rows"][0]["mode"] = "fade"
    slam = [S["masthead-s001"], S["slam-6000"], allA, allB, *per_shot(S["slam-allhands-2"])]
    # lyrics
    Y = {c["id"]: c for c in T["lyrics"]["clips"]}
    Y["cov-s003"]["props"]["spots"] = [{"at": 0, "x": 1320, "y": 300, "width": 520}]
    Y["cov-s005"]["props"]["spots"] = [{"at": 0, "x": 72, "y": 320, "width": 640}]
    c67 = Y["cov-s006-7"]
    c67 = split_words(c67, 625, 714)
    c67["id"] = "cov-s007"
    c67["props"]["spots"] = [{"at": 0, "x": 1420, "y": 330, "width": 420}]
    Y["cov-s009"]["props"]["spots"] = [{"at": 0, "x": 72, "y": 180, "width": 600}]
    Y["cov-s010"]["duration"] = BLACK_F - Y["cov-s010"]["from"]
    lyrics = [Y["cov-s003"], Y["sub-s004"], Y["cov-s005"], c67, Y["sub-s008"], Y["cov-s009"], Y["cov-s010"],
              *per_shot(Y["sung-chorus"]), *per_shot(Y["sung-postchorus"])]
    # devices
    D = {c["id"]: c for c in T["devices"]["clips"]}
    dev = []
    # s001: the pager label bottom right; its leader follows the pager (positions read off the v2 picture, frames 55-98)
    dev.append(callout("lcd-s001", 55, 99, {"x": 580, "y": 640}, {"x": 1440, "y": 860}, "ON CALL · IRIS",
                       note="v2: board s001 pager.lcd @2.287 (f55); label bottom right, leader on the pager (track)",
                       track=[(55, 580, 640), (62, 650, 620), (69, 600, 620), (76, 560, 640), (83, 600, 700), (90, 760, 760), (98, 820, 900)]))
    dev.append(classifier("cls-s001-iris", 30, 99, [box(0, 1060, 240, 520, 480, "IRIS", "AWAKE", 0.93)],
                          note="v2: board s001 action (the page wakes her); box on her face"))
    # s002
    dev.append(callout("label-guestlist", 143, 231, {"x": 330, "y": 760}, {"x": 72, "y": 880}, "GUEST LIST",
                       ["SEATING · ON-CALL ENGINEERS ONLY"], note="board s002 label @5.979 (f143); v2 bottom left"))
    dev.append(callout("leader-outside", 188, 231, {"x": 1205, "y": 590}, {"x": 1420, "y": 300}, "OUTSIDE",
                       note="board s002 leader on the fire-door gap @7.814 (f188); top right"))
    dev.append(classifier("cls-s002-frontrow", 150, 231, [box(0, 40, 420, 520, 420, "FRONT ROW", "ON-CALL", 0.96)],
                          note="v2: the seating of board s002's guest list, boxed on the front row (left)"))
    # s003 (still)
    ch = D["chart-frontrow"]
    ch["props"].update({"x": 1320, "y": 820})
    dev.append(ch)
    dev.append(D["classifier-engineer"])
    dev.append(callout("label-s003-paged", 236, 307, {"x": 520, "y": 600}, {"x": 72, "y": 880}, "PAGED", ["INC-WEEK · SEV-LOW"],
                       note="v2: board s004 ticket id / SEV, on the engineer's phone; bottom left"))
    # s004
    dev.append(callout("slip-s004", 310, 406, {"x": 1290, "y": 880}, {"x": 1400, "y": 640}, "EVERY LOOK · PAGED",
                       ["SHOW SCALE · ONLY P0 IS OPENAI'S OWN ALERT LEVEL"],
                       note="v2: board s004 ticket title / scale (the card's print), as a tag on her badge; right"))
    lp = D["leader-phone"]
    dev.append(lp)
    # s005
    cs = D["chat-s005"]
    cs["props"].update({"x": 1290, "y": 600, "w": 560})
    dev.append(cs)
    dev.append(classifier("cls-s005-page", 412, 493, [box(0, 820, 520, 520, 480, "PAGE BACK", "HALF", 0.88)],
                          note="v2: lyric 'It got back half a page'; box on the page in her hands"))
    # s006
    dev.append(classifier("cls-s006-flash", 505, 625, [box(0, 20, 250, 380, 440, "PHOTOGRAPHER", "FLASH", 0.95),
                                                        box(8, 420, 200, 300, 380, "PHOTOGRAPHER", "FLASH", 0.91)],
                          note="v2: board s006 flash device (the take's own flashes), boxed on the photographers (left)"))
    dev.append(callout("label-s006-street", 520, 625, {"x": 1180, "y": 520}, {"x": 1460, "y": 820}, "STREET LOOKS",
                       note="v2: the chapter c2 name (HUD) as a tag on her; bottom right"))
    # s007 (still)
    dev.append(classifier("cls-s007-billboard", 650, 714, [box(0, 20, 40, 560, 520, "BILLBOARD", "OBSCURED", 0.62)],
                          note="v2: board s007 'billboard behind a tree'; box on the billboard (left)"))
    # s008
    dev.append(D["classifier-sticker"])
    dev.append(callout("label-s008-name", 730, 791, {"x": 1100, "y": 760}, {"x": 1440, "y": 880}, "NAME", ["BLANK"],
                       note="v2: board s008 'the blank name sticker'; bottom right"))
    # s009 (still)
    stk = D["strike-s009a"]
    stk["from"], stk["duration"] = 806, 869 - 806
    dev.append(stk)
    dev.append(classifier("cls-s009-not", 844, 869, [box(0, 1500, 280, 300, 260, "NOT", "SCRATCHED", 0.97, side="below")],
                          note="v2: lyric 'scratched the not' (f844); box on the scratch"))
    # s010 (still; black from 956)
    sp = D["spell-s010"]
    sp["duration"] = BLACK_F - sp["from"]
    dev.append(sp)
    dev.append(classifier("cls-s010-billboard", 889, BLACK_F, [box(0, 90, 330, 300, 200, "BILLBOARD", "US-101", 0.9, side="below")],
                          note="v2: board s010 source (US-101 near Potrero Hill); box on the billboard"))
    # s011
    g = D["gauge-s011"]
    g["duration"] = 1078 - g["from"]
    g["props"].update({"x": 1600, "y": 400})
    dev.append(g)
    # s012a-d
    dev.append(D["classifier-holding"])
    dev.append(classifier("cls-s012b-hold", 1130, 1178, [box(0, 720, 80, 760, 860, "HOLDING ON", "TIGHT", 0.9)],
                          note="v2: lyric 'hold on tight'; box on her"))
    dev.append(callout("label-s012b-paged", 1135, 1178, {"x": 1150, "y": 960}, {"x": 1460, "y": 860}, "PAGED", ["SEV-HIGH"],
                       note="v2: the ticket's SEV on her waist pager; bottom right"))
    hy = D["hypnogram-s012"]
    hy["duration"] = 1211 - hy["from"]
    hy["props"].update({"x": 1380, "y": 260})
    dev.append(hy)
    dev.append(classifier("cls-s012c-eyes", 1186, 1211, [box(0, 760, 120, 420, 300, "EYES", "CLOSED", 0.97)],
                          note="v2: s012c closed-eye close-up; box on her eyes"))
    # s013a/b
    dev.append(callout("label-s013a-call", 1226, 1255, {"x": 520, "y": 520}, {"x": 1380, "y": 800}, "INCOMING",
                       ["SEV-HIGH · DECLINE DISABLED"], note="v2: board s013 ui.call words; bottom right"))
    dev.append(classifier("cls-s013a-phone", 1230, 1255, [box(0, 300, 160, 520, 720, "CALL", "INCOMING", 0.99)],
                          note="v2: box on the phone"))
    dev.append(classifier("cls-s013b-oncall", 1262, 1322, [box(0, 700, 40, 700, 760, "ON CALL", "ALL NIGHT", 0.95)],
                          note="v2: board s011 gauge words; box on her"))
    dev.append(callout("label-s013b-pager", 1270, 1322, {"x": 1100, "y": 960}, {"x": 1460, "y": 860}, "PAGED", ["13"],
                       note="v2: the chip's count on her waist pager; bottom right"))
    # s014
    pg = D["pagers-s014"]
    pg["props"].update({"x": 1800, "bottom": 950 if V2D else 990})     # v2d: clear of the HUD's SONG/BAR readout
    for piece in per_shot(pg):
        if piece is not pg:
            piece["props"]["offset"] = piece["from"] - pg["from"]
        dev.append(piece)
    if V3:
        dev.append(callout("callout-s014p-pager", PAGER_TRACK[0][0], 1366, {"x": PAGER_TRACK[0][1], "y": PAGER_TRACK[0][2]}, {"x": 1380, "y": 560},
                           "PAGER · 10:02 · BUZZING", note="v3: the punch-in on the pager press; leader on the pager (track, read off the v3 picture)",
                           track=PAGER_TRACK))
    dev.append(classifier("cls-s014a-frontrow", 1372 if V3 else 1330, 1410 if V2C else 1377,
                          [box(0, 40, 600, 520, 380, "LOOKING AT", "THEIR LAPTOP" if V2D else "THEIR PAGER", 0.96)],
                          note="v2: board s003 chart words, on the front row of the runway (left)"
                               + ("; v2c: ends on the 1410 cut (s014 r6-2 is one shot; the front row stays heads down)" if V2C else "")))
    for c in dev + lyrics + slam:
        e = c["from"] + c["duration"]
        if e > shot_end(c["from"]) or (c["from"] < BLACK_F <= e - 1 and c["id"] != "slam-all-black"):
            raise SystemExit(f"{c['id']} runs over its cut ({c['from']}-{e})")
    srt = lambda cs: sorted(cs, key=lambda c: c["from"])
    T["slam"]["clips"], T["lyrics"]["clips"], T["devices"]["clips"] = srt(slam), srt(lyrics), srt(dev)
    # overlapping clips go to extra lanes (devices-b, -c ...): one track holds clips one after another
    lanes: list[list[dict]] = []
    for c in T["devices"]["clips"]:
        lane = next((ln for ln in lanes if ln[-1]["from"] + ln[-1]["duration"] <= c["from"]), None)
        if lane is None:
            lanes.append(lane := [])
        lane.append(c)
    T["devices"]["clips"] = lanes[0]
    extra = [{"id": f"devices-{chr(98 + i)}", "name": f"事件图形 {chr(66 + i)}", "kind": "scene", "clips": ln} for i, ln in enumerate(lanes[1:])]
    tracks = []
    for t in L["tracks"]:
        if t["id"] == "ticket":
            tracks.append(chip)
        tracks.append(t)
        if t["id"] == "devices":
            tracks.extend(extra)
        if t["id"] == "pic-print":
            if hidden_v2c:
                tracks.append(hidden_v2c)
            if hidden_v2:
                tracks.append(hidden_v2)
            tracks.append(hidden_v4r11)
    L["tracks"] = tracks
    (PROJ / "layers.json").write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"devices": len(dev), "lyrics": len(lyrics), "slam": len(slam)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
