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
from ai_video.production.composition import resolve_composition  # noqa: E402
from ai_video.production.state_commit import (  # noqa: E402
    BeginRenderAttemptRequest,
    CommitPhase,
    ProductionStateCommitter,
)
from ai_video.production.hyperframes import _render_with_hyperframes  # noqa: E402
from production_project_factory import (  # noqa: E402
    attach_p5_dependency_transition,
    attach_p5_render_dependency_transition,
    make_audio_import_upgrade_request,
    make_manifest_23_project,
    make_p5_dependency_inputs,
    make_p5_bootstrap_transition,
    make_p7_image_candidate_preparer,
    make_p7_image_generation_base,
    _p7_png,
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
from test_production_state_commit import (  # noqa: E402
    make_image_call_bundle,
    make_image_provider_result,
)
from test_production_p7_1_local_image_e2e import (  # noqa: E402
    _local_bundle,
    _profile,
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
    mode = sys.argv[4] if len(sys.argv) > 4 else "project_commit"
    if mode in {"image", "image_local_profile"}:
        base_inputs = make_p7_image_generation_base(root)
        profile = _profile() if mode == "image_local_profile" else None
        request, preview, authorization = (
            _local_bundle(root, profile)
            if profile is not None
            else make_image_call_bundle(root)
        )

        class _Provider:
            def preflight(self, candidate):
                if profile is not None and candidate != request:
                    raise AssertionError("image worker preflight request mismatch")

            def generate(self, candidate, candidate_authorization, permit):
                if not permit._consume_image_generation_permit(
                    request_fingerprint=candidate.request_fingerprint
                ):
                    raise AssertionError("image worker permit was not consumable")
                return make_image_provider_result(
                    candidate, candidate_authorization, _p7_png()
                )

        ProductionStateCommitter(
            root,
            crash_injector=ExitInjector(phase, occurrence),
            image_candidate_preparer=make_p7_image_candidate_preparer(base_inputs),
        ).generate_image_asset(
            request,
            preview,
            authorization,
            _Provider(),
            execution_profile=profile,
        )
        return 0
    if mode == "graph_bootstrap":
        graph, transition, desired = make_p5_bootstrap_transition(root)
        ProductionStateCommitter(
            root, crash_injector=ExitInjector(phase, occurrence)
        ).bootstrap_dependency_graph(
            attempt_id="graph-bootstrap-process-crash",
            graph=graph,
            transition=transition,
            expected_desired_fingerprints=desired,
        )
        return 0
    if mode == "graph_project_commit":
        if ProductionManifest.model_validate_json(
            (root / "state/manifest.json").read_bytes()
        ).schema_version != "2.3":
            make_manifest_23_project(root)
        request = make_revision_two_request(
            root, attempt_id="graph-project-process-crash"
        )
        request, _ = attach_p5_dependency_transition(root, request)
        ProductionStateCommitter(
            root, crash_injector=ExitInjector(phase, occurrence)
        ).commit(request)
        return 0
    if mode == "graph_voice_activate":
        if ProductionManifest.model_validate_json(
            (root / "state/manifest.json").read_bytes()
        ).schema_version != "2.3":
            make_manifest_23_project(root)
        request = make_voice_request(root, attempt_id="graph-voice-process-crash")
        preview, authorization = make_voice_preview_and_authorization(request)
        writer = ProductionStateCommitter(
            root, crash_injector=ExitInjector(phase, occurrence)
        )
        writer.begin_voice_generation(
            request,
            preview,
            authorization,
            dependency_transition_preparer_available=True,
        )
        writer.record_voice_submit_intent(request, preview, authorization)
        manifest = ProductionManifest.model_validate_json(
            (root / "state/manifest.json").read_text(encoding="utf-8")
        )
        activation, audio_ids = make_voice_activation_request(
            root,
            request,
            authorization,
            expected_manifest_revision=manifest.manifest_revision,
        )
        activation, _ = attach_p5_dependency_transition(root, activation)
        writer.activate_voice_assets(activation, audio_asset_ids=audio_ids)
        return 0
    if mode in {"render", "graph_render_activate"}:
        if mode == "graph_render_activate":
            if ProductionManifest.model_validate_json(
                (root / "state/manifest.json").read_bytes()
            ).schema_version != "2.3":
                make_manifest_23_project(root)
        manifest_path = root / "state/manifest.json"
        manifest_payload = manifest_path.read_bytes()
        manifest = ProductionManifest.model_validate_json(manifest_payload)
        if mode == "graph_render_activate":
            inputs = make_p5_dependency_inputs(root)
            manifest_path.write_bytes(manifest_payload)
            timeline = resolve_composition(
                inputs.project,
                inputs.composition_spec,
                renderer_version="0.7.103",
            )
            asset_sources = {
                span.asset_id: inputs.project.asset_paths[span.asset_id]
                for span in (*timeline.visual_spans, *timeline.audio_spans)
            }
            asset_sources.update(
                {
                    cue.caption_asset_id: inputs.project.asset_paths[
                        cue.caption_asset_id
                    ]
                    for cue in timeline.caption_cues
                }
            )
            style = inputs.composition_spec.caption_tracks[0].style_reference
            if style is None:
                raise AssertionError("P5 crash fixture requires a caption style.")
            asset_sources[style.artifact_id] = root / style.path
            probe = {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": timeline.delivery_profile.width,
                        "height": timeline.delivery_profile.height,
                        "r_frame_rate": f"{timeline.delivery_profile.fps}/1",
                        "nb_frames": str(timeline.total_frames),
                        "codec_name": "h264",
                    },
                    {
                        "codec_type": "audio",
                        "index": 1,
                        "codec_name": "aac",
                        "sample_rate": str(timeline.sample_rate),
                        "channels": 2,
                        "channel_layout": "stereo",
                    },
                ],
                "packets": [
                    {
                        "stream_index": 1,
                        "pts": "-1024",
                        "duration": "1024",
                        "side_data_list": [
                            {
                                "side_data_type": "Skip Samples",
                                "skip_samples": 1024,
                                "discard_padding": 0,
                            }
                        ],
                    },
                    {"stream_index": 1, "pts": "0", "duration": "768"},
                ],
            }
            decoded_audio = lambda _fd, _rate, _channels: (
                timeline.total_samples + 256,
                "a" * 64,
            )
        else:
            timeline = make_resolved_timeline()
            asset_sources = make_asset_sources(root, timeline)
            probe = {
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
            }
            decoded_audio = None
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
            asset_sources=asset_sources,
            allowed_asset_root=root,
            runner_factory=lambda: FakeRunner(),
            browser_path=browser,
            ip_path=ip_path,
            expected_version="0.7.103",
            dependency_transition_preparer=(
                (lambda activation: attach_p5_render_dependency_transition(root, activation))
                if mode == "graph_render_activate"
                else None
            ),
            probe=lambda _fd: probe,
            decoded_frames=lambda fd: hashlib.sha256(
                os.pread(fd, os.fstat(fd).st_size, 0)
            ).hexdigest(),
            decoded_audio=decoded_audio,
        )
        return 0
    if mode == "voice":
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
            CommitPhase.AFTER_MANIFEST_REPLACE,
            CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
        }:
            activation, audio_ids = make_voice_activation_request(
                root, request, authorization, expected_manifest_revision=3
            )
            writer.activate_voice_assets(activation, audio_asset_ids=audio_ids)
        return 0
    if mode == "audio_import":
        request = make_audio_import_upgrade_request(
            root, attempt_id="audio-import-process-crash", include_assets=True
        )
        ProductionStateCommitter(
            root, crash_injector=ExitInjector(phase, occurrence)
        ).commit(request)
        return 0
    request = make_revision_two_request(root)
    ProductionStateCommitter(
        root, crash_injector=ExitInjector(phase, occurrence)
    ).commit(request)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
