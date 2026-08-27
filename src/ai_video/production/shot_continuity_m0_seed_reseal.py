"""State-bound validation for an explicit fixed-seed M0 reseal."""

from __future__ import annotations

import base64
import binascii
import json
from pathlib import Path
from typing import Any

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_execution_stack_materialization_source_path,
)
from ai_video.production.shot_continuity_m0_qualification import (
    CONTENT_ADDRESSED_M0_SEED,
    FIXED_M0_SEED_RESEAL,
    M0QualificationProfile,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _unchanged_profile_contract(profile: Any) -> dict[str, object]:
    return profile.model_dump(
        mode="json",
        exclude={
            "prepared_receipt_hash",
            "registry_content_hash",
            "seed_derivation",
            "fixed_seed_source_prepared_receipt_hash",
            "fixed_seed_source_execution_stack_hash",
            "fixed_seed_source_profile_hash",
        },
    )


def validate_m0_fixed_seed_reseal(*, committer: Any, profile: Any) -> None:
    """Prove that a fixed seed comes from one exact historical M0 stack."""

    if profile.seed_derivation == CONTENT_ADDRESSED_M0_SEED:
        return
    if profile.seed_derivation != FIXED_M0_SEED_RESEAL:
        raise _invalid("M0 fixed-seed reseal mode is unsupported.")
    try:
        historical = committer.reopen_p0_qualification_history(
            profile.fixed_seed_source_prepared_receipt_hash
        )
        receipt, candidates = historical[:2]
        if len(candidates) != 2:
            raise ValueError("historical P0 candidate coverage changed")
        source_stack = candidates[0]
        if (
            receipt.content_hash != profile.fixed_seed_source_prepared_receipt_hash
            or source_stack.execution_stack_hash
            != profile.fixed_seed_source_execution_stack_hash
            or source_stack.materialization_status != "materialized"
            or source_stack.profile_hash != profile.fixed_seed_source_profile_hash
        ):
            raise ValueError("historical fixed-seed stack identity changed")
        root = Path(committer.project_root).resolve(strict=True)
        source_path = root / canonical_execution_stack_materialization_source_path(
            "profile", source_stack.profile_hash
        )
        snapshot = _read_regular_file_nofollow(source_path, contained_by=root)
        if snapshot.file_sha256 != source_stack.profile_hash:
            raise ValueError("historical fixed-seed profile source hash changed")
        envelope = json.loads(snapshot.data)
        if not isinstance(envelope, dict) or envelope.get("schema_version") != "1":
            raise ValueError("historical fixed-seed profile envelope is invalid")
        source_profile = M0QualificationProfile.model_validate_json(
            base64.b64decode(envelope["profile_bytes_base64"], validate=True)
        )
    except (
        AiVideoError,
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        binascii.Error,
    ) as exc:
        if isinstance(exc, AiVideoError) and exc.code is ErrorCode.VIDEO_REQUEST_INVALID:
            raise
        raise _invalid("M0 fixed-seed historical source could not be reopened.", str(exc)) from exc
    if (
        source_profile.seed_derivation != CONTENT_ADDRESSED_M0_SEED
        or source_profile.sealed_seed != profile.sealed_seed
        or _unchanged_profile_contract(source_profile)
        != _unchanged_profile_contract(profile)
    ):
        raise _invalid("M0 fixed-seed reseal changed the execution contract.")


__all__ = ["validate_m0_fixed_seed_reseal"]
