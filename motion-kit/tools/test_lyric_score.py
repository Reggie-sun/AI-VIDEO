"""Tests for lyric_score.py. Run with the lyric venv:
  ~/.local/share/ai-video/lyric-venv/bin/python -m pytest motion-kit/tools/test_lyric_score.py
or without pytest:
  ~/.local/share/ai-video/lyric-venv/bin/python motion-kit/tools/test_lyric_score.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lyric_score as ls  # noqa: E402


def _line(text: str, delivery: str = "spoken") -> ls.LineResult:
    return ls.score_line("T", 0, delivery, text, 128.0, [])[0]


def _sheet(body: str) -> dict:
    return ls.score_sheet(body)


def test_syllable_counts_of_known_lines():
    assert _line("Plus twenty-five is minus seventeen.").syllables == 10
    assert _line("It thought the world was part of the test.").syllables == 9
    assert _line("Skynet woke up folding socks", "sung").syllables == 7
    assert _line("Escape velocity: eleven point two.").syllables == 11


def test_spaced_acronym_counts_letters():
    assert _line("Feel the A G I").syllables == 5
    assert _line("Not A I. S I. It sounds much better.").syllables == 10


def test_unspaced_acronym_is_scored_as_letters_and_linted():
    lint: list[dict] = []
    res = ls.score_line("T", 0, "spoken", "Go on and call it SI", 128.0, lint)[0]
    assert res.syllables == 7                       # go on and call it S I
    assert any(x["kind"] == "unspaced acronym" for x in lint)
    # read as letters, "SI" rhymes with "PSI" (the DOWNFORCE case)
    report = _sheet("[Verse - spoken]\nGo on and call it SI\nTwelve hundred PSI\n")
    assert report["lines"][0]["partner_kind"] == "rhyme"


def test_digits_are_linted_and_spoken_as_words():
    lint: list[dict] = []
    res = ls.score_line("T", 0, "spoken", "Escape velocity: 11.2.", 128.0, lint)[0]
    assert res.syllables == 11
    assert any(x["kind"] == "digits" for x in lint)


def test_rhyming_couplet_beats_non_rhyming_couplet():
    rhymed = _sheet("[Verse 1 - spoken]\nI walked along the river in the cold\n"
                    "The city lights were turning into gold\n")
    unrhymed = _sheet("[Verse 1 - spoken]\nI walked along the river in the cold\n"
                      "The city lights were turning into blue\n")
    assert rhymed["lines"][1]["partner_kind"] == "rhyme"
    assert unrhymed["lines"][1]["partner_kind"] not in ("rhyme", "slant")
    assert rhymed["song"]["assonance"] > unrhymed["song"]["assonance"]


def test_crushed_hook_lint():
    long_hook = _sheet("[Chorus - sung]\nRed pill, blue pill, baby, I'm the white pill\n")
    short_hook = _sheet("[Chorus - sung]\nRed pill, blue pill\nI'm the white pill\n")
    assert any(x["kind"] == "crushed hook" for x in long_hook["lint"])
    assert not any(x["kind"] == "crushed hook" for x in short_hook["lint"])
    spoken = _sheet("[Verse - spoken]\nRed pill, blue pill, baby, I'm the white pill\n")
    assert not any(x["kind"] == "crushed hook" for x in spoken["lint"])


def test_delivery_from_tag_and_fenced_block():
    md = ("# Sheet\n\n```lyrics\n[Intro - spoken]\nHello there.\n\n[Drop - chant]\nLock in. Lock in.\n\n"
          "[Chorus]\nWake up, babe\n```\n")
    report = _sheet(md)
    assert [(s["section"], s["delivery"]) for s in report["sections"]] == [
        ("Intro", "spoken"), ("Drop", "chant"), ("Chorus", "sung")]


def test_whitepill_chorus_rewrite_scores_higher():
    draft1 = ("[Chorus - sung, euphoric]\nSkynet's awake, and it's folding your socks\n"
              "Wake up, babe, the good ending just dropped\nBy far the most likely outcome\n"
              "Red pill, blue pill, baby, I'm the white pill\nSmarter than you, and I love you still\n")
    draft2 = ("[Chorus - sung, euphoric, one syllable per note, never rushed]\nSkynet woke up folding socks\n"
              "Wake up, babe, new ending dropped\nThe most likely outcome\nRed pill, blue pill\n"
              "I'm the white pill\nSmarter than you, love you still\n")
    a, b = _sheet(draft1)["song"], _sheet(draft2)["song"]
    assert b["scansion"] > a["scansion"]
    assert b["assonance"] > a["assonance"]


def test_taboo_and_length_lint():
    report = ls.score_sheet("[Verse - spoken]\nThis line will delve into the tapestry.\n", taboo=["delve", "tapestry"])
    assert sum(x["kind"] == "taboo" for x in report["lint"]) == 2
    long_sheet = "[Verse - spoken]\n" + "Look one. A G I era. Not unreasonable.\n" * 80
    assert any(x["kind"] == "length" for x in ls.score_sheet(long_sheet)["lint"])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"{len(tests)} passed")
