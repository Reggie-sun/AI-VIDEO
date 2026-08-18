from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    ActorIdentity,
    EvidenceStrength,
    FinalAcceptanceReceipt,
    ProductionManifest,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    QaVerdict,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
    SourceReference,
    StateCommitAttempt,
    ToolIdentity,
    VisualStrategy,
)
from ai_video.production.paths import canonical_review_evidence_path
from ai_video.production.project import (
    load_final_acceptance_receipt,
    load_production_project,
)
from ai_video.production.review import (
    ReviewIdentity,
    adjudicate_layer,
    adjudicate_review_evidence,
    adjudicate_visual_motion,
    build_technical_review_context,
    evaluate_final_acceptance,
    is_review_current,
    validate_technical_review_context,
)
from ai_video.production.state_commit import (
    ProductionStateCommitter,
    _canonical_json_bytes,
)
import production_project_factory as project_factory
from test_production_hyperframes import make_manifest_25_render_fixture


ZERO_HASH = "0" * 64


def _p7_attempts(manifest: ProductionManifest) -> tuple[StateCommitAttempt, ...]:
    return tuple(
        item for item in manifest.attempts if item.operation == "image_generation"
    )


def _qa_policy(
    *,
    required_layers: tuple[QaLayer, ...],
    repair_authorities: tuple[ActorIdentity, ...] = (),
) -> QaPolicy:
    return seal_artifact(
        QaPolicy(
            artifact_id="qa-policy-manifest-25-review",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="qa-policy-manifest-25-review",
            source_provenance=(
                SourceReference(kind="derived", reference="base-e2e-review-fixture"),
            ),
            policy_id="qa-manifest-25-review",
            policy_version="1",
            required_layers=required_layers,
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
            semantic_requirement="optional",
            repair_authorities=repair_authorities,
        )
    )


