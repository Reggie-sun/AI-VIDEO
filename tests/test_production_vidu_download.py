"""Credential-free result transfers and exact post-download media evidence."""

from io import BytesIO
import hashlib
import http.client
import socket
import ssl
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.hashing import canonical_sha256
from ai_video.production.remote_media import RemoteMediaMaterializationReceipt
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


@pytest.mark.parametrize("mode,origins", [("anything", ())])
def test_profile_rejects_ambiguous_or_implicit_trust(mode, origins):
    with pytest.raises(ValueError):
        _profile(result_trust=mode, result_origins=origins)


def test_fixed_origin_list_is_legacy_metadata_and_may_be_empty():
    profile = _profile(result_trust="fixed_origins", result_origins=())
    assert profile.result_origins == ()


def _materialization(origin, transport_kind):
    return RemoteMediaMaterializationReceipt.create(
        transport_kind=transport_kind,
        provider_kind="vidu",
        model_id="viduq3-pro",
        submission_fingerprint="a" * 64,
        paid_submit_receipt_fingerprint="b" * 64,
        provider_file_id="creation-1",
        remote_origin=origin,
        remote_locator_sha256="c" * 64,
        artifact_sha256="d" * 64,
        artifact_size_bytes=128,
        artifact_mime_type="video/mp4",
        accessibility_verification="exact_get",
        verified_at=datetime(2026, 10, 21, tzinfo=UTC),
    )


def test_materialization_receipt_accepts_canonical_http_and_preserves_https_shape():
    https_receipt = _materialization("https://cdn.example", "provider_output_https")
    assert RemoteMediaMaterializationReceipt.model_validate_json(https_receipt.model_dump_json()) == https_receipt
    assert https_receipt.model_dump(mode="json")["transport_kind"] == "provider_output_https"
    http_receipt = _materialization("http://127.0.0.1:8080", "provider_output_http")
    assert http_receipt.remote_origin == "http://127.0.0.1:8080"
    with pytest.raises(ValidationError):
        _materialization("http://cdn.example", "provider_output_https")
    with pytest.raises(ValidationError):
        _materialization("https://cdn.example", "provider_output_http")
    with pytest.raises(ValidationError):
        _materialization("http://cdn.example:80", "provider_output_http")


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

    def setsockopt(self, *args):
        pass

    def connect(self, address):
        self.address = address

    def sendall(self, data):
        self.writes.append(bytes(data))

    def makefile(self, *args):
        return BytesIO(self.response)

    def close(self):
        self.closed = True


def _wire(monkeypatch, *, addresses=("8.8.8.8",), status=200, headers=b"", body=MP4,
          tls_error=False, responses=None):
    state = {"dns": [], "sockets": [], "sni": [], "contexts": []}
    def resolve(host, port, *args, **kwargs):
        state["dns"].append((host, port, args, kwargs))
        return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "",
                 (ip, port, 0, 0) if ":" in ip else (ip, port)) for ip in addresses]
    def make_socket(family, kind, protocol=0):
        if responses:
            spec = responses.pop(0)
            response_status = spec.get("status", 200)
            response_headers = spec.get("headers", b"")
            response_body = spec.get("body", MP4)
            content_type = spec.get("content_type", "video/mp4")
        else:
            response_status, response_headers, response_body, content_type = status, headers, body, "video/mp4"
        response = (f"HTTP/1.1 {response_status} Result\r\nContent-Type: {content_type}\r\nContent-Length: {len(response_body)}\r\n".encode()
                    + response_headers + b"\r\n" + response_body)
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


def test_media_wire_isolates_api_credentials_and_proxy(monkeypatch, caplog):
    state = _wire(monkeypatch)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    seen = []
    with httpx.Client(transport=httpx.MockTransport(lambda req: seen.append(req)),
                      auth=("user", "password"), headers={"Authorization": "CLIENT-SECRET"},
                      cookies={"private": "cookie"}) as client:
        transport = HttpxViduTransport(client=client)
        with transport.stream(ViduTransportRequest("GET", URL, {"accept": "*/*"})) as response:
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
    assert wire.startswith(b"GET /output.mp4?private=token HTTP/1.1\r\n")
    assert b"Host: media.vidu.example\r\n" in wire
    assert b"Accept: */*\r\n" in wire
    assert b"Accept-Encoding: identity\r\n" in wire
    assert b"Connection: close\r\n" in wire
    assert b"Authorization:" not in wire and b"Cookie:" not in wire
    assert URL not in caplog.text


