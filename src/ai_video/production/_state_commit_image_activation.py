from __future__ import annotations

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image import (
    ImageAssetProvider,
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    ImageProviderResult,
)
from ai_video.production.models import (
    ProductionManifest,
    StateCommitAttempt,
    StateCommitStatus,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _dependency_states_hash,
    _outcome_unknown,
    _state_invalid,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import _DurableImageSubmitPermit


def _image_outcome_unknown(exc: BaseException, message: str) -> AiVideoError:
    if (
        isinstance(exc, AiVideoError)
        and exc.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    ):
        return exc
    error = AiVideoError(
        ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
        message,
        type(exc).__name__,
        retryable=False,
    )
    error.add_note(f"Original image lifecycle failure type: {type(exc).__name__}")
    return error


class _StateCommitImageActivationMixin:
    def generate_image_asset(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        provider: ImageAssetProvider,
    ) -> ProductionManifest:
        """Invoke exactly one permitted local Provider call, then activate its result."""

        self.begin_image_generation(request, preview, authorization)
        permit = self.record_image_submit_intent(request, preview, authorization)
        try:
            result = provider.generate(request, authorization, permit)
        except Exception as exc:
            self._record_image_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                detail="Image Provider outcome is unknown; blind retry is forbidden.",
            )
            raise _image_outcome_unknown(
                exc,
                "Image Provider outcome is unknown; blind retry is forbidden.",
            ) from exc
        if not permit._image_generation_was_consumed(
            request_fingerprint=request.request_fingerprint
        ):
            error = _state_invalid(
                "Image Provider returned without consuming the exact durable permit."
            )
            self._record_image_outcome_unknown(
                request.attempt_id,
                phase="provider_call",
                detail=error.user_message,
            )
            raise _image_outcome_unknown(
                error,
                "Image Provider outcome is unknown; blind retry is forbidden.",
            ) from error
        return self.activate_image_asset(
            request,
            preview,
            authorization,
            result,
            permit,
        )

    def activate_image_asset(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        result: ImageProviderResult,
        permit: _DurableImageSubmitPermit,
    ) -> ProductionManifest:
        """Persist a validated image candidate and atomically select its bundle."""

        if not isinstance(permit, _DurableImageSubmitPermit) or not (
            permit._image_generation_was_consumed(
                request_fingerprint=request.request_fingerprint
            )
        ):
            raise _state_invalid(
                "Image activation requires the exact consumed durable permit."
            )
        final_replaced = [False]
        try:
            return self._activate_image_asset_locked(
                request,
                preview,
                authorization,
                result,
                permit,
                final_replaced,
            )
        except Exception as exc:
            if final_replaced[0]:
                raise _outcome_unknown(exc) from exc
            current = self._read_manifest()
            attempt = next(
                (
                    item
                    for item in current.attempts
                    if item.attempt_id == request.attempt_id
                ),
                None,
            )
            if attempt is not None and attempt.status is StateCommitStatus.RUNNING:
                self._record_image_outcome_unknown(
                    request.attempt_id,
                    phase=(
                        "candidate"
                        if attempt.image_phase == "candidate"
                        else "materialize"
                    ),
                    detail=(
                        "Image result could not be durably activated; "
                        "explicit recovery is required."
                    ),
                )
            raise _image_outcome_unknown(
                exc,
                "Image result activation outcome is unknown; explicit recovery is required.",
            ) from exc

    def _activate_image_asset_locked(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        result: ImageProviderResult,
        permit: _DurableImageSubmitPermit,
        final_replaced: list[bool],
    ) -> ProductionManifest:
        with self._exclusive_lock():
            if not permit._image_generation_was_consumed(
                request_fingerprint=request.request_fingerprint
            ):
                raise _state_invalid(
                    "Image activation durable R+2 evidence is no longer current."
                )
            manifest = self._read_manifest()
            self._validate_image_request_context(manifest, request, preview)
            attempt = self._require_image_submit_attempt(manifest, request)
            base_project = self._load_production_project(
                self._project_root / "project.yaml"
            )
            if base_project.manifest != manifest:
                raise _state_invalid(
                    "Image activation base bundle does not match durable R+2."
                )

            measured, receipt, result_artifacts = self._persist_image_provider_result(
                request, authorization, result
            )
            accepted, candidate_artifacts = self._prepare_validated_image_candidate(
                base_project=base_project,
                request=request,
                authorization=authorization,
                result=result,
                measured=measured,
                receipt=receipt,
            )
            reopened_candidates = self._persist_image_candidate_artifacts(
                request, candidate_artifacts
            )
            request_artifact = self._reopen_image_request_artifact(request)
            exact_artifacts = (
                request_artifact,
                *result_artifacts,
                *reopened_candidates,
            )
            if len(exact_artifacts) != 8:
                raise _state_invalid(
                    "Image activation candidate artifact set is not exact."
                )
            candidate_hash = _candidate_artifacts_hash(exact_artifacts)
            states_hash = _dependency_states_hash(accepted.resolution.states)
            candidate_attempt = _validated_transition(
                attempt,
                {
                    "candidate_project": accepted.candidate_project_pointer,
                    "candidate_registry": accepted.candidate_registry_pointer,
                    "candidate_artifacts_hash": candidate_hash,
                    "image_phase": "candidate",
                    "provider_request_id": result.provider_request_id,
                    "candidate_image_asset_ids": (accepted.image_asset_id,),
                    "candidate_dependency_graph": accepted.candidate_graph_pointer,
                    "candidate_dependency_states_hash": states_hash,
                },
            )
            succeeded_attempt = _validated_transition(
                candidate_attempt,
                {
                    "status": StateCommitStatus.SUCCEEDED,
                    "image_phase": "activate",
                    "finished_at": _timestamp(),
                    "error_code": None,
                    "error_message": None,
                },
            )
            verification_attempts = tuple(
                succeeded_attempt
                if item.attempt_id == request.attempt_id
                else item
                for item in manifest.attempts
            )
            self._verify_dependency_candidate(
                manifest,
                accepted.candidate_graph,
                accepted.resolution.states,
                project_pointer=accepted.candidate_project_pointer,
                registry_pointer=accepted.candidate_registry_pointer,
                attempts=verification_attempts,
            )
            candidate_manifest = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        candidate_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(candidate_manifest)
            reopened_candidate = self._read_manifest()
            if reopened_candidate != candidate_manifest:
                raise _state_invalid(
                    "Image candidate Manifest reopen verification failed."
                )

            final = _validated_transition(
                reopened_candidate,
                {
                    "manifest_revision": reopened_candidate.manifest_revision + 1,
                    "active_project": accepted.candidate_project_pointer,
                    "active_registry": accepted.candidate_registry_pointer,
                    "active_dependency_graph": accepted.candidate_graph_pointer,
                    "dependency_states": accepted.resolution.states,
                    "attempts": tuple(
                        succeeded_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in reopened_candidate.attempts
                    ),
                },
            )

            def mark_replaced() -> None:
                final_replaced[0] = True

            self._write_manifest_atomic(final, on_replace=mark_replaced)
            reopened = self._read_manifest()
            if reopened != final:
                raise _state_invalid(
                    "Image final Manifest reopen verification failed."
                )
            selected = self._load_production_project(
                self._project_root / "project.yaml"
            )
            if (
                selected.manifest != final
                or selected.project != accepted.candidate_project.project
                or selected.registry != accepted.candidate_registry
                or selected.dependency_graph != accepted.candidate_graph
            ):
                raise _state_invalid(
                    "Image selected bundle does not match the validated candidate."
                )
            return reopened

    @staticmethod
    def _require_image_submit_attempt(
        manifest: ProductionManifest,
        request: ImageGenerationRequest,
    ) -> StateCommitAttempt:
        attempt = next(
            (
                item
                for item in manifest.attempts
                if item.attempt_id == request.attempt_id
            ),
            None,
        )
        if (
            attempt is None
            or attempt.operation != "image_generation"
            or attempt.status is not StateCommitStatus.RUNNING
            or attempt.image_phase != "submit_intent"
            or attempt.image_request is None
            or attempt.image_request.request_fingerprint
            != request.request_fingerprint
            or attempt.base_project != request.base_project
            or attempt.base_registry != request.base_registry
            or attempt.base_dependency_graph != request.base_dependency_graph
        ):
            raise _state_invalid(
                "Image activation requires the exact current durable R+2 attempt."
            )
        return attempt

    def _record_image_outcome_unknown(
        self,
        attempt_id: str,
        *,
        phase: str,
        detail: str,
    ) -> ProductionManifest:
        with self._exclusive_lock():
            manifest = self._read_manifest()
            attempt = next(
                (item for item in manifest.attempts if item.attempt_id == attempt_id),
                None,
            )
            if attempt is None:
                raise _state_invalid(
                    "Image outcome cannot be recorded without its durable attempt."
                )
            if attempt.status is StateCommitStatus.OUTCOME_UNKNOWN:
                return manifest
            if attempt.status is not StateCommitStatus.RUNNING:
                raise _state_invalid(
                    "Image outcome can only close a running attempt."
                )
            unknown = _validated_transition(
                attempt,
                {
                    "status": StateCommitStatus.OUTCOME_UNKNOWN,
                    "image_phase": phase,
                    "finished_at": _timestamp(),
                    "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                    "error_message": detail[-2_048:],
                },
            )
            updated = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        unknown if item.attempt_id == attempt_id else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(updated)
            return self._read_manifest()
