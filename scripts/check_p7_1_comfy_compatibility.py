from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ai_video.production.comfy_image import (  # noqa: E402
    load_local_image_binding,
    load_local_image_execution_profile,
)
from ai_video.workflow_loader import (  # noqa: E402
    SubgraphUiWorkflowConverter,
    load_workflow_template,
)
from ai_video.workflow_renderer import validate_api_workflow  # noqa: E402


EXPECTED_COMFY_COMMIT = "7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa"
OFFICIAL_TEMPLATE_HASHES = {
    "image_qwen_image_edit_2511.json": "d561a38c15bd7d08758a5e6773d467142244d5b83fc5d3aecdf6d8df9fe881b6",
    "image_flux2_klein_image_edit_4b_distilled.json": "e0388a8870495802314d58fa61616ddcdb7064dac5f85a8787c9e08180b8a560",
}
PROFILE_PATHS = {
    "qwen": REPO_ROOT / "workflows/profiles/p7_1_qwen_image_edit_2511.json",
    "flux": REPO_ROOT / "workflows/profiles/p7_1_flux2_klein_4b.json",
}
GIB = 1024**3


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _template_root() -> Path:
    spec = importlib.util.find_spec("comfyui_workflow_templates_json")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("comfyui_workflow_templates_json is not installed")
    return Path(next(iter(spec.submodule_search_locations))) / "templates"


def _model_kind(path: Path) -> tuple[str, int]:
    with path.open("rb") as handle:
        raw = handle.read(8)
        if len(raw) != 8:
            raise RuntimeError(f"invalid safetensors header: {path}")
        length = struct.unpack("<Q", raw)[0]
        if length <= 0 or length > 64 * 1024 * 1024:
            raise RuntimeError(f"unsafe safetensors header length: {path}")
        header = json.loads(handle.read(length))
    keys = set(header) - {"__metadata__"}
    metadata = header.get("__metadata__") or {}
    model_type = str(metadata.get("model_type", "")).lower()
    if "wan" in model_type or "blocks.0.cross_attn.k.bias" in keys:
        return "wan2.2", length
    if "__index_timestep_zero__" in keys and "img_in.weight" in keys:
        return "qwen_image_edit_2511", length
    if "double_blocks.0.img_attn.qkv.weight" in keys:
        return "flux2_klein", length
    if "adaln_t_table" in keys and "audio_patch_proj.weight" in keys:
        return "minimax_h3", length
    return "unknown", length


def _folder_inventory(comfy_root: Path) -> dict[str, list[dict[str, Any]]]:
    sys.path.insert(0, str(comfy_root))
    import folder_paths  # type: ignore[import-not-found]

    result: dict[str, list[dict[str, Any]]] = {}
    for category in ("diffusion_models", "text_encoders", "vae", "loras"):
        entries: list[dict[str, Any]] = []
        seen: set[Path] = set()
        for directory in folder_paths.get_folder_paths(category):
            root = Path(directory).resolve(strict=True)
            for candidate in sorted(root.rglob("*.safetensors")):
                resolved = candidate.resolve(strict=True)
                identity = candidate.absolute()
                if identity in seen:
                    continue
                seen.add(identity)
                item: dict[str, Any] = {
                    "path": str(candidate),
                    "resolved_path": str(resolved),
                    "size_bytes": resolved.stat().st_size,
                    "symlink": candidate.is_symlink(),
                }
                if category == "diffusion_models":
                    item["model_kind"], item["header_bytes"] = _model_kind(resolved)
                entries.append(item)
        result[category] = entries
    return result


def _required_nodes_present(comfy_root: Path, names: set[str]) -> dict[str, bool]:
    source = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(
            (
                *comfy_root.glob("*.py"),
                *comfy_root.glob("comfy/**/*.py"),
                *comfy_root.glob("comfy_extras/**/*.py"),
            )
        )
    )
    return {name: name in source for name in sorted(names)}


def _lineage_bytes(template: Path, lane: str) -> bytes:
    if lane == "qwen":
        graph = load_workflow_template(template)
        graph["170:161"]["inputs"]["unet_name"] = (
            "qwen_image_edit_2511_bf16.safetensors"
        )
        graph["170:160"] = {
            "_meta": {"title": "Exact request size"},
            "class_type": "ImageScale",
            "inputs": {
                "crop": "disabled",
                "height": 720,
                "image": ["41", 0],
                "upscale_method": "lanczos",
                "width": 1456,
            },
        }
        for node_id in (
            "170:153",
            "170:154",
            "170:155",
            "170:163",
            "170:164",
            "170:165",
            "170:166",
            "170:167",
            "170:168",
        ):
            graph.pop(node_id)
        graph["170:169"]["inputs"].update(
            {"cfg": 4, "model": ["170:152", 0], "steps": 40}
        )
    else:
        raw = json.loads(template.read_bytes())
        for node in raw["nodes"]:
            if node["id"] in {92, 94}:
                node["mode"] = 0
            if node["id"] in {75, 9}:
                node["mode"] = 4
        graph = SubgraphUiWorkflowConverter(raw).convert()
        graph["92:107"]["inputs"]["unet_name"] = "flux-2-klein-4b.safetensors"
        graph["92:111"] = {
            "_meta": {"title": "Exact request size"},
            "class_type": "ImageScale",
            "inputs": {
                "crop": "disabled",
                "height": 720,
                "image": ["76", 0],
                "upscale_method": "lanczos",
                "width": 1456,
            },
        }
        graph["92:86"] = {
            "_meta": {"title": "Negative prompt"},
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["92:108", 0], "text": ""},
        }
    return json.dumps(
        graph, ensure_ascii=False, sort_keys=True, indent=2
    ).encode("utf-8") + b"\n"


