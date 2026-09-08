"""Whole-output regressions through the existing Review / Repair entry points."""

from dataclasses import replace

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.final_output_contracts import FinalOutputContract, FinalOutputRequirement
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import ApprovedRepairReceipt, EvidenceStrength, QaLayer, QaPolicy, QaVerdict, ToolIdentity
from ai_video.production.project import load_production_project
from ai_video.production.review import adjudicate_review_evidence
from test_production_review import _qa_policy, evidence, _Manifest25ReviewFixture
from test_production_repair import make_manifest_25_failed_layout_review_fixture


def viewing_policy():
    return seal_artifact(QaPolicy.model_validate({
        **_qa_policy(required_layers=(QaLayer.SEMANTIC,)).model_dump(mode="python"),
        "semantic_requirement": "required",
        "semantic_authorities": (ToolIdentity(name="fixture-evaluator", version="1"),),
        "final_output": FinalOutputContract(goal_id="shot", goal_version="1",
            user_goal="Action by 1.5s, natural hold, and a natural whole shot",
            requirements=tuple(FinalOutputRequirement(requirement_id=name,
                observable=description, proof="human") for name, description in (
                    ("timing", "Action completes within 1.5s"),
                    ("natural", "Natural performance continues through cut"),
                    ("audio", "Original broadcast remains clear and complete")))),
    }))


def viewing_evidence(policy, verdicts, **overrides):
    return evidence(QaLayer.SEMANTIC, EvidenceStrength.HUMAN,
        evaluator_identity="fixture-evaluator@1", semantic_match=True,
        final_output={"contract_hash": policy.final_output.contract_hash,
            "review_request_content_hash": "a" * 64,
            "viewing_speed_milli": 1000,
            "findings": tuple({"requirement_id": name, "verdict": verdict,
                "observation": "Injected human observation for offline boundary test"}
                for name, verdict in verdicts.items()), **overrides})


@pytest.mark.parametrize("verdicts,expected", [
    ({"timing": "pass", "natural": "fail", "audio": "pass"}, QaVerdict.FAIL),
    ({"timing": "pass", "audio": "pass"}, QaVerdict.NOT_EVALUATED),
    ({"timing": "pass", "natural": "not_evaluated", "audio": "pass"}, QaVerdict.NOT_EVALUATED),
    ({"timing": "fail", "natural": "pass", "audio": "pass"}, QaVerdict.FAIL),
    ({"timing": "pass", "natural": "pass", "audio": "pass"}, QaVerdict.PASS),
])
def test_review_requires_complete_final_output_even_when_local_metric_passes(verdicts, expected):
    policy = viewing_policy()
    assert adjudicate_review_evidence(policy, QaLayer.SEMANTIC,
        (viewing_evidence(policy, verdicts),), review_request_content_hash="a" * 64) is expected


@pytest.mark.parametrize("change", [
    {"contract_hash": "b" * 64}, {"review_request_content_hash": "b" * 64},
    {"viewing_speed_milli": 2000},
])
def test_review_cannot_inherit_stale_or_non_normal_speed_human_conclusions(change):
    policy = viewing_policy()
    item = viewing_evidence(policy, dict.fromkeys(("timing", "natural", "audio"), "pass"), **change)
    assert adjudicate_review_evidence(policy, QaLayer.SEMANTIC, (item,),
        review_request_content_hash="a" * 64) is QaVerdict.NOT_EVALUATED


