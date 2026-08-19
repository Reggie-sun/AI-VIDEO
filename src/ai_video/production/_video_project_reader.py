from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._lifecycle_schema import (
    LocalVideoFetchReceiptPointer,
    LocalVideoStatusReceiptPointer,
    LocalVideoSubmitIntentPointer,
    LocalVideoSubmitReceiptPointer,
)
from ai_video.production._paid_provider_project_reader import (
    load_paid_provider_budget_by_content_hash,
    load_paid_provider_gate_receipt,
    load_paid_provider_submit_receipt,
)
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    PaidProviderAttemptPhase,
    ProductionManifest,
    StateCommitStatus,
    StateCommitAttempt,
    VideoAttemptPhase,
    VideoFetchReceiptPointer,
    VideoGenerationAttemptState,
    VideoRequestReceiptPointer,
    VideoStatusReceiptPointer,
    TerminalFrameEvidencePointer,
    TerminalFrameExtractionReceiptPointer,
)
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
    LocalVideoTaskObservation,
)
from ai_video.production.paid_provider import BudgetReservationStatus
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_video_probe_receipt_path,
    canonical_video_provenance_receipt_path,
    canonical_image_asset_path,
    canonical_terminal_frame_extraction_receipt_path,
    resolve_contained_path,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoSubmission,
    VideoTaskObservation,
    VideoTaskState,
    TerminalFrameEvidence,
)
from ai_video.production.video_artifact import (
    TerminalFrameExtractionReceipt,
    VideoProbeReceipt,
    VideoProvenanceReceipt,
    bind_terminal_frame_evidence,
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


def load_video_fetch_receipt(
    root: str | Path, pointer: VideoFetchReceiptPointer
) -> VideoFetchReceipt:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved,
            contained_by=resolved_root / "state",
        )
        receipt = VideoFetchReceipt.model_validate_json(raw.data)
        artifact_path = resolve_contained_path(
            resolved_root,
            pointer.artifact_path,
            allowed_root=resolved_root / "state" / "video-generation" / "fetch",
        )
        artifact = _read_regular_file_nofollow(
            artifact_path,
            contained_by=resolved_root / "state" / "video-generation" / "fetch",
        )
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen video fetch evidence.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or receipt.fetch_fingerprint != pointer.fetch_fingerprint
        or receipt.artifact_sha256 != pointer.artifact_sha256
        or receipt.size_bytes != pointer.artifact_size_bytes
        or artifact.file_sha256 != pointer.artifact_sha256
        or len(artifact.data) != pointer.artifact_size_bytes
    ):
        raise _invalid("Video fetch evidence pointer identity is invalid.")
    return receipt


def load_local_video_submit_intent(
    root: str | Path, pointer: LocalVideoSubmitIntentPointer
) -> LocalVideoSubmitIntent:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        intent = LocalVideoSubmitIntent.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen local video submit intent.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or intent.intent_fingerprint != pointer.intent_fingerprint
        or intent.request_fingerprint != pointer.request_fingerprint
    ):
        raise _invalid("Local video submit intent pointer identity is invalid.")
    return intent


def load_local_video_submit_receipt(
    root: str | Path, pointer: LocalVideoSubmitReceiptPointer
) -> LocalVideoSubmitResult:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        result = LocalVideoSubmitResult.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen local video submit receipt.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or result.result_fingerprint != pointer.result_fingerprint
        or result.resolved_generation_hash != pointer.request_fingerprint
        or result.provider_request_id != pointer.provider_request_id
    ):
        raise _invalid("Local video submit receipt pointer identity is invalid.")
    return result


def load_local_video_status_receipt(
    root: str | Path, pointer: LocalVideoStatusReceiptPointer
) -> LocalVideoTaskObservation:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        observation = LocalVideoTaskObservation.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen local video observation.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or observation.observation_fingerprint != pointer.observation_fingerprint
        or observation.submit_result_fingerprint
        != pointer.submit_result_fingerprint
    ):
        raise _invalid("Local video observation pointer identity is invalid.")
    return observation


