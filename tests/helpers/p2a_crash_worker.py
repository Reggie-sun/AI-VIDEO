from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(TESTS_DIR))

from ai_video.production.models import (  # noqa: E402
    ProductionManifest,
    RendererKind,
    RendererSelectionReceipt,
)
from ai_video.production.state_commit import (  # noqa: E402
    BeginRenderAttemptRequest,
    CommitPhase,
    ProductionStateCommitter,
)
from ai_video.production.hyperframes import _render_with_hyperframes  # noqa: E402
from production_project_factory import (  # noqa: E402
    make_revision_two_request,
    make_voice_activation_request,
    make_voice_preview_and_authorization,
    make_voice_request,
)
from test_production_hyperframes import (  # noqa: E402
    FakeRunner,
    make_asset_sources,
    make_resolved_timeline,
)


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
    if len(sys.argv) > 4 and sys.argv[4] == "render":
        manifest = ProductionManifest.model_validate_json(
            (root / "state/manifest.json").read_text(encoding="utf-8")
        )
        timeline = make_resolved_timeline()
        selection = RendererSelectionReceipt(
            receipt_id="selection-process-crash",
            attempt_id="render-process-crash",
            requested_kind=RendererKind.HYPERFRAMES,
            selected_kinds=(RendererKind.HYPERFRAMES,),
            renderer_version="0.7.103",
            timeline_fingerprint=timeline.composition_fingerprint,
            current_project=manifest.active_project,
            current_registry=manifest.active_registry,
        )
        tools = root / "worker-tools"
        tools.mkdir(exist_ok=True)
        browser = tools / "chrome"
        ip_path = tools / "ip"
        for executable in (browser, ip_path):
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o700)
        _render_with_hyperframes(
            committer=ProductionStateCommitter(
                root, crash_injector=ExitInjector(phase, occurrence)
            ),
            begin_request=BeginRenderAttemptRequest(
                manifest.manifest_revision, manifest.active_render_state, selection
            ),
            timeline=timeline,
            asset_sources=make_asset_sources(root, timeline),
            allowed_asset_root=root,
            runner_factory=lambda: FakeRunner(),
            browser_path=browser,
            ip_path=ip_path,
            expected_version="0.7.103",
            probe=lambda fd: {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 320,
                        "height": 180,
                        "r_frame_rate": "24/1",
                        "nb_frames": "10",
                        "codec_name": "h264",
                    }
                ]
            },
            decoded_frames=lambda fd: hashlib.sha256(
                os.pread(fd, os.fstat(fd).st_size, 0)
            ).hexdigest(),
        )
        return 0
    if len(sys.argv) > 4 and sys.argv[4] == "voice":
        request = make_voice_request(root, attempt_id="voice-process-crash")
        preview, authorization = make_voice_preview_and_authorization(request)
        injector = ExitInjector(phase, occurrence)
        if phase is CommitPhase.AFTER_VOICE_PROVIDER_RESULT:
            class _Provider:
                def preview(self, candidate):
                    return preview

                def generate(self, candidate, candidate_authorization, permit):
                    binding = {
                        "attempt_id": candidate.attempt_id,
                        "request_fingerprint": candidate.voice_request_fingerprint,
                        "authorization_fingerprint": candidate_authorization.authorization_fingerprint,
                        "destination": candidate_authorization.destination,
                        "budget_reservation_receipt_id": candidate_authorization.budget_reservation_receipt_id,
                        "egress_authorization_receipt_id": candidate_authorization.egress_authorization_receipt_id,
                    }
                    if not permit._consume_voice_submit_permit(**binding):
                        raise AssertionError("voice worker permit was not consumable")
                    return object()

            def prepare(*_args):
                activation, audio_ids = make_voice_activation_request(
                    root, request, authorization, expected_manifest_revision=3
                )
                return activation, audio_ids, ()

            ProductionStateCommitter(
                root,
                crash_injector=injector,
                voice_candidate_preparer=prepare,
            ).generate_voice_asset(request, _Provider(), authorization)
            return 0
        writer = ProductionStateCommitter(root, crash_injector=injector)
        writer.begin_voice_generation(request, preview, authorization)
        writer.record_voice_submit_intent(request, preview, authorization)
        if phase in {
            CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST,
            CommitPhase.AFTER_VOICE_FINAL_MANIFEST_REPLACE,
        }:
            activation, audio_ids = make_voice_activation_request(
                root, request, authorization, expected_manifest_revision=3
            )
            writer.activate_voice_assets(activation, audio_asset_ids=audio_ids)
        return 0
    request = make_revision_two_request(root)
    ProductionStateCommitter(
        root, crash_injector=ExitInjector(phase, occurrence)
    ).commit(request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
