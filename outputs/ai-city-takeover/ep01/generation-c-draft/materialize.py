"""Explicit C authoring via canonical owners; no submit, retries or lifecycle shortcuts.

Default mode is read-only inspection. --apply is for Parent only after its explicit
A01 Per-Shot Gate PASS decision; this program also reopens the retained canonical
analyzer evaluation. An independent source root is an explicit alternative, never
an automatic fallback. Neither path creates the final episode timeline.
"""
from __future__ import annotations
import argparse
from dataclasses import fields,is_dataclass,replace
from enum import Enum
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from ai_video.production.models import (AssetRegistrySnapshot,ProductionBrief,Story,StoryBeat,
    Scene,Shot,Storyboard,StoryboardBeat,ProductionProject,ProjectArtifactRefs,ArtifactReference,
    QaPolicy,StateCommitStatus)
from ai_video.production.hashing import canonical_sha256,seal_artifact,verify_artifact_hash
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (ProductionStateCommitter,PreparedArtifact,
    prepare_project_registry_commit,_canonical_yaml_bytes)
from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production._generation_feedback_reader import load_generation_execution_binding,load_generation_experience
from ai_video.production.jimeng_contracts import JimengProfile
from ai_video.production.shot_router import VideoRoutingPolicy,RouterPolicyIdentity
from ai_video.production.generation_decision import DecisionPolicy,ExecutionLimits
from ai_video.canvas_dependencies import initialize_canvas_graph
from scripts.jimeng_feedback_driver import DriverConfiguration,create_runtime
from assert_resolved_bindings import validate as validate_bindings
P=Path(__file__).resolve().parent
REPO=P.parents[3]

class PreparationBlocked(ValueError):pass

