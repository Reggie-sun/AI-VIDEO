"""Frozen historical evidence replays for generation-feedback policy boundaries.

The historical runs predate the typed production projection.  This test maps
their source-addressed Gate observations into a sealed, reconstructed raw-stage
requirement inventory.  It never turns an old observation into a PASS or claims
that a counterfactual policy would have improved media quality.
"""

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.production.generation_diagnosis import AttemptEvidence, Finding, diagnose_attempt
from ai_video.production.generation_experience import GenerationExperience
from ai_video.production.generation_feedback import GenerationHistory, derive_generation_interventions
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.hashing import canonical_sha256
from ai_video.production.shot_router import AdapterCompilerContract, VideoGenerationResolver
from ai_video.production.video import VideoExecutionKind, VideoGenerationMode

from test_production_generation_decision import acceptance_policy, recipe_with_rules, setup_decision
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_shot_router import _capabilities, _output, _profile, _variant


ROOT = Path(__file__).parents[1]
FIXTURE = Path(__file__).with_name("fixtures") / "generation_feedback_history.json"


def _history():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _rules(names):
    dimensions = {
        "left_hand_raise_right_hand_phone": "action",
        "foreground_identity_and_missing_reflection": "reflection",
        "exact_pa_dialogue_timing": "dialogue",
        "approximately_two_centimeter_hover": "action",
        "pa_voice_and_foreground_silence": "dialogue",
        "lighting_continuity": "continuity",
        "hand_phone": "action",
        "palm_orientation": "action",
        "reflection": "reflection",
        "camera": "camera",
        "generated_captions": "captions",
        "hover": "action",
        "reflection_absence": "reflection",
        "identity_badge": "identity",
        "dialogue_exact": "dialogue",
        "audio_perceptual": "audio",
        "final_caption": "captions",
    }
    return tuple(RequirementExpression(
        requirement_id=name, level="acceptance", stage="raw_generation",
        dimension=dimensions[name], observable=f"reconstructed historical {name}",
        tolerance="source gate verdict", measurement="frozen historical Gate mapping",
        proof="analyzer", intent_paths=("historical_replay",), native_text=(),
        production_owner="historical_replay",
    ) for name in sorted(names))


def _record_candidate_setup(record):
    """Reconstruct one historical source identity without claiming its projection survived."""
    reference = hashlib.sha256(record["id"].encode()).hexdigest()
    setup = setup_decision(reference_hash=reference)
    projection = _replace_requirement(
        setup["projection"],
        source_request_content_hash=hashlib.sha256(record["requirement_hash"].encode()).hexdigest(),
    )
    original = setup["inputs"].candidates[0]
    recipe = recipe_with_rules(original.recipe, _rules(_history()["accepted_generation_requirements"]))
    source = _history()["frozen_source_projection"].get(record["id"],
                                                         _history()["frozen_source_projection"]["h3"])
    remote = record["provider"] == "vidu"
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        capability_id=f"{record['provider']}-{record['id']}",
        execution_kind=VideoExecutionKind.REMOTE if remote else VideoExecutionKind.LOCAL,
        provider_kind=record["provider"], model_id=record["model"],
    )
    compiler = AdapterCompilerContract.create(
        compiler_id=f"historical-{record['provider']}-compiler",
        compiler_version=f"source-{source['adapter_compiler_hash'][:16]}",
    )
    profile = _profile(profile_id=f"historical-{record['provider']}-{record['id']}",
                       profile_sha256=source["profile_sha256"])
    recipe = recipe.model_copy(update={
        "profile_sha256": profile.profile_sha256,
        "compiler_hash": compiler.compiler_hash,
        "requirement_hash": projection.requirement.requirement_hash,
    })
    candidate = original.model_copy(update={
        "candidate_id": f"{record['provider']}/{record['id']}",
        "provider_profile": profile,
        "capabilities": _capabilities(variant, provider_name=record["provider"]),
        "capability_id": variant.capability_id,
        "compiler_contract": compiler,
        "output_requirement": _output(),
        "recipe": recipe,
    })
    facts_hash = canonical_sha256(projection.requirement.model_dump(
        mode="json", exclude={"requirement_id", "requirement_hash"}))
    return setup, projection, candidate, facts_hash


