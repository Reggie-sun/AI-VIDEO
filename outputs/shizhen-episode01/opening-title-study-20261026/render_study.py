"""Two title studies on the unchanged focus-002 opening.

The edit, native dialogue, music, clocks, captions and AI badge stay.
Only the CO-A3 title graphic changes. No new paid generation.
"""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import sys

from ai_video.production.models import *
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.composition import resolve_composition
from ai_video.production.commercial_graphics import GraphicTreatment, GraphicRole
from ai_video.production.text_design import TextDesign, TextVisualNode, TextRun, MotionPose
from ai_video.production.hyperframes import (
    HyperFramesAdapter, HyperFramesRenderAttempt, _NetworkIsolatedHyperFramesRunner,
    decoded_audio_sha256_fd_with_executable, probe_clip_fd_with_executable,
)
import glyphs

REPO = Path.cwd()
HERE = Path(__file__).resolve().parent
OLD = REPO / "outputs/shizhen-episode01/cold-open-execution-20261026/composition"
FOCUS = REPO / "outputs/shizhen-episode01/opening-narrative-integration-20261026"
TOOLS = Path("/home/reggie/.config/jianji/tools/ffmpeg/bin")
BROWSER = Path("/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome")
EASE_OUT = (160, 1000, 300, 1000)


def clocks(old):
    original = old.clock_graphics()
    before = [x for x in original if x.shot_id == "CO-A1"]
    after = next(x for x in original if x.graphic_id == "clock-after")
    tail = after.model_copy(update={"start_frame_offset": 54})
    continuation = after.model_copy(update={
        "graphic_id": "clock-after-continuation", "shot_id": "CO-A3",
        "start_frame_offset": 0, "duration_frames": 12,
    })
    design = after.text_design
    node = design.nodes[0]
    run = node.runs[0].model_copy(update={"text": "03:17:12"})
    design = design.model_copy(update={
        "nodes": (node.model_copy(update={"node_id": "clock-next-second", "runs": (run,)}),),
    })
    next_second = after.model_copy(update={
        "graphic_id": "clock-next-second", "shot_id": "CO-A3",
        "start_frame_offset": 12, "duration_frames": 13,
        "text": "03:17:12", "text_design": design,
    })
    return (*before, tail, continuation, next_second)


def title_graphic(kind, font):
    if kind == "exposure":
        path = glyphs.exposure_path()
        fill = "#06080AB0"
        blur = 0
        purpose = "Rain that remains is the ink; one shared column is the frame that dropped"
        intent = "四句对白结束后，雨夜只留在失帧两个字里。同一列缺口是少掉的那一帧，人物并不知道片名出现。"
    elif kind == "inscription":
        path = glyphs.inscription_path()
        fill = "#1C1914C4"
        blur = 700
        purpose = "The name is written on the glass and misses one column; the street stays"
        intent = "画面不灭。片名像写在玻璃上，同一列笔画空着，用来回应刚才少掉的人。"
    else:
        raise ValueError(kind)
    if not path or len(path) > 65536:
        raise RuntimeError(f"{kind} path length {len(path)}")
    visible = TextVisualNode(
        node_id="title-path", purpose=purpose,
        x_px=0, y_px=0, width_px=1920, height_px=1080,
        path=path, fill=fill, stroke="none", stroke_width_px=0,
        motion=(
            MotionPose(frame=0, opacity_milli=0),
            MotionPose(frame=126, opacity_milli=0, blur_milli_px=blur, easing=EASE_OUT),
            MotionPose(frame=156, opacity_milli=1000, blur_milli_px=blur),
            MotionPose(frame=191, opacity_milli=1000, blur_milli_px=blur),
        ),
    )
    hidden = TextVisualNode(
        node_id="title-copy",
        purpose="Exact title copy kept for the graphic contract; it is not drawn",
        x_px=220, y_px=140, width_px=240, height_px=80,
        runs=(TextRun(text="失帧", font_family=font.family, font_size_px=48, color="#E7E0D2"),),
        motion=(MotionPose(frame=0, opacity_milli=0), MotionPose(frame=191, opacity_milli=0)),
    )
    design = TextDesign(
        intent=intent,
        hierarchy="对白和消失先完成；音乐进入后片名才出现。时钟、字幕和 AI 生成标记保持原样。",
        reference_width_px=1920, reference_height_px=1080, fonts=(font,),
        nodes=(visible, hidden),
    )
    return GraphicTreatment(
        graphic_id="shizhen-title-" + kind, role=GraphicRole.HEADLINE, text="失帧",
        shot_id="CO-A3", start_frame_offset=0, duration_frames=192,
        x_milli=0, y_milli=0, width_milli=1000, font_size_px=48, font_weight=400,
        text_color="#E7E0D2", z_index=100, text_design=design,
    )


