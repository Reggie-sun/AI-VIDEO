#!/usr/bin/env python3
"""Stage 8: generate shots/shot_NNNN.md from shots/shot_NNNN.json (JSON is the only source of truth).

Each md starts with a marker line `<!-- generated-from: shot_NNNN.json sha256:<12 hex> -->` that
validate_all.py re-checks, so md can never silently drift from json.

Run: python -I scripts/08_gen_shot_md.py <analysis_root>
"""
import hashlib
import json
import sys
from pathlib import Path


def bb(b):
    if not b:
        return "n/a"
    return f"x={b['x']:.3f} y={b['y']:.3f} w={b['w']:.3f} h={b['h']:.3f}"


def kv(d, indent=""):
    out = []
    for k, v in d.items():
        if isinstance(v, (dict, list)):
            out.append(f"{indent}- **{k}**: `{json.dumps(v, ensure_ascii=False)}`")
        else:
            out.append(f"{indent}- **{k}**: {v}")
    return "\n".join(out)


def render(s, digest, name):
    L = [f"<!-- generated-from: {name} sha256:{digest} -->"]
    L.append(f"# {s['shot_id']}  ·  frames {s['start_frame']}–{s['end_frame']}  ·  {s['start_tc']} → {s['end_tc']}  ·  {s['duration_s']}s ({s['duration_frames']}f)")
    L.append(f"\n**Type**: {s['scene_type']} · **Complexity**: {s['visual_complexity']['level']} — {s['visual_complexity']['rationale']}  \n**Confidence**: {s['confidence']}")
    L.append(f"\n**Narrative role**: {s['narrative_role']}  \n**Subject**: {s['subject']}")
    L.append("\n## Scene\n" + s["scene_description"])
    L.append("\n## Reference frames")
    for r in s["reference_frames"]:
        L.append(f"- `{r['path']}` — frame {r['frame']} ({r['role']}){' — ' + r['note'] if r.get('note') else ''}")
    L.append("\n## Composition\n" + kv(s["composition"]))
    L.append("\n## Camera\n" + kv(s["camera"]))
    L.append("\n## Lighting\n" + kv(s["lighting"]))
    L.append("\n## Colors")
    for p in s["colors"]["palette"]:
        L.append(f"- {p['hex']} — {p['role']}" + (f" ({p['fraction']})" if p.get("fraction") is not None else "") + f" [{p.get('method','')}]")
    L.append(f"- contrast: {s['colors']['contrast']}\n- grain/halftone: {s['colors']['grain_halftone']}\n- temporal change: {s['colors']['temporal_change']}")
    L.append("\n## Persistent layer state\n" + (kv(s["persistent_layer_state"]) or "(none)"))
    L.append(f"\n## Elements ({len(s['elements'])})")
    for e in s["elements"]:
        L.append(f"\n### {e['element_id']} · {e['type']}" + (f" · asset {e['asset_id']}" if e.get("asset_id") else "") + f" · z={e['z_index']} · frames {e['start_frame']}–{e['end_frame']} · conf {e['confidence']}")
        L.append(e["description"])
        L.append(f"- bbox: {bb(e['bounding_box'])}")
        if e.get("text"):
            L.append(f"- text: `{json.dumps(e['text'], ensure_ascii=False)}`")
        L.append(f"- appearance: `{json.dumps(e['appearance'], ensure_ascii=False)}`")
        L.append(f"- motion: `{json.dumps(e['motion'], ensure_ascii=False)}`")
        if e["keyframes"]:
            L.append(f"- keyframes: `{json.dumps(e['keyframes'], ensure_ascii=False)}`")
        if e["effects"]:
            L.append(f"- effects: {'; '.join(e['effects'])}")
        L.append(f"- ref frames: {e['reference_frames']}")
        if e["uncertainties"]:
            L.append(f"- uncertainties: {'; '.join(e['uncertainties'])}")
        if e.get("reconstruction_hint"):
            L.append(f"- reconstruct: {e['reconstruction_hint']}")
    L.append("\n## Animations")
    for a in s["animations"]:
        L.append(f"- {a['anim_id']} → {a['target_element_ids']} f{a['start_frame']}–{a['end_frame']}: {a['description']}" + (f" (easing {a['easing']})" if a.get("easing") else "") + (f" [audio: {a['audio_sync']}]" if a.get("audio_sync") else ""))
    if s.get("in_shot_events"):
        L.append("\n## In-shot events")
        for e in s["in_shot_events"]:
            L.append(f"- {e['type']} f{e['frame_range'][0]}–{e['frame_range'][1]}: {e['description']}")
    L.append("\n## Transitions")
    for k in ("in", "out"):
        t = s["transitions"][k]
        L.append(f"- **{k}**: {t['type']}" + (f" span {t['span']}" if t.get("span") else "") + f" — {t['description']}" + (f" | driver: {t['driver']}" if t.get("driver") else "") + (f" | technique: {t['recommended_technique']}" if t.get("recommended_technique") else ""))
    L.append("\n## Audio events")
    for a in s["audio_events"]:
        L.append(f"- {a['audio_event_id']} — {a['relation']}" + (f" (frame {a['frame']})" if a.get("frame") is not None else ""))
    L.append("\n## Production hypothesis")
    for h in s["production_hypothesis"]["layers"]:
        L.append(f"- **{h['layer']}** — {h['technique']} · **{h['evidence_level']}** — {h['rationale']}" + (f" (refs: {', '.join(h['source_refs'])})" if h.get("source_refs") else ""))
    L.append("\n## Source references")
    for r in s["source_references"]:
        L.append(f"- [{r['kind']}] {r['ref']}" + (f" — {r['note']}" if r.get("note") else ""))
    L.append("\n## Uncertainties")
    L += [f"- {u}" for u in s["uncertainties"]] or ["- none recorded"]
    rn = s["reconstruction_notes"]
    L.append(f"\n## Reconstruction\n- **Method**: {rn['recommended_method']}\n- **Dependencies**: {', '.join(rn['dependencies'])}\n- **Difficulty**: {rn['difficulty']}/5 — {rn['difficulty_notes']}\n- **Alternatives**: {rn['alternatives']}")
    return "\n".join(L) + "\n"


def main(root):
    root = Path(root)
    n = 0
    for jf in sorted((root / "shots").glob("shot_*.json")):
        raw = jf.read_bytes()
        s = json.loads(raw)
        digest = hashlib.sha256(raw).hexdigest()[:12]
        (root / "shots" / (jf.stem + ".md")).write_text(render(s, digest, jf.name))
        n += 1
    print("md generated", n)


if __name__ == "__main__":
    main(sys.argv[1])
