"""Bounded public diagnostics; provider response prose is never forwarded."""

import json
import re

# Exact public codes from https://docs.volcengine.com/docs/ark/error-codes.
# Unknown codes deliberately retain the original HTTP-only diagnostic.
_PUBLIC_CODES = frozenset({
    "MissingParameter", "InvalidParameter", "InvalidParameter.UnsupportedParameter",
    "InvalidParameter.TaskTypeConstraint", "InvalidParameter.TaskTypeMismatch",
    "InvalidParameter.TosURLInvalid", "InvalidImageURL.EmptyURL",
    "InvalidImageURL.InvalidFormat", "InvalidEndpoint.ClosedEndpoint",
    "InvalidEndpointOrModel.NotFound", "InvalidEndpointOrModel.ModelIDAccessDisabled",
    "AuthenticationError", "InvalidAccountStatus", "AccountOverdueError",
    "AccessDenied", "ModelNotOpen", "OperationDenied.ServiceNotOpen",
    "OperationDenied.ServiceOverdue", "OperationDenied.PermissionDenied",
    "InputTextSensitiveContentDetected", "InputImageSensitiveContentDetected",
    "InputVideoSensitiveContentDetected", "InputAudioSensitiveContentDetected",
    "InputImageSensitiveContentDetected.PrivacyInformation",
    "InputVideoSensitiveContentDetected.PrivacyInformation",
    "InputTextSensitiveContentDetected.PolicyViolation",
    "InputImageSensitiveContentDetected.PolicyViolation",
    "InputVideoSensitiveContentDetected.PolicyViolation",
    "SensitiveContentDetected", "SensitiveContentDetected.SevereViolation",
})
_PARAMETERS = frozenset({
    "model", "content", "duration", "frames", "resolution", "ratio", "seed",
    "generate_audio", "watermark", "camera_fixed", "return_last_frame",
    "service_tier", "draft", "priority", "omni_reference_task_type",
})
_NAMED_PARAMETER = re.compile(r"\bparameter\s+[`'\"]([a-z_]+)[`'\"]", re.I)


def submit_rejection_message(status: int, body: bytes) -> str:
    message = f"Seedance submit was rejected with HTTP {status}."
    if len(body) > 65536:
        return message
    try:
        response = json.loads(body)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return message
    error = response.get("error") if isinstance(response, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    if not isinstance(code, str) or code not in _PUBLIC_CODES:
        return message
    message += f" Provider error: {code}."
    prose = error.get("message")
    parameter = _NAMED_PARAMETER.search(prose) if isinstance(prose, str) else None
    if parameter and parameter.group(1).lower() in _PARAMETERS:
        message += f" Parameter: {parameter.group(1).lower()}."
    return message
