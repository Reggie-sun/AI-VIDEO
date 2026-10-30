"""Bootstrap one dispatch scene Shot through existing Production owners; no submission.

Usage: python bootstrap.py <SHOT>. Seals the exact Director coverage v5 as a
content-addressed authoring input in Project/Shot provenance.
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import json
import sys

from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import seal_artifact, canonical_sha256
from ai_video.production.models import *  # noqa: F403
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, _canonical_yaml_bytes

HERE = Path(__file__).resolve().parent
SHOT = sys.argv[1]
V = HERE / SHOT
ROOT = Path.cwd() / "runs/shizhen-opening-dispatch-20261030" / SHOT
SHOTS = ("D2", "D3", "D4", "D6")
assert SHOT in SHOTS + ("D2r1", "D4r1") and not (ROOT / "project.yaml").exists()


def dump_once(path: Path, value) -> None:
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def bound() -> dict:
    path = V / "operator-bound.json"
    if path.exists():
        return json.loads(path.read_text())
    now = datetime.now(timezone.utc)
    readonly = json.loads((V / "native-readonly.json").read_text())
    value = {"authority": "current-task-parent-bounded-operator",
             "authorization_quote": "先把画面做出来",
             "scope": f"One {SHOT} dispatch scene 1080p Seedance 2.0 VIP preview; no activation",
             **({"repair_of": {"attempt_id": "shizhen-dispatch-D2-preview-001", "gate": "qa/D2/post-media-gate.json",
                               "verdict": "FAIL", "single_variable": "first_frame start anchor"},
                 "dispatch_repair_ceiling": 1} if SHOT == "D2r1" else
                {"repair_of": {"attempt_id": "shizhen-dispatch-D4-preview-001", "gate": "qa/D4/post-media-gate.json",
                               "verdict": "FAIL", "single_variable": "first_frame start anchor"},
                 "dispatch_repair_ceiling": 1} if SHOT == "D4r1" else {}),
             "issued_at": now.isoformat(), "expires_at": (now + timedelta(hours=3)).isoformat(),
             "max_submit_count": 1, "automatic_retries": 0,
             "dispatch_unit_ceiling": {"scenes": list(SHOTS), "initial_submits_per_scene": 1,
                                       "dialogue_master": 1, "total_initial": 5},
             "per_call_credit_upper_bound": 1500, "quote_credits": readonly["quote"]["credits"],
             "quote_evidence": "native-readonly.json"}
    dump_once(path, value)
    return value


data = json.loads((V / "data.json").read_text())
row = json.loads((V / "row.json").read_text())
operator = bound()
coverage = json.loads((HERE.parent / "director-coverage.v5.json").read_text())
assert canonical_sha256(coverage) == data["coverage"]["coverage_hash"]
envelope = {"kind": "shizhen-dispatch-authoring/1", "row": row, "data": data, "bound": operator,
            "authority": "user: 先把画面做出来 / 语言也做下直接用seedance出; bounded preview, no activation"}
ref = authoring_input_reference(envelope)
coverage_ref = authoring_input_reference(coverage)
packet = {"source_snapshot_sha256": canonical_sha256(envelope),
          "assets": [{"id": a["node_id"], "type": "image", "data": {"resourceId": a["resource_id"]}} for a in data["images"]]}
registry, images = prepare_canvas_png_assets(packet=packet, selections=data["images"], allowed_asset_root=Path.cwd())
source = (ref, coverage_ref, *(authoring_input_reference(json.loads(a.payload)) for a in images
                               if str(a.relative_path).startswith("evidence/authoring-input/")))
label = "dispatch-" + SHOT


def seal(cls, key, **kw):
    return seal_artifact(cls(artifact_id=f"shizhen-{label}-{key}", revision=1, content_hash="0" * 64,
                             creation_receipt_id=f"shizhen-{label}-{key}-authored", source_provenance=source, **kw))


brief = seal(ProductionBrief, "brief", title="失帧 冷开场 调度蒙太奇 " + SHOT, objective=data["objective"],
             audience="都市灵异悬疑剧观众", format="可信真人摄影", language="zh",
             constraints=tuple(row["shot"]["continuity_constraints"]))
story = seal(Story, "story", language="zh", logline="对讲每报一起异常，画面落到那起的现场",
             synopsis=data["objective"], beats=(StoryBeat(beat_id=row["shot"]["storyboard_beat_id"], summary=data["objective"]),))
chars = [seal(Character, "character-" + x["character_id"], **x) for x in data["characters"]]
sc = data["scene"]
scene = seal(Scene, "scene", scene_id=sc["scene_id"], location=sc["location"], time="雨夜", mood=sc["mood"],
             visual_reference_asset_ids=tuple(data["scene_images"]))
shot = seal(Shot, "shot", **row["shot"])
board = seal(Storyboard, "board", beats=(StoryboardBeat(beat_id=row["shot"]["storyboard_beat_id"], scene_id=sc["scene_id"],
                                                         shot_ids=(SHOT,), narrative_intent=data["objective"]),))
models = [(brief, "creative/brief.yaml"), (story, "creative/story.yaml"), (board, "creative/storyboard.yaml"),
          (scene, f"creative/scenes/{sc['scene_id']}.yaml"), (shot, f"creative/shots/{SHOT}.yaml"),
          *((x, "creative/characters/" + x.character_id + ".yaml") for x in chars)]


def ar(m):
    return ArtifactReference(artifact_id=m.artifact_id, revision=m.revision, content_hash=m.content_hash,
                             path=Path(next(p for x, p in models if x == m)))


project = seal_artifact(ProductionProject(
    artifact_id="shizhen-project-" + label, revision=1, content_hash="0" * 64,
    creation_receipt_id=f"shizhen-{label}-bootstrap", source_provenance=source,
    project_id=f"shizhen-{label}-20261030", title="失帧 冷开场 调度蒙太奇 " + SHOT, default_language="zh",
    delivery_profile=DeliveryProfile(width=1920, height=1080, fps=24), renderer_policy=RendererPolicy(),
    artifacts=ProjectArtifactRefs(brief=ar(brief), story=ar(story), characters=tuple(ar(x) for x in chars),
                                  scenes=(ar(scene),), storyboard=ar(board), shots=(ar(shot),))))
old = load_production_project("runs/shizhen-episode01-jimeng25-20261025-001/trial-S02-v1/project.yaml")
payload = {k: v for k, v in old.qa_policy.generation_acceptance.profile_payload.items()
           if k not in {"content_hash", "generation_requirements"}}
obs = data["observations"]
payload.update(profile_id=f"shizhen-{label}-raw", profile_version="1", required_requirement_ids=list(obs),
               generation_requirements=[{
                   "requirement_id": k, "level": "acceptance", "stage": "raw_generation", "dimension": k,
                   "observable": v, "tolerance": "逐项满足分镜与完整动作；不凭静态图片或工具成功推断视频通过",
                   "measurement": "Exact project-local video-analysis plus frame sequences and qualified audio observations",
                   "proof": "analyzer", "intent_paths": data["paths"][k], "native_text": data["fragments"][k],
                   "native_text_mapping": {"intent_sha256": data["intent_sha256"], "bindings": [
                       {"intent_path": path, "fragment_indices": list(range(len(data["fragments"][k])))}
                       for path in data["paths"][k]]},
                   "production_owner": "shot_authoring"} for k, v in obs.items()])
h = canonical_sha256(payload)
final = FinalOutputContract(goal_id=f"shizhen-{label}", goal_version="20261030-preview-v1", user_goal=data["objective"],
                            requirements=tuple({"requirement_id": k, "observable": v, "proof": "human"} for k, v in obs.items()))
qa = seal_artifact(old.qa_policy.model_copy(update={
    "artifact_id": f"shizhen-{label}-qa", "revision": 1, "source_provenance": source,
    "policy_id": f"shizhen-{label}-raw", "policy_version": "1", "final_output": final,
    "generation_acceptance": DomainAcceptancePolicy(
        domain_id=payload["domain_id"], profile_id=payload["profile_id"], profile_version="1",
        measurement_contract_version=payload["measurement_contract_version"], required_requirement_ids=tuple(obs),
        profile_content_hash=h, profile_payload={**payload, "content_hash": h})}))


def art(path, raw):
    return PreparedArtifact(Path(path), raw, hashlib.sha256(raw).hexdigest())


ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
committer = ProductionStateCommitter(ROOT)
m = committer.bootstrap_initial_state(
    attempt_id=f"shizhen-{label}-bootstrap", project=project, registry=registry,
    artifacts=tuple([*images, art(ref.reference, authoring_input_payload(envelope)),
                     art(coverage_ref.reference, authoring_input_payload(coverage)),
                     *(art(path, _canonical_yaml_bytes(x)) for x, path in models)]))
m = initialize_canvas_graph(committer, f"shizhen-{label}-graph")
m = committer.upgrade_manifest_schema("2.14", expected_manifest_revision=m.manifest_revision)
m = committer.activate_qa_policy(qa, attempt_id=f"shizhen-{label}-qa", expected_manifest_revision=m.manifest_revision)
print(json.dumps({"root": str(ROOT), "manifest_revision": m.manifest_revision, "new_video_calls": 0}))
