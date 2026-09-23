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
        (QaLayer.CAPTION, EcommerceFinalReviewFrontier.PREPARE_COMPOSITION),
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

    assert inspect_ecommerce_review_frontier(tmp_path) is expected


def test_semantic_domain_failure_requires_diagnosis() -> None:
    frontier = _semantic_repair_frontier(
        _semantic_evidence(domain_verdict=QaVerdict.FAIL, cta_verdict="fail"),
    )

    assert frontier is EcommerceFinalReviewFrontier.DIAGNOSIS_REQUIRED
