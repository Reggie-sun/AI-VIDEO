"""Explicit supersession preserves exact paid video evidence for a new goal."""

import pytest

from ai_video.errors import AiVideoError
from ai_video.errors import ErrorCode
from ai_video.production.final_output_contracts import (
    FinalOutputContract,
    FinalOutputRequirement,
)
from ai_video.production.models import ActorIdentity, PaidProviderAttemptPhase, StateCommitStatus
from ai_video.production._generation_feedback_reader import (
    load_generation_visual_supersession,
)
from test_production_paid_submit_quota import _goal, _new_goal_pending


ACTOR = ActorIdentity(actor_id="codex-visual-revision", actor_kind="codex")
AUTHORIZATION = "user-authorization-2026-10-26-d-visual-revision"


def _target_goal():
    old = _goal("1")
    return FinalOutputContract(
        goal_id=old.goal_id,
        goal_version="2-visual-d",
        user_goal=old.user_goal + " Preserve the selected mature D visual design.",
        requirements=(
            *old.requirements,
            FinalOutputRequirement(
                requirement_id="selected-d-visual-revision",
                observable="Use the user's selected D character reference in the new first frame.",
                proof="human",
            ),
        ),
    )


def _supersede(writer, prior, experience, *, goal=None, first_frame_sha256=None,
               authorization=AUTHORIZATION):
    from ai_video.production._generation_feedback_reader import load_generation_experience

    state = prior.video_generation_state
    assert state is not None
    return writer.supersede_video_generation(
        attempt_id=prior.attempt_id,
        expected_manifest_revision=writer._read_manifest().manifest_revision,
        experience_content_hash=state.generation_experiences[-1].content_hash,
        actor=ACTOR,
        authorization_receipt_id=authorization,
        reason="用户选择 D 版人物后要求重新制作首镜。",
        target_goal=goal or _target_goal(),
        target_first_frame_sha256=first_frame_sha256 or "f" * 64,
    )


def _ready_fixture(tmp_path, *, evaluation_verdict="NOT_EVALUATED"):
    writer, _, prior, experience, _ = _new_goal_pending(
        tmp_path, stop_after_goal=True, evaluation_verdict=evaluation_verdict
    )
    old_policy = experience.evaluation_sources[0].qa_policy_snapshot
    assert old_policy is not None
    writer.activate_qa_policy(
        old_policy,
        expected_manifest_revision=writer._read_manifest().manifest_revision,
        attempt_id="restore-original-qa-policy",
    )
    current_prior = next(
        item for item in writer._read_manifest().attempts if item.attempt_id == prior.attempt_id
    )
    return writer, current_prior, experience


def _ready_fixture_without_durable_experience(tmp_path, monkeypatch):
    from ai_video.production._state_commit_generation_feedback import (
        _StateCommitGenerationFeedbackMixin,
    )

    with monkeypatch.context() as patch:
        patch.setattr(
            _StateCommitGenerationFeedbackMixin,
            "record_generation_experience",
            lambda *args, **kwargs: None,
        )
        writer, _, prior, experience, _ = _new_goal_pending(
            tmp_path, stop_after_goal=True
        )
    old_policy = experience.evaluation_sources[0].qa_policy_snapshot
    assert old_policy is not None
    writer.activate_qa_policy(
        old_policy,
        expected_manifest_revision=writer._read_manifest().manifest_revision,
        attempt_id="restore-original-qa-policy",
    )
    current_prior = next(
        item for item in writer._read_manifest().attempts if item.attempt_id == prior.attempt_id
    )
    return writer, current_prior, experience