@pytest.mark.parametrize("url", [
    "ftp://cdn.example/v", "https://user:secret@cdn.example/v",
    "https://cdn.example/v\r\n", "https://cdn.example\\@evil.example/v",
    "https://cdn.example:/v", "https://cdn.example:70000/v", "https:///v",
])
def test_invalid_locator_rejected_before_dns(monkeypatch, url):
    state = _wire(monkeypatch)
    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(url, timeout_seconds=1):
            pytest.fail("invalid locator accepted")
    assert not state["dns"] and not state["sockets"]


def test_empty_query_delimiter_is_preserved_on_wire(monkeypatch):
    state = _wire(monkeypatch)
    with vidu_download.stream_public_video("https://cdn.example/v?", timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    assert state["sockets"][0].writes[0].startswith(b"GET /v? HTTP/1.1\r\n")


@pytest.mark.parametrize(
    ("url", "expected_host", "expected_target"),
    [
        ("https://café.example/片段?q=值#client-fragment", "xn--caf-dma.example", "/%E7%89%87%E6%AE%B5?q=%E5%80%BC"),
        ("https://cdn_stage.example/video.mp4", "cdn_stage.example", "/video.mp4"),
    ],
)
def test_unicode_and_reg_name_locators_are_normalized_for_http(monkeypatch, url, expected_host, expected_target):
    state = _wire(monkeypatch)
    locator = vidu_download.parse_result_url(url)
    assert locator.hostname == expected_host
    assert locator.origin == f"https://{expected_host}"
    with vidu_download.stream_public_video(url, timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    wire = b"".join(state["sockets"][0].writes)
    assert wire.startswith(f"GET {expected_target} HTTP/1.1\r\n".encode())
    assert f"Host: {expected_host}\r\n".encode() in wire


def test_global_http_debug_does_not_print_signed_locator(monkeypatch, capsys):
    _wire(monkeypatch)
    monkeypatch.setattr(http.client.HTTPConnection, "debuglevel", 1)
    with vidu_download.stream_public_video(URL, timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_private_ip_http_destination_and_alternate_port_are_allowed(monkeypatch):
    state = _wire(monkeypatch, addresses=("127.0.0.1",))
    url = "http://127.0.0.1:8080/video.mp4?token=private"
    locator = vidu_download.parse_result_url(url)
    assert locator.origin == "http://127.0.0.1:8080"
    with vidu_download.stream_public_video(url, timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    assert state["dns"] == [("127.0.0.1", 8080, (0, socket.SOCK_STREAM), {})]
    assert state["sockets"][0].address == ("127.0.0.1", 8080)
    assert state["sni"] == []


def test_https_ipv6_keeps_original_sni_and_uses_alternate_port(monkeypatch):
    state = _wire(monkeypatch, addresses=("2606:4700:4700::1111",))
    with vidu_download.stream_public_video("https://[2606:4700:4700::1111]:8443/v", timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
    assert state["sockets"][0].address == ("2606:4700:4700::1111", 8443, 0, 0)
    assert state["sni"] == ["2606:4700:4700::1111"]


def test_explicit_resolver_is_used_without_ambient_dns_fallback(monkeypatch):
    state = _wire(monkeypatch, addresses=("198.18.0.24",))
    resolver_calls = []

    def resolver(host, port, **kwargs):
        resolver_calls.append((host, port, kwargs))
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "",
                 ("140.206.110.62", port))]

    with vidu_download.stream_public_video(URL, timeout_seconds=1,
                                           download_resolver=resolver) as response:
        assert b"".join(response.iter_bytes()) == MP4

    assert resolver_calls == [("media.vidu.example", 443,
                               {"type": socket.SOCK_STREAM, "proto": socket.IPPROTO_TCP})]
    assert not state["dns"]
    assert state["sockets"][0].address == ("140.206.110.62", 443)
    assert state["sni"] == ["media.vidu.example"]
    assert b"Authorization" not in b"".join(state["sockets"][0].writes)


@pytest.mark.parametrize("answer", [
    (),
    ((socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 80)),),
    ((socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("8.8.8.8", 443)),),
    ((socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "", ("8.8.8.8", 443)),),
    ((socket.AF_INET, socket.SOCK_STREAM),),
    (None,),
])
def test_explicit_resolver_invalid_answers_fail_without_ambient_fallback(monkeypatch, answer):
    state = _wire(monkeypatch, addresses=("8.8.8.8",))
    resolver_calls = []

    def resolver(host, port, **kwargs):
        resolver_calls.append((host, port, kwargs))
        return answer

    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(URL, timeout_seconds=1,
                                               download_resolver=resolver):
            pytest.fail("invalid resolver answer accepted")
    assert len(resolver_calls) == 1
    assert not state["dns"] and not state["sockets"]


def test_explicit_resolver_error_fails_closed_without_ambient_fallback(monkeypatch):
    state = _wire(monkeypatch, addresses=("8.8.8.8",))

    def resolver(host, port, **kwargs):
        raise socket.gaierror("private signed locator must not leak")

    with pytest.raises(AiVideoError) as error:
        with vidu_download.stream_public_video(URL, timeout_seconds=1,
                                               download_resolver=resolver):
            pytest.fail("resolver failure accepted")
    assert "private signed locator" not in str(error.value)
    assert not state["dns"] and not state["sockets"]


def test_cross_host_redirect_is_followed_without_forwarding_credentials(monkeypatch):
    state = _wire(monkeypatch, addresses=("10.0.0.7",), responses=[
        {"status": 302, "headers": b"Location: https://other.example:8443/final.mp4?signature=second\r\n", "body": b""},
        {"status": 200, "headers": b"Set-Cookie: session=server-cookie\r\n", "body": MP4, "content_type": "text/plain"},
    ])
    with vidu_download.stream_public_video("http://first.example/start?signature=first", timeout_seconds=1) as response:
        assert b"".join(response.iter_bytes()) == MP4
        assert response.headers["Content-Type"] == "text/plain"
    assert [entry[:2] for entry in state["dns"]] == [("first.example", 80), ("other.example", 8443)]
    assert len(state["sockets"]) == 2
    first_wire, second_wire = [b"".join(sock.writes) for sock in state["sockets"]]
    for wire in (first_wire, second_wire):
        assert b"Authorization:" not in wire and b"Cookie:" not in wire
    assert b"Host: first.example\r\n" in first_wire
    assert b"Host: other.example:8443\r\n" in second_wire
    assert b"GET /final.mp4?signature=second HTTP/1.1" in second_wire
    assert state["sni"] == ["other.example"]


def test_redirect_loop_is_bounded(monkeypatch):
    redirect = {"status": 302, "headers": b"Location: /again\r\n", "body": b""}
    state = _wire(monkeypatch, responses=[dict(redirect) for _ in range(12)])
    with pytest.raises(AiVideoError):
        with vidu_download.stream_public_video(URL, timeout_seconds=1):
            pytest.fail("redirect loop accepted")
    assert len(state["sockets"]) <= 11


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


@pytest.mark.parametrize("failure", ["truncated", "sink"])
def test_incomplete_or_sink_failure_never_emits_receipt_and_closes_socket(monkeypatch, failure):
    state = _wire(monkeypatch)
    profile = _profile(result_trust="authenticated_task", result_origins=(), max_download_bytes=12)
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
    sink = FailingSink() if failure == "sink" else BytesIO()
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=fake.query))) as client:
        provider._transport = HttpxViduTransport(client=client)
        with pytest.raises(AiVideoError):
            provider.fetch(submission, receipt, observation, sink)
    assert len(state["sockets"]) == 1 and state["sockets"][0].closed
    if failure == "truncated":
        assert sink.getvalue() == MP4[:-1]


