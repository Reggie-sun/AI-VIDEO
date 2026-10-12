"""Read-only OAuth subscription usage, without claiming generation admission."""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.grok_subscription import (
    GROK_BILLING_URL, GROK_SUBSCRIPTION_ORIGIN, GrokSubscriptionBinding,
    parse_subscription_usage, require_current_subscription,
)
from ai_video.production.hashing import canonical_sha256


def read_grok_subscription_usage(*, account_fingerprint: str,
        credential: Callable[[], str], client: httpx.Client | None = None) -> dict[str, object]:
    """The credential supplier must bind the given account; this performs one GET."""
    if len(account_fingerprint) != 64 or any(c not in "0123456789abcdef" for c in account_fingerprint):
        raise AiVideoError(code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            user_message="Grok subscription usage requires an exact account fingerprint.")
    try:
        usage = parse_subscription_usage(_read_fixed_json(GROK_BILLING_URL,
            credential=credential, client=client))
        return {"account_fingerprint": account_fingerprint,
            "observed_at": datetime.now(UTC).isoformat(), "used_percent": usage.used_percent,
            "period_end": usage.period_end.isoformat() if usage.period_end else None,
            "generation_state": "blocked", "included_only_verified": False,
            "reason": "Subscription usage does not prove an included-only media billing boundary."}
    except Exception:
        raise AiVideoError(code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            user_message="Grok subscription usage could not be verified; generation remains blocked.") from None


def _read_fixed_json(url: str, *, credential: Callable[[], str],
        client: httpx.Client | None) -> object:
    if url not in (GROK_BILLING_URL, GROK_SUBSCRIPTION_ORIGIN + "/v1/auto-topup-rule"):
        raise ValueError("untrusted billing endpoint")
    owns_client = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=False)
    try:
        token = credential()
        if not isinstance(token, str) or not token or any(c in token for c in "\r\n"):
            raise ValueError("invalid credential")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
            "x-grok-client-mode": "cli", "x-grok-client-version": "1.0.4"}
        request = httpx.Request("GET", url, headers=headers,
            extensions={"timeout": httpx.Timeout(30).as_dict()})
        response = client.send(request, auth=None, follow_redirects=False, stream=True)
        try:
            if response.status_code != 200:
                raise ValueError("billing response rejected")
            raw = bytearray()
            for chunk in response.iter_bytes():
                if len(raw) + len(chunk) > 256 * 1024:
                    raise ValueError("billing response exceeded its bound")
                raw.extend(chunk)
            return json.loads(raw)
        finally:
            response.close()
    finally:
        if owns_client:
            client.close()


class GrokIncludedOnlyAuthority:
    """Explicit live authority for a unified pool with every cash path disabled.

    Uses xAI credits and auto-topup schemas; never changes server configuration.
    An OAuth/model catalog observation remains a separate capability prerequisite.
    """

    def __init__(self, *, account_fingerprint: str, credential: Callable[[], str],
            client: httpx.Client | None = None, now: Callable[[], datetime] | None = None):
        if len(account_fingerprint) != 64 or any(c not in "0123456789abcdef" for c in account_fingerprint):
            raise ValueError("invalid subscription account fingerprint")
        self._account = account_fingerprint
        self._credential = credential
        self._client = client
        self._now = now or (lambda: datetime.now(UTC))

    def observe(self, *, model_id: str, operation_path: str) -> GrokSubscriptionBinding:
        try:
            # Validate model/operation before lookup or any HTTP effect.
            paths = ({"/v1/images/edits"} if model_id == "grok-imagine-image-2.0" else
                {"/v1/videos/generations", "/v1/videos/edits", "/v1/videos/extensions"}
                if model_id == "grok-imagine-video" else {"/v1/videos/generations"}
                if model_id in ("grok-imagine-video-1.5", "grok-imagine-video-1.5-lite") else set())
            if operation_path not in paths:
                raise ValueError("unsupported subscription operation")
            payload = _read_fixed_json(GROK_BILLING_URL,
                credential=self._credential, client=self._client)
            usage = parse_subscription_usage(payload)
            config = payload["config"]
            if config.get("isUnifiedBillingUser") is not True or any(
                not (type(config.get(key)) is dict and type(config[key].get("val")) is int
                     and config[key]["val"] == 0)
                for key in ("onDemandCap", "onDemandUsed", "prepaidBalance")
            ):
                raise ValueError("cash boundary is not disabled")
            topup = _read_fixed_json(GROK_SUBSCRIPTION_ORIGIN + "/v1/auto-topup-rule",
                credential=self._credential, client=self._client)
            if type(topup) is not dict or set(topup) - {"rule"}:
                raise ValueError("unknown auto-topup schema")
            rule = topup.get("rule")
            if rule is not None and (type(rule) is not dict or
                    set(rule) - {"enabled", "minBeforeHittingSl", "topupAmount", "maxAmountPerMonth"}
                    or type(rule.get("enabled", False)) is not bool or rule.get("enabled", False)):
                raise ValueError("auto-topup is not disabled")
            now = self._now()
            if (now.tzinfo is None or usage.period_end is None or now >= usage.period_end
                    or usage.used_percent is None or not 0 <= usage.used_percent < 100):
                raise ValueError("subscription quota is not current")
            evidence = canonical_sha256({"account": self._account, "model": model_id,
                "operation": operation_path, "origin": GROK_SUBSCRIPTION_ORIGIN,
                "period_end": usage.period_end.isoformat(), "cash_paths": "disabled",
                "sources": [GROK_BILLING_URL, GROK_SUBSCRIPTION_ORIGIN + "/v1/auto-topup-rule"]})
            return GrokSubscriptionBinding(account_fingerprint=self._account,
                credential_reference_id="GROK_OAUTH", destination=GROK_SUBSCRIPTION_ORIGIN,
                model_id=model_id, operation_path=operation_path, quota_observed_at=now,
                quota_expires_at=min(now + timedelta(minutes=5), usage.period_end),
                period_end=usage.period_end, used_percent=usage.used_percent,
                included_only_evidence_id="grok-included-only:" + evidence)
        except Exception:
            raise AiVideoError(code=ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
                user_message="Grok included-only billing boundary could not be verified; generation is blocked.") from None

    def __call__(self, binding: GrokSubscriptionBinding) -> None:
        try:
            require_current_subscription(binding, account_fingerprint=self._account,
                model_id=binding.model_id, destination=GROK_SUBSCRIPTION_ORIGIN,
                operation_path=binding.operation_path, now=self._now())
            current = self.observe(model_id=binding.model_id, operation_path=binding.operation_path)
            if current.included_only_evidence_id != binding.included_only_evidence_id:
                raise ValueError("subscription evidence identity changed")
            require_current_subscription(binding, account_fingerprint=self._account,
                model_id=binding.model_id, destination=GROK_SUBSCRIPTION_ORIGIN,
                operation_path=binding.operation_path, now=self._now())
        except Exception:
            raise AiVideoError(code=ErrorCode.PAID_PROVIDER_BUDGET_REJECTED,
                user_message="Grok included-only billing authority is not current; generation is blocked.") from None
