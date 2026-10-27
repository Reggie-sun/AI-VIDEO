"""One bounded qualification repair through existing authoring and provider owners."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib, shutil, re
from PIL import Image
from ai_video.production.video_requirement import GenerationIntent
from ai_video.production.hashing import canonical_sha256
from ai_video.production.jimeng_contracts import JimengProfile
from ai_video.production.project import load_production_project

R=Path.cwd();V=Path(__file__).resolve().parent;OLD=V.parent/'MC03-05'
ROOT=R/'runs/shizhen-macro-opening-20261027/MC03-05-repair-v2'
def dump(name,obj):
 with (V/name).open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
olddata=json.loads((OLD/'data.json').read_text());row=json.loads((OLD/'row.json').read_text());g=row['generation']['generation_intent']
prompt=(V/'native-prompt.zh.txt').read_text().strip();parts=prompt.splitlines();assert len(parts)==5 and not re.search('[A-Za-z]',prompt)
start=R/'referces/shizhen/macro-opening-20261027/L01-r1.png';end=R/'referces/shizhen/macro-opening-20261027/door-push-repair-03/L03-push-open.png'
images=[]
for i,(path,role) in enumerate([(start,'first_frame'),(end,'last_frame')]):
 with Image.open(path) as im:w,h=im.size;im.verify()
 rec=dict(schema_version='agent-generated-image-observation/1',sha256=sha(path),size_bytes=path.stat().st_size,width=w,height=h,generator='builtin image_gen.imagegen',tool_identity_claim='builtin only; exact internal model not exposed',fictional_characters=True,platform_admission='NOT_EVALUATED',semantic_review='Parent viewed exact ordinary-platform start and physically recessed inward-open endpoint; static evidence does not prove video action',source_path=str(path.relative_to(R)),reference_role=role)
 name='reference-'+str(i+1)+'-source.json';dump(name,rec);aid='MC03-05-repair-v2-'+role
 images.append(dict(asset_id=aid,node_id=aid+'-node',resource_id=aid+'-local-generated',path=str(path),usage_license='Original fictional task references for authorized Shizhen stair repair',generated_source=dict(record_path=str((V/name).relative_to(R)),record_sha256=sha(V/name),tool=dict(name='builtin-imagegen',version='tool-interface'))))
g['subject_action']['progression']='\n'.join(parts[1:4])
g['camera_intent'].update(movement='短随真实下行，完成到达后直接切门外中景，一次推门和同侧停步核对',framing_intent='先看清正常平台凹痕与管道，再用门外中景同时看到右手、门槛、门内凹痕和旧印；不另切掉接触过程',stability='稳定短跟随和门外稳定观察')
g['camera_endpoint']['end_framing']='同侧门外中景，门扇退在门框后方、右手保持接触，两个门内线索可见'
g['axis_continuity']['framing_continuity']='下行到达后从门外同侧看一次向内推门，门边退远而非伸向摄影机，右手随把手前伸'
g['performance_intent']['visible_response']='见到两处细节差异后停步核对，再轻微侧头听辨，肩背与侧脸反应克制'
g['lighting_intent']['direction']='沿首帧普通平台和尾帧门外中景的实用光保持'
g['camera_subject_relation']['end_relation']='门外同侧观察董文慧扶门与两个门内线索，不丢右手接触'
g=GenerationIntent.model_validate(g).model_dump(mode='json');row['generation']['generation_intent']=g
row['shot'].update(intent=prompt,generated_video_rationale='已知失败的同一MC03–MC05修复：可用下行不足以剪辑保住完整事件，因此用严格首尾帧约束一次完整12秒，保留原剧情与人物，不再六参考自由排序')
row['generation']['references']=[dict(role=role,asset_id=x['asset_id']) for role,x in zip(['approved_keyframe','last_frame'],images)]
dump('row.json',row)
data=olddata;data.update(images=images,scene_images=[x['asset_id'] for x in images],intent_sha256=canonical_sha256(g),objective='修复同一MC03–MC05的提前揭示、反向上楼和拉门：先建立正常凹痕与管道、真实下楼到达、一次向内推门、停步核对听辨；不改B6、字体、音乐或角色')
data['characters'][0]['reference_asset_ids']=[x['asset_id'] for x in images]
data['fragments']={k:[parts[i] for i in indexes] for k,indexes in dict(identity=[0],action=[1,2,3],camera=[1,2,3],performance=[1,2,3],space=[1,2,3],art=[0,4],sound=[4]).items()}
data['observations']['camera']='首帧为普通楼梯、不能提前展示开门；下行到达后直接切同侧门外中景，连续看清推门接触及停步核对，不叠化或重演'
data['observations']['space']='正常平台灭火器旁有管道，低处门内相同凹痕旁无管道有旧印；真实下行至低处，门自由边退入门框后方、右手前伸且双脚门外，不后退拉门'
dump('data.json',data)
anc=[]
for name in ['MC01-02','MC01-02-720p-v2','MC01-02-1080p-v3','MC03-05']:
 root=R/'runs/shizhen-macro-opening-20261027'/name;p=load_production_project(root/'project.yaml');calls=[a for a in p.manifest.attempts if a.operation=='video_generation'];assert len(calls)==1;a=calls[0]
 assert a.paid_provider_state.phase.value=='accepted' and a.video_generation_state.fetch_receipt and a.status.value not in {'outcome_unknown','interrupted'}
 f=json.loads((V.parent/name/'fetch-result.json').read_text());assert sha(root/f['artifact_path'])==f['sha256']
 anc.append(dict(root=str(root.relative_to(R)),attempt_id=a.attempt_id,manifest_sha256=sha(root/'state/manifest.json'),artifact_sha256=f['sha256'],known_fetched=True))
prior=json.loads((OLD/'operator-bound.json').read_text());now=datetime.now(timezone.utc)
bound={**prior,'authorization_quote':'繼續','scope':'One same-event12s1080p Seedance2.0 native first_last_frame qualification repair; original4 submissions retained, no automatic retry or next event; two builtin image calls already known','predecessor_bound_path':str((OLD/'operator-bound.json').relative_to(R)),'predecessor_bound_sha256':sha(OLD/'operator-bound.json'),'issued_at':now.isoformat(),'expires_at':(now+timedelta(hours=2)).isoformat(),'macro_paid_submits_before':4,'macro_cumulative_ceiling_after_authorized_unit':5,'macro_cumulative_internal_credit_upper_bound':7500,'ancestors':anc,'failed_same_shot_gate_path':str((OLD/'qa/post-media-gate.json').relative_to(R)),'failed_same_shot_gate_sha256':sha(OLD/'qa/post-media-gate.json'),'failed_same_shot_sha256':anc[-1]['artifact_sha256']};dump('operator-bound.json',bound)
n=json.loads((V/'node-created.json').read_text());cfg=json.loads((V/'native-model-config.json').read_text());assert cfg['mode']['mode']==3 and cfg['mode']['materials']['roles']==[1,2] and 12000 in cfg['mode']['duration']['valuesMs']
profile=JimengProfile(model_id='seedance_2.0_vip',input_mode='first_last_frame',account_sha256=n['account_sha256'],project_id=n['project_id'],node_id=n['node_id'],duration_seconds=12,resolution='1080p',aspect_ratio='16:9',benefit_amount=12,benefit_type=cfg['commerce']['resolutionBenefitKeys']['1080p']['benefitType'],credit_upper_bound=1500);dump('profile.json',profile.model_dump(mode='json'))
for name in ['predecessor-media-clearance.json','predecessor-assembly-user-accepted.json','predecessor-assembly-verdict.json']:
 shutil.copyfile(OLD/name,V/name)
s=(OLD/'bootstrap.py').read_text().replace("ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05'","ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05-repair-v2'").replace("'-1080p-v1-20261027'","'-1080p-repair-v2-20261027'");(V/'bootstrap.py').write_text(s)
s=(OLD/'execute.py').read_text().replace("ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05'","ROOT=Path.cwd()/'runs/shizhen-macro-opening-20261027/MC03-05-repair-v2'").replace('shizhen-macro-MC03-05-1080p-qualification-004','shizhen-macro-MC03-05-firstlast-repair-005').replace("bound['macro_paid_submits_before']==3 and bound['macro_cumulative_ceiling_after_authorized_unit']==4","bound['macro_paid_submits_before']==4 and bound['macro_cumulative_ceiling_after_authorized_unit']==5").replace("('seedance_2.0_vip','multimodal',12,'1080p')","('seedance_2.0_vip','first_last_frame',12,'1080p')").replace('shizhen-MC03-05-user-second-shot','shizhen-MC03-05-user-firstlast-repair').replace("'prior_macro_paid_calls':3","'prior_macro_paid_calls':4").replace("'new_macro_call_number':4,'new_macro_ceiling':4","'new_macro_call_number':5,'new_macro_ceiling':5").replace("'macro_cumulative_calls':4,'this_second_event_unit_calls':1","'macro_cumulative_calls':5,'this_same_shot_repair_calls':1").replace('shizhen-macro-MC03-05-1080p-reservation-004','shizhen-macro-MC03-05-firstlast-reservation-005')
startidx=s.index('  lint={');endidx=s.index("\n  dump('prompt-lint.json'",startidx)
s=s[:startidx]+"  lint={'two_exact_endpoints':[x.asset_id for x in req.image_bindings]==[x['asset_id'] for x in expected],'native_endpoint_roles':tuple(x.role for x in req.image_bindings)==('first_frame','last_frame'),'pure_chinese_body':not re.search(r'[A-Za-z]',prompt),'exact_authored_prompt':prompt.strip()==(V/'native-prompt.zh.txt').read_text().strip(),'no_dialogue_music':'无对白、配乐' in prompt,'inward_push':'向前推' in prompt and '门的自由边与把手朝门内退远' in prompt,'first_frame_ordinary':'首帧的普通楼梯' in prompt,'duration12':p.compilation.request.output_requirement.duration_seconds==12,'1080p':p.compilation.request.output_requirement.resolution_label=='1080p','native_audio':p.compilation.request.output_requirement.native_audio}"+s[endidx:]
(V/'execute.py').write_text(s)
dump('source-preservation-diff.json',dict(failed_raw_sha256=anc[-1]['artifact_sha256'],changed=['generic multimodal6 references -> native first_last_frame2 bound endpoints','same-side door medium framing retains contact and reaction together','repair prose explicitly requires downward foot progression and receding door edge'],preserved=['same12s complete event','same character and outfit','ordinary dent+pipe before missing-pipe reveal','right-hand inward push and outside-threshold stop','original speed and native sound','B6/font/music unchanged'],new_builtin_image_calls=2,new_paid_video_calls=0,new_paid_video_limit=1,original_FAIL_retained=True))
print(json.dumps({'prepared':True,'prompt_chars':len(prompt),'mode':profile.input_mode,'endpoint_roles':['first_frame','last_frame'],'old_paid_calls':4,'new_count_limit':1}))
