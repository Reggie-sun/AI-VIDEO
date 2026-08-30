from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import httpx

from ai_video.comfy_client import ComfyClient, JobStatus


REPO = Path("/home/reggie/vscode_folder/AI-VIDEO")
COMFY_ROOT = Path("/home/reggie/ComfyUI")
T8_ROOT = COMFY_ROOT / "custom_nodes/minimax-h3-audio-T8"
TASK_ROOT = REPO / "artifacts/qingyan-miao-ad-20260825"
ROOT = TASK_ROOT / "runtime/t8_portrait_ad"
TEMPLATE = REPO / "workflows/templates/minimax_h3_t8_i2va_turbo_native_v2_api.json"
ENDPOINT = "http://127.0.0.1:8188"
WIDTH = 768
HEIGHT = 1344
LENGTH = 56
FPS = 24


SHOTS = (
    {
        "id": "01_concern",
        "seed": 8252201,
        "source": TASK_ROOT / "assets/01-concern.png",
        "action": (
            "Starting exactly from Picture 1, she briefly checks the fabric beside her underarm "
            "with one restrained natural touch, exhales softly, then lowers her hand. Her expression "
            "shows only mild concern. Subtle breathing, a small blink and gentle earring movement; "
            "no exaggerated sweat, no grimace, no camera movement, no body morphing."
        ),
    },
    {
        "id": "02_product_lift",
        "seed": 8252202,
        "source": TASK_ROOT / "runtime/inputs/product-use-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she looks down at the yellow bottle in her hands, "
            "lifts it smoothly to chest height and gives a small confident smile. The closed white cap, "
            "yellow label, bottle silhouette and her fingers remain stable. No opening, no spraying, "
            "no extra object, no camera movement, no label morphing."
        ),
    },
    {
        "id": "03_product_use",
        "seed": 8252203,
        "source": TASK_ROOT / "runtime/inputs/product-use-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she raises the small yellow bottle with its white cap "
            "toward the side of her blouse near the underarm, making a clean elegant pre-use gesture, "
            "then relaxes her shoulder. The action only implies application; no exposed skin and no "
            "visible liquid. Keep the bottle shape, yellow label, white cap, face and hands stable. "
            "No camera movement, no anatomy distortion, no extra fingers."
        ),
    },
    {
        "id": "03b_product_use_clean",
        "seed": 8252208,
        "source": TASK_ROOT / "runtime/inputs/product-use-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, only her right hand lifts the small yellow bottle "
            "smoothly from waist height toward the side of her upper blouse in a clean pre-use gesture. "
            "Her left hand stays relaxed at her waist and never reaches across her body. The white cap "
            "stays on; no visible mist and no exposed skin. Exactly two hands belonging to her, no other "
            "hand or arm enters from any edge. Keep bottle shape, yellow label, face and fingers stable. "
            "Locked camera, no anatomy distortion, no extra person."
        ),
    },
    {
        "id": "04_walk_forward",
        "seed": 8252204,
        "source": TASK_ROOT / "runtime/inputs/walk-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she takes two calm natural steps forward along the stone "
            "lane while remaining centered. Both shoes stay visible; heel contact, weight transfer and "
            "toe-off are continuous. Her arms, skirt hem, loose hair and silver earrings move gently. "
            "Locked tripod camera, no pan, no zoom, no jump, no foot skating, no body morphing."
        ),
    },
    {
        "id": "05_walk_smile",
        "seed": 8252205,
        "source": TASK_ROOT / "runtime/inputs/walk-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she continues one smooth forward step and turns her gaze "
            "slightly toward the camera with a natural warm smile. Her body keeps moving forward; skirt "
            "and earrings show restrained continuous secondary motion. Locked tripod camera, stable "
            "background, no sudden turn, no jump, no foot skating, no facial drift."
        ),
    },
    {
        "id": "06_social_turn",
        "seed": 8252206,
        "source": TASK_ROOT / "runtime/inputs/social-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, she turns gently toward her two friends and shares a "
            "brief natural smile; the friends respond with small relaxed smiles and subtle hand motion. "
            "All three women remain in their original positions with stable faces and clothing. Locked "
            "tripod camera, no crowd, no duplicated person, no body morphing, no abrupt motion."
        ),
    },
    {
        "id": "07_social回眸",
        "seed": 8252207,
        "source": TASK_ROOT / "runtime/inputs/social-936x1664.png",
        "action": (
            "Starting exactly from Picture 1, the main woman takes one light step past the foreground "
            "table, then looks back toward the camera with a soft confident smile. Her skirt swings "
            "slightly and settles; the two friends continue a quiet natural conversation behind her. "
            "Locked tripod camera, no zoom, no cut, no extra person, no identity drift, no anatomy error."
        ),
    },
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def prompt_for(action: str) -> str:
    return f"""For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action premium personal-care commercial in native portrait composition, featuring the same modern 22-year-old Miao woman with a natural Chinese face, ivory blouse with refined indigo Miao embroidery, navy skirt, restrained silver earrings and silver hair ornament. {action} Bright clean natural daylight, soft skin texture, airy background, one continuous shot, no text, no logo.
overall_soundscape: Soft room or outdoor ambience matching the source scene, subtle fabric movement and a restrained silver-earring chime. No dialogue and no crowd noise.
non_diegetic_music: Light modern plucked strings with an even medium-tempo pulse, low in the mix, without dramatic percussion."""


