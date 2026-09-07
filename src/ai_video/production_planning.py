"""Application entry point connecting pure Planning to existing Product owners."""

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.planning.production_strategy import (
    ProductionCapabilities, ProductionStrategyPolicy, ProductionStrategyResolver,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.production_strategy_materialization import (
    build_strategy_composition, prepare_strategy_commit,
)


def _invalid(message):
    return AiVideoError(ErrorCode.PRODUCTION_PROJECT_INVALID, message)


class ProductionPlanningService:
    """No strategy store, automatic generation, activation or repair lifecycle."""

    def __init__(self, *, committer, targets=(), policy=None):
        self.committer = committer
        self.targets = tuple(targets)
        self.policy = policy or ProductionStrategyPolicy()

    def _load(self):
        return load_production_project(self.committer.project_root / "project.yaml")

    def _capabilities(self):
        # Adapter capabilities are immutable observations, never remote discovery.
        observations = tuple({
            "profile": t.profile.model_dump(mode="json"),
            "compiler": t.compiler_contract.model_dump(mode="json"),
            "output": t.output_requirement.model_dump(mode="json"),
            "capabilities": t.provider.capabilities().model_dump(mode="json"),
        } for t in self.targets)
        return ProductionCapabilities(generation_available=any(
            item["capabilities"]["variants"] for item in observations),
            generation_targets_hash=canonical_sha256({"targets": observations}))

    def _resolve(self, loaded, parent_shot_id):
        return ProductionStrategyResolver().resolve(loaded=loaded,
            parent_shot_id=parent_shot_id, policy=self.policy, capabilities=self._capabilities())

    def prepare(self, *, parent_shot_id):
        """Standard read, bounded candidate production, no state/media effects."""
        return self._resolve(self._load(), parent_shot_id)

    def reassess_generation(self, *, component_shot_id, prepared_generation):
        """Route generation's authoring exit back to the same approved intent."""
        if prepared_generation.decision.disposition not in {
            "SPLIT_SHOT", "REASSESS_FEASIBILITY", "CHANGE_GENERATION_STRATEGY", "CAPABILITY_BOUNDARY",
        }:
            raise _invalid("Generation result has no production-strategy reassessment exit.")
        if prepared_generation.target_shot_id != component_shot_id:
            raise _invalid("Generation reassessment targets another component.")
        return self.prepare(parent_shot_id=component_shot_id)

    def materialize(self, *, decision, attempt_id):
        """Recompute immediately before the sole canonical author's transaction."""
        loaded = self._load()
        current = self._resolve(loaded, decision.parent_shot_id)
        if current != decision or current.selected is None:
            raise _invalid("Production strategy is stale or has no selected candidate.")
        from ai_video.production.production_strategy_reader import production_parent_context

        parent, _, _, _ = production_parent_context(loaded, decision.parent_shot_id)
        family = {parent.shot_id, *(u.shot_id for c in parent.production_intent.coverage_options for u in c.units)}
        for attempt in loaded.manifest.attempts:
            state = attempt.video_generation_state
            if state is None:
                continue
            request = self.committer._reopen_video_request(state.request)
            scope = request.activation_scope
            if scope is None or scope.request.target_shot_id not in family:
                continue
            if attempt.status.value in {"outcome_unknown", "interrupted"}:
                raise _invalid("Production family requires explicit generation recovery.")
            fetch = state.local_fetch_receipt or state.fetch_receipt
            experiences = tuple(self.committer._reopen_generation_experience(p)
                                for p in state.generation_experiences)
            if fetch is not None and not any(e.outcome == "media" and
                    e.artifact_sha256 == fetch.artifact_sha256 for x in experiences for e in x.evidence):
                raise _invalid("Production family needs exact media evaluation before reallocation.")
            if fetch is None and attempt.status.value == "running" and state.phase.value != "request":
                raise _invalid("Production family has an unfinished generation attempt.")
        request = prepare_strategy_commit(loaded=loaded, decision=current, attempt_id=attempt_id)
        return self.committer.commit(request)

    def composition(self, *, decision, renderer_version, composition_id="production-strategy"):
        """Build from reopened selected components; the existing timeline resolves it."""
        from ai_video.production.composition import resolve_composition

        loaded = self._load()
        spec = build_strategy_composition(loaded=loaded, decision=decision,
                                          composition_id=composition_id)
        return spec, resolve_composition(loaded, spec, renderer_version)

    def prepare_generation(self, *, component_shot_id, context_loader, limits, generation_policy):
        """Only a selected missing dynamic component reaches Generation Orchestrator."""
        from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator

        loaded = self._load()
        shot = next((s for s in loaded.shots if s.shot_id == component_shot_id), None)
        if (shot is None or shot.production_lineage is None
                or shot.production_lineage.source is not None
                or any(r.asset_ids for r in shot.required_asset_roles if r.role == "primary_visual")):
            raise _invalid("Only an unresolved selected generation component can be generated.")
        if limits.task_id != shot.production_lineage.task_id:
            raise _invalid("Generation must retain the production task identity.")
        current_strategy = self._resolve(loaded, component_shot_id)
        selected = current_strategy.selected
        selected_unit = next((u for u in selected.units
            if u.component.shot_id == component_shot_id), None) if selected else None
        if (selected_unit is None or selected_unit.source is not None
                or selected.coverage.coverage_id != shot.production_lineage.coverage_id
                or selected.allocation_hash != shot.production_lineage.allocation_hash):
            raise _invalid("Production inputs changed; reassess and materialize the current strategy first.")

        def selected_context(current):
            result = context_loader(current, component_shot_id)
            if result["context"].target_shot_id != component_shot_id:
                raise _invalid("Generation projection targets another production component.")
            return result

        return GenerationFeedbackOrchestrator.for_project(committer=self.committer,
            targets=self.targets, context_loader=selected_context,
            policy=generation_policy).prepare(limits=limits)
