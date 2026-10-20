"""Real local pilot fixtures using public Canvas/Production import and render seams."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import subprocess
import time
from pathlib import Path

from ai_video.canvas_production import CanvasProductionService
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_video_assets import prepare_canvas_video_assets
from ai_video.production.audio import AudioImportRequest, AudioProbeToolchain
from ai_video.production.captions import CaptionImportRequest, caption_timing_fingerprint, caption_style_fingerprint
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRecord, AssetRegistrySnapshot, AudioSource, AudioTrackSpec, CaptionAssetMetadata,
    CaptionSegmentationPolicy, CaptionStyleReference, CaptionTrack,
    CaptionTrackBinding, SourceReference, ToolIdentity,
    AssetType, AssetSourceKind, AudioKind,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from ai_video.production.state_commit import prepare_audio_registry_commit
from ai_video.production.project import load_production_project
from ai_video.production.text_fonts import EmbeddedFont
from scripts.canvas_sequence_packet import build_sequence_packet
from test_canvas_render import _policy


REPO = Path(__file__).resolve().parents[1]
FFMPEG = Path("/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg").resolve()
FFPROBE = FFMPEG.parent / "ffprobe"
BROWSER = Path("/home/reggie/.cache/puppeteer/chrome-headless-shell/linux-152.0.7928.2/chrome-headless-shell-linux64/chrome-headless-shell")


def subset_font(path: Path, text: str, *, family: str | None = None, face: int = 0) -> EmbeddedFont:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    font = TTFont(path, fontNumber=face, recalcTimestamp=False)
    options = subset.Options()
    options.name_IDs = [0,1,2,3,4,5,6,13,14,16,17]
    sub = subset.Subsetter(options=options)
    sub.populate(text=text)
    sub.subset(font)
    names = {n.toUnicode() for n in font["name"].names if n.nameID in {1,16}}
    family = family or sorted(names)[0]
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    return EmbeddedFont(family=family, sha256=hashlib.sha256(data).hexdigest(),
                        data_base64=base64.b64encode(data).decode(), license="SIL Open Font License 1.1; Noto CJK / Google")


def _prepared(path, payload):
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def _caption_assets(audio, segments, style):
    style_bytes = json.dumps(style, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(style_bytes).hexdigest()
    reference = CaptionStyleReference(artifact_id="pilot-subtitle-style", revision=1,
                                     content_hash=digest, path=Path(f"assets/styles/{digest}.json"))
    script = "\n".join(s.text for s in segments)
    track = CaptionTrack(artifact_id="pilot-subtitle-track", revision=1, content_hash="0"*64,
        creation_receipt_id="pilot-authoring", source_provenance=(SourceReference(kind="imported", reference="pilot-authored-timing"),),
        caption_track_id="dialogue", language="zh", script_hash=audio.audio_metadata.script_hash,
        transcript_hash=hashlib.sha256(script.encode()).hexdigest(), source_audio_asset_id=audio.asset_id,
        source_audio_sha256=audio.sha256, source_sample_rate_hz=48000, segments=segments,
        segmentation_policy=CaptionSegmentationPolicy(policy_id="pilot-segments",policy_version="1",
            max_characters=120,max_lines=2,break_strategy="provider_segments"),
        alignment_provider="explicit-authored-local-asr-reference", alignment_model="whisper-small",
        alignment_receipt_id="pilot-authoring", style_reference_id=reference.artifact_id,timing_fingerprint="0"*64)
    track = seal_artifact(track.model_copy(update={"timing_fingerprint":caption_timing_fingerprint(track)}))
    prepared = CaptionImportRequest.create(caption_track=track,style_reference=reference,style_bytes=style_bytes)
    path = Path(f"assets/files/{prepared.track_sha256}.json")
    record = AssetRecord(asset_id="pilot-captions",asset_type=AssetType.CAPTION,artifact_path=path,
        sha256=prepared.track_sha256,size_bytes=len(prepared.track_bytes),mime_type="application/json",
        source_kind=AssetSourceKind.IMPORTED,tool=ToolIdentity(name="pilot-caption-import",version="1"),
        input_artifact_ids=(audio.asset_id,),input_fingerprint=audio.sha256,creation_receipt_id="pilot-authoring",
        usage_license="Internal typography comparison; not publication clearance",
        caption_metadata=CaptionAssetMetadata(caption_track_id=track.caption_track_id,language=track.language,
            source_audio_asset_id=audio.asset_id,source_audio_sha256=audio.sha256,script_hash=track.script_hash,
            transcript_hash=track.transcript_hash,segment_count=len(segments),word_count=sum(len(s.words or ()) for s in segments),
            segmentation_policy_id=track.segmentation_policy.policy_id,segmentation_policy_version="1",
            alignment_receipt_id=track.alignment_receipt_id,timing_fingerprint=track.timing_fingerprint,
            style_reference_id=reference.artifact_id,style_reference_revision=1,style_content_hash=digest))
    binding = CaptionTrackBinding(binding_id="dialogue",caption_asset_id=record.asset_id,
        source_audio_track_id="dialogue",shot_id="sample",style_reference=reference)
    return record, (_prepared(path,prepared.track_bytes),_prepared(reference.path,style_bytes)), binding


def render_case(root: Path, *, source: Path, profile: dict, duration_seconds: int,
                graphics=(), style=None, segments=(), preserve_audio=False):
    """Import exact local media, bootstrap, resolve and durably render; no fake runner."""
    root.mkdir(parents=True)
    kind = "video" if source.suffix == ".mp4" else "image"
    original = {"nodes":[{"id":"selected", "type":kind,"data":{"resourceId":"local-source"}},
        {"id":"occurrence","type":"video","data":{"generationDraft":{
            "references":[{"slotId":"media","nodeId":"selected","role":"reference"}],
            "parts":[{"type":"text","text":"Preserve the selected local source for typography comparison."},
                     {"type":"extension","extension_type":"node","object_id":"media"}],
            "contentSettings":{"durationSeconds":duration_seconds,"resolution":"720p"}}}}],
        "edges":[{"id":"source-reference","source":"selected","target":"occurrence","type":"reference"}]}
    packet = build_sequence_packet(original,{"node_ids":["occurrence"]})
    selection = dict(asset_id="source",node_id="selected",resource_id="local-source",path=source,
                     usage_license="Existing project asset; internal comparison only; publication rights not requalified")
    if kind == "video":
        selection["tool"]={"name":"existing-project-footage","version":"1"}
        registry, artifacts = prepare_canvas_video_assets(packet=packet,selections=[selection],
            allowed_asset_root=source.parent,ffprobe_executable=FFPROBE)
    else:
        registry, artifacts = prepare_canvas_png_assets(packet=packet,selections=[selection],allowed_asset_root=REPO)
    records, artifacts = list(registry.assets), list(artifacts)
    audio_tracks, caption_tracks = (), ()
    pending_caption = None
    if preserve_audio or segments:
        wav = root / "source-audio.wav"
        subprocess.run([str(FFMPEG),"-v","error","-i",str(source),"-t",str(duration_seconds),
                        "-vn","-ar","48000","-ac","2","-c:a","pcm_s16le",str(wav)],check=True)
        request = AudioImportRequest(asset_id="pilot-dialogue",audio_kind=AudioKind.DIALOGUE,mime_type="audio/wav",
            source=AudioSource(kind=AssetSourceKind.IMPORTED,provider_or_tool=ToolIdentity(name="ffmpeg",version="local"),
                input_artifact_ids=("source",),input_fingerprint=records[0].sha256),language="zh",
            script_hash=hashlib.sha256("\n".join(s.text for s in segments).encode()).hexdigest(),
            provenance_receipt_id="pilot-audio-import",creation_receipt_id="pilot-audio-import",
            usage_license="Existing footage native audio; no gain change")
        tools=AudioProbeToolchain(ffmpeg_path=FFMPEG,ffprobe_path=FFPROBE,
            ffmpeg=ToolIdentity(name="ffmpeg",version="local"),ffprobe=ToolIdentity(name="ffprobe",version="local"))
        with wav.open("rb") as f:
            imported = request.prepare(f.fileno(),toolchain=tools)
        audio = imported.asset_record
        records.append(audio)
        artifacts.append(_prepared(audio.artifact_path,imported.payload))
        audio_tracks=(AudioTrackSpec(track_id="dialogue",audio_kind=AudioKind.DIALOGUE,asset_id=audio.asset_id,shot_id="sample"),)
        if segments:
            record, prepared, binding = _caption_assets(audio,segments,style)
            pending_caption = (record, prepared)
            caption_tracks=(binding,)
    registry = AssetRegistrySnapshot(schema_version="2.2" if kind == "video" else "2.1",revision_id="0"*64,content_hash="0"*64,
                                    assets=tuple(sorted(records,key=lambda a:a.asset_id)))
    digest=registry_semantic_sha256(registry)
    registry=registry.model_copy(update={"revision_id":digest,"content_hash":digest})
    shot=dict(shot_id="sample",scene_id="scene",storyboard_beat_id="beat",intent="Preserve source action; design only the overlaid text.",
              duration_policy={"mode":"fixed","seconds":duration_seconds},
              visual_strategy="existing_video" if kind == "video" else "static_image",
              required_asset_roles=[{"role":"primary_visual","asset_ids":["source"],"allowed_asset_types":[kind]}])
    direction=dict(project_id="text-visual-pilot",title="Text visual capability comparison",language="zh",
        delivery_profile=profile,brief={"objective":"Compare typography against identical media", "audience":"Internal review","format":"visual capability pilot"},
        story={"logline":"An exact-media typography comparison","synopsis":"Source action remains unchanged.","beats":[{"beat_id":"beat","summary":"Typography demonstration"}]},
        characters=[],scenes=[{"scene_id":"scene","location":"existing source","time":"source","mood":"source"}],
        storyboard={"beats":[{"beat_id":"beat","scene_id":"scene","shot_ids":["sample"],"narrative_intent":"Compare text design"}]},
        shots=[{"occurrence_id":"occurrence","adaptation_reason":"Explicit existing-footage comparison without new generation",
                "shot":shot,"composition":{"asset_id":"source","muted":True}}])
    committer=ProductionStateCommitter(root)
    service=CanvasProductionService(committer=committer,packet=packet,direction=direction,targets=())
    bundle=service.author(registry=registry,asset_artifacts=tuple(artifacts))
    service.approve_authoring(bundle=bundle,attempt_id="pilot-authoring",qa_policy=_policy())
    if pending_caption is not None:
        from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
        base = load_production_project(root/"project.yaml")
        record, prepared = pending_caption
        candidate = base.registry.model_copy(update={"assets":(*base.registry.assets,record)})
        digest = registry_semantic_sha256(candidate)
        candidate = candidate.model_copy(update={"revision_id":digest,"content_hash":digest})
        request = prepare_audio_registry_commit(manifest=base.manifest,project=base.project,
            base_registry=base.registry,registry=candidate,attempt_id="pilot-caption-import",artifacts=prepared,
            active_project_artifact=_prepared(base.manifest.active_project.path,(root/base.manifest.active_project.path).read_bytes()))
        request = prepare_strategy_dependency_transition(base_loaded=base,
            candidate_loaded=base.model_copy(update={"registry":candidate}),request=request)
        committer.commit(request)
    arguments=dict(audio_tracks=audio_tracks,caption_tracks=caption_tracks,text_layers=graphics)
    style_fingerprints = tuple((b.style_reference.artifact_id,
        caption_style_fingerprint(b.style_reference, (root/b.style_reference.path).read_bytes())) for b in caption_tracks)
    spec,timeline=service.compose(**arguments)
    (root/"pilot-composition.json").write_text(spec.model_dump_json(indent=2))
    began=time.monotonic()
    service.render(attempt_id="pilot-render",toolchain=dict(binary_path=REPO/"node_modules/.bin/hyperframes",
        browser_path=BROWSER.resolve(),unshare_path=Path("/usr/bin/unshare").resolve(),ip_path=Path("/usr/sbin/ip").resolve(),
        bash_path=Path("/usr/bin/bash").resolve(),ffmpeg_path=FFMPEG,ffprobe_path=FFPROBE),
        caption_style_fingerprints=style_fingerprints,**arguments)
    loaded,final_timeline=service.deliver()
    output=loaded.root/loaded.render_state.output.path
    report={"source":str(source),"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "output":str(output),"output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
            "seconds":time.monotonic()-began,"timeline_fingerprint":final_timeline.composition_fingerprint,
            "production_render_active":True,"p6_final_acceptance":"NOT_EVALUATED"}
    (root/"pilot-evidence.json").write_text(json.dumps(report,indent=2))
    return report
