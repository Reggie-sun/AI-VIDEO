"""Bounded development speech tests through the existing Production committer."""
from __future__ import annotations

import hashlib
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unicodedata
from typing import Callable, Literal

import yaml
from pydantic import ConfigDict, Field, field_validator, model_serializer

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioProbeToolchain, VoiceCallAuthorization, VoiceGenerationRequest,
    VoicePricingSnapshot, VoiceProviderParameters,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.minimax_speech import (
    MiniMaxSpeechVoiceProvider, MiniMaxSpeechProviderPolicy,
    MiniMaxSpeechCredential, MiniMaxSpeechTransport,
)
from ai_video.production.models import (
    ActorIdentity, ArtifactReference, AssetRegistrySnapshot, AudioKind,
    AssetRecord, AssetRoleRequirement, AssetSourceKind, AssetType, ToolIdentity,
    DeliveryProfile, DurationPolicy, ProductionBrief, ProductionProject,
    ProjectArtifactRefs, RendererPolicy, Scene, Shot, SourceReference,
    StateCommitStatus, Story, StoryBeat, Storyboard, StoryboardBeat, StrictModel,
    VisualStrategy,
)
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision, PaidProviderCallPreview,
    PaidProviderEgressItem, SecretReference,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from ai_video.production.voice_candidate import make_voice_candidate_preparer
from ai_video.production._dependency_authoring import (
    build_authoring_dependency_projection, build_authoring_project_evidence_states,
)
from ai_video.production.dependency import build_dependency_graph, desired_fingerprints
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
from ai_video.production.state_commit import prepare_dependency_graph_transition


class MiniMaxSpeechTestBatch(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    batch_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,70}$")
    scripts: tuple[str, ...] = Field(min_length=1, max_length=1000)
    source_reference: str = Field(min_length=1)
    model_id: Literal["speech-2.8-hd", "speech-2.8-turbo"] = "speech-2.8-hd"
    voice_id: str = "male-qn-jingying"
    speaker_id: str = "P2"
    language: Literal["Chinese", "English"] = "Chinese"
    sample_rate_hz: Literal[8000, 16000, 22050, 24000, 32000, 44100] = 44100
    speed_milli: int = Field(default=1000, strict=True, ge=700, le=1200)
    region: Literal["cn"] | None = None

    @model_serializer(mode="wrap")
    def _preserve_legacy_batch(self, handler):
        data = handler(self)
        if self.region is None:
            data.pop("region", None)
        return data

    @property
    def credential_reference_id(self) -> str:
        return "MINIMAX_SPEECH_CN_API_KEY" if self.region == "cn" else "MINIMAX_SPEECH_API_KEY"

    @field_validator("scripts")
    @classmethod
    def _scripts_are_exact(cls, values):
        if any(not text or len(text) >= 10_000 or unicodedata.normalize("NFC", text) != text
               for text in values):
            raise ValueError("Speech scripts must be nonempty NFC text under 10000 characters")
        return values

    @property
    def policy_id(self) -> str:
        return "speech-batch-" + canonical_sha256(self)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(code=ErrorCode.VOICE_REQUEST_INVALID,
                        user_message=message, retryable=False)


