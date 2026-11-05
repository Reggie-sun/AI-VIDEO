#!/usr/bin/env python3
"""Stage 13: match our shots to the author's published Midjourney images (visual retrieval, DINOv2).

Inputs : work/author_images/img/*.webp (author gallery, kind plate/character/set/reference), source_docs/api_films_escape-velocity.json
         work/shots.json, work/f960/*.jpg
Output : work/plate_matches.json  {shot_id: [{item_id, kind, job, score, frame_used, is_plate_flag}] top 5}
Method : DINOv2 ViT-B/14 CLS embedding (224x224). Plates are embedded whole + 5 crops (centre 70%, four corner 60% windows) because the film
         crops/zooms plates; each shot is embedded at 5 frames (not the HUD-heavy bottom band is NOT masked: DINO is tolerant, and the halftone is
         removed by the 224 downsample). Score = max cosine over (shot frames x plate views).
Evidence level of any mapping derived from this: `inferred` (visual retrieval). A human/agent must verify before use.
Run: python -I scripts/13_match_plates.py <analysis_root>
"""
import json
import sys
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image

dev = "cuda" if torch.cuda.is_available() else "cpu"


def model():
    m = timm.create_model("vit_base_patch14_dinov2.lvd142m", pretrained=True, num_classes=0).eval().to(dev)
    cfg = timm.data.resolve_data_config({}, model=m)
    return m, timm.data.create_transform(**cfg)


@torch.no_grad()
def embed(m, tf, imgs):
    out = []
    for i in range(0, len(imgs), 64):
        x = torch.stack([tf(im.convert("RGB")) for im in imgs[i : i + 64]]).to(dev)
        f = m(x)
        out.append(torch.nn.functional.normalize(f, dim=-1).cpu())
    return torch.cat(out).numpy()


def views(im):
    w, h = im.size
    v = [im]
    cw, ch = int(w * 0.7), int(h * 0.7)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    v.append(im.crop((x0, y0, x0 + cw, y0 + ch)))
    cw, ch = int(w * 0.6), int(h * 0.6)
    for (x0, y0) in [(0, 0), (w - cw, 0), (0, h - ch), (w - cw, h - ch)]:
        v.append(im.crop((x0, y0, x0 + cw, y0 + ch)))
    return v


def main(root):
    root = Path(root)
    api = json.loads((root / "source_docs" / "api_films_escape-velocity.json").read_text())
    items = {i["id"]: i for i in api["items"]}
    files = sorted((root / "work" / "author_images" / "img").glob("*.webp"))
    m, tf = model()
    pv, pmeta = [], []
    for f in files:
        iid = f.stem
        if iid not in items:
            continue
        try:
            im = Image.open(f)
            im.load()
        except Exception:  # noqa: BLE001
            continue
        for v in views(im):
            pv.append(v)
            pmeta.append(iid)
    P = embed(m, tf, pv)
    print("plate views", len(pv))
    shots = json.loads((root / "work" / "shots.json").read_text())
    res = {}
    for s in shots:
        a, b = s["start_frame"], s["end_frame"]
        fr = sorted(set(np.linspace(a, b, 5).round().astype(int).tolist()))
        ims = [Image.open(root / "work" / "f960" / f"{i:05d}.jpg") for i in fr]
        F = embed(m, tf, ims)
        sim = F @ P.T  # frames x views
        best = {}
        for fi in range(sim.shape[0]):
            for j in np.argsort(-sim[fi])[:40]:
                iid = pmeta[j]
                sc = float(sim[fi, j])
                if iid not in best or sc > best[iid][0]:
                    best[iid] = (sc, fr[fi])
        top = sorted(best.items(), key=lambda kv: -kv[1][0])[:6]
        res[s["shot_id"]] = [
            {"item_id": k, "kind": items[k]["kind"], "job": items[k]["job"], "batch": items[k]["batch"], "score": round(v[0], 4), "frame_used": v[1], "is_plate_flag": bool(items[k].get("plate"))}
            for k, v in top
        ]
    (root / "work" / "plate_matches.json").write_text(json.dumps(res, indent=1))
    sc = [r[0]["score"] for r in res.values() if r]
    print("shots", len(res), "top-score percentiles", np.percentile(sc, [10, 50, 90]).round(3))


if __name__ == "__main__":
    main(sys.argv[1])