def approved_repair(tmp_path, *, with_goal=False):
    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    bundle = load_production_project(tmp_path / "project.yaml")
    if with_goal:
        policy = seal_artifact(viewing_policy().model_copy(update={
            "required_layers": (QaLayer.LAYOUT, QaLayer.SEMANTIC),
            "repair_authorities": bundle.qa_policy.repair_authorities,
            "semantic_authorities": (ToolIdentity(name="base-e2e-analyzer", version="1"),)}))
        fixture.committer.activate_qa_policy(policy,
            expected_manifest_revision=bundle.manifest.manifest_revision, attempt_id="goal-baseline-policy")
        _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
            timeline=fixture.render_fixture.timeline, policy=policy, review_layer=QaLayer.LAYOUT,
            review_fails=True, review_attempt_id="goal-baseline-layout").run_required_review()
        run_viewing_review(fixture, policy, attempt="goal-baseline-view", timing="fail")
        bundle = load_production_project(tmp_path / "project.yaml")
    _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
        timeline=fixture.render_fixture.timeline, policy=bundle.qa_policy,
        review_attempt_id="baseline-technical").run_required_review()
    manifest = fixture.load_manifest()
    request = seal_artifact(fixture.repair_request.model_copy(update={
        "base_manifest_revision": manifest.manifest_revision,
        "review_receipt_ids": tuple(p.review_id for p in manifest.active_review_receipts),
        "baseline_review_receipts": manifest.active_review_receipts,
        "qa_policy": manifest.active_qa_policy,
    }))
    approval = seal_artifact(ApprovedRepairReceipt.model_validate({
        **request.model_dump(mode="python"), "request_content_hash": request.content_hash,
        "artifact_id": "approved-whole-output-repair"}))
    fixture = replace(fixture, repair_request=request, approval=approval)
    approved = fixture.committer.record_approved_repair_receipt(request, approval,
        expected_manifest_revision=manifest.manifest_revision, attempt_id="approve-output-repair")
    pointer = approved.active_approved_repair
    fixture.committer.commit(fixture.state_commit_request(pointer))
    fixture.rerender()
    return fixture, pointer


def run_viewing_review(fixture, policy, *, attempt, timing="pass"):
    def observations(request, original):
        payload = viewing_evidence(policy, {"timing": timing, "natural": "pass", "audio": "pass"},
            review_request_content_hash=request.content_hash).measured_payload
        return seal_artifact(original.model_copy(update={"strength": EvidenceStrength.HUMAN,
            "measured_payload": {**payload, "evaluator_identity": "base-e2e-analyzer@1"}}))
    return _Manifest25ReviewFixture(root=fixture.root, committer=fixture.committer,
        timeline=fixture.render_fixture.timeline, policy=policy, review_layer=QaLayer.SEMANTIC,
        review_attempt_id=attempt, evidence_factory=observations,
        expected_verdict=QaVerdict(timing)).run_required_review()


def test_repair_cannot_close_on_local_pass_with_preserved_layer_omitted(tmp_path):
    fixture, pointer = approved_repair(tmp_path)
    fresh = fixture.run_fresh_layout_review()
    before = fixture.load_manifest()
    with pytest.raises(AiVideoError, match="[Ff]inal.output|[Nn]o.regression"):
        fixture.committer.record_repair_outcome(fixture.outcome(pointer, fresh),
            expected_manifest_revision=before.manifest_revision, attempt_id="incomplete-outcome")
    assert fixture.load_manifest() == before


def test_complete_new_reviews_close_repair_without_inheriting_old_media_pass(tmp_path):
    fixture, pointer = approved_repair(tmp_path)
    fresh = fixture.run_fresh_layout_review()
    bundle = load_production_project(tmp_path / "project.yaml")
    technical = _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
        timeline=fixture.render_fixture.timeline, policy=bundle.qa_policy,
        review_attempt_id="new-technical").run_required_review()
    outcome = seal_artifact(fixture.outcome(pointer, fresh).model_copy(update={
        "fresh_review_receipts": (fresh, technical)}))
    closed = fixture.committer.record_repair_outcome(outcome,
        expected_manifest_revision=fixture.load_manifest().manifest_revision, attempt_id="complete-outcome")
    assert closed.repair_outcome_receipts[-1].content_hash == outcome.content_hash
    assert load_production_project(tmp_path / "project.yaml").manifest == closed


