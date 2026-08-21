from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.comfy_image import LocalImageExecutionProfile
from ai_video.production._video_project_reader import (
    load_terminal_frame_evidence,
    load_video_request_receipt,
)
from ai_video.production.image import (
    ContinuityTerminalImageReferenceBinding,
    ImageGenerationAuthorization,
    ImageGenerationPreview,
    ImageGenerationRequest,
    _validate_continuity_terminal_reference,
)
from ai_video.production.models import (
    ImageRequestReceipt,
    ProductionManifest,
    StateCommitAttempt,
    StateCommitStatus,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_image_authorization_path,
    canonical_image_execution_profile_path,
    canonical_image_preview_path,
    canonical_image_request_path,
    canonical_image_submit_intent_path,
)

from ._state_commit_common import (
    _candidate_artifacts_hash,
    _canonical_json_bytes,
    _state_commit_failed,
    _timestamp,
    _validated_transition,
)
from ._state_commit_contracts import (
    PreparedArtifact,
    _DurableImageSubmitPermit,
    _IMAGE_PERMIT_TOKEN,
)


def _image_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.IMAGE_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class _StateCommitImageIntentMixin:
    @staticmethod
    def _validated_image_execution_profile(
        request: ImageGenerationRequest,
        execution_profile: LocalImageExecutionProfile | None,
    ) -> LocalImageExecutionProfile | None:
        if request.provider_kind != "comfyui_local":
            if execution_profile is not None:
                raise _image_invalid(
                    "Execution profiles are reserved for the comfyui_local Provider."
                )
            return None
        if execution_profile is None:
            raise _image_invalid(
                "The comfyui_local Provider requires an exact execution profile."
            )
        try:
            checked = LocalImageExecutionProfile.model_validate(
                execution_profile.model_dump(mode="python")
            )
        except (AttributeError, ValidationError, ValueError) as exc:
            raise _image_invalid(
                "The local image execution profile is not sealed.", str(exc)
            ) from exc
        if checked != execution_profile or request.model_id != checked.profile_id:
            raise _image_invalid(
                "Image request model_id does not match the exact execution profile."
            )
        return checked

    @staticmethod
    def _image_receipt(
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
    ) -> ImageRequestReceipt:
        try:
            checked_request = ImageGenerationRequest.model_validate(
                request.model_dump(mode="python")
            )
            checked_preview = ImageGenerationPreview.model_validate(
                preview.model_dump(mode="python")
            )
            checked_authorization = ImageGenerationAuthorization.model_validate(
                authorization.model_dump(mode="python")
            )
        except (AttributeError, ValidationError, ValueError) as exc:
            raise _image_invalid(
                "Image request, preview, or authorization is not sealed.", str(exc)
            ) from exc
        if (
            checked_request != request
            or checked_preview != preview
            or checked_authorization != authorization
            or preview.request_fingerprint != request.request_fingerprint
            or preview.reference_asset_ids
            != tuple(item.asset_id for item in request.references)
            or not preview.local_only
            or preview.remote
            or preview.output_count != 1
            or preview.output_mime_type != "image/png"
            or authorization.request_fingerprint != request.request_fingerprint
            or authorization.preview_fingerprint != preview.preview_fingerprint
            or not authorization.provider_enabled
            or not authorization.local_only
        ):
            raise _image_invalid(
                "Image preview or authorization does not match the immutable request."
            )
        return ImageRequestReceipt(
            request_id=request.request_id,
            attempt_id=request.attempt_id,
            request_fingerprint=request.request_fingerprint,
            provider_kind=request.provider_kind,
            model_id=request.model_id,
            target_shot_id=request.target_shot_id,
            target_asset_role=request.target_asset_role,
            output_asset_id=request.output_asset_id,
            preview_fingerprint=preview.preview_fingerprint,
            authorization_fingerprint=authorization.authorization_fingerprint,
            policy_receipt_id=authorization.policy_receipt_id,
            usage_license=authorization.usage_license,
        )

    def _validate_image_request_context(
        self,
        manifest: ProductionManifest,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
    ) -> None:
        if manifest.schema_version not in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"}:
            raise _image_invalid(
                "Image generation requires an active Manifest dependency graph."
            )
        if (
            manifest.active_dependency_graph is None
            or request.base_project != manifest.active_project
            or request.base_registry != manifest.active_registry
            or request.base_dependency_graph != manifest.active_dependency_graph
        ):
            raise _image_invalid("Image request base project, registry, or graph is stale.")
        try:
            loaded = self._load_production_project(
                self._project_root / "project.yaml"
            )
        except (AiVideoError, OSError, ValidationError, ValueError) as exc:
            detail = exc.technical_detail if isinstance(exc, AiVideoError) else str(exc)
            raise _image_invalid(
                "Image request base project could not be reopened.", detail
            ) from exc
        if (
            loaded.manifest != manifest
            or loaded.dependency_graph is None
            or loaded.manifest.active_dependency_graph != request.base_dependency_graph
            or loaded.dependency_graph.revision_id
            != request.base_dependency_graph.revision_id
            or loaded.dependency_graph.content_hash
            != request.base_dependency_graph.content_hash
        ):
            raise _image_invalid("Image request active graph identity is inconsistent.")
        target_shot = next(
            (item for item in loaded.shots if item.shot_id == request.target_shot_id),
            None,
        )
        if target_shot is None or request.target_asset_role not in {
            item.role for item in target_shot.required_asset_roles
        }:
            raise _image_invalid("Image request target Shot role does not exist.")

        assets = {item.asset_id: item for item in loaded.registry.assets}
        characters = {item.artifact_id: item for item in loaded.characters}
        scenes = {item.artifact_id: item for item in loaded.scenes}
        reference_bytes = 0
        for reference in request.references:
            if isinstance(reference, ContinuityTerminalImageReferenceBinding):
                try:
                    _validate_continuity_terminal_reference(reference, loaded)
                    source_attempt = next(
                        attempt
                        for attempt in loaded.manifest.attempts
                        if attempt.video_generation_state is not None
                        and attempt.video_generation_state.terminal_frame_evidence
                        is not None
                        and attempt.video_generation_state.terminal_frame_evidence.content_hash
                        == reference.terminal_frame.content_hash
                    )
                    source_state = source_attempt.video_generation_state
                    assert source_state is not None
                    pointer = source_state.terminal_frame_evidence
                    assert pointer is not None
                    source_request = load_video_request_receipt(
                        self._project_root, source_state.request
                    )
                    source_scope = source_request.activation_scope
                    if (
                        load_terminal_frame_evidence(self._project_root, pointer)
                        != reference.terminal_frame
                        or source_scope is None
                        or source_scope.request.target_shot_id
                        != reference.terminal_frame.source_shot_id
                        or source_scope.request.target_shot_revision
                        != reference.terminal_frame.source_shot_revision
                        or source_scope.request.target_shot_content_hash
                        != reference.terminal_frame.source_shot_content_hash
                    ):
                        raise ValueError(
                            "continuity terminal does not match durable evidence bytes"
                        )
                except (StopIteration, ValueError) as exc:
                    raise _image_invalid(
                        "Image continuity terminal identity is stale or invalid.",
                        str(exc),
                    ) from exc
                asset = assets.get(reference.asset_id)
                if asset is None:
                    raise _image_invalid(
                        "Image continuity terminal is absent from the active Registry."
                    )
                reference_bytes += asset.size_bytes
                continue
            if reference.role == "character":
                creative = characters.get(reference.creative_artifact_id)
                allowed_asset_ids = (
                    creative.reference_asset_ids if creative is not None else ()
                )
            elif reference.role == "scene":
                creative = scenes.get(reference.creative_artifact_id)
                allowed_asset_ids = (
                    creative.visual_reference_asset_ids if creative is not None else ()
                )
            else:
                raise _image_invalid(
                    "Image generation supports exact Character and Scene references only."
                )
            asset = assets.get(reference.asset_id)
            if (
                creative is None
                or creative.revision != reference.creative_revision
                or creative.content_hash != reference.creative_content_hash
                or reference.asset_id not in allowed_asset_ids
                or asset is None
                or asset.sha256 != reference.asset_sha256
            ):
                raise _image_invalid(
                    "Image reference identity is stale or not selected by its creative artifact."
                )
            reference_bytes += asset.size_bytes
        if preview.reference_total_bytes != reference_bytes:
            raise _image_invalid(
                "Image preview reference byte total does not match the active Registry."
            )

    def _image_prepared_artifact(
        self, attempt_id: str, relative_path: Path, payload: bytes
    ) -> PreparedArtifact:
        return self.prepare_artifact(attempt_id, relative_path, payload)

    def _expected_image_r1_artifacts(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        execution_profile: LocalImageExecutionProfile | None = None,
    ) -> tuple[PreparedArtifact, ...]:
        checked_profile = self._validated_image_execution_profile(
            request, execution_profile
        )
        evidence = (
            self._image_prepared_artifact(
                request.attempt_id,
                canonical_image_request_path(request.request_fingerprint),
                _canonical_json_bytes(request),
            ),
            self._image_prepared_artifact(
                request.attempt_id,
                canonical_image_preview_path(preview.preview_fingerprint),
                _canonical_json_bytes(preview),
            ),
            self._image_prepared_artifact(
                request.attempt_id,
                canonical_image_authorization_path(
                    authorization.authorization_fingerprint
                ),
                _canonical_json_bytes(authorization),
            ),
        )
        if checked_profile is None:
            return evidence
        return (
            *evidence,
            self._image_prepared_artifact(
                request.attempt_id,
                canonical_image_execution_profile_path(
                    checked_profile.profile_content_hash
                ),
                _canonical_json_bytes(checked_profile),
            ),
        )

    def begin_image_generation(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        *,
        execution_profile: LocalImageExecutionProfile | None = None,
    ) -> ProductionManifest:
        """Persist exact image R+1 evidence without invoking a Provider."""

        receipt = self._image_receipt(request, preview, authorization)
        evidence = self._expected_image_r1_artifacts(
            request, preview, authorization, execution_profile
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            self._validate_image_request_context(manifest, request, preview)
            existing = next(
                (
                    item
                    for item in manifest.attempts
                    if item.attempt_id == request.attempt_id
                ),
                None,
            )
            if existing is not None:
                if (
                    existing.operation == "image_generation"
                    and existing.status is StateCommitStatus.RUNNING
                    and existing.image_phase == "request"
                    and existing.image_request == receipt
                    and existing.base_project == request.base_project
                    and existing.base_registry == request.base_registry
                    and existing.base_dependency_graph
                    == request.base_dependency_graph
                ):
                    reopened = self._reopen_image_evidence(
                        request,
                        preview,
                        authorization,
                        execution_profile=execution_profile,
                        include_intent=False,
                    )
                    if (
                        reopened != evidence
                        or _candidate_artifacts_hash(reopened)
                        != existing.candidate_artifacts_hash
                    ):
                        raise _image_invalid("Image R+1 replay evidence is not exact.")
                    return manifest
                raise _image_invalid(
                    "Image attempt ID was already used by another request."
                )
            if any(
                item.status
                in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                for item in manifest.attempts
            ):
                raise _image_invalid(
                    "Production state has an unresolved attempt; explicit recovery is required."
                )
            for artifact in evidence:
                self._write_immutable_artifact(
                    artifact, attempt_id=request.attempt_id
                )
            attempt = StateCommitAttempt(
                attempt_id=request.attempt_id,
                operation="image_generation",
                status=StateCommitStatus.RUNNING,
                base_manifest_revision=manifest.manifest_revision,
                base_project=manifest.active_project,
                base_registry=manifest.active_registry,
                base_dependency_graph=manifest.active_dependency_graph,
                candidate_artifacts_hash=_candidate_artifacts_hash(evidence),
                image_request=receipt,
                image_phase="request",
                started_at=_timestamp(),
            )
            r1 = _validated_transition(
                manifest,
                {
                    "schema_version": (
                        manifest.schema_version
                        if manifest.schema_version in {"2.5", "2.6", "2.7", "2.8", "2.9"}
                        else "2.5"
                    ),
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": manifest.attempts + (attempt,),
                },
            )
            self._write_manifest_atomic(r1)
            reopened = self._read_manifest()
            if reopened != r1:
                raise _state_commit_failed(
                    "Image request Manifest reopen verification failed."
                )
            return reopened

    def record_image_submit_intent(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        *,
        execution_profile: LocalImageExecutionProfile | None = None,
    ) -> _DurableImageSubmitPermit:
        """Persist exact image R+2 intent before minting a one-use permit."""

        receipt = self._image_receipt(request, preview, authorization)
        with self._exclusive_lock():
            manifest = self._read_manifest()
            self._validate_image_request_context(manifest, request, preview)
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
                or attempt.image_phase != "request"
                or attempt.image_request != receipt
                or attempt.base_project != request.base_project
                or attempt.base_registry != request.base_registry
                or attempt.base_dependency_graph != request.base_dependency_graph
            ):
                raise _image_invalid(
                    "Image submit intent requires the exact current R+1 attempt."
                )
            expected_r1 = self._expected_image_r1_artifacts(
                request, preview, authorization, execution_profile
            )
            reopened_r1 = self._reopen_image_evidence(
                request,
                preview,
                authorization,
                execution_profile=execution_profile,
                include_intent=False,
            )
            if (
                reopened_r1 != expected_r1
                or _candidate_artifacts_hash(reopened_r1)
                != attempt.candidate_artifacts_hash
            ):
                raise _image_invalid("Image R+1 evidence changed before submit intent.")

            intent_payload = self._image_submit_intent_payload(
                request,
                preview,
                authorization,
                evidence_hash=attempt.candidate_artifacts_hash,
            )
            intent_artifact = self._image_prepared_artifact(
                request.attempt_id,
                canonical_image_submit_intent_path(request.request_fingerprint),
                intent_payload,
            )
            self._write_immutable_artifact(
                intent_artifact, attempt_id=request.attempt_id
            )
            aggregate = _candidate_artifacts_hash((*reopened_r1, intent_artifact))
            r2_attempt = _validated_transition(
                attempt,
                {
                    "image_phase": "submit_intent",
                    "candidate_artifacts_hash": aggregate,
                },
            )
            r2 = _validated_transition(
                manifest,
                {
                    "manifest_revision": manifest.manifest_revision + 1,
                    "attempts": tuple(
                        r2_attempt
                        if item.attempt_id == request.attempt_id
                        else item
                        for item in manifest.attempts
                    ),
                },
            )
            self._write_manifest_atomic(r2)
            reopened = self._read_manifest()
            reopened_attempt = next(
                item
                for item in reopened.attempts
                if item.attempt_id == request.attempt_id
            )
            if (
                reopened != r2
                or reopened_attempt.image_phase != "submit_intent"
                or reopened_attempt.candidate_artifacts_hash != aggregate
            ):
                raise _state_commit_failed(
                    "Image submit intent Manifest reopen verification failed."
                )
            reopened_all = self._reopen_image_evidence(
                request,
                preview,
                authorization,
                execution_profile=execution_profile,
                include_intent=True,
            )
            if (
                reopened_all != (*expected_r1, intent_artifact)
                or _candidate_artifacts_hash(reopened_all) != aggregate
            ):
                raise _state_commit_failed(
                    "Image submit intent exact-byte verification failed."
                )
            manifest_snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            binding: dict[str, object] = {
                "attempt_id": request.attempt_id,
                "request_fingerprint": request.request_fingerprint,
                "preview_fingerprint": preview.preview_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
                "base_project": request.base_project,
                "base_registry": request.base_registry,
                "base_dependency_graph": request.base_dependency_graph,
                "manifest_revision": reopened.manifest_revision,
                "manifest_file_sha256": manifest_snapshot.file_sha256,
                "evidence_hash": aggregate,
                "submit_intent_sha256": intent_artifact.file_sha256,
            }
            return _DurableImageSubmitPermit(
                _IMAGE_PERMIT_TOKEN,
                binding=binding,
                manifest_revision=reopened.manifest_revision,
                manifest_file_sha256=manifest_snapshot.file_sha256,
                durability_validator=lambda: self._image_submit_intent_is_current(
                    request,
                    preview,
                    authorization,
                    execution_profile=execution_profile,
                    receipt=receipt,
                    manifest_revision=reopened.manifest_revision,
                    manifest_file_sha256=manifest_snapshot.file_sha256,
                    aggregate_hash=aggregate,
                    intent_artifact=intent_artifact,
                ),
            )

    @staticmethod
    def _image_submit_intent_payload(
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        *,
        evidence_hash: str,
    ) -> bytes:
        payload = json.dumps(
            {
                "schema": "ai-video-image-submit-intent/1",
                "attempt_id": request.attempt_id,
                "request_fingerprint": request.request_fingerprint,
                "preview_fingerprint": preview.preview_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
                "policy_receipt_id": authorization.policy_receipt_id,
                "usage_license": authorization.usage_license,
                "base_project": request.base_project.model_dump(mode="json"),
                "base_registry": request.base_registry.model_dump(mode="json"),
                "base_dependency_graph": request.base_dependency_graph.model_dump(
                    mode="json"
                ),
                "evidence_hash": evidence_hash,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return (payload + "\n").encode("utf-8")

    def _reopen_image_evidence(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        *,
        execution_profile: LocalImageExecutionProfile | None = None,
        include_intent: bool,
    ) -> tuple[PreparedArtifact, ...]:
        checked_profile = self._validated_image_execution_profile(
            request, execution_profile
        )
        selected = [
            canonical_image_request_path(request.request_fingerprint),
            canonical_image_preview_path(preview.preview_fingerprint),
            canonical_image_authorization_path(
                authorization.authorization_fingerprint
            ),
        ]
        if checked_profile is not None:
            selected.append(
                canonical_image_execution_profile_path(
                    checked_profile.profile_content_hash
                )
            )
        if include_intent:
            selected.append(
                canonical_image_submit_intent_path(request.request_fingerprint)
            )
        artifacts = []
        try:
            for relative_path in selected:
                snapshot = _read_regular_file_nofollow(
                    self._project_root / relative_path,
                    contained_by=self._project_root,
                )
                artifacts.append(
                    PreparedArtifact(
                        relative_path=relative_path,
                        payload=snapshot.data,
                        file_sha256=snapshot.file_sha256,
                    )
                )
        except (OSError, ValueError) as exc:
            raise _image_invalid(
                "Image durable evidence could not be reopened.", str(exc)
            ) from exc
        return tuple(artifacts)

    def _image_submit_intent_is_current(
        self,
        request: ImageGenerationRequest,
        preview: ImageGenerationPreview,
        authorization: ImageGenerationAuthorization,
        *,
        execution_profile: LocalImageExecutionProfile | None,
        receipt: ImageRequestReceipt,
        manifest_revision: int,
        manifest_file_sha256: str,
        aggregate_hash: str,
        intent_artifact: PreparedArtifact,
    ) -> bool:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / "state/manifest.json",
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != manifest_file_sha256:
                return False
            manifest = ProductionManifest.model_validate_json(snapshot.data)
            self._validate_image_request_context(manifest, request, preview)
            evidence = self._reopen_image_evidence(
                request,
                preview,
                authorization,
                execution_profile=execution_profile,
                include_intent=True,
            )
            expected = (
                *self._expected_image_r1_artifacts(
                    request, preview, authorization, execution_profile
                ),
                intent_artifact,
            )
        except (AiVideoError, OSError, ValidationError, ValueError):
            return False
        attempt = next(
            (
                item
                for item in manifest.attempts
                if item.attempt_id == request.attempt_id
            ),
            None,
        )
        return (
            manifest.manifest_revision == manifest_revision
            and manifest.active_project == request.base_project
            and manifest.active_registry == request.base_registry
            and manifest.active_dependency_graph == request.base_dependency_graph
            and attempt is not None
            and attempt.operation == "image_generation"
            and attempt.status is StateCommitStatus.RUNNING
            and attempt.image_phase == "submit_intent"
            and attempt.image_request == receipt
            and attempt.base_project == request.base_project
            and attempt.base_registry == request.base_registry
            and attempt.base_dependency_graph == request.base_dependency_graph
            and attempt.candidate_artifacts_hash == aggregate_hash
            and evidence == expected
            and _candidate_artifacts_hash(evidence) == aggregate_hash
            and evidence[-1].file_sha256 == intent_artifact.file_sha256
        )
