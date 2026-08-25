from __future__ import annotations

from argparse import Namespace
from datetime import UTC, datetime
import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmission,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_source_qualification import (
    ShotContinuitySourceQualificationProfile,
    load_source_qualification_profile,
)
from ai_video.production.shot_continuity_source_runtime import (
    APPROVED_ENDPOINT_ROLE,
    make_source_production_committer,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
    VideoTaskState,
)
from scripts.prepare_shot_continuity_p0 import prepare


REPO_ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION_PROFILE = Path(
    "workflows/qualification/minimax_h3_fl2va_rainy_station_source_v1_profile.json"
)


def _operator_module():
    try:
        return importlib.import_module(
            "ai_video.production.shot_continuity_source_operator"
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"source qualification operator is missing: {exc}")


def _script_module():
    try:
        return importlib.import_module("scripts.execute_shot_continuity_source")
    except ModuleNotFoundError as exc:
        pytest.fail(f"source qualification operator script is missing: {exc}")


def _prepare_project(tmp_path: Path):
    image_paths = []
    for ordinal, color in enumerate(("red", "green", "blue", "yellow"), 1):
        source_dir = tmp_path / f"a{ordinal}"
        source_dir.mkdir()
        path = source_dir / "image-01.png"
        Image.new("RGB", (1659, 948), color).save(path)
        (source_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "backend": "chatgpt-web",
                    "mode": "direct-typescript-browser",
                    "prompt": f"rainy station source {ordinal}",
                    "created_at": f"2026-08-25T03:0{ordinal}:00.000Z",
                }
            ),
            encoding="utf-8",
        )
        image_paths.append(path)
    root = tmp_path / "production"
    prepare(
        Namespace(
            root=root,
            a1=image_paths[0],
            a2=image_paths[1],
            a3=image_paths[2],
            a4=image_paths[3],
            approved_at="2026-08-25T12:00:00+08:00",
            imported_at="2026-08-25T12:01:00+08:00",
        )
    )
    return root, load_production_project(root / "project.yaml")


def _profile_for(project) -> tuple[ShotContinuitySourceQualificationProfile, str]:
    sealed, document_hash = load_source_qualification_profile(
        QUALIFICATION_PROFILE,
        artifact_root=REPO_ROOT,
    )
    registry = {item.asset_id: item for item in project.registry.assets}
    frames = []
    for shot in project.shots[1:3]:
        asset_id = next(
            role.asset_ids[0]
            for role in shot.required_asset_roles
            if role.role == APPROVED_ENDPOINT_ROLE
        )
        frames.append(registry[asset_id])
    target = project.shots[2]
    values = sealed.model_dump(
        mode="python",
        exclude={
            "prompt_sha256",
            "sealed_seed",
            "output_contract_hash",
            "profile_content_hash",
        },
    )
    values.update(
        {
            "project_content_hash": project.project.content_hash,
            "registry_content_hash": project.registry.content_hash,
            "target_shot_revision": target.revision,
            "target_shot_content_hash": target.content_hash,
            "first_frame_asset_id": frames[0].asset_id,
            "first_frame_sha256": frames[0].sha256,
            "first_frame_size_bytes": frames[0].size_bytes,
            "first_frame_width": frames[0].width,
            "first_frame_height": frames[0].height,
            "last_frame_asset_id": frames[1].asset_id,
            "last_frame_sha256": frames[1].sha256,
            "last_frame_size_bytes": frames[1].size_bytes,
            "last_frame_width": frames[1].width,
            "last_frame_height": frames[1].height,
        }
    )
    return ShotContinuitySourceQualificationProfile.create(**values), document_hash


