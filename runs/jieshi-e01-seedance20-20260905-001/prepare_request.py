"""Historical wrapper; explicit configuration only."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.generation_feedback_driver import main as driver_main

def main(argv=None):
    return driver_main(argv, prepare_only=True)
if __name__ == "__main__":
    raise SystemExit(main())
