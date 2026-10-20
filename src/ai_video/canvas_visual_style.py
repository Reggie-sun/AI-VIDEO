"""Exact, read-only visual-style declarations for Canvas Shot references."""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Literal

from pydantic import Field, ValidationError, field_validator

from ai_video.production.artifact_contracts import StrictModel

_SHA256 = r"^[0-9a-f]{64}$"
_CHARACTER_REFERENCE = "character_reference"
_SCENE_REFERENCE = "scene_reference"
_FRAME_ROLES = {"approved_keyframe", "last_frame", "previous_shot_terminal"}


class _StyleSource(StrictModel):
    asset_id: str = Field(min_length=1, strict=True)
    asset_sha256: str = Field(pattern=_SHA256, strict=True)


class _StyleReview(StrictModel):
    asset_id: str = Field(min_length=1, strict=True)
    asset_sha256: str = Field(pattern=_SHA256, strict=True)
    role: str = Field(min_length=1, strict=True)
    owner_id: str = Field(min_length=1, strict=True)
    current_style_sha256: str = Field(pattern=_SHA256, strict=True)
    disposition: Literal["current_style", "identity_layout_only"]
    observation: str = Field(min_length=1, strict=True)
    scope_text: str | None = Field(default=None, strict=True)
    reason: str | None = Field(default=None, strict=True)
    covered_owner_ids: tuple[str, ...] = ()

    @field_validator("asset_id", "role", "owner_id", "observation")
    @classmethod
    def _nonblank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("must not be blank")
        return value


class _VisualStyleDeclaration(StrictModel):
    contract_version: Literal["canvas-visual-style/1"]
    source: _StyleSource
    reviews: tuple[_StyleReview, ...]
    scope: Literal["whole_shot", "mixed_reference_guidance"] = "whole_shot"
    mixed_reference_reason: str | None = Field(default=None, strict=True)

def _owners(row: object) -> tuple[set[str], str | None, set[str]]:
    shot = row.get("shot") if isinstance(row, Mapping) else None
    if not isinstance(shot, Mapping):
        return set(), None, set()
    characters = shot.get("character_ids", ())
    character_ids = {value for value in characters if isinstance(value, str) and value.strip()} \
        if isinstance(characters, (list, tuple, set)) else set()
    scene_id = shot.get("scene_id")
    visible_character_ids = set(character_ids)
    generation = row.get("generation", {}) if isinstance(row, Mapping) else {}
    generation_intent = (generation.get("generation_intent")
        if isinstance(generation, Mapping) else None)
    try:
        from ai_video.production.video_requirement import GenerationIntent

        typed_intent = GenerationIntent.model_validate(generation_intent)
    except (ValidationError, TypeError, ValueError):
        pass
    else:
        performance = typed_intent.performance_intent
        if performance is not None:
            offscreen = {
                direction.character_id
                for direction in performance.character_directions
                if direction.visibility == "offscreen" and direction.offscreen_reason is not None
            }
            visible_character_ids.difference_update(offscreen)
    return (character_ids,
        scene_id if isinstance(scene_id, str) and scene_id.strip() else None,
        visible_character_ids)


def _base_report(row: object, *, declaration_status: str, coverage: str,
                 issues: tuple[str, ...] = (), source: dict | None = None,
                 selected_images: int = 0, reviewed_images: int = 0,
                 exclusions: tuple[dict, ...] = (),
                 style_application: str = "NOT_EVALUATED") -> dict:
    characters, scene_id, visible_characters = _owners(row)
    return {
        "schema_version": "canvas-visual-style-report/1",
        "declaration_status": declaration_status,
        "coverage": coverage,
        "style_application": style_application,
        "source": source,
        "target_owners": {"characters": len(characters),
            "required_visible_characters": len(visible_characters),
            "scenes": int(scene_id is not None)},
        "reference_counts": {"selected_images": selected_images, "reviewed_images": reviewed_images},
        "exclusions": list(exclusions),
        "issues": list(issues),
        "aesthetic_acceptance": "NOT_EVALUATED",
        "source_consumption": "NOT_EVALUATED",
    }


