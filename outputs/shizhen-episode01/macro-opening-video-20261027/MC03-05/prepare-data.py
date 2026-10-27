"""Prepare approved stair-event authoring inputs; no upload or generation."""
from pathlib import Path
import json, hashlib, re
from PIL import Image
from ai_video.production.video_requirement import GenerationIntent
from ai_video.production.hashing import canonical_sha256

R=Path.cwd();V=Path(__file__).resolve().parent;B=V.parent
old=json.loads((B/'MC01-02-1080p-v3/row.json').read_text());r=json.loads(json.dumps(old))
prompt=(V/'native-prompt.zh.txt').read_text().strip();parts=prompt.splitlines()
assert not re.search(r'[A-Za-z]',re.sub(r'\{\{image:\d+\}\}','',prompt))
manifest=R/'referces/shizhen/macro-opening-20261027/repair-02/current-reference-usage.json';m=json.loads(manifest.read_text());wanted=['L01','L01-X','L02','L02-O','L03','L04'];images=[];roles=[]
def dump(name,obj):
 with (V/name).open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
for i,k in enumerate(wanted):
 x=next(a for a in m['selected'] if a['reference_role']==k);p=R/x['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==x['sha256']
 with Image.open(p) as im:width,height=im.size;im.verify()
 record=dict(schema_version='agent-generated-image-observation/1',sha256=x['sha256'],size_bytes=len(raw),width=width,height=height,generator='builtin image_gen.imagegen',tool_identity_claim='builtin only; exact internal model not exposed',fictional_characters=True,platform_admission='NOT_EVALUATED',semantic_review='Actual image viewed and byte-checked for this approved stair event; static state does not prove motion',source_path=x['path'],reference_role=k)
 name='reference-'+str(i+1)+'-source.json';dump(name,record)
 aid='MC03-05-ref-'+str(i+1);images.append(dict(asset_id=aid,node_id=aid+'-node',resource_id=aid+'-local-generated',path=str(p),usage_license='Original fictional references generated for authorized Shizhen macro opening',generated_source=dict(record_path=str((V/name).relative_to(R)),record_sha256=hashlib.sha256((V/name).read_bytes()).hexdigest(),tool=dict(name='builtin-imagegen',version='tool-interface'))))
 roles.append(dict(reference_role=k,path=x['path'],sha256=x['sha256'],actual_model_index=i,semantic_job=x['shot_purpose'],static_observation='VIEWED',video_acceptance='NOT_EVALUATED'))
g=r['generation']['generation_intent']
op='董文慧在老住宅上平台，经过带斜向凹痕的红灭火器与旁边外露管道，准备沿折返楼梯下行'
cl='她留在低处平台门槛外，右手保持扶门，已看清门内同样凹痕及消失管道留下的旧卡箍印，核对后轻微侧头听辨，尚无答案'
g['open_state'].update(state_text=op);g['close_state'].update(state_text=cl)
g['identity_continuity'].update(character_ids=['dong-wenhui'])
g['scene_continuity'].update(scene_id='residential-switchback',time_of_day='雨夜',mood='普通住宅路径中出现熟悉细节与缺失差异',state_constraints=['同一董文慧、灰褐外套、深灰裤、低马尾','上平台管道存在，低处门内管道缺失而凹痕相同','右手推门始终留在门槛外，不加解释或新机制'])
g['space_continuity'].update(subject_position='上平台经过灭火器，沿折返梯段向下到较低平台门外',screen_direction='沿已建立的梯段实际下行，门向远离她的方向内开',crossing_policy='身体不跨门槛，不穿门或栏杆')
g['axis_continuity'].update(camera_axis='下行斜侧观察，开门从身后偏左同侧观察',framing_continuity='闭门、半开、开门和反应连续，右手随把手运动，门框锚点可见',crossing_policy='开门与反应保持门槛外同侧，不越轴')
g['subject_action'].update(start_state=op,progression='\n'.join(parts[1:4]));g['subject_action']['endpoint'].update(state_text=cl)
g['motion_envelope'].update(onset='经过上平台凹痕与管道，正常下楼',peak='到低处平台右手压把手向前推门，逐渐显露凹痕和旧管箍印',settle='保持扶门并停步，核对后听辨',direction='连续下行，随后门向内开',amplitude_class='自然步幅和有限开门、轻微侧头')
g['pacing'].update(cadence='普通下行、到达推门、先看清差异、停步核对听辨',tempo_class='正常原速，保留完整下行与开门反应，不按固定秒数切镜',shot_duration_seconds=12)
g['camera_intent'].update(movement='斜侧中全景短随下行；到达后身后偏左中景随门显露，停步后直接切同侧中近景',stability='稳定短跟随与固定反应',framing_intent='下行保持梯段纵深，开门同框右手门扇与门内线索，反应保留门框')
g['camera_endpoint'].update(start_framing='上平台斜侧中全景，同时可辨董文慧、灭火器及管道',end_framing='门槛外同侧中近景，右手扶门，门框和门内线索同框')
g['performance_intent'].update(trigger='门开后看到相同凹痕但旁边管道缺失',visible_response='先停步、核对两处细节，再轻微侧头听辨',gaze_target='灭火器凹痕和旧卡箍印',body_behavior='先普通下行，到门外停步，不跨门槛',hand_behavior='右手压把手向内推门并保持接触，左手自然垂下',terminal_performance_state='克制疑惑，听辨而未得到答案')
g['performance_intent']['character_directions']=[dict(character_id='dong-wenhui',screen_identity='灰褐外套低马尾的董文慧',role='principal',visibility='visible',beats=[dict(phase='throughout',trigger='普通下楼之后，门内出现熟悉凹痕与缺失管道的差异',emotion='先平常通行，再克制核对',intensity='subtle',facial_expression='平静中轻微疑惑，不提前惊恐',gaze_target='先看路，再核对凹痕与管道旧印',breathing='自然平稳',body_behavior='右手扶门，脚步停在门槛外，随后轻微侧头听辨')])]
g['visual_treatment'].update(medium_look='正常速度真人实拍质感',palette='住宅旧墙灰绿与实用暖灯、窗外冷光',material_treatment='旧楼墙漆、湿台阶、真实衣料、红灭火器和金属门',prohibited_visual_drift=['叠化、透明重影、分格或瞬移','新增人物、光效、片名或字幕'])
g['lighting_intent'].update(motivated_source='楼梯实用灯和雨夜窗外冷光',direction='延续已核对六张场景参考的实用光',exposure_priority='凹痕、管道存在与缺失、右手门把接触和台阶可辨',continuity_state='同一住宅雨夜，无闪光或突然换时段')
g['ambience_intent'].update(environment_bed='平台滴水、住宅生活底噪，门后环境声与门外不同',foley_cues=['正常脚步','衣料摩擦','随开门的门轴声'],explicitly_silent=False)
g['primary_camera_motion'].update(movement_kind='pedestal_down',direction='down',amplitude_class='subtle',speed_class='slow',start_motion_state='in_motion',end_motion_state='settled')
g['camera_subject_relation'].update(subject_id='dong-wenhui',relation_kind='follow',start_relation='人物、灭火器管道与折返梯段可读',end_relation='人物扶门反应与门内差异同框')
g=GenerationIntent.model_validate(g).model_dump(mode='json');r['generation']['generation_intent']=g
r['shot'].update(shot_id='MC03-05',scene_id='residential-switchback',storyboard_beat_id='stairs-familiar-mark',intent=prompt,duration_policy=dict(mode='fixed',seconds=12),character_ids=['dong-wenhui'],continuity_constraints=['遵原MC03–MC05完整事件，不改剧情或角色','同一凹痕、上平台有管道、门内无管道但有旧印','下行真实连续、右手随把手、门槛外停步与同次反应','市政转楼梯明确换场，机器声不迁入住宅','不改B6、字体、音乐或后续事件'],generated_video_rationale='原分镜楼梯MC03–MC05合为完整12秒事件；同一角色下行、推门与核对，不按单镜机械拆段')
r['generation']['references']=[dict(role='character_reference' if i==0 else 'scene_reference',asset_id=x['asset_id'],**({'owner_id':'dong-wenhui'} if i==0 else {})) for i,x in enumerate(images)]
r['generation']['output_need']['duration_seconds']=12
dump('row.json',r)
def leaves(x,path):
 if isinstance(x,dict):
  for k,v in x.items():yield from leaves(v,path+'.'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from leaves(v,path+'.'+str(i))
 elif x is not None:yield path
groups={'identity':['identity_continuity'],'action':['open_state','close_state','subject_action','motion_envelope','pacing'],'camera':['axis_continuity','camera_intent','camera_endpoint','primary_camera_motion','camera_subject_relation'],'performance':['performance_intent'],'space':['space_continuity'],'art':['scene_continuity','visual_treatment','lighting_intent'],'sound':['ambience_intent','dialogue_intent','music_intent']}
paths={k:[p for root in roots for p in leaves(g[root],'generation_intent.'+root)] for k,roots in groups.items()}
fragments={k:[parts[i] for i in indexes] for k,indexes in {'identity':[0],'action':[1,2,3],'camera':[1,2,3],'performance':[1,2,3],'space':[1,2,3],'art':[0,1,4],'sound':[4]}.items()}
observations=dict(identity='同一董文慧脸、低马尾、灰褐外套和深灰裤，无身份变化或多人复制',action='经过带凹痕灭火器和管道，真实下行至低平台；右手连续推门显露相同凹痕与缺失管道的旧印，随后停步核对',camera='梯段空间可读，身后偏左中景呈现开门，停步后直接切同侧反应，无叠化或错误重复动作',performance='开始普通走路，不提前惊恐；见差异后停步核对再听辨，保持门槛外右手扶门',space='上平台凹痕灭火器旁有管道，门内相同凹痕旁无管道有旧印；下行路径和左铰链内开门符合实际参考，手门身体不穿透',art='同一写实旧住宅、灰绿旧墙实用灯，无光效、字幕或片名',sound='原生脚步、衣料、门轴随动作，平台与门后声场可区分，无对白、配乐、耳语或惊吓重击，不继承市政机器声')
dump('data.json',dict(objective='依据原分镜MC03–MC05制作董文慧下行、推门发现重复凹痕与缺失管道、停步核对的完整事件；不新增机制、不改B6字体音乐',images=images,characters=[dict(character_id='dong-wenhui',name='董文慧',identity='28岁，夜间应急服务文字记录者；原分镜中经过住宅楼梯、察觉细节差异而核对听辨，不解释规则',appearance_bible='沿既有董文慧identity-v1面貌、低马尾；本宏观场景灰褐外套、深灰打底裤与黑鞋，不移植第二集场次的包本',reference_asset_ids=[images[0]['asset_id'],images[5]['asset_id']])],scene_images=[x['asset_id'] for x in images],observations=observations,paths=paths,fragments=fragments,intent_sha256=canonical_sha256(g)))
identity=R/m['reused_identity'];dump('reference-input-plan.json',dict(source_manifest=str(manifest.relative_to(R)),source_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),identity_parent=dict(path=m['reused_identity'],sha256=hashlib.sha256(identity.read_bytes()).hexdigest(),role='Review-only original identity board; inherited by six exact clean scene references, not sent as a multi-person board'),actual_video_images=roles,selected_model='seedance_2.0_vip',selected_mode='multimodal',duration_seconds=12,resolution='1080p',max_images=9,new_image_generation_calls=0,prior_static_failures_preserved=True,predecessor=dict(path='MC01-02-edit-v4/失帧-市政异常-1080p-剪辑修订04.mp4',sha256='b3d5a404eaf19453081309754ad11b997725d81130973a991530a78ff663f05d',relationship='explicit scene change, do not inherit municipal cable or sound',required_media_gate='NOT_EVALUATED_PENDING_EVIDENCE'),generation_POSTs=0))
dump('authoring-lint.json',dict(pure_chinese_prompt=True,six_exact_markers=all('{{image:'+str(i)+'}}' in prompt for i in range(6)),all_reference_bytes_verified=True,all_images_viewed=True,prompt_characters=len(prompt),duration_seconds=12,model_rule='at most15 seconds Seedance2.0',resolution_rule='Seedance2.0 defaults1080p',scene_change_not_continuous_action=True,predecessor_gate='NOT_EVALUATED',submit_ready=False,new_paid_calls=0))
print(json.dumps({'prepared':True,'prompt_chars':len(prompt),'exact_images':len(images),'duration':12,'generation_POSTs':0,'submit_ready':False}))