def prepare_minimax_speech_test_project(root: Path, batch: MiniMaxSpeechTestBatch) -> None:
    """Create an independent, provenance-bound audio experiment, never copy a ledger."""
    root = Path(root).resolve()
    if (root / "project.yaml").exists():
        loaded = load_production_project(root / "project.yaml")
        if (loaded.project.project_id != batch.batch_id
                or loaded.brief.objective != batch.model_dump_json()):
            raise _invalid("Existing speech project does not match the exact batch.")
        return
    if root.exists() and any(root.iterdir()):
        raise _invalid("Speech test bootstrap requires an empty destination.")
    provenance = (SourceReference(kind="user_input", reference=batch.source_reference),)

    def artifact(cls, name, **values):
        return seal_artifact(cls(artifact_id=f"{batch.batch_id}-{name}", revision=1,
                                 content_hash="0" * 64, creation_receipt_id=batch.policy_id,
                                 source_provenance=provenance, **values))

    brief = artifact(ProductionBrief, "brief", title="MiniMax Speech test",
                     objective=batch.model_dump_json(), audience="Development",
                     format="Standalone WAV test", language=batch.language,
                     constraints=("No source project recovery or video acceptance",))
    story = artifact(Story, "story", language=batch.language, logline="Speech test",
                     synopsis="Independent dialogue evaluation",
                     beats=(StoryBeat(beat_id="test", summary="Evaluate generated speech"),))
    scene = artifact(Scene, "scene", scene_id="test", location="Audio test",
                     time="Unspecified", mood="Unspecified")
    shot = artifact(Shot, "shot", shot_id="test", scene_id="test", storyboard_beat_id="test",
                    intent="Audio-only development test; no visual generation",
                    duration_policy=DurationPolicy(mode="fixed", seconds=3),
                    visual_strategy=VisualStrategy.STATIC_IMAGE,
                    required_asset_roles=(AssetRoleRequirement(role="test_canvas",
                        asset_ids=("test-canvas",), allowed_asset_types=(AssetType.IMAGE,)),))
    storyboard = artifact(Storyboard, "storyboard", beats=(StoryboardBeat(
        beat_id="test", scene_id="test", shot_ids=("test",), narrative_intent="Speech test"),))
    prepared = []

    def ref(value):
        path = Path("creative") / f"{value.artifact_id}.yaml"
        payload = yaml.safe_dump(value.model_dump(mode="json"), allow_unicode=True,
                                 sort_keys=True).encode()
        prepared.append(PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest()))
        return ArtifactReference(artifact_id=value.artifact_id, revision=1,
                                 content_hash=value.content_hash, path=path)

    refs = ProjectArtifactRefs(brief=ref(brief), story=ref(story), characters=(),
                               scenes=(ref(scene),), shots=(ref(shot),), storyboard=ref(storyboard))
    project = artifact(ProductionProject, "project", project_id=batch.batch_id,
                       title="Independent MiniMax Speech test", default_language=batch.language,
                       delivery_profile=DeliveryProfile(width=1280, height=720, fps=24),
                       renderer_policy=RendererPolicy(), artifacts=refs)
    # A fixed one-pixel canvas satisfies the existing Project visual contract;
    # this experiment never renders it or claims a source-video revision.
    canvas = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")
    canvas_hash = hashlib.sha256(canvas).hexdigest()
    canvas_path = Path("assets/files") / f"{canvas_hash}.png"
    prepared.append(PreparedArtifact(canvas_path, canvas, canvas_hash))
    canvas_record = AssetRecord(asset_id="test-canvas", asset_type=AssetType.IMAGE,
        artifact_path=canvas_path, sha256=canvas_hash, size_bytes=len(canvas), mime_type="image/png",
        width=1, height=1, source_kind=AssetSourceKind.DERIVED,
        tool=ToolIdentity(name="speech-test-canvas", version="1"),
        input_artifact_ids=(brief.artifact_id,), input_fingerprint=brief.content_hash,
        creation_receipt_id=batch.policy_id, usage_license="project-authored-test-canvas")
    registry = AssetRegistrySnapshot(schema_version="2.0", revision_id="0" * 64,
                                     content_hash="0" * 64, assets=(canvas_record,))
    digest = registry_semantic_sha256(registry)
    registry = registry.model_copy(update={"revision_id": digest, "content_hash": digest})
    root.mkdir(parents=True, exist_ok=True)
    ProductionStateCommitter(root).bootstrap_initial_state(
        attempt_id=f"{batch.batch_id}-bootstrap", project=project,
        registry=registry, artifacts=tuple(prepared))


def _prepare_test_graph(root):
    loaded = load_production_project(root / "project.yaml")
    if loaded.dependency_graph is not None:
        return
    # This standalone test has no composition/render consumers. Use the existing
    # authoring projection; registered WAV provenance is verified by the voice reader.
    projection = build_authoring_dependency_projection(loaded)
    graph = build_dependency_graph(projection.nodes, projection.edges)
    desired = desired_fingerprints(graph)
    states = build_authoring_project_evidence_states(graph=graph, projection=projection,
        project_pointer=loaded.manifest.active_project, desired=desired)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=loaded.manifest.manifest_revision,
        base_dependency_graph=None, candidate_graph=graph,
        candidate_dependency_states=states, expected_desired_fingerprints=desired)
    ProductionStateCommitter(root).bootstrap_dependency_graph(
        attempt_id=f"{loaded.project.project_id}-graph", graph=graph,
        transition=transition, expected_desired_fingerprints=desired)


def _prepare_test_transition(root, request):
    base = load_production_project(root / "project.yaml")
    artifacts = {a.relative_path: a for a in request.artifacts}
    project = ProductionProject.model_validate(yaml.safe_load(artifacts[request.next_project.path].payload))
    registry = AssetRegistrySnapshot.model_validate_json(artifacts[request.next_registry.path].payload)
    candidate = base.model_copy(update={"project": project, "registry": registry})
    return prepare_strategy_dependency_transition(
        base_loaded=base, candidate_loaded=candidate, request=request)


