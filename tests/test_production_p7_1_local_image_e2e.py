from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.comfy_client import JobResult, JobStatus
from ai_video.production.comfy_image import (
    ComfyLocalImageProvider,
    LocalImageExecutionProfile,
    load_local_image_execution_profile,
)
from ai_video.production.image import ImageGenerationRequest
from ai_video.production.paths import canonical_image_execution_profile_path
from ai_video.production.project import load_production_project
from ai_video.production.models import StateCommitStatus
from ai_video.production.state_commit import ProductionStateCommitter
import production_project_factory as project_factory
from test_production_state_commit import (
    make_image_call_bundle,
    make_image_provider_result,
)


FIXTURES = Path(__file__).parent / "fixtures/p7_1"
ROOT = Path(__file__).parents[1]
REAL_QWEN_PROFILE = ROOT / "workflows/profiles/p7_1_qwen_image_edit_2511.json"


def _profile() -> LocalImageExecutionProfile:
    return load_local_image_execution_profile(
        FIXTURES / "qwen_profile.json",
        artifact_root=ROOT,
    )


def _runtime_profile(root: Path) -> LocalImageExecutionProfile:
    source = load_local_image_execution_profile(
        REAL_QWEN_PROFILE, artifact_root=ROOT
    )
    components = []
    for item in source.components:
        directory = {
            "diffusion": "diffusion_models",
            "text_encoder": "text_encoders",
            "vae": "vae",
            "lora": "loras",
        }[item.role]
        path = root / "comfy/models" / directory / item.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"e2e-{item.role}".encode()
        path.write_bytes(payload)
        components.append(
            item.model_copy(
                update={
                    "size_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        )
    values = source.model_dump(
        mode="python", exclude={"profile_content_hash"}
    )
    values.update(components=tuple(components), min_width=1, min_height=1)
    return LocalImageExecutionProfile.create(**values)


def _local_bundle(root: Path, profile: LocalImageExecutionProfile):
    request, _, _ = make_image_call_bundle(root)
    values = request.model_dump(
        mode="json",
        exclude={"request_id", "request_fingerprint", "output_asset_id"},
    )
    values.update(provider_kind="comfyui_local", model_id=profile.profile_id)
    local_request = ImageGenerationRequest.create(**values)
    from ai_video.production.image import (
        ImageGenerationAuthorization,
        ImageGenerationPreview,
    )

    loaded = load_production_project(root / "project.yaml")
    assets = {item.asset_id: item for item in loaded.registry.assets}
    preview = ImageGenerationPreview.create(
        request=local_request,
        reference_total_bytes=sum(
            assets[item.asset_id].size_bytes for item in local_request.references
        ),
    )
    authorization = ImageGenerationAuthorization.create(
        request=local_request,
        preview=preview,
        usage_license="fixture-only",
        policy_receipt_id="fixture-local-image-policy",
    )
    return local_request, preview, authorization


def test_local_profile_is_required_and_persisted_in_exact_r1_r2(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    profile = _profile()
    request, preview, authorization = _local_bundle(tmp_path, profile)
    writer = ProductionStateCommitter(tmp_path)

    with pytest.raises(AiVideoError) as exc_info:
        writer.begin_image_generation(request, preview, authorization)
    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID

    r1 = writer.begin_image_generation(
        request,
        preview,
        authorization,
        execution_profile=profile,
    )
    profile_path = canonical_image_execution_profile_path(
        profile.profile_content_hash
    )
    assert (tmp_path / profile_path).read_bytes().endswith(b"\n")
    r1_paths = (
        Path(f"state/images/requests/{request.request_fingerprint}.json"),
        Path(f"state/images/previews/{preview.preview_fingerprint}.json"),
        Path(
            "state/images/authorizations/"
            f"{authorization.authorization_fingerprint}.json"
        ),
        profile_path,
    )
    pairs = sorted(
        (path.as_posix(), hashlib.sha256((tmp_path / path).read_bytes()).hexdigest())
        for path in r1_paths
    )
    assert r1.attempts[-1].candidate_artifacts_hash == hashlib.sha256(
        json.dumps(pairs, separators=(",", ":")).encode()
    ).hexdigest()

    writer.record_image_submit_intent(
        request,
        preview,
        authorization,
        execution_profile=profile,
    )


def test_local_profile_tamper_blocks_submit_before_permit_mint(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    profile = _profile()
    request, preview, authorization = _local_bundle(tmp_path, profile)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_image_generation(
        request,
        preview,
        authorization,
        execution_profile=profile,
    )
    path = tmp_path / canonical_image_execution_profile_path(
        profile.profile_content_hash
    )
    path.write_bytes(path.read_bytes() + b" ")

    with pytest.raises(AiVideoError) as exc_info:
        writer.record_image_submit_intent(
            request,
            preview,
            authorization,
            execution_profile=profile,
        )
    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID


def test_local_preflight_failure_leaves_no_r1_or_provider_call(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_p7_image_generation_base(tmp_path)
    profile = _profile()
    request, preview, authorization = _local_bundle(tmp_path, profile)
    manifest_path = tmp_path / "state/manifest.json"
    before = manifest_path.read_bytes()

    class _Provider:
        calls = 0

        def preflight(self, candidate):
            raise AiVideoError(
                ErrorCode.IMAGE_REQUEST_INVALID,
                "fixture component mismatch",
                retryable=False,
            )

        def generate(self, *args):
            self.calls += 1
            raise AssertionError("provider must not run")

    provider = _Provider()
    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).generate_image_asset(
            request,
            preview,
            authorization,
            provider,
            execution_profile=profile,
        )
    assert exc_info.value.code is ErrorCode.IMAGE_REQUEST_INVALID
    assert manifest_path.read_bytes() == before
    assert provider.calls == 0
    assert not (tmp_path / "state/images/requests").exists()


def test_local_profile_is_part_of_nine_artifact_activation_and_replay(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    base_inputs = project_factory.make_p7_image_generation_base(tmp_path)
    profile = _profile()
    request, preview, authorization = _local_bundle(tmp_path, profile)
    calls = 0

    class _Provider:
        def preflight(self, candidate):
            assert candidate == request

        def generate(self, candidate, candidate_authorization, permit):
            nonlocal calls
            calls += 1
            assert permit._consume_image_generation_permit(
                request_fingerprint=candidate.request_fingerprint
            )
            return make_image_provider_result(
                candidate,
                candidate_authorization,
                project_factory._p7_png(),
            )

    writer = ProductionStateCommitter(
        tmp_path,
        image_candidate_preparer=project_factory.make_p7_image_candidate_preparer(
            base_inputs
        ),
    )
    first = writer.generate_image_asset(
        request,
        preview,
        authorization,
        _Provider(),
        execution_profile=profile,
    )
    attempt = first.attempts[-1]
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.manifest == first
    assert len(
        {
            canonical_image_execution_profile_path(profile.profile_content_hash),
            attempt.candidate_project.path,
            attempt.candidate_registry.path,
            attempt.candidate_dependency_graph.path,
        }
    ) == 4

    replay = ProductionStateCommitter(
        tmp_path,
        image_candidate_preparer=project_factory.make_p7_image_candidate_preparer(
            base_inputs
        ),
    ).generate_image_asset(
        request,
        preview,
        authorization,
        _Provider(),
        execution_profile=profile,
    )
    assert replay == first
    assert calls == 1


def test_local_r2_recovery_is_no_network_and_never_remints_permit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    profile = _profile()
    request, preview, authorization = _local_bundle(tmp_path, profile)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_image_generation(
        request,
        preview,
        authorization,
        execution_profile=profile,
    )
    writer.record_image_submit_intent(
        request,
        preview,
        authorization,
        execution_profile=profile,
    )

    def deny_socket(*args, **kwargs):
        raise AssertionError("recovery must not open a socket")

    monkeypatch.setattr(socket, "socket", deny_socket)
    report = writer.recover()
    recovered = load_production_project(tmp_path / "project.yaml").manifest

    assert report.manifest_revision_after == recovered.manifest_revision
    assert recovered.attempts[-1].status is StateCommitStatus.OUTCOME_UNKNOWN

    class _Provider:
        calls = 0

        def generate(self, *args):
            self.calls += 1
            raise AssertionError("recovery replay must not call Provider")

    provider = _Provider()
    with pytest.raises(AiVideoError) as exc_info:
        writer.generate_image_asset(
            request,
            preview,
            authorization,
            provider,
            execution_profile=profile,
        )
    assert exc_info.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert provider.calls == 0


@pytest.mark.parametrize("failure", ["history_timeout", "png_fetch"])
def test_comfy_failure_after_submit_recovers_without_transport_or_remint(
    tmp_path: Path, failure: str
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_p7_image_generation_base(tmp_path)
    profile = _runtime_profile(tmp_path)
    request, preview, authorization = _local_bundle(tmp_path, profile)
    loaded = load_production_project(tmp_path / "project.yaml")
    reference_paths = {
        item.asset_id: loaded.asset_paths[item.asset_id] for item in request.references
    }

    class _Transport:
        def __init__(self) -> None:
            self.object_info_calls = 0
            self.prompt_calls = 0
            self.fetch_calls = 0

        def get_object_info(self):
            self.object_info_calls += 1
            names = {
                "CFGNorm",
                "CLIPLoader",
                "ComfySwitchNode",
                "FluxKontextMultiReferenceLatentMethod",
                "ImageScale",
                "KSampler",
                "LoadImage",
                "LoraLoaderModelOnly",
                "ModelSamplingAuraFlow",
                "PrimitiveBoolean",
                "PrimitiveFloat",
                "PrimitiveInt",
                "SaveImage",
                "TextEncodeQwenImageEditPlus",
                "UNETLoader",
                "VAEDecode",
                "VAEEncode",
                "VAELoader",
            }
            return {name: {} for name in names}

        def upload_image(self, path):
            return Path(path).name

        def submit_prompt(self, workflow):
            self.prompt_calls += 1
            return "accepted-prompt"

        def poll_job(self, prompt_id, **kwargs):
            if failure == "history_timeout":
                return JobResult(JobStatus.TIMEOUT, prompt_id)
            return JobResult(
                JobStatus.COMPLETED,
                prompt_id,
                history={
                    "outputs": {
                        "9": {
                            "images": [
                                {
                                    "filename": "result.png",
                                    "subfolder": "",
                                    "type": "output",
                                }
                            ]
                        }
                    }
                },
            )

        def fetch_artifact_bytes(self, **kwargs):
            self.fetch_calls += 1
            raise AiVideoError(
                ErrorCode.COMFY_OUTPUT_MISSING,
                "fixture fetch failed",
                retryable=True,
            )

    transport = _Transport()
    provider = ComfyLocalImageProvider(
        profile,
        artifact_root=ROOT,
        comfy_root=tmp_path / "comfy",
        reference_root=tmp_path,
        reference_resolver=lambda reference: reference_paths[reference.asset_id],
        transport=transport,
        commit_resolver=lambda: profile.comfyui_commit,
    )
    writer = ProductionStateCommitter(tmp_path)

    with pytest.raises(AiVideoError) as exc_info:
        writer.generate_image_asset(
            request,
            preview,
            authorization,
            provider,
            execution_profile=profile,
        )
    assert exc_info.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    calls = (transport.object_info_calls, transport.prompt_calls, transport.fetch_calls)
    assert calls == (1, 1, 0 if failure == "history_timeout" else 1)
    assert writer.recover().manifest_revision_after >= 1

    with pytest.raises(AiVideoError) as replay_error:
        writer.generate_image_asset(
            request,
            preview,
            authorization,
            provider,
            execution_profile=profile,
        )
    assert replay_error.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert (transport.object_info_calls, transport.prompt_calls, transport.fetch_calls) == calls
