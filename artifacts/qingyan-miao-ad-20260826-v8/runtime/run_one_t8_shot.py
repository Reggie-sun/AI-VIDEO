from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

import httpx

from ai_video.comfy_client import ComfyClient, JobStatus


REPO = Path("/home/reggie/vscode_folder/AI-VIDEO")
COMFY_ROOT = Path("/home/reggie/ComfyUI")
T8_ROOT = COMFY_ROOT / "custom_nodes/minimax-h3-audio-T8"
TASK_ROOT = REPO / "artifacts/qingyan-miao-ad-20260826-v8"
OUTPUT_ROOT = TASK_ROOT / "runtime/t8_portrait_ad"
TEMPLATE = REPO / "workflows/templates/minimax_h3_t8_t2va_quality_api.json"
ENDPOINT = "http://127.0.0.1:8188"
WIDTH = 768
HEIGHT = 1344
FPS = 24
SHOT_ID_PATTERN = re.compile(r"^[0-9]{2}_[a-z0-9_]+$")


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


def build_workflow(
    template: dict,
    uploaded_name: str,
    last_uploaded_name: str | None,
    prompt: str,
    length: int,
    seed: int,
    shot_id: str,
) -> dict:
    workflow = json.loads(json.dumps(template))
    workflow["5"]["inputs"].update(
        {
            "prompt": prompt,
            "width": WIDTH,
            "height": HEIGHT,
            "length": length,
            "task_type": "FL2VA" if last_uploaded_name else "I2VA",
            "first_frame": ["12", 0],
        }
    )
    if last_uploaded_name:
        workflow["5"]["inputs"]["last_frame"] = ["13", 0]
    workflow["7"]["inputs"]["noise_seed"] = seed
    workflow["11"]["inputs"]["filename_prefix"] = (
        f"development_experiment/qingyan_v8_{shot_id}_seed{seed}"
    )
    workflow["12"] = {
        "class_type": "LoadImage",
        "inputs": {"image": uploaded_name},
    }
    if last_uploaded_name:
        workflow["13"] = {
            "class_type": "LoadImage",
            "inputs": {"image": last_uploaded_name},
        }
    return workflow


def validate_workflow(workflow: dict, length: int, has_last_frame: bool) -> None:
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
        conditioning["task_type"] != ("FL2VA" if has_last_frame else "I2VA")
        or conditioning["width"] != WIDTH
        or conditioning["height"] != HEIGHT
        or conditioning["length"] != length
        or conditioning["first_frame"] != ["12", 0]
        or sampler["steps"] != 20
        or sampler["sampler_name"] != "res_multistep"
        or sampler["scheduler"] != "simple"
    ):
        raise RuntimeError("portrait T8 quality settings changed")
    if has_last_frame and conditioning.get("last_frame") != ["13", 0]:
        raise RuntimeError("FL2VA last-frame binding changed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shot-id", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--last-frame", type=Path)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--length", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    if not SHOT_ID_PATTERN.fullmatch(args.shot_id):
        parser.error("--shot-id must match NN_lowercase_name")
    if args.length < 124 or args.length > 362 or args.length % 17 != 5:
        parser.error("--length must be an accepted 17n+5 frame count from 124 through 362")
    return args


def main() -> None:
    args = parse_args()
    source = args.source.resolve(strict=True)
    last_frame = args.last_frame.resolve(strict=True) if args.last_frame else None
    prompt_path = args.prompt.resolve(strict=True)
    if not source.is_file() or not prompt_path.is_file():
        raise RuntimeError("source and prompt must be regular files")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_ROOT / f"{args.shot_id}.mp4"
    receipt_path = OUTPUT_ROOT / f"{args.shot_id}.receipt.json"
    state_path = OUTPUT_ROOT / f"{args.shot_id}.state.json"
    graph_path = OUTPUT_ROOT / f"{args.shot_id}.submitted-workflow.json"
    if any(path.exists() for path in (output, receipt_path, state_path, graph_path)):
        raise RuntimeError(f"{args.shot_id} already has durable state; do not retry blindly")

    template_bytes = TEMPLATE.read_bytes()
    template = json.loads(template_bytes)
    source_bytes = source.read_bytes()
    last_frame_bytes = last_frame.read_bytes() if last_frame else None
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    source_sha = sha256(source_bytes)

    with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as http:
        http.get(f"{ENDPOINT}/system_stats").raise_for_status()
        queue_response = http.get(f"{ENDPOINT}/queue")
        queue_response.raise_for_status()
        queue_payload = queue_response.json()
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
            f"qingyan-v8-{args.shot_id}-{source_sha[:16]}{source.suffix.lower()}",
            source_bytes,
        )
        last_uploaded_name = None
        if last_frame and last_frame_bytes is not None:
            last_uploaded_name = client.upload_input_bytes(
                f"qingyan-v8-{args.shot_id}-last-{sha256(last_frame_bytes)[:16]}{last_frame.suffix.lower()}",
                last_frame_bytes,
            )
        workflow = build_workflow(
            template,
            uploaded_name,
            last_uploaded_name,
            prompt,
            args.length,
            args.seed,
            args.shot_id,
        )
        validate_workflow(workflow, args.length, last_frame is not None)
        graph_bytes = json.dumps(
            workflow,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        graph_path.write_text(
            json.dumps(workflow, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        state = {
            "status": "prepared",
            "shot_id": args.shot_id,
            "seed": args.seed,
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
            timeout_seconds=2400.0,
        )
        if result.status is not JobStatus.COMPLETED or result.history is None:
            state.update({"status": "failed", "job_status": result.status.value})
            atomic_json(state_path, state)
            raise RuntimeError(
                f"single T8 submit for {args.shot_id} did not complete: "
                f"{result.status.value}; do not retry blindly"
            )

        candidates = []
        for node in result.history.get("outputs", {}).values():
            for item in node.get("gifs", []):
                if str(item.get("filename", "")).endswith("-audio.mp4"):
                    candidates.append(item)
        if len(candidates) != 1:
            raise RuntimeError(
                f"expected one final AV artifact for {args.shot_id}, got {len(candidates)}"
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
                "single local T8-only 20-step development clip; "
                "not Production activation, P6, or Final Acceptance"
            ),
            "shot_id": args.shot_id,
            "provider_effects": {
                "local_submit_count": 1,
                "retry_count": 0,
                "fallback_count": 0,
                "remote_submit_count": 0,
            },
            "prompt_id": prompt_id,
            "prompt_path": prompt_path.relative_to(REPO).as_posix(),
            "prompt_sha256": sha256(prompt.encode("utf-8")),
            "seed": args.seed,
            "settings": {
                "mode": "FL2VA" if last_frame else "I2VA",
                "width": WIDTH,
                "height": HEIGHT,
                "frame_count": args.length,
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
                "path": source.relative_to(REPO).as_posix(),
                "sha256": source_sha,
                "uploaded_name": uploaded_name,
            },
            "last_frame": (
                {
                    "path": last_frame.relative_to(REPO).as_posix(),
                    "sha256": sha256(last_frame_bytes),
                    "uploaded_name": last_uploaded_name,
                }
                if last_frame and last_frame_bytes is not None
                else None
            ),
            "template": {
                "path": TEMPLATE.relative_to(REPO).as_posix(),
                "source_sha256": sha256(template_bytes),
                "submitted_graph_path": graph_path.relative_to(REPO).as_posix(),
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
