from pathlib import Path
from types import SimpleNamespace

import pytest
from test_production_ecommerce_job_assembly import _plan_and_handoff

from ai_video.production.ecommerce_job_review import EcommercePostMediaExecutionPlan
from ai_video.production.ecommerce_job_review import (
    EcommerceFinalReviewFrontier,
    _semantic_repair_frontier,
    inspect_ecommerce_review_frontier,
)
from ai_video.production.caption_quality_contracts import (
    CAPTION_REQUIREMENT_GROUPS,
    CaptionCoverageStatus,
    CaptionEvidencePayload,
    CaptionFindingReasonCode,
    CaptionRequirementFinding,
    CaptionRequirementGroup,
)
from ai_video.production.ecommerce_media_acceptance import (
    EcommerceAcceptanceEvidencePayload,
    EcommerceRequirementFinding,
    create_qingyan_ecommerce_acceptance_profile,
)
from ai_video.production.models import QaLayer, QaVerdict, ToolIdentity


def _execution(tmp_path: Path, *, policy):
    runtime_handoff, plan, compiled = _plan_and_handoff()
    committer = SimpleNamespace(
        project_root=tmp_path,
        current_final_media_target=lambda: (
            SimpleNamespace(qa_policy=policy),
            SimpleNamespace(caption_cues=()),
        ),
    )
    execution = EcommercePostMediaExecutionPlan(
        handoff=compiled,
        plan=plan,
        shot_facades={},
        committer=committer,
        universal_profile=SimpleNamespace(),
        run_hard_check=lambda *_: None,
        run_review_layer=lambda *_: None,
        tool_identity=ToolIdentity(name="review-test", version="1"),
        evaluate=lambda *_: None,
        review_attempt_id="review-attempt",
        review_request_id="review-request",
        evidence_id="review-evidence",
        review_id="review-receipt",
        final_acceptance_id="final-acceptance",
    )
    return runtime_handoff, execution


def test_job_review_refuses_policy_without_handoff_final_output_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, execution = _execution(
        tmp_path,
        policy=SimpleNamespace(
            final_output=None,
            domain_acceptance=SimpleNamespace(domain_id="ecommerce"),
            caption_policy=None,
            required_layers=(),
        ),
    )
    calls: list[str] = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.close_ecommerce_post_media_candidate",
        lambda **_: calls.append("closure"),
    )

    with pytest.raises(ValueError, match="final-output"):
        execution.run(runtime_handoff, project_root=tmp_path)

    assert calls == []


def test_job_review_refuses_partial_handoff_final_output_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, execution = _execution(
        tmp_path,
        policy=SimpleNamespace(
            final_output=SimpleNamespace(requirements=()),
            domain_acceptance=SimpleNamespace(domain_id="ecommerce"),
            caption_policy=None,
            required_layers=(),
        ),
    )
    calls: list[str] = []
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.close_ecommerce_post_media_candidate",
        lambda **_: calls.append("closure"),
    )

    with pytest.raises(ValueError, match="final-output"):
        execution.run(runtime_handoff, project_root=tmp_path)

    assert calls == []


def _semantic_evidence(*, domain_verdict: QaVerdict, cta_verdict: str):
    profile = create_qingyan_ecommerce_acceptance_profile()
    domain = EcommerceAcceptanceEvidencePayload.create(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_content_hash=profile.content_hash,
        findings=tuple(
            EcommerceRequirementFinding(
                requirement_id=requirement_id,
                verdict=domain_verdict,
                rationale="exact final output observation",
            )
            for requirement_id in profile.required_requirement_ids
        ),
    )
    return SimpleNamespace(
        measured_payload={
            "domain_acceptance": domain.model_dump(mode="json"),
            "final_output": {
                "contract_hash": "a" * 64,
                "review_request_content_hash": "b" * 64,
                "findings": [
                    {
                        "requirement_id": "cta",
                        "verdict": cta_verdict,
                        "observation": "observed exact CTA",
                    },
                    {
                        "requirement_id": "captions",
                        "verdict": "pass",
                        "observation": "observed exact captions",
                    },
                ],
            },
        }
    )


def test_plan_bound_cta_failure_cannot_use_composition_repair_frontier() -> None:
    frontier = _semantic_repair_frontier(
        _semantic_evidence(domain_verdict=QaVerdict.PASS, cta_verdict="fail"),
    )

    assert frontier is EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED


def test_review_execution_blocks_cta_repair_before_a_render_attempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_handoff, execution = _execution(
        tmp_path,
        policy=SimpleNamespace(caption_policy=None, required_layers=()),
    )
    pointer = object()
    evidence_pointer = object()
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.validate_ecommerce_final_output_contract",
        lambda *_args: None,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_production_project",
        lambda _path: SimpleNamespace(
            manifest=SimpleNamespace(
                final_acceptance_state=None,
                active_review_receipts=(pointer,),
            )
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_receipt",
        lambda _root, _pointer: SimpleNamespace(
            verdict=QaVerdict.FAIL,
            layer=QaLayer.SEMANTIC,
            evidence=(evidence_pointer,),
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_evidence",
        lambda _root, _pointer: _semantic_evidence(
            domain_verdict=QaVerdict.PASS, cta_verdict="fail"
        ),
    )

    assert execution.inspect_frontier(
        runtime_handoff, project_root=tmp_path
    ) is EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED


@pytest.mark.parametrize(
    ("layer", "expected"),
    (
        (QaLayer.LAYOUT, EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED),
        (QaLayer.CAPTION, EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED),
    ),
)
def test_unattributed_layout_failure_requires_diagnosis_before_composition_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    layer: QaLayer,
    expected: EcommerceFinalReviewFrontier,
) -> None:
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_production_project",
        lambda _path: SimpleNamespace(
            manifest=SimpleNamespace(active_review_receipts=(object(),))
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_receipt",
        lambda _root, _pointer: SimpleNamespace(
            verdict=QaVerdict.FAIL, layer=layer
        ),
    )
    def invalid_caption_chain(**_kwargs):
        raise ValueError("no exact caption evidence")

    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.reopen_caption_review_chain",
        invalid_caption_chain,
    )

    assert inspect_ecommerce_review_frontier(tmp_path) is expected


@pytest.mark.parametrize(
    ("group", "reason", "expected"),
    (
        (
            CaptionRequirementGroup.UNINTENDED_TEXT,
            CaptionFindingReasonCode.UNINTENDED_TEXT_DETECTED,
            EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED,
        ),
        (
            CaptionRequirementGroup.LAYOUT_READABILITY,
            CaptionFindingReasonCode.LAYOUT_UNREADABLE,
            EcommerceFinalReviewFrontier.PREPARE_COMPOSITION,
        ),
        (
            CaptionRequirementGroup.LAYOUT_READABILITY,
            CaptionFindingReasonCode.CONFLICTING_EVIDENCE,
            EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED,
        ),
        (
            CaptionRequirementGroup.TIMING_CONTRACT,
            CaptionFindingReasonCode.UNINTENDED_TEXT_DETECTED,
            EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED,
        ),
    ),
)
def test_caption_failure_requires_exact_group_before_local_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    group: CaptionRequirementGroup,
    reason: CaptionFindingReasonCode,
    expected: EcommerceFinalReviewFrontier,
) -> None:
    pointer = object()
    project = SimpleNamespace(
        manifest=SimpleNamespace(active_review_receipts=(pointer,))
    )
    payload = _caption_payload(failed_group=group, failed_reason=reason)
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_production_project",
        lambda _path: project,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_receipt",
        lambda _root, _pointer: SimpleNamespace(
            verdict=QaVerdict.FAIL, layer=QaLayer.CAPTION
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.reopen_caption_review_chain",
        lambda **_kwargs: _reopened_caption(payload),
        raising=False,
    )

    assert inspect_ecommerce_review_frontier(tmp_path) is expected


def _caption_payload(
    *,
    failed_group: CaptionRequirementGroup,
    failed_reason: CaptionFindingReasonCode,
    unevaluated_group: CaptionRequirementGroup | None = None,
    omitted_group: CaptionRequirementGroup | None = None,
) -> CaptionEvidencePayload:
    findings = []
    for group in CaptionRequirementGroup:
        if group is omitted_group:
            continue
        verdict = (
            "fail"
            if group is failed_group
            else "not_evaluated"
            if group is unevaluated_group
            else "pass"
        )
        findings.append(
            CaptionRequirementFinding(
                requirement_group=group,
                verdict=verdict,
                reason_code=(
                    failed_reason
                    if verdict == "fail"
                    else CaptionFindingReasonCode.LOW_CONFIDENCE
                    if verdict == "not_evaluated"
                    else CaptionFindingReasonCode.REQUIREMENT_CONFIRMED
                ),
                covered_subject_ids=(
                    "render-1" if group is CaptionRequirementGroup.UNINTENDED_TEXT
                    else "cue-1",
                ),
                raw_evidence_references=("exact-render",),
                coverage_status=CaptionCoverageStatus.COMPLETE,
                observation_fingerprint="c" * 64,
            )
        )
    return CaptionEvidencePayload(
        caption_policy_hash="a" * 64,
        caption_context_hash="b" * 64,
        findings=tuple(findings),
    )


