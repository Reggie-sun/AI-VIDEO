"""Canonical pre-submit authoring correction; preserve the original no-call revision."""
from pathlib import Path
from dataclasses import replace
import hashlib,json
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.models import ArtifactReference
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,prepare_project_registry_commit,_canonical_yaml_bytes
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A1'
l=load_production_project(ROOT/'project.yaml');assert l.project.revision==1 and not any(a.operation=='video_generation' for a in l.manifest.attempts)
raw=(V/'CO-A1-row.json').read_bytes();(V/'CO-A1-row-v1.json').write_bytes(raw);r=json.loads(raw)
r['generation']['references'][1]['role']='last_frame'
r['generation']['generation_intent']['subject_action']['progression']='罗敏已在通话，向司机报两位。高峥听见接车，望一眼湿路并顺口提醒不要急。罗敏听完看他一眼，继续听电话，不重复转述。随后普通灰白厢式货车从摄影机极近前景左向右驶过，不停车不开门，车厢逐渐遮住两人和站棚，最后灰白金属侧板完整填满画面。两人不离开、不上车、不透明消失；各自随身物保持。'
r['shot']['intent']=r['generation']['generation_intent']['subject_action']['progression']
evidence={'kind':'cold-open-pre-submit-input-correction/1','old_row_sha256':hashlib.sha256(raw).hexdigest(),'new_row':r,'reason':'Use canonical LAST_FRAME planning role; keep exact lines only in dialogue turns to prevent duplicated native dialogue. Same approved action and framing, no paid call and no quality repair claim.'}
ref=authoring_input_reference(evidence);s=seal_artifact(l.shots[0].model_copy(update={'revision':2,'intent':r['shot']['intent'],'source_provenance':(*l.shots[0].source_provenance,ref)}));sp=Path('creative/shots/CO-A1-v2.yaml');sr=ArtifactReference(artifact_id=s.artifact_id,revision=s.revision,content_hash=s.content_hash,path=sp)
p=seal_artifact(l.project.model_copy(update={'revision':2,'source_provenance':(*l.project.source_provenance,ref),'artifacts':l.project.artifacts.model_copy(update={'shots':(sr,)})}))
def a(path,b):return PreparedArtifact(Path(path),b,hashlib.sha256(b).hexdigest())
q=prepare_project_registry_commit(manifest=l.manifest,project=p,registry=l.registry,attempt_id='shizhen-CO-A1-input-v2');q=replace(q,artifacts=tuple(sorted((*q.artifacts,a(ref.reference,authoring_input_payload(evidence)),a(sp,_canonical_yaml_bytes(s))),key=lambda x:str(x.relative_path))))
q=prepare_strategy_dependency_transition(base_loaded=l,candidate_loaded=l.model_copy(update={'project':p,'shots':(s,)}),request=q);m=ProductionStateCommitter(ROOT).commit(q)
(V/'CO-A1-row.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');(V/'input-revision-02.json').write_text(json.dumps({'manifest_revision':m.manifest_revision,'project_revision':2,'new_video_calls':0,'reference':ref.model_dump(mode='json')},ensure_ascii=False,indent=2)+'\n');print({'revised':True,'new_video_calls':0,'manifest_revision':m.manifest_revision})