def build(kind):
    os.environ["PATH"] = str(TOOLS) + os.pathsep + os.environ.get("PATH", os.defpath)
    inp = json.loads((FOCUS / "focus-002-input-receipt.json").read_text())
    project = load_production_project(Path(inp["project"]) / "project.yaml")
    module = importlib.util.spec_from_file_location("old_context_tools", OLD / "render.py")
    old = importlib.util.module_from_spec(module)
    module.loader.exec_module(old)
    font = old.font(
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "失帧", 2, "Noto Serif CJK SC",
    )
    layers, audio = [], []
    for row in inp["sources"]:
        layers.append(CompositionLayerSpec(
            layer_id="original-visual-" + row["shot_id"], shot_id=row["shot_id"],
            asset_role="primary_visual", asset_id=row["asset_id"],
            trim_start_frame=row["start"], trim_duration_frames=row["frames"],
            source_audio_policy="KEEP", transform=FixedTransform.model_validate(row["transform"]),
        ))
        audio.append(AudioTrackSpec(
            track_id="original-mix-" + row["shot_id"], audio_kind="dialogue",
            asset_id=row["audio_id"], shot_id=row["shot_id"],
            trim_start_sample=row["start"] * 2000, trim_duration_samples=row["frames"] * 2000,
        ))
    audio.append(AudioTrackSpec(
        track_id="missing-response-after-reveal", audio_kind="bgm",
        asset_id=inp["music_asset_id"], start_sample=756000, trim_duration_samples=128000,
        gain_millidb=-10000, fade_in_samples=24000, fade_out_samples=48000,
    ))
    order = [x for x in inp["order"] if x != "TITLE"]
    style = CaptionStyleReference.model_validate(inp["style"])
    spec = seal_artifact(CompositionSpec(
        artifact_id="title-study-" + kind, schema_version="2.3", revision=1,
        content_hash="0" * 64, creation_receipt_id="no-paid-title-study",
        source_provenance=project.project.source_provenance,
        composition_id="two-passengers-title-" + kind, shot_ids=tuple(order),
        layers=tuple(layers),
        transitions=tuple(
            TransitionSpec(from_shot_id=a, to_shot_id=b, kind="cut", duration_frames=0)
            for a, b in zip(order, order[1:])
        ),
        delivery_profile=project.project.delivery_profile, sample_rate=48000,
        requested_renderer="hyperframes", audio_tracks=tuple(audio),
        caption_tracks=(CaptionTrackBinding(
            binding_id="A1-editorial-captions", caption_asset_id=inp["caption_id"],
            source_audio_track_id="original-mix-CO-A1", shot_id="CO-A1", style_reference=style,
        ),),
        text_layers=(*clocks(old), title_graphic(kind, font)),
    ))
    timeline = resolve_composition(project, spec, renderer_version="0.7.103")
    if timeline.total_frames != 442 or timeline.total_samples != 884000:
        raise RuntimeError((timeline.total_frames, timeline.total_samples))
    music = next(x for x in timeline.audio_spans if x.track_id == "missing-response-after-reveal")
    if music.start_sample != 756000 or music.duration_samples != 128000:
        raise RuntimeError((music.start_sample, music.duration_samples))
    return project, spec, timeline, style, inp


