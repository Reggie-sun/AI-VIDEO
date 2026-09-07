from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError
from ai_video.production._state_commit_video import _StateCommitVideoMixin
from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase, PaidProviderAttemptPhase


def _limits(**updates):
    values = dict(
        task_id="guard-task",
        generation_forbidden=False,
        paid_submit_ceiling=2,
        paid_submits_used=0,
        local_batch_limit=2,
        local_batch_used=0,
        local_total_limit=2,
        local_total_used=0,
        local_resource_available=True,
    )
    values.update(updates)
    return ExecutionLimits(**values)


def _binding(*, limits, policy, shot_id="guard-shot"):
    candidate = SimpleNamespace(
        candidate_id="local-candidate",
        capability_id="local-capability",
        capabilities=SimpleNamespace(
            variants=(
                SimpleNamespace(
                    capability_id="local-capability",
                    execution_kind=SimpleNamespace(value="local"),
                ),
            )
        ),
    )
    return SimpleNamespace(
        inputs=SimpleNamespace(limits=limits, policy=policy, candidates=(candidate,)),
        decision=SimpleNamespace(selected_candidate_id="local-candidate"),
        context=SimpleNamespace(target_shot_id=shot_id),
        validate_request=lambda _request: None,
        validate_current_project=lambda _project: None,
    )


def _request(*, shot_id="guard-shot", request_hash="a" * 64):
    return SimpleNamespace(
        request_input_hash=request_hash,
        activation_scope=SimpleNamespace(request=SimpleNamespace(target_shot_id=shot_id)),
    )


class _Committer(_StateCommitVideoMixin):
    def __init__(self, bindings, requests) -> None:
        self._bindings = bindings
        self._requests = requests
        self._project_root = Path("/tmp/generation-execution-guards")

    def _load_production_project(self, _path):
        return SimpleNamespace(shots=tuple(SimpleNamespace(shot_id=shot_id,
            production_lineage=None) for shot_id in
            {"guard-shot", *(b.context.target_shot_id for b in self._bindings.values())}))

    def _reopen_generation_execution_binding(self, pointer):
        return self._bindings[pointer]

    def _reopen_video_request(self, pointer):
        return self._requests[pointer]


class _HistoryCommitter(_Committer):
    def __init__(self, bindings, requests, experiences, manifest) -> None:
        super().__init__(bindings, requests)
        self._experiences = experiences
        self._manifest = manifest
        self._project_root = Path("/tmp/generation-execution-guards")

    def _reopen_generation_experience(self, pointer):
        return self._experiences[id(pointer)]

    def _load_production_project(self, _path):
        loaded = super()._load_production_project(_path)
        loaded.manifest = self._manifest
        return loaded

    def _require_current_generation_acceptance(self, _loaded, _binding) -> None:
        return None


def _attempt(*, attempt_id, binding, request, local_submit=False):
    return SimpleNamespace(
        attempt_id=attempt_id,
        status=StateCommitStatus.RUNNING,
        paid_provider_state=None,
        video_generation_state=SimpleNamespace(
            generation_id=attempt_id,
            execution_binding=binding,
            request=request,
            local_submit_receipt=object() if local_submit else None,
            local_submit_intent=None,
            paid_submit_receipt=None,
            local_fetch_receipt=None,
            fetch_receipt=None,
            phase=VideoAttemptPhase.REQUEST,
        ),
    )


@pytest.mark.parametrize("verdict", ["FAIL", "NOT_EVALUATED", "PASS"])
def test_next_component_requires_previous_exact_required_findings_pass(monkeypatch, verdict):
    from test_production_generation_decision import setup_decision, evidence

    setup = setup_decision()
    candidate = setup["inputs"].candidates[0]
    observation = evidence(setup, verdict=verdict).model_copy(update={"shot_id": "child-a"})
    experience = SimpleNamespace(candidate=candidate, evidence=(observation,))
    old_pass = SimpleNamespace(candidate=candidate, evidence=(
        evidence(setup, verdict="PASS").model_copy(update={"shot_id": "child-a", "attempt_id": "old",
            "request_hash": "d" * 64, "artifact_sha256": "e" * 64}),))
    lineage = SimpleNamespace(source=None, coverage_id="coverage")
    children = tuple(SimpleNamespace(shot_id=name, production_lineage=lineage)
                     for name in ("child-a", "child-b"))
    parent = SimpleNamespace(production_intent=SimpleNamespace(coverage_options=(
        SimpleNamespace(coverage_id="coverage", units=children),)))
    monkeypatch.setattr("ai_video.production.production_strategy_reader.production_parent_context",
                        lambda *_: (parent, (), None, None))
    loaded = SimpleNamespace(shots=children)
    binding = SimpleNamespace(context=SimpleNamespace(target_shot_id="child-b"),
                              inputs=SimpleNamespace(experiences=(experience, old_pass)))
    committer = _Committer({}, {})
    if verdict == "PASS":
        committer._require_production_predecessors(loaded, binding, (old_pass, experience))
    else:
        with pytest.raises(AiVideoError, match="not all PASS"):
            committer._require_production_predecessors(loaded, binding, (old_pass, experience))


