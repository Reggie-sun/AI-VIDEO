from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "execute_t8_smoothness.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("qingyan_t8_portrait_runner", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the T8 smoothness experiment runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    runner = load_runner()
    runner.OUTPUT = HERE / "qingyan-miao-t8-stock20-portrait-smoothness.mp4"
    runner.RECEIPT = HERE / "receipt-portrait.json"
    runner.SEED = 8252028
    runner.WIDTH = 768
    runner.HEIGHT = 1344
    runner.FILENAME_PREFIX = (
        "development_experiment/qingyan_miao_t8_stock20_portrait_smoothness_seed8252028"
    )
    runner.PROMPT = """integrated_multimodal_description: [Shot 1] Live-action premium personal-care commercial, native portrait composition. A modern 22-year-old Miao woman with a natural Chinese face wears an ivory blouse with refined indigo Miao embroidery, a dark ankle-length skirt, small silver earrings and a restrained silver hair ornament. A full-body vertical shot shows her from hair ornament to both shoes with clean negative space above and below. She walks calmly forward along a bright clean mountain-village lane, taking four natural evenly paced steps toward the camera while remaining centered. Every heel contact, weight transfer and toe-off is continuous and physically natural; no foot skating, no sudden pose reset, no jump, no duplicated limb, no body morphing. Her arms swing gently while the skirt hem, loose hair strands and silver earrings have subtle continuous secondary motion. The camera is locked on a tripod with no pan, no tilt, no push, no zoom, no shake and no reframing. Stable background, constant body scale progression, one continuous shot, no cut, no text, no logo.
overall_soundscape: Four evenly paced natural footsteps on stone, soft outdoor breeze, subtle fabric movement and a faint clean silver-earring chime. No dialogue and no crowd noise.
non_diegetic_music: Light modern plucked strings with a restrained even pulse at medium tempo, low in the mix, fresh and commercial without dramatic percussion."""
    runner.main()


if __name__ == "__main__":
    main()