def visual_style_report(row: object, registry: object) -> dict:
    """Report exact style-reference coverage without judging image aesthetics.

    Legacy rows remain readable as ``NOT_DECLARED``. For declared rows, every
    selected image reference must have one exact review binding, and every visible
    target Character and Scene must have an explicit owner binding.
    """
    declaration_raw = row.get("visual_style") if isinstance(row, Mapping) else None
    if declaration_raw is None:
        return _base_report(row, declaration_status="NOT_DECLARED", coverage="NOT_DECLARED",
            style_application="NOT_DECLARED")

    try:
        declaration = _VisualStyleDeclaration.model_validate(declaration_raw)
    except (ValidationError, TypeError, ValueError):
        return _base_report(row, declaration_status="INVALID", coverage="INCOMPLETE",
            issues=("invalid_declaration",), style_application="NOT_EVALUATED")

    issues: list[str] = []
    if (declaration.scope == "mixed_reference_guidance"
            and not (declaration.mixed_reference_reason or "").strip()):
        issues.append("mixed_reference_reason_missing")
    if (declaration.scope == "whole_shot"
            and any(review.disposition == "identity_layout_only" for review in declaration.reviews)):
        issues.append("whole_shot_style_incomplete")
    assets_raw = getattr(registry, "assets", ())
    by_id: dict[str, list[object]] = {}
    if isinstance(assets_raw, (list, tuple)):
        for asset in assets_raw:
            asset_id = getattr(asset, "asset_id", None)
            if isinstance(asset_id, str):
                by_id.setdefault(asset_id, []).append(asset)

    generation = row.get("generation", {}) if isinstance(row, Mapping) else {}
    references = generation.get("references", ()) if isinstance(generation, Mapping) else ()
    if not isinstance(references, (list, tuple)):
        references = ()
        issues.append("invalid_generation_references")

    image_bindings: dict[tuple[str, str, str | None], object] = {}
    characters, scene_id, visible_characters = _owners(row)
    target_owner_ids = characters | ({scene_id} if scene_id is not None else set())
    covered_characters: set[str] = set()
    covered_scenes: set[str] = set()

    for reference in references:
        if not isinstance(reference, Mapping):
            issues.append("invalid_generation_references")
            continue
        asset_id = reference.get("asset_id")
        role = reference.get("role")
        owner_id = reference.get("owner_id")
        if not isinstance(asset_id, str) or not asset_id.strip() or not isinstance(role, str):
            issues.append("invalid_generation_references")
            continue
        matches = by_id.get(asset_id, ())
        if len(matches) != 1:
            issues.append("image_reference_missing_from_registry")
            continue
        asset = matches[0]
        mime_type = getattr(asset, "mime_type", "")
        if not isinstance(mime_type, str) or not mime_type.lower().startswith("image/"):
            continue

        binding = (asset_id, role, owner_id if isinstance(owner_id, str) else None)
        if binding in image_bindings:
            issues.append("duplicate_image_reference")
        else:
            image_bindings[binding] = asset

        if owner_id is None or not isinstance(owner_id, str) or not owner_id.strip():
            issues.append("image_reference_owner_missing")
        elif role == _CHARACTER_REFERENCE:
            if owner_id not in characters:
                issues.append("image_reference_owner_mismatch")
            else:
                covered_characters.add(owner_id)
        elif role == _SCENE_REFERENCE:
            if scene_id is None or owner_id != scene_id:
                issues.append("image_reference_owner_mismatch")
            else:
                covered_scenes.add(owner_id)
        elif role in {"approved_keyframe", "last_frame"}:
            if owner_id != row["shot"]["shot_id"]:
                issues.append("image_reference_owner_mismatch")
        elif role != "previous_shot_terminal" and owner_id not in target_owner_ids:
            issues.append("image_reference_owner_mismatch")

    source_asset_matches = [asset for asset in by_id.get(declaration.source.asset_id, ())
        if getattr(asset, "sha256", None) == declaration.source.asset_sha256
        and isinstance(getattr(asset, "mime_type", None), str)
        and asset.mime_type.lower().startswith("image/")]
    source_id_selected = any(key[0] == declaration.source.asset_id for key in image_bindings)
    source_selected = source_id_selected and any(
        asset in source_asset_matches for key, asset in image_bindings.items()
        if key[0] == declaration.source.asset_id)
    if not source_selected:
        issues.append("source_anchor_sha_mismatch" if source_id_selected else "source_anchor_not_selected")
    review_by_binding: dict[tuple[str, str, str], _StyleReview] = {}
    exclusions: list[dict] = []
    shot = row.get("shot", {}) if isinstance(row, Mapping) else {}
    intent = shot.get("intent") if isinstance(shot, Mapping) else None
    for review in declaration.reviews:
        key = (review.asset_id, review.role, review.owner_id)
        if key in review_by_binding:
            issues.append("duplicate_review")
        else:
            review_by_binding[key] = review
        selected_asset = by_id.get(review.asset_id, ())
        selected = image_bindings.get(key)
        review_asset_matches = selected is not None and (
            len(selected_asset) == 1 and review.asset_sha256 == getattr(selected, "sha256", None))
        if selected is None:
            issues.append("extra_review")
        elif not review_asset_matches:
            issues.append("review_asset_sha_mismatch")
        style_is_current = review.current_style_sha256 == declaration.source.asset_sha256
        if not style_is_current:
            issues.append("stale_style_review")
        if review.covered_owner_ids:
            targets = set(review.covered_owner_ids)
            if (review.role not in _FRAME_ROLES or len(targets) != len(review.covered_owner_ids)
                    or not targets <= target_owner_ids):
                issues.append("invalid_frame_target_coverage")
            elif review_asset_matches and style_is_current:
                covered_characters.update(targets & characters)
                covered_scenes.update(targets & ({scene_id} if scene_id is not None else set()))
        if review.disposition == "identity_layout_only":
            scope_present = bool(review.scope_text and review.scope_text.strip())
            scope_matches = scope_present and isinstance(intent, str) and review.scope_text in intent
            reason_present = bool(review.reason and review.reason.strip())
            if not scope_present:
                issues.append("identity_layout_scope_missing")
            elif not scope_matches:
                issues.append("identity_layout_scope_not_in_intent")
            if not reason_present:
                issues.append("identity_layout_reason_missing")
            if (review_asset_matches and style_is_current and scope_matches and reason_present
                    and review.asset_id != declaration.source.asset_id):
                exclusions.append({"asset_id": review.asset_id, "role": review.role,
                    "owner_id": review.owner_id, "scope_text": review.scope_text,
                    "reason": review.reason})

    if not visible_characters <= covered_characters:
        issues.append("missing_character_reference")
    if scene_id is None or scene_id not in covered_scenes:
        issues.append("missing_scene_reference")
    for asset_id, role, owner_id in image_bindings:
        if owner_id is None or (asset_id, role, owner_id) not in review_by_binding:
            issues.append("missing_review")

    anchor_reviews = [review for review in declaration.reviews
        if review.asset_id == declaration.source.asset_id
        and review.asset_sha256 == declaration.source.asset_sha256]
    if not any(review.disposition == "current_style" for review in anchor_reviews):
        issues.append("source_anchor_not_current_style")

    if source_selected:
        source = {"source_kind": "selected_reference_anchor",
            "asset_id": declaration.source.asset_id,
            "asset_sha256": declaration.source.asset_sha256}
    else:
        source = None
    unique_issues = tuple(dict.fromkeys(issues))
    if declaration.scope == "mixed_reference_guidance":
        style_application = "PARTIAL_REFERENCE_STYLE"
    elif "whole_shot_style_incomplete" in unique_issues:
        style_application = "WHOLE_SHOT_STYLE_INCOMPLETE"
    elif unique_issues:
        style_application = "INCOMPLETE"
    else:
        style_application = "ALL_REFERENCES_CURRENT_STYLE"
    reviewed_images = sum(1 for key in image_bindings
        if key[2] is not None and key in review_by_binding)
    return _base_report(row, declaration_status="VALID",
        coverage="INCOMPLETE" if unique_issues else "COMPLETE", issues=unique_issues,
        source=source, selected_images=len(image_bindings), reviewed_images=reviewed_images,
        exclusions=tuple(exclusions), style_application=style_application)