def run_minimax_speech_batch(
    root: Path, batch: MiniMaxSpeechTestBatch, *,
    transport: MiniMaxSpeechTransport, credential: MiniMaxSpeechCredential,
    toolchain: AudioProbeToolchain,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> tuple[Path, ...]:
    """Stop on the first failure/unknown; completed exact calls reopen without effects.

    Batch length is the finite durable ceiling. No user monetary configuration or
    interactive authorizer is involved; every call still has its own sealed Gate.
    """
    prepare_minimax_speech_test_project(root, batch)
    root = Path(root).resolve(strict=True)
    _prepare_test_graph(root)
    policy = MiniMaxSpeechProviderPolicy(
        provider_enabled=True, credential_reference_kind="secret_store",
        credential_reference_id=batch.credential_reference_id, retention_mode="provider_standard",
        license_policy_decision="system-voice-development-test", license_allowed=True,
        use_policy_allowed=True, voice_authorization_verified=True, policy_receipt_id=batch.policy_id,
        origin="https://api.minimaxi.com" if batch.region == "cn" else "https://api.minimax.io")
    pricing = VoicePricingSnapshot(snapshot_id=batch.policy_id, effective_date=clock().date(),
                                   currency="CNY" if batch.region == "cn" else "USD", pricing_unit="character",
                                   unit_price_microunits=None, minimum_billable_units=1)
    provider = MiniMaxSpeechVoiceProvider(transport=transport, pricing=pricing,
                                         api_key=credential, policy=policy)
    outputs = []
    for index, text in enumerate(batch.scripts, 1):
        loaded = load_production_project(root / "project.yaml")
        attempt_id = f"{batch.batch_id}-{index}"
        existing = next((a for a in loaded.manifest.attempts if a.attempt_id == attempt_id), None)
        if existing is not None:
            if existing.status is not StateCommitStatus.SUCCEEDED:
                raise _invalid("Speech batch attempt is not completed; explicit recovery is required.")
            outputs.append(loaded.asset_paths[f"voice-{attempt_id}"])
            continue
        request = VoiceGenerationRequest.create(
            request_id=f"request-{attempt_id}", attempt_id=attempt_id,
            provider_kind="minimax-speech", model_id=batch.model_id, audio_kind=AudioKind.DIALOGUE,
            script_text=text, speaker_id=batch.speaker_id, voice_id=batch.voice_id,
            language=batch.language, output_container="wav", output_codec="pcm_s16le",
            output_sample_rate_hz=batch.sample_rate_hz, output_channels=1,
            provider_parameters=VoiceProviderParameters(speed_milli=batch.speed_milli),
            base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
            input_artifact_ids=(loaded.brief.artifact_id,), input_fingerprint=loaded.brief.content_hash,
            pricing_snapshot_id=batch.policy_id, budget_reservation_receipt_id=f"paid-{attempt_id}",
            egress_authorization_receipt_id=batch.policy_id)
        preview = provider.preview(request)
        authorization = VoiceCallAuthorization.create(
            request_fingerprint=request.voice_request_fingerprint, preview_fingerprint=preview.preview_fingerprint,
            pricing_snapshot_id=batch.policy_id, budget_reservation_receipt_id=request.budget_reservation_receipt_id,
            egress_authorization_receipt_id=batch.policy_id, destination=preview.destination,
            payload_categories=preview.payload_categories, cost_ceiling_microunits=None, provider_enabled=True)
        paid = PaidProviderCallPreview.create(
            attempt_id=attempt_id, operation="voice_generation", provider_kind=request.provider_kind,
            model_id=request.model_id, request_fingerprint=request.voice_request_fingerprint,
            billing_mode="minimax_speech_batch", currency=preview.currency,
            estimated_cost_upper_bound_microunits=None, destination=preview.destination, method="POST",
            egress_items=(PaidProviderEgressItem(item_id="script", sha256=request.script_hash,
                size_bytes=len(text.encode("utf-8")), mime_type="text/plain", purpose="script"),),
            retention_mode=policy.retention_mode, provider_policy_snapshot_id=batch.policy_id,
            secret_reference=SecretReference(kind="secret_store", reference_id=policy.credential_reference_id))

        def authorize(exact):
            if exact != paid:
                return None
            now = clock()
            return PaidProviderAuthorizationDecision.create(
                attempt_id=attempt_id, preview_fingerprint=paid.preview_fingerprint, explicit_opt_in=True,
                actor=ActorIdentity(actor_id="minimax-speech-test", actor_kind="codex"),
                opt_in_policy_receipt_id=batch.policy_id, budget_policy_id=batch.policy_id,
                budget_currency=paid.currency, project_budget_ceiling_microunits=None,
                per_call_ceiling_microunits=None, voice_batch_submit_limit=len(batch.scripts),
                egress_authorized=True, egress_policy_receipt_id=batch.policy_id,
                live_test_authorized=True, live_authorization_receipt_id=batch.policy_id,
                issued_at=now, expires_at=now + timedelta(minutes=10), max_submit_count=1)

        committer = ProductionStateCommitter(
            root, paid_provider_authorizer=authorize, paid_provider_clock=clock,
            voice_candidate_preparer=make_voice_candidate_preparer(root, toolchain))
        committer.generate_voice_asset(request, provider, authorization, paid_preview=paid,
            dependency_transition_preparer=lambda candidate: _prepare_test_transition(root, candidate))
        reopened = load_production_project(root / "project.yaml")
        outputs.append(reopened.asset_paths[f"voice-{attempt_id}"])
    return tuple(outputs)
