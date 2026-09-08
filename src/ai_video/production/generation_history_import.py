"""Immutable import preparation for a completed remote generation attempt.

The import is deliberately only a reader/preparer.  It never mutates either
project, submits a Provider task, or treats retrospective review as original
submit authorization.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource,
    validate_generation_evaluation_sources,
)
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ActorIdentity, QaPolicy, StateCommitStatus
from ai_video.production.paths import _read_regular_file_nofollow, resolve_contained_path
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoTaskObservation,
    VideoTaskState,
)
from ai_video.production.paid_provider import (
    PaidProviderSubmitOutcome,
    PaidProviderSubmitReceipt,
)


_SHA256 = r"^[0-9a-f]{64}$"


class ImportedGenerationSourceDocument(StrictModel):
    """Verbatim observation provenance, retained without an automated truth claim."""

    kind: Literal["historical", "retrospective"]
    relative_path: Path
    sha256: str = Field(pattern=_SHA256)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_bytes(self) -> "ImportedGenerationSourceDocument":
        if self.relative_path.is_absolute() or ".." in self.relative_path.parts:
            raise ValueError("imported source document path must be relative and contained")
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.sha256:
            raise ValueError("imported source document hash does not match its UTF-8 text")
        return self


class ImportedGenerationEvaluationSourceAttribution(StrictModel):
    """Connect an evaluator record to independently retained raw observations."""

    evaluation_source_sha256: str = Field(pattern=_SHA256)
    document_sha256s: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_documents(self) -> "ImportedGenerationEvaluationSourceAttribution":
        if len(set(self.document_sha256s)) != len(self.document_sha256s):
            raise ValueError("evaluation source attribution repeats a document")
        return self


class ImportedGenerationExperienceReceipt(StrictModel):
    """A sealed retrospective snapshot, never a source attempt lifecycle record."""

    schema_version: Literal["imported-generation-experience/1"] = (
        "imported-generation-experience/1"
    )
    import_id: str = Field(min_length=1)
    actor: ActorIdentity
    source_manifest_json: str = Field(min_length=1)
    source_manifest_sha256: str = Field(pattern=_SHA256)
    source_attempt_id: str = Field(min_length=1)
    source_request_json: str = Field(min_length=1)
    source_submit_json: str = Field(min_length=1)
    source_status_json: str = Field(min_length=1)
    source_fetch_json: str = Field(min_length=1)
    experience: GenerationExperience
    # This is the policy selected when retrospective evidence was imported.
    # It makes no claim about the policy active at the source submit.
    evaluation_policy: QaPolicy
    source_documents: tuple[ImportedGenerationSourceDocument, ...] = Field(min_length=1)
    evaluation_source_attributions: tuple[
        ImportedGenerationEvaluationSourceAttribution, ...
    ] = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @property
    def source_manifest(self):
        from ai_video.production.models import ProductionManifest

        return ProductionManifest.model_validate_json(self.source_manifest_json)

    @property
    def source_request(self) -> ResolvedVideoGenerationRequest:
        return ResolvedVideoGenerationRequest.model_validate_json(self.source_request_json)

    @property
    def source_fetch(self) -> VideoFetchReceipt:
        return VideoFetchReceipt.model_validate_json(self.source_fetch_json)

    @property
    def source_submit(self) -> PaidProviderSubmitReceipt:
        return PaidProviderSubmitReceipt.model_validate_json(self.source_submit_json)

    @property
    def source_status(self) -> VideoTaskObservation:
        return VideoTaskObservation.model_validate_json(self.source_status_json)

    @model_validator(mode="after")
    def _validate_snapshot(self) -> "ImportedGenerationExperienceReceipt":
        from ai_video.production.generation_decision import GenerationCandidate
        from ai_video.production.generation_experience import bind_experience_models

        bind_experience_models(GenerationCandidate)
        manifest = self.source_manifest
        request = self.source_request
        submit = self.source_submit
        status = self.source_status
        fetch = self.source_fetch
        if hashlib.sha256(self.source_manifest_json.encode("utf-8")).hexdigest() != self.source_manifest_sha256:
            raise ValueError("imported source manifest hash does not match its exact raw bytes")
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == self.source_attempt_id),
            None,
        )
        if attempt is None or attempt.operation != "video_generation":
            raise ValueError("imported source attempt is not a video generation attempt")
        state = attempt.video_generation_state
        if sum(item.video_generation_state is not None for item in manifest.attempts) != 1:
            raise ValueError("multi-attempt source history cannot be selectively imported")
        if state is None or state.fetch_receipt is None:
            raise ValueError("imported source has no fetched remote video evidence")
        if state.latest_observation is None or state.paid_submit_receipt is None:
            raise ValueError("imported source has no completed remote submit and observation")
        if state.local_fetch_receipt is not None:
            raise ValueError("imported source must use the remote video lane")
        if state.execution_binding is not None or state.qualification_binding is not None:
            raise ValueError("decision- or qualification-bound source cannot be imported")
        if manifest.imported_generation_experiences:
            raise ValueError("an imported source history cannot be imported again")
        if attempt.status not in {StateCommitStatus.RUNNING, StateCommitStatus.SUCCEEDED}:
            raise ValueError("interrupted, failed, or unknown source attempt cannot be imported")
        if state.phase.value not in {"validate", "candidate", "activate"}:
            raise ValueError("imported source must already have fetched media")
        if (
            state.request.request_input_hash != request.request_input_hash
            or state.request.file_sha256
            != hashlib.sha256(self.source_request_json.encode("utf-8")).hexdigest()
            or state.paid_submit_receipt.file_sha256
            != hashlib.sha256(self.source_submit_json.encode("utf-8")).hexdigest()
            or state.latest_observation.file_sha256
            != hashlib.sha256(self.source_status_json.encode("utf-8")).hexdigest()
            or state.fetch_receipt.file_sha256
            != hashlib.sha256(self.source_fetch_json.encode("utf-8")).hexdigest()
            or state.paid_submit_receipt.submit_receipt_fingerprint
            != submit.submit_receipt_fingerprint
            or state.latest_observation.observation_fingerprint
            != status.observation_fingerprint
            or state.latest_observation.request_receipt_fingerprint
            != request.desired_generation_fingerprint
            or state.latest_observation.paid_submit_receipt_fingerprint
            != submit.submit_receipt_fingerprint
            or state.fetch_receipt.fetch_fingerprint != fetch.fetch_fingerprint
            or state.fetch_receipt.artifact_sha256 != fetch.artifact_sha256
            or state.fetch_receipt.artifact_size_bytes != fetch.size_bytes
            or submit.attempt_id != self.source_attempt_id
            or submit.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or submit.request_fingerprint != request.desired_generation_fingerprint
            or status.state is not VideoTaskState.SUCCEEDED
            or status.submission_fingerprint != fetch.submission_fingerprint
            or status.observation_fingerprint != fetch.observation_fingerprint
            or status.paid_submit_receipt_fingerprint
            != fetch.paid_submit_receipt_fingerprint
        ):
            raise ValueError("imported source remote evidence identity is invalid")

        if self.evaluation_policy.content_hash != canonical_sha256(self.evaluation_policy):
            raise ValueError("retrospective evaluation policy content hash is invalid")
        self._validate_experience(request, fetch)
        if self.experience.candidate.final_output_goal is not None:
            raise ValueError("unbound historical source cannot attest a generation-time final-output goal")
        if (
            self.experience.candidate.recipe.comparison is not None
            or any(
                evidence.intervention_id is not None
                or evidence.intervention_semantic_hash is not None
                or evidence.actual_delta
                for evidence in self.experience.evidence
            )
        ):
            raise ValueError("unbound historical source cannot claim a controlled intervention")
        documents = {item.sha256: item for item in self.source_documents}
        if len(documents) != len(self.source_documents):
            raise ValueError("imported source documents must have unique hashes")
        if any(source.analysis_evidence is not None for source in self.experience.evaluation_sources):
            raise ValueError("new analysis bridge evidence cannot be retroactively imported")
        sources = {
            source.source_sha256: source
            for source in self.experience.evaluation_sources
        }
        attributions = {
            item.evaluation_source_sha256: item.document_sha256s
            for item in self.evaluation_source_attributions
        }
        if len(attributions) != len(self.evaluation_source_attributions) or set(attributions) != set(sources):
            raise ValueError("every imported evaluation source needs one raw-observation attribution")
        for source_hash, source in sources.items():
            attributed = attributions[source_hash]
            if not set(attributed) <= set(documents):
                raise ValueError("evaluation source attribution names an absent document")
            if all(
                _is_evaluator_source_json(documents[item].text, source)
                for item in attributed
            ):
                raise ValueError("evaluator JSON cannot be its own sole raw-observation proof")
        try:
            for evidence in self.experience.evidence:
                validate_generation_evaluation_sources(
                    sources=self.experience.evaluation_sources,
                    evidence=evidence,
                    qa_policy=self.evaluation_policy,
                )
        except (AttributeError, ValueError) as exc:
            raise ValueError("imported generation evaluation sources are invalid") from exc
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("imported generation experience receipt content hash is invalid")
        return self

    def _validate_experience(
        self, request: ResolvedVideoGenerationRequest, fetch: VideoFetchReceipt
    ) -> None:
        candidate = self.experience.candidate
        projection = self.experience.projection
        try:
            variant = next(
                item
                for item in candidate.capabilities.variants
                if item.capability_id == candidate.capability_id
            )
        except StopIteration as exc:
            raise ValueError("imported candidate names no source capability") from exc
        sealed = request.activation_scope.request if request.activation_scope else None
        if (
            candidate.capabilities.provider_name != request.provider_name
            or variant.model_id != request.model_id
            or variant.provider_kind != request.provider_kind
            or variant.mode != request.mode
            or variant.execution_kind.value != request.execution_kind.value
            or candidate.provider_profile != request.provider_profile
            or candidate.output_requirement != request.effective_output
            or candidate.recipe.profile_sha256 != request.provider_profile.profile_sha256
            or candidate.recipe.compiler_hash != request.adapter_compiler_hash
            or candidate.recipe.requirement_hash != projection.requirement.requirement_hash
            or request.requirement_hash != projection.requirement.requirement_hash
            or sealed is None
            or sealed.target_shot_id != projection.target_shot_id
            or sealed.target_shot_revision != projection.target_shot_revision
            or sealed.target_shot_content_hash != projection.target_shot_content_hash
            or request.effective_seed != candidate.recipe.seed.value
        ):
            raise ValueError("imported experience does not match exact source request")
        facts_hash = canonical_sha256(
            projection.requirement.model_dump(
                mode="json", exclude={"requirement_id", "requirement_hash"}
            )
        )
        if any(
            evidence.attempt_id != self.source_attempt_id
            or evidence.request_hash != request.request_input_hash
            or evidence.artifact_sha256 != fetch.artifact_sha256
            or evidence.outcome != "media"
            or evidence.shot_id != projection.target_shot_id
            or evidence.recipe_scope_hash != candidate.scope_hash
            or evidence.facts_hash != facts_hash
            or evidence.rubric_hash != candidate.recipe.rubric_hash
            for evidence in self.experience.evidence
        ):
            raise ValueError("imported experience evidence does not match exact source media")

    @classmethod
    def create(cls, **values: object) -> "ImportedGenerationExperienceReceipt":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(candidate.model_dump(mode="json"))
        return cls.model_validate(data)


def _read_source_json(root: Path, relative: Path) -> tuple[str, str]:
    path = resolve_contained_path(root, relative, allowed_root=root / "state")
    raw = _read_regular_file_nofollow(path, contained_by=root / "state")
    return raw.data.decode("utf-8"), raw.file_sha256


def _is_evaluator_source_json(text: str, source: GenerationEvaluationSource) -> bool:
    """Formatting does not turn an evaluator document into independent proof."""

    try:
        return GenerationEvaluationSource.model_validate_json(text) == source
    except ValueError:
        return False


def _verify_source_documents(
    evidence_root: Path, documents: tuple[ImportedGenerationSourceDocument, ...]
) -> tuple[ImportedGenerationSourceDocument, ...]:
    """Reopen all raw observations before sealing their retained text bytes."""

    verified = []
    for document in documents:
        try:
            path = resolve_contained_path(
                evidence_root, document.relative_path, allowed_root=evidence_root
            )
            raw = _read_regular_file_nofollow(path, contained_by=evidence_root)
            text = raw.data.decode("utf-8")
        except (OSError, RuntimeError, UnicodeDecodeError, ValueError) as exc:
            raise ValueError("could not reopen imported source document") from exc
        if raw.file_sha256 != document.sha256 or text != document.text:
            raise ValueError("imported source document differs from its exact retained file")
        verified.append(document)
    return tuple(verified)


def prepare_generation_history_import(
    source_root: str | Path,
    *,
    expected_source_manifest_sha256: str,
    import_id: str,
    source_attempt_id: str,
    experience: GenerationExperience,
    evaluation_policy: QaPolicy,
    source_documents: tuple[ImportedGenerationSourceDocument, ...],
    evaluation_source_attributions: tuple[ImportedGenerationEvaluationSourceAttribution, ...],
    evidence_root: str | Path,
    actor: ActorIdentity,
) -> tuple[ImportedGenerationExperienceReceipt, bytes]:
    """Read one exact completed remote source attempt into immutable import bytes."""

    root = Path(source_root).resolve(strict=True)
    evidence = Path(evidence_root).resolve(strict=True)
    source_documents = _verify_source_documents(evidence, tuple(source_documents))
    manifest_json, manifest_sha256 = _read_source_json(root, Path("state/manifest.json"))
    if manifest_sha256 != expected_source_manifest_sha256:
        raise ValueError("source manifest no longer matches the expected exact raw snapshot")
    from ai_video.production.project import load_production_project
    from ai_video.production._paid_provider_project_reader import load_paid_provider_submit_receipt
    from ai_video.production._video_project_reader import (
        load_video_fetch_receipt,
        load_video_request_receipt,
        load_video_status_receipt,
    )

    loaded = load_production_project(root / "project.yaml")
    attempt = next(
        (item for item in loaded.manifest.attempts if item.attempt_id == source_attempt_id),
        None,
    )
    if attempt is None or attempt.video_generation_state is None:
        raise ValueError("source attempt does not contain video generation state")
    state = attempt.video_generation_state
    if state.fetch_receipt is None or state.latest_observation is None or state.paid_submit_receipt is None:
        raise ValueError("source attempt has no completed remote fetched video")
    request = load_video_request_receipt(root, state.request)
    fetch = load_video_fetch_receipt(root, state.fetch_receipt)
    observation = load_video_status_receipt(root, state.latest_observation)
    submit = load_paid_provider_submit_receipt(root, state.paid_submit_receipt)
    if (
        observation.state is not VideoTaskState.SUCCEEDED
        or fetch.observation_fingerprint != observation.observation_fingerprint
        or fetch.submission_fingerprint != observation.submission_fingerprint
        or fetch.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
        or submit.request_fingerprint != request.desired_generation_fingerprint
    ):
        raise ValueError("source remote submit, observation, fetch, and request do not form one result")
    request_json, request_sha256 = _read_source_json(root, state.request.path)
    submit_json, submit_sha256 = _read_source_json(root, state.paid_submit_receipt.path)
    status_json, status_sha256 = _read_source_json(root, state.latest_observation.path)
    fetch_json, fetch_sha256 = _read_source_json(root, state.fetch_receipt.path)
    artifact_path = resolve_contained_path(
        root,
        state.fetch_receipt.artifact_path,
        allowed_root=root / "state" / "video-generation" / "fetch",
    )
    media = _read_regular_file_nofollow(
        artifact_path, contained_by=root / "state" / "video-generation" / "fetch"
    )
    if (
        request_sha256 != state.request.file_sha256
        or submit_sha256 != state.paid_submit_receipt.file_sha256
        or status_sha256 != state.latest_observation.file_sha256
        or fetch_sha256 != state.fetch_receipt.file_sha256
        or media.file_sha256 != fetch.artifact_sha256
        or media.size_bytes != fetch.size_bytes
    ):
        raise ValueError("source request, fetch, or media bytes changed during import")
    receipt = ImportedGenerationExperienceReceipt.create(
        import_id=import_id,
        actor=actor,
        source_manifest_json=manifest_json,
        source_manifest_sha256=manifest_sha256,
        source_attempt_id=source_attempt_id,
        source_request_json=request_json,
        source_submit_json=submit_json,
        source_status_json=status_json,
        source_fetch_json=fetch_json,
        experience=experience,
        evaluation_policy=evaluation_policy,
        source_documents=source_documents,
        evaluation_source_attributions=evaluation_source_attributions,
    )
    final_manifest_json, final_manifest_sha256 = _read_source_json(root, Path("state/manifest.json"))
    if final_manifest_sha256 != expected_source_manifest_sha256 or final_manifest_json != manifest_json:
        raise ValueError("source manifest changed while history import was prepared")
    return receipt, media.data


def load_imported_generation_experience(root: str | Path, pointer):
    """Reopen one copied receipt and its exact copied MP4 without source access."""

    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production._lifecycle_schema import (
        ImportedGenerationExperienceReceiptPointer,
    )

    try:
        pointer = ImportedGenerationExperienceReceiptPointer.model_validate(
            pointer.model_dump(mode="python")
        )
        resolved_root = Path(root).resolve(strict=True)
        expected_path = Path(
            f"state/video-generation/imported-experiences/{pointer.content_hash}.json"
        )
        if pointer.path != expected_path:
            raise ValueError("imported generation experience pointer path is not canonical")
        path = resolve_contained_path(
            resolved_root, pointer.path, allowed_root=resolved_root / "state"
        )
        raw = _read_regular_file_nofollow(path, contained_by=resolved_root / "state")
        receipt = ImportedGenerationExperienceReceipt.model_validate_json(raw.data)
        media_path = resolve_contained_path(
            resolved_root,
            Path(
                "state/video-generation/imported-media/"
                f"{receipt.source_fetch.artifact_sha256}.mp4"
            ),
            allowed_root=resolved_root / "state" / "video-generation" / "imported-media",
        )
        media = _read_regular_file_nofollow(
            media_path,
            contained_by=resolved_root / "state" / "video-generation" / "imported-media",
        )
        if (
            raw.file_sha256 != pointer.file_sha256
            or receipt.content_hash != pointer.content_hash
            or receipt.source_request.request_input_hash != pointer.request_fingerprint
            or any(
                evidence.request_hash != pointer.request_fingerprint
                for evidence in receipt.experience.evidence
            )
            or media.file_sha256 != receipt.source_fetch.artifact_sha256
            or media.size_bytes != receipt.source_fetch.size_bytes
        ):
            raise ValueError("imported generation experience pointer or copied media is invalid")
    except (AiVideoError, OSError, RuntimeError, UnicodeDecodeError, ValueError) as exc:
        if isinstance(exc, AiVideoError):
            raise
        raise AiVideoError(
            code=ErrorCode.PRODUCTION_PROJECT_INVALID,
            user_message="Could not reopen imported generation experience.",
            technical_detail=str(exc),
            retryable=False,
        ) from exc
    return receipt
