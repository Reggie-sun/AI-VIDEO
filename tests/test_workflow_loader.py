import json
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.workflow_loader import load_workflow_template


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_workflow_template_accepts_api_prompt(tmp_path):
    template = tmp_path / "api.json"
    template.write_text(
        '{"3":{"class_type":"KSampler","inputs":{"seed":1}}}',
        encoding="utf-8",
    )

    loaded = load_workflow_template(template)

    assert loaded["3"]["class_type"] == "KSampler"
    assert loaded["3"]["inputs"]["seed"] == 1


def test_load_workflow_template_converts_wan22_ui_workflow():
    loaded = load_workflow_template(FIXTURE_DIR / "wan22_i2v_ui.json")

    assert "549" in loaded
    assert "554" not in loaded
    assert "556" not in loaded
    assert "558" not in loaded
    assert loaded["549"]["class_type"] == "Textbox"
    assert loaded["549"]["inputs"]["text"] == ""
    assert loaded["521"]["inputs"]["image"] == "0 (559).jpg"
    assert loaded["561"]["inputs"]["value"] == 0
    assert loaded["548"]["inputs"]["positive_prompt"] == ["549", 0]
    assert loaded["548"]["inputs"]["negative_prompt"].startswith("still image")
    assert loaded["548"]["inputs"]["t5"] == ["559", 2]
    assert loaded["514"]["inputs"]["start_image"] == ["546", 0]
    assert loaded["514"]["inputs"]["num_frames"] == ["523", 0]
    assert loaded["28"]["inputs"]["vae"] == ["559", 3]
    assert loaded["30"]["inputs"]["filename_prefix"] == "WAN 2.2 FunCamera I2V"


def test_load_workflow_template_rejects_unknown_widget_mapping(tmp_path):
    template = tmp_path / "ui.json"
    template.write_text(
        '{"nodes":[{"id":1,"type":"MysteryNode","widgets_values":[1,2,3]}],"links":[]}',
        encoding="utf-8",
    )

    with pytest.raises(AiVideoError) as exc:
        load_workflow_template(template)

    assert exc.value.code is ErrorCode.WORKFLOW_INVALID
    assert "widget mapping" in exc.value.user_message.lower()


def test_load_workflow_template_flattens_nested_subgraph_ports(tmp_path):
    template = tmp_path / "subgraph.json"
    template.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": 1,
                        "type": "LoadImage",
                        "inputs": [],
                        "widgets_values": ["reference.png", "image"],
                    },
                    {
                        "id": 2,
                        "type": "subgraph-1",
                        "mode": 0,
                        "inputs": [
                            {"name": "image", "type": "IMAGE", "link": 1},
                            {
                                "name": "text",
                                "type": "STRING",
                                "widget": {"name": "text"},
                                "link": None,
                            },
                        ],
                        "widgets_values": ["bound prompt"],
                    },
                    {
                        "id": 3,
                        "type": "SaveImage",
                        "inputs": [{"name": "images", "link": 2}],
                        "widgets_values": ["result"],
                    },
                ],
                "links": [
                    [1, 1, 0, 2, 0, "IMAGE"],
                    [2, 2, 0, 3, 0, "IMAGE"],
                ],
                "definitions": {
                    "subgraphs": [
                        {
                            "id": "subgraph-1",
                            "inputs": [
                                {"name": "image", "type": "IMAGE", "linkIds": [10]},
                                {"name": "text", "type": "STRING", "linkIds": [11]},
                            ],
                            "outputs": [
                                {"name": "IMAGE", "type": "IMAGE", "linkIds": [12]}
                            ],
                            "nodes": [
                                {
                                    "id": 4,
                                    "type": "CLIPTextEncode",
                                    "inputs": [
                                        {"name": "image", "link": 10},
                                        {
                                            "name": "text",
                                            "widget": {"name": "text"},
                                            "link": 11,
                                        },
                                    ],
                                    "widgets_values": ["default prompt"],
                                }
                            ],
                            "links": [
                                {
                                    "id": 10,
                                    "origin_id": -10,
                                    "origin_slot": 0,
                                    "target_id": 4,
                                    "target_slot": 0,
                                },
                                {
                                    "id": 11,
                                    "origin_id": -10,
                                    "origin_slot": 1,
                                    "target_id": 4,
                                    "target_slot": 1,
                                },
                                {
                                    "id": 12,
                                    "origin_id": 4,
                                    "origin_slot": 0,
                                    "target_id": -20,
                                    "target_slot": 0,
                                },
                            ],
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    loaded = load_workflow_template(template)

    assert loaded["2:4"]["inputs"] == {
        "image": ["1", 0],
        "text": "bound prompt",
    }
    assert loaded["3"]["inputs"]["images"] == ["2:4", 0]
