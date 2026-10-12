"""Read-only OAuth subscription usage, without claiming generation admission."""

import json
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.grok_subscription import GROK_BILLING_URL, parse_subscription_usage


def read_grok_subscription_usage(*, account_fingerprint: str,
        credential: Callable[[], str], client: httpx.Client | None = None) -> dict[str, object]:
    """The credential supplier must bind the given account; this performs one GET."""
    if len(account_fingerprint) != 64 or any(c not in "0123456789abcdef" for c in account_fingerprint):
        raise AiVideoError(code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            user_message="Grok subscription usage requires an exact account fingerprint.")
    owns_client = client is None
    client = client or httpx.Client(timeout=30, follow_redirects=False)
    try:
        token = credential()
        if not isinstance(token, str) or not token or any(c in token for c in "\r\n"):
            raise ValueError("invalid credential")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
            "x-grok-client-mode": "cli", "x-grok-client-version": "1.0.4"}
        exact = httpx.Request("GET", GROK_BILLING_URL, headers=headers,
            extensions={"timeout": httpx.Timeout(30).as_dict()})
        response = client.send(exact, auth=None, follow_redirects=False, stream=True)
        try:
            if response.status_code != 200:
                raise ValueError("billing response rejected")
            raw = bytearray()
            for chunk in response.iter_bytes():
                if len(raw) + len(chunk) > 256 * 1024:
                    raise ValueError("billing response exceeded its bound")
                raw.extend(chunk)
        finally:
            response.close()
        usage = parse_subscription_usage(json.loads(raw))
        return {"account_fingerprint": account_fingerprint,
            "observed_at": datetime.now(UTC).isoformat(), "used_percent": usage.used_percent,
            "period_end": usage.period_end.isoformat() if usage.period_end else None,
            "generation_state": "blocked", "included_only_verified": False,
            "reason": "Subscription usage does not prove an included-only media billing boundary."}
    except Exception:
        raise AiVideoError(code=ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED,
            user_message="Grok subscription usage could not be verified; generation remains blocked.") from None
    finally:
        if owns_client:
            client.close()
