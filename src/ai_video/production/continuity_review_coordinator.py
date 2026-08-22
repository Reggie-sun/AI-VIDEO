"""Explicit one-shot Product caller for exact-bound continuity review."""

from __future__ import annotations

import hashlib
import os
import stat
from contextlib import AbstractContextManager, ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Protocol

from pydantic import Field, ValidationError, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.local_continuity_reviewer import (
    LocalCudaContinuityReviewerConfig,
    create_local_cuda_continuity_reviewer,
)
from ai_video.production.models import (
    EvidenceStrength,
    StateCommitStatus,
    StrictModel,
    ToolIdentity,
    VideoAttemptPhase,
)
from ai_video.production.project import load_qa_policy
from ai_video.production.review import GeneratedShotContinuityEvidence
from ai_video.production.video_artifact import (
    GeneratedShotContinuityReviewer,
    MeasuredVideoMetadata,
)


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"
HumanReviewValue = Literal["PASS", "FAIL", "NOT_SURE"]


def _review_error(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.REVIEW_EVIDENCE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _state_error(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _identity_is_bound(identity: ToolIdentity) -> bool:
    return bool(identity.name.strip() and identity.version.strip())


class HumanReviewRequestV1(StrictModel):
    """Read-only projection binding one review to exact canonical inputs."""

    attempt_id: str = Field(pattern=_SAFE_ID)
    source_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    artifact_sha256: str = Field(pattern=_SHA256)
    continuity_constraints_hash: str = Field(pattern=_SHA256)
    qa_policy_content_hash: str = Field(pattern=_SHA256)
    automatic_evaluator: ToolIdentity
    required_reviewer: ToolIdentity
    media_identity: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "HumanReviewRequestV1":
        if not _identity_is_bound(self.automatic_evaluator) or not _identity_is_bound(
            self.required_reviewer
        ):
            raise ValueError("review request identities must be nonblank")
        if self.media_identity != f"sha256:{self.artifact_sha256}":
            raise ValueError("review request media identity is not exact")
        expected = canonical_sha256(
            {
                "schema": "human-continuity-review-request/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("review request content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HumanReviewRequestV1":
        candidate = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    {
                        "schema": "human-continuity-review-request/1",
                        **candidate.model_dump(
                            mode="json",
                            exclude={"content_hash"},
                            warnings=False,
                        ),
                    }
                ),
            }
        )


class HumanReviewDecisionV1(StrictModel):
    """Immutable authoring payload; never canonical Production evidence."""

    review_request_content_hash: str = Field(pattern=_SHA256)
    reviewer_identity: ToolIdentity
    identity: HumanReviewValue
    camera_axis: HumanReviewValue
    framing: HumanReviewValue
    motion_direction: HumanReviewValue
    entrance: HumanReviewValue
    exit: HumanReviewValue
    unexpected_reentry: HumanReviewValue
    rationale: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "HumanReviewDecisionV1":
        if not _identity_is_bound(self.reviewer_identity) or not self.rationale.strip():
            raise ValueError("review decision identity and rationale must be nonblank")
        expected = canonical_sha256(
            {
                "schema": "human-continuity-review-decision/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("review decision content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "HumanReviewDecisionV1":
        candidate = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    {
                        "schema": "human-continuity-review-decision/1",
                        **candidate.model_dump(
                            mode="json",
                            exclude={"content_hash"},
                            warnings=False,
                        ),
                    }
                ),
            }
        )

    def require_complete(self) -> None:
        if "NOT_SURE" in (
            self.identity,
            self.camera_axis,
            self.framing,
            self.motion_direction,
            self.entrance,
            self.exit,
            self.unexpected_reentry,
        ):
            raise _review_error(
                "Human continuity decision is incomplete; NOT_SURE cannot activate a candidate."
            )


class _VideoService(Protocol):
    def fetch_and_activate(
        self,
        *,
        attempt_id: str,
        continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
    ) -> object: ...


ReviewerFactory = Callable[..., GeneratedShotContinuityReviewer]


@dataclass(frozen=True)
class _ReviewSnapshot:
    request: HumanReviewRequestV1
    resolved_request: object


