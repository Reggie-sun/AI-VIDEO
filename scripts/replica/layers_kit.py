"""Shared pieces for building Agentcut layers.json for a replica (tutorial layout: phone + side panels).

An episode script (see examples/reference-replica/giftcard-jp/build_layers.py) owns the shot lists and calls:

- Timeline(tl): line / at helpers over make_timeline.py output.
- make_mapper(tl_old, tl_new, end_old, rewritten): map frames written on an older timeline onto the current one,
  piecewise-linear through every line start/end, so re-voiced groups shift and stretch the shots after them.
  Where one old frame is both a line end and the next line start, the start's new frame is used.
- remap_phone(): keep each phone shot's source span; recompute its playback rate for the new length.
- phone_clips / graphic_clips / side_clips / voice_sub_clips: clips for a frame range [lo, hi).
- assemble(): write layers.json + durationInFrames.

Phone shot: (from, to, source_key, trim_seconds, rate, boxes); box: (x0, y0, x1, y1, t0, t1) in source px / seconds.
Graphic shot: (from, to, scene, props). Side panel: (from, to, section, [(frame, "主句|副句")], [(frame, "步骤")]).
"""
from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
from contextlib import contextmanager
from fcntl import LOCK_EX, LOCK_NB, flock
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode

from ._local import agentcut_project, project_root, read_json, write_bytes

FPS = 30
SCREEN_TOP = 16
SCREEN_H = 896


class Timeline:
    def __init__(self, tl: list[dict]):
        self.groups = tl
        self.G = {g["id"]: g for g in tl}

    def line(self, gid: str, i: int) -> dict:
        return self.G[gid]["lines"][i]

    def at(self, gid: str, i: int, frac: float) -> int:
        ln = self.line(gid, i)
        return round(ln["from"] + (ln["to"] - ln["from"]) * frac)

    def end(self) -> int:
        last = self.groups[-1]
        return last["from"] + last["dur"]


def make_mapper(tl_old: list[dict], tl_new: list[dict], end_old: int, rewritten: dict[str, tuple[int, int, int, int]] | None = None):
    """Return (M, end_new). rewritten: gid -> (old_block_from, old_block_to, new_block_from, new_block_to) for groups
    whose lines changed count; their inside is laid out again by the episode, only the block edges are anchored."""
    rewritten = rewritten or {}
    G = {g["id"]: g for g in tl_new}
    ends, starts = {}, {}
    for g0 in tl_old:
        if g0["id"] in rewritten:
            continue
        if g0["id"] not in G:
            raise ValueError(f"group {g0['id']} is gone from the new timeline; list it in rewritten with its block edges")
        g = G[g0["id"]]
        starts[g0["from"]] = g["from"]
        ends[g0["from"] + g0["dur"]] = g["from"] + g["dur"]
        if len(g0["lines"]) == len(g["lines"]):
            for a, b in zip(g0["lines"], g["lines"]):
                starts[a["from"]] = b["from"]
                ends[a["to"]] = b["to"]
    # One old frame can be both a line's end and the next line's start. Shots cut on line starts, so starts win.
    pts = {0: 0, **ends, **starts}
    for oa, ob, na, nb in rewritten.values():
        pts[oa] = na
        pts[ob] = nb
    last0 = tl_old[-1]["from"] + tl_old[-1]["dur"]
    last = tl_new[-1]["from"] + tl_new[-1]["dur"]
    pts[end_old] = last + (end_old - last0)
    anchors = [(x, pts[x]) for x in sorted(pts)]
    for (a, b), (c, d) in zip(anchors, anchors[1:]):
        if d < b:
            raise ValueError(f"non-monotonic anchors {a}->{b}, {c}->{d}")

    def M(f: int) -> int:
        for (a, b), (c, d) in zip(anchors, anchors[1:]):
            if a <= f <= c:
                return round(b + (d - b) * (f - a) / (c - a)) if c > a else b
        raise ValueError(f)

    return M, anchors[-1][1]


def remap_phone(ph0, M):
    out = []
    for a, b, k, trim, rate, boxes in ph0:
        na, nb = M(a), M(b)
        if nb <= na:
            raise ValueError(f"shot {a}-{b} maps to {na}-{nb} (zero length)")
        out.append((na, nb, k, trim, rate * (b - a) / (nb - na), boxes))
    return out


def tile_check(ph, gr, end):
    spans = sorted([(a, b) for a, b, *_ in ph] + [(a, b) for a, b, *_ in gr])
    t = 0
    for a, b in spans:
        if a != t:
            raise ValueError(f"gap/overlap at {a} (expected {t})")
        if b <= a:
            raise ValueError(f"empty shot {a}-{b}")
        t = b
    if t != end:
        raise ValueError(f"shots end at {t}, timeline ends at {end}")


