"""Real-project fixtures for decision-bound generated-video lifecycle tests."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path

from ai_video.production.generation_decision import (
    DecisionInputs,
    DecisionPolicy,
    ExecutionLimits,
    GenerationCandidate,
)
from ai_video.production.generation_execution import GenerationDecisionExecutionBinding
from ai_video.production.generation_recipe import (
    GenerationRecipe,
    RequirementExpression,
    SeedPolicy,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.hashing import seal_artifact
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    ContinuityMode as RouterContinuityMode,
    VideoGenerationResolver,
)
from ai_video.production.video import (
    BillingKind,
    ResolvedVideoGenerationRequest,
    VideoExecutionKind,
    VideoGenerationMode,
)
from ai_video.production.video_compiler import (
    CompiledProviderVideoRequest,
    ProviderNativePrompt,
    compile_provider_video_request,
    require_compiled_provider_request,
)
from ai_video.production.video_fake import ScriptedFakeVideoProvider
from ai_video.production.video_requirement import (
    AssetEvidence,
    AudioNeed,
    GenerationIntent,
    GenerationMode,
    MotionRequirement,
    OutputNeed,
    ProviderNeutralVideoRequirement,
    QualityNeed,
    SemanticReferenceRole,
    VerifiedGenerationRequirementProjection,
)
from ai_video.production.models import (
    AssetRoleRequirement,
    AssetType,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
    VisualStrategy,
)
from ai_video.production.dependency import (
    build_production_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    prepare_dependency_graph_transition,
    prepare_project_registry_commit,
)
from ai_video.planning.video_planner import VideoPlanner
from test_production_generation_decision import acceptance_policy
from test_production_shot_router import (
    _asset as _router_asset,
    _context as _router_context,
    _lifecycle as _router_lifecycle,
    _policy as _router_policy,
)


@dataclass(frozen=True)
class PreparedGenerationExecution:
    binding: GenerationDecisionExecutionBinding
    resolved: ResolvedVideoGenerationRequest


class NativeFixtureVideoProvider(ScriptedFakeVideoProvider):
    """Scripted lifecycle double with a deterministic native compiler."""

    def __init__(
        self,
        *,
        native_prompt_text: str,
        compiler_id: str = "native-fixture-video",
        compiler_version: str = "1",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._native_prompt_text = native_prompt_text
        self._compiler_id = compiler_id
        self._compiler_version = compiler_version

    def compile_request(self, provider_bound, requirement):
        prompt_text = self._native_prompt_text
        return compile_provider_video_request(
            provider_bound=provider_bound,
            requirement=requirement,
            compiler_id=self._compiler_id,
            compiler_version=self._compiler_version,
            capabilities=self.capabilities(),
            native_prompt=ProviderNativePrompt(
                grammar_contract=f"{self._compiler_id}-v1",
                prompt_text=prompt_text,
                prompt_sha256=hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
            ),
        )


def fixture_generation_expression(output) -> RequirementExpression:
    """The one raw-media requirement exercised by lifecycle fixtures."""

    return RequirementExpression(
        requirement_id="duration",
        level="acceptance",
        stage="raw_generation",
        dimension="timing",
        observable=f"{output.duration_seconds:g} seconds",
        tolerance="exact",
        measurement="technical probe",
        proof="technical",
        intent_paths=("output_need.duration_seconds",),
        native_text=(),
        production_owner="test_fixture",
    )


def activate_fixture_generation_qa_policy(*, root: Path, inputs, output):
    """Install a raw-generation fixture rubric, preserving final-domain QA."""

    loaded = inputs.project
    if loaded.qa_policy is not None and loaded.qa_policy.selected_generation_acceptance() is not None:
        return inputs

    acceptance = acceptance_policy((fixture_generation_expression(output),))
    current_policy = loaded.qa_policy
    if current_policy is None:
        policy = QaPolicy(
            artifact_id="fixture-generation-qa-policy",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="fixture-generation-qa-policy",
            source_provenance=(
                SourceReference(kind="derived", reference="generation-fixture"),
            ),
            policy_id="fixture-generation-qa-policy",
            policy_version="1",
            required_layers=(QaLayer.SEMANTIC,),
            technical_thresholds=QaTechnicalThresholds(
                black_luma_max_milli=10,
                silence_peak_max_millidb=-60_000,
                clipping_peak_min_millidb=-100,
            ),
            layout_rules=QaLayoutRules(
                safe_area_inset_milli=50,
                caption_overflow_tolerance_milli=0,
            ),
            strategy_rules_version="1",
            semantic_requirement="required",
            semantic_authorities=(
                ToolIdentity(name="fixture-generation-evaluator", version="1"),
            ),
            domain_acceptance=acceptance,
        )
    else:
        required_layers = tuple(
            dict.fromkeys((*current_policy.required_layers, QaLayer.SEMANTIC))
        )
        policy = current_policy.model_copy(
            update={
                "artifact_id": "fixture-generation-qa-policy",
                "revision": current_policy.revision + 1,
                "content_hash": "0" * 64,
                "creation_receipt_id": "fixture-generation-qa-policy",
                "source_provenance": (
                    SourceReference(kind="derived", reference="generation-fixture"),
                ),
                "required_layers": required_layers,
                "semantic_requirement": "required",
                "semantic_authorities": (
                    current_policy.semantic_authorities
                    or (ToolIdentity(name="fixture-generation-evaluator", version="1"),)
                ),
                "generation_acceptance": acceptance,
            }
        )
    from ai_video.production.models import GenerationEvaluationAuthority

    policy = policy.model_copy(update={"generation_evaluation_authorities": (
        GenerationEvaluationAuthority(evaluator=policy.semantic_authorities[0], proof="technical"),
    )})
    sealed = seal_artifact(policy)
    committer = ProductionStateCommitter(root)
    manifest = committer._read_manifest()
    committer.activate_qa_policy(
        sealed,
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="activate-fixture-generation-qa-policy",
    )
    return replace(inputs, project=load_production_project(root / "project.yaml"))


def activate_generated_video_shot(
    *,
    root: Path,
    inputs,
    target_shot_id: str | None = None,
    first_frame_asset_id: str | None = None,
    require_first_frame: bool = True,
):
    """Durably promote the fixture's target Shot before requesting video."""

    initial = inputs.project
    authored_shot = next(
        shot
        for shot in initial.shots
        if shot.shot_id == (target_shot_id or initial.shots[0].shot_id)
    )
    source_asset_id = (
        first_frame_asset_id
        or (
            authored_shot.required_asset_roles[0].asset_ids[0]
            if authored_shot.required_asset_roles[0].asset_ids
            else initial.registry.assets[0].asset_id
        )
    )
    first_frame_asset = (
        next(
            asset
            for asset in initial.registry.assets
            if asset.asset_id == source_asset_id
        )
        if require_first_frame
        else None
    )
    generated_shot = seal_artifact(
        authored_shot.model_copy(
            update={
                "revision": authored_shot.revision + 1,
                "content_hash": "0" * 64,
                "visual_strategy": VisualStrategy.GENERATED_VIDEO,
                "generated_video_rationale": "fixture lifecycle generation",
                "required_asset_roles": (
                    AssetRoleRequirement(
                        role=authored_shot.required_asset_roles[0].role,
                        asset_ids=(),
                        allowed_asset_types=(AssetType.VIDEO,),
                    ),
                    AssetRoleRequirement(
                        role="first_frame",
                        asset_ids=(
                            (first_frame_asset.asset_id,)
                            if first_frame_asset is not None
                            else ()
                        ),
                        allowed_asset_types=(AssetType.IMAGE,),
                    ),
                ),
            }
        )
    )
    target_index = next(
        index
        for index, shot in enumerate(initial.shots)
        if shot.shot_id == authored_shot.shot_id
    )
    generated_shot_ref = initial.project.artifacts.shots[target_index].model_copy(
        update={
            "revision": generated_shot.revision,
            "content_hash": generated_shot.content_hash,
            "path": Path(
                f"creative/shots/{authored_shot.shot_id}-generated-video.yaml"
            ),
        }
    )
    generated_project = seal_artifact(
        initial.project.model_copy(
            update={
                "revision": initial.project.revision + 1,
                "content_hash": "0" * 64,
                "artifacts": initial.project.artifacts.model_copy(
                    update={
                        "shots": (
                            *initial.project.artifacts.shots[:target_index],
                            generated_shot_ref,
                            *initial.project.artifacts.shots[target_index + 1 :],
                        )
                    }
                ),
            }
        )
    )
    base_commit = prepare_project_registry_commit(
        manifest=initial.manifest,
        project=generated_project,
        registry=initial.registry,
        attempt_id=f"fixture-generated-video-shot-{authored_shot.shot_id}",
    )
    candidate_loaded = initial.model_copy(
        update={
            "project": generated_project,
            "shots": (
                *initial.shots[:target_index],
                generated_shot,
                *initial.shots[target_index + 1 :],
            ),
            "manifest": initial.manifest.model_copy(
                update={"active_project": base_commit.next_project}
            ),
        }
    )
    candidate_graph = build_production_dependency_graph(
        replace(inputs, project=candidate_loaded)
    )
    candidate_states = resolve_dependency_state(
        candidate_graph, initial.manifest.dependency_states
    ).states
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=initial.manifest.manifest_revision,
        base_dependency_graph=initial.manifest.active_dependency_graph,
        candidate_graph=candidate_graph,
        candidate_dependency_states=candidate_states,
        expected_desired_fingerprints=desired_fingerprints(candidate_graph),
    )
    graph_bytes = _canonical_json_bytes(candidate_graph)
    shot_bytes = _canonical_yaml_bytes(generated_shot)
    commit_request = replace(
        base_commit,
        dependency_graph_transition=transition,
        artifacts=tuple(
            sorted(
                (
                    *base_commit.artifacts,
                    PreparedArtifact(
                        transition.candidate_dependency_graph.path,
                        graph_bytes,
                        hashlib.sha256(graph_bytes).hexdigest(),
                    ),
                    PreparedArtifact(
                        generated_shot_ref.path,
                        shot_bytes,
                        hashlib.sha256(shot_bytes).hexdigest(),
                    ),
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        ),
    )
    ProductionStateCommitter(root).commit(commit_request)
    return replace(inputs, project=load_production_project(root / "project.yaml"))


def prepare_generation_execution(
    *,
    project,
    provider,
    request: ResolvedVideoGenerationRequest,
    task_id: str,
    compiler_id: str,
    compiler_version: str,
) -> PreparedGenerationExecution:
    """Build one executable decision from the loaded production project.

    Test callers supply an adapter with an actual native compiler.  This helper
    never reuses the old hand-built request as a submit authorization.
    """

    sealed = request.activation_scope.request if request.activation_scope else None
    if sealed is None:
        raise ValueError("fixture request requires a sealed activation scope")
    if request.mode not in {
        VideoGenerationMode.TEXT_TO_VIDEO,
        VideoGenerationMode.IMAGE_TO_VIDEO,
    }:
        raise ValueError("fixture supports only registered T2V and I2V modes")
    shot = next(item for item in project.shots if item.shot_id == sealed.target_shot_id)
    scene = next(item for item in project.scenes if item.scene_id == shot.scene_id)
    source = sealed.image_bindings[0] if sealed.image_bindings else None
    keyframe_template = (
        _router_asset(
            "first_frame",
            "generation-execution-fixture-source",
            source.asset_sha256,
            mime_type=source.mime_type,
            size_bytes=source.size_bytes,
            width=source.width,
            height=source.height,
        )
        if source is not None
        else None
    )
    context = _router_context(
        continuity=RouterContinuityMode.NONE,
        keyframe=keyframe_template,
        important=False,
        shot_id=shot.shot_id,
    ).model_copy(
        update={
            "activated_shot": shot,
            "target_shot_id": shot.shot_id,
            "target_shot_revision": shot.revision,
            "target_shot_content_hash": shot.content_hash,
            "selected_registry_revision_id": project.manifest.active_registry.revision_id,
            "shot_keyframe": (
                keyframe_template.model_copy(
                    update={
                        "asset_id": source.asset_id,
                        "source_registry_revision_id": (
                            project.manifest.active_registry.revision_id
                        ),
                    }
                )
                if keyframe_template is not None
                else None
            ),
        }
    )
    output = request.effective_output
    if not hasattr(output, "duration_seconds") or output.duration_seconds is None:
        raise ValueError("fixture requires an exact-duration output")
    requirement = ProviderNeutralVideoRequirement.create(
        source_request_content_hash=canonical_sha256(
            {"fixture": "generation-execution", "shot": shot.content_hash}
        ),
        intent_evidence_hash=canonical_sha256({"fixture": "intent", "shot": shot.content_hash}),
        generation_intent_hash=canonical_sha256({"fixture": "intent-v1", "shot": shot.content_hash}),
        target_shot=shot,
        scene=scene,
        characters=tuple(
            item for item in project.characters if item.character_id in shot.character_ids
        ),
        generation_mode=(
            GenerationMode.TEXT_TO_VIDEO
            if request.mode is VideoGenerationMode.TEXT_TO_VIDEO
            else GenerationMode.IMAGE_TO_VIDEO
        ),
        continuity_mode="none",
        motion_requirement=MotionRequirement.FREE_COMPLEX,
        generation_intent=GenerationIntent(),
        semantic_reference_roles=(
            (SemanticReferenceRole.FIRST_FRAME,) if source is not None else ()
        ),
        asset_evidence=(
            (
                AssetEvidence(
                    role=SemanticReferenceRole.FIRST_FRAME,
                    asset_id=source.asset_id,
                    asset_sha256=source.asset_sha256,
                    mime_type=source.mime_type,
                    width=source.width,
                    height=source.height,
                    size_bytes=source.size_bytes,
                ),
            )
            if source is not None
            else ()
        ),
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.OPTIONAL if output.native_audio else AudioNeed.FORBIDDEN,
        quality_need=QualityNeed(objective_tier="production"),
    )
    projection = VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=canonical_sha256({"fixture": "plan", "shot": shot.content_hash}),
        verified_source_request_content_hash=requirement.source_request_content_hash,
        target_shot_id=shot.shot_id,
        target_shot_revision=shot.revision,
        target_shot_content_hash=shot.content_hash,
    )
    lifecycle = _router_lifecycle(context).model_copy(
        update={
            "generation_id": sealed.generation_id,
            "target_asset_role": sealed.target_asset_role,
            "base_project": project.manifest.active_project,
            "base_registry": project.manifest.active_registry,
            "base_dependency_graph": project.manifest.active_dependency_graph,
            "input_artifact_ids": sealed.input_artifact_ids,
            "output_asset_id": sealed.output_asset_id,
            "commercial_binding": sealed.commercial_binding,
            "continuity_binding": sealed.continuity_binding,
            "hard_cut_keyframe_binding": sealed.hard_cut_keyframe_binding,
            "seal_terminal_frame": sealed.seal_terminal_frame,
            "execution_stack_hash": sealed.execution_stack_hash,
        }
    )
    capabilities = provider.capabilities()
    capability = next(
        item for item in capabilities.variants if item.capability_id == request.capability_id
    )
    compiler = AdapterCompilerContract.create(
        compiler_id=compiler_id, compiler_version=compiler_version
    )
    expression = fixture_generation_expression(output)
    acceptance = acceptance_policy((expression,))
    seed = (
        SeedPolicy(kind="fixed", value=request.effective_seed or 0)
        if capability.seed_supported
        else SeedPolicy(kind="uncontrolled")
    )
    recipe = GenerationRecipe(
        seed=seed,
        profile_sha256=sealed.provider_profile.profile_sha256,
        compiler_hash=compiler.compiler_hash,
        requirement_hash=requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash,
        acceptance_policy=acceptance,
        expressions=(expression,),
    )
    candidate = GenerationCandidate(
        candidate_id="selected",
        provider_profile=sealed.provider_profile,
        capabilities=capabilities,
        capability_id=capability.capability_id,
        compiler_contract=compiler,
        output_requirement=output,
        recipe=recipe,
    )
    inputs = DecisionInputs(
        projection_hash=projection.projection_hash,
        facts_hash=VideoPlanner.generation_difficulty(projection)["facts_hash"],
        rubric_hash=acceptance.profile_content_hash,
        policy=DecisionPolicy(allow_bounded_exploration=True),
        limits=ExecutionLimits(
            task_id=task_id,
            generation_forbidden=False,
            allowed_remote_candidates=(
                (candidate.candidate_id,)
                if capability.execution_kind is VideoExecutionKind.REMOTE
                else ()
            ),
            paid_submit_ceiling=1 if capability.billing_kind is BillingKind.METERED else 0,
            paid_submits_used=0,
            local_batch_limit=1,
            local_batch_used=0,
            local_total_used=0,
            local_resource_available=True,
        ),
        candidates=(candidate,),
    )
    policy = _router_policy(
        remote_authorized=capability.execution_kind is VideoExecutionKind.REMOTE,
        budget_authorized=capability.billing_kind is BillingKind.METERED,
    )
    decision = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=policy,
        lifecycle=lifecycle,
        inputs=inputs,
    )
    if decision.routing is None or decision.routing.provider_bound_request is None:
        raise ValueError(
            "fixture decision did not produce a bound request: "
            f"{decision.disposition}; {decision.rationale}"
        )
    compiled = require_compiled_provider_request(
        provider.compile_request(decision.routing.provider_bound_request, requirement)
    )
    if not isinstance(compiled, CompiledProviderVideoRequest):
        raise AssertionError("compiled provider request was not typed")
    resolved = provider.resolve(compiled.request)
    binding = GenerationDecisionExecutionBinding.create(
        projection=projection,
        context=context,
        policy=policy,
        lifecycle=lifecycle,
        inputs=inputs,
        decision=decision,
        compiled_request=resolved,
    )
    return PreparedGenerationExecution(binding=binding, resolved=resolved)


__all__ = [
    "NativeFixtureVideoProvider",
    "PreparedGenerationExecution",
    "activate_generated_video_shot",
    "activate_fixture_generation_qa_policy",
    "fixture_generation_expression",
    "prepare_generation_execution",
]
