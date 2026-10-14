from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ai_video.errors import AiVideoError, ErrorCode

if TYPE_CHECKING:
    from ai_video.production.comfy_image import (
        LocalImageBinding,
        LocalImageExecutionProfile,
    )


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        ErrorCode.IMAGE_REQUEST_INVALID,
        message,
        detail,
        retryable=False,
    )


SEALED_NODE_CLASSES = {
    "qwen_image_edit_2511_local": {
        "170:145": "ModelSamplingAuraFlow",
        "170:146": "VAELoader",
        "170:147": "FluxKontextMultiReferenceLatentMethod",
        "170:148": "FluxKontextMultiReferenceLatentMethod",
        "170:149": "TextEncodeQwenImageEditPlus",
        "170:151": "TextEncodeQwenImageEditPlus",
        "170:152": "CFGNorm",
        "170:156": "VAEEncode",
        "170:158": "VAEDecode",
        "170:160": "ImageScale",
        "170:161": "UNETLoader",
        "170:162": "CLIPLoader",
        "170:169": "KSampler",
        "41": "LoadImage",
        "83": "LoadImage",
        "9": "SaveImage",
    },
    "qwen_image_edit_2511_masked_local": {
        "170:145": "ModelSamplingAuraFlow",
        "170:146": "VAELoader",
        "170:147": "FluxKontextMultiReferenceLatentMethod",
        "170:148": "FluxKontextMultiReferenceLatentMethod",
        "170:149": "TextEncodeQwenImageEditPlus",
        "170:151": "TextEncodeQwenImageEditPlus",
        "170:152": "CFGNorm",
        "170:156": "VAEEncode",
        "170:158": "VAEDecode",
        "170:160": "ImageScale",
        "170:161": "UNETLoader",
        "170:162": "CLIPLoader",
        "170:169": "KSampler",
        "170:172": "ImageToMask",
        "170:173": "SetLatentNoiseMask",
        "170:174": "ImageCompositeMasked",
        "41": "LoadImage",
        "83": "LoadImage",
        "84": "LoadImage",
        "9": "SaveImage",
    },
    "flux2_klein_4b_local": {
        "76": "LoadImage",
        "81": "LoadImage",
        "92:101": "KSamplerSelect",
        "92:102": "Flux2Scheduler",
        "92:103": "CFGGuider",
        "92:104": "SamplerCustomAdvanced",
        "92:105": "VAEDecode",
        "92:106": "RandomNoise",
        "92:107": "UNETLoader",
        "92:108": "CLIPLoader",
        "92:109": "CLIPTextEncode",
        "92:110": "VAELoader",
        "92:111": "ImageScale",
        "92:112:115": "ReferenceLatent",
        "92:112:116": "VAEEncode",
        "92:112:117": "ReferenceLatent",
        "92:113": "EmptyFlux2LatentImage",
        "92:114": "GetImageSize",
        "92:84:118": "ReferenceLatent",
        "92:84:119": "VAEEncode",
        "92:84:120": "ReferenceLatent",
        "92:85": "ImageScaleToTotalPixels",
        "92:86": "CLIPTextEncode",
        "94": "SaveImage",
    },
}


def input_edge(workflow: dict[str, Any], node_id: str, input_name: str) -> Any:
    return workflow.get(node_id, {}).get("inputs", {}).get(input_name)


def loader_consumers(
    workflow: dict[str, Any], loader_ids: set[str]
) -> set[tuple[str, str, str]]:
    consumers = set()
    for node_id, node in workflow.items():
        inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
        for input_name, value in inputs.items():
            if (
                isinstance(value, list)
                and len(value) == 2
                and value[0] in loader_ids
            ):
                consumers.add((node_id, input_name, value[0]))
    return consumers


