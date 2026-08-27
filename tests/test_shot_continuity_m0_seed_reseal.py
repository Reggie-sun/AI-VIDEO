from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.paths import (
    canonical_execution_stack_materialization_source_path,
)
from ai_video.production.shot_continuity_m0_qualification import (
    FIXED_M0_SEED_RESEAL,
    M0QualificationProfile,
    RUNTIME_REPAIR_M0_SEED_RESEAL,
)
from ai_video.production.shot_continuity_m0_seed_reseal import (
    validate_m0_fixed_seed_reseal,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)


class _HistoricalCommitter:
    def __init__(
        self,
        root: Path,
        *,
        receipt_hash: str,
        m0_stack: object,
        m1_stack: object | None = None,
    ) -> None:
        self.project_root = root
        self.receipt_hash = receipt_hash
        self.m0_stack = m0_stack
        self.m1_stack = m1_stack or SimpleNamespace(
            execution_stack_hash="9" * 64,
            materialization_status="materialized",
            profile_hash="8" * 64,
        )

    def reopen_p0_qualification_history(self, _content_hash: str):
        return (
            SimpleNamespace(content_hash=self.receipt_hash),
            (self.m0_stack, self.m1_stack),
            (),
            None,
            (),
            (),
        )


def _profiles(tmp_path: Path) -> tuple[_HistoricalCommitter, dict[str, object]]:
    source_values = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    source_profile = M0QualificationProfile.model_validate(source_values)
    source_payload = json.dumps(
        source_profile.model_dump(mode="json", exclude_none=True),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    envelope = json.dumps(
        {
            "binding_bytes_base64": base64.b64encode(b"binding").decode("ascii"),
            "profile_bytes_base64": base64.b64encode(source_payload).decode("ascii"),
            "schema_version": "1",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    profile_hash = hashlib.sha256(envelope).hexdigest()
    source_path = tmp_path / canonical_execution_stack_materialization_source_path(
        "profile", profile_hash
    )
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(envelope)
    receipt_hash = "1" * 64
    execution_stack_hash = "2" * 64
    committer = _HistoricalCommitter(
        tmp_path,
        receipt_hash=receipt_hash,
        m0_stack=SimpleNamespace(
            execution_stack_hash=execution_stack_hash,
            materialization_status="materialized",
            profile_hash=profile_hash,
        ),
    )
    fixed_values = {
        **source_values,
        "prepared_receipt_hash": "3" * 64,
        "registry_content_hash": "4" * 64,
        "seed_derivation": FIXED_M0_SEED_RESEAL,
        "fixed_seed_source_prepared_receipt_hash": receipt_hash,
        "fixed_seed_source_execution_stack_hash": execution_stack_hash,
        "fixed_seed_source_profile_hash": profile_hash,
    }
    return committer, fixed_values


def test_fixed_seed_profile_requires_all_historical_source_fields() -> None:
    values = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    values["seed_derivation"] = FIXED_M0_SEED_RESEAL

    with pytest.raises(ValidationError, match="historical source fields"):
        M0QualificationProfile.model_validate(values)


def test_content_addressed_profile_rejects_fixed_seed_source_fields() -> None:
    values = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    values["fixed_seed_source_profile_hash"] = "1" * 64

    with pytest.raises(ValidationError, match="must not declare"):
        M0QualificationProfile.model_validate(values)


def test_fixed_seed_reseal_reopens_exact_historical_profile(tmp_path: Path) -> None:
    committer, values = _profiles(tmp_path)
    profile = M0QualificationProfile.model_validate(values)

    validate_m0_fixed_seed_reseal(committer=committer, profile=profile)


def test_fixed_seed_reseal_rejects_matching_m1_when_m0_does_not_match(
    tmp_path: Path,
) -> None:
    committer, values = _profiles(tmp_path)
    expected_hash = values["fixed_seed_source_execution_stack_hash"]
    committer.m0_stack = SimpleNamespace(
        execution_stack_hash="7" * 64,
        materialization_status="materialized",
        profile_hash=values["fixed_seed_source_profile_hash"],
    )
    committer.m1_stack = SimpleNamespace(
        execution_stack_hash=expected_hash,
        materialization_status="materialized",
        profile_hash=values["fixed_seed_source_profile_hash"],
    )
    profile = M0QualificationProfile.model_validate(values)

    with pytest.raises(AiVideoError, match="fixed-seed"):
        validate_m0_fixed_seed_reseal(committer=committer, profile=profile)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("sealed_seed", 1),
        ("prompt_sha256", "8" * 64),
        ("fixed_seed_source_prepared_receipt_hash", "5" * 64),
        ("fixed_seed_source_execution_stack_hash", "6" * 64),
        ("fixed_seed_source_profile_hash", "7" * 64),
    ),
)
def test_fixed_seed_reseal_rejects_seed_contract_or_lineage_drift(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    committer, values = _profiles(tmp_path)
    values[field] = value
    profile = M0QualificationProfile.model_validate(values)

    with pytest.raises(AiVideoError, match="fixed-seed"):
        validate_m0_fixed_seed_reseal(committer=committer, profile=profile)


def _replace_runtime(
    values: dict[str, object],
    *,
    name: str,
    version: str,
    content_hash: str,
) -> None:
    runtime_seals = [dict(item) for item in values["runtime_seals"]]
    target = next(item for item in runtime_seals if item["name"] == name)
    target.update(version=version, content_hash=content_hash)
    values["runtime_seals"] = runtime_seals


def test_runtime_repair_fixed_seed_reseal_allows_only_comfyui_runtime_change(
    tmp_path: Path,
) -> None:
    committer, values = _profiles(tmp_path)
    values["seed_derivation"] = RUNTIME_REPAIR_M0_SEED_RESEAL
    _replace_runtime(
        values,
        name="comfyui",
        version="0.33.0+e01fb4c56b7a",
        content_hash="9" * 64,
    )
    profile = M0QualificationProfile.model_validate(values)

    validate_m0_fixed_seed_reseal(committer=committer, profile=profile)


def test_runtime_repair_fixed_seed_reseal_rejects_non_comfyui_change(
    tmp_path: Path,
) -> None:
    committer, values = _profiles(tmp_path)
    values["seed_derivation"] = RUNTIME_REPAIR_M0_SEED_RESEAL
    _replace_runtime(
        values,
        name="minimax-h3-audio-t8",
        version="changed",
        content_hash="8" * 64,
    )
    profile = M0QualificationProfile.model_validate(values)

    with pytest.raises(AiVideoError, match="fixed-seed"):
        validate_m0_fixed_seed_reseal(committer=committer, profile=profile)


def test_runtime_repair_fixed_seed_reseal_requires_exactly_one_runtime_change(
    tmp_path: Path,
) -> None:
    committer, values = _profiles(tmp_path)
    values["seed_derivation"] = RUNTIME_REPAIR_M0_SEED_RESEAL
    profile = M0QualificationProfile.model_validate(values)

    with pytest.raises(AiVideoError, match="fixed-seed"):
        validate_m0_fixed_seed_reseal(committer=committer, profile=profile)


def test_runtime_repair_fixed_seed_reseal_rejects_prompt_drift(
    tmp_path: Path,
) -> None:
    committer, values = _profiles(tmp_path)
    values["seed_derivation"] = RUNTIME_REPAIR_M0_SEED_RESEAL
    values["prompt_sha256"] = "8" * 64
    _replace_runtime(
        values,
        name="comfyui",
        version="0.33.0+e01fb4c56b7a",
        content_hash="9" * 64,
    )
    profile = M0QualificationProfile.model_validate(values)

    with pytest.raises(AiVideoError, match="fixed-seed"):
        validate_m0_fixed_seed_reseal(committer=committer, profile=profile)
