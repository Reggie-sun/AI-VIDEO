from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import httpx
import pytest

from ai_video.comfy_client import ComfyClient, JobStatus
from ai_video.errors import AiVideoError, ErrorCode


def test_upload_input_reuses_loopback_image_route_for_generic_bytes(tmp_path):
    source = tmp_path / "reference.mp4"
    source.write_bytes(b"reference-video")

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        assert request.method == "POST"
        assert request.url.path == "/upload/image"
        assert b'name="image"' in body
        assert b'filename="reference.mp4"' in body
        assert b"reference-video" in body
        return httpx.Response(200, json={"name": "server-reference.mp4"})

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.upload_input(source) == "server-reference.mp4"


def test_upload_input_bytes_reuses_the_same_upload_route_without_a_tempfile():
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read()
        assert request.url.path == "/upload/image"
        assert b'filename="source-frame.png"' in body
        assert b"immutable-frame" in body
        return httpx.Response(200, json={"name": "server-source-frame.png"})

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert (
        client.upload_input_bytes("source-frame.png", b"immutable-frame")
        == "server-source-frame.png"
    )


def test_upload_image_remains_a_compatible_upload_input_wrapper(
    tmp_path, monkeypatch
):
    source = tmp_path / "frame.png"
    source.write_bytes(b"png")
    client = ComfyClient("http://127.0.0.1:8188")
    seen = []
    monkeypatch.setattr(
        client,
        "upload_input",
        lambda path: seen.append(path) or "server-frame.png",
    )

    assert client.upload_image(source) == "server-frame.png"
    assert seen == [source]


def test_get_object_info_returns_registered_node_inventory():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/object_info"
        return httpx.Response(200, json={"SaveImage": {"display_name": "Save Image"}})

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert set(client.get_object_info()) == {"SaveImage"}


def test_get_object_info_rejects_non_object_payload():
    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=["SaveImage"])
            )
        ),
    )
    with pytest.raises(AiVideoError) as exc_info:
        client.get_object_info()
    assert exc_info.value.code is ErrorCode.COMFY_UNAVAILABLE


def test_submit_rejects_node_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": "bad prompt", "node_errors": {"6": "bad"}})

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(AiVideoError) as exc:
        client.submit_prompt({"6": {"inputs": {}, "class_type": "Test"}})
    assert exc.value.code is ErrorCode.COMFY_SUBMISSION_FAILED
    assert exc.value.retryable is False


def test_poll_completed_history_collects_status():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/queue":
            return httpx.Response(200, json={"queue_running": [], "queue_pending": []})
        if request.url.path == "/history/prompt-1":
            return httpx.Response(
                200,
                json={
                    "prompt-1": {
                        "outputs": {
                            "42": {
                                "gifs": [
                                    {"filename": "clip.mp4", "subfolder": "", "type": "output"}
                                ]
                            }
                        }
                    }
                },
            )
        return httpx.Response(404)

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.poll_job("prompt-1", poll_interval_seconds=0, timeout_seconds=1)
    assert result.status is JobStatus.COMPLETED
    assert result.history["outputs"]["42"]["gifs"][0]["filename"] == "clip.mp4"


def test_poll_error_history_wins_over_empty_outputs():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/queue":
            return httpx.Response(200, json={"queue_running": [], "queue_pending": []})
        if request.url.path == "/history/prompt-oom":
            return httpx.Response(
                200,
                json={
                    "prompt-oom": {
                        "outputs": {},
                        "status": {
                            "status_str": "error",
                            "messages": [
                                [
                                    "execution_error",
                                    {
                                        "exception_message": "Allocation on device",
                                        "exception_type": "torch.OutOfMemoryError",
                                    },
                                ]
                            ],
                        },
                    }
                },
            )
        return httpx.Response(404)

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    result = client.poll_job("prompt-oom", poll_interval_seconds=0, timeout_seconds=1)
    assert result.status is JobStatus.FAILED
    assert result.error is not None
    assert result.error.code is ErrorCode.COMFY_JOB_FAILED
    assert "OutOfMemoryError" in (result.error.technical_detail or "")


