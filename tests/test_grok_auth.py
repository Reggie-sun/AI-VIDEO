from __future__ import annotations

import base64
import json
import subprocess
import sys
import threading
from datetime import UTC, datetime, timedelta

import pytest

from ai_video.production.grok_auth import (
    GrokAuthError,
    HttpxGrokOAuthTransport,
    GrokOAuthManager,
    GrokOAuthTransportResponse,
    GrokTokenStore,
)


AUTH_ORIGIN = "https://auth.x.ai"
DEVICE_CODE = "device-code-secret"
ACCESS_TOKEN = "access-token-secret"
REFRESH_TOKEN = "refresh-token-secret"
ACCOUNT_SUB = "xai-account-123"


@pytest.fixture(autouse=True)
def private_auth_runtime(monkeypatch, tmp_path):
    from ai_video.production import _grok_auth_lock
    tmp_path.chmod(0o700)
    monkeypatch.setattr(_grok_auth_lock, "_runtime_directory", lambda: tmp_path)


class FakeOAuthTransport:
    def __init__(self):
        self.calls: list[tuple[str, str, dict[str, str], dict[str, str]]] = []
        self.device_pending = 0
        self.device_slow_down = 0
        self.refresh_error: BaseException | None = None
        self.refresh_response = {
            "access_token": "refreshed-access-token",
            "refresh_token": "rotated-refresh-token",
            "expires_in": 3600,
        }
        self.account_sub = ACCOUNT_SUB

    def request(self, method, url, *, headers=None, data=None):
        fields = dict(data or {})
        self.calls.append((method, url, dict(headers or {}), fields))
        if method == "GET" and url == f"{AUTH_ORIGIN}/.well-known/openid-configuration":
            body = {
                "issuer": AUTH_ORIGIN,
                "device_authorization_endpoint": f"{AUTH_ORIGIN}/oauth/device/code",
                "token_endpoint": f"{AUTH_ORIGIN}/oauth/token",
                "userinfo_endpoint": f"{AUTH_ORIGIN}/oauth/userinfo",
            }
            return _response(200, body)
        if method == "POST" and url == f"{AUTH_ORIGIN}/oauth/device/code":
            return _response(200, {
                "device_code": DEVICE_CODE,
                "user_code": "ABCD-EFGH",
                "verification_uri": f"{AUTH_ORIGIN}/activate",
                "verification_uri_complete": (
                    f"{AUTH_ORIGIN}/activate?device_code={DEVICE_CODE}"
                ),
                "expires_in": 300,
                "interval": 1,
            })
        if method == "POST" and url == f"{AUTH_ORIGIN}/oauth/token":
            if fields.get("grant_type") == "urn:ietf:params:oauth:grant-type:device_code":
                assert fields.get("device_code") == DEVICE_CODE
                if self.device_pending:
                    self.device_pending -= 1
                    return _response(400, {"error": "authorization_pending"})
                if self.device_slow_down:
                    self.device_slow_down -= 1
                    return _response(400, {"error": "slow_down"})
                return _response(200, {
                    "access_token": ACCESS_TOKEN,
                    "refresh_token": REFRESH_TOKEN,
                    "expires_in": 3600,
                })
            if fields.get("grant_type") == "refresh_token":
                if self.refresh_error is not None:
                    error = self.refresh_error
                    self.refresh_error = None
                    raise error
                return _response(200, self.refresh_response)
        if method == "GET" and url == f"{AUTH_ORIGIN}/oauth/userinfo":
            assert headers.get("Authorization") == f"Bearer {ACCESS_TOKEN}" or headers.get(
                "Authorization"
            ) == "Bearer refreshed-access-token"
            return _response(200, {"sub": self.account_sub})
        raise AssertionError(f"unexpected OAuth request: {method} {url}")


