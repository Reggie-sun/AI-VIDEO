"""One committer-owned reference-membership correction before a video request."""
from pathlib import Path
from types import SimpleNamespace
import hashlib


def validate_target_rebase(before, after):
    before, after = before.verify(), after.verify()
    omitted = {'content_hash', 'target_project'}
    if (before.model_dump(mode='json', exclude=omitted) != after.model_dump(mode='json', exclude=omitted)
            or after.target_project.revision != before.target_project.revision + 1
            or after.target_project.content_hash == before.target_project.content_hash):
        raise ValueError('Reference repair may only advance the exact target Project once')


def validate_owner_models(before, after, allowed_owners):
    """Only add already selected image IDs to existing Character references."""
    ignored = {'revision', 'content_hash', 'creation_receipt_id', 'source_provenance', 'artifacts'}
    a, b = before.project, after.project
    if (b.revision != a.revision + 1
            or a.model_dump(mode='json', exclude=ignored) != b.model_dump(mode='json', exclude=ignored)
            or a.artifacts.model_dump(exclude={'characters'}) != b.artifacts.model_dump(exclude={'characters'})
            or any(ref not in b.source_provenance for ref in a.source_provenance)):
        raise ValueError('Reference repair cannot change other Project authoring')
    old = {c.artifact_id: c for c in before.characters}
    new = {c.artifact_id: c for c in after.characters}
    if set(old) != set(new):
        raise ValueError('Reference repair cannot add or remove characters')
    changed = False
    for identifier, previous in old.items():
        current = new[identifier]
        if previous == current:
            continue
        fields = {'revision', 'content_hash', 'creation_receipt_id', 'source_provenance', 'reference_asset_ids'}
        added = set(current.reference_asset_ids) - set(previous.reference_asset_ids)
        if (current.revision != previous.revision + 1 or not added or any(allowed_owners.get(aid) != previous.character_id for aid in added)
                or not set(previous.reference_asset_ids) <= set(current.reference_asset_ids)
                or previous.model_dump(mode='json', exclude=fields) != current.model_dump(mode='json', exclude=fields)
                or any(ref not in current.source_provenance for ref in previous.source_provenance)):
            raise ValueError('Reference repair must retain identity and only add selected reference ownership')
        changed = True
    if not changed:
        raise ValueError('Reference repair requires an actual missing owner relation')


def _owner_snapshot(root, pointer):
    from ai_video.production._generation_feedback_reader import _root_and_path
    from ai_video.production.paths import _read_regular_file_nofollow
    from ai_video.production.project import _load_yaml_artifact, _load_referenced_artifact
    from ai_video.production.models import ProductionProject, Character
    resolved_root, path = _root_and_path(root, pointer.path)
    raw = _read_regular_file_nofollow(path, contained_by=resolved_root / 'state')
    project = _load_yaml_artifact(path, ProductionProject)
    if (raw.file_sha256 != pointer.file_sha256 or project.revision != pointer.revision
            or project.content_hash != pointer.content_hash):
        raise ValueError('Reference repair Project pointer differs from immutable bytes')
    return SimpleNamespace(project=project, characters=tuple(
        _load_referenced_artifact(resolved_root, ref, Character) for ref in project.artifacts.characters))


def validate_reference_correction(root, previous, corrected):
    if (previous.schema_version != 'generation-visual-supersession/5'
            or corrected.schema_version != previous.schema_version
            or previous.previous_supersession is not None
            or corrected.previous_supersession is None
            or corrected.previous_supersession.content_hash != previous.content_hash):
        raise ValueError('Reference repair requires exactly one retained /5 predecessor')
    ignored = {'content_hash', 'expected_manifest_revision', 'reason', 'previous_supersession', 'authored_retarget'}
    if previous.model_dump(mode='json', exclude=ignored) != corrected.model_dump(mode='json', exclude=ignored):
        raise ValueError('Reference repair cannot change source, goal, authority or paid history')
    validate_target_rebase(previous.authored_retarget, corrected.authored_retarget)
    from ai_video.production._generation_feedback_reader import load_generation_execution_binding
    source = load_generation_execution_binding(root, previous.execution_binding)
    bound = {item.asset_id: item.asset_sha256 for item in previous.authored_retarget.image_bindings}
    owners = {item.asset_id: item.canonical_owner_id
        for item in source.projection.requirement.asset_evidence
        if item.role.value == 'identity' and bound.get(item.asset_id) == item.asset_sha256
        and item.canonical_owner_id is not None}
    validate_owner_models(_owner_snapshot(root, previous.authored_retarget.target_project),
        _owner_snapshot(root, corrected.authored_retarget.target_project), owners)


