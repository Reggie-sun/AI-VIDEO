from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from ai_video.comfy_client import JobResult, JobStatus
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import (
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production.shot_continuity_m0_qualification import (
    M0ValidationPreflightSnapshot,
)
from ai_video.production.shot_continuity_source_qualification import (
    ShotContinuitySourceQualificationCaller,
    ShotContinuitySourceQualificationProfile,
    ShotContinuitySourceQualificationProvider,
    SourceQualificationNodeSchemaSeal,
    derive_source_qualification_seed,
    load_source_qualification_profile,
)
from ai_video.production.shot_continuity_source_schema import SOURCE_REQUIRED_NODES
from ai_video.production.shot_continuity_source_stack import (
    load_shot_continuity_source_execution_sources,
)
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    ResolvedVideoGenerationRequest,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoTaskState,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/"
    "minimax_h3_fl2va_rainy_station_source_v1_profile.json"
)
NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
PROMPT = (
    "For the target video, <Picture 1> is fully referenced as the exact first "
    "frame and <Picture 2> is fully referenced as the exact last frame.\n\n"
    "integrated_multimodal_description: [Shot 1] One continuous live-action, "
    "photorealistic cinematic medium right-facing side-profile shot on the same "
    "rain-soaked railway platform at blue hour. The exact same lone adult East "
    "Asian woman with a short blunt black bob, mustard-yellow hooded raincoat, "
    "black trousers, black boots and the same red cross-body leather satchel "
    "walks steadily screen-right toward the clock. A chest-height natural-"
    "perspective camera tracks parallel at slow constant speed, preserving a "
    "level horizon and stable body scale. Begin at the exact supplied first "
    "frame and finish at the exact supplied last frame while she remains mid-"
    "stride with continuing gait and satchel motion. Exactly one person; no cut, "
    "extra person, axis reversal, teleport, wardrobe change, random zoom, jitter, "
    "text or logo.\n"
    "overall_soundscape: Steady rain, measured synchronized boot footsteps, "
    "restrained station ambience and small physical leather-satchel movement.\n"
    "non_diegetic_music: No non-diegetic music."
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _p0(source_stack_hash: str) -> M0ValidationPreflightSnapshot:
    return M0ValidationPreflightSnapshot(
        candidate_label="m0",
        qualification_receipt_hash=(
            "25145d177de07384bb4594e53023563e809a3f1bdcdb7ff294acd1cff5ae1e91"
        ),
        execution_stack_hash=(
            "8f9661c358162544a3cefd0f7ff4483063658fcb37de09f301ef7fe2500039d2"
        ),
        source_execution_stack_hash=source_stack_hash,
        profile_hash=(
            "9bf6588c04712887b117a8fd3c7496c15b5667b112d8cea750047928ccc36517"
        ),
        compiler_hash=(
            "e2ba38bb110e26a5221a5582ea19f777752a1946ffacbe31b1445073d1530d19"
        ),
        workflow_hash=(
            "963bd91ad81ca102053deb08b29a7aa8fb6849a6256a78ccbfbc6138d7a855d2"
        ),
        validation_set_hash=(
            "6685f2661de2e0415bd42241cc6efec1c23127717c0a96e353509659e4569ab4"
        ),
        policy_hashes=(
            "8f8033495b92a4f234279e6f6da587f039fdc087c44312e04884ae4ded924d28",
            "f82a280d9b9a9d050e92b9b7e12ad5c13ab365ee7e7113717800a163b93d8fd8",
            "3b3623932abbe5edfcb6307c4750798402a7858e61b7e75babfe30e2d229531b",
        ),
        qualification_input_hashes=(
            ("inventory", "4238c5f19589fac49c78481e2e1a5b996a0680019e907ed1eac5f95d2c64add1"),
            ("calibration_fixture", "0c03c4e59122a3331860b890eecf1af9b99a003b1fb24c3c2787235d6ba20cdb"),
            ("rubric", "25cd722cffe804273a797a947d60d5c7530a85d1f4f30f4754261b4586243364"),
            ("effect_budget", "e5ac6842f1c0b35744f8df90994986b37e22ee033047d1c667e0abccca562200"),
            ("human_freeze", "53435443c6a17c201f41029026c568ab1bb7f23ae4f0ca0c1e7d5d45e71b2d9e"),
        ),
    )


def _profile(
    sources: Any,
    p0: M0ValidationPreflightSnapshot,
) -> ShotContinuitySourceQualificationProfile:
    return ShotContinuitySourceQualificationProfile.create(
        schema_version="1",
        status="qualification_only",
        provider_name="comfy-local-h3",
        provider_kind="minimax_h3_fl2va",
        deployment_identity="loopback-127.0.0.1-8188",
        loopback_endpoint="http://127.0.0.1:8188",
        model_id="minimax-h3-fl2va",
        capability_id="minimax-h3-fl2va-local-v1",
        candidate_id="minimax-h3-fl2va-rainy-station-source-v1",
        contract_version="1",
        provider_profile_sha256=sources.profile.profile_content_hash,
        adapter_compiler_id="comfy-local-h3-video-compiler",
        adapter_compiler_version="1",
        source_execution_stack_hash=sources.materialized_stack.execution_stack_hash,
        source_profile_hash=sources.materialization.profile_hash,
        source_compiler_hash=sources.materialization.compiler_hash,
        source_workflow_hash=sources.materialization.workflow_hash,
        source_node_schema_status="sealed",
        source_node_schema_seals=tuple(
            SourceQualificationNodeSchemaSeal(
                node_name=name,
                schema_sha256="9" * 64,
            )
            for name in (
                "UNETLoader", "CLIPLoader", "VAELoader",
                "MiniMaxH3ImageToVideo", "RandomNoise", "BasicGuider",
                "KSamplerSelect", "BasicScheduler", "SamplerCustomAdvanced",
                "VAEDecode", "VAEDecodeAudio", "CreateVideo", "SaveVideo",
                "LoadImage",
            )
        ),
        p0_qualification_receipt_hash=p0.qualification_receipt_hash,
        m0_execution_stack_hash=p0.execution_stack_hash,
        m0_profile_hash=p0.profile_hash,
        m0_compiler_hash=p0.compiler_hash,
        m0_workflow_hash=p0.workflow_hash,
        p0_validation_set_hash=p0.validation_set_hash,
        p0_policy_hashes=p0.policy_hashes,
        p0_input_hashes=p0.qualification_input_hashes,
        project_content_hash=(
            "b89c1e18f1085c6dab85d070e363fe39eb2e60b3fdd84c4e73738ebae9a1a3ca"
        ),
        registry_content_hash=(
            "b292cb0b35226f6201228dbc0caa62d54823f4d03040af9fa218f9666af732e9"
        ),
        target_shot_id="rainy-station-3",
        target_shot_revision=1,
        target_shot_content_hash=(
            "5ae7704ac1b2b048da8f97f1c5f07535480ea77e0ac0e96c513c81814eb083d1"
        ),
        target_asset_role="approved_endpoint",
        output_asset_id="video-shot-rainy-station-3-source-v1",
        first_frame_asset_id=(
            "image-import-e8b1d85d4e599d584ca63fb503b86515fd4b8dd8174ac0a6c304ad3c167d3163"
        ),
        first_frame_sha256=(
            "c50517a17313402ef271694ea058d6c92b0b750c4b854e39858bdaf5d73c5768"
        ),
        first_frame_size_bytes=1984532,
        first_frame_width=1659,
        first_frame_height=948,
        last_frame_asset_id=(
            "image-import-550b07e0ee96c4d8889b906292ad76f41c66adfbfd1dc80bbe9b9cf6ba290a5f"
        ),
        last_frame_sha256=(
            "03f4c5ebd177486dd65b21d61901f2296ef7255f12819c66099ef93815a7fc7c"
        ),
        last_frame_size_bytes=1966518,
        last_frame_width=1659,
        last_frame_height=948,
        prompt=PROMPT,
        seed_derivation="source-qualification-closure-sha256-low63-v1",
        width=1344,
        height=768,
        frame_count=124,
        fps=24,
        native_audio=True,
        output_container="mp4",
        remote_provider_enabled=False,
        cloud_fallback_enabled=False,
        retry_enabled=False,
    )


def test_source_profile_accepts_exact_revised_target_shot_identity() -> None:
    sources = load_shot_continuity_source_execution_sources(artifact_root=REPO_ROOT)
    base = _profile(
        sources,
        _p0(sources.materialized_stack.execution_stack_hash),
    )
    values = base.model_dump(mode="python")
    values.update(
        project_content_hash="8" * 64,
        target_shot_revision=2,
        target_shot_content_hash="7" * 64,
    )
    for key in (
        "prompt_sha256",
        "sealed_seed",
        "output_contract_hash",
        "profile_content_hash",
    ):
        values.pop(key, None)

    revised = ShotContinuitySourceQualificationProfile.create(**values)

    assert revised.target_shot_revision == 2
    assert revised.target_shot_content_hash == "7" * 64
    assert revised.project_content_hash == "8" * 64
    assert revised.sealed_seed != base.sealed_seed
    assert revised.profile_content_hash != base.profile_content_hash


def test_typed_resolved_request_uses_canonical_shot_scope_identity() -> None:
    import ai_video.production.shot_continuity_source_qualification as module

    sources = load_shot_continuity_source_execution_sources(artifact_root=REPO_ROOT)
    profile = _profile(sources, _p0(sources.materialized_stack.execution_stack_hash))
    graph_hash = "d" * 64
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        duration_seconds=None,
        frame_count=profile.frame_count,
        dimension_mode="exact",
        width=profile.width,
        height=profile.height,
        resolution_label="h3_native",
        ratio="adaptive",
        fps=profile.fps,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    request = VideoGenerationRequest.create(
        generation_id="source-generation-typed-v1",
        provider_name=profile.provider_name,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        provider_profile=ProviderProfilePointer(
            profile_id=profile.candidate_id,
            profile_version="v1",
            profile_path=Path(
                f"provider-profiles/{profile.provider_profile_sha256}.json"
            ),
            profile_sha256=profile.provider_profile_sha256,
        ),
        requirement_hash="1" * 64,
        provider_bound_request_hash="2" * 64,
        adapter_compiler_id=profile.adapter_compiler_id,
        adapter_compiler_version=profile.adapter_compiler_version,
        adapter_compiler_hash=profile.source_compiler_hash,
        execution_stack_hash=profile.source_execution_stack_hash,
        target_shot_id=profile.target_shot_id,
        target_shot_revision=profile.target_shot_revision,
        target_shot_content_hash=profile.target_shot_content_hash,
        target_asset_role=profile.target_asset_role,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text=profile.prompt,
        negative_prompt_text="",
        image_bindings=(
            VideoImageReferenceBinding(
                role="first_frame",
                asset_id=profile.first_frame_asset_id,
                asset_sha256=profile.first_frame_sha256,
                mime_type="image/png",
                width=profile.first_frame_width,
                height=profile.first_frame_height,
                size_bytes=profile.first_frame_size_bytes,
            ),
            VideoImageReferenceBinding(
                role="last_frame",
                asset_id=profile.last_frame_asset_id,
                asset_sha256=profile.last_frame_sha256,
                mime_type="image/png",
                width=profile.last_frame_width,
                height=profile.last_frame_height,
                size_bytes=profile.last_frame_size_bytes,
            ),
        ),
        seal_terminal_frame=True,
        output_requirement=output,
        seed=profile.sealed_seed,
        base_project=ProjectSnapshotPointer(
            path=Path(
                "state/projects/project.1."
                f"{profile.project_content_hash}.yaml"
            ),
            revision=1,
            content_hash=profile.project_content_hash,
            file_sha256="3" * 64,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{profile.registry_content_hash}.json"),
            revision_id=profile.registry_content_hash,
            content_hash=profile.registry_content_hash,
            file_sha256="4" * 64,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            revision_id=graph_hash,
            content_hash=graph_hash,
            path=Path(f"state/dependency_graph.{graph_hash}.json"),
            file_sha256="5" * 64,
        ),
        input_artifact_ids=(
            profile.first_frame_asset_id,
            profile.last_frame_asset_id,
        ),
        output_asset_id=profile.output_asset_id,
    )
    capability = VideoCapabilityVariant(
        capability_id=profile.capability_id,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        profile_version="v1",
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        output_capability=VideoOutputCapability(
            min_duration_seconds=1,
            max_duration_seconds=60,
            provider_selected_duration=False,
            timing_modes=("frame_count",),
            frame_count_min=1,
            frame_count_max=1000,
            frame_count_step=1,
            frame_count_remainder=0,
            dimension_modes=("exact",),
            min_width=1,
            max_width=4096,
            min_height=1,
            max_height=4096,
            dimension_multiple=1,
            resolution_labels=("h3_native",),
            ratios=("adaptive",),
            fps_values=(profile.fps,),
            containers=("mp4",),
            native_audio_options=(True,),
        ),
        allowed_image_roles=("first_frame", "last_frame"),
        required_first_frame=True,
        max_reference_count=0,
        allowed_image_mime_types=("image/png",),
        max_image_bytes=104_857_600,
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=False,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    resolved = ResolvedVideoGenerationRequest.create(
        request=request,
        capability=capability,
        effective_output=output,
        effective_seed=profile.sealed_seed,
        effective_negative_prompt_text="",
    )

    module._validate_request(resolved, profile, sources)


class _Permit:
    def __init__(self) -> None:
        self.consumed = False

    def _consume_local_video_submit_permit(
        self,
        *,
        intent_fingerprint: str,
        request_fingerprint: str,
    ) -> bool:
        del intent_fingerprint, request_fingerprint
        if self.consumed:
            return False
        self.consumed = True
        return True


class _Transport:
    deployment_identity = "loopback-127.0.0.1-8188"
    base_url = "http://127.0.0.1:8188"

    def __init__(self) -> None:
        self.object_info: dict[str, object] = {"schemas": "exact"}
        self.object_info_calls = 0
        self.uploads = []
        self.workflows = []
        self.submit_error: Exception | None = None
        self.job_result = JobResult(
            JobStatus.COMPLETED,
            "source-prompt-1",
            history={
                "outputs": {
                    "14": {
                        "videos": [
                            {
                                "filename": "source-output.mp4",
                                "subfolder": "video",
                                "type": "output",
                            }
                        ]
                    }
                }
            },
        )
        self.artifact_bytes = b"\x00\x00\x00\x14ftypisomsource-video"
        self.poll_calls: list[str] = []
        self.fetch_calls: list[dict[str, str]] = []
        self.before_first_upload: Callable[[], None] | None = None
        self.permit_probe: Callable[[], bool] | None = None

    def get_object_info(self) -> dict[str, object]:
        self.object_info_calls += 1
        return self.object_info

    def upload_input(self, item: Any) -> str:
        if self.permit_probe is not None:
            assert self.permit_probe() is True
        if not self.uploads and self.before_first_upload is not None:
            callback = self.before_first_upload
            self.before_first_upload = None
            callback()
        self.uploads.append(item)
        return f"uploaded-{len(self.uploads)}.png"

    def submit_prompt(self, workflow: dict[str, Any]) -> str:
        self.workflows.append(workflow)
        if self.submit_error is not None:
            raise self.submit_error
        return "source-prompt-1"

    def poll_job(self, prompt_id: str, **_: object) -> JobResult:
        self.poll_calls.append(prompt_id)
        return self.job_result

    def fetch_artifact_bytes(self, **locator: str) -> bytes:
        self.fetch_calls.append(locator)
        return self.artifact_bytes


class _Committer:
    def __init__(self, request: Any, source_stack: Any) -> None:
        self.request = request
        self.source_stack = source_stack
        self.attempt: Any | None = None
        self.start_writes = 0
        self.intent_writes = 0
        self.result_writes = 0
        self.failure_writes = 0
        self.permit = _Permit()

    def reopen_p0_qualification_source_stacks(
        self, *, require_materialized: bool = False
    ) -> tuple[Any, ...]:
        assert require_materialized
        return (self.source_stack,)

    def begin_video_generation(self, *, attempt_id: str, request: Any) -> Any:
        if self.attempt is not None:
            raise ValueError("duplicate attempt")
        self.start_writes += 1
        self.request = request
        self.attempt = SimpleNamespace(
            attempt_id=attempt_id,
            status=StateCommitStatus.RUNNING,
            paid_provider_state=None,
            video_generation_state=SimpleNamespace(
                phase=VideoAttemptPhase.REQUEST,
                request=SimpleNamespace(path=Path("request.json")),
            ),
        )
        return SimpleNamespace()

    def _read_manifest(self) -> Any:
        return SimpleNamespace(attempts=() if self.attempt is None else (self.attempt,))

    def _video_attempt(self, manifest: Any, attempt_id: str) -> Any:
        del manifest
        assert self.attempt is not None and self.attempt.attempt_id == attempt_id
        return self.attempt

    def _reopen_video_request(self, pointer: Any) -> Any:
        del pointer
        return self.request

    def record_local_video_submit_intent(
        self,
        *,
        attempt_id: str,
        preview: Any,
        pre_submit_guard: Callable[[Any], None] | None = None,
    ) -> tuple[LocalVideoSubmitIntent, _Permit]:
        assert self.attempt is not None and self.attempt.attempt_id == attempt_id
        if pre_submit_guard is not None:
            pre_submit_guard(self.request)
        self.intent_writes += 1
        return (
            LocalVideoSubmitIntent.create(
                attempt_id=attempt_id,
                request=self.request,
                preview=preview,
                recorded_at=NOW,
            ),
            self.permit,
        )

    def record_local_video_submit_result(self, *, attempt_id: str, result: Any) -> None:
        del attempt_id, result
        self.result_writes += 1

    def record_video_provider_failure(
        self, *, attempt_id: str, error_code: ErrorCode, message: str
    ) -> None:
        del attempt_id, error_code, message
        self.failure_writes += 1


@dataclass
class _Case:
    caller: ShotContinuitySourceQualificationCaller
    provider: ShotContinuitySourceQualificationProvider
    committer: _Committer
    transport: _Transport
    request: Any
    profile: ShotContinuitySourceQualificationProfile
    p0_box: dict[str, M0ValidationPreflightSnapshot]
    project: Any
    paths: dict[str, Path]
    payloads: dict[str, bytes]


def _make_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> _Case:
    import ai_video.production.shot_continuity_source_qualification as module

    sources = load_shot_continuity_source_execution_sources(artifact_root=REPO_ROOT)
    p0 = _p0(sources.materialized_stack.execution_stack_hash)
    profile = _profile(sources, p0)
    p0_box = {"value": p0}
    payloads = {
        "first": b"\x89PNG\r\n\x1a\nfirst-frame",
        "last": b"\x89PNG\r\n\x1a\nlast-frame",
    }
    values = profile.model_dump(mode="python")
    values.update(
        first_frame_sha256=_sha(payloads["first"]),
        first_frame_size_bytes=len(payloads["first"]),
        last_frame_sha256=_sha(payloads["last"]),
        last_frame_size_bytes=len(payloads["last"]),
    )
    for key in ("prompt_sha256", "sealed_seed", "output_contract_hash", "profile_content_hash"):
        values.pop(key, None)
    profile = ShotContinuitySourceQualificationProfile.create(**values)
    input_root = tmp_path / "project"
    input_root.mkdir()
    paths = {"first": input_root / "first.png", "last": input_root / "last.png"}
    paths["first"].write_bytes(payloads["first"])
    paths["last"].write_bytes(payloads["last"])
    graph_hash = "d" * 64
    base_graph = SimpleNamespace(content_hash=graph_hash)
    scope_request = SimpleNamespace(
        target_shot_id=profile.target_shot_id,
        target_shot_revision=profile.target_shot_revision,
        target_shot_content_hash=profile.target_shot_content_hash,
        target_asset_role=profile.target_asset_role,
        input_artifact_ids=(profile.first_frame_asset_id, profile.last_frame_asset_id),
        base_project=SimpleNamespace(content_hash=profile.project_content_hash),
        base_registry=SimpleNamespace(content_hash=profile.registry_content_hash),
        base_dependency_graph=base_graph,
    )
    request = SimpleNamespace(
        generation_id="source-generation-1",
        provider_name=profile.provider_name,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        capability_id=profile.capability_id,
        provider_profile=SimpleNamespace(
            profile_id=profile.candidate_id,
            profile_version="v1",
            profile_sha256=profile.provider_profile_sha256,
        ),
        adapter_compiler_id=profile.adapter_compiler_id,
        adapter_compiler_version=profile.adapter_compiler_version,
        adapter_compiler_hash=profile.source_compiler_hash,
        execution_stack_hash=profile.source_execution_stack_hash,
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text=profile.prompt,
        image_bindings=(
            SimpleNamespace(
                role="first_frame", asset_id=profile.first_frame_asset_id,
                asset_sha256=profile.first_frame_sha256, mime_type="image/png",
                width=profile.first_frame_width, height=profile.first_frame_height,
                size_bytes=profile.first_frame_size_bytes,
            ),
            SimpleNamespace(
                role="last_frame", asset_id=profile.last_frame_asset_id,
                asset_sha256=profile.last_frame_sha256, mime_type="image/png",
                width=profile.last_frame_width, height=profile.last_frame_height,
                size_bytes=profile.last_frame_size_bytes,
            ),
        ),
        c4_multi_anchor_binding=None,
        continuity_binding=None,
        hard_cut_keyframe_binding=None,
        seal_terminal_frame=True,
        media_bindings=(),
        effective_seed=profile.sealed_seed,
        effective_negative_prompt_text="",
        effective_output=VideoFlexibleOutputRequirement(
            timing_mode="frame_count", duration_seconds=None, frame_count=124,
            dimension_mode="exact", width=1344, height=768,
            resolution_label="h3_native", ratio="adaptive", fps=24,
            container="mp4", mime_type="video/mp4", native_audio=True,
        ),
        target_shot_id=profile.target_shot_id,
        target_shot_revision=profile.target_shot_revision,
        target_shot_content_hash=profile.target_shot_content_hash,
        output_asset_id=profile.output_asset_id,
        activation_scope=SimpleNamespace(request=scope_request),
        resolved_generation_hash="a" * 64,
    )
    records = (
        SimpleNamespace(
            asset_id=profile.first_frame_asset_id, sha256=profile.first_frame_sha256,
            size_bytes=profile.first_frame_size_bytes, width=profile.first_frame_width,
            height=profile.first_frame_height, mime_type="image/png",
        ),
        SimpleNamespace(
            asset_id=profile.last_frame_asset_id, sha256=profile.last_frame_sha256,
            size_bytes=profile.last_frame_size_bytes, width=profile.last_frame_width,
            height=profile.last_frame_height, mime_type="image/png",
        ),
    )
    project = SimpleNamespace(
        root=input_root,
        manifest=SimpleNamespace(
            active_project=SimpleNamespace(content_hash=profile.project_content_hash),
            active_registry=SimpleNamespace(content_hash=profile.registry_content_hash),
            active_dependency_graph=base_graph,
        ),
        dependency_graph=SimpleNamespace(content_hash=graph_hash),
        project=SimpleNamespace(content_hash=profile.project_content_hash),
        registry=SimpleNamespace(content_hash=profile.registry_content_hash, assets=records),
        shots=(SimpleNamespace(
            shot_id=profile.target_shot_id, revision=profile.target_shot_revision,
            content_hash=profile.target_shot_content_hash,
        ),),
        asset_paths={
            profile.first_frame_asset_id: paths["first"],
            profile.last_frame_asset_id: paths["last"],
        },
    )
    committer = _Committer(request, sources.materialized_stack)
    transport = _Transport()
    transport.permit_probe = lambda: committer.permit.consumed
    monkeypatch.setattr(
        module, "load_source_qualification_profile",
        lambda path, artifact_root: (profile, "f" * 64),
    )
    monkeypatch.setattr(
        module, "reopen_m0_validation_preflight", lambda **kwargs: p0_box["value"]
    )
    monkeypatch.setattr(
        module, "reopen_materialized_shot_continuity_source_execution_sources",
        lambda **kwargs: sources,
    )
    monkeypatch.setattr(
        module, "load_m0_qualification_execution_sources",
        lambda **kwargs: SimpleNamespace(),
    )

    def validate_schemas(object_info: dict[str, object], current_sources: Any) -> None:
        del current_sources
        if object_info != {"schemas": "exact"}:
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="schema drift",
                retryable=False,
            )

    monkeypatch.setattr(module, "validate_m0_live_node_schemas", validate_schemas)
    monkeypatch.setattr(module, "_missing_required_node_inputs", lambda *args: [])
    monkeypatch.setattr(
        module,
        "source_node_schema_seals",
        lambda object_info: profile.source_node_schema_seals,
    )
    monkeypatch.setattr(
        module, "m0_node_schema_seals",
        lambda object_info: (SimpleNamespace(node_name="sealed", schema_sha256="e" * 64),),
    )

    def component_hash(path: Path, *, root: Path) -> tuple[str, int]:
        del root
        item = next(
            component for component in sources.profile.components
            if component.filename == path.name
        )
        return item.sha256, item.size_bytes

    monkeypatch.setattr(module, "_hash_component", component_hash)
    comfy_root = tmp_path / "comfy"
    comfy_root.mkdir()
    provider = ShotContinuitySourceQualificationProvider(
        committer=committer,
        qualification_profile_path=PROFILE_PATH,
        m0_profile_path=REPO_ROOT / (
            "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json"
        ),
        artifact_root=REPO_ROOT,
        project_root=input_root,
        comfy_root=comfy_root,
        transport=transport,
        project_loader=lambda: project,
        commit_resolver=lambda: sources.profile.comfyui_commit,
        clock=lambda: NOW,
    )
    caller = ShotContinuitySourceQualificationCaller(
        committer=committer, provider=provider
    )
    return _Case(
        caller, provider, committer, transport, request, profile,
        p0_box, project, paths, payloads,
    )


def _qualify(case: _Case) -> Any:
    return case.caller.qualify(
        attempt_id="source-attempt", resolved_request=case.request
    )


def _submission(case: _Case) -> LocalVideoSubmission:
    result = LocalVideoSubmitResult.create(
        resolved=case.request,
        provider_request_id="source-prompt-1",
        submitted_at=NOW,
    )
    return LocalVideoSubmission.from_submit_result(
        resolved=case.request,
        result=result,
    )


def _submission_for_hash(case: _Case, resolved_hash: str) -> LocalVideoSubmission:
    request = SimpleNamespace(**vars(case.request))
    request.resolved_generation_hash = resolved_hash
    result = LocalVideoSubmitResult.create(
        resolved=request,
        provider_request_id="source-prompt-other",
        submitted_at=NOW,
    )
    return LocalVideoSubmission.from_submit_result(
        resolved=request,
        result=result,
    )


def _assert_zero_effect(case: _Case) -> None:
    assert case.committer.start_writes == 0
    assert case.committer.intent_writes == 0
    assert case.committer.result_writes == 0
    assert case.committer.failure_writes == 0
    assert case.transport.uploads == []
    assert case.transport.workflows == []


def test_source_qualification_submits_once_after_permit_with_exact_a2_a3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)

    outcome = _qualify(case)

    assert outcome.provider_request_id == "source-prompt-1"
    assert outcome.source_execution_stack_hash == case.profile.source_execution_stack_hash
    assert outcome.sealed_seed == case.profile.sealed_seed
    assert case.committer.permit.consumed is True
    assert [item.file_name for item in case.transport.uploads] == ["first.png", "last.png"]
    workflow = case.transport.workflows[0]
    assert workflow["6"]["inputs"]["noise_seed"] == case.profile.sealed_seed
    assert workflow["15"]["inputs"]["image"] == "uploaded-1.png"
    assert workflow["16"]["inputs"]["image"] == "uploaded-2.png"
    assert workflow["5"]["inputs"]["prompt"] == case.profile.prompt
    assert (case.committer.start_writes, case.committer.intent_writes) == (1, 1)
    assert (case.committer.result_writes, case.committer.failure_writes) == (1, 0)
    assert case.transport.object_info_calls == 4


