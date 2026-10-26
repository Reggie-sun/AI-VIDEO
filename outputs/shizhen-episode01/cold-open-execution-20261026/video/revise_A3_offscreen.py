from pathlib import Path
from dataclasses import replace
import hashlib,json
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.models import ArtifactReference
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,prepare_project_registry_commit,_canonical_yaml_bytes
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
v=Path(__file__).resolve().parent;root=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A3';l=load_production_project(root/'project.yaml');assert l.project.revision==2 and not any(a.operation=='video_generation' for a in l.manifest.attempts)
p=v/'CO-A3-row.json';raw=p.read_bytes();(v/'CO-A3-row-v2.json').write_bytes(raw);r=json.loads(raw);r['shot']['character_ids']=['gaozheng','luomin'];r['generation']['generation_intent']['identity_continuity']['character_ids']=['gaozheng','luomin'];e={'kind':'offscreen-dialogue-projection-correction/1','old_row_sha256':hashlib.sha256(raw).hexdigest(),'new_row':r,'reason':'Driver is voice-only: existing conversation supports undeclared offscreen speaker, whereas Shot.character_ids request visible identity references. Keep offscreen driver Character and fourth-turn script; select only the two actual visible characters, no invented driver face or fake reference.'};ref=authoring_input_reference(e)
shot=seal_artifact(l.shots[0].model_copy(update={'revision':2,'character_ids':('gaozheng','luomin'),'source_provenance':(*l.shots[0].source_provenance,ref)}));sp=Path('creative/shots/CO-A3-v2.yaml');sr=ArtifactReference(artifact_id=shot.artifact_id,revision=shot.revision,content_hash=shot.content_hash,path=sp)
project=seal_artifact(l.project.model_copy(update={'revision':3,'source_provenance':(*l.project.source_provenance,ref),'artifacts':l.project.artifacts.model_copy(update={'shots':(sr,)})}));q=prepare_project_registry_commit(manifest=l.manifest,project=project,registry=l.registry,attempt_id='shizhen-CO-A3-offscreen-v3')
def a(p,b):return PreparedArtifact(Path(p),b,hashlib.sha256(b).hexdigest())
q=replace(q,artifacts=tuple(sorted((*q.artifacts,a(ref.reference,authoring_input_payload(e)),a(sp,_canonical_yaml_bytes(shot))),key=lambda x:str(x.relative_path))));q=prepare_strategy_dependency_transition(base_loaded=l,candidate_loaded=l.model_copy(update={'project':project,'shots':(shot,)}),request=q);m=ProductionStateCommitter(root).commit(q);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print({'manifest_revision':m.manifest_revision,'new_paid_calls':0})
