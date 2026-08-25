from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ecommerce_media_acceptance import (
    CommercialShotEvaluationIntent,
    EcommerceRequirementFinding,
    GeneratedCommercialShotEvidence,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.commercial_video_validation import (
    validate_commercial_source_binding,
)
from ai_video.production.models import (
    CommercialShotEvaluationIntentPointer,
    CommercialShotEvaluationPhase,
    CommercialShotEvaluationState,
    EvidenceStrength,
    GeneratedCommercialShotEvidencePointer,
    QaVerdict,
    ToolIdentity,
)
from ai_video.production.paths import (
    canonical_commercial_shot_evaluation_intent_path,
    canonical_generated_commercial_shot_evidence_path,
)
from ai_video.production.video_artifact import (
    MeasuredVideoMetadata,
    VideoProbeReceipt,
    invoke_generated_commercial_shot_reviewer,
    validate_generated_commercial_shot_evidence,
    validate_generated_commercial_shot_intent,
)

from test_production_video import (
    _commercial_binding,
    _continuity_fetch_receipt,
    _request,
    _resolved,
)


POLICY_HASH = "a" * 64
EVALUATOR = ToolIdentity(name="commercial-shot-evaluator", version="1")
PROFILE_HASH = "c" * 64


def _commercial_request():
    return _resolved(_request(commercial_binding=_commercial_binding()))


def _measured(request, artifact_bytes: bytes):
    fetch = _continuity_fetch_receipt(request, artifact_bytes)
    return fetch, MeasuredVideoMetadata(
        container_name="mp4",
        codec_name="h264",
        width=1280,
        height=720,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=6000,
        frame_count=144,
        audio_stream_count=0,
        size_bytes=len(artifact_bytes),
        artifact_sha256=hashlib.sha256(artifact_bytes).hexdigest(),
    )


def _intent(request, measured):
    return CommercialShotEvaluationIntent.create(
        binding=request.commercial_binding,
        resolved_generation_hash=request.resolved_generation_hash,
        artifact_sha256=measured.artifact_sha256,
        measured_metadata_hash=canonical_sha256(measured),
        qa_policy_content_hash=POLICY_HASH,
        evaluator=EVALUATOR,
        evaluator_profile_content_hash=PROFILE_HASH,
    )


def _evidence(request, measured, *, verdict: QaVerdict = QaVerdict.PASS):
    intent = _intent(request, measured)
    return GeneratedCommercialShotEvidence.create(
        intent=intent,
        strength=EvidenceStrength.EXPLICIT_EVALUATOR,
        findings=tuple(
            EcommerceRequirementFinding(
                requirement_id=requirement_id,
                verdict=verdict if index == 0 else QaVerdict.PASS,
                rationale=f"observed {requirement_id}",
            )
            for index, requirement_id in enumerate(
                request.commercial_binding.applicable_requirement_ids
            )
        ),
    )


def test_commercial_evidence_binds_exact_request_mp4_policy_and_authority() -> None:
    request = _commercial_request()
    _, measured = _measured(request, b"commercial-video")
    evidence = _evidence(request, measured)

    assert (
        validate_generated_commercial_shot_evidence(
            evidence,
            request=request,
            measured=measured,
            policy_content_hash=POLICY_HASH,
            authorities=(EVALUATOR,),
            require_pass=True,
        )
        == evidence
    )
    changed = measured.model_copy(update={"artifact_sha256": "f" * 64})
    with pytest.raises(AiVideoError) as replaced:
        validate_generated_commercial_shot_evidence(
            evidence,
            request=request,
            measured=changed,
            policy_content_hash=POLICY_HASH,
            authorities=(EVALUATOR,),
            require_pass=True,
        )
    assert replaced.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID

    with pytest.raises(AiVideoError) as unauthorized:
        validate_generated_commercial_shot_evidence(
            evidence,
            request=request,
            measured=measured,
            policy_content_hash=POLICY_HASH,
            authorities=(ToolIdentity(name="other", version="1"),),
            require_pass=True,
        )
    assert unauthorized.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID


def test_commercial_intent_rejects_evaluator_profile_drift() -> None:
    request = _commercial_request()
    _, measured = _measured(request, b"commercial-video")
    changed = _intent(request, measured).model_copy(
        update={"evaluator_profile_content_hash": "f" * 64}
    )

    with pytest.raises(AiVideoError) as rejected:
        validate_generated_commercial_shot_intent(
            changed,
            request=request,
            measured=measured,
            policy_content_hash=POLICY_HASH,
            authorities=(EVALUATOR,),
        )

    assert rejected.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID


def test_commercial_product_hashes_require_reopened_source_approval() -> None:
    with pytest.raises(ValueError, match="no current source approval"):
        validate_commercial_source_binding(_commercial_binding(), None)


@pytest.mark.parametrize("verdict", (QaVerdict.FAIL, QaVerdict.NOT_EVALUATED))
def test_commercial_evidence_requires_pass_before_candidate(verdict: QaVerdict) -> None:
    request = _commercial_request()
    _, measured = _measured(request, b"commercial-video")
    evidence = _evidence(request, measured, verdict=verdict)

    assert (
        validate_generated_commercial_shot_evidence(
            evidence,
            request=request,
            measured=measured,
            policy_content_hash=POLICY_HASH,
            authorities=(EVALUATOR,),
            require_pass=False,
        )
        == evidence
    )
    with pytest.raises(AiVideoError) as rejected:
        validate_generated_commercial_shot_evidence(
            evidence,
            request=request,
            measured=measured,
            policy_content_hash=POLICY_HASH,
            authorities=(EVALUATOR,),
            require_pass=True,
        )
    assert rejected.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID


def test_commercial_reviewer_consumes_duplicate_held_fd_and_restores_position(
    tmp_path: Path,
) -> None:
    request = _commercial_request()
    artifact_bytes = b"commercial-video"
    source = tmp_path / "candidate.mp4"
    source.write_bytes(artifact_bytes)
    _, measured = _measured(request, artifact_bytes)
    intent = _intent(request, measured)
    observed: list[bytes] = []

    def reviewer(held_fd, exact_request, exact_measured, exact_intent):
        observed.append(os.read(held_fd, len(artifact_bytes)))
        assert exact_request == request
        assert exact_measured == measured
        assert exact_intent == intent
        return _evidence(request, measured)

    with source.open("rb") as held:
        held.seek(4)
        evidence = invoke_generated_commercial_shot_reviewer(
            held.fileno(),
            request,
            measured,
            intent,
            reviewer,
            POLICY_HASH,
            (EVALUATOR,),
        )
        assert held.tell() == 4

    assert observed == [artifact_bytes]
    assert evidence == _evidence(request, measured)


def test_commercial_reviewer_exception_is_typed(tmp_path: Path) -> None:
    request = _commercial_request()
    artifact_bytes = b"commercial-video"
    source = tmp_path / "candidate.mp4"
    source.write_bytes(artifact_bytes)
    _, measured = _measured(request, artifact_bytes)

    def reviewer(*_):
        raise RuntimeError("evaluator unavailable")

    with source.open("rb") as held:
        with pytest.raises(AiVideoError) as caught:
            invoke_generated_commercial_shot_reviewer(
                held.fileno(),
                request,
                measured,
                _intent(request, measured),
                reviewer,
                POLICY_HASH,
                (EVALUATOR,),
            )
    assert caught.value.code is ErrorCode.REVIEW_EVIDENCE_INVALID


def test_probe_receipt_additively_binds_commercial_evidence() -> None:
    request = _commercial_request()
    artifact_bytes = b"commercial-video"
    fetch, measured = _measured(request, artifact_bytes)
    evidence = _evidence(request, measured)
    receipt = VideoProbeReceipt.create(
        request=request,
        fetch_receipt=fetch,
        measured=measured,
        commercial_evidence=evidence,
    )

    assert receipt.commercial_evidence == evidence
    historical = VideoProbeReceipt.create(
        request=_resolved(),
        fetch_receipt=_continuity_fetch_receipt(_resolved(), artifact_bytes),
        measured=measured,
    ).model_dump(mode="json")
    assert "commercial_evidence" not in historical
    assert "continuity_evidence" not in historical


def test_commercial_checkpoint_state_requires_exact_evidenced_identity() -> None:
    intent = CommercialShotEvaluationIntentPointer(
        path=canonical_commercial_shot_evaluation_intent_path("1" * 64),
        content_hash="1" * 64,
        evaluation_fingerprint="2" * 64,
        binding_content_hash="3" * 64,
        artifact_sha256="4" * 64,
        evaluator_profile_content_hash="5" * 64,
        file_sha256="6" * 64,
    )
    evidence = GeneratedCommercialShotEvidencePointer(
        path=canonical_generated_commercial_shot_evidence_path("7" * 64),
        content_hash="7" * 64,
        intent_content_hash=intent.content_hash,
        evaluation_fingerprint=intent.evaluation_fingerprint,
        binding_content_hash=intent.binding_content_hash,
        artifact_sha256=intent.artifact_sha256,
        file_sha256="8" * 64,
    )

    assert CommercialShotEvaluationState(
        phase=CommercialShotEvaluationPhase.EVIDENCED,
        intent=intent,
        evidence=evidence,
    ).evidence == evidence
    with pytest.raises(ValueError):
        CommercialShotEvaluationState(
            phase=CommercialShotEvaluationPhase.EVIDENCED,
            intent=intent,
            evidence=evidence.model_copy(update={"artifact_sha256": "f" * 64}),
        )