def _attempt(record, *, candidate, facts_hash, shot_id):
    findings = ()
    if record["outcome"] == "media":
        findings = tuple(
            Finding(requirement_id=name, rubric_hash=candidate.recipe.rubric_hash,
                    stage="raw_generation", proof="analyzer", verdict=verdict,
                    source_sha256=record["gate"][1],
                    observation=f"reconstructed from frozen {record['id']} Gate")
            for verdict, names in (("FAIL", record["failed"]),
                                   ("NOT_EVALUATED", record["not_evaluated"]))
            for name in names
        )
    return AttemptEvidence(
        task_id="frozen-historical-replay", shot_id=shot_id,
        attempt_id=record["id"], recipe_scope_hash=candidate.scope_hash,
        facts_hash=facts_hash, rubric_hash=candidate.recipe.rubric_hash,
        request_hash=record["request_hash"], artifact_sha256=record["artifact_sha256"],
        outcome=record["outcome"], findings=findings,
        runtime_reason=record.get("runtime_reason"),
    )


def _experiences(records):
    entries = []
    for record in records:
        setup, projection, candidate, facts_hash = _record_candidate_setup(record)
        evidence = _attempt(record, candidate=candidate, facts_hash=facts_hash,
                            shot_id=setup["context"].target_shot_id)
        entries.append((setup, projection, candidate,
                        GenerationExperience(projection=projection, candidate=candidate, evidence=(evidence,))))
    return tuple(entries)


def _feedback_proposals(records):
    entries = _experiences(records)
    setup, projection, candidate, _ = entries[-1][:4]
    experiences = tuple(entry[-1] for entry in entries)
    history = GenerationHistory(experiences=experiences,
                                latest_attempt_hash=experiences[-1].evidence[0].evidence_hash)
    proposals, conflicts = derive_generation_interventions(
        projection=projection, candidates=(candidate,), history=history,
        policy=setup["inputs"].policy)
    return proposals, conflicts, entries


def test_frozen_sources_are_present_and_hash_bound_without_touching_media():
    fixture = _history()
    assert fixture["schema"] == "generation-feedback-history/1"
    assert fixture["reconstructed_fields"]
    assert fixture["reconstructed_proof"] == "analyzer"
    assert len(fixture["records"]) == 19
    source_paths = [(record["id"], pair) for record in fixture["records"]
                    for pair in (record["gate"], record["compiled"])]
    if not all((ROOT / path).is_file() for _, (path, _) in source_paths):
        pytest.skip("historical run archive is not present in this checkout; fixture remains self-contained")
    for record in fixture["records"]:
        for path, expected_hash in (record["gate"], record["compiled"]):
            source = ROOT / path
            assert source.is_file(), path
            assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_hash
    assert not any("PASS" in record.get("failed", ()) for record in fixture["records"])


def test_legacy_replay_recipe_and_experience_serialization_are_frozen():
    """The simulated non-Vidu replay stays a /1-era contract, including no goal."""
    fixture = _history()
    record = next(item for item in fixture["records"] if item["id"] == "h3-015")
    experience = _experiences((record,))[0][-1]
    candidate = experience.candidate
    recipe_payload = candidate.recipe.model_dump(mode="json")
    candidate_payload = candidate.model_dump(mode="json")
    evidence_payload = experience.evidence[0].model_dump(mode="json")
    diagnosis = diagnose_attempt(experience.evidence[0], candidate.recipe)

    assert canonical_sha256(fixture) == "afc752e430d183a377418ebb86df9343d2af503df6936347d7bc102fddebfaaa"
    assert candidate.recipe.recipe_hash == "0582649a4c6b3eaf0071f5d8bfe87005a436b4ffc8d09cf5013572ab9fa34b95"
    assert canonical_sha256(experience.model_dump(mode="json")) == "de3a44ea29d9c79b69cc61cbcf618cb233332efc33fb2eafd2a720eb27e6a977"
    assert experience.evidence[0].evidence_hash == "6c7a42c6b193071f87583466ec838cac653bcaa80392f8c974a8502ca93990d6"
    assert "final_output_goal" not in candidate_payload
    assert recipe_payload["contract_version"] == "generation-recipe/1"
    assert recipe_payload["comparison"] is None
    assert evidence_payload["actual_delta"] == []
    assert evidence_payload["intervention_id"] is None
    assert GenerationExperience.model_validate(
        experience.model_dump(mode="python")
    ).model_dump(mode="json") == experience.model_dump(mode="json")
    assert diagnosis.failure_classes == ("EVIDENCE_GAP", "QUALITY_FAILURE")
    assert diagnosis.failed_requirements == (
        "exact_pa_dialogue_timing", "left_hand_raise_right_hand_phone",
    )


