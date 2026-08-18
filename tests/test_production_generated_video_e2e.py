from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    DependencyLifecycle,
    RegistryDependencyEvidence,
    StateCommitStatus,
    VideoAttemptPhase,
)
from ai_video.production._video_project_reader import (
    load_video_fetch_receipt,
    load_video_request_receipt,
    load_video_status_receipt,
)
from ai_video.production.hyperframes import probe_clip_fd
from ai_video.production.paths import _open_regular_file_nofollow
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRequirement,
    VideoProviderCapabilities,
    VideoTaskState,
)
from ai_video.production.video_fake import (
    FakeVideoScenario,
    ScriptedFakeVideoProvider,
)
from ai_video.production.video_artifact import probe_generated_video_candidate
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.project import load_production_project
from production_project_factory import (
    make_p8_video_candidate_preparer,
    make_p8_video_generation_base,
)
from test_production_video import _paid_authorization, _paid_preview


FIXTURE = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"
ATTEMPT_ID = "p8-generated-video-e2e"


def _runtime(root: Path):
    inputs = make_p8_video_generation_base(root)
    loaded = inputs.project
    shot = loaded.shots[0]
    source = loaded.registry.assets[0]
    output = VideoOutputRequirement(
        duration_seconds=1,
        width=64,
        height=64,
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )
    profile_sha = "d" * 64
    request = VideoGenerationRequest.create(
        generation_id="p8-generation-001",
        provider_name="fake-video",
        provider_kind="fake_video",
        model_id="fake-h264",
        provider_profile=ProviderProfilePointer(
            profile_id="fake-video-profile",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile_sha}.json"),
            profile_sha256=profile_sha,
        ),
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
        target_asset_role=shot.required_asset_roles[0].role,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text="A sealed one-second archive-room push-in.",
        negative_prompt_text="flicker",
        image_bindings=(
            VideoImageReferenceBinding(
                role="first_frame",
                asset_id=source.asset_id,
                asset_sha256=source.sha256,
                mime_type=source.mime_type,
                width=source.width or 64,
                height=source.height or 64,
                size_bytes=source.size_bytes,
            ),
        ),
        output_requirement=output,
        seed=17,
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=(shot.artifact_id, source.asset_id),
        output_asset_id="video-output-p8-001",
    )
    variant = VideoCapabilityVariant(
        capability_id="fake-i2v-1s-64",
        provider_kind="fake_video",
        model_id="fake-h264",
        profile_version="v1",
        execution_kind=VideoExecutionKind.REMOTE,
        billing_kind=BillingKind.METERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        output=output,
        allowed_image_roles=("first_frame",),
        required_first_frame=True,
        max_reference_count=0,
        allowed_image_mime_types=(source.mime_type,),
        max_image_bytes=max(source.size_bytes, 1),
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=True,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    provider = ScriptedFakeVideoProvider(
        capabilities=VideoProviderCapabilities.create(
            provider_name="fake-video", variants=(variant,)
        ),
        artifact_bytes=FIXTURE.read_bytes(),
        scenario=FakeVideoScenario(
            status_events=(
                VideoTaskState.QUEUED,
                "transient_error",
                VideoTaskState.RUNNING,
                VideoTaskState.SUCCEEDED,
            )
        ),
    )
    resolved = provider.resolve(request)
    video_preview = provider.preview(resolved)
    paid_preview = _paid_preview(
        resolved,
        attempt_id=ATTEMPT_ID,
        video_preview=video_preview,
    )
    authorization = _paid_authorization(paid_preview)
    committer = ProductionStateCommitter(
        root,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=(
            lambda exact: authorization if exact == paid_preview else None
        ),
        paid_provider_clock=lambda: authorization.issued_at,
    )
    return inputs, provider, resolved, paid_preview, committer


def _reach_fetch(root: Path, *, settle: bool = True):
    inputs, provider, resolved, paid_preview, committer = _runtime(root)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=ATTEMPT_ID, request=resolved)
    service.submit_once(
        attempt_id=ATTEMPT_ID,
        paid_preview=paid_preview,
        reservation_id="p8-video-reservation-1",
    )
    service.refresh_once(attempt_id=ATTEMPT_ID)
    with pytest.raises(AiVideoError):
        service.refresh_once(attempt_id=ATTEMPT_ID)
    service.refresh_once(attempt_id=ATTEMPT_ID)
    service.refresh_once(attempt_id=ATTEMPT_ID)
    if settle:
        committer.settle_paid_provider_reservation(
            attempt_id=ATTEMPT_ID,
            actual_cost_microunits=1_000_000,
        )
    return inputs, provider, resolved, committer


