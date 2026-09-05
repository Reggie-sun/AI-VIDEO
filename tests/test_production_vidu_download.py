"""Vidu authenticated result trust and pinned public HTTPS boundary."""

from io import BytesIO
import hashlib
import http.client
import socket
import ssl

import httpx
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.hashing import canonical_sha256
from ai_video.production.vidu import HttpxViduTransport, ViduTransportRequest, ViduVideoProvider
from ai_video.production.vidu_profile import ViduProviderProfile
from ai_video.production import vidu_download
from tests.test_production_vidu import _profile, _setup, _submitted, NOW, MP4, URL


def test_authenticated_task_profile_requires_no_prior_cdn():
    profile = _profile(result_trust="authenticated_task", result_origins=())
    assert profile.result_origins == ()
    assert profile.model_dump(mode="json")["result_trust"] == "authenticated_task"


def test_legacy_profile_serialization_and_hash_are_preserved():
    profile = _profile()
    original = {
        "origin": "https://api.vidu.cn",
        "result_origins": ["https://media.vidu.example"],
        "cost_upper_bound_microunits": 10_000_000,
        "pricing_observed_at": "2026-09-05T00:00:00Z",
        "pricing_expires_at": "2026-09-06T00:00:00Z",
        "max_download_bytes": 512 * 1024 * 1024,
    }
    assert profile.model_dump(mode="json") == original
    assert profile.pointer().profile_sha256 == canonical_sha256(original)


@pytest.mark.parametrize("mode,origins", [("fixed_origins", ()), ("authenticated_task", ("https://cdn.example",)), ("anything", ())])
def test_profile_rejects_ambiguous_or_implicit_trust(mode, origins):
    with pytest.raises(ValueError):
        _profile(result_trust=mode, result_origins=origins)


@pytest.mark.parametrize("mode", ["fixed_origins", "authenticated_task"])
def test_profile_roundtrip_preserves_exact_pointer(mode):
    profile = _profile(result_trust=mode, result_origins=() if mode == "authenticated_task" else ("https://cdn.example",))
    reopened = ViduProviderProfile.model_validate_json(profile.model_dump_json())
    assert reopened.result_trust == mode
    assert reopened.pointer() == profile.pointer()


class WireSocket:
    def __init__(self, response):
        self.response = response
        self.writes = []
        self.address = None
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, address):
        self.address = address

    def sendall(self, data):
        self.writes.append(bytes(data))

    def makefile(self, *args):
        return BytesIO(self.response)

    def close(self):
        self.closed = True


