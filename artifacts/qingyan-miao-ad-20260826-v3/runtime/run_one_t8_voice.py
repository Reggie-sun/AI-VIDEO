from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


REPO = Path("/home/reggie/vscode_folder/AI-VIDEO")
SOURCE_RUNNER = (
    REPO
    / "artifacts/qingyan-miao-ad-20260825/runtime/execute_t8_portrait_ad_batch.py"
)
OUTPUT_ROOT = REPO / "artifacts/qingyan-miao-ad-20260826-v3/runtime/voice"
SOURCE_IMAGE = (
    REPO / "artifacts/qingyan-miao-ad-20260825/assets/04-golden-fluid.png"
)


VOICE_SHOTS = {
    "vo01_hook": {
        "id": "vo01_hook",
        "seed": 8262701,
        "length": 107,
        "line": "天气一热，汗湿黏腻，异味尴尬，真的影响每一次靠近。",
        "speaker": (
            "A warm clear 23-year-old Chinese female commercial narrator (S1), "
            "neutral Mandarin, medium pace, bright natural timbre"
        ),
    },
    "vo02_product": {
        "id": "vo02_product",
        "seed": 8262702,
        "length": 107,
        "line": "出门前，我会先用青颜抑汗净味喷雾。",
        "speaker": (
            "The same warm clear 23-year-old Chinese female commercial narrator (S1), "
            "neutral Mandarin, medium pace, bright natural timbre"
        ),
    },
    "vo03_benefit": {
        "id": "vo03_benefit",
        "seed": 8262703,
        "length": 107,
        "line": "抑汗净味，清爽舒适，帮助减少汗湿困扰。",
        "speaker": (
            "The same warm clear 23-year-old Chinese female commercial narrator (S1), "
            "neutral Mandarin, medium pace, bright natural timbre"
        ),
    },
    "vo04_dialogue": {
        "id": "vo04_dialogue",
        "seed": 8262704,
        "length": 124,
        "line": "今天状态真好！|出门前，我用了青颜。",
        "speaker": "two young adult Chinese women speaking in neutral Mandarin",
    },
    "vo05_close": {
        "id": "vo05_close",
        "seed": 8262705,
        "length": 90,
        "line": "青颜，清爽自在，自信不用藏。",
        "speaker": (
            "The same warm clear 23-year-old Chinese female commercial narrator (S1), "
            "neutral Mandarin, medium pace, bright natural timbre"
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


def narration_prompt(shot: dict) -> str:
    if shot["id"] == "vo04_dialogue":
        dialogue = (
            "An off-screen young Chinese woman (S1), clear bright voice, says "
            "<d>[Chinese]今天状态真好！</d> After a short natural pause, a second "
            "off-screen young Chinese woman (S2), warm confident voice, replies "
            "<d>[Chinese]出门前，我用了青颜。</d>"
        )
    else:
        dialogue = (
            f"{shot['speaker']} says exactly "
            f"<d>[Chinese]{shot['line']}</d>"
        )
    return f"""For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action premium personal-care commercial in native portrait composition. Starting exactly from Picture 1, retain a clean abstract golden-fluid background with only very slow continuous liquid movement and no visible person, face, mouth, product text or logo. {dialogue} The speech starts after a brief 0.15-second clean lead-in and is spoken once only, with no repeated word, no added greeting and no trailing phrase. Locked camera, no cut, no visual text.
overall_soundscape: Foreground dry studio-quality Mandarin speech, clearly audible and centered. Very soft clean room tone only; no other voice, no echo and no crowd noise.
non_diegetic_music: No music."""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("shot_id", choices=tuple(VOICE_SHOTS))
    args = parser.parse_args()
    shot = dict(VOICE_SHOTS[args.shot_id])
    shot["source"] = SOURCE_IMAGE
    shot["action"] = "voice-only source"

    runner = load_runner()
    runner.ROOT = OUTPUT_ROOT
    runner.LENGTH = shot["length"]
    runner.SHOTS = (shot,)
    runner.prompt_for = lambda _action: narration_prompt(shot)
    runner.main()


if __name__ == "__main__":
    main()
