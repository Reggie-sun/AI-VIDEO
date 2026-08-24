from __future__ import annotations

import hashlib

import httpx
import pytest

from ai_video.errors import AiVideoError
from ai_video.production.shot_continuity_source_contracts import (
    SourceQualificationInput,
)
from ai_video.production.shot_continuity_source_transport import (
    ComfySourceQualificationTransport,
)
from ai_video.production import shot_continuity_source_transport


def test_source_transport_default_client_disables_environment_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_client = httpx.Client
    client_kwargs: dict[str, object] = {}

    def make_client(**kwargs: object) -> httpx.Client:
        client_kwargs.update(kwargs)
        return real_client(transport=httpx.MockTransport(lambda _: httpx.Response(500)))

    monkeypatch.setattr(shot_continuity_source_transport.httpx, "Client", make_client)
    transport = ComfySourceQualificationTransport()

    assert client_kwargs == {
        "timeout": 30,
        "trust_env": False,
        "follow_redirects": False,
    }
    transport._client.http.close()


def test_source_transport_routes_every_operation_through_one_loopback_origin() -> None:
    requests: list[httpx.Request] = []
    history_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal history_calls
        requests.append(request)
        if request.url.path == "/object_info":
            return httpx.Response(200, json={"SaveVideo": {"input": {}}})
        if request.url.path == "/upload/image":
            return httpx.Response(200, json={"name": "source-frame.png"})
        if request.url.path == "/prompt":
            return httpx.Response(200, json={"prompt_id": "source-prompt-1"})
        if request.url.path == "/history/source-prompt-1":
            history_calls += 1
            if history_calls == 1:
                return httpx.Response(200, json={"source-prompt-1": {"outputs": {}}})
            return httpx.Response(
                200,
                json={"source-prompt-1": {"outputs": {"42": {"gifs": []}}}},
            )
        if request.url.path == "/queue":
            return httpx.Response(
                200,
                json={
                    "queue_running": [[0, "source-prompt-1"]],
                    "queue_pending": [],
                },
            )
        if request.url.path == "/view":
            return httpx.Response(200, content=b"source-video")
        return httpx.Response(404)

    transport = ComfySourceQualificationTransport(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    payload = b"immutable-source-frame"
    item = SourceQualificationInput(
        file_name="source-frame.png",
        data=payload,
        file_sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
    )

    assert set(transport.get_object_info()) == {"SaveVideo"}
    assert transport.upload_input(item) == "source-frame.png"
    assert transport.submit_prompt({"1": {"class_type": "SaveVideo"}}) == "source-prompt-1"
    assert transport.poll_job(
        "source-prompt-1", poll_interval_seconds=0, timeout_seconds=1
    ).prompt_id == "source-prompt-1"
    assert transport.fetch_artifact_bytes(
        filename="source.mp4", subfolder="", type_="output"
    ) == b"source-video"

    assert transport.base_url == "http://127.0.0.1:8188"
    assert transport.deployment_identity == "loopback-127.0.0.1-8188"
    assert [request.url.path for request in requests] == [
        "/object_info",
        "/upload/image",
        "/prompt",
        "/history/source-prompt-1",
        "/queue",
        "/history/source-prompt-1",
        "/view",
    ]
    assert {
        (request.url.scheme, request.url.host, request.url.port)
        for request in requests
    } == {("http", "127.0.0.1", 8188)}


def test_source_transport_rejects_non_loopback_before_any_request() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    with pytest.raises(AiVideoError):
        ComfySourceQualificationTransport(
            base_url="https://example.com:8188",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )

    assert calls == 0


def test_source_transport_rejects_tampered_input_before_upload() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    transport = ComfySourceQualificationTransport(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(AiVideoError):
        transport.upload_input(
            SourceQualificationInput(
                file_name="source-frame.png",
                data=b"tampered",
                file_sha256=hashlib.sha256(b"sealed").hexdigest(),
                size_bytes=len(b"tampered"),
            )
        )

    assert calls == 0
