from ai_video.errors import (
    AiVideoError,
    ErrorCode,
    config_error,
    retryable_error,
)


def test_config_error_is_not_retryable():
    error = config_error(ErrorCode.CONFIG_INVALID, "Bad config", "missing project_name")
    assert error.code is ErrorCode.CONFIG_INVALID
    assert error.user_message == "Bad config"
    assert error.technical_detail == "missing project_name"
    assert error.retryable is False
    assert str(error) == "Bad config"


def test_retryable_error_preserves_cause():
    cause = RuntimeError("connection reset")
    error = retryable_error(ErrorCode.COMFY_UNAVAILABLE, "ComfyUI unavailable", cause=cause)
    assert error.retryable is True
    assert error.cause is cause
    assert isinstance(error, AiVideoError)


def test_p8_video_error_codes_are_stable_public_values():
    assert {
        ErrorCode.VIDEO_REQUEST_INVALID.value,
        ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED.value,
        ErrorCode.VIDEO_PROVIDER_FAILED.value,
        ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN.value,
        ErrorCode.VIDEO_ARTIFACT_INVALID.value,
    } == {
        "video_request_invalid",
        "video_capability_unsupported",
        "video_provider_failed",
        "video_provider_outcome_unknown",
        "video_artifact_invalid",
    }
