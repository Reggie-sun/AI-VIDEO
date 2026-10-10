"""Reviewable authoring uses canonical artifacts, never source prose as approval."""
from copy import deepcopy

import pytest

from ai_video.canvas_authoring import author_canvas_project
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from test_canvas_sequence_packet import document
from scripts.canvas_sequence_packet import build_sequence_packet


def direction():
    data = {
        "project_id": "canvas-demo", "title": "Canvas demo", "language": "zh",
        "brief": {"objective": "Show an arrival", "audience": "General", "format": "short drama"},
        "story": {"logline": "An arrival", "synopsis": "A traveller arrives.",
                  "beats": [{"beat_id": "arrival", "summary": "Arrival"}]},
        "characters": [],
        "scenes": [{"scene_id": "road", "location": "road", "time": "day", "mood": "quiet"}],
        "storyboard": {"beats": [{"beat_id": "arrival", "scene_id": "road",
                                   "shot_ids": ["one", "two"], "narrative_intent": "Arrival"}]},
        "shots": [{"occurrence_id": node, "adaptation_reason": "Director authored a fixture intent",
                   "shot": {"shot_id": sid, "scene_id": "road", "storyboard_beat_id": "arrival",
                            "intent": "Enter the road", "duration_policy": {"mode": "fixed", "seconds": 1},
                            "visual_strategy": "generated_video", "generated_video_rationale": "Walking",
                            "required_asset_roles": [{"role": "primary_visual", "asset_ids": [],
                                                      "allowed_asset_types": ["video"]}]}}
                  for node, sid in (("a", "one"), ("b", "two"))],
    }
    data["shots"][1]["boundary"] = {"independent": True, "reason": "Explicit fixture scene reset"}
    return data


def packet():
    return build_sequence_packet(document(), {"node_ids": ["a", "b"]})


def test_authoring_is_pure_and_bootstraps_through_real_owner(tmp_path):
    source, data = packet(), direction()
    before = deepcopy((source, data))
    bundle = author_canvas_project(packet=source, direction=data)
    assert (source, data) == before
    assert list(tmp_path.iterdir()) == []
    assert bundle.project.delivery_profile.height == 480
    assert bundle.project.renderer_policy.default_preference == "hyperframes"
    assert all(verify_artifact_hash(a) for a in bundle.creative_artifacts)
    assert len(bundle.adaptations) == 2
    assert bundle.adaptations[0]["original"] == source["units"][0]["source_text"]
    committer = ProductionStateCommitter(tmp_path)
    bundle.bootstrap(committer=committer, attempt_id="author-fixture")
    reopened = load_production_project(tmp_path / "project.yaml")
    assert [s.shot_id for s in reopened.shots] == ["one", "two"]
    assert reopened.characters == ()
    assert reopened.shots[0].dialogue == ""
    assert reopened.project.artifacts.shots[0].content_hash == reopened.shots[0].content_hash


@pytest.mark.parametrize("damage", ["occurrence", "order", "identity", "reason", "dialogue", "hash"])
def test_authoring_rejects_ambiguous_or_forged_data(damage):
    data = direction()
    if damage == "occurrence":
        data["shots"][1]["occurrence_id"] = "a"
    elif damage == "order":
        data["shots"].reverse()
    elif damage == "identity":
        data["shots"][0]["shot"]["content_hash"] = "f" * 64
    elif damage == "reason":
        data["shots"][0].pop("adaptation_reason")
    elif damage == "dialogue":
        data["shots"][0]["source_dialogue"] = "Stay."
        data["shots"][0]["shot"]["dialogue"] = "Go."
    else:
        data["story"]["creation_receipt_id"] = "invented"
    with pytest.raises(ValueError):
        author_canvas_project(packet=packet(), direction=data)


@pytest.mark.parametrize("ratio,dimensions", [("16:9", (854, 480)), ("9:16", (480, 854)), ("1:1", (480, 480))])
def test_default_480p_preserves_observed_framing(ratio, dimensions):
    source = packet()
    for unit in source["units"]:
        unit["observed_parameters"]["aspectRatio"] = ratio
    bundle = author_canvas_project(packet=source, direction=direction())
    assert (bundle.project.delivery_profile.width, bundle.project.delivery_profile.height) == dimensions
    assert all(u["observed_parameters"]["aspectRatio"] == ratio for u in source["units"])


def test_mixed_source_framing_requires_an_explicit_director_decision():
    source = packet()
    source["units"][0]["observed_parameters"]["aspectRatio"] = "16:9"
    source["units"][1]["observed_parameters"]["aspectRatio"] = "9:16"
    with pytest.raises(ValueError, match="mixed source aspect ratios"):
        author_canvas_project(packet=source, direction=direction())
    data = direction()
    data["delivery_profile"] = {"width": 854, "height": 480, "fps": 24}
    assert author_canvas_project(packet=source, direction=data).project.delivery_profile.width == 854