class FakeSecretService:
    def __init__(self):
        self.value: bytes | None = None
        self.calls: list[tuple[list[str], bytes]] = []

    def run(self, argv, *, input=None, capture_output, timeout, check):
        self.calls.append((list(argv), input or b""))
        if argv[:2] == ["secret-tool", "lookup"]:
            if self.value is None:
                return subprocess.CompletedProcess(argv, 1, b"", b"")
            return subprocess.CompletedProcess(argv, 0, self.value + b"\n", b"")
        if argv[:2] == ["secret-tool", "store"]:
            self.value = input
            return subprocess.CompletedProcess(argv, 0, b"", b"")
        raise AssertionError(f"unexpected Secret Service command: {argv[:2]}")


def _response(status_code: int, payload: dict[str, object], *, headers=None):
    return GrokOAuthTransportResponse(
        status_code=status_code,
        headers=headers or {"content-type": "application/json"},
        body=json.dumps(payload).encode("utf-8"),
    )


def _manager(transport=None, *, now=None, sleep=None, secret_service=None):
    store = GrokTokenStore(runner=(secret_service or FakeSecretService()).run)
    return GrokOAuthManager(
        store=store,
        transport=transport or FakeOAuthTransport(),
        now=now or (lambda: datetime(2026, 10, 12, tzinfo=UTC)),
        sleep=sleep or (lambda _seconds: None),
    )


@pytest.mark.parametrize("other_command", ["refresh", "login"])
def test_concurrent_refresh_cannot_exchange_a_token_after_an_unknown_outcome(other_command):
    service = FakeSecretService()
    _manager(secret_service=service).login()
    started, finished = threading.Event(), threading.Event()
    errors = []

    class PausedDiscovery(FakeOAuthTransport):
        def request(self, method, url, **kwargs):
            if url.endswith("openid-configuration"):
                started.set()
                assert finished.wait(3)
            return super().request(method, url, **kwargs)

    first = _manager(PausedDiscovery(), secret_service=service)
    transport = FakeOAuthTransport()
    transport.refresh_error = TimeoutError("synthetic lost response")
    second = _manager(transport, secret_service=service)

    def refresh_first():
        try:
            first.refresh()
        except Exception as error:
            errors.append(type(error).__name__)

    thread = threading.Thread(target=refresh_first)
    thread.start()
    try:
        assert started.wait(3)
        with pytest.raises(GrokAuthError, match="busy"):
            getattr(second, other_command)()
    finally:
        finished.set()
        thread.join(3)
    assert not thread.is_alive()
    assert errors == []
    assert transport.calls == []
    assert first.status().state == "ready"


def test_auth_mutation_lock_is_cross_process_and_released_on_failure(tmp_path):
    from pathlib import Path
    from ai_video.production import _grok_auth_lock
    from ai_video.production._grok_auth_lock import grok_auth_mutation_lock
    script = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from ai_video.production import _grok_auth_lock as owner
owner._runtime_directory = lambda: Path(sys.argv[1])
try:
    with owner.grok_auth_mutation_lock():
        print("acquired")
except owner.GrokAuthLockError:
    print("busy")