def _gpu_preflight() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,memory.free",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": result.returncode,
        "rows": [line.strip() for line in result.stdout.splitlines() if line.strip()],
        "stderr": result.stderr.strip(),
    }


def check(args: argparse.Namespace) -> dict[str, Any]:
    comfy_root = args.comfy_root.resolve(strict=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=comfy_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    template_root = _template_root()
    official = {
        "qwen": template_root / args.qwen_official_template,
        "flux": template_root / args.flux_official_template,
    }
    official_hashes = {lane: _sha256(path) for lane, path in official.items()}
    inventory = _folder_inventory(comfy_root)
    profiles = {
        lane: load_local_image_execution_profile(path, artifact_root=REPO_ROOT)
        for lane, path in PROFILE_PATHS.items()
    }
    component_roots = {
        "diffusion": comfy_root / "models/diffusion_models",
        "text_encoder": comfy_root / "models/text_encoders",
        "vae": comfy_root / "models/vae",
    }
    component_checks: dict[str, list[dict[str, Any]]] = {}
    for lane, profile in profiles.items():
        checks = []
        for component in profile.components:
            path = (component_roots[component.role] / component.filename).resolve(
                strict=True
            )
            checks.append(
                {
                    "role": component.role,
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "expected_size_bytes": component.size_bytes,
                    "sha256": _sha256(path),
                    "expected_sha256": component.sha256,
                }
            )
        component_checks[lane] = checks
        workflow = load_workflow_template(REPO_ROOT / profile.workflow_path)
        validate_api_workflow(workflow)
        load_local_image_binding((REPO_ROOT / profile.binding_path).read_bytes())
    required = {
        item.name for profile in profiles.values() for item in profile.required_nodes
    }
    disk = shutil.disk_usage(comfy_root)
    ram_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    import torch

    lane_component_bytes = {
        lane: sum(item.size_bytes for item in profile.components)
        for lane, profile in profiles.items()
    }
    report = {
        "schema": "ai-video-p7.1-comfy-compatibility/1",
        "network_used": False,
        "comfy_root": str(comfy_root),
        "comfy_commit": commit,
        "expected_comfy_commit": EXPECTED_COMFY_COMMIT,
        "official_templates": {
            lane: {
                "path": str(path),
                "sha256": official_hashes[lane],
                "expected_sha256": OFFICIAL_TEMPLATE_HASHES[path.name],
                "derived_workflow_exact": _lineage_bytes(path, lane)
                == (REPO_ROOT / profiles[lane].workflow_path).read_bytes(),
                "declared_mutations": (
                    [
                        "diffusion filename",
                        "exact ImageScale width/height",
                        "remove disabled optional LoRA branch and pin base settings",
                    ]
                    if lane == "qwen"
                    else [
                        "enabled official edit subgraph",
                        "diffusion filename",
                        "exact ImageScale width/height",
                        "explicit negative CLIPTextEncode",
                    ]
                ),
            }
            for lane, path in official.items()
        },
        "components": component_checks,
        "inventory": inventory,
        "required_nodes": _required_nodes_present(comfy_root, required),
        "disk": {
            "free_bytes": disk.free,
            "minimum_free_bytes": 200 * GIB,
            "p7_1_component_bytes": sum(
                item.size_bytes
                for profile in profiles.values()
                for item in profile.components
            ),
            "hard_cap_bytes": 160 * GIB,
            "qwen_budget_bytes": 90 * GIB,
            "flux_budget_bytes": 40 * GIB,
            "reserve_bytes": 30 * GIB,
            "lane_component_bytes": lane_component_bytes,
        },
        "host": {
            "ram_total_bytes": ram_bytes,
            "torch_version": torch.__version__,
            "torch_cuda_version": torch.version.cuda,
            "gpu": _gpu_preflight(),
        },
    }
    blockers = []
    if commit != EXPECTED_COMFY_COMMIT:
        blockers.append("comfy_commit_mismatch")
    if any(
        item["sha256"] != item["expected_sha256"]
        or item["size_bytes"] != item["expected_size_bytes"]
        for checks in component_checks.values()
        for item in checks
    ):
        blockers.append("component_integrity_mismatch")
    if any(item["model_kind"] == "unknown" for item in inventory["diffusion_models"]):
        blockers.append("unknown_diffusion_model")
    if not all(report["required_nodes"].values()):
        blockers.append("required_node_missing")
    if disk.free < 200 * GIB:
        blockers.append("disk_free_below_gate")
    if report["disk"]["p7_1_component_bytes"] > 160 * GIB:
        blockers.append("p7_1_component_cap_exceeded")
    if lane_component_bytes["qwen"] > 90 * GIB:
        blockers.append("qwen_component_budget_exceeded")
    if lane_component_bytes["flux"] > 40 * GIB:
        blockers.append("flux_component_budget_exceeded")
    if any(
        value["sha256"] != value["expected_sha256"]
        or not value["derived_workflow_exact"]
        for value in report["official_templates"].values()
    ):
        blockers.append("official_template_lineage_mismatch")
    report["blockers"] = blockers
    report["passed"] = not blockers
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comfy-root", type=Path, required=True)
    parser.add_argument("--qwen-official-template", required=True)
    parser.add_argument("--flux-official-template", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.output.is_absolute():
        parser.error("--output must be absolute")
    report = check(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"passed": report["passed"], "blockers": report["blockers"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
