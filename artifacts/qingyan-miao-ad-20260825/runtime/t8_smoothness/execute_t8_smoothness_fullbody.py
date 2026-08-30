from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "execute_t8_smoothness.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("qingyan_t8_smoothness_runner", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the first T8 experiment runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    runner = load_runner()
    runner.OUTPUT = HERE / "qingyan-miao-t8-stock20-fullbody-smoothness.mp4"
    runner.RECEIPT = HERE / "receipt-fullbody.json"
    runner.SEED = 8252027
    runner.PROMPT = """integrated_multimodal_description: [Shot 1] Live-action commercial realism, a modern 22-year-old Miao woman with a natural Chinese face wears an ivory blouse with refined indigo Miao embroidery, a dark ankle-length skirt, small silver earrings and a restrained silver hair ornament. A wide full-body side-profile shot shows her entire body from hair ornament to both shoes, with clear empty space below her feet and around her silhouette, on a clean level stone path in bright soft morning light. She starts in the left third and takes exactly four calm natural steps toward screen right at constant speed, ending near the right third. Both feet, ankles and knees remain visible in every frame; each heel contact, weight transfer, toe-off and next foot plant is clearly visible. Her face, chest, hips, knees and toes remain oriented toward screen right. No pivot, no turn around, no backward step, no backpedal, no sideways slide, no walking in place, no foot skating. Her arms swing gently and naturally while the skirt hem, loose hair strands and silver earrings show subtle secondary motion. The camera is completely locked off on a tripod with no pan, no track, no push, no zoom, no shake and no reframing. Consistent body scale, stable background, no cut, no text, no logo.
overall_soundscape: Four evenly paced natural footsteps on stone, soft outdoor breeze, subtle fabric movement and a faint clean silver-earring chime. No dialogue and no crowd noise.
non_diegetic_music: Light modern plucked strings with a restrained even pulse at medium tempo, low in the mix, fresh and commercial without dramatic percussion."""
    runner.main()


if __name__ == "__main__":
    main()