@dataclass(frozen=True)
class _Manifest25ReviewFixture:
    root: Path
    committer: ProductionStateCommitter
    timeline: object
    policy: QaPolicy
    review_layer: QaLayer = QaLayer.TECHNICAL
    review_fails: bool = False
    review_attempt_id: str = "base-e2e-technical-review"

    def load_manifest(self) -> ProductionManifest:
        return load_production_project(self.root / "project.yaml").manifest

    def run_required_review(self) -> ReviewReceiptPointer:
        bundle = load_production_project(self.root / "project.yaml")
        manifest = bundle.manifest
        assert manifest.active_dependency_graph is not None
        assert manifest.active_render_state is not None
        assert manifest.active_qa_policy is not None
        assert bundle.render_state is not None
        tool = ToolIdentity(name="base-e2e-analyzer", version="1")
        context = build_technical_review_context(
            bundle,
            self.timeline,
            render_output_sha256=bundle.render_state.output.file_sha256,
            measurement_contract_version="1",
        )
        request = seal_artifact(
            ReviewRequest(
                artifact_id="review-request-manifest-25",
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id="review-request-manifest-25",
                source_provenance=(
                    SourceReference(kind="derived", reference="base-e2e-review-fixture"),
                ),
                request_id="review-request-manifest-25",
                base_manifest_revision=manifest.manifest_revision,
                dependency_graph=manifest.active_dependency_graph,
                dependency_states_hash=canonical_sha256(
                    {
                        "dependency_states": [
                            item.model_dump(mode="json")
                            for item in manifest.dependency_states
                        ]
                    }
                ),
                render_state=manifest.active_render_state,
                render_output_sha256=bundle.render_state.output.file_sha256,
                timeline_fingerprint=bundle.render_state.timeline_fingerprint,
                qa_policy=manifest.active_qa_policy,
                requested_layers=(self.review_layer,),
                evidence_tool_identities=(tool,),
                technical_context=context,
            )
        )
        begun = self.committer.begin_review(
            request, attempt_id=self.review_attempt_id
        )
        request_pointer = begun.attempts[-1].review_request
        assert request_pointer is not None

        def analyze(durable_request, permit):
            assert permit._consume_review_analysis_permit(
                request_content_hash=durable_request.content_hash,
                render_output_sha256=durable_request.render_output_sha256,
                technical_context_hash=canonical_sha256(
                    durable_request.technical_context.model_dump(mode="json")
                ),
            )
            return durable_request

        self.committer.run_review_analysis(
            review_request=request_pointer,
            expected_manifest_revision=begun.manifest_revision,
            analyzer=analyze,
        )
        measured = self.load_manifest()
        if self.review_layer is QaLayer.LAYOUT:
            measured_payload = {
                "coverage_complete": True,
                "caption_overflow_milli": 1 if self.review_fails else 0,
                "safe_area_inset_milli": 50,
                "layer_collision_count": 0,
                "transition_boundary_violation_count": 0,
            }
        else:
            measured_payload = {
                "coverage_complete": True,
                "minimum_luma_milli": 500,
                "audio_peak_millidb": -1_000,
                "expects_audio": any(item.expects_audio for item in context.windows),
                "windows": [
                    {
                        "status": "measured",
                        "visual_strategy": item.visual_strategy.value,
                        "unique_frame_count": 1,
                    }
                    for item in context.windows
                ],
            }
        evidence = seal_artifact(
            ReviewEvidence(
                artifact_id=f"review-evidence-manifest-25-{self.review_layer.value}",
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id=f"review-evidence-manifest-25-{self.review_layer.value}",
                source_provenance=(
                    SourceReference(kind="derived", reference="base-e2e-analyzer"),
                ),
                evidence_id=f"review-evidence-manifest-25-{self.review_layer.value}",
                layer=self.review_layer,
                strength=(
                    EvidenceStrength.RENDERER_BOUND
                    if self.review_layer is QaLayer.LAYOUT
                    else EvidenceStrength.MEASURED
                ),
                render_output_sha256=request.render_output_sha256,
                timeline_fingerprint=request.timeline_fingerprint,
                dependency_graph_revision_id=request.dependency_graph.revision_id,
                tool_identity=tool,
                measurement_contract_version="1",
                subject_ids=tuple(item.shot_id for item in context.windows),
                measured_payload=measured_payload,
            )
        )
        evidence_payload = _canonical_json_bytes(evidence)
        evidence_pointer = ReviewEvidencePointer(
            path=canonical_review_evidence_path(evidence.content_hash),
            evidence_id=evidence.evidence_id,
            layer=evidence.layer,
            strength=evidence.strength,
            content_hash=evidence.content_hash,
            file_sha256=hashlib.sha256(evidence_payload).hexdigest(),
        )
        receipt = seal_artifact(
            ReviewReceipt(
                artifact_id=f"review-receipt-manifest-25-{self.review_layer.value}",
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id=f"review-receipt-manifest-25-{self.review_layer.value}",
                source_provenance=(
                    SourceReference(kind="derived", reference=evidence.evidence_id),
                ),
                review_id=f"review-receipt-manifest-25-{self.review_layer.value}",
                layer=self.review_layer,
                review_request=request_pointer,
                render_state=request.render_state,
                render_output_sha256=request.render_output_sha256,
                timeline_fingerprint=request.timeline_fingerprint,
                dependency_graph_revision_id=request.dependency_graph.revision_id,
                qa_policy=request.qa_policy,
                evidence=(evidence_pointer,),
                evidence_ids=(evidence.evidence_id,),
                tool_identities=(tool,),
                verdict=QaVerdict.FAIL if self.review_fails else QaVerdict.PASS,
            )
        )
        reviewed = self.committer.record_review_receipt(
            receipt,
            (evidence,),
            expected_manifest_revision=measured.manifest_revision,
            attempt_id=self.review_attempt_id,
        )
        return next(
            item
            for item in reviewed.active_review_receipts
            if item.layer is self.review_layer
        )

    def acceptance(self, receipt: ReviewReceiptPointer) -> FinalAcceptanceReceipt:
        bundle = load_production_project(self.root / "project.yaml")
        manifest = bundle.manifest
        assert manifest.active_dependency_graph is not None
        assert manifest.active_render_state is not None
        assert manifest.active_qa_policy is not None
        assert bundle.render_state is not None
        return seal_artifact(
            FinalAcceptanceReceipt(
                artifact_id="final-acceptance-manifest-25",
                revision=1,
                content_hash=ZERO_HASH,
                creation_receipt_id="final-acceptance-manifest-25",
                source_provenance=(
                    SourceReference(kind="derived", reference=receipt.review_id),
                ),
                acceptance_id="final-acceptance-manifest-25",
                dependency_graph=manifest.active_dependency_graph,
                dependency_states_hash=canonical_sha256(
                    {
                        "dependency_states": [
                            item.model_dump(mode="json")
                            for item in manifest.dependency_states
                        ]
                    }
                ),
                render_state=manifest.active_render_state,
                render_output_sha256=bundle.render_state.output.file_sha256,
                timeline_fingerprint=bundle.render_state.timeline_fingerprint,
                qa_policy=manifest.active_qa_policy,
                required_review_receipts=(receipt,),
                verdict=QaVerdict.PASS,
            )
        )


