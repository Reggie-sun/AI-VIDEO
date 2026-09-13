"""Pure Vidu one-click-ad request and response codecs."""

from __future__ import annotations

import base64
import json
import re

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.vidu_download import parse_result_url


_MAX_JSON_BYTES = 1_000_000
_MAX_BODY_BYTES = 20 * 1024 * 1024
_MAX_IMAGE_BYTES = 50 * 1024 * 1024
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_STATES = frozenset({"created", "queueing", "processing", "success", "failed"})
_IMAGE_MIME_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})


def _request_error(message: str) -> AiVideoError:
    return AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID, user_message=message)


def _provider_error(message: str) -> AiVideoError:
    return AiVideoError(code=ErrorCode.VIDEO_PROVIDER_FAILED, user_message=message)


def _identifier(value: object) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise _provider_error("Vidu ad response identity is invalid.")
    return value


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _reject_nonstandard_json(_: str) -> object:
    raise ValueError("non-standard JSON value")


def _json_object(body: bytes) -> dict[str, object]:
    if not isinstance(body, bytes) or len(body) > _MAX_JSON_BYTES:
        raise _provider_error("Vidu ad response is invalid.")
    try:
        value = json.loads(
            body,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_json,
        )
    except (TypeError, UnicodeError, ValueError):
        raise _provider_error("Vidu ad response is invalid.") from None
    if not isinstance(value, dict):
        raise _provider_error("Vidu ad response must be an object.")
    return value


def encode_create(*, prompt: str, duration: int, aspect_ratio: str, language: str,
                  creative: bool, images: tuple[tuple[str, bytes], ...]) -> bytes:
    """Encode the official one-click-ad request body without performing I/O."""
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
        raise _request_error("Vidu ad prompt is invalid.")
    if type(duration) is not int or not 8 <= duration <= 60:
        raise _request_error("Vidu ad duration is invalid.")
    if not isinstance(aspect_ratio, str) or aspect_ratio not in {"1:1", "16:9", "9:16"}:
        raise _request_error("Vidu ad aspect ratio is invalid.")
    if not isinstance(language, str) or language not in {"zh", "en"}:
        raise _request_error("Vidu ad language is invalid.")
    if type(creative) is not bool:
        raise _request_error("Vidu ad creative setting is invalid.")
    if not isinstance(images, tuple) or not 1 <= len(images) <= 7:
        raise _request_error("Vidu ad images are invalid.")

    data_uris: list[str] = []
    for image in images:
        if not isinstance(image, tuple) or len(image) != 2:
            raise _request_error("Vidu ad image is invalid.")
        mime_type, raw = image
        if (not isinstance(mime_type, str) or mime_type not in _IMAGE_MIME_TYPES
                or not isinstance(raw, bytes) or not raw or len(raw) > _MAX_IMAGE_BYTES):
            raise _request_error("Vidu ad image is invalid.")
        data_uris.append(f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}")

    try:
        body = json.dumps(
            {
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "language": language,
                "creative": creative,
                "images": data_uris,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise _request_error("Vidu ad request is invalid.") from None
    if len(body) > _MAX_BODY_BYTES:
        raise _request_error("Vidu ad request exceeds the body size limit.")
    return body


def parse_submission(body: bytes) -> str:
    """Return the safe task identity from an accepted one-click-ad response."""
    payload = _json_object(body)
    task_id = _identifier(payload.get("task_id"))
    state = payload.get("state")
    if not isinstance(state, str) or state not in _STATES:
        raise _provider_error("Vidu ad response state is invalid.")
    return task_id


def parse_status(body: bytes, *, task_id: str) -> tuple[str, str | None, str | None]:
    """Return state and, only for success, the validated creation identity and URL."""
    expected_task_id = _identifier(task_id)
    payload = _json_object(body)
    if _identifier(payload.get("id")) != expected_task_id:
        raise _provider_error("Vidu ad response identity changed.")
    state = payload.get("state")
    if not isinstance(state, str) or state not in _STATES:
        raise _provider_error("Vidu ad response state is invalid.")
    if state != "success":
        return state, None, None

    creations = payload.get("creations")
    if not isinstance(creations, list) or len(creations) != 1 or not isinstance(creations[0], dict):
        raise _provider_error("Vidu ad result must contain exactly one creation.")
    creation_id = _identifier(creations[0].get("id"))
    url = creations[0].get("url")
    if not isinstance(url, str):
        raise _provider_error("Vidu ad result URL is missing.")
    try:
        parse_result_url(url)
    except AiVideoError:
        raise _provider_error("Vidu ad result URL is invalid.") from None
    return state, creation_id, url