def _inside(a: int, b: int, lo: int, hi: int, what: str) -> bool:
    """True if [a, b) lies in [lo, hi), False if it lies outside; a clip straddling an edge is an error."""
    if lo <= a and b <= hi:
        return True
    if b <= lo or a >= hi:
        return False
    raise ValueError(f"{what} {a}-{b} crosses the range edge {lo}-{hi}; split it at the edge")


def range_check(ph, gr, lo: int, hi: int):
    """Shots inside [lo, hi) must tile it exactly (use before building a split part)."""
    tile_check([(a - lo, b - lo) for a, b, *_ in ph if _inside(a, b, lo, hi, "shot")],
               [(a - lo, b - lo) for a, b, *_ in gr if _inside(a, b, lo, hi, "graphic")], hi - lo)


def phone_clips(ph, src: dict, lo: int, hi: int):
    """src: key -> (asset_path, width, height, duration_seconds)."""
    video, overlay = [], []
    for i, (a, b, k, trim, rate, boxes) in enumerate(ph):
        if not _inside(a, b, lo, hi, "shot"):
            continue
        path, sw, sh, dur = src[k]
        end_src = trim + (b - a) / FPS * rate
        if end_src > dur + 0.01:
            raise ValueError(f"shot {i} reads {k} to {end_src:.2f}s past its {dur}s")
        w = SCREEN_H * sw / sh
        box = {"x": (1920 - w) / 2 / 1920, "y": SCREEN_TOP / 1080, "width": w / 1920, "height": SCREEN_H / 1080}
        video.append({"id": f"ph-{a}", "name": f"{k} {trim:.1f}s ×{rate:.2f}", "from": a, "duration": b - a, "src": path,
                      "trimStart": round(trim * FPS), "playbackRate": round(rate, 4), "muted": True, "fit": "cover", "box": box,
                      "note": f"{k} 源 {trim:.2f}–{end_src:.2f}s"})
        bx = []
        for x0, y0, x1, y1, t0, t1 in boxes:
            f0 = max(0, round((t0 - trim) / rate * FPS))
            f1 = min(b - a, math.ceil((t1 - trim) / rate * FPS))
            if f1 > f0:
                bx.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "from": f0, "to": f1})
        overlay.append({"id": f"pf-{a}", "name": "机身/点击框", "from": a, "duration": b - a, "scene": "Phone",
                        "props": {"sw": sw, "sh": sh, "boxes": bx}})
    return video, overlay


def graphic_clips(gr, lo: int, hi: int, resolve=None):
    """resolve(from_frame, scene, props) may turn a placeholder into props laid out relative to the clip start."""
    out = []
    for a, b, name, props in gr:
        if _inside(a, b, lo, hi, f"graphic {name}"):
            p = resolve(a, name, props) if resolve else props
            out.append({"id": f"gr-{a}", "name": name, "from": a, "duration": b - a, "scene": name, "props": p})
    return out


def side_clips(side, lo: int, hi: int, rename: dict | None = None):
    out = []
    for a, b, sec, caps, steps in side:
        if _inside(a, b, lo, hi, f"side panel {sec}"):
            out.append({"id": f"side-{a}", "name": sec, "from": a, "duration": b - a, "scene": "Steps",
                        "props": {"section": (rename or {}).get(sec, sec),
                                  "captions": [{"text": t, "from": f - a} for f, t in caps],
                                  "steps": [{"text": t, "from": f - a} for f, t in steps]}})
    return out


def voice_sub_clips(G: dict, gids, sub_text, font_size: int = 44):
    """Subtitle clips hold 4 frames past the voice, but never into the next group (G is in timeline order)."""
    order = list(G)
    subs, voice = [], []
    for gid in gids:
        g = G[gid]
        k = order.index(gid)
        hold = g["dur"] + 4
        if k + 1 < len(order):
            hold = min(hold, G[order[k + 1]]["from"] - g["from"])
        lines = [{"text": sub_text(ln["text"]), "from": max(0, ln["from"] - g["from"] - 2), "to": ln["to"] - g["from"]} for ln in g["lines"]]
        subs.append({"id": f"subs-{gid}", "name": f"字幕 {gid}", "from": g["from"], "duration": hold,
                     "scene": "Subs", "props": {"lines": lines, "fontSize": font_size}})
        voice.append({"id": f"vo-{gid}", "name": f"口播 {gid}", "from": g["from"], "duration": g["dur"], "src": g["src"], "volume": 1, "role": "voice"})
    return subs, voice


def shift(clips, d: int):
    for c in clips:
        c["from"] += d
    return clips


def _project_error(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.CONFIG_INVALID, message)


@contextmanager
def _exclusive_directory(directory: Path):
    fd = os.open(directory, os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            flock(fd, LOCK_EX | LOCK_NB)
        except BlockingIOError:
            raise _project_error("Agentcut project directory is busy.") from None
        yield
    finally:
        os.close(fd)


def _object(path: Path) -> dict:
    value = read_json(path)
    if not isinstance(value, dict):
        raise _project_error(f"{path.name} must be a JSON object.")
    return value


def _json_bytes(value: dict, indent: int) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=indent).encode("utf-8")


