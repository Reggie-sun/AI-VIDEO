#!/usr/bin/env python3
"""Stage 10: aggregate shot records into timeline.json + elements.json and link audio events.

Inputs : shots/shot_*.json (source of truth), work/shots.json, work/boundaries_all.json, audio_timeline.json (optional)
Outputs: timeline.json, elements.json, (re)writes `audio_events` inside shot json when --link-audio is given
         (audio events whose frame span overlaps the shot; relation text is generated, existing manual links are kept).
Run: python -I scripts/10_aggregate.py <analysis_root> [--link-audio]
"""
import json
import sys
from pathlib import Path

FPS = 24


def main(root, link_audio=False):
    root = Path(root)
    ws = {s["shot_id"]: s for s in json.loads((root / "work" / "shots.json").read_text())}
    bnd = json.loads((root / "work" / "boundaries_all.json").read_text())
    audio = None
    if (root / "audio_timeline.json").exists():
        audio = json.loads((root / "audio_timeline.json").read_text())
    shots, elements, evs = [], [], []
    for sid in sorted(ws):
        f = root / "shots" / f"shot_{sid[1:]}.json"
        if not f.exists():
            shots.append({"shot_id": sid, "status": "MISSING_RECORD", "start_frame": ws[sid]["start_frame"], "end_frame": ws[sid]["end_frame"]})
            continue
        s = json.loads(f.read_text())
        if link_audio and audio:
            have = {a["audio_event_id"] for a in s["audio_events"]}
            for ae in audio.get("events", []):
                a0, a1 = ae.get("start_frame"), ae.get("end_frame", ae.get("start_frame"))
                if a0 is None:
                    continue
                if a0 <= s["end_frame"] and a1 >= s["start_frame"] and ae["event_id"] not in have:
                    rel = f"{ae['type']} ({ae.get('origin','unknown')}) at frame {a0}" + (f"–{a1}" if a1 != a0 else "") + f"; {ae.get('evidence','')}"[:160]
                    s["audio_events"].append({"audio_event_id": ae["event_id"], "relation": rel, "frame": max(a0, s["start_frame"])})
            f.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
        shots.append(
            {
                "shot_id": sid, "file": f"shots/shot_{sid[1:]}.json", "md": f"shots/shot_{sid[1:]}.md",
                "start_frame": s["start_frame"], "end_frame": s["end_frame"], "start_time": s["start_time"], "end_time": s["end_time"],
                "duration_frames": s["duration_frames"], "start_tc": s["start_tc"], "end_tc": s["end_tc"],
                "scene_type": s["scene_type"], "visual_complexity": s["visual_complexity"]["level"],
                "transition_in": s["transitions"]["in"]["type"], "transition_out": s["transitions"]["out"]["type"],
                "n_elements": len(s["elements"]), "n_audio_events": len(s["audio_events"]), "confidence": s["confidence"],
                "contactsheet": f"contactsheets/{sid}.jpg",
            }
        )
        for e in s["elements"]:
            elements.append(e)
        for ev in s.get("in_shot_events", []):
            evs.append({"shot_id": sid, **ev})
    tl = {
        "schema": "ev-timeline/v1", "fps": FPS, "total_frames": 7353, "duration_s": 306.375,
        "convention": "frames are 0-based; end_frame inclusive; shots tile 0..7352 with no gaps",
        "shots": shots, "boundaries": bnd, "in_shot_events": evs,
        "audio_sections": (audio or {}).get("sections", []),
    }
    (root / "timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False))
    (root / "elements.json").write_text(json.dumps({"schema": "ev-elements/v1", "count": len(elements), "elements": elements}, indent=1, ensure_ascii=False))
    print("shots", len(shots), "elements", len(elements), "missing", sum(1 for s in shots if s.get("status")))


if __name__ == "__main__":
    main(sys.argv[1], "--link-audio" in sys.argv)
