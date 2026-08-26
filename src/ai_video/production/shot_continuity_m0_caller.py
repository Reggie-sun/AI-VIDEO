"""Candidate-neutral, qualification-only M0 local submit caller."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import (
    DurableLocalVideoSubmitPermit,
    LocalVideoSubmitIntent,
    LocalVideoSubmitResult,
)
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.shot_continuity_m0_fast_validation import (
    M0FastQualificationExecutionSources,
    M0FastValidationPreSubmitGuard,
    compile_m0_fast_qualification_workflow,
    load_m0_fast_qualification_execution_sources,
    reopen_m0_fast_validation_preflight,
    validate_m0_fast_live_node_schemas,
)
from ai_video.production.shot_continuity_m0_policy import (
    M0ValidationPolicyCatalog,
    M0ValidationPolicyId,
    M0ValidationSelection,
)
from ai_video.production.shot_continuity_m0_qualification import (
    M0QualificationCompileInputs,
    M0QualificationExecutionSources,
    M0ValidationPreSubmitGuard,
    M0ValidationPreflightSnapshot,
    compile_m0_qualification_workflow,
    load_m0_qualification_execution_sources,
    reopen_m0_validation_preflight,
    validate_m0_live_node_schemas,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoGenerationPreview,
    validate_terminal_frame_evidence_against_project,
)
from ai_video.production.video_generation import VideoGenerationService


@dataclass(frozen=True)
class M0QualificationInput:
    """Immutable bytes that were reopened and sealed before permit consumption."""

    file_name: str
    data: bytes
    file_sha256: str
    size_bytes: int


@dataclass(frozen=True)
class M0AcceptedUpstreamSnapshot:
    """Read-only projection from canonical upstream evidence owners."""

    terminal_evidence_hash: str
    source_shot_id: str
    source_shot_revision: int
    source_shot_content_hash: str
    source_video_asset_id: str
    source_video_sha256: str
    source_registry_revision_id: str
    source_generation_id: str
    source_request_input_hash: str
    source_resolved_generation_hash: str
    source_execution_stack_hash: str
    source_provenance_receipt_id: str
    source_provenance_receipt_sha256: str
    source_p6_acceptance_evidence_id: str
    source_p6_acceptance_evidence_sha256: str
    motion_tail_registry_revision_id: str
    motion_tail_extraction_receipt_id: str
    motion_tail_extraction_receipt_sha256: str
    motion_tail_materialization_receipt_id: str
    motion_tail_materialization_receipt_sha256: str
    motion_tail_asset_id: str
    motion_tail_asset_sha256: str


class M0AcceptedUpstreamReopener(Protocol):
    """Reopen canonical generation/P6/derivation evidence without writing.

    The returned source execution stack must come from the reopened canonical
    source generation request, not from the destination request or P0 policy.
    """

    def __call__(
        self,
        *,
        project: Any,
        source_video_asset_id: str,
        motion_tail_asset_id: str,
    ) -> M0AcceptedUpstreamSnapshot: ...


class M0QualificationTransport(Protocol):
    deployment_identity: str

    def get_object_info(self) -> dict[str, Any]: ...

    def upload_input(self, item: M0QualificationInput) -> str: ...

    def submit_prompt(self, workflow: dict[str, Any]) -> str: ...


M0QualificationAssetResolver = Callable[[str, str], Path]


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _value(value: object) -> object:
    return getattr(value, "value", value)


def _validate_request(
    request: ResolvedVideoGenerationRequest | Any,
    sources: M0QualificationExecutionSources | M0FastQualificationExecutionSources,
) -> None:
    profile = sources.profile
    try:
        c4 = request.c4_multi_anchor_binding
        tail = c4.motion_tail
        terminal = c4.terminal
        images = tuple(request.image_bindings)
        media = tuple(request.media_bindings)
        if (
            request.provider_name != profile.provider_kind
            or request.provider_kind != profile.provider_kind
            or request.model_id != profile.model_id
            or request.capability_id != profile.capability_id
            or request.provider_profile.profile_id != profile.candidate_id
            or request.provider_profile.profile_version
            != f"v{profile.contract_version}"
            or request.provider_profile.profile_sha256
            != sources.profile_document_hash
            or request.adapter_compiler_hash
            != sources.materialization.compiler_hash
        ):
            raise _invalid("M0 qualification request identity does not match.")
        if (
            _value(request.execution_kind) != "local"
            or _value(request.billing_kind) != "local_unmetered"
            or _value(request.mode) != "image_to_video"
            or c4 is None
            or _value(c4.tier) != "motion_boundary"
            or tail is None
        ):
            raise _invalid("M0 qualification requires the local motion-boundary contract.")
        if tuple(item.role for item in images) != (
            "first_frame",
            "last_frame",
            "reference",
        ) or tuple((item.kind, item.role) for item in media) != (
            ("video", "reference_video"),
        ):
            raise _invalid("M0 qualification requires exact four-anchor cardinality.")
        first, last, identity = images
        motion = media[0]
        if (
            first.asset_id != terminal.extracted_asset_id
            or first.asset_sha256 != terminal.extracted_sha256
            or last.asset_id != c4.approved_endpoint.asset_id
            or last.asset_sha256 != c4.approved_endpoint.asset_sha256
            or identity.asset_id != c4.identity_anchor.asset_id
            or identity.asset_sha256 != c4.identity_anchor.asset_sha256
            or motion.asset_id != tail.extracted_asset_id
            or motion.asset_sha256 != tail.extracted_sha256
        ):
            raise _invalid("M0 qualification anchor lineage is not exact.")
        if (
            tail.source_video_asset_id != terminal.source_video_asset_id
            or tail.source_video_sha256 != terminal.source_video_sha256
            or tail.terminal_frame_evidence.content_hash != terminal.content_hash
            or tail.terminal_frame_evidence.source_video_asset_id
            != terminal.source_video_asset_id
            or tail.terminal_frame_evidence.source_video_sha256
            != terminal.source_video_sha256
            or tail.extracted_asset_id == terminal.source_video_asset_id
        ):
            raise _invalid(
                "M0 terminal and motion tail must derive from the same "
                "content-addressed accepted upstream video."
            )
        if (
            isinstance(request.effective_seed, bool)
            or not isinstance(request.effective_seed, int)
            or request.effective_seed < 0
            or request.effective_seed != profile.sealed_seed
        ):
            raise _invalid(
                "M0 qualification requires the exact content-addressed sealed seed."
            )
        try:
            M0QualificationCompileInputs(
                prompt=request.prompt_text,
                seed=request.effective_seed,
                first_frame="first-frame.png",
                last_frame="last-frame.png",
                reference="identity.png",
                reference_video="motion-tail.mp4",
            )
        except ValueError as exc:
            raise _invalid(
                "M0 qualification seed is outside the exact compiler range.",
                str(exc),
            ) from exc
        if (
            hashlib.sha256(request.prompt_text.encode("utf-8")).hexdigest()
            != profile.prompt_sha256
            or request.effective_negative_prompt_text
        ):
            raise _invalid("M0 qualification prompt does not match.")
        output = request.effective_output
        if (
            getattr(output, "timing_mode", None) != "frame_count"
            or getattr(output, "frame_count", None) != profile.frame_count
            or getattr(output, "duration_seconds", None) is not None
            or getattr(output, "dimension_mode", None) != "exact"
            or output.width != profile.width
            or output.height != profile.height
            or output.fps != profile.fps
            or output.container != profile.output_container
            or output.mime_type != "video/mp4"
            or output.native_audio is not profile.native_audio
        ):
            raise _invalid("M0 qualification output contract does not match.")
    except AttributeError as exc:
        raise _invalid("M0 qualification request is incomplete.", str(exc)) from exc


def _reopen_input(
    *,
    root: Path,
    resolver: M0QualificationAssetResolver,
    asset_id: str,
    asset_sha256: str,
    mime_type: str,
    expected_size: int | None,
    label: str,
) -> M0QualificationInput:
    try:
        resolved_path = Path(resolver(asset_id, asset_sha256)).resolve(strict=True)
        reopened = _read_regular_file_nofollow(
            resolved_path,
            contained_by=root,
        )
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        raise _invalid(f"M0 {label} input could not be reopened.", str(exc)) from exc
    if reopened.file_sha256 != asset_sha256 or (
        expected_size is not None and len(reopened.data) != expected_size
    ):
        raise _invalid(f"M0 {label} input bytes do not match the sealed binding.")
    head = reopened.data[:64]
    if mime_type == "image/png":
        if not head.startswith(b"\x89PNG\r\n\x1a\n"):
            raise _invalid(f"M0 {label} input is not PNG bytes.")
    elif mime_type in {"video/mp4", "video/quicktime"}:
        if b"ftyp" not in head:
            raise _invalid(f"M0 {label} input is not MP4/MOV bytes.")
    else:
        raise _invalid(f"M0 {label} input MIME is unsupported.")
    return M0QualificationInput(
        file_name=resolved_path.name,
        data=reopened.data,
        file_sha256=reopened.file_sha256,
        size_bytes=reopened.size_bytes,
    )


@dataclass(frozen=True)
class _ValidatedInputs:
    source_video: M0QualificationInput
    uploads: tuple[
        M0QualificationInput,
        M0QualificationInput,
        M0QualificationInput,
        M0QualificationInput,
    ]
    source_video_sha256: str
    sources: M0QualificationExecutionSources | M0FastQualificationExecutionSources


@dataclass(frozen=True)
class M0QualificationOutcome:
    attempt_id: str
    provider_request_id: str
    source_video_sha256: str
    m0_validation_policy_id: M0ValidationPolicyId
    candidate_capability_id: str


def _expected_upstream_snapshot(
    request: ResolvedVideoGenerationRequest | Any,
    *,
    source_execution_stack_hash: str,
) -> M0AcceptedUpstreamSnapshot:
    terminal = request.c4_multi_anchor_binding.terminal
    tail = request.c4_multi_anchor_binding.motion_tail
    try:
        return M0AcceptedUpstreamSnapshot(
            terminal_evidence_hash=terminal.content_hash,
            source_shot_id=tail.source_shot_id,
            source_shot_revision=tail.source_shot_revision,
            source_shot_content_hash=tail.source_shot_content_hash,
            source_video_asset_id=tail.source_video_asset_id,
            source_video_sha256=tail.source_video_sha256,
            source_registry_revision_id=tail.source_registry_revision_id,
            source_generation_id=tail.source_generation_id,
            source_request_input_hash=tail.source_request_input_hash,
            source_resolved_generation_hash=tail.source_resolved_generation_hash,
            source_execution_stack_hash=source_execution_stack_hash,
            source_provenance_receipt_id=tail.source_provenance_receipt_id,
            source_provenance_receipt_sha256=(
                tail.source_provenance_receipt_sha256
            ),
            source_p6_acceptance_evidence_id=(
                tail.source_p6_acceptance_evidence_id
            ),
            source_p6_acceptance_evidence_sha256=(
                tail.source_p6_acceptance_evidence_sha256
            ),
            motion_tail_registry_revision_id=tail.registry_revision_id,
            motion_tail_extraction_receipt_id=tail.extraction_receipt_id,
            motion_tail_extraction_receipt_sha256=tail.extraction_receipt_sha256,
            motion_tail_materialization_receipt_id=tail.materialization_receipt_id,
            motion_tail_materialization_receipt_sha256=(
                tail.materialization_receipt_sha256
            ),
            motion_tail_asset_id=tail.extracted_asset_id,
            motion_tail_asset_sha256=tail.extracted_sha256,
        )
    except AttributeError as exc:
        raise _invalid(
            "M0 accepted upstream evidence is incomplete.",
            str(exc),
        ) from exc


class M0QualificationProvider:
    """Single-candidate qualification transport seam; not a registered child."""

    def __init__(
        self,
        *,
        profile_path: str | Path,
        artifact_root: str | Path,
        input_root: str | Path,
        transport: M0QualificationTransport,
        asset_resolver: M0QualificationAssetResolver,
        m0_policy_id: M0ValidationPolicyId,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._profile_path = profile_path
        self._artifact_root = artifact_root
        self._input_root = Path(input_root).resolve(strict=True)
        self._transport = transport
        self._asset_resolver = asset_resolver
        self._m0_policy_id = M0ValidationPolicyId(m0_policy_id)
        self._clock = clock or (lambda: datetime.now(UTC))

    @property
    def m0_policy_id(self) -> M0ValidationPolicyId:
        return self._m0_policy_id

    def _sources(
        self,
    ) -> M0QualificationExecutionSources | M0FastQualificationExecutionSources:
        if self._m0_policy_id is M0ValidationPolicyId.FAST_V1:
            return load_m0_fast_qualification_execution_sources(
                profile_path=self._profile_path,
                artifact_root=self._artifact_root,
            )
        return load_m0_qualification_execution_sources(
            profile_path=self._profile_path,
            artifact_root=self._artifact_root,
        )

    def validate_pre_effect(
        self, request: ResolvedVideoGenerationRequest | Any
    ) -> _ValidatedInputs:
        sources = self._sources()
        _validate_request(request, sources)
        if self._transport.deployment_identity != sources.profile.deployment_identity:
            raise _invalid(
                "M0 qualification transport does not match the sealed deployment."
            )
        if self._m0_policy_id is M0ValidationPolicyId.FAST_V1:
            validate_m0_fast_live_node_schemas(
                self._transport.get_object_info(),
                sources,
            )
        else:
            validate_m0_live_node_schemas(
                self._transport.get_object_info(),
                sources,
            )
        terminal = request.c4_multi_anchor_binding.terminal
        source = _reopen_input(
            root=self._input_root,
            resolver=self._asset_resolver,
            asset_id=terminal.source_video_asset_id,
            asset_sha256=terminal.source_video_sha256,
            mime_type="video/mp4",
            expected_size=None,
            label="accepted source video",
        )
        bindings = (*request.image_bindings, request.media_bindings[0])
        uploads = tuple(
            _reopen_input(
                root=self._input_root,
                resolver=self._asset_resolver,
                asset_id=item.asset_id,
                asset_sha256=item.asset_sha256,
                mime_type=item.mime_type,
                expected_size=item.size_bytes,
                label=item.role,
            )
            for item in bindings
        )
        return _ValidatedInputs(
            source_video=source,
            uploads=uploads,
            source_video_sha256=terminal.source_video_sha256,
            sources=sources,
        )

    def preview(
        self, request: ResolvedVideoGenerationRequest | Any
    ) -> VideoGenerationPreview:
        return self._preview_from_sources(request, self._sources())

    @staticmethod
    def _preview_from_sources(
        request: ResolvedVideoGenerationRequest | Any,
        sources: M0QualificationExecutionSources
        | M0FastQualificationExecutionSources,
    ) -> VideoGenerationPreview:
        _validate_request(request, sources)
        return VideoGenerationPreview.create(
            resolved=request,
            estimated_cost_upper_bound_microunits=None,
            currency=None,
            destination=None,
            egress_item_ids=(),
        )

    def preflight(self, request: ResolvedVideoGenerationRequest | Any) -> None:
        self.validate_pre_effect(request)

    def submit_local(
        self,
        request: ResolvedVideoGenerationRequest | Any,
        preview: VideoGenerationPreview,
        intent: LocalVideoSubmitIntent,
        permit: DurableLocalVideoSubmitPermit,
    ) -> LocalVideoSubmitResult:
        validated = self.validate_pre_effect(request)
        if preview != self._preview_from_sources(request, validated.sources) or (
            intent.request_fingerprint != request.resolved_generation_hash
            or intent.preview_fingerprint != preview.preview_fingerprint
        ):
            raise _invalid("M0 qualification preview or intent identity is invalid.")
        if not permit._consume_local_video_submit_permit(
            intent_fingerprint=intent.intent_fingerprint,
            request_fingerprint=request.resolved_generation_hash,
        ):
            raise _invalid("M0 qualification requires one fresh local permit.")
        try:
            uploaded = tuple(
                self._transport.upload_input(item) for item in validated.uploads
            )
            inputs = M0QualificationCompileInputs(
                prompt=request.prompt_text,
                seed=request.effective_seed,
                first_frame=uploaded[0],
                last_frame=uploaded[1],
                reference=uploaded[2],
                reference_video=uploaded[3],
            )
            workflow = (
                compile_m0_fast_qualification_workflow(
                    sources=validated.sources,
                    inputs=inputs,
                )
                if self._m0_policy_id is M0ValidationPolicyId.FAST_V1
                else compile_m0_qualification_workflow(
                    sources=validated.sources,
                    inputs=inputs,
                )
            )
            prompt_id = self._transport.submit_prompt(workflow)
            return LocalVideoSubmitResult.create(
                resolved=request,
                provider_request_id=prompt_id,
                submitted_at=self._clock(),
            )
        except Exception as exc:
            raise AiVideoError(
                code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
                user_message=(
                    "M0 qualification effect outcome is unknown; do not retry or "
                    "fall back."
                ),
                technical_detail=f"{type(exc).__name__}: effect failed",
                retryable=False,
                cause=exc,
            ) from exc


class M0QualificationCaller:
    """Validate the full pre-effect seam, then delegate one local submit."""

    def __init__(
        self,
        *,
        committer: Any,
        provider: M0QualificationProvider,
        profile_path: str | Path,
        artifact_root: str | Path,
        project_loader: Callable[[], Any],
        accepted_upstream_reopener: M0AcceptedUpstreamReopener,
        policy_catalog: M0ValidationPolicyCatalog,
        selection: M0ValidationSelection,
    ) -> None:
        self._committer = committer
        self._provider = provider
        self._profile_path = profile_path
        self._artifact_root = artifact_root
        self._selected_policy = policy_catalog.resolve_selection(selection)
        self._m0_policy_id = self._selected_policy.policy_id
        if provider.m0_policy_id is not self._m0_policy_id:
            raise _invalid("M0 caller and Provider policy selections do not match.")
        if self._m0_policy_id is M0ValidationPolicyId.FAST_V1:
            self._guard = M0FastValidationPreSubmitGuard(
                committer=committer,
                profile_path=profile_path,
                artifact_root=artifact_root,
            )
            self._reopen_preflight = reopen_m0_fast_validation_preflight
        else:
            self._guard = M0ValidationPreSubmitGuard(
                committer=committer,
                profile_path=profile_path,
                artifact_root=artifact_root,
            )
            self._reopen_preflight = reopen_m0_validation_preflight
        self._project_loader = project_loader
        self._accepted_upstream_reopener = accepted_upstream_reopener

    def qualify(
        self,
        *,
        attempt_id: str,
        resolved_request: ResolvedVideoGenerationRequest | Any,
    ) -> M0QualificationOutcome:
        validated, expected_snapshot = self._validate_pre_effect(resolved_request)
        expected_hash = resolved_request.resolved_generation_hash

        def exact_guard(current: ResolvedVideoGenerationRequest) -> None:
            if current.resolved_generation_hash != expected_hash:
                raise _invalid("M0 durable request changed before submit.")
            self._validate_pre_effect(
                current,
                expected_snapshot=expected_snapshot,
            )

        submission = VideoGenerationService(
            committer=self._committer,
            provider=self._provider,
        ).submit_local_once(
            attempt_id=attempt_id,
            pre_submit_guard=exact_guard,
        )
        return M0QualificationOutcome(
            attempt_id=attempt_id,
            provider_request_id=submission.provider_request_id,
            source_video_sha256=validated.source_video_sha256,
            m0_validation_policy_id=self._m0_policy_id,
            candidate_capability_id=resolved_request.capability_id,
        )

    def _validate_pre_effect(
        self,
        request: ResolvedVideoGenerationRequest | Any,
        *,
        expected_snapshot: M0ValidationPreflightSnapshot | None = None,
    ) -> tuple[_ValidatedInputs, M0ValidationPreflightSnapshot]:
        self._guard(request)
        snapshot = self._reopen_preflight(
            committer=self._committer,
            profile_path=self._profile_path,
            artifact_root=self._artifact_root,
        )
        if expected_snapshot is not None and snapshot != expected_snapshot:
            raise _invalid(
                "M0 qualification closure drifted before durable submit intent."
            )
        rubric_hash = dict(snapshot.qualification_input_hashes).get("rubric")
        current_sources = self._provider._sources()
        if (
            snapshot.execution_stack_hash
            != self._selected_policy.execution_stack_hash
            or current_sources.profile_document_hash
            != self._selected_policy.profile_document_hash
            or rubric_hash != self._selected_policy.rubric_hash
            or request.capability_id
            != self._selected_policy.conclusion_capability_id
        ):
            raise _invalid(
                "M0 validation selection does not match the reopened execution closure."
            )
        try:
            project = self._project_loader()
            binding = request.c4_multi_anchor_binding
            validate_terminal_frame_evidence_against_project(
                binding.terminal,
                project,
            )
            validate_terminal_frame_evidence_against_project(
                binding.motion_tail.terminal_frame_evidence,
                project,
            )
            reopened_upstream = self._accepted_upstream_reopener(
                project=project,
                source_video_asset_id=binding.terminal.source_video_asset_id,
                motion_tail_asset_id=binding.motion_tail.extracted_asset_id,
            )
            expected_upstream = _expected_upstream_snapshot(
                request,
                source_execution_stack_hash=snapshot.source_execution_stack_hash,
            )
        except (AiVideoError, AttributeError, KeyError, OSError, ValueError) as exc:
            raise _invalid(
                "M0 accepted upstream source video lineage is not active or exact.",
                str(exc),
            ) from exc
        if reopened_upstream != expected_upstream:
            raise _invalid(
                "M0 accepted upstream P6 or derivation evidence is not exact."
            )
        return self._provider.validate_pre_effect(request), snapshot


__all__ = [
    "M0QualificationCaller",
    "M0AcceptedUpstreamReopener",
    "M0AcceptedUpstreamSnapshot",
    "M0QualificationInput",
    "M0QualificationOutcome",
    "M0QualificationProvider",
    "M0QualificationTransport",
]
