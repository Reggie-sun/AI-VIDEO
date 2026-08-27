from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from ai_video.production.models import (
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    RuntimeSeal,
    StackComponentIdentity,
)
from ai_video.production.video_transition import (
    BoundaryKind,
    CandidateStackBinding,
    CausalDimension,
    CausalEdgeSemantics,
    CausalStateChange,
    CausalTransitionMode,
    ContinuityAnchorBinding,
    ContinuityAnchorRole,
    ContinuityObligation,
    ContinuityTransitionPolicy,
    CreativeArtifactIdentity,
    MotionCoverage,
    P0QualificationInput,
    P0QualificationPreparedReceipt,
    RealShotValidationSet,
    ValidationEdgeBinding,
)


HASHES = tuple(f"{index:x}" * 64 for index in range(1, 16))
TEST_PROMPT = """For the target video, <Picture 1> supplies the exact first frame; <Picture 2> supplies the exact last frame; <Picture 3> supplies identity; <Video 1> supplies motion.

integrated_multimodal_description: [Shot 1] Live-action subject. The camera tracks with small amplitude at slow speed.
overall_soundscape: Rain and footsteps.
non_diegetic_music: No non-diegetic music."""


def _calibration_payload(*, prompt: str = TEST_PROMPT) -> dict[str, object]:
    return {
        "source_aspect_ratio": "7:4",
        "source_dimensions": [1659, 948],
        "target_canvas": [1344, 768],
        "target_tensor_layout": "BHWC",
        "target_tensor_shape": [1, 768, 1344, 3],
        "target_tensor_dtype": "float32_normalized_0_to_1",
        "dimension_multiple": 32,
        "exact_scale_ratio": "64/79",
        "preprocessing": {
            "first_frame": "lanczos_crop_disabled_isotropic",
            "last_frame": "lanczos_center_crop_no_crop_at_exact_7_to_4",
            "reference": "match_area_round32_resolves_1344x768",
        },
        "task_type": "Hybrid",
        "role_mapping": {
            "first_frame": "conditioning.first_frame",
            "last_frame": "conditioning.last_frame",
            "reference": "ref_images.ref_image_0",
            "reference_video": "ref_videos.ref_video_0",
        },
        "ref_video_audios": [],
        "ref_audios": [],
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "frame_count": 124,
        "fps": 24,
        "steps": 20,
        "sampler": "dual_clock_euler",
        "scheduler": "native_flow",
        "turbo_lora": False,
        "output_container": "mp4",
        "output_crf": 17,
        "native_audio": True,
    }


def _project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=canonical_project_snapshot_path(1, HASHES[0]),
        revision=1,
        content_hash=HASHES[0],
        file_sha256=HASHES[1],
    )


def _registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=canonical_registry_snapshot_path(HASHES[2]),
        revision_id=HASHES[2],
        content_hash=HASHES[2],
        file_sha256=HASHES[3],
    )


def _stack(candidate_id: str, component_hash: str) -> GenerationExecutionStackIdentity:
    return GenerationExecutionStackIdentity.create(
        materialization_status="materialized",
        candidate_id=candidate_id,
        contract_version="1",
        provider_kind="comfyui",
        deployment_identity="loopback-127.0.0.1-8188",
        model_id="minimax-h3-t8",
        capability_id="c4-native-boundary-motion",
        profile_hash=HASHES[0],
        compiler_hash=HASHES[1],
        workflow_hash="none",
        components=(
            StackComponentIdentity(
                ordinal=0,
                kind="checkpoint",
                component_id="ref2va-stock20",
                content_hash=component_hash,
            ),
        ),
        sampler_identity="dual_clock_euler",
        scheduler_identity="native_flow",
        runtime_seals=(
            RuntimeSeal(
                name="comfyui",
                version="0.33.2",
                content_hash=HASHES[4],
            ),
            RuntimeSeal(
                name="minimax-h3-turbo-plugin",
                version="1.36.2",
                content_hash=HASHES[5],
            ),
        ),
        output_contract_hash=HASHES[6],
    )


def _shot(number: int) -> CreativeArtifactIdentity:
    return CreativeArtifactIdentity(
        artifact_id=f"shot-rainy-station-{number}",
        revision=1,
        content_hash=f"{number + 1:x}" * 64,
    )


def _anchors() -> tuple[ContinuityAnchorBinding, ...]:
    return (
        ContinuityAnchorBinding(
            role=ContinuityAnchorRole.FIRST_FRAME,
            source_kind="planned_derivation",
            source_identity="shot-1-terminal-frame",
            content_hash=HASHES[7],
            evidence_fingerprint=HASHES[8],
        ),
        ContinuityAnchorBinding(
            role=ContinuityAnchorRole.LAST_FRAME,
            source_kind="registered_asset",
            source_identity="image-a2",
            content_hash=HASHES[9],
            evidence_fingerprint=HASHES[10],
            materialization_receipt_id="receipt-a2",
        ),
        ContinuityAnchorBinding(
            role=ContinuityAnchorRole.REFERENCE,
            source_kind="registered_asset",
            source_identity="image-character-master",
            content_hash=HASHES[11],
            evidence_fingerprint=HASHES[12],
            materialization_receipt_id="receipt-character-master",
        ),
        ContinuityAnchorBinding(
            role=ContinuityAnchorRole.REFERENCE_VIDEO,
            source_kind="planned_derivation",
            source_identity="shot-1-motion-tail",
            content_hash=HASHES[13],
            evidence_fingerprint=HASHES[14],
        ),
    )


def _policy(
    *,
    source: int,
    target: int,
    stack_hash: str,
    boundary_kind: BoundaryKind = BoundaryKind.HARD_CUT,
    obligation: ContinuityObligation = ContinuityObligation.FULL_CONTINUITY,
) -> ContinuityTransitionPolicy:
    return ContinuityTransitionPolicy.create(
        policy_id=f"edge-{source}-{target}",
        project=_project_pointer(),
        registry=_registry_pointer(),
        source_shot=_shot(source),
        target_shot=_shot(target),
        boundary_kind=boundary_kind,
        continuity_obligation=obligation,
        take_id=(
            "take-rainy-station"
            if boundary_kind is BoundaryKind.WITHIN_CONTINUOUS_TAKE
            else None
        ),
        source_execution_stack_hash=stack_hash,
        destination_execution_stack_hash=stack_hash,
        continuity_grade="c4_native_boundary_motion",
        required_carryover_dimensions=tuple(sorted((
            "identity",
            "wardrobe",
            "screen_axis",
            "action_phase",
            "camera_velocity",
        ))),
        anchors=_anchors(),
        qa_policy_hash=HASHES[4],
        authoring_evidence_hash=HASHES[5],
    )


def _causal_policy(
    *,
    semantics: CausalEdgeSemantics,
    changes: tuple[CausalStateChange, ...],
    boundary_kind: BoundaryKind = BoundaryKind.HARD_CUT,
    obligation: ContinuityObligation = ContinuityObligation.FULL_CONTINUITY,
) -> ContinuityTransitionPolicy:
    original = _policy(
        source=1,
        target=2,
        stack_hash=HASHES[0],
        boundary_kind=boundary_kind,
        obligation=obligation,
    )
    base = {
        field: getattr(original, field)
        for field in type(original).model_fields
        if field
        not in {
            "schema_version",
            "source_generation_intent_hash",
            "target_generation_intent_hash",
            "causal_edge_semantics",
            "causal_state_changes",
            "policy_hash",
        }
    }
    return ContinuityTransitionPolicy.create(
        **base,
        schema_version="2",
        source_generation_intent_hash=HASHES[6],
        target_generation_intent_hash=HASHES[7],
        causal_edge_semantics=semantics,
        causal_state_changes=changes,
    )


def test_visible_holder_change_requires_named_bridge_beat() -> None:
    with pytest.raises(ValidationError, match="named bridge beat"):
        CausalStateChange(
            dimension=CausalDimension.PROP_HOLDER,
            source_close="elder",
            target_open="girl",
            transition_mode=CausalTransitionMode.VISIBLE_CHANGE,
        )


def test_direct_edge_rejects_unexplained_character_disappearance() -> None:
    change = CausalStateChange(
        dimension=CausalDimension.CHARACTER_PRESENCE,
        source_close="elder present",
        target_open="elder absent",
        transition_mode=CausalTransitionMode.AUTHORIZED_RELEASE,
    )

    with pytest.raises(ValidationError, match="direct continuity cannot authorize"):
        _causal_policy(
            semantics=CausalEdgeSemantics.DIRECT_CONTINUITY,
            changes=(change,),
        )


def test_commercial_cut_can_explicitly_release_character_presence() -> None:
    change = CausalStateChange(
        dimension=CausalDimension.CHARACTER_PRESENCE,
        source_close="elder present",
        target_open="packshot has no cast",
        transition_mode=CausalTransitionMode.AUTHORIZED_RELEASE,
    )

    policy = _causal_policy(
        semantics=CausalEdgeSemantics.COMMERCIAL_CUT,
        changes=(change,),
        obligation=ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
    )

    assert policy.schema_version == "2"
    assert policy.causal_state_changes == (change,)


def test_continuous_take_rejects_reset_or_commercial_cut_semantics() -> None:
    change = CausalStateChange(
        dimension=CausalDimension.CHARACTER_PRESENCE,
        source_close="elder present",
        target_open="elder absent",
        transition_mode=CausalTransitionMode.AUTHORIZED_RELEASE,
    )

    with pytest.raises(ValidationError, match="continuous take requires direct"):
        _causal_policy(
            semantics=CausalEdgeSemantics.COMMERCIAL_CUT,
            changes=(change,),
            boundary_kind=BoundaryKind.WITHIN_CONTINUOUS_TAKE,
        )


def test_full_continuity_rejects_commercial_or_ellipsis_release() -> None:
    change = CausalStateChange(
        dimension=CausalDimension.CHARACTER_PRESENCE,
        source_close="elder present",
        target_open="elder absent",
        transition_mode=CausalTransitionMode.AUTHORIZED_RELEASE,
    )

    for semantics in (
        CausalEdgeSemantics.COMMERCIAL_CUT,
        CausalEdgeSemantics.CAUSAL_ELLIPSIS,
    ):
        with pytest.raises(
            ValidationError,
            match="full continuity requires direct",
        ):
            _causal_policy(semantics=semantics, changes=(change,))


def test_execution_stack_identity_is_content_addressed_and_component_drift_changes_hash():
    first = _stack("m0-ref2va-stock20", HASHES[7])
    replay = _stack("m0-ref2va-stock20", HASHES[7])
    drifted = _stack("m0-ref2va-stock20", HASHES[8])

    assert first == replay
    assert first.status == "qualification_candidate"
    assert first.workflow_hash == "none"
    assert first.execution_stack_hash != drifted.execution_stack_hash


def test_p0_qualification_input_is_content_addressed_and_rejects_local_path_material():
    first = P0QualificationInput.create(
        input_kind="calibration_fixture",
        input_id="rainy-station-c4-v1",
        payload=_calibration_payload(),
    )
    drifted = P0QualificationInput.create(
        input_kind="calibration_fixture",
        input_id="rainy-station-c4-v1",
        payload=_calibration_payload(
            prompt=TEST_PROMPT.replace("Rain and footsteps", "Rain, footsteps and wind")
        ),
    )
    assert first.content_hash != drifted.content_hash

    invalid_geometry = _calibration_payload()
    invalid_geometry["source_dimensions"] = [7, 4]
    with pytest.raises(ValidationError):
        P0QualificationInput.create(
            input_kind="calibration_fixture",
            input_id="wrong-source-geometry",
            payload=invalid_geometry,
        )

    with pytest.raises(ValidationError):
        P0QualificationInput.create(
            input_kind="inventory",
            input_id="unsafe-inventory",
            payload={"checkpoint": "/home/operator/model.safetensors"},
        )


def test_execution_stack_requires_contiguous_components_and_canonical_runtime_seals():
    values = _stack("m0-ref2va-stock20", HASHES[7]).model_dump(mode="python")
    values["components"] = (
        StackComponentIdentity(
            ordinal=1,
            kind="checkpoint",
            component_id="late",
            content_hash=HASHES[8],
        ),
    )
    values["execution_stack_hash"] = HASHES[0]
    with pytest.raises(ValidationError):
        GenerationExecutionStackIdentity.model_validate(values)

    with pytest.raises(ValidationError):
        StackComponentIdentity(
            ordinal=0,
            kind="artifact",
            component_id="missing-hybrid",
            presence="absent",
            content_hash=HASHES[8],
        )

    absent = StackComponentIdentity(
        ordinal=0,
        kind="artifact",
        component_id="missing-hybrid",
        presence="absent",
        content_hash="none",
    )
    assert absent.model_dump(mode="json") == {
        "ordinal": 0,
        "kind": "artifact",
        "component_id": "missing-hybrid",
        "presence": "absent",
        "content_hash": "none",
    }

    values = _stack("m0-ref2va-stock20", HASHES[7]).model_dump(mode="python")
    values["runtime_seals"] = tuple(reversed(values["runtime_seals"]))
    values["execution_stack_hash"] = HASHES[0]
    with pytest.raises(ValidationError):
        GenerationExecutionStackIdentity.model_validate(values)


def test_transition_policy_rejects_cross_stack_continuous_take_and_incomplete_anchors():
    stack = _stack("m0-ref2va-stock20", HASHES[7])
    values = _policy(
        source=1,
        target=2,
        stack_hash=stack.execution_stack_hash,
        boundary_kind=BoundaryKind.WITHIN_CONTINUOUS_TAKE,
    ).model_dump(mode="python")
    values["take_id"] = "take-1"
    values["destination_execution_stack_hash"] = HASHES[0]
    values["policy_hash"] = HASHES[1]
    with pytest.raises(ValidationError):
        ContinuityTransitionPolicy.model_validate(values)

    values = _policy(source=1, target=2, stack_hash=stack.execution_stack_hash).model_dump(
        mode="python"
    )
    values["anchors"] = values["anchors"][:-1]
    values["policy_hash"] = HASHES[1]
    with pytest.raises(ValidationError):
        ContinuityTransitionPolicy.model_validate(values)


def test_transition_policy_reset_requires_scene_boundary_and_no_carryover():
    stack = _stack("m0-ref2va-stock20", HASHES[7])
    base = _policy(source=1, target=2, stack_hash=stack.execution_stack_hash)
    reset = ContinuityTransitionPolicy.create(
        policy_id=base.policy_id,
        project=base.project,
        registry=base.registry,
        source_shot=base.source_shot,
        target_shot=base.target_shot,
        boundary_kind=BoundaryKind.SCENE_BOUNDARY,
        continuity_obligation=ContinuityObligation.SUBSTANTIAL_RESET,
        take_id=None,
        source_execution_stack_hash=base.source_execution_stack_hash,
        destination_execution_stack_hash=base.destination_execution_stack_hash,
        continuity_grade=base.continuity_grade,
        required_carryover_dimensions=(),
        anchors=(),
        qa_policy_hash=base.qa_policy_hash,
        authoring_evidence_hash=base.authoring_evidence_hash,
    )
    assert reset.continuity_obligation is ContinuityObligation.SUBSTANTIAL_RESET

    invalid = reset.model_dump(mode="python")
    invalid["required_carryover_dimensions"] = ("identity",)
    invalid["policy_hash"] = HASHES[0]
    with pytest.raises(ValidationError):
        ContinuityTransitionPolicy.model_validate(invalid)


def test_real_shot_validation_set_requires_adjacent_edges_and_both_motion_classes():
    stack = _stack("m0-ref2va-stock20", HASHES[7])
    policies = tuple(
        _policy(source=source, target=source + 1, stack_hash=stack.execution_stack_hash)
        for source in range(1, 4)
    )
    validation_set = RealShotValidationSet.create(
        validation_set_id="rainy-station-four-shot-v1",
        project=_project_pointer(),
        registry=_registry_pointer(),
        character=CreativeArtifactIdentity(
            artifact_id="character-traveler",
            revision=1,
            content_hash=HASHES[6],
        ),
        scene=CreativeArtifactIdentity(
            artifact_id="scene-rainy-station",
            revision=1,
            content_hash=HASHES[7],
        ),
        shots=tuple(_shot(number) for number in range(1, 5)),
        edges=(
            ValidationEdgeBinding(
                source_shot_id="shot-rainy-station-1",
                target_shot_id="shot-rainy-station-2",
                policy_hash=policies[0].policy_hash,
                motion_coverage=(MotionCoverage.SUBJECT_MOTION,),
            ),
            ValidationEdgeBinding(
                source_shot_id="shot-rainy-station-2",
                target_shot_id="shot-rainy-station-3",
                policy_hash=policies[1].policy_hash,
                motion_coverage=(MotionCoverage.CAMERA_MOTION,),
            ),
            ValidationEdgeBinding(
                source_shot_id="shot-rainy-station-3",
                target_shot_id="shot-rainy-station-4",
                    policy_hash=policies[2].policy_hash,
                    motion_coverage=(MotionCoverage.CAMERA_MOTION, MotionCoverage.SUBJECT_MOTION),
            ),
        ),
        human_freeze_evidence_hash=HASHES[8],
        rubric_hash=HASHES[9],
    )
    assert len(validation_set.shots) == 4
    assert len(validation_set.edges) == 3

    invalid = validation_set.model_dump(mode="python")
    invalid["edges"][0]["target_shot_id"] = "shot-rainy-station-3"
    invalid["content_hash"] = HASHES[0]
    with pytest.raises(ValidationError):
        RealShotValidationSet.model_validate(invalid)


def test_p0_receipt_binds_exactly_m0_and_m1_without_outcome_semantics():
    m0 = _stack("m0-ref2va-stock20", HASHES[7])
    m1 = _stack("m1-hybrid-stock20", HASHES[8])
    receipt = P0QualificationPreparedReceipt.create(
        receipt_id="rainy-station-p0-v1",
        project=_project_pointer(),
        registry=_registry_pointer(),
        inventory_receipt_hash=HASHES[4],
        calibration_fixture_hash=HASHES[5],
        rubric_hash=HASHES[6],
        effect_budget_hash=HASHES[7],
        human_freeze_evidence_hash=HASHES[8],
        validation_set_hash=HASHES[9],
        policy_hashes=(HASHES[10], HASHES[11], HASHES[12]),
        candidate_stacks=(
            CandidateStackBinding(label="m0", execution_stack_hash=m0.execution_stack_hash),
            CandidateStackBinding(label="m1", execution_stack_hash=m1.execution_stack_hash),
        ),
        limitations=("No media generated.", "No capability activated."),
    )
    assert receipt.status == "qualification_prepared"

    duplicate = receipt.model_dump(mode="python")
    duplicate["candidate_stacks"][1]["execution_stack_hash"] = duplicate[
        "candidate_stacks"
    ][0]["execution_stack_hash"]
    duplicate["content_hash"] = HASHES[0]
    with pytest.raises(ValidationError):
        P0QualificationPreparedReceipt.model_validate(duplicate)

    with pytest.raises(ValidationError):
        P0QualificationPreparedReceipt.model_validate(
            {**receipt.model_dump(mode="python"), "winner": "m0"}
        )
