from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    DependencyLifecycle,
    EvidenceStrength,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaPolicyPointer,
    QaTechnicalThresholds,
    ProductionManifest,
    RegistryDependencyEvidence,
    SourceReference,
    StateCommitStatus,
    ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production._video_project_reader import (
    load_terminal_frame_evidence,
    load_video_fetch_receipt,
    load_video_request_receipt,
    load_video_status_receipt,
)
from ai_video.production.image import (
    ContinuityTerminalImageReferenceBinding,
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageProviderParameters,
    ImageReferenceBinding,
)
from ai_video.production.hyperframes import probe_clip_fd
from ai_video.production.paths import (
    _open_regular_file_nofollow,
    canonical_image_request_path,
    canonical_qa_policy_path,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.review import (
    ContinuityEvaluationIntent,
    GeneratedShotContinuityEvidence,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video import (
    BillingKind,
    ContinuityConstraintSet,
    HardCutKeyframeBinding,
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
from ai_video.production.video_artifact import (
    _default_terminal_frame_extractor,
    probe_generated_video_candidate,
)
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.project import load_production_project
from production_project_factory import (
    _p7_png,
    make_p7_image_candidate_preparer,
    make_p8_video_candidate_preparer,
    make_p8_video_generation_base,
)
from test_production_state_commit import make_image_provider_result
from test_production_video import (
    _continuity_binding,
    _paid_authorization,
    _paid_preview,
    _terminal_frame,
)


FIXTURE = Path(__file__).parent / "fixtures/generated_video/fake-video.mp4"
ATTEMPT_ID = "p8-generated-video-e2e"
CONTINUITY_EVALUATOR = ToolIdentity(
    name="fixture-durable-continuity-evaluator", version="1"
)


def _runtime(
    root: Path, *, seal_terminal_frame: bool = False, continuity: bool = False
):
    inputs = make_p8_video_generation_base(
        root,
        schema_version=(
            "2.9" if continuity else "2.8" if seal_terminal_frame else "2.7"
        ),
    )
    loaded = inputs.project
    if continuity:
        policy = seal_artifact(
            QaPolicy(
                artifact_id="qa-policy-continuity-evaluator-v1",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id="qa-policy-continuity-evaluator-v1",
                source_provenance=(
                    SourceReference(kind="derived", reference="continuity-fixture"),
                ),
                policy_id="qa-continuity-evaluator-v1",
                policy_version="1",
                required_layers=(QaLayer.SEMANTIC,),
                technical_thresholds=QaTechnicalThresholds(
                    black_luma_max_milli=10,
                    silence_peak_max_millidb=-60_000,
                    clipping_peak_min_millidb=-100,
                ),
                layout_rules=QaLayoutRules(
                    safe_area_inset_milli=50,
                    caption_overflow_tolerance_milli=0,
                ),
                strategy_rules_version="1",
                semantic_requirement="required",
                semantic_authorities=(CONTINUITY_EVALUATOR,),
            )
        )
        policy_bytes = policy.model_dump_json().encode("utf-8")
        policy_path = canonical_qa_policy_path(policy.content_hash)
        (root / policy_path).parent.mkdir(parents=True, exist_ok=True)
        (root / policy_path).write_bytes(policy_bytes)
        policy_pointer = QaPolicyPointer(
            path=policy_path,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            content_hash=policy.content_hash,
            file_sha256=hashlib.sha256(policy_bytes).hexdigest(),
        )
        manifest_path = root / "state/manifest.json"
        manifest = loaded.manifest.model_copy(
            update={
                "manifest_revision": loaded.manifest.manifest_revision + 1,
                "active_qa_policy": policy_pointer,
            }
        )
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        loaded = load_production_project(root / "project.yaml")
        inputs = replace(inputs, project=loaded)
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
    continuity_binding = None
    image_bindings = (
        VideoImageReferenceBinding(
            role="first_frame",
            asset_id=source.asset_id,
            asset_sha256=source.sha256,
            mime_type=source.mime_type,
            width=source.width or 64,
            height=source.height or 64,
            size_bytes=source.size_bytes,
        ),
    )
    input_artifact_ids = (shot.artifact_id, source.asset_id)
    if continuity:
        source_shot = loaded.shots[1]
        terminal = _terminal_frame(
            source_shot_id=source_shot.shot_id,
            source_shot_revision=source_shot.revision,
            source_shot_content_hash=source_shot.content_hash,
            source_video_asset_id=loaded.registry.assets[1].asset_id,
            extracted_asset_id=source.asset_id,
            extracted_sha256=source.sha256,
            extracted_mime_type=source.mime_type,
            extracted_width=source.width or 64,
            extracted_height=source.height or 64,
            extracted_size_bytes=source.size_bytes,
        )
        continuity_binding = _continuity_binding(
            terminal_frame=terminal,
            target_shot_id=shot.shot_id,
            target_shot_revision=shot.revision,
            target_shot_content_hash=shot.content_hash,
        )
        input_artifact_ids = (
            shot.artifact_id,
            terminal.source_shot_id,
            terminal.source_video_asset_id,
            source.asset_id,
        )
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
        image_bindings=image_bindings,
        continuity_binding=continuity_binding,
        seal_terminal_frame=seal_terminal_frame,
        output_requirement=output,
        seed=17,
        base_project=loaded.manifest.active_project,
        base_registry=loaded.manifest.active_registry,
        base_dependency_graph=loaded.manifest.active_dependency_graph,
        input_artifact_ids=input_artifact_ids,
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


def _reach_fetch(
    root: Path,
    *,
    settle: bool = True,
    seal_terminal_frame: bool = False,
    continuity: bool = False,
):
    inputs, provider, resolved, paid_preview, committer = _runtime(
        root, seal_terminal_frame=seal_terminal_frame, continuity=continuity
    )
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


def test_terminal_frame_is_extracted_registered_activated_and_replayed_exactly(
    tmp_path: Path,
):
    inputs, provider, resolved, committer = _reach_fetch(
        tmp_path, seal_terminal_frame=True
    )
    service = VideoGenerationService(committer=committer, provider=provider)

    activated = service.fetch_and_activate(attempt_id=ATTEMPT_ID)
    selected = load_production_project(tmp_path / "project.yaml")
    state = activated.attempts[-1].video_generation_state

    assert state is not None
    assert state.terminal_frame_evidence is not None
    assert state.candidate_video_asset_ids == (resolved.output_asset_id,)
    assert state.candidate_continuity_asset_ids == (
        f"{resolved.output_asset_id}:terminal-frame",
    )
    video_asset, terminal_asset = selected.registry.assets[-2:]
    assert video_asset.asset_id == resolved.output_asset_id
    assert video_asset.video_metadata is not None
    provenance_payload = json.loads(
        (
            tmp_path
            / "state/video-generation/provenance"
            / f"{video_asset.video_metadata.provenance_receipt_id}.json"
        ).read_text(encoding="utf-8")
    )
    assert "paid_submit_receipt_fingerprint" in provenance_payload
    assert "local_submit_result_fingerprint" not in provenance_payload
    assert terminal_asset.asset_id == state.terminal_frame_evidence.extracted_asset_id
    assert terminal_asset.input_artifact_ids == (video_asset.asset_id,)
    assert (tmp_path / terminal_asset.artifact_path).read_bytes().startswith(
        b"\x89PNG\r\n\x1a\n"
    )
    evidence_path = tmp_path / state.terminal_frame_evidence.path
    terminal_path = tmp_path / terminal_asset.artifact_path
    before = (evidence_path.read_bytes(), terminal_path.read_bytes())

    replayed = service.fetch_and_activate(attempt_id=ATTEMPT_ID)

    assert replayed == activated
    assert (evidence_path.read_bytes(), terminal_path.read_bytes()) == before


def test_hard_cut_keyframe_activation_reopens_exact_terminal_and_replays_zero_call(
    tmp_path: Path,
) -> None:
    inputs, provider, _, source_committer = _reach_fetch(
        tmp_path, seal_terminal_frame=True
    )
    VideoGenerationService(
        committer=source_committer, provider=provider
    ).fetch_and_activate(attempt_id=ATTEMPT_ID)
    selected = load_production_project(tmp_path / "project.yaml")
    source_state = selected.manifest.attempts[-1].video_generation_state
    assert source_state is not None and source_state.terminal_frame_evidence is not None
    terminal = load_terminal_frame_evidence(
        tmp_path, source_state.terminal_frame_evidence
    )
    target = selected.shots[1]
    character = selected.characters[0]
    scene = selected.scenes[0]
    assets = {asset.asset_id: asset for asset in selected.registry.assets}
    character_asset = assets[character.reference_asset_ids[0]]
    terminal_asset = assets[terminal.extracted_asset_id]
    constraints = ContinuityConstraintSet.create(
        scene_identity={
            "artifact_id": scene.artifact_id,
            "revision": scene.revision,
            "content_hash": scene.content_hash,
        },
        character_identities=(
            {
                "artifact_id": character.artifact_id,
                "revision": character.revision,
                "content_hash": character.content_hash,
            },
        ),
        camera_axis="camera-left-of-door-table-axis",
        framing="hard-cut-medium-from-medium-wide",
        lighting="window-key-camera-left",
        color="neutral-warm-red-scarf",
        motion_direction="screen-left-to-right",
        exit_state="right-hand-on-chair-back",
        entrance_state="right-hand-on-chair-back-continuing",
    )
    request = ImageGenerationRequest.create(
        attempt_id="hard-cut-keyframe-image",
        provider_kind="fake-local",
        model_id="fixture-image-model-1",
        target_shot_id=target.shot_id,
        target_asset_role=target.required_asset_roles[0].role,
        prompt_text="Alice continues from the chair-touch exit state in a new medium framing.",
        negative_prompt_text="identity drift, axis reversal, changed wardrobe",
        parameters=ImageProviderParameters(
            seed=23,
            width=2,
            height=1,
            output_format="png",
            generation_revision=1,
        ),
        references=(
            ImageReferenceBinding(
                role="character",
                creative_artifact_id=character.artifact_id,
                creative_revision=character.revision,
                creative_content_hash=character.content_hash,
                asset_id=character_asset.asset_id,
                asset_sha256=character_asset.sha256,
            ),
            ContinuityTerminalImageReferenceBinding.create(
                role="continuity_terminal",
                terminal_frame=terminal,
                asset_id=terminal_asset.asset_id,
                asset_sha256=terminal_asset.sha256,
                target_shot_id=target.shot_id,
                target_shot_revision=target.revision,
                target_shot_content_hash=target.content_hash,
                constraints=constraints,
            ),
        ),
        base_project=selected.manifest.active_project,
        base_registry=selected.manifest.active_registry,
        base_dependency_graph=selected.manifest.active_dependency_graph,
    )
    preview = ImageGenerationPreview.create(
        request=request,
        reference_total_bytes=character_asset.size_bytes + terminal_asset.size_bytes,
    )
    authorization = ImageGenerationAuthorization.create(
        request=request,
        preview=preview,
        usage_license="fixture-only",
        policy_receipt_id="hard-cut-local-policy",
    )

    class _Provider:
        calls = 0

        def generate(self, candidate, candidate_authorization, permit):
            self.calls += 1
            assert permit._consume_image_generation_permit(
                request_fingerprint=candidate.request_fingerprint
            )
            return make_image_provider_result(
                candidate,
                candidate_authorization,
                _p7_png(),
            )

    image_provider = _Provider()
    prepare = make_p7_image_candidate_preparer(inputs)
    prepare_calls = 0

    def _prepare(*args, **kwargs):
        nonlocal prepare_calls
        prepare_calls += 1
        candidate = prepare(*args, **kwargs)
        return candidate

    image_committer = ProductionStateCommitter(
        tmp_path,
        image_candidate_preparer=_prepare,
    )
    activated = image_committer.generate_image_asset(
        request,
        preview,
        authorization,
        image_provider,
    )
    reopened = load_production_project(tmp_path / "project.yaml")

    assert activated.schema_version == "2.8"
    assert reopened.manifest == activated
    assert request.output_asset_id in {
        asset_id
        for role in reopened.shots[1].required_asset_roles
        for asset_id in role.asset_ids
    }
    replayed = image_committer.generate_image_asset(
        request,
        preview,
        authorization,
        image_provider,
    )
    assert replayed == activated
    assert image_provider.calls == 1
    assert prepare_calls == 1

    keyframe_project = reopened
    target = keyframe_project.shots[1]
    keyframe = next(
        asset
        for asset in keyframe_project.registry.assets
        if asset.asset_id == request.output_asset_id
    )
    hard_cut = HardCutKeyframeBinding.create(
        role="hard_cut_keyframe",
        terminal_frame=terminal,
        keyframe_asset_id=keyframe.asset_id,
        keyframe_asset_sha256=keyframe.sha256,
        keyframe_mime_type="image/png",
        keyframe_width=keyframe.width,
        keyframe_height=keyframe.height,
        keyframe_size_bytes=keyframe.size_bytes,
        keyframe_request_fingerprint=request.request_fingerprint,
        keyframe_provenance_receipt_id=keyframe.creation_receipt_id,
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        constraints=constraints,
    )
    video_output = VideoOutputRequirement(
        duration_seconds=1,
        width=64,
        height=64,
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )
    profile_sha = "e" * 64
    video_request = VideoGenerationRequest.create(
        generation_id="hard-cut-video-generation",
        provider_name="fake-hard-cut-video",
        provider_kind="fake_video",
        model_id="fake-h264",
        provider_profile=ProviderProfilePointer(
            profile_id="fake-hard-cut-profile",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile_sha}.json"),
            profile_sha256=profile_sha,
        ),
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        target_asset_role=target.required_asset_roles[0].role,
        target_visual_strategy="generated_video",
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text="Alice pulls the chair and sits without changing axis or wardrobe.",
        negative_prompt_text="identity drift, axis reversal, lighting change",
        image_bindings=(
            VideoImageReferenceBinding(
                role="first_frame",
                asset_id=keyframe.asset_id,
                asset_sha256=keyframe.sha256,
                mime_type=keyframe.mime_type,
                width=keyframe.width,
                height=keyframe.height,
                size_bytes=keyframe.size_bytes,
            ),
        ),
        hard_cut_keyframe_binding=hard_cut,
        output_requirement=video_output,
        seed=29,
        base_project=keyframe_project.manifest.active_project,
        base_registry=keyframe_project.manifest.active_registry,
        base_dependency_graph=keyframe_project.manifest.active_dependency_graph,
        input_artifact_ids=(target.artifact_id, keyframe.asset_id),
        output_asset_id="video-output-hard-cut-shot-2",
    )
    variant = VideoCapabilityVariant(
        capability_id="fake-hard-cut-i2v",
        provider_kind="fake_video",
        model_id="fake-h264",
        profile_version="v1",
        execution_kind=VideoExecutionKind.REMOTE,
        billing_kind=BillingKind.METERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        output=video_output,
        allowed_image_roles=("first_frame",),
        required_first_frame=True,
        max_reference_count=0,
        allowed_image_mime_types=("image/png",),
        max_image_bytes=max(keyframe.size_bytes, 1),
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=True,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=False,
        lookup_supported=False,
    )
    video_provider = ScriptedFakeVideoProvider(
        capabilities=VideoProviderCapabilities.create(
            provider_name="fake-hard-cut-video", variants=(variant,)
        ),
        artifact_bytes=FIXTURE.read_bytes(),
        scenario=FakeVideoScenario(
            external_effect_id="fake-hard-cut-task-2",
            provider_file_id="fake-hard-cut-file-2",
        ),
    )
    resolved_video = video_provider.resolve(video_request)
    video_preview = video_provider.preview(resolved_video)
    paid_preview = _paid_preview(
        resolved_video,
        attempt_id="hard-cut-video-attempt",
        video_preview=video_preview,
    )
    paid_authorization = _paid_authorization(paid_preview)
    video_committer = ProductionStateCommitter(
        tmp_path,
        video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        paid_provider_authorizer=(
            lambda exact: paid_authorization if exact == paid_preview else None
        ),
        paid_provider_clock=lambda: paid_authorization.issued_at,
    )
    video_service = VideoGenerationService(
        committer=video_committer,
        provider=video_provider,
    )
    video_service.start(
        attempt_id="hard-cut-video-attempt",
        request=resolved_video,
    )
    video_service.submit_once(
        attempt_id="hard-cut-video-attempt",
        paid_preview=paid_preview,
        reservation_id="hard-cut-video-reservation",
    )
    video_service.refresh_once(attempt_id="hard-cut-video-attempt")
    video_service.refresh_once(attempt_id="hard-cut-video-attempt")
    video_service.refresh_once(attempt_id="hard-cut-video-attempt")
    video_committer.settle_paid_provider_reservation(
        attempt_id="hard-cut-video-attempt",
        actual_cost_microunits=1_000_000,
    )
    video_activated = video_service.fetch_and_activate(
        attempt_id="hard-cut-video-attempt"
    )
    final_project = load_production_project(tmp_path / "project.yaml")
    before_replay = video_provider.call_counts
    video_replayed = video_service.fetch_and_activate(
        attempt_id="hard-cut-video-attempt"
    )

    assert final_project.manifest == video_activated
    assert video_replayed == video_activated
    assert video_provider.call_counts == before_replay
    assert video_provider.call_counts.submit == 1
    assert video_provider.call_counts.fetch == 1
    recovered = ProductionStateCommitter(tmp_path).recover()
    assert recovered.manifest_revision_before == video_activated.manifest_revision
    assert recovered.manifest_revision_after == video_activated.manifest_revision
    assert load_production_project(tmp_path / "project.yaml").manifest == video_activated
    assert video_provider.call_counts == before_replay

    (tmp_path / canonical_image_request_path(request.request_fingerprint)).write_text(
        "{}\n", encoding="utf-8"
    )
    with pytest.raises(AiVideoError, match="P7 image candidate history"):
        load_production_project(tmp_path / "project.yaml")


def test_terminal_frame_replay_rejects_tampered_evidence(tmp_path: Path):
    _, provider, _, committer = _reach_fetch(
        tmp_path, seal_terminal_frame=True
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    activated = service.fetch_and_activate(attempt_id=ATTEMPT_ID)
    state = activated.attempts[-1].video_generation_state
    assert state is not None and state.terminal_frame_evidence is not None
    (tmp_path / state.terminal_frame_evidence.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError, match="terminal frame evidence"):
        service.fetch_and_activate(attempt_id=ATTEMPT_ID)


def test_active_project_reader_rejects_tampered_terminal_frame_evidence(
    tmp_path: Path,
):
    _, provider, _, committer = _reach_fetch(tmp_path, seal_terminal_frame=True)
    activated = VideoGenerationService(
        committer=committer, provider=provider
    ).fetch_and_activate(attempt_id=ATTEMPT_ID)
    state = activated.attempts[-1].video_generation_state
    assert state is not None and state.terminal_frame_evidence is not None
    (tmp_path / state.terminal_frame_evidence.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError, match="terminal frame evidence"):
        load_production_project(tmp_path / "project.yaml")


def test_active_project_reader_rejects_tampered_terminal_extraction_receipt(
    tmp_path: Path,
):
    _, provider, _, committer = _reach_fetch(tmp_path, seal_terminal_frame=True)
    activated = VideoGenerationService(
        committer=committer, provider=provider
    ).fetch_and_activate(attempt_id=ATTEMPT_ID)
    state = activated.attempts[-1].video_generation_state
    assert state is not None and state.terminal_frame_extraction is not None
    (tmp_path / state.terminal_frame_extraction.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError, match="terminal frame extraction"):
        load_production_project(tmp_path / "project.yaml")


def test_terminal_extraction_checkpoint_prevents_repeat_after_candidate_failure(
    tmp_path: Path,
):
    inputs, provider, _, _ = _reach_fetch(tmp_path, seal_terminal_frame=True)
    extraction_calls = 0

    def counted_extractor(source: bytes, frame_index: int):
        nonlocal extraction_calls
        extraction_calls += 1
        return _default_terminal_frame_extractor(source, frame_index)

    def failing_preparer(*_args):
        raise RuntimeError("candidate preparation interrupted")

    interrupted = VideoGenerationService(
        committer=ProductionStateCommitter(
            tmp_path, video_candidate_preparer=failing_preparer
        ),
        provider=provider,
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        interrupted.fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            terminal_frame_extractor=counted_extractor,
        )
    checkpointed = ProductionStateCommitter(tmp_path)._read_manifest()
    checkpoint_state = checkpointed.attempts[-1].video_generation_state
    assert checkpoint_state is not None
    assert checkpoint_state.terminal_frame_extraction is not None
    assert extraction_calls == 1
    ProductionStateCommitter(tmp_path).recover()

    resumed = VideoGenerationService(
        committer=ProductionStateCommitter(
            tmp_path,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    )
    resumed.fetch_and_activate(
        attempt_id=ATTEMPT_ID,
        terminal_frame_extractor=counted_extractor,
    )

    assert extraction_calls == 1


class _CountingDurableContinuityReviewer:
    def __init__(self, *, fail_during_evaluation: bool = False) -> None:
        self.calls = 0
        self.fail_during_evaluation = fail_during_evaluation
        self.intent: ContinuityEvaluationIntent | None = None

    def create_intent(self, request, measured, qa_policy_content_hash):
        binding = request.continuity_binding
        original = request.activation_scope.request
        assert binding is not None
        self.intent = ContinuityEvaluationIntent.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=CONTINUITY_EVALUATOR,
            evaluator_profile_content_hash="f" * 64,
        )
        return self.intent

    def __call__(self, held_fd, request, measured, qa_policy_content_hash):
        del held_fd
        self.calls += 1
        if self.fail_during_evaluation:
            raise RuntimeError("evaluator interrupted after durable intent")
        assert self.intent is not None
        binding = request.continuity_binding
        original = request.activation_scope.request
        assert binding is not None
        return GeneratedShotContinuityEvidence.create(
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=measured.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=qa_policy_content_hash,
            evaluator=CONTINUITY_EVALUATOR,
            strength=EvidenceStrength.HUMAN,
            coverage_complete=True,
            identity_match=True,
            camera_axis_match=True,
            framing_match=True,
            motion_direction_match=True,
            entrance_state_match=True,
            exit_state_match=True,
            unexpected_reentry=False,
            evaluation_fingerprint=self.intent.evaluation_fingerprint,
            rationale="Fixture human reviewed every exact continuity dimension.",
        )


def test_continuity_evidence_checkpoint_prevents_repeat_after_candidate_failure(
    tmp_path: Path,
) -> None:
    inputs, provider, _, committer = _reach_fetch(tmp_path, continuity=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    reviewer = _CountingDurableContinuityReviewer()

    def failing_preparer(*_args):
        raise RuntimeError("candidate preparation interrupted")

    interrupted = VideoGenerationService(
        committer=ProductionStateCommitter(
            tmp_path, video_candidate_preparer=failing_preparer
        ),
        provider=provider,
    )
    with pytest.raises(RuntimeError, match="candidate preparation interrupted"):
        interrupted.fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            continuity_reviewer=reviewer,
        )
    checkpointed = ProductionStateCommitter(tmp_path)._read_manifest()
    checkpoint_state = checkpointed.attempts[-1].video_generation_state
    assert checkpoint_state is not None
    assert checkpoint_state.continuity_evaluation is not None
    assert checkpoint_state.continuity_evaluation.phase.value == "evidenced"
    assert reviewer.calls == 1
    ProductionStateCommitter(tmp_path).recover()

    resumed = VideoGenerationService(
        committer=ProductionStateCommitter(
            tmp_path,
            video_candidate_preparer=make_p8_video_candidate_preparer(inputs),
        ),
        provider=provider,
    )
    activated = resumed.fetch_and_activate(attempt_id=ATTEMPT_ID)
    replayed = resumed.fetch_and_activate(attempt_id=ATTEMPT_ID)

    assert replayed == activated
    assert reviewer.calls == 1
    historical_shape = activated.model_dump(mode="json")
    historical_shape["schema_version"] = "2.8"
    with pytest.raises(ValueError, match="Manifest 2.9 is required"):
        ProductionManifest.model_validate(historical_shape)


def test_continuity_intent_only_retry_never_repeats_unknown_evaluator(
    tmp_path: Path,
) -> None:
    _, provider, _, committer = _reach_fetch(tmp_path, continuity=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    reviewer = _CountingDurableContinuityReviewer(fail_during_evaluation=True)
    service = VideoGenerationService(committer=committer, provider=provider)

    with pytest.raises(AiVideoError, match="evaluator failed"):
        service.fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            continuity_reviewer=reviewer,
        )
    assert reviewer.calls == 1
    with pytest.raises(AiVideoError) as unknown:
        service.fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            continuity_reviewer=reviewer,
        )

    assert unknown.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert reviewer.calls == 1


def test_recovery_rejects_tampered_continuity_evidence_checkpoint(
    tmp_path: Path,
) -> None:
    _, provider, _, committer = _reach_fetch(tmp_path, continuity=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    reviewer = _CountingDurableContinuityReviewer()

    def failing_preparer(*_args):
        raise RuntimeError("candidate preparation interrupted")

    with pytest.raises(RuntimeError, match="candidate preparation interrupted"):
        VideoGenerationService(
            committer=ProductionStateCommitter(
                tmp_path, video_candidate_preparer=failing_preparer
            ),
            provider=provider,
        ).fetch_and_activate(
            attempt_id=ATTEMPT_ID,
            continuity_reviewer=reviewer,
        )
    manifest = ProductionStateCommitter(tmp_path)._read_manifest()
    state = manifest.attempts[-1].video_generation_state
    assert state is not None and state.continuity_evaluation is not None
    assert state.continuity_evaluation.evidence is not None
    (tmp_path / state.continuity_evaluation.evidence.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError) as rejected:
        ProductionStateCommitter(tmp_path).recover()

    assert rejected.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


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


@pytest.mark.parametrize("seal_terminal_frame", (False, True))
def test_candidate_recovery_keeps_old_tuple_until_explicit_activation(
    tmp_path: Path, seal_terminal_frame: bool
):
    inputs, provider, _, committer = _reach_fetch(
        tmp_path, seal_terminal_frame=seal_terminal_frame
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.fetch_once(attempt_id=ATTEMPT_ID)
    base = committer._read_manifest()
    candidate = committer.prepare_video_activation_candidate(attempt_id=ATTEMPT_ID)
    candidate_attempt = candidate.attempts[-1]
    assert candidate_attempt.video_generation_state is not None
    assert candidate_attempt.video_generation_state.phase is VideoAttemptPhase.CANDIDATE
    assert bool(
        candidate_attempt.video_generation_state.terminal_frame_evidence
    ) is seal_terminal_frame
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


def test_candidate_recovery_rejects_tampered_terminal_frame_evidence(
    tmp_path: Path,
):
    _, provider, _, committer = _reach_fetch(
        tmp_path, seal_terminal_frame=True
    )
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    candidate = committer.prepare_video_activation_candidate(
        attempt_id=ATTEMPT_ID
    )
    state = candidate.attempts[-1].video_generation_state
    assert state is not None and state.terminal_frame_evidence is not None
    (tmp_path / state.terminal_frame_evidence.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


def test_activation_rejects_tampered_terminal_extraction_receipt(tmp_path: Path):
    _, provider, _, committer = _reach_fetch(tmp_path, seal_terminal_frame=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    candidate = committer.prepare_video_activation_candidate(
        attempt_id=ATTEMPT_ID
    )
    state = candidate.attempts[-1].video_generation_state
    assert state is not None and state.terminal_frame_extraction is not None
    (tmp_path / state.terminal_frame_extraction.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError, match="terminal frame extraction"):
        committer.activate_video_candidate(attempt_id=ATTEMPT_ID)


def test_candidate_recovery_rejects_tampered_terminal_extraction_receipt(
    tmp_path: Path,
):
    _, provider, _, committer = _reach_fetch(tmp_path, seal_terminal_frame=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    candidate = committer.prepare_video_activation_candidate(
        attempt_id=ATTEMPT_ID
    )
    state = candidate.attempts[-1].video_generation_state
    assert state is not None and state.terminal_frame_extraction is not None
    (tmp_path / state.terminal_frame_extraction.path).write_text(
        "{}", encoding="utf-8"
    )

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


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
