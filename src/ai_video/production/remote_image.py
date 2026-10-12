"""Remote image joins and provenance behind the existing image/paid owners."""

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.models import EgressMetadata, StrictModel
from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision, PaidProviderCallPreview,
    PaidProviderSubmitOutcome, PaidProviderSubmitReceipt, validate_paid_provider_authorization,
)


class RemoteImageAuthorization(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    preview: PaidProviderCallPreview
    authorization: PaidProviderAuthorizationDecision

    @model_validator(mode="after")
    def _exact_media_scope(self):
        if self.preview.operation != "image_generation":
            raise ValueError("remote image authorization requires an image operation")
        validate_paid_provider_authorization(self.preview, self.authorization,
            now=self.authorization.issued_at)
        return self


class RemoteImageEvidence(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    submit_receipt: PaidProviderSubmitReceipt
    wire_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    wire_size_bytes: int = Field(strict=True, gt=0)
    wire_mime_type: str = Field(pattern=r"^image/(png|jpeg|webp)$")
    conversion: str = Field(pattern=r"^(identity-png|pillow-lossless-png)$")

    @model_validator(mode="after")
    def _accepted_only(self):
        if self.submit_receipt.outcome is not PaidProviderSubmitOutcome.ACCEPTED:
            raise ValueError("remote image evidence requires an accepted submit")
        if (self.conversion == "identity-png") != (self.wire_mime_type == "image/png"):
            raise ValueError("remote image conversion does not match the wire format")
        return self


def remote_image_egress(remote: RemoteImageAuthorization | None) -> EgressMetadata:
    if remote is None:
        return EgressMetadata(remote=False)
    p, a = remote.preview, remote.authorization
    return EgressMetadata(remote=True, destination=p.destination,
        authorization_receipt_id=a.egress_policy_receipt_id,
        request_fingerprint=p.request_fingerprint, payload_fingerprint=p.preview_fingerprint,
        retention_mode=p.retention_mode, provider_policy_snapshot_id=p.provider_policy_snapshot_id)


def remote_image_permit_binding(remote: RemoteImageAuthorization) -> dict[str, str]:
    p, a = remote.preview, remote.authorization
    return dict(attempt_id=p.attempt_id, operation=p.operation,
        request_fingerprint=p.request_fingerprint, destination=p.destination,
        provider_kind=p.provider_kind, model_id=p.model_id, currency=p.currency,
        estimated_cost_upper_bound_microunits=str(p.estimated_cost_upper_bound_microunits),
        authorization_fingerprint=a.authorization_fingerprint,
        provider_policy_snapshot_id=p.provider_policy_snapshot_id, retention_mode=p.retention_mode,
        secret_reference_kind=p.secret_reference.kind, secret_reference_id=p.secret_reference.reference_id)