def load_local_video_fetch_receipt(
    root: str | Path, pointer: LocalVideoFetchReceiptPointer
) -> LocalVideoFetchReceipt:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        receipt = LocalVideoFetchReceipt.model_validate_json(raw.data)
        artifact_path = resolve_contained_path(
            resolved_root,
            pointer.artifact_path,
            allowed_root=resolved_root / "state" / "video-generation" / "fetch",
        )
        artifact = _read_regular_file_nofollow(
            artifact_path,
            contained_by=resolved_root / "state" / "video-generation" / "fetch",
        )
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen local video fetch evidence.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or receipt.fetch_fingerprint != pointer.fetch_fingerprint
        or receipt.artifact_sha256 != pointer.artifact_sha256
        or receipt.size_bytes != pointer.artifact_size_bytes
        or artifact.file_sha256 != pointer.artifact_sha256
        or len(artifact.data) != pointer.artifact_size_bytes
    ):
        raise _invalid("Local video fetch pointer identity is invalid.")
    return receipt


def load_terminal_frame_evidence(
    root: str | Path, pointer: TerminalFrameEvidencePointer
) -> TerminalFrameEvidence:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        evidence = TerminalFrameEvidence.model_validate_json(raw.data)
        extraction_path = resolve_contained_path(
            resolved_root,
            canonical_terminal_frame_extraction_receipt_path(
                evidence.extraction_receipt_id
            ),
            allowed_root=resolved_root / "state" / "video-generation",
        )
        extraction_raw = _read_regular_file_nofollow(
            extraction_path,
            contained_by=resolved_root / "state" / "video-generation",
        )
        extraction = TerminalFrameExtractionReceipt.model_validate_json(
            extraction_raw.data
        )
        image_path = resolve_contained_path(
            resolved_root,
            canonical_image_asset_path(evidence.extracted_sha256),
            allowed_root=resolved_root / "assets",
        )
        image = _read_regular_file_nofollow(
            image_path, contained_by=resolved_root / "assets"
        )
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen terminal frame evidence.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or evidence.content_hash != pointer.content_hash
        or evidence.extracted_asset_id != pointer.extracted_asset_id
        or evidence.extracted_sha256 != pointer.extracted_sha256
        or extraction.content_hash != evidence.extraction_receipt_id
        or bind_terminal_frame_evidence(
            extraction, source_registry=evidence.source_registry
        )
        != evidence
        or image.file_sha256 != evidence.extracted_sha256
        or len(image.data) != evidence.extracted_size_bytes
    ):
        raise _invalid("Terminal frame evidence pointer identity is invalid.")
    return evidence


def load_terminal_frame_extraction(
    root: str | Path, pointer: TerminalFrameExtractionReceiptPointer
) -> tuple[bytes, TerminalFrameExtractionReceipt]:
    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(
            resolved, contained_by=resolved_root / "state"
        )
        extraction = TerminalFrameExtractionReceipt.model_validate_json(raw.data)
        image_path = resolve_contained_path(
            resolved_root,
            canonical_image_asset_path(extraction.extracted_sha256),
            allowed_root=resolved_root / "assets",
        )
        image = _read_regular_file_nofollow(
            image_path, contained_by=resolved_root / "assets"
        )
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid("Could not reopen terminal frame extraction.", str(exc)) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or extraction.content_hash != pointer.content_hash
        or extraction.extracted_asset_id != pointer.extracted_asset_id
        or extraction.extracted_sha256 != pointer.extracted_sha256
        or image.file_sha256 != extraction.extracted_sha256
        or len(image.data) != extraction.extracted_size_bytes
    ):
        raise _invalid("Terminal frame extraction pointer identity is invalid.")
    return image.data, extraction


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
        if state.local_submit_intent is not None:
            intent = load_local_video_submit_intent(root, state.local_submit_intent)
            if intent.request_fingerprint != request.resolved_generation_hash:
                raise _invalid("Local video intent does not match its request.")
            if state.local_submit_receipt is None:
                continue
            result = load_local_video_submit_receipt(
                root, state.local_submit_receipt
            )
            try:
                from ai_video.production.local_video import LocalVideoSubmission

                submission = LocalVideoSubmission.from_submit_result(
                    resolved=request, result=result
                )
            except (AiVideoError, ValueError) as exc:
                raise _invalid(
                    "Local video submit result cannot reconstruct its submission.",
                    str(exc),
                ) from exc
            if state.local_latest_observation is None:
                continue
            observation = load_local_video_status_receipt(
                root, state.local_latest_observation
            )
            if (
                observation.submission_fingerprint
                != submission.submission_fingerprint
                or observation.submit_result_fingerprint
                != result.result_fingerprint
                or state.provider_file_id != observation.provider_file_id
            ):
                raise _invalid("Local video observation identity is invalid.")
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
                raise _invalid("Local video fetch phases require success.")
            if state.local_fetch_receipt is not None:
                fetch = load_local_video_fetch_receipt(
                    root, state.local_fetch_receipt
                )
                if (
                    fetch.submission_fingerprint
                    != submission.submission_fingerprint
                    or fetch.observation_fingerprint
                    != observation.observation_fingerprint
                    or fetch.submit_result_fingerprint != result.result_fingerprint
                    or fetch.provider_file_id != observation.provider_file_id
                ):
                    raise _invalid("Local video fetch evidence is not exact.")
            continue
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
        if state.fetch_receipt is not None:
            fetch = load_video_fetch_receipt(root, state.fetch_receipt)
            if (
                fetch.submission_fingerprint != submission.submission_fingerprint
                or fetch.observation_fingerprint
                != observation.observation_fingerprint
                or fetch.paid_submit_receipt_fingerprint
                != submit_receipt.submit_receipt_fingerprint
                or fetch.provider_file_id != observation.provider_file_id
            ):
                raise _invalid(
                    "Video fetch evidence does not match its exact submission."
                )
    if len(request_owners) != len(set(request_owners)):
        raise _invalid("Video generation request ownership is ambiguous.")


