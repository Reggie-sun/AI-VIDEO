"""Generation dependencies and CompositionSpec order are separate selections."""
from copy import deepcopy

import pytest

from ai_video.canvas_authoring import author_canvas_project
from test_canvas_authoring import direction, packet


def test_edit_order_does_not_reorder_generation_artifacts():
    data = direction()
    data["composition_order"] = ["b", "a"]
    before = deepcopy(data)
    bundle = author_canvas_project(packet=packet(), direction=data)
    assert data == before
    from ai_video.production.models import Storyboard
    storyboard = next(a for a in bundle.creative_artifacts if isinstance(a, Storyboard))
    assert storyboard.beats[0].shot_ids == ("one", "two")


@pytest.mark.parametrize("order", [["a"], ["a", "a"], ["a", "unknown"], "ab"])
def test_edit_order_rejects_omission_duplicate_unknown_and_string(order):
    data = direction()
    data["composition_order"] = order
    with pytest.raises(ValueError, match="composition_order"):
        author_canvas_project(packet=packet(), direction=data)
