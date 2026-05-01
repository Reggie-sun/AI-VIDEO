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
