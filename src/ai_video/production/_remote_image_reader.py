"""Read-only joins between durable image and paid evidence."""

from pathlib import Path
import hashlib
import json

from ai_video.production.image import ImageGenerationAuthorization, ImageGenerationPreview, ImageGenerationRequest
from ai_video.production.models import StateCommitStatus, PaidProviderAttemptPhase
from ai_video.production.paid_provider import PaidProviderSubmitOutcome
from ai_video.production.paths import (
    _read_regular_file_nofollow, canonical_image_request_path,
    canonical_image_authorization_path, canonical_image_preview_path,
    canonical_image_submit_intent_path,
)


def reopen_remote_image_authority(root, attempt):
    s = attempt.image_request
    if s is None:
        raise ValueError("remote image request summary is missing")
    def read(path, model):
        return model.model_validate_json(_read_regular_file_nofollow(
            Path(root) / path, contained_by=Path(root)).data)
    request = read(canonical_image_request_path(s.request_fingerprint), ImageGenerationRequest)
    preview = read(canonical_image_preview_path(s.preview_fingerprint), ImageGenerationPreview)
    auth = read(canonical_image_authorization_path(s.authorization_fingerprint), ImageGenerationAuthorization)
    if (auth.local_only or auth.remote_binding is None or preview.local_only or not preview.remote
            or preview.remote_call != auth.remote_binding.preview
            or request.attempt_id != attempt.attempt_id
            or request.request_fingerprint != s.request_fingerprint
            or preview.request_fingerprint != request.request_fingerprint
            or auth.request_fingerprint != request.request_fingerprint
            or auth.preview_fingerprint != preview.preview_fingerprint
            or auth.authorization_fingerprint != s.authorization_fingerprint):
        raise ValueError("remote image authority does not match its durable request")
    return request, preview, auth


def validate_remote_image_paid_intent(root, attempt, paid_preview, paid_authorization):
    request, preview, auth = reopen_remote_image_authority(root, attempt)
    if (attempt.operation != "image_generation" or attempt.status is not StateCommitStatus.RUNNING
            or attempt.image_phase != "submit_intent" or auth.remote_binding.preview != paid_preview
            or auth.remote_binding.authorization != paid_authorization
            or paid_preview.attempt_id != request.attempt_id
            or paid_preview.request_fingerprint != request.request_fingerprint
            or paid_preview.provider_kind != request.provider_kind or paid_preview.model_id != request.model_id):
        raise ValueError("paid image intent does not match its exact image authority")
    # Reopen the complete canonical image R+2 audit before issuing POST authority.
    rows = []
    for path in (canonical_image_request_path(request.request_fingerprint),
                 canonical_image_preview_path(preview.preview_fingerprint),
                 canonical_image_authorization_path(auth.authorization_fingerprint)):
        raw = _read_regular_file_nofollow(Path(root) / path, contained_by=Path(root))
        rows.append((path.as_posix(), raw.file_sha256))
    intent_path = canonical_image_submit_intent_path(request.request_fingerprint)
    intent_raw = _read_regular_file_nofollow(Path(root) / intent_path, contained_by=Path(root))
    intent = json.loads(intent_raw.data)
    def digest(pairs):
        return hashlib.sha256(json.dumps(sorted(pairs), separators=(",", ":")).encode()).hexdigest()
    expected = dict(schema="ai-video-image-submit-intent/1", attempt_id=request.attempt_id,
        request_fingerprint=request.request_fingerprint, preview_fingerprint=preview.preview_fingerprint,
        authorization_fingerprint=auth.authorization_fingerprint, policy_receipt_id=auth.policy_receipt_id,
        usage_license=auth.usage_license, base_project=request.base_project.model_dump(mode="json"),
        base_registry=request.base_registry.model_dump(mode="json"),
        base_dependency_graph=request.base_dependency_graph.model_dump(mode="json"),
        evidence_hash=digest(rows))
    if intent != expected:
        raise ValueError("remote image intent bytes differ from the sealed image request")
    if digest((*rows, (intent_path.as_posix(), intent_raw.file_sha256))) != attempt.candidate_artifacts_hash:
        raise ValueError("remote image R+2 artifact set differs from its durable summary")


def verify_remote_image_submit(root, attempt, authorization, evidence):
    from ai_video.production._paid_provider_project_reader import (
        load_paid_provider_gate_receipt, load_paid_provider_submit_receipt,
    )
    state = attempt.paid_provider_state
    remote = authorization.remote_binding
    if state is None or remote is None or state.phase not in {
            PaidProviderAttemptPhase.ACCEPTED, PaidProviderAttemptPhase.SETTLED} or state.submit_receipt is None:
        raise ValueError("remote image has no accepted durable paid receipt")
    gate = load_paid_provider_gate_receipt(root, state.gate_receipt)
    submit = load_paid_provider_submit_receipt(root, state.submit_receipt)
    if (gate.preview != remote.preview or gate.authorization != remote.authorization
            or submit != evidence.submit_receipt or submit.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or submit.gate_receipt_fingerprint != gate.gate_receipt_fingerprint
            or submit.reservation_id != state.reservation_id):
        raise ValueError("remote image paid provenance join is inconsistent")


def remote_image_wire_path(evidence, provider_kind="grok"):
    suffix = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}[evidence.wire_mime_type]
    if provider_kind not in {"grok", "seedream"}:
        raise ValueError("unsupported remote image wire owner")
    return Path(f"assets/files/{provider_kind}-wire/{evidence.wire_sha256}.{suffix}")


def reopen_remote_image_result(root, attempt, receipt, png_bytes, result_value):
    from ai_video.production.image import ImageProviderResult
    from ai_video.production.grok_image_bytes import decode_grok_image

    root = Path(root)
    request, _, authorization = reopen_remote_image_authority(root, attempt)
    evidence = receipt.remote_evidence
    wire_path = remote_image_wire_path(evidence, request.provider_kind)
    wire = _read_regular_file_nofollow(root / wire_path, contained_by=root / "assets/files")
    if wire.file_sha256 != evidence.wire_sha256 or wire.size_bytes != evidence.wire_size_bytes:
        raise ValueError("remote image wire bytes do not match provenance")
    if request.provider_kind == "seedream":
        from ai_video.production.image import measure_png_bytes
        measure_png_bytes(wire.data)
        decoded, mime, conversion = wire.data, "image/png", "identity-png"
    else:
        decoded, mime, conversion = decode_grok_image(wire.data)
    if decoded != png_bytes or mime != evidence.wire_mime_type or conversion != evidence.conversion:
        raise ValueError("remote image PNG differs from its preserved wire conversion")
    verify_remote_image_submit(root, attempt, authorization, evidence)
    result = ImageProviderResult.model_validate(
        {**result_value, "image_bytes": png_bytes, "wire_image_bytes": wire.data})
    return authorization, result, ((wire_path, wire.file_sha256),)
