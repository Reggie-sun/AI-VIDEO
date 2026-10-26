from pathlib import Path
from dataclasses import replace
import json,hashlib
from ai_video.production.project import load_production_project
from ai_video.production.models import ArtifactReference
from ai_video.production.hashing import seal_artifact
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,prepare_project_registry_commit,_canonical_yaml_bytes
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A2';l=load_production_project(ROOT/'project.yaml');assert l.project.revision==1 and not any(a.operation=='video_generation' for a in l.manifest.attempts)
r=json.loads((V/'CO-A2-row.json').read_bytes());(V/'CO-A2-row-v1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
r['generation']['references']=[{'role':'scene_reference','asset_id':'co-actual-truck-frame'},{'role':'character_reference','asset_id':'co-after-image','owner_id':'luomin'}];r['generation'].pop('conditioning_compatibility');r['generation']['output_need']['duration_seconds']=4
r['shot']['required_asset_roles']=[{'role':'primary_visual','asset_ids':[],'allowed_asset_types':['video']}]
r['generation']['generation_intent']['scene_continuity']['state_constraints'].append('参考素材1是上一段实际最后一帧，只指导开头满幅灰白车厢与横向运动；参考素材2指导车驶离后同一站棚、右侧罗敏、服装、脸与空位。不能将两图溶解；必须物理车厢尾缘持续向右离场。')
evidence={'kind':'cold-open-pre-submit-route-correction/1','old_row_sha256':hashlib.sha256((V/'CO-A2-row.json').read_bytes()).hexdigest(),'new_row':r,'reason':'Actual terminal is1918x1080 and original after-state1672x941; nativeFLF requires identical geometry. Preserve both exact originals without re-generating/resizing. Explicitly choose Seedance2.5 native multimodal references, keep physical reveal and end-state QA unchanged. Correct output duration inherited8 to authored4. No paid call occurred.'};ref=authoring_input_reference(evidence)
shot=seal_artifact(l.shots[0].model_copy(update={'revision':2,'required_asset_roles':tuple(type(l.shots[0].required_asset_roles[0]).model_validate(x) for x in r['shot']['required_asset_roles']),'source_provenance':(*l.shots[0].source_provenance,ref)}));scene=seal_artifact(l.scenes[0].model_copy(update={'revision':2,'visual_reference_asset_ids':('co-actual-truck-frame','co-after-image'),'source_provenance':(*l.scenes[0].source_provenance,ref)}))
def ar(m,p):return ArtifactReference(artifact_id=m.artifact_id,revision=m.revision,content_hash=m.content_hash,path=Path(p))
sp='creative/shots/CO-A2-route-v3.yaml';cp='creative/scenes/rain-stop-route-v3.yaml';project=seal_artifact(l.project.model_copy(update={'revision':2,'source_provenance':(*l.project.source_provenance,ref),'artifacts':l.project.artifacts.model_copy(update={'shots':(ar(shot,sp),),'scenes':(ar(scene,cp),)})}))
def a(p,b):return PreparedArtifact(Path(p),b,hashlib.sha256(b).hexdigest())
request=prepare_project_registry_commit(manifest=l.manifest,project=project,registry=l.registry,attempt_id='shizhen-CO-A2-route-v3');request=replace(request,artifacts=tuple(sorted((*request.artifacts,a(ref.reference,authoring_input_payload(evidence)),a(sp,_canonical_yaml_bytes(shot)),a(cp,_canonical_yaml_bytes(scene))),key=lambda x:str(x.relative_path))));request=prepare_strategy_dependency_transition(base_loaded=l,candidate_loaded=l.model_copy(update={'project':project,'shots':(shot,),'scenes':(scene,)}),request=request);m=ProductionStateCommitter(ROOT).commit(request)
(V/'CO-A2-row.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');p=V/'CO-A2-profile.json';raw=p.read_bytes();(V/'CO-A2-profile-v1.json').write_bytes(raw);profile=json.loads(raw);profile['input_mode']='multimodal';p.write_text(json.dumps(profile,indent=2)+'\n');print({'revision':m.manifest_revision,'route':'multimodal','paid_calls':0})
