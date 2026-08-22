from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from ai_video.production.models import (
    ProductionManifest,
    RecoveryDisposition,
    RecoveryItem,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_execution_stack_materialization_source_path,
)
from ai_video.production.video_execution_stack import GenerationExecutionStackIdentity
from ai_video.production.video_transition import (
    ContinuityTransitionPolicy,
    P0QualificationInput,
    P0QualificationPreparedReceipt,
    RealShotValidationSet,
)


class _P0RecoveryOwner(Protocol):
    _project_root: Path

    def _p0_active_recovery_items(
        self, manifest: ProductionManifest
    ) -> tuple[RecoveryItem, ...]: ...

    def _recovery_namespace_entries(
        self, directory: Path, pattern: re.Pattern[str]
    ) -> tuple[tuple[Path, re.Match[str]], ...]: ...


def p0_orphan_items(
    owner: _P0RecoveryOwner,
    manifest: ProductionManifest,
) -> tuple[RecoveryItem, ...]:
    active = {item.path for item in owner._p0_active_recovery_items(manifest)}
    namespaces = (
        (
            owner._project_root / "state/video-qualification/execution-stacks",
            re.compile(r"^(?P<hash>[0-9a-f]{64})\.json$"),
            GenerationExecutionStackIdentity,
            "execution_stack_hash",
        ),
        (
            owner._project_root / "state/video-qualification/transition-policies",
            re.compile(r"^(?P<hash>[0-9a-f]{64})\.json$"),
            ContinuityTransitionPolicy,
            "policy_hash",
        ),
        (
            owner._project_root / "state/video-qualification/validation-sets",
            re.compile(r"^(?P<hash>[0-9a-f]{64})\.json$"),
            RealShotValidationSet,
            "content_hash",
        ),
        (
            owner._project_root / "state/video-qualification/prepared-receipts",
            re.compile(r"^(?P<hash>[0-9a-f]{64})\.json$"),
            P0QualificationPreparedReceipt,
            "content_hash",
        ),
        (
            owner._project_root / "state/video-qualification/inputs",
            re.compile(
                r"^(?:inventory|calibration_fixture|rubric|effect_budget|human_freeze)\."
                r"(?P<hash>[0-9a-f]{64})\.json$"
            ),
            P0QualificationInput,
            "content_hash",
        ),
    )
    items: list[RecoveryItem] = []
    for directory, pattern, model_type, identity_field in namespaces:
        for path, match in owner._recovery_namespace_entries(directory, pattern):
            relative = path.relative_to(owner._project_root)
            if relative in active:
                continue
            try:
                snapshot = _read_regular_file_nofollow(
                    path,
                    contained_by=owner._project_root / "state",
                )
                model = model_type.model_validate_json(snapshot.data)
                if getattr(model, identity_field) != match.group("hash"):
                    continue
            except (OSError, ValidationError, ValueError):
                continue
            items.append(
                RecoveryItem(
                    path=relative,
                    disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                    sha256=snapshot.file_sha256,
                )
            )
    for kind in ("profile", "compiler", "workflow"):
        directory = (
            owner._project_root
            / canonical_execution_stack_materialization_source_path(
                kind,
                "0" * 64,
            ).parent
        )
        pattern = re.compile(r"^(?P<hash>[0-9a-f]{64})\.bin$")
        for path, match in owner._recovery_namespace_entries(directory, pattern):
            relative = path.relative_to(owner._project_root)
            if relative in active:
                continue
            try:
                snapshot = _read_regular_file_nofollow(
                    path,
                    contained_by=owner._project_root / "state",
                )
            except (OSError, ValueError):
                continue
            if snapshot.file_sha256 != match.group("hash"):
                continue
            items.append(
                RecoveryItem(
                    path=relative,
                    disposition=RecoveryDisposition.ORPHAN_PRESERVED,
                    sha256=snapshot.file_sha256,
                )
            )
    return tuple(items)
