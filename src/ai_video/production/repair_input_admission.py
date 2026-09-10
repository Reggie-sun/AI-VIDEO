"""Development-only failed remote video input; no history import or qualification.

Preparation is read-only. Bootstrap owns all writes; Registry reopens the
immutable captured source documents without depending on a mutable foreign root.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel, ToolIdentity
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import AssetRecord, AssetSourceKind, AssetType, ProductionManifest
from ai_video.production.paths import _read_regular_file_nofollow, canonical_video_fetch_artifact_path

REPAIR_INPUT_TOOL = ToolIdentity(name="ai-video-development-repair-input", version="1")
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
        diagnosis = validate_quality_rejection_experience(binding=binding, experience=experience,
            evidence=evidence, request=request, attempt_id=self.source_attempt_id,
            artifact_sha256=self.artifact_sha256, qa_policy=qa_policy, history=history)
        if rejection.diagnosis != diagnosis:
            raise ValueError("Captured diagnosis differs from original evaluator evidence")
        return self


def prepare_repair_input(*, target_root, project, registry, source_root, source_attempt_id,
                         source_sha256, asset_id, usage_license):
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
        if any(a.asset_id == asset_id or a.tool == REPAIR_INPUT_TOOL for a in registry.assets):
            raise ValueError("Admission requires one new, unbound repair input")
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
        provisional = RepairInputAdmissionReceipt.model_construct(**values, content_hash="0" * 64)
        receipt = RepairInputAdmissionReceipt.model_validate({**provisional.model_dump(mode="python"),
            "content_hash": canonical_sha256(provisional.model_dump(mode="json"))})
        asset = AssetRecord(asset_id=asset_id, asset_type=AssetType.VIDEO,
            artifact_path=Path("assets/repair-inputs") / (source_sha256 + ".mp4"),
            sha256=source_sha256, size_bytes=len(media), mime_type="video/mp4",
            source_kind=AssetSourceKind.IMPORTED, tool=REPAIR_INPUT_TOOL,
            input_fingerprint=receipt.content_hash, creation_receipt_id=receipt.content_hash,
            usage_license=usage_license)
        updated = registry.model_copy(update={"assets": (*registry.assets, asset)})
        digest = registry_semantic_sha256(updated)
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
    receipt = RepairInputAdmissionReceipt.model_validate_json(
        _read_regular_file_nofollow(root / path, contained_by=root / "state").data)
    if (record.tool != REPAIR_INPUT_TOOL
            or record.source_kind is not AssetSourceKind.IMPORTED or record.asset_type is not AssetType.VIDEO
            or record.creation_receipt_id != receipt.content_hash or record.input_fingerprint != receipt.content_hash
            or record.asset_id != receipt.asset_id or record.sha256 != receipt.artifact_sha256
            or record.size_bytes != receipt.size_bytes or record.usage_license != receipt.usage_license
            or record.video_metadata is not None or record.mime_type != "video/mp4"
            or record.artifact_path != Path("assets/repair-inputs") / (record.sha256 + ".mp4")):
        raise ValueError("Development repair input differs from its admission receipt")
    return receipt
