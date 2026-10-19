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
                 decision_policy=None, production_policy=None, execution_stack=None, handoff_preparer=None):
        self.committer = committer
        self.packet, self.direction = deepcopy(packet), deepcopy(direction)
        self.targets = tuple(targets)
        self.routing_policy, self.decision_policy = routing_policy, decision_policy
        self.production_policy = production_policy
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
        previous = None
        if self.committer is not None:
            project_path = self.committer.project_root / "project.yaml"
            if project_path.exists():
                previous = load_production_project(project_path)
        return author_canvas_project(packet=self.packet, direction=self.direction,
            registry=registry, asset_artifacts=asset_artifacts, previous=previous)

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
    def revise_authoring(self, *, attempt_id, registry=None, asset_artifacts=()):
        """Approve new director input; preserve history and let the P5 owner rebase."""
        from dataclasses import replace
        from ai_video.production.state_commit import prepare_project_registry_commit
        from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
        from ai_video.production.models import ProductionBrief, Story, Character, Scene, Storyboard, Shot
        previous = load_production_project(self.committer.project_root / "project.yaml")
        if (direction_reference(self.packet, self.direction) in previous.project.source_provenance
                and (registry is None or registry == previous.registry)):
            return previous.manifest
        bundle = author_canvas_project(packet=self.packet, direction=self.direction, previous=previous,
            registry=registry, asset_artifacts=asset_artifacts)
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
        expected = []
        active = {s.shot_id for s in loaded.shots}
        for row in self.direction["shots"]:
            shot_id = row["shot"]["shot_id"]
            if shot_id in active:
                expected.append(shot_id)
            else:
                from ai_video.production.production_strategy_reader import production_parent_context
                _, family, _, _ = production_parent_context(loaded, shot_id)
                expected.extend(family)
        if expected != [s for b in loaded.storyboard.beats for s in b.shot_ids]:
            raise _blocked("Selected canvas occurrences no longer match the approved Storyboard.")
        return loaded

    def _production_planning(self):
        from ai_video.production_planning import ProductionPlanningService
        self._load()
        return ProductionPlanningService(committer=self.committer, targets=self.targets, policy=self.production_policy)

    @_input_errors
    def prepare_production(self, *, parent_shot_id, include_control_report=False):
        """Assess existing-source/edit means before any generation, without writes."""
        return self._production_planning().prepare(parent_shot_id=parent_shot_id,
            include_control_report=include_control_report)

    @_input_errors
    def materialize_production(self, *, decision, attempt_id):
        from ai_video.production.production_strategy_contracts import ProductionStrategyDecision
        decision = ProductionStrategyDecision.model_validate(decision)
        return self._production_planning().materialize(decision=decision, attempt_id=attempt_id)

    @_input_errors
    def compose_production(self, *, decision, renderer_version="0.7.103"):
        from ai_video.production.production_strategy_contracts import ProductionStrategyDecision
        decision = ProductionStrategyDecision.model_validate(decision)
        return self._production_planning().composition(decision=decision, renderer_version=renderer_version)

    @_input_errors
    def prepare_image_assets(self, *, operations):
        from ai_video.production.image_preparation import prepare_canvas_image_assets
        return prepare_canvas_image_assets(self._load(), operations)

    @_input_errors
    def bootstrap_video_cleanup(self, *, bundle, cleanup_plan, ffmpeg_executable,
                                ffprobe_executable, viewing_proxy=True, **arguments):
        """One explicit local cleanup capture; never adopts or activates a Shot."""
        from pathlib import Path
        from ai_video.production.video_cleanup_media import VideoCleanupTools
        from ai_video.production.repair_input_admission import verify_repair_input

        manifest = self.committer.bootstrap_repair_input(project=bundle.project,
            registry=bundle.registry, artifacts=bundle.artifacts, cleanup_plan=cleanup_plan,
            cleanup_tools=VideoCleanupTools(ffmpeg=Path(ffmpeg_executable), ffprobe=Path(ffprobe_executable)),
            cleanup_viewing_proxy=viewing_proxy,
            **arguments)
        loaded = load_production_project(self.committer.project_root / "project.yaml")
        master = next(item for item in loaded.registry.assets if item.asset_id == arguments["asset_id"])
        output_id = master.asset_id + "-viewing" if viewing_proxy else master.asset_id
        asset = next(item for item in loaded.registry.assets if item.asset_id == output_id)
        receipt = verify_repair_input(asset, loaded.root)
        return {"manifest_revision": manifest.manifest_revision,
            "output_path": str(loaded.asset_paths[asset.asset_id]), "output_sha256": asset.sha256,
            "master_path": str(loaded.asset_paths[master.asset_id]), "master_sha256": master.sha256,
            "viewing_proxy": viewing_proxy,
            "source_sha256": receipt.artifact_sha256, "receipt_hash": receipt.content_hash,
            "qualification": receipt.qualification, "generation_calls": 0,
            "tracking": "explicit_affine_per_frame", "audio": "original_samples_preserved",
            "production_acceptance": "NOT_EVALUATED"}

    @_input_errors
    def prepare_image_workflow(self, **arguments):
        from ai_video.canvas_image_workflow import prepare_canvas_masked_image
        return prepare_canvas_masked_image(loaded=self._load(), **arguments)

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

    def _bound_state_reference(self, loaded, row):
        from ai_video.canvas_handoff import require_canvas_state_reference, require_canvas_video_reference
        plan = row["state_reference"]
        expected = {"source_shot_id": plan["source_shot_id"], "frame_index": plan["frame_index"],
                    "original_asset_id": plan["replace_asset_id"]}
        matches = [(aid, value) for aid, value in row.get("reference_replacements", {}).items()
                   if all(value.get(key) == value_ for key, value_ in expected.items())]
        if not matches:
            return None
        if len(matches) != 1:
            raise _blocked("Selected state reference has ambiguous lineage.")
        aid, replacement = matches[0]
        asset = next(a for a in loaded.registry.assets if a.asset_id == aid)
        state = require_canvas_state_reference(loaded=loaded, asset=asset)
        if (state["source_shot_id"] != plan["source_shot_id"]
                or state["reference"]["frame_index"] != plan["frame_index"]
                or asset.usage_license != plan["usage_license"]
                or state["assessment"]["context"]["checks"] != plan["checks"]):
            raise _blocked("Selected state reference Gate no longer covers the authored requirements.")
        conditioning = plan.get("conditioning", "extracted_frame")
        if conditioning == "source_video":
            video_asset = next(a for a in loaded.registry.assets
                               if a.asset_id == replacement.get("video_asset_id"))
            video = require_canvas_video_reference(loaded=loaded, asset=video_asset,
                                                   source_shot_id=plan["source_shot_id"])
            expected.update(conditioning="source_video", video_asset_id=video_asset.asset_id,
                            video_asset_sha256=video_asset.sha256)
            selected = [ref for ref in row["generation"]["references"]
                        if ref.get("asset_id") == video_asset.asset_id and ref.get("role") == "existing_video"]
            if (len(selected) != 1 or state["reference"]["source_video_sha256"] != video_asset.sha256
                    or state["source_request_hash"] != video["request_input_hash"]):
                raise _blocked("Selected original MP4 and approved state do not share accepted-source lineage.")
        elif conditioning != "extracted_frame":
            raise _blocked("Unsupported state reference conditioning.")
        if replacement != expected:
            raise _blocked("State reference replacement differs from the approved conditioning plan.")
        return asset

    @_input_errors
    def position(self):
        """Reopen progress from actual requests/adoption, never occurrence counters."""
        loaded = self._load()
        for row in self.direction["shots"]:
            shot_id = row["shot"]["shot_id"]
            shot = next((s for s in loaded.shots if s.shot_id == shot_id), None)
            if shot is None:
                from ai_video.production.production_strategy_reader import (
                    production_parent_context,
                    require_production_source_eligibility,
                )

                _, family_ids, _, _ = production_parent_context(loaded, shot_id)
                family_children = tuple(
                    child for child in loaded.shots
                    if child.shot_id in set(family_ids) and child.production_lineage is not None
                )
                family_attempts = [
                    attempt
                    for family_shot_id in (shot_id, *family_ids)
                    for attempt in self._attempts(loaded, family_shot_id)
                ]
                unresolved = next((attempt for attempt in family_attempts
                                   if attempt.status.value in {"outcome_unknown", "interrupted"}), None)
                if unresolved is not None:
                    return CanvasWorkflowPosition(row["occurrence_id"], shot_id,
                                                  unresolved.attempt_id, "stop")
                if not family_children or any(child.production_lineage.source is None
                                              for child in family_children):
                    return CanvasWorkflowPosition(row["occurrence_id"], shot_id, None,
                                                  "prepare_production")
                try:
                    require_production_source_eligibility(
                        loaded, family_shot_id=family_children[0].shot_id
                    )
                except AiVideoError:
                    return CanvasWorkflowPosition(row["occurrence_id"], shot_id, None,
                                                  "prepare_production")
                continue
            if shot.production_intent is not None:
                return CanvasWorkflowPosition(row["occurrence_id"], shot_id, None, "prepare_production")
            # Existing static/graphics composition remains available without Video Provider.
            if shot.visual_strategy.value != "generated_video":
                continue
            attempts = self._attempts(loaded, shot_id)
            if not attempts:
                plan = row.get("state_reference")
                if plan is not None:
                    if self._bound_state_reference(loaded, row) is None:
                        return CanvasWorkflowPosition(row["occurrence_id"], shot_id, None, "handoff_reference")
                return CanvasWorkflowPosition(row["occurrence_id"], shot_id, None, "prepare")
            from ai_video.canvas_recovery import current_canvas_attempt
            attempt = current_canvas_attempt(self.committer, attempts)
            action = VideoGenerationService(committer=self.committer, provider=None).resume_next_action(
                attempt_id=attempt.attempt_id)
            if action == "done":
                # Activation alone is not a per-Shot PASS. Missing evidence stops before the next Shot.
                accepted_sequence_source(loaded, shot)
                continue
            return CanvasWorkflowPosition(row["occurrence_id"], shot_id, attempt.attempt_id, action)
        return CanvasWorkflowPosition(None, None, None, "compose")

    def _orchestrator(self, row, *, repair_receipt=None):
        if self.routing_policy is None or self.decision_policy is None:
            raise _blocked("Configure the existing routing/decision policies before generation.")

        unsubmitted_predecessor_evidence_hash = None
        if getattr(repair_receipt, "outcome", None) == "not_submitted":
            from ai_video.canvas_recovery import closed_unsubmitted_evidence

            shot_id = row["shot"]["shot_id"]
            loaded = self._load()
            matching = [
                attempt for attempt in self._attempts(loaded, shot_id)
                if closed_unsubmitted_evidence(self.committer, attempt) == repair_receipt
            ]
            if len(matching) != 1:
                raise _blocked("Closed unsubmitted predecessor is not unique and canonical.")
            predecessor = matching[0]
            binding = self.committer._reopen_generation_execution_binding(
                predecessor.video_generation_state.execution_binding
            )
            if (binding.context.target_shot_id != shot_id
                    or binding.inputs.limits.task_id != repair_receipt.task_id
                    or repair_receipt.shot_id != shot_id):
                raise _blocked("Closed unsubmitted predecessor differs from the current Shot or task.")
            unsubmitted_predecessor_evidence_hash = repair_receipt.evidence_hash

        def context(loaded):
            # Every prepare reopens source bytes, approved director binding and actual predecessor.
            self._load()
            current = canvas_feedback_context(loaded=loaded, row=row, policy=self.routing_policy,
                execution_stack=self.execution_stack, handoff_preparer=self.handoff_preparer)
            if repair_receipt is not None:
                from ai_video.canvas_authoring import input_hash
                receipt_hash = (getattr(repair_receipt, "content_hash", None)
                                or getattr(repair_receipt, "evidence_hash", None)
                                or getattr(repair_receipt, "observation_fingerprint", None)
                                or repair_receipt.submit_receipt_fingerprint)
                identity = input_hash({"generation": current["lifecycle"].generation_id,
                                       "rejection": receipt_hash})[:32]
                current["lifecycle"] = current["lifecycle"].model_copy(update={
                    "generation_id": f"canvas-generation-repair-{identity}",
                    "output_asset_id": f"canvas-video-repair-{identity}"})
            return current

        return GenerationFeedbackOrchestrator.for_project(committer=self.committer,
            targets=self.targets, context_loader=context, policy=self.decision_policy,
            unsubmitted_predecessor_evidence_hash=unsubmitted_predecessor_evidence_hash)

    @_input_errors
    def prepare(self, *, limits):
        position = self.position()
        if position.next_action != "prepare":
            raise _blocked(f"Current canvas action is {position.next_action}; do not create another attempt.")
        row = next(r for r in self.direction["shots"] if r["occurrence_id"] == position.occurrence_id)
        return self._orchestrator(row).prepare(limits=limits)

    def _repair_context(self, limits, interventions):
        position = self.position()
        if position.next_action != "stop" or position.attempt_id is None:
            raise _blocked("Explicit repair requires a closed quality or known-no-effect failure.")
        loaded = self._load()
        attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == position.attempt_id)
        from ai_video.production.models import StateCommitStatus
        if attempt.status is not StateCommitStatus.FAILED:
            raise _blocked("Explicit repair requires a closed quality or known-no-effect failure; unknown stops remain closed.")
        pointer = attempt.video_generation_state.quality_rejection
        if pointer is not None:
            receipt = self.committer._reopen_generation_quality_rejection(pointer)
        else:
            from ai_video.canvas_recovery import closed_unsubmitted_evidence
            receipt = closed_unsubmitted_evidence(self.committer, attempt)
            if receipt is None:
                from ai_video.production._lifecycle_schema import PaidProviderAttemptPhase
                paid = attempt.paid_provider_state
                if (paid is not None and paid.phase in {
                        PaidProviderAttemptPhase.ACCEPTED,
                        PaidProviderAttemptPhase.SETTLED,
                }):
                    from ai_video.production._state_commit_video_runtime_repair import (
                        closed_paid_known_failure_proof,
                    )
                    _paid_receipt, _submission, receipt, _request = closed_paid_known_failure_proof(
                        self.committer, attempt
                    )
                else:
                    from ai_video.production._state_commit_video_runtime_repair import closed_paid_no_effect_receipt
                    receipt = closed_paid_no_effect_receipt(self.committer, attempt)
        binding = self.committer._reopen_generation_execution_binding(
            attempt.video_generation_state.execution_binding)
        if limits.task_id != binding.inputs.limits.task_id:
            raise _blocked("Explicit repair must retain the predecessor task identity.")
        row = next(r for r in self.direction["shots"] if r["occurrence_id"] == position.occurrence_id)
        return position, row, receipt

    def _quality_repair_strategy(self, position):
        """Return to the sole production-means owner before another quality attempt."""
        loaded = self._load()
        attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == position.attempt_id)
        if attempt.video_generation_state.quality_rejection is None:
            return None
        from ai_video.production.production_strategy_reader import production_parent_context
        try:
            production_parent_context(loaded, position.shot_id)
        except AiVideoError as error:
            raise _blocked("Closed quality repair requires an authored ProductionIntent with existing-source/edit "
                           "options and protected requirements; run prepare_production before more generation.") from error
        return self.prepare_production(parent_shot_id=position.shot_id)

    @_input_errors
    def prepare_repair(self, *, limits, interventions=()):
        """Explicitly hand a closed exact result to the existing decision owner."""
        position, row, receipt = self._repair_context(limits, interventions)
        strategy = self._quality_repair_strategy(position)
        if strategy is not None:
            return strategy
        return self._orchestrator(row, repair_receipt=receipt).prepare(
            limits=limits, interventions=interventions)

    @_input_errors
    def start_repair(self, *, limits, interventions=()):
        """Start at most one proven successor; never submit or close old media."""
        position = self.position()
        if position.attempt_id is not None and position.next_action != "stop":
            if len(self._attempts(self._load(), position.shot_id)) > 1:
                return position
        position, row, receipt = self._repair_context(limits, interventions)
        strategy = self._quality_repair_strategy(position)
        if strategy is not None:
            return strategy
        prepared = self._orchestrator(row, repair_receipt=receipt).prepare(
            limits=limits, interventions=interventions)
        return self._start_prepared(position, prepared, limits)

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
        return self._start_prepared(position, prepared, limits)

    def _start_prepared(self, position, prepared, limits):
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
                        from ai_video.canvas_target_gate import require_target_state_findings
                        row = next(r for r in self.direction["shots"]
                                   if r["shot"]["shot_id"] == entry.shot_id)
                        try:
                            require_target_state_findings(loaded=self._load(), row=row, entry=entry)
                        except ValueError as error:
                            raise _blocked(str(error)) from error
                        return result
                    raise _blocked("Exact media Gate is FAIL or NOT_EVALUATED; stop this attempt.")
        raise _blocked("Exact media Gate evidence is missing or stale.")

    async def evaluate(self, *, session, adjudicate=None, repair_evidence=False, presentation_verifier=None,
                       understand_audio=False):
        """Explicit project-local video-analysis path; replay stays in its owner."""
        from ai_video_mcp.generation_feedback import review_generation_attempt
        position = self.position()
        if position.attempt_id is None or position.next_action == "stop":
            raise _blocked("No known fetched attempt is eligible for media evaluation.")
        return await review_generation_attempt(committer=self.committer, attempt_id=position.attempt_id,
            session=session, adjudicate=adjudicate, repair_evidence=repair_evidence,
            presentation_verifier=presentation_verifier, understand_audio=understand_audio)

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
    def cut_packet(self):
        from ai_video.canvas_review import canvas_cut_packet
        loaded, timeline = self.deliver()
        return canvas_cut_packet(loaded=loaded, timeline=timeline, direction=self.direction)

    @_input_errors
    def review_delivery(self, **arguments):
        from ai_video.canvas_review import review_canvas_delivery
        return review_canvas_delivery(service=self, **arguments)

    @_input_errors
    def handoff_reference(self, *, source_shot_id, target_occurrence_id, frame_index,
                          replace_asset_id, usage_license, checks, session, adjudicate, tool_identity):
        """Assess an intermediate state and bind the explicitly selected source.

        The target keeps its original prose and chip. The replacement and its
        accepted-source provenance are explicit; no last-frame assertion or
        semantic state verdict is manufactured.
        """
        from ai_video.canvas_handoff import prepare_canvas_state_reference, replace_state_reference
        from ai_video.production.registry import registry_semantic_sha256
        from ai_video.production.state_commit import prepare_project_registry_commit
        from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
        from dataclasses import replace
        loaded = self._load()
        row = next(r for r in self.direction["shots"] if r["occurrence_id"] == target_occurrence_id)
        supplied = {"source_shot_id": source_shot_id, "frame_index": frame_index,
                    "replace_asset_id": replace_asset_id, "checks": checks, "usage_license": usage_license}
        if row.get("state_reference") is None:
            raise _blocked("Intermediate handoff requires an approved state reference plan.")
        if "conditioning" in row["state_reference"]:
            supplied["conditioning"] = row["state_reference"]["conditioning"]
        if row["state_reference"] != supplied:
            raise _blocked("State reference differs from the approved selected scene reference plan.")
        registered = self._bound_state_reference(loaded, row)
        if registered is not None:
            return registered
        position = self.position()
        if (position.occurrence_id != target_occurrence_id
                or position.next_action not in {"prepare", "handoff_reference"}):
            raise _blocked("State reference handoff requires the current unsubmitted target.")
        selected = prepare_canvas_state_reference(loaded=loaded, source_shot_id=source_shot_id,
            frame_index=frame_index, usage_license=usage_license)
        revised = replace_state_reference(direction=self.direction, loaded=loaded,
            target_occurrence_id=target_occurrence_id, replace_asset_id=replace_asset_id,
            asset=selected.asset, source_shot_id=source_shot_id, frame_index=frame_index)
        from ai_video.canvas_handoff import assess_canvas_state_reference
        selected = assess_canvas_state_reference(loaded=loaded, selected=selected, checks=checks,
            session=session, adjudicate=adjudicate, tool_identity=tool_identity)
        revised = replace_state_reference(direction=self.direction, loaded=loaded,
            target_occurrence_id=target_occurrence_id, replace_asset_id=replace_asset_id,
            asset=selected.asset, source_shot_id=source_shot_id, frame_index=frame_index)
        existing = next((a for a in loaded.registry.assets if a.asset_id == selected.asset.asset_id), None)
        if existing is None:
            registry = loaded.registry.model_copy(update={"assets": tuple(sorted(
                (*loaded.registry.assets, selected.asset), key=lambda a: a.asset_id))})
            digest = registry_semantic_sha256(registry)
            registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
            request = prepare_project_registry_commit(manifest=loaded.manifest, project=loaded.project,
                registry=registry, attempt_id=f"canvas-state-register-{selected.asset.input_fingerprint}")
            request = replace(request, artifacts=tuple(sorted((*request.artifacts, *selected.artifacts),
                key=lambda a: a.relative_path.as_posix())))
            candidate = loaded.model_copy(update={"registry": registry})
            request = prepare_strategy_dependency_transition(base_loaded=loaded,
                candidate_loaded=candidate, request=request)
            self.committer.commit(request)
            loaded = self._load()
        elif existing != selected.asset:
            raise _blocked("State reference identity was reused with different inputs.")
        self.direction = revised
        self.revise_authoring(attempt_id=f"canvas-state-bind-{selected.asset.input_fingerprint}")
        return selected.asset

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
        matches = [a for a in self._attempts(loaded, shot_id)
                   if self.committer._reopen_video_request(a.video_generation_state.request)
                   == request]
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
