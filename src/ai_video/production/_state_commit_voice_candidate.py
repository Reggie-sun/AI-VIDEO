from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from ai_video.production.audio import (
    PreparedAudioImport,
    VoiceCallAuthorization,
    VoiceCostReceipt,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoiceProvenanceReceipt,
    VoiceProviderResult,
    _result_fingerprint,
)
from ai_video.production.captions import (
    CaptionImportRequest,
    _canonical_track_bytes,
    caption_timing_fingerprint,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    AudioAssetMetadata,
    AudioSource,
    CaptionAssetMetadata,
    CaptionTrack,
    EgressMetadata,
    ProductionProject,
    SourceReference,
    StateCommitAttempt,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_audio_asset_path,
)
from ai_video.production.registry import registry_semantic_sha256

from ._state_commit_common import (
    _canonical_json_bytes,
    _state_commit_failed,
    _state_invalid,
    prepare_audio_registry_commit,
)
from ._state_commit_contracts import (
    PreparedArtifact,
    PreparedVoiceCandidate,
    StateCommitRequest,
)


class _StateCommitVoiceCandidateMixin:
    def _prepare_voice_activation_request(
        self,
        request: VoiceGenerationRequest,
        preview: VoiceGenerationPreview,
        authorization: VoiceCallAuthorization,
        result: VoiceProviderResult,
        prepared: PreparedVoiceCandidate,
    ) -> tuple[StateCommitRequest, tuple[str, ...], tuple[str, ...]]:
        self._validate_voice_provider_result(request, preview, authorization, result)
        if not isinstance(prepared, PreparedVoiceCandidate) or not isinstance(
            prepared.audio, PreparedAudioImport
        ):
            raise _state_invalid("Voice candidate preparer returned an unsafe capability.")
        audio = prepared.audio
        probe = audio.probe
        if (
            audio.payload != result.audio_bytes
            or probe.file_sha256 != result.audio_sha256
            or probe.size_bytes != len(result.audio_bytes)
            or probe.mime_type != result.content_type
            or probe.codec_name != request.output_codec
            or probe.sample_rate_hz != request.output_sample_rate_hz
            or probe.channels != request.output_channels
        ):
            raise _state_invalid("Prepared voice audio does not match the exact provider result.")

        paths = self.voice_attempt_paths(request.attempt_id)
        provenance_bytes = _canonical_json_bytes(result.provenance_receipt)
        cost_bytes = _canonical_json_bytes(result.cost_receipt)
        provenance_hash = hashlib.sha256(provenance_bytes).hexdigest()
        cost_hash = hashlib.sha256(cost_bytes).hexdigest()
        alignment_hash = result.alignment_receipt_sha256
        audio_id = f"voice-{request.attempt_id}"
        audio_record = AssetRecord(
            asset_id=audio_id,
            asset_type=AssetType.VOICE,
            artifact_path=canonical_audio_asset_path(result.audio_sha256),
            sha256=result.audio_sha256,
            size_bytes=len(result.audio_bytes),
            mime_type=result.content_type,
            source_kind=AssetSourceKind.GENERATED,
            tool=result.provenance_receipt.adapter,
            input_artifact_ids=request.input_artifact_ids,
            input_fingerprint=request.input_fingerprint,
            creation_receipt_id=f"voice-result-{result.result_fingerprint}",
            usage_license=result.provenance_receipt.license_policy_decision,
            egress=EgressMetadata(
                remote=True,
                destination=authorization.destination,
                authorization_receipt_id=request.egress_authorization_receipt_id,
                request_fingerprint=request.voice_request_fingerprint,
                payload_fingerprint=request.script_hash,
                retention_mode=result.provenance_receipt.retention_mode,
                provider_policy_snapshot_id=result.provenance_receipt.policy_receipt_id,
            ),
            cost_receipt_id=f"cost-{cost_hash}",
            audio_metadata=AudioAssetMetadata(
                audio_kind=request.audio_kind,
                source=AudioSource(
                    kind=AssetSourceKind.GENERATED,
                    provider_or_tool=result.provenance_receipt.adapter,
                    input_artifact_ids=request.input_artifact_ids,
                    input_fingerprint=request.input_fingerprint,
                ),
                speaker_id=request.speaker_id,
                voice_id=request.voice_id,
                language=request.language,
                script_hash=request.script_hash,
                duration_samples=probe.duration_samples,
                sample_rate_hz=probe.sample_rate_hz,
                channels=probe.channels,
                channel_layout=probe.channel_layout,
                codec_name=probe.codec_name,
                loudness=probe.loudness,
                provenance_receipt_id=f"provenance-{provenance_hash}",
                alignment_receipt_id=f"alignment-{alignment_hash}",
            ),
        )
        asset_artifacts = [
            PreparedArtifact(audio_record.artifact_path, audio.payload, result.audio_sha256)
        ]
        new_records = [audio_record]
        caption_ids: tuple[str, ...] = ()
        if prepared.caption is not None:
            assert prepared.caption_asset_record is not None
            caption = prepared.caption
            supplied = prepared.caption_asset_record
            caption_id = f"caption-{request.attempt_id}"
            try:
                CaptionImportRequest(
                    caption_track=caption.caption_track,
                    track_bytes=caption.track_bytes,
                    track_sha256=caption.track_sha256,
                    style_reference=caption.style_reference,
                    style_bytes=caption.style_bytes,
                    style_sha256=caption.style_sha256,
                )
            except ValidationError as exc:
                raise _state_invalid("Prepared caption bytes are not canonical.", str(exc)) from exc
            track = caption.caption_track
            expected_caption_record = AssetRecord(
                asset_id=caption_id,
                asset_type=AssetType.CAPTION,
                artifact_path=Path(f"assets/captions/{caption.track_sha256}.json"),
                sha256=caption.track_sha256,
                size_bytes=len(caption.track_bytes),
                mime_type="application/json",
                source_kind=AssetSourceKind.DERIVED,
                tool=result.provenance_receipt.adapter,
                input_artifact_ids=(audio_id,),
                input_fingerprint=result.audio_sha256,
                creation_receipt_id=track.creation_receipt_id,
                usage_license=result.provenance_receipt.license_policy_decision,
                caption_metadata=CaptionAssetMetadata(
                    caption_track_id=track.caption_track_id,
                    language=track.language,
                    source_audio_asset_id=audio_id,
                    source_audio_sha256=result.audio_sha256,
                    script_hash=track.script_hash,
                    transcript_hash=track.transcript_hash,
                    segment_count=len(track.segments),
                    word_count=sum(len(item.words or ()) for item in track.segments),
                    segmentation_policy_id=track.segmentation_policy.policy_id,
                    segmentation_policy_version=track.segmentation_policy.policy_version,
                    alignment_receipt_id=track.alignment_receipt_id,
                    timing_fingerprint=track.timing_fingerprint,
                    style_reference_id=(
                        caption.style_reference.artifact_id
                        if caption.style_reference is not None
                        else None
                    ),
                    style_content_hash=(
                        caption.style_reference.content_hash
                        if caption.style_reference is not None
                        else None
                    ),
                    style_reference_revision=(
                        caption.style_reference.revision
                        if caption.style_reference is not None
                        else None
                    ),
                ),
            )
            if (
                supplied != expected_caption_record
                or track.source_audio_asset_id != audio_id
                or track.source_audio_sha256 != result.audio_sha256
                or track.script_hash != request.script_hash
                or track.transcript_hash != request.script_hash
                or track.source_sample_rate_hz != request.output_sample_rate_hz
                or track.language != request.language
                or track.alignment_receipt_id
                != f"alignment-{result.alignment_receipt_sha256}"
                or track.creation_receipt_id
                != f"caption-result-{result.result_fingerprint}"
                or track.source_provenance
                != (
                    SourceReference(
                        kind="derived",
                        reference=f"alignment-{result.alignment_receipt_sha256}",
                    ),
                )
                or track.timing_fingerprint != caption_timing_fingerprint(track)
            ):
                raise _state_invalid("Prepared caption identity does not match generated voice.")
            new_records.append(supplied)
            asset_artifacts.append(
                PreparedArtifact(supplied.artifact_path, caption.track_bytes, caption.track_sha256)
            )
            if caption.style_reference is not None:
                assert caption.style_bytes is not None and caption.style_sha256 is not None
                asset_artifacts.append(
                    PreparedArtifact(
                        caption.style_reference.path,
                        caption.style_bytes,
                        caption.style_sha256,
                    )
                )
            caption_ids = (caption_id,)

        manifest = self._read_manifest()
        project_snapshot = _read_regular_file_nofollow(
            self._project_root / request.base_project.path,
            contained_by=self._project_root,
        )
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / request.base_registry.path,
            contained_by=self._project_root,
        )
        try:
            project = ProductionProject.model_validate(yaml.safe_load(project_snapshot.data))
            base_registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError, yaml.YAMLError) as exc:
            raise _state_invalid("Voice base project or registry could not be reopened.", str(exc)) from exc
        ordered_new = tuple(sorted(new_records, key=lambda item: item.asset_id))
        registry = AssetRegistrySnapshot(
            schema_version="2.1",
            revision_id="0" * 64,
            content_hash="0" * 64,
            assets=base_registry.assets + ordered_new,
        )
        registry_hash = registry_semantic_sha256(registry)
        registry = registry.model_copy(
            update={"revision_id": registry_hash, "content_hash": registry_hash}
        )
        base_commit = prepare_audio_registry_commit(
            manifest=manifest,
            project=project,
            base_registry=base_registry,
            registry=registry,
            attempt_id=request.attempt_id,
            artifacts=tuple(asset_artifacts),
            active_project_artifact=PreparedArtifact(
                request.base_project.path, project_snapshot.data, project_snapshot.file_sha256
            ),
        )
        outcome_payload = (
            json.dumps(
                {
                    "request_id": result.request_id,
                    "request_fingerprint": result.request_fingerprint,
                    "preview_fingerprint": result.preview_fingerprint,
                    "authorization_fingerprint": result.authorization_fingerprint,
                    "result_fingerprint": result.result_fingerprint,
                    "provider_request_id": result.provider_request_id,
                    "provider_trace_id": result.provider_trace_id,
                    "audio_sha256": result.audio_sha256,
                    "alignment_receipt_sha256": result.alignment_receipt_sha256,
                    "content_type": result.content_type,
                    "policy_receipt_id": result.provenance_receipt.policy_receipt_id,
                    "retention_mode": result.provenance_receipt.retention_mode,
                    "terminal_status": result.terminal_status,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        evidence = (
            *self._reopen_voice_evidence(request.attempt_id, include_intent=True),
            PreparedArtifact(
                paths.alignment_path.relative_to(self._project_root),
                result.alignment_receipt_bytes,
                alignment_hash,
            ),
            PreparedArtifact(
                paths.cost_path.relative_to(self._project_root), cost_bytes, cost_hash
            ),
            PreparedArtifact(
                paths.provenance_path.relative_to(self._project_root),
                provenance_bytes,
                provenance_hash,
            ),
            PreparedArtifact(
                paths.outcome_path.relative_to(self._project_root),
                outcome_payload,
                hashlib.sha256(outcome_payload).hexdigest(),
            ),
        )
        by_path = {
            item.relative_path: item for item in (*base_commit.artifacts, *evidence)
        }
        commit = StateCommitRequest(
            attempt_id=request.attempt_id,
            operation="voice_generation",
            expected_manifest_revision=manifest.manifest_revision,
            artifacts=tuple(sorted(by_path.values(), key=lambda item: item.relative_path.as_posix())),
            next_project=base_commit.next_project,
            next_registry=base_commit.next_registry,
        )
        return commit, (audio_id,), caption_ids

    def _validate_voice_activation_graph(
        self,
        commit: StateCommitRequest,
        attempt: StateCommitAttempt,
        candidate_registry: AssetRegistrySnapshot,
        audio_asset_ids: tuple[str, ...],
        caption_asset_ids: tuple[str, ...],
    ) -> str | None:
        if len(set(caption_asset_ids)) != len(caption_asset_ids):
            raise _state_invalid("Voice candidate graph contains duplicate caption asset IDs.")
        paths = self.voice_attempt_paths(commit.attempt_id)
        artifacts = {item.relative_path: item for item in commit.artifacts}
        evidence_paths = {
            path.relative_to(self._project_root)
            for path in (
                paths.request_path,
                paths.preview_path,
                paths.authorization_path,
                paths.submit_intent_path,
                paths.alignment_path,
                paths.cost_path,
                paths.provenance_path,
                paths.outcome_path,
            )
        }
        if not evidence_paths.issubset(artifacts):
            raise _state_invalid("Voice candidate graph is missing durable lifecycle evidence.")
        try:
            voice_request = VoiceGenerationRequest.model_validate_json(
                artifacts[paths.request_path.relative_to(self._project_root)].payload
            )
            preview = VoiceGenerationPreview.model_validate_json(
                artifacts[paths.preview_path.relative_to(self._project_root)].payload
            )
            authorization = VoiceCallAuthorization.model_validate_json(
                artifacts[paths.authorization_path.relative_to(self._project_root)].payload
            )
            cost = VoiceCostReceipt.model_validate_json(
                artifacts[paths.cost_path.relative_to(self._project_root)].payload
            )
            provenance = VoiceProvenanceReceipt.model_validate_json(
                artifacts[paths.provenance_path.relative_to(self._project_root)].payload
            )
            outcome = json.loads(
                artifacts[paths.outcome_path.relative_to(self._project_root)].payload
            )
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            raise _state_invalid("Voice candidate evidence is malformed.", str(exc)) from exc
        receipt = self._voice_receipt(voice_request, preview, authorization)
        if (
            receipt != attempt.voice_request
            or voice_request.base_project != attempt.base_project
            or voice_request.base_registry != attempt.base_registry
            or outcome.get("request_id") != voice_request.request_id
            or outcome.get("request_fingerprint") != voice_request.voice_request_fingerprint
            or outcome.get("preview_fingerprint") != preview.preview_fingerprint
            or outcome.get("authorization_fingerprint")
            != authorization.authorization_fingerprint
            or outcome.get("provider_request_id") != cost.provider_request_id
            or outcome.get("provider_request_id") != provenance.provider_request_id
            or outcome.get("provider_trace_id") != provenance.provider_trace_id
            or outcome.get("terminal_status") != "succeeded"
            or outcome.get("alignment_receipt_sha256")
            != artifacts[paths.alignment_path.relative_to(self._project_root)].file_sha256
        ):
            raise _state_invalid("Voice candidate evidence identity is inconsistent.")
        base_snapshot = _read_regular_file_nofollow(
            self._project_root / attempt.base_registry.path,
            contained_by=self._project_root,
        )
        try:
            base_registry = AssetRegistrySnapshot.model_validate_json(base_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_invalid("Voice candidate base registry is invalid.", str(exc)) from exc
        if candidate_registry.assets[: len(base_registry.assets)] != base_registry.assets:
            raise _state_invalid("Voice candidate registry mutated or deleted base assets.")
        new_records = candidate_registry.assets[len(base_registry.assets) :]
        expected_ids = set(audio_asset_ids) | set(caption_asset_ids)
        if {item.asset_id for item in new_records} != expected_ids:
            raise _state_invalid("Voice candidate registry contains extra or missing assets.")
        audio_records = tuple(
            item for item in new_records if item.asset_id in audio_asset_ids
        )
        if len(audio_records) != 1:
            raise _state_invalid("Voice candidate graph requires exactly one generated audio asset.")
        audio_record = audio_records[0]
        expected_result_fingerprint = _result_fingerprint(
            {
                "request_id": voice_request.request_id,
                "request_fingerprint": voice_request.voice_request_fingerprint,
                "audio_sha256": audio_record.sha256,
                "content_type": outcome.get("content_type"),
                "provider_request_id": outcome.get("provider_request_id"),
                "provider_trace_id": outcome.get("provider_trace_id"),
                "alignment_receipt_sha256": outcome.get(
                    "alignment_receipt_sha256"
                ),
                "cost_receipt": cost.model_dump(mode="json"),
                "provenance_receipt": provenance.model_dump(mode="json"),
                "terminal_status": outcome.get("terminal_status"),
                "preview_fingerprint": preview.preview_fingerprint,
                "authorization_fingerprint": authorization.authorization_fingerprint,
            }
        )
        metadata = audio_record.audio_metadata
        if (
            outcome.get("result_fingerprint") != expected_result_fingerprint
            or outcome.get("audio_sha256") != audio_record.sha256
            or outcome.get("content_type") != audio_record.mime_type
            or outcome.get("policy_receipt_id") != provenance.policy_receipt_id
            or outcome.get("retention_mode") != provenance.retention_mode
            or audio_record.creation_receipt_id
            != f"voice-result-{expected_result_fingerprint}"
            or audio_record.cost_receipt_id
            != f"cost-{hashlib.sha256(_canonical_json_bytes(cost)).hexdigest()}"
            or audio_record.egress.retention_mode != provenance.retention_mode
            or audio_record.egress.provider_policy_snapshot_id
            != provenance.policy_receipt_id
            or metadata is None
            or metadata.provenance_receipt_id
            != f"provenance-{hashlib.sha256(_canonical_json_bytes(provenance)).hexdigest()}"
            or metadata.alignment_receipt_id
            != f"alignment-{outcome.get('alignment_receipt_sha256')}"
        ):
            raise _state_invalid("Voice candidate result, policy, or registry identity is inconsistent.")
        caption_records = tuple(
            item for item in new_records if item.asset_id in caption_asset_ids
        )
        if len(caption_records) != len(caption_asset_ids):
            raise _state_invalid("Voice candidate caption registry identity is inconsistent.")
        expected_alignment_id = f"alignment-{outcome.get('alignment_receipt_sha256')}"
        expected_caption_receipt = f"caption-result-{expected_result_fingerprint}"
        for caption_record in caption_records:
            caption_artifact = artifacts.get(caption_record.artifact_path)
            caption_metadata = caption_record.caption_metadata
            if caption_artifact is None or caption_metadata is None:
                raise _state_invalid("Voice candidate caption artifact is missing.")
            try:
                track = CaptionTrack.model_validate_json(caption_artifact.payload)
            except (ValidationError, ValueError) as exc:
                raise _state_invalid("Voice candidate caption track is malformed.", str(exc)) from exc
            word_count = sum(len(segment.words or ()) for segment in track.segments)
            metadata_identity = (
                caption_metadata.caption_track_id,
                caption_metadata.language,
                caption_metadata.source_audio_asset_id,
                caption_metadata.source_audio_sha256,
                caption_metadata.script_hash,
                caption_metadata.transcript_hash,
                caption_metadata.segment_count,
                caption_metadata.word_count,
                caption_metadata.segmentation_policy_id,
                caption_metadata.segmentation_policy_version,
                caption_metadata.alignment_receipt_id,
                caption_metadata.timing_fingerprint,
                caption_metadata.style_reference_id,
            )
            track_identity = (
                track.caption_track_id,
                track.language,
                track.source_audio_asset_id,
                track.source_audio_sha256,
                track.script_hash,
                track.transcript_hash,
                len(track.segments),
                word_count,
                track.segmentation_policy.policy_id,
                track.segmentation_policy.policy_version,
                track.alignment_receipt_id,
                track.timing_fingerprint,
                track.style_reference_id,
            )
            if (
                caption_artifact.payload != _canonical_track_bytes(track)
                or not verify_artifact_hash(track)
                or track.timing_fingerprint != caption_timing_fingerprint(track)
                or metadata_identity != track_identity
                or track.source_audio_asset_id != audio_record.asset_id
                or track.source_audio_sha256 != audio_record.sha256
                or track.source_sample_rate_hz != metadata.sample_rate_hz
                or track.script_hash != voice_request.script_hash
                or track.transcript_hash != voice_request.script_hash
                or track.alignment_receipt_id != expected_alignment_id
                or track.alignment_receipt_id != metadata.alignment_receipt_id
                or track.creation_receipt_id != expected_caption_receipt
                or caption_record.creation_receipt_id != track.creation_receipt_id
                or caption_record.input_artifact_ids != (audio_record.asset_id,)
                or caption_record.input_fingerprint != audio_record.sha256
            ):
                raise _state_invalid("Voice candidate caption identity is inconsistent.")
            if caption_metadata.style_reference_id is None:
                if caption_metadata.style_content_hash is not None:
                    raise _state_invalid("Voice candidate caption style identity is inconsistent.")
            else:
                style_hash = caption_metadata.style_content_hash
                style_path = Path(f"assets/styles/{style_hash}.json")
                style_artifact = artifacts.get(style_path)
                if (
                    style_hash is None
                    or style_artifact is None
                    or style_artifact.file_sha256 != style_hash
                    or hashlib.sha256(style_artifact.payload).hexdigest() != style_hash
                ):
                    raise _state_invalid("Voice candidate caption style identity is inconsistent.")
        declared_paths = {item.artifact_path for item in new_records}
        declared_paths.update(
            Path(f"assets/styles/{item.caption_metadata.style_content_hash}.json")
            for item in new_records
            if item.caption_metadata is not None
            and item.caption_metadata.style_content_hash is not None
        )
        exact_paths = evidence_paths | declared_paths | {
            commit.next_project.path,
            commit.next_registry.path,
        }
        if commit.dependency_graph_transition is not None:
            graph_path = commit.dependency_graph_transition.candidate_dependency_graph.path
            if graph_path in artifacts:
                exact_paths.add(graph_path)
        if set(artifacts) != exact_paths:
            raise _state_invalid("Voice candidate graph contains extra or missing artifacts.")
        for record in new_records:
            artifact = artifacts.get(record.artifact_path)
            if (
                artifact is None
                or artifact.file_sha256 != record.sha256
                or len(artifact.payload) != record.size_bytes
            ):
                raise _state_invalid("Voice candidate registry bytes are inconsistent.")
        return outcome.get("provider_request_id")

    def _verify_voice_committed_candidates(self, request: StateCommitRequest) -> None:
        for artifact in request.artifacts:
            snapshot = _read_regular_file_nofollow(
                self._project_root / artifact.relative_path,
                contained_by=self._project_root,
            )
            if snapshot.file_sha256 != artifact.file_sha256:
                raise _state_commit_failed("Voice candidate artifact reopen verification failed.")
        registry_snapshot = _read_regular_file_nofollow(
            self._project_root / request.next_registry.path,
            contained_by=self._project_root,
        )
        try:
            registry = AssetRegistrySnapshot.model_validate_json(registry_snapshot.data)
        except (ValidationError, ValueError) as exc:
            raise _state_commit_failed("Voice candidate registry reopen failed.", str(exc)) from exc
        if (
            registry.revision_id != request.next_registry.revision_id
            or registry.content_hash != request.next_registry.content_hash
            or registry_semantic_sha256(registry) != registry.content_hash
            or registry_snapshot.file_sha256 != request.next_registry.file_sha256
        ):
            raise _state_commit_failed("Voice candidate registry identity is invalid.")