def _load_video_receipt(root: Path, path: Path, model, label: str):
    try:
        raw = _read_regular_file_nofollow(
            root / path,
            contained_by=root / "state" / "video-generation",
        )
        receipt = model.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise _invalid(f"Could not reopen {label}.", str(exc)) from exc
    return receipt


def _verify_active_terminal_frame(
    bundle: LoadedProductionProject,
    attempt: StateCommitAttempt,
    request: ResolvedVideoGenerationRequest,
    video_asset: AssetRecord,
    provenance: VideoProvenanceReceipt,
) -> None:
    state = attempt.video_generation_state
    scope = request.activation_scope
    if state is None or scope is None:
        raise _invalid("Active generated video has no durable authoring scope.")
    expects_terminal = scope.request.seal_terminal_frame
    pointers_present = (
        state.terminal_frame_extraction is not None
        and state.terminal_frame_evidence is not None
    )
    if not expects_terminal:
        if (
            pointers_present
            or state.terminal_frame_extraction is not None
            or state.terminal_frame_evidence is not None
            or state.candidate_continuity_asset_ids
        ):
            raise _invalid("Unexpected terminal frame state is active.")
        return
    if not pointers_present:
        raise _invalid("Active terminal frame evidence is incomplete.")

    assert state.terminal_frame_extraction is not None
    assert state.terminal_frame_evidence is not None
    _, extraction = load_terminal_frame_extraction(
        bundle.root, state.terminal_frame_extraction
    )
    evidence = load_terminal_frame_evidence(bundle.root, state.terminal_frame_evidence)
    expected_asset_id = f"{request.output_asset_id}:terminal-frame"
    assets = {asset.asset_id: asset for asset in bundle.registry.assets}
    terminal_asset = assets.get(expected_asset_id)
    metadata = video_asset.video_metadata
    if (
        metadata is None
        or state.candidate_continuity_asset_ids != (expected_asset_id,)
        or extraction.content_hash != evidence.extraction_receipt_id
        or evidence.source_registry != bundle.manifest.active_registry
        or evidence.source_registry != attempt.candidate_registry
        or evidence.source_shot_id != scope.request.target_shot_id
        or evidence.source_shot_revision != scope.request.target_shot_revision
        or evidence.source_shot_content_hash
        != scope.request.target_shot_content_hash
        or evidence.source_video_asset_id != request.output_asset_id
        or evidence.source_video_sha256 != video_asset.sha256
        or evidence.source_generation_id != request.generation_id
        or evidence.source_request_input_hash != request.request_input_hash
        or evidence.source_resolved_generation_hash
        != request.resolved_generation_hash
        or evidence.source_provenance_receipt_id != provenance.content_hash
        or evidence.source_container_name != metadata.container_name
        or evidence.source_codec_name != metadata.codec_name
        or evidence.source_width != metadata.width
        or evidence.source_height != metadata.height
        or evidence.source_fps_numerator != metadata.fps_numerator
        or evidence.source_fps_denominator != metadata.fps_denominator
        or evidence.source_duration_milliseconds != metadata.duration_milliseconds
        or evidence.source_frame_count != metadata.frame_count
        or terminal_asset is None
        or terminal_asset.asset_type is not AssetType.IMAGE
        or terminal_asset.source_kind is not AssetSourceKind.DERIVED
        or terminal_asset.artifact_path
        != canonical_image_asset_path(evidence.extracted_sha256)
        or terminal_asset.sha256 != evidence.extracted_sha256
        or terminal_asset.size_bytes != evidence.extracted_size_bytes
        or terminal_asset.mime_type != evidence.extracted_mime_type
        or terminal_asset.width != evidence.extracted_width
        or terminal_asset.height != evidence.extracted_height
        or terminal_asset.input_artifact_ids != (request.output_asset_id,)
        or terminal_asset.input_fingerprint != extraction.content_hash
        or terminal_asset.creation_receipt_id != extraction.content_hash
        or terminal_asset.usage_license != scope.usage_license
    ):
        raise _invalid("Active terminal frame evidence chain is invalid.")


