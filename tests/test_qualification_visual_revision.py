"""A new authored visual version retains cumulative known media history."""
from copy import copy
from types import SimpleNamespace

import pytest

from ai_video.production._qualification_visual_revision import allows_authored_visual_revision
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.video import VideoGenerationRequest
from test_production_paid_submit_quota import _goal
from test_qualification_quality_repair import _make_evaluated_trial


@pytest.fixture(scope='module')
def visual_revision(tmp_path_factory):
    old, candidate = _make_evaluated_trial(tmp_path_factory.mktemp('visual-version'))
    prior = old.inputs.experiences[-1]
    candidate = candidate.model_copy(update={'final_output_goal': _goal('1')})
    evidence = prior.evidence[-1].model_copy(update={'recipe_scope_hash': candidate.scope_hash})
    prior = GenerationExperience(projection=prior.projection, candidate=candidate,
        evidence=(evidence,), evaluation_sources=prior.evaluation_sources)
    next_candidate = candidate.model_copy(update={'final_output_goal': _goal('2')})
    before = old.inputs.baseline_request
    raw = before.model_dump(mode='python', exclude={'request_input_hash'})
    raw['image_bindings'] = (before.image_bindings[0].model_copy(update={
        'asset_id': 'authored-new-first-frame', 'asset_sha256': 'f' * 64}),)
    request = VideoGenerationRequest.create(**raw)
    binding = copy(old)
    binding.projection = prior.projection
    binding.inputs = old.inputs.model_copy(update={'experiences': (prior,),
        'evidence': (evidence,), 'latest_attempt_hash': evidence.evidence_hash})
    binding.decision = copy(old.decision)
    binding.decision.intervention = None
    binding.compiled_request = SimpleNamespace(activation_scope=SimpleNamespace(request=request))
    return binding, next_candidate


def test_one_changed_frame_new_goal_is_prospective_admissible(visual_revision):
    binding, candidate = visual_revision
    assert allows_authored_visual_revision(binding, candidate)


@pytest.mark.parametrize('change', ['same_goal', 'different_goal', 'drop_requirement',
    'same_frame', 'changed_output', 'unknown', 'reset_count', 'expanded_ceiling',
    'resample', 'intervention', 'changed_dialogue', 'dropped_raw_rule'])
def test_invalid_scope_does_not_admit(visual_revision, change):
    original, candidate = visual_revision
    binding = copy(original)
    if change == 'same_goal':
        candidate = candidate.model_copy(update={'final_output_goal': _goal('1')})
    elif change == 'different_goal':
        candidate = candidate.model_copy(update={'final_output_goal':
            _goal('2').model_copy(update={'goal_id': 'another-task-goal'})})
    elif change == 'drop_requirement':
        candidate = candidate.model_copy(update={'final_output_goal':
            _goal('2').model_copy(update={'requirements': ()})})
    elif change in {'same_frame', 'changed_output'}:
        request = binding.compiled_request.activation_scope.request
        raw = request.model_dump(mode='python', exclude={'request_input_hash'})
        if change == 'same_frame':
            raw['image_bindings'] = binding.inputs.baseline_request.image_bindings
        else:
            raw['output_requirement'] = request.output_requirement.model_copy(update={'duration_seconds': 9})
        binding.compiled_request = SimpleNamespace(activation_scope=SimpleNamespace(
            request=VideoGenerationRequest.create(**raw)))
    elif change == 'unknown':
        evidence = binding.inputs.evidence[-1].model_copy(update={'outcome': 'unknown_outcome'})
        binding.inputs = binding.inputs.model_copy(update={'evidence': (evidence,)})
    elif change in {'reset_count', 'expanded_ceiling'}:
        field, value = ('paid_submits_used', 0) if change == 'reset_count' else ('paid_submit_ceiling', 3)
        binding.inputs = binding.inputs.model_copy(update={'limits': binding.inputs.limits.model_copy(update={field: value})})
    elif change == 'resample':
        binding.inputs = binding.inputs.model_copy(update={'policy': binding.inputs.policy.model_copy(update={'max_resamples': 1})})
    elif change == 'intervention':
        binding.decision = copy(original.decision)
        binding.decision.intervention = object()
    elif change == 'changed_dialogue':
        from ai_video.production.video_requirement import DialogueIntent
        requirement = binding.projection.requirement
        intent = requirement.generation_intent.model_copy(update={'dialogue_intent': DialogueIntent(mode='none')})
        binding.projection = binding.projection.model_copy(update={'requirement': requirement.model_copy(update={'generation_intent': intent})})
    elif change == 'dropped_raw_rule':
        candidate = candidate.model_copy(update={'recipe': candidate.recipe.model_copy(update={'expressions': ()})})
    assert not allows_authored_visual_revision(binding, candidate)


def test_submit_lock_requires_the_canonical_supersession_and_exact_target(tmp_path):
    from ai_video.errors import AiVideoError
    from ai_video.production._qualification_visual_revision import require_authored_visual_revision_predecessor
    from test_generation_visual_revision import _ready_fixture, _supersede, _target_goal

    writer, prior, experience = _ready_fixture(tmp_path)
    state = prior.video_generation_state
    old = writer._reopen_generation_execution_binding(state.execution_binding)
    baseline = writer._reopen_video_request(state.request).activation_scope.request
    evidence = experience.evidence[-1]
    selected = experience.candidate.model_copy(update={'final_output_goal': _target_goal()})
    raw = baseline.model_dump(mode='python', exclude={'request_input_hash'})
    from ai_video.production.models import canonical_project_snapshot_path
    next_revision=baseline.base_project.revision+1
    raw.update(image_bindings=(baseline.image_bindings[0].model_copy(update={
        'asset_id': 'new-frame', 'asset_sha256': 'f'*64}),),
        base_project=baseline.base_project.model_copy(update={'revision': next_revision,
            'path':canonical_project_snapshot_path(next_revision, baseline.base_project.content_hash)}))
    request = VideoGenerationRequest.create(**raw)
    binding = SimpleNamespace(policy=SimpleNamespace(execution_purpose='qualification'),
        projection=old.projection, context=old.context,
        inputs=old.inputs.model_copy(update={'experiences': (experience,), 'evidence': experience.evidence,
            'latest_attempt_hash': evidence.evidence_hash, 'baseline_request': baseline,
            'limits': old.inputs.limits.model_copy(update={'paid_submit_ceiling': 2, 'paid_submits_used': 1})}),
        compiled_request=SimpleNamespace(activation_scope=SimpleNamespace(request=request)),
        decision=SimpleNamespace(runtime_repair=None, intervention=None, selected_candidate_id=selected.candidate_id))
    binding.inputs=binding.inputs.model_copy(update={'candidates': (selected,),
        'policy':binding.inputs.policy.model_copy(update={'max_resamples':0})})
    assert allows_authored_visual_revision(binding, selected)
    before=writer._read_manifest()
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match='canonical supersession'):
        require_authored_visual_revision_predecessor(writer, before, binding)
    closed=_supersede(writer, prior, experience)
    with writer._exclusive_lock():
        require_authored_visual_revision_predecessor(writer, closed, binding)
    raw['image_bindings']=(raw['image_bindings'][0].model_copy(update={'asset_sha256':'e'*64}),)
    binding.compiled_request=SimpleNamespace(activation_scope=SimpleNamespace(request=VideoGenerationRequest.create(**raw)))
    with writer._exclusive_lock(), pytest.raises(AiVideoError, match='sealed target'):
        require_authored_visual_revision_predecessor(writer, closed, binding)
    assert writer._read_manifest()==closed