def make_manifest_25_review_fixture(tmp_path: Path) -> _Manifest25ReviewFixture:
    runtime = project_factory.make_p7_reuse_runtime(tmp_path)
    runtime.generate_all()
    return _Manifest25ReviewFixture(
        root=tmp_path,
        committer=ProductionStateCommitter(tmp_path),
        timeline=runtime.base_inputs.composition_spec,
        policy=_qa_policy(required_layers=(QaLayer.TECHNICAL,)),
    )


def make_manifest_25_passing_review_fixture(
    tmp_path: Path,
) -> _Manifest25ReviewFixture:
    render_fixture = make_manifest_25_render_fixture(tmp_path)
    render_fixture.render()
    fixture = _Manifest25ReviewFixture(
        root=tmp_path,
        committer=ProductionStateCommitter(tmp_path),
        timeline=render_fixture.timeline,
        policy=_qa_policy(required_layers=(QaLayer.TECHNICAL,)),
    )
    before = fixture.load_manifest()
    fixture.committer.activate_qa_policy(
        fixture.policy,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="base-e2e-passing-review-policy",
    )
    return fixture


def identity(**changes: str) -> ReviewIdentity:
    values = {
        "dependency_graph_revision_id": "0" * 64,
        "dependency_states_hash": "1" * 64,
        "render_state_content_hash": "2" * 64,
        "render_output_sha256": "3" * 64,
        "timeline_fingerprint": "4" * 64,
        "qa_policy_content_hash": "5" * 64,
    }
    values.update(changes)
    return ReviewIdentity(**values)


@pytest.mark.parametrize(
    "field",
    [
        "dependency_graph_revision_id",
        "render_state_content_hash",
        "render_output_sha256",
        "timeline_fingerprint",
        "qa_policy_content_hash",
    ],
)
def test_identity_drift_makes_review_stale(field):
    assert not is_review_current(
        receipt_identity=identity(),
        current_identity=identity(**{field: "f" * 64}),
        layer=QaLayer.TECHNICAL,
    )


def test_semantic_requires_explicit_evaluator_or_human_evidence():
    assert adjudicate_layer(
        QaLayer.SEMANTIC, [{"strength": "measured", "result": "pass"}]
    ) is QaVerdict.NOT_EVALUATED
    assert adjudicate_layer(
        QaLayer.SEMANTIC,
        [{"strength": "explicit_evaluator", "result": "pass"}],
    ) is QaVerdict.PASS


def policy():
    semantic_tool = ToolIdentity(name="fixture-evaluator", version="1")
    return QaPolicy.model_construct(
        technical_thresholds=QaTechnicalThresholds(
            black_luma_max_milli=10,
            silence_peak_max_millidb=-60_000,
            clipping_peak_min_millidb=-100,
        ),
        layout_rules=QaLayoutRules(
            safe_area_inset_milli=50,
            caption_overflow_tolerance_milli=0,
        ),
        semantic_authorities=(semantic_tool,),
    )


def evidence(layer, strength, **payload):
    return ReviewEvidence.model_construct(
        layer=layer,
        strength=strength,
        tool_identity=ToolIdentity(name="fixture-evaluator", version="1"),
        measured_payload={"coverage_complete": True, **payload},
    )


def test_selected_policy_recomputes_technical_and_layout_verdicts():
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.TECHNICAL,
        (evidence(
            QaLayer.TECHNICAL,
            EvidenceStrength.MEASURED,
            minimum_luma_milli=9,
            black_ranges=[],
            silence_ranges=[],
            audio_peak_millidb=-1000,
            expects_audio=False,
            windows=[],
        ),),
    ) is QaVerdict.FAIL
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.LAYOUT,
        (evidence(
            QaLayer.LAYOUT,
            EvidenceStrength.RENDERER_BOUND,
            caption_overflow_milli=1,
            safe_area_inset_milli=50,
            layer_collision_count=0,
            transition_boundary_violation_count=0,
        ),),
    ) is QaVerdict.FAIL


