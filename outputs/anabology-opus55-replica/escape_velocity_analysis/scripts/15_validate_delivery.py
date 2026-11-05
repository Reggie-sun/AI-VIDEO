#!/usr/bin/env python3
"""Strict delivery checks, separate data integrity from perceptual completion.

Exit 1: broken package. Exit 2: structurally valid, analysis unfinished.
Exit 0: structural checks and recorded review coverage complete (not human acceptance).
"""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path


REQUIRED_JSON = ("manifest.json", "timeline.json", "audio_timeline.json", "visual_system.json",
                 "elements.json", "source_mapping.json", "synchronization.json")
REQUIRED_DOCS = ("README.md", "reconstruction_plan.md", "analysis_report.md")


def assess(root, integrity_errors=()):
    root = Path(root)
    errors, unfinished = list(integrity_errors), []
    data = {}
    for name in REQUIRED_JSON:
        try:
            data[name] = json.loads((root / name).read_text())
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
    for name in REQUIRED_DOCS:
        if not (root / name).is_file():
            errors.append(f"required document absent: {name}")
    if errors:
        return dict(errors=errors, unfinished=unfinished, status="INVALID_PACKAGE")
    manifest = data["manifest.json"]
    expected = json.loads((root / "work/shots.json").read_text())
    nf = manifest["source_video"]["video"]["nb_frames_decoded"]
    fps = manifest["source_video"]["video"]["fps"]
    records, unique, cursor = {}, set(), 0
    for s in expected:
        if s["start_frame"] != cursor:
            errors.append(f"noncontiguous shot: {s['shot_id']}")
        cursor = s["end_frame"] + 1
        path = root / f"shots/shot_{s['shot_id'][1:]}.json"
        if not path.exists():
            errors.append(f"missing shot record: {s['shot_id']}")
            continue
        record = json.loads(path.read_text())
        records[s["shot_id"]] = record
        if record.get("analysis_status") != "DETAILED_VISUAL_REVIEW":
            unfinished.append(f"{s['shot_id']}: detailed review not certified; see shot uncertainties")
        for e in record["elements"]:
            if e["element_id"] in unique:
                errors.append(f"duplicate element: {e['element_id']}")
            unique.add(e["element_id"])
        for key in ("start_frame", "end_frame", "duration_frames"):
            if record[key] != s[key]:
                errors.append(f"{s['shot_id']}: {key} differs from boundary source")
    if cursor != nf:
        errors.append(f"video frame coverage {cursor} != decoded {nf}")
    aggregate = data["elements.json"]["elements"]
    if {e["element_id"] for e in aggregate} != unique or len(aggregate) != len(unique):
        errors.append("aggregate elements differ from shot records")
    canonical_elements = {e["element_id"]: e for s in records.values() for e in s["elements"]}
    for element in aggregate:
        if element != canonical_elements.get(element["element_id"]):
            errors.append(f"aggregate element payload differs: {element['element_id']}")
    tids = {s["shot_id"] for s in data["timeline.json"]["shots"]}
    if tids != {s["shot_id"] for s in expected}:
        errors.append("aggregate shot IDs differ from boundary source")
    entries = data["timeline.json"]["shots"]
    if len(entries) != len(tids):
        errors.append("duplicate timeline shot IDs")
    for entry in entries:
        record = records.get(entry["shot_id"])
        if record is None:
            continue
        projected = {k: record[k] for k in ("shot_id", "start_frame", "end_frame", "start_time", "end_time",
                     "duration_frames", "start_tc", "end_tc", "scene_type", "confidence")}
        projected.update(file=f"shots/shot_{record['shot_id'][1:]}.json", md=f"shots/shot_{record['shot_id'][1:]}.md",
                         contactsheet=f"contactsheets/{record['shot_id']}.jpg", n_elements=len(record["elements"]),
                         n_audio_events=len(record["audio_events"]), visual_complexity=record["visual_complexity"]["level"],
                         transition_in=record["transitions"]["in"]["type"], transition_out=record["transitions"]["out"]["type"])
        if entry != projected:
            errors.append(f"timeline metadata differs from shot record: {record['shot_id']}")
    events = [{"shot_id": s["shot_id"], **event} for s in records.values() for event in s.get("in_shot_events", [])]
    if data["timeline.json"].get("in_shot_events") != events:
        errors.append("timeline in-shot events differ from shot records")
    audio = data["audio_timeline.json"]
    if data["timeline.json"].get("audio_sections") != audio["sections"]:
        errors.append("timeline audio sections differ from audio timeline")
    ids = set()
    for e in audio["events"]:
        if e["event_id"] in ids:
            errors.append(f"duplicate audio event: {e['event_id']}")
        ids.add(e["event_id"])
        if not 0 <= e["start_s"] <= e["end_s"] <= audio["duration_s"]:
            errors.append(f"invalid audio time range: {e['event_id']}")
        if not 0 <= e["start_frame"] <= e["end_frame"] < nf:
            errors.append(f"invalid audio visual frame reference: {e['event_id']}")
        if not set(e["shot_ids"]).issubset(tids):
            errors.append(f"dangling audio shot reference: {e['event_id']}")
    sections = audio["sections"]
    end = 0
    for section in sections:
        if not math.isclose(section["start_s"], end, abs_tol=1e-6):
            errors.append("gap/overlap in audio sections")
        end = section["end_s"]
    if not math.isclose(end, audio["duration_s"], abs_tol=1e-6):
        errors.append("audio sections do not cover full audio duration")
    for s in records.values():
        for e in s["audio_events"]:
            if e["audio_event_id"] not in ids:
                errors.append(f"{s['shot_id']}: dangling audio event {e['audio_event_id']}")
    visual_ids = set()
    for e in data["synchronization.json"]["events"]:
        if e["visual_event_id"] in visual_ids:
            errors.append(f"duplicate visual event: {e['visual_event_id']}")
        visual_ids.add(e["visual_event_id"])
        if e["nearest_beat"]["audio_event_id"] not in ids:
            errors.append(f"dangling nearest beat: {e['visual_event_id']}")
        if not set(e["overlapping_word_candidates"]).issubset(ids):
            errors.append(f"dangling word candidate: {e['visual_event_id']}")
    for e in audio["events"]:
        if not set(e.get("visual_event_ids", [])).issubset(visual_ids):
            errors.append(f"dangling visual backlink: {e['event_id']}")
    if audio["coverage"]["perceptual_listening"] != "COMPLETE":
        unfinished.append("audio perceptual listening/SFX identity not evaluated")
    for src in data["source_mapping.json"]["sources"]:
        p = root / src["path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != src["expected_sha256"]:
            errors.append(f"author source identity mismatch: {src['path']}")
    state = "INVALID_PACKAGE" if errors else "ANALYSIS_INCOMPLETE" if unfinished else "REVIEW_COVERAGE_COMPLETE"
    return dict(status=state, errors=errors, unfinished=unfinished,
                shots_expected=len(expected), shots_present=len(records), elements=len(unique),
                audio_events=len(ids), fps=fps, decoded_frames=nf,
                scope="Analysis artifact integrity and recorded coverage only; not reconstruction qualification or human acceptance")


if __name__ == "__main__":
    r = Path(sys.argv[1])
    baseline = subprocess.run([sys.executable, "-I", str(r/"scripts/validate_all.py"), str(r)],
                              capture_output=True, text=True)
    integrity = []
    if baseline.returncode:
        integrity.append("validate_all.py failed: " + (baseline.stdout+baseline.stderr)[-1200:])
    report = assess(r, integrity)
    (r / "qa/delivery_validation.json").write_text(json.dumps(report, indent=1, ensure_ascii=False)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("errors", "unfinished")}, ensure_ascii=False))
    for e in report["errors"][:20]:
        print("ERROR", e)
    print("unfinished checks", len(report["unfinished"]))
    sys.exit(1 if report["errors"] else 2 if report["unfinished"] else 0)
