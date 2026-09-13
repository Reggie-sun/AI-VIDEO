import base64
import json

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.vidu_ad_wire import encode_create, parse_status, parse_submission


def test_encode_create_preserves_reference_order_and_exact_contract():
    body = encode_create(
        prompt="下班，换个状态。",
        duration=28,
        aspect_ratio="9:16",
        language="zh",
        creative=True,
        images=(("image/png", b"first"), ("image/webp", b"second")),
    )

    assert json.loads(body) == {
        "prompt": "下班，换个状态。",
        "duration": 28,
        "aspect_ratio": "9:16",
        "language": "zh",
        "creative": True,
        "images": [
            "data:image/png;base64," + base64.b64encode(b"first").decode("ascii"),
            "data:image/webp;base64," + base64.b64encode(b"second").decode("ascii"),
        ],
    }


@pytest.mark.parametrize(
    "values",
    [
        {"prompt": "   "},
        {"prompt": "x" * 2001},
        {"duration": True},
        {"duration": 7},
        {"duration": 61},
        {"aspect_ratio": "4:3"},
        {"language": "ja"},
        {"creative": 1},
        {"images": ()},
        {"images": (("image/jpg", b"x"),)},
        {"images": (("image/png", b""),)},
        {"images": (("image/png", b"x"),) * 8},
    ],
)
def test_encode_create_rejects_invalid_inputs(values):
    args = dict(
        prompt="ad",
        duration=8,
        aspect_ratio="9:16",
        language="zh",
        creative=False,
        images=(("image/jpeg", b"x"),),
    )
    args.update(values)

    with pytest.raises(AiVideoError) as exc_info:
        encode_create(**args)

    assert exc_info.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_encode_create_enforces_raw_and_encoded_size_limits():
    args = dict(
        prompt="ad",
        duration=8,
        aspect_ratio="9:16",
        language="zh",
        creative=False,
        images=(("image/png", b"x"),),
    )
    with pytest.raises(AiVideoError) as raw:
        encode_create(**{**args, "images": (("image/png", b"x" * (50 * 1024 * 1024 + 1)),)})
    assert raw.value.code is ErrorCode.VIDEO_REQUEST_INVALID

    with pytest.raises(AiVideoError) as body:
        encode_create(**{**args, "images": (("image/png", b"x" * (16 * 1024 * 1024)),)})
    assert body.value.code is ErrorCode.VIDEO_REQUEST_INVALID


def test_parse_submission_accepts_safe_task_and_known_state():
    assert parse_submission(b'{"task_id":"ad.task:1","state":"queueing"}') == "ad.task:1"


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b"[]",
        b'{"task_id":"bad/task","state":"created"}',
        b'{"task_id":"safe","state":"unknown"}',
        b'{"task_id":"safe","state":[]}',
        b'{"task_id":"one","task_id":"two","state":"created"}',
        b'{"task_id":"safe","state":"created","nested":{"x":1,"x":2}}',
    ],
)
def test_parse_submission_rejects_malformed_or_ambiguous_responses(body):
    with pytest.raises(AiVideoError) as exc_info:
        parse_submission(body)
    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED


def test_parse_status_returns_terminal_creation_and_validated_public_url():
    body = json.dumps({
        "id": "ad.task:1",
        "state": "success",
        "creations": [{"id": "creation.1", "url": "https://media.vidu.example/output.mp4?token=signed"}],
    }).encode()

    assert parse_status(body, task_id="ad.task:1") == (
        "success", "creation.1", "https://media.vidu.example/output.mp4?token=signed",
    )


@pytest.mark.parametrize(
    "body",
    [
        b'{"id":"other","state":"processing"}',
        b'{"id":"ad.task:1","state":"unknown"}',
        b'{"id":"ad.task:1","state":[]}',
        b'{"id":"ad.task:1","id":"other","state":"processing"}',
        b'{"id":"ad.task:1","state":"success","creations":[]}',
        b'{"id":"ad.task:1","state":"success","creations":[{"id":"c"},{"id":"d"}]}',
        b'{"id":"ad.task:1","state":"success","creations":[{"id":"c","url":"http://private.example/a"}]}',
    ],
)
def test_parse_status_rejects_wrong_identity_or_invalid_success_payload_without_leaking_url(body):
    with pytest.raises(AiVideoError) as exc_info:
        parse_status(body, task_id="ad.task:1")

    assert exc_info.value.code is ErrorCode.VIDEO_PROVIDER_FAILED
    assert "private.example" not in str(exc_info.value) + repr(exc_info.value)


@pytest.mark.parametrize("state", ["created", "queueing", "processing", "failed"])
def test_parse_status_non_success_returns_no_creation_or_url(state):
    body = json.dumps({"id": "ad.task:1", "state": state, "error": "provider detail"}).encode()
    assert parse_status(body, task_id="ad.task:1") == (state, None, None)


def test_response_limits_and_private_url_are_sanitized():
    with pytest.raises(AiVideoError) as oversized:
        parse_submission(b"{" + b"x" * 1_000_000)
    assert oversized.value.code is ErrorCode.VIDEO_PROVIDER_FAILED

    private_url = "https://127.0.0.1/private?signature=secret"
    body = json.dumps({
        "id": "ad.task:1", "state": "success",
        "creations": [{"id": "creation.1", "url": private_url}],
    }).encode()
    with pytest.raises(AiVideoError) as invalid_url:
        parse_status(body, task_id="ad.task:1")
    assert private_url not in str(invalid_url.value) + repr(invalid_url.value)
