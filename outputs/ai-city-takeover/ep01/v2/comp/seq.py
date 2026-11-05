#!/usr/bin/env python3
"""Generated shots -> numbered JPG sequences the motion-kit runtime plays as plates (run from the repository root):

  uv run python outputs/ai-city-takeover/ep01/v2/comp/seq.py [--chorus comp/chorus.json]

Each source is the exact MP4 that passed its per-shot gate or that the user chose (path and SHA-256 checked).
The window [in, in + duration] of the source is conformed to 30 fps CFR with ffmpeg's fps filter (nearest-frame,
no interpolation) and written as seq/<shot>/0000.jpg ... Writes seq/sequences.json for build.py and main.js.
A chorus pass (chorus.json, the same file build.py read) plays one lip-sync take at the lag that
motion-kit/tools/sync_check.py measured: in-point = shot start - song_t0 + lag, from the take's sync.json, whose
take SHA-256 must match. Still segments of a pass are plates the engine moves; they need no sequence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

COMP = Path(__file__).resolve().parent
V2 = COMP.parent
FPS = 30
FETCH = "project/state/video-generation/fetch/files"

# shot: (source mp4, sha256, in-point seconds in the source, why this window)
SOURCES = {
    # v3 (user: no visible waking in c1): K1a -> K1c, the lid lifts from clip 2.4 s and is fully open by 3.3 s.
    # c3 keeps c1's S2 cut on 'woke' (2.867 s), so in-point 0.6667 opens the eye at about 1.73-2.63 s, before the cut
    "S1": (V2 / "gen/S1v3" / FETCH / "4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5.mp4",
           "4d37fe3d9ebc1a9309866f72b2a3dfc018739e49caecd2aec01a19fac8e424d5", 0.6667, "the eye opens before 'woke'"),
    # c5 (user on c4: stills, the mouth barely moves; "睁眼之后突然转到这个人也非常奇怪"): S2 no longer plays A01-v2
    # (she looks down, another face) and S5 no longer plays S5v3 (the frown); main.js moves their approved stills
    "S3": (V2 / "gen/S3" / FETCH / "4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7.mp4",
           "4d017c1be08117a628ec7ed6b434b487c5c19c31f13881c19615770c0d7529d7", 2.0, "later half of the push, nearer the red gap"),
    # v3: her eyes leave the lens for a pane at clip 1.15 s and come back from 4.6 s; in-point 1.4 starts the
    # turn back on 'cached' (18.0 s) and lands it on the lens by about 18.4 s
    "S7": (V2 / "gen/S7v3" / FETCH / "3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4",
           "3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21", 1.4, "watching the panes, back to us on 'cached'"),
    # c10: her last look on "through the": S7v3 again from clip 4.95 s, back on the lens with the slight smile the user
    # liked (「这里倒是可以」), framed closer by the code camera in main.js
    "S9h": (V2 / "gen/S7v3" / FETCH / "3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21.mp4",
            "3bf717956815a3b7a62b92f5e4b4633b1cfd9865144655c2f842be730dfd4c21", 4.95, "her last look: back on the lens, slight smile"),
    # the chorus passes S8a and S8b (and their cutaways) come from chorus.json; see chorus_sources()
    "S9a": (V2 / "gen/S9a" / FETCH / "9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728.mp4",
            "9616a8a21cdfa2fc0eaf0c4cd04813bc94dea2b3fda04dd5a4c604c660407728", 0.16,
            "door fully shut at source 2.45 s = end of 'closed' (shot time 2.29 s)"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetched(take: str) -> tuple[Path, str]:
    """The one fetched MP4 of a generated take (its file name is its SHA-256)."""
    files = sorted((V2 / "gen" / take / FETCH).glob("*.mp4"))
    if len(files) != 1:
        raise SystemExit(f"{take}: expected one fetched MP4, found {len(files)}")
    return files[0], files[0].stem


def chorus_sources(chorus: dict, starts: dict) -> dict:
    """Image sequences for the chorus segments that play a take; still segments are plates the engine moves."""
    out = {}
    for p in chorus["passes"]:
        for seg in p["segments"]:
            if seg["kind"] != "take":
                continue
            if "sync" not in seg:                                     # c13: a take with no lip sync plays from its own 'in'
                src, sha = fetched(seg["take"])
                out[seg["shot"]] = (src, sha, seg["in"], f"{seg['take']} from {seg['in']} s: {seg['why']}")
                continue
            sync = json.loads((V2 / seg["sync"]).read_text())
            lag, t0 = sync["placement"]["lag_s"], sync["song_t0"]
            out[seg["shot"]] = (COMP.parents[4] / sync["take"], sync["take_sha256"], round(starts[seg["shot"]] - t0 + lag, 4),
                                f"{seg['take']} at its measured lag {lag:+.4f} s ({sync['placement']['method']}; {seg['sync']})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chorus", type=Path, default=COMP / "chorus.json", help="the chorus edit build.py was run with")
    args = ap.parse_args()
    events = json.loads((COMP / "data/events.json").read_text())["events"]
    # c12 inserts (data/inserts.json, from build.py) cut away and back over a c11 shot: the c11 shots keep their windows
    ins_path = COMP / "data/inserts.json"
    ins = json.loads(ins_path.read_text()) if ins_path.exists() else {"inserts": {}, "pips": {}}
    full = json.loads((COMP / "inserts.json").read_text()) if ins["inserts"] or ins["pips"] else {"inserts": [], "pips": []}
    is_insert = lambda s: s in ins["inserts"] or s.endswith("_back")
    cuts = sorted((k[4:] for k in events if k.startswith("cut_") and not is_insert(k[4:])), key=lambda s: events[f"cut_{s}"]["t"])
    order = ["S1", *cuts]
    starts = {s: (0.0 if s == "S1" else events[f"cut_{s}"]["t"]) for s in order}
    ends = {s: (starts[order[i + 1]] if i + 1 < len(order) else 30.5) for i, s in enumerate(order)}
    sources = {**SOURCES, **chorus_sources(json.loads(args.chorus.read_text()), starts)}
    # an insert from a take: its own window, [start, back cut or the c11 cut it runs into]
    cut_t = {k[4:]: v["t"] for k, v in events.items() if k.startswith("cut_")}
    for i in full["inserts"]:
        if i["kind"] != "take":
            continue
        src, sha = fetched(i["take"])
        t0 = cut_t[i["id"]]
        t1 = cut_t.get(f"{i['id']}_back") or cut_t[i["end"]["cut"]]
        starts[i["id"]], ends[i["id"]] = t0, t1
        sources[i["id"]] = (src, sha, i["in"], f"insert: {i['why']}")
    missing = [s for s in sources if s not in starts]
    if missing:
        raise SystemExit(f"no cut for {missing}: run build.py with the same --chorus first")
    out_root = COMP / "seq"
    out_root.mkdir(exist_ok=True)
    for old in out_root.iterdir():                                  # a shot dropped by another chorus edit
        if old.is_dir() and old.name not in sources:
            shutil.rmtree(old)
    manifest = {}
    for shot, (src, sha, t_in, why) in sources.items():
        actual = sha256(src)
        if not actual.startswith(sha):
            raise SystemExit(f"{shot}: source changed ({actual[:12]})")
        count = math.ceil((ends[shot] - starts[shot]) * FPS) + 2           # +2 frames of margin past the cut
        out = out_root / shot
        if out.exists():
            shutil.rmtree(out)
        out.mkdir()
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t_in:.4f}", "-i", str(src), "-vf", f"fps={FPS}",
                        "-frames:v", str(count), "-q:v", "2", "-start_number", "0", str(out / "%04d.jpg")], check=True)
        written = len(list(out.glob("*.jpg")))
        if written != count:
            raise SystemExit(f"{shot}: wrote {written} of {count} frames (source too short for the window)")
        manifest[shot] = {"dir": f"seq/{shot}", "count": count, "source": str(src.relative_to(COMP.parents[4])),
                          "source_sha256": actual, "in_seconds": t_in, "comp_start": starts[shot], "comp_end": ends[shot],
                          "why": why}
    (out_root / "sequences.json").write_text(json.dumps(manifest, indent=1) + "\n")
    # picture-in-picture frames from a take: 480x270 JPGs the 2D layer draws (main.js), in point and count from inserts.json
    pip_root = COMP / "pip"
    if pip_root.exists():
        shutil.rmtree(pip_root)
    pips = {}
    for p in full["pips"]:
        if p["kind"] != "take":
            continue
        src, sha = fetched(p["take"])
        out = pip_root / p["id"]
        out.mkdir(parents=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{p['in']:.4f}", "-i", str(src), "-vf", f"fps={FPS},scale=480:270",
                        "-frames:v", str(p["frames"]), "-q:v", "2", "-start_number", "0", str(out / "%04d.jpg")], check=True)
        if len(list(out.glob("*.jpg"))) != p["frames"]:
            raise SystemExit(f"{p['id']}: short source")
        pips[p["id"]] = {"dir": f"pip/{p['id']}", "count": p["frames"], "source": str(src.relative_to(COMP.parents[4])),
                         "source_sha256": sha256(src), "in_seconds": p["in"], "why": p["why"]}
    if pips:
        (pip_root / "pips.json").write_text(json.dumps(pips, indent=1) + "\n")
    print(json.dumps({k: v["count"] for k, v in manifest.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