def test_authenticated_fetch_ignores_origin_size_and_mime_metadata_after_exact_task_query():
    profile = _profile(result_trust="authenticated_task", result_origins=(), max_download_bytes=12)
    provider, fake, args = _setup(profile=profile)
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    url = "http://127.0.0.1:8080/result.mp4?sig=private"
    fake.query["creations"][0]["url"] = url
    fake.headers = {"content-type": "text/plain", "content-length": str(len(MP4))}
    sink = BytesIO()
    fetched = provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == MP4
    assert fetched.remote_materialization.remote_origin == "http://127.0.0.1:8080"
    assert fetched.remote_materialization.transport_kind == "provider_output_http"


@pytest.mark.parametrize("body", [b"not an mp4", MP4[:-1]])
def test_bad_or_incomplete_media_is_written_before_post_download_rejection(body):
    provider, fake, args = _setup(profile=_profile(max_download_bytes=12))
    submission, receipt = _submitted(provider, args)
    observation = provider.get_status(submission, receipt)
    fake.body = body
    fake.headers = {"content-type": "application/octet-stream", "content-length": str(len(body) + 1)}
    sink = BytesIO()
    with pytest.raises(AiVideoError):
        provider.fetch(submission, receipt, observation, sink)
    assert sink.getvalue() == body
