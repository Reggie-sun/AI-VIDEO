"""Director data only; no node mutation, generation, activation or QA claim."""
from pathlib import Path
import copy,json
from ai_video.production.video_requirement import GenerationIntent
V=Path(__file__).resolve().parent;base=json.loads((V/'CO-A1-row.json').read_text())
def save(label,row):
 GenerationIntent.model_validate(row['generation']['generation_intent'])
 with (V/(label+'-row.json')).open('x') as f:json.dump(row,f,ensure_ascii=False,indent=2)
r=copy.deepcopy(base);s=r['shot'];s.update(shot_id='CO-A2',storyboard_beat_id='after',duration_policy={'mode':'fixed','seconds':4},character_ids=['luomin'],dialogue='',continuity_constraints=['同一站棚同一机位，右侧罗敏左手持手机','货车向右驶离，左侧原高峥及其包已不在；不展示离开或上车'],generated_video_rationale='Physical foreground truck reveal of the after-state for a concealed editorial cut')
opening='灰白配送货车的雨湿金属车厢在极近前景完整遮满画面，车仍向右经过。'
close='货车已经从右边驶出画面，恢复同一站棚固定中远景。右侧罗敏左手手机贴左耳，墨绿雨衣和黑包保持；左侧高峥与其包的位置为空，站棚出口和脚边完整可见。'
progress='灰白货车从镜头近前景继续向右驶过，侧板横向运动，尾缘从左向右扫过并离开画面，逐渐揭开后方同一站棚和右侧独自候车的罗敏。她自然听电话，不看空位、不寻找、不惊恐。车辆不停、不进站、不开门，人物不下车或出入画面。车驶离后让空位和正常反应同时可读。'
s['intent']=progress;s['required_asset_roles']=[{'role':'primary_visual','asset_ids':[],'allowed_asset_types':['video']},*({'role':role,'asset_ids':[aid],'allowed_asset_types':['image']} for role,aid in [('first_frame','co-truck-image'),('last_frame','co-after-image')])]
g=r['generation'];g['references']=[{'role':'approved_keyframe','asset_id':'co-truck-image'},{'role':'last_frame','asset_id':'co-after-image'}];g['conditioning_compatibility'].update(first_anchor_id='co-truck-image',last_anchor_id='co-after-image',available_duration_seconds=4)
i=g['generation_intent'];i['open_state']={'kind':'typed_text','state_text':opening};i['close_state']={'kind':'typed_text','state_text':close,'required_change':True};i['subject_action']={'start_state':opening,'progression':progress,'endpoint':{'state_text':close,'required_change':True}};i['identity_continuity']={'character_ids':['luomin'],'preservation':'exact'}
i['scene_continuity']['state_constraints']=['同一机位，罗敏在右，左侧为空','左手手机贴左耳，衣服与黑包保持','车厢只朝右驶离，不停站、不开门；无上下车或人走开','不加入原不存在的人，不用透明、烟雾、闪光或渐隐','无对白、音乐、鬼声、字幕、片名或精确数字']
i['space_continuity'].update(subject_position='罗敏同首图右侧，左侧为空',screen_direction='同机位不镜像，货车持续左向右',crossing_policy='不越轴，不展示任何人出入')
i['axis_continuity'].update(framing_continuity='近车厢遮挡自然揭开同一固定站棚中远景')
i['motion_envelope'].update(onset='车厢正持续向右经过',peak='尾缘从左向右扫过，揭开站棚',settle='货车驶离，正常候车与空位可读',direction='货车持续向右',amplitude_class='正常实时动作')
i['pacing'].update(cadence='货车自然驶过，不放慢，不停成灰色静帧；揭开后留一口正常呼吸',shot_duration_seconds=4)
i['camera_intent']['framing_intent']='全程同一固定机位。车厢自然驶离后，同时看见左侧空位、站棚出口和右侧罗敏；无推拉、切镜、溶解或黑屏'
i['camera_endpoint'].update(start_framing=opening,end_framing=close)
i['camera_subject_relation'].update(start_relation='同机位被车厢完整遮住',end_relation='恢复站棚，罗敏在右，左侧为空')
p=i['performance_intent'];p.update(trigger='电话仍在继续，货车在前景经过',visible_response='罗敏被揭出时自然听电话，不向左寻找或惊恐',gaze_target='听电话，视线自然向前方路面',body_behavior='正常站立和呼吸',hand_behavior='左手手机贴左耳，黑包不交换',terminal_performance_state=close,character_directions=[p['character_directions'][1]])
b=p['character_directions'][0]['beats'][0];b.update(trigger='普通等待接车电话',facial_expression='自然闭口倾听，无惊恐',gaze_target='前方道路，不看左侧空位',body_behavior='站在原位自然听电话，左手不换手')
i['dialogue_intent']={'mode':'none','lip_sync_required':False};i['ambience_intent']={'environment_bed':'货车正常向右驶离，近雨棚雨声与远车流持续，无对白、音乐、异常冲击或全局静音','foley_cues':['货车轮胎湿路声自然远离，衣料轻响']}
r['occurrence_id']='co-after';r['adaptation_reason']='Approved after-state component; submit only after CO-A1 exact raw gate passes. Common full occlusion conceals the cut; actual physical reveal must be verified.';save('CO-A2',r)
print(json.dumps({'prepared':'CO-A2','duration':4,'paid_calls':0}))
