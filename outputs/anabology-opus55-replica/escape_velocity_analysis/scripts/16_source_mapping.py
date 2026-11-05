#!/usr/bin/env python3
"""Index immutable author snapshots and time-window hints without inventing a shot mapping."""
import hashlib
import json
import re
import sys
from pathlib import Path


def main(root):
    root = Path(root)
    index = (root / "source_docs/INDEX.md").read_text()
    snapshots = []
    for line in index.splitlines():
        fields = [s.strip() for s in line.strip("|").split("|")]
        if len(fields) != 5 or not fields[1].startswith("https://"):
            continue
        name, url, size, digest, fetched = fields
        path = root / "source_docs" / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        snapshots.append(dict(path=f"source_docs/{name}", url=url, fetched_utc=fetched,
                              expected_sha256=digest, actual_sha256=actual,
                              integrity="PASS" if actual == digest and path.stat().st_size == int(size) else "FAIL"))
    hints = json.loads((root / "work/author_clip_hints.json").read_text())
    shots = json.loads((root / "work/shots.json").read_text())
    mappings = []
    for s in shots:
        mappings.append(dict(shot_id=s["shot_id"], start_frame=s["start_frame"], end_frame=s["end_frame"],
                             evidence_level="inferred" if hints[s["shot_id"]] else "unknown",
                             method="overlap with author's published Seedance song-time windows; not image identity matching",
                             candidates=hints[s["shot_id"]],
                             source_path="source_docs/prompts-seedance.md",
                             source_url="https://claudia.gallery/record/escape-velocity/prompts-seedance.md",
                             confidence=0.5 if hints[s["shot_id"]] else 0.0,
                             uncertainties=["Author storyboard sNNN identifiers and observed SNNNN identifiers belong to different segmentations",
                                            "A time-window overlap does not prove this exact source clip appears in this observed shot",
                                            "No visual plate identity or prompt-to-final-shot match is asserted"]))
    api = json.loads((root / "source_docs/api_films_escape-velocity.json").read_text())
    assets = [dict(asset_id="AUTHOR-"+item["id"], item_id=item["id"],
                   source_path="source_docs/api_films_escape-velocity.json",
                   json_pointer=f"/items/{i}", source_url=item.get("page"),
                   image_url=item.get("url"), kind=item.get("kind"),
                   prompt_evidence_level="confirmed", final_shot_mapping="unknown")
              for i, item in enumerate(api["items"])]
    confirmed = [
        ("base_images", "Midjourney v8.2 with --raw --hd and personal profile"),
        ("song", "Suno v6; published lyrics, style and exclude fields"),
        ("moving_footage", "Seedance 2.5; source plates and exact song slices"),
        ("graphics", "custom JavaScript engine in headless Chromium, Canvas plus WebGL print pass"),
        ("local_analysis", "htdemucs stems, beat map, wav2vec2 word alignment and depth/tracking tools"),
    ]
    out = dict(schema="ev-source-mapping/v1", sources=snapshots, shot_mappings=mappings,
               author_asset_index=assets,
               confirmed_film_level=[dict(layer=k, statement=v, evidence_level="confirmed",
                                         source_path="source_docs/readme.md", heading="The stack",
                                         url="https://claudia.gallery/record/escape-velocity/readme.md") for k,v in confirmed],
               local_reconstruction_recommendations=[
                   dict(layer="graphics_and_compositing", technique="existing HyperFrames / motion-kit Canvas/WebGL",
                        evidence_level="inferred", note="Recommendation for future work only; no reconstruction performed"),
                   dict(layer="typography", technique="measure cap height, glyph widths and word-time steps; candidate fonts only",
                        evidence_level="inferred", note="Author wiki font names are not proof of this film's exact font files"),
               ],
               uncertainties=["Published author board has 141 shots; observed cut segmentation has 153. IDs must not be equated",
                              "Author reports 7354 rendered frames; this downloaded file decodes to 7353. Original master not available here",
                              "Published pages are dated snapshots, not proof of current provider features or runtime availability",
                              "Clip-window mappings and plate suggestions require visual identity verification before future reconstruction"])
    (root / "source_mapping.json").write_text(json.dumps(out, ensure_ascii=False, indent=1)+"\n")
    print(f"author snapshots={len(snapshots)}, failed integrity={sum(x['integrity']!='PASS' for x in snapshots)}, shots={len(mappings)}, public assets={len(assets)}")


if __name__ == "__main__":
    main(sys.argv[1])
