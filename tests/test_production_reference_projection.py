"""Reference conditioning keeps semantic inputs separate from frame anchors."""

import pytest
from pydantic import ValidationError

from ai_video.production.video_requirement import (
    AudioNeed, GenerationOperation, OutputNeed,
    ProviderNeutralGenerationIntentProjection, QualityNeed, SemanticReferenceRole,
)
from tests.test_production_video_intent_validation import _complete_intent, _compatible_fl2va


def projection(*, roles=(), operation=GenerationOperation.AUTO, conditioning=None, intent=None):
    return ProviderNeutralGenerationIntentProjection.create(
        generation_intent=intent or _complete_intent(),
        generation_operation=operation, semantic_reference_roles=roles,
        conditioning_compatibility=conditioning,
        output_need=OutputNeed(timing_mode="frame_count", frame_count=124, fps=24,
                              width=1344, height=768, aspect_ratio="16:9", container_mime="video/mp4"),
        audio_need=AudioNeed.REQUIRED, quality_need=QualityNeed(objective_tier="preview"),
    )


@pytest.mark.parametrize("roles", [
    (SemanticReferenceRole.IDENTITY, SemanticReferenceRole.SCENE, SemanticReferenceRole.AUDIO_REFERENCE),
    (SemanticReferenceRole.VIDEO_REFERENCE,),
    (SemanticReferenceRole.AUDIO_REFERENCE,),
])
def test_rich_reference_projection_uses_exact_references_without_frame_attestation(roles):
    result = projection(roles=roles)
    assert result.conditioning_compatibility is None
    assert result.generation_intent.primary_camera_motion == _complete_intent().primary_camera_motion
    assert ProviderNeutralGenerationIntentProjection.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("roles", [(), (SemanticReferenceRole.FIRST_FRAME,),
                                   (SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.IDENTITY)])
def test_frame_or_unspecified_auto_projection_still_requires_conditioning(roles):
    with pytest.raises(ValidationError, match="requires conditioning"):
        projection(roles=roles)


def test_reference_projection_rejects_fabricated_frame_attestation():
    with pytest.raises(ValidationError, match="conditioning compatibility"):
        projection(roles=(SemanticReferenceRole.SCENE,), conditioning=_compatible_fl2va())


def test_reference_projection_still_requires_complete_rich_camera_intent():
    incomplete = _complete_intent().model_copy(update={"performance_intent": None})
    with pytest.raises(ValidationError, match="complete rich generation intent"):
        projection(roles=(SemanticReferenceRole.SCENE,), intent=incomplete)