def test_selected_policy_fails_closed_when_required_measurement_is_absent():
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.TECHNICAL,
        (evidence(
            QaLayer.TECHNICAL,
            EvidenceStrength.MEASURED,
            black_ranges=[],
            silence_ranges=[],
            expects_audio=True,
            windows=[],
        ),),
    ) is QaVerdict.NOT_EVALUATED


def test_semantic_typed_evidence_requires_evaluator_identity():
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.SEMANTIC,
        (evidence(QaLayer.SEMANTIC, EvidenceStrength.EXPLICIT_EVALUATOR, semantic_match=True),),
    ) is QaVerdict.NOT_EVALUATED
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.SEMANTIC,
        (evidence(
            QaLayer.SEMANTIC,
            EvidenceStrength.EXPLICIT_EVALUATOR,
            evaluator_identity="fixture-evaluator@1",
            semantic_match=True,
        ),),
    ) is QaVerdict.PASS


def test_semantic_cannot_self_upgrade_without_policy_selected_authority():
    untrusted_policy = policy().model_copy(update={"semantic_authorities": ()})
    asserted = evidence(
        QaLayer.SEMANTIC,
        EvidenceStrength.EXPLICIT_EVALUATOR,
        evaluator_identity="fixture-evaluator@1",
        semantic_match=True,
    )
    assert adjudicate_review_evidence(
        untrusted_policy, QaLayer.SEMANTIC, (asserted,)
    ) is QaVerdict.NOT_EVALUATED


@pytest.mark.parametrize(
    "payload",
    [
        {"minimum_luma_milli": 0},
        {"expects_audio": True, "audio_peak_millidb": -70_000},
        {"audio_peak_millidb": -10},
        {"windows": [{
            "status": "measured",
            "visual_strategy": "generated_video",
            "unique_frame_count": 1,
        }]},
    ],
)
def test_selected_policy_detects_black_silent_clipped_and_frozen(payload):
    measured = {
        "minimum_luma_milli": 500,
        "audio_peak_millidb": -1000,
        "expects_audio": False,
        "windows": [],
        **payload,
    }
    assert adjudicate_review_evidence(
        policy(),
        QaLayer.TECHNICAL,
        (evidence(QaLayer.TECHNICAL, EvidenceStrength.MEASURED, **measured),),
    ) is QaVerdict.FAIL


@pytest.mark.parametrize(
    ("layer", "issue_id"),
    [
        (QaLayer.TECHNICAL, "frozen_frames"),
        (QaLayer.TECHNICAL, "black_frames"),
        (QaLayer.TECHNICAL, "silent_audio"),
        (QaLayer.TECHNICAL, "clipped_audio"),
        (QaLayer.LAYOUT, "caption_overflow"),
        (QaLayer.LAYOUT, "safe_area_violation"),
        (QaLayer.LAYOUT, "layer_collision"),
        (QaLayer.LAYOUT, "transition_boundary"),
        (QaLayer.STRATEGY, "strategy_mismatch"),
    ],
)
def test_measured_failures_fail_their_owned_layer(layer, issue_id):
    evidence = [{"strength": "measured", "result": "fail", "issue_id": issue_id}]
    assert adjudicate_layer(layer, evidence) is QaVerdict.FAIL


def test_static_and_explicit_low_motion_strategy_are_not_misclassified():
    assert adjudicate_visual_motion(
        visual_strategy=VisualStrategy.STATIC_IMAGE,
        unique_frame_ratio=0.01,
        motion_expectation=None,
    ) is QaVerdict.PASS
    expectation = {"minimum_measured_delta_milli": 10, "tolerance_milli": 2}
    assert adjudicate_visual_motion(
        visual_strategy=VisualStrategy.IMAGE_MOTION,
        unique_frame_ratio=0.01,
        motion_expectation=expectation,
        measured_delta_milli=8,
    ) is QaVerdict.PASS
    assert adjudicate_visual_motion(
        visual_strategy=VisualStrategy.MOTION_GRAPHICS,
        unique_frame_ratio=0.01,
        motion_expectation=expectation,
        measured_delta_milli=7,
    ) is QaVerdict.FAIL


