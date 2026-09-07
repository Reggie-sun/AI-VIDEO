"""Private explicit-config driver; import is side-effect free."""
from __future__ import annotations
import json
import argparse
import asyncio
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from dataclasses import dataclass, field
import base64
from ai_video.planning import VideoPlanningRequest, VideoGenerationPlan
from ai_video.planning.generation_feedback_context import require_feedback_context
from ai_video.production.generation_decision import DecisionPolicy, ExecutionLimits
from ai_video.production._shot_router_contracts import ShotRoutingContext, VideoRoutingPolicy, VideoGenerationLifecycleEnvelope
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.seedance_profile import SeedanceProviderProfile
from ai_video.production.seedance_asset import SeedanceAssetMaterializationReceipt, SeedanceAssetReferenceResolver
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator, RegisteredGenerationTarget
from ai_video.production.seedance import SeedanceVideoProvider, HttpxSeedanceTransport
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision, PaidProviderCallPreview
from ai_video.production.video import VideoTaskState, build_video_paid_permit_binding
from ai_video.production.video_generation import VideoGenerationService
from ai_video.production.hashing import canonical_sha256

@dataclass(frozen=True)
class DriverConfiguration:
    planning_request: VideoPlanningRequest
    video_plan: VideoGenerationPlan
    context: ShotRoutingContext
    routing_policy: VideoRoutingPolicy
    lifecycle: VideoGenerationLifecycleEnvelope
    decision_policy: DecisionPolicy
    limits: ExecutionLimits
    profile: SeedanceProviderProfile
    output: VideoFlexibleOutputRequirement
    reference_receipts: tuple[SeedanceAssetMaterializationReceipt, ...] = ()
    reference_confirmations: dict[str, bytes] = field(default_factory=dict)

    @classmethod
    def from_json(cls, raw: dict) -> "DriverConfiguration":
        if raw.get("schema_version") != "generation-feedback-driver/1":
            raise ValueError("unsupported generation feedback driver configuration")
        required = {"schema_version", "planning_request", "video_plan", "context", "routing_policy",
                    "lifecycle", "decision_policy", "execution_limits", "seedance_profile", "output_requirement"}
        if not required <= set(raw) or set(raw) - required - {"reference_receipts", "reference_confirmations_base64"}:
            raise ValueError("driver configuration has missing or unknown fields")
        return cls(
            VideoPlanningRequest.model_validate(raw["planning_request"]),
            VideoGenerationPlan.model_validate(raw["video_plan"]),
            ShotRoutingContext.model_validate(raw["context"]),
            VideoRoutingPolicy.model_validate(raw["routing_policy"]),
            VideoGenerationLifecycleEnvelope.model_validate(raw["lifecycle"]),
            DecisionPolicy.model_validate(raw["decision_policy"]),
            ExecutionLimits.model_validate(raw["execution_limits"]),
            SeedanceProviderProfile.model_validate(raw["seedance_profile"]),
            VideoFlexibleOutputRequirement.model_validate(raw["output_requirement"]),
            tuple(SeedanceAssetMaterializationReceipt.model_validate(x) for x in raw.get("reference_receipts", ())),
            {key: base64.b64decode(value, validate=True)
             for key, value in raw.get("reference_confirmations_base64", {}).items()},
        )

    def reference_resolver(self):
        return SeedanceAssetReferenceResolver(self.reference_receipts,
            provider_confirmation_evidence=self.reference_confirmations)

    def context_loader(self, loaded):
        return require_feedback_context(loaded=loaded, planning_request=self.planning_request,
            video_plan=self.video_plan, context=self.context, routing_policy=self.routing_policy,
            lifecycle=self.lifecycle)


def _forbidden(*_a, **_k): raise RuntimeError("offline preparation cannot use transport or credentials")

def load_configuration(path: str | Path) -> DriverConfiguration:
    return DriverConfiguration.from_json(json.loads(Path(path).read_text(encoding="utf-8")))

