from __future__ import annotations

from copy import deepcopy
from io import BytesIO
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from PIL import Image

from ai_video.errors import AiVideoError
from ai_video.production._state_commit_video_source_boundary import (
    _validate_supported_rubric,
)
from ai_video.production.models import QaVerdict, ToolIdentity
from ai_video.production.shot_continuity_source_review import (
    SourceBoundaryEndpointMeasurement,
    SourceBoundaryHumanDecisionV1,
    SourceBoundaryMeasurementContractV1,
    SourceBoundaryReviewEvidence,
    SourceBoundaryReviewIntent,
    SourceBoundaryReviewReceipt,
    SourceBoundaryReviewerV1,
    adjudicate_source_boundary_review,
    is_source_boundary_qualification_request,
    validate_source_boundary_qualification_request,
)
from ai_video.production.continuity_evaluator import SampledRgbFrame
from ai_video.production.video_artifact import MeasuredVideoMetadata


_A = "a" * 64
_B = "b" * 64
_C = "c" * 64
_D = "d" * 64
_E = "e" * 64
_F = "f" * 64


def _source_request_shape(**changes: object) -> SimpleNamespace:
    bindings = {
        "c4_multi_anchor_binding": None,
        "continuity_binding": None,
        "commercial_binding": None,
        "hard_cut_keyframe_binding": None,
    }
    original = SimpleNamespace(
        target_asset_role="approved_endpoint",
        seal_terminal_frame=True,
        image_bindings=(
            SimpleNamespace(role="first_frame"),
            SimpleNamespace(role="last_frame"),
        ),
        **bindings,
    )
    values = {
        "activation_scope": SimpleNamespace(request=original),
        "seal_terminal_frame": True,
        "image_bindings": (
            SimpleNamespace(role="first_frame"),
            SimpleNamespace(role="last_frame"),
        ),
        **bindings,
    }
    values.update(changes)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    "drift",
    (
        {"c4_multi_anchor_binding": object()},
        {"continuity_binding": object()},
        {"commercial_binding": object()},
        {"hard_cut_keyframe_binding": object()},
        {"image_bindings": (SimpleNamespace(role="first_frame"),)},
    ),
)
def test_reserved_source_request_rejects_alternate_p6_shapes(
    drift: dict[str, object],
) -> None:
    request = _source_request_shape(**drift)

    assert is_source_boundary_qualification_request(request)
    with pytest.raises(ValueError, match="must not include continuity"):
        validate_source_boundary_qualification_request(request)


def _contract() -> SourceBoundaryMeasurementContractV1:
    return SourceBoundaryMeasurementContractV1.create(
        p0_qualification_receipt_hash=_A,
        p0_rubric_hash=_B,
        first_frame_asset_id="first",
        first_frame_sha256=_C,
        last_frame_asset_id="last",
        last_frame_sha256=_D,
        sample_width=1344,
        sample_height=768,
        decoder=ToolIdentity(name="ffmpeg", version="7.1.1"),
    )


def _human(
    verdict: QaVerdict = QaVerdict.PASS,
) -> SourceBoundaryHumanDecisionV1:
    values: tuple[bool | None, ...]
    if verdict is QaVerdict.PASS:
        values = (True,) * 7
    elif verdict is QaVerdict.FAIL:
        values = (True, True, True, False, True, True, True)
    else:
        values = (True, True, True, None, True, True, True)
    return SourceBoundaryHumanDecisionV1.create(
        resolved_generation_hash=_E,
        artifact_sha256=_F,
        reviewer=ToolIdentity(name="human-user", version="2026-08-26"),
        raw_full_speed_reviewed=True,
        identity_match=values[0],
        camera_axis_match=values[1],
        framing_match=values[2],
        motion_direction_match=values[3],
        action_phase_match=values[4],
        entrance_exit_match=values[5],
        no_unexpected_stop_or_reentry=values[6],
        pacing_waiver=True,
        rationale="Exact v9 media accepted; pacing alone is waived.",
    )