def _verify_active_generated_video(
    bundle: LoadedProductionProject,
    attempt,
    request: ResolvedVideoGenerationRequest,
) -> None:
    state = attempt.video_generation_state
    if state is None:
        raise _invalid("Active video generation attempt has no lifecycle state.")
    if (
        attempt.status is not StateCommitStatus.SUCCEEDED
        or state.phase is not VideoAttemptPhase.ACTIVATE
        or attempt.candidate_project != bundle.manifest.active_project
        or attempt.candidate_registry != bundle.manifest.active_registry
        or attempt.candidate_dependency_graph
        != bundle.manifest.active_dependency_graph
        or state.candidate_video_asset_ids != (request.output_asset_id,)
    ):
        raise _invalid("Active generated video selection is not exact.")
    assets = {
        asset.asset_id: asset for asset in bundle.registry.assets
    }
    asset = assets.get(request.output_asset_id)
    if (
        asset is None
        or asset.asset_type is not AssetType.VIDEO
        or asset.source_kind is not AssetSourceKind.GENERATED
        or asset.video_metadata is None
        or asset.input_fingerprint != request.resolved_generation_hash
        or asset.video_metadata.request_receipt_fingerprint
        != request.desired_generation_fingerprint
        or asset.video_metadata.resolved_generation_hash
        != request.resolved_generation_hash
    ):
        raise _invalid("Active generated video Registry evidence is invalid.")
    try:
        artifact = _read_regular_file_nofollow(
            bundle.asset_paths[asset.asset_id],
            contained_by=bundle.root / "assets",
        )
    except (KeyError, OSError, ValueError) as exc:
        raise _invalid("Could not reopen active generated video asset.", str(exc)) from exc
    if artifact.file_sha256 != asset.sha256 or len(artifact.data) != asset.size_bytes:
        raise _invalid("Active generated video bytes do not match the Registry.")

    metadata = asset.video_metadata
    probe = _load_video_receipt(
        bundle.root,
        canonical_video_probe_receipt_path(metadata.probe_receipt_id),
        VideoProbeReceipt,
        "active generated video probe receipt",
    )
    provenance = _load_video_receipt(
        bundle.root,
        canonical_video_provenance_receipt_path(metadata.provenance_receipt_id),
        VideoProvenanceReceipt,
        "active generated video provenance receipt",
    )
    local_lane = state.local_submit_intent is not None
    observation = (
        load_local_video_status_receipt(bundle.root, state.local_latest_observation)
        if local_lane and state.local_latest_observation is not None
        else load_video_status_receipt(bundle.root, state.latest_observation)
        if state.latest_observation is not None
        else None
    )
    fetch = (
        load_local_video_fetch_receipt(bundle.root, state.local_fetch_receipt)
        if local_lane and state.local_fetch_receipt is not None
        else load_video_fetch_receipt(bundle.root, state.fetch_receipt)
        if state.fetch_receipt is not None
        else None
    )
    paid_state = attempt.paid_provider_state
    historical_budget = (
        load_paid_provider_budget_by_content_hash(bundle.root, asset.cost_receipt_id)
        if asset.cost_receipt_id is not None
        else None
    )
    reservation = next(
        (
            item
            for item in historical_budget.reservations
            if paid_state is not None and item.reservation_id == paid_state.reservation_id
        ),
        None,
    ) if historical_budget is not None else None
    if (
        probe.content_hash != metadata.probe_receipt_id
        or probe.request_receipt_fingerprint
        != request.desired_generation_fingerprint
        or probe.resolved_generation_hash != request.resolved_generation_hash
        or probe.measured.artifact_sha256 != asset.sha256
        or probe.measured.size_bytes != asset.size_bytes
        or probe.measured.width != metadata.width
        or probe.measured.height != metadata.height
        or probe.measured.fps_numerator != metadata.fps_numerator
        or probe.measured.fps_denominator != metadata.fps_denominator
        or probe.measured.duration_milliseconds != metadata.duration_milliseconds
        or probe.measured.frame_count != metadata.frame_count
        or provenance.content_hash != metadata.provenance_receipt_id
        or provenance.generation_id != request.generation_id
        or provenance.request_receipt_fingerprint
        != request.desired_generation_fingerprint
        or provenance.resolved_generation_hash != request.resolved_generation_hash
        or provenance.provider_kind != request.provider_kind
        or provenance.model_id != request.model_id
        or provenance.profile_sha256 != request.provider_profile.profile_sha256
        or provenance.artifact_sha256 != asset.sha256
        or provenance.probe_receipt_id != probe.content_hash
        or observation is None
        or fetch is None
        or provenance.observation_fingerprint
        != observation.observation_fingerprint
        or provenance.fetch_fingerprint != fetch.fetch_fingerprint
        or provenance.provider_file_id != fetch.provider_file_id
        or asset.creation_receipt_id != provenance.content_hash
        or asset.usage_license != provenance.usage_license
    ):
        raise _invalid("Active generated video provenance chain is invalid.")
    if local_lane:
        if (
            state.local_submit_receipt is None
            or fetch.submit_result_fingerprint
            != state.local_submit_receipt.result_fingerprint
            or provenance.local_submit_result_fingerprint
            != fetch.submit_result_fingerprint
            or provenance.paid_submit_receipt_fingerprint is not None
            or paid_state is not None
            or asset.cost_receipt_id is not None
            or asset.egress.remote
        ):
            raise _invalid("Active local video provenance chain is invalid.")
    elif (
        provenance.paid_submit_receipt_fingerprint
        != fetch.paid_submit_receipt_fingerprint
        or provenance.local_submit_result_fingerprint is not None
        or paid_state is None
        or paid_state.phase is not PaidProviderAttemptPhase.SETTLED
        or reservation is None
        or reservation.status is not BudgetReservationStatus.SETTLED
        or reservation.attempt_id != attempt.attempt_id
        or reservation.request_fingerprint != request.resolved_generation_hash
        or reservation.submit_receipt_fingerprint
        != provenance.paid_submit_receipt_fingerprint
        or reservation.actual_cost_microunits is None
    ):
        raise _invalid("Active remote video provenance chain is invalid.")
    _verify_active_terminal_frame(bundle, attempt, request, asset, provenance)