def validate_sealed_workflow_contract(
    profile: LocalImageExecutionProfile,
    workflow: dict[str, Any],
    binding: LocalImageBinding,
) -> None:
    actual_node_classes = {
        node_id: node.get("class_type")
        for node_id, node in workflow.items()
        if isinstance(node, dict)
    }
    if actual_node_classes != SEALED_NODE_CLASSES[profile.lane_id]:
        raise _invalid("Local image workflow node topology is not sealed.")

    loader_contract = {
        "UNETLoader": ("diffusion", "unet_name"),
        "CLIPLoader": ("text_encoder", "clip_name"),
        "VAELoader": ("vae", "vae_name"),
        "LoraLoaderModelOnly": ("lora", "lora_name"),
    }
    actual_components = []
    for node in workflow.values():
        if not isinstance(node, dict) or node.get("class_type") not in loader_contract:
            continue
        role, input_name = loader_contract[node["class_type"]]
        filename = node.get("inputs", {}).get(input_name)
        if not isinstance(filename, str):
            raise _invalid("Local image workflow model loader is malformed.")
        actual_components.append((role, filename))
    expected_components = [
        (component.role, component.filename) for component in profile.components
    ]
    if sorted(actual_components) != sorted(expected_components):
        raise _invalid(
            "Local image workflow model loaders do not match the sealed components."
        )

    if profile.lane_id in {
        "qwen_image_edit_2511_local",
        "qwen_image_edit_2511_masked_local",
    }:
        reference_slots = (
            ("41", "inputs", "image"),
            ("83", "inputs", "image"),
        )
        if profile.lane_id == "qwen_image_edit_2511_masked_local":
            reference_slots += (("84", "inputs", "image"),)
        expected_binding = {
            "positive_prompt": ("170:151", "inputs", "prompt"),
            "negative_prompt": ("170:149", "inputs", "prompt"),
            "seed": ("170:169", "inputs", "seed"),
            "width": ("170:160", "inputs", "width"),
            "height": ("170:160", "inputs", "height"),
            "reference_images": reference_slots,
        }
        settings = (
            workflow.get("170:169", {}).get("inputs", {}).get("sampler_name")
            == profile.sampler
            and workflow.get("170:169", {}).get("inputs", {}).get("scheduler")
            == profile.scheduler
            and workflow.get("170:169", {}).get("inputs", {}).get("steps")
            == profile.steps
            and workflow.get("170:169", {}).get("inputs", {}).get("cfg")
            == profile.guidance
        )
        model_edges = (
            input_edge(workflow, "170:145", "model") == ["170:161", 0]
            and input_edge(workflow, "170:152", "model") == ["170:145", 0]
            and input_edge(workflow, "170:169", "model") == ["170:152", 0]
        )
        loader_consumers_expected = {
            ("170:145", "model", "170:161"),
            ("170:149", "clip", "170:162"),
            ("170:149", "vae", "170:146"),
            ("170:151", "clip", "170:162"),
            ("170:151", "vae", "170:146"),
            ("170:156", "vae", "170:146"),
            ("170:158", "vae", "170:146"),
        }
        loader_ids = {"170:161", "170:162", "170:146"}
        if profile.lane_id == "qwen_image_edit_2511_masked_local":
            masked_edges = (
                workflow.get("170:169", {}).get("inputs", {}).get("denoise") == 1
                and
                workflow.get("170:147", {}).get("inputs", {})
                == {
                    "conditioning": ["170:149", 0],
                    "reference_latents_method": "index_timestep_zero",
                }
                and workflow.get("170:148", {}).get("inputs", {})
                == {
                    "conditioning": ["170:151", 0],
                    "reference_latents_method": "index_timestep_zero",
                }
                and workflow.get("170:169", {}).get("inputs", {}).get("negative")
                == ["170:147", 0]
                and workflow.get("170:169", {}).get("inputs", {}).get("positive")
                == ["170:148", 0]
                and workflow.get("170:169", {}).get("inputs", {}).get("latent_image")
                == ["170:173", 0]
                and workflow.get("170:172", {}).get("inputs", {})
                == {"image": ["84", 0], "channel": "red"}
                and workflow.get("170:173", {}).get("inputs", {})
                == {"samples": ["170:156", 0], "mask": ["170:172", 0]}
                and workflow.get("170:174", {}).get("inputs", {})
                == {
                    "destination": ["83", 0],
                    "source": ["170:158", 0],
                    "x": 0,
                    "y": 0,
                    "resize_source": False,
                    "mask": ["170:172", 0],
                }
                and workflow.get("170:158", {}).get("inputs", {}).get("samples")
                == ["170:169", 0]
                and workflow.get("9", {}).get("inputs", {}).get("images")
                == ["170:174", 0]
                and workflow.get("170:160", {}).get("inputs", {}).get("image")
                == ["83", 0]
                and workflow.get("170:160", {}).get("inputs", {}).get("crop")
                == "disabled"
                and workflow.get("170:149", {}).get("inputs", {}).get("image1")
                == ["170:160", 0]
                and workflow.get("170:151", {}).get("inputs", {}).get("image1")
                == ["170:160", 0]
                and workflow.get("170:149", {}).get("inputs", {}).get("image2")
                == ["41", 0]
                and workflow.get("170:151", {}).get("inputs", {}).get("image2")
                == ["41", 0]
                and workflow.get("170:156", {}).get("inputs", {}).get("pixels")
                == ["170:160", 0]
            )
            loader_consumers_expected.update(
                {
                    ("170:149", "image2", "41"),
                    ("170:151", "image2", "41"),
                    ("170:160", "image", "83"),
                    ("170:174", "destination", "83"),
                    ("170:172", "image", "84"),
                }
            )
            loader_ids.update({"41", "83", "84"})
            settings = settings and masked_edges
    else:
        expected_binding = {
            "positive_prompt": ("92:109", "inputs", "text"),
            "negative_prompt": ("92:86", "inputs", "text"),
            "seed": ("92:106", "inputs", "noise_seed"),
            "width": ("92:111", "inputs", "width"),
            "height": ("92:111", "inputs", "height"),
            "reference_images": (
                ("76", "inputs", "image"),
                ("81", "inputs", "image"),
            ),
        }
        settings = (
            profile.scheduler == "flux2_distilled"
            and workflow.get("92:101", {}).get("inputs", {}).get("sampler_name")
            == profile.sampler
            and workflow.get("92:102", {}).get("inputs", {}).get("steps")
            == profile.steps
            and workflow.get("92:103", {}).get("inputs", {}).get("cfg")
            == profile.guidance
        )
        model_edges = input_edge(workflow, "92:103", "model") == ["92:107", 0]
        loader_consumers_expected = {
            ("92:103", "model", "92:107"),
            ("92:105", "vae", "92:110"),
            ("92:109", "clip", "92:108"),
            ("92:112:116", "vae", "92:110"),
            ("92:84:119", "vae", "92:110"),
            ("92:86", "clip", "92:108"),
        }
        loader_ids = {"92:107", "92:108", "92:110"}

    actual_binding = {key: getattr(binding, key) for key in expected_binding}
    if (
        actual_binding != expected_binding
        or not settings
        or not model_edges
        or loader_consumers(workflow, loader_ids) != loader_consumers_expected
    ):
        raise _invalid(
            "Local image workflow does not implement the sealed request semantics."
        )


__all__ = [
    "SEALED_NODE_CLASSES",
    "input_edge",
    "loader_consumers",
    "validate_sealed_workflow_contract",
]