def test_fake_video_fetch_activate_reopen_and_replay_are_exact(tmp_path: Path):
    inputs, provider, resolved, committer = _reach_fetch(tmp_path)
    restarted = VideoGenerationService(
        committer=ProductionStateCommitter(
            tmp_path,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    )
    before = load_production_project(tmp_path / "project.yaml")
    unaffected_assets = {
        asset.asset_id: asset
        for asset in before.registry.assets
        if asset.asset_id != "image-shot-1"
    }
    unaffected_states = {
        state.node_id: state
        for state in before.manifest.dependency_states
        if state.node_id
        in {
            "asset:image-shot-2",
            "asset:voice-narration",
            "creative:shot:shot-2:visual",
        }
    }
    probe_calls = 0

    def counted_probe(held_fd: int):
        nonlocal probe_calls
        probe_calls += 1
        return probe_clip_fd(held_fd)

    activated = restarted.fetch_and_activate(
        attempt_id=ATTEMPT_ID,
        probe=counted_probe,
    )
    selected = load_production_project(tmp_path / "project.yaml")

    attempt = activated.attempts[-1]
    state = attempt.video_generation_state
    assert attempt.status is StateCommitStatus.SUCCEEDED
    assert state is not None and state.phase is VideoAttemptPhase.ACTIVATE
    assert selected.manifest == activated
    assert selected.manifest.active_project != before.manifest.active_project
    assert selected.manifest.active_registry != before.manifest.active_registry
    assert selected.manifest.active_dependency_graph != before.manifest.active_dependency_graph
    generated = selected.registry.assets[-1]
    assert generated.asset_id == "video-output-p8-001"
    assert generated.video_metadata is not None
    assert (tmp_path / generated.artifact_path).read_bytes() == FIXTURE.read_bytes()
    assert next(
        item for item in selected.shots if item.shot_id == "shot-1"
    ).visual_strategy.value == "generated_video"
    assert next(item for item in selected.shots if item.shot_id == "shot-2") == next(
        item for item in before.shots if item.shot_id == "shot-2"
    )
    assert {
        asset.asset_id: asset
        for asset in selected.registry.assets
        if asset.asset_id in unaffected_assets
    } == unaffected_assets
    selected_states = {state.node_id: state for state in selected.manifest.dependency_states}
    for node_id, before_state in unaffected_states.items():
        after_state = selected_states[node_id]
        assert after_state.lifecycle == before_state.lifecycle
        assert after_state.desired_fingerprint == before_state.desired_fingerprint
        assert after_state.applied_evidence == before_state.applied_evidence
        assert after_state.blocked_by == before_state.blocked_by
    for node_id in (
        "creative:shot:shot-1:visual",
        "asset:video-output-p8-001",
    ):
        applied = selected_states[node_id]
        assert applied.lifecycle is DependencyLifecycle.FRESH
        assert applied.applied_fingerprint == applied.desired_fingerprint
        assert applied.applied_evidence is not None
    video_evidence = selected_states[
        "asset:video-output-p8-001"
    ].applied_evidence
    assert isinstance(video_evidence, RegistryDependencyEvidence)
    assert video_evidence.pointer == selected.manifest.active_registry
    assert video_evidence.artifact_fingerprint == selected_states[
        "asset:video-output-p8-001"
    ].desired_fingerprint

    reopened_request = load_video_request_receipt(tmp_path, state.request)
    reopened_observation = load_video_status_receipt(
        tmp_path, state.latest_observation
    )
    reopened_fetch = load_video_fetch_receipt(tmp_path, state.fetch_receipt)
    original = reopened_request.activation_scope
    assert reopened_request == resolved
    assert original is not None
    assert original.request.target_shot_id == "shot-1"
    assert original.request.target_asset_role == "still"
    assert original.request.prompt_text == resolved.prompt_text
    assert original.request.image_bindings == resolved.image_bindings
    assert reopened_observation.provider_file_id == reopened_fetch.provider_file_id
    assert reopened_fetch.artifact_sha256 == generated.sha256
    assert generated.tool is not None
    assert generated.tool.name == resolved.provider_kind
    assert generated.input_fingerprint == resolved.resolved_generation_hash
    assert selected.manifest.active_paid_provider_budget is not None
    assert generated.cost_receipt_id == (
        selected.manifest.active_paid_provider_budget.content_hash
    )
    assert generated.video_metadata.request_receipt_fingerprint == (
        resolved.desired_generation_fingerprint
    )
    assert provider.call_counts.submit == 1
    assert provider.call_counts.status == 4
    assert provider.call_counts.fetch == 1
    assert probe_calls == 1

    files_before = tuple(
        sorted(
            (
                path.relative_to(tmp_path),
                path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in tmp_path.rglob("*")
            if path.is_file()
        )
    )
    replayed = restarted.fetch_and_activate(
        attempt_id=ATTEMPT_ID,
        probe=counted_probe,
    )
    files_after = tuple(
        sorted(
            (
                path.relative_to(tmp_path),
                path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in tmp_path.rglob("*")
            if path.is_file()
        )
    )
    assert replayed == activated
    assert files_after == files_before
    assert provider.call_counts.submit == 1
    assert provider.call_counts.fetch == 1
    assert probe_calls == 1


def test_active_video_reopens_after_later_paid_budget_revision(tmp_path: Path):
    inputs, provider, resolved, committer = _reach_fetch(tmp_path)
    VideoGenerationService(committer=committer, provider=provider).fetch_and_activate(
        attempt_id=ATTEMPT_ID
    )
    selected = load_production_project(tmp_path / "project.yaml")
    generated = next(
        asset for asset in selected.registry.assets
        if asset.asset_id == resolved.output_asset_id
    )
    historical_cost_id = generated.cost_receipt_id
    assert historical_cost_id is not None
    scope = resolved.activation_scope
    assert scope is not None
    next_values = scope.request.model_dump(
        mode="python", exclude={"request_input_hash"}
    )
    next_values.update(
        generation_id="p8-generation-002",
        output_asset_id="video-output-p8-002",
    )
    next_request = VideoGenerationRequest.create(**next_values)
    next_resolved = provider.resolve(next_request)
    next_attempt_id = "p8-generated-video-next"
    next_preview = _paid_preview(
        next_resolved,
        attempt_id=next_attempt_id,
        video_preview=provider.preview(next_resolved),
    )
    next_authorization = _paid_authorization(next_preview)
    next_committer = ProductionStateCommitter(
        tmp_path,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=(
            lambda exact: next_authorization if exact == next_preview else None
        ),
        paid_provider_clock=lambda: next_authorization.issued_at,
    )
    next_service = VideoGenerationService(
        committer=next_committer,
        provider=provider,
    )
    next_service.start(attempt_id=next_attempt_id, request=next_resolved)
    next_committer.record_paid_provider_submit_intent(
        next_preview,
        reservation_id="p8-video-reservation-2",
    )

    advanced = load_production_project(tmp_path / "project.yaml")
    assert advanced.manifest.active_project == selected.manifest.active_project
    assert advanced.manifest.active_registry == selected.manifest.active_registry
    assert (
        advanced.manifest.active_dependency_graph
        == selected.manifest.active_dependency_graph
    )
    assert advanced.manifest.active_paid_provider_budget is not None
    assert advanced.manifest.active_paid_provider_budget.content_hash != historical_cost_id
    reopened = next(
        asset for asset in advanced.registry.assets
        if asset.asset_id == resolved.output_asset_id
    )
    assert reopened.cost_receipt_id == historical_cost_id


def test_candidate_recovery_keeps_old_tuple_until_explicit_activation(tmp_path: Path):
    inputs, provider, _, committer = _reach_fetch(tmp_path)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.fetch_once(attempt_id=ATTEMPT_ID)
    base = committer._read_manifest()
    candidate = committer.prepare_video_activation_candidate(attempt_id=ATTEMPT_ID)
    candidate_attempt = candidate.attempts[-1]
    assert candidate_attempt.video_generation_state is not None
    assert candidate_attempt.video_generation_state.phase is VideoAttemptPhase.CANDIDATE
    assert candidate.active_project == base.active_project
    assert candidate.active_registry == base.active_registry
    assert candidate.active_dependency_graph == base.active_dependency_graph

    recovered_committer = ProductionStateCommitter(
        tmp_path,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
    )
    recovered_committer.recover()
    recovered = recovered_committer._read_manifest()
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert recovered.active_project == base.active_project

    final = recovered_committer.activate_video_candidate(attempt_id=ATTEMPT_ID)
    assert final.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert final.active_project == candidate_attempt.candidate_project


def test_candidate_rejects_fetch_path_replacement_after_held_fd_probe(tmp_path: Path):
    inputs, provider, _, committer = _reach_fetch(tmp_path)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    before = committer._read_manifest()
    state = before.attempts[-1].video_generation_state
    assert state is not None and state.fetch_receipt is not None
    fetch_path = tmp_path / state.fetch_receipt.artifact_path
    original_preparer = make_p8_video_candidate_preparer(inputs)

    def replacing_preparer(*args):
        fetch_path.write_bytes(b"X" * fetch_path.stat().st_size)
        return original_preparer(*args)

    tampering_committer = ProductionStateCommitter(
        tmp_path,
        video_candidate_preparer=replacing_preparer,
    )
    with pytest.raises(AiVideoError, match="changed after held-file validation"):
        tampering_committer.prepare_video_activation_candidate(
            attempt_id=ATTEMPT_ID
        )

    after = tampering_committer._read_manifest()
    attempt = after.attempts[-1]
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.VALIDATE
    assert attempt.candidate_project is None
    assert not (tmp_path / "assets/files" / f"{state.fetch_receipt.artifact_sha256}.mp4").exists()


def test_candidate_rejects_unsettled_budget_before_any_candidate_write(tmp_path: Path):
    _, provider, _, committer = _reach_fetch(tmp_path, settle=False)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    before_files = tuple(
        sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    )

    with pytest.raises(AiVideoError, match="settled evidence"):
        committer.prepare_video_activation_candidate(attempt_id=ATTEMPT_ID)

    after = committer._read_manifest()
    attempt = after.attempts[-1]
    assert attempt.video_generation_state is not None
    assert attempt.video_generation_state.phase is VideoAttemptPhase.VALIDATE
    assert attempt.candidate_project is None
    assert tuple(
        sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file())
    ) == before_files


@pytest.mark.parametrize(
    "invalid_measurement",
    (
        "non_mp4",
        "multiple_video_streams",
        "duration",
        "resolution",
        "fps",
        "frame_count",
        "native_audio",
        "oversize",
        "empty",
    ),
)
def test_generated_video_probe_rejects_invalid_measured_artifacts(
    tmp_path: Path,
    invalid_measurement: str,
):
    _, provider, resolved, committer = _reach_fetch(tmp_path)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    state = committer._read_manifest().attempts[-1].video_generation_state
    assert state is not None and state.fetch_receipt is not None
    fetch_receipt = load_video_fetch_receipt(tmp_path, state.fetch_receipt)
    source_path = tmp_path / state.fetch_receipt.artifact_path
    max_size_bytes = 1 if invalid_measurement == "oversize" else 2_147_483_648

    if invalid_measurement == "empty":
        source_path = tmp_path / "state/video-generation/fetch/empty.mp4"
        source_path.write_bytes(b"")
        fetch_receipt = fetch_receipt.model_copy(
            update={
                "size_bytes": 0,
                "artifact_sha256": hashlib.sha256(b"").hexdigest(),
            }
        )

    def invalid_probe(held_fd: int):
        measured = deepcopy(probe_clip_fd(held_fd))
        video = next(
            item for item in measured["streams"] if item.get("codec_type") == "video"
        )
        if invalid_measurement == "non_mp4":
            measured["format"]["format_name"] = "matroska"
        elif invalid_measurement == "multiple_video_streams":
            measured["streams"].append(dict(video))
        elif invalid_measurement == "duration":
            video["duration"] = "2.0"
        elif invalid_measurement == "resolution":
            video["width"] = 65
        elif invalid_measurement == "fps":
            video["avg_frame_rate"] = "25/1"
        elif invalid_measurement == "frame_count":
            video["nb_frames"] = "25"
        elif invalid_measurement == "native_audio":
            measured["streams"].append({"codec_type": "audio"})
        return measured

    with _open_regular_file_nofollow(
        source_path,
        contained_by=tmp_path / "state/video-generation/fetch",
    ) as (held_fd, _):
        with pytest.raises(AiVideoError) as exc_info:
            probe_generated_video_candidate(
                held_fd,
                resolved,
                fetch_receipt,
                probe=invalid_probe,
                max_size_bytes=max_size_bytes,
            )

    assert exc_info.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID
