from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    P0QualificationPreparedReceiptPointer,
    ProductionManifest,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RegistrySnapshotPointer,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.paths import (
    canonical_continuity_transition_policy_path,
    canonical_execution_stack_identity_path,
    canonical_p0_qualification_input_path,
    canonical_p0_qualification_receipt_path,
    canonical_real_shot_validation_set_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import CommitPhase, ProductionStateCommitter
from ai_video.production._state_commit_common import _validated_transition
from ai_video.production.video_execution_stack import (
    ExecutionStackMaterialization,
    GenerationExecutionStackIdentity,
    RuntimeSeal,
    StackComponentIdentity,
)
from ai_video.production.video_transition import (
    BoundaryKind,
    CandidateStackBinding,
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
import production_project_factory as project_factory


HASHES = tuple(f"{index:x}" * 64 for index in range(1, 16))
TEST_PROMPT = """For the target video, <Picture 1> supplies the exact first frame; <Picture 2> supplies the exact last frame; <Picture 3> supplies identity; <Video 1> supplies motion.

integrated_multimodal_description: [Shot 1] Live-action subject. The camera tracks with small amplitude at slow speed.
overall_soundscape: Rain and footsteps.
non_diegetic_music: No non-diegetic music."""


def _calibration_payload() -> dict[str, object]:
    return {
        "source_images": [],
        "source_format": "PNG RGB",
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
        "prompt": TEST_PROMPT,
        "prompt_sha256": hashlib.sha256(TEST_PROMPT.encode("utf-8")).hexdigest(),
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


def _stack(label: str, component_hash: str) -> GenerationExecutionStackIdentity:
    return GenerationExecutionStackIdentity.create(
        materialization_status="unmaterialized",
        candidate_id=f"{label}-rainy-station-stock20",
        contract_version="1",
        provider_kind="comfyui",
        deployment_identity="loopback-127.0.0.1-8188",
        model_id="minimax-h3-t8",
        capability_id="c4-native-boundary-motion",
        profile_hash="none",
        compiler_hash="none",
        workflow_hash="none",
        components=(
            StackComponentIdentity(
                ordinal=0,
                kind="checkpoint",
                component_id=f"{label}-checkpoint",
                content_hash=component_hash,
            ),
        ),
        sampler_identity="dual_clock_euler",
        scheduler_identity="native_flow",
        runtime_seals=(
            RuntimeSeal(
                name="comfyui",
                version="0.33.2",
                content_hash=HASHES[2],
            ),
        ),
        output_contract_hash=canonical_sha256(
            {
                "width": 1344,
                "height": 768,
                "frames": 124,
                "fps": 24,
                "container": "mp4",
                "crf": 17,
                "native_audio": True,
            }
        ),
    )


def _bundle(root: Path):
    loaded = project_factory.write_and_load_multi_shot_project(
        root,
        filenames=("a1.png", "a2.png", "a3.png", "a4.png"),
        seconds=(3.0, 3.0, 3.0, 3.0),
        decodable_pngs=True,
        asset_role="approved_endpoint",
        content_addressed_receipts=True,
    )
    writer = ProductionStateCommitter(root)
    upgraded = writer.upgrade_manifest_schema(
        "2.11", expected_manifest_revision=loaded.manifest.manifest_revision
    )
    loaded = load_production_project(root / "project.yaml")
    assert loaded.manifest == upgraded

    m0 = _stack("m0", HASHES[4])
    m1 = _stack("m1", HASHES[5])
    m1 = GenerationExecutionStackIdentity.create(
        schema_version=m1.schema_version,
        status=m1.status,
        materialization_status=m1.materialization_status,
        candidate_id=m1.candidate_id,
        contract_version=m1.contract_version,
        provider_kind=m1.provider_kind,
        deployment_identity=m1.deployment_identity,
        model_id=m1.model_id,
        capability_id=m1.capability_id,
        profile_hash=m1.profile_hash,
        compiler_hash=m1.compiler_hash,
        workflow_hash=m1.workflow_hash,
        components=(
            m1.components[0],
            StackComponentIdentity(
                ordinal=1,
                kind="artifact",
                component_id="hybrid-artifact-candidate-v1",
                presence="absent",
                content_hash="none",
            ),
        ),
        sampler_identity=m1.sampler_identity,
        scheduler_identity=m1.scheduler_identity,
        runtime_seals=m1.runtime_seals,
        output_contract_hash=m1.output_contract_hash,
    )
    shot_identities = tuple(
        CreativeArtifactIdentity(
            artifact_id=shot.artifact_id,
            revision=shot.revision,
            content_hash=shot.content_hash,
        )
        for shot in loaded.shots
    )
    rubric = P0QualificationInput.create(
        input_kind="rubric",
        input_id="rainy-station-rubric-v1",
        payload={
            "boundary": {
                "decoded_first_and_last_required": True,
                "perceptual_backend_missing": (
                    "NOT_EVALUATED_requires_exact_human_review"
                ),
            },
            "sequence": {
                "raw_full_speed_review_required": True,
                "crossfade_optical_flow_interpolation_retime_forbidden": True,
            },
            "verdict_owner": "P6",
            "human_evidence_required": True,
        },
    )
    human_freeze = P0QualificationInput.create(
        input_kind="human_freeze",
        input_id="rainy-station-human-freeze-v1",
        payload={
            "approved_candidate_order": ["A1", "A2", "A3", "A4"],
            "approval_scope": "freeze_source_candidates_for_P0_only",
            "not_claimed": ["creative_PASS", "P6_PASS", "Final_Acceptance"],
        },
    )

    def anchors(index: int) -> tuple[ContinuityAnchorBinding, ...]:
        source = shot_identities[index]
        return (
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.FIRST_FRAME,
                source_kind="planned_derivation",
                source_identity=f"{source.artifact_id}:terminal-frame",
                content_hash=canonical_sha256(
                    {
                        "derivation": "exact-terminal-frame/1",
                        "source_shot": source.model_dump(mode="json"),
                    }
                ),
                evidence_fingerprint=canonical_sha256(
                    {"kind": "terminal", "source": source.content_hash}
                ),
            ),
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.LAST_FRAME,
                source_kind="registered_asset",
                source_identity=loaded.registry.assets[index + 1].asset_id,
                content_hash=loaded.registry.assets[index + 1].sha256,
                evidence_fingerprint=(
                    loaded.registry.assets[index + 1].creation_receipt_id
                ),
                materialization_receipt_id=(
                    loaded.registry.assets[index + 1].creation_receipt_id
                ),
            ),
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.REFERENCE,
                source_kind="registered_asset",
                source_identity=loaded.registry.assets[0].asset_id,
                content_hash=loaded.registry.assets[0].sha256,
                evidence_fingerprint=loaded.registry.assets[0].creation_receipt_id,
                materialization_receipt_id=loaded.registry.assets[0].creation_receipt_id,
            ),
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.REFERENCE_VIDEO,
                source_kind="planned_derivation",
                source_identity=f"{source.artifact_id}:motion-tail",
                content_hash=canonical_sha256(
                    {
                        "derivation": "exact-motion-tail/1",
                        "source_shot": source.model_dump(mode="json"),
                    }
                ),
                evidence_fingerprint=canonical_sha256(
                    {"kind": "motion-tail", "source": source.content_hash}
                ),
            ),
        )

    policies = tuple(
        ContinuityTransitionPolicy.create(
            policy_id=f"edge-{index + 1}-{index + 2}",
            project=loaded.manifest.active_project,
            registry=loaded.manifest.active_registry,
            source_shot=shot_identities[index],
            target_shot=shot_identities[index + 1],
            boundary_kind=BoundaryKind.HARD_CUT,
            continuity_obligation=ContinuityObligation.FULL_CONTINUITY,
            take_id=None,
            source_execution_stack_hash=m0.execution_stack_hash,
            destination_execution_stack_hash=m0.execution_stack_hash,
            continuity_grade="c4_native_boundary_motion",
            required_carryover_dimensions=(
                "action_phase",
                "camera_velocity",
                "identity",
                "screen_axis",
                "wardrobe",
            ),
            anchors=anchors(index),
            qa_policy_hash=rubric.content_hash,
            authoring_evidence_hash=human_freeze.content_hash,
        )
        for index in range(3)
    )
    qualification_inputs = (
        P0QualificationInput.create(
            input_kind="inventory",
            input_id="local-t8-inventory-v1",
            payload={
                "components": [
                    {
                        "id": "m0-checkpoint",
                        "presence": "present",
                        "sha256": HASHES[4],
                    },
                    {
                        "id": "m1-checkpoint",
                        "presence": "present",
                        "sha256": HASHES[5],
                    },
                    {
                        "id": "hybrid-artifact-candidate-v1",
                        "presence": "absent",
                        "sha256": "none",
                    },
                ],
                "hybrid_artifact_present": False,
                "remote_provider_enabled": False,
                "cloud_fallback_enabled": False,
            },
        ),
        P0QualificationInput.create(
            input_kind="calibration_fixture",
            input_id="rainy-station-c4-fixture-v1",
            payload=_calibration_payload(),
        ),
        rubric,
        P0QualificationInput.create(
            input_kind="effect_budget",
            input_id="rainy-station-effect-budget-v1",
            payload={
                "provider": "loopback_local_comfyui",
                "submits_per_generation": 1,
                "retry": False,
                "fallback": False,
                "remote": False,
                "paid": False,
                "automatic_activation": False,
                "unknown_outcome": "explicit_recovery_only",
            },
        ),
        human_freeze,
    )
    inputs_by_kind = {item.input_kind: item for item in qualification_inputs}
    validation_set = RealShotValidationSet.create(
        validation_set_id="rainy-station-four-shot-v1",
        project=loaded.manifest.active_project,
        registry=loaded.manifest.active_registry,
        character=CreativeArtifactIdentity(
            artifact_id=loaded.characters[0].artifact_id,
            revision=loaded.characters[0].revision,
            content_hash=loaded.characters[0].content_hash,
        ),
        scene=CreativeArtifactIdentity(
            artifact_id=loaded.scenes[0].artifact_id,
            revision=loaded.scenes[0].revision,
            content_hash=loaded.scenes[0].content_hash,
        ),
        shots=shot_identities,
        edges=(
            ValidationEdgeBinding(
                source_shot_id=shot_identities[0].artifact_id,
                target_shot_id=shot_identities[1].artifact_id,
                policy_hash=policies[0].policy_hash,
                motion_coverage=(MotionCoverage.SUBJECT_MOTION,),
            ),
            ValidationEdgeBinding(
                source_shot_id=shot_identities[1].artifact_id,
                target_shot_id=shot_identities[2].artifact_id,
                policy_hash=policies[1].policy_hash,
                motion_coverage=(MotionCoverage.CAMERA_MOTION,),
            ),
            ValidationEdgeBinding(
                source_shot_id=shot_identities[2].artifact_id,
                target_shot_id=shot_identities[3].artifact_id,
                policy_hash=policies[2].policy_hash,
                motion_coverage=(MotionCoverage.CAMERA_MOTION, MotionCoverage.SUBJECT_MOTION),
            ),
        ),
        human_freeze_evidence_hash=inputs_by_kind["human_freeze"].content_hash,
        rubric_hash=inputs_by_kind["rubric"].content_hash,
    )
    receipt = P0QualificationPreparedReceipt.create(
        receipt_id="rainy-station-p0-v1",
        project=loaded.manifest.active_project,
        registry=loaded.manifest.active_registry,
        inventory_receipt_hash=inputs_by_kind["inventory"].content_hash,
        calibration_fixture_hash=inputs_by_kind["calibration_fixture"].content_hash,
        rubric_hash=inputs_by_kind["rubric"].content_hash,
        effect_budget_hash=inputs_by_kind["effect_budget"].content_hash,
        human_freeze_evidence_hash=inputs_by_kind["human_freeze"].content_hash,
        validation_set_hash=validation_set.content_hash,
        policy_hashes=tuple(sorted(item.policy_hash for item in policies)),
        candidate_stacks=(
            CandidateStackBinding(label="m0", execution_stack_hash=m0.execution_stack_hash),
            CandidateStackBinding(label="m1", execution_stack_hash=m1.execution_stack_hash),
        ),
        limitations=("No media generated.", "No capability activated."),
    )
    return (
        writer,
        loaded,
        m0,
        m1,
        policies,
        validation_set,
        qualification_inputs,
        receipt,
    )


def _replace_first_policy(
    *,
    policies: tuple[ContinuityTransitionPolicy, ...],
    validation_set: RealShotValidationSet,
    receipt: P0QualificationPreparedReceipt,
    updates: dict[str, object],
):
    base = policies[0]
    values = {
        name: getattr(base, name)
        for name in type(base).model_fields
        if name != "policy_hash"
    }
    replacement = ContinuityTransitionPolicy.create(**{**values, **updates})
    changed_policies = (replacement, *policies[1:])
    validation_values = {
        name: getattr(validation_set, name)
        for name in type(validation_set).model_fields
        if name != "content_hash"
    }
    changed_edges = (
        validation_set.edges[0].model_copy(
            update={"policy_hash": replacement.policy_hash}
        ),
        *validation_set.edges[1:],
    )
    changed_validation = RealShotValidationSet.create(
        **{**validation_values, "edges": changed_edges}
    )
    receipt_values = {
        name: getattr(receipt, name)
        for name in type(receipt).model_fields
        if name != "content_hash"
    }
    changed_receipt = P0QualificationPreparedReceipt.create(
        **{
            **receipt_values,
            "validation_set_hash": changed_validation.content_hash,
            "policy_hashes": tuple(
                sorted(item.policy_hash for item in changed_policies)
            ),
        }
    )
    return changed_policies, changed_validation, changed_receipt


def test_manifest_211_alone_can_select_p0_prepared_pointer():
    pointer = P0QualificationPreparedReceiptPointer(
        path=canonical_p0_qualification_receipt_path(HASHES[0]),
        content_hash=HASHES[0],
        file_sha256=HASHES[1],
    )
    base = ProductionManifest(
        schema_version="2.0",
        project_id="p0-pointer-test",
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=canonical_project_snapshot_path(1, HASHES[2]),
            revision=1,
            content_hash=HASHES[2],
            file_sha256=HASHES[3],
        ),
        active_registry=RegistrySnapshotPointer(
            path=canonical_registry_snapshot_path(HASHES[4]),
            revision_id=HASHES[4],
            content_hash=HASHES[4],
            file_sha256=HASHES[5],
        ),
    )
    with pytest.raises(ValidationError):
        ProductionManifest.model_validate(
            {
                **base.model_dump(mode="python"),
                "schema_version": "2.10",
                "active_p0_qualification_prepared": pointer,
            }
        )
    selected = ProductionManifest.model_validate(
        {
            **base.model_dump(mode="python"),
            "schema_version": "2.11",
            "active_p0_qualification_prepared": pointer,
        }
    )
    assert selected.active_p0_qualification_prepared == pointer


def test_p0_prepared_commit_is_reopenable_and_exact_replay_is_zero_write(tmp_path: Path):
    (
        writer,
        loaded,
        m0,
        m1,
        policies,
        validation_set,
        qualification_inputs,
        receipt,
    ) = _bundle(tmp_path)
    committed = writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=qualification_inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="rainy-station-p0",
    )
    before = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    replayed = writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=qualification_inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="rainy-station-p0-replay",
    )
    after = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert replayed == committed
    assert before == after
    reopened = writer.reopen_p0_qualification_prepared()
    assert reopened == (
        receipt,
        (m0, m1),
        policies,
        validation_set,
        qualification_inputs,
    )


def test_project_change_invalidates_selected_p0_preparation(tmp_path: Path):
    (
        writer,
        loaded,
        m0,
        m1,
        policies,
        validation_set,
        qualification_inputs,
        receipt,
    ) = _bundle(tmp_path)
    selected = writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=qualification_inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="rainy-station-p0",
    )

    changed = _validated_transition(
        selected,
        {
            "active_project": ProjectSnapshotPointer(
                path=canonical_project_snapshot_path(2, HASHES[0]),
                revision=2,
                content_hash=HASHES[0],
                file_sha256=HASHES[1],
            )
        },
    )

    assert changed.active_p0_qualification_prepared is None
    writer._write_manifest_atomic(changed)
    with pytest.raises(AiVideoError) as error:
        writer.reopen_p0_qualification_prepared()
    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_recovery_reopens_all_selected_p0_evidence_and_rejects_tamper(
    tmp_path: Path,
):
    (
        writer,
        loaded,
        m0,
        m1,
        policies,
        validation_set,
        qualification_inputs,
        receipt,
    ) = _bundle(tmp_path)
    manifest = writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=qualification_inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="rainy-station-p0",
    )

    report = writer.recover()
    active_paths = {
        item.path for item in report.items if item.disposition.value == "active"
    }
    assert manifest.active_p0_qualification_prepared.path in active_paths
    calibration = next(
        item
        for item in qualification_inputs
        if item.input_kind == "calibration_fixture"
    )
    calibration_path = canonical_p0_qualification_input_path(
        calibration.input_kind, calibration.content_hash
    )
    assert calibration_path in active_paths

    (tmp_path / calibration_path).write_text("{}\n", encoding="utf-8")
    with pytest.raises(AiVideoError) as error:
        writer.recover()
    assert error.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


def test_recovery_tracks_and_rehashes_materialized_source_artifacts(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-source-recovery-base",
    )
    materials = (_materialization("m0", 6), _materialization("m1", 9))
    writer.materialize_p0_qualification(
        materializations=materials,
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-source-recovery-materialize",
    )

    report = writer.recover()
    active_paths = {
        item.path for item in report.items if item.disposition.value == "active"
    }
    expected_sources = {
        _materialization_source_path(tmp_path, kind, content_hash).relative_to(tmp_path)
        for materialization in materials
        for kind, content_hash in (
            ("profile", materialization.profile_hash),
            ("compiler", materialization.compiler_hash),
            ("workflow", materialization.workflow_hash),
        )
    }
    assert expected_sources <= active_paths

    damaged = _materialization_source_path(
        tmp_path,
        "workflow",
        materials[0].workflow_hash,
    )
    damaged.write_bytes(b"damaged-workflow")
    with pytest.raises(AiVideoError) as error:
        writer.recover()
    assert error.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


def test_recovery_preserves_source_promoted_before_materialization_manifest(
    tmp_path: Path,
):
    class _CrashAfterFirstArtifactPromotion:
        def checkpoint(self, phase: CommitPhase) -> None:
            if phase is CommitPhase.AFTER_ARTIFACT_PROMOTION:
                raise RuntimeError("fixture crash after first artifact promotion")

    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    prepared = writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-source-orphan-base",
    )
    crashing = ProductionStateCommitter(
        tmp_path,
        crash_injector=_CrashAfterFirstArtifactPromotion(),
    )
    with pytest.raises(AiVideoError, match="promote immutable"):
        crashing.materialize_p0_qualification(
            materializations=(_materialization("m0", 6), _materialization("m1", 9)),
            expected_manifest_revision=prepared.manifest_revision,
            attempt_id="p0-source-orphan-materialize",
        )

    assert ProductionStateCommitter(tmp_path).reopen_p0_qualification_prepared()[0] == receipt
    source_paths = tuple(
        path.relative_to(tmp_path)
        for path in tmp_path.glob(
            "state/video-qualification/execution-stack-sources/*/*.bin"
        )
    )
    assert len(source_paths) == 1
    report = ProductionStateCommitter(tmp_path).recover()
    assert any(
        item.path == source_paths[0]
        and item.disposition is RecoveryDisposition.ORPHAN_PRESERVED
        for item in report.items
    )


def test_p0_commit_rejects_receipt_not_bound_to_current_project(tmp_path: Path):
    (
        writer,
        loaded,
        m0,
        m1,
        policies,
        validation_set,
        qualification_inputs,
        receipt,
    ) = _bundle(tmp_path)
    receipt_values = {
        name: getattr(receipt, name)
        for name in type(receipt).model_fields
        if name != "content_hash"
    }
    mismatched = P0QualificationPreparedReceipt.create(
        **{
            **receipt_values,
            "project": receipt.project.model_copy(update={"content_hash": HASHES[0]}),
        }
    )
    with pytest.raises(AiVideoError) as error:
        writer.record_p0_qualification_prepared(
            mismatched,
            candidate_stacks=(m0, m1),
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=qualification_inputs,
            expected_manifest_revision=loaded.manifest.manifest_revision,
            attempt_id="rainy-station-p0-mismatch",
        )
    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


@pytest.mark.parametrize(
    "case",
    (
        "shot_identity",
        "unselected_stack",
        "rubric",
        "human_freeze",
        "reference_membership",
        "anchor_evidence",
        "endpoint_membership",
        "planned_derivation",
    ),
)
def test_p0_commit_rejects_semantically_resealed_policy_drift(
    tmp_path: Path, case: str
):
    (
        writer,
        loaded,
        m0,
        m1,
        policies,
        validation_set,
        qualification_inputs,
        receipt,
    ) = _bundle(tmp_path)
    base = policies[0]
    updates: dict[str, object]
    if case == "shot_identity":
        updates = {
            "source_shot": base.source_shot.model_copy(
                update={"content_hash": HASHES[14]}
            )
        }
    elif case == "unselected_stack":
        updates = {"destination_execution_stack_hash": HASHES[14]}
    elif case == "rubric":
        updates = {"qa_policy_hash": HASHES[14]}
    elif case == "human_freeze":
        updates = {"authoring_evidence_hash": HASHES[14]}
    else:
        anchors = list(base.anchors)
        if case == "reference_membership":
            asset = loaded.registry.assets[2]
            index = next(
                i
                for i, item in enumerate(anchors)
                if item.role is ContinuityAnchorRole.REFERENCE
            )
            anchors[index] = anchors[index].model_copy(
                update={
                    "source_identity": asset.asset_id,
                    "content_hash": asset.sha256,
                    "evidence_fingerprint": asset.creation_receipt_id,
                    "materialization_receipt_id": asset.creation_receipt_id,
                }
            )
        elif case == "anchor_evidence":
            index = next(
                i
                for i, item in enumerate(anchors)
                if item.role is ContinuityAnchorRole.REFERENCE
            )
            anchors[index] = anchors[index].model_copy(
                update={"evidence_fingerprint": HASHES[14]}
            )
        elif case == "endpoint_membership":
            asset = loaded.registry.assets[0]
            index = next(
                i
                for i, item in enumerate(anchors)
                if item.role is ContinuityAnchorRole.LAST_FRAME
            )
            anchors[index] = anchors[index].model_copy(
                update={
                    "source_identity": asset.asset_id,
                    "content_hash": asset.sha256,
                    "evidence_fingerprint": asset.creation_receipt_id,
                    "materialization_receipt_id": asset.creation_receipt_id,
                }
            )
        else:
            index = next(
                i
                for i, item in enumerate(anchors)
                if item.role is ContinuityAnchorRole.FIRST_FRAME
            )
            anchors[index] = anchors[index].model_copy(
                update={"content_hash": HASHES[14]}
            )
        updates = {"anchors": tuple(anchors)}
    changed_policies, changed_validation, changed_receipt = _replace_first_policy(
        policies=policies,
        validation_set=validation_set,
        receipt=receipt,
        updates=updates,
    )

    with pytest.raises(AiVideoError) as error:
        writer.record_p0_qualification_prepared(
            changed_receipt,
            candidate_stacks=(m0, m1),
            policies=changed_policies,
            validation_set=changed_validation,
            qualification_inputs=qualification_inputs,
            expected_manifest_revision=loaded.manifest.manifest_revision,
            attempt_id=f"rainy-station-p0-{case}",
        )
    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_p0_commit_rejects_resealed_inventory_that_no_longer_binds_stacks(
    tmp_path: Path,
) -> None:
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(
        tmp_path
    )
    changed_payload = dict(inputs[0].payload)
    changed_components = [dict(item) for item in changed_payload["components"]]
    changed_components[0]["sha256"] = HASHES[14]
    changed_payload["components"] = changed_components
    changed_inventory = P0QualificationInput.create(
        input_kind="inventory",
        input_id=inputs[0].input_id,
        payload=changed_payload,
    )
    receipt_values = {
        name: getattr(receipt, name)
        for name in type(receipt).model_fields
        if name != "content_hash"
    }
    receipt_values["inventory_receipt_hash"] = changed_inventory.content_hash
    changed_receipt = P0QualificationPreparedReceipt.create(**receipt_values)

    with pytest.raises(AiVideoError) as error:
        writer.record_p0_qualification_prepared(
            changed_receipt,
            candidate_stacks=(m0, m1),
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=(changed_inventory, *inputs[1:]),
            expected_manifest_revision=loaded.manifest.manifest_revision,
            attempt_id="rainy-station-p0-inventory-drift",
        )
    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_p0_commit_rejects_resealed_stack_that_no_longer_binds_calibration(
    tmp_path: Path,
) -> None:
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(
        tmp_path
    )
    stack_values = {
        name: getattr(m1, name)
        for name in type(m1).model_fields
        if name != "execution_stack_hash"
    }
    stack_values["output_contract_hash"] = HASHES[14]
    changed_m1 = GenerationExecutionStackIdentity.create(**stack_values)
    receipt_values = {
        name: getattr(receipt, name)
        for name in type(receipt).model_fields
        if name != "content_hash"
    }
    receipt_values["candidate_stacks"] = (
        receipt.candidate_stacks[0],
        CandidateStackBinding(
            label="m1", execution_stack_hash=changed_m1.execution_stack_hash
        ),
    )
    changed_receipt = P0QualificationPreparedReceipt.create(**receipt_values)

    with pytest.raises(AiVideoError) as error:
        writer.record_p0_qualification_prepared(
            changed_receipt,
            candidate_stacks=(m0, changed_m1),
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=inputs,
            expected_manifest_revision=loaded.manifest.manifest_revision,
            attempt_id="rainy-station-p0-calibration-drift",
        )
    assert error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def _materialization(label: str, profile_index: int) -> ExecutionStackMaterialization:
    return ExecutionStackMaterialization.from_bytes(
        candidate_label=label,
        profile_bytes=HASHES[profile_index].encode(),
        compiler_bytes=HASHES[profile_index + 1].encode(),
        workflow_bytes=HASHES[profile_index + 2].encode(),
    )


def _materialization_source_path(
    root: Path,
    kind: str,
    content_hash: str,
) -> Path:
    return (
        root
        / "state/video-qualification/execution-stack-sources"
        / kind
        / f"{content_hash}.bin"
    )


def test_unmaterialized_p0_denies_execution_stack_use(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-unmaterialized",
    )
    with pytest.raises(AiVideoError, match="materialized"):
        writer.reopen_p0_qualification_prepared(require_materialized=True)


def test_materialization_reseals_all_stack_dependents_and_keeps_m1_absent(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-materialize-base",
    )
    before = writer.reopen_p0_qualification_prepared()
    manifest = writer.materialize_p0_qualification(
        materializations=(_materialization("m0", 6), _materialization("m1", 9)),
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-materialize",
    )
    reopened = writer.reopen_p0_qualification_prepared(require_materialized=True)
    new_receipt, new_stacks, new_policies, new_set, new_inputs = reopened
    assert manifest.manifest_revision == loaded.manifest.manifest_revision + 2
    assert all(item.materialization_status == "materialized" for item in new_stacks)
    assert tuple(item.execution_stack_hash for item in new_stacks) != tuple(
        item.execution_stack_hash for item in before[1]
    )
    assert tuple(item.policy_hash for item in new_policies) != tuple(
        item.policy_hash for item in before[2]
    )
    assert new_set.content_hash != before[3].content_hash
    assert new_receipt.content_hash != before[0].content_hash
    assert all(item.execution_stack_hashes == tuple(sorted(item.execution_stack_hashes)) for item in new_inputs)
    assert all(item.execution_stack_hashes == tuple(sorted(stack.execution_stack_hash for stack in new_stacks)) for item in new_inputs)
    assert new_stacks[1].components[1].presence == "absent"
    assert new_stacks[1].components[1].content_hash == "none"


def test_materialization_persists_exact_content_addressed_source_bytes(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-materialize-source-base",
    )
    materials = (_materialization("m0", 6), _materialization("m1", 9))
    writer.materialize_p0_qualification(
        materializations=materials,
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-materialize-source",
    )

    for materialization in materials:
        for kind in ("profile", "compiler", "workflow"):
            content_hash = getattr(materialization, f"{kind}_hash")
            payload = getattr(materialization, f"{kind}_bytes")
            assert _materialization_source_path(
                tmp_path, kind, content_hash
            ).read_bytes() == payload


@pytest.mark.parametrize("damage", ("missing", "tampered", "swapped", "symlink"))
def test_materialized_source_artifact_damage_fails_closed(
    tmp_path: Path,
    damage: str,
):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id=f"p0-materialize-source-{damage}-base",
    )
    materials = (_materialization("m0", 6), _materialization("m1", 9))
    writer.materialize_p0_qualification(
        materializations=materials,
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id=f"p0-materialize-source-{damage}",
    )
    profile_path = _materialization_source_path(
        tmp_path,
        "profile",
        materials[0].profile_hash,
    )
    if damage == "missing":
        profile_path.unlink()
    elif damage == "tampered":
        profile_path.write_bytes(b"tampered-profile")
    elif damage == "swapped":
        profile_path.write_bytes(materials[0].compiler_bytes)
    else:
        profile_path.unlink()
        profile_path.symlink_to(tmp_path / "project.yaml")

    with pytest.raises(AiVideoError, match="source"):
        writer.reopen_p0_qualification_prepared(require_materialized=True)


def test_materialized_stack_drift_and_stale_dependents_are_denied(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-materialize-drift-base",
    )
    writer.materialize_p0_qualification(
        materializations=(_materialization("m0", 6), _materialization("m1", 9)),
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-materialize-drift",
    )
    with pytest.raises(AiVideoError, match="drift"):
        writer.materialize_p0_qualification(
            materializations=(_materialization("m0", 7), _materialization("m1", 9)),
            expected_manifest_revision=loaded.manifest.manifest_revision + 2,
            attempt_id="p0-materialize-drift-again",
        )
    with pytest.raises(AiVideoError):
        writer.record_p0_qualification_prepared(
            receipt,
            candidate_stacks=(m0, m1),
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=inputs,
            expected_manifest_revision=loaded.manifest.manifest_revision + 2,
            attempt_id="p0-stale-reseal",
        )


