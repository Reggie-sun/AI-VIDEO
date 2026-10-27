"""Complete only the preparation tail after known read-only dependency failure."""
"""Author an isolated qualification source; retain full stair obligations separately."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,re,shutil
from ai_video.production.video_requirement import GenerationIntent
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.jimeng_contracts import JimengProfile
R=Path.cwd();V=Path(__file__).resolve().parent;OLD=V.parent/'MC03-05';LABEL='MC03-DESCENT'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(n,x):
 with (V/n).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
assert (V/'data.json').exists() and not (V/'operator-bound.json').exists()
prompt=(V/'native-prompt.zh.txt').read_text().strip()
anc=[]
for name in ['MC01-02','MC01-02-720p-v2','MC01-02-1080p-v3','MC03-05','MC03-05-repair-v2']:
 root=R/'runs/shizhen-macro-opening-20261027'/name;proj=load_production_project(root/'project.yaml');paid=[a for a in proj.manifest.attempts if a.operation=='video_generation'];assert len(paid)==1;a=paid[0];assert a.paid_provider_state.phase.value=='accepted' and a.video_generation_state.fetch_receipt and a.status.value not in {'outcome_unknown','interrupted'};f=json.loads((V.parent/name/'fetch-result.json').read_text());assert sha(root/f['artifact_path'])==f['sha256'];anc.append(dict(root=str(root.relative_to(R)),attempt_id=a.attempt_id,manifest_sha256=sha(root/'state/manifest.json'),artifact_sha256=f['sha256'],known_fetched=True))
prior=json.loads((V.parent/'MC03-05-repair-v2/operator-bound.json').read_text());now=datetime.now(timezone.utc);gate=V.parent/'MC03-05-repair-v2/qa/post-media-gate.json'
bound={**prior,'authorization_quote':'開始吧','scope':'One8s1080p descent-arrival qualification source using3 actual multimodal image inputs; conditional doorway source later; full stair goal retained','predecessor_bound_path':str((V.parent/'MC03-05-repair-v2/operator-bound.json').relative_to(R)),'predecessor_bound_sha256':sha(V.parent/'MC03-05-repair-v2/operator-bound.json'),'issued_at':now.isoformat(),'expires_at':(now+timedelta(hours=2)).isoformat(),'macro_paid_submits_before':5,'macro_cumulative_ceiling_after_authorized_unit':6,'paired_unit_cumulative_ceiling':7,'macro_cumulative_internal_credit_upper_bound':9000,'ancestors':anc,'failed_same_shot_gate_path':str(gate.relative_to(R)),'failed_same_shot_gate_sha256':sha(gate),'failed_same_shot_sha256':anc[-1]['artifact_sha256']};dump('operator-bound.json',bound)
n=json.loads((V/'node-created.json').read_text());cfg=json.loads((V/'native-model-config.json').read_text());assert cfg['mode']['mode']==4 and 8000 in cfg['mode']['duration']['valuesMs'] and cfg['mode']['materials']['maxCount']>=3
profile=JimengProfile(model_id='seedance_2.0_vip',input_mode='multimodal',account_sha256=n['account_sha256'],project_id=n['project_id'],node_id=n['node_id'],duration_seconds=8,resolution='1080p',aspect_ratio='16:9',benefit_amount=8,benefit_type=cfg['commerce']['resolutionBenefitKeys']['1080p']['benefitType'],credit_upper_bound=1500);dump('profile.json',profile.model_dump(mode='json'))
for name in ['predecessor-media-clearance.json','predecessor-assembly-user-accepted.json','predecessor-assembly-verdict.json']:shutil.copyfile(OLD/name,V/name)
s=(OLD/'bootstrap.py').read_text().replace("ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05';label='MC03-05'","ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-descent-v1';label='MC03-DESCENT'").replace("'-1080p-v1-20261027'","'-descent-v1-20261027'")
(V/'bootstrap.py').write_text(s)
dump('source-preservation-diff.json',{'parent_full_event_raw':'aecf88b4f06a005e5db32b11138dcc9b3db3700ab08c993187263e2ed21038c5','parent_full_goal':json.loads((OLD/'data.json').read_text())['objective'],'changed':['separate descent-arrival qualification before doorway','three actual same-camera references','fixed high camera for travel and foot support'],'preserved':['identity and wardrobe','normal extinguisher and pipe','same lower closed door','native speed/sound','B6/font/music'],'remaining_required_in_B':['right-hand reach/contact','one inward push','same dent/no pipe/old marks','outside-threshold stop and listening'],'full_stair_status':'NOT_EVALUATED; A alone is incomplete','new_video_calls':0,'new_call_limit':1})
print(json.dumps({'authored':True,'shot':LABEL,'prompt_chars':len(prompt),'images':3,'duration':8,'new_video_calls':0}))