def assemble(
    project_dir: Path, end: int, *, subs, voice, chapters, overlay, side, graphics,
    video, music: dict, extra_voice=(), voice_label: str = "口播",
):
    """Assemble the native timeline of an explicitly selected Agentcut project."""
    layers = {
        "version": 1,
        "tracks": [
            {"id": "subs", "name": "口播字幕", "kind": "scene", "clips": subs},
            {"id": "chapters", "name": "章节栏", "kind": "scene", "clips": [
                {"id": "chapters-bar", "name": "章节", "from": 0, "duration": end, "scene": "Chapters",
                 "props": {"chapters": [{"label": l, "from": f} for l, f in chapters]}}]},
            {"id": "phone", "name": "机身与点击框", "kind": "scene", "clips": overlay},
            {"id": "side", "name": "两侧步骤", "kind": "scene", "clips": side},
            {"id": "graphics", "name": "图示", "kind": "scene", "clips": graphics},
            {"id": "shots", "name": "录屏", "kind": "video", "clips": video},
            {"id": "bg", "name": "背景", "kind": "scene", "clips": [
                {"id": "bg-grid", "name": "网格背景", "from": 0, "duration": end, "scene": "GridBg", "props": {}}]},
            {"id": "voice", "name": voice_label, "kind": "audio", "clips": voice + list(extra_voice)},
            {"id": "music", "name": "背景音乐", "kind": "audio", "clips": [
                {"id": "music-bed", "name": music["name"], "from": 0, "duration": end, **{k: v for k, v in music.items() if k != "name"}}]},
        ],
        "markers": [],
    }
    project_dir = agentcut_project(Path(project_dir))
    with _exclusive_directory(project_dir):
        backup = project_dir / ".full-backup"
        if backup.exists() or backup.is_symlink():
            raise _project_error("Restore the full Agentcut project before assembling layers.")
        layers_path = project_dir / "layers.json"
        if layers_path.is_symlink() or (layers_path.exists() and not layers_path.is_file()):
            raise _project_error("Agentcut layers.json must be a regular file.")
        metadata_path = project_dir / "project.json"
        pj = _object(metadata_path)
        pj["durationInFrames"] = end
        write_bytes(layers_path, _json_bytes(layers, 1))
        write_bytes(metadata_path, _json_bytes(pj, 2))
    print(project_dir.name, "end", end, "phone", len(video), "graphics", len(graphics), "side", len(side), "subs", len(subs))


def ensure_project(root: Path, slug: str, name: str, from_slug: str, scenes_src: Path) -> Path:
    """Create an Agentcut split part and reuse it only with matching scenes and assets."""
    if slug == from_slug or any(
        not value or value.startswith(".") or Path(value).name != value or "\\" in value
        for value in (slug, from_slug)
    ):
        raise _project_error("The main and part must be distinct project names.")
    root = project_root(Path(root))
    main = agentcut_project(root / from_slug)
    assets = main / "assets"
    if assets.is_symlink() or not assets.is_dir():
        raise _project_error("The main project's assets must be a directory within the project.")
    scenes_src = Path(scenes_src)
    if scenes_src.is_symlink() or not scenes_src.is_dir():
        raise _project_error("Scene sources must be an existing directory.")
    entries = sorted(scenes_src.rglob("*"))
    for entry in entries:
        if entry.is_symlink() or not (entry.is_dir() or entry.is_file()):
            raise _project_error("Scene sources must contain only regular files and directories.")
    part = root / slug
    with _exclusive_directory(root):
        if part.exists() or part.is_symlink():
            part = agentcut_project(part)
            pin = part / "assets"
            scenes = part / "scenes"
            if (_object(part / "project.json").get("name") != name
                    or not pin.is_symlink() or pin.resolve() != assets
                    or scenes.is_symlink() or not scenes.is_dir()):
                raise _project_error("The existing Agentcut part does not match this split.")
            for entry in entries:
                current = scenes / entry.relative_to(scenes_src)
                if (current.is_symlink() or current.is_dir() != entry.is_dir()
                        or (entry.is_file() and (
                            not current.is_file() or current.read_bytes() != entry.read_bytes()
                        ))):
                    raise _project_error("The existing Agentcut part has different scene files.")
        else:
            metadata = _object(main / "project.json")
            metadata["name"] = name
            with tempfile.TemporaryDirectory(prefix=".replica-part-", dir=root) as work:
                candidate = Path(work) / slug
                (candidate / "renders").mkdir(parents=True)
                write_bytes(candidate / "project.json", _json_bytes(metadata, 2))
                shutil.copytree(scenes_src, candidate / "scenes")
                (candidate / "assets").symlink_to(assets, target_is_directory=True)
                candidate.rename(part)
    return part
