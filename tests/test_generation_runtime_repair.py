"""Runtime repair grant: planner resume branch and committer one-use lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.generation_runtime_repair import (
    MAX_RUNTIME_REPAIRS_PER_SHOT,
    RuntimeRepairAuthorization,
    RuntimeRepairGrant,
)
from ai_video.production.models import (
    ActorIdentity,
    StateCommitStatus,
)
from ai_video.production.video import VideoTaskState
from ai_video.production.video_generation import VideoGenerationService

from test_production_generation_decision import decide, evidence, setup_decision

ACTOR = ActorIdentity(actor_id="test-runtime-owner", actor_kind="automation")
REPAIR_BASIS = "local_resource_exhaustion: co-tenant VRAM holder stopped before re-submit"


def _grant(entry, *, consumed=False, attempt=None, evidence_hash=None):
    authorization = RuntimeRepairAuthorization.create(
        attempt_id=attempt or entry.attempt_id,
        evidence_hash=evidence_hash or entry.evidence_hash,
        repair_basis=REPAIR_BASIS,
        actor=ACTOR,
        expected_manifest_revision=0,
    )
    return RuntimeRepairGrant(authorization=authorization, consumed=consumed)


def test_runtime_failure_blocks_without_grant():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash)
    assert result.disposition == "RUNTIME_FAILURE"
    assert result.runtime_repair is None


def _retarget_case(*, required_hash=None):
    from ai_video.production.generation_runtime_repair import PaidNoEffectRetarget
    setup = setup_decision(remote=True, seed_supported=False)
    old = setup["inputs"].candidates[0]
    profile = old.provider_profile.model_copy(update={"profile_sha256": "a" * 64,
        "profile_path": Path("provider-profiles/" + "a" * 64 + ".json")})
    recipe = old.recipe.model_copy(update={"profile_sha256": profile.profile_sha256,
        **({"requirement_hash": required_hash} if required_hash else {})})
    target = old.model_copy(update={"provider_profile": profile, "recipe": recipe})
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    grant = RuntimeRepairGrant(authorization=RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/3", attempt_id=entry.attempt_id,
        evidence_hash=entry.evidence_hash, repair_basis="explicit model/profile recovery after paid rejection",
        actor=ACTOR, expected_manifest_revision=0,
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint="d" * 64, target_scope_hash=target.scope_hash)), consumed=False)
    limits = setup["inputs"].limits.model_copy(update={"allowed_remote_candidates": (target.candidate_id,)})
    return setup, old, target, entry, grant, limits


def test_paid_no_effect_retarget_selects_only_exact_authorized_strategy():
    setup, old, target, entry, grant, limits = _retarget_case()
    result = decide(setup, candidates=(target,), historical_recipes=(old,), limits=limits,
        evidence=(entry,), latest_attempt_hash=entry.evidence_hash, runtime_repairs=(grant,))
    assert target.scope_hash != old.scope_hash
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair == grant.authorization
    assert result.routing.provider_bound_request.provider_profile == target.provider_profile


def test_paid_no_effect_provider_switch_requires_exact_output_and_one_use_grant():
    from ai_video.production.generation_runtime_repair import (
        PaidNoEffectRetarget, retarget_preserves_strategy,
    )
    from ai_video.production.video import VideoProviderCapabilities

    setup, old, target, entry, _, limits = _retarget_case()
    capabilities = VideoProviderCapabilities.create(
        provider_name="second-provider", variants=target.capabilities.variants,
    )
    target = target.model_copy(update={"capabilities": capabilities})
    grant = RuntimeRepairGrant(authorization=RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/3", attempt_id=entry.attempt_id,
        evidence_hash=entry.evidence_hash, repair_basis="explicit exact-contract provider switch",
        actor=ACTOR, expected_manifest_revision=0,
        paid_no_effect_retarget=PaidNoEffectRetarget(
            submit_receipt_fingerprint="d" * 64, target_scope_hash=target.scope_hash)), consumed=False)
    assert retarget_preserves_strategy(old, target)
    arguments = dict(candidates=(target,), historical_recipes=(old,), limits=limits,
        evidence=(entry,), latest_attempt_hash=entry.evidence_hash)
    result = decide(setup, **arguments, runtime_repairs=(grant,))
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair == grant.authorization
    assert decide(setup, **arguments).disposition == "RUNTIME_FAILURE"
    assert decide(setup, **arguments, runtime_repairs=(
        RuntimeRepairGrant(authorization=grant.authorization, consumed=True),
    )).disposition == "RUNTIME_FAILURE"
    changed = target.model_copy(update={"output_requirement":
        target.output_requirement.model_copy(update={"width": 960})})
    assert not retarget_preserves_strategy(old, changed)


def _paid_known_failure_reference_case():
    from ai_video.production.final_output_contracts import (
        FinalOutputContract,
        FinalOutputRequirement,
    )
    from ai_video.production.generation_runtime_repair import PaidKnownFailureRetarget

    old_setup = setup_decision(remote=True, seed_supported=False)
    setup = setup_decision(remote=True, seed_supported=False, reference_hash="f" * 64)
    goal = FinalOutputContract(
        goal_id="asset-first-continuity",
        goal_version="1",
        user_goal="Preserve the approved action and continuity in the final output.",
        requirements=(FinalOutputRequirement(
            requirement_id="continuous-action",
            observable="The approved action remains continuous through the cut.",
            proof="human",
        ),),
    )
    old = old_setup["inputs"].candidates[0].model_copy(update={
        "final_output_goal": goal,
    })
    target = setup["inputs"].candidates[0].model_copy(update={
        "final_output_goal": goal,
    })
    setup["inputs"] = setup["inputs"].model_copy(update={"candidates": (target,)})
    entry = evidence(old_setup, candidate=old, outcome="runtime_failure", task_id="task")
    grant = RuntimeRepairGrant(authorization=RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/4",
        attempt_id=entry.attempt_id,
        evidence_hash=entry.evidence_hash,
        repair_basis="explicit original-image input strategy after accepted terminal failure",
        actor=ACTOR,
        expected_manifest_revision=1,
        paid_known_failure_retarget=PaidKnownFailureRetarget(
            paid_submit_receipt_fingerprint="d" * 64,
            failed_observation_fingerprint="e" * 64,
            target_scope_hash=target.scope_hash,
        ),
    ), consumed=False)
    limits = setup["inputs"].limits.model_copy(update={
        "allowed_remote_candidates": (target.candidate_id,),
    })
    return setup, old, target, entry, grant, limits


def test_paid_known_failure_retarget_selects_exact_reference_strategy_and_keeps_goal():
    setup, old, target, entry, grant, limits = _paid_known_failure_reference_case()
    result = decide(setup, candidates=(target,), historical_recipes=(old,), limits=limits,
        evidence=(entry,), latest_attempt_hash=entry.evidence_hash, runtime_repairs=(grant,))
    assert old.capabilities.variants[0].mode.value == "text_to_video"
    assert target.capabilities.variants[0].mode.value == "image_to_video"
    assert target.final_output_goal == old.final_output_goal
    assert target.recipe.expressions == old.recipe.expressions
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair == grant.authorization
    assert result.selected_candidate_id == target.candidate_id


def test_paid_known_failure_retarget_rejects_changed_output_or_acceptance_criteria():
    from ai_video.production.generation_runtime_repair import paid_failure_retarget_preserves_strategy

    _, old, target, _, _, _ = _paid_known_failure_reference_case()
    changed_output = target.model_copy(update={
        "output_requirement": target.output_requirement.model_copy(update={
            "duration_seconds": target.output_requirement.duration_seconds + 1,
        }),
    })
    changed_goal = target.model_copy(update={
        "final_output_goal": target.final_output_goal.model_copy(update={
            "requirements": (target.final_output_goal.requirements[0].model_copy(update={
                "observable": "The action may break before the cut.",
            }),),
        }),
    })
    changed_criterion = target.model_copy(update={
        "recipe": target.recipe.model_copy(update={
            "expressions": (target.recipe.expressions[0].model_copy(update={
                "observable": "The approved action may be discontinuous.",
            }),),
        }),
    })
    assert not paid_failure_retarget_preserves_strategy(old, changed_output)
    assert not paid_failure_retarget_preserves_strategy(old, changed_goal)
    assert not paid_failure_retarget_preserves_strategy(old, changed_criterion)


def test_paid_known_failure_retarget_accepts_fresh_same_contract_operator_profile():
    from ai_video.production.generation_runtime_repair import paid_failure_retarget_preserves_strategy
    _, old, target, _, _, _ = _paid_known_failure_reference_case()
    digest = "e" * 64 if old.provider_profile.profile_sha256 != "e" * 64 else "f" * 64
    renewed = target.provider_profile.model_copy(update={"profile_sha256": digest,
        "profile_path": Path("provider-profiles/" + digest + ".json")})
    target = target.model_copy(update={"provider_profile": renewed,
        "recipe": target.recipe.model_copy(update={"profile_sha256": renewed.profile_sha256})})
    assert paid_failure_retarget_preserves_strategy(old, target)
    changed = target.model_copy(update={"provider_profile": renewed.model_copy(update={"profile_version": "different"})})
    assert not paid_failure_retarget_preserves_strategy(old, changed)


def test_paid_known_failure_retarget_allows_profile_hash_drift_with_same_requirements():
    from ai_video.production.generation_runtime_repair import PaidKnownFailureRetarget
    from ai_video.production.hashing import canonical_sha256

    setup, old, target, entry, grant, limits = _paid_known_failure_reference_case()
    acceptance = target.recipe.acceptance_policy
    payload = acceptance.profile_payload.copy()
    payload.pop("content_hash")
    payload["profile_id"] = "asset-first-rubric-revision"
    payload["profile_version"] = "2"
    digest = canonical_sha256(payload)
    revised_acceptance = acceptance.model_copy(update={
        "profile_id": payload["profile_id"],
        "profile_version": payload["profile_version"],
        "profile_content_hash": digest,
        "profile_payload": {**payload, "content_hash": digest},
    })
    target = target.model_copy(update={"recipe": target.recipe.model_copy(update={
        "acceptance_policy": revised_acceptance,
        "rubric_hash": digest,
    })})
    auth = RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/4",
        attempt_id=entry.attempt_id,
        evidence_hash=entry.evidence_hash,
        repair_basis=grant.authorization.repair_basis,
        actor=ACTOR,
        expected_manifest_revision=1,
        paid_known_failure_retarget=PaidKnownFailureRetarget(
            paid_submit_receipt_fingerprint=grant.authorization.paid_known_failure_retarget.paid_submit_receipt_fingerprint,
            failed_observation_fingerprint=grant.authorization.paid_known_failure_retarget.failed_observation_fingerprint,
            target_scope_hash=target.scope_hash,
        ),
    )
    limits = limits.model_copy(update={"allowed_remote_candidates": (target.candidate_id,)})
    result = decide(setup, candidates=(target,), historical_recipes=(old,), limits=limits,
        evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
        runtime_repairs=(RuntimeRepairGrant(authorization=auth, consumed=False),),
        rubric_hash=digest)
    assert target.recipe.rubric_hash != old.recipe.rubric_hash
    assert target.final_output_goal == old.final_output_goal
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair == auth


def _cross_provider_no_effect_case():
    from pathlib import Path
    import hashlib

    from ai_video.production.generation_decision import GenerationCandidate
    from ai_video.production.generation_runtime_repair import (
        PaidCrossProviderNoEffectRetarget,
    )
    from ai_video.production.video import VideoOutputCapability, VideoProviderCapabilities
    from ai_video.production._shot_router_contracts import AdapterCompilerContract
    from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
    from ai_video.production.video_requirement import (
        AudioNeed, OutputGeometryPolicy, OutputNeed, ProviderNeutralVideoRequirement,
        VerifiedGenerationRequirementProjection,
    )
    from ai_video.production.final_output_contracts import (
        FinalOutputContract, FinalOutputRequirement,
    )
    from ai_video.production.generation_recipe import RequirementExpression
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.artifact_contracts import SourceReference
    from test_production_generation_decision import acceptance_policy
    from ai_video.planning.video_planner import VideoPlanner

    setup = setup_decision(remote=True, seed_supported=False, reference_hash="f" * 64)
    old = setup["inputs"].candidates[0]
    source_need = OutputNeed(
        timing_mode="content_driven", duration_seconds=4,
        geometry_policy=OutputGeometryPolicy.EXACT, width=496, height=864,
        aspect_ratio=None, fps=24, container_mime="video/mp4",
    )
    source_requirement = ProviderNeutralVideoRequirement.create(**{
        **setup["projection"].requirement.model_dump(
            mode="python", exclude={"requirement_id", "requirement_hash"}),
        "output_need": source_need,
        "audio_need": AudioNeed.REQUIRED,
    })
    target_shot = seal_artifact(source_requirement.target_shot.model_copy(update={
        "revision": source_requirement.target_shot.revision + 1,
        "content_hash": "0" * 64,
        "creation_receipt_id": "fixture-authoring-revision",
        "source_provenance": (*source_requirement.target_shot.source_provenance,
            SourceReference(kind="derived", reference="authoring-revision",
                            content_hash="a" * 64)),
    }))
    target_need = source_need.model_copy(update={
        "geometry_policy": OutputGeometryPolicy.ADAPTIVE,
        "width": None, "height": None,
    })
    target_requirement = ProviderNeutralVideoRequirement.create(**{
        **source_requirement.model_dump(
            mode="python", exclude={"requirement_id", "requirement_hash"}),
        "target_shot": target_shot,
        "output_need": target_need,
    })
    source_projection = VerifiedGenerationRequirementProjection.create(**{
        **setup["projection"].model_dump(mode="python", exclude={"projection_hash"}),
        "requirement": source_requirement,
    })
    target_projection = VerifiedGenerationRequirementProjection.create(**{
        **setup["projection"].model_dump(mode="python", exclude={"projection_hash"}),
        "requirement": target_requirement,
        "target_shot_revision": target_shot.revision,
        "target_shot_content_hash": target_shot.content_hash,
    })

    source_expression = RequirementExpression(
        requirement_id="s01-source-output", level="acceptance", stage="raw_generation",
        dimension="source_fidelity", observable="4秒/480p/24fps且含原生音轨",
        tolerance="exact", measurement="request and native media inspection",
        proof="technical", intent_paths=("output_need",),
        production_owner="shot_authoring",
    )
    target_expression = source_expression.model_copy(update={
        "observable": source_expression.observable.replace("480p", "768P"),
    })
    source_expressions = tuple(sorted((*old.recipe.expressions, source_expression),
                                      key=lambda item: item.requirement_id))
    target_expressions = tuple(sorted((
        *(expression for expression in old.recipe.expressions), target_expression,
    ), key=lambda item: item.requirement_id))
    source_policy = acceptance_policy(source_expressions)
    target_policy = acceptance_policy(target_expressions)
    source_goal = FinalOutputContract(
        goal_id="jieshi-s01-output", goal_version="seedance-native-480p-S01-20261016-001",
        user_goal="Preserve the original S01 scene and its accepted raw output.",
        requirements=(
            FinalOutputRequirement(requirement_id="s01-source-output",
                observable="4秒/480p/24fps且含原生音轨", proof="evaluator"),
            FinalOutputRequirement(requirement_id="s02-source-output",
                observable="S02仍为4秒/480p/24fps并保留原对白", proof="evaluator"),
            FinalOutputRequirement(requirement_id="story-preservation",
                observable="保留林砚左手悬窗、广播和异常倒影", proof="human"),
        ),
    )
    target_goal = source_goal.model_copy(update={
        "goal_version": "metaso-h3-native-768p-S01-20261016-001",
        "requirements": (
            source_goal.requirements[0].model_copy(update={
                "observable": source_goal.requirements[0].observable.replace("480p", "768P"),
            }),
            *source_goal.requirements[1:],
        ),
    })
    source_compiler = old.compiler_contract
    source_profile_sha = old.provider_profile.profile_sha256
    old_output = VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds", duration_seconds=4,
        dimension_mode="exact", width=496, height=864,
        resolution_label="480p", ratio="9:16", fps=24,
        container="mp4", mime_type="video/mp4", native_audio=True,
    )
    old_variant = old.capabilities.variants[0].model_copy(update={
        "capability_id": "seedance-i2v-480p-v1",
        "provider_kind": "volcengine_ark_seedance",
        "model_id": "Seedance-2.5",
        "output": None,
        "output_capability": VideoOutputCapability(
            min_duration_seconds=4, max_duration_seconds=4,
            provider_selected_duration=False, timing_modes=("nominal_seconds",),
            dimension_modes=("exact",), resolution_labels=("480p",), ratios=("9:16",),
            fps_values=(24,), containers=("mp4",), native_audio_options=(True,),
        ),
    })
    old_capabilities = VideoProviderCapabilities.create(
        provider_name="seedance", variants=(old_variant,))
    old_profile = old.provider_profile.model_copy(update={
        "profile_id": "seedance", "profile_version": "seedance-2.5-v1",
    })
    old = old.model_copy(update={
        "capabilities": old_capabilities, "capability_id": old_variant.capability_id,
        "output_requirement": old_output,
        "provider_profile": old_profile, "final_output_goal": source_goal,
        "recipe": old.recipe.model_copy(update={
            "profile_sha256": old_profile.profile_sha256,
            "compiler_hash": source_compiler.compiler_hash,
            "requirement_hash": source_requirement.requirement_hash,
            "acceptance_policy": source_policy,
            "expressions": source_expressions,
            "rubric_hash": source_policy.profile_content_hash,
        }),
    })
    profile_sha = hashlib.sha256(b"metaso-profile").hexdigest()
    profile = old.provider_profile.model_copy(update={
        "profile_id": "metaso_h3", "profile_version": "metaso-h3-ref2va-v1",
        "profile_path": Path(f"provider-profiles/{profile_sha}.json"),
        "profile_sha256": profile_sha,
    })
    variant = old.capabilities.variants[0].model_copy(update={
        "capability_id": "metaso-h3-fl2va-v1", "provider_kind": "metaso_h3",
        "model_id": "MiniMax-H3", "profile_version": "metaso-h3-ref2va-v1",
        "seed_supported": False,
        "negative_prompt_supported": False,
        "output": None,
        "output_capability": VideoOutputCapability(
            min_duration_seconds=4, max_duration_seconds=4,
            provider_selected_duration=False, timing_modes=("nominal_seconds",),
            dimension_modes=("adaptive",), resolution_labels=("768P",), ratios=("adaptive",),
            fps_values=(24,), containers=("mp4",), native_audio_options=(True,),
        ),
    })
    capabilities = VideoProviderCapabilities.create(
        provider_name="metaso_h3", variants=(variant,))
    compiler = AdapterCompilerContract.create(
        compiler_id="metaso-h3-compiler", compiler_version="1")
    recipe = old.recipe.model_copy(update={
        "profile_sha256": profile_sha, "compiler_hash": compiler.compiler_hash,
        "requirement_hash": target_requirement.requirement_hash,
        "acceptance_policy": target_policy,
        "expressions": target_expressions,
        "rubric_hash": target_policy.profile_content_hash,
    })
    h3_output = VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds", duration_seconds=4,
        dimension_mode="adaptive", resolution_label="768P", ratio="adaptive",
        fps=24, container="mp4", mime_type="video/mp4", native_audio=True,
    )
    target = GenerationCandidate(
        candidate_id="metaso-h3", provider_profile=profile, capabilities=capabilities,
        capability_id=variant.capability_id, compiler_contract=compiler,
        output_requirement=h3_output, recipe=recipe,
        final_output_goal=target_goal, voice_route=old.voice_route,
    )
    setup["projection"] = source_projection
    setup["inputs"] = setup["inputs"].model_copy(update={
        "projection_hash": source_projection.projection_hash,
        "facts_hash": VideoPlanner.generation_difficulty(source_projection)["facts_hash"],
        "rubric_hash": old.recipe.rubric_hash,
        "candidates": (old,),
    })
    entry = evidence(setup, candidate=old, outcome="runtime_failure", task_id="task")
    setup["projection"] = target_projection
    setup["context"] = setup["context"].model_copy(update={
        "activated_shot": target_shot,
        "target_shot_revision": target_shot.revision,
        "target_shot_content_hash": target_shot.content_hash,
    })
    adaptation = PaidCrossProviderNoEffectRetarget(
        submit_receipt_fingerprint="d" * 64,
        source_scope_hash=old.scope_hash,
        source_provider_name=old.capabilities.provider_name,
        target_scope_hash=target.scope_hash,
        target_provider_name=target.capabilities.provider_name,
        source_requirement_hash=source_requirement.requirement_hash,
        target_requirement_hash=target_requirement.requirement_hash,
        output_requirement_id="s01-source-output",
        source_resolution_label="480p",
        target_resolution_label="768P",
    )
    grant = RuntimeRepairGrant(authorization=RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/5", attempt_id=entry.attempt_id,
        evidence_hash=entry.evidence_hash, repair_basis="explicit cross-provider no-effect recovery",
        actor=ACTOR, expected_manifest_revision=1,
        paid_cross_provider_no_effect_retarget=adaptation,
    ), consumed=False)
    inputs = setup["inputs"].model_copy(update={
        "projection_hash": target_projection.projection_hash,
        "facts_hash": VideoPlanner.generation_difficulty(target_projection)["facts_hash"],
        "rubric_hash": target.recipe.rubric_hash,
        "candidates": (target,), "historical_recipes": (old,),
        "evidence": (entry,), "latest_attempt_hash": entry.evidence_hash,
        "experiences": (), "runtime_repairs": (grant,),
        "limits": setup["inputs"].limits.model_copy(update={
            "allowed_remote_candidates": (target.candidate_id,), "paid_submits_used": 1,
        }),
    })
    setup["inputs"] = inputs
    return setup, old, target, source_requirement, target_requirement, entry, grant, inputs


def test_cross_provider_known_no_effect_grant_is_exact_and_preserves_semantics():
    from ai_video.production.generation_runtime_repair import (
        PaidCrossProviderNoEffectRetarget,
        cross_provider_no_effect_retarget_preserves_strategy,
    )
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

    setup, old, target, source_requirement, target_requirement, entry, grant, inputs = _cross_provider_no_effect_case()
    scope = grant.authorization.paid_cross_provider_no_effect_retarget
    assert scope.source_scope_hash == old.scope_hash
    assert scope.target_scope_hash == target.scope_hash
    assert old.final_output_goal.goal_version != target.final_output_goal.goal_version
    assert old.final_output_goal.requirements[1] == target.final_output_goal.requirements[1]
    assert scope.output_requirement_id == "s01-source-output"
    assert scope.source_resolution_label == "480p"
    assert scope.target_resolution_label == "768P"
    assert cross_provider_no_effect_retarget_preserves_strategy(
        old, target, source_requirement, target_requirement, scope)

    decision = decide(setup, candidates=(target,), historical_recipes=(old,),
        limits=inputs.limits, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
        runtime_repairs=(grant,))
    assert decision.disposition == "GENERATE_ONCE"
    assert decision.runtime_repair == grant.authorization
    assert decision.selected_candidate_id == target.candidate_id

    altered_output = target.model_copy(update={
        "output_requirement": target.output_requirement.model_copy(update={"fps": 30}),
    })
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, altered_output, source_requirement, target_requirement, scope)
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target, source_requirement,
        target_requirement.model_copy(update={"intent_evidence_hash": "e" * 64}), scope)

    changed_dialogue_shot = target_requirement.target_shot.model_copy(update={
        "dialogue": "A changed line must not pass as a geometry adaptation.",
    })
    changed_dialogue_shot = seal_artifact(changed_dialogue_shot)
    changed_dialogue = ProviderNeutralVideoRequirement.create(**{
        **target_requirement.model_dump(
            mode="python", exclude={"requirement_id", "requirement_hash", "target_shot"}),
        "target_shot": changed_dialogue_shot,
    })
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target, source_requirement, changed_dialogue, scope)

    changed_reference = ProviderNeutralVideoRequirement.create(**{
        **target_requirement.model_dump(
            mode="python", exclude={"requirement_id", "requirement_hash", "asset_evidence"}),
        "asset_evidence": tuple(asset.model_copy(update={
            "canonical_owner_content_hash": "e" * 64,
        }) for asset in target_requirement.asset_evidence),
    })
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target, source_requirement, changed_reference, scope)

    changed_s02 = target.final_output_goal.model_copy(update={
        "requirements": (
            target.final_output_goal.requirements[0],
            target.final_output_goal.requirements[1].model_copy(update={
                "observable": "S02 must change to 720p and omit its original dialogue.",
            }),
            *target.final_output_goal.requirements[2:],
        ),
    })
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target.model_copy(update={"final_output_goal": changed_s02}),
        source_requirement, target_requirement, scope)

    changed_other_recipe_rule = target.recipe.expressions[0].model_copy(update={
        "observable": "The duration may change.",
    })
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target.model_copy(update={"recipe": target.recipe.model_copy(update={
            "expressions": (changed_other_recipe_rule, *target.recipe.expressions[1:]),
        })}), source_requirement, target_requirement, scope)

    wrong_rule_scope = scope.model_copy(update={"output_requirement_id": "s02-source-output"})
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target, source_requirement, target_requirement, wrong_rule_scope)

    changed_aspect = target_requirement.model_copy(update={
        "output_need": target_requirement.output_need.model_copy(update={
            "aspect_ratio": "9:16",
        }),
    })
    assert not cross_provider_no_effect_retarget_preserves_strategy(
        old, target, source_requirement, changed_aspect, scope)


def test_cross_provider_retarget_consumed_grant_cannot_reauthorize_generation():
    setup, old, target, _source, _target_req, entry, grant, inputs = _cross_provider_no_effect_case()
    consumed = RuntimeRepairGrant(authorization=grant.authorization, consumed=True)
    result = decide(
        setup, candidates=(target,), historical_recipes=(old,), limits=inputs.limits,
        evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
        runtime_repairs=(consumed,),
    )
    assert result.disposition == "RUNTIME_FAILURE"
    assert result.runtime_repair is None


def test_cross_provider_canvas_reopen_after_paid_intent_uses_consumed_lineage(tmp_path):
    from dataclasses import replace
    from types import MethodType

    from ai_video.canvas_dependencies import canvas_video_candidate_preparer
    from ai_video.canvas_planning import canvas_feedback_context
    from ai_video.canvas_production import CanvasProductionService
    from ai_video.production._shot_router_contracts import AdapterCompilerContract
    from ai_video.production._state_commit_video_runtime_repair import (
        closed_paid_no_effect_receipt,
    )
    from ai_video.production.generation_feedback import (
        RegisteredGenerationTarget,
        create_generation_candidates,
        record_attempt_evaluation,
    )
    from ai_video.production.generation_recipe import RequirementExpression
    from ai_video.production.generation_runtime_repair import (
        PaidCrossProviderNoEffectRetarget,
        cross_provider_no_effect_retarget_preserves_strategy,
    )
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.models import ActorIdentity
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video import (
        BillingKind,
        ResolvedVideoGenerationRequest,
        VideoExecutionKind,
        VideoGenerationMode,
        VideoProviderCapabilities,
    )
    from ai_video.production.video_contracts import (
        VideoFlexibleOutputRequirement,
        VideoOutputCapability,
    )
    from test_canvas_production import runtime
    from test_production_generation_decision import acceptance_policy
    from test_production_video import _paid_authorization, _paid_preview

    service, provider, limits, authorizations = runtime(tmp_path)
    source_expression = RequirementExpression(
        requirement_id="s01-source-output", level="acceptance", stage="raw_generation",
        dimension="source_fidelity", observable="4秒/480p/24fps且含原生音轨",
        tolerance="exact", measurement="request and native media inspection",
        proof="technical", intent_paths=("output_need.duration_seconds",), production_owner="shot_authoring",
    )
    target_expression = source_expression.model_copy(update={
        "observable": source_expression.observable.replace("480p", "768P"),
    })

    def install_policy(expression, *, attempt_id):
        loaded = service._load()
        policy = seal_artifact(loaded.qa_policy.model_copy(update={
            "revision": loaded.qa_policy.revision + 1,
            "content_hash": "0" * 64,
            "generation_acceptance": acceptance_policy((expression,)),
        }))
        service.committer.activate_qa_policy(
            policy,
            attempt_id=attempt_id,
            expected_manifest_revision=loaded.manifest.manifest_revision,
        )

    def flexible_resolve(self, request):
        matching = tuple(v for v in self._capabilities.variants if (
            v.provider_kind == request.provider_kind
            and v.model_id == request.model_id
            and v.profile_version == request.provider_profile.profile_version
            and v.mode is request.mode
        ))
        if len(matching) != 1:
            raise ValueError("fixture Provider capability did not match the prepared request")
        return ResolvedVideoGenerationRequest.create(
            request=request, capability=matching[0],
            effective_output=request.output_requirement,
            effective_seed=request.seed,
            effective_negative_prompt_text=request.negative_prompt_text,
        )

    provider.resolve = MethodType(flexible_resolve, provider)
    source_variant = provider.capabilities().variants[0].model_copy(update={
        "capability_id": "seedance-i2v-480p-v1",
        "provider_kind": "volcengine_ark_seedance",
        "model_id": "Seedance-2.5",
        "profile_version": "seedance-2.5-v1",
        "execution_kind": VideoExecutionKind.REMOTE,
        "billing_kind": BillingKind.METERED,
        "mode": VideoGenerationMode.IMAGE_TO_VIDEO,
        "output": None,
        "output_capability": VideoOutputCapability(
            min_duration_seconds=4, max_duration_seconds=4,
            provider_selected_duration=False, timing_modes=("nominal_seconds",),
            dimension_modes=("exact",), resolution_labels=("480p",), ratios=("9:16",),
            fps_values=(24,), containers=("mp4",), native_audio_options=(True,),
        ),
        "allowed_image_roles": ("first_frame",),
        "required_first_frame": True,
        "max_reference_count": 0,
        "seed_supported": False,
    })
    provider._capabilities = VideoProviderCapabilities.create(
        provider_name="seedance", variants=(source_variant,)
    )
    source_profile = service.targets[0].profile.model_copy(update={
        "profile_id": "seedance", "profile_version": "seedance-2.5-v1",
    })
    source_output = VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds", duration_seconds=4,
        dimension_mode="exact", width=496, height=864,
        resolution_label="480p", ratio="9:16", fps=24,
        container="mp4", mime_type="video/mp4", native_audio=True,
    )
    source_compiler = service.targets[0].compiler_contract
    service.targets = (RegisteredGenerationTarget(
        provider, source_profile, source_compiler, source_output,
    ),)
    source_row = service.direction["shots"][0]
    source_row["generation"]["output_need"] = {
        "duration_seconds": 4, "geometry_policy": "exact", "width": 496, "height": 864,
        "aspect_ratio": None, "fps": 24, "container_mime": "video/mp4",
        "timing_mode": "content_driven",
    }
    source_row["generation"]["audio_need"] = "required"
    service.revise_authoring(attempt_id="fixture-seedance-authoring")
    install_policy(source_expression, attempt_id="fixture-seedance-policy")
    loaded = service._load()
    source_context = canvas_feedback_context(
        loaded=loaded, row=source_row, policy=service.routing_policy,
    )
    source_candidates, _ = create_generation_candidates(
        projection=source_context["projection"], targets=service.targets,
        acceptance=loaded.qa_policy.selected_generation_acceptance(),
    )
    source_limits = limits.model_copy(update={
        "allowed_remote_candidates": tuple(c.candidate_id for c in source_candidates),
    })

    provider._scenario = replace(provider._scenario, submit_outcome="rejected")
    failed_position = service.start(limits=source_limits)
    assert hasattr(failed_position, "next_action"), (
        f"source preparation did not produce an attempt: {failed_position!r}; "
        f"decision={getattr(failed_position, 'decision', None)!r}; "
        f"compilation={getattr(failed_position, 'compilation', None)!r}"
    )
    assert failed_position.next_action == "submit"
    _, failed_state = service._service(failed_position.attempt_id)._state(failed_position.attempt_id)
    failed_request = service.committer._reopen_video_request(failed_state.request)
    failed_preview = _paid_preview(
        failed_request, attempt_id=failed_position.attempt_id,
        video_preview=provider.preview(failed_request),
    )
    authorizations[failed_preview.preview_fingerprint] = _paid_authorization(failed_preview)
    with pytest.raises(AiVideoError):
        service.execute(
            action="submit", paid_preview=failed_preview,
            reservation_id="fixture-seedance-no-effect",
        )
    experience = record_attempt_evaluation(
        committer=service.committer, attempt_id=failed_position.attempt_id,
    )
    failed_attempt = next(a for a in service._load().manifest.attempts
        if a.attempt_id == failed_position.attempt_id)
    old_binding = service.committer._reopen_generation_execution_binding(
        failed_attempt.video_generation_state.execution_binding,
    )
    old_candidate = next(c for c in old_binding.inputs.candidates
        if c.candidate_id == old_binding.decision.selected_candidate_id)

    h3_variant = source_variant.model_copy(update={
        "capability_id": "metaso-h3-fl2va-v1",
        "provider_kind": "metaso_h3",
        "model_id": "MiniMax-H3",
        "profile_version": "metaso-h3-ref2va-v1",
        "output_capability": VideoOutputCapability(
            min_duration_seconds=4, max_duration_seconds=4,
            provider_selected_duration=False, timing_modes=("nominal_seconds",),
            dimension_modes=("adaptive",), resolution_labels=("768P",), ratios=("adaptive",),
            fps_values=(24,), containers=("mp4",), native_audio_options=(True,),
        ),
        "negative_prompt_supported": False,
    })
    provider._capabilities = VideoProviderCapabilities.create(
        provider_name="metaso_h3", variants=(h3_variant,),
    )
    import hashlib
    profile_sha = hashlib.sha256(b"fixture-metaso-h3-profile").hexdigest()
    h3_profile = source_profile.model_copy(update={
        "profile_id": "metaso_h3", "profile_version": "metaso-h3-ref2va-v1",
        "profile_path": Path(f"provider-profiles/{profile_sha}.json"),
        "profile_sha256": profile_sha,
    })
    h3_compiler = AdapterCompilerContract.create(
        compiler_id="generated-video-e2e-fixture", compiler_version="1",
    )
    h3_output = VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds", duration_seconds=4,
        dimension_mode="adaptive", resolution_label="768P", ratio="adaptive",
        fps=24, container="mp4", mime_type="video/mp4", native_audio=True,
    )
    service.targets = (RegisteredGenerationTarget(
        provider, h3_profile, h3_compiler, h3_output,
    ),)
    source_row["generation"]["output_need"] = {
        "duration_seconds": 4, "geometry_policy": "adaptive", "width": None, "height": None,
        "aspect_ratio": None, "fps": 24, "container_mime": "video/mp4",
        "timing_mode": "content_driven",
    }
    service.revise_authoring(attempt_id="fixture-h3-authoring")
    install_policy(target_expression, attempt_id="fixture-h3-policy")
    loaded = service._load()
    target_context = canvas_feedback_context(
        loaded=loaded, row=source_row, policy=service.routing_policy,
    )
    target_candidates, _ = create_generation_candidates(
        projection=target_context["projection"], targets=service.targets,
        acceptance=loaded.qa_policy.selected_generation_acceptance(),
    )
    target_candidate = target_candidates[0]
    target_requirement = target_context["projection"].requirement
    source_requirement = old_binding.projection.requirement
    assert source_requirement.source_request_content_hash != target_requirement.source_request_content_hash
    assert source_requirement.intent_evidence_hash != target_requirement.intent_evidence_hash
    assert source_requirement.generation_intent_hash != target_requirement.generation_intent_hash
    assert cross_provider_no_effect_retarget_preserves_strategy(
        old_candidate, target_candidate, source_requirement, target_requirement,
        PaidCrossProviderNoEffectRetarget(
            submit_receipt_fingerprint="0" * 64,
            source_scope_hash=old_candidate.scope_hash,
            source_provider_name="seedance",
            source_requirement_hash=source_requirement.requirement_hash,
            target_scope_hash=target_candidate.scope_hash,
            target_provider_name="metaso_h3",
            target_requirement_hash=target_requirement.requirement_hash,
            output_requirement_id="s01-source-output",
            source_resolution_label="480p", target_resolution_label="768P",
        ),
    )
    target_limits = source_limits.model_copy(update={
        "allowed_remote_candidates": (target_candidate.candidate_id,),
    })

    receipt = closed_paid_no_effect_receipt(service.committer, failed_attempt)
    adaptation = PaidCrossProviderNoEffectRetarget(
        submit_receipt_fingerprint=receipt.submit_receipt_fingerprint,
        source_scope_hash=old_candidate.scope_hash,
        source_provider_name="seedance",
        source_requirement_hash=source_requirement.requirement_hash,
        target_scope_hash=target_candidate.scope_hash,
        target_provider_name="metaso_h3",
        target_requirement_hash=target_requirement.requirement_hash,
        output_requirement_id="s01-source-output",
        source_resolution_label="480p", target_resolution_label="768P",
    )
    pointer = service.committer.record_runtime_repair_authorization(
        attempt_id=failed_position.attempt_id,
        evidence_hash=experience.evidence[-1].evidence_hash,
        repair_basis="explicit one-use METASO H3 recovery after known no-effect",
        actor=ActorIdentity(actor_id="canvas-test", actor_kind="codex"),
        paid_cross_provider_no_effect_retarget=adaptation,
        target_candidate=target_candidate,
        target_requirement=target_requirement,
    )
    assert service.committer._reopen_runtime_repair_authorization(pointer).schema_version == "runtime-repair/5"
    successor = service.start_repair(limits=target_limits)
    assert hasattr(successor, "attempt_id"), (
        f"registered cross-provider recovery did not prepare a successor: {successor!r}; "
        f"decision={getattr(successor, 'decision', None)!r}; "
        f"compilation={getattr(successor, 'compilation', None)!r}"
    )
    assert successor.attempt_id != failed_position.attempt_id
    assert successor.next_action == "submit"
    assert service.position() == successor

    provider._scenario = replace(provider._scenario, submit_outcome="accepted")
    _, successor_state = service._service(successor.attempt_id)._state(successor.attempt_id)
    successor_request = service.committer._reopen_video_request(successor_state.request)
    successor_preview = _paid_preview(
        successor_request, attempt_id=successor.attempt_id,
        video_preview=provider.preview(successor_request),
    )
    authorizations[successor_preview.preview_fingerprint] = _paid_authorization(successor_preview)
    service.execute(
        action="submit", paid_preview=successor_preview,
        reservation_id="fixture-metaso-h3-successor",
    )
    failed_after_submit = next(a for a in service._load().manifest.attempts
        if a.attempt_id == failed_position.attempt_id)
    assert failed_after_submit.video_generation_state.runtime_repairs[0].consumed
    assert provider.call_counts.submit == 2

    reopened_committer = ProductionStateCommitter(
        service.committer.project_root,
        video_candidate_preparer=canvas_video_candidate_preparer(),
    )
    reopened = CanvasProductionService(
        committer=reopened_committer, packet=service.packet, direction=service.direction,
        targets=service.targets, routing_policy=service.routing_policy,
        decision_policy=service.decision_policy,
    )
    assert reopened.position().attempt_id == successor.attempt_id
    assert reopened.position().next_action == "poll"
    assert reopened.start_repair(limits=target_limits) == reopened.position()
    assert provider.call_counts.submit == 2


def test_paid_retarget_cannot_replace_frozen_generation_requirement():
    setup, old, target, entry, grant, limits = _retarget_case(required_hash="e" * 64)
    with pytest.raises(ValueError, match="stale candidate requirement"):
        decide(setup, candidates=(target,), historical_recipes=(old,), limits=limits,
            evidence=(entry,), latest_attempt_hash=entry.evidence_hash, runtime_repairs=(grant,))


def test_old_runtime_grant_cannot_retarget_new_profile():
    setup, old, target, entry, _, limits = _retarget_case()
    result = decide(setup, candidates=(target,), historical_recipes=(old,), limits=limits,
        evidence=(entry,), latest_attempt_hash=entry.evidence_hash, runtime_repairs=(_grant(entry),))
    assert result.disposition == "EVIDENCE_GAP"
    assert result.routing is None


def test_runtime_repair_grant_authorizes_exact_reexecution():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry),))
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair is not None
    assert result.runtime_repair.evidence_hash == entry.evidence_hash
    assert result.selected_candidate_id == setup["inputs"].candidates[0].candidate_id
    assert result.intervention is None


def test_consumed_grant_still_blocks():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry, consumed=True),))
    assert result.disposition == "RUNTIME_FAILURE"
    assert result.runtime_repair is None


def test_mismatched_evidence_hash_still_blocks():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry, evidence_hash="d" * 64),))
    assert result.disposition == "RUNTIME_FAILURE"


def test_mismatched_attempt_id_still_blocks():
    setup = setup_decision()
    entry = evidence(setup, outcome="runtime_failure", task_id="task")
    result = decide(setup, evidence=(entry,), latest_attempt_hash=entry.evidence_hash,
                    runtime_repairs=(_grant(entry, attempt="other-attempt"),))
    assert result.disposition == "RUNTIME_FAILURE"


def test_authorization_receipt_is_exact_and_self_validated():
    authorization = RuntimeRepairAuthorization.create(
        attempt_id="attempt-x",
        evidence_hash="e" * 64,
        repair_basis=REPAIR_BASIS,
        actor=ACTOR,
        expected_manifest_revision=0,
    )
    payload = authorization.model_dump(mode="json")
    payload["repair_basis"] = "tampered basis"
    with pytest.raises(ValueError, match="content hash is invalid"):
        RuntimeRepairAuthorization.model_validate(payload)


def _orchestrator(tmp_path, *, status_state):
    from ai_video.production.generation_feedback import (
        GenerationFeedbackOrchestrator,
        RegisteredGenerationTarget,
    )
    from test_production_local_video_state import _runtime

    _, provider, _, template, committer = _runtime(tmp_path, status_state=status_state)
    candidate = template.inputs.candidates[0]
    sequence = [0]

    def context(loaded):
        return {
            "projection": template.projection,
            "context": template.context,
            "policy": template.policy,
            "acceptance": candidate.recipe.acceptance_policy,
            "lifecycle": template.lifecycle.model_copy(update={
                "generation_id": f"runtime-repair-{sequence[0]}",
                "output_asset_id": f"runtime-repair-video-{sequence[0]}",
                "base_project": loaded.manifest.active_project,
                "base_registry": loaded.manifest.active_registry,
                "base_dependency_graph": loaded.manifest.active_dependency_graph,
            }),
        }

    limits = template.inputs.limits.model_copy(update={"local_batch_limit": 3})
    caller = GenerationFeedbackOrchestrator.for_project(
        committer=committer,
        targets=(RegisteredGenerationTarget(
            provider, candidate.provider_profile, candidate.compiler_contract,
            candidate.output_requirement),),
        context_loader=context,
        policy=template.inputs.policy,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    return provider, committer, caller, service, limits, sequence


def _fail_attempt(*, committer, caller, service, limits, sequence, number, attempt_id):
    from ai_video.production.generation_feedback import record_attempt_evaluation

    sequence[0] = number
    prepared = caller.start(committer=committer, attempt_id=attempt_id, limits=limits)
    assert prepared.execution_binding is not None, prepared
    service.submit_local_once(attempt_id=attempt_id)
    observation = service.refresh_local_once(attempt_id=attempt_id)
    assert observation.state is VideoTaskState.FAILED
    record_attempt_evaluation(committer=committer, attempt_id=attempt_id)
    return prepared


def _attempt(committer, attempt_id):
    return next(a for a in committer._read_manifest().attempts if a.attempt_id == attempt_id)


def test_runtime_repair_requires_failed_attempt(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.SUCCEEDED)
    caller.start(committer=committer, attempt_id="repair-running", limits=limits)
    with pytest.raises(AiVideoError, match="failed video attempt"):
        committer.record_runtime_repair_authorization(
            attempt_id="repair-running", repair_basis=REPAIR_BASIS, actor=ACTOR)


def test_runtime_repair_requires_runtime_failure_evidence(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    sequence[0] = 0
    caller.start(committer=committer, attempt_id="repair-failed", limits=limits)
    service.submit_local_once(attempt_id="repair-failed")
    service.refresh_local_once(attempt_id="repair-failed")
    assert _attempt(committer, "repair-failed").status is StateCommitStatus.FAILED
    with pytest.raises(AiVideoError, match="durable runtime failure evidence"):
        committer.record_runtime_repair_authorization(
            attempt_id="repair-failed", repair_basis=REPAIR_BASIS, actor=ACTOR)


def test_runtime_repair_roundtrip_one_use(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)

    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=0, attempt_id="repair-attempt-1")
    assert _attempt(committer, "repair-attempt-1").status is StateCommitStatus.FAILED

    # Without a grant the Shot stays decision-blocked on the runtime failure.
    blocked = caller.prepare(limits=limits)
    assert blocked.decision.disposition == "RUNTIME_FAILURE"
    assert blocked.decision.runtime_repair is None

    pointer = committer.record_runtime_repair_authorization(
        attempt_id="repair-attempt-1", repair_basis=REPAIR_BASIS, actor=ACTOR)
    assert pointer.path == Path(
        f"state/video-generation/runtime-repair/{pointer.content_hash}.json")
    assert pointer.consumed is False
    revision = committer._read_manifest().manifest_revision
    again = committer.record_runtime_repair_authorization(
        attempt_id="repair-attempt-1", repair_basis=REPAIR_BASIS, actor=ACTOR)
    assert again == pointer
    assert committer._read_manifest().manifest_revision == revision

    # The grant authorizes exactly one identical-strategy re-execution.
    sequence[0] = 1
    prepared = caller.start(committer=committer, attempt_id="repair-attempt-2", limits=limits)
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert prepared.decision.runtime_repair is not None
    assert prepared.decision.runtime_repair.evidence_hash == pointer.evidence_hash
    assert prepared.decision.intervention is None

    provider.status_state = VideoTaskState.SUCCEEDED
    service.submit_local_once(attempt_id="repair-attempt-2")
    observation = service.refresh_local_once(attempt_id="repair-attempt-2")
    assert observation.state is VideoTaskState.SUCCEEDED

    # Consumption landed in the same atomic write as the replacement submit intent.
    prior = _attempt(committer, "repair-attempt-1")
    assert prior.video_generation_state.runtime_repairs[0].consumed is True

    # No unconsumed grant remains: the next prepare is blocked again.
    sequence[0] = 2
    blocked_again = caller.prepare(limits=limits)
    assert blocked_again.decision.disposition == "RUNTIME_FAILURE"
    assert blocked_again.decision.runtime_repair is None


def test_runtime_repair_budget_is_per_shot(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    assert MAX_RUNTIME_REPAIRS_PER_SHOT == 2

    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=0, attempt_id="repair-budget-1")
    committer.record_runtime_repair_authorization(
        attempt_id="repair-budget-1", repair_basis=REPAIR_BASIS, actor=ACTOR)

    # Second bounded repair is still within the per-Shot budget.
    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=1, attempt_id="repair-budget-2")
    committer.record_runtime_repair_authorization(
        attempt_id="repair-budget-2", repair_basis=REPAIR_BASIS, actor=ACTOR)

    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=2, attempt_id="repair-budget-3")
    with pytest.raises(AiVideoError, match="budget is exhausted"):
        committer.record_runtime_repair_authorization(
            attempt_id="repair-budget-3", repair_basis=REPAIR_BASIS, actor=ACTOR)


def test_local_unmetered_new_batch_keeps_history_and_one_use_runtime_grant(tmp_path):
    provider, committer, caller, service, limits, sequence = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    initial = limits.model_copy(update={"local_batch_limit": 1, "local_total_limit": 1})
    _fail_attempt(committer=committer, caller=caller, service=service, limits=initial,
        sequence=sequence, number=0, attempt_id="unmetered-initial")
    pointer = committer.record_runtime_repair_authorization(
        attempt_id="unmetered-initial", repair_basis=REPAIR_BASIS, actor=ACTOR)
    sequence[0] = 1
    continued = initial.model_copy(update={"local_batch_limit": 2, "local_total_limit": None})
    prepared = caller.start(committer=committer, attempt_id="unmetered-continued", limits=continued)
    assert prepared.inputs.limits.local_total_used == prepared.inputs.limits.local_batch_used == 1
    assert prepared.decision.runtime_repair.evidence_hash == pointer.evidence_hash
    provider.status_state = VideoTaskState.SUCCEEDED
    service.submit_local_once(attempt_id="unmetered-continued")
    assert service.refresh_local_once(attempt_id="unmetered-continued").state is VideoTaskState.SUCCEEDED
    assert _attempt(committer, "unmetered-initial").video_generation_state.runtime_repairs[0].consumed
    assert provider.submit_calls == 2
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="unmetered-continued")
    assert provider.submit_calls == 2


def _exhausted_local_repairs(tmp_path):
    runtime = _orchestrator(tmp_path, status_state=VideoTaskState.FAILED)
    provider, committer, caller, service, limits, sequence = runtime
    for number in range(3):
        attempt_id = f"extension-failure-{number}"
        _fail_attempt(committer=committer, caller=caller, service=service,
                      limits=limits, sequence=sequence, number=number, attempt_id=attempt_id)
        if number < 2:
            committer.record_runtime_repair_authorization(
                attempt_id=attempt_id, repair_basis=REPAIR_BASIS, actor=ACTOR)
    return runtime


def _extension(committer, **updates):
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    state = _attempt(committer, "extension-failure-2").video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    return LocalRuntimeRepairExtension(**{
        "task_id": binding.inputs.limits.task_id,
        "shot_id": binding.context.target_shot_id,
        "failed_binding_hash": binding.binding_hash,
        "expected_manifest_revision": committer._read_manifest().manifest_revision,
        **updates,
    })


def test_v1_runtime_repair_payload_and_hash_remain_exact():
    from ai_video.production.hashing import canonical_sha256
    payload = {
        "schema_version": "runtime-repair/1", "attempt_id": "old-attempt",
        "evidence_hash": "e" * 64, "repair_basis": REPAIR_BASIS,
        "actor": ACTOR.model_dump(mode="json"), "expected_manifest_revision": 8,
        "content_hash": "0" * 64,
    }
    payload["content_hash"] = canonical_sha256(payload)
    reopened = RuntimeRepairAuthorization.model_validate(payload)
    assert reopened.model_dump(mode="json") == payload
    assert RuntimeRepairAuthorization.model_validate_json(reopened.model_dump_json()) == reopened


def test_explicit_third_local_runtime_repair_is_one_use_and_keeps_counts(tmp_path):
    provider, committer, caller, service, limits, sequence = _exhausted_local_repairs(tmp_path)
    extension = _extension(committer)
    pointer = committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=extension)
    receipt = committer._reopen_runtime_repair_authorization(pointer)
    assert receipt.schema_version == "runtime-repair/2"
    assert receipt.local_extension == extension
    revision = committer._read_manifest().manifest_revision
    assert committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=extension) == pointer
    assert committer._read_manifest().manifest_revision == revision
    sequence[0] = 3
    continued = limits.model_copy(update={"local_batch_limit": 4, "local_total_limit": None})
    prepared = caller.start(committer=committer, attempt_id="extension-last", limits=continued)
    assert prepared.inputs.limits.local_batch_used == prepared.inputs.limits.local_total_used == 3
    service.submit_local_once(attempt_id="extension-last")
    prior = _attempt(committer, "extension-failure-2").video_generation_state
    assert prior.runtime_repairs[0].consumed
    assert _attempt(committer, "extension-last").video_generation_state.local_submit_intent
    assert provider.submit_calls == 4
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="extension-last")
    assert provider.submit_calls == 4
    service.refresh_local_once(attempt_id="extension-last")
    from ai_video.production.generation_feedback import record_attempt_evaluation
    record_attempt_evaluation(committer=committer, attempt_id="extension-last")
    with pytest.raises(AiVideoError, match="budget is exhausted"):
        committer.record_runtime_repair_authorization(
            attempt_id="extension-last", repair_basis=REPAIR_BASIS, actor=ACTOR,
            local_extension=extension.model_copy(update={
                "expected_manifest_revision": committer._read_manifest().manifest_revision}))


@pytest.mark.parametrize("updates, actor, evidence_hash", [
    ({"task_id": "different-task"}, ACTOR, None),
    ({"shot_id": "different-shot"}, ACTOR, None),
    ({"failed_binding_hash": "0" * 64}, ACTOR, None),
    ({"expected_manifest_revision": 0}, ACTOR, None),
    ({}, ActorIdentity(actor_id="other-owner", actor_kind="automation"), None),
    ({}, ACTOR, "0" * 64),
])
def test_third_repair_rejects_identity_and_stale_revision(tmp_path, updates, actor, evidence_hash):
    provider, committer, _, _, _, _ = _exhausted_local_repairs(tmp_path)
    before = committer._read_manifest()
    with pytest.raises(AiVideoError):
        committer.record_runtime_repair_authorization(
            attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=actor,
            evidence_hash=evidence_hash, local_extension=_extension(committer, **updates))
    assert committer._read_manifest() == before
    assert provider.submit_calls == 3


def test_third_repair_scope_rechecked_at_submit(tmp_path):
    provider, committer, caller, service, limits, sequence = _exhausted_local_repairs(tmp_path)
    committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=_extension(committer))
    sequence[0] = 3
    wrong_task = limits.model_copy(update={"task_id": "reset-task", "local_batch_limit": 4})
    with pytest.raises(AiVideoError, match="extension scope"):
        caller.start(committer=committer, attempt_id="wrong-task", limits=wrong_task)
        service.submit_local_once(attempt_id="wrong-task")
    assert provider.submit_calls == 3


def test_v2_extension_tamper_and_version_mismatch_are_rejected(tmp_path):
    _, committer, _, _, _, _ = _exhausted_local_repairs(tmp_path)
    extension = _extension(committer)
    receipt = RuntimeRepairAuthorization.create(
        schema_version="runtime-repair/2", attempt_id="extension-failure-2",
        evidence_hash="e" * 64, repair_basis=REPAIR_BASIS, actor=ACTOR,
        expected_manifest_revision=extension.expected_manifest_revision + 1,
        local_extension=extension)
    payload = receipt.model_dump(mode="json")
    payload["local_extension"]["task_id"] = "tampered"
    with pytest.raises(ValueError):
        RuntimeRepairAuthorization.model_validate(payload)
    with pytest.raises(ValueError):
        RuntimeRepairAuthorization.create(
            attempt_id="bad-v1", evidence_hash="e" * 64, repair_basis=REPAIR_BASIS,
            actor=ACTOR, expected_manifest_revision=0, local_extension=extension)


@pytest.mark.parametrize("ceiling", [3, 4, 5, 6])
def test_runtime_repair_extension_cannot_authorize_unknown_submit(tmp_path, ceiling):
    from ai_video.errors import ErrorCode
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    provider, committer, caller, service, limits, _ = _orchestrator(
        tmp_path, status_state=VideoTaskState.FAILED)
    prepared = caller.start(committer=committer, attempt_id="unknown-extension", limits=limits)
    provider.submit_error = ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="unknown-extension")
    before = committer._read_manifest()
    assert _attempt(committer, "unknown-extension").status is StateCommitStatus.OUTCOME_UNKNOWN
    extension = LocalRuntimeRepairExtension(task_id=limits.task_id,
        shot_id=prepared.execution_binding.context.target_shot_id,
        failed_binding_hash=prepared.execution_binding.binding_hash,
        expected_manifest_revision=before.manifest_revision, ceiling=ceiling)
    with pytest.raises(AiVideoError, match="failed video attempt"):
        committer.record_runtime_repair_authorization(attempt_id="unknown-extension",
            repair_basis=REPAIR_BASIS, actor=ACTOR, local_extension=extension)
    assert committer._read_manifest() == before


def _consumed_third_local_repair(tmp_path):
    runtime = _exhausted_local_repairs(tmp_path)
    provider, committer, caller, service, limits, sequence = runtime
    committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=_extension(committer))
    limits = limits.model_copy(update={"local_batch_limit": 5, "local_total_limit": None})
    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=3, attempt_id="extension-failure-3")
    return provider, committer, caller, service, limits, sequence


def _fourth_extension(committer, **updates):
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    state = _attempt(committer, "extension-failure-3").video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    return LocalRuntimeRepairExtension(**{
        "task_id": binding.inputs.limits.task_id,
        "shot_id": binding.context.target_shot_id,
        "failed_binding_hash": binding.binding_hash,
        "expected_manifest_revision": committer._read_manifest().manifest_revision,
        "ceiling": 4, **updates,
    })


def _consumed_fourth_local_repair(tmp_path):
    runtime = _consumed_third_local_repair(tmp_path)
    provider, committer, caller, service, limits, sequence = runtime
    committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-3", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=_fourth_extension(committer))
    limits = limits.model_copy(update={"local_batch_limit": 6})
    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=4, attempt_id="extension-failure-4")
    return provider, committer, caller, service, limits, sequence


def _consumed_fifth_local_repair(tmp_path):
    runtime = _consumed_fourth_local_repair(tmp_path)
    provider, committer, caller, service, limits, sequence = runtime
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    state = _attempt(committer, "extension-failure-4").video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    committer.record_runtime_repair_authorization(
        attempt_id="extension-failure-4", repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=LocalRuntimeRepairExtension(
            task_id=binding.inputs.limits.task_id, shot_id=binding.context.target_shot_id,
            failed_binding_hash=binding.binding_hash,
            expected_manifest_revision=committer._read_manifest().manifest_revision, ceiling=5))
    limits = limits.model_copy(update={"local_batch_limit": 7})
    _fail_attempt(committer=committer, caller=caller, service=service, limits=limits,
                  sequence=sequence, number=5, attempt_id="extension-failure-5")
    return provider, committer, caller, service, limits, sequence


@pytest.mark.parametrize("ceiling", [4, 5, 6])
def test_exact_extended_local_repair_preserves_history_replay_and_one_use(tmp_path, ceiling):
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    setup = {4: _consumed_third_local_repair, 5: _consumed_fourth_local_repair,
             6: _consumed_fifth_local_repair}[ceiling]
    provider, committer, caller, service, limits, sequence = setup(tmp_path)
    source_attempt = f"extension-failure-{ceiling - 1}"
    state = _attempt(committer, source_attempt).video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    extension = LocalRuntimeRepairExtension(
        task_id=binding.inputs.limits.task_id, shot_id=binding.context.target_shot_id,
        failed_binding_hash=binding.binding_hash,
        expected_manifest_revision=committer._read_manifest().manifest_revision, ceiling=ceiling)
    before = committer._read_manifest()
    pointer = committer.record_runtime_repair_authorization(
        attempt_id=source_attempt, repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=extension)
    receipt = committer._reopen_runtime_repair_authorization(pointer)
    assert receipt.schema_version == "runtime-repair/2"
    assert receipt.local_extension.ceiling == ceiling
    revision = committer._read_manifest().manifest_revision
    assert committer.record_runtime_repair_authorization(
        attempt_id=source_attempt, repair_basis=REPAIR_BASIS, actor=ACTOR,
        local_extension=extension) == pointer
    assert committer._read_manifest().manifest_revision == revision
    assert committer._read_manifest().attempts[:-1] == before.attempts[:-1]
    sequence[0] = ceiling
    prepared = caller.start(committer=committer, attempt_id="fourth-last", limits=limits)
    assert prepared.inputs.limits.local_batch_used == prepared.inputs.limits.local_total_used == ceiling
    assert prepared.decision.runtime_repair.evidence_hash == pointer.evidence_hash
    service.submit_local_once(attempt_id="fourth-last")
    assert provider.submit_calls == ceiling + 1
    assert _attempt(committer, source_attempt).video_generation_state.runtime_repairs[0].consumed
    with pytest.raises(AiVideoError):
        service.submit_local_once(attempt_id="fourth-last")
    assert provider.submit_calls == ceiling + 1
    service.refresh_local_once(attempt_id="fourth-last")
    from ai_video.production.generation_feedback import record_attempt_evaluation
    record_attempt_evaluation(committer=committer, attempt_id="fourth-last")
    final = committer._read_manifest()
    state = _attempt(committer, "fourth-last").video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    reused = extension.model_copy(update={"failed_binding_hash": binding.binding_hash,
        "expected_manifest_revision": final.manifest_revision})
    with pytest.raises(AiVideoError, match="budget is exhausted"):
        committer.record_runtime_repair_authorization(
            attempt_id="fourth-last", repair_basis=REPAIR_BASIS, actor=ACTOR,
            local_extension=reused)
    assert committer._read_manifest() == final
    states = [a.video_generation_state for a in final.attempts if a.video_generation_state is not None]
    assert sum(len(s.runtime_repairs) for s in states) == ceiling
    assert all(p.consumed for s in states for p in s.runtime_repairs)


@pytest.mark.parametrize("ceiling", [4, 5, 6])
def test_extension_cannot_skip_prior_grants(tmp_path, ceiling):
    provider, committer, _, _, _, _ = _exhausted_local_repairs(tmp_path)
    before = committer._read_manifest()
    with pytest.raises(AiVideoError, match="extension is premature"):
        committer.record_runtime_repair_authorization(
            attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
            local_extension=_extension(committer, ceiling=ceiling))
    assert committer._read_manifest() == before
    assert provider.submit_calls == 3


@pytest.mark.parametrize("ceiling", [4, 5, 6])
@pytest.mark.parametrize("updates, actor, evidence_hash", [
    ({"task_id": "different-task"}, ACTOR, None),
    ({"shot_id": "different-shot"}, ACTOR, None),
    ({"failed_binding_hash": "0" * 64}, ACTOR, None),
    ({"expected_manifest_revision": 0}, ACTOR, None),
    ({}, ActorIdentity(actor_id="other-owner", actor_kind="automation"), None),
    ({}, ACTOR, "0" * 64),
])
def test_extended_repair_rejects_identity_and_stale_revision(tmp_path, updates, actor, evidence_hash, ceiling):
    setup = {4: _consumed_third_local_repair, 5: _consumed_fourth_local_repair,
             6: _consumed_fifth_local_repair}[ceiling]
    provider, committer, _, _, _, _ = setup(tmp_path)
    source_attempt = f"extension-failure-{ceiling - 1}"
    state = _attempt(committer, source_attempt).video_generation_state
    binding = committer._reopen_generation_execution_binding(state.execution_binding)
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    values = {"task_id": binding.inputs.limits.task_id, "shot_id": binding.context.target_shot_id,
              "failed_binding_hash": binding.binding_hash,
              "expected_manifest_revision": committer._read_manifest().manifest_revision,
              "ceiling": ceiling, **updates}
    before = committer._read_manifest()
    with pytest.raises(AiVideoError):
        committer.record_runtime_repair_authorization(
            attempt_id=source_attempt, repair_basis=REPAIR_BASIS, actor=actor,
            evidence_hash=evidence_hash, local_extension=LocalRuntimeRepairExtension(**values))
    assert committer._read_manifest() == before
    assert provider.submit_calls == ceiling


def test_runtime_repair_extension_rejects_unbounded_ceiling():
    from ai_video.production.generation_runtime_repair import LocalRuntimeRepairExtension
    with pytest.raises(ValueError):
        LocalRuntimeRepairExtension(task_id="task", shot_id="shot", failed_binding_hash="b" * 64,
            expected_manifest_revision=0, ceiling=7)


def test_runtime_repair_extension_revalidates_copied_models_before_mutation(tmp_path):
    provider, committer, _, _, _, _ = _exhausted_local_repairs(tmp_path)
    extension = _extension(committer).model_copy(update={"ceiling": 7})
    before = committer._read_manifest()
    with pytest.raises(AiVideoError, match="typed and exact"):
        committer.record_runtime_repair_authorization(
            attempt_id="extension-failure-2", repair_basis=REPAIR_BASIS, actor=ACTOR,
            local_extension=extension)
    assert committer._read_manifest() == before
    assert provider.submit_calls == 3


@pytest.mark.parametrize("ceiling", [3, 4, 5])
def test_existing_v2_extension_payload_remains_exact(ceiling):
    from ai_video.production.hashing import canonical_sha256
    payload = {
        "schema_version": "runtime-repair/2", "attempt_id": "old-third",
        "evidence_hash": "e" * 64, "repair_basis": REPAIR_BASIS,
        "actor": ACTOR.model_dump(mode="json"), "expected_manifest_revision": 9,
        "content_hash": "0" * 64,
        "local_extension": {"task_id": "task", "shot_id": "shot",
            "failed_binding_hash": "b" * 64, "expected_manifest_revision": 8, "ceiling": ceiling},
    }
    payload["content_hash"] = canonical_sha256(payload)
    reopened = RuntimeRepairAuthorization.model_validate(payload)
    assert reopened.model_dump(mode="json") == payload
    assert RuntimeRepairAuthorization.model_validate_json(reopened.model_dump_json()) == reopened


def test_earlier_quality_failure_does_not_block_runtime_repair_for_runtime_failure():
    """`diagnosis` is computed per-latest-attempt via `diagnose_exact_result`,
    which early-returns when `latest.outcome != "media"`. A previous
    QUALITY_FAILURE attempt is part of the Shot history but does not enter the
    latest's diagnosis, so the runtime repair branch still authorises a
    single re-execution of the runtime-failed attempt. The contract is:
    runtime repair is bounded to the latest attempt's outcome, not
    re-litigation of older media evidence."""
    setup = setup_decision()
    failed = evidence(setup, verdict="FAIL", task_id="task", attempt="media-1")
    runtime = evidence(setup, outcome="runtime_failure", task_id="task", attempt="runtime-1")
    grant = _grant(runtime)
    result = decide(setup, evidence=(failed, runtime),
                    latest_attempt_hash=runtime.evidence_hash,
                    runtime_repairs=(grant,))
    assert result.disposition == "GENERATE_ONCE"
    assert result.runtime_repair is not None
    assert result.runtime_repair.evidence_hash == runtime.evidence_hash
    assert result.intervention is None


def test_snapshot_hash_stable_across_runtime_repair_iteration_order():
    """`runtime_repairs` joins the sorted-fields list so that
    `DecisionInputs.snapshot_hash` is invariant to the underlying iterator
    order. Without this, a hash drift could trigger spurious stale-binding
    failures inside `_validate_binding`."""
    setup = setup_decision()
    runtime = evidence(setup, outcome="runtime_failure", task_id="task", attempt="rt-1")
    grant = _grant(runtime)
    forward = setup["inputs"].model_copy(update={"runtime_repairs": (grant,)})
    reverse = setup["inputs"].model_copy(update={"runtime_repairs": (grant,)})
    assert forward.snapshot_hash == reverse.snapshot_hash
    # Different grant bodies still produce distinct hashes.
    other = _grant(runtime, evidence_hash="d" * 64)
    divergent = setup["inputs"].model_copy(update={"runtime_repairs": (other,)})
    assert divergent.snapshot_hash != forward.snapshot_hash