def test_supersession_closes_attempt_and_preserves_paid_media_and_mixed_observations(tmp_path):
    writer, prior, experience = _ready_fixture(tmp_path, evaluation_verdict="PASS")
    before = writer._read_manifest()
    old_attempt = next(item for item in before.attempts if item.attempt_id == prior.attempt_id)
    old_state = old_attempt.video_generation_state
    old_paid = old_attempt.paid_provider_state
    old_fetch = writer._reopen_video_fetch(old_state.fetch_receipt)
    old_experience_bytes = (tmp_path / old_state.generation_experiences[-1].path).read_bytes()
    assert {item.verdict for item in experience.evidence[0].findings} == {"PASS", "NOT_EVALUATED"}

    closed = _supersede(writer, old_attempt, experience)
    superseded = next(item for item in closed.attempts if item.attempt_id == prior.attempt_id)
    state = superseded.video_generation_state
    assert superseded.status is StateCommitStatus.FAILED
    assert superseded.error_code == "generation_visual_superseded"
    assert state.phase.value == "validate"
    assert superseded.paid_provider_state == old_paid
    assert superseded.paid_provider_state.phase is PaidProviderAttemptPhase.ACCEPTED
    assert writer._reopen_video_fetch(state.fetch_receipt) == old_fetch
    assert (tmp_path / state.generation_experiences[-1].path).read_bytes() == old_experience_bytes
    assert state.quality_rejection is None

    receipt = load_generation_visual_supersession(tmp_path, state.visual_supersession)
    assert receipt.target_goal == _target_goal()
    assert receipt.target_first_frame_sha256 == "f" * 64
    assert receipt.experience_content_hash == state.generation_experiences[-1].content_hash


def test_exact_visual_supersession_replay_has_no_second_manifest_transition(tmp_path):
    writer, prior, experience = _ready_fixture(tmp_path)
    closed = _supersede(writer, prior, experience)
    pointer = next(a for a in closed.attempts if a.attempt_id == prior.attempt_id).video_generation_state.visual_supersession
    revision = closed.manifest_revision

    replay = writer.supersede_video_generation(
        attempt_id=prior.attempt_id,
        expected_manifest_revision=revision - 1,
        experience_content_hash=pointer.experience_content_hash,
        actor=ACTOR,
        authorization_receipt_id=AUTHORIZATION,
        reason="用户选择 D 版人物后要求重新制作首镜。",
        target_goal=_target_goal(),
        target_first_frame_sha256="f" * 64,
    )
    assert replay == closed
    assert writer._read_manifest().manifest_revision == revision

    with pytest.raises(AiVideoError):
        writer.supersede_video_generation(
            attempt_id=prior.attempt_id,
            expected_manifest_revision=revision - 1,
            experience_content_hash=pointer.experience_content_hash,
            actor=ACTOR,
            authorization_receipt_id=AUTHORIZATION,
            reason="Different creative revision.",
            target_goal=_target_goal(),
            target_first_frame_sha256="f" * 64,
        )


def test_stale_manifest_and_missing_experience_identity_are_rejected_without_closure(tmp_path):
    writer, prior, experience = _ready_fixture(tmp_path)
    manifest = writer._read_manifest()
    state = prior.video_generation_state
    with pytest.raises(AiVideoError):
        writer.supersede_video_generation(
            attempt_id=prior.attempt_id,
            expected_manifest_revision=manifest.manifest_revision - 1,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
            authorization_receipt_id=AUTHORIZATION,
            reason="User selected the D visual revision.",
            target_goal=_target_goal(),
            target_first_frame_sha256="f" * 64,
        )
    with pytest.raises(AiVideoError):
        writer.supersede_video_generation(
            attempt_id=prior.attempt_id,
            expected_manifest_revision=manifest.manifest_revision,
            experience_content_hash="0" * 64,
            actor=ACTOR,
            authorization_receipt_id=AUTHORIZATION,
            reason="User selected the D visual revision.",
            target_goal=_target_goal(),
            target_first_frame_sha256="f" * 64,
        )
    assert writer._read_manifest() == manifest