def write(name,payload):
    path=P/name
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def serial(value):
    if hasattr(value,'model_dump'):return value.model_dump(mode='json')
    if is_dataclass(value):return {f.name:serial(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,dict):return {str(k):serial(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [serial(v) for v in value]
    if isinstance(value,Enum):return value.value
    if isinstance(value,Path):return str(value)
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return type(value).__name__

def prepared(path,payload):return PreparedArtifact(Path(path),payload,hashlib.sha256(payload).hexdigest())
def typed(name,cls):
    obj=cls.model_validate_json((P/name).read_bytes())
    if not verify_artifact_hash(obj):raise PreparationBlocked('Draft semantic hash changed: '+name)
    return obj

def require_parent_source_gate(loaded,attempt_id,gate_path=None):
    """Reopen canonical bridge-backed observations, never turn a CLI flag into PASS."""
    unknown=[a.attempt_id for a in loaded.manifest.attempts if a.status.value in {'outcome_unknown','interrupted'}]
    if unknown:raise PreparationBlocked('Parent source has unresolved outcome: '+','.join(unknown))
    attempt=next((a for a in loaded.manifest.attempts if a.attempt_id==attempt_id),None)
    state=None if attempt is None else attempt.video_generation_state
    if state is None or state.fetch_receipt is None or state.execution_binding is None:
        raise PreparationBlocked('A01 exact fetched media and execution binding are not yet retained')
    fetch=state.fetch_receipt
    media=(loaded.root/fetch.artifact_path).resolve(strict=True)
    if not media.is_relative_to(loaded.root) or hashlib.sha256(media.read_bytes()).hexdigest()!=fetch.artifact_sha256:
        raise PreparationBlocked('A01 fetched media identity changed')
    binding=load_generation_execution_binding(loaded.root,state.execution_binding)
    experiences=tuple(load_generation_experience(loaded.root,p) for p in state.generation_experiences)
    entries=tuple(e for x in experiences for e in x.evidence)
    sources=tuple(s for x in experiences for s in x.evaluation_sources)
    if not sources or not any(s.proof=='analyzer' and s.analysis_evidence is not None
                             and s.artifact_sha256==fetch.artifact_sha256 for s in sources):
        raise PreparationBlocked('A01 canonical project-local MCP analyzer source is not retained; Parent must record the real Gate first')
    matches=[]
    for experience in experiences:
        if experience.projection!=binding.projection:continue
        for entry in experience.evidence:
            if entry.outcome!='media' or entry.artifact_sha256!=fetch.artifact_sha256 or entry.attempt_id!=attempt_id:continue
            diagnosis=diagnose_exact_result(entry,entries,experience.candidate.recipe,
                evaluation_sources=sources,requirement=binding.projection.requirement)
            if diagnosis.all_required_observed_pass:matches.append(entry.evidence_hash)
    if not matches:raise PreparationBlocked('A01 canonical exact-media criteria are not all PASS')
    gate_path=Path(gate_path) if gate_path is not None else P.parent/'qa/A01-v2/post-media-gate.json'
    if not gate_path.is_file():raise PreparationBlocked('Parent A01-v2 Post-Media Gate is not yet on disk')
    gate_raw=gate_path.read_bytes();post_gate=json.loads(gate_raw)
    if (post_gate.get('attempt_id')!=attempt_id or post_gate.get('artifact_sha256')!=fetch.artifact_sha256
            or post_gate.get('verdict')!='PASS' or post_gate.get('all_required_observed_pass') is not True
            or any(item.get('verdict')!='PASS' for item in post_gate.get('required_findings',()))):
        raise PreparationBlocked('Parent Post-Media Gate is not exact all-PASS for this fetched source')
    return {'post_media_gate_path':str(gate_path.resolve()),'post_media_gate_sha256':hashlib.sha256(gate_raw).hexdigest(),'attempt_id':attempt_id,'artifact_sha256':fetch.artifact_sha256,
            'evaluation_evidence_hashes':sorted(set(matches)),'state_status':attempt.status.value,
            'state_phase':state.phase.value,'parent_project_sha256':loaded.project.content_hash}

def append_blockers(loaded):
    return [a.attempt_id+':'+a.status.value for a in loaded.manifest.attempts
            if a.status in {StateCommitStatus.RUNNING,StateCommitStatus.OUTCOME_UNKNOWN}]

def merge_registry(loaded,independent):
    draft=AssetRegistrySnapshot.model_validate_json((P/'registry-draft.json').read_bytes())
    base={a.asset_id:a for a in loaded.registry.assets}
    selected={a.asset_id:a for a in draft.assets}
    for aid in ('iris-cf-face','iris-cf-details'):
        if aid not in base or base[aid].sha256!=selected[aid].sha256:
            raise PreparationBlocked('Existing canonical identity differs: '+aid)
    scene=selected['iris-c-interior']
    if scene.asset_id in base and base[scene.asset_id]!=scene:
        raise PreparationBlocked('C scene asset label already belongs to different bytes/provenance')
    records={aid:base[aid] for aid in ('iris-cf-face','iris-cf-details')} if independent else base.copy()
    records[scene.asset_id]=scene
    registry=AssetRegistrySnapshot(revision_id='0'*64,content_hash='0'*64,assets=tuple(sorted(records.values(),key=lambda a:a.asset_id)))
    h=registry_semantic_sha256(registry)
    return registry.model_copy(update={'revision_id':h,'content_hash':h})

def bundle(loaded,*,independent,gate):
    """Pure candidate preparation; no directories, snapshots or Manifest writes."""
    registry=merge_registry(loaded,independent)
    scene,shot,qa=typed('scene.json',Scene),typed('shot.json',Shot),typed('qa-policy.json',QaPolicy)
    selections=json.loads((P/'source-selections.json').read_text())
    artifacts={}
    for item in selections:
        source=(REPO/item['path']).resolve(strict=True)
        if not source.is_relative_to(REPO):raise PreparationBlocked('Source escaped repository')
        raw=source.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256'] or len(raw)!=item['size_bytes']:
            raise PreparationBlocked('Approved C source changed: '+item['asset_id'])
        record=next(a for a in registry.assets if a.asset_id==item['asset_id'])
        artifacts[record.artifact_path]=prepared(record.artifact_path,raw)
    char=next(c for c in loaded.characters if c.character_id=='IRIS')
    # Preserve exact existing identity and its creative evidence, never clone attempts/history.
    provenance=list(dict.fromkeys((*scene.source_provenance,*shot.source_provenance,*qa.source_provenance,*char.source_provenance)))
    cost_history={'kind':'iris-c-cumulative-source-budget/1','source':'Parent current same-account live balance observation and explicit new bounded C unit','initial_observed_balance_credits':68189,'current_observed_balance_credits':67793,'prior_video_submits':2,'prior_observed_total_credits':396,'prior_a1_observed_credits':198,'prior_a2_observed_credits':198,'cumulative_video_submit_ceiling':3,'cumulative_operator_credit_ceiling':750,'new_c_unit_max_submits':1,'new_c_operator_credit_ceiling':250,'automatic_retries':0,'prior_a1':{'project_root':str(P.parent/'generation/project'),'attempt_id':'iris-ep01-a01-qualification-001','artifact_sha256':'65f17d6860cbde39df398f42138149a7b4fc7a0bda7fdd96952b88134a0601d5','verdict':'FAIL retained'},'prior_a2':gate,'authority':'retained history and bounded preparation data only; no submit permit or Production activation'}
    cost_ref=authoring_input_reference(cost_history);provenance.append(cost_ref)
    artifacts[Path(cost_ref.reference)]=prepared(cost_ref.reference,authoring_input_payload(cost_history))
    lineage={'kind':'iris-c-parent-source-lineage/1','parent_root':str(loaded.root),
             'parent_project':loaded.manifest.active_project.model_dump(mode='json'),'gate':gate,
             'authority':'source provenance only; not permission, qualification promotion or final acceptance'}
    lineage_ref=authoring_input_reference(lineage);provenance.append(lineage_ref)
    artifacts[Path(lineage_ref.reference)]=prepared(lineage_ref.reference,authoring_input_payload(lineage))
    for ref in provenance:
        if ref in (lineage_ref,cost_ref):continue
        if not ref.reference.startswith('evidence/authoring-input/'):continue
        own=P/ref.reference;original=loaded.root/ref.reference
        source=own if own.is_file() else original
        raw=source.read_bytes()
        if canonical_sha256(json.loads(raw))!=ref.content_hash:raise PreparationBlocked('Creative provenance changed')
        artifacts[Path(ref.reference)]=prepared(ref.reference,raw)
    def reseal(obj,**updates):return seal_artifact(obj.model_copy(update=updates))
    def model_artifact(model):
        path=Path('creative')/model.artifact_id/(model.content_hash+'.yaml')
        artifacts[path]=prepared(path,_canonical_yaml_bytes(model))
        return ArtifactReference(artifact_id=model.artifact_id,revision=model.revision,content_hash=model.content_hash,path=path)
    scene=reseal(scene,artifact_id='iris-c-scene')
    shot=reseal(shot,artifact_id='iris-c-shot')
    if independent:
        brief=seal_artifact(ProductionBrief(artifact_id='iris-c-brief',revision=1,content_hash='0'*64,creation_receipt_id='iris-c-authoring',source_provenance=tuple(provenance),title='IRIS EP01 interior source',objective='已认可室内观察六秒源片；保留显示器背面，独立图形由最终剪辑负责',audience='中文短视频观众',format='1920×1080 30fps horizontal source',language='zh',constraints=shot.continuity_constraints))
        story=seal_artifact(Story(artifact_id='iris-c-story',revision=1,content_hash='0'*64,creation_receipt_id='iris-c-authoring',source_provenance=tuple(provenance),language='zh',logline='同一冷静观察者看向室内设备',synopsis='闭口观察，不操作设备，不向显示器背面贴图',beats=(StoryBeat(beat_id='dns',summary='室内观察反应'),)))
        board=seal_artifact(Storyboard(artifact_id='iris-c-storyboard',revision=1,content_hash='0'*64,creation_receipt_id='iris-c-authoring',source_provenance=tuple(provenance),beats=(StoryboardBeat(beat_id='dns',scene_id='interior',shot_ids=('ep01-dns',),narrative_intent='独立室内源片，不是假装从前镜连续走入'),)))
        refs=ProjectArtifactRefs(brief=model_artifact(brief),story=model_artifact(story),characters=(model_artifact(char),),scenes=(model_artifact(scene),),storyboard=model_artifact(board),shots=(model_artifact(shot),))
        project=seal_artifact(ProductionProject(artifact_id='iris-c-project',revision=1,content_hash='0'*64,creation_receipt_id='iris-c-authoring',source_provenance=tuple(provenance),project_id='iris-ep01-c-source',title='IRIS EP01 C interior source',default_language='zh',delivery_profile=loaded.project.delivery_profile,renderer_policy=loaded.project.renderer_policy,artifacts=refs))
        candidate=None
    else:
        if any(s.shot_id=='ep01-dns' for s in loaded.shots):raise PreparationBlocked('C Shot already exists; inspect current revision instead of rematerializing')
        if any(s.scene_id=='interior' for s in loaded.scenes):raise PreparationBlocked('Interior Scene already exists; explicit reuse/revision required')
        story=reseal(loaded.story,revision=loaded.story.revision+1,source_provenance=tuple(dict.fromkeys((*loaded.story.source_provenance,*provenance))),beats=(*loaded.story.beats,StoryBeat(beat_id='dns',summary='同一人物的独立室内观察反应')))
        board=reseal(loaded.storyboard,revision=loaded.storyboard.revision+1,source_provenance=tuple(dict.fromkeys((*loaded.storyboard.source_provenance,*provenance))),beats=(*loaded.storyboard.beats,StoryboardBeat(beat_id='dns',scene_id='interior',shot_ids=('ep01-dns',),narrative_intent='由最终剪辑独立切入室内观察，不伪装为连续动作')))
        prior=loaded.project.artifacts
        refs=prior.model_copy(update={'story':model_artifact(story),'storyboard':model_artifact(board),'scenes':(*prior.scenes,model_artifact(scene)),'shots':(*prior.shots,model_artifact(shot))})
        project=reseal(loaded.project,revision=loaded.project.revision+1,title='IRIS EP01 source previews',source_provenance=tuple(dict.fromkeys((*loaded.project.source_provenance,*provenance))),artifacts=refs)
        candidate=loaded.model_copy(update={'project':project,'registry':registry,'story':story,'storyboard':board,'scenes':(*loaded.scenes,scene),'shots':(*loaded.shots,shot)})
        old_final=loaded.qa_policy.final_output
        if old_final is not None:
            final=list(old_final.requirements)
            for req in qa.final_output.requirements:
                existing=next((x for x in final if x.requirement_id==req.requirement_id),None)
                if existing is not None and existing!=req:raise PreparationBlocked('Final requirement ID collision; explicit QA authoring required')
                if existing is None:final.append(req)
            qa=reseal(qa,source_provenance=tuple(provenance),final_output=old_final.model_copy(update={'goal_version':old_final.goal_version+'-with-c','user_goal':old_final.user_goal+'；追加同一人物室内观察源片，保留前镜所有观看要求','requirements':tuple(final)}))
    return project,registry,tuple(artifacts[p] for p in sorted(artifacts)),qa,candidate

def make_config(profile,row):
    if (profile.model_id,profile.input_mode,profile.duration_seconds,profile.resolution,profile.aspect_ratio)!=('seedance_2.0_vip','multimodal',6,'1080p','16:9'):
        raise PreparationBlocked('Parent must provide the exact C 6s1080p16:9 multimodal live profile')
    routing=VideoRoutingPolicy(identity=RouterPolicyIdentity(policy_id='iris-c-qualification',policy_version='1',policy_sha256=canonical_sha256({'shot':'ep01-dns','profile':profile.model_dump(mode='json'),'ceiling':1,'prior_submits':2,'prior_observed_cost_credits':396,'cumulative_submit_ceiling':3,'cumulative_credit_ceiling':750})),local_resources_available=False,remote_authorized=True,budget_authorized=True,execution_purpose='qualification')
    limits=ExecutionLimits(task_id='iris-ep01-c-source-003',generation_forbidden=False,allowed_remote_candidates=('jimeng/'+profile.capability_id,),paid_submit_ceiling=1,paid_submits_used=0,local_batch_limit=1,local_batch_used=0,local_total_used=0,local_resource_available=False)
    return {'schema_version':'jimeng-feedback-driver/1','row':row,'routing_policy':routing.model_dump(mode='json'),'decision_policy':DecisionPolicy(max_resamples=0,allow_bounded_exploration=True).model_dump(mode='json'),'execution_limits':limits.model_dump(mode='json'),'jimeng_profile':profile.model_dump(mode='json')}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=P.parent/'a01-first-frame-repair/project')
    parser.add_argument('--a01-attempt',default='iris-ep01-a01-two-reference-repair-002')
    parser.add_argument('--post-media-gate',type=Path,default=P.parent/'qa/A01-v2/post-media-gate.json')
    parser.add_argument('--profile',type=Path,help='Parent-supplied freshly observed C node/profile; required for --apply')
    parser.add_argument('--independent-source-root',type=Path,help='Explicit alternative; must be a new contained C source directory')
    parser.add_argument('--apply',action='store_true',help='Parent executes only after explicitly deciding A01 Per-Shot Gate all PASS')
    args=parser.parse_args()
    loaded=load_production_project(args.project_root/'project.yaml')
    blockers=append_blockers(loaded)
    independent=args.independent_source_root is not None
    if not args.apply:
        print(json.dumps({'mode':'read_only_inspection','append_blockers':blockers,'requires_parent_explicit_a01_gate_pass':True,'canonical_gate_required':'retained exact-media MCP evaluator observations all PASS','independent_alternative':'explicit --independent-source-root within generation-c-draft only; keeps A01 history intact','mutations':0},ensure_ascii=False));return
    if args.profile is None:raise PreparationBlocked('--profile is required for materialization')
    gate=require_parent_source_gate(loaded,args.a01_attempt,args.post_media_gate)
    if blockers and not independent:
        raise PreparationBlocked('Canonical append refused before mutation: unresolved '+','.join(blockers)+'. Qualification cannot activate as production; prospective-target exception cannot change Project/Registry. Parent may explicitly select a separate source project after real Gate PASS.')
    profile=JimengProfile.model_validate_json(args.profile.read_bytes())
    row=json.loads((P/'row.json').read_text());config=make_config(profile,row)
    project,registry,artifacts,qa,candidate=bundle(loaded,independent=independent,gate=gate)
    before_attempts=loaded.manifest.attempts
    if independent:
        root=args.independent_source_root.resolve()
        if not root.is_relative_to(P) or root==P or root.exists():raise PreparationBlocked('Independent root must be a NEW directory strictly within this owned draft directory')
        root.mkdir(parents=True,mode=0o700)
        committer=ProductionStateCommitter(root)
        manifest=committer.bootstrap_initial_state(attempt_id='iris-c-bootstrap',project=project,registry=registry,artifacts=artifacts)
        manifest=initialize_canvas_graph(committer,'iris-c-graph')
        manifest=committer.upgrade_manifest_schema('2.14',expected_manifest_revision=manifest.manifest_revision)
    else:
        root=loaded.root;committer=ProductionStateCommitter(root)
        request=prepare_project_registry_commit(manifest=loaded.manifest,project=project,registry=registry,attempt_id='iris-c-authoring-'+project.content_hash[:16])
        request=replace(request,artifacts=tuple(sorted((*request.artifacts,*artifacts),key=lambda a:a.relative_path.as_posix())))
        request=prepare_strategy_dependency_transition(base_loaded=loaded,candidate_loaded=candidate,request=request)
        manifest=committer.commit(request)
        current=load_production_project(root/'project.yaml')
        if current.manifest.attempts[:len(before_attempts)]!=before_attempts:raise PreparationBlocked('Existing attempt history changed unexpectedly')
        original=next(s for s in loaded.shots if s.shot_id=='ep01-intro')
        if next(s for s in current.shots if s.shot_id=='ep01-intro')!=original:raise PreparationBlocked('A01 Shot changed unexpectedly')
    committer.activate_qa_policy(qa,attempt_id='iris-c-qa-'+qa.content_hash[:16],expected_manifest_revision=manifest.manifest_revision)
    write('driver-config.json',config)
    runtime=create_runtime(project_root=root,configuration=DriverConfiguration.from_json(config))
    result=runtime.prepare();write('prepare-result.json',serial(result))
    if result.resolved_request is None or result.execution_binding is None:
        write('prepare-blocker.json',{'decision':serial(result.decision),'compilation':serial(result.compilation),'new_provider_calls':0})
        raise PreparationBlocked('C authoring retained; prepare is blocked, inspect prepare-blocker.json; do not start or submit')
    binding_validation=validate_bindings({'resolved_request':result.resolved_request.model_dump(mode='json')})
    (P/'compiled-native-prompt.zh.txt').write_text(result.compilation.request.prompt_text+'\n')
    write('materialization-result.json',{'project_root':str(root),'independent_source':independent,'parent_gate':gate,'binding_validation':binding_validation,'request_hash':result.resolved_request.resolved_generation_hash,'new_provider_calls':0,'new_attempt_started':False})
    print(json.dumps({'project_root':str(root),'prepared':True,'new_provider_calls':0,'new_attempt_started':False},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except PreparationBlocked as error:
        print(json.dumps({'blocked':True,'reason':str(error)},ensure_ascii=False),file=sys.stderr);raise SystemExit(2)