@pytest.mark.parametrize("mutation", ["missing", "substituted"])
def test_approval_rejects_incomplete_or_substituted_baseline_before_write(tmp_path, mutation):
    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    pointers = fixture.repair_request.baseline_review_receipts
    if mutation == "missing":
        pointers = ()
    else:
        pointers = (pointers[0].model_copy(update={"file_sha256": "f" * 64}),)
    request = seal_artifact(fixture.repair_request.model_copy(update={"baseline_review_receipts": pointers}))
    approval = seal_artifact(ApprovedRepairReceipt.model_validate({
        **request.model_dump(mode="python"), "request_content_hash": request.content_hash}))
    before = fixture.load_manifest()
    with pytest.raises(AiVideoError, match="Final-output"):
        fixture.committer.record_approved_repair_receipt(request, approval,
            expected_manifest_revision=before.manifest_revision, attempt_id="invalid-baseline")
    assert fixture.load_manifest() == before


@pytest.mark.parametrize("operation", ["crop", "interpolate", "speedup", "occlude", "retime", "regenerate", "preview"])
def test_known_violation_rejects_any_repair_operation_before_execution(tmp_path, operation):
    from ai_video.production.models import RepairAction
    from ai_video.production.final_output_contracts import KnownRequirementViolation

    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    original = fixture.repair_request
    action = RepairAction(kind=operation, parameters_fingerprint="b" * 64,
        known_requirement_violations=(KnownRequirementViolation(requirement_id="natural",
            evidence_sha256="c" * 64, reason="Plan destroys required natural performance"),))
    scope = canonical_sha256({"repair_id": original.repair_id,
        "actor": original.actor.model_dump(mode="json"), "action": action.model_dump(mode="json"),
        "target_artifact_ids": list(original.exact_target_artifact_ids),
        "target_node_ids": list(original.exact_target_node_ids),
        "expected_invalidation_node_ids": list(original.expected_invalidation_node_ids)})
    request = seal_artifact(original.model_copy(update={"selected_repair_action": action,
        "authorization": original.authorization.model_copy(update={"scope_fingerprint": scope})}))
    approval = seal_artifact(ApprovedRepairReceipt.model_validate({
        **request.model_dump(mode="python"), "request_content_hash": request.content_hash}))
    before = fixture.load_manifest()
    with pytest.raises(AiVideoError, match="known requirement violations"):
        fixture.committer.record_approved_repair_receipt(request, approval,
            expected_manifest_revision=before.manifest_revision, attempt_id="known-bad-plan")
    assert fixture.load_manifest() == before


def test_repair_cannot_replace_frozen_policy_to_hide_old_failure(tmp_path):
    fixture, pointer = approved_repair(tmp_path)
    bundle = load_production_project(tmp_path / "project.yaml")
    changed = seal_artifact(bundle.qa_policy.model_copy(update={
        "policy_version": "new-goal", "revision": bundle.qa_policy.revision + 1}))
    fixture.committer.activate_qa_policy(changed,
        expected_manifest_revision=bundle.manifest.manifest_revision, attempt_id="explicit-new-goal")
    fresh = fixture.run_fresh_layout_review()
    before = fixture.load_manifest()
    with pytest.raises(AiVideoError, match="frozen goal"):
        fixture.committer.record_repair_outcome(fixture.outcome(pointer, fresh),
            expected_manifest_revision=before.manifest_revision, attempt_id="replace-goal")
    assert fixture.load_manifest() == before


@pytest.mark.parametrize("verdict,expected", [("fail", QaVerdict.FAIL),
    ("not_evaluated", QaVerdict.NOT_EVALUATED), ("pass", QaVerdict.PASS)])
def test_real_review_entry_records_whole_output_verdict_on_new_bytes(tmp_path, verdict, expected):
    from test_production_hyperframes import make_manifest_25_render_fixture
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.project import load_review_receipt

    render = make_manifest_25_render_fixture(tmp_path)
    render.render()
    committer = ProductionStateCommitter(tmp_path)
    policy = seal_artifact(viewing_policy().model_copy(update={
        "semantic_authorities": (ToolIdentity(name="base-e2e-analyzer", version="1"),)}))
    bundle = load_production_project(tmp_path / "project.yaml")
    committer.activate_qa_policy(policy, expected_manifest_revision=bundle.manifest.manifest_revision,
        attempt_id="select-final-output-contract")

    def observations(request, original):
        payload = viewing_evidence(policy, {"timing": "pass", "natural": verdict, "audio": "pass"},
            review_request_content_hash=request.content_hash).measured_payload
        return seal_artifact(original.model_copy(update={"strength": EvidenceStrength.HUMAN,
            "measured_payload": {**payload, "evaluator_identity": "base-e2e-analyzer@1"}}))

    pointer = _Manifest25ReviewFixture(root=tmp_path, committer=committer, timeline=render.timeline,
        policy=policy, review_layer=QaLayer.SEMANTIC, review_attempt_id="whole-output-review",
        evidence_factory=observations, expected_verdict=expected).run_required_review()
    assert load_review_receipt(tmp_path, pointer).verdict is expected
    assert load_production_project(tmp_path / "project.yaml").manifest.active_review_receipts == (pointer,)


