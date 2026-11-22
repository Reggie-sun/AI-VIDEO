"""Select exact replica takes and submit them through the existing MiniMax voice owner."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib import import_module
import json
from pathlib import Path
import re
from typing import Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production._paid_provider_project_reader import load_paid_provider_budget
from ai_video.production.audio import (
    VoiceCallAuthorization,
    VoiceGenerationRequest,
    VoiceProviderParameters,
    validate_voice_call_authorization,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.minimax_speech import MiniMaxSpeechVoiceProvider
from ai_video.production.minimax_speech_batch import (
    prepare_standalone_voice_graph,
    prepare_standalone_voice_project,
    prepare_standalone_voice_transition,
)
from ai_video.production.models import AudioKind, StateCommitStatus
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    PaidProviderEgressItem,
    SecretReference,
    reserve_paid_provider_budget,
    validate_paid_provider_authorization,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.voice_candidate import make_voice_candidate_preparer
from scripts.minimax_speech_batch import minimax_speech_capabilities

from ._local import cli, read_json, tool_path
from .voice_operator import VoiceOperator


_WORKSPACE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,39}")


class VoiceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    region: Literal["cn", "international"]
    voice_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$")
    model_id: Literal["speech-2.8-hd", "speech-2.8-turbo"] = "speech-2.8-hd"
    language: Literal["Chinese", "English"] = "Chinese"
    speed_milli: int = Field(default=1000, ge=700, le=1200)
    sample_rate_hz: Literal[8000, 16000, 22050, 24000, 32000, 44100] = 44100

    @property
    def origin(self) -> str:
        return "https://api.minimaxi.com" if self.region == "cn" else "https://api.minimax.io"

    @property
    def credential_reference(self) -> str:
        return "MINIMAX_SPEECH_CN_API_KEY" if self.region == "cn" else "MINIMAX_SPEECH_API_KEY"


def _error(message: str, code: ErrorCode = ErrorCode.VOICE_REQUEST_INVALID) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


def voice_settings(cfg: dict) -> VoiceSettings:
    try:
        return VoiceSettings.model_validate(cfg["voice"])
    except (ValidationError, KeyError, TypeError):
        raise _error("Expected explicit MiniMax voice settings.") from None


def selected_groups(cfg: dict, only=()) -> list[dict]:
    groups = cfg.get("groups") if isinstance(cfg, dict) else None
    if not isinstance(groups, list) or not groups:
        raise _error("Expected a nonempty voice group list.")
    seen = set()
    for group in groups:
        gid = group.get("id") if isinstance(group, dict) else None
        if not isinstance(gid, str) or not _WORKSPACE_ID.fullmatch(gid) or gid in seen:
            raise _error("Voice group IDs must be safe and unique.")
        say = group.get("say")
        if not isinstance(say, str) or not say.strip() or len(say) >= 10_000 or unicodedata.normalize("NFC", say) != say:
            raise _error("Each voice group must have nonempty NFC spoken text under 10000 characters.")
        seen.add(gid)
    requested = set(only)
    if requested - seen:
        raise _error("Some requested voice group IDs are absent from the plan.")
    return [group for group in groups if not requested or group["id"] in requested]


def fingerprint(group: dict, cfg: dict) -> str:
    return canonical_sha256({
        "provider": "minimax-speech",
        "settings": voice_settings(cfg).model_dump(mode="json"),
        "say": group["say"],
    })


def take_name(group: dict, cfg: dict) -> str:
    group_id = group.get("id")
    if not isinstance(group_id, str) or not _WORKSPACE_ID.fullmatch(group_id):
        raise _error("A safe voice group ID is required.")
    return f"{group_id}-{fingerprint(group, cfg)}"


def _project_id(cfg: dict) -> str:
    episode_id = cfg.get("episode_id")
    if not isinstance(episode_id, str) or not _WORKSPACE_ID.fullmatch(episode_id):
        raise _error("An explicit, stable episode_id is required.")
    return f"replica-voice-{episode_id}"


def voice_root(vo_dir: Path) -> Path:
    directory = Path(vo_dir).absolute()
    root = directory / "voice-state"
    if root.resolve() != root or (root / "project.yaml").is_symlink():
        raise _error("The voice state path must be a direct, nonsymlink workspace path.")
    for ancestor in (directory, *directory.parents):
        if (ancestor / "project.yaml").exists() or (ancestor / "state/manifest.json").exists():
            raise _error("Replica voice state requires its own workspace outside Production projects.")
    return root


def load_voice_project(vo_dir: Path, cfg: dict):
    root = voice_root(vo_dir)
    project_id = _project_id(cfg)
    loaded = load_production_project(root / "project.yaml")
    if loaded.project.project_id != project_id or loaded.brief.objective != project_id:
        raise _error("The voice state belongs to a different episode.")
    return loaded


def current_artifact(loaded, group: dict, cfg: dict) -> Path | None:
    attempt_id = take_name(group, cfg)
    for attempt in loaded.manifest.attempts:
        if attempt.attempt_id != attempt_id:
            continue
        if attempt.status is StateCommitStatus.OUTCOME_UNKNOWN:
            raise _error("This take has an unknown submit outcome. Recover its existing attempt.",
                         ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN)
        if attempt.status is not StateCommitStatus.SUCCEEDED:
            raise _error("This take is pending or failed. Recover its existing attempt.",
                         ErrorCode.VOICE_PROVIDER_FAILED)
        settings = voice_settings(cfg)
        receipt = attempt.voice_request
        script_hash = hashlib.sha256(group["say"].encode()).hexdigest()
        if receipt is None or (
            receipt.script_hash, receipt.model_id, receipt.voice_id, receipt.language, receipt.destination
        ) != (script_hash, settings.model_id, settings.voice_id, settings.language, settings.origin):
            raise _error("The completed attempt does not match the selected voice take.")
        path = loaded.asset_paths.get(f"voice-{attempt_id}")
        if path is None or not path.is_file():
            raise _error("The successful take's canonical WAV is missing. Recover the WAV.",
                         ErrorCode.AUDIO_ASSET_INVALID)
        return path
    return None


def _validate_operator(operator, settings):
    if not isinstance(operator, VoiceOperator):
        raise _error("A trusted voice operator is required.", ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
    policy = operator.policy
    pricing = operator.pricing
    if not (
        policy.provider_enabled and policy.license_allowed and policy.use_policy_allowed
        and policy.voice_authorization_verified and policy.origin == settings.origin
        and policy.credential_reference_kind == "secret_store"
        and policy.credential_reference_id == settings.credential_reference
        and policy.license_policy_decision != "system-voice-development-test"
        and operator.egress_receipt_id and callable(operator.authorize)
    ):
        raise _error("MiniMax voice use, origin, credential or egress policy is incomplete.",
                     ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED)
    expected_currency = "CNY" if settings.region == "cn" else "USD"
    if not pricing.unit_price_microunits or pricing.currency != expected_currency:
        raise _error("An operator monetary ceiling matching the region is required.", ErrorCode.VOICE_BUDGET_REJECTED)


def _voice_request(loaded, group, cfg, settings, operator):
    attempt_id = take_name(group, cfg)
    return VoiceGenerationRequest.create(
        request_id=f"request-{attempt_id}", attempt_id=attempt_id,
        provider_kind="minimax-speech", model_id=settings.model_id, audio_kind=AudioKind.NARRATION,
        script_text=group["say"], speaker_id="narrator", voice_id=settings.voice_id,
        language=settings.language, output_container="wav", output_codec="pcm_s16le",
        output_sample_rate_hz=settings.sample_rate_hz, output_channels=1,
        provider_parameters=VoiceProviderParameters(speed_milli=settings.speed_milli),
        base_project=loaded.manifest.active_project, base_registry=loaded.manifest.active_registry,
        input_artifact_ids=(loaded.brief.artifact_id,), input_fingerprint=loaded.brief.content_hash,
        pricing_snapshot_id=operator.pricing.snapshot_id,
        budget_reservation_receipt_id=f"paid-{attempt_id}",
        egress_authorization_receipt_id=operator.egress_receipt_id,
    )


def _paid_preview(request, preview, policy) -> PaidProviderCallPreview:
    payload = request.synthesis_text.encode()
    return PaidProviderCallPreview.create(
        attempt_id=request.attempt_id, operation="voice_generation", provider_kind=request.provider_kind,
        model_id=request.model_id, request_fingerprint=request.voice_request_fingerprint,
        billing_mode="remote_metered", currency=preview.currency,
        estimated_cost_upper_bound_microunits=preview.estimated_cost_upper_bound_microunits,
        destination=preview.destination, method="POST",
        egress_items=(PaidProviderEgressItem(
            item_id="script", sha256=hashlib.sha256(payload).hexdigest(), size_bytes=len(payload),
            mime_type="text/plain", purpose="script",
        ),),
        retention_mode=policy.retention_mode, provider_policy_snapshot_id=policy.policy_receipt_id,
        secret_reference=SecretReference(kind="secret_store", reference_id=policy.credential_reference_id),
    )


def _authorize(operator, paid, approved_digest, clock):
    try:
        decision = operator.authorize(paid, approved_digest)
    except Exception:
        raise _error("The trusted operator could not authorize this exact voice request.",
                     ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED) from None
    if not isinstance(decision, PaidProviderAuthorizationDecision):
        raise _error("The trusted operator denied authority for this exact voice request.",
                     ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
    validate_paid_provider_authorization(paid, decision, now=clock())
    if decision.egress_policy_receipt_id != operator.egress_receipt_id:
        raise _error("The paid authorization's egress receipt did not match.", ErrorCode.VOICE_EGRESS_NOT_AUTHORIZED)
    return decision


def run_takes(cfg, vo_dir, *, approved_digest, operator, transport, credential, toolchain, only=(),
              clock=lambda: datetime.now(timezone.utc)) -> dict[str, Path]:
    groups = selected_groups(cfg, only)
    settings = voice_settings(cfg)
    project_id = _project_id(cfg)
    if approved_digest != canonical_sha256(cfg):
        raise _error("The current complete narration plan lacks matching approval evidence.",
                     ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
    _validate_operator(operator, settings)
    root = voice_root(vo_dir)
    old_ledger = root.parent / "ledger.json"
    if old_ledger.exists() or old_ledger.is_symlink():
        raise _error("The upstream billing ledger requires separate reconciliation before using this workspace.")
    if not (root / "project.yaml").is_file() and root.parent.exists():
        if any(entry != root for entry in root.parent.iterdir()):
            raise _error("Existing voice files require their original canonical state. Use an empty workspace for new episodes.")
    prepare_standalone_voice_project(
        root, project_id=project_id, objective=project_id, source_reference=project_id,
        creation_receipt_id=project_id, language=settings.language, title="Replica narration",
    )
    prepare_standalone_voice_graph(root)
    provider = MiniMaxSpeechVoiceProvider(
        transport=transport, pricing=operator.pricing, api_key=credential, policy=operator.policy,
    )
    outputs = {}
    for group in groups:
        loaded = load_voice_project(vo_dir, cfg)
        artifact = current_artifact(loaded, group, cfg)
        if artifact is None:
            if any(attempt.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
                   for attempt in loaded.manifest.attempts):
                raise _error("The voice workspace has an unresolved attempt. Recover it before new submissions.",
                             ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN)
            request = _voice_request(loaded, group, cfg, settings, operator)
            preview = provider.preview(request)
            paid = _paid_preview(request, preview, operator.policy)
            decision = _authorize(operator, paid, approved_digest, clock)
            authorization = VoiceCallAuthorization.create(
                request_fingerprint=request.voice_request_fingerprint,
                preview_fingerprint=preview.preview_fingerprint, pricing_snapshot_id=request.pricing_snapshot_id,
                budget_reservation_receipt_id=request.budget_reservation_receipt_id,
                egress_authorization_receipt_id=request.egress_authorization_receipt_id,
                destination=preview.destination, payload_categories=preview.payload_categories,
                cost_ceiling_microunits=decision.per_call_ceiling_microunits, provider_enabled=True,
            )
            validate_voice_call_authorization(request, preview, authorization, pricing=operator.pricing)
            pointer = loaded.manifest.active_paid_provider_budget
            budget = load_paid_provider_budget(root, pointer) if pointer is not None else None
            reserve_paid_provider_budget(
                budget, preview=paid, authorization=decision, reservation_id=request.budget_reservation_receipt_id,
            )
            committer = ProductionStateCommitter(
                root, paid_provider_authorizer=lambda exact: decision if exact == paid else None,
                paid_provider_clock=clock, voice_candidate_preparer=make_voice_candidate_preparer(root, toolchain),
            )
            committer.generate_voice_asset(
                request, provider, authorization, paid_preview=paid,
                dependency_transition_preparer=lambda candidate: prepare_standalone_voice_transition(root, candidate),
            )
            artifact = current_artifact(load_voice_project(vo_dir, cfg), group, cfg)
            if artifact is None:
                raise _error("The successful take did not reopen.", ErrorCode.AUDIO_ASSET_INVALID)
        outputs[group["id"]] = artifact
    return outputs


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("vo_dir", type=Path)
    parser.add_argument("groups", nargs="*")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-plan-sha256")
    parser.add_argument("--runtime", help="Explicit trusted local operator factory module:function")
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--ffprobe", type=Path)
    args = parser.parse_intermixed_args(argv)
    cfg = read_json(args.plan)
    groups = selected_groups(cfg, args.groups)
    settings = voice_settings(cfg)
    _project_id(cfg)
    digest = canonical_sha256(cfg)
    if not args.execute:
        print(json.dumps({"status": "selection_preview", "plan_sha256": digest,
                          "takes": [take_name(group, cfg) for group in groups]}, ensure_ascii=False))
        return
    if args.approved_plan_sha256 != digest or not args.runtime or ":" not in args.runtime:
        raise _error("Execution requires an approved plan SHA-256 and a trusted local operator.",
                     ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED)
    module, name = args.runtime.split(":", 1)
    try:
        operator = getattr(import_module(module), name)(episode_id=cfg["episode_id"], voice_root=voice_root(args.vo_dir))
    except Exception:
        raise _error("The trusted voice operator could not be loaded.",
                     ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED) from None
    _validate_operator(operator, settings)
    transport, credential, toolchain = minimax_speech_capabilities(
        settings.credential_reference, ffmpeg=tool_path("ffmpeg", args.ffmpeg),
        ffprobe=tool_path("ffprobe", args.ffprobe),
    )
    outputs = run_takes(
        cfg, args.vo_dir, only=args.groups, approved_digest=digest, operator=operator,
        transport=transport, credential=credential, toolchain=toolchain,
    )
    print(json.dumps({"status": "succeeded", "wav_files": {key: str(path) for key, path in outputs.items()}},
                     ensure_ascii=False))


if __name__ == "__main__":
    cli(main)