def _intent(
    contract: SourceBoundaryMeasurementContractV1,
    human: SourceBoundaryHumanDecisionV1,
) -> SourceBoundaryReviewIntent:
    return SourceBoundaryReviewIntent.create(
        resolved_generation_hash=_E,
        request_input_hash="1" * 64,
        artifact_sha256=_F,
        artifact_size_bytes=100,
        fetch_fingerprint="2" * 64,
        target_shot_id="shot-3",
        target_shot_revision=2,
        target_shot_content_hash="3" * 64,
        source_profile_content_hash="4" * 64,
        source_execution_stack_hash="5" * 64,
        measurement_contract_hash=contract.content_hash,
        human_decision_hash=human.content_hash,
        evaluator=ToolIdentity(name="source-boundary-review", version="1"),
    )


def _evidence(
    *,
    contract: SourceBoundaryMeasurementContractV1 | None = None,
    human: SourceBoundaryHumanDecisionV1 | None = None,
    first_psnr_millidb: int = 33_460,
    first_ssim_millionths: int = 920_355,
    last_psnr_millidb: int = 32_506,
    last_ssim_millionths: int = 905_835,
) -> SourceBoundaryReviewEvidence:
    contract = contract or _contract()
    human = human or _human()
    intent = _intent(contract, human)
    return SourceBoundaryReviewEvidence.create(
        intent=intent,
        measurement_contract=contract,
        human_decision=human,
        measured_metadata_hash="6" * 64,
        first_frame=SourceBoundaryEndpointMeasurement(
            role="first_frame",
            frame_index=0,
            anchor_asset_id="first",
            anchor_sha256=_C,
            psnr_millidb=first_psnr_millidb,
            ssim_millionths=first_ssim_millionths,
        ),
        last_frame=SourceBoundaryEndpointMeasurement(
            role="last_frame",
            frame_index=123,
            anchor_asset_id="last",
            anchor_sha256=_D,
            psnr_millidb=last_psnr_millidb,
            ssim_millionths=last_ssim_millionths,
        ),
    )


def test_exact_automatic_and_human_boundary_evidence_passes() -> None:
    evidence = _evidence()

    receipt = adjudicate_source_boundary_review(evidence)

    assert receipt.verdict is QaVerdict.PASS
    assert receipt.intent_content_hash == evidence.intent.content_hash
    assert receipt.evidence_content_hash == evidence.content_hash
    assert (
        SourceBoundaryReviewReceipt.model_validate_json(receipt.model_dump_json())
        == receipt
    )


@pytest.mark.parametrize(
    ("evidence", "expected"),
    (
        (_evidence(first_ssim_millionths=899_999), QaVerdict.FAIL),
        (_evidence(human=_human(QaVerdict.FAIL)), QaVerdict.FAIL),
        (
            _evidence(human=_human(QaVerdict.NOT_EVALUATED)),
            QaVerdict.NOT_EVALUATED,
        ),
    ),
)
def test_boundary_adjudication_is_fail_closed(
    evidence: SourceBoundaryReviewEvidence,
    expected: QaVerdict,
) -> None:
    assert adjudicate_source_boundary_review(evidence).verdict is expected


def test_evidence_rejects_substituted_contract_human_or_anchor() -> None:
    evidence = _evidence()
    payload = evidence.model_dump(mode="json")

    for mutation in (
        lambda value: value["measurement_contract"].__setitem__(
            "p0_rubric_hash", "9" * 64
        ),
        lambda value: value["human_decision"].__setitem__(
            "resolved_generation_hash", "8" * 64
        ),
        lambda value: value["last_frame"].__setitem__("anchor_sha256", "7" * 64),
    ):
        candidate = deepcopy(payload)
        mutation(candidate)
        with pytest.raises(ValidationError):
            SourceBoundaryReviewEvidence.model_validate(candidate)


