from __future__ import annotations

import pytest

from scripts.prepare_shot_continuity_p0 import validate_h3_prompt_contract


VALID_PROMPT = """For the target video, <Picture 1> supplies the exact first frame; <Picture 2> supplies the exact last frame; <Picture 3> supplies identity; <Video 1> supplies motion.

integrated_multimodal_description: [Shot 1] Live-action cinematic subject. The camera tracks with small amplitude at slow speed.
overall_soundscape: Rain and footsteps.
non_diegetic_music: No non-diegetic music."""


def test_h3_prompt_contract_accepts_conditioning_instruction_and_three_fields():
    assert validate_h3_prompt_contract(VALID_PROMPT) == VALID_PROMPT


@pytest.mark.parametrize(
    "prompt",
    (
        "A cinematic woman walks through rain.",
        VALID_PROMPT.replace("overall_soundscape:", "soundscape:"),
        VALID_PROMPT.replace("small amplitude", "a little"),
        VALID_PROMPT.replace("<Video 1>", "Video 1"),
    ),
)
def test_h3_prompt_contract_rejects_bare_or_incomplete_prose(prompt: str):
    with pytest.raises(ValueError):
        validate_h3_prompt_contract(prompt)
