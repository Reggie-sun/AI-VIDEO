#!/usr/bin/env python3
"""Stage 9: map author-published Seedance clip windows (source_docs/FINDINGS.md section C2 table) onto our shots.

A clip row = {clip, song_start_s, len_s, kind, plate, storyboard_shots, words}. A shot overlaps a clip if the
shot's time range intersects [song_start, song_start+len]. This is only a *hint*: the edit may use any sub-window of a clip,
and covers/continuations share windows. Label every use of it `inferred` unless the author states the shot id.
Output: work/author_clip_hints.json  {shot_id: [clip rows overlapping]}
Run: python -I scripts/09_author_clip_hints.py <analysis_root>
"""
import json
import re
import sys
from pathlib import Path


def main(root):
    root = Path(root)
    txt = (root / "source_docs" / "FINDINGS.md").read_text()
    rows = []
    for line in txt.splitlines():
        m = re.match(r"\|\s*((?:SD|SX)\d+[^|]*|test-[^|]*)\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*(\w+)\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*(.*?)\s*\|\s*$", line)
        if not m:
            continue
        clip, start, ln, kind, plate, sb, words = m.groups()
        rows.append(dict(clip=clip.strip(), song_start_s=float(start), len_s=float(ln), kind=kind, plate=plate.strip(), storyboard_shots=[x.strip() for x in sb.split(",") if x.strip()], quoted_words=words.strip()))
    shots = json.loads((root / "work" / "shots.json").read_text())
    out = {}
    for s in shots:
        a, b = s["start_time"], s["end_time"]
        hit = [r for r in rows if r["song_start_s"] < b and r["song_start_s"] + r["len_s"] > a and not r["clip"].startswith("test-")]
        out[s["shot_id"]] = hit
    (root / "work" / "author_clip_hints.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("clip rows", len(rows), "shots with hint", sum(1 for v in out.values() if v))


if __name__ == "__main__":
    main(sys.argv[1])