def test_source_qualification_real_provider_polls_and_fetches_exact_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission(case)

    observation = case.provider.get_local_status(case.request, submission)
    sink = io.BytesIO()
    receipt = case.provider.fetch_local(
        case.request,
        submission,
        observation,
        sink,
    )

    assert observation.state is VideoTaskState.SUCCEEDED
    assert observation.progress_milli == 1000
    assert observation.provider_file_id == "video:source-output.mp4:output"
    assert case.transport.poll_calls == ["source-prompt-1"]
    assert case.transport.fetch_calls == [
        {
            "filename": "source-output.mp4",
            "subfolder": "video",
            "type_": "output",
        }
    ]
    assert sink.getvalue() == case.transport.artifact_bytes
    assert receipt.artifact_sha256 == _sha(case.transport.artifact_bytes)
    assert receipt.size_bytes == len(case.transport.artifact_bytes)


def test_source_qualification_real_provider_rejects_submission_before_poll(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission_for_hash(case, "b" * 64)

    with pytest.raises(AiVideoError) as caught:
        case.provider.get_local_status(case.request, submission)

    assert caught.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert case.transport.poll_calls == []


def test_source_qualification_real_provider_rejects_observation_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission(case)
    other_submission = _submission_for_hash(case, "b" * 64)
    observation = LocalVideoTaskObservation.create(
        submission=other_submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=NOW,
        progress_milli=1000,
        provider_file_id="video:other.mp4:output",
    )
    sink = io.BytesIO()

    with pytest.raises(AiVideoError) as caught:
        case.provider.fetch_local(
            case.request,
            submission,
            observation,
            sink,
        )

    assert caught.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert case.transport.fetch_calls == []
    assert sink.getvalue() == b""


def test_source_qualification_real_provider_rejects_submission_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission_for_hash(case, "b" * 64)
    observation = LocalVideoTaskObservation.create(
        submission=submission,
        state=VideoTaskState.SUCCEEDED,
        observed_at=NOW,
        progress_milli=1000,
        provider_file_id="video:other.mp4:output",
    )
    sink = io.BytesIO()

    with pytest.raises(AiVideoError) as caught:
        case.provider.fetch_local(
            case.request,
            submission,
            observation,
            sink,
        )

    assert caught.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert case.transport.fetch_calls == []
    assert sink.getvalue() == b""


def test_source_qualification_real_provider_records_terminal_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission(case)
    case.transport.job_result = JobResult(
        JobStatus.FAILED,
        "source-prompt-1",
        error=AiVideoError(
            code=ErrorCode.COMFY_JOB_FAILED,
            user_message="source generation failed",
            retryable=False,
        ),
    )

    observation = case.provider.get_local_status(case.request, submission)

    assert observation.state is VideoTaskState.FAILED
    assert observation.provider_file_id is None
    assert case.transport.poll_calls == ["source-prompt-1"]


def test_source_qualification_real_provider_classifies_invalid_completed_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission(case)
    case.transport.job_result = JobResult(
        JobStatus.COMPLETED,
        "source-prompt-1",
        history={"outputs": {}},
    )

    with pytest.raises(AiVideoError) as caught:
        case.provider.get_local_status(case.request, submission)

    assert caught.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert caught.value.retryable is False
    assert case.transport.poll_calls == ["source-prompt-1"]


def test_source_qualification_real_provider_fails_closed_on_unknown_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission(case)
    case.transport.job_result = JobResult(
        JobStatus.TIMEOUT,
        "source-prompt-1",
        error=AiVideoError(
            code=ErrorCode.COMFY_JOB_TIMEOUT,
            user_message="source status timed out",
            retryable=False,
        ),
    )

    with pytest.raises(AiVideoError) as caught:
        case.provider.get_local_status(case.request, submission)

    assert caught.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert caught.value.retryable is False
    assert case.transport.poll_calls == ["source-prompt-1"]
    assert case.transport.fetch_calls == []


def test_source_qualification_real_provider_rejects_non_mp4_without_writing_sink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    submission = _submission(case)
    observation = case.provider.get_local_status(case.request, submission)
    case.transport.artifact_bytes = b"not-a-video"
    sink = io.BytesIO()

    with pytest.raises(AiVideoError) as caught:
        case.provider.fetch_local(
            case.request,
            submission,
            observation,
            sink,
        )

    assert caught.value.code is ErrorCode.VIDEO_REQUEST_INVALID
    assert sink.getvalue() == b""


def test_source_upload_uses_pre_permit_immutable_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    original = case.payloads["first"]
    case.transport.before_first_upload = lambda: case.paths["first"].write_bytes(
        b"\x89PNG\r\n\x1a\nreplaced-after-validation"
    )

    _qualify(case)

    assert case.transport.uploads[0].data == original
    assert case.paths["first"].read_bytes() != original
    assert len(case.transport.workflows) == 1


@pytest.mark.parametrize(
    "drift",
    (
        "missing_source", "missing_seed", "negative_seed", "boolean_seed",
        "different_seed", "schema", "stack", "source_stack", "p0_receipt",
        "dependent_evidence", "cardinality", "lineage", "project",
        "registry", "request_revision", "active_revision", "missing_graph",
        "component", "endpoint",
    ),
)
def test_source_qualification_denials_are_zero_write_and_zero_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift: str
) -> None:
    import ai_video.production.shot_continuity_source_qualification as module

    case = _make_case(tmp_path, monkeypatch)
    if drift == "missing_source":
        case.paths["first"].unlink()
    elif drift == "missing_seed":
        case.request.effective_seed = None
    elif drift == "negative_seed":
        case.request.effective_seed = -1
    elif drift == "boolean_seed":
        case.request.effective_seed = True
    elif drift == "different_seed":
        case.request.effective_seed = case.profile.sealed_seed ^ 1
    elif drift == "schema":
        case.transport.object_info = {"schemas": "drift"}
    elif drift == "stack":
        case.request.execution_stack_hash = "0" * 64
    elif drift == "source_stack":
        case.p0_box["value"] = replace(
            case.p0_box["value"], source_execution_stack_hash="0" * 64
        )
    elif drift == "p0_receipt":
        case.p0_box["value"] = replace(
            case.p0_box["value"], qualification_receipt_hash="0" * 64
        )
    elif drift == "dependent_evidence":
        case.p0_box["value"] = replace(
            case.p0_box["value"], policy_hashes=("0" * 64,)
        )
    elif drift == "cardinality":
        case.request.image_bindings = case.request.image_bindings[:1]
    elif drift == "lineage":
        case.request.image_bindings[0].asset_sha256 = "0" * 64
    elif drift == "project":
        case.project.manifest.active_project.content_hash = "0" * 64
    elif drift == "registry":
        case.project.registry.content_hash = "0" * 64
    elif drift == "request_revision":
        case.request.activation_scope.request.target_shot_revision = (
            case.profile.target_shot_revision + 1
        )
    elif drift == "active_revision":
        case.project.shots[0].revision = case.profile.target_shot_revision + 1
    elif drift == "missing_graph":
        case.project.manifest.active_dependency_graph = None
    elif drift == "component":
        monkeypatch.setattr(
            module, "_hash_component", lambda *args, **kwargs: ("0" * 64, 1)
        )
    elif drift == "endpoint":
        case.transport.base_url = "https://example.com:8188"

    with pytest.raises((AiVideoError, OSError)):
        _qualify(case)

    _assert_zero_effect(case)


def test_closure_drift_after_request_write_still_blocks_before_permit_or_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    original_begin = case.committer.begin_video_generation

    def begin_and_drift(*, attempt_id: str, request: Any) -> Any:
        result = original_begin(attempt_id=attempt_id, request=request)
        case.p0_box["value"] = replace(
            case.p0_box["value"], validation_set_hash="0" * 64
        )
        return result

    case.committer.begin_video_generation = begin_and_drift  # type: ignore[method-assign]
    with pytest.raises(AiVideoError):
        _qualify(case)

    assert case.committer.start_writes == 1
    assert case.committer.intent_writes == 0
    assert case.committer.permit.consumed is False
    assert case.transport.uploads == []
    assert case.transport.workflows == []


def test_permit_replay_has_no_second_upload_or_submit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    preview = case.provider.preview(case.request)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="source-attempt", request=case.request,
        preview=preview, recorded_at=NOW,
    )
    permit = _Permit()
    case.transport.permit_probe = lambda: permit.consumed

    case.provider.submit_local(case.request, preview, intent, permit)
    uploads = tuple(case.transport.uploads)
    workflows = tuple(case.transport.workflows)
    with pytest.raises(AiVideoError) as exc:
        case.provider.submit_local(case.request, preview, intent, permit)

    assert exc.value.retryable is False
    assert tuple(case.transport.uploads) == uploads
    assert tuple(case.transport.workflows) == workflows


def test_unknown_submit_outcome_is_recorded_once_without_retry_or_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    case.transport.submit_error = TimeoutError("unknown")

    with pytest.raises(AiVideoError) as exc:
        _qualify(case)

    assert exc.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert exc.value.retryable is False
    assert len(case.transport.uploads) == 2
    assert len(case.transport.workflows) == 1
    assert case.committer.intent_writes == 1
    assert case.committer.result_writes == 0
    assert case.committer.failure_writes == 1


def test_seed_derivation_binds_every_pre_generation_root() -> None:
    sources = load_shot_continuity_source_execution_sources(artifact_root=REPO_ROOT)
    profile = _profile(sources, _p0(sources.materialized_stack.execution_stack_hash))
    values = profile.model_dump(mode="python")
    baseline = derive_source_qualification_seed(values)

    for field in (
        "source_execution_stack_hash", "p0_qualification_receipt_hash",
        "m0_execution_stack_hash", "project_content_hash", "registry_content_hash",
        "target_shot_content_hash", "first_frame_sha256", "last_frame_sha256",
        "prompt_sha256", "output_contract_hash",
    ):
        changed = dict(values)
        changed[field] = "0" * 64
        assert derive_source_qualification_seed(changed) != baseline


def test_repository_source_qualification_profile_is_canonical_and_sealed() -> None:
    profile, file_sha256 = load_source_qualification_profile(
        PROFILE_PATH, artifact_root=REPO_ROOT
    )

    assert file_sha256 == _sha(PROFILE_PATH.read_bytes())
    assert profile.prompt == PROMPT
    assert profile.sealed_seed == derive_source_qualification_seed(
        profile.model_dump(mode="python")
    )
    assert profile.remote_provider_enabled is False
    assert profile.cloud_fallback_enabled is False
    assert profile.retry_enabled is False
    assert profile.loopback_endpoint == "http://127.0.0.1:8188"
    assert profile.source_node_schema_status == "sealed"
    assert tuple(
        item.node_name for item in profile.source_node_schema_seals
    ) == SOURCE_REQUIRED_NODES
    assert tuple(
        item.schema_sha256 for item in profile.source_node_schema_seals
    ) == (
        "0803bca8808c9e196cac6a5029c01943786166ec1c643e00389b8bdc1396c8ee",
        "e9f485efa1b625aed932d738f4bd78e1770f573acbe551c2a800972d92ee1385",
        "437f9bf7258fa818125a864fb43fdefa5f1fdc5b80a4f6f318a76bc9d21a9f4e",
        "195f056570e0629062ad01c6a1a5efcabae8462a1ee63f278a4afcb98d89c6c0",
        "41d9d603f14caf9196ebc80c5b5a5f68d4c303341b307a3a1230c461d64eebcc",
        "c561c18f4ab40c62009ced56fce369d4cdcbc5fbc3b8f2e0cbb654b475c0940b",
        "c1fa5850e2f75ca74bd92c29a817caf63e12049bf1a8fe49e7dca656a33abfab",
        "4890f0552783fc47c37a445202b713a47e9c83cb85049fa78310fc3124c23931",
        "261a495a933da3a3ffd113e1f909c0d714a60e4643eac6a057a1c488ffa19716",
        "6a87f3e8b7b30130af981b39248eb9bb84707428707b282a2496b33423b14024",
        "3080368e30dd0e77d6339b115d7d239d3a226254072f5077f1eac7a121e9d1e2",
        "b4fdcd28df18e20b430f8978dbcd2865a650e0a0d68efc85b2bc4a5425d07f11",
        "8f2f8c8755675c5d0572b6c6c9ab033e85611a0bd7aebfac8f3fab31d74f5f8a",
        "ecf1b0bb9558c1a84dea6e1fcf4f9a9d79ac5d09ed557092f1c062abcef4ead6",
    )


