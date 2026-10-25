"""Public closure rejects malformed output targets before immutable writes."""
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_resolution_revision import ResolutionRevisionTarget
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from test_generation_visual_revision import _ready_fixture,ACTOR,AUTHORIZATION
from test_production_paid_submit_quota import _goal


def _target():
    old=VideoFlexibleOutputRequirement(timing_mode='nominal_seconds',duration_seconds=16,
        dimension_mode='adaptive',resolution_label='480p',ratio='16:9',fps=None,
        container='mp4',mime_type='video/mp4',native_audio=True)
    return ResolutionRevisionTarget.create(old_output=old,
        target_output=old.model_copy(update={'resolution_label':'1080p'}),rationale='Explicit user-approved HD version.')


@pytest.mark.parametrize('invalid',['native_audio','fps','duration','tier','old_output_mismatch'])
def test_invalid_resolution_target_cannot_write_receipt_or_manifest(tmp_path,invalid):
    writer,prior,_experience=_ready_fixture(tmp_path)
    target=_target()
    if invalid!='old_output_mismatch':
        field,value={'native_audio':('native_audio','invalid-bool'),'fps':('fps',True),
            'duration':('duration_seconds',17),'tier':('resolution_label','480p')}[invalid]
        target=target.model_copy(update={'target_output':target.target_output.model_copy(update={field:value})})
        target=target.model_copy(update={'content_hash':canonical_sha256(target.model_dump(mode='json',exclude={'content_hash'}))})
    request=writer._reopen_video_request(prior.video_generation_state.request).activation_scope.request
    before=(tmp_path/'state/manifest.json').read_bytes()
    directory=tmp_path/'state/video-generation/supersessions'
    receipts={p.name:p.read_bytes()for p in directory.glob('*.json')}
    with pytest.raises(AiVideoError):
        writer.supersede_video_generation(attempt_id=prior.attempt_id,
            expected_manifest_revision=writer._read_manifest().manifest_revision,
            experience_content_hash=prior.video_generation_state.generation_experiences[-1].content_hash,
            actor=ACTOR,authorization_receipt_id=AUTHORIZATION,reason='Create explicitly requested HD version.',
            target_goal=_goal('HD2'),target_first_frame_sha256=request.image_bindings[0].asset_sha256,
            resolution_revision=target)
    assert (tmp_path/'state/manifest.json').read_bytes()==before
    assert {p.name:p.read_bytes()for p in directory.glob('*.json')}==receipts


@pytest.mark.parametrize('purpose',['production','qualification'])
def test_prospective_resolution_goal_recognition_is_qualification_only(purpose):
    from test_production_generation_decision import setup_decision,decide,evidence
    from test_production_shot_router import _capabilities

    setup=setup_decision()
    original=setup['inputs'].candidates[0]
    capabilities=_capabilities(original.capabilities.variants[0].model_copy(update={'production_qualification':'QUALIFIED'}))
    output=VideoFlexibleOutputRequirement(timing_mode='nominal_seconds',duration_seconds=4,
        dimension_mode='adaptive',resolution_label='480p',ratio='16:9',fps=24,
        container='mp4',mime_type='video/mp4',native_audio=False)
    old=original.model_copy(update={'capabilities':capabilities,'output_requirement':output,'final_output_goal':_goal('1')})
    new=old.model_copy(update={'output_requirement':output.model_copy(update={'resolution_label':'1080p'}),
        'final_output_goal':_goal('HD2')})
    item=evidence(setup,candidate=old,verdict='NOT_EVALUATED')
    setup['policy']=setup['policy'].model_copy(update={'execution_purpose':purpose})
    result=decide(setup,candidates=(new,),historical_recipes=(old,),evidence=(item,),latest_attempt_hash=item.evidence_hash)
    if purpose=='production':assert result.disposition=='EVIDENCE_GAP'
    else:assert result.disposition!='EVIDENCE_GAP'
