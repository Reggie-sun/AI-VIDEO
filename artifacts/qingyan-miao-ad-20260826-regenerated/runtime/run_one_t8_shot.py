from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


REPO = Path("/home/reggie/vscode_folder/AI-VIDEO")
SOURCE_RUNNER = (
    REPO
    / "artifacts/qingyan-miao-ad-20260825/runtime/execute_t8_portrait_ad_batch.py"
)
OUTPUT_ROOT = (
    REPO
    / "artifacts/qingyan-miao-ad-20260826-regenerated/runtime/t8_portrait_ad"
)
SOURCE_ROOT = REPO / "artifacts/qingyan-miao-ad-20260825"


SHOTS = {
    "01_concern": {
        "id": "01_concern",
        "seed": 8262601,
        "source": SOURCE_ROOT / "assets/01-concern.png",
        "action": (
            "Starting exactly from Picture 1, she makes one restrained check of the blouse "
            "fabric beside her underarm, pauses for a moment, then lowers her hand naturally. "
            "Her mild concern relaxes into a neutral expression. Keep exactly two hands, one "
            "continuous arm path, stable facial identity and stable clothing. Subtle breathing "
            "and one blink only. Locked camera, no sweat close-up, no body morphing, no jump."
        ),
    },
    "02_product_lift": {
        "id": "02_product_lift",
        "seed": 8262602,
        "source": SOURCE_ROOT / "runtime/inputs/product-use-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she looks briefly at the yellow bottle already in "
            "her hands and raises it only a few centimeters to a comfortable chest-level product "
            "presentation, then looks back with a small confident smile. Both hands remain close "
            "to their starting positions; no hand or arm enters from any frame edge. The closed "
            "white cap, yellow label and cylindrical bottle silhouette remain stable. Locked "
            "camera, no opening, no spraying, no label morphing, no extra fingers."
        ),
    },
    "03_preuse_hint": {
        "id": "03_preuse_hint",
        "seed": 8262603,
        "source": SOURCE_ROOT / "runtime/inputs/product-use-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she keeps the capped yellow bottle centered in "
            "front of her waist and gently rotates it toward camera by a few degrees, then gives "
            "a calm ready-to-go smile. This is a clean pre-use implication only: no exposed skin, "
            "no visible mist and no cross-body reaching. Both forearms stay fully inside the frame "
            "and follow one short continuous motion. Keep exactly two hands, stable fingers, stable "
            "white cap, yellow label, bottle shape and facial identity. Locked camera, no extra arm."
        ),
    },
    "04_walk_forward": {
        "id": "04_walk_forward",
        "seed": 8262604,
        "source": SOURCE_ROOT / "runtime/inputs/walk-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she completes one calm natural step forward along "
            "the stone lane while remaining centered. Both shoes stay visible through heel contact, "
            "weight transfer and toe-off. Her arms, skirt hem, loose hair and earrings move gently "
            "with continuous restrained motion. Locked tripod camera and stable background, no pan, "
            "no zoom, no jump, no foot skating, no body morphing."
        ),
    },
    "05_social_turn": {
        "id": "05_social_turn",
        "seed": 8262605,
        "source": SOURCE_ROOT / "runtime/inputs/social-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, the main woman turns her gaze gently toward her two "
            "friends and shares a brief natural smile; the friends respond with small relaxed "
            "smiles and minimal hand movement. All three remain in their original positions with "
            "stable faces, hands and clothing. The main woman then returns her gaze near camera. "
            "Locked tripod camera, no crowd, no duplicated person, no abrupt motion or identity drift."
        ),
    },
}


def load_runner():
    spec = importlib.util.spec_from_file_location("qingyan_t8_batch_runner", SOURCE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the existing T8 runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("shot_id", choices=tuple(SHOTS))
    args = parser.parse_args()

    runner = load_runner()
    runner.ROOT = OUTPUT_ROOT
    runner.SHOTS = (SHOTS[args.shot_id],)
    runner.main()


if __name__ == "__main__":
    main()
