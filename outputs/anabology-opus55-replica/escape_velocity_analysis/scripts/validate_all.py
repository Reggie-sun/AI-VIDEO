#!/usr/bin/env python3
"""Whole-package integrity check. Exit 1 on any ERROR; writes qa/validation_report.json.

Checks: every top-level JSON parses; shots tile 0..7352 with no gap/overlap; every shot has a record that passes
validate_shot (schema + cross-checks); element ids globally unique; G-* asset ids registered; md files exist and match
the json sha256 marker; timeline.json / elements.json agree with shot records; manifest/source_mapping file references
exist; audio_timeline validator passes if present.

Run: python -I scripts/validate_all.py <analysis_root> [--allow-missing]
  --allow-missing: do not fail on shots that have no record yet (progress check)
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_shot import check, load_context  # noqa: E402


def main(root, allow_missing=False):
    root = Path(root)
    errors, warns = [], []
    top = {}
    for f in sorted(root.glob("*.json")) + sorted((root / "shots").glob("*.json")):
        try:
            top[f.name] = json.loads(f.read_text())
        except Exception as ex:  # noqa: BLE001
            errors.append(f"unparseable {f.relative_to(root)}: {ex}")
    shots, by_id, v, assets = load_context(root)
    # tiling
    exp = 0
    for s in shots:
        if s["start_frame"] != exp:
            errors.append(f"tiling gap/overlap at {s['shot_id']}: expected start {exp}, got {s['start_frame']}")
        exp = s["end_frame"] + 1
    if exp != 7353:
        errors.append(f"shots end at {exp - 1}, expected 7352")
    audio_ids = None
    if "audio_timeline.json" in top:
        audio_ids = {e["event_id"] for e in top["audio_timeline.json"].get("events", [])}
    all_el, missing, n_ok = {}, [], 0
    for s in shots:
        rel = f"shots/shot_{s['shot_id'][1:]}.json"
        if not (root / rel).exists():
            missing.append(s["shot_id"])
            continue
        e, w = check(root, rel, by_id, v, assets, audio_ids)
        errors += [f"{rel}: {x}" for x in e]
        warns += [f"{rel}: {x}" for x in w]
        n_ok += not e
        data = top.get(Path(rel).name, {})
        for el in data.get("elements", []):
            if el["element_id"] in all_el:
                errors.append(f"duplicate element id across shots: {el['element_id']}")
            all_el[el["element_id"]] = el
        md = root / rel.replace(".json", ".md")
        if not md.exists():
            errors.append(f"missing md for {s['shot_id']}")
        else:
            head = md.read_text().split("\n", 1)[0]
            m = re.search(r"sha256:([0-9a-f]{12})", head)
            digest = hashlib.sha256((root / rel).read_bytes()).hexdigest()[:12]
            if not m or m.group(1) != digest:
                errors.append(f"{md.name} is stale vs json (marker {m.group(1) if m else None} != {digest})")
    if missing:
        (warns if allow_missing else errors).append(f"{len(missing)} shots without record: {missing[:10]}{'...' if len(missing) > 10 else ''}")
    # aggregate consistency
    if "elements.json" in top and top["elements.json"].get("count") != len(all_el):
        errors.append(f"elements.json count {top['elements.json'].get('count')} != records {len(all_el)}")
    if "timeline.json" in top:
        tl = {x["shot_id"]: x for x in top["timeline.json"]["shots"]}
        for s in shots:
            t = tl.get(s["shot_id"])
            if not t:
                errors.append(f"timeline.json missing {s['shot_id']}")
            elif (t["start_frame"], t["end_frame"]) != (s["start_frame"], s["end_frame"]):
                errors.append(f"timeline.json frame range differs for {s['shot_id']}")
    # file references in manifest/source_mapping
    for name in ("manifest.json", "source_mapping.json"):
        d = top.get(name)
        if not d:
            warns.append(f"{name} not present")
            continue
        for ref in re.findall(r'"((?:source_docs|keyframes|contactsheets|audio|shots|qa)/[^"\s]+)"', json.dumps(d)):
            if not (root / ref).exists() and not ref.endswith("/"):
                errors.append(f"{name} references missing file {ref}")
    # audio validator
    av = root / "scripts" / "03_audio_validate.py"
    if av.exists() and "audio_timeline.json" in top:
        r = subprocess.run([sys.executable, "-I", str(av), str(root)], capture_output=True, text=True)
        if r.returncode:
            errors.append("audio validator failed: " + (r.stdout + r.stderr)[-400:])
    report = {"shots_expected": len(shots), "shots_with_valid_record": n_ok, "shots_missing": missing, "elements_total": len(all_el), "errors": errors, "warnings": warns}
    (root / "qa").mkdir(exist_ok=True)
    (root / "qa" / "validation_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    for e in errors[:60]:
        print("ERROR", e)
    print(f"shots {len(shots)}, valid records {n_ok}, missing {len(missing)}, elements {len(all_el)}, errors {len(errors)}, warnings {len(warns)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--allow-missing" in sys.argv))