def prepare_configuration(*, project_root: str | Path, configuration: DriverConfiguration, provider=None):
    if provider is None:
        provider = SeedanceVideoProvider(profile=configuration.profile, transport=None, credential=_forbidden,
            input_reference=configuration.reference_resolver())
    if provider.capabilities().variants != tuple(item.variant for item in configuration.profile.capabilities):
        raise ValueError("registered provider capabilities differ from sealed configuration")
    target = RegisteredGenerationTarget(provider=provider, profile=configuration.profile.pointer(),
        compiler_contract=AdapterCompilerContract.create(compiler_id="seedance-video-compiler", compiler_version="2"),
        output_requirement=configuration.output)
    committer = ProductionStateCommitter(project_root)
    def current_context(loaded):
        current = configuration.context_loader(loaded)
        history = tuple(x for x in committer.read_generation_experiences()
                        if any(e.shot_id == configuration.context.target_shot_id for e in x.evidence))
        if history:
            identity = canonical_sha256({"task": configuration.limits.task_id,
                "shot": configuration.context.target_shot_id,
                "lifecycle": current["lifecycle"].model_dump(mode="json"),
                "evidence": [e.evidence_hash for x in history for e in x.evidence]})
            current["lifecycle"] = current["lifecycle"].model_copy(update={
                "generation_id": f"feedback-{identity[:32]}",
                "output_asset_id": f"feedback-output-{identity[:32]}"})
        return current
    prepared = GenerationFeedbackOrchestrator.for_project(committer=committer, targets=(target,),
        context_loader=current_context, policy=configuration.decision_policy).prepare(limits=configuration.limits)
    if prepared.resolved_request is not None:
        for binding in (*prepared.resolved_request.image_bindings, *prepared.resolved_request.media_bindings):
            configuration.reference_resolver()(binding)
    return prepared

def execute_prepared(*, project_root: str | Path, prepared, provider, paid_preview: PaidProviderCallPreview,
                     authorization: PaidProviderAuthorizationDecision, attempt_id: str, max_polls: int = 60,
                     reservation_id: str, poll_interval_seconds: float = 5):
    """Submit one freshly prepared decision; evaluation remains an injected owner."""
    if (getattr(prepared, "execution_binding", None) is None
            or getattr(prepared, "resolved_request", None) is None
            or getattr(prepared, "provider", None) is not provider):
        raise ValueError("execute requires the exact freshly prepared provider binding")
    if type(max_polls) is not int or not 1 <= max_polls <= 120 or not 0 <= poll_interval_seconds <= 30:
        raise ValueError("polling must be bounded")
    if attempt_id != paid_preview.attempt_id:
        raise ValueError("paid preview identifies another attempt")
    from ai_video.production.paid_provider import validate_paid_provider_authorization
    current_preview = provider.preview(prepared.resolved_request)
    build_video_paid_permit_binding(prepared.resolved_request, current_preview, paid_preview, authorization)
    validate_paid_provider_authorization(paid_preview, authorization, now=datetime.now(UTC))
    # Native payload preparation resolves every registered Ark reference before
    # any durable intent. This is pure for the explicit driver resolver.
    provider._payload(prepared.resolved_request)
    committer = ProductionStateCommitter(project_root,
        paid_provider_authorizer=lambda exact: authorization if exact == paid_preview else None)
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=attempt_id, request=prepared.resolved_request,
                  execution_binding=prepared.execution_binding)
    service.submit_once(attempt_id=attempt_id, paid_preview=paid_preview, reservation_id=reservation_id)
    for _ in range(max_polls):
        observation = service.refresh_once(attempt_id=attempt_id)
        if observation.state is VideoTaskState.SUCCEEDED:
            fetched = service.fetch_once(attempt_id=attempt_id)
            return {"attempt_id": attempt_id, "artifact_path": str(fetched.relative_path),
                    "evaluation_required": True}
        if observation.state is VideoTaskState.FAILED:
            from ai_video.production.generation_feedback import record_attempt_evaluation
            record_attempt_evaluation(committer=committer, attempt_id=attempt_id)
            return {"attempt_id": attempt_id, "runtime_failed": True}
        time.sleep(poll_interval_seconds)
    raise ValueError("bounded polling exhausted; do not retry automatically")


def _credential():
    result = subprocess.run(["secret-tool", "lookup", "application", "ai-video",
        "provider", "seedance", "credential", "ARK_API_KEY"], capture_output=True, timeout=8)
    if result.returncode or not result.stdout.strip():
        raise ValueError("credential supplier unavailable")
    return result.stdout.decode().strip()


async def evaluate_configuration(*, project_root, configuration, attempt_id, session, adjudicate,
                                 repair_evidence=False):
    from ai_video_mcp.generation_feedback import review_generation_attempt
    committer = ProductionStateCommitter(project_root)
    diagnosis = await review_generation_attempt(committer=committer, attempt_id=attempt_id,
        session=session, adjudicate=adjudicate, repair_evidence=repair_evidence)
    if diagnosis.all_required_observed_pass:
        return {"diagnosis": diagnosis.model_dump(mode="json"),
                "status": "required_observations_pass_activation_not_requested"}
    prepared = prepare_configuration(project_root=project_root, configuration=configuration)
    return {"diagnosis": diagnosis.model_dump(mode="json"),
            "next_decision": prepared.decision.model_dump(mode="json")}