def test_h3_015_to_030_replay_preserves_evidence_gaps_and_oom_as_non_quality_failure():
    records = [record for record in _history()["records"] if record["id"].startswith("h3-")]
    entries = _experiences(records)
    attempts = [entry[-1].evidence[0] for entry in entries]
    candidate = entries[-1][2]
    setup, projection, _, _ = entries[-1]
    facts_hash = canonical_sha256(projection.requirement.model_dump(
        mode="json", exclude={"requirement_id", "requirement_hash"}))
    media = attempts[:-1]
    diagnoses = [diagnose_attempt(attempt, candidate.recipe) for attempt in media]
    assert all("QUALITY_FAILURE" in diagnosis.failure_classes for diagnosis in diagnoses)
    assert all("EVIDENCE_GAP" in diagnosis.failure_classes for diagnosis in diagnoses)
    assert all("exact_pa_dialogue_timing" in diagnosis.failed_requirements for diagnosis in diagnoses)
    assert sum("foreground_identity_and_missing_reflection" in diagnosis.failed_requirements
               for diagnosis in diagnoses) == 10
    oom = diagnose_attempt(attempts[-1], candidate.recipe)
    assert oom.failure_classes == ("RUNTIME_FAILURE",)
    assert not oom.failed_requirements

    # The latest source result still has required proof gaps, so the Router
    # stops for evidence repair before it can treat any historical FAIL as a
    # license for an equivalent retry.
    current_task_media = tuple(attempt.model_copy(update={"task_id": setup["inputs"].limits.task_id})
                               for attempt in media)
    latest = current_task_media[-1]
    result = VideoGenerationResolver().resolve_requirement(
        **{**{key: value for key, value in setup.items() if key != "inputs"},
           "projection": projection},
        inputs=setup["inputs"].model_copy(update={
            "projection_hash": projection.projection_hash, "facts_hash": facts_hash,
            "candidates": (candidate,), "rubric_hash": candidate.recipe.rubric_hash,
            "evidence": current_task_media, "latest_attempt_hash": latest.evidence_hash,
            "historical_recipes": tuple(entry[2] for entry in entries),
        }),
    )
    assert result.disposition == "EVIDENCE_GAP"
    assert result.routing is None


def test_h3_repeated_cross_recipe_failures_emit_authoring_reassessment_not_another_sample():
    records = [record for record in _history()["records"]
               if record["id"].startswith("h3-") and record["outcome"] == "media"]
    assert len({record["requirement_hash"] for record in records}) > 3
    proposals, conflicts, entries = _feedback_proposals(records)
    assert not conflicts
    assert proposals
    assert len({entry[2].scope_hash for entry in entries}) == len(records)
    assert all(proposal.disposition in {"SPLIT_SHOT", "CAPABILITY_BOUNDARY"}
               for proposal in proposals)
    assert all(proposal.disposition != "GENERATE_ONCE" for proposal in proposals)


def test_h3_replays_every_historical_prefix_and_counts_only_conditional_avoided_attempts():
    records = [record for record in _history()["records"]
               if record["id"].startswith("h3-") and record["outcome"] == "media"]
    threshold = setup_decision()["inputs"].policy.repeated_failure_threshold
    prefix_proposals = []
    for end in range(1, len(records) + 1):
        proposals, conflicts, _ = _feedback_proposals(records[:end])
        assert not conflicts
        prefix_proposals.append(proposals)
    first_reassessment = next(index for index, proposals in enumerate(prefix_proposals, start=1)
                               if proposals)
    assert first_reassessment == threshold
    assert all(not proposals for proposals in prefix_proposals[:first_reassessment - 1])
    assert all(proposal.disposition != "GENERATE_ONCE"
               for proposals in prefix_proposals[first_reassessment - 1:]
               for proposal in proposals)
    # This is a policy counterfactual only: it counts source attempts after the
    # first authoring reassessment, never successful media or saved cost.
    conditionally_avoided = len(records) - first_reassessment
    assert conditionally_avoided == sum(bool(proposals) for proposals in prefix_proposals) - 1
    assert conditionally_avoided > 0


def test_vidu_02_to_04_cross_recipe_caption_failures_remain_failures_and_reassess():
    records = [record for record in _history()["records"] if record["id"].startswith("vidu-")]
    assert len({record["request_hash"] for record in records}) == 3
    assert len({record["requirement_hash"] for record in records}) == 2
    assert all("generated_captions" in record["failed"] for record in records)
    assert all(record["artifact_sha256"] is not None for record in records)

    proposals, conflicts, entries = _feedback_proposals(records)
    assert not conflicts
    assert proposals
    assert len({entry[2].scope_hash for entry in entries}) == len(records)
    assert {entry[2].capabilities.provider_name for entry in entries} == {"vidu"}
    assert all(proposal.disposition in {"SPLIT_SHOT", "CAPABILITY_BOUNDARY"}
               for proposal in proposals)
    assert all(proposal.disposition != "GENERATE_ONCE" for proposal in proposals)
