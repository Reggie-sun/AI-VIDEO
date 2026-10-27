"""Bind first/last input images to the Shot through the canonical authoring commit."""
from pathlib import Path
from dataclasses import replace
import json,hashlib
from ai_video.production.models import AssetRoleRequirement,AssetType,ArtifactReference
from ai_video.production.project import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.state_commit import ProductionStateCommitter,PreparedArtifact,prepare_project_registry_commit,_canonical_yaml_bytes
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
V=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05-repair-v2';p=load_production_project(ROOT/'project.yaml');assert p.project.revision==2 and not [a for a in p.manifest.attempts if a.operation=='video_generation'];row=json.loads((V/'row.json').read_text());images=json.loads((V/'data.json').read_text())['images'];evidence=dict(kind='shot-input-frame-roles-authoring/1',shot_id='MC03-05',roles={role:image['asset_id'] for role,image in zip(['first_frame','last_frame'],images)},scope='Explicit source-frame inputs for already-approved full stair repair; no output acceptance',parent_assessment_sha256=hashlib.sha256((V/'conditioning-assessment.json').read_bytes()).hexdigest());ref=authoring_input_reference(evidence)
roles=(*p.shots[0].required_asset_roles,*(AssetRoleRequirement(role=role,asset_ids=(image['asset_id'],),allowed_asset_types=(AssetType.IMAGE,)) for role,image in zip(['first_frame','last_frame'],images)))
shot=seal_artifact(p.shots[0].model_copy(update={'revision':p.shots[0].revision+1,'content_hash':'0'*64,'source_provenance':(*p.shots[0].source_provenance,ref),'required_asset_roles':roles}));path=Path('creative/shots/MC03-05-r2-frame-inputs.yaml');ptr=ArtifactReference(artifact_id=shot.artifact_id,revision=shot.revision,content_hash=shot.content_hash,path=path)
project=seal_artifact(p.project.model_copy(update={'revision':p.project.revision+1,'content_hash':'0'*64,'source_provenance':(*p.project.source_provenance,ref),'artifacts':p.project.artifacts.model_copy(update={'shots':(ptr,)})}))
request=prepare_project_registry_commit(manifest=p.manifest,project=project,registry=p.registry,attempt_id='stair-firstlast-explicit-input-bindings')
b=_canonical_yaml_bytes(shot);a=authoring_input_payload(evidence);extras=(PreparedArtifact(path,b,hashlib.sha256(b).hexdigest()),PreparedArtifact(Path(ref.reference),a,hashlib.sha256(a).hexdigest()));request=replace(request,artifacts=tuple(sorted((*request.artifacts,*extras),key=lambda x:x.relative_path.as_posix())))
request=prepare_strategy_dependency_transition(base_loaded=p,candidate_loaded=p.model_copy(update={'project':project,'shots':(shot,)}),request=request);ProductionStateCommitter(ROOT).commit(request)
row['shot']['required_asset_roles']=[x.model_dump(mode='json') for x in roles];(V/'row.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');(V/'frame-role-binding.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'project_revision':project.revision,'shot_revision':shot.revision,'bound_roles':['first_frame','last_frame'],'new_paid_calls':0}))
