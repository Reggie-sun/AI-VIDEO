from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from ai_video.errors import AiVideoError  # noqa: E402
from ai_video.production.comfy_image import (  # noqa: E402
    ComfyLocalImageProvider,
    load_local_image_execution_profile,
    validate_loopback_endpoint,
)
from ai_video.production.image import (  # noqa: E402
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
)
from ai_video.production.project import load_production_project  # noqa: E402
from ai_video.production.state_commit import ProductionStateCommitter  # noqa: E402
import production_project_factory as project_factory  # noqa: E402
from test_production_p7_1_local_image_e2e import _local_bundle  # noqa: E402


PROFILES = {
    "qwen_image_edit_2511": REPO_ROOT
    / "workflows/profiles/p7_1_qwen_image_edit_2511.json",
    "flux2_klein_4b": REPO_ROOT
    / "workflows/profiles/p7_1_flux2_klein_4b.json",
}


def _gpu_snapshot() -> list[str]:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _request_for_profile(root: Path, profile, lane: str):
    request, _, _ = _local_bundle(root, profile)
    values = request.model_dump(
        mode="json",
        exclude={"request_id", "request_fingerprint", "output_asset_id"},
    )
    values["attempt_id"] = f"p7-1-live-{lane}"
    values["parameters"] = {
        **values["parameters"],
        "width": 1456,
        "height": 720,
    }
    request = ImageGenerationRequest.create(**values)
    loaded = load_production_project(root / "project.yaml")
    assets = {item.asset_id: item for item in loaded.registry.assets}
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=sum(
            assets[item.asset_id].size_bytes for item in request.references
        ),
    )
    authorization = ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="local-smoke-fixture-only",
        policy_receipt_id="p7-1-explicit-live-local-smoke",
    )
    return request, preview, authorization


class _CountingProvider:
    def __init__(self, provider: ComfyLocalImageProvider) -> None:
        self.provider = provider
        self.calls = 0

    def generate(self, request, authorization, permit):
        self.calls += 1
        return self.provider.generate(request, authorization, permit)

    def preflight(self, request):
        return self.provider.preflight(request)


def _run_lane(
    root: Path, lane: str, endpoint: str, comfy_root: Path
) -> dict[str, object]:
    root.mkdir(parents=True)
    project_factory.write_production_project(root)
    base_inputs = project_factory.make_p7_image_generation_base(root)
    profile = load_local_image_execution_profile(PROFILES[lane], artifact_root=REPO_ROOT)
    request, preview, authorization = _request_for_profile(root, profile, lane)
    loaded = load_production_project(root / "project.yaml")
    reference_paths = {
        item.asset_id: loaded.asset_paths[item.asset_id]
        for item in request.references
    }
    provider = _CountingProvider(
        ComfyLocalImageProvider(
            profile,
            artifact_root=REPO_ROOT,
            comfy_root=comfy_root,
            reference_root=root,
            reference_resolver=lambda reference: reference_paths[reference.asset_id],
            endpoint=endpoint,
        )
    )
    writer = ProductionStateCommitter(
        root,
        image_candidate_preparer=project_factory.make_p7_image_candidate_preparer(
            base_inputs
        ),
    )
    before_gpu = _gpu_snapshot()
    started = time.monotonic()
    try:
        first = writer.generate_image_asset(
            request,
            preview,
            authorization,
            provider,
            execution_profile=profile,
        )
        calls_after_first = provider.calls
        replay = writer.generate_image_asset(
            request,
            preview,
            authorization,
            provider,
            execution_profile=profile,
        )
    except AiVideoError as exc:
        recovery = writer.recover()
        return {
            "lane": lane,
            "passed": False,
            "error_code": exc.code.value,
            "error_message": exc.user_message,
            "provider_calls": provider.calls,
            "recovery_revision": recovery.manifest_revision_after,
        }
    attempt = first.attempts[-1]
    asset = next(
        item
        for item in load_production_project(root / "project.yaml").registry.assets
        if item.asset_id == request.output_asset_id
    )
    return {
        "lane": lane,
        "passed": replay == first and calls_after_first == 1 and provider.calls == 1,
        "profile_id": profile.profile_id,
        "comfyui_commit": profile.comfyui_commit,
        "workflow_sha256": profile.workflow_sha256,
        "model_component_sha256": [item.sha256 for item in profile.components],
        "provider_request_id": attempt.provider_request_id,
        "elapsed_milliseconds": int((time.monotonic() - started) * 1000),
        "provider_calls_first": calls_after_first,
        "provider_calls_after_replay": provider.calls,
        "output_sha256": asset.sha256,
        "output_size_bytes": asset.size_bytes,
        "gpu_before": before_gpu,
        "gpu_after": _gpu_snapshot(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--comfy-root", type=Path, required=True)
    parser.add_argument("--comfy-url", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--max-provider-calls", type=int, required=True)
    parser.add_argument("--max-output-count-per-profile", type=int, required=True)
    parser.add_argument("--replay-once", action="store_true")
    parser.add_argument("--require-loopback", action="store_true")
    parser.add_argument("--confirm-live-local-generation", action="store_true")
    args = parser.parse_args()
    if not args.confirm_live_local_generation:
        parser.error("--confirm-live-local-generation is required")
    if not args.replay_once or not args.require_loopback:
        parser.error("--replay-once and --require-loopback are required")
    endpoint = validate_loopback_endpoint(args.comfy_url)
    root = args.project_root
    comfy_root = args.comfy_root
    if not root.is_absolute() or ".." in root.parts:
        parser.error("--project-root must be a clean absolute path")
    if root.exists() and any(root.iterdir()):
        parser.error("--project-root must not contain existing files")
    if not comfy_root.is_absolute() or not comfy_root.is_dir():
        parser.error("--comfy-root must be an existing absolute directory")
    lanes = tuple(item.strip() for item in args.profiles.split(",") if item.strip())
    if not lanes or any(item not in PROFILES for item in lanes):
        parser.error("--profiles contains an unsupported lane")
    if args.max_provider_calls != len(lanes) or args.max_output_count_per_profile != 1:
        parser.error("live smoke caps must be exactly one call/output per profile")
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for lane in lanes:
        result = _run_lane(root / lane, lane, endpoint, comfy_root)
        results.append(result)
        if not result["passed"]:
            break
    report = {
        "schema": "ai-video-p7.1-live-local-smoke/1",
        "endpoint": endpoint,
        "browser_used": False,
        "remote_used": False,
        "results": results,
        "passed": len(results) == len(lanes) and all(item["passed"] for item in results),
    }
    (root / "p7-1-live-smoke-report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