class _RecordedProvider:
    def __init__(self) -> None:
        self.preflight_calls = 0
        self.submit_calls = 0
        self.poll_calls = 0
        self.fetch_calls = 0
        self.on_preflight = None

    def validate_pre_effect(self, request: ResolvedVideoGenerationRequest):
        self.preflight_calls += 1
        if self.on_preflight is not None:
            self.on_preflight()
        return SimpleNamespace(
            qualification_profile_hash="1" * 64,
            source_execution_stack_hash=request.execution_stack_hash,
            sealed_seed=request.effective_seed,
            p0=SimpleNamespace(
                candidate_label="m0",
                qualification_receipt_hash="2" * 64,
                execution_stack_hash="3" * 64,
                source_execution_stack_hash=request.execution_stack_hash,
                profile_hash="4" * 64,
                compiler_hash="5" * 64,
                workflow_hash="6" * 64,
                validation_set_hash="7" * 64,
                policy_hashes=("8" * 64,),
                qualification_input_hashes=(("inventory", "9" * 64),),
            ),
            source_profile_hash="a" * 64,
            source_compiler_hash="b" * 64,
            source_workflow_hash="c" * 64,
            project_content_hash="d" * 64,
            registry_content_hash="e" * 64,
            dependency_graph_content_hash="f" * 64,
            m0_node_schema_hashes=(("M0Node", "1" * 64),),
            source_node_schema_hashes=(("SourceNode", "2" * 64),),
            component_hashes=(("diffusion", "3" * 64),),
            inputs=(
                SimpleNamespace(
                    file_name="a2.png",
                    data=b"SENSITIVE-A2-BYTES",
                    file_sha256="4" * 64,
                    size_bytes=18,
                ),
                SimpleNamespace(
                    file_name="a3.png",
                    data=b"SENSITIVE-A3-BYTES",
                    file_sha256="5" * 64,
                    size_bytes=18,
                ),
            ),
        )

    def preview(
        self, request: ResolvedVideoGenerationRequest
    ) -> VideoGenerationPreview:
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def submit_local(self, request, preview, intent, permit):
        assert isinstance(intent, LocalVideoSubmitIntent)
        assert preview == self.preview(request)
        assert permit._consume_local_video_submit_permit(
            intent_fingerprint=intent.intent_fingerprint,
            request_fingerprint=request.resolved_generation_hash,
        )
        self.submit_calls += 1
        return LocalVideoSubmitResult.create(
            resolved=request,
            provider_request_id="source-operator-prompt-1",
            submitted_at=datetime(2026, 8, 25, 4, tzinfo=UTC),
        )

    def get_local_status(
        self,
        request: ResolvedVideoGenerationRequest,
        submission: LocalVideoSubmission,
    ) -> LocalVideoTaskObservation:
        self.poll_calls += 1
        return LocalVideoTaskObservation.create(
            submission=submission,
            state=VideoTaskState.SUCCEEDED,
            progress_milli=1000,
            provider_file_id="video:source-operator.mp4:output",
            observed_at=datetime(2026, 8, 25, 4, 1, tzinfo=UTC),
        )

    def fetch_local(self, request, submission, observation, sink):
        payload = b"\x00\x00\x00\x14ftypisomsource-operator"
        self.fetch_calls += 1
        sink.write(payload)
        return LocalVideoFetchReceipt.create(
            submission=submission,
            observation=observation,
            content_type="video/mp4",
            size_bytes=len(payload),
            artifact_sha256=hashlib.sha256(payload).hexdigest(),
            fetched_at=datetime(2026, 8, 25, 4, 2, tzinfo=UTC),
        )


def test_builder_uses_exact_active_lineage_without_fixture_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _operator_module()
    compiler = importlib.import_module("ai_video.production.video_compiler")
    captured = []
    real_compile = compiler.compile_video_generation_request

    def _compile(projection):
        captured.append(projection)
        return real_compile(projection)

    monkeypatch.setattr(module, "compile_video_generation_request", _compile)
    _, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)

    first = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v1",
    )
    second = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v1",
    )

    assert first == second
    assert len(captured) == 2
    assert all(
        isinstance(item, compiler.VideoGenerationRequestCompilation)
        and item.compilation_kind == "qualification"
        for item in captured
    )
    tampered = captured[0].model_dump(mode="python")
    tampered["prompt_text"] = "drifted after compilation"
    with pytest.raises(ValueError, match="compilation_hash"):
        compiler.VideoGenerationRequestCompilation.model_validate(tampered)
    copied_without_validation = captured[0].model_copy(
        update={"prompt_text": "model-copy drift"}
    )
    with pytest.raises(ValueError, match="compilation_hash"):
        real_compile(copied_without_validation)
    assert first.activation_scope is not None
    assert (
        first.activation_scope.request.base_project
        == project.manifest.active_project
    )
    assert (
        first.activation_scope.request.base_registry
        == project.manifest.active_registry
    )
    assert (
        first.activation_scope.request.base_dependency_graph
        == project.manifest.active_dependency_graph
    )
    assert first.requirement_hash not in {"1" * 64, "b" * 64}
    assert first.provider_bound_request_hash not in {"2" * 64, "c" * 64}
    assert tuple(item.asset_id for item in first.image_bindings) == (
        profile.first_frame_asset_id,
        profile.last_frame_asset_id,
    )
    assert first.effective_seed == profile.sealed_seed
    assert first.effective_output.frame_count == 124
    assert first.effective_output.width == 1344
    assert first.effective_output.height == 768
    assert first.effective_output.fps == 24