def correct_unsubmitted_retarget_references(committer, *, attempt_id, expected_manifest_revision,
                                           actor, authorization_receipt_id, corrected_target, reason):
    from ai_video.production.project import load_production_project
    from ai_video.production.generation_visual_revision import (
        load_generation_visual_supersession, GenerationVisualSupersessionReceipt)
    from ai_video.production.generation_authored_retarget import validate_authored_generation_retarget_target
    from ai_video.production.models import StateCommitStatus
    from ai_video.production._lifecycle_schema import GenerationVisualSupersessionReceiptPointer
    from ai_video.production._state_commit_common import _canonical_json_bytes, _state_invalid, _validated_transition
    from ai_video.production._state_commit_contracts import PreparedArtifact
    corrected_target = corrected_target.verify()
    if not isinstance(reason, str) or not reason.strip():
        raise _state_invalid('Reference repair requires an explicit reason')
    with committer._exclusive_lock():
        manifest = committer._read_manifest()
        attempt = committer._video_attempt(manifest, attempt_id)
        state = attempt.video_generation_state
        if (state is None or state.visual_supersession is None
                or attempt.status is not StateCommitStatus.FAILED):
            raise _state_invalid('Reference repair requires its closed fetched source')
        previous = load_generation_visual_supersession(committer.project_root, state.visual_supersession)
        if previous.previous_supersession is not None:
            if (previous.authored_retarget == corrected_target and previous.actor == actor
                    and previous.authorization_receipt_id == authorization_receipt_id
                    and previous.expected_manifest_revision == expected_manifest_revision
                    and previous.reason == reason.strip()):
                return manifest
            raise _state_invalid('Reference repair cannot extend or replace a retained correction')
        loaded = load_production_project(committer.project_root / 'project.yaml')
        index = next(i for i, a in enumerate(manifest.attempts) if a.attempt_id == attempt_id)
        if (expected_manifest_revision != manifest.manifest_revision or loaded.manifest != manifest
                or previous.actor != actor or previous.authorization_receipt_id != authorization_receipt_id
                or previous.authored_retarget is None
                or manifest.active_project != corrected_target.target_project
                or loaded.qa_policy is None or loaded.qa_policy.final_output != previous.target_goal
                or loaded.qa_policy.generation_acceptance != previous.authored_retarget.acceptance
                or any(a.operation == 'video_generation' for a in manifest.attempts[index+1:])):
            raise _state_invalid('Reference repair authority, exact Project, QA and zero-request boundary must hold')
        values = {name: getattr(previous, name) for name in type(previous).model_fields if name != 'content_hash'}
        values.update(authored_retarget=corrected_target, reason=reason.strip(),
            expected_manifest_revision=manifest.manifest_revision, previous_supersession=state.visual_supersession)
        corrected = GenerationVisualSupersessionReceipt.create(**values)
        try:
            validate_reference_correction(committer.project_root, previous, corrected)
            binding = committer._reopen_generation_execution_binding(state.execution_binding)
            experience = committer._reopen_generation_experience(state.generation_experiences[-1])
            validate_authored_generation_retarget_target(binding, experience, previous.authored_retarget)
        except (AttributeError, TypeError, ValueError) as error:
            raise _state_invalid('Reference repair differs from its sealed source and ownership-only delta', str(error)) from error
        payload = _canonical_json_bytes(corrected)
        digest = hashlib.sha256(payload).hexdigest()
        path = Path('state/video-generation/supersessions') / (corrected.content_hash + '.json')
        pointer = GenerationVisualSupersessionReceiptPointer(path=path, content_hash=corrected.content_hash,
            attempt_id=attempt_id, request_fingerprint=corrected.request_fingerprint,
            artifact_sha256=corrected.artifact_sha256, experience_content_hash=corrected.experience_content_hash,
            file_sha256=digest)
        committer._write_immutable_artifact(PreparedArtifact(path, payload, digest), attempt_id=attempt_id)
        replacement = _validated_transition(attempt, {'video_generation_state':
            state.model_copy(update={'visual_supersession': pointer})})
        successor = _validated_transition(manifest, {'manifest_revision': manifest.manifest_revision+1,
            'attempts': tuple(replacement if a.attempt_id == attempt_id else a for a in manifest.attempts)})
        committer._write_manifest_atomic(successor)
        load_production_project(committer.project_root / 'project.yaml')
        return committer._read_manifest()