def test_final_output_contract_changes_identity_without_rewriting_old_goal():
    original = viewing_policy()
    updated = seal_artifact(original.model_copy(update={"final_output": original.final_output.model_copy(
        update={"goal_version": "2", "user_goal": "An explicitly different user goal"})}))
    assert updated.content_hash != original.content_hash
    assert original.final_output.goal_version == "1"


@pytest.mark.parametrize("case", ["regression", "not_evaluated", "stale", "missing_evidence", "unfixed"])
def test_real_repair_outcome_blocks_regression_and_invalid_evidence(tmp_path, case):
    from ai_video.production.project import load_review_receipt

    fixture, pointer = approved_repair(tmp_path)
    if case == "unfixed":
        bundle = load_production_project(tmp_path / "project.yaml")
        fresh = _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
            timeline=fixture.render_fixture.timeline, policy=bundle.qa_policy,
            review_layer=QaLayer.LAYOUT, review_fails=True,
            review_attempt_id="still-failed-layout").run_required_review()
    else:
        fresh = fixture.run_fresh_layout_review()
    bundle = load_production_project(tmp_path / "project.yaml")

    def observations(request, original):
        updates = {"minimum_luma_milli": 0} if case == "regression" else {"coverage_complete": False}
        return seal_artifact(original.model_copy(update={
            "measured_payload": {**original.measured_payload, **updates}}))

    if case == "stale":
        technical = next(p for p in fixture.approval.baseline_review_receipts if p.layer is QaLayer.TECHNICAL)
    else:
        technical = _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
            timeline=fixture.render_fixture.timeline, policy=bundle.qa_policy,
            evidence_factory=observations if case in {"regression", "not_evaluated"} else None,
            expected_verdict={"regression": QaVerdict.FAIL, "not_evaluated": QaVerdict.NOT_EVALUATED}.get(case),
            review_attempt_id="post-repair-technical").run_required_review()
    outcome = seal_artifact(fixture.outcome(pointer, fresh).model_copy(update={
        "fresh_review_receipts": (fresh, technical)}))
    revision = fixture.load_manifest().manifest_revision
    before = (tmp_path / "state/manifest.json").read_bytes()
    if case == "missing_evidence":
        old = next(p for p in fixture.approval.baseline_review_receipts if p.layer is QaLayer.TECHNICAL)
        (tmp_path / load_review_receipt(tmp_path, old).evidence[0].path).unlink()
    with pytest.raises((AiVideoError, OSError), match=None if case == "missing_evidence" else "Final-output"):
        fixture.committer.record_repair_outcome(outcome,
            expected_manifest_revision=revision,
            attempt_id="invalid-repair-outcome")
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_final_acceptance_cannot_skip_repair_outcome_gate(tmp_path):
    fixture, _ = approved_repair(tmp_path)
    fresh = fixture.run_fresh_layout_review()
    bundle = load_production_project(tmp_path / "project.yaml")
    review = _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
        timeline=fixture.render_fixture.timeline, policy=bundle.qa_policy, review_layer=QaLayer.LAYOUT)
    before = fixture.load_manifest()
    with pytest.raises(AiVideoError, match="no-regression gate"):
        fixture.committer.record_final_acceptance(review.acceptance(fresh),
            expected_manifest_revision=before.manifest_revision, attempt_id="bypass-repair-comparison")
    assert fixture.load_manifest() == before