def _read_exact_file(path: Path, *, maximum_bytes: int) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise _state_error("Continuity review input could not be opened.", str(exc)) from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise _state_error("Continuity review input must be one regular file.")
        if opened.st_size > maximum_bytes:
            raise _review_error("Human continuity decision file is too large.")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        payload = b"".join(chunks)
        if len(payload) != opened.st_size:
            raise _state_error("Continuity review input changed while being read.")
        return payload
    except AiVideoError:
        raise
    except OSError as exc:
        raise _state_error("Continuity review input could not be read.", str(exc)) from exc
    finally:
        os.close(fd)


def _measure_exact_file(path: Path) -> tuple[str, int]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise _state_error("Fetched continuity artifact could not be opened.", str(exc)) from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise _state_error("Fetched continuity artifact must be one regular file.")
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(fd, 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        if size != opened.st_size:
            raise _state_error("Fetched continuity artifact changed while being read.")
        return digest.hexdigest(), size
    except AiVideoError:
        raise
    except OSError as exc:
        raise _state_error("Fetched continuity artifact could not be read.", str(exc)) from exc
    finally:
        os.close(fd)


def _hash_held_fd(held_fd: int) -> tuple[str, int]:
    position = os.lseek(held_fd, 0, os.SEEK_CUR)
    try:
        os.lseek(held_fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        size = 0
        while chunk := os.read(held_fd, 1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        return digest.hexdigest(), size
    finally:
        os.lseek(held_fd, position, os.SEEK_SET)


class ContinuityReviewCoordinator:
    """Prepare one exact projection, then invoke the existing activation seam once."""

    def __init__(
        self,
        *,
        committer: object,
        video_service: _VideoService,
        reviewer_config: LocalCudaContinuityReviewerConfig,
        reviewer_identity: ToolIdentity,
        gpu_execution_lease: Callable[[], AbstractContextManager[None]],
        reviewer_factory: ReviewerFactory = create_local_cuda_continuity_reviewer,
    ) -> None:
        if not _identity_is_bound(reviewer_identity):
            raise ValueError("continuity reviewer identity must be nonblank")
        self._committer = committer
        self._video_service = video_service
        self._reviewer_config = reviewer_config
        self._reviewer_identity = reviewer_identity
        self._gpu_execution_lease = gpu_execution_lease
        self._reviewer_factory = reviewer_factory

    def _snapshot(self, *, attempt_id: str, allow_existing: bool) -> _ReviewSnapshot:
        committer = self._committer
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (
            attempt.status is not StateCommitStatus.RUNNING
            or state is None
            or state.phase is not VideoAttemptPhase.VALIDATE
        ):
            raise _state_error(
                "Continuity review request requires a running VALIDATE attempt."
            )
        if state.continuity_evaluation is not None and not allow_existing:
            raise _state_error(
                "Continuity review request is unavailable after evaluation has started."
            )
        request = committer._reopen_video_request(state.request)
        binding = request.continuity_binding
        activation_scope = request.activation_scope
        original = activation_scope.request if activation_scope is not None else None
        if binding is None or original is None:
            raise _state_error(
                "Continuity review requires an exact continuity activation binding."
            )
        if (
            binding.target_shot_id != original.target_shot_id
            or binding.target_shot_content_hash != original.target_shot_content_hash
        ):
            raise _state_error("Continuity target binding is not exact.")
        fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
        if fetch_pointer is None or (
            state.local_fetch_receipt is not None and state.fetch_receipt is not None
        ):
            raise _state_error("Continuity review requires one exact fetched artifact.")
        reopen_fetch = (
            committer._reopen_local_video_fetch
            if state.local_fetch_receipt is not None
            else committer._reopen_video_fetch
        )
        fetch_receipt = reopen_fetch(fetch_pointer)
        if (
            fetch_receipt.artifact_sha256 != fetch_pointer.artifact_sha256
            or fetch_receipt.artifact_size_bytes != fetch_pointer.artifact_size_bytes
        ):
            raise _state_error("Fetched continuity receipt does not match its pointer.")
        expected_artifact_path = Path(
            "state/video-generation/fetch/files/"
            f"{fetch_pointer.artifact_sha256}.mp4"
        )
        if fetch_pointer.artifact_path != expected_artifact_path:
            raise _state_error("Fetched continuity artifact path is not canonical.")
        artifact_sha256, artifact_size = _measure_exact_file(
            committer.project_root / fetch_pointer.artifact_path
        )
        if (
            artifact_size != fetch_pointer.artifact_size_bytes
            or artifact_sha256 != fetch_pointer.artifact_sha256
        ):
            raise _state_error("Fetched continuity artifact bytes are stale.")
        policy_pointer = manifest.active_qa_policy
        if policy_pointer is None:
            raise _state_error("Continuity review requires an active QA policy.")
        policy = load_qa_policy(committer.project_root, policy_pointer)
        if (
            policy.policy_id != policy_pointer.policy_id
            or policy.policy_version != policy_pointer.policy_version
            or policy.content_hash != policy_pointer.content_hash
        ):
            raise _state_error("Continuity QA policy is stale.")
        authorities = policy.semantic_authorities
        if (
            self._reviewer_config.evaluator not in authorities
            or self._reviewer_identity not in authorities
        ):
            raise _state_error(
                "Continuity evaluator and human reviewer must be selected by policy."
            )
        projection = HumanReviewRequestV1.create(
            attempt_id=attempt_id,
            source_shot_id=binding.terminal_frame.source_shot_id,
            target_shot_id=original.target_shot_id,
            target_shot_content_hash=original.target_shot_content_hash,
            resolved_generation_hash=request.resolved_generation_hash,
            artifact_sha256=fetch_pointer.artifact_sha256,
            continuity_constraints_hash=binding.constraints.content_hash,
            qa_policy_content_hash=policy.content_hash,
            automatic_evaluator=self._reviewer_config.evaluator,
            required_reviewer=self._reviewer_identity,
            media_identity=f"sha256:{fetch_pointer.artifact_sha256}",
        )
        return _ReviewSnapshot(request=projection, resolved_request=request)

    def prepare_request(self, *, attempt_id: str) -> HumanReviewRequestV1:
        return self._snapshot(attempt_id=attempt_id, allow_existing=False).request

    def _read_decision(self, path: Path) -> HumanReviewDecisionV1:
        try:
            payload = _read_exact_file(path, maximum_bytes=64 * 1024)
            return HumanReviewDecisionV1.model_validate_json(payload)
        except AiVideoError as exc:
            if exc.code is ErrorCode.REVIEW_EVIDENCE_INVALID:
                raise
            raise _review_error("Human continuity decision could not be opened.") from exc
        except (ValidationError, ValueError) as exc:
            raise _review_error(
                "Human continuity decision is invalid or tampered.", str(exc)
            ) from exc

    def _human_fallback(
        self,
        snapshot: _ReviewSnapshot,
        decision: HumanReviewDecisionV1,
    ):
        def fallback(
            held_fd: int,
            request,
            measured: MeasuredVideoMetadata,
            qa_policy_content_hash: str,
        ) -> GeneratedShotContinuityEvidence:
            expected = snapshot.request
            binding = request.continuity_binding
            original = request.activation_scope.request if request.activation_scope else None
            artifact_sha256, artifact_size = _hash_held_fd(held_fd)
            if (
                binding is None
                or original is None
                or request.resolved_generation_hash != expected.resolved_generation_hash
                or binding.terminal_frame.source_shot_id != expected.source_shot_id
                or original.target_shot_id != expected.target_shot_id
                or original.target_shot_content_hash
                != expected.target_shot_content_hash
                or binding.constraints.content_hash
                != expected.continuity_constraints_hash
                or measured.artifact_sha256 != expected.artifact_sha256
                or measured.size_bytes != artifact_size
                or artifact_sha256 != expected.artifact_sha256
                or qa_policy_content_hash != expected.qa_policy_content_hash
            ):
                raise _review_error(
                    "Human continuity decision does not bind exact runtime inputs."
                )
            return GeneratedShotContinuityEvidence.create(
                source_shot_id=expected.source_shot_id,
                target_shot_id=expected.target_shot_id,
                target_shot_content_hash=expected.target_shot_content_hash,
                resolved_generation_hash=expected.resolved_generation_hash,
                artifact_sha256=expected.artifact_sha256,
                continuity_constraints_hash=expected.continuity_constraints_hash,
                qa_policy_content_hash=expected.qa_policy_content_hash,
                evaluator=decision.reviewer_identity,
                strength=EvidenceStrength.HUMAN,
                coverage_complete=True,
                identity_match=decision.identity == "PASS",
                camera_axis_match=decision.camera_axis == "PASS",
                framing_match=decision.framing == "PASS",
                motion_direction_match=decision.motion_direction == "PASS",
                entrance_state_match=decision.entrance == "PASS",
                exit_state_match=decision.exit == "PASS",
                unexpected_reentry=decision.unexpected_reentry == "FAIL",
                rationale=decision.rationale.strip(),
            )

        return fallback

    def _guard_reviewer(
        self,
        snapshot: _ReviewSnapshot,
        reviewer,
    ):
        expected = snapshot.request

        def validate(request, measured, qa_policy_content_hash: str) -> None:
            binding = request.continuity_binding
            original = request.activation_scope.request if request.activation_scope else None
            if (
                binding is None
                or original is None
                or request.resolved_generation_hash
                != expected.resolved_generation_hash
                or binding.terminal_frame.source_shot_id != expected.source_shot_id
                or original.target_shot_id != expected.target_shot_id
                or original.target_shot_content_hash
                != expected.target_shot_content_hash
                or binding.constraints.content_hash
                != expected.continuity_constraints_hash
                or measured.artifact_sha256 != expected.artifact_sha256
                or qa_policy_content_hash != expected.qa_policy_content_hash
            ):
                raise _review_error(
                    "Human continuity decision became stale before evaluation."
                )

        class BoundReviewer:
            def create_intent(self, request, measured, qa_policy_content_hash):
                validate(request, measured, qa_policy_content_hash)
                return reviewer.create_intent(
                    request, measured, qa_policy_content_hash
                )

            def __call__(self, held_fd, request, measured, qa_policy_content_hash):
                validate(request, measured, qa_policy_content_hash)
                return reviewer(
                    held_fd, request, measured, qa_policy_content_hash
                )

        return BoundReviewer()

    def validate_and_activate(
        self,
        *,
        attempt_id: str,
        decision_path: Path,
    ) -> object:
        manifest = self._committer._read_manifest()
        attempt = self._committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if state is None:
            raise _state_error("Video generation state is missing.")
        if (
            state.phase in {VideoAttemptPhase.CANDIDATE, VideoAttemptPhase.ACTIVATE}
            or state.continuity_evaluation is not None
        ):
            return self._video_service.fetch_and_activate(
                attempt_id=attempt_id,
                continuity_reviewer=None,
            )
        snapshot = self._snapshot(attempt_id=attempt_id, allow_existing=False)
        decision = self._read_decision(decision_path)
        if (
            decision.review_request_content_hash != snapshot.request.content_hash
            or decision.reviewer_identity != snapshot.request.required_reviewer
        ):
            raise _review_error(
                "Human continuity decision does not match the current review request."
            )
        decision.require_complete()
        fallback = self._human_fallback(snapshot, decision)
        with ExitStack() as stack:
            try:
                stack.enter_context(self._gpu_execution_lease())
            except AiVideoError:
                raise
            except Exception as exc:
                raise AiVideoError(
                    code=ErrorCode.PRODUCTION_STATE_BUSY,
                    user_message="Local continuity evaluator lease is unavailable.",
                    technical_detail=str(exc),
                    retryable=True,
                    cause=exc,
                ) from exc
            try:
                reviewer = self._reviewer_factory(
                    config=self._reviewer_config,
                    human_fallback=fallback,
                    human_fallback_identity=self._reviewer_identity,
                )
            except AiVideoError:
                raise
            except Exception as exc:
                raise _review_error(
                    "Local continuity reviewer runtime is invalid.", str(exc)
                ) from exc
            guarded_reviewer = self._guard_reviewer(snapshot, reviewer)
            return self._video_service.fetch_and_activate(
                attempt_id=attempt_id,
                continuity_reviewer=guarded_reviewer,
            )
