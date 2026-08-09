import pytest
from pydantic import ValidationError

from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    DurationPolicy,
    RendererPolicy,
    SourceReference,
    Story,
    StoryBeat,
)


def make_story() -> Story:
    return Story(
        artifact_id="story-main",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-story-1",
        source_provenance=[SourceReference(kind="user_input", reference="brief-1")],
        language="zh-CN",
        logline="一位侦探追查失踪的记忆。",
        synopsis="侦探在三幕故事中找到真相。",
        beats=[StoryBeat(beat_id="beat-1", summary="案件出现")],
        source_references=["source-novel-1"],
    )


def test_semantic_hash_ignores_mapping_order_and_content_hash():
    assert canonical_sha256({"b": 2, "a": 1, "content_hash": "x"}) == canonical_sha256(
        {"content_hash": "y", "a": 1, "b": 2}
    )


def test_sealed_artifact_detects_content_change():
    sealed = seal_artifact(make_story())
    assert verify_artifact_hash(sealed)
    assert not verify_artifact_hash(sealed.model_copy(update={"logline": "不同内容"}))


def test_artifact_hash_covers_receipt_and_provenance_envelope():
    sealed = seal_artifact(make_story())
    assert not verify_artifact_hash(
        sealed.model_copy(update={"creation_receipt_id": "receipt-story-2"})
    )


def test_domain_models_reject_unknown_fields():
    data = make_story().model_dump()
    data["unexpected"] = True
    with pytest.raises(ValidationError):
        Story.model_validate(data)


def test_domain_models_are_frozen():
    story = make_story()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        story.logline = "不允许就地修改"


def test_fixed_duration_requires_seconds():
    with pytest.raises(ValidationError, match="requires seconds"):
        DurationPolicy(mode="fixed")


def test_duration_bounds_must_be_ordered():
    with pytest.raises(ValidationError, match="cannot exceed"):
        DurationPolicy(mode="content_driven", minimum_seconds=5, maximum_seconds=4)


def test_renderer_default_must_be_allowed():
    with pytest.raises(ValidationError, match="must be present"):
        RendererPolicy(allowed=["remotion"], default_preference="hyperframes")
