"""Visual requirements use the real SEMANTIC adjudicator, not a second score."""

import pytest

from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import EvidenceStrength, QaLayer, QaPolicy, QaVerdict, ReviewEvidence, ToolIdentity
from ai_video.production.review import adjudicate_review_evidence
from ai_video.production.visual_quality import VisualDirection, visual_requirements
from test_production_final_output import viewing_policy


def direction():
    return VisualDirection(
        typography="标题层级明确，字形清晰，文字有足够阅读时间。",
        palette="黑白与车身橙色呼应，强调色统一。",
        layout="文字避开人物与车辆细节，留白有秩序。",
        style="实拍与产品卡的光线、色调和图形风格连贯。",
        holistic="正常速度看完整片，画面、文字进出和视觉重心协调。",
    )


def visual_policy():
    original = viewing_policy()
    contract = FinalOutputContract(goal_id="visual", goal_version="1",
        user_goal="成片整体视觉协调", requirements=visual_requirements(direction()))
    return seal_artifact(QaPolicy.model_validate({
        **original.model_dump(mode="python"), "final_output": contract,
    }))


def visual_evidence(policy, *, verdict="pass", changed=None, **overrides):
    item = ReviewEvidence(artifact_id="visual-evidence", revision=1, content_hash="0" * 64,
        creation_receipt_id="offline", source_provenance=({"kind": "user_input", "reference": "fixture"},),
        evidence_id="visual-evidence", layer=QaLayer.SEMANTIC, strength=EvidenceStrength.HUMAN,
        render_output_sha256="e" * 64, timeline_fingerprint="f" * 64,
        dependency_graph_revision_id="b" * 64, tool_identity=ToolIdentity(name="fixture-evaluator", version="1"),
        measurement_contract_version="visual-review/1", subject_ids=("render",), measured_payload={})
    findings = [{"requirement_id": r.requirement_id,
        "verdict": verdict if r.visual_dimension == changed else "pass",
        "observation": "Explicit offline injected observation, not live viewing.",
        "visual_frames": [{"timestamp_ms": 1000, "frame_sha256": "c" * 64,
            "render_output_sha256": item.render_output_sha256}]}
        for r in policy.final_output.requirements]
    return seal_artifact(item.model_copy(update={"measured_payload": {
        "coverage_complete": True, "evaluator_identity": "fixture-evaluator@1",
        "final_output": {"contract_hash": policy.final_output.contract_hash,
            "review_request_content_hash": "a" * 64, "viewing_speed_milli": 1000,
            "viewing_mode": "full_playback", "findings": findings,
            "visual_frame_inventory": {"duration_ms": 2000, "frames": findings[0]["visual_frames"]}, **overrides},
    }}))


def judge(policy, item):
    return adjudicate_review_evidence(policy, QaLayer.SEMANTIC, (item,),
        review_request_content_hash="a" * 64)


@pytest.mark.parametrize("dimension", ["typography", "palette", "layout", "style", "holistic"])
@pytest.mark.parametrize("verdict", ["fail", "not_evaluated"])
def test_one_bad_visual_dimension_cannot_be_averaged_away(dimension, verdict):
    policy = visual_policy()
    assert judge(policy, visual_evidence(policy, verdict=verdict, changed=dimension)) == QaVerdict(verdict)


def test_complete_explicit_visual_review_passes_existing_semantic_gate():
    policy = visual_policy()
    assert judge(policy, visual_evidence(policy)) is QaVerdict.PASS


@pytest.mark.parametrize("mutation", ["missing", "old_frame", "empty_observation", "sampled", "wrong_contract", "wrong_request", "nonexistent_frame", "outside_duration", "missing_inventory"])
def test_incomplete_or_substituted_visual_evidence_never_passes(mutation):
    policy = visual_policy()
    item = visual_evidence(policy)
    data = item.model_dump(mode="python")
    payload = data["measured_payload"]["final_output"]
    if mutation == "missing":
        payload["findings"][0]["visual_frames"] = []
    elif mutation == "old_frame":
        payload["findings"][0]["visual_frames"][0]["render_output_sha256"] = "d" * 64
    elif mutation == "empty_observation":
        payload["findings"][0]["observation"] = "   "
    elif mutation == "sampled":
        payload["viewing_mode"] = "sampled_frames"
    elif mutation == "wrong_contract":
        payload["contract_hash"] = "d" * 64
    elif mutation == "nonexistent_frame":
        payload["findings"][0]["visual_frames"][0]["frame_sha256"] = "0" * 64
    elif mutation == "outside_duration":
        payload["visual_frame_inventory"]["duration_ms"] = 500
    elif mutation == "missing_inventory":
        payload.pop("visual_frame_inventory")
    else:
        payload["review_request_content_hash"] = "d" * 64
    assert judge(policy, type(item).model_validate(data)) is QaVerdict.NOT_EVALUATED


