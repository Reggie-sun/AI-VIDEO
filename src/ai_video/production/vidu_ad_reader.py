"""Strict read-only reopening of whole-ad source evidence."""

from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.vidu_ad_contracts import AdGenerationRequest, AdSourceCandidate
from ai_video.production.vidu_profile import ViduAdProviderProfile


def _read(root, path):
    return _read_regular_file_nofollow(Path(root) / path, contained_by=Path(root))


def reopen_ad_request(root, attempt):
    state = attempt.ad_generation_state
    if state is None:
        raise ValueError("missing ad state")
    request = AdGenerationRequest.model_validate_json(_read(root, state.request.path).data)
    if request != state.request:
        raise ValueError("ad request file changed")
    profile = ViduAdProviderProfile.model_validate_json(
        _read(root, Path(f"provider-profiles/{request.profile_hash}.json")).data
    )
    if profile.pointer().profile_sha256 != request.profile_hash:
        raise ValueError("ad profile changed")
    return request, profile


def validate_ad_intent(root, manifest, attempt, preview, now):
    from ai_video.production.vidu_ad_provider import ad_preview
    request, profile = reopen_ad_request(root, attempt)
    state = attempt.ad_generation_state
    if (preview != ad_preview(request, profile, attempt.attempt_id)
            or preview.preview_fingerprint != state.preview_fingerprint
            or state.observation != "unsubmitted" or state.candidate is not None
            or attempt.base_project != manifest.active_project
            or attempt.base_registry != manifest.active_registry
            or not profile.pricing_observed_at <= now < min(profile.pricing_expires_at, request.expires_at)):
        raise ValueError("ad intent is stale or changed")
    validate_ad_images(root, attempt)
    siblings = [a for a in manifest.attempts if a.ad_generation_state is not None
                and a.ad_generation_state.request.task_id == request.task_id]
    if any(a.ad_generation_state.request.submit_limit != request.submit_limit
           or a.ad_generation_state.request.policy_id != request.policy_id for a in siblings):
        raise ValueError("ad task quota scope changed")
    if any(a.paid_provider_state is not None and a.paid_provider_state.phase.value
           in {"submit_intent", "outcome_unknown"} for a in siblings):
        raise ValueError("ad task has an unresolved submit")
    consumed = sum(a.paid_provider_state is not None for a in siblings)
    if consumed >= request.submit_limit:
        raise ValueError("ad task submit ceiling exhausted")


def validate_ad_images(root, attempt):
    from ai_video.production.registry import load_asset_registry
    request = attempt.ad_generation_state.request
    registry, paths = load_asset_registry(attempt.base_registry.path, root, Path(root) / "assets")
    if registry.content_hash != request.registry_hash or registry.revision_id != attempt.base_registry.revision_id:
        raise ValueError("ad input registry changed")
    for image in request.images:
        record = next((x for x in registry.assets if x.asset_id == image.asset_id), None)
        if record is None or record.asset_type.value != "image" or (
            record.sha256, record.size_bytes, record.mime_type, record.width, record.height
        ) != (image.sha256, image.size_bytes, image.mime_type, image.width, image.height):
            raise ValueError("ad image does not match registered product bytes")
        raw = _read_regular_file_nofollow(paths[image.asset_id], contained_by=Path(root) / "assets")
        if raw.file_sha256 != image.sha256 or len(raw.data) != image.size_bytes:
            raise ValueError("ad input bytes changed")


def verify_ad_evidence(root, manifest):
    from ai_video.production.vidu_ad_provider import ad_preview
    from ai_video.production._paid_provider_project_reader import (
        load_paid_provider_gate_receipt, load_paid_provider_submit_receipt,
    )
    try:
        scopes = {}
        for attempt in manifest.attempts:
            state = attempt.ad_generation_state
            if state is None:
                continue
            request, profile = reopen_ad_request(root, attempt)
            if request.project_id != manifest.project_id:
                raise ValueError("ad project changed")
            validate_ad_images(root, attempt)
            preview = ad_preview(request, profile, attempt.attempt_id)
            if preview.preview_fingerprint != state.preview_fingerprint:
                raise ValueError("ad preview changed")
            previous = scopes.setdefault(request.task_id, (request.submit_limit, request.policy_id))
            if previous != (request.submit_limit, request.policy_id):
                raise ValueError("ad task quota scope changed")
            paid = attempt.paid_provider_state
            if paid is None:
                continue
            gate = load_paid_provider_gate_receipt(root, paid.gate_receipt)
            if gate.preview != preview:
                raise ValueError("ad paid gate does not bind exact request")
            candidate = state.candidate
            if candidate is not None:
                if AdSourceCandidate.model_validate_json(_read(root, candidate.receipt_path).data) != candidate:
                    raise ValueError("ad source receipt changed")
                receipt = load_paid_provider_submit_receipt(root, paid.submit_receipt)
                if (receipt.external_effect_id != candidate.task_id
                        or receipt.submit_receipt_fingerprint != candidate.submit_receipt_hash):
                    raise ValueError("ad candidate task or receipt changed")
                raw = _read(root, candidate.path)
                if (len(raw.data) != candidate.size_bytes or raw.file_sha256 != candidate.sha256
                        or candidate.size_bytes > profile.max_download_bytes):
                    raise ValueError("ad candidate bytes changed")
        for task_id, (limit, _) in scopes.items():
            if sum(a.ad_generation_state is not None and a.ad_generation_state.request.task_id == task_id
                   and a.paid_provider_state is not None for a in manifest.attempts) > limit:
                raise ValueError("ad task submit ceiling exceeded")
    except (OSError, ValueError, TypeError, AttributeError, AiVideoError):
        raise AiVideoError(code=ErrorCode.PRODUCTION_PROJECT_INVALID,
                           user_message="Whole-ad source evidence is invalid.") from None
