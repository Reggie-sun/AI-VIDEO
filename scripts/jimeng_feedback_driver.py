"""Explicit, single-submit Jimeng wiring over the canonical generation owners.

Import and preparation do not launch a browser. A live transport and the existing
paid-provider authorizer must be supplied separately for submission. This module
does not issue approval, retry, evaluate, activate, or declare media acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from ai_video.canvas_planning import canvas_feedback_context
from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
from ai_video.production.jimeng import JimengVideoProvider
from ai_video.production.jimeng_contracts import JimengProfile
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.project import load_production_project
from ai_video.production.shot_router import AdapterCompilerContract, VideoRoutingPolicy
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService


@dataclass(frozen=True)
class DriverConfiguration:
    row: dict
    routing_policy: VideoRoutingPolicy
    decision_policy: DecisionPolicy
    execution_limits: ExecutionLimits
    jimeng_profile: JimengProfile

    @classmethod
    def from_json(cls, raw: dict) -> "DriverConfiguration":
        fields = {"schema_version", "row", "routing_policy", "decision_policy",
                  "execution_limits", "jimeng_profile"}
        if not isinstance(raw, dict) or set(raw) != fields or raw["schema_version"] != "jimeng-feedback-driver/1":
            raise ValueError("unsupported Jimeng driver configuration fields or version")
        row = raw["row"]
        if not isinstance(row, dict) or not isinstance(row.get("shot"), dict) or not row["shot"].get("shot_id"):
            raise ValueError("driver requires a director row with an exact target Shot")
        if not isinstance(row.get("generation"), dict):
            raise ValueError("driver requires director generation input")
        result = cls(json.loads(json.dumps(row)),
            VideoRoutingPolicy.model_validate(raw["routing_policy"]),
            DecisionPolicy.model_validate(raw["decision_policy"]),
            ExecutionLimits.model_validate(raw["execution_limits"]),
            JimengProfile.model_validate(raw["jimeng_profile"]))
        limits, policy = result.execution_limits, result.decision_policy
        candidate = "jimeng/" + result.jimeng_profile.capability_id
        if (limits.allowed_remote_candidates != (candidate,) or limits.paid_submit_ceiling != 1
                or limits.paid_submits_used > 1 or policy.max_resamples != 0):
            raise ValueError("Jimeng driver requires one exact candidate, one paid submit and no resamples")
        return result


def load_configuration(path: str | Path) -> DriverConfiguration:
    return DriverConfiguration.from_json(json.loads(Path(path).read_text(encoding="utf-8")))


def registered_reference_resolver(project_root: Path):
    """Reopen selected Registry bytes, rejecting stale bindings before upload."""
    def resolve(binding):
        loaded = load_production_project(project_root / "project.yaml")
        asset = next((a for a in loaded.registry.assets if a.asset_id == binding.asset_id), None)
        if asset is None:
            raise ValueError("Jimeng reference is not in the selected Registry")
        payload = _read_regular_file_nofollow(
            loaded.asset_paths[asset.asset_id], contained_by=project_root).data
        if hashlib.sha256(payload).hexdigest() != binding.asset_sha256 or len(payload) != binding.size_bytes:
            raise ValueError("Jimeng reference bytes differ from the resolved binding")
        return payload
    return resolve


@dataclass(frozen=True)
class JimengRuntime:
    configuration: DriverConfiguration
    committer: ProductionStateCommitter
    provider: JimengVideoProvider
    orchestrator: GenerationFeedbackOrchestrator
    service: VideoGenerationService
    reference_resolver: object
    live_transport_supplied: bool

    def _request(self, prepared):
        if (getattr(prepared, "provider", None) is not self.provider
                or getattr(prepared, "resolved_request", None) is None
                or getattr(prepared, "execution_binding", None) is None):
            raise ValueError("operation requires this runtime's exact prepared provider binding")
        return prepared.resolved_request

    def prepare(self):
        prepared = self.orchestrator.prepare(limits=self.configuration.execution_limits)
        if prepared.resolved_request is not None:
            for binding in (*prepared.resolved_request.image_bindings, *prepared.resolved_request.media_bindings):
                self.reference_resolver(binding)
        return prepared

    def preview(self, prepared):
        request = self._request(prepared)
        return {"provider_preview": self.provider.preview(request),
                "egress_items": self.provider.egress_items(request)}

    def start(self, *, prepared, attempt_id):
        request = self._request(prepared)
        return self.service.start(attempt_id=attempt_id, request=request,
                                  execution_binding=prepared.execution_binding)

    def submit_once(self, *, attempt_id, paid_preview, reservation_id):
        if not self.live_transport_supplied:
            raise ValueError("submission requires an explicitly supplied live transport")
        return self.service.submit_once(attempt_id=attempt_id, paid_preview=paid_preview,
                                        reservation_id=reservation_id)

    def refresh_once(self, *, attempt_id):
        if not self.live_transport_supplied:
            raise ValueError("observation requires an explicitly supplied live transport")
        return self.service.refresh_once(attempt_id=attempt_id)

    def fetch_once(self, *, attempt_id):
        if not self.live_transport_supplied:
            raise ValueError("fetch requires an explicitly supplied live transport")
        return self.service.fetch_once(attempt_id=attempt_id)


def create_runtime(*, project_root: str | Path, configuration: DriverConfiguration,
                   transport=None, paid_provider_authorizer=None) -> JimengRuntime:
    """Wire existing owners; configuration is data, never paid authorization."""
    # Revalidate dataclass callers as strictly as file-based callers.
    configuration = DriverConfiguration.from_json({"schema_version": "jimeng-feedback-driver/1",
        "row": configuration.row,
        **{name: getattr(configuration, name).model_dump(mode="json") for name in
           ("routing_policy", "decision_policy", "execution_limits", "jimeng_profile")}})
    root = Path(project_root).resolve(strict=True)
    committer = ProductionStateCommitter(root, paid_provider_authorizer=paid_provider_authorizer)
    resolver = registered_reference_resolver(root)
    profile = configuration.jimeng_profile
    provider = JimengVideoProvider(profile=profile, transport=transport,
        reference_resolver=resolver, committer=committer)
    target = RegisteredGenerationTarget(provider=provider, profile=profile.pointer(),
        compiler_contract=AdapterCompilerContract.create(compiler_id=profile.compiler_id, compiler_version="1"),
        output_requirement=profile.output())
    orchestrator = GenerationFeedbackOrchestrator.for_project(committer=committer, targets=(target,),
        context_loader=lambda loaded: canvas_feedback_context(loaded=loaded,
            row=configuration.row, policy=configuration.routing_policy),
        policy=configuration.decision_policy)
    return JimengRuntime(configuration, committer, provider, orchestrator,
        VideoGenerationService(committer=committer, provider=provider), resolver, transport is not None)
