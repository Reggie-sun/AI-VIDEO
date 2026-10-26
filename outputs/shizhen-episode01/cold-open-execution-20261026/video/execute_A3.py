"""Thin operator wiring over existing generation, committer and Jimeng owners."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
from ai_video.canvas_planning import canvas_feedback_context
from ai_video.production.generation_decision import DecisionPolicy,ExecutionLimits
from ai_video.production.generation_feedback import GenerationFeedbackOrchestrator,RegisteredGenerationTarget,create_generation_candidates
from ai_video.production.hashing import canonical_sha256
from ai_video.production.jimeng import JimengVideoProvider
from ai_video.production.jimeng_browser import JimengBrowserTransport
from ai_video.production.jimeng_contracts import JimengProfile,JIMENG_ORIGIN
from ai_video.production.models import ActorIdentity
from ai_video.production.paid_provider import PaidProviderCallPreview,PaidProviderAuthorizationDecision,SecretReference
from ai_video.production.project import load_production_project
from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance
from ai_video.production.shot_router import AdapterCompilerContract,VideoRoutingPolicy,RouterPolicyIdentity
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService
V=Path(__file__).resolve().parent;RUN=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001';ROOT=RUN/'cold-open-execution/CO-A3';ATTEMPT='shizhen-CO-A3-qualification-001'
sys.path.insert(0,str(RUN));from execute_repair import _jsonable

def dump(name,x):
 with (V/('CO-A3-'+name)).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def stack():
 loaded=load_production_project(ROOT/'project.yaml');ancestors=[a for name in ['trial-S01-v3','trial-S02-v1','cold-open-execution/CO-A1','cold-open-execution/CO-A2','trial-S03-v2'] for a in load_production_project(RUN/name/'project.yaml').manifest.attempts if a.operation=='video_generation']
 assert len(ancestors)==9 and all(a.paid_provider_state and a.paid_provider_state.phase.value not in {'outcome_unknown','submit_intent'} for a in ancestors)
 local=[a for a in loaded.manifest.attempts if a.operation=='video_generation'];assert len(local)<=1 and all(a.attempt_id==ATTEMPT for a in local)
 assert all(a.status.value not in {'outcome_unknown','interrupted'} and (a.paid_provider_state is None or a.paid_provider_state.phase.value!='outcome_unknown') for a in local)
 raw=(V/'operator-bound-cross-window.json').read_bytes();bound=json.loads(raw);assert bound['new_film_video_ceiling']==10 and bound['old_video_submit_count']==6 and bound['automatic_retries']==0
 profile=JimengProfile.model_validate_json((V/'CO-A3-profile.json').read_bytes());assert (profile.input_mode,profile.duration_seconds,profile.resolution)==('multimodal',22,'1080p')
 gate=json.loads((V.parent/'qa/CO-A2-post-media-gate.json').read_text());assert gate['verdict']=='PASS' and all(x['verdict']=='PASS' for x in gate['required_findings']);assert hashlib.sha256(Path(gate['artifact_path']).read_bytes()).hexdigest()==gate['artifact_sha256']
 authorized={};c=ProductionStateCommitter(ROOT,paid_provider_authorizer=lambda p:authorized.get(p.preview_fingerprint))
 def reference(binding):
  a=next(x for x in loaded.registry.assets if x.asset_id==binding.asset_id);b=loaded.asset_paths[a.asset_id].read_bytes();assert hashlib.sha256(b).hexdigest()==binding.asset_sha256 and len(b)==binding.size_bytes;return b
 provider=JimengVideoProvider(profile=profile,transport=JimengBrowserTransport(profile_dir=Path('/home/reggie/.local/share/ai-video/playwright-mcp/profile'),playwright_module=Path('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright')),reference_resolver=reference,committer=c)
 target=RegisteredGenerationTarget(provider=provider,profile=profile.pointer(),compiler_contract=AdapterCompilerContract.create(compiler_id=profile.compiler_id,compiler_version='1'),output_requirement=profile.output())
 routing=VideoRoutingPolicy(identity=RouterPolicyIdentity(policy_id='shizhen-cold-open-qualification',policy_version='1',policy_sha256=canonical_sha256({'operator_bound_sha256':hashlib.sha256(raw).hexdigest(),'shot_id':'CO-A3'})),local_resources_available=False,remote_authorized=True,budget_authorized=True,execution_purpose='qualification')
 row=json.loads((V/'CO-A3-row.json').read_text());context=lambda cur:canvas_feedback_context(loaded=cur,row=row,policy=routing)
 candidates,_=create_generation_candidates(projection=context(loaded)['projection'],targets=(target,),acceptance=selected_shot_generation_acceptance(loaded,'CO-A3'),final_output_goal=loaded.qa_policy.final_output,source_project=loaded,generation_id=context(loaded)['lifecycle'].generation_id,task_id='shizhen-CO-A3-qualification')
 limits=ExecutionLimits(task_id='shizhen-CO-A3-qualification',generation_forbidden=False,allowed_remote_candidates=tuple(x.candidate_id for x in candidates),paid_submit_ceiling=1,paid_submits_used=sum(a.paid_provider_state is not None for a in local),local_batch_limit=1,local_batch_used=0,local_total_used=0,local_resource_available=False)
 orchestrator=GenerationFeedbackOrchestrator.for_project(committer=c,targets=(target,),context_loader=context,policy=DecisionPolicy(max_resamples=0,allow_bounded_exploration=True))
 return dict(loaded=loaded,local=local,profile=profile,provider=provider,committer=c,bound=bound,boundraw=raw,authorized=authorized,orchestrator=orchestrator,limits=limits)
def paid(s,request):
 p=s['provider'].preview(request);assert p.estimated_cost_upper_bound_microunits==1500*1000000
 return PaidProviderCallPreview.create(attempt_id=ATTEMPT,operation='video_generation',provider_kind='jimeng',model_id='seedance_2.5',request_fingerprint=request.resolved_generation_hash,billing_mode='remote_metered',currency='CRD',estimated_cost_upper_bound_microunits=1500*1000000,destination=JIMENG_ORIGIN,method='POST',egress_items=s['provider'].egress_items(request),retention_mode='provider_standard',provider_policy_snapshot_id='shizhen-cold-open-CO-A3',secret_reference=SecretReference(kind='secret_store',reference_id='JIMENG_BROWSER_SESSION'))
def main(action):
 s=stack();service=VideoGenerationService(committer=s['committer'],provider=s['provider'])
 if action=='prepare':
  assert not s['local'];p=s['orchestrator'].prepare(limits=s['limits'])
  if p.execution_binding is None or p.resolved_request is None:
   dump('prepare-blocker.json',{'decision':_jsonable(p.decision),'compilation':_jsonable(p.compilation)});print(json.dumps({'executable':False,'disposition':p.decision.disposition,'unsupported':getattr(p.compilation,'unsupported_field_paths',None)}));return
  req=p.resolved_request;prompt=p.compilation.request.prompt_text
  for b in (*req.image_bindings,*req.media_bindings):s['provider']._reference_resolver(b)
  lint={'three_native_references':[x.asset_id for x in req.image_bindings]==['CO-A3-ref-01-before','CO-A3-ref-02-after','CO-A3-ref-03-close'],'native_multimodal_markers':all(x in prompt for x in ['{{image:0}}','{{image:1}}','{{image:2}}']),'four_lines_each_once':all(prompt.count(x)==1 for x in ['师傅，我们在站里，两位。','让他别急，路滑。','就你一位？','嗯，就我一个。']),'no_music':'Music: none.' in prompt,'left_hand':'左手' in prompt,'physical_occlusion_and_reveal':'遮满' in prompt and '尾缘' in prompt,'two_camera_setups':'胸上近景' in prompt and '固定中远景' in prompt,'duration22':p.compilation.request.output_requirement.duration_seconds==22,'1080p':p.compilation.request.output_requirement.resolution_label=='1080p'}
  dump('prompt-lint.json',lint)
  if not all(lint.values()):raise RuntimeError('Native prompt lint failed')
  pp=paid(s,req);dump('prepare.json',{'execution_binding':_jsonable(p.execution_binding),'compiled_request':_jsonable(p.compilation.request),'resolved_request':_jsonable(req),'paid_provider_preview':_jsonable(pp),'historical_video_calls':9,'new_video_calls':0});(V/'CO-A3-native-prompt.zh.txt').write_text(prompt+'\n');print(json.dumps({'executable':True,'lint':lint,'prompt_chars':len(prompt)}))
 elif action=='start':
  assert not s['local'];p=s['orchestrator'].prepare(limits=s['limits']);assert p.execution_binding.binding_hash==json.loads((V/'CO-A3-prepare.json').read_text())['execution_binding']['binding_hash'];m=service.start(attempt_id=ATTEMPT,request=p.resolved_request,execution_binding=p.execution_binding);print(json.dumps({'started':True,'manifest_revision':m.manifest_revision}))
 elif action=='submit':
  assert len(s['local'])==1 and s['local'][0].paid_provider_state is None
  _,state=service._state(ATTEMPT);assert state.phase.value=='request';req=s['committer']._reopen_video_request(state.request);pp=paid(s,req);b=s['bound'];issued=datetime.fromisoformat(b['issued_at']);expires=datetime.fromisoformat(b['expires_at']);assert issued<=datetime.now(timezone.utc)<expires
  receipt='cold-open-bound-'+hashlib.sha256(s['boundraw']).hexdigest()[:16]
  auth=PaidProviderAuthorizationDecision.create(attempt_id=ATTEMPT,preview_fingerprint=pp.preview_fingerprint,explicit_opt_in=True,actor=ActorIdentity(actor_id='user',actor_kind='human'),opt_in_policy_receipt_id=receipt,budget_policy_id='shizhen-cold-open-4500-internal-CRD',budget_currency='CRD',project_budget_ceiling_microunits=4500*1000000,per_call_ceiling_microunits=1500*1000000,egress_authorized=True,egress_policy_receipt_id=receipt,live_test_authorized=True,live_authorization_receipt_id=receipt,issued_at=issued,expires_at=expires,max_submit_count=1)
  s['authorized'][pp.preview_fingerprint]=auth;dump('submit-intent.json',{'attempt_id':ATTEMPT,'old_calls':9,'new_call_number':3,'overall_ceiling':10,'request_hash':req.resolved_generation_hash,'preview_fingerprint':pp.preview_fingerprint,'created_at':datetime.now(timezone.utc).isoformat()})
  result=service.submit_once(attempt_id=ATTEMPT,paid_preview=pp,reservation_id='shizhen-CO-A3-reservation-001');dump('submit-result.json',_jsonable(result));print(json.dumps({'accepted':True,'overall_video_calls':10,'cold_open_video_calls':3}))
 elif action=='poll':
  r=service.refresh_once(attempt_id=ATTEMPT);print(json.dumps({'state':r.state.value,'progress_milli':r.progress_milli}))
 elif action=='fetch':
  r=service.fetch_once(attempt_id=ATTEMPT);result={'artifact_path':str(r.relative_path),'sha256':r.receipt.artifact_sha256,'bytes':r.receipt.size_bytes};dump('fetch-result.json',result);print(json.dumps(result))
 else:raise ValueError('prepare/start/submit/poll/fetch')
if __name__=='__main__':main(sys.argv[1])
