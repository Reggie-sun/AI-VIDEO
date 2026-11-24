#!/usr/bin/env python3
"""Pick one start/end per lyric word from three independent timings -> timing/words.json + timing/listen.json.

  python3 -I outputs/ai-city-takeover/ep01/v4/song/resolve.py

Inputs (all in timing/): words-ctc.json (CTC on the vocal stem, timing.py; each word also carries suno_start),
whisper-transcribe.json (unprompted Whisper large-v3 on the vocal stem; never saw the lyric).
Rule per word:
  - CTC and Suno within 0.25 s  -> CTC.
  - otherwise find the same word in Whisper within 3 s of either; if Whisper is nearer Suno -> Suno, nearer CTC -> CTC
    (Whisper starts run ~0.2-0.3 s early on this stem, so it only votes, it never supplies a time).
  - no Whisper match -> CTC, and the word goes to listen.json for a human ear check.
  - OVERRIDES: lines whose sung position is known to be the first of a repeated ad-lib take Suno for the whole line.
Starts are kept monotonic inside a line (a word never starts before the previous one).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

T = Path(__file__).resolve().parent / "timing"
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
# First post-chorus: "P zero. That's all." is sung at ~76.3 s (Suno, Whisper 75.8) and repeated as an ad-lib at ~83 s;
# CTC locked onto the repeat. The lyric line is the first one.
OVERRIDES = {("P zero. That's all.", 0): "suno"}


def main() -> None:
    ctc = json.loads((T / "words-ctc.json").read_text())
    wh = [(norm(w["text"]), w["start"]) for w in json.loads((T / "whisper-transcribe.json").read_text())["words"]]
    seen: dict[str, int] = {}
    listen, counts, lines = [], {"ctc": 0, "suno": 0, "ctc-unconfirmed": 0}, []
    for ln in ctc["lines"]:
        occ = seen.get(ln["en"], 0)
        seen[ln["en"]] = occ + 1
        force = OVERRIDES.get((ln["en"], occ))
        words, prev = [], 0.0
        for w in ln["words"]:
            c, s = w["start"], w["suno_start"]
            if force == "suno":
                src = "suno"
            elif abs(c - s) <= 0.25:
                src = "ctc"
            else:
                n = norm(w["text"])
                cand = [t for x, t in wh if x == n and min(abs(t - c), abs(t - s)) < 3]
                if not cand:
                    src = "ctc-unconfirmed"
                    listen.append({"t": c, "suno": s, "word": w["text"], "line": ln["en"]})
                else:
                    t = min(cand, key=lambda t: min(abs(t - c), abs(t - s)))
                    src = "suno" if abs(t - s) < abs(t - c) else "ctc"
            counts[src] += 1
            if src == "suno":
                dur = max(0.12, w["end"] - w["start"])
                st, en = s, s + dur
            else:
                st, en = c, w["end"]
            st = max(st, prev)
            en = max(en, st + 0.05)
            prev = st
            words.append({"text": w["text"], "start": round(st, 3), "end": round(en, 3), "src": src})
        lines.append({"en": ln["en"], "mode": ln["mode"], "section": ln["section"],
                      "start": words[0]["start"], "end": words[-1]["end"], "words": words})
    out = {**ctc, "timing_source": "per word: CTC (MMS_FA, vocal stem) unless Suno and an unprompted Whisper pass agree "
                                   "against it; see resolve.py", "lines": lines}
    (T / "words.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    (T / "listen.json").write_text(json.dumps({"note": "CTC and Suno disagree by >0.25 s and Whisper did not hear the word; "
                                                       "check by ear on the karaoke page", "words": listen},
                                              ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({**counts, "listen": len(listen)}))


if __name__ == "__main__":
    main()
