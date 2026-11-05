"""Read-only candidate preparation; never starts or submits a generation."""
from pathlib import Path
import json
from dataclasses import fields,is_dataclass
from enum import Enum
from ai_video.production.shot_router import VideoRoutingPolicy,RouterPolicyIdentity
from ai_video.production.hashing import canonical_sha256
from ai_video.production.generation_decision import DecisionPolicy,ExecutionLimits
from ai_video.production.jimeng_contracts import JimengProfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from scripts.jimeng_feedback_driver import create_runtime,DriverConfiguration
P=Path(__file__).resolve().parent

def js(x):
    if hasattr(x,'model_dump'):return x.model_dump(mode='json')
    if is_dataclass(x):return {f.name:js(getattr(x,f.name)) for f in fields(x)}
    if isinstance(x,Enum):return x.value
    if isinstance(x,Path):return str(x)
    if isinstance(x,dict):return {str(k):js(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [js(v) for v in x]
    if x is None or isinstance(x,(str,int,float,bool)):return x
    return type(x).__name__

def main():
    profile=JimengProfile.model_validate_json((P.parent/'a01-repair-binding/profile.json').read_bytes())
    policy=VideoRoutingPolicy(identity=RouterPolicyIdentity(policy_id='iris-a01-two-reference-repair-qualification',policy_version='1',policy_sha256=canonical_sha256({'shot':'ep01-intro','repair_strategy':'multimodal-two-reference: ID7b identity + A01 scene; omit CF-a side/back','cumulative_attempt_ceiling':2,'cumulative_credit_ceiling':500,'prior_actual_credits':198,'profile_sha256':canonical_sha256(profile.model_dump(mode='json')),'ceiling':1})),local_resources_available=False,remote_authorized=True,budget_authorized=True,execution_purpose='qualification')
    limits=ExecutionLimits(task_id='iris-ep01-a01-two-reference-repair-002',generation_forbidden=False,allowed_remote_candidates=('jimeng/'+profile.capability_id,),paid_submit_ceiling=1,paid_submits_used=0,local_batch_limit=1,local_batch_used=0,local_total_used=0,local_resource_available=False)
    raw={'schema_version':'jimeng-feedback-driver/1','row':json.loads((P/'row.json').read_text()),'routing_policy':policy.model_dump(mode='json'),'decision_policy':DecisionPolicy(max_resamples=0,allow_bounded_exploration=True).model_dump(mode='json'),'execution_limits':limits.model_dump(mode='json'),'jimeng_profile':profile.model_dump(mode='json')}
    (P/'driver-config.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
    runtime=create_runtime(project_root=P/'project',configuration=DriverConfiguration.from_json(raw))
    result=runtime.prepare();out=js(result)
    (P/'prepare-result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    summary={'decision':out['decision'],'compilation':out.get('compilation'),'executable':result.execution_binding is not None and result.resolved_request is not None}
    if summary['executable']:
        (P/'compiled-native-prompt.zh.txt').write_text(result.compilation.request.prompt_text+'\n')
        summary['preview']=js(runtime.preview(result))
    (P/'prepare-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'executable':summary['executable'],'disposition':out['decision']['disposition'],'compilation':out.get('compilation',{}).get('outcome') if out.get('compilation') else None,'unsupported':out.get('compilation',{}).get('unsupported_field_paths') if out.get('compilation') else None},ensure_ascii=False))
if __name__=='__main__':main()
