"""Tests for board_audit.py: a minimal passing board and one failure per main gate."""
import copy
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("board_audit", Path(__file__).with_name("board_audit.py"))
ba = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ba)

BEATS = {"duration": 16.0, "beats": [i * 0.5 for i in range(33)], "downbeats": [i * 2.0 for i in range(9)]}
WORDS = {"lines": [
    {"en": "one two", "words": [{"text": "one", "start": 1.0, "end": 1.4}, {"text": "two", "start": 1.5, "end": 1.9}]},
    {"en": "three", "words": [{"text": "three", "start": 9.0, "end": 9.5}]},
]}
KINDS = ["counter", "tag", "chart", "terminal", "strike", "map"]


def shot(i, t0, t1, **kw):
    s = {"id": f"s{i:03d}", "t0": t0, "t1": t1, "lead_on_screen": True, "framing": "MS", "motion_tier": "still",
         "plate": f"p{i}", "type": [], "devices": []}
    s.update(kw)
    return s


def good_board():
    shots = [
        shot(1, 0.0, 4.0, type=[{"line": 0, "mode": "subtitle", "text": "one two"}],
             devices=[{"kind": k, "line": 0} for k in KINDS[:3]]),
        shot(2, 4.0, 8.0, motion_tier="sung", clip="C1"),
        shot(3, 8.0, 12.0, type=[{"line": 1, "mode": "subtitle", "text": "three"}],
             devices=[{"kind": k, "line": 1} for k in KINDS[3:]], motion_tier="plate3d", treatment="parallax"),
        shot(4, 12.0, 16.0, motion_tier="plate3d", treatment="rack"),
    ]
    return {"duration": 16.0, "shots": shots}


def run(board, **kw):
    args = dict(lead=0.7, sung_max=110, motion_max=140, banned=["Tumbler"])
    args.update(kw)
    return ba.audit(board, WORDS, BEATS, **args)


def test_good_board_passes():
    r = run(good_board())
    assert r["pass"], r["fails"]
    assert r["report"]["lead_share"] == 1.0


def test_gap_fails_tile():
    b = good_board()
    b["shots"][1]["t1"] = 7.5
    assert "tile" in run(b)["fails"]


def test_off_beat_cut_fails():
    b = good_board()
    b["shots"][0]["t1"] = b["shots"][1]["t0"] = 4.2
    assert "cuts" in run(b)["fails"]


def test_untyped_line_fails():
    b = good_board()
    b["shots"][2]["type"] = []
    assert "words_typed" in run(b)["fails"]


def test_line_without_graphic_fails():
    b = good_board()
    b["shots"][2]["devices"] = []
    assert "graphics" in run(b)["fails"]


def test_low_lead_share_fails():
    b = good_board()
    for s in b["shots"][:3]:
        s["lead_on_screen"] = False
    assert "lead_share" in run(b)["fails"]


def test_long_sung_clip_fails():
    b = good_board()
    for s in b["shots"][2:]:
        s.update(motion_tier="sung", clip="C1")
    assert "clip_windows" in run(b)["fails"]


def test_plate_reused_far_apart_fails():
    b = good_board()
    b["shots"][3]["plate"] = "p1"
    assert "plates_unique" in run(b)["fails"]


def test_repeated_treatment_fails():
    b = good_board()
    b["shots"][3]["treatment"] = "parallax"
    assert "treatments" in run(b)["fails"]


def test_banned_word_fails():
    b = copy.deepcopy(good_board())
    b["shots"][0]["action"] = "a Tumbler Ridge headline"
    assert "banned" in run(b)["fails"]