def test_collect_output_downloads_view(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/view":
            return httpx.Response(200, content=b"video")
        return httpx.Response(404)

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    target = tmp_path / "clip.mp4"
    client.download_artifact(filename="clip.mp4", subfolder="", type_="output", target=target)
    assert target.read_bytes() == b"video"


def test_fetch_artifact_bytes_does_not_write_a_target():
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.url.params["filename"]))
        return httpx.Response(200, content=b"image-bytes")

    client = ComfyClient(
        "http://127.0.0.1:8188",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    assert client.fetch_artifact_bytes(
        filename="frame.png", subfolder="", type_="output"
    ) == b"image-bytes"
    assert seen == [("/view", "frame.png")]


@contextmanager
def _artifact_server(*, loop=False, truncated=False, status=200):
    seen = []
    payload = b"arbitrary-downloaded-bytes"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, dict(self.headers)))
            self.send_response(302 if loop else status)
            if loop:
                self.send_header("Location", "/loop?signature=SIGNED_DOWNLOAD_CANARY")
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(payload) + (10 if truncated else 0)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, seen, payload
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("write_file", [False, True])
def test_artifact_download_follows_cdn_redirect_without_client_credentials(tmp_path, write_file, caplog):
    caplog.set_level("INFO")
    seen = []
    with _artifact_server() as (port, downloaded, payload):
        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(302, headers={
                "location": f"http://redirect-user:redirect-secret@127.0.0.1:{port}/file?signature=SIGNED_DOWNLOAD_CANARY",
            })

        with httpx.Client(transport=httpx.MockTransport(handler),
                          auth=("api-user", "api-secret"), headers={"x-api-key": "private-key"}) as http:
            http.cookies.set("session", "private-cookie", domain="127.0.0.1")
            client = ComfyClient("http://127.0.0.1:8188", http_client=http)
            if write_file:
                target = tmp_path / "download.bin"
                client.download_artifact(filename="result.bin", subfolder="", type_="output", target=target)
                assert target.read_bytes() == payload
            else:
                assert client.fetch_artifact_bytes(filename="result.bin", subfolder="", type_="output") == payload
        assert len(seen) == len(downloaded) == 1
        assert "authorization" in seen[0].headers
        assert "x-api-key" in seen[0].headers
        assert "SIGNED_DOWNLOAD_CANARY" in downloaded[0][0]
        assert not {"authorization", "cookie", "x-api-key"}.intersection(
            key.lower() for key in downloaded[0][1]
        )
    assert "SIGNED_DOWNLOAD_CANARY" not in caplog.text
    assert "redirect-secret" not in caplog.text


@pytest.mark.parametrize("failure", ["loop", "truncated", "http"])
def test_artifact_download_failure_is_typed_without_leaking_signed_url(failure, caplog):
    caplog.set_level("INFO")
    with _artifact_server(loop=failure == "loop", truncated=failure == "truncated",
                          status=404 if failure == "http" else 200) as (port, downloaded, _):
        def handler(request):
            return httpx.Response(302, headers={
                "location": f"http://127.0.0.1:{port}/file?signature=SIGNED_DOWNLOAD_CANARY",
            })
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            client = ComfyClient("http://127.0.0.1:8188", http_client=http)
            with pytest.raises(AiVideoError) as exc_info:
                client.fetch_artifact_bytes(filename="result.bin", subfolder="", type_="output")
        assert exc_info.value.code is ErrorCode.COMFY_OUTPUT_MISSING
        assert len(downloaded) == (11 if failure == "loop" else 1)
        assert "SIGNED_DOWNLOAD_CANARY" not in str(exc_info.value)
        assert "SIGNED_DOWNLOAD_CANARY" not in exc_info.value.technical_detail
    assert "SIGNED_DOWNLOAD_CANARY" not in caplog.text


@pytest.mark.parametrize("status", [200, 302, 503])
def test_artifact_real_http_transport_debug_logs_are_private_and_scope_isolated(
    monkeypatch, caplog, status
):
    import logging
    from httpcore import MockBackend
    from ai_video import comfy_client

    caplog.set_level("DEBUG")
    # Use the real HTTPX/httpcore stack so response-header DEBUG records are emitted.
    wire = (
        f"HTTP/1.1 {status} Test\r\n"
        "Location: https://cdn.example/file?signature=SIGNED_DEBUG_CANARY\r\n"
        "Set-Cookie: private=SERVER_COOKIE_CANARY\r\n"
        "Content-Length: 5\r\n\r\nbytes"
    ).encode()
    transport = httpx.HTTPTransport()
    transport._pool._network_backend = MockBackend([wire])
    seen = []

    @contextmanager
    def native_download(url, **_kwargs):
        seen.append(url)
        yield type("Downloaded", (), {
            "status_code": 200,
            "iter_bytes": lambda self: iter([b"bytes"]),
        })()

    monkeypatch.setattr(comfy_client, "stream_public_video", native_download)

    def concurrent_diagnostic(_response):
        # A different request/thread must retain its diagnostics while the
        # artifact request's sensitive response headers are being processed.
        thread = Thread(target=lambda: logging.getLogger("httpcore.http11").debug(
            "UNRELATED_CONCURRENT_CANARY"
        ))
        thread.start()
        thread.join(timeout=2)
        assert not thread.is_alive()

    with httpx.Client(transport=transport, event_hooks={"response": [concurrent_diagnostic]}) as http:
        client = ComfyClient("http://127.0.0.1:8188", http_client=http)
        if status == 503:
            with pytest.raises(AiVideoError):
                client.fetch_artifact_bytes(filename="result.bin", subfolder="", type_="output")
        else:
            assert client.fetch_artifact_bytes(filename="result.bin", subfolder="", type_="output") == b"bytes"
    logging.getLogger("httpcore.http11").debug("AFTER_ARTIFACT_SCOPE_CANARY")
    assert len(seen) == (1 if status == 302 else 0)
    assert "SIGNED_DEBUG_CANARY" not in caplog.text
    assert "SERVER_COOKIE_CANARY" not in caplog.text
    assert "UNRELATED_CONCURRENT_CANARY" in caplog.text
    assert "AFTER_ARTIFACT_SCOPE_CANARY" in caplog.text