def _run(argv=None, *, prepare_only=False):
    """Private run tooling, never the public ai-video CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root", required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--execute", action="store_true")
    action.add_argument("--evaluate", action="store_true")
    action.add_argument("--analyze", action="store_true")
    parser.add_argument("--attempt-id")
    parser.add_argument("--paid-preview")
    parser.add_argument("--authorization")
    parser.add_argument("--reservation-id")
    parser.add_argument("--sources")
    parser.add_argument("--mcp-python")
    parser.add_argument("--repair-evidence", action="store_true")
    args = parser.parse_args(argv)
    configuration = load_configuration(args.config)
    if prepare_only and (args.execute or args.evaluate or args.analyze):
        parser.error("preparation wrapper cannot execute or evaluate")
    if args.evaluate or args.analyze:
        if not all((args.attempt_id, args.mcp_python)) or (args.evaluate and not args.sources):
            parser.error("evaluation requires --attempt-id, --sources and --mcp-python")
        from ai_video.production.generation_evaluation import GenerationEvaluationSource
        from ai_video_mcp.generation_feedback import ProjectAnalysisSession
        session = ProjectAnalysisSession(args.mcp_python)
        if args.analyze:
            from ai_video_mcp.generation_feedback import review_generation_attempt
            review = asyncio.run(review_generation_attempt(committer=ProductionStateCommitter(args.project_root),
                attempt_id=args.attempt_id, session=session, adjudicate=None, analysis_only=True))
            result = {"status": "awaiting_selected_evaluator", **{
                name: getattr(review, name).model_dump(mode="json")
                for name in ("request", "projection", "recipe", "qa_policy", "analysis")}}
        else:
            def imported_evaluation(_review):
                # Bridge rejects documents not explicitly bound to exact raw analysis.
                return tuple(GenerationEvaluationSource.model_validate(x)
                             for x in json.loads(Path(args.sources).read_bytes()))
            result = asyncio.run(evaluate_configuration(project_root=args.project_root,
                configuration=configuration, attempt_id=args.attempt_id,
                session=session, adjudicate=imported_evaluation,
                repair_evidence=args.repair_evidence))
    else:
        prepared = prepare_configuration(project_root=args.project_root, configuration=configuration)
        result = {"decision": prepared.decision.model_dump(mode="json"),
                  "execution_binding": prepared.execution_binding.model_dump(mode="json")
                  if prepared.execution_binding else None}
        if args.execute:
            if not all((args.attempt_id, args.paid_preview, args.authorization, args.reservation_id)):
                parser.error("execution requires --attempt-id, --paid-preview, --authorization and --reservation-id")
            if prepared.execution_binding is None:
                print(json.dumps(result, ensure_ascii=False))
                return
            preview = PaidProviderCallPreview.model_validate_json(Path(args.paid_preview).read_bytes())
            authorization = PaidProviderAuthorizationDecision.model_validate_json(Path(args.authorization).read_bytes())
            if preview.secret_reference.kind != "secret_store" or preview.secret_reference.reference_id != "ARK_API_KEY":
                raise ValueError("unsupported credential reference for this Seedance driver")
            transport = HttpxSeedanceTransport(timeout_seconds=40)
            try:
                provider = SeedanceVideoProvider(profile=configuration.profile, transport=transport,
                    credential=_credential,
                    input_reference=configuration.reference_resolver())
                fresh = prepare_configuration(project_root=args.project_root,
                    configuration=configuration, provider=provider)
                result = execute_prepared(project_root=args.project_root, prepared=fresh, provider=provider,
                    paid_preview=preview, authorization=authorization, attempt_id=args.attempt_id,
                    reservation_id=args.reservation_id)
            finally:
                transport.close()
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main(argv=None, *, prepare_only=False):
    from ai_video.errors import AiVideoError
    try:
        return _run(argv, prepare_only=prepare_only)
    except (AiVideoError, ValueError, OSError, KeyError):
        print(json.dumps({"status": "blocked", "reason":
            "Current configuration, authorization, references or exact evaluation evidence is unavailable or invalid."}))
        return 2