def test_sampled_visual_failure_remains_failure_even_without_full_playback():
    policy = visual_policy()
    item = visual_evidence(policy, changed="layout", verdict="fail", viewing_mode="sampled_frames")
    assert judge(policy, item) is QaVerdict.FAIL


def test_visual_factory_keeps_holistic_human_and_legacy_bytes_unchanged():
    from ai_video.production.final_output_contracts import FinalOutputRequirement
    old = {"requirement_id": "legacy", "observable": "Unchanged", "proof": "human"}
    assert FinalOutputRequirement.model_validate(old).model_dump(mode="json") == old
    assert visual_requirements(direction())[-1].proof == "human"
    with pytest.raises(ValueError):
        VisualDirection.model_validate({**direction().model_dump(), "layout": "  "})


def test_visual_requirements_reject_duplicate_dimensions_and_downgraded_holistic():
    from ai_video.production.final_output_contracts import FinalOutputRequirement
    requirements = visual_requirements(direction())
    with pytest.raises(ValueError):
        FinalOutputRequirement.model_validate({**requirements[-1].model_dump(), "proof": "evaluator"})
    with pytest.raises(ValueError):
        FinalOutputContract(goal_id="v", goal_version="1", user_goal="visual",
            requirements=requirements + (requirements[0].model_copy(update={"requirement_id": "duplicate"}),))
    with pytest.raises(ValueError):
        FinalOutputContract(goal_id="v", goal_version="1", user_goal="visual", requirements=requirements[:-1])


@pytest.mark.parametrize("verdict", ["pass", "fail", "not_evaluated"])
def test_real_committer_and_strict_reopen_block_unaccepted_visual_output(tmp_path, verdict):
    from dataclasses import replace
    from ai_video.errors import AiVideoError
    from ai_video.production.project import load_production_project
    from test_production_review import make_manifest_25_passing_review_fixture

    fixture = make_manifest_25_passing_review_fixture(tmp_path)
    policy = seal_artifact(visual_policy().model_copy(update={
        "required_layers": (QaLayer.TECHNICAL, QaLayer.SEMANTIC),
        "semantic_authorities": (ToolIdentity(name="base-e2e-analyzer", version="1"),)}))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=fixture.load_manifest().manifest_revision, attempt_id="visual-policy")
    technical = replace(fixture, policy=policy).run_required_review()

    def observations(request, original):
        data = visual_evidence(policy, changed="layout", verdict=verdict).model_dump(mode="python")["measured_payload"]
        data["evaluator_identity"] = "base-e2e-analyzer@1"
        data["final_output"]["review_request_content_hash"] = request.content_hash
        for frame in data["final_output"]["visual_frame_inventory"]["frames"]:
            frame["render_output_sha256"] = request.render_output_sha256
        for finding in data["final_output"]["findings"]:
            for frame in finding["visual_frames"]:
                frame["render_output_sha256"] = request.render_output_sha256
        return seal_artifact(original.model_copy(update={"strength": EvidenceStrength.HUMAN, "measured_payload": data}))

    visual = replace(fixture, policy=policy, review_layer=QaLayer.SEMANTIC,
        review_attempt_id="visual-review", evidence_factory=observations, expected_verdict=QaVerdict(verdict))
    pointer = visual.run_required_review()
    before = (tmp_path / "state/manifest.json").read_bytes()
    acceptance = seal_artifact(visual.acceptance(pointer).model_copy(update={"required_review_receipts": (technical, pointer)}))
    if verdict == "pass":
        accepted = fixture.committer.record_final_acceptance(acceptance,
            expected_manifest_revision=fixture.load_manifest().manifest_revision, attempt_id="visual-acceptance")
        assert load_production_project(tmp_path / "project.yaml").manifest == accepted
    else:
        with pytest.raises(AiVideoError):
            fixture.committer.record_final_acceptance(acceptance,
                expected_manifest_revision=fixture.load_manifest().manifest_revision, attempt_id="visual-acceptance")
        assert (tmp_path / "state/manifest.json").read_bytes() == before
        assert load_production_project(tmp_path / "project.yaml").manifest.final_acceptance_state is None
