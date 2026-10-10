"""Reusable canvas workflow over canonical Production owners, with no state store."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from pydantic import ValidationError

from ai_video.canvas_authoring import author_canvas_project, direction_reference
from ai_video.canvas_planning import canvas_feedback_context
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._sequence_source import accepted_sequence_source
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator
from ai_video.production.project import load_production_project
from ai_video.production.video_generation import VideoGenerationService


def _blocked(message):
    return AiVideoError(ErrorCode.PRODUCTION_PROJECT_INVALID, message, retryable=False)


def _input_errors(method):
    @wraps(method)
    def call(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except ValidationError as error:
            locations = ", ".join(".".join(map(str, e["loc"])) or "input"
                                  for e in error.errors(include_input=False))
            raise _blocked(f"Canvas typed input rejected at {locations}.") from error
        except OSError as error:
            raise _blocked(f"Canvas local input is unavailable ({type(error).__name__}).") from error
        except (ValueError, KeyError, TypeError, StopIteration) as error:
            raise _blocked(f"Canvas input rejected: {error}") from error
    return call


@dataclass(frozen=True)
class CanvasWorkflowPosition:
    occurrence_id: str | None
    shot_id: str | None
    attempt_id: str | None
    next_action: str


class CanvasProductionService:
    """Configured once; stories supply data rather than their own execution code.

    Each call performs at most one durable action. Provider effects, budgets,
    evaluation, activation, graph transitions and rendering keep their existing
    owners. Unknown outcomes return STOP and require explicit canonical recovery.
    """

    def __init__(self, *, committer, packet, direction, targets=(), routing_policy=None,
                 decision_policy=None, execution_stack=None, handoff_preparer=None):
        self.committer = committer
        self.packet, self.direction = deepcopy(packet), deepcopy(direction)
        self.targets = tuple(targets)
        self.routing_policy, self.decision_policy = routing_policy, decision_policy
        self.execution_stack, self.handoff_preparer = execution_stack, handoff_preparer

    @classmethod
    @_input_errors
    def from_inspection(cls, *, inspection, **configuration):
        """Consume the explicit source adapter result without importing scripts."""
        from ai_video.canvas_authoring import input_hash
        selection = inspection.get("selection", {})
        if selection.get("status") != "CANONICAL_PACKET_AVAILABLE":
            raise _blocked("Selected canvas source has unresolved inspection blockers.")
        packet = selection.get("sequence_packet")
        if (packet is None or input_hash(inspection["source_snapshot"]) != inspection["source_snapshot_sha256"]
                or packet["source_snapshot_sha256"] != inspection["source_snapshot_sha256"]
                or input_hash(packet) != selection.get("sequence_packet_sha256")):
            raise _blocked("Inspected canvas snapshot identity changed.")
        return cls(packet=packet, **configuration)

    @_input_errors
    def author(self, *, registry=None, asset_artifacts=(), png_selections=None, allowed_asset_root=None):
        if png_selections is not None:
            if registry is not None or asset_artifacts or allowed_asset_root is None:
                raise ValueError("choose existing Registry inputs or explicit contained PNG selections")
            from ai_video.canvas_assets import prepare_canvas_png_assets
            registry, asset_artifacts = prepare_canvas_png_assets(packet=self.packet,
                selections=png_selections, allowed_asset_root=allowed_asset_root)
        return author_canvas_project(packet=self.packet, direction=self.direction,
            registry=registry, asset_artifacts=asset_artifacts)

    def approve_authoring(self, *, bundle, attempt_id, qa_policy):
        """Persist explicit creative approval and the supplied existing QA policy."""
        from ai_video.canvas_dependencies import initialize_canvas_graph
        if direction_reference(self.packet, self.direction) not in bundle.project.source_provenance:
            raise _blocked("Authoring bundle does not bind this canvas and director input.")
        bundle.bootstrap(committer=self.committer, attempt_id=attempt_id)
        self._load()
        initialize_canvas_graph(self.committer, f"{attempt_id}-graph")
        loaded = self._load()
        manifest = self.committer.upgrade_manifest_schema("2.14",
            expected_manifest_revision=loaded.manifest.manifest_revision)
        return self.committer.activate_qa_policy(qa_policy, attempt_id=f"{attempt_id}-qa",
            expected_manifest_revision=manifest.manifest_revision)

    @_input_errors
    def revise_authoring(self, *, attempt_id):
        """Approve new director input; preserve history and let the P5 owner rebase."""
        from dataclasses import replace
        from ai_video.production.state_commit import prepare_project_registry_commit
        from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
        from ai_video.production.models import ProductionBrief, Story, Character, Scene, Storyboard, Shot
        previous = load_production_project(self.committer.project_root / "project.yaml")
        if direction_reference(self.packet, self.direction) in previous.project.source_provenance:
            return previous.manifest
        bundle = author_canvas_project(packet=self.packet, direction=self.direction, previous=previous)
        request = prepare_project_registry_commit(manifest=previous.manifest, project=bundle.project,
            registry=bundle.registry, attempt_id=attempt_id)
        request = replace(request, artifacts=tuple(sorted((*request.artifacts, *bundle.artifacts),
            key=lambda a: a.relative_path.as_posix())))
        def models(kind):
            return tuple(m for m in bundle.creative_artifacts if isinstance(m, kind))
        candidate = previous.model_copy(update={"project": bundle.project, "registry": bundle.registry,
            "brief": models(ProductionBrief)[0], "story": models(Story)[0],
            "characters": models(Character), "scenes": models(Scene),
            "storyboard": models(Storyboard)[0], "shots": models(Shot)})
        request = prepare_strategy_dependency_transition(base_loaded=previous,
            candidate_loaded=candidate, request=request)
        return self.committer.commit(request)

    def _load(self):
        loaded = load_production_project(self.committer.project_root / "project.yaml")
        if direction_reference(self.packet, self.direction) not in loaded.project.source_provenance:
            raise _blocked("Canvas source or director data changed; approve a canonical authoring revision.")
        expected = [row["shot"]["shot_id"] for row in self.direction["shots"]]
        if expected != [s for b in loaded.storyboard.beats for s in b.shot_ids]:
            raise _blocked("Selected canvas occurrences no longer match the approved Storyboard.")
        return loaded

    def _attempts(self, loaded, shot_id):
        found = []
        for attempt in loaded.manifest.attempts:
            state = attempt.video_generation_state
            if state is None:
                continue
            request = self.committer._reopen_video_request(state.request)
            if request.activation_scope is not None and request.activation_scope.request.target_shot_id == shot_id:
                found.append(attempt)
        return found

    @_input_errors
    def position(self):
        """Reopen progress from actual requests/adoption, never occurrence counters."""
        loaded = self._load()
        for row in self.direction["shots"]:
            shot_id = row["shot"]["shot_id"]
            shot = next(s for s in loaded.shots if s.shot_id == shot_id)
            # Existing static/graphics composition remains available without Video Provider.
            if shot.visual_strategy.value != "generated_video":
                continue
            attempts = self._attempts(loaded, shot_id)
            if len(attempts) > 1:
                raise _blocked("Multiple attempts require explicit adopted-version/recovery decisions.")
            if not attempts:
                return CanvasWorkflowPosition(row["occurrence_id"], shot_id, None, "prepare")
            attempt = attempts[0]
            action = VideoGenerationService(committer=self.committer, provider=None).resume_next_action(
                attempt_id=attempt.attempt_id)
            if action == "done":
                # Activation alone is not a per-Shot PASS. Missing evidence stops before the next Shot.
                accepted_sequence_source(loaded, shot)
                continue
            return CanvasWorkflowPosition(row["occurrence_id"], shot_id, attempt.attempt_id, action)
        return CanvasWorkflowPosition(None, None, None, "compose")

    def _orchestrator(self, row):
        if self.routing_policy is None or self.decision_policy is None:
            raise _blocked("Configure the existing routing/decision policies before generation.")

        def context(loaded):
            # Every prepare reopens source bytes, approved director binding and actual predecessor.
            self._load()
            return canvas_feedback_context(loaded=loaded, row=row, policy=self.routing_policy,
                execution_stack=self.execution_stack, handoff_preparer=self.handoff_preparer)

        return GenerationFeedbackOrchestrator.for_project(committer=self.committer,
            targets=self.targets, context_loader=context, policy=self.decision_policy)

    @_input_errors
    def prepare(self, *, limits):
        position = self.position()
        if position.next_action != "prepare":
            raise _blocked(f"Current canvas action is {position.next_action}; do not create another attempt.")
        row = next(r for r in self.direction["shots"] if r["occurrence_id"] == position.occurrence_id)
        return self._orchestrator(row).prepare(limits=limits)

    def generate_voice(self, *, prepared, **authorized_runtime):
        """Use the existing selected voice handoff, then reprepare from its Registry."""
        position = self.position()
        if position.next_action != "prepare" or position.shot_id != prepared.target_shot_id:
            raise _blocked("Voice handoff does not match the current unsubmitted Shot.")
        row = next(r for r in self.direction["shots"] if r["occurrence_id"] == position.occurrence_id)
        return self._orchestrator(row).generate_selected_voice(committer=self.committer,
            prepared=prepared, **authorized_runtime)

    @_input_errors
    def start(self, *, limits):
        position = self.position()
        if position.next_action != "prepare":
            return position
        row = next(r for r in self.direction["shots"] if r["occurrence_id"] == position.occurrence_id)
        prepared = self._orchestrator(row).prepare(limits=limits)
        if prepared.execution_binding is None:
            return prepared  # Router's typed capability/authoring exit, no Provider effect.
        from ai_video.canvas_authoring import input_hash
        attempt_id = "canvas-" + input_hash({"project": self.direction["project_id"],
            "task": limits.task_id, "shot": position.shot_id,
            "generation": prepared.execution_binding.lifecycle.generation_id})[:40]
        VideoGenerationService(committer=self.committer, provider=prepared.provider).start(
            attempt_id=attempt_id, request=prepared.resolved_request,
            execution_binding=prepared.execution_binding)
        return self.position()

    def _service(self, attempt_id):
        loaded = self._load()
        attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == attempt_id)
        state = attempt.video_generation_state
        if state is None or state.execution_binding is None:
            raise _blocked("Canvas attempt has no canonical generation execution binding.")
        binding = self.committer._reopen_generation_execution_binding(state.execution_binding)
        route = binding.selected_provider_route
        targets = [t for t in self.targets if t.profile == route.provider_profile
                   and t.compiler_contract == route.compiler_contract
                   and t.provider.capabilities().provider_name == route.provider_name]
        if len(targets) != 1:
            raise _blocked("Reopened attempt requires one exact configured Provider; no fallback.")
        return VideoGenerationService(committer=self.committer, provider=targets[0].provider)

    def _require_evaluation(self, attempt_id):
        self._load()
        attempt, state = VideoGenerationService(committer=self.committer, provider=None)._state(attempt_id)
        fetch = state.local_fetch_receipt or state.fetch_receipt
        if fetch is None or not state.generation_experiences:
            raise _blocked("Exact fetched MP4 requires the explicit per-Shot media Gate.")
        from ai_video.production.generation_diagnosis import diagnose_exact_result
        histories = self.committer.read_generation_experiences()
        experiences = [x for x in histories if any(e.attempt_id == attempt_id for e in x.evidence)]
        entries = tuple(e for x in histories for e in x.evidence)
        sources = tuple(s for x in histories for s in x.evaluation_sources)
        for experience in reversed(experiences):
            for entry in reversed(experience.evidence):
                if entry.attempt_id == attempt_id and entry.artifact_sha256 == fetch.artifact_sha256:
                    result = diagnose_exact_result(entry, entries, experience.candidate.recipe,
                        evaluation_sources=sources, requirement=experience.projection.requirement)
                    if result.all_required_observed_pass:
                        return result
                    raise _blocked("Exact media Gate is FAIL or NOT_EVALUATED; stop this attempt.")
        raise _blocked("Exact media Gate evidence is missing or stale.")

    async def evaluate(self, *, session, adjudicate, repair_evidence=False):
        """Explicit project-local video-analysis path; replay stays in its owner."""
        from ai_video_mcp.generation_feedback import review_generation_attempt
        position = self.position()
        if position.attempt_id is None or position.next_action == "stop":
            raise _blocked("No known fetched attempt is eligible for media evaluation.")
        return await review_generation_attempt(committer=self.committer, attempt_id=position.attempt_id,
            session=session, adjudicate=adjudicate, repair_evidence=repair_evidence)

    def execute(self, *, action, **arguments):
        """Perform one exact next action using current existing gates/permits."""
        position = self.position()
        if action != position.next_action or action not in {"submit", "poll", "fetch", "validate", "activate"}:
            raise _blocked(f"Requested {action}; durable next action is {position.next_action}.")
        service = self._service(position.attempt_id)
        _, state = service._state(position.attempt_id)
        request = self.committer._reopen_video_request(state.request)
        local = request.execution_kind.value == "local"
        if action == "submit":
            if local:
                return service.submit_local_once(attempt_id=position.attempt_id, **arguments)
            return service.submit_once(attempt_id=position.attempt_id, **arguments)
        if action == "poll":
            refresh = service.refresh_local_once if local else service.refresh_once
            return refresh(attempt_id=position.attempt_id, **arguments)
        if action == "fetch":
            fetch = service.fetch_local_once if local else service.fetch_once
            return fetch(attempt_id=position.attempt_id, **arguments)
        self._require_evaluation(position.attempt_id)
        if action == "validate":
            return service.validate_once(attempt_id=position.attempt_id, **arguments)
        return service.activate_once(attempt_id=position.attempt_id, **arguments)

    @_input_errors
    def compose(self, *, renderer_version="0.7.103", audio_tracks=(), caption_tracks=(), voice_sources=()):
        from ai_video.canvas_composition import compose_canvas
        loaded = self._load()
        if self.position().next_action != "compose":
            raise _blocked("Every selected generated Shot must pass and be adopted before composition.")
        return compose_canvas(loaded=loaded, direction=self.direction, renderer_version=renderer_version,
            audio_tracks=audio_tracks, caption_tracks=caption_tracks, voice_sources=voice_sources)

    def deliver(self):
        """Exact canonical final media; this read never signs human acceptance."""
        self._load()
        return self.committer.current_final_media_target()

    @_input_errors
    def register_native_audio(self, *, shot_id, audio_kind, usage_license, toolchain,
                              speaker_id=None, voice_id=None, language=None):
        """Extract exact adopted video audio through its existing owner, never mux."""
        from ai_video.canvas_authoring import input_hash
        from ai_video.canvas_dependencies import canvas_audio_transition_preparer
        from ai_video.production.generated_video_audio import GeneratedVideoAudioRequest
        from ai_video.production.models import AudioKind
        loaded = self._load()
        shot = next(s for s in loaded.shots if s.shot_id == shot_id)
        _, request, _, _, _ = accepted_sequence_source(loaded, shot)
        matches = self._attempts(loaded, shot_id)
        if len(matches) != 1:
            raise _blocked("Native audio requires one exact accepted source attempt.")
        kind = AudioKind(audio_kind)
        script = shot.dialogue if kind is AudioKind.DIALOGUE else shot.narration if kind is AudioKind.NARRATION else None
        import hashlib
        identity = input_hash({"request": request.request_input_hash, "kind": kind.value,
            "speaker": speaker_id, "voice": voice_id, "language": language, "license": usage_license})[:40]
        asset_id = f"canvas-audio-{identity}"
        audio_request = GeneratedVideoAudioRequest(attempt_id=f"canvas-audio-import-{identity}",
            asset_id=asset_id, source_project_root=loaded.root, source_attempt_id=matches[0].attempt_id,
            audio_kind=kind, usage_license=usage_license, speaker_id=speaker_id, voice_id=voice_id,
            language=language, script_hash=hashlib.sha256(script.encode()).hexdigest() if script else None)
        return self.committer.register_generated_video_audio(audio_request, toolchain=toolchain,
            dependency_transition_preparer=canvas_audio_transition_preparer(self.committer,
                shot_id=shot_id, asset_id=asset_id, audio_kind=kind))

    def render(self, *, attempt_id, toolchain, renderer_version="0.7.103", audio_tracks=(),
               caption_tracks=(), voice_sources=(), voice_requests=(), caption_style_fingerprints=()):
        """One configured HyperFrames invocation; durable replay stays in its owner."""
        from ai_video.canvas_dependencies import canvas_dependency_inputs, canvas_render_transition_preparer
        from ai_video.production.hyperframes import render_with_hyperframes
        from ai_video.production.models import RendererSelectionReceipt
        from ai_video.production.state_commit import BeginRenderAttemptRequest
        spec, timeline = self.compose(renderer_version=renderer_version, audio_tracks=audio_tracks,
            caption_tracks=caption_tracks, voice_sources=voice_sources)
        loaded = self._load()
        selection = RendererSelectionReceipt(receipt_id=f"canvas-render-{attempt_id}", attempt_id=attempt_id,
            requested_kind="hyperframes", selected_kinds=("hyperframes",), renderer_version=renderer_version,
            timeline_fingerprint=timeline.composition_fingerprint, current_project=loaded.manifest.active_project,
            current_registry=loaded.manifest.active_registry)
        sources = {span.asset_id: loaded.asset_paths[span.asset_id]
                   for span in (*timeline.visual_spans, *timeline.audio_spans)}
        sources.update({cue.caption_asset_id: loaded.asset_paths[cue.caption_asset_id] for cue in timeline.caption_cues})
        for binding in spec.caption_tracks:
            if binding.style_reference:
                sources[binding.style_reference.artifact_id] = loaded.root / binding.style_reference.path
        inputs = canvas_dependency_inputs(loaded, spec, renderer_version,
            voice_requests=voice_requests, caption_style_fingerprints=caption_style_fingerprints)
        existing = next((a for a in loaded.manifest.attempts if a.attempt_id == attempt_id), None)
        if existing is not None:
            if existing.operation != "render_state" or existing.renderer_selection != selection:
                raise _blocked("Render attempt identity was already used for different inputs.")
            begin = BeginRenderAttemptRequest(existing.base_manifest_revision,
                existing.base_render_state, existing.renderer_selection)
        else:
            begin = BeginRenderAttemptRequest(loaded.manifest.manifest_revision,
                loaded.manifest.active_render_state, selection)
        return render_with_hyperframes(committer=self.committer,
            begin_request=begin, timeline=timeline,
            asset_sources=sources, allowed_asset_root=loaded.root, expected_version=renderer_version,
            dependency_transition_preparer=canvas_render_transition_preparer(self.committer, inputs), **toolchain)