def require_canvas_visual_style(row: object, registry: object) -> dict:
    """Return the report, rejecting malformed or incomplete declarations safely."""
    report = visual_style_report(row, registry)
    if report["coverage"] == "INCOMPLETE":
        raise ValueError("Canvas visual-style declaration is invalid or incomplete.")
    return report


def require_prepared_visual_style(row: object, prepared: object) -> None:
    """Require the prepared provider request to carry exact, reviewed image evidence."""
    declaration_raw = row.get("visual_style") if isinstance(row, Mapping) else None
    if declaration_raw is None:
        return None
    binding = getattr(prepared, "execution_binding", None)
    if binding is None:
        return None

    try:
        declaration = _VisualStyleDeclaration.model_validate(declaration_raw)
        from ai_video.canvas_planning import _ROLES
        from ai_video.planning import AssetRole
        from ai_video.production._video_requirement_routing import native_binding_role

        requirement = binding.projection.requirement
        image_evidence = tuple(item for item in requirement.asset_evidence
            if isinstance(item.mime_type, str) and item.mime_type.lower().startswith("image/"))
        declared = Counter(
            (review.asset_id, review.asset_sha256,
             _ROLES[AssetRole(review.role)], review.owner_id)
            for review in declaration.reviews
        )
        evidence = Counter(
            (item.asset_id, item.asset_sha256, item.role, item.canonical_owner_id)
            for item in image_evidence
        )
        if not image_evidence or declared != evidence:
            raise ValueError

        request = prepared.resolved_request
        expected_bindings = Counter(
            (item.asset_id, item.asset_sha256, native_binding_role(item.role))
            for item in image_evidence
        )
        actual_bindings = Counter(
            (item.asset_id, item.asset_sha256, item.role)
            for item in request.image_bindings
        )
        if expected_bindings != actual_bindings:
            raise ValueError

        anchor = declaration.source
        if any(review.current_style_sha256 != anchor.asset_sha256
               for review in declaration.reviews):
            raise ValueError
        if not any(item.asset_id == anchor.asset_id and item.asset_sha256 == anchor.asset_sha256
                   for item in image_evidence) or not any(
            item.asset_id == anchor.asset_id and item.asset_sha256 == anchor.asset_sha256
            for item in request.image_bindings
        ):
            raise ValueError
        anchor_reviewed_current = any(
            review.asset_id == anchor.asset_id
            and review.asset_sha256 == anchor.asset_sha256
            and review.current_style_sha256 == anchor.asset_sha256
            and review.disposition == "current_style"
            for review in declaration.reviews
        )
        if not anchor_reviewed_current:
            raise ValueError
        if (declaration.scope == "mixed_reference_guidance"
                and not (declaration.mixed_reference_reason or "").strip()):
            raise ValueError
        if (declaration.scope == "whole_shot"
                and any(review.disposition == "identity_layout_only" for review in declaration.reviews)):
            raise ValueError
        prompt = request.prompt_text
        for review in declaration.reviews:
            if review.disposition == "identity_layout_only" and (
                not review.scope_text or review.scope_text not in prompt
                or not review.reason or not review.reason.strip()
            ):
                raise ValueError
    except (AttributeError, KeyError, TypeError, ValueError, ValidationError):
        raise ValueError("Canvas visual-style binding does not match the prepared generation request.") from None
    return None