def _reopened_caption(
    payload: CaptionEvidencePayload,
    *,
    unevaluated_group: CaptionRequirementGroup | None = None,
):
    by_group = {finding.requirement_group: finding for finding in payload.findings}
    return SimpleNamespace(
        verdict=QaVerdict.FAIL,
        evidence=(SimpleNamespace(measured_payload=payload.model_dump(mode="json")),),
        adjudication=SimpleNamespace(
            group_verdicts=tuple(
                QaVerdict.NOT_EVALUATED
                if group is unevaluated_group or group not in by_group
                else QaVerdict(by_group[group].verdict)
                for group in CAPTION_REQUIREMENT_GROUPS
            ),
            authorized_findings=tuple(
                (by_group[group],) if group in by_group else ()
                for group in CAPTION_REQUIREMENT_GROUPS
            ),
        ),
    )


@pytest.mark.parametrize(
    ("unevaluated_group", "omitted_group"),
    (
        (CaptionRequirementGroup.UNINTENDED_TEXT, None),
        (None, CaptionRequirementGroup.UNINTENDED_TEXT),
    ),
)
def test_caption_failure_with_incomplete_required_evidence_repairs_evidence_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unevaluated_group: CaptionRequirementGroup | None,
    omitted_group: CaptionRequirementGroup | None,
) -> None:
    pointer = object()
    payload = _caption_payload(
        failed_group=CaptionRequirementGroup.TIMING_CONTRACT,
        failed_reason=CaptionFindingReasonCode.TIMING_OUT_OF_BOUNDS,
        unevaluated_group=unevaluated_group,
        omitted_group=omitted_group,
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_production_project",
        lambda _path: SimpleNamespace(
            manifest=SimpleNamespace(active_review_receipts=(pointer,))
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_receipt",
        lambda _root, _pointer: SimpleNamespace(
            verdict=QaVerdict.FAIL, layer=QaLayer.CAPTION
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.reopen_caption_review_chain",
        lambda **_kwargs: _reopened_caption(payload),
    )

    assert inspect_ecommerce_review_frontier(
        tmp_path
    ) is EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED


def test_caption_failure_with_incomplete_canonical_cue_coverage_repairs_evidence_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pointer = object()
    payload = _caption_payload(
        failed_group=CaptionRequirementGroup.TIMING_CONTRACT,
        failed_reason=CaptionFindingReasonCode.TIMING_OUT_OF_BOUNDS,
    )
    payload = payload.model_copy(
        update={
            "findings": tuple(
                finding.model_copy(update={"covered_subject_ids": ()})
                if finding.requirement_group is CaptionRequirementGroup.UNINTENDED_TEXT
                else finding
                for finding in payload.findings
            )
        }
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_production_project",
        lambda _path: SimpleNamespace(
            manifest=SimpleNamespace(active_review_receipts=(pointer,))
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_receipt",
        lambda _root, _pointer: SimpleNamespace(
            verdict=QaVerdict.FAIL, layer=QaLayer.CAPTION
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.reopen_caption_review_chain",
        lambda **_kwargs: _reopened_caption(
            payload,
            unevaluated_group=CaptionRequirementGroup.UNINTENDED_TEXT,
        ),
    )

    assert inspect_ecommerce_review_frontier(
        tmp_path
    ) is EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED


def test_persisted_not_evaluated_caption_evidence_is_not_blindly_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_production_project",
        lambda _path: SimpleNamespace(
            manifest=SimpleNamespace(active_review_receipts=(object(),))
        ),
    )
    monkeypatch.setattr(
        "ai_video.production.ecommerce_job_review.load_review_receipt",
        lambda _root, _pointer: SimpleNamespace(
            verdict=QaVerdict.NOT_EVALUATED, layer=QaLayer.CAPTION
        ),
    )

    assert inspect_ecommerce_review_frontier(
        tmp_path
    ) is EcommerceFinalReviewFrontier.EVIDENCE_REPAIR_REQUIRED


def test_semantic_domain_failure_requires_diagnosis() -> None:
    frontier = _semantic_repair_frontier(
        _semantic_evidence(domain_verdict=QaVerdict.FAIL, cta_verdict="fail"),
    )

    assert frontier is EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
