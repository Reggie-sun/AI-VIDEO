"""Exact authored Seedance prose pinned to one provider-bound recipe.

The caller supplies already-approved source prose. This binding does not infer
approval, repair text, suppress recipe coverage checks, or change references.
"""
from __future__ import annotations

import hashlib
from pydantic import Field, model_validator

from ai_video.production.models import StrictModel
from ai_video.production.video_compiler import ProviderNativePrompt


class SeedanceNativePromptBinding(StrictModel):
    provider_bound_request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_text: str = Field(min_length=1, max_length=5000)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _exact_text(self):
        if hashlib.sha256(self.prompt_text.encode()).hexdigest() != self.prompt_sha256:
            raise ValueError("Seedance authored prompt seal does not match")
        return self

    def compile(self, provider_bound, mechanically_expressed_controls, *, requirement=None):
        if provider_bound.provider_bound_request_hash != self.provider_bound_request_hash:
            raise ValueError("Seedance authored prompt targets another provider-bound recipe")
        controls = mechanically_expressed_controls
        if requirement is not None:
            dialogue = requirement.generation_intent.dialogue_intent
            # Verbatim Chinese dialogue already expresses the language; do not
            # append an English language label to an exact authored prompt.
            if (dialogue.mode == "dialogue" and dialogue.language in {"zh", "zh-CN"}
                    and dialogue.verbatim_text and dialogue.verbatim_text in self.prompt_text
                    and any("\u4e00" <= char <= "\u9fff" for char in dialogue.verbatim_text)):
                controls = (*controls, "generation_intent.dialogue_intent.language",
                            "generation_intent.dialogue_intent.mode")
            motion = requirement.generation_intent.primary_camera_motion
            if (motion is not None and motion.movement_kind == "dolly_in"
                    and motion.direction == "forward" and "推近" in self.prompt_text):
                controls = (*controls, "generation_intent.primary_camera_motion.direction")
        return ProviderNativePrompt(
            grammar_contract="remote-video-prose-v1", prompt_text=self.prompt_text,
            prompt_sha256=self.prompt_sha256,
            expressed_control_paths=controls,
        )
