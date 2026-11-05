#!/usr/bin/env python3
"""Validate one shot JSON: schema + cross-checks against work/shots.json and files on disk.

Run: python -I scripts/validate_shot.py <analysis_root> shots/shot_NNNN.json [more files...]
Exit code 1 if any ERROR. WARN lines do not fail but should be read.
"""
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

TIMING = ["shot_id", "start_frame", "end_frame", "start_time", "end_time", "duration_frames", "duration_s", "start_tc", "end_tc"]


def check(root, rel, shots_by_id, schema_validator, assets=None, strict_audio=None):
    errs, warns = [], []
    p = root / rel
    try:
        s = json.loads(p.read_text())
    except Exception as ex:  # noqa: BLE001
        return [f"cannot parse {rel}: {ex}"], []
    for e in sorted(schema_validator.iter_errors(s), key=lambda e: list(e.path)):
        errs.append(f"schema {'/'.join(str(x) for x in e.path)}: {e.message[:200]}")
    sid = s.get("shot_id")
    ref = shots_by_id.get(sid)
    if not ref:
        errs.append(f"unknown shot_id {sid}")
        return errs, warns
    for k in TIMING:
        if s.get(k) != ref.get(k):
            errs.append(f"timing mismatch {k}: json={s.get(k)} expected={ref.get(k)}")
    if p.stem != "shot_" + sid[1:]:
        errs.append(f"filename {p.name} does not match {sid}")
    a, b = ref["start_frame"], ref["end_frame"]
    ids = set()
    for e in s.get("elements", []):
        eid = e.get("element_id", "?")
        if eid in ids:
            errs.append(f"duplicate element_id {eid}")
        ids.add(eid)
        if not eid.startswith(sid + "-E"):
            errs.append(f"{eid} does not belong to {sid}")
        if e.get("shot_id") != sid:
            errs.append(f"{eid} shot_id {e.get('shot_id')}")
        if not (a <= e.get("start_frame", -1) <= e.get("end_frame", -1) <= b):
            errs.append(f"{eid} frames {e.get('start_frame')}-{e.get('end_frame')} outside shot {a}-{b}")
        bb = e.get("bounding_box")
        if bb:
            if not (-0.15 <= bb["x"] <= 1.15 and -0.15 <= bb["y"] <= 1.15 and 0 <= bb["w"] <= 1.6 and 0 <= bb["h"] <= 1.6):
                warns.append(f"{eid} bbox looks off-frame {bb}")
        for kf in e.get("keyframes", []):
            if not (a <= kf["frame"] <= b):
                errs.append(f"{eid} keyframe {kf['frame']} outside shot")
        for rf in e.get("reference_frames", []):
            if not (a <= rf <= b):
                errs.append(f"{eid} reference frame {rf} outside shot")
        aid = e.get("asset_id")
        if aid and not re.match(r"^(G|N)-[A-Za-z0-9_.-]+$", aid):
            errs.append(f"{eid} asset_id {aid} must look like G-... or N-...")
        if aid and aid.startswith("G-") and assets is not None and aid not in assets:
            errs.append(f"{eid} asset_id {aid} not in visual_system.json global_layers/assets")
        if e.get("type", "").startswith("text_") and not e.get("text"):
            warns.append(f"{eid} text element without text block")
    for rf in s.get("reference_frames", []):
        if not (root / rf["path"]).exists():
            errs.append(f"reference frame file missing {rf['path']}")
        if not (a <= rf["frame"] <= b):
            errs.append(f"reference frame {rf['frame']} outside shot")
    roles = {r["role"] for r in s.get("reference_frames", [])}
    for need in ("first", "middle", "last"):
        if need not in roles:
            errs.append(f"reference_frames missing role {need}")
    for an in s.get("animations", []):
        for t in an["target_element_ids"]:
            if t not in ids:
                errs.append(f"animation {an['anim_id']} targets unknown element {t}")
        if not (a <= an["start_frame"] <= an["end_frame"] <= b):
            errs.append(f"animation {an['anim_id']} frames outside shot")
    for ev in s.get("in_shot_events", []):
        if not (a <= ev["frame_range"][0] <= ev["frame_range"][1] <= b):
            errs.append(f"in_shot_event {ev['type']} outside shot")
    if strict_audio is not None:
        for ae in s.get("audio_events", []):
            if ae["audio_event_id"] not in strict_audio:
                errs.append(f"audio_event_id {ae['audio_event_id']} not in audio_timeline.json")
    if ref["duration_frames"] >= 12 and len(s.get("elements", [])) < 3:
        warns.append(f"only {len(s.get('elements', []))} elements for a {ref['duration_frames']}-frame shot")
    if s.get("scene_type") == "strobe_burst" and not s.get("strobe_constituents"):
        errs.append("strobe_burst needs strobe_constituents")
    return errs, warns


def load_context(root):
    shots = json.loads((root / "work" / "shots.json").read_text())
    by_id = {x["shot_id"]: x for x in shots}
    schema = json.loads((root / "schema" / "shot.schema.json").read_text())
    v = Draft202012Validator(schema)
    assets = None
    vs = root / "visual_system.json"
    if vs.exists():
        d = json.loads(vs.read_text())
        assets = {x["asset_id"] for x in d.get("global_layers", [])} | {x["asset_id"] for x in d.get("assets", [])}
    return shots, by_id, v, assets


def main(root, *files):
    root = Path(root)
    _, by_id, v, assets = load_context(root)
    bad = 0
    for f in files:
        errs, warns = check(root, f, by_id, v, assets)
        for e in errs:
            print(f"ERROR {f}: {e}")
        for w in warns:
            print(f"WARN  {f}: {w}")
        print(f"{f}: {len(errs)} errors, {len(warns)} warnings")
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
