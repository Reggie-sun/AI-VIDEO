"""A single metadata-only repair never changes the sealed creative request."""
from types import SimpleNamespace
import pytest
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import ArtifactReference
from ai_video.production.project import load_production_project
from production_project_factory import write_production_project


def _models(tmp_path):
    write_production_project(tmp_path)
    loaded = load_production_project(tmp_path / 'project.yaml')
    write_production_project(tmp_path, extra_assets=(loaded.registry.assets[0].model_copy(update={'asset_id': 'image-pose-2'}),))
    loaded = load_production_project(tmp_path / 'project.yaml')
    original = loaded.characters[0]
    extra = 'image-pose-2'
    assert extra not in original.reference_asset_ids
    char = seal_artifact(original.model_copy(update={
        'revision': original.revision + 1,
        'reference_asset_ids': (*original.reference_asset_ids, extra)}))
    refs = tuple(ArtifactReference(artifact_id=char.artifact_id, revision=char.revision,
        content_hash=char.content_hash, path='creative/characters/corrected.yaml')
        if item.artifact_id == char.artifact_id else item for item in loaded.project.artifacts.characters)
    project = seal_artifact(loaded.project.model_copy(update={
        'revision': loaded.project.revision + 1,
        'artifacts': loaded.project.artifacts.model_copy(update={'characters': refs})}))
    after = SimpleNamespace(project=project,
        characters=tuple(char if c.artifact_id == char.artifact_id else c for c in loaded.characters))
    return loaded, after, {extra: original.character_id}


def test_only_additive_reference_membership_can_repair_a_project(tmp_path):
    from ai_video.production.unsubmitted_retarget_references import validate_owner_models
    before, after, allowed = _models(tmp_path)
    validate_owner_models(before, after, allowed)


@pytest.mark.parametrize('mutation', ['remove', 'appearance', 'revision', 'unselected', 'project_title', 'no_change', 'wrong_owner'])
def test_owner_repair_rejects_creative_or_unbounded_changes(tmp_path, mutation):
    from ai_video.production.unsubmitted_retarget_references import validate_owner_models
    before, after, allowed = _models(tmp_path)
    chars = list(after.characters)
    if mutation in ('remove', 'appearance', 'revision'):
        changes = {'remove': {'reference_asset_ids': chars[0].reference_asset_ids[-1:]},
                   'appearance': {'appearance_bible': 'Different actor face'},
                   'revision': {'revision': chars[0].revision + 1}}[mutation]
        chars[0] = seal_artifact(chars[0].model_copy(update=changes));after.characters = tuple(chars)
    elif mutation == 'unselected':
        allowed = {}
    elif mutation == 'wrong_owner':
        allowed = {key: 'another-character' for key in allowed}
    elif mutation == 'project_title':
        after.project = seal_artifact(after.project.model_copy(update={'title': 'Changed story'}))
    else:
        after = before
    with pytest.raises(ValueError):
        validate_owner_models(before, after, allowed)


def test_rebased_target_is_still_locked_to_every_original_request_field(tmp_path):
    from ai_video.production.unsubmitted_retarget_references import validate_target_rebase
    from test_generation_authored_retarget import _same_model_reference_repair
    from ai_video.production.generation_authored_retarget import AuthoredGenerationRetargetTarget
    from ai_video.production.models import ProjectSnapshotPointer, canonical_project_snapshot_path
    _, _, target, _, _ = _same_model_reference_repair(tmp_path)
    pointer = ProjectSnapshotPointer(path=canonical_project_snapshot_path(target.target_project.revision+1,'a'*64),
        revision=target.target_project.revision+1, content_hash='a'*64, file_sha256='b'*64)
    values = {name: getattr(target, name) for name in type(target).model_fields if name != 'content_hash'}
    values['target_project'] = pointer
    rebased = AuthoredGenerationRetargetTarget.create(**values)
    validate_target_rebase(target, rebased)
    for field, value in [('rationale', 'Changed intent justification'), ('authorization_reference', 'new-authority')]:
        changed = AuthoredGenerationRetargetTarget.create(**{**values, field: value})
        with pytest.raises(ValueError): validate_target_rebase(target, changed)


def test_second_project_step_needs_an_explicit_original_target(tmp_path):
    from test_generation_authored_retarget import _same_model_reference_repair, _retarget_binding
    from ai_video.production.generation_authored_retarget import (
        AuthoredGenerationRetargetTarget, validate_authored_generation_retarget_binding)
    from ai_video.production.models import ProjectSnapshotPointer, canonical_project_snapshot_path
    baseline, retained, target, _, _ = _same_model_reference_repair(tmp_path)
    values = {name: getattr(target, name) for name in type(target).model_fields if name != 'content_hash'}
    values['target_project'] = ProjectSnapshotPointer(
        path=canonical_project_snapshot_path(target.target_project.revision+1,'a'*64),
        revision=target.target_project.revision+1,content_hash='a'*64,file_sha256='b'*64)
    rebased = AuthoredGenerationRetargetTarget.create(**values)
    binding, selected = _retarget_binding(baseline, retained, rebased, request_changes={
        'prompt_text':baseline.compiled_request.activation_scope.request.prompt_text+' Urgent restrained speech.'})
    selected.capabilities=retained.candidate.capabilities
    kwargs=dict(target_goal=selected.final_output_goal,authorization_receipt_id=target.authorization_reference)
    with pytest.raises(ValueError, match='one revision'):
        validate_authored_generation_retarget_binding(binding,selected,rebased,**kwargs)
    # This helper is not an authority: the locked owner must obtain previous_target
    # from the strict reader's actual canonical one-hop receipt, proven separately.
    validate_authored_generation_retarget_binding(binding,selected,rebased,previous_target=target,**kwargs)


def test_public_reference_recovery_rejects_an_unclosed_source_without_writes(tmp_path):
    from test_generation_visual_revision import _ready_fixture
    from test_generation_authored_retarget import _retarget_target
    from ai_video.production.models import ActorIdentity
    from ai_video.errors import AiVideoError
    writer, prior, experience=_ready_fixture(tmp_path,evaluation_verdict='FAIL')
    binding=writer._reopen_generation_execution_binding(prior.video_generation_state.execution_binding)
    target=_retarget_target(binding,experience)
    before=(tmp_path/'state/manifest.json').read_bytes()
    with pytest.raises(AiVideoError):
        writer.correct_unsubmitted_retarget_references(attempt_id=prior.attempt_id,
            expected_manifest_revision=writer._read_manifest().manifest_revision,
            actor=ActorIdentity(actor_id='test',actor_kind='codex'),
            authorization_receipt_id=target.authorization_reference,corrected_target=target,reason='restore owner')
    assert (tmp_path/'state/manifest.json').read_bytes()==before
