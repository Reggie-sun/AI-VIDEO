"""Explicit legacy observation import through the existing Manifest writer."""

import hashlib
from pathlib import Path

from ai_video.production._lifecycle_schema import ImportedGenerationExperienceReceiptPointer
from ai_video.production._state_commit_common import (
    _canonical_json_bytes, _state_invalid, _validated_transition,
)
from ai_video.production._state_commit_contracts import PreparedArtifact


class _StateCommitGenerationHistoryMixin:
    def import_generation_experience(
        self, source_root, *, expected_manifest_revision, expected_source_manifest_sha256,
        import_id, source_attempt_id, experience, source_documents,
        evaluation_source_attributions, evidence_root, actor,
    ):
        """Copy verified legacy media evidence, without reconstructing execution.

        Imports precede new video attempts. Replay uses the retained source
        snapshot and does not require the external source directory to survive.
        No paid budget, source lifecycle, or candidate pointer is changed.
        """
        from ai_video.production.generation_history_import import prepare_generation_history_import
        from ai_video.production._generation_feedback_reader import load_imported_history
        from ai_video.production.project import load_production_project
        from ai_video.production.manifest_schema import ManifestCapability, manifest_supports

        with self._exclusive_lock():
            manifest = self._read_manifest()
            retained = load_imported_history(self._project_root, manifest)
            prior = next((r for r in retained if r.import_id == import_id), None)
            if prior is not None:
                if (prior.source_manifest_sha256 != expected_source_manifest_sha256
                        or prior.source_attempt_id != source_attempt_id
                        or prior.experience != experience or prior.actor != actor
                        or prior.source_documents != tuple(source_documents)
                        or prior.evaluation_source_attributions != tuple(evaluation_source_attributions)):
                    raise _state_invalid("Historical import replay differs from retained evidence.")
                return manifest
            if manifest.manifest_revision != expected_manifest_revision:
                raise _state_invalid("Historical import Manifest revision is stale.")
            if not manifest_supports(manifest.schema_version, ManifestCapability.VIDEO_GENERATION):
                raise _state_invalid("Historical import requires video-generation capability.")
            if any(a.video_generation_state is not None for a in manifest.attempts):
                raise _state_invalid("Historical import must precede new video attempts.")
            loaded = load_production_project(self._project_root / "project.yaml")
            if loaded.qa_policy is None:
                raise _state_invalid("Historical import requires a selected retrospective QA policy.")
            try:
                receipt, media = prepare_generation_history_import(
                    source_root, expected_source_manifest_sha256=expected_source_manifest_sha256,
                    import_id=import_id, source_attempt_id=source_attempt_id,
                    experience=experience, evaluation_policy=loaded.qa_policy,
                    source_documents=tuple(source_documents), actor=actor,
                    evidence_root=evidence_root,
                    evaluation_source_attributions=tuple(evaluation_source_attributions),
                )
            except (ValueError, OSError) as exc:
                raise _state_invalid("Historical generation import is invalid.", str(exc)) from exc
            source_request = receipt.source_request
            if source_request.activation_scope is None:
                raise _state_invalid("Historical source has no Production Shot identity.")
            source_shot = source_request.activation_scope.request
            shot = next((s for s in loaded.shots if s.shot_id == source_shot.target_shot_id), None)
            if (receipt.source_manifest.project_id != manifest.project_id or shot is None
                    or shot.artifact_id not in source_shot.input_artifact_ids):
                raise _state_invalid("Historical source does not belong to this project and Shot.")
            if any(r.source_request.request_input_hash == source_request.request_input_hash
                   for r in retained):
                raise _state_invalid("Historical source request is already imported.")
            if retained and receipt.source_fetch.fetched_at < retained[-1].source_fetch.fetched_at:
                raise _state_invalid("Historical imports must preserve source fetch chronology.")
            raw = _canonical_json_bytes(receipt)
            path = Path(f"state/video-generation/imported-experiences/{receipt.content_hash}.json")
            pointer = ImportedGenerationExperienceReceiptPointer(
                path=path, content_hash=receipt.content_hash,
                file_sha256=hashlib.sha256(raw).hexdigest(),
                request_fingerprint=source_request.request_input_hash,
            )
            media_path = Path(f"state/video-generation/imported-media/{receipt.source_fetch.artifact_sha256}.mp4")
            self._write_immutable_artifact(
                PreparedArtifact(media_path, media, hashlib.sha256(media).hexdigest()),
                attempt_id=import_id,
            )
            self._write_immutable_artifact(PreparedArtifact(path, raw, pointer.file_sha256), attempt_id=import_id)
            next_manifest = _validated_transition(manifest, {
                "manifest_revision": manifest.manifest_revision + 1,
                "imported_generation_experiences": (*manifest.imported_generation_experiences, pointer),
            })
            self._write_manifest_atomic(next_manifest)
            load_production_project(self._project_root / "project.yaml")
            return self._read_manifest()
