#!/usr/bin/env python3
"""Plates that differ from a base still only inside one region: the replacement-mouth and blink method of 2D
animation, for a still a sung line or a blink steps through frame by frame (motion-kit/src/mouth.js picks the plate).

  python -I motion-kit/tools/region_plates.py --config COMP/mouth.json --root ROOT --out COMP/plates

Each variant is an image edit of the base (same framing and light, one region changed). It is aligned to the base with
ECC (affine, on the align box outside the region), shifted to the base's colour on the feather ring, and pasted into
the base through the region's feathered shape. Outside the feather every pixel is the base's; the run checks it and
stops otherwise. Writes <base><region key><letter>.png into --out and <base>-regions.json beside them (inputs with
SHA-256, transform, ECC score, colour offset, changed box). Config paths are relative to --root. Needs OpenCV and
NumPy (the video-analysis venv).

Config: {"base": "K7", "base_path": "...", "regions": {"m": {"polygons": [[[x, y], ...]], "ellipses": [[cx, cy, ax, ay,
angle]], "feather_px": 10, "align_box": [x0, y0, x1, y1], "variants": {"B": "path", ...}}, ...}}
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

ECC_CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
MIN_ECC = 0.95          # below this the variant is not the same picture with one region changed
RING = (0.05, 0.6)      # feather band where the colour offset is measured


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def region_alpha(shape: tuple[int, int], region: dict) -> tuple[np.ndarray, np.ndarray]:
    """Hard mask (uint8) and feathered alpha (float32, exactly 0 where the feather has no effect)."""
    hard = np.zeros(shape, np.uint8)
    for poly in region.get("polygons", []):
        cv2.fillPoly(hard, [np.array(poly, np.int32)], 255)
    for cx, cy, ax, ay, angle in region.get("ellipses", []):
        cv2.ellipse(hard, (int(cx), int(cy)), (int(ax), int(ay)), angle, 0, 360, 255, -1)
    alpha = cv2.GaussianBlur(hard.astype(np.float32) / 255, (0, 0), region["feather_px"])
    alpha[alpha < 1 / 512] = 0
    return hard, alpha


def align(base: np.ndarray, variant: np.ndarray, hard: np.ndarray, region: dict) -> tuple[np.ndarray, np.ndarray, float]:
    """Warp the variant onto the base, matched on the align box with the changed region left out."""
    x0, y0, x1, y1 = region["align_box"]
    keep = np.zeros(hard.shape, np.uint8)
    keep[y0:y1, x0:x1] = 255
    grow = int(3 * region["feather_px"]) | 1
    keep[cv2.dilate(hard, np.ones((grow, grow), np.uint8)) > 0] = 0
    def gray(im: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)

    warp = np.eye(2, 3, dtype=np.float32)
    score, warp = cv2.findTransformECC(gray(base), gray(variant), warp, cv2.MOTION_AFFINE, ECC_CRITERIA, keep, 5)
    aligned = cv2.warpAffine(variant, warp, (base.shape[1], base.shape[0]),
                             flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    return aligned, warp, float(score)


def paste(base: np.ndarray, aligned: np.ndarray, alpha: np.ndarray) -> tuple[np.ndarray, list[float]]:
    ring = (alpha > RING[0]) & (alpha < RING[1])
    offset = [float(base[..., c][ring].mean() - aligned[..., c][ring].mean()) for c in range(3)]
    shifted = aligned.astype(np.float32) + np.array(offset, np.float32)
    a = alpha[..., None]
    out = base.astype(np.float32) * (1 - a) + shifted * a
    out = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    out[alpha == 0] = base[alpha == 0]
    return out, offset


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--root", type=Path, required=True, help="the directory config paths are relative to")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text())
    base_path = args.root / cfg["base_path"]
    base = cv2.imread(str(base_path), cv2.IMREAD_COLOR)
    if base is None:
        raise SystemExit(f"cannot read {base_path}")
    args.out.mkdir(parents=True, exist_ok=True)
    report = {"base": cfg["base"], "base_path": cfg["base_path"], "base_sha256": sha256(base_path), "plates": {}}
    for key, region in cfg["regions"].items():
        hard, alpha = region_alpha(base.shape[:2], region)
        ys, xs = np.nonzero(alpha)
        for letter, rel in region["variants"].items():
            src = args.root / rel
            variant = cv2.imread(str(src), cv2.IMREAD_COLOR)
            if variant is None or variant.shape != base.shape:
                raise SystemExit(f"{rel}: missing or not the base's size")
            aligned, warp, score = align(base, variant, hard, region)
            if score < MIN_ECC:
                raise SystemExit(f"{rel}: ECC {score:.3f} < {MIN_ECC}, not the base picture with one region changed")
            out, offset = paste(base, aligned, alpha)
            outside = alpha == 0
            if not np.array_equal(out[outside], base[outside]):
                raise SystemExit(f"{rel}: pixels outside the region changed")
            name = f"{cfg['base']}{key}{letter}"
            dest = args.out / f"{name}.png"
            cv2.imwrite(str(dest), out)
            report["plates"][name] = {
                "variant": rel, "variant_sha256": sha256(src), "plate_sha256": sha256(dest), "ecc": round(score, 4),
                "warp": np.round(warp, 5).tolist(), "colour_offset_bgr": [round(o, 2) for o in offset],
                "changed_box": [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1],
                "outside_region_identical": True}
            print(name, f"ecc {score:.4f}", "offset", [round(o, 1) for o in offset])
    (args.out / f"{cfg['base']}-regions.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
