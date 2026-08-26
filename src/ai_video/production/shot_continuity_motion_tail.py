"""Logical full-source motion-tail evidence for the Shot Continuity M0 path.

The source MP4 is not copied or re-encoded.  Instead this module records a
separate, derived registry asset whose bytes deliberately alias the exact
activated source asset.  The immutable receipt proves that this is a complete
0..terminal selection, not an accidental reuse of a source asset ID.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._state_commit_common import (
    _canonical_json_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_contracts import (
    PreparedArtifact,
    StateCommitRequest,
)
from ai_video.production._video_continuity import (
    C4MotionTailEvidence,
    TerminalFrameEvidence,
)
from ai_video.production._video_project_reader import (
    load_source_boundary_review_evidence,
    load_source_boundary_review_intent,
    load_source_boundary_review_receipt,
    load_terminal_frame_evidence,
    load_video_provenance_receipt,
    load_video_request_receipt,
)
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.dependency import (
    build_applied_dependency_evidence,
    resolve_dependency_state,
)
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    QaVerdict,
    ToolIdentity,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_dependency_graph_snapshot_path,
    canonical_full_source_motion_analysis_receipt_path,
    canonical_full_source_motion_tail_receipt_path,
    canonical_video_asset_path,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.shot_continuity_motion_analysis import (
    FullSourceMotionAnalysisReceipt,
    FullSourceMotionSpanMeasurement,
    analyze_full_source_motion,
)
from ai_video.production.shot_continuity_source_runtime import build_source_closure


_SHA256 = r"^[0-9a-f]{64}$"
_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_TAIL_TOOL = ToolIdentity(name="ai-video-full-source-motion-tail", version="1")


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class _TailStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class FullSourceMotionTailReceipt(_TailStrictModel):
    """Sealed proof for a distinct logical tail that aliases all source bytes."""

    source_attempt_id: str = Field(pattern=_SAFE_ID)
    source_shot_id: str = Field(pattern=_SAFE_ID)
    source_shot_revision: int = Field(strict=True, ge=1)
    source_shot_content_hash: str = Field(pattern=_SHA256)
    source_video_asset_id: str = Field(pattern=_SAFE_ID)
    source_video_sha256: str = Field(pattern=_SHA256)
    source_registry_revision_id: str = Field(pattern=_SHA256)
    source_generation_id: str = Field(pattern=_SAFE_ID)
    source_request_input_hash: str = Field(pattern=_SHA256)
    source_resolved_generation_hash: str = Field(pattern=_SHA256)
    source_provenance_receipt_id: str = Field(pattern=_SHA256)
    source_provenance_receipt_sha256: str = Field(pattern=_SHA256)
    source_p6_acceptance_evidence_id: str = Field(pattern=_SHA256)
    source_p6_acceptance_evidence_sha256: str = Field(pattern=_SHA256)
    source_p6_acceptance_receipt_id: str = Field(pattern=_SHA256)
    source_p6_acceptance_receipt_sha256: str = Field(pattern=_SHA256)
    tail_asset_id: str = Field(pattern=_SAFE_ID)
    selection_rule_version: Literal["full-source-zero-copy-v1"]
    start_timestamp_numerator: int = Field(strict=True, ge=0)
    start_timestamp_denominator: int = Field(strict=True, gt=0)
    end_timestamp_numerator: int = Field(strict=True, ge=0)
    end_timestamp_denominator: int = Field(strict=True, gt=0)
    start_frame_index: int = Field(strict=True, ge=0)
    end_frame_index: int = Field(strict=True, ge=0)
    source_fps_numerator: int = Field(strict=True, gt=0)
    source_fps_denominator: int = Field(strict=True, gt=0)
    source_frame_count: int = Field(strict=True, ge=3)
    source_duration_milliseconds: int = Field(strict=True, gt=0)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    provider_min_duration_milliseconds: int = Field(strict=True, gt=0)
    provider_max_duration_milliseconds: int = Field(strict=True, gt=0)
    terminal_frame_evidence: TerminalFrameEvidence
    motion_analysis_receipt_hash: str = Field(pattern=_SHA256)
    target_shot_id: str = Field(pattern=_SAFE_ID)
    target_shot_revision: int = Field(strict=True, ge=1)
    target_shot_content_hash: str = Field(pattern=_SHA256)
    continuity_constraint_snapshot_hash: str = Field(pattern=_SHA256)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_full_source_selection(self) -> "FullSourceMotionTailReceipt":
        terminal = self.terminal_frame_evidence
        if (
            self.tail_asset_id == self.source_video_asset_id
            or self.source_p6_acceptance_evidence_id
            != self.source_p6_acceptance_evidence_sha256
            or self.source_p6_acceptance_receipt_id
            != self.source_p6_acceptance_receipt_sha256
            or self.source_provenance_receipt_id
            != self.source_provenance_receipt_sha256
        ):
            raise ValueError("full-source tail identities are not distinct and exact")
        if (
            self.source_shot_id != terminal.source_shot_id
            or self.source_shot_revision != terminal.source_shot_revision
            or self.source_shot_content_hash != terminal.source_shot_content_hash
            or self.source_video_asset_id != terminal.source_video_asset_id
            or self.source_video_sha256 != terminal.source_video_sha256
            or self.source_registry_revision_id != terminal.source_registry.revision_id
            or self.source_generation_id != terminal.source_generation_id
            or self.source_request_input_hash != terminal.source_request_input_hash
            or self.source_resolved_generation_hash
            != terminal.source_resolved_generation_hash
            or self.source_provenance_receipt_id
            != terminal.source_provenance_receipt_id
        ):
            raise ValueError("full-source tail does not match terminal lineage")
        if (
            self.start_frame_index != 0
            or self.start_timestamp_numerator != 0
            or self.end_frame_index != terminal.frame_index
            or self.end_frame_index != self.source_frame_count - 1
            or self.end_timestamp_numerator * terminal.timestamp_denominator
            != terminal.timestamp_numerator * self.end_timestamp_denominator
            or self.source_fps_numerator != terminal.source_fps_numerator
            or self.source_fps_denominator != terminal.source_fps_denominator
            or self.source_frame_count != terminal.source_frame_count
            or self.source_width != terminal.source_width
            or self.source_height != terminal.source_height
            or self.source_duration_milliseconds
            != terminal.source_duration_milliseconds
        ):
            raise ValueError(
                "full-source tail selection must span frame zero through terminal"
            )
        if (
            self.provider_min_duration_milliseconds > self.source_duration_milliseconds
            or self.source_duration_milliseconds
            > self.provider_max_duration_milliseconds
        ):
            raise ValueError("full-source tail is outside provider duration bounds")
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        if self.content_hash != _seal_tail(payload):
            raise ValueError("full-source motion-tail receipt hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "FullSourceMotionTailReceipt":
        data = dict(values)
        data.pop("content_hash", None)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = _seal_tail(
            candidate.model_dump(mode="json", exclude={"content_hash"}, warnings=False)
        )
        return cls.model_validate(data)

    def to_c4_motion_tail_evidence(
        self,
        *,
        registry_revision_id: str,
        tail_asset: AssetRecord,
    ) -> C4MotionTailEvidence:
        """Project the sealed receipt into the existing M0 C4 evidence contract."""

        if (
            tail_asset.asset_id != self.tail_asset_id
            or tail_asset.asset_type is not AssetType.VIDEO
            or tail_asset.source_kind is not AssetSourceKind.DERIVED
            or tail_asset.sha256 != self.source_video_sha256
            or tail_asset.video_metadata is None
            or tail_asset.creation_receipt_id != self.content_hash
        ):
            raise _invalid("Full-source tail registry asset is not exact.")
        metadata = tail_asset.video_metadata
        return C4MotionTailEvidence.create(
            source_shot_id=self.source_shot_id,
            source_shot_revision=self.source_shot_revision,
            source_shot_content_hash=self.source_shot_content_hash,
            source_video_asset_id=self.source_video_asset_id,
            source_video_sha256=self.source_video_sha256,
            source_registry_revision_id=self.source_registry_revision_id,
            source_generation_id=self.source_generation_id,
            source_request_input_hash=self.source_request_input_hash,
            source_resolved_generation_hash=self.source_resolved_generation_hash,
            source_provenance_receipt_id=self.source_provenance_receipt_id,
            source_provenance_receipt_sha256=self.source_provenance_receipt_sha256,
            source_p6_acceptance_evidence_id=self.source_p6_acceptance_evidence_id,
            source_p6_acceptance_evidence_sha256=self.source_p6_acceptance_evidence_sha256,
            registry_revision_id=registry_revision_id,
            extraction_receipt_id=self.content_hash,
            extraction_receipt_sha256=self.content_hash,
            materialization_receipt_id=self.content_hash,
            materialization_receipt_sha256=self.content_hash,
            selection_rule_version=self.selection_rule_version,
            start_timestamp_numerator=self.start_timestamp_numerator,
            start_timestamp_denominator=self.start_timestamp_denominator,
            end_timestamp_numerator=self.end_timestamp_numerator,
            end_timestamp_denominator=self.end_timestamp_denominator,
            start_frame_index=self.start_frame_index,
            end_frame_index=self.end_frame_index,
            source_fps_numerator=self.source_fps_numerator,
            source_fps_denominator=self.source_fps_denominator,
            source_frame_count=self.source_frame_count,
            extracted_asset_id=tail_asset.asset_id,
            extracted_sha256=tail_asset.sha256,
            extracted_mime_type=tail_asset.mime_type,
            extracted_size_bytes=tail_asset.size_bytes,
            extracted_width=tail_asset.width,
            extracted_height=tail_asset.height,
            extracted_fps_numerator=metadata.fps_numerator,
            extracted_fps_denominator=metadata.fps_denominator,
            extracted_duration_milliseconds=metadata.duration_milliseconds,
            extracted_frame_count=metadata.frame_count,
            extractor_name=_TAIL_TOOL.name,
            extractor_version=_TAIL_TOOL.version,
            terminal_frame_evidence=self.terminal_frame_evidence,
            target_shot_id=self.target_shot_id,
            target_shot_revision=self.target_shot_revision,
            target_shot_content_hash=self.target_shot_content_hash,
            continuity_constraint_snapshot_hash=self.continuity_constraint_snapshot_hash,
        )


@dataclass(frozen=True)
class PreparedFullSourceMotionTail:
    receipt: FullSourceMotionTailReceipt
    tail_asset: AssetRecord
    commit_request: StateCommitRequest | None
    replayed: bool = False


def _seal_with_schema(schema: str, payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            {"schema": schema, **payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _seal_tail(payload: dict[str, object]) -> str:
    return _seal_with_schema("ai-video-full-source-motion-tail/2", payload)


def _source_attempt(project: LoadedProductionProject, attempt_id: str):
    attempt = next(
        (item for item in project.manifest.attempts if item.attempt_id == attempt_id),
        None,
    )
    if (
        attempt is None
        or attempt.operation != "video_generation"
        or attempt.video_generation_state is None
    ):
        raise _invalid(
            "Full-source motion tail requires one exact source video attempt."
        )
    state = attempt.video_generation_state
    evaluation = state.source_boundary_evaluation
    if (
        attempt.status.value != "succeeded"
        or state.phase.value != "activate"
        or evaluation is None
        or evaluation.evidence is None
        or evaluation.receipt is None
        or evaluation.provenance is None
        or state.terminal_frame_evidence is None
    ):
        raise _invalid(
            "Full-source motion tail requires an activated source P6 closure."
        )
    return attempt, state, evaluation


def _source_lineage(
    project_root: Path,
    project: LoadedProductionProject,
    source_attempt_id: str,
):
    attempt, state, evaluation = _source_attempt(project, source_attempt_id)
    request = load_video_request_receipt(project_root, state.request)
    evidence = load_source_boundary_review_evidence(project_root, evaluation.evidence)
    receipt = load_source_boundary_review_receipt(project_root, evaluation.receipt)
    intent = load_source_boundary_review_intent(project_root, evaluation.intent)
    provenance = load_video_provenance_receipt(project_root, evaluation.provenance)
    terminal = load_terminal_frame_evidence(project_root, state.terminal_frame_evidence)
    if (
        receipt.verdict is not QaVerdict.PASS
        or evidence.intent.content_hash != intent.content_hash
        or receipt.evidence_content_hash != evidence.content_hash
        or receipt.resolved_generation_hash != request.resolved_generation_hash
        or provenance.content_hash != terminal.source_provenance_receipt_id
        or provenance.request_receipt_fingerprint
        != request.desired_generation_fingerprint
        or provenance.resolved_generation_hash != request.resolved_generation_hash
        or provenance.artifact_sha256 != terminal.source_video_sha256
        or request.output_asset_id != terminal.source_video_asset_id
    ):
        raise _invalid("Full-source motion tail source P6 lineage is not exact.")
    source_asset = next(
        (
            item
            for item in project.registry.assets
            if item.asset_id == request.output_asset_id
        ),
        None,
    )
    if (
        source_asset is None
        or source_asset.asset_type is not AssetType.VIDEO
        or source_asset.source_kind is not AssetSourceKind.GENERATED
        or source_asset.sha256 != terminal.source_video_sha256
        or source_asset.video_metadata is None
        or source_asset.egress.remote
        or source_asset.artifact_path != canonical_video_asset_path(source_asset.sha256)
    ):
        raise _invalid(
            "Full-source motion tail source asset is not an exact local generated MP4."
        )
    try:
        raw = _read_regular_file_nofollow(
            project_root / source_asset.artifact_path,
            contained_by=project_root / "assets",
        )
    except (OSError, ValueError) as exc:
        raise _invalid(
            "Full-source motion tail source bytes cannot be reopened.", str(exc)
        ) from exc
    if (
        raw.file_sha256 != source_asset.sha256
        or raw.size_bytes != source_asset.size_bytes
    ):
        raise _invalid("Full-source motion tail source bytes are not exact.")
    return request, source_asset, terminal, evidence, receipt, provenance


def _seal_registry(
    registry: AssetRegistrySnapshot, assets: tuple[AssetRecord, ...]
) -> AssetRegistrySnapshot:
    provisional = AssetRegistrySnapshot.model_construct(
        schema_version=registry.schema_version,
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=assets,
    )
    content_hash = registry_semantic_sha256(provisional)
    return AssetRegistrySnapshot(
        schema_version=registry.schema_version,
        revision_id=content_hash,
        content_hash=content_hash,
        assets=assets,
    )


def _tail_asset(
    *,
    source_asset: AssetRecord,
    terminal: TerminalFrameEvidence,
    receipt: FullSourceMotionTailReceipt,
) -> AssetRecord:
    metadata = source_asset.video_metadata
    assert metadata is not None
    return AssetRecord(
        asset_id=receipt.tail_asset_id,
        asset_type=AssetType.VIDEO,
        artifact_path=source_asset.artifact_path,
        sha256=source_asset.sha256,
        size_bytes=source_asset.size_bytes,
        mime_type=source_asset.mime_type,
        duration_seconds=source_asset.duration_seconds,
        width=source_asset.width,
        height=source_asset.height,
        source_kind=AssetSourceKind.DERIVED,
        tool=_TAIL_TOOL,
        input_artifact_ids=(source_asset.asset_id, terminal.extracted_asset_id),
        input_fingerprint=receipt.content_hash,
        creation_receipt_id=receipt.content_hash,
        usage_license=source_asset.usage_license,
        video_metadata=metadata,
    )


def prepare_full_source_motion_tail_commit(
    *,
    project_root: str | Path,
    committer,
    project: LoadedProductionProject,
    attempt_id: str,
    source_attempt_id: str,
    tail_asset_id: str,
    target_shot_id: str,
    target_shot_revision: int,
    target_shot_content_hash: str,
    continuity_constraint_snapshot_hash: str,
    provider_min_duration_milliseconds: int,
    provider_max_duration_milliseconds: int,
    motion_analysis: FullSourceMotionAnalysisReceipt,
) -> PreparedFullSourceMotionTail:
    """Prepare, but do not execute, the one canonical registry/P5 commit."""

    root = Path(project_root).resolve(strict=True)
    if (
        root != project.root.resolve(strict=True)
        or committer._read_manifest() != project.manifest
    ):
        raise _invalid("Full-source motion-tail base project is stale.")
    try:
        checked_analysis = FullSourceMotionAnalysisReceipt.model_validate(
            motion_analysis.model_dump(mode="json")
        )
    except (AttributeError, ValueError) as exc:
        raise _invalid("Full-source motion analysis receipt is invalid.", str(exc)) from exc
    existing_tail = next(
        (item for item in project.registry.assets if item.asset_id == tail_asset_id),
        None,
    )
    if existing_tail is not None:
        receipt = validate_full_source_motion_tail(root, project, existing_tail)
        if (
            receipt.source_attempt_id != source_attempt_id
            or receipt.target_shot_id != target_shot_id
            or receipt.target_shot_revision != target_shot_revision
            or receipt.target_shot_content_hash != target_shot_content_hash
            or receipt.continuity_constraint_snapshot_hash
            != continuity_constraint_snapshot_hash
            or receipt.provider_min_duration_milliseconds
            != provider_min_duration_milliseconds
            or receipt.provider_max_duration_milliseconds
            != provider_max_duration_milliseconds
            or receipt.motion_analysis_receipt_hash != checked_analysis.content_hash
        ):
            raise _invalid("Existing full-source motion tail does not match replay.")
        reopened_analysis = reopen_full_source_motion_analysis_receipt(
            root, receipt.motion_analysis_receipt_hash
        )
        if reopened_analysis != checked_analysis:
            raise _invalid("Existing full-source motion analysis does not match replay.")
        return PreparedFullSourceMotionTail(
            receipt=receipt,
            tail_asset=existing_tail,
            commit_request=None,
            replayed=True,
        )
    target = next(
        (item for item in project.shots if item.shot_id == target_shot_id), None
    )
    if target is None or (target.revision, target.content_hash) != (
        target_shot_revision,
        target_shot_content_hash,
    ):
        raise _invalid("Full-source motion-tail target Shot is not exact.")
    request, source_asset, terminal, evidence, p6_receipt, provenance = _source_lineage(
        root, project, source_attempt_id
    )
    metadata = source_asset.video_metadata
    assert metadata is not None
    if (
        checked_analysis.source_video_asset_id != source_asset.asset_id
        or checked_analysis.source_video_sha256 != source_asset.sha256
        or checked_analysis.source_frame_count != metadata.frame_count
    ):
        raise _invalid("Full-source motion analysis does not bind the source video.")
    measured_analysis = analyze_full_source_motion(root, source_asset)
    if measured_analysis != checked_analysis:
        raise _invalid(
            "Full-source motion analysis does not match the fixed analyzer output."
        )
    receipt = FullSourceMotionTailReceipt.create(
        source_attempt_id=source_attempt_id,
        source_shot_id=terminal.source_shot_id,
        source_shot_revision=terminal.source_shot_revision,
        source_shot_content_hash=terminal.source_shot_content_hash,
        source_video_asset_id=source_asset.asset_id,
        source_video_sha256=source_asset.sha256,
        source_registry_revision_id=terminal.source_registry.revision_id,
        source_generation_id=request.generation_id,
        source_request_input_hash=request.request_input_hash,
        source_resolved_generation_hash=request.resolved_generation_hash,
        source_provenance_receipt_id=provenance.content_hash,
        source_provenance_receipt_sha256=provenance.content_hash,
        source_p6_acceptance_evidence_id=evidence.content_hash,
        source_p6_acceptance_evidence_sha256=evidence.content_hash,
        source_p6_acceptance_receipt_id=p6_receipt.content_hash,
        source_p6_acceptance_receipt_sha256=p6_receipt.content_hash,
        tail_asset_id=tail_asset_id,
        selection_rule_version="full-source-zero-copy-v1",
        start_timestamp_numerator=0,
        start_timestamp_denominator=metadata.fps_numerator,
        end_timestamp_numerator=terminal.timestamp_numerator,
        end_timestamp_denominator=terminal.timestamp_denominator,
        start_frame_index=0,
        end_frame_index=terminal.frame_index,
        source_fps_numerator=metadata.fps_numerator,
        source_fps_denominator=metadata.fps_denominator,
        source_frame_count=metadata.frame_count,
        source_duration_milliseconds=metadata.duration_milliseconds,
        source_width=metadata.width,
        source_height=metadata.height,
        provider_min_duration_milliseconds=provider_min_duration_milliseconds,
        provider_max_duration_milliseconds=provider_max_duration_milliseconds,
        terminal_frame_evidence=terminal,
        motion_analysis_receipt_hash=checked_analysis.content_hash,
        target_shot_id=target_shot_id,
        target_shot_revision=target_shot_revision,
        target_shot_content_hash=target_shot_content_hash,
        continuity_constraint_snapshot_hash=continuity_constraint_snapshot_hash,
    )
    tail_asset = _tail_asset(
        source_asset=source_asset, terminal=terminal, receipt=receipt
    )
    candidate_registry = _seal_registry(
        project.registry, project.registry.assets + (tail_asset,)
    )
    base_request = prepare_project_registry_commit(
        manifest=project.manifest,
        project=project.project,
        registry=candidate_registry,
        attempt_id=attempt_id,
    )
    candidate_manifest = project.manifest.model_copy(
        update={
            "active_project": base_request.next_project,
            "active_registry": base_request.next_registry,
        }
    )
    candidate_project = project.model_copy(
        update={
            "manifest": candidate_manifest,
            "registry": candidate_registry,
            "asset_paths": {
                **project.asset_paths,
                tail_asset.asset_id: root / tail_asset.artifact_path,
            },
        }
    )
    closure = build_source_closure(candidate_project)
    states = resolve_dependency_state(
        closure.graph,
        build_applied_dependency_evidence(closure.inputs, None),
    ).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=project.manifest.manifest_revision,
        base_dependency_graph=project.manifest.active_dependency_graph,
        candidate_graph=closure.graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=closure.desired_fingerprints,
    )
    receipt_payload = _canonical_json_bytes(receipt)
    analysis_payload = _canonical_json_bytes(checked_analysis)
    graph_payload = _canonical_json_bytes(closure.graph)
    artifacts = base_request.artifacts + (
        PreparedArtifact(
            relative_path=canonical_full_source_motion_analysis_receipt_path(
                checked_analysis.content_hash
            ),
            payload=analysis_payload,
            file_sha256=hashlib.sha256(analysis_payload).hexdigest(),
        ),
        PreparedArtifact(
            relative_path=canonical_full_source_motion_tail_receipt_path(
                receipt.content_hash
            ),
            payload=receipt_payload,
            file_sha256=hashlib.sha256(receipt_payload).hexdigest(),
        ),
        PreparedArtifact(
            relative_path=canonical_dependency_graph_snapshot_path(
                closure.graph.revision_id
            ),
            payload=graph_payload,
            file_sha256=hashlib.sha256(graph_payload).hexdigest(),
        ),
    )
    return PreparedFullSourceMotionTail(
        receipt=receipt,
        tail_asset=tail_asset,
        commit_request=replace(
            base_request,
            artifacts=tuple(
                sorted(artifacts, key=lambda item: item.relative_path.as_posix())
            ),
            dependency_graph_transition=transition,
        ),
    )


def reopen_full_source_motion_analysis_receipt(
    project_root: str | Path,
    receipt_hash: str,
) -> FullSourceMotionAnalysisReceipt:
    """Strictly reopen one canonical quantitative source-motion analysis."""

    root = Path(project_root).resolve(strict=True)
    try:
        path = canonical_full_source_motion_analysis_receipt_path(receipt_hash)
        raw = _read_regular_file_nofollow(root / path, contained_by=root / "state")
        receipt = FullSourceMotionAnalysisReceipt.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _invalid(
            "Could not reopen full-source motion analysis receipt.", str(exc)
        ) from exc
    if (
        receipt.content_hash != receipt_hash
        or raw.data != _canonical_json_bytes(receipt)
        or path
        != canonical_full_source_motion_analysis_receipt_path(receipt.content_hash)
    ):
        raise _invalid("Full-source motion analysis receipt identity is invalid.")
    return receipt


def reopen_full_source_motion_tail_receipt(
    project_root: str | Path,
    receipt_or_asset: str | AssetRecord,
) -> FullSourceMotionTailReceipt:
    """Strictly reopen a canonical zero-copy receipt by hash or tail asset."""

    root = Path(project_root).resolve(strict=True)
    if isinstance(receipt_or_asset, AssetRecord):
        receipt_hash = receipt_or_asset.creation_receipt_id
    elif len(receipt_or_asset) == 64 and all(
        character in "0123456789abcdef" for character in receipt_or_asset
    ):
        receipt_hash = receipt_or_asset
    else:
        loaded = __import__(
            "ai_video.production.project",
            fromlist=["load_production_project"],
        )
        project = loaded.load_production_project(root / "project.yaml")
        asset = next(
            (
                item
                for item in project.registry.assets
                if item.asset_id == receipt_or_asset
            ),
            None,
        )
        if asset is None:
            raise _invalid("Full-source motion-tail asset is not registered.")
        receipt_hash = asset.creation_receipt_id
    try:
        path = canonical_full_source_motion_tail_receipt_path(receipt_hash)
        raw = _read_regular_file_nofollow(root / path, contained_by=root / "state")
        receipt = FullSourceMotionTailReceipt.model_validate_json(raw.data)
    except (OSError, ValueError) as exc:
        raise _invalid(
            "Could not reopen full-source motion-tail receipt.", str(exc)
        ) from exc
    if (
        receipt.content_hash != receipt_hash
        or raw.data != _canonical_json_bytes(receipt)
        or path != canonical_full_source_motion_tail_receipt_path(receipt.content_hash)
    ):
        raise _invalid("Full-source motion-tail receipt identity is invalid.")
    return receipt


def validate_full_source_motion_tail(
    project_root: str | Path,
    project: LoadedProductionProject,
    receipt_or_asset: str | AssetRecord,
) -> FullSourceMotionTailReceipt:
    """Reopen and validate the receipt, active tail asset, and source P6 lineage."""

    root = Path(project_root).resolve(strict=True)
    if root != project.root.resolve(strict=True):
        raise _invalid("Full-source motion-tail project root is not exact.")
    receipt = reopen_full_source_motion_tail_receipt(root, receipt_or_asset)
    analysis = reopen_full_source_motion_analysis_receipt(
        root, receipt.motion_analysis_receipt_hash
    )
    request, source_asset, terminal, evidence, p6_receipt, provenance = _source_lineage(
        root, project, receipt.source_attempt_id
    )
    if (
        request.output_asset_id != receipt.source_video_asset_id
        or source_asset.sha256 != receipt.source_video_sha256
        or terminal != receipt.terminal_frame_evidence
        or evidence.content_hash != receipt.source_p6_acceptance_evidence_sha256
        or p6_receipt.content_hash != receipt.source_p6_acceptance_receipt_sha256
        or provenance.content_hash != receipt.source_provenance_receipt_sha256
        or analysis.source_video_asset_id != receipt.source_video_asset_id
        or analysis.source_video_sha256 != receipt.source_video_sha256
        or analysis.source_frame_count != receipt.source_frame_count
    ):
        raise _invalid("Full-source motion-tail source lineage drifted.")
    if analyze_full_source_motion(root, source_asset) != analysis:
        raise _invalid("Full-source motion analysis no longer reproduces exactly.")
    tail = next(
        (
            item
            for item in project.registry.assets
            if item.asset_id == receipt.tail_asset_id
        ),
        None,
    )
    expected_tail = _tail_asset(
        source_asset=source_asset, terminal=terminal, receipt=receipt
    )
    if tail != expected_tail:
        raise _invalid("Full-source motion-tail registry asset is invalid.")
    receipt.to_c4_motion_tail_evidence(
        registry_revision_id=project.registry.revision_id,
        tail_asset=tail,
    )
    return receipt


__all__ = [
    "analyze_full_source_motion",
    "FullSourceMotionAnalysisReceipt",
    "FullSourceMotionSpanMeasurement",
    "FullSourceMotionTailReceipt",
    "PreparedFullSourceMotionTail",
    "prepare_full_source_motion_tail_commit",
    "reopen_full_source_motion_analysis_receipt",
    "reopen_full_source_motion_tail_receipt",
    "validate_full_source_motion_tail",
]