def test_missing_durable_experience_cannot_close_fetched_attempt(tmp_path, monkeypatch):
    writer, prior, unattached_experience = _ready_fixture_without_durable_experience(
        tmp_path, monkeypatch
    )
    assert prior.video_generation_state.generation_experiences == ()
    with pytest.raises(AiVideoError):
        writer.supersede_video_generation(
            attempt_id=prior.attempt_id,
            expected_manifest_revision=writer._read_manifest().manifest_revision,
            experience_content_hash=unattached_experience.evidence[0].evidence_hash,
            actor=ACTOR,
            authorization_receipt_id=AUTHORIZATION,
            reason="User selected the D visual revision.",
            target_goal=_target_goal(),
            target_first_frame_sha256="f" * 64,
        )
    assert writer._read_manifest().attempts[-1].video_generation_state.generation_experiences == ()


def test_unknown_attempt_outcome_cannot_be_superseded(tmp_path):
    writer, prior, _ = _ready_fixture(tmp_path)
    writer.record_video_provider_failure(
        attempt_id=prior.attempt_id,
        error_code=ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN,
        message="Fixture deliberately changes the lifecycle to UNKNOWN.",
    )
    before = writer._read_manifest()
    state = next(item for item in before.attempts if item.attempt_id == prior.attempt_id).video_generation_state
    with pytest.raises(AiVideoError):
        writer.supersede_video_generation(
            attempt_id=prior.attempt_id,
            expected_manifest_revision=before.manifest_revision,
            experience_content_hash=state.generation_experiences[-1].content_hash,
            actor=ACTOR,
            authorization_receipt_id=AUTHORIZATION,
            reason="User selected the D visual revision.",
            target_goal=_target_goal(),
            target_first_frame_sha256="f" * 64,
        )
    assert writer._read_manifest() == before


@pytest.mark.parametrize("case", ["same_version", "dropped_requirement", "same_frame"])
def test_visual_revision_requires_new_goal_and_preserves_existing_requirements(tmp_path, case):
    writer, prior, experience = _ready_fixture(tmp_path)
    goal = _target_goal()
    first_frame = "f" * 64
    if case == "same_version":
        goal = goal.model_copy(update={"goal_version": "1"})
    elif case == "dropped_requirement":
        goal = goal.model_copy(update={"requirements": goal.requirements[1:]})
    else:
        request = writer._reopen_video_request(prior.video_generation_state.request)
        first_frame = request.activation_scope.request.image_bindings[0].asset_sha256

    with pytest.raises(AiVideoError):
        _supersede(writer, prior, experience, goal=goal, first_frame_sha256=first_frame)


def test_supersession_reader_rejects_tampered_receipt_bytes(tmp_path):
    writer, prior, experience = _ready_fixture(tmp_path)
    closed = _supersede(writer, prior, experience)
    state = next(a for a in closed.attempts if a.attempt_id == prior.attempt_id).video_generation_state
    pointer = state.visual_supersession
    path = tmp_path / pointer.path
    payload = bytearray(path.read_bytes())
    payload[-2] = ord(" ") if payload[-2] != ord(" ") else ord("x")
    path.write_bytes(payload)
    with pytest.raises(AiVideoError):
        load_generation_visual_supersession(tmp_path, pointer)


def test_closed_attempt_allows_exact_readback_but_rejects_new_experience(tmp_path):
    from ai_video.production.generation_feedback import record_attempt_evaluation

    writer, prior, experience = _ready_fixture(tmp_path)
    closed = _supersede(writer, prior, experience)
    state = next(item for item in closed.attempts if item.attempt_id == prior.attempt_id).video_generation_state

    replayed = record_attempt_evaluation(committer=writer, attempt_id=prior.attempt_id)
    assert replayed == experience
    same = writer.record_generation_experience(attempt_id=prior.attempt_id, experience=experience)
    assert same == closed

    evidence = experience.evidence[-1].model_copy(update={
        "outcome": "runtime_failure",
        "artifact_sha256": None,
        "findings": (),
        "runtime_reason": "Attempt to append a new outcome after closure.",
    })
    changed = experience.model_copy(update={"evidence": (evidence,)})
    with pytest.raises(AiVideoError):
        writer.record_generation_experience(attempt_id=prior.attempt_id, experience=changed)
    assert writer._read_manifest().attempts[-1].video_generation_state.visual_supersession == state.visual_supersession


