from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._paid_provider_project_reader import (
    load_paid_provider_gate_receipt,
    load_paid_provider_submit_receipt,
)
from ai_video.production.models import (
    ProductionManifest,
    VideoAttemptPhase,
    VideoGenerationAttemptState,
    VideoRequestReceiptPointer,
    VideoStatusReceiptPointer,
)
from ai_video.production.paths import _read_regular_file_nofollow, resolve_contained_path
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoTaskObservation,
    VideoTaskState,
    VideoSubmission,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _root_and_path(root: str | Path, stored: Path) -> tuple[Path, Path]:
    try:
        resolved_root = Path(root).resolve(strict=True)
        resolved = resolve_contained_path(
            resolved_root, stored, allowed_root=resolved_root / "state"
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid("Video generation evidence path is unsafe.", str(exc)) from exc
    return resolved_root, resolved


def load_video_request_receipt(
    root: str | Path, pointer: VideoRequestReceiptPointer
) -> ResolvedVideoGenerationRequest:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        request = ResolvedVideoGenerationRequest.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen video generation request.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or request.desired_generation_fingerprint != pointer.request_receipt_fingerprint
        or request.generation_id != pointer.generation_id
        or request.request_input_hash != pointer.request_input_hash
        or request.resolved_generation_hash != pointer.resolved_generation_hash
        or request.output_asset_id != pointer.output_asset_id
    ):
        raise _invalid("Video generation request pointer identity is invalid.")
    return request


def load_video_status_receipt(
    root: str | Path, pointer: VideoStatusReceiptPointer
) -> VideoTaskObservation:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        observation = VideoTaskObservation.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen video generation observation.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or observation.observation_fingerprint != pointer.observation_fingerprint
        or observation.paid_submit_receipt_fingerprint
        != pointer.paid_submit_receipt_fingerprint
    ):
        raise _invalid("Video generation observation pointer identity is invalid.")
    return observation


def verify_video_evidence(
    root: str | Path, states: Iterable[VideoGenerationAttemptState]
) -> None:
    request_owners: list[str] = []
    for state in states:
        request = load_video_request_receipt(root, state.request)
        request_owners.append(state.request.request_receipt_fingerprint)
        if (
            request.generation_id != state.generation_id
            or request.resolved_generation_hash != state.resolved_generation_hash
        ):
            raise _invalid("Video attempt identity does not match its request evidence.")
        if state.latest_observation is None:
            continue
        if (
            state.latest_observation.request_receipt_fingerprint
            != state.request.request_receipt_fingerprint
        ):
            raise _invalid("Video observation does not belong to the attempt request.")
        observation = load_video_status_receipt(root, state.latest_observation)
        if state.paid_submit_receipt is None:
            raise _invalid("Video observation requires exact Gate submit evidence.")
        submit_receipt = load_paid_provider_submit_receipt(
            root, state.paid_submit_receipt
        )
        if submit_receipt.request_fingerprint != request.resolved_generation_hash:
            raise _invalid("Video Gate submit receipt does not match its request.")
        try:
            submission = VideoSubmission.from_paid_submit_receipt(
                resolved=request,
                receipt=submit_receipt,
            )
        except AiVideoError as exc:
            raise _invalid(
                "Video Gate submit receipt cannot reconstruct its submission.",
                str(exc),
            ) from exc
        if (
            state.paid_submit_receipt is not None
            and observation.paid_submit_receipt_fingerprint
            != state.paid_submit_receipt.submit_receipt_fingerprint
        ):
            raise _invalid("Video observation does not match the attempt submit receipt.")
        if observation.submission_fingerprint != submission.submission_fingerprint:
            raise _invalid("Video observation does not match the exact Gate submission.")
        if state.provider_file_id != observation.provider_file_id:
            raise _invalid("Video provider file locator does not match its observation.")
        if (
            state.phase
            in {
                VideoAttemptPhase.FETCH,
                VideoAttemptPhase.VALIDATE,
                VideoAttemptPhase.CANDIDATE,
                VideoAttemptPhase.ACTIVATE,
            }
            and observation.state is not VideoTaskState.SUCCEEDED
        ):
            raise _invalid("Video fetch phases require a succeeded observation.")
    if len(request_owners) != len(set(request_owners)):
        raise _invalid("Video generation request ownership is ambiguous.")


def verify_manifest_video_evidence(root: Path, manifest: ProductionManifest) -> None:
    states: list[VideoGenerationAttemptState] = []
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        states.append(state)
        if state.phase is VideoAttemptPhase.REQUEST:
            continue
        paid_state = attempt.paid_provider_state
        if paid_state is None:
            raise _invalid("Video attempt is missing Paid Provider Gate evidence.")
        gate = load_paid_provider_gate_receipt(root, paid_state.gate_receipt)
        request = load_video_request_receipt(root, state.request)
        if (
            gate.preview.operation != "video_generation"
            or gate.preview.attempt_id != attempt.attempt_id
            or gate.preview.request_fingerprint != request.resolved_generation_hash
            or gate.preview.provider_kind != request.provider_kind
            or gate.preview.model_id != request.model_id
        ):
            raise _invalid("Video attempt does not match its exact Paid Provider Gate.")
    verify_video_evidence(root, states)
