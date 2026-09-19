"""Exact Ecommerce composition preparation over canonical Production owners."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.ad_creative_types import (
    AdCreativePlan,
    AdCreativePlanProposal,
    CompiledAdCreativeHandoff,
)
from ai_video.production.commercial_graphics import (
    AdSoundRole,
    GraphicLayerAnimation,
    GraphicRole,
)
from ai_video.production.composition import resolve_composition
from ai_video.production.composition_contracts import (
    AudioKind,
    CompositionSpec,
    RendererKind,
    ResolvedTimeline,
)
from ai_video.production.ecommerce_job_contracts import (
    EcommerceJobNextAction,
    EcommerceProductionHandoff,
)
from ai_video.production.dependency import desired_fingerprints
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.hyperframes import (
    RenderDependencyTransitionPreparer,
    render_with_hyperframes,
)
from ai_video.production.models import (
    ProductionManifest,
    DependencyLifecycle,
    DependencyNodeKind,
    RenderDependencyEvidence,
    RendererSelectionReceipt,
    StateCommitStatus,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    ProductionStateCommitter,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_STATE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def validate_ecommerce_plan_binding(
    runtime_handoff: EcommerceProductionHandoff,
    compiled_handoff: CompiledAdCreativeHandoff,
    plan: AdCreativePlan,
) -> None:
    """Require the same sealed plan identity used by Shot and composition execution."""

    try:
        proposal = AdCreativePlanProposal.model_validate(
            plan.model_dump(
                mode="python",
                exclude={
                    "schema_version",
                    "artifact_id",
                    "revision",
                    "content_hash",
                    "creation_receipt_id",
                    "source_provenance",
                },
            )
        )
    except ValidationError as exc:
        raise _invalid("Ecommerce AdCreativePlan projection is invalid.", str(exc)) from exc
    provenance = {
        (item.reference, item.content_hash) for item in plan.source_provenance
    }
    required_provenance = {
        (
            f"ecommerce-handoff:{runtime_handoff.handoff_id}",
            runtime_handoff.handoff_id,
        ),
        (
            "ecommerce-compile-profile:"
            f"{runtime_handoff.compile_profile.profile_id}",
            runtime_handoff.compile_profile.profile_id,
        ),
    }
    if (
        not verify_artifact_hash(plan)
        or proposal != runtime_handoff.ad_creative_plan_proposal
        or not required_provenance.issubset(provenance)
        or compiled_handoff.plan_id != plan.artifact_id
        or compiled_handoff.plan_content_hash != plan.content_hash
    ):
        raise _invalid("Compiled Ecommerce execution is not bound to the selected plan.")


@dataclass(frozen=True)
class PreparedEcommerceComposition:
    project_root: Path
    composition_spec: CompositionSpec
    timeline: ResolvedTimeline
    asset_sources: Mapping[str, Path]
    begin_request: BeginRenderAttemptRequest


@dataclass(frozen=True)
class EcommerceHyperFramesInvocation:
    """Exact canonical render identity and pinned offline toolchain."""

    committer: ProductionStateCommitter
    attempt_id: str
    selection_receipt_id: str
    binary_path: Path
    browser_path: Path
    unshare_path: Path
    ip_path: Path
    bash_path: Path
    ffmpeg_path: Path | None = None
    ffprobe_path: Path | None = None
    dependency_transition_preparer: RenderDependencyTransitionPreparer | None = None


class EcommerceAssemblyState(str, Enum):
    RENDER = "render"
    ACTIVE = "active"
    RECOVER = "recover"


@dataclass(frozen=True)
class EcommerceAssemblyDecision:
    next_action: EcommerceJobNextAction
    error: BaseException | None = None


@dataclass(frozen=True)
class EcommerceCompositionExecutionPlan:
    """One exact HyperFrames invocation; canonical renderer/state owners stay external."""

    handoff: CompiledAdCreativeHandoff
    plan: AdCreativePlan
    renderer_version: str
    hyperframes: EcommerceHyperFramesInvocation

    def prepare(
        self,
        runtime_handoff: EcommerceProductionHandoff,
        *,
        project_root: Path,
    ) -> PreparedEcommerceComposition:
        validate_ecommerce_plan_binding(runtime_handoff, self.handoff, self.plan)
        if not project_root.is_absolute() or not self.renderer_version.strip():
            raise _invalid("Ecommerce composition execution identity is incomplete.")
        spec = self.handoff.composition_spec
        if (
            spec.schema_version != "2.2"
            or spec.requested_renderer is not RendererKind.HYPERFRAMES
            or spec.ad_creative_plan_id != self.plan.artifact_id
            or spec.ad_creative_plan_hash != self.plan.content_hash
        ):
            raise _invalid("Ecommerce composition is not bound to exact HyperFrames plan inputs.")
        expected_shots = tuple(
            item.shot_id for item in runtime_handoff.artifact_proposals.shots
        )
        if (
            spec.shot_ids != expected_shots
            or tuple(item.shot_id for item in self.handoff.shot_proposals)
            != expected_shots
        ):
            raise _invalid("Ecommerce composition Shot order does not match the handoff.")
        delivery = runtime_handoff.delivery_profile
        if (
            spec.delivery_profile.width != delivery.width
            or spec.delivery_profile.height != delivery.height
            or spec.delivery_profile.fps != delivery.fps
            or spec.delivery_profile.codec_profile != delivery.codec_profile
            or spec.sample_rate != delivery.audio_sample_rate_hz
        ):
            raise _invalid("Ecommerce composition delivery profile is stale.")

        expected_graphics = tuple(
            item
            for item in self.plan.graphic_treatments
            if item.role is not GraphicRole.DIALOGUE_SUBTITLE
        )
        if spec.commercial_graphics != expected_graphics:
            raise _invalid("Ecommerce commercial graphic binding is stale.")
        layer_by_id = {item.layer_id: item for item in spec.layers}
        expected_animations: list[GraphicLayerAnimation] = []
        for presentation in self.plan.product_presentations:
            if presentation.composition_layer_id is None:
                continue
            layer = layer_by_id.get(presentation.composition_layer_id)
            if (
                layer is None
                or layer.shot_id != presentation.shot_id
                or layer.asset_id != presentation.asset_id
                or layer.transform != presentation.transform_intent.transform
                or layer.opacity_milli
                != presentation.transform_intent.opacity_milli
            ):
                raise _invalid("Ecommerce product presentation binding is stale.")
            expected_animations.append(
                GraphicLayerAnimation(
                    layer_id=layer.layer_id,
                    entrance=presentation.entrance,
                    exit=presentation.exit,
                )
            )
        if spec.graphic_layer_animations != tuple(expected_animations):
            raise _invalid("Ecommerce product presentation animation is stale.")
        caption_ids = {item.binding_id for item in spec.caption_tracks}
        if any(
            item.role is GraphicRole.DIALOGUE_SUBTITLE
            and item.caption_binding_id not in caption_ids
            for item in self.plan.graphic_treatments
        ):
            raise _invalid("Ecommerce dialogue caption binding is missing or stale.")
        expected_sound_cues = tuple(
            (
                item.cue_id,
                item.role,
                item.audio_track_id,
                item.synchronized_event_id,
            )
            for item in self.plan.sound_cues
        )
        actual_sound_cues = tuple(
            (
                item.cue_id,
                item.role,
                item.audio_track_id,
                item.synchronized_event_id,
            )
            for item in spec.advertising_sound_cues
        )
        if actual_sound_cues != expected_sound_cues:
            raise _invalid("Ecommerce advertising sound cue binding is stale.")
        requirements = self.handoff.composition_requirements
        if (
            spec.graphic_layer_ids != requirements.graphic_layer_ids
            or tuple(item.graphic_id for item in spec.commercial_graphics)
            != requirements.commercial_graphic_ids
            or tuple(item.track_id for item in spec.audio_tracks)
            != requirements.audio_track_ids
        ):
            raise _invalid("Ecommerce audio or graphic composition requirements are stale.")
        audio_tracks = {item.track_id: item for item in spec.audio_tracks}
        audio_kind_by_role = {
            AdSoundRole.DIALOGUE: AudioKind.DIALOGUE,
            AdSoundRole.VOICE_OVER: AudioKind.NARRATION,
            AdSoundRole.MUSIC: AudioKind.BGM,
            AdSoundRole.SFX: AudioKind.SFX,
            AdSoundRole.REVEAL_HIT: AudioKind.SFX,
        }
        if any(
            item.role is not AdSoundRole.INTENTIONAL_SILENCE
            and (
                item.audio_track_id not in audio_tracks
                or audio_tracks[item.audio_track_id].audio_kind
                is not audio_kind_by_role[item.role]
            )
            for item in self.plan.sound_cues
        ):
            raise _invalid("Ecommerce required audio track is missing or mismatched.")

        if Path(self.hyperframes.committer.project_root).resolve() != project_root.resolve():
            raise _invalid("Ecommerce renderer is bound to another Project root.")
        loaded = load_production_project(project_root / "project.yaml")
        shots = {item.shot_id: item for item in loaded.shots}
        for layer in spec.layers:
            shot = shots.get(layer.shot_id)
            role = None if shot is None else next(
                (
                    item
                    for item in shot.required_asset_roles
                    if item.role == layer.asset_role
                ),
                None,
            )
            if role is None or layer.asset_id not in role.asset_ids:
                raise _invalid("Ecommerce composition references an unaccepted Shot asset.")

        timeline = resolve_composition(loaded, spec, self.renderer_version)
        asset_ids = {
            item.asset_id for item in (*timeline.visual_spans, *timeline.audio_spans)
        }
        asset_ids.update(item.caption_asset_id for item in timeline.caption_cues)
        sources: dict[str, Path] = {}
        for asset_id in sorted(asset_ids):
            source = loaded.asset_paths.get(asset_id)
            if source is None:
                raise _invalid("Resolved Ecommerce timeline has an unregistered source asset.")
            sources[asset_id] = Path(source)
        for binding in spec.caption_tracks:
            if binding.style_reference is not None:
                sources[binding.style_reference.artifact_id] = (
                    project_root / binding.style_reference.path
                )
        matching_attempts = tuple(
            item
            for item in loaded.manifest.attempts
            if item.attempt_id == self.hyperframes.attempt_id
        )
        if len(matching_attempts) > 1:
            raise _invalid("Ecommerce render attempt identity is ambiguous.")
        if matching_attempts:
            existing = matching_attempts[0]
            selection = existing.renderer_selection
            if (
                existing.operation != "render_state"
                or selection is None
                or selection.receipt_id != self.hyperframes.selection_receipt_id
                or selection.attempt_id != self.hyperframes.attempt_id
                or selection.requested_kind is not RendererKind.HYPERFRAMES
                or selection.selected_kinds != (RendererKind.HYPERFRAMES,)
                or selection.renderer_version != self.renderer_version
                or selection.timeline_fingerprint
                != timeline.composition_fingerprint
            ):
                raise _invalid("Durable Ecommerce render request identity is stale.")
            begin_request = BeginRenderAttemptRequest(
                expected_manifest_revision=existing.base_manifest_revision,
                base_render_state=existing.base_render_state,
                renderer_selection=selection,
            )
        else:
            selection = RendererSelectionReceipt(
                receipt_id=self.hyperframes.selection_receipt_id,
                attempt_id=self.hyperframes.attempt_id,
                requested_kind=RendererKind.HYPERFRAMES,
                selected_kinds=(RendererKind.HYPERFRAMES,),
                renderer_version=self.renderer_version,
                timeline_fingerprint=timeline.composition_fingerprint,
                current_project=loaded.manifest.active_project,
                current_registry=loaded.manifest.active_registry,
            )
            begin_request = BeginRenderAttemptRequest(
                expected_manifest_revision=loaded.manifest.manifest_revision,
                base_render_state=loaded.manifest.active_render_state,
                renderer_selection=selection,
            )
        return PreparedEcommerceComposition(
            project_root=project_root,
            composition_spec=spec,
            timeline=timeline,
            asset_sources=MappingProxyType(sources),
            begin_request=begin_request,
        )

    def render(
        self,
        prepared: PreparedEcommerceComposition,
    ) -> ProductionManifest:
        if (
            prepared.composition_spec.content_hash
            != self.handoff.composition_spec.content_hash
            or prepared.timeline.composition_spec_hash
            != prepared.composition_spec.content_hash
            or prepared.timeline.renderer.kind is not RendererKind.HYPERFRAMES
            or prepared.timeline.renderer.version != self.renderer_version
            or prepared.begin_request.renderer_selection.timeline_fingerprint
            != prepared.timeline.composition_fingerprint
        ):
            raise _invalid("Prepared Ecommerce render identity is stale.")
        invocation = self.hyperframes
        return render_with_hyperframes(
            committer=invocation.committer,
            begin_request=prepared.begin_request,
            timeline=prepared.timeline,
            asset_sources=prepared.asset_sources,
            allowed_asset_root=prepared.project_root,
            binary_path=invocation.binary_path,
            browser_path=invocation.browser_path,
            unshare_path=invocation.unshare_path,
            ip_path=invocation.ip_path,
            bash_path=invocation.bash_path,
            ffmpeg_path=invocation.ffmpeg_path,
            ffprobe_path=invocation.ffprobe_path,
            expected_version=self.renderer_version,
            dependency_transition_preparer=(
                invocation.dependency_transition_preparer
            ),
        )


def active_render_matches_prepared(
    prepared: PreparedEcommerceComposition,
) -> bool:
    """Verify the canonical active render against current desired inputs."""

    loaded = load_production_project(prepared.project_root / "project.yaml")
    pointer = loaded.manifest.active_render_state
    if pointer is None:
        return False
    state = loaded.render_state
    if state is None:
        return False
    graph = getattr(loaded, "dependency_graph", None)
    if graph is not None:
        render_kinds = {
            DependencyNodeKind.COMPOSITION_SPEC,
            DependencyNodeKind.RESOLVED_TIMELINE,
            DependencyNodeKind.RENDERER_SOURCE,
            DependencyNodeKind.RENDER,
        }
        render_nodes = tuple(item for item in graph.nodes if item.kind in render_kinds)
        states = {item.node_id: item for item in loaded.manifest.dependency_states}
        if len(render_nodes) != 4 or any(
            (node_state := states.get(node.node_id)) is None
            or node_state.lifecycle is not DependencyLifecycle.FRESH
            or node_state.applied_fingerprint != node_state.desired_fingerprint
            or not isinstance(node_state.applied_evidence, RenderDependencyEvidence)
            or node_state.applied_evidence.pointer != pointer
            for node in render_nodes
        ):
            return False
        desired = desired_fingerprints(graph)
        if any(
            states[node.node_id].desired_fingerprint != desired[node.node_id]
            for node in render_nodes
        ):
            return False
    return (
        state.timeline_fingerprint == prepared.timeline.composition_fingerprint
        and state.renderer.kind is RendererKind.HYPERFRAMES
        and state.renderer.version == prepared.timeline.renderer.version
        and state.renderer_selection.timeline_fingerprint
        == prepared.timeline.composition_fingerprint
        and state.project == loaded.manifest.active_project
        and state.registry == loaded.manifest.active_registry
    )


def inspect_ecommerce_assembly(
    execution: EcommerceCompositionExecutionPlan,
    runtime_handoff: EcommerceProductionHandoff,
    *,
    project_root: Path,
) -> EcommerceAssemblyState:
    """Recompute desired composition and classify canonical render state."""

    loaded = load_production_project(project_root / "project.yaml")
    if any(
        item.operation == "render_state"
        and item.status in {
            StateCommitStatus.RUNNING,
            StateCommitStatus.OUTCOME_UNKNOWN,
        }
        for item in loaded.manifest.attempts
    ):
        return EcommerceAssemblyState.RECOVER
    prepared = execution.prepare(runtime_handoff, project_root=project_root)
    if active_render_matches_prepared(prepared):
        return EcommerceAssemblyState.ACTIVE
    return EcommerceAssemblyState.RENDER


def inspect_ecommerce_job_assembly(
    execution: EcommerceCompositionExecutionPlan | None,
    runtime_handoff: EcommerceProductionHandoff,
    *,
    project_root: Path,
) -> EcommerceAssemblyDecision:
    if execution is None:
        return EcommerceAssemblyDecision(EcommerceJobNextAction.PREPARE_COMPOSITION)
    try:
        state = inspect_ecommerce_assembly(
            execution, runtime_handoff, project_root=project_root
        )
    except (AiVideoError, OSError, TypeError, ValueError) as exc:
        return EcommerceAssemblyDecision(EcommerceJobNextAction.BLOCKED, exc)
    action = {
        EcommerceAssemblyState.RENDER: EcommerceJobNextAction.RENDER_FINAL,
        EcommerceAssemblyState.ACTIVE: EcommerceJobNextAction.REVIEW_FINAL,
        EcommerceAssemblyState.RECOVER: EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME,
    }[state]
    return EcommerceAssemblyDecision(action)


def advance_ecommerce_job_assembly(
    execution: EcommerceCompositionExecutionPlan,
    runtime_handoff: EcommerceProductionHandoff,
    *,
    project_root: Path,
    render: bool,
) -> EcommerceAssemblyDecision:
    if not render:
        return inspect_ecommerce_job_assembly(
            execution, runtime_handoff, project_root=project_root
        )
    try:
        prepared = execution.prepare(runtime_handoff, project_root=project_root)
        manifest = execution.render(prepared)
        attempt_id = prepared.begin_request.renderer_selection.attempt_id
        attempt = next(
            (item for item in manifest.attempts if item.attempt_id == attempt_id),
            None,
        )
        if attempt is None:
            return EcommerceAssemblyDecision(
                EcommerceJobNextAction.BLOCKED,
                _invalid("Canonical render result omitted the exact attempt."),
            )
        if attempt.status in {
            StateCommitStatus.RUNNING,
            StateCommitStatus.OUTCOME_UNKNOWN,
        }:
            return EcommerceAssemblyDecision(
                EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME
            )
        if attempt.status is not StateCommitStatus.SUCCEEDED:
            return EcommerceAssemblyDecision(
                EcommerceJobNextAction.BLOCKED,
                _invalid(
                    "Canonical render attempt is terminal; provide a new diagnosed attempt."
                ),
            )
    except (AiVideoError, OSError, TypeError, ValueError) as exc:
        reopened = inspect_ecommerce_job_assembly(
            execution, runtime_handoff, project_root=project_root
        )
        if reopened.next_action in {
            EcommerceJobNextAction.RECOVER_UNKNOWN_OUTCOME,
            EcommerceJobNextAction.REVIEW_FINAL,
        }:
            return reopened
        return EcommerceAssemblyDecision(EcommerceJobNextAction.BLOCKED, exc)
    return inspect_ecommerce_job_assembly(
        execution, runtime_handoff, project_root=project_root
    )


__all__ = [
    "EcommerceCompositionExecutionPlan",
    "EcommerceHyperFramesInvocation",
    "EcommerceAssemblyState",
    "EcommerceAssemblyDecision",
    "PreparedEcommerceComposition",
    "active_render_matches_prepared",
    "inspect_ecommerce_assembly",
    "inspect_ecommerce_job_assembly",
    "advance_ecommerce_job_assembly",
    "validate_ecommerce_plan_binding",
]
