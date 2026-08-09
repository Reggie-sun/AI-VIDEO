from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from ai_video.config import sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetRecord, AssetRegistrySnapshot
from ai_video.production.paths import resolve_contained_path


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.ASSET_REGISTRY_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def registry_semantic_sha256(registry: AssetRegistrySnapshot) -> str:
    payload = registry.model_dump(
        mode="json",
        exclude={"content_hash", "revision_id"},
    )
    return canonical_sha256(payload)


def _verify_asset(record: AssetRecord, root: Path, asset_root: Path) -> Path:
    try:
        resolved = resolve_contained_path(
            root,
            record.artifact_path,
            allowed_root=asset_root,
        )
    except ValueError as exc:
        raise _invalid(f"Asset path is unsafe: {record.asset_id}", str(exc)) from exc
    if not resolved.is_file():
        raise _invalid(f"Asset file does not exist: {record.asset_id}", str(resolved))
    try:
        size = resolved.stat().st_size
        digest = sha256_file(resolved)
    except OSError as exc:
        raise _invalid(f"Could not verify asset file: {record.asset_id}", str(exc)) from exc
    if size != record.size_bytes:
        raise _invalid(f"Asset size mismatch: {record.asset_id}", str(resolved))
    if digest != record.sha256:
        raise _invalid(f"Asset hash mismatch: {record.asset_id}", str(resolved))
    return resolved


def load_asset_registry(
    path: str | Path,
    project_root: str | Path,
    asset_root: str | Path,
) -> tuple[AssetRegistrySnapshot, dict[str, Path]]:
    root = Path(project_root).resolve()
    try:
        registry_path = resolve_contained_path(
            root,
            Path(path),
            allowed_root=root / "assets",
        )
        resolved_asset_root = Path(asset_root).resolve()
        resolved_asset_root.relative_to(root)
    except ValueError as exc:
        raise _invalid("Asset registry path configuration is unsafe.", str(exc)) from exc
    try:
        registry = AssetRegistrySnapshot.model_validate_json(
            registry_path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(f"Could not load asset registry: {registry_path}", str(exc)) from exc
    ids = [asset.asset_id for asset in registry.assets]
    if len(ids) != len(set(ids)):
        raise _invalid("Asset registry contains duplicate asset_id values.")
    if registry_semantic_sha256(registry) != registry.content_hash:
        raise _invalid("Asset registry content hash does not match.")
    if registry.revision_id != registry.content_hash:
        raise _invalid("Asset registry revision_id must equal content_hash.")
    if registry_path.name != f"registry.{registry.revision_id}.json":
        raise _invalid("Asset registry filename does not match revision_id.")
    asset_paths = {
        item.asset_id: _verify_asset(item, root, resolved_asset_root)
        for item in registry.assets
    }
    return registry, asset_paths
