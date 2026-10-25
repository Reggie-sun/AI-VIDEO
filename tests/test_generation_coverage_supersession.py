"""Canonical same-frame coverage renewal preserves prior paid/media evidence."""
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_coverage_revision import CoverageRevisionTarget
from ai_video.production.generation_visual_revision import load_generation_visual_supersession
from ai_video.production.project import load_production_project
from test_generation_visual_revision import _ready_fixture, ACTOR, AUTHORIZATION
from test_production_paid_submit_quota import _goal


def _inputs(writer, prior, experience):
    state=prior.video_generation_state
    request=writer._reopen_video_request(state.request).activation_scope.request
    intent=experience.projection.requirement.generation_intent
    revised=intent.model_copy(update={'camera_intent':intent.camera_intent.model_copy(update={
        'framing_intent':'Start with the established medium frame, then cut on the listener reaction to a same-axis close-up.'})})
    target=CoverageRevisionTarget.create(intent=revised,acceptance=experience.candidate.recipe.acceptance_policy,
        rationale='Explicit user-requested camera coverage revision after a known fetched failure.')
    return dict(attempt_id=prior.attempt_id,expected_manifest_revision=writer._read_manifest().manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,actor=ACTOR,
        authorization_receipt_id=AUTHORIZATION,reason='Revise approved coverage while retaining exact reference and audio.',
        target_goal=_goal('2-coverage'),target_first_frame_sha256=request.image_bindings[0].asset_sha256,
        coverage_revision=target)


def test_same_frame_coverage_closure_and_replay_are_exact(tmp_path):
    writer,prior,experience=_ready_fixture(tmp_path,evaluation_verdict='FAIL')
    args=_inputs(writer,prior,experience)
    old_paid=prior.paid_provider_state;old_fetch=prior.video_generation_state.fetch_receipt
    result=writer.supersede_video_generation(**args)
    loaded=load_production_project(tmp_path/'project.yaml')
    closed=next(a for a in loaded.manifest.attempts if a.attempt_id==prior.attempt_id)
    assert closed.paid_provider_state==old_paid
    assert closed.video_generation_state.fetch_receipt==old_fetch
    assert closed.video_generation_state.generation_experiences==prior.video_generation_state.generation_experiences
    receipt=load_generation_visual_supersession(tmp_path,closed.video_generation_state.visual_supersession)
    assert receipt.schema_version=='generation-visual-supersession/2'
    assert receipt.old_first_frame_sha256==receipt.target_first_frame_sha256
    assert receipt.coverage_revision==args['coverage_revision']
    assert writer.supersede_video_generation(**args)==result
    changed={**args,'coverage_revision':CoverageRevisionTarget.create(intent=args['coverage_revision'].intent,
        acceptance=args['coverage_revision'].acceptance,rationale='Different target authorization rationale.')}
    with pytest.raises(AiVideoError):writer.supersede_video_generation(**changed)


@pytest.mark.parametrize('change',['v1_same_frame','v2_changed_frame','protected_visual','protected_dialogue'])
def test_coverage_renewal_cannot_borrow_v1_or_change_protected_inputs(tmp_path,change):
    writer,prior,experience=_ready_fixture(tmp_path,evaluation_verdict='FAIL')
    args=_inputs(writer,prior,experience);target=args['coverage_revision']
    if change=='v1_same_frame':args.pop('coverage_revision')
    elif change=='v2_changed_frame':args['target_first_frame_sha256']='e'*64
    elif change=='protected_visual':
        from ai_video.production.video_requirement import VisualTreatment
        intent=target.intent.model_copy(update={'visual_treatment':VisualTreatment(
            medium_look='Unapproved different visual design',palette='Different palette',
            material_treatment='Different material',prohibited_visual_drift=('Keep this different design',))})
        args['coverage_revision']=CoverageRevisionTarget.create(intent=intent,acceptance=target.acceptance,rationale=target.rationale)
    else:
        from ai_video.production.video_requirement import DialogueIntent
        intent=target.intent.model_copy(update={'dialogue_intent':DialogueIntent(mode='none')})
        args['coverage_revision']=CoverageRevisionTarget.create(intent=intent,acceptance=target.acceptance,rationale=target.rationale)
    before=(tmp_path/'state/manifest.json').read_bytes()
    with pytest.raises(AiVideoError):writer.supersede_video_generation(**args)
    assert (tmp_path/'state/manifest.json').read_bytes()==before


@pytest.mark.parametrize('invalid',['camera_bool','camera_enum','acceptance_hash'])
def test_nested_model_copy_corruption_is_rejected_before_any_receipt_or_manifest_write(tmp_path,invalid):
    from ai_video.production.hashing import canonical_sha256
    writer,prior,experience=_ready_fixture(tmp_path,evaluation_verdict='FAIL')
    args=_inputs(writer,prior,experience);target=args['coverage_revision']
    if invalid=='camera_bool':
        intent=target.intent.model_copy(update={'camera_endpoint':target.intent.camera_endpoint.model_copy(update={'position_lock':'invalid-bool'})})
        bad=target.model_copy(update={'intent':intent})
    elif invalid=='camera_enum':
        from ai_video.production.video_requirement import CameraMotionContract
        motion=CameraMotionContract(movement_kind='locked',direction='none',amplitude_class='subtle',
            speed_class='very_slow',start_motion_state='stationary',end_motion_state='settled')
        intent=target.intent.model_copy(update={'primary_camera_motion':motion.model_copy(update={'movement_kind':'invalid-camera-kind'})})
        bad=target.model_copy(update={'intent':intent})
    else:
        bad=target.model_copy(update={'acceptance':target.acceptance.model_copy(update={'profile_content_hash':'f'*64})})
    bad=bad.model_copy(update={'content_hash':canonical_sha256(bad.model_dump(mode='json',exclude={'content_hash'}))})
    args['coverage_revision']=bad
    before=(tmp_path/'state/manifest.json').read_bytes()
    receipts={p.relative_to(tmp_path):p.read_bytes() for p in (tmp_path/'state/video-generation/supersessions').glob('*.json')}
    with pytest.raises(AiVideoError):writer.supersede_video_generation(**args)
    assert (tmp_path/'state/manifest.json').read_bytes()==before
    assert {p.relative_to(tmp_path):p.read_bytes() for p in (tmp_path/'state/video-generation/supersessions').glob('*.json')}==receipts
