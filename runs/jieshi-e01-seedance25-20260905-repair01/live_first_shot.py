"""Historical execution wrapper; explicit execute is required."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.generation_feedback_driver import main as driver_main

def main(argv=None):
    return driver_main(argv)
if __name__ == "__main__":
    raise SystemExit(main())