def test_durable_local_submit_count_cannot_be_reset_by_input_projection() -> None:
    previous = _binding(limits=_limits(local_total_used=1, local_batch_used=1), policy=DecisionPolicy())
    current = _binding(limits=_limits(), policy=DecisionPolicy())
    committer = _Committer(
        {"previous": previous}, {"previous-request": _request(request_hash="b" * 64)}
    )
    manifest = SimpleNamespace(
        attempts=(
            _attempt(
                attempt_id="previous-attempt",
                binding="previous",
                request="previous-request",
                local_submit=True,
            ),
        )
    )
    current_state = SimpleNamespace(generation_id="current-attempt")

    with pytest.raises(AiVideoError, match="submit counters"):
        committer._require_persisted_generation_limits(
            manifest, current_state, current
        )


@pytest.mark.parametrize("task_id", ["guard-task", "new-task-name"])
def test_same_shot_cannot_expand_persisted_resample_policy(task_id) -> None:
    previous = _binding(limits=_limits(), policy=DecisionPolicy(max_resamples=1))
    current = _binding(limits=_limits(task_id=task_id), policy=DecisionPolicy(max_resamples=2))
    committer = _Committer(
        {"previous": previous}, {"previous-request": _request(request_hash="b" * 64)}
    )
    manifest = SimpleNamespace(
        attempts=(
            _attempt(
                attempt_id="previous-attempt",
                binding="previous",
                request="previous-request",
            ),
        )
    )
    current_state = SimpleNamespace(generation_id="current-attempt")

    with pytest.raises(AiVideoError, match="repair policy"):
        committer._require_persisted_generation_limits(
            manifest, current_state, current
        )


def test_global_durable_experience_cannot_be_omitted_from_next_binding() -> None:
    current = _binding(limits=_limits(), policy=DecisionPolicy())
    current.inputs = SimpleNamespace(
        **vars(current.inputs), evidence=(), experiences=()
    )
    stale_evidence = SimpleNamespace(evidence_hash="c" * 64, shot_id="other-shot")
    experience = SimpleNamespace(
        evidence=(stale_evidence,), model_dump=lambda mode: {"experience": "old"}
    )
    pointer = SimpleNamespace(
        content_hash=canonical_sha256(experience.model_dump(mode="json"))
    )
    unrelated = _attempt(
        attempt_id="unrelated-attempt",
        binding=None,
        request="unrelated-request",
    )
    unrelated.video_generation_state.generation_experiences = (pointer,)
    unrelated.video_generation_state.execution_binding = None
    manifest = SimpleNamespace(attempts=(unrelated,))
    committer = _HistoryCommitter(
        {"current": current},
        {"current-request": _request(), "unrelated-request": _request(shot_id="other-shot")},
        {id(pointer): experience},
        manifest,
    )
    state = SimpleNamespace(
        generation_id="current-attempt", execution_binding="current", qualification_binding=None
    )

    with pytest.raises(AiVideoError, match="stale relative to durable history"):
        committer._require_submit_execution_binding(
            manifest, state, _request()
        )


