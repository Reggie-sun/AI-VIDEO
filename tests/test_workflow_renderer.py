import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.models import (
    CharacterProfile,
    CharacterRefBinding,
    ClipOutputBinding,
    DefaultsConfig,
    JsonPathBinding,
    ShotSpec,
    WorkflowBinding,
)
from ai_video.workflow_renderer import (
    collect_clip_artifact,
    render_workflow,
    validate_api_workflow,
)


def binding() -> WorkflowBinding:
    return WorkflowBinding(
        positive_prompt=JsonPathBinding(path=["6", "inputs", "text"]),
        negative_prompt=JsonPathBinding(path=["7", "inputs", "text"]),
        seed=JsonPathBinding(path=["3", "inputs", "seed"]),
        init_image=JsonPathBinding(path=["12", "inputs", "image"]),
        output_prefix=JsonPathBinding(path=["42", "inputs", "filename_prefix"]),
        character_refs=[
            CharacterRefBinding(
                character="hero",
                image_path=["20", "inputs", "image"],
                weight_path=["25", "inputs", "weight"],
            )
        ],
        clip_output=ClipOutputBinding(
            node="42", kind="gifs", extensions=[".mp4"], select="first"
        ),
    )


def workflow() -> dict:
    return {
        "3": {"class_type": "KSampler", "inputs": {"seed": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},
        "12": {"class_type": "LoadImage", "inputs": {"image": ""}},
        "20": {"class_type": "LoadImage", "inputs": {"image": ""}},
        "25": {"class_type": "IPAdapter", "inputs": {"weight": 0.0}},
        "42": {"class_type": "VHS_VideoCombine", "inputs": {"filename_prefix": ""}},
    }


def test_rejects_ui_workflow_json():
    with pytest.raises(AiVideoError) as exc:
        validate_api_workflow({"nodes": [], "links": []})
    assert exc.value.code is ErrorCode.WORKFLOW_INVALID
    assert "API-format" in exc.value.user_message


def test_render_workflow_replaces_bound_fields(tmp_path):
    shot = ShotSpec(id="shot_001", prompt="walks in", characters=["hero"])
    character = CharacterProfile(
        id="hero",
        name="Hero",
        description="same face",
        reference_images=[tmp_path / "hero.png"],
    )
    rendered = render_workflow(
        template=workflow(),
        binding=binding(),
        shot=shot,
        defaults=DefaultsConfig(seed=100, style_prompt="cinematic", negative_prompt="blur"),
        characters={"hero": character},
        shot_index=0,
        chain_image_name="prev.png",
        character_image_names={"hero": "hero_uploaded.png"},
        output_prefix="demo/run/shot_001/attempt_1",
    )
    assert rendered.workflow["6"]["inputs"]["text"] == "cinematic, same face, walks in"
    assert rendered.workflow["7"]["inputs"]["text"] == "blur"
    assert rendered.workflow["3"]["inputs"]["seed"] == 100
    assert rendered.workflow["12"]["inputs"]["image"] == "prev.png"
    assert rendered.workflow["20"]["inputs"]["image"] == "hero_uploaded.png"
    assert rendered.workflow["25"]["inputs"]["weight"] == 1.0
    assert rendered.workflow["42"]["inputs"]["filename_prefix"] == "demo/run/shot_001/attempt_1"


def test_collect_clip_artifact_filters_extensions():
    history = {
        "outputs": {
            "42": {
                "gifs": [
                    {"filename": "preview.gif", "subfolder": "", "type": "output"},
                    {"filename": "clip.mp4", "subfolder": "demo", "type": "output"},
                ]
            }
        }
    }
    artifact = collect_clip_artifact(history, binding().clip_output)
    assert artifact.filename == "clip.mp4"
    assert artifact.subfolder == "demo"
    assert artifact.extension == ".mp4"