def build_workflow(template: dict, shot: dict, uploaded_name: str) -> tuple[dict, str]:
    workflow = json.loads(json.dumps(template))
    prompt = prompt_for(shot["action"])
    conditioning = workflow["6"]["inputs"]
    conditioning.update(
        {
            "prompt": prompt,
            "width": WIDTH,
            "height": HEIGHT,
            "length": LENGTH,
            "task_type": "I2VA",
            "first_frame": ["13", 0],
        }
    )
    workflow["8"]["inputs"]["noise_seed"] = shot["seed"]
    workflow["12"]["inputs"]["filename_prefix"] = (
        f"development_experiment/qingyan_t8_portrait_ad_{shot['id']}_seed{shot['seed']}"
    )
    workflow["13"]["inputs"]["image"] = uploaded_name
    return workflow, prompt


def validate_workflow(workflow: dict) -> None:
    classes = tuple(node["class_type"] for node in workflow.values())
    required = {
        "MiniMaxH3AudioConditioningT8",
        "MiniMaxH3DualClockSamplerT8",
        "MiniMaxH3AVDecodeT8",
        "LoraLoaderBypassModelOnly",
        "LoadImage",
    }
    forbidden = {
        "MiniMaxH3TurboLoRA",
        "MiniMaxH3TurboSampler",
        "LoraLoader",
        "LoraLoaderModelOnly",
    }
    if not required.issubset(classes) or forbidden.intersection(classes):
        raise RuntimeError("submitted graph is not the accepted T8-only Stock20 I2VA route")
    conditioning = workflow["6"]["inputs"]
    sampler = workflow["7"]["inputs"]
    if (
        conditioning["task_type"] != "I2VA"
        or conditioning["width"] != WIDTH
        or conditioning["height"] != HEIGHT
        or conditioning["length"] != LENGTH
        or sampler["steps"] != 4
        or sampler["sampler_name"] != "dual_clock_euler"
        or sampler["scheduler"] != "native_flow"
    ):
        raise RuntimeError("portrait Turbo4 ad settings changed")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    template_bytes = TEMPLATE.read_bytes()
    template = json.loads(template_bytes)
    required_nodes = {
        "MiniMaxH3AudioConditioningT8",
        "MiniMaxH3DualClockSamplerT8",
        "MiniMaxH3AVDecodeT8",
        "LoraLoaderBypassModelOnly",
        "LoadImage",
    }

    with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as http:
        stats = http.get(f"{ENDPOINT}/system_stats")
        stats.raise_for_status()
        queue = http.get(f"{ENDPOINT}/queue")
        queue.raise_for_status()
        queue_payload = queue.json()
        if queue_payload.get("queue_running") or queue_payload.get("queue_pending"):
            raise RuntimeError("ComfyUI queue is not empty")

        client = ComfyClient(ENDPOINT, http_client=http)
        object_info = client.get_object_info()
        missing = sorted(required_nodes.difference(object_info))
        if missing:
            raise RuntimeError(f"ComfyUI is missing required T8 nodes: {missing}")

        for shot in SHOTS:
            output = ROOT / f"{shot['id']}.mp4"
            receipt_path = ROOT / f"{shot['id']}.receipt.json"
            state_path = ROOT / f"{shot['id']}.state.json"
            if output.exists() and receipt_path.exists():
                continue
            if output.exists() or receipt_path.exists() or state_path.exists():
                raise RuntimeError(
                    f"{shot['id']} has partial durable state; do not retry blindly"
                )

            source_bytes = shot["source"].read_bytes()
            source_sha = sha256(source_bytes)
            uploaded_name = client.upload_input_bytes(
                f"qingyan-{shot['id']}-{source_sha[:16]}.png", source_bytes
            )
            workflow, prompt = build_workflow(template, shot, uploaded_name)
            validate_workflow(workflow)
            graph_bytes = json.dumps(
                workflow,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            state = {
                "status": "prepared",
                "shot_id": shot["id"],
                "seed": shot["seed"],
                "source_sha256": source_sha,
                "submitted_graph_sha256": sha256(graph_bytes),
            }
            atomic_json(state_path, state)

            started = time.monotonic()
            prompt_id = client.submit_prompt(workflow)
            state.update({"status": "submitted", "prompt_id": prompt_id})
            atomic_json(state_path, state)
            result = client.poll_job(
                prompt_id,
                poll_interval_seconds=2.0,
                timeout_seconds=900.0,
            )
            if result.status is not JobStatus.COMPLETED or result.history is None:
                raise RuntimeError(
                    f"single T8 submit for {shot['id']} did not complete: "
                    f"{result.status.value}; do not retry blindly"
                )

            candidates = []
            for node in result.history.get("outputs", {}).values():
                for item in node.get("gifs", []):
                    if str(item.get("filename", "")).endswith("-audio.mp4"):
                        candidates.append(item)
            if len(candidates) != 1:
                raise RuntimeError(
                    f"expected one final AV artifact for {shot['id']}, got {len(candidates)}"
                )
            artifact = candidates[0]
            payload = client.fetch_artifact_bytes(
                filename=artifact["filename"],
                subfolder=artifact.get("subfolder", ""),
                type_=artifact.get("type", "output"),
            )
            output.write_bytes(payload)
            receipt = {
                "acceptance_boundary": (
                    "single local T8 Turbo4 I2VA development clip for a portrait ad; "
                    "not Production activation, P6, or Final Acceptance"
                ),
                "shot_id": shot["id"],
                "provider_effects": {
                    "local_submit_count": 1,
                    "retry_count": 0,
                    "fallback_count": 0,
                    "remote_submit_count": 0,
                },
                "prompt_id": prompt_id,
                "prompt_sha256": sha256(prompt.encode("utf-8")),
                "seed": shot["seed"],
                "settings": {
                    "mode": "I2VA",
                    "width": WIDTH,
                    "height": HEIGHT,
                    "frame_count": LENGTH,
                    "fps": FPS,
                    "steps": 4,
                    "sampler": "dual_clock_euler",
                    "scheduler": "native_flow",
                    "native_audio": True,
                    "crf": 17,
                },
                "runtime": {
                    "comfyui_commit": git_head(COMFY_ROOT),
                    "t8_commit": git_head(T8_ROOT),
                    "endpoint": ENDPOINT,
                },
                "source": {
                    "path": shot["source"].relative_to(REPO).as_posix(),
                    "sha256": source_sha,
                    "uploaded_name": uploaded_name,
                },
                "template": {
                    "path": TEMPLATE.relative_to(REPO).as_posix(),
                    "source_sha256": sha256(template_bytes),
                    "submitted_graph_sha256": sha256(graph_bytes),
                },
                "output": {
                    "path": output.relative_to(REPO).as_posix(),
                    "sha256": sha256(payload),
                    "size_bytes": len(payload),
                },
                "wall_time_seconds": round(time.monotonic() - started, 3),
            }
            atomic_json(receipt_path, receipt)
            state.update(
                {
                    "status": "completed",
                    "output_sha256": receipt["output"]["sha256"],
                    "receipt": receipt_path.relative_to(REPO).as_posix(),
                }
            )
            atomic_json(state_path, state)
            print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