def test_technical_context_is_derived_from_exact_shots_and_timeline(tmp_path):
    project_factory.write_production_project(tmp_path)
    inputs, applied = project_factory.make_p5_selective_rebuild_fixture(tmp_path)
    context = build_technical_review_context(
        inputs.project,
        applied.timeline,
        render_output_sha256=applied.render_state.output.file_sha256,
        measurement_contract_version="1",
    )

    assert context.windows
    assert context.windows[0].start_frame == 0
    assert context.windows[-1].end_frame_exclusive == applied.timeline.total_frames
    assert tuple(item.shot_id for item in context.windows) == tuple(
        dict.fromkeys(item.shot_id for item in applied.timeline.visual_spans)
    )
    assert all(
        item.visual_strategy
        == next(shot.visual_strategy for shot in inputs.project.shots if shot.shot_id == item.shot_id)
        for item in context.windows
    )
    assert validate_technical_review_context(
        context,
        inputs.project,
        applied.timeline,
        render_output_sha256=applied.render_state.output.file_sha256,
    ) == context


def test_technical_context_rejects_forged_strategy_or_missing_window(tmp_path):
    project_factory.write_production_project(tmp_path)
    inputs, applied = project_factory.make_p5_selective_rebuild_fixture(tmp_path)
    context = build_technical_review_context(
        inputs.project,
        applied.timeline,
        render_output_sha256=applied.render_state.output.file_sha256,
        measurement_contract_version="1",
    )
    forged_window = context.windows[0].model_copy(
        update={"visual_strategy": VisualStrategy.GENERATED_VIDEO}
    )
    forged = context.model_copy(
        update={"windows": (forged_window, *context.windows[1:])}
    )
    missing = context.model_copy(update={"windows": context.windows[:-1]})

    with pytest.raises(AiVideoError):
        validate_technical_review_context(
            forged,
            inputs.project,
            applied.timeline,
            render_output_sha256=applied.render_state.output.file_sha256,
        )
    with pytest.raises(AiVideoError):
        validate_technical_review_context(
            missing,
            inputs.project,
            applied.timeline,
            render_output_sha256=applied.render_state.output.file_sha256,
        )


def test_final_acceptance_fails_closed_for_stale_or_missing_pass():
    with pytest.raises(AiVideoError):
        evaluate_final_acceptance(
            required_layers=(QaLayer.TECHNICAL,),
            verdicts={QaLayer.TECHNICAL: QaVerdict.PASS},
            receipts_current=False,
        )
    with pytest.raises(AiVideoError):
        evaluate_final_acceptance(
            required_layers=(QaLayer.TECHNICAL, QaLayer.SEMANTIC),
            verdicts={QaLayer.TECHNICAL: QaVerdict.PASS},
            receipts_current=True,
        )


def test_manifest_25_qa_policy_activation_does_not_downgrade_or_drop_p7(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_review_fixture(tmp_path)
    before = fixture.load_manifest()
    after = fixture.committer.activate_qa_policy(
        fixture.policy,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="base-e2e-qa-policy",
    )

    assert after.schema_version == "2.5"
    assert _p7_attempts(after) == _p7_attempts(before)
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.active_qa_policy is not None


def test_manifest_25_review_and_final_acceptance_bind_current_render_and_preserve_p7(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_passing_review_fixture(tmp_path)
    before = fixture.load_manifest()

    receipt = fixture.run_required_review()
    acceptance = fixture.acceptance(receipt)
    accepted = fixture.committer.record_final_acceptance(
        acceptance,
        expected_manifest_revision=fixture.load_manifest().manifest_revision,
        attempt_id="base-e2e-final-acceptance",
    )

    assert accepted.schema_version == "2.5"
    assert _p7_attempts(accepted) == _p7_attempts(before)
    assert accepted.final_acceptance_state is not None
    assert accepted.final_acceptance_state.active_receipt is not None
    final_receipt = load_final_acceptance_receipt(
        tmp_path, accepted.final_acceptance_state.active_receipt
    )
    assert final_receipt.render_state == accepted.active_render_state