def test_operator_keeps_preflight_read_only_and_stops_fetch_at_validate(
    tmp_path: Path,
) -> None:
    module = _operator_module()
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v1",
    )
    provider = _RecordedProvider()
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=provider,
        request=request,
        attempt_id="rainy-station-source-a2-a3-attempt-v1",
    )
    manifest_path = root / "state/manifest.json"
    before = manifest_path.read_bytes()

    preflight = operator.preflight(require_new_attempt=True)

    assert preflight["durable_state_unchanged"] is True
    assert preflight["next_action"] == "submit"
    assert manifest_path.read_bytes() == before
    assert provider.submit_calls == provider.poll_calls == provider.fetch_calls == 0
    serialized = json.dumps(script_json := _script_module()._jsonable(preflight))
    assert "SENSITIVE" not in serialized
    assert script_json["preflight"]["inputs"] == [
        {"file_name": "a2.png", "file_sha256": "4" * 64, "size_bytes": 18},
        {"file_name": "a3.png", "file_sha256": "5" * 64, "size_bytes": 18},
    ]

    outcome = operator.submit(require_new_attempt=True)
    assert outcome.provider_request_id == "source-operator-prompt-1"
    assert operator.status()["next_action"] == "poll"
    assert provider.submit_calls == 1

    with pytest.raises(AiVideoError) as caught:
        operator.submit(require_new_attempt=True)
    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert provider.submit_calls == 1

    observation = operator.poll()
    assert observation.state is VideoTaskState.SUCCEEDED
    assert operator.status()["next_action"] == "fetch"

    fetched = operator.fetch()
    assert fetched.relative_path.suffix == ".mp4"
    assert operator.status()["next_action"] == "validate"
    assert provider.poll_calls == provider.fetch_calls == 1
    assert not any(
        item.status.value == "succeeded"
        for item in load_production_project(root / "project.yaml").manifest.attempts
        if item.attempt_id == "rainy-station-source-a2-a3-attempt-v1"
    )

    replacement_request = module.build_source_qualification_request(
        project=project,
        profile=profile,
        profile_document_hash=document_hash,
        generation_id="rainy-station-source-a2-a3-test-v2",
    )
    replacement = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(
            root, load_production_project(root / "project.yaml")
        ),
        provider=provider,
        request=replacement_request,
        attempt_id="rainy-station-source-a2-a3-attempt-v2",
    )
    with pytest.raises(AiVideoError) as replacement_caught:
        replacement.submit(require_new_attempt=True)
    assert replacement_caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert provider.submit_calls == 1


def test_preflight_detects_non_state_bundle_mutation(tmp_path: Path) -> None:
    module = _operator_module()
    root, project = _prepare_project(tmp_path)
    profile, document_hash = _profile_for(project)
    provider = _RecordedProvider()
    provider.on_preflight = lambda: (root / "project.yaml").write_bytes(
        b"mutated outside state"
    )
    operator = module.ShotContinuitySourceOperator(
        project_root=root,
        committer=make_source_production_committer(root, project),
        provider=provider,
        request=module.build_source_qualification_request(
            project=project,
            profile=profile,
            profile_document_hash=document_hash,
            generation_id="rainy-station-source-mutation-test-v1",
        ),
        attempt_id="rainy-station-source-mutation-attempt-v1",
    )

    with pytest.raises(AiVideoError) as caught:
        operator.preflight(require_new_attempt=True)

    assert caught.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_cli_json_serialization_rejects_binary_or_unknown_objects() -> None:
    script = _script_module()

    with pytest.raises(ValueError, match="binary"):
        script._jsonable(b"raw")
    with pytest.raises(ValueError, match="unsupported"):
        script._jsonable(object())


def test_cli_main_sanitizes_unsupported_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script = _script_module()
    monkeypatch.setattr(script, "execute", lambda _: object())
    monkeypatch.setattr(
        "sys.argv",
        [
            "execute_shot_continuity_source.py",
            "status",
            "--root",
            "/tmp/source-root",
            "--artifact-root",
            "/tmp/artifact-root",
            "--comfy-root",
            "/tmp/comfy-root",
            "--generation-id",
            "source-generation-v1",
            "--attempt-id",
            "source-attempt-v1",
        ],
    )

    assert script.main() == 2
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert '"error_code": "source_operator_invalid"' in captured.err


def test_cli_exposes_only_explicit_local_actions() -> None:
    script = _script_module()
    parser = script._parser()
    base = [
        "preflight",
        "--root",
        "/tmp/source-root",
        "--artifact-root",
        "/tmp/artifact-root",
        "--comfy-root",
        "/tmp/comfy-root",
        "--generation-id",
        "source-generation-v1",
        "--attempt-id",
        "source-attempt-v1",
        "--require-new-attempt",
    ]

    assert parser.parse_args(base).action == "preflight"
    for forbidden in ("--retry", "--endpoint", "--model", "--prompt", "--seed"):
        with pytest.raises(SystemExit):
            parser.parse_args([*base, forbidden, "override"])


def test_cli_dispatches_exactly_one_action() -> None:
    script = _script_module()
    calls: list[tuple[str, bool]] = []

    class _Operator:
        def preflight(self, *, require_new_attempt: bool):
            calls.append(("preflight", require_new_attempt))
            return {"next_action": "submit"}

    args = script._parser().parse_args(
        [
            "preflight",
            "--root",
            "/tmp/source-root",
            "--artifact-root",
            "/tmp/artifact-root",
            "--comfy-root",
            "/tmp/comfy-root",
            "--generation-id",
            "source-generation-v1",
            "--attempt-id",
            "source-attempt-v1",
            "--require-new-attempt",
        ]
    )

    result = script.execute(args, opener=lambda **_: _Operator())

    assert result == {"next_action": "submit"}
    assert calls == [("preflight", True)]
