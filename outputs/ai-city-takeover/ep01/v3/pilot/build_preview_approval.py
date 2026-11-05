"""Seal the user's checkpoint-B approval of the stage-7 pilot package as user-preview-approval/1.

Binds the exact Director coverage (ep01/v3/director-coverage.json), the pilot units, every file the user saw
(first frames, vocal windows, the package page and inputs, the a2 animatic) with its SHA-256 re-read from disk,
and the user's exact answer. Fails if any file no longer matches the SHA recorded in preview-inputs.json.
No identity waiver is recorded: the package page never asked the user to waive an identity sheet.
Run from the repository root: uv run python outputs/ai-city-takeover/ep01/v3/pilot/build_preview_approval.py
"""
import hashlib
import json
from pathlib import Path

from ai_video.production.preview_approval import KIND, preview_approval_authoring_input
from ai_video.production.reference_authoring import director_coverage_authoring_input

PILOT = Path(__file__).resolve().parent
V3 = PILOT.parent
REPO = V3.parents[3]
USER_QUOTE = "认可，进入试拍"          # AskUserQuestion answer at checkpoint B, 2026-11-04 (exact label the user chose)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inputs = json.loads((PILOT / "preview-inputs.json").read_text(encoding="utf-8"))
    roles: dict[str, list[str]] = {}
    recorded: dict[str, str] = {}

    def add(entry: dict, role: str) -> None:
        path = entry["path"]
        if recorded.setdefault(path, entry["sha256"]) != entry["sha256"]:
            raise SystemExit(f"{path}: two different recorded SHAs")
        roles.setdefault(path, []).append(role)

    for unit, take in inputs["digital_human"]["takes"].items():
        add(take["image"], f"first frame {unit} (digital human)")
        add(take["audio"], f"vocal window {unit}")
    for unit, shot in inputs["seedance"]["units"].items():
        add(shot["first_frame"], f"first frame {unit} (Seedance)")
    artifacts = []
    for path, want in recorded.items():
        got = sha(REPO / path)
        if got != want:
            raise SystemExit(f"{path}: on disk {got} != recorded {want}; the approved package changed")
        artifacts.append({"path": path, "sha256": got, "role": "; ".join(roles[path])})
    for rel, role in (("outputs/ai-city-takeover/ep01/v3/pilot/preview-inputs.json", "pilot package inputs (prompts, windows, acceptance)"),
                      ("outputs/ai-city-takeover/ep01/v3/pilot/preview.html", "pilot package page the user reviewed"),
                      ("outputs/ai-city-takeover/ep01/v3/renders/IRIS-EP01-v3-animatic-a2-review.mp4", "animatic a2 the user watched")):
        artifacts.append({"path": rel, "sha256": sha(REPO / rel), "role": role})

    coverage_hash, _ = director_coverage_authoring_input(json.loads((V3 / "director-coverage.json").read_text(encoding="utf-8")))
    units = sorted([*inputs["digital_human"]["takes"], *inputs["seedance"]["units"]])
    payload = {"kind": KIND, "coverage_hash": coverage_hash, "unit_ids": units, "preview_artifacts": artifacts,
               "user_quote": USER_QUOTE}
    approval_hash, _ = preview_approval_authoring_input(payload)
    (PILOT / "preview-approval.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"approval_hash": approval_hash, "coverage_hash": coverage_hash, "units": units,
                      "artifacts": len(artifacts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