@pytest.mark.parametrize("new_goal", [False, True])
def test_explicit_new_goal_can_be_accepted_without_rewriting_failed_repair(tmp_path, new_goal):
    fixture, _ = approved_repair(tmp_path, with_goal=True)
    bundle = load_production_project(tmp_path / "project.yaml")
    goal = bundle.qa_policy.final_output
    if new_goal:
        goal = goal.model_copy(update={"goal_version": "2", "user_goal": "Explicit revised final-output goal"})
    policy = seal_artifact(bundle.qa_policy.model_copy(update={"policy_version": "2", "final_output": goal}))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=bundle.manifest.manifest_revision, attempt_id="new-goal-policy")
    layout = fixture.run_fresh_layout_review()
    semantic = run_viewing_review(fixture, policy, attempt="new-goal-view")
    bundle = load_production_project(tmp_path / "project.yaml")
    review = _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
        timeline=fixture.render_fixture.timeline, policy=policy, review_layer=QaLayer.LAYOUT)
    acceptance = seal_artifact(review.acceptance(layout).model_copy(update={
        "required_review_receipts": (layout, semantic)}))
    if not new_goal:
        with pytest.raises(AiVideoError, match="no-regression gate"):
            fixture.committer.record_final_acceptance(acceptance,
                expected_manifest_revision=bundle.manifest.manifest_revision, attempt_id="accept-new-goal")
    else:
        result = fixture.committer.record_final_acceptance(acceptance,
            expected_manifest_revision=bundle.manifest.manifest_revision, attempt_id="accept-new-goal")
        assert result.final_acceptance_state.active_receipt is not None
        assert result.repair_outcome_receipts == ()  # Old repair was never declared successful.
        assert fixture.approval.qa_policy != result.active_qa_policy
        assert load_production_project(tmp_path / "project.yaml").manifest == result


def test_repair_execution_reopens_baseline_evidence_before_effects(tmp_path):
    from ai_video.production.project import load_review_receipt

    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    before = fixture.load_manifest()
    approved = fixture.committer.record_approved_repair_receipt(fixture.repair_request, fixture.approval,
        expected_manifest_revision=before.manifest_revision, attempt_id="approve-before-evidence-loss")
    request = fixture.state_commit_request(approved.active_approved_repair)
    old = load_review_receipt(tmp_path, fixture.approval.baseline_review_receipts[0])
    (tmp_path / old.evidence[0].path).unlink()
    manifest_bytes = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises((AiVideoError, OSError)):
        fixture.committer.commit(request)
    assert (tmp_path / "state/manifest.json").read_bytes() == manifest_bytes


@pytest.mark.parametrize("remove", [False, True])
def test_qa_activation_cannot_rewrite_or_remove_same_goal_requirements(tmp_path, remove):
    fixture, _ = approved_repair(tmp_path, with_goal=True)
    bundle = load_production_project(tmp_path / "project.yaml")
    goal = None if remove else bundle.qa_policy.final_output.model_copy(update={
        "requirements": bundle.qa_policy.final_output.requirements[:1]})
    altered = seal_artifact(bundle.qa_policy.model_copy(update={"final_output": goal}))
    with pytest.raises(AiVideoError, match="explicit new goal version"):
        fixture.committer.activate_qa_policy(altered,
            expected_manifest_revision=bundle.manifest.manifest_revision, attempt_id="rewrite-goal-in-place")
    assert fixture.load_manifest() == bundle.manifest


