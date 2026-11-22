"""Contract for a trusted operator supplying client narration authority."""

from collections.abc import Callable
from dataclasses import dataclass

from ai_video.production.audio import VoicePricingSnapshot
from ai_video.production.minimax_speech import MiniMaxSpeechProviderPolicy
from ai_video.production.paid_provider import PaidProviderAuthorizationDecision, PaidProviderCallPreview


@dataclass(frozen=True)
class VoiceOperator:
    policy: MiniMaxSpeechProviderPolicy
    pricing: VoicePricingSnapshot
    egress_receipt_id: str
    authorize: Callable[[PaidProviderCallPreview, str], PaidProviderAuthorizationDecision | None]
