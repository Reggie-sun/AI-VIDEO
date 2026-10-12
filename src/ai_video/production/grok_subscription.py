"""Read-only subscription evidence; usage never proves a cash overage cap."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import StrictModel

GROK_SUBSCRIPTION_ORIGIN = "https://cli-chat-proxy.grok.com"
GROK_BILLING_URL = GROK_SUBSCRIPTION_ORIGIN + "/v1/billing?format=credits"
GROK_CREDENTIAL_REFERENCE = "GROK_OAUTH"


class GrokSubscriptionBinding(StrictModel):
    """Public binding to an independently verified exact included-only boundary.

    Creating this model does not authorize a call. The injected authority must
    reopen the boundary before the durable permit and again before transport.
    The currently documented billing endpoint cannot provide that authority.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    account_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    credential_reference_id: Literal["GROK_OAUTH"]
    destination: Literal["https://cli-chat-proxy.grok.com"]
    model_id: Literal["grok-imagine-video-1.5", "grok-imagine-image-2.0"]
    quota_observed_at: datetime
    quota_expires_at: datetime
    period_end: datetime
    used_percent: float = Field(ge=0, lt=100, allow_inf_nan=False)
    overage_policy: Literal["included_only"] = "included_only"
    included_only_evidence_id: str = Field(pattern=r"^[A-Za-z0-9._:/-]{1,256}$")

    @model_validator(mode="after")
    def _finite_window(self):
        if any(t.tzinfo is None or t.utcoffset() is None for t in (
            self.quota_observed_at, self.quota_expires_at, self.period_end,
        )) or not (self.quota_observed_at < self.quota_expires_at <= self.period_end):
            raise ValueError("subscription quota requires an aware finite window")
        if self.quota_expires_at - self.quota_observed_at > timedelta(minutes=5):
            raise ValueError("subscription quota observation must expire within five minutes")
        return self


def require_current_subscription(binding: GrokSubscriptionBinding, *,
        account_fingerprint: str, model_id: str, destination: str,
        now: datetime) -> GrokSubscriptionBinding:
    checked = GrokSubscriptionBinding.model_validate(binding.model_dump(mode="python"))
    if (checked != binding or binding.account_fingerprint != account_fingerprint
            or binding.model_id != model_id or binding.destination != destination
            or now.tzinfo is None
            or not binding.quota_observed_at <= now < binding.quota_expires_at):
        raise AiVideoError(code=ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            user_message="Grok subscription account, model or quota evidence is not current.")
    return binding


@dataclass(frozen=True)
class GrokSubscriptionUsage:
    used_percent: float | None
    period_end: datetime | None
    # No documented server-side included-only switch exists in this response.
    included_only_verified: Literal[False] = False


def parse_subscription_usage(payload: object) -> GrokSubscriptionUsage:
    config = payload.get("config") if isinstance(payload, dict) else None
    if not isinstance(config, dict):
        raise AiVideoError(code=ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
            user_message="Grok billing response does not contain subscription evidence.")
    percent = config.get("creditUsagePercent", config.get("credit_usage_percent"))
    if percent is None:
        used, limit = config.get("used"), config.get("monthlyLimit", config.get("monthly_limit"))
        used = used.get("val") if isinstance(used, dict) else None
        limit = limit.get("val") if isinstance(limit, dict) else None
        if (isinstance(used, (int, str)) and not isinstance(used, bool)
                and isinstance(limit, (int, str)) and not isinstance(limit, bool)):
            try:
                u, total = int(used), int(limit)
                percent = u / total * 100 if u >= 0 and total > 0 else None
            except (ValueError, OverflowError):
                percent = None
    if (type(percent) not in (int, float) or not 0 <= percent <= 100):
        percent = None
    period = config.get("currentPeriod", config.get("current_period"))
    period_type = period.get("type") if isinstance(period, dict) else None
    end = period.get("end") if isinstance(period, dict) else None
    end = end or config.get("billingPeriodEnd", config.get("billing_period_end"))
    period_end = None
    if isinstance(period_type, str) and period_type.endswith(("WEEKLY", "MONTHLY")) and isinstance(end, str):
        try:
            parsed = datetime.fromisoformat(end.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                period_end = parsed
        except ValueError:
            pass
    return GrokSubscriptionUsage(percent, period_end)


def reject_unverified_included_only(binding: GrokSubscriptionBinding) -> None:
    """Default live authority: fail closed rather than invent a server hard cap."""
    raise AiVideoError(code=ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
        user_message="SuperGrok included-only media billing is not verified; generation is blocked.")