def verify_manifest_video_evidence(
    bundle: LoadedProductionProject, manifest: ProductionManifest
) -> None:
    root = bundle.root
    states: list[VideoGenerationAttemptState] = []
    for attempt in manifest.attempts:
        state = attempt.video_generation_state
        if state is None:
            continue
        states.append(state)
        if state.phase is VideoAttemptPhase.REQUEST:
            continue
        paid_state = attempt.paid_provider_state
        request = load_video_request_receipt(root, state.request)
        if state.local_submit_intent is not None:
            intent = load_local_video_submit_intent(root, state.local_submit_intent)
            if (
                paid_state is not None
                or intent.attempt_id != attempt.attempt_id
                or intent.request_fingerprint != request.resolved_generation_hash
                or request.execution_kind.value != "local"
                or request.billing_kind.value != "local_unmetered"
            ):
                raise _invalid("Local video attempt identity is invalid.")
            if (
                state.phase is VideoAttemptPhase.ACTIVATE
                and attempt.candidate_project == manifest.active_project
                and attempt.candidate_registry == manifest.active_registry
                and attempt.candidate_dependency_graph
                == manifest.active_dependency_graph
            ):
                _verify_active_generated_video(bundle, attempt, request)
            continue
        if paid_state is None:
            raise _invalid("Video attempt is missing Paid Provider Gate evidence.")
        gate = load_paid_provider_gate_receipt(root, paid_state.gate_receipt)
        if (
            gate.preview.operation != "video_generation"
            or gate.preview.attempt_id != attempt.attempt_id
            or gate.preview.request_fingerprint != request.resolved_generation_hash
            or gate.preview.provider_kind != request.provider_kind
            or gate.preview.model_id != request.model_id
        ):
            raise _invalid("Video attempt does not match its exact Paid Provider Gate.")
        if (
            state.phase is VideoAttemptPhase.ACTIVATE
            and attempt.candidate_project == manifest.active_project
            and attempt.candidate_registry == manifest.active_registry
            and attempt.candidate_dependency_graph
            == manifest.active_dependency_graph
        ):
            _verify_active_generated_video(bundle, attempt, request)
    verify_video_evidence(root, states)