@pytest.mark.parametrize('closed', [False, True])
def test_resealed_experience_cannot_substitute_other_execution_inputs(tmp_path, closed):
    """Inject self-consistent disk corruption; do not mistake rehashing for lineage."""
    import hashlib
    from pathlib import Path
    from ai_video.production._state_commit_common import _canonical_json_bytes
    from ai_video.production._lifecycle_schema import GenerationExperienceReceiptPointer, GenerationVisualSupersessionReceiptPointer
    from ai_video.production.generation_experience import GenerationExperience
    from ai_video.production.generation_visual_revision import GenerationVisualSupersessionReceipt
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.project import load_production_project

    writer, prior, experience = _ready_fixture(tmp_path)
    if closed:
        _supersede(writer, prior, experience)
    manifest=writer._read_manifest()
    prior=next(a for a in manifest.attempts if a.attempt_id==prior.attempt_id)
    state=prior.video_generation_state
    candidate=experience.candidate.model_copy(update={'final_output_goal':_goal('another-valid-goal-version')})
    evidence=experience.evidence[-1].model_copy(update={'recipe_scope_hash':candidate.scope_hash})
    forged=GenerationExperience(projection=experience.projection,candidate=candidate,
        evidence=(evidence,),evaluation_sources=experience.evaluation_sources)
    digest=canonical_sha256(forged.model_dump(mode='json'))
    raw=_canonical_json_bytes(forged)
    path=Path('state/video-generation/experience')/(digest+'.json')
    (tmp_path/path).write_bytes(raw)
    pointer=GenerationExperienceReceiptPointer(path=path,content_hash=digest,
        request_fingerprint=state.request.request_input_hash,file_sha256=hashlib.sha256(raw).hexdigest())
    changes={'generation_experiences':(*state.generation_experiences[:-1],pointer)}
    if closed:
        receipt=load_generation_visual_supersession(tmp_path,state.visual_supersession)
        values=receipt.model_dump(mode='python',exclude={'content_hash'})
        values.update(experience_content_hash=digest,evidence_hash=evidence.evidence_hash)
        receipt=GenerationVisualSupersessionReceipt.create(**values)
        raw=_canonical_json_bytes(receipt)
        path=Path('state/video-generation/supersessions')/(receipt.content_hash+'.json')
        (tmp_path/path).write_bytes(raw)
        changes['visual_supersession']=GenerationVisualSupersessionReceiptPointer(
            path=path,content_hash=receipt.content_hash,attempt_id=prior.attempt_id,
            request_fingerprint=state.request.request_input_hash,artifact_sha256=state.fetch_receipt.artifact_sha256,
            experience_content_hash=digest,file_sha256=hashlib.sha256(raw).hexdigest())
    corrupted=prior.model_copy(update={'video_generation_state':state.model_copy(update=changes)})
    manifest=manifest.model_copy(update={'attempts':tuple(corrupted if a.attempt_id==prior.attempt_id else a for a in manifest.attempts)})
    (tmp_path/'state/manifest.json').write_bytes(_canonical_json_bytes(manifest))
    if closed:
        with pytest.raises(AiVideoError):load_production_project(tmp_path/'project.yaml')
    else:
        with pytest.raises(AiVideoError):_supersede(writer,corrupted,forged)


def test_identical_reason_with_surrounding_whitespace_replays(tmp_path):
    writer,prior,experience=_ready_fixture(tmp_path)
    kwargs=dict(attempt_id=prior.attempt_id,expected_manifest_revision=writer._read_manifest().manifest_revision,
        experience_content_hash=prior.video_generation_state.generation_experiences[-1].content_hash,
        actor=ACTOR,authorization_receipt_id=AUTHORIZATION,reason='  Explicit user visual revision.  ',
        target_goal=_target_goal(),target_first_frame_sha256='f'*64)
    first=writer.supersede_video_generation(**kwargs)
    assert writer.supersede_video_generation(**kwargs)==first
