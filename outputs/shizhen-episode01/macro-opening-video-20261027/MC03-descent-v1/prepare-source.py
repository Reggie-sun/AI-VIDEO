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
parts=[
'素材一{{image:0}}固定同一董文慧、灰褐外套和下楼起态；素材二{{image:1}}说明沿同一梯段继续下降；素材三{{image:2}}说明到达低处关闭灰门前、双手空着的终态。三张图按这个动作顺序参考，不是照片轮播。',
'从素材一的背向姿态开始，先让观众看清上平台红灭火器的斜凹痕和旁边外露管道。她背对摄影机，沿画面由近处台阶走向远处灰门，每步从较高踏步落到前方较低踏步，连续走完可见梯段。人物因走远自然变小，不转身朝摄影机上楼，不返回上平台、不跳步或瞬移。到达低平台后双脚落在关门前平地，双手仍空着自然下垂；门始终关闭。',
'固定参考中的俯视机位，看清梯段、栏杆和下方平台，完整拍下这一段下行，不切镜或叠化。她只是普通通行，神态平静，视线看前方落脚处，不提前恐惧或回头听辨。真人电影质感，灰绿旧墙、湿台阶、暖顶灯和冷窗光保持；不出现门后异常、额外人物、片名、字幕或光效。',
'正常原速，脚步踏实且随走远变轻，保留自然衣料声、住宅微弱滴水与底噪；无对白、配乐、耳语或惊吓重击，不加入机器声。']
prompt='\n'.join(parts);assert not re.search('[A-Za-z]',re.sub(r'\{\{image:\d+\}\}','',prompt));(V/'native-prompt.zh.txt').write_text(prompt+'\n')
row=json.loads((OLD/'row.json').read_text());data=json.loads((OLD/'data.json').read_text());g=row['generation']['generation_intent']
start='董文慧背向摄影机处于通往远处关闭灰门的下行梯段，上平台红灭火器与管道可见';end='她走完可见梯段，到达较低平台关闭灰门前，双脚在平地、双手空着，尚未接触把手'
g['open_state']['state_text']=start;g['close_state']['state_text']=end;g['subject_action'].update(start_state=start,progression=parts[1]);g['subject_action']['endpoint']['state_text']=end
g['scene_continuity'].update(mood='普通住宅正常下行，尚未显露异常',state_constraints=['同一董文慧、低马尾、灰褐外套、深灰裤','上平台凹痕灭火器旁管道始终存在，下方灰门始终关闭','逐级下行到低平台，双手空着，不开门或提前反应'])
g['space_continuity'].update(subject_position='由近处较高踏步走到远处灰门所在低平台',screen_direction='背向摄影机远离，沿梯段由高到低',crossing_policy='不穿栏杆、台阶、门或地面，不进门')
g['axis_continuity'].update(camera_axis='固定高处向下看同一楼梯',framing_continuity='同机位保持上平台线索、梯段与低平台关系',crossing_policy='不换轴、不转身上楼、不镜像')
g['motion_envelope'].update(onset='看清普通平台线索后背向走低',peak='沿可见梯段逐级下降',settle='双脚到低平台平地，双手空着',direction='从较高台阶到远处更低平台',amplitude_class='正常步幅，人物随走远变小')
g['pacing'].update(cadence='普通下楼到达后自然站定',tempo_class='正常原速，完整走完梯段，不强塞开门',shot_duration_seconds=8)
g['camera_intent'].update(movement='固定高处俯视，不切镜',stability='稳定固定机位',framing_intent='完整梯段、上下平台、落脚及正常凹痕管道同框')
g['camera_endpoint'].update(start_framing='参考起态的固定楼梯全景',end_framing='同机位中人物走远到低处关闭灰门前',position_lock=True,orientation_lock=True)
g['primary_camera_motion'].update(movement_kind='locked',direction='none',amplitude_class='subtle',speed_class='very_slow',start_motion_state='stationary',end_motion_state='settled')
g['camera_subject_relation'].update(relation_kind='fixed_frame',start_relation='高处观察背向下行人物、正常线索与远处门',end_relation='相同机位观察人物已到低平台，因走远自然变小')
p=g['performance_intent'];p.update(trigger='正常通行下楼，尚未遇到异常',visible_response='平常看路、逐级下行，到门前自然站住',gaze_target='前方较低落脚处和关闭灰门',body_behavior='连续下行交替承重，到平地站定，不转身向上',hand_behavior='双手自然摆动后下垂，均空着，不摸把手',terminal_performance_state='站在关门前、双手空着，未察觉异常')
p['character_directions'][0]['beats'][0].update(trigger=p['trigger'],emotion='平常通行',facial_expression='自然平静，不提前恐惧',gaze_target=p['gaze_target'],body_behavior=p['body_behavior'])
g['lighting_intent'].update(direction='延续三张同机位楼梯图实用光',exposure_priority='踏步支撑、栏杆、正常凹痕管道和关门可辨')
g['ambience_intent'].update(environment_bed='住宅微弱滴水和底噪，随走远变化的自然脚步',foley_cues=['踏实的正常脚步','自然衣料摩擦','住宅微弱滴水'])
g=GenerationIntent.model_validate(g).model_dump(mode='json');row['generation']['generation_intent']=g
images=[];manifest=json.loads((V.parent/'reference-sequences-v4/reference-input-plan.json').read_text())
for i,a in enumerate(manifest['images'][:3]):
 path=R/a['path'];assert sha(path)==a['sha256'];name=f'reference-{i+1}-source.json';dump(name,{'schema_version':'agent-generated-image-observation/1','sha256':a['sha256'],'size_bytes':path.stat().st_size,'width':a['width'],'height':a['height'],'generator':'builtin image_gen.imagegen','tool_identity_claim':'builtin only; exact internal model not exposed','fictional_characters':True,'platform_admission':'NOT_EVALUATED','semantic_review':'Parent and independent static review; motion NOT_EVALUATED','source_path':a['path'],'reference_role':['identity_start','descent_progress','lower_landing_arrival'][i]})
 aid=LABEL+f'-ref-{i+1}';images.append(dict(asset_id=aid,node_id=aid+'-node',resource_id=aid+'-local-generated',path=str(path),usage_license='Task-owned same-identity action reference for authorized Shizhen qualification',generated_source=dict(record_path=str((V/name).relative_to(R)),record_sha256=sha(V/name),tool=dict(name='builtin-imagegen',version='tool-interface'))))
