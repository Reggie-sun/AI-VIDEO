"""Development-only failed remote video input; no history import or qualification.

Preparation is read-only. Bootstrap owns all writes; Registry reopens the
immutable captured source documents without depending on a mutable foreign root.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel, ToolIdentity
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.video_artifact import VideoProbeReceipt
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    ProductionManifest,
    VideoAssetMetadata,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_video_asset_path,
    canonical_video_fetch_artifact_path,
)
from ai_video.production.video_retime import VideoTimeMap
from ai_video.production.composition_contracts import FixedTransform

REPAIR_INPUT_TOOL = ToolIdentity(name="ai-video-development-repair-input", version="1")
REPAIR_PREVIEW_INPUT_TOOL = ToolIdentity(name=REPAIR_INPUT_TOOL.name, version="2")
REPAIR_AV_PREVIEW_INPUT_TOOL = ToolIdentity(name=REPAIR_INPUT_TOOL.name, version="3")
REPAIR_REPLACEMENT_PREVIEW_INPUT_TOOL = ToolIdentity(name=REPAIR_INPUT_TOOL.name, version="6")
_SHA = r"^[0-9a-f]{64}$"


def repair_input_receipt_path(digest: str) -> Path:
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid repair input receipt identity")
    return Path("state/repair-inputs") / (digest + ".json")


def _source_state(manifest, attempt_id):
    attempt = next((a for a in manifest.attempts if a.attempt_id == attempt_id), None)
    state = attempt.video_generation_state if attempt else None
    if (attempt is None or attempt.status.value != "failed" or state is None
            or state.quality_rejection is None or state.fetch_receipt is None
            or state.local_fetch_receipt is not None or state.execution_binding is None
            or state.latest_observation is None or state.paid_submit_receipt is None
            or state.candidate_video_asset_ids or state.candidate_continuity_asset_ids):
        raise ValueError("Repair input requires a closed, fetched remote quality failure")
    if any(a.status.value in {"outcome_unknown", "interrupted"} for a in manifest.attempts):
        raise ValueError("Source requires explicit recovery")
    return state


def _pointers(state, manifest, qa_pointer):
    return (state.request, state.fetch_receipt, state.quality_rejection,
            state.execution_binding, state.latest_observation, state.paid_submit_receipt,
            *state.generation_experiences, qa_pointer,
            *((manifest.active_paid_provider_budget,) if manifest.active_paid_provider_budget else ()))


class CapturedSourceDocument(StrictModel):
    path: Path
    file_sha256: str = Field(pattern=_SHA)
    text: str

    @model_validator(mode="after")
    def _identity(self):
        if self.path.is_absolute() or ".." in self.path.parts or not self.path.parts or self.path.parts[0] != "state":
            raise ValueError("Captured source document path must be contained in state")
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.file_sha256:
            raise ValueError("Captured source document bytes changed")
        return self


class RepairInputAdmissionReceipt(StrictModel):
    contract_version: Literal["development-repair-input/1"] = "development-repair-input/1"
    qualification: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    target_project_id: str
    target_project_hash: str = Field(pattern=_SHA)
    asset_id: str
    artifact_sha256: str = Field(pattern=_SHA)
    size_bytes: int = Field(strict=True, gt=0)
    usage_license: str = Field(min_length=1)
    source_attempt_id: str
    source_manifest_json: str
    source_manifest_sha256: str = Field(pattern=_SHA)
    documents: tuple[CapturedSourceDocument, ...]
    content_hash: str = Field(pattern=_SHA)

    @model_validator(mode="after")
    def _source_chain(self):
        if self.contract_version == "development-qualification-preview/1":
            from ai_video.production.qualification_preview_input import validate_qualification_capture
            validate_qualification_capture(self)
            return self
        from ai_video.production.video import (
            ResolvedVideoGenerationRequest, VideoFetchReceipt, VideoTaskObservation, VideoSubmission,
        )
        from ai_video.production.generation_rejection import (
            GenerationQualityRejectionReceipt, validate_quality_rejection_experience,
        )
        from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
        from ai_video.production.generation_experience import GenerationExperience
        from ai_video.production.models import QaPolicy
        from ai_video.production.paid_provider import PaidProviderSubmitReceipt

        if self.content_hash != canonical_sha256(self.model_dump(mode="json")):
            raise ValueError("Repair input admission seal changed")
        if hashlib.sha256(self.source_manifest_json.encode("utf-8")).hexdigest() != self.source_manifest_sha256:
            raise ValueError("Source Manifest bytes changed")
        manifest = ProductionManifest.model_validate_json(self.source_manifest_json)
        state = _source_state(manifest, self.source_attempt_id)
        if self.target_project_id == manifest.project_id:
            raise ValueError("Development input needs an independent project identity")
        documents = {d.path: d for d in self.documents}
        rejection_document = documents.get(state.quality_rejection.path)
        if rejection_document is None:
            raise ValueError("Missing captured quality rejection")
        rejection = GenerationQualityRejectionReceipt.model_validate_json(rejection_document.text)
        pointers = _pointers(state, manifest, rejection.qa_policy)
        if len(documents) != len(self.documents) or set(documents) != {p.path for p in pointers}:
            raise ValueError("Repair source document closure is incomplete")

        def reopen(pointer, model):
            doc = documents[pointer.path]
            if doc.file_sha256 != pointer.file_sha256:
                raise ValueError("Source document differs from its Manifest pointer")
            return model.model_validate_json(doc.text)

        # Verify every captured pointer, including the historical budget snapshot.
        for pointer in pointers:
            if documents[pointer.path].file_sha256 != pointer.file_sha256:
                raise ValueError("Captured source pointer changed")
        request = reopen(state.request, ResolvedVideoGenerationRequest)
        fetch = reopen(state.fetch_receipt, VideoFetchReceipt)
        rejection = reopen(state.quality_rejection, GenerationQualityRejectionReceipt)
        binding = reopen(state.execution_binding, GenerationDecisionExecutionBinding)
        observation = reopen(state.latest_observation, VideoTaskObservation)
        submit = reopen(state.paid_submit_receipt, PaidProviderSubmitReceipt)
        submission = VideoSubmission.from_paid_submit_receipt(resolved=request, receipt=submit)
        binding.validate_request(request)
        qa_policy = reopen(rejection.qa_policy, QaPolicy)
        experiences = tuple(reopen(p, GenerationExperience) for p in state.generation_experiences)
        history = tuple(e for x in experiences for e in x.evidence)
        experience = next((x for x in experiences if canonical_sha256(x.model_dump(mode="json"))
                           == rejection.experience_content_hash), None)
        evidence = next((e for e in history if e.evidence_hash == rejection.evidence_hash), None)
        if (request.request_input_hash != state.request.request_input_hash
                or request.desired_generation_fingerprint != state.request.request_receipt_fingerprint
                or request.generation_id != state.request.generation_id
                or request.resolved_generation_hash != state.request.resolved_generation_hash
                or request.output_asset_id != state.request.output_asset_id
                or rejection.content_hash != state.quality_rejection.content_hash
                or rejection.attempt_id != self.source_attempt_id
                or rejection.request_fingerprint != request.request_input_hash
                or rejection.artifact_sha256 != self.artifact_sha256
                or rejection.artifact_size_bytes != self.size_bytes
                or fetch.artifact_sha256 != self.artifact_sha256 or fetch.size_bytes != self.size_bytes
                or fetch.fetch_fingerprint != state.fetch_receipt.fetch_fingerprint
                or fetch.artifact_sha256 != state.fetch_receipt.artifact_sha256
                or fetch.size_bytes != state.fetch_receipt.artifact_size_bytes
                or fetch.content_type != "video/mp4"
                or fetch.observation_fingerprint != observation.observation_fingerprint
                or fetch.submission_fingerprint != submission.submission_fingerprint
                or observation.submission_fingerprint != submission.submission_fingerprint
                or fetch.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint
                or submit.submit_receipt_fingerprint != state.paid_submit_receipt.submit_receipt_fingerprint
                or observation.observation_fingerprint != state.latest_observation.observation_fingerprint
                or observation.provider_file_id != fetch.provider_file_id
                or observation.provider_file_id != state.provider_file_id
                or observation.state.value != "succeeded"
                or submit.attempt_id != self.source_attempt_id
                or binding.binding_hash != state.execution_binding.binding_hash
                or qa_policy.content_hash != rejection.qa_policy.content_hash
                or not verify_artifact_hash(qa_policy)
                or qa_policy.policy_id != rejection.qa_policy.policy_id
                or qa_policy.policy_version != rejection.qa_policy.policy_version
                or experience is None or evidence is None or evidence not in experience.evidence
                or evidence.attempt_id != self.source_attempt_id or evidence.artifact_sha256 != self.artifact_sha256
                or evidence.request_hash != request.request_input_hash):
            raise ValueError("Repair input does not preserve the exact failed source chain")
        prior_sources = tuple(s for x in experiences if x != experience for s in x.evaluation_sources)
        diagnosis = validate_quality_rejection_experience(binding=binding, experience=experience,
            evidence=evidence, request=request, attempt_id=self.source_attempt_id,
            artifact_sha256=self.artifact_sha256, qa_policy=qa_policy, history=history,
            evaluation_sources=prior_sources)
        if rejection.diagnosis != diagnosis:
            raise ValueError("Captured diagnosis differs from original evaluator evidence")
        if rejection.schema_version == "generation-quality-rejection/2":
            from ai_video.production.generation_rejection import validate_abandoned_result

            validate_abandoned_result(
                rejection,
                experience=experience,
                evidence=evidence,
                history=history,
                evaluation_sources=prior_sources,
            )
        if self.contract_version in {
            "development-repair-input/2",
            "development-repair-input/3",
            "development-repair-input/4",
            "development-repair-input/5",
            "development-repair-input/6",
        }:
            _validate_preview_probe(
                self.preview_probe,
                request=request,
                fetch=fetch,
                artifact_sha256=self.artifact_sha256,
                size_bytes=self.size_bytes,
            )
            if (self.preview_use.trim_start_frame + self.preview_use.trim_duration_frames
                    > self.preview_probe.measured.frame_count):
                raise ValueError("Development repair preview trim exceeds measured source frames")
            if self.contract_version == "development-repair-input/6":
                if (self.preview_use.scope != "replacement_audio_preview"
                        or self.preview_use.source_time_map.contract_version != "video-time-map/1"):
                    raise ValueError("Development repair input/6 requires explicitly replaced source audio")
            elif (self.contract_version == "development-repair-input/2"
                    or (self.contract_version in {"development-repair-input/4", "development-repair-input/5"}
                        and self.preview_use.scope == "muted_visual_preview")):
                if (self.preview_use.scope != "muted_visual_preview"
                        or self.preview_use.source_time_map.contract_version != "video-time-map/1"):
                    raise ValueError("Development repair input/2 cannot carry native A/V retiming")
            elif (self.preview_use.scope != "retimed_av_preview"
                  or self.preview_use.source_time_map.contract_version != "video-time-map/2"
                  or self.preview_probe.measured.audio_stream_count != 1):
                raise ValueError("Development repair input/3 requires one exact native audio stream")
        return self


class RepairPreviewUse(StrictModel):
    """One sealed visual, native A/V, or normal-speed replacement-audio use."""

    shot_id: str = Field(min_length=1)
    asset_role: str = Field(min_length=1)
    trim_start_frame: int = Field(strict=True, ge=0)
    trim_duration_frames: int = Field(strict=True, gt=0)
    source_time_map: VideoTimeMap
    transform: FixedTransform
    scope: Literal["muted_visual_preview", "retimed_av_preview", "replacement_audio_preview"] = "muted_visual_preview"

    @model_validator(mode="after")
    def _exact_source_window_and_mute(self):
        expected = {
            "muted_visual_preview": ("video-time-map/1", "mute"),
            "retimed_av_preview": ("video-time-map/2", "retime_preserve_pitch"),
            "replacement_audio_preview": ("video-time-map/1", "mute"),
        }[self.scope]
        if (self.source_time_map.contract_version, self.source_time_map.audio_policy) != expected:
            raise ValueError("Development repair preview scope differs from its exact time-map version")
        if self.source_time_map.source_duration_frames != self.trim_duration_frames:
            raise ValueError("Development repair preview time map must cover its exact trim")
        if self.scope == "replacement_audio_preview" and any(
            point.source_frame != point.output_frame for point in self.source_time_map.points
        ):
            raise ValueError("Replacement audio preview requires normal-speed video")
        return self


class RepairPreviewInputAdmissionReceipt(RepairInputAdmissionReceipt):
    contract_version: Literal["development-repair-input/2"] = "development-repair-input/2"
    preview_use: RepairPreviewUse
    preview_probe: VideoProbeReceipt


class RepairAudioPreviewInputAdmissionReceipt(RepairPreviewInputAdmissionReceipt):
    contract_version: Literal["development-repair-input/3"] = "development-repair-input/3"


class RepairReplacementPreviewInputAdmissionReceipt(RepairPreviewInputAdmissionReceipt):
    contract_version: Literal["development-repair-input/6"] = "development-repair-input/6"


def _preview_input_tool(receipt):
    if receipt.contract_version == "development-qualification-preview/1":
        return ToolIdentity(name=REPAIR_INPUT_TOOL.name, version="7")
    if receipt.contract_version == "development-repair-input/6":
        return REPAIR_REPLACEMENT_PREVIEW_INPUT_TOOL
    if receipt.contract_version == "development-repair-input/3":
        return REPAIR_AV_PREVIEW_INPUT_TOOL
    return REPAIR_PREVIEW_INPUT_TOOL


def _validate_preview_probe(probe, *, request, fetch, artifact_sha256, size_bytes):
    from ai_video.production.video_artifact import VideoProbeReceipt

    probe = VideoProbeReceipt.model_validate(probe.model_dump(mode="python"))
    measured = probe.measured
    if (
        probe.request_receipt_fingerprint != request.desired_generation_fingerprint
        or probe.resolved_generation_hash != request.resolved_generation_hash
        or probe.fetch_fingerprint != fetch.fetch_fingerprint
        or measured.container_name != "mp4"
        or measured.artifact_sha256 != artifact_sha256
        or measured.size_bytes != size_bytes
        or probe.continuity_evidence is not None
        or probe.commercial_evidence is not None
        or probe.nominal_endpoint_recovery is not None
    ):
        raise ValueError("Development preview probe differs from the exact fetched failed bytes")


def _preview_video_metadata(receipt: RepairPreviewInputAdmissionReceipt) -> VideoAssetMetadata:
    measured = receipt.preview_probe.measured
    return VideoAssetMetadata(
        container_name=measured.container_name,
        codec_name=measured.codec_name,
        width=measured.width,
        height=measured.height,
        fps_numerator=measured.fps_numerator,
        fps_denominator=measured.fps_denominator,
        duration_milliseconds=measured.duration_milliseconds,
        frame_count=measured.frame_count,
        probe_receipt_id=receipt.preview_probe.content_hash,
        request_receipt_fingerprint=receipt.preview_probe.request_receipt_fingerprint,
        resolved_generation_hash=receipt.preview_probe.resolved_generation_hash,
        provenance_receipt_id=receipt.content_hash,
    )


def prepare_repair_input(*, target_root, project, registry, source_root, source_attempt_id,
                         source_sha256, asset_id, usage_license, preview_use=None,
                         preview_probe=None):
    """Capture one checked source, not a synthetic history or source-use finding."""
    from ai_video.production._state_commit_common import _canonical_json_bytes, _state_invalid
    from ai_video.production._state_commit_contracts import PreparedArtifact
    from ai_video.production.project import load_production_project
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production.generation_rejection import GenerationQualityRejectionReceipt

    try:
        root = Path(source_root).resolve(strict=True)
        target = Path(target_root).resolve(strict=True)
        if root.is_relative_to(target) or target.is_relative_to(root):
            raise ValueError("Source and target roots must not overlap")
        loaded = load_production_project(root / "project.yaml")
        raw = _read_regular_file_nofollow(root / "state/manifest.json", contained_by=root / "state").data
        manifest = ProductionManifest.model_validate_json(raw)
        if manifest != loaded.manifest:
            raise ValueError("Source changed during admission")
        state = _source_state(manifest, source_attempt_id)
        if state.fetch_receipt.artifact_sha256 != source_sha256:
            raise ValueError("Source hash does not match selected fetch")
        if any(a.asset_id == asset_id or a.tool.name == REPAIR_INPUT_TOOL.name for a in registry.assets):
            raise ValueError("Admission requires one new, unbound repair input")
        if (preview_use is None) != (preview_probe is None):
            raise ValueError("Retimed preview admission requires both preview use and exact probe")
        rejection = GenerationQualityRejectionReceipt.model_validate_json(_read_regular_file_nofollow(
            root / state.quality_rejection.path, contained_by=root / "state").data)
        pointers = _pointers(state, manifest, rejection.qa_policy)
        docs = tuple(CapturedSourceDocument(path=p.path, file_sha256=p.file_sha256,
            text=_read_regular_file_nofollow(root / p.path, contained_by=root / "state").data.decode("utf-8"))
            for p in pointers)
        media = _read_regular_file_nofollow(root / canonical_video_fetch_artifact_path(source_sha256),
                                          contained_by=root / "state").data
        if hashlib.sha256(media).hexdigest() != source_sha256:
            raise ValueError("Source media bytes changed")
        values = dict(target_project_id=project.project_id, target_project_hash=project.content_hash,
            asset_id=asset_id, artifact_sha256=source_sha256, size_bytes=len(media), usage_license=usage_license,
            source_attempt_id=source_attempt_id, source_manifest_json=raw.decode("utf-8"),
            source_manifest_sha256=hashlib.sha256(raw).hexdigest(), documents=docs)
        if preview_use is None:
            receipt_type = RepairInputAdmissionReceipt
        elif preview_use.scope == "retimed_av_preview":
            receipt_type = RepairAudioPreviewInputAdmissionReceipt
        elif preview_use.scope == "replacement_audio_preview":
            receipt_type = RepairReplacementPreviewInputAdmissionReceipt
        else:
            receipt_type = RepairPreviewInputAdmissionReceipt
        receipt_values = dict(values)
        if preview_use is not None:
            receipt_values.update(preview_use=preview_use, preview_probe=preview_probe)
        provisional = receipt_type.model_construct(**receipt_values, content_hash="0" * 64)
        receipt = receipt_type.model_validate({**provisional.model_dump(mode="python"),
            "content_hash": canonical_sha256(provisional.model_dump(mode="json"))})
        preview = isinstance(receipt, RepairPreviewInputAdmissionReceipt)
        measured = receipt.preview_probe.measured if preview else None
        asset_path = (canonical_video_asset_path(source_sha256) if preview else
                      Path("assets/repair-inputs") / (source_sha256 + ".mp4"))
        preview_tool = _preview_input_tool(receipt)
        asset = AssetRecord(asset_id=asset_id, asset_type=AssetType.VIDEO,
            artifact_path=asset_path,
            sha256=source_sha256, size_bytes=len(media), mime_type="video/mp4",
            duration_seconds=(measured.duration_milliseconds / 1000 if measured else None),
            width=(measured.width if measured else None), height=(measured.height if measured else None),
            source_kind=AssetSourceKind.IMPORTED,
            tool=preview_tool if preview else REPAIR_INPUT_TOOL,
            input_fingerprint=receipt.content_hash, creation_receipt_id=receipt.content_hash,
            usage_license=usage_license,
            video_metadata=_preview_video_metadata(receipt) if preview else None)
        updated = registry.model_copy(update={"assets": (*registry.assets, asset)})
        if preview and updated.schema_version != "2.2":
            updated = updated.model_copy(update={"schema_version": "2.2"})
        digest = registry_semantic_sha256(updated)
        if preview:
            updated = AssetRegistrySnapshot.model_validate({
                **updated.model_dump(mode="python"),
                "revision_id": digest,
                "content_hash": digest,
            })
        else:
            updated = updated.model_copy(update={"revision_id": digest, "content_hash": digest})
        payload = _canonical_json_bytes(receipt)
        artifacts = (PreparedArtifact(asset.artifact_path, media, source_sha256),
            PreparedArtifact(repair_input_receipt_path(receipt.content_hash), payload,
                             hashlib.sha256(payload).hexdigest()))
        if _read_regular_file_nofollow(root / "state/manifest.json", contained_by=root / "state").data != raw:
            raise ValueError("Source changed during admission")
        return updated, artifacts
    except (OSError, ValueError, StopIteration) as exc:
        raise _state_invalid("Development repair input admission is invalid.", str(exc)) from exc


def verify_repair_input(record, root):
    """Strict Registry reopen: no foreign reads, network, writes or acceptance."""
    path = repair_input_receipt_path(record.creation_receipt_id)
    payload = _read_regular_file_nofollow(root / path, contained_by=root / "state").data
    try:
        version = json.loads(payload).get("contract_version")
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Development repair input receipt is invalid") from exc
    if version == "development-repair-input/4":
        from ai_video.production.video_cleanup_admission import verify_cleaned_repair_input
        return verify_cleaned_repair_input(record, root, payload)
    if version == "development-repair-input/5":
        from ai_video.production.video_cleanup_viewing_admission import verify_viewing_repair_input
        return verify_viewing_repair_input(record, root, payload)
    receipt_type = {
        "development-repair-input/1": RepairInputAdmissionReceipt,
        "development-repair-input/2": RepairPreviewInputAdmissionReceipt,
        "development-repair-input/3": RepairAudioPreviewInputAdmissionReceipt,
        "development-repair-input/6": RepairReplacementPreviewInputAdmissionReceipt,
    }.get(version)
    if version == "development-qualification-preview/1":
        from ai_video.production.qualification_preview_input import QualificationPreviewInputReceipt
        receipt_type = QualificationPreviewInputReceipt
    if receipt_type is None:
        raise ValueError("Development repair input version is unsupported")
    receipt = receipt_type.model_validate_json(payload)
    common_mismatch = (
        record.source_kind is not AssetSourceKind.IMPORTED or record.asset_type is not AssetType.VIDEO
        or record.creation_receipt_id != receipt.content_hash or record.input_fingerprint != receipt.content_hash
        or record.asset_id != receipt.asset_id or record.sha256 != receipt.artifact_sha256
        or record.size_bytes != receipt.size_bytes or record.usage_license != receipt.usage_license
        or record.mime_type != "video/mp4" or record.audio_metadata is not None
        or record.caption_metadata is not None or record.egress.remote or record.cost_receipt_id is not None
    )
    if isinstance(receipt, RepairPreviewInputAdmissionReceipt):
        expected_metadata = _preview_video_metadata(receipt)
        expected_tool = _preview_input_tool(receipt)
        if (record.tool != expected_tool
                or record.video_metadata != expected_metadata
                or record.width != expected_metadata.width or record.height != expected_metadata.height
                or record.duration_seconds != expected_metadata.duration_milliseconds / 1000
                or record.artifact_path != canonical_video_asset_path(record.sha256)
                or common_mismatch):
            raise ValueError("Development repair preview differs from its exact admission receipt")
    elif (record.tool != REPAIR_INPUT_TOOL
            or record.source_kind is not AssetSourceKind.IMPORTED or record.asset_type is not AssetType.VIDEO
            or record.creation_receipt_id != receipt.content_hash or record.input_fingerprint != receipt.content_hash
            or record.asset_id != receipt.asset_id or record.sha256 != receipt.artifact_sha256
            or record.size_bytes != receipt.size_bytes or record.usage_license != receipt.usage_license
            or record.video_metadata is not None or record.mime_type != "video/mp4"
            or record.artifact_path != Path("assets/repair-inputs") / (record.sha256 + ".mp4")):
        raise ValueError("Development repair input differs from its admission receipt")
    return receipt


def is_repair_input_record(record, root: Path | None = None) -> bool:
    """Recognize both preserved v1 captures and sealed v2 preview captures."""
    if (record.tool.name == REPAIR_INPUT_TOOL.name
            or record.artifact_path.is_relative_to(Path("assets/repair-inputs"))):
        return True
    if root is None:
        return False
    try:
        receipt_path = repair_input_receipt_path(record.creation_receipt_id)
    except ValueError:
        return False
    try:
        _read_regular_file_nofollow(Path(root) / receipt_path, contained_by=Path(root) / "state")
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return True
    return True


def allows_repair_preview_layer(loaded, layer, shot) -> bool:
    """Permit only the exact versioned capture use sealed for this unbound preview."""
    asset = next((item for item in loaded.registry.assets if item.asset_id == layer.asset_id), None)
    if asset is None or not is_repair_input_record(asset, loaded.root):
        return False
    receipt = verify_repair_input(asset, loaded.root)
    if not isinstance(receipt, RepairPreviewInputAdmissionReceipt):
        raise ValueError("Legacy development repair input cannot be used as a retimed preview")
    use = receipt.preview_use
    layer_time_map = None if use.scope == "replacement_audio_preview" else use.source_time_map
    if (loaded.project.project_id != receipt.target_project_id
            or loaded.project.content_hash != receipt.target_project_hash):
        raise ValueError("Development preview target project differs from its admission")
    current_shot = next((item for item in loaded.shots if item.shot_id == use.shot_id), None)
    if (current_shot is None or shot.shot_id != use.shot_id
            or shot.content_hash != current_shot.content_hash
            or shot.revision != current_shot.revision):
        raise ValueError("Development preview target Shot differs from its admission")
    if (
        layer.shot_id != use.shot_id
        or layer.asset_id != asset.asset_id
        or layer.asset_role != use.asset_role
        or layer.trim_start_frame != use.trim_start_frame
        or layer.trim_duration_frames != use.trim_duration_frames
        or layer.source_time_map != layer_time_map
        or layer.transform != use.transform
        or layer.trim_start_frame + layer.trim_duration_frames > receipt.preview_probe.measured.frame_count
    ):
        raise ValueError("Composition layer differs from the sealed development preview use")
    return True


def require_production_render_sources(root, registry_pointer, timeline) -> None:
    """A caller cannot promote captured bytes by relabeling a preview timeline."""
    from ai_video.production.registry import load_asset_registry

    root = Path(root)
    raw = _read_regular_file_nofollow(root / registry_pointer.path, contained_by=root / "assets")
    if raw.file_sha256 != registry_pointer.file_sha256:
        raise ValueError("Render Registry pointer bytes changed")
    registry, _ = load_asset_registry(registry_pointer.path, root, root / "assets")
    if (registry.revision_id != registry_pointer.revision_id
            or registry.content_hash != registry_pointer.content_hash):
        raise ValueError("Render Registry pointer identity changed")
    captured = {a.sha256 for a in registry.assets if is_repair_input_record(a, root)}
    if captured.intersection(s.asset_sha256 for s in timeline.visual_spans):
        raise ValueError("Development repair preview bytes cannot be activated for Production")
