from __future__ import annotations

import json

from ai_video.production.image import (
    ImageActivationCandidate,
    ImageGenerationAuthorization,
    ImageGenerationRequest,
    ImageProvenanceReceipt,
    ImageProviderResult,
    MeasuredPng,
    validate_image_activation_candidate,
    validate_image_result,
)
from ai_video.production.models import LoadedProductionProject
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_image_asset_path,
    canonical_image_receipt_path,
    canonical_image_request_path,
    canonical_image_result_path,
)

from ._state_commit_common import _canonical_json_bytes, _state_commit_failed, _state_invalid
from ._state_commit_contracts import PreparedArtifact, PreparedImageCandidate


class _StateCommitImageCandidateMixin:
    @staticmethod
    def _image_result_bytes(result: ImageProviderResult) -> bytes:
        payload = json.dumps(
            result.model_dump(mode="json", exclude={"image_bytes"}),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return (payload + "\n").encode("utf-8")

    def _reopen_exact_image_artifact(
        self, artifact: PreparedArtifact
    ) -> PreparedArtifact:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / artifact.relative_path,
                contained_by=self._project_root,
            )
        except (OSError, ValueError) as exc:
            raise _state_commit_failed(
                "Image candidate artifact could not be reopened.", str(exc)
            ) from exc
        reopened = PreparedArtifact(
            relative_path=artifact.relative_path,
            payload=snapshot.data,
            file_sha256=snapshot.file_sha256,
        )
        if reopened != artifact:
            raise _state_commit_failed(
                "Image candidate artifact exact-byte verification failed."
            )
        return reopened

    def _persist_image_provider_result(
        self,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        result: ImageProviderResult,
    ) -> tuple[
        MeasuredPng,
        ImageProvenanceReceipt,
        tuple[PreparedArtifact, PreparedArtifact, PreparedArtifact],
    ]:
        measured, receipt = validate_image_result(request, authorization, result)
        result_artifact = self.prepare_artifact(
            request.attempt_id,
            canonical_image_result_path(result.result_fingerprint),
            self._image_result_bytes(result),
        )
        image_artifact = self.prepare_artifact(
            request.attempt_id,
            canonical_image_asset_path(measured.sha256),
            result.image_bytes,
        )
        receipt_artifact = self.prepare_artifact(
            request.attempt_id,
            canonical_image_receipt_path(receipt.content_hash),
            _canonical_json_bytes(receipt),
        )
        for artifact in (result_artifact, image_artifact, receipt_artifact):
            self._write_immutable_artifact(
                artifact, attempt_id=request.attempt_id
            )
            self._reopen_exact_image_artifact(artifact)
        return measured, receipt, (result_artifact, image_artifact, receipt_artifact)

    def _prepare_validated_image_candidate(
        self,
        *,
        base_project: LoadedProductionProject,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        result: ImageProviderResult,
        measured: MeasuredPng,
        receipt: ImageProvenanceReceipt,
    ) -> tuple[ImageActivationCandidate, tuple[PreparedArtifact, ...]]:
        if self._image_candidate_preparer is None:
            raise _state_invalid(
                "Image candidate preparation requires an injected local deterministic preparer."
            )
        prepared = self._image_candidate_preparer(
            base_project,
            request,
            authorization,
            result,
            measured,
            receipt,
        )
        if not isinstance(prepared, PreparedImageCandidate):
            raise _state_invalid(
                "Image candidate preparer returned an unsafe capability."
            )
        accepted = validate_image_activation_candidate(
            base_project=base_project,
            base_inputs=prepared.base_inputs,
            base_dependency_states=base_project.manifest.dependency_states,
            request=request,
            authorization=authorization,
            result=result,
            measured=measured,
            receipt=receipt,
            candidate_project=prepared.candidate_project,
            candidate_registry=prepared.candidate_registry,
            candidate_graph=prepared.candidate_graph,
            candidate_inputs=prepared.candidate_inputs,
            resolution=prepared.resolution,
            candidate_project_pointer=prepared.candidate_project_pointer,
            candidate_registry_pointer=prepared.candidate_registry_pointer,
            candidate_graph_pointer=prepared.candidate_graph_pointer,
            candidate_project_bytes=prepared.candidate_project_bytes,
            candidate_registry_bytes=prepared.candidate_registry_bytes,
            candidate_graph_bytes=prepared.candidate_graph_bytes,
        )
        artifacts = (
            self.prepare_artifact(
                request.attempt_id,
                accepted.candidate_shot_path,
                accepted.candidate_shot_bytes,
            ),
            self.prepare_artifact(
                request.attempt_id,
                accepted.candidate_project_pointer.path,
                accepted.candidate_project_bytes,
            ),
            self.prepare_artifact(
                request.attempt_id,
                accepted.candidate_registry_pointer.path,
                accepted.candidate_registry_bytes,
            ),
            self.prepare_artifact(
                request.attempt_id,
                accepted.candidate_graph_pointer.path,
                accepted.candidate_graph_bytes,
            ),
        )
        return accepted, artifacts

    def _persist_image_candidate_artifacts(
        self,
        request: ImageGenerationRequest,
        artifacts: tuple[PreparedArtifact, ...],
    ) -> tuple[PreparedArtifact, ...]:
        reopened = []
        for artifact in artifacts:
            self._write_immutable_artifact(
                artifact,
                attempt_id=request.attempt_id,
                dependency_graph=artifact.relative_path.name.startswith(
                    "dependency_graph."
                ),
            )
            reopened.append(self._reopen_exact_image_artifact(artifact))
        return tuple(reopened)

    def _reopen_image_request_artifact(
        self, request: ImageGenerationRequest
    ) -> PreparedArtifact:
        expected = self.prepare_artifact(
            request.attempt_id,
            canonical_image_request_path(request.request_fingerprint),
            _canonical_json_bytes(request),
        )
        return self._reopen_exact_image_artifact(expected)
