"""Private contracts owned exclusively by the production state committer facade.

The dataclasses, callables, crash-injection protocols, and durable permit
classes defined here are private building blocks for
``ai_video.production.state_commit``. They are not part of the public
``ai_video.production`` API and may evolve as long as ``state_commit``
re-exports them with the same object identity.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Callable, Literal, Protocol

from ai_video.production.audio import (
    PreparedAudioImport,
    VoiceCallAuthorization,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoiceProviderResult,
)
from ai_video.production.captions import PreparedCaptionImport
from ai_video.production.dependency import (
    DependencyResolution,
    ProductionDependencyInputs,
)
from ai_video.production.image import (
    ImageGenerationAuthorization,
    ImageGenerationRequest,
    ImageProvenanceReceipt,
    ImageProviderResult,
    MeasuredPng,
)
from ai_video.production.models import (
    ApprovedRepairReceiptPointer,
    AssetRecord,
    AssetRegistrySnapshot,
    DependencyGraphSnapshot,
    DependencyGraphSnapshotPointer,
    DependencyGraphTransition,
    LoadedProductionProject,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    RendererSelectionReceipt,
    RenderStateSnapshotPointer,
)


@dataclass(frozen=True)
class PreparedArtifact:
    relative_path: Path
    payload: bytes
    file_sha256: str


@dataclass(frozen=True)
class StateCommitRequest:
    attempt_id: str
    operation: str
    expected_manifest_revision: int
    artifacts: tuple[PreparedArtifact, ...]
    next_project: ProjectSnapshotPointer
    next_registry: RegistrySnapshotPointer
    dependency_graph_transition: DependencyGraphTransition | None = None
    approved_repair_receipt: ApprovedRepairReceiptPointer | None = None


@dataclass(frozen=True)
class BeginRenderAttemptRequest:
    expected_manifest_revision: int
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt


@dataclass(frozen=True)
class RecordRenderFailureRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt
    phase: Literal["source", "lint", "check", "render", "verify"]
    error_code: str
    error_message: str


@dataclass(frozen=True)
class ActivateRenderStateRequest:
    attempt_id: str
    expected_manifest_revision: int
    current_project: ProjectSnapshotPointer
    current_registry: RegistrySnapshotPointer
    base_render_state: RenderStateSnapshotPointer | None
    renderer_selection: RendererSelectionReceipt
    artifacts: tuple[PreparedArtifact, ...]
    next_render_state: RenderStateSnapshotPointer
    dependency_graph_transition: DependencyGraphTransition | None = None


@dataclass(frozen=True)
class RenderAttemptPaths:
    attempt_root: Path
    source_root: Path
    staged_output_path: Path
    verification_snapshot_path: Path


@dataclass(frozen=True)
class VoiceAttemptPaths:
    attempt_root: Path
    request_path: Path
    preview_path: Path
    authorization_path: Path
    submit_intent_path: Path
    audio_candidate_path: Path
    alignment_path: Path
    cost_path: Path
    provenance_path: Path
    outcome_path: Path


VoiceCandidatePreparer = Callable[
    [
        VoiceGenerationRequest,
        VoiceGenerationPreview,
        VoiceCallAuthorization,
        VoiceProviderResult,
        VoiceAttemptPaths,
    ],
    "PreparedVoiceCandidate",
]
VoiceDependencyTransitionPreparer = Callable[
    [StateCommitRequest], StateCommitRequest
]


@dataclass(frozen=True)
class PreparedVoiceCandidate:
    """Narrow local-only output; it carries no registry/write/activation authority."""

    audio: PreparedAudioImport
    caption: PreparedCaptionImport | None = None
    caption_asset_record: AssetRecord | None = None

    def __post_init__(self) -> None:
        if (self.caption is None) != (self.caption_asset_record is None):
            raise ValueError("Prepared voice caption bytes and AssetRecord must be all-or-none.")


@dataclass(frozen=True)
class PreparedImageCandidate:
    """Pure candidate identities; it carries no write or activation authority."""

    base_inputs: ProductionDependencyInputs
    candidate_project: LoadedProductionProject
    candidate_registry: AssetRegistrySnapshot
    candidate_inputs: ProductionDependencyInputs
    candidate_graph: DependencyGraphSnapshot
    resolution: DependencyResolution
    candidate_project_pointer: ProjectSnapshotPointer
    candidate_registry_pointer: RegistrySnapshotPointer
    candidate_graph_pointer: DependencyGraphSnapshotPointer
    candidate_project_bytes: bytes
    candidate_registry_bytes: bytes
    candidate_graph_bytes: bytes


class ImageCandidatePreparer(Protocol):
    def __call__(
        self,
        base_project: LoadedProductionProject,
        request: ImageGenerationRequest,
        authorization: ImageGenerationAuthorization,
        result: ImageProviderResult,
        measured: MeasuredPng,
        receipt: ImageProvenanceReceipt,
    ) -> PreparedImageCandidate: ...


class CommitPhase(str, Enum):
    AFTER_ATTEMPT_STARTED = "after_attempt_started"
    AFTER_ARTIFACT_TEMP_WRITE = "after_artifact_temp_write"
    AFTER_ARTIFACT_FILE_FSYNC = "after_artifact_file_fsync"
    AFTER_ARTIFACT_PROMOTION = "after_artifact_promotion"
    AFTER_ARTIFACT_DIRECTORY_FSYNC = "after_artifact_directory_fsync"
    AFTER_ARTIFACT_VERIFICATION = "after_artifact_verification"
    AFTER_GRAPH_CANDIDATE_TEMP_WRITE = "after_graph_candidate_temp_write"
    AFTER_GRAPH_CANDIDATE_FILE_FSYNC = "after_graph_candidate_file_fsync"
    AFTER_GRAPH_CANDIDATE_PROMOTION = "after_graph_candidate_promotion"
    AFTER_GRAPH_CANDIDATE_DIRECTORY_FSYNC = "after_graph_candidate_directory_fsync"
    AFTER_GRAPH_CANDIDATE_VERIFICATION = "after_graph_candidate_verification"
    AFTER_GRAPH_FINAL_MANIFEST_REPLACE = "after_graph_final_manifest_replace"
    AFTER_MANIFEST_TEMP_WRITE = "after_manifest_temp_write"
    AFTER_MANIFEST_FILE_FSYNC = "after_manifest_file_fsync"
    AFTER_MANIFEST_REPLACE = "after_manifest_replace"
    AFTER_MANIFEST_DIRECTORY_FSYNC = "after_manifest_directory_fsync"
    BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION = "before_render_candidate_manifest_serialization"
    AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN = "after_render_candidate_manifest_temp_open"
    AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE = "after_render_candidate_manifest_temp_write"
    AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC = "after_render_candidate_manifest_file_fsync"
    BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE = "before_render_candidate_manifest_replace"
    AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE = "after_render_candidate_manifest_replace"
    AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC = "after_render_candidate_manifest_directory_fsync"
    AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION = "after_render_candidate_manifest_verification"
    AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE = "after_render_final_manifest_temp_write"
    AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC = "after_render_final_manifest_file_fsync"
    BEFORE_RENDER_FINAL_MANIFEST_REPLACE = "before_render_final_manifest_replace"
    AFTER_RENDER_FINAL_MANIFEST_REPLACE = "after_render_final_manifest_replace"
    AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC = "after_render_final_manifest_directory_fsync"
    BEFORE_VOICE_SUBMIT_INTENT = "before_voice_submit_intent"
    AFTER_VOICE_SUBMIT_INTENT = "after_voice_submit_intent"
    AFTER_VOICE_PROVIDER_RESULT = "after_voice_provider_result"
    AFTER_VOICE_CANDIDATE_MANIFEST = "after_voice_candidate_manifest"
    AFTER_VOICE_FINAL_MANIFEST_REPLACE = "after_voice_final_manifest_replace"
    BEFORE_IMAGE_PROVIDER_CALL = "before_image_provider_call"
    AFTER_IMAGE_PERMIT_CONSUMED = "after_image_permit_consumed"
    AFTER_IMAGE_PROVIDER_RESULT = "after_image_provider_result"
    AFTER_IMAGE_CANDIDATE_MANIFEST_REPLACE = "after_image_candidate_manifest_replace"
    AFTER_IMAGE_CANDIDATE_MANIFEST_VERIFICATION = "after_image_candidate_manifest_verification"
    AFTER_IMAGE_FINAL_MANIFEST_REPLACE = "after_image_final_manifest_replace"
    AFTER_IMAGE_FINAL_MANIFEST_VERIFICATION = "after_image_final_manifest_verification"


class CrashInjector(Protocol):
    def checkpoint(self, phase: CommitPhase) -> None: ...


class NoopCrashInjector:
    def checkpoint(self, phase: CommitPhase) -> None:
        return None


_VOICE_PERMIT_TOKEN = object()
_REVIEW_PERMIT_TOKEN = object()
_IMAGE_PERMIT_TOKEN = object()


class _DurableReviewAnalysisPermit:
    """Process-local one-use proof of a durable committer-owned review intent."""

    __slots__ = ("_binding", "_durability_validator", "_consumed", "_lock")

    def __init__(
        self,
        token: object,
        *,
        binding: dict[str, str],
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _REVIEW_PERMIT_TOKEN:
            raise TypeError("Review analysis permits are minted only by ProductionStateCommitter.")
        self._binding = dict(binding)
        self._durability_validator = durability_validator
        self._consumed = False
        self._lock = threading.Lock()

    def _consume_review_analysis_permit(self, **binding: str) -> bool:
        with self._lock:
            if (
                self._consumed
                or binding != self._binding
                or not self._durability_validator()
            ):
                return False
            self._consumed = True
            return True


class _DurableVoiceSubmitPermit:
    """Process-local one-use proof that the exact R+2 intent is durable."""

    __slots__ = (
        "_binding",
        "_manifest_revision",
        "_manifest_file_sha256",
        "_durability_validator",
        "_consumed",
        "_lock",
    )

    def __init__(
        self,
        token: object,
        *,
        binding: dict[str, str],
        manifest_revision: int,
        manifest_file_sha256: str,
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _VOICE_PERMIT_TOKEN:
            raise TypeError("Voice submit permits are minted only by ProductionStateCommitter.")
        self._binding = dict(binding)
        self._manifest_revision = manifest_revision
        self._manifest_file_sha256 = manifest_file_sha256
        self._durability_validator = durability_validator
        self._consumed = False
        self._lock = threading.Lock()

    def _validate_voice_submit_permit(self, **binding: str) -> bool:
        return (
            not self._consumed
            and binding == self._binding
            and self._durability_validator()
        )

    def _consume_voice_submit_permit(self, **binding: str) -> bool:
        with self._lock:
            if not self._validate_voice_submit_permit(**binding):
                return False
            self._consumed = True
            return True

    def __reduce__(self) -> object:
        raise TypeError("Voice submit permits cannot be serialized.")


class _DurableImageSubmitPermit:
    """Process-local one-use proof that the exact image R+2 intent is durable."""

    __slots__ = (
        "_binding",
        "_manifest_revision",
        "_manifest_file_sha256",
        "_durability_validator",
        "_consume_callback",
        "_consumed",
        "_lock",
    )

    def __init__(
        self,
        token: object,
        *,
        binding: dict[str, object],
        manifest_revision: int,
        manifest_file_sha256: str,
        durability_validator: Callable[[], bool],
    ) -> None:
        if token is not _IMAGE_PERMIT_TOKEN:
            raise TypeError(
                "Image submit permits are minted only by ProductionStateCommitter."
            )
        self._binding = MappingProxyType(dict(binding))
        self._manifest_revision = manifest_revision
        self._manifest_file_sha256 = manifest_file_sha256
        self._durability_validator = durability_validator
        self._consume_callback: Callable[[], None] | None = None
        self._consumed = False
        self._lock = threading.Lock()

    def _validate_image_generation_permit(
        self, *, request_fingerprint: str
    ) -> bool:
        return (
            not self._consumed
            and request_fingerprint == self._binding["request_fingerprint"]
            and self._durability_validator()
        )

    def _consume_image_generation_permit(
        self, *, request_fingerprint: str
    ) -> bool:
        with self._lock:
            if not self._validate_image_generation_permit(
                request_fingerprint=request_fingerprint
            ):
                return False
            self._consumed = True
            if self._consume_callback is not None:
                self._consume_callback()
            return True

    def _set_image_generation_consume_callback(
        self, callback: Callable[[], None]
    ) -> None:
        with self._lock:
            if self._consumed or self._consume_callback is not None:
                raise RuntimeError("Image permit consume checkpoint is already bound.")
            self._consume_callback = callback

    def _image_generation_was_consumed(
        self, *, request_fingerprint: str
    ) -> bool:
        with self._lock:
            return (
                self._consumed
                and request_fingerprint == self._binding["request_fingerprint"]
                and self._durability_validator()
            )

    def __reduce__(self) -> object:
        raise TypeError("Image submit permits cannot be serialized.")


if TYPE_CHECKING:
    DurableVoiceSubmitPermit = _DurableVoiceSubmitPermit
    DurableImageSubmitPermit = _DurableImageSubmitPermit