def test_materialized_bundle_cannot_be_written_through_preparation_owner(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-owner-base",
    )
    writer.materialize_p0_qualification(
        materializations=(_materialization("m0", 6), _materialization("m1", 9)),
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-owner-materialize",
    )
    materialized = writer.reopen_p0_qualification_prepared(require_materialized=True)
    with pytest.raises(AiVideoError, match="materialization owner"):
        writer.record_p0_qualification_prepared(
            materialized[0],
            candidate_stacks=materialized[1],
            policies=materialized[2],
            validation_set=materialized[3],
            qualification_inputs=materialized[4],
            expected_manifest_revision=loaded.manifest.manifest_revision + 2,
            attempt_id="p0-owner-bypass",
        )


def test_preparation_owner_rejects_materialized_input_before_initial_commit(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    materialized_m0 = m0.materialize(_materialization("m0", 6))
    with pytest.raises(AiVideoError, match="materialization owner"):
        writer.record_p0_qualification_prepared(
            receipt,
            candidate_stacks=(materialized_m0, m1),
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=inputs,
            expected_manifest_revision=loaded.manifest.manifest_revision,
            attempt_id="p0-owner-initial-bypass",
        )


def test_materialization_rejects_fabricated_artifact_hashes():
    with pytest.raises(ValidationError, match="artifact bytes"):
        ExecutionStackMaterialization(
            candidate_label="m0",
            profile_bytes=b"real-profile",
            compiler_bytes=b"real-compiler",
            workflow_bytes=b"real-workflow",
            profile_hash=HASHES[0],
            compiler_hash=HASHES[1],
            workflow_hash=HASHES[2],
        )


@pytest.mark.parametrize("dependency", ("stack", "policy", "validation", "input"))
def test_materialized_dependency_tamper_fails_closed(tmp_path: Path, dependency: str):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id=f"p0-tamper-{dependency}-base",
    )
    writer.materialize_p0_qualification(
        materializations=(_materialization("m0", 6), _materialization("m1", 9)),
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id=f"p0-tamper-{dependency}",
    )
    current = writer.reopen_p0_qualification_prepared(require_materialized=True)
    if dependency == "stack":
        relative = canonical_execution_stack_identity_path(current[1][0].execution_stack_hash)
    elif dependency == "policy":
        relative = canonical_continuity_transition_policy_path(current[2][0].policy_hash)
    elif dependency == "validation":
        relative = canonical_real_shot_validation_set_path(current[3].content_hash)
    else:
        item = next(item for item in current[4] if item.input_kind == "calibration_fixture")
        relative = canonical_p0_qualification_input_path(item.input_kind, item.content_hash)
    (tmp_path / relative).write_text("{}\n", encoding="utf-8")
    with pytest.raises(AiVideoError):
        writer.reopen_p0_qualification_prepared(require_materialized=True)


def test_materialization_tamper_and_exact_replay(tmp_path: Path):
    writer, loaded, m0, m1, policies, validation_set, inputs, receipt = _bundle(tmp_path)
    writer.record_p0_qualification_prepared(
        receipt,
        candidate_stacks=(m0, m1),
        policies=policies,
        validation_set=validation_set,
        qualification_inputs=inputs,
        expected_manifest_revision=loaded.manifest.manifest_revision,
        attempt_id="p0-materialize-replay-base",
    )
    materials = (_materialization("m0", 6), _materialization("m1", 9))
    committed = writer.materialize_p0_qualification(
        materializations=materials,
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-materialize-replay",
    )
    snapshot = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    replayed = writer.materialize_p0_qualification(
        materializations=materials,
        expected_manifest_revision=loaded.manifest.manifest_revision + 1,
        attempt_id="p0-materialize-replay-again",
    )
    assert replayed == committed
    assert snapshot == {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    stack_path = next(
        tmp_path.rglob(f"{committed.active_p0_qualification_prepared.content_hash}.json")
    )
    stack_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(AiVideoError):
        writer.reopen_p0_qualification_prepared(require_materialized=True)
