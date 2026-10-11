from copy import deepcopy

import pytest

from ai_video.canvas_subject import subject_material_references


def subject_node():
    return {
        "id": "character",
        "type": "subject",
        "data": {
            "title": "Character",
            "main": {"refType": "resource_snapshot", "resourceId": "main-png"},
            "auxiliaries": [
                {"refType": "resource_snapshot", "resourceId": "front-png"},
                {"refType": "resource_snapshot", "resourceId": "back-png"},
            ],
            "provenance": {"origin_subject_id": "source-character"},
        },
    }


def test_subject_material_references_preserve_main_and_auxiliary_order_without_mutation():
    source = subject_node()
    before = deepcopy(source)

    assert subject_material_references(source) == {
        "main": {"ref_type": "resource_snapshot", "resource_id": "main-png"},
        "auxiliaries": [
            {"index": 0, "ref_type": "resource_snapshot", "resource_id": "front-png"},
            {"index": 1, "ref_type": "resource_snapshot", "resource_id": "back-png"},
        ],
    }
    assert source == before


def test_subject_without_auxiliaries_is_supported():
    source = subject_node()
    source["data"].pop("auxiliaries")

    assert subject_material_references(source) == {
        "main": {"ref_type": "resource_snapshot", "resource_id": "main-png"},
        "auxiliaries": [],
    }


@pytest.mark.parametrize(
    "damage",
    ["not_subject", "missing_main", "wrong_main_ref_type", "empty_main_id",
     "aux_not_list", "aux_not_object", "wrong_aux_ref_type", "empty_aux_id",
     "main_aux_duplicate", "duplicate_aux"],
)
def test_malformed_subject_snapshots_are_rejected(damage):
    source = subject_node()
    data = source["data"]
    if damage == "not_subject":
        source["type"] = "image"
    elif damage == "missing_main":
        data.pop("main")
    elif damage == "wrong_main_ref_type":
        data["main"]["refType"] = "resource"
    elif damage == "empty_main_id":
        data["main"]["resourceId"] = " "
    elif damage == "aux_not_list":
        data["auxiliaries"] = {"refType": "resource_snapshot", "resourceId": "aux"}
    elif damage == "aux_not_object":
        data["auxiliaries"] = ["aux"]
    elif damage == "wrong_aux_ref_type":
        data["auxiliaries"][0]["refType"] = "upload"
    elif damage == "empty_aux_id":
        data["auxiliaries"][0]["resourceId"] = ""
    elif damage == "main_aux_duplicate":
        data["auxiliaries"][0]["resourceId"] = data["main"]["resourceId"]
    else:
        data["auxiliaries"].append(deepcopy(data["auxiliaries"][0]))

    with pytest.raises(ValueError, match="subject"):
        subject_material_references(source)
