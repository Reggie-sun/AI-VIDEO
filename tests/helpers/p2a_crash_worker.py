from __future__ import annotations

import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(TESTS_DIR))

from ai_video.production.state_commit import CommitPhase, ProductionStateCommitter
from production_project_factory import make_revision_two_request


class ExitInjector:
    def __init__(self, target: CommitPhase, occurrence: int) -> None:
        self.target = target
        self.occurrence = occurrence
        self.count = 0

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.target:
            self.count += 1
            if self.count == self.occurrence:
                os._exit(91)


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    phase = CommitPhase(sys.argv[2])
    occurrence = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    if occurrence < 1:
        raise ValueError("phase occurrence must be positive")
    request = make_revision_two_request(root)
    ProductionStateCommitter(
        root, crash_injector=ExitInjector(phase, occurrence)
    ).commit(request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