def _wire(monkeypatch, *, addresses=("8.8.8.8",), status=200, headers=b"", body=MP4, tls_error=False):
    state = {"dns": [], "sockets": [], "sni": [], "contexts": []}
    def resolve(host, port, **kwargs):
        state["dns"].append((host, port, kwargs))
        return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "",
                 (ip, port, 0, 0) if ":" in ip else (ip, port)) for ip in addresses]
    def make_socket(family, kind):
        response = (f"HTTP/1.1 {status} Result\r\nContent-Type: video/mp4\r\nContent-Length: {len(body)}\r\n".encode()
                    + headers + b"\r\n" + body)
        sock = WireSocket(response)
        state["sockets"].append(sock)
        return sock
    def wrap(context, sock, *, server_hostname):
        state["sni"].append(server_hostname)
        state["contexts"].append(context)
        if tls_error:
            raise ssl.SSLCertVerificationError("private URL should never leak")
        return sock
    monkeypatch.setattr(vidu_download.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(vidu_download.socket, "socket", make_socket)
    monkeypatch.setattr(vidu_download.ssl.SSLContext, "wrap_socket", wrap)
    return state


def test_media_wire_pins_dns_and_isolates_api_credentials_and_proxy(monkeypatch, caplog):
    state = _wire(monkeypatch)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    seen = []
    with httpx.Client(transport=httpx.MockTransport(lambda req: seen.append(req)),
                      auth=("user", "password"), headers={"Authorization": "CLIENT-SECRET"},
                      cookies={"private": "cookie"}) as client:
        transport = HttpxViduTransport(client=client)
        with transport.stream(ViduTransportRequest("GET", URL, {"accept": "video/mp4"})) as response:
            assert b"".join(response.iter_bytes()) == MP4
    assert not seen
    assert len(state["dns"]) == len(state["sockets"]) == 1
    sock = state["sockets"][0]
    assert sock.address == ("8.8.8.8", 443)
    assert sock.closed
    assert state["sni"] == ["media.vidu.example"]
    assert state["contexts"][0].check_hostname
    assert state["contexts"][0].verify_mode == ssl.CERT_REQUIRED
    wire = b"".join(sock.writes)
    assert wire == (b"GET /output.mp4?private=token HTTP/1.1\r\nHost: media.vidu.example\r\n"
                    b"Accept: video/mp4\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n")
    assert URL not in caplog.text


@pytest.mark.parametrize("url", [
    "http://cdn.example/v", "https://user:secret@cdn.example/v", "https://cdn.example:444/v",
    "https://cdn.example/v#", "https://cdn.example/v#fragment", "https://cdn.example/v\r\n",
    "https://cdn.example\\@evil.example/v", "https://cdn.example./v", "https://local/v",
    "https://127.0.0.1/v", "https://10.0.0.1/v", "https://169.254.169.254/v",
    "https://[::1]/v", "https://[::ffff:8.8.8.8]/v", "https://[2002:0808:0808::1]/v",
    "https://cdn%2eexample/v", "https://cdn.example:/v", "https://cdn.example:0443/v",
    "https://cdn.example//video.mp4",
])
def test_bad_locator_rejected_before_dns(monkeypatch, url):
    state = _wire(monkeypatch)
    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(url, timeout_seconds=1):
            pytest.fail("unsafe locator accepted")
    assert not state["dns"] and not state["sockets"]


def test_empty_query_delimiter_is_preserved_on_wire(monkeypatch):
    state = _wire(monkeypatch)
    with vidu_download.stream_public_video("https://cdn.example/v?", timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    assert state["sockets"][0].writes[0].startswith(b"GET /v? HTTP/1.1\r\n")


def test_global_http_debug_does_not_print_signed_locator(monkeypatch, capsys):
    _wire(monkeypatch)
    monkeypatch.setattr(http.client.HTTPConnection, "debuglevel", 1)
    with vidu_download.stream_public_video(URL, timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("addresses", [(), ("127.0.0.1",), ("10.0.0.1",), ("169.254.169.254",),
    ("100.64.0.1",), ("198.18.0.1",), ("192.0.2.1",), ("224.0.0.1",), ("::1",), ("fc00::1",),
    ("fe80::1",), ("::ffff:8.8.8.8",), ("64:ff9b::a00:1",), ("8.8.8.8", "10.0.0.1"),
])
def test_all_dns_answers_must_be_public_before_any_connection(monkeypatch, addresses):
    state = _wire(monkeypatch, addresses=addresses)
    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(URL, timeout_seconds=1):
            pytest.fail("unsafe address accepted")
    assert len(state["dns"]) == 1 and not state["sockets"]


def test_native_ipv6_address_is_pinned_with_original_sni(monkeypatch):
    state = _wire(monkeypatch, addresses=("2606:4700:4700::1111",))
    with vidu_download.stream_public_video(URL, timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    assert state["sockets"][0].address == ("2606:4700:4700::1111", 443, 0, 0)
    assert state["sni"] == ["media.vidu.example"]


@pytest.mark.parametrize("status,headers", [(302, b"Location: https://127.0.0.1/private\r\n"),
                                            (200, b"Content-Encoding: gzip\r\n")])
def test_redirects_and_encoded_bodies_are_not_followed_or_consumed(monkeypatch, status, headers):
    state = _wire(monkeypatch, status=status, headers=headers)
    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(URL, timeout_seconds=1):
            pytest.fail("bad response exposed")
    assert len(state["sockets"]) == len(state["dns"]) == 1
    assert state["sockets"][0].closed


def test_tls_failure_sends_no_http_and_closes_socket(monkeypatch):
    state = _wire(monkeypatch, tls_error=True)
    with pytest.raises(AiVideoError) as exc:
        with vidu_download.stream_public_video(URL, timeout_seconds=1):
            pytest.fail("invalid certificate accepted")
    assert "private URL" not in str(exc.value)
    assert not state["sockets"][0].writes and state["sockets"][0].closed


def test_consumer_failure_closes_socket_without_retry(monkeypatch):
    state = _wire(monkeypatch)
    with pytest.raises(RuntimeError):
        with vidu_download.stream_public_video(URL, timeout_seconds=1):
            raise RuntimeError("sink failed")
    assert len(state["sockets"]) == 1 and state["sockets"][0].closed


@pytest.mark.parametrize("timeout", [None, 0, -1, float("inf"), float("nan")])
def test_unbounded_or_invalid_timeout_rejected_before_dns(monkeypatch, timeout):
    state = _wire(monkeypatch)
    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(URL, timeout_seconds=timeout):
            pytest.fail("unbounded timeout")
    assert not state["dns"]


@pytest.mark.parametrize("method,headers,body", [("POST", {"accept": "video/mp4"}, b""),
    ("GET", {"accept": "video/mp4", "authorization": "SECRET"}, b""),
    ("GET", {"accept": "video/mp4"}, b"payload")])
def test_media_transport_rejects_extra_egress_before_dns(monkeypatch, method, headers, body):
    state = _wire(monkeypatch)
    with httpx.Client(transport=httpx.MockTransport(lambda _: pytest.fail("API client used"))) as client:
        with pytest.raises(AiVideoError):
            with HttpxViduTransport(client=client).stream(ViduTransportRequest(method, URL, headers, body)):
                pytest.fail("unexpected egress")
    assert not state["dns"]


def test_authenticated_result_fetch_uses_requeried_creation_and_sealed_materialization(monkeypatch):
    state = _wire(monkeypatch)
    provider, fake, args = _setup(profile=_profile(result_trust="authenticated_task", result_origins=()))
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    refreshed = "https://new-cdn.example/video.mp4?signature=SECRET"
    fake.query["creations"][0]["url"] = refreshed
    def api(request):
        assert str(request.url) == "https://api.vidu.cn/ent/v2/tasks/task-1/creations"
        assert request.headers["authorization"] == "Token PRIVATE-KEY"
        return httpx.Response(200, json=fake.query)
    with httpx.Client(transport=httpx.MockTransport(api)) as client:
        provider._transport = HttpxViduTransport(client=client)
        sink = BytesIO()
        fetched = provider.fetch(submission, receipt, observation, sink)
    proof = fetched.remote_materialization
    assert sink.getvalue() == MP4
    assert proof.remote_origin == "https://new-cdn.example"
    assert proof.remote_locator_sha256 == hashlib.sha256(refreshed.encode()).hexdigest()
    assert proof.artifact_sha256 == hashlib.sha256(MP4).hexdigest()
    assert "SECRET" not in fetched.model_dump_json()
    assert state["sni"] == ["new-cdn.example"]


@pytest.mark.parametrize("change", ["task", "model", "creation", "profile"])
def test_dynamic_fetch_rejects_changed_identity_before_download(change):
    profile = _profile(result_trust="authenticated_task", result_origins=())
    provider, fake, args = _setup(profile=profile)
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    if change == "profile":
        provider = ViduVideoProvider(profile=_profile(), transport=fake, credential=lambda: "key", now=lambda: NOW)
    elif change == "creation":
        fake.query["creations"][0]["id"] = "changed"
    else:
        fake.query["task_id" if change == "task" else "model"] = "changed"
    before = len(fake.calls)
    with pytest.raises(AiVideoError):
        provider.fetch(submission, receipt, observation, BytesIO())
    assert not fake.downloads
    if change == "profile":
        assert len(fake.calls) == before


@pytest.mark.parametrize("failure", ["limit", "truncated", "sink"])
def test_pinned_fetch_failure_never_emits_receipt_and_closes_socket(monkeypatch, failure):
    state = _wire(monkeypatch)
    profile = _profile(result_trust="authenticated_task", result_origins=(),
                       max_download_bytes=12 if failure == "limit" else 1024)
    provider, fake, args = _setup(profile=profile)
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    class FailingSink(BytesIO):
        def write(self, chunk):
            raise OSError("disk full")
    socket_factory = vidu_download.socket.socket
    def make_socket(*args):
        sock = socket_factory(*args)
        if failure == "truncated":
            sock.response = sock.response[:-1]
        return sock
    monkeypatch.setattr(vidu_download.socket, "socket", make_socket)
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=fake.query))) as client:
        provider._transport = HttpxViduTransport(client=client)
        with pytest.raises(AiVideoError):
            provider.fetch(submission, receipt, observation, FailingSink() if failure == "sink" else BytesIO())
    assert len(state["sockets"]) == 1 and state["sockets"][0].closed
