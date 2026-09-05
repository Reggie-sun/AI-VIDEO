"""Read-only evidence for reusing a fetched Vidu creation as extension input."""

from __future__ import annotations

from pydantic import ConfigDict, model_validator

from ai_video.production.models import StrictModel
from ai_video.production.paid_provider import PaidProviderSubmitReceipt, PaidProviderSubmitOutcome
from ai_video.production.video import VideoFetchReceipt, VideoMediaReferenceBinding, VideoSubmission
from ai_video.production.video_artifact import VideoProbeReceipt


class ViduExtensionSource(StrictModel):
    """Reopened canonical receipts, supplied by the caller; no remote URL or writer."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    submission: VideoSubmission
    submit_receipt: PaidProviderSubmitReceipt
    fetch_receipt: VideoFetchReceipt
    probe_receipt: VideoProbeReceipt

    @model_validator(mode="after")
    def _validate_chain(self) -> "ViduExtensionSource":
        submit, paid, fetched, probe = self.submission, self.submit_receipt, self.fetch_receipt, self.probe_receipt
        measured = probe.measured
        if (
            paid.outcome is not PaidProviderSubmitOutcome.ACCEPTED
            or submit.paid_submit_receipt_fingerprint != paid.submit_receipt_fingerprint
            or submit.resolved_generation_hash != paid.request_fingerprint
            or fetched.submission_fingerprint != submit.submission_fingerprint
            or fetched.paid_submit_receipt_fingerprint != paid.submit_receipt_fingerprint
            or probe.fetch_fingerprint != fetched.fetch_fingerprint
            or probe.resolved_generation_hash != submit.resolved_generation_hash
            or probe.request_receipt_fingerprint != submit.resolved_generation_hash
            or measured.artifact_sha256 != fetched.artifact_sha256
            or measured.size_bytes != fetched.size_bytes
            or fetched.content_type != "video/mp4"
            or measured.audio_stream_count != 0
        ):
            raise ValueError("Vidu extension source receipts do not match a silent fetched video")
        return self

    def matches(self, binding: VideoMediaReferenceBinding) -> bool:
        measured = self.probe_receipt.measured
        return (
            binding.kind == "video" and binding.mime_type == self.fetch_receipt.content_type
            and binding.asset_sha256 == measured.artifact_sha256
            and binding.size_bytes == measured.size_bytes
            and binding.duration_millis == measured.duration_milliseconds
            and binding.width == measured.width and binding.height == measured.height
            and binding.fps * measured.fps_denominator == measured.fps_numerator
        )
