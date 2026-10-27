"""Immutable closure evidence for an explicitly requested authored visual revision."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field, model_serializer, model_validator

from ai_video.production.artifact_contracts import QaPolicyPointer, StrictModel
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import canonical_sha256
from ai_video.production.generation_coverage_revision import CoverageRevisionTarget
from ai_video.production.generation_resolution_revision import ResolutionRevisionTarget
from ai_video.production.generation_authoring_revision import (
    AuthoredGenerationRevisionTarget,
    validate_authored_generation_revision_target,
)
from ai_video.production.generation_authored_retarget import (
    AuthoredGenerationRetargetTarget,
    validate_authored_generation_retarget_target,
)
from ai_video.production.models import (
    ActorIdentity,
    GenerationExecutionBindingPointer,
    PaidProviderSubmitReceiptPointer,
    ProjectSnapshotPointer,
    VideoFetchReceiptPointer,
    VideoRequestReceiptPointer,
    VideoAttemptPhase,
    StateCommitStatus,
    PaidProviderAttemptPhase,
)
from ai_video.production._lifecycle_schema import GenerationVisualSupersessionReceiptPointer


_SHA256 = r"^[0-9a-f]{64}$"


def validate_visual_revision_goal(old: FinalOutputContract, new: FinalOutputContract) -> None:
    """Require a new version of the same goal that preserves every old requirement."""
    old = FinalOutputContract.model_validate_json(old.model_dump_json())
    new = FinalOutputContract.model_validate_json(new.model_dump_json())
    old_requirements = {item.requirement_id: item for item in old.requirements}
    new_requirements = {item.requirement_id: item for item in new.requirements}
    if old.goal_id != new.goal_id or old.goal_version == new.goal_version:
        raise ValueError("visual revision must advance the same final-output goal")
    if any(new_requirements.get(key) != value for key, value in old_requirements.items()):
        raise ValueError("visual revision cannot remove or weaken an existing requirement")


class GenerationVisualSupersessionReceipt(StrictModel):
    """Record one explicit creative replacement while retaining the earlier media."""

    schema_version: Literal[
        "generation-visual-supersession/1",
        "generation-visual-supersession/2",
        "generation-visual-supersession/3",
        "generation-visual-supersession/4",
        "generation-visual-supersession/5",
    ] = "generation-visual-supersession/1"
    attempt_id: str = Field(min_length=1)
    actor: ActorIdentity
    authorization_receipt_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    request_fingerprint: str = Field(pattern=_SHA256)
    fetch_receipt: VideoFetchReceiptPointer
    paid_submit_receipt: PaidProviderSubmitReceiptPointer
    artifact_sha256: str = Field(pattern=_SHA256)
    artifact_size_bytes: int = Field(strict=True, gt=0)
    execution_binding: GenerationExecutionBindingPointer
    experience_content_hash: str = Field(pattern=_SHA256)
    evidence_hash: str = Field(pattern=_SHA256)
    qa_policy: QaPolicyPointer
    base_project: ProjectSnapshotPointer
    task_id: str = Field(min_length=1)
    shot_id: str = Field(min_length=1)
    old_goal: FinalOutputContract
    target_goal: FinalOutputContract
    old_first_frame_sha256: str | None = Field(default=None, pattern=_SHA256)
    target_first_frame_sha256: str | None = Field(default=None, pattern=_SHA256)
    expected_manifest_revision: int = Field(strict=True, ge=0)
    coverage_revision: CoverageRevisionTarget | None = None
    resolution_revision: ResolutionRevisionTarget | None = None
    authored_revision: AuthoredGenerationRevisionTarget | None = None
    authored_retarget: AuthoredGenerationRetargetTarget | None = None
    previous_supersession: GenerationVisualSupersessionReceiptPointer | None = None
    content_hash: str = Field(pattern=_SHA256)

    @model_serializer(mode="wrap")
    def _legacy_payload(self, handler):
        data = handler(self)
        if self.coverage_revision is None:
            data.pop("coverage_revision", None)
        if self.resolution_revision is None:
            data.pop("resolution_revision", None)
        if self.authored_revision is None:
            data.pop("authored_revision", None)
        if self.authored_retarget is None:
            data.pop("authored_retarget", None)
        if self.schema_version == "generation-visual-supersession/5" and self.target_first_frame_sha256 is None:
            data.pop("target_first_frame_sha256", None)
        if self.previous_supersession is None:
            data.pop("previous_supersession", None)
        return data

    @model_validator(mode="after")
    def _validate_seal(self):
        if self.schema_version == "generation-visual-supersession/4":
            from ai_video.production.generation_authoring_revision import validate_authored_revision_goal

            if self.authored_revision is None:
                raise ValueError("authored supersession must bind one exact typed target")
            validate_authored_revision_goal(
                self.old_goal,
                self.target_goal,
                goal_requirement_revisions=self.authored_revision.goal_requirement_revisions,
                authorization_receipt_id=self.authorization_receipt_id,
            )
        elif self.schema_version == "generation-visual-supersession/5":
            from ai_video.production.generation_authored_retarget import _same_goal_with_new_version

            if (
                self.authored_retarget is None
                or self.authored_retarget.task_id != self.task_id
                or self.authored_retarget.shot_id != self.shot_id
                or self.authored_retarget.authorization_reference != self.authorization_receipt_id
                or not _same_goal_with_new_version(self.old_goal, self.target_goal)
            ):
                raise ValueError("retarget supersession must preserve all old goal fields and advance its version")
        else:
            validate_visual_revision_goal(self.old_goal, self.target_goal)
        if self.schema_version == "generation-visual-supersession/1":
            if (self.coverage_revision is not None or self.resolution_revision is not None
                    or self.authored_revision is not None
                    or self.authored_retarget is not None
                    or self.old_first_frame_sha256 is None
                    or self.old_first_frame_sha256 == self.target_first_frame_sha256):
                raise ValueError("visual supersession must select a different first-frame image")
        elif self.schema_version == "generation-visual-supersession/2":
            if (self.coverage_revision is None or self.resolution_revision is not None
                    or self.authored_revision is not None
                    or self.authored_retarget is not None
                    or self.old_first_frame_sha256 is None
                    or self.old_first_frame_sha256 != self.target_first_frame_sha256):
                raise ValueError("coverage supersession must retain its first frame and exact authored target")
        elif self.schema_version == "generation-visual-supersession/3":
            if (self.resolution_revision is None or self.coverage_revision is not None
                    or self.authored_revision is not None
                    or self.authored_retarget is not None
                    or self.old_first_frame_sha256 is None
                    or self.old_first_frame_sha256 != self.target_first_frame_sha256):
                raise ValueError("resolution supersession must retain its first frame and exact output target")
        elif self.schema_version == "generation-visual-supersession/4":
            if (self.authored_revision is None or self.authored_retarget is not None
                    or self.coverage_revision is not None or self.resolution_revision is not None
                    or self.target_first_frame_sha256 != self.authored_revision.first_frame_sha256):
                raise ValueError("authored supersession must bind one exact typed target and first frame")
        elif self.schema_version == "generation-visual-supersession/5":
            if (self.authored_retarget is None or self.authored_revision is not None
                    or self.coverage_revision is not None or self.resolution_revision is not None
                    or self.target_first_frame_sha256 is not None):
                raise ValueError("retarget supersession must bind one exact multimodal target without a first frame")
        else:
            if (self.authored_revision is not None or self.authored_retarget is not None
                    or self.coverage_revision is not None or self.resolution_revision is not None):
                raise ValueError("legacy visual supersession cannot contain authored targets")
        if self.coverage_revision is not None:
            self.coverage_revision.verify()
        if self.resolution_revision is not None:
            self.resolution_revision.verify()
        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("visual supersession receipt content hash is invalid")
        return self

    @classmethod
    def create(cls, **values):
        data = dict(values)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(provisional.model_dump(mode="json"))
        return cls.model_validate(data)


def load_generation_visual_supersession(root, pointer):
    """Reopen canonical receipt bytes and verify every immutable pointer field."""
    from pydantic import ValidationError

    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production._generation_feedback_reader import _root_and_path
    from ai_video.production.paths import _read_regular_file_nofollow

    resolved_root, resolved = _root_and_path(root, pointer.path)
    try:
        raw = _read_regular_file_nofollow(resolved, contained_by=resolved_root / "state")
        receipt = GenerationVisualSupersessionReceipt.model_validate_json(raw.data)
    except (OSError, ValidationError, ValueError, AiVideoError) as exc:
        raise AiVideoError(
            code=ErrorCode.PRODUCTION_PROJECT_INVALID,
            user_message="Could not reopen the visual supersession receipt.",
            technical_detail=str(exc),
            retryable=False,
        ) from exc
    if (
        raw.file_sha256 != pointer.file_sha256
        or receipt.content_hash != pointer.content_hash
        or receipt.attempt_id != pointer.attempt_id
        or receipt.request_fingerprint != pointer.request_fingerprint
        or receipt.artifact_sha256 != pointer.artifact_sha256
        or receipt.experience_content_hash != pointer.experience_content_hash
    ):
        raise AiVideoError(
            code=ErrorCode.PRODUCTION_PROJECT_INVALID,
            user_message="Visual supersession receipt pointer differs from its retained bytes.",
            retryable=False,
        )
    if receipt.previous_supersession is not None:
        try:
            prior_path = _root_and_path(root, receipt.previous_supersession.path)[1]
            prior_raw = _read_regular_file_nofollow(prior_path, contained_by=resolved_root / "state")
            prior = GenerationVisualSupersessionReceipt.model_validate_json(prior_raw.data)
            if prior.previous_supersession is not None:
                raise ValueError("Timing correction cannot form an unbounded amendment chain")
            prior = load_generation_visual_supersession(root, receipt.previous_supersession)
            if receipt.authored_retarget is not None:
                from .unsubmitted_retarget_references import validate_reference_correction
                validate_reference_correction(root, prior, receipt)
            else:
                validate_authored_timing_correction(prior, receipt)
        except (OSError, TypeError, ValueError, AiVideoError) as exc:
            raise AiVideoError(code=ErrorCode.PRODUCTION_PROJECT_INVALID,
                user_message="Could not reopen the exact timing correction lineage.",
                technical_detail=str(exc), retryable=False) from exc
    return receipt


def supersede_video_generation(
    committer,
    *,
    attempt_id: str,
    expected_manifest_revision: int,
    experience_content_hash: str,
    actor: ActorIdentity,
    authorization_receipt_id: str,
    reason: str,
    target_goal: FinalOutputContract,
    target_first_frame_sha256: str | None,
    coverage_revision: CoverageRevisionTarget | None = None,
    resolution_revision: ResolutionRevisionTarget | None = None,
    authored_revision: AuthoredGenerationRevisionTarget | None = None,
    authored_retarget: AuthoredGenerationRetargetTarget | None = None,
):
    """Close one fetched attempt after explicit creative replacement authorization."""
    import re

    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production._lifecycle_schema import GenerationVisualSupersessionReceiptPointer
    from ai_video.production._state_commit_common import (
        _canonical_json_bytes,
        _state_invalid,
        _timestamp,
        _validated_transition,
    )
    from ai_video.production._generation_feedback_reader import (
        load_generation_experience,
        load_generation_visual_supersession as reopen_supersession,
    )
    from ai_video.production._video_project_reader import load_video_fetch_receipt
    from ai_video.production.models import StateCommitStatus
    from ai_video.production.project import load_production_project

    if not isinstance(actor, ActorIdentity):
        raise _state_invalid("Visual supersession requires an exact actor identity.")
    if not isinstance(authorization_receipt_id, str) or not authorization_receipt_id.strip():
        raise _state_invalid("Visual supersession requires the user's authorization receipt ID.")
    if not isinstance(reason, str) or not reason.strip():
        raise _state_invalid("Visual supersession requires a clear creative revision reason.")
    reason = reason.strip()
    if not isinstance(target_goal, FinalOutputContract):
        raise _state_invalid("Visual supersession target goal must be the typed final-output contract.")
    try:
        target_goal = FinalOutputContract.model_validate_json(target_goal.model_dump_json())
    except ValueError as exc:
        raise _state_invalid("Visual supersession target goal is invalid.", str(exc)) from exc
    if authored_retarget is None:
        if not isinstance(target_first_frame_sha256, str) or re.fullmatch(_SHA256, target_first_frame_sha256) is None:
            raise _state_invalid("Visual supersession target first-frame identity is invalid.")
    elif target_first_frame_sha256 is not None:
        raise _state_invalid("Multimodal retarget cannot claim a single target first-frame identity.")
    if coverage_revision is not None:
        try:
            if not isinstance(coverage_revision, CoverageRevisionTarget):
                raise ValueError("coverage revision must be typed")
            coverage_revision = coverage_revision.verify()
        except (AttributeError, TypeError, ValueError) as exc:
            raise _state_invalid("Coverage supersession target is not sealed.", str(exc)) from exc
    if resolution_revision is not None:
        try:
            if coverage_revision is not None or not isinstance(resolution_revision, ResolutionRevisionTarget):
                raise ValueError("resolution revision must be typed and cannot also revise coverage")
            resolution_revision = resolution_revision.verify()
        except (AttributeError, TypeError, ValueError) as exc:
            raise _state_invalid("Resolution supersession target is not sealed.", str(exc)) from exc
    if authored_revision is not None:
        try:
            if (not isinstance(authored_revision, AuthoredGenerationRevisionTarget)
                    or coverage_revision is not None or resolution_revision is not None):
                raise ValueError("authored generation revision is mutually exclusive with narrower revisions")
            authored_revision = authored_revision.verify()
            if target_first_frame_sha256 != authored_revision.first_frame_sha256:
                raise ValueError("target frame differs from the sealed authored revision")
        except (AttributeError, TypeError, ValueError) as exc:
            raise _state_invalid("Authored supersession target is not sealed.", str(exc)) from exc
    if authored_retarget is not None:
        try:
            if (not isinstance(authored_retarget, AuthoredGenerationRetargetTarget)
                    or coverage_revision is not None or resolution_revision is not None
                    or authored_revision is not None):
                raise ValueError("authored retarget is mutually exclusive with other supersession targets")
            authored_retarget = authored_retarget.verify()
            if authored_retarget.authorization_reference != authorization_receipt_id:
                raise ValueError("retarget authority differs from the exact authorization receipt")
        except (AttributeError, TypeError, ValueError) as exc:
            raise _state_invalid("Authored retarget supersession target is not sealed.", str(exc)) from exc

    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None:
            raise _state_invalid("Visual supersession requires a video-generation attempt.")

        # Exact replay is idempotent even though the Manifest revision advanced.
        if state.visual_supersession is not None:
            try:
                loaded = load_production_project(committer._project_root / "project.yaml")
                receipt = reopen_supersession(committer._project_root, state.visual_supersession)
                request = committer._reopen_video_request(state.request)
                old_frames = tuple(item for item in request.activation_scope.request.image_bindings
                                   if item.role == "first_frame")
                if len(old_frames) > 1:
                    raise ValueError("the prior request has more than one first-frame endpoint")
                old_frame = old_frames[0].asset_sha256 if old_frames else None
                if (
                    loaded.manifest != manifest
                    or expected_manifest_revision != receipt.expected_manifest_revision
                    or experience_content_hash != receipt.experience_content_hash
                    or actor != receipt.actor
                    or authorization_receipt_id != receipt.authorization_receipt_id
                    or reason != receipt.reason
                    or target_goal != receipt.target_goal
                    or target_first_frame_sha256 != receipt.target_first_frame_sha256
                    or old_frame != receipt.old_first_frame_sha256
                    or coverage_revision != receipt.coverage_revision
                    or resolution_revision != receipt.resolution_revision
                    or authored_revision != receipt.authored_revision
                    or authored_retarget != receipt.authored_retarget
                ):
                    raise _state_invalid("Visual supersession replay differs from its exact retained authorization.")
            except AiVideoError:
                raise
            except (AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
                raise _state_invalid("Visual supersession replay cannot reopen its exact prior evidence.", str(exc)) from exc
            return manifest

        if expected_manifest_revision != manifest.manifest_revision:
            raise _state_invalid("Visual supersession Manifest revision is stale.")
        if (
            attempt.operation != "video_generation"
            or attempt.status is not StateCommitStatus.RUNNING
            or state.phase is not VideoAttemptPhase.VALIDATE
            or state.execution_binding is None
            or state.fetch_receipt is None
            or state.local_fetch_receipt is not None
            or state.paid_submit_receipt is None
            or state.quality_rejection is not None
            or state.candidate_video_asset_ids
            or state.candidate_continuity_asset_ids
            or attempt.paid_provider_state is None
            or attempt.paid_provider_state.phase not in {
                PaidProviderAttemptPhase.ACCEPTED,
                PaidProviderAttemptPhase.SETTLED,
            }
            or attempt.paid_provider_state.submit_receipt != state.paid_submit_receipt
            or not state.generation_experiences
            or state.generation_experiences[-1].content_hash != experience_content_hash
        ):
            raise _state_invalid("Visual supersession requires one fetched paid VALIDATE result with durable experience.")
        if any(
            other.attempt_id != attempt_id
            and other.operation == "video_generation"
            and other.status in {
                StateCommitStatus.RUNNING,
                StateCommitStatus.OUTCOME_UNKNOWN,
                StateCommitStatus.INTERRUPTED,
            }
            for other in manifest.attempts
        ):
            raise _state_invalid("Visual supersession cannot proceed with another unresolved video attempt.")

        try:
            loaded = load_production_project(committer._project_root / "project.yaml")
            if loaded.manifest != manifest or loaded.qa_policy is None or loaded.manifest.active_qa_policy is None:
                raise ValueError("the old evaluation QA authority must be current and reopenable")
            request = committer._reopen_video_request(state.request)
            binding = committer._reopen_generation_execution_binding(state.execution_binding)
            binding.validate_request(request)
            fetch = load_video_fetch_receipt(committer._project_root, state.fetch_receipt)
            experience_pointer = state.generation_experiences[-1]
            experience = load_generation_experience(committer._project_root, experience_pointer)
            candidates = tuple(candidate for candidate in binding.inputs.candidates
                               if candidate.candidate_id == binding.decision.selected_candidate_id)
            if len(candidates) != 1 or candidates[0].final_output_goal is None:
                raise ValueError("the old binding must have one selected candidate with a complete goal")
            if experience.projection != binding.projection or experience.candidate != candidates[0]:
                raise ValueError("the retained experience must match the exact old execution inputs")
            old_goal = candidates[0].final_output_goal
            if authored_revision is None and authored_retarget is None:
                validate_visual_revision_goal(old_goal, target_goal)
            elif authored_revision is not None:
                from ai_video.production.generation_authoring_revision import validate_authored_revision_goal

                validate_authored_revision_goal(
                    old_goal,
                    target_goal,
                    goal_requirement_revisions=authored_revision.goal_requirement_revisions,
                    authorization_receipt_id=authorization_receipt_id,
                )
            if loaded.qa_policy.final_output != old_goal:
                raise ValueError("closure must retain the same old goal whose media was evaluated")
            activation = request.activation_scope
            if activation is None or activation.request.base_project != attempt.base_project:
                raise ValueError("the old request must retain its exact base Project pointer")
            first_frames = tuple(item for item in activation.request.image_bindings if item.role == "first_frame")
            if authored_revision is not None:
                if len(first_frames) > 1:
                    raise ValueError("the prior request has more than one first-frame endpoint")
                old_first_frame = first_frames[0].asset_sha256 if first_frames else None
                validate_authored_generation_revision_target(binding, experience, authored_revision)
            elif authored_retarget is not None:
                from ai_video.production.generation_authored_retarget import _same_goal_with_new_version

                if not _same_goal_with_new_version(old_goal, target_goal):
                    raise ValueError("retarget must preserve all existing goal requirements")
                old_first_frame = first_frames[0].asset_sha256 if len(first_frames) == 1 else None
                validate_authored_generation_retarget_target(binding, experience, authored_retarget)
            else:
                if len(first_frames) != 1:
                    raise ValueError("the old request must bind one exact first-frame image")
                old_first_frame = first_frames[0].asset_sha256
            if (authored_revision is None and authored_retarget is None
                    and coverage_revision is None and resolution_revision is None
                    and target_first_frame_sha256 == old_first_frame):
                raise ValueError("visual supersession requires a different authored first frame")
            if coverage_revision is not None:
                from ai_video.production.generation_coverage_revision import validate_coverage_target

                if target_first_frame_sha256 != old_first_frame:
                    raise ValueError("coverage supersession must preserve the original first frame")
                validate_coverage_target(binding, experience, coverage_revision)
            if resolution_revision is not None:
                from ai_video.production.generation_resolution_revision import validate_resolution_target

                if target_first_frame_sha256 != old_first_frame:
                    raise ValueError("resolution supersession must preserve the original first frame")
                validate_resolution_target(binding, experience, resolution_revision)
            if not experience.evidence:
                raise ValueError("visual supersession requires retained evidence in its latest experience")
            matching_evidence = tuple(
                item for item in experience.evidence
                if item.attempt_id == attempt_id
                and item.request_hash == request.request_input_hash
                and item.outcome == "media"
                and item.artifact_sha256 == fetch.artifact_sha256
                and item.task_id == binding.inputs.limits.task_id
                and item.shot_id == binding.context.target_shot_id
                and item.facts_hash == binding.inputs.facts_hash
                and item.recipe_scope_hash == candidates[0].scope_hash
                and item.rubric_hash == candidates[0].recipe.rubric_hash
            )
            if not matching_evidence:
                raise ValueError("latest experience has no exact evidence for the fetched attempt")
            from ai_video.production.generation_evaluation import validate_generation_evaluation_sources

            validate_generation_evaluation_sources(
                sources=experience.evaluation_sources,
                evidence=matching_evidence[-1],
                qa_policy=loaded.qa_policy,
                size_bytes=fetch.size_bytes,
                acceptance=candidates[0].recipe.acceptance_policy,
                requirement=experience.projection.requirement,
            )
        except (AiVideoError, OSError, AttributeError, KeyError, StopIteration, TypeError, ValueError) as exc:
            if isinstance(exc, AiVideoError) and exc.code is ErrorCode.PRODUCTION_PROJECT_INVALID:
                raise _state_invalid("Visual supersession evidence is not exact.", str(exc)) from exc
            raise _state_invalid("Visual supersession evidence is not exact.", str(exc)) from exc

        receipt = GenerationVisualSupersessionReceipt.create(
            schema_version=("generation-visual-supersession/5" if authored_retarget is not None
                            else "generation-visual-supersession/4" if authored_revision is not None
                            else "generation-visual-supersession/3" if resolution_revision is not None
                            else "generation-visual-supersession/2" if coverage_revision is not None
                            else "generation-visual-supersession/1"),
            coverage_revision=coverage_revision,
            resolution_revision=resolution_revision,
            authored_revision=authored_revision,
            authored_retarget=authored_retarget,
            attempt_id=attempt_id,
            actor=actor,
            authorization_receipt_id=authorization_receipt_id,
            reason=reason.strip(),
            request_fingerprint=request.request_input_hash,
            fetch_receipt=state.fetch_receipt,
            paid_submit_receipt=state.paid_submit_receipt,
            artifact_sha256=fetch.artifact_sha256,
            artifact_size_bytes=fetch.size_bytes,
            execution_binding=state.execution_binding,
            experience_content_hash=experience_pointer.content_hash,
            evidence_hash=matching_evidence[-1].evidence_hash,
            qa_policy=loaded.manifest.active_qa_policy,
            base_project=attempt.base_project,
            task_id=binding.inputs.limits.task_id,
            shot_id=binding.context.target_shot_id,
            old_goal=old_goal,
            target_goal=target_goal,
            old_first_frame_sha256=old_first_frame,
            target_first_frame_sha256=target_first_frame_sha256,
            expected_manifest_revision=manifest.manifest_revision,
        )
        payload = _canonical_json_bytes(receipt)
        file_hash = hashlib.sha256(payload).hexdigest()
        path = Path("state/video-generation/supersessions") / f"{receipt.content_hash}.json"
        from ai_video.production._state_commit_contracts import PreparedArtifact

        artifact = PreparedArtifact(path, payload, file_hash)
        pointer = GenerationVisualSupersessionReceiptPointer(
            path=path,
            content_hash=receipt.content_hash,
            attempt_id=attempt_id,
            request_fingerprint=receipt.request_fingerprint,
            artifact_sha256=receipt.artifact_sha256,
            experience_content_hash=receipt.experience_content_hash,
            file_sha256=file_hash,
        )
        committer._write_immutable_artifact(artifact, attempt_id=attempt_id)
        next_state = state.model_copy(update={"visual_supersession": pointer})
        next_attempt = _validated_transition(
            attempt,
            {
                "status": StateCommitStatus.FAILED,
                "finished_at": _timestamp(),
                "error_code": ErrorCode.VIDEO_VISUAL_SUPERSEDED.value,
                "error_message": "Prior fetched media was retained after an authorized authored visual revision.",
                "video_generation_state": next_state,
            },
        )
        next_manifest = _validated_transition(
            manifest,
            {
                "manifest_revision": manifest.manifest_revision + 1,
                "attempts": tuple(next_attempt if item.attempt_id == attempt_id else item
                                   for item in manifest.attempts),
            },
        )
        committer._write_manifest_atomic(next_manifest)
        reopen_supersession(committer._project_root, pointer)
        return committer._read_manifest()


def validate_authored_timing_correction(previous, corrected):
    """Only reconcile an unexecuted output clock to its unchanged authored intent."""
    if (previous.schema_version != 'generation-visual-supersession/4'
            or previous.previous_supersession is not None
            or corrected.schema_version != previous.schema_version
            or corrected.previous_supersession is None
            or corrected.previous_supersession.content_hash != previous.content_hash):
        raise ValueError('Timing correction requires one exact original authored supersession')
    ignored = {'content_hash', 'reason', 'expected_manifest_revision',
               'previous_supersession', 'authored_revision'}
    if (previous.model_dump(mode='json', exclude=ignored)
            != corrected.model_dump(mode='json', exclude=ignored)):
        raise ValueError('Timing correction cannot change source, goal, authority or accounting lineage')
    before, after = previous.authored_revision, corrected.authored_revision
    if before is None or after is None:
        raise ValueError('Timing correction requires exact authored targets')
    allowed = {'content_hash', 'output_requirement', 'provider_profile', 'capabilities_fingerprint'}
    if before.model_dump(mode='json', exclude=allowed) != after.model_dump(mode='json', exclude=allowed):
        raise ValueError('Timing correction cannot change intent, QA, first frame, model or project')
    old_output, new_output = before.output_requirement, after.output_requirement
    desired = before.intent.pacing.shot_duration_seconds
    if (desired is None or old_output.duration_seconds == desired
            or new_output.duration_seconds != desired
            or old_output.model_dump(exclude={'duration_seconds'})
            != new_output.model_dump(exclude={'duration_seconds'})):
        raise ValueError('Timing correction must resolve an actual duration mismatch to unchanged intent')


def correct_unsubmitted_authored_timing(committer, *, attempt_id, expected_manifest_revision,
                                       actor, authorization_receipt_id, corrected_target, reason):
    """Retain the bad sealed target and replace only its unsubmitted duration plan."""
    from ai_video.production.project import load_production_project
    from ai_video.production._state_commit_common import (
        _canonical_json_bytes, _state_invalid, _validated_transition,
    )
    from ai_video.production._state_commit_contracts import PreparedArtifact

    corrected_target = corrected_target.verify()
    if not isinstance(reason, str) or not reason.strip():
        raise _state_invalid('Timing correction requires a reason')
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        loaded = load_production_project(committer.project_root / 'project.yaml')
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (loaded.manifest != manifest or expected_manifest_revision != manifest.manifest_revision
                or state is None or state.visual_supersession is None
                or attempt.status is not StateCommitStatus.FAILED):
            raise _state_invalid('Timing correction requires the current closed source')
        previous = load_generation_visual_supersession(committer.project_root, state.visual_supersession)
        if (previous.actor != actor or previous.authorization_receipt_id != authorization_receipt_id
                or previous.authored_revision is None
                or manifest.active_project != previous.authored_revision.target_project
                or loaded.qa_policy is None
                or loaded.qa_policy.final_output != previous.target_goal
                or loaded.qa_policy.generation_acceptance != previous.authored_revision.acceptance):
            raise _state_invalid('Timing correction authority and active target must be exact')
        # Any later video request, including unsubmitted/unknown, requires its own recovery.
        index = next(i for i, a in enumerate(manifest.attempts) if a.attempt_id == attempt_id)
        if any(a.operation == 'video_generation' for a in manifest.attempts[index + 1:]):
            raise _state_invalid('Timing correction is forbidden after any successor video request')
        values = {name: getattr(previous, name) for name in type(previous).model_fields
                  if name != 'content_hash'}
        values.update(authored_revision=corrected_target, reason=reason.strip(),
                      expected_manifest_revision=manifest.manifest_revision,
                      previous_supersession=state.visual_supersession)
        corrected = GenerationVisualSupersessionReceipt.create(**values)
        validate_authored_timing_correction(previous, corrected)
        binding = committer._reopen_generation_execution_binding(state.execution_binding)
        experience = committer._reopen_generation_experience(state.generation_experiences[-1])
        validate_authored_generation_revision_target(binding, experience, corrected_target)
        payload = _canonical_json_bytes(corrected)
        digest = hashlib.sha256(payload).hexdigest()
        path = Path('state/video-generation/supersessions') / f'{corrected.content_hash}.json'
        pointer = GenerationVisualSupersessionReceiptPointer(
            path=path, content_hash=corrected.content_hash, attempt_id=attempt_id,
            request_fingerprint=corrected.request_fingerprint,
            artifact_sha256=corrected.artifact_sha256,
            experience_content_hash=corrected.experience_content_hash, file_sha256=digest)
        committer._write_immutable_artifact(PreparedArtifact(path, payload, digest), attempt_id=attempt_id)
        replacement = _validated_transition(attempt, {
            'video_generation_state':state.model_copy(update={'visual_supersession':pointer})})
        successor = _validated_transition(manifest, {
            'manifest_revision':manifest.manifest_revision + 1,
            'attempts':tuple(replacement if a.attempt_id == attempt_id else a for a in manifest.attempts)})
        committer._write_manifest_atomic(successor)
        load_production_project(committer.project_root / 'project.yaml')
        return committer._read_manifest()