@pytest.mark.parametrize("kind", ["local", "paid"])
def test_pending_submit_intent_on_another_shot_reserves_task_count(kind):
    previous = _binding(limits=_limits(), policy=DecisionPolicy(), shot_id="other-shot")
    current = _binding(limits=_limits(), policy=DecisionPolicy())
    prior = _attempt(attempt_id="pending", binding="previous", request="old-request")
    if kind == "local":
        prior.video_generation_state.local_submit_intent = object()
    else:
        prior.paid_provider_state = SimpleNamespace(
            phase=PaidProviderAttemptPhase.SUBMIT_INTENT, submit_receipt=None)
    committer = _Committer({"previous": previous}, {"old-request": _request(shot_id="other-shot")})
    with pytest.raises(AiVideoError, match="submit counters"):
        committer._require_persisted_generation_limits(
            SimpleNamespace(attempts=(prior,)), SimpleNamespace(generation_id="new"), current)


@pytest.mark.parametrize("later_state", ["unknown", "fetched"])
def test_not_submitted_experience_cannot_hide_later_durable_outcome(later_state):
    current = _binding(limits=_limits(), policy=DecisionPolicy())
    old_evidence = SimpleNamespace(evidence_hash="c" * 64, shot_id="guard-shot", outcome="not_submitted", artifact_sha256=None)
    experience = SimpleNamespace(evidence=(old_evidence,), model_dump=lambda mode: {"experience": "old"})
    pointer = SimpleNamespace(content_hash=canonical_sha256(experience.model_dump(mode="json")))
    current.inputs = SimpleNamespace(**vars(current.inputs), evidence=(old_evidence,), experiences=(experience,))
    prior = _attempt(attempt_id="old", binding="previous", request="old-request")
    prior.video_generation_state.generation_experiences = (pointer,)
    if later_state == "unknown":
        prior.status = StateCommitStatus.OUTCOME_UNKNOWN
        prior.video_generation_state.local_submit_intent = object()
        message = "explicit recovery"
    else:
        prior.video_generation_state.local_fetch_receipt = SimpleNamespace(artifact_sha256="d" * 64)
        message = "exact media evaluation"
    manifest = SimpleNamespace(attempts=(prior,))
    committer = _HistoryCommitter({"current": current, "previous": current},
        {"old-request": _request()}, {id(pointer): experience}, manifest)
    with pytest.raises(AiVideoError, match=message):
        committer._require_submit_execution_binding(manifest,
            SimpleNamespace(generation_id="new", execution_binding="current"), _request())


def test_unpersisted_extra_experience_cannot_influence_next_submit():
    current = _binding(limits=_limits(), policy=DecisionPolicy())
    invented = SimpleNamespace(evidence_hash="c" * 64)
    experience = SimpleNamespace(evidence=(invented,), model_dump=lambda mode: {"experience": "invented"})
    current.inputs = SimpleNamespace(**vars(current.inputs), evidence=(invented,), experiences=(experience,))
    manifest = SimpleNamespace(attempts=())
    committer = _HistoryCommitter({"current": current}, {}, {}, manifest)
    with pytest.raises(AiVideoError, match="complete durable experience"):
        committer._require_submit_execution_binding(manifest,
            SimpleNamespace(generation_id="new", execution_binding="current"), _request())


@pytest.mark.parametrize("latest", [None, "c" * 64])
def test_permit_requires_latest_from_ordered_durable_shot_history(latest):
    current = _binding(limits=_limits(), policy=DecisionPolicy())
    observations = tuple(SimpleNamespace(evidence_hash=key * 64, shot_id="guard-shot",
        outcome="media", artifact_sha256="e" * 64) for key in ("c", "d"))
    experiences = tuple(SimpleNamespace(evidence=(entry,), model_dump=lambda mode, index=index:
        {"experience": index}) for index, entry in enumerate(observations))
    pointers = tuple(SimpleNamespace(content_hash=canonical_sha256(x.model_dump(mode="json")))
                     for x in experiences)
    current.inputs = SimpleNamespace(**vars(current.inputs), evidence=observations,
                                    experiences=experiences, latest_attempt_hash=latest)
    prior = _attempt(attempt_id="old", binding="previous", request="old-request")
    prior.video_generation_state.generation_experiences = pointers
    prior.video_generation_state.local_fetch_receipt = SimpleNamespace(artifact_sha256="e" * 64)
    manifest = SimpleNamespace(attempts=(prior,))
    committer = _HistoryCommitter({"current": current, "previous": current},
        {"old-request": _request()}, {id(p): x for p, x in zip(pointers, experiences)}, manifest)
    with pytest.raises(AiVideoError, match="ordered durable history"):
        committer._require_submit_execution_binding(manifest,
            SimpleNamespace(generation_id="new", execution_binding="current"), _request())
