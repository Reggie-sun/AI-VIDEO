"""Explicit xAI OAuth login and a Secret Service backed token supplier."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol
from urllib.parse import urlsplit

import httpx

from ai_video.production.paid_provider import SecretReference
from ai_video.production._grok_auth_lock import GrokAuthLockError, grok_auth_mutation_lock


AUTH_ISSUER = "https://auth.x.ai"
# Shared public client from OpenClaw's xAI adapter; this project does not claim a separate registration.
OAUTH_CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"
OAUTH_SCOPE = "openid profile email offline_access grok-cli:access api:access"
DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
SECRET_REFERENCE = SecretReference(kind="secret_store", reference_id="GROK_OAUTH")

_SECRET_ATTRIBUTES = (
    "application", "ai-video", "provider", "grok", "credential", "GROK_OAUTH",
)
_SECRET_LABEL = "AI-VIDEO Grok OAuth"
_MAX_RESPONSE_BYTES = 256 * 1024
_MAX_SECRET_BYTES = 512 * 1024
_HTTP_TIMEOUT_SECONDS = 30.0
_DEVICE_CODE_TIMEOUT_SECONDS = 300.0
_MAX_DEVICE_CODE_TIMEOUT_SECONDS = 600.0
_MAX_DEVICE_CODE_LIFETIME_SECONDS = 86_400.0
_MAX_TOKEN_LIFETIME_SECONDS = 31_536_000
_DEVICE_CODE_POLL_MIN_SECONDS = 1.0
_DEVICE_CODE_DEFAULT_INTERVAL_SECONDS = 5.0
_DEVICE_CODE_SLOW_DOWN_SECONDS = 5.0

_DEVICE_ENDPOINT_PATHS = frozenset({"/oauth/device/code", "/oauth2/device/code"})
_TOKEN_ENDPOINT_PATHS = frozenset({"/oauth/token", "/oauth2/token"})
_USERINFO_ENDPOINT_PATHS = frozenset({"/oauth/userinfo", "/oauth2/userinfo", "/userinfo"})


class GrokAuthError(RuntimeError):
    """Sanitized authentication failure safe to show in a CLI."""


@dataclass(frozen=True)
class GrokOAuthTransportResponse:
    status_code: int
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)


class GrokOAuthTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        data: Mapping[str, str] | None = None,
    ) -> GrokOAuthTransportResponse: ...


class HttpxGrokOAuthTransport:
    """Small no-redirect transport for the fixed xAI OAuth origin."""

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=_HTTP_TIMEOUT_SECONDS, follow_redirects=False)
        self._owns_client = client is None

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        data: Mapping[str, str] | None = None,
    ) -> GrokOAuthTransportResponse:
        try:
            exact = httpx.Request(method, url, headers=dict(headers or {}),
                data=dict(data) if data is not None else None,
                extensions={"timeout": httpx.Timeout(_HTTP_TIMEOUT_SECONDS).as_dict()})
            response = self._client.send(exact, auth=None, follow_redirects=False, stream=True)
            try:
                body = bytearray()
                for chunk in response.iter_bytes():
                    if len(body) + len(chunk) > _MAX_RESPONSE_BYTES:
                        raise GrokAuthError("xAI OAuth response exceeds the size limit.")
                    body.extend(chunk)
                return GrokOAuthTransportResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=bytes(body),
                )
            finally:
                response.close()
        except GrokAuthError:
            raise
        except Exception:
            # HTTP client errors can contain request metadata or reflected response data.
            raise GrokAuthError("xAI OAuth network request failed.") from None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class GrokTokenStore:
    """Exact Secret Service item owner; never searches another credential source."""

    def __init__(self, *, runner: Callable[..., object] | None = None) -> None:
        self._runner = runner or subprocess.run

    @property
    def secret_reference(self) -> SecretReference:
        return SECRET_REFERENCE

    def load(self) -> dict[str, object] | None:
        argv = ["secret-tool", "lookup", *_SECRET_ATTRIBUTES]
        try:
            result = self._runner(argv, capture_output=True, timeout=15, check=False)
        except Exception:
            raise GrokAuthError("Grok OAuth Secret Service lookup failed.") from None
        returncode = getattr(result, "returncode", None)
        stdout = getattr(result, "stdout", b"")
        stderr = getattr(result, "stderr", b"")
        if isinstance(stdout, str):
            stdout = stdout.encode("utf-8")
        if isinstance(stderr, str):
            stderr = stderr.encode("utf-8")
        if returncode == 1 and not stdout and not stderr:
            return None
        if returncode != 0:
            raise GrokAuthError("Grok OAuth Secret Service lookup failed.")
        if not isinstance(stdout, bytes) or not stdout or len(stdout) > _MAX_SECRET_BYTES:
            raise GrokAuthError("Grok OAuth Secret Service credential is invalid.")
        try:
            value = json.loads(stdout.decode("utf-8"), parse_constant=_reject_json_constant)
        except (ValueError, UnicodeError, TypeError):
            raise GrokAuthError("Grok OAuth Secret Service credential is invalid.") from None
        return _validate_record(value)

    def save(self, record: Mapping[str, object]) -> None:
        value = _validate_record(dict(record))
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        if len(payload) > _MAX_SECRET_BYTES:
            raise GrokAuthError("Grok OAuth credential exceeds the size limit.")
        argv = ["secret-tool", "store", f"--label={_SECRET_LABEL}", *_SECRET_ATTRIBUTES]
        try:
            result = self._runner(argv, input=payload, capture_output=True, timeout=15, check=False)
        except Exception:
            raise GrokAuthError("Grok OAuth Secret Service write failed.") from None
        if getattr(result, "returncode", None) != 0:
            raise GrokAuthError("Grok OAuth Secret Service write failed.")


@dataclass(frozen=True)
class GrokAuthStatus:
    state: Literal["missing", "ready", "expired", "refresh_unknown"]
    account_fingerprint: str | None
    expires_at: datetime | None
    secret_reference: SecretReference = SECRET_REFERENCE

    @property
    def private_reference(self) -> str:
        return self.secret_reference.reference_id

    def public_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "account_fingerprint": self.account_fingerprint,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "secret_reference": self.secret_reference.model_dump(mode="json"),
        }


@dataclass(frozen=True)
class GrokCredential:
    access_token: str = field(repr=False)
    account_fingerprint: str
    expires_at: datetime
    secret_reference: SecretReference = SECRET_REFERENCE


@dataclass(frozen=True)
class _OAuthEndpoints:
    device_authorization: str
    token: str
    userinfo: str


class GrokOAuthManager:
    """Own explicit device login, explicit refresh, and account-bound access reads."""

    def __init__(
        self,
        *,
        store: GrokTokenStore,
        transport: GrokOAuthTransport | None = None,
        now: Callable[[], datetime] | None = None,
        sleep: Callable[[float], None] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._store = store
        self._transport = transport or HttpxGrokOAuthTransport()
        self._now = now or (lambda: datetime.now(UTC))
        self._sleep = sleep or time.sleep
        self._monotonic = monotonic or time.monotonic

    def login(
        self,
        *,
        timeout_seconds: float = _DEVICE_CODE_TIMEOUT_SECONDS,
        on_device_code: Callable[[str, str], None] | None = None,
    ) -> GrokAuthStatus:
        try:
            with grok_auth_mutation_lock():
                return self._login(timeout_seconds=timeout_seconds, on_device_code=on_device_code)
        except GrokAuthLockError as error:
            raise GrokAuthError(str(error)) from None

    def _login(
        self,
        *,
        timeout_seconds: float,
        on_device_code: Callable[[str, str], None] | None,
    ) -> GrokAuthStatus:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not 0 < timeout_seconds <= _MAX_DEVICE_CODE_TIMEOUT_SECONDS
        ):
            raise GrokAuthError("Grok OAuth login timeout must be between 0 and 600 seconds.")
        endpoints = self._discover_endpoints()
        device = self._request_device_code(endpoints.device_authorization)
        verification_uri = _trusted_verification_uri(device.get("verification_uri"))
        user_code = _nonblank_string(device.get("user_code"), max_length=128)
        device_code = _nonblank_string(device.get("device_code"), max_length=4096)
        expires_in = _positive_seconds(
            device.get("expires_in"), maximum=_MAX_DEVICE_CODE_LIFETIME_SECONDS,
        )
        interval = _positive_seconds(
            device.get("interval", _DEVICE_CODE_DEFAULT_INTERVAL_SECONDS), maximum=120,
        )
        if on_device_code is not None:
            on_device_code(verification_uri, user_code)
        token_payload = self._poll_device_code(
            endpoints.token,
            device_code=device_code,
            expires_in=expires_in,
            interval_seconds=max(_DEVICE_CODE_POLL_MIN_SECONDS, interval),
            timeout_seconds=timeout_seconds,
        )
        access_token, refresh_token, expires_at = self._read_token_payload(
            token_payload, require_refresh_token=True,
        )
        account_fingerprint = self._account_fingerprint(endpoints.userinfo, access_token)
        self._store.save({
            "schema_version": 1,
            "issuer": AUTH_ISSUER,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "account_fingerprint": account_fingerprint,
            "expires_at": expires_at.isoformat(),
            "refresh_state": "ready",
        })
        return self.status()

    def status(self) -> GrokAuthStatus:
        record = self._store.load()
        if record is None:
            return GrokAuthStatus(
                state="missing", account_fingerprint=None, expires_at=None,
            )
        expires_at = _parse_datetime(record["expires_at"])
        if record["refresh_state"] == "unknown":
            state: Literal["ready", "expired", "refresh_unknown"] = "refresh_unknown"
        elif self._current_time() >= expires_at:
            state = "expired"
        else:
            state = "ready"
        return GrokAuthStatus(
            state=state,
            account_fingerprint=str(record["account_fingerprint"]),
            expires_at=expires_at,
        )

    def credential_supplier(
        self, expected_account_fingerprint: str,
    ) -> Callable[[], str]:
        if not _is_fingerprint(expected_account_fingerprint):
            raise GrokAuthError("Expected Grok account fingerprint is invalid.")

        def supply() -> str:
            credential = self._credential(expected_account_fingerprint)
            return credential.access_token

        return supply

    def credential(
        self, expected_account_fingerprint: str,
    ) -> GrokCredential:
        if not _is_fingerprint(expected_account_fingerprint):
            raise GrokAuthError("Expected Grok account fingerprint is invalid.")
        return self._credential(expected_account_fingerprint)

    def refresh(self) -> GrokAuthStatus:
        try:
            with grok_auth_mutation_lock():
                return self._refresh()
        except GrokAuthLockError as error:
            raise GrokAuthError(str(error)) from None

    def _refresh(self) -> GrokAuthStatus:
        record = self._store.load()
        if record is None:
            raise GrokAuthError("Grok OAuth is not logged in; run login first.")
        if record["refresh_state"] == "unknown":
            raise GrokAuthError("Grok OAuth refresh outcome is unknown; re-login before continuing.")
        prior = _validated_ready_record(record)
        endpoints = self._discover_endpoints()

        # Persist the one-way stop marker before exchanging a rotating refresh token.
        unknown_record = dict(prior)
        unknown_record["refresh_state"] = "unknown"
        self._store.save(unknown_record)

        try:
            response = self._post_form(
                endpoints.token,
                {
                    "grant_type": "refresh_token",
                    "client_id": OAUTH_CLIENT_ID,
                    "refresh_token": str(prior["refresh_token"]),
                },
            )
            if response.status_code != 200:
                raise GrokAuthError("Grok OAuth refresh was rejected; re-login is required.")
            token_payload = _json_object(response.body)
            access_token, refresh_token, expires_at = self._read_token_payload(
                token_payload,
                require_refresh_token=False,
                previous_refresh_token=str(prior["refresh_token"]),
            )
            account_fingerprint = self._account_fingerprint(endpoints.userinfo, access_token)
            if account_fingerprint != prior["account_fingerprint"]:
                raise GrokAuthError("Grok OAuth account changed during refresh; re-login is required.")
            self._store.save({
                "schema_version": 1,
                "issuer": AUTH_ISSUER,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "account_fingerprint": account_fingerprint,
                "expires_at": expires_at.isoformat(),
                "refresh_state": "ready",
            })
        except Exception:
            # The durable unknown marker stays in place for every ambiguous or invalid result.
            raise GrokAuthError(
                "Grok OAuth refresh outcome is unknown; re-login before continuing."
            ) from None
        return self.status()

    def _credential(self, expected_account_fingerprint: str) -> GrokCredential:
        record = self._store.load()
        if record is None:
            raise GrokAuthError("Grok OAuth credential is unavailable; run login first.")
        if record["refresh_state"] == "unknown":
            raise GrokAuthError("Grok OAuth credential is unavailable after an unknown refresh outcome.")
        validated = _validated_ready_record(record)
        if validated["account_fingerprint"] != expected_account_fingerprint:
            raise GrokAuthError("Grok OAuth account does not match the expected account.")
        expires_at = _parse_datetime(validated["expires_at"])
        if self._current_time() >= expires_at:
            raise GrokAuthError("Grok OAuth access token has expired; refresh explicitly before use.")
        return GrokCredential(
            access_token=str(validated["access_token"]),
            account_fingerprint=str(validated["account_fingerprint"]),
            expires_at=expires_at,
        )

    def _discover_endpoints(self) -> _OAuthEndpoints:
        response = self._request("GET", f"{AUTH_ISSUER}/.well-known/openid-configuration")
        if response.status_code != 200:
            raise GrokAuthError("xAI OAuth discovery request failed.")
        document = _json_object(response.body)
        if document.get("issuer") != AUTH_ISSUER:
            raise GrokAuthError("xAI OAuth discovery issuer is invalid.")
        return _OAuthEndpoints(
            device_authorization=_trusted_endpoint(
                document.get("device_authorization_endpoint"), _DEVICE_ENDPOINT_PATHS,
                "device authorization",
            ),
            token=_trusted_endpoint(document.get("token_endpoint"), _TOKEN_ENDPOINT_PATHS, "token"),
            userinfo=_trusted_endpoint(
                document.get("userinfo_endpoint"), _USERINFO_ENDPOINT_PATHS, "userinfo",
            ),
        )

    def _request_device_code(self, endpoint: str) -> dict[str, object]:
        response = self._post_form(endpoint, {
            "client_id": OAUTH_CLIENT_ID,
            "scope": OAUTH_SCOPE,
        })
        if response.status_code != 200:
            raise GrokAuthError("xAI OAuth device-code request failed.")
        return _json_object(response.body)

    def _poll_device_code(
        self,
        endpoint: str,
        *,
        device_code: str,
        expires_in: float,
        interval_seconds: float,
        timeout_seconds: float,
    ) -> dict[str, object]:
        deadline = self._monotonic() + min(expires_in, timeout_seconds)
        interval = interval_seconds
        while self._monotonic() < deadline:
            response = self._post_form(endpoint, {
                "grant_type": DEVICE_CODE_GRANT,
                "client_id": OAUTH_CLIENT_ID,
                "device_code": device_code,
            })
            payload = _json_object(response.body)
            if response.status_code == 200:
                return payload
            error = payload.get("error")
            if response.status_code in {400, 428} and error == "authorization_pending":
                pass
            elif response.status_code in {400, 428} and error == "slow_down":
                interval += _DEVICE_CODE_SLOW_DOWN_SECONDS
            elif isinstance(error, str) and error in {"access_denied", "authorization_denied"}:
                raise GrokAuthError("Grok OAuth device authorization was denied.")
            elif isinstance(error, str) and error == "expired_token":
                raise GrokAuthError("Grok OAuth device code expired; run login again.")
            else:
                raise GrokAuthError("Grok OAuth device-token exchange failed.")
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                break
            self._sleep(min(interval, remaining))
        raise GrokAuthError("Grok OAuth device authorization timed out.")

    def _account_fingerprint(self, endpoint: str, access_token: str) -> str:
        response = self._request(
            "GET", endpoint, headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise GrokAuthError("xAI authenticated account identity lookup failed.")
        userinfo = _json_object(response.body)
        subject = _nonblank_string(userinfo.get("sub"), max_length=512)
        digest = hashlib.sha256(f"grok-account\0{AUTH_ISSUER}\0{subject}".encode()).hexdigest()
        return digest

    def _read_token_payload(
        self,
        payload: Mapping[str, object],
        *,
        require_refresh_token: bool,
        previous_refresh_token: str | None = None,
    ) -> tuple[str, str, datetime]:
        access_token = _nonblank_string(payload.get("access_token"), max_length=65_536)
        refresh_token = payload.get("refresh_token")
        if refresh_token is None and not require_refresh_token:
            refresh_token = previous_refresh_token
        refresh_token = _nonblank_string(refresh_token, max_length=65_536)
        now = self._current_time()
        expires_in = payload.get("expires_in")
        if expires_in is None:
            expires_at = _access_token_expiry(access_token)
            if (
                expires_at is None
                or not now < expires_at <= now + timedelta(seconds=_MAX_TOKEN_LIFETIME_SECONDS)
            ):
                raise GrokAuthError("xAI OAuth access-token expiry is unavailable.")
        else:
            duration = _positive_seconds(expires_in, maximum=_MAX_TOKEN_LIFETIME_SECONDS)
            expires_at = now + timedelta(seconds=duration)
        return access_token, refresh_token, expires_at

    def _current_time(self) -> datetime:
        value = self._now()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise GrokAuthError("Grok OAuth clock must return a timezone-aware time.")
        return value.astimezone(UTC)

    def _post_form(self, url: str, data: Mapping[str, str]) -> GrokOAuthTransportResponse:
        return self._request(
            "POST", url,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            data=data,
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        data: Mapping[str, str] | None = None,
    ) -> GrokOAuthTransportResponse:
        try:
            response = self._transport.request(method, url, headers=headers, data=data)
        except Exception:
            # Do not surface HTTP library text: it may echo a token or response payload.
            raise GrokAuthError("xAI OAuth network request failed.") from None
        if not isinstance(response, GrokOAuthTransportResponse):
            raise GrokAuthError("xAI OAuth transport response is invalid.")
        if response.status_code in {301, 302, 303, 307, 308}:
            raise GrokAuthError("xAI OAuth redirect was rejected.")
        if (
            isinstance(response.status_code, bool)
            or not isinstance(response.status_code, int)
            or not 100 <= response.status_code <= 599
            or not isinstance(response.body, bytes)
            or len(response.body) > _MAX_RESPONSE_BYTES
        ):
            raise GrokAuthError("xAI OAuth response is invalid.")
        return response


def _trusted_endpoint(value: object, allowed_paths: frozenset[str], label: str) -> str:
    if not isinstance(value, str):
        raise GrokAuthError(f"xAI OAuth {label} endpoint is unavailable.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise GrokAuthError(f"xAI OAuth {label} endpoint is invalid.") from None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "auth.x.ai"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.path not in allowed_paths
        or parsed.query
        or parsed.fragment
        or value != f"{AUTH_ISSUER}{parsed.path}"
    ):
        raise GrokAuthError(f"xAI OAuth {label} endpoint is not trusted.")
    return value


def _trusted_verification_uri(value: object) -> str:
    if not isinstance(value, str):
        raise GrokAuthError("xAI OAuth verification URI is invalid.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise GrokAuthError("xAI OAuth verification URI is invalid.") from None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "auth.x.ai"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or not parsed.path.startswith("/")
        or parsed.query
        or parsed.fragment
        or value != f"{AUTH_ISSUER}{parsed.path}"
    ):
        raise GrokAuthError("xAI OAuth verification URI is not trusted.")
    return value


def _json_object(body: bytes) -> dict[str, object]:
    if not isinstance(body, bytes) or not body or len(body) > _MAX_RESPONSE_BYTES:
        raise GrokAuthError("xAI OAuth response is invalid.")
    try:
        value = json.loads(body.decode("utf-8"), parse_constant=_reject_json_constant)
    except (ValueError, UnicodeError, TypeError):
        raise GrokAuthError("xAI OAuth response is not valid JSON.") from None
    if not isinstance(value, dict):
        raise GrokAuthError("xAI OAuth response must be an object.")
    return value


def _validate_record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "issuer", "access_token", "refresh_token",
        "account_fingerprint", "expires_at", "refresh_state",
    }:
        raise GrokAuthError("Grok OAuth Secret Service credential is invalid.")
    if (
        value.get("schema_version") != 1
        or value.get("issuer") != AUTH_ISSUER
        or value.get("refresh_state") not in {"ready", "unknown"}
        or not _is_fingerprint(value.get("account_fingerprint"))
    ):
        raise GrokAuthError("Grok OAuth Secret Service credential is invalid.")
    _nonblank_string(value.get("access_token"), max_length=65_536)
    _nonblank_string(value.get("refresh_token"), max_length=65_536)
    _parse_datetime(value.get("expires_at"))
    return dict(value)


def _validated_ready_record(value: Mapping[str, object]) -> dict[str, object]:
    record = _validate_record(dict(value))
    if record["refresh_state"] != "ready":
        raise GrokAuthError("Grok OAuth credential is unavailable after an unknown refresh outcome.")
    return record


def _parse_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise GrokAuthError("Grok OAuth credential expiry is invalid.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise GrokAuthError("Grok OAuth credential expiry is invalid.") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GrokAuthError("Grok OAuth credential expiry is invalid.")
    return parsed.astimezone(UTC)


def _positive_seconds(value: object, *, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise GrokAuthError("xAI OAuth duration is invalid.")
    seconds = float(value)
    if not 0 < seconds <= maximum:
        raise GrokAuthError("xAI OAuth duration is invalid.")
    return seconds


def _access_token_expiry(access_token: str) -> datetime | None:
    # OpenClaw's pinned xAI adapter uses the access-token exp claim only when
    # expires_in is absent; account identity is bound separately via userinfo.
    parts = access_token.split(".")
    if len(parts) != 3 or not parts[1]:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(
            base64.b64decode(payload.encode("ascii"), altchars=b"-_", validate=True).decode("utf-8"),
            parse_constant=_reject_json_constant,
        )
    except (ValueError, UnicodeError, TypeError):
        return None
    if not isinstance(claims, dict):
        return None
    expiry = claims.get("exp")
    if isinstance(expiry, bool) or not isinstance(expiry, (float, int)):
        return None
    seconds = float(expiry)
    if seconds <= 0:
        return None
    try:
        return datetime.fromtimestamp(seconds, UTC)
    except (OverflowError, OSError, ValueError):
        return None


def _nonblank_string(value: object, *, max_length: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or value.strip() != value:
        raise GrokAuthError("xAI OAuth response is missing a required value.")
    return value


def _is_fingerprint(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-standard JSON constant")