def test_failed_repair_then_success_preserves_each_outcome_and_allows_acceptance(tmp_path):
    from ai_video.production.models import RepairOutcomeReceipt

    first, first_pointer = approved_repair(tmp_path)
    bundle = load_production_project(tmp_path / "project.yaml")
    def review(fixture, layer, attempt, fails=False):
        return _Manifest25ReviewFixture(root=tmp_path, committer=fixture.committer,
            timeline=fixture.render_fixture.timeline, policy=bundle.qa_policy,
            review_layer=layer, review_fails=fails, review_attempt_id=attempt).run_required_review()

    failed = review(first, QaLayer.LAYOUT, "first-repair-failed-layout", True)
    technical = review(first, QaLayer.TECHNICAL, "first-repair-technical")
    failed_outcome = seal_artifact(first.outcome(first_pointer, failed).model_copy(update={
        "fresh_review_receipts": (failed, technical), "verdict": "fail"}))
    closed_failure = first.committer.record_repair_outcome(failed_outcome,
        expected_manifest_revision=first.load_manifest().manifest_revision, attempt_id="close-first-failure")
    failed_pointer = closed_failure.repair_outcome_receipts[-1]
    original_failure_bytes = (tmp_path / failed_pointer.path).read_bytes()
    assert RepairOutcomeReceipt.model_validate_json(original_failure_bytes).verdict == "fail"

    bundle = load_production_project(tmp_path / "project.yaml")
    manifest = bundle.manifest
    original = first.repair_request
    action = original.selected_repair_action.model_copy(update={"parameters_fingerprint": "d" * 64})
    scope = canonical_sha256({"repair_id": "second-repair", "actor": original.actor.model_dump(mode="json"),
        "action": action.model_dump(mode="json"), "target_artifact_ids": list(original.exact_target_artifact_ids),
        "target_node_ids": list(original.exact_target_node_ids),
        "expected_invalidation_node_ids": list(original.expected_invalidation_node_ids)})
    request = seal_artifact(original.model_copy(update={"repair_id": "second-repair",
        "base_manifest_revision": manifest.manifest_revision, "dependency_graph": manifest.active_dependency_graph,
        "dependency_states_hash": canonical_sha256({"dependency_states": [s.model_dump(mode="json") for s in manifest.dependency_states]}),
        "render_state": manifest.active_render_state, "render_output_sha256": bundle.render_state.output.file_sha256,
        "timeline_fingerprint": bundle.render_state.timeline_fingerprint,
        "review_receipt_ids": tuple(p.review_id for p in manifest.active_review_receipts),
        "baseline_review_receipts": manifest.active_review_receipts, "selected_repair_action": action,
        "authorization": original.authorization.model_copy(update={"scope_fingerprint": scope})}))
    approval = seal_artifact(ApprovedRepairReceipt.model_validate({**request.model_dump(mode="python"),
        "request_content_hash": request.content_hash, "artifact_id": "second-approval"}))
    second = replace(first, repair_request=request, approval=approval)
    approved = second.committer.record_approved_repair_receipt(request, approval,
        expected_manifest_revision=manifest.manifest_revision, attempt_id="approve-second-repair")
    second_pointer = approved.active_approved_repair
    second.committer.commit(replace(second.state_commit_request(second_pointer), attempt_id="execute-second-repair"))
    second.rerender(attempt_id="second-repair-render")
    layout = review(second, QaLayer.LAYOUT, "second-repair-layout")
    technical = review(second, QaLayer.TECHNICAL, "second-repair-technical")
    outcome = seal_artifact(second.outcome(second_pointer, layout).model_copy(update={
        "fresh_review_receipts": (layout, technical)}))

    borrowed = seal_artifact(first.outcome(first_pointer, layout).model_copy(update={
        "fresh_review_receipts": (layout, technical)}))
    with pytest.raises(AiVideoError, match="borrow a later repair"):
        first.committer.record_repair_outcome(borrowed,
            expected_manifest_revision=second.load_manifest().manifest_revision, attempt_id="rewrite-first-as-success")
    second.committer.record_repair_outcome(outcome,
        expected_manifest_revision=second.load_manifest().manifest_revision, attempt_id="close-second-success")
    reviewer = _Manifest25ReviewFixture(root=tmp_path, committer=second.committer,
        timeline=second.render_fixture.timeline, policy=bundle.qa_policy, review_layer=QaLayer.LAYOUT)
    accepted = second.committer.record_final_acceptance(reviewer.acceptance(layout),
        expected_manifest_revision=second.load_manifest().manifest_revision, attempt_id="accept-second-repair")
    assert accepted.final_acceptance_state.active_receipt is not None
    assert (tmp_path / failed_pointer.path).read_bytes() == original_failure_bytes
    assert len(accepted.repair_outcome_receipts) == 2
    assert load_production_project(tmp_path / "project.yaml").manifest == accepted
