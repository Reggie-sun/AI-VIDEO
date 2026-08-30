from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

import httpx

from ai_video.comfy_client import ComfyClient, JobStatus


REPO = Path("/home/reggie/vscode_folder/AI-VIDEO")
COMFY_ROOT = Path("/home/reggie/ComfyUI")
T8_ROOT = COMFY_ROOT / "custom_nodes/minimax-h3-audio-T8"
ROOT = REPO / "artifacts/qingyan-miao-ad-20260825/runtime/t8_smoothness"
TEMPLATE = REPO / "workflows/templates/minimax_h3_t8_t2va_quality_api.json"
OUTPUT = ROOT / "qingyan-miao-t8-stock20-smoothness.mp4"
RECEIPT = ROOT / "receipt.json"
ENDPOINT = "http://127.0.0.1:8188"
SEED = 8252026
WIDTH = 1344
HEIGHT = 768
FILENAME_PREFIX = "development_experiment/qingyan_miao_t8_stock20_smoothness_seed8252026"

PROMPT = """integrated_multimodal_description: [Shot 1] Live-action commercial realism, a modern 22-year-old Miao woman with a natural Chinese face wears an ivory blouse with refined indigo Miao embroidery, a dark flowing skirt, small silver earrings and a restrained silver hair ornament. In bright clean morning sunlight on a quiet mountain village lane, she walks steadily toward screen right at a natural relaxed pace. Her face, chest, hips, knees and toes remain oriented toward screen right; every foot plant lands farther toward screen right than the previous one. Her arms swing naturally, the skirt hem, loose hair strands and silver earrings respond with subtle secondary motion. No pivot, no turn around, no backward step, no backpedal, no sideways slide, no walking in place. A medium full-body side-profile camera tracks toward screen right at matched speed with small amplitude and steady motion, preserving consistent body scale and clean background parallax. No cut, no text, no logo.
overall_soundscape: Soft outdoor breeze, light natural footsteps on stone, subtle fabric movement and a faint clean silver-earring chime. No dialogue and no crowd noise.
non_diegetic_music: Light modern plucked strings with a restrained crisp rhythm at medium tempo, low in the mix, fresh and commercial without dramatic percussion."""


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def main() -> None:
    if OUTPUT.exists() or RECEIPT.exists():
        raise RuntimeError("single-submit experiment already has durable output")

    template_bytes = TEMPLATE.read_bytes()
    workflow = json.loads(template_bytes)
    workflow["5"]["inputs"]["prompt"] = PROMPT
    workflow["5"]["inputs"]["width"] = WIDTH
    workflow["5"]["inputs"]["height"] = HEIGHT
    workflow["7"]["inputs"]["noise_seed"] = SEED
    workflow["11"]["inputs"]["filename_prefix"] = FILENAME_PREFIX

    classes = tuple(node["class_type"] for node in workflow.values())
    required = {
        "MiniMaxH3AudioConditioningT8",
        "MiniMaxH3DualClockSamplerT8",
        "MiniMaxH3AVDecodeT8",
    }
    forbidden = {
        "MiniMaxH3TurboLoRA",
        "MiniMaxH3TurboSampler",
        "LoraLoaderBypassModelOnly",
        "LoraLoader",
        "LoraLoaderModelOnly",
    }
    if not required.issubset(classes) or forbidden.intersection(classes):
        raise RuntimeError("submitted graph is not the accepted T8-only Stock20 route")
    conditioning = workflow["5"]["inputs"]
    sampler = workflow["6"]["inputs"]
    if (
        conditioning["task_type"] != "T2VA"
        or conditioning["width"] != WIDTH
        or conditioning["height"] != HEIGHT
        or conditioning["length"] != 124
        or sampler["steps"] != 20
        or sampler["sampler_name"] != "res_multistep"
        or sampler["scheduler"] != "simple"
    ):
        raise RuntimeError("Stock20 motion-validation settings changed")

    started = time.monotonic()
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
        missing = sorted(required.difference(object_info))
        if missing:
            raise RuntimeError(f"ComfyUI is missing required T8 nodes: {missing}")

        prompt_id = client.submit_prompt(workflow)
        result = client.poll_job(
            prompt_id,
            poll_interval_seconds=2.0,
            timeout_seconds=900.0,
        )
        if result.status is not JobStatus.COMPLETED or result.history is None:
            raise RuntimeError(
                f"single T8 submit did not complete: {result.status.value}; "
                "do not retry blindly"
            )
        candidates = []
        for node in result.history.get("outputs", {}).values():
            for item in node.get("gifs", []):
                if str(item.get("filename", "")).endswith("-audio.mp4"):
                    candidates.append(item)
        if len(candidates) != 1:
            raise RuntimeError(f"expected one final AV artifact, got {len(candidates)}")
        artifact = candidates[0]
        payload = client.fetch_artifact_bytes(
            filename=artifact["filename"],
            subfolder=artifact.get("subfolder", ""),
            type_=artifact.get("type", "output"),
        )

    OUTPUT.write_bytes(payload)
    receipt = {
        "acceptance_boundary": (
            "single local T8 Stock20 development experiment for human motion "
            "smoothness review; not Production activation or final acceptance"
        ),
        "provider_effects": {
            "local_submit_count": 1,
            "retry_count": 0,
            "fallback_count": 0,
            "remote_submit_count": 0,
        },
        "prompt_id": prompt_id,
        "prompt_sha256": sha256(PROMPT.encode("utf-8")),
        "seed": SEED,
        "settings": {
            "mode": "T2VA",
            "width": WIDTH,
            "height": HEIGHT,
            "frame_count": 124,
            "fps": 24,
            "steps": 20,
            "sampler": "res_multistep",
            "scheduler": "simple",
            "native_audio": True,
            "crf": 17,
        },
        "runtime": {
            "comfyui_commit": git_head(COMFY_ROOT),
            "t8_commit": git_head(T8_ROOT),
            "endpoint": ENDPOINT,
        },
        "template": {
            "path": TEMPLATE.relative_to(REPO).as_posix(),
            "source_sha256": sha256(template_bytes),
            "submitted_graph_sha256": sha256(
                json.dumps(
                    workflow,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ),
        },
        "output": {
            "path": OUTPUT.relative_to(REPO).as_posix(),
            "sha256": sha256(payload),
            "size_bytes": len(payload),
        },
        "wall_time_seconds": round(time.monotonic() - started, 3),
    }
    RECEIPT.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