def test_reviewer_measures_exact_decoded_first_and_terminal_frames() -> None:
    payload = BytesIO()
    Image.new("RGB", (8, 8), (30, 60, 90)).save(payload, format="PNG")
    anchor = payload.getvalue()
    anchor_hash = __import__("hashlib").sha256(anchor).hexdigest()
    identity = ToolIdentity(name="ffmpeg", version="7.1.1")
    contract = SourceBoundaryMeasurementContractV1.create(
        p0_qualification_receipt_hash=_A,
        p0_rubric_hash=_B,
        first_frame_asset_id="first",
        first_frame_sha256=anchor_hash,
        last_frame_asset_id="last",
        last_frame_sha256=anchor_hash,
        sample_width=8,
        sample_height=8,
        decoder=identity,
    )
    human = _human()
    intent = _intent(contract, human)
    pixels = bytes((30, 60, 90)) * 64

    class _Sampler:
        def __init__(self) -> None:
            self.identity = identity

        def sample(self, _fd, _measured, indices):
            assert indices == (0, 1)
            return tuple(
                SampledRgbFrame(
                    frame_index=index,
                    width=8,
                    height=8,
                    pixels=pixels,
                )
                for index in indices
            )

    reviewer = SourceBoundaryReviewerV1(
        source_profile_content_hash="4" * 64,
        source_execution_stack_hash="5" * 64,
        measurement_contract=contract,
        human_decision=human,
        evaluator=ToolIdentity(name="source-boundary", version="1"),
        sampler=_Sampler(),
        first_anchor_bytes=anchor,
        last_anchor_bytes=anchor,
    )
    measured = MeasuredVideoMetadata(
        container_name="mp4",
        codec_name="h264",
        width=8,
        height=8,
        fps_numerator=24,
        fps_denominator=1,
        duration_milliseconds=84,
        frame_count=2,
        audio_stream_count=0,
        size_bytes=100,
        artifact_sha256=_F,
    )

    evidence = reviewer(
        7,
        SimpleNamespace(resolved_generation_hash=_E),
        measured,
        intent,
    )

    assert evidence.first_frame.psnr_millidb == 999_000
    assert evidence.first_frame.ssim_millionths == 1_000_000
    assert evidence.last_frame.frame_index == 1
    assert adjudicate_source_boundary_review(evidence).verdict is QaVerdict.PASS


def _supported_rubric_payload() -> dict[str, object]:
    return {
        "boundary": {
            "decoded_first_and_last_required": True,
            "perceptual_backend_missing": ("NOT_EVALUATED_requires_exact_human_review"),
            "psnr_db_minimum": 30.0,
            "ssim_minimum": 0.9,
        },
        "identity": {
            "automatic_missing": "NOT_EVALUATED_requires_exact_human_review",
            "dimensions": ["face", "hair", "wardrobe", "satchel", "body_scale"],
        },
        "motion": {
            "dimensions": [
                "subject_direction_velocity",
                "camera_direction_velocity",
                "action_phase",
                "entrance_exit",
                "unexpected_stop_or_reentry",
            ],
            "single_frame_metric_sufficient": False,
        },
        "sequence": {
            "raw_full_speed_review_required": True,
            "crossfade_optical_flow_interpolation_retime_forbidden": True,
        },
        "verdict_owner": "P6",
        "human_evidence_required": True,
    }


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload["boundary"].__setitem__("ssim_minimum", 0.91),
        lambda payload: payload["identity"]["dimensions"].append("tattoo"),
        lambda payload: payload["motion"]["dimensions"].append("hand_contact"),
        lambda payload: payload["sequence"].__setitem__(
            "raw_full_speed_review_required", False
        ),
    ),
)
def test_checkpoint_rejects_rubric_semantic_drift(mutate) -> None:
    payload = _supported_rubric_payload()
    mutate(payload)
    rubric = SimpleNamespace(
        input_kind="rubric",
        content_hash=_B,
        payload=payload,
    )

    with pytest.raises(AiVideoError, match="active P0 rubric"):
        _validate_supported_rubric((rubric,), SimpleNamespace(rubric_hash=_B))


def test_checkpoint_accepts_only_the_exact_supported_rubric() -> None:
    rubric = SimpleNamespace(
        input_kind="rubric",
        content_hash=_B,
        payload=_supported_rubric_payload(),
    )

    _validate_supported_rubric((rubric,), SimpleNamespace(rubric_hash=_B))