def main():
    kind = sys.argv[1]
    if kind not in {"exposure", "inscription"}:
        raise SystemExit("expected exposure or inscription")
    project, spec, timeline, style, inp = build(kind)
    names = {"exposure": "失帧-开场-曝光.mp4", "inscription": "失帧-开场-玻璃.mp4"}
    folder = HERE / kind
    folder.mkdir(exist_ok=True)
    (folder / "composition.json").write_text(spec.model_dump_json(indent=2))
    (folder / "resolved-timeline.json").write_text(timeline.model_dump_json(indent=2))
    if "--check" in sys.argv:
        print(json.dumps({"kind": kind, "frames": timeline.total_frames, "samples": timeline.total_samples}))
        return
    stage = REPO / "runs/shizhen-opening-title-study-20261026" / kind
    stage.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(stage, 0o700)
    ip = Path("/usr/sbin/ip").resolve(strict=True)

    class Runner(_NetworkIsolatedHyperFramesRunner):
        def run(self, command, args, **kwargs):
            result = super().run(command, args, **kwargs)
            (stage / (command + "-diagnostic.json")).write_text(json.dumps({
                "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            }, ensure_ascii=False, indent=2))
            return result

    runner = Runner(
        project_root=REPO, binary=REPO / "node_modules/.bin/hyperframes", browser_path=BROWSER,
        ip_path=ip, unshare_path=Path("/usr/bin/unshare"), bash_path=Path("/usr/bin/bash"),
    )
    adapter = HyperFramesAdapter(
        runner=runner, expected_version="0.7.103", browser_path=BROWSER, ip_path=ip,
        decoded_audio=lambda fd, rate, channels: decoded_audio_sha256_fd_with_executable(
            fd, rate, channels, TOOLS / "ffmpeg"),
        probe=lambda fd: probe_clip_fd_with_executable(fd, TOOLS / "ffprobe"),
    )
    selection = RendererSelectionReceipt(
        receipt_id="title-study-" + kind, attempt_id="title-study-" + kind,
        requested_kind="hyperframes", selected_kinds=("hyperframes",), renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=project.manifest.active_project, current_registry=project.manifest.active_registry,
    )
    assets = {x.asset_id: project.asset_paths[x.asset_id] for x in (*timeline.visual_spans, *timeline.audio_spans)}
    assets.update({x.caption_asset_id: project.asset_paths[x.caption_asset_id] for x in timeline.caption_cues})
    assets[style.artifact_id] = project.root / style.path
    before = (project.root / "state/manifest.json").read_bytes()
    output = folder / names[kind]
    if output.exists():
        raise FileExistsError(output)
    result = adapter.render(HyperFramesRenderAttempt(
        attempt_id=selection.attempt_id, selection=selection, timeline=timeline,
        asset_sources=assets, allowed_asset_root=project.root, staging_root=stage / "source",
        allowed_staging_parent=stage, output_path=stage / "output" / names[kind],
        verification_snapshot_path=stage / "verified.mp4",
    ))
    if before != (project.root / "state/manifest.json").read_bytes():
        raise RuntimeError("manifest changed")
    if not all(c.exit_code == 0 and c.error_count == 0 for c in result.checks):
        raise RuntimeError([c.model_dump(mode="json") for c in result.checks])
    shutil.copyfile(result.output.untrusted_staged_path, output)
    report = {
        "output": str(output.relative_to(REPO)),
        "sha256": result.output.output_sha256,
        "bytes": result.output.output_size_bytes,
        "measured": result.output.measured.model_dump(mode="json"),
        "checks": [c.model_dump(mode="json") for c in result.checks],
        "predecessor": "outputs/shizhen-episode01/opening-narrative-integration-20261026/focus-002/失帧-两位-关键事件重剪-002.mp4",
        "kind": kind,
        "native_dialogue": "KEEP exact source windows; no speech gain or fade",
        "music": "same Suno B, sample 756000, 128000 samples, -10 dB",
        "s01": "OUT_OF_SCOPE_NOT_INCLUDED",
        "paid_generation_calls": 0,
        "human_review": "PENDING",
        "publication": "NOT_PUBLISHED",
        "title_note": inp["music_note"],
    }
    (folder / "render-receipt.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": report["output"], "sha256": report["sha256"], "bytes": report["bytes"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
