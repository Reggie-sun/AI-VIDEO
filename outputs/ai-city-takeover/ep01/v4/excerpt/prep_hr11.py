#!/usr/bin/env python3
"""v4r11 (2026-11-20): s012d's crop into the engineer from the 4K take instead of the 2304-wide picture. s012d holds
SG03-w1's picture 84 of media/seq/s012b under a 1.8x view (1.50x of the 2304 picture on the 1920 frame; the author's
rule, blur_study/REPORT.md section 3: "never punch a 1080p source past 1.1x"). The same clip picture (data/media-v4r1.json
s012b map[84]) decoded at the clip's own 3840x2160 is 0.90x under that view. It goes through the same steps as the
2304 picture (prep_media.decode, tail_lights_to_orange: the reds outside her matte to orange), at 3840x2160. The engine
(v4r11) scales the shot's view by the picture's own width. Run from the repository root:

  uv run python outputs/ai-city-takeover/ep01/v4/excerpt/prep_hr11.py

Writes media/hr11/s012d/0000.jpg and data/hr-v4r11.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prep_media as PM  # noqa: E402
from edl import EXC, V4  # noqa: E402

PIC = 84                                         # edl.SHOTS_V4R6 s012d fixed_pic


def main() -> int:
    m = json.loads((EXC / "data/media-v4r1.json").read_text())["shots"]["s012b"]
    idx = m["map"][PIC]
    clip = V4 / m["clip"]
    if PM.sha(clip) != m["clip_sha256"]:
        raise SystemExit("s012b clip SHA-256 differs from data/media-v4r1.json")
    PM.SEQ_W, PM.SEQ_H = 3840, 2160              # decode and the hue step read these at call time
    rgb = next(r for i, r in PM.decode(clip, {idx}) if i == idx)
    rgb, st = PM.tail_lights_to_orange(rgb)
    dst = EXC / "media/hr11/s012d/0000.jpg"
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(dst, quality=93, subsampling=0)
    meta = {"s012d": {"clip": m["clip"], "clip_sha256": m["clip_sha256"], "clip_picture": idx, "seq_picture": PIC,
                      "size": [3840, 2160], "hue": st, "file": str(dst.relative_to(EXC)), "sha256": PM.sha(dst),
                      "replaces": "media/seq/s012b/0084.jpg (2304x1296)"}}
    (EXC / "data/hr-v4r11.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