row['shot'].update(shot_id=LABEL,storyboard_beat_id='stairs-descent-arrival',intent=prompt,duration_policy={'mode':'fixed','seconds':8},continuity_constraints=['原MC03–MC05仍需推门显露和反应，本段不冒充完整事件','同一人物、服装、楼梯和正常灭火器管道','背向下楼到低平台，不反向返回、提前开门或恐惧','到达手空，下一机位从同一关门手空状态接续','不改B6、字体、音乐或后续剧情'],generated_video_rationale='用户批准重整参考后先验证完整可见梯段下楼到达；固定机位服务地理和落脚可读性，开门属于后续源和全事件验收')
row['generation']['references']=[dict(role='character_reference' if i==0 else 'scene_reference',asset_id=x['asset_id'],**({'owner_id':'dong-wenhui'} if i==0 else {})) for i,x in enumerate(images)];row['generation']['output_need']['duration_seconds']=8
row['generation'].pop('conditioning_compatibility',None)
data.update(objective='为原楼梯事件取得合格下楼到达源：看清正常灭火器管道，董文慧连续下楼到关闭灰门前、双手空着。推门显露与反应归后续B源和完整拼接验收，本段不代表完整事件通过。',images=images,scene_images=[x['asset_id'] for x in images],intent_sha256=canonical_sha256(g));data['characters'][0]['reference_asset_ids']=[images[0]['asset_id']]
data['observations']={'identity':'同一董文慧、低马尾、灰褐外套、深灰裤，没有新增或复制人物','action':'背向起态逐级连续下楼到低平台关门前，没有回身上楼、跳步或瞬移','camera':'固定高处看完整梯段，人物走远变小，无切镜叠化','performance':'普通走路、踏实承重，到达双手空着，不提前恐惧或听辨','space':'正常凹痕灭火器与管道存在，下方灰门保持关闭；平台可定位，最终双脚落在低平台平地','art':'写实旧楼、灰绿墙、湿台阶、暖顶灯冷窗光，无额外文字奇观','sound':'可闻自然脚步衣料住宅底噪，随走远变化，无对白音乐门声或机器声'}
data['fragments']={k:[parts[j] for j in ids] for k,ids in dict(identity=[0],action=[0,1,3],camera=[0,2],performance=[1,2,3],space=[0,1,2],art=[0,2],sound=[3]).items()};dump('row.json',row);dump('data.json',data)
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
