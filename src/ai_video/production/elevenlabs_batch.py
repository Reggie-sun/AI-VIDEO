"""Bounded development speech tests through the existing Production committer."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import unicodedata
from typing import Callable, Literal

from pydantic import ConfigDict, Field, field_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioProbeToolchain, VoiceCallAuthorization, VoiceGenerationRequest,
    VoicePricingSnapshot, VoiceProviderParameters,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.elevenlabs import (
    ElevenLabsVoiceProvider, ElevenLabsProviderPolicy, ElevenLabsTransport,
)
from ai_video.production.models import ActorIdentity, AudioKind, StateCommitStatus, StrictModel
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision, PaidProviderCallPreview,
    PaidProviderEgressItem, SecretReference,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.voice_candidate import make_voice_candidate_preparer
from ai_video.production.minimax_speech_batch import (
    prepare_minimax_speech_test_project, _prepare_test_graph, _prepare_test_transition,
)


class ElevenLabsSpeechTestBatch(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    batch_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,70}$")
    scripts: tuple[str, ...] = Field(min_length=1, max_length=1000)
    source_reference: str = Field(min_length=1)
    voice_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$")
    model_id: Literal["eleven_multilingual_v2"] = "eleven_multilingual_v2"
    language: Literal["zh", "en"] = "zh"
    speaker_id: str = "narrator"
    unit_price_microunits: int = Field(strict=True, gt=0)
    per_call_ceiling_microunits: int = Field(strict=True, gt=0)
    project_ceiling_microunits: int = Field(strict=True, gt=0)
    parameters: VoiceProviderParameters = Field(default_factory=lambda: VoiceProviderParameters(
        stability_milli=500, similarity_boost_milli=750, style_milli=0,
        speed_milli=1000, use_speaker_boost=True))

    @field_validator("scripts")
    @classmethod
    def _scripts_are_exact(cls, values):
        if any(not text or len(text) >= 10000 or unicodedata.normalize("NFC", text) != text
               for text in values):
            raise ValueError("Speech scripts must be nonempty NFC text under 10000 characters")
        return values

    @property
    def policy_id(self) -> str:
        return "elevenlabs-batch-" + canonical_sha256(self)


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(code=ErrorCode.VOICE_REQUEST_INVALID,
                        user_message=message, retryable=False)


def run_elevenlabs_speech_batch(
    root: Path, batch: ElevenLabsSpeechTestBatch, *,
    transport: ElevenLabsTransport, credential: object,
    toolchain: AudioProbeToolchain,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> tuple[Path, ...]:
    """Stop on the first failure/unknown; completed exact calls reopen without effects.

    Exact scripts and explicit operator monetary ceilings are sealed before submit.
    Every call has its own durable Gate; unknown outcomes require explicit recovery.
    """
    prepare_minimax_speech_test_project(root, batch, title="ElevenLabs Speech test")
    root = Path(root).resolve(strict=True)
    _prepare_test_graph(root)
    policy = ElevenLabsProviderPolicy(
        provider_enabled=True, enable_logging=True, zero_retention_entitled=False,
        credential_reference_kind="secret_store", credential_reference_id="ELEVENLABS_API_KEY",
        license_policy_decision="operator-authorized-voice-test", license_allowed=True,
        use_policy_allowed=True, voice_authorization_verified=True, policy_receipt_id=batch.policy_id)
    pricing = VoicePricingSnapshot(snapshot_id=batch.policy_id, effective_date=clock().date(),
        currency="USD", pricing_unit="character", unit_price_microunits=batch.unit_price_microunits,
        minimum_billable_units=1)
    provider = ElevenLabsVoiceProvider(transport=transport, pricing=pricing,
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
            provider_kind="elevenlabs", model_id=batch.model_id, audio_kind=AudioKind.DIALOGUE,
            script_text=text, speaker_id=batch.speaker_id, voice_id=batch.voice_id,
            language=batch.language, output_container="wav", output_codec="pcm_s16le",
            output_sample_rate_hz=48000, output_channels=1,
            provider_parameters=batch.parameters,
            base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
            input_artifact_ids=(loaded.brief.artifact_id,), input_fingerprint=loaded.brief.content_hash,
            pricing_snapshot_id=batch.policy_id, budget_reservation_receipt_id=f"paid-{attempt_id}",
            egress_authorization_receipt_id=batch.policy_id)
        preview = provider.preview(request)
        authorization = VoiceCallAuthorization.create(
            request_fingerprint=request.voice_request_fingerprint, preview_fingerprint=preview.preview_fingerprint,
            pricing_snapshot_id=batch.policy_id, budget_reservation_receipt_id=request.budget_reservation_receipt_id,
            egress_authorization_receipt_id=batch.policy_id, destination=preview.destination,
            payload_categories=preview.payload_categories, cost_ceiling_microunits=batch.per_call_ceiling_microunits, provider_enabled=True)
        paid = PaidProviderCallPreview.create(
            attempt_id=attempt_id, operation="voice_generation", provider_kind=request.provider_kind,
            model_id=request.model_id, request_fingerprint=request.voice_request_fingerprint,
            billing_mode="remote_metered", currency=preview.currency,
            estimated_cost_upper_bound_microunits=preview.estimated_cost_upper_bound_microunits, destination=preview.destination, method="POST",
            egress_items=(PaidProviderEgressItem(item_id="script", sha256=request.script_hash,
                size_bytes=len(text.encode("utf-8")), mime_type="text/plain", purpose="script"),),
            retention_mode="provider_standard", provider_policy_snapshot_id=batch.policy_id,
            secret_reference=SecretReference(kind="secret_store", reference_id=policy.credential_reference_id))

        def authorize(exact):
            if exact != paid:
                return None
            now = clock()
            return PaidProviderAuthorizationDecision.create(
                attempt_id=attempt_id, preview_fingerprint=paid.preview_fingerprint, explicit_opt_in=True,
                actor=ActorIdentity(actor_id="elevenlabs-speech-test", actor_kind="codex"),
                opt_in_policy_receipt_id=batch.policy_id, budget_policy_id=batch.policy_id,
                budget_currency=paid.currency, project_budget_ceiling_microunits=batch.project_ceiling_microunits,
                per_call_ceiling_microunits=batch.per_call_ceiling_microunits,
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
