#!/usr/bin/env python3
"""Temporal correspondence, never a claim of causal or perceptually correct sync."""
import json
import sys
from pathlib import Path


def main(root):
    root = Path(root)
    audio = json.loads((root / "audio_timeline.json").read_text())
    beats = [e for e in audio["events"] if e["type"] == "beat_candidate"]
    words = [e for e in audio["events"] if "word_candidate" in e["type"]]
    boundaries = json.loads((root / "work/boundaries_all.json").read_text())
    events = []
    for b in boundaries:
        events.append(dict(visual_event_id="V-"+b["boundary_id"], type="shot_boundary",
                           frame=b["first_frame_of_new_shot"], source="work/boundaries_all.json",
                           description=b["type"]))
    for path in sorted((root / "shots").glob("shot_*.json")):
        s = json.loads(path.read_text())
        for i, e in enumerate(s.get("in_shot_events", [])):
            events.append(dict(visual_event_id=f"V-{s['shot_id']}-I{i+1:03d}", type=e["type"],
                               frame=e["frame_range"][0], source=str(path.relative_to(root)),
                               description=e["description"]))
        for e in s.get("elements", []):
            for i, k in enumerate(e["keyframes"]):
                events.append(dict(visual_event_id=f"V-{e['element_id']}-K{i+1:03d}",
                                   type="element_keyframe", frame=k["frame"],
                                   source=str(path.relative_to(root)), description=e["description"]))
    for e in events:
        t = e["frame"]/24
        b = min(beats, key=lambda x: abs(x["start_s"]-t))
        e["time_s"] = t
        e["nearest_beat"] = dict(audio_event_id=b["event_id"], delta_ms=round((t-b["start_s"])*1000, 2),
                                 kick_supported=b["kick_supported"])
        e["overlapping_word_candidates"] = [w["event_id"] for w in words if w["start_s"] <= t <= w["end_s"]]
        e["interpretation"] = "temporal correspondence only; causal beat locking and audible sync NOT_EVALUATED"
    by_audio = {e["event_id"]: e for e in audio["events"]}
    for e in by_audio.values():
        e["visual_event_ids"] = []
    for e in events:
        links = [e["nearest_beat"]["audio_event_id"], *e["overlapping_word_candidates"]]
        for aid in links:
            by_audio[aid]["visual_event_ids"].append(e["visual_event_id"])
    result = dict(schema="ev-synchronization/v1", events=events,
                  note="Stable visual event IDs allow comparison by a later agent; unverified keyframes inherit shot uncertainty")
    (root / "synchronization.json").write_text(json.dumps(result, ensure_ascii=False, indent=1)+"\n")
    (root / "audio_timeline.json").write_text(json.dumps(audio, ensure_ascii=False, indent=1)+"\n")
    print("visual/audio correspondence rows", len(events))


if __name__ == "__main__":
    main(sys.argv[1])