def test_profile_seed_tamper_is_rejected(tmp_path: Path) -> None:
    import json

    payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    payload["sealed_seed"] ^= 1
    tampered = tmp_path / PROFILE_PATH.name
    tampered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AiVideoError, match="profile is invalid"):
        load_source_qualification_profile(tampered, artifact_root=tmp_path)


def test_source_node_schema_seals_ignore_only_runtime_file_inventory() -> None:
    import ai_video.production.shot_continuity_source_schema as schema_module

    object_info = {}
    for name in schema_module.SOURCE_REQUIRED_NODES:
        required = {"value": ["STRING", {"default": "sealed"}]}
        for field in schema_module.SOURCE_RUNTIME_FILE_CHOOSERS.get(name, ()):
            required[field] = [["one.safetensors"], {}]
        object_info[name] = {
            "input": {"required": required, "optional": {}},
            "input_order": {"required": tuple(required)},
            "output_name": ["OUTPUT"],
        }
    first = schema_module.source_node_schema_seals(object_info)
    object_info["UNETLoader"]["input"]["required"]["unet_name"][0] = [
        "different.safetensors"
    ]
    assert schema_module.source_node_schema_seals(object_info) == first
    object_info["UNETLoader"]["input"]["required"]["value"][0] = "INT"
    assert schema_module.source_node_schema_seals(object_info) != first


def test_missing_active_graph_denies_before_runtime_inspection_or_any_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    case.project.manifest.active_dependency_graph = None

    with pytest.raises(AiVideoError, match="active project lineage"):
        _qualify(case)

    _assert_zero_effect(case)
    assert case.transport.object_info_calls == 0


def test_unsealed_source_node_schemas_block_before_runtime_or_any_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.shot_continuity_source_qualification as module

    case = _make_case(tmp_path, monkeypatch)
    unsealed = case.profile.model_copy(
        update={
            "source_node_schema_status": "unsealed",
            "source_node_schema_seals": (),
        }
    )
    monkeypatch.setattr(
        module,
        "load_source_qualification_profile",
        lambda path, artifact_root: (unsealed, "f" * 64),
    )

    with pytest.raises(AiVideoError, match="node schemas are not sealed"):
        _qualify(case)

    _assert_zero_effect(case)
    assert case.transport.object_info_calls == 0
