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
TASK_ROOT = REPO / "artifacts/qingyan-miao-ad-20260826-v5"
OUTPUT_ROOT = TASK_ROOT / "runtime/t8_portrait_ad"
SOURCE = (
    REPO
    / "artifacts/qingyan-miao-ad-20260825/runtime/inputs/product-use-936x1664.png"
)
TEMPLATE = REPO / "workflows/templates/minimax_h3_t8_t2va_quality_api.json"
ENDPOINT = "http://127.0.0.1:8188"
SHOT_ID = "03_spoken_recommendation"
SEED = 8262703
WIDTH = 768
HEIGHT = 1344
LENGTH = 124
FPS = 24
EXACT_DIALOGUE = "出门前用青颜，抑汗净味，清爽舒适。"


PROMPT = f"""For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action premium personal-care commercial in native portrait composition, featuring the same modern 22-year-old Miao woman with a natural Chinese face, ivory blouse with refined indigo Miao embroidery, navy skirt, restrained silver earrings and silver hair ornament. Starting exactly from Picture 1, she keeps the capped yellow bottle at comfortable chest height, looks directly toward the camera and speaks once with natural continuous Mandarin lip movement. Speaker 1 (S1) is the on-screen 22-year-old Chinese woman with a warm clear mid-high voice, moderate conversational rate and standard Mandarin. Speaker 1 (S1) says exactly and only: <d>[Chinese] {EXACT_DIALOGUE}</d> After the final word she closes her mouth and gives a small confident smile. Both hands stay fully inside frame; the closed white cap, yellow label, bottle silhouette, face, clothing and body scale remain stable. Locked tripod camera, one continuous shot, no cut, no zoom, no extra hand, no duplicated person, no label morphing, no text and no logo.
overall_soundscape: Quiet clean indoor room tone, subtle fabric movement and one restrained silver-earring chime. No other voice and no speech outside the marked dialogue.
non_diegetic_music: Very soft modern plucked strings at an even medium tempo, kept far below the spoken voice without dramatic percussion."""


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


def build_workflow(template: dict, uploaded_name: str) -> dict:
    workflow = json.loads(json.dumps(template))
    workflow["5"]["inputs"].update(
        {
            "prompt": PROMPT,
            "width": WIDTH,
            "height": HEIGHT,
            "length": LENGTH,
            "task_type": "I2VA",
            "first_frame": ["12", 0],
        }
    )
    workflow["7"]["inputs"]["noise_seed"] = SEED
    workflow["11"]["inputs"]["filename_prefix"] = (
        "development_experiment/qingyan_t8_portrait_spoken_recommendation_"
        f"seed{SEED}"
    )
    workflow["12"] = {
        "class_type": "LoadImage",
        "inputs": {"image": uploaded_name},
    }
    return workflow


def validate_workflow(workflow: dict) -> None:
    classes = tuple(node["class_type"] for node in workflow.values())
    required = {
        "UNETLoader",
        "CLIPLoader",
        "VAELoader",
        "MiniMaxH3AudioConditioningT8",
        "MiniMaxH3DualClockSamplerT8",
        "MiniMaxH3AVDecodeT8",
        "LoadImage",
    }
    forbidden = {
        "MiniMaxH3TurboLoRA",
        "MiniMaxH3TurboSampler",
        "LoraLoaderBypassModelOnly",
        "LoraLoader",
        "LoraLoaderModelOnly",
    }
    if not required.issubset(classes) or forbidden.intersection(classes):
        raise RuntimeError("submitted graph is not the accepted T8-only quality route")
    conditioning = workflow["5"]["inputs"]
    sampler = workflow["6"]["inputs"]
    if (
        conditioning["task_type"] != "I2VA"
        or conditioning["width"] != WIDTH
        or conditioning["height"] != HEIGHT
        or conditioning["length"] != LENGTH
        or conditioning["first_frame"] != ["12", 0]
        or sampler["steps"] != 20
        or sampler["sampler_name"] != "res_multistep"
        or sampler["scheduler"] != "simple"
    ):
        raise RuntimeError("portrait T8 quality settings changed")


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_ROOT / f"{SHOT_ID}.mp4"
    receipt_path = OUTPUT_ROOT / f"{SHOT_ID}.receipt.json"
    state_path = OUTPUT_ROOT / f"{SHOT_ID}.state.json"
    if output.exists() or receipt_path.exists() or state_path.exists():
        raise RuntimeError(f"{SHOT_ID} already has durable state; do not retry blindly")

    template_bytes = TEMPLATE.read_bytes()
    template = json.loads(template_bytes)
    source_bytes = SOURCE.read_bytes()
    source_sha = sha256(source_bytes)

    with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as http:
        http.get(f"{ENDPOINT}/system_stats").raise_for_status()
        queue = http.get(f"{ENDPOINT}/queue")
        queue.raise_for_status()
        queue_payload = queue.json()
        if queue_payload.get("queue_running") or queue_payload.get("queue_pending"):
            raise RuntimeError("ComfyUI queue is not empty")

        client = ComfyClient(ENDPOINT, http_client=http)
        object_info = client.get_object_info()
        missing = sorted(
            {
                "MiniMaxH3AudioConditioningT8",
                "MiniMaxH3DualClockSamplerT8",
                "MiniMaxH3AVDecodeT8",
                "LoadImage",
            }.difference(object_info)
        )
        if missing:
            raise RuntimeError(f"ComfyUI is missing required T8 nodes: {missing}")

        uploaded_name = client.upload_input_bytes(
            f"qingyan-{SHOT_ID}-{source_sha[:16]}.png", source_bytes
        )
        workflow = build_workflow(template, uploaded_name)
        validate_workflow(workflow)
        graph_bytes = json.dumps(
            workflow,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        state = {
            "status": "prepared",
            "shot_id": SHOT_ID,
            "seed": SEED,
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
            timeout_seconds=1800.0,
        )
        if result.status is not JobStatus.COMPLETED or result.history is None:
            raise RuntimeError(
                f"single T8 submit for {SHOT_ID} did not complete: "
                f"{result.status.value}; do not retry blindly"
            )

        candidates = []
        for node in result.history.get("outputs", {}).values():
            for item in node.get("gifs", []):
                if str(item.get("filename", "")).endswith("-audio.mp4"):
                    candidates.append(item)
        if len(candidates) != 1:
            raise RuntimeError(
                f"expected one final AV artifact for {SHOT_ID}, got {len(candidates)}"
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
                "single local T8-only 20-step I2VA dialogue development clip; "
                "not Production activation, P6, or Final Acceptance"
            ),
            "shot_id": SHOT_ID,
            "provider_effects": {
                "local_submit_count": 1,
                "retry_count": 0,
                "fallback_count": 0,
                "remote_submit_count": 0,
            },
            "prompt_id": prompt_id,
            "prompt_sha256": sha256(PROMPT.encode("utf-8")),
            "exact_dialogue": EXACT_DIALOGUE,
            "seed": SEED,
            "settings": {
                "mode": "I2VA",
                "width": WIDTH,
                "height": HEIGHT,
                "frame_count": LENGTH,
                "fps": FPS,
                "steps": 20,
                "sampler": "res_multistep",
                "scheduler": "simple",
                "native_audio": True,
                "lora_enabled": False,
                "crf": 17,
            },
            "runtime": {
                "comfyui_commit": git_head(COMFY_ROOT),
                "t8_commit": git_head(T8_ROOT),
                "endpoint": ENDPOINT,
            },
            "source": {
                "path": SOURCE.relative_to(REPO).as_posix(),
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