'''
    def child():
        source_root = Path(_grok_auth_lock.__file__).parents[2]
        result = subprocess.run([sys.executable, "-c", script, str(tmp_path), str(source_root)],
            capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip()
    with pytest.raises(ValueError):
        with grok_auth_mutation_lock():
            assert child() == "busy"
            raise ValueError("synthetic mutation failure")
    assert child() == "acquired"
    assert (tmp_path / "ai-video-grok-oauth.lock").read_bytes() == b""


def test_auth_lock_rejects_symlink_without_modifying_its_target(tmp_path):
    from ai_video.production._grok_auth_lock import GrokAuthLockError, grok_auth_mutation_lock
    target = tmp_path / "unrelated"
    target.write_bytes(b"preserved")
    (tmp_path / "ai-video-grok-oauth.lock").symlink_to(target)
    with pytest.raises(GrokAuthLockError):
        with grok_auth_mutation_lock():
            pytest.fail("symlink cannot supply auth mutation authority")
    assert target.read_bytes() == b"preserved"


def test_cli_interruption_keeps_unknown_refresh_and_requires_explicit_login(monkeypatch, capsys):
    from scripts import grok_auth as cli
    transport = FakeOAuthTransport()
    manager = _manager(transport)
    manager.login()
    transport.refresh_error = KeyboardInterrupt()
    monkeypatch.setattr(cli, "_manager", lambda: manager)
    try:
        result = cli.main(["refresh"])
    except KeyboardInterrupt:
        pytest.fail("authentication cancellation escaped the CLI")
    assert result == 130
    output = capsys.readouterr().out
    assert json.loads(output)["status"] == "stopped"
    assert all(secret not in output for secret in (ACCESS_TOKEN, REFRESH_TOKEN, DEVICE_CODE))
    assert manager.status().state == "refresh_unknown"
    prior = len(transport.calls)
    with pytest.raises(GrokAuthError):
        manager.refresh()
    assert len(transport.calls) == prior
    assert manager.login().state == "ready"


def test_device_login_uses_trusted_oauth_endpoints_and_hides_device_code():
    transport = FakeOAuthTransport()
    secret_service = FakeSecretService()
    transport.device_pending = 1
    transport.device_slow_down = 1
    waits = []
    manager = _manager(transport, sleep=waits.append, secret_service=secret_service)
    displayed = []

    status = manager.login(on_device_code=lambda uri, code: displayed.append((uri, code)))

    assert displayed == [(f"{AUTH_ORIGIN}/activate", "ABCD-EFGH")]
    assert waits == [1.0, 6.0]
    assert status.state == "ready"
    assert len(status.account_fingerprint) == 64
    assert status.private_reference == "GROK_OAUTH"
    assert all(call[1].startswith(AUTH_ORIGIN + "/") for call in transport.calls)
    assert transport.calls[0][0:2] == (
        "GET", f"{AUTH_ORIGIN}/.well-known/openid-configuration"
    )
    assert transport.calls[1][2]["Content-Type"] == "application/x-www-form-urlencoded"
    assert transport.calls[1][3] == {
        "client_id": "b1a00492-073a-47ea-816f-4c329264a828",
        "scope": "openid profile email offline_access grok-cli:access api:access",
    }
    assert json.loads(secret_service.value)["account_fingerprint"] == status.account_fingerprint
    assert all(ACCESS_TOKEN not in argv and REFRESH_TOKEN not in argv for argv, _ in secret_service.calls)
    assert any(payload and ACCESS_TOKEN in payload.decode() for _, payload in secret_service.calls)
    assert DEVICE_CODE not in repr(status)
    assert ACCESS_TOKEN not in repr(status)
    assert REFRESH_TOKEN not in repr(status)


def test_credential_supplier_checks_identity_expiry_and_never_refreshes():
    now = [datetime(2026, 10, 12, tzinfo=UTC)]
    transport = FakeOAuthTransport()
    manager = _manager(transport, now=lambda: now[0])
    status = manager.login()
    calls_before_supplier = len(transport.calls)

    supplier = manager.credential_supplier(status.account_fingerprint)
    assert supplier() == ACCESS_TOKEN
    assert len(transport.calls) == calls_before_supplier
    with pytest.raises(GrokAuthError, match="account does not match"):
        manager.credential_supplier("0" * 64)()

    now[0] += timedelta(hours=1)
    with pytest.raises(GrokAuthError, match="expired"):
        supplier()
    assert len(transport.calls) == calls_before_supplier


def test_refresh_rotation_updates_token_and_preserves_same_account():
    transport = FakeOAuthTransport()
    secret_service = FakeSecretService()
    manager = _manager(transport, secret_service=secret_service)
    before = manager.login()
    transport.refresh_response = {
        "access_token": "refreshed-access-token",
        "refresh_token": "rotated-refresh-token",
        "expires_in": 7200,
    }

    after = manager.refresh()

    assert after.account_fingerprint == before.account_fingerprint
    assert after.expires_at == datetime(2026, 10, 12, 2, tzinfo=UTC)
    assert transport.calls[-2][3] == {
        "grant_type": "refresh_token",
        "client_id": "b1a00492-073a-47ea-816f-4c329264a828",
        "refresh_token": REFRESH_TOKEN,
    }
    assert manager.credential_supplier(after.account_fingerprint)() == "refreshed-access-token"
    saved = json.loads(secret_service.value)
    assert saved["refresh_token"] == "rotated-refresh-token"


def test_missing_expires_in_uses_only_access_token_expiry_claim():
    now = datetime(2026, 10, 12, tzinfo=UTC)
    claim = json.dumps({"exp": int((now + timedelta(minutes=10)).timestamp())}).encode()
    encoded = base64.urlsafe_b64encode(claim).rstrip(b"=").decode()
    token = f"header.{encoded}.signature"
    manager = _manager(now=lambda: now)

    _access, _refresh, expires_at = manager._read_token_payload(
        {"access_token": token, "refresh_token": REFRESH_TOKEN},
        require_refresh_token=True,
    )

    assert expires_at == now + timedelta(minutes=10)


def test_refresh_transport_loss_persists_unknown_and_prevents_retry():
    transport = FakeOAuthTransport()
    secret_service = FakeSecretService()
    manager = _manager(transport, secret_service=secret_service)
    status = manager.login()
    transport.refresh_error = TimeoutError("private token data must not surface")

    with pytest.raises(GrokAuthError, match="outcome is unknown") as raised:
        manager.refresh()

    assert "private token data" not in str(raised.value)
    unknown = manager.status()
    assert unknown.state == "refresh_unknown"
    calls_after_first_refresh = len(transport.calls)
    with pytest.raises(GrokAuthError, match="re-login"):
        manager.refresh()
    with pytest.raises(GrokAuthError, match="unavailable"):
        manager.credential_supplier(status.account_fingerprint)()
    assert len(transport.calls) == calls_after_first_refresh
    saved = json.loads(secret_service.value)
    assert saved["refresh_state"] == "unknown"


def test_refresh_account_mismatch_keeps_unknown_marker():
    transport = FakeOAuthTransport()
    secret_service = FakeSecretService()
    manager = _manager(transport, secret_service=secret_service)
    status = manager.login()
    transport.account_sub = "different-account"

    with pytest.raises(GrokAuthError, match="outcome is unknown"):
        manager.refresh()

    assert manager.status().state == "refresh_unknown"
    with pytest.raises(GrokAuthError, match="unknown refresh outcome"):
        manager.credential_supplier(status.account_fingerprint)()
    assert json.loads(secret_service.value)["refresh_state"] == "unknown"


def test_device_exchange_transport_loss_is_not_retried_or_stored():
    class LostDeviceTokenResponse(FakeOAuthTransport):
        def request(self, method, url, *, headers=None, data=None):
            fields = dict(data or {})
            if method == "POST" and fields.get("grant_type") == (
                "urn:ietf:params:oauth:grant-type:device_code"
            ):
                self.calls.append((method, url, dict(headers or {}), fields))
                raise TimeoutError("access_token=must-not-leak")
            return super().request(method, url, headers=headers, data=data)

    transport = LostDeviceTokenResponse()
    secret_service = FakeSecretService()
    manager = _manager(transport, secret_service=secret_service)
    with pytest.raises(GrokAuthError, match="network request failed") as raised:
        manager.login()
    assert "must-not-leak" not in str(raised.value)
    assert sum(
        call[3].get("grant_type") == "urn:ietf:params:oauth:grant-type:device_code"
        for call in transport.calls
    ) == 1
    assert secret_service.value is None


def test_untrusted_discovery_endpoint_and_redirect_are_rejected():
    class BadDiscoveryTransport(FakeOAuthTransport):
        def request(self, method, url, *, headers=None, data=None):
            if method == "GET" and url == f"{AUTH_ORIGIN}/.well-known/openid-configuration":
                return _response(200, {
                    "issuer": AUTH_ORIGIN,
                    "device_authorization_endpoint": "https://evil.example/device",
                    "token_endpoint": f"{AUTH_ORIGIN}/oauth/token",
                    "userinfo_endpoint": f"{AUTH_ORIGIN}/oauth/userinfo",
                })
            return super().request(method, url, headers=headers, data=data)

    manager = _manager(BadDiscoveryTransport())
    with pytest.raises(GrokAuthError, match="endpoint is not trusted"):
        manager.login()

    class RedirectTransport(FakeOAuthTransport):
        def request(self, method, url, *, headers=None, data=None):
            if method == "GET" and url == f"{AUTH_ORIGIN}/.well-known/openid-configuration":
                return _response(302, {}, headers={"location": "https://evil.example/"})
            return super().request(method, url, headers=headers, data=data)

    manager = _manager(RedirectTransport())
    with pytest.raises(GrokAuthError, match="redirect was rejected"):
        manager.login()


def test_httpx_oauth_transport_does_not_follow_redirects():
    import httpx

    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(302, headers={"location": "https://evil.example/"})

    client = httpx.Client(transport=httpx.MockTransport(respond), follow_redirects=True)
    transport = HttpxGrokOAuthTransport(client=client)
    response = transport.request("GET", f"{AUTH_ORIGIN}/.well-known/openid-configuration")

    assert response.status_code == 302
    assert len(requests) == 1
    client.close()


def test_store_uses_only_exact_secret_service_reference_and_sanitizes_errors():
    secret_service = FakeSecretService()
    store = GrokTokenStore(runner=secret_service.run)
    store.save({
        "schema_version": 1,
        "issuer": AUTH_ORIGIN,
        "access_token": ACCESS_TOKEN,
        "refresh_token": REFRESH_TOKEN,
        "account_fingerprint": "0" * 64,
        "expires_at": "2026-10-12T01:00:00+00:00",
        "refresh_state": "ready",
    })
    assert [argv for argv, _ in secret_service.calls] == [
        ["secret-tool", "store", "--label=AI-VIDEO Grok OAuth", "application", "ai-video",
         "provider", "grok", "credential", "GROK_OAUTH"]
    ]
    assert ACCESS_TOKEN not in secret_service.calls[0][0]
    assert store.load()["access_token"] == ACCESS_TOKEN

    class FailedSecretService:
        def run(self, argv, **kwargs):
            return subprocess.CompletedProcess(argv, 1, b"", b"secret data must not leak")

    with pytest.raises(GrokAuthError, match="Secret Service") as raised:
        GrokTokenStore(runner=FailedSecretService().run).load()
    assert "secret data" not in str(raised.value)


def test_cli_login_and_status_only_print_public_auth_metadata(monkeypatch, capsys):
    from scripts import grok_auth as cli

    manager = _manager()
    monkeypatch.setattr(cli, "_manager", lambda: manager)

    assert cli.main(["login"]) == 0
    login_output = capsys.readouterr().out
    assert f"Verification URI: {AUTH_ORIGIN}/activate" in login_output
    assert "User code: ABCD-EFGH" in login_output
    for secret in (DEVICE_CODE, ACCESS_TOKEN, REFRESH_TOKEN):
        assert secret not in login_output

    assert cli.main(["status"]) == 0
    status_output = capsys.readouterr().out
    assert "ready" in status_output
    assert "account_fingerprint" in status_output
    for secret in (DEVICE_CODE, ACCESS_TOKEN, REFRESH_TOKEN):
        assert secret not in status_output


def test_cli_refresh_failure_is_sanitized(monkeypatch, capsys):
    from scripts import grok_auth as cli

    transport = FakeOAuthTransport()
    manager = _manager(transport)
    manager.login()
    transport.refresh_error = RuntimeError("refresh_token=secret-value")
    monkeypatch.setattr(cli, "_manager", lambda: manager)

    assert cli.main(["refresh"]) == 1
    output = capsys.readouterr().out
    assert "unknown" in output
    assert "secret-value" not in output
