"""Task-local offline authoring. No transport, browser or paid calls."""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import GenerationIntent
from ai_video.production.preview_approval import validate_preview_approval
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
REPO=Path.cwd()
def write(name,x): (HERE/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def leaves(x,p):
 if isinstance(x,dict):
  for k,v in x.items(): yield from leaves(v,p+'.'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x): yield from leaves(v,p+'.'+str(i))
 elif x is not None: yield p
coverage=json.loads((BASE/'director-coverage.v4.json').read_text()); ch=canonical_sha256(coverage)
board=BASE/'refs/storyboard-v2.png'; aid='municipal-board-v2'; cid='municipal-worker'; sid='municipal-rain-gate'
approval={'kind':'user-preview-approval/1','coverage_hash':ch,'unit_ids':['municipal'],'preview_artifacts':[{'path':str(board.relative_to(REPO)),'sha256':sha(board),'role':'reference_image'}],'user_quote':'那你再用这个做出来视频我看看'}
validate_preview_approval(approval); write('preview-approval.json',approval)
opening='低机位近处钢缆收紧，左侧电闸与戴黄色安全帽的工人可见，绞盘连接右侧铁门。'
closing='电闸已断开，工人回看；绞盘仍转、钢缆仍收紧，连接的铁门抵住限位。'
identity='只借参考图第一、二格同一工人的黄色安全帽、深蓝工作服反光条和浅色手套，保留该工人身份。'
action='工人伸手将电闸明确拉到断开位置并松手；镜头仍能确认断开状态，绞盘继续收缆，钢缆始终连接铁门，门被拉到限位后停止但钢缆仍绷紧。工人回头看绞盘，保持克制，不惊叫、不开口。'
camera='一个连续六秒镜头，低机位从电闸和近处收紧钢缆小幅向右摇，连接工人操作与仍运转绞盘，最后稳定在绞盘、钢缆、铁门受力关系；不切镜、不越轴、不变焦。'
sound='原生同期雨声、绞盘电机声与钢缆受力声，断电后机械声继续，无对白、无配乐、无字幕。'
art='雨夜真实摄影，冷灰雨幕与现场实用灯，潮湿金属和真实衣物；无慢动作、闪屏、黑屏、鬼影、格线、编号或文字。'
events=[{'event_id':'start-composition','kind':'composition','visual_state':opening,'purpose':'看清工人、电闸和钢缆起始关系','phase':'start','control':'model_guidance','priority':'required'}, {'event_id':'end-composition','kind':'composition','visual_state':closing,'purpose':'看清断电后仍运作的受力证据','phase':'end','control':'model_guidance','priority':'required'}]
prompt='\n'.join(['{{image:0}}仅为软参考，不是首帧。只使用第一、二格工人、电闸、绞盘、钢缆和铁门，不复制其他格人物、地点、格线、编号或分格排版。',identity,opening,action,camera,closing,*[e['purpose'] for e in events],sound,art])
gi={'open_state':{'kind':'typed_text','state_text':opening},'close_state':{'kind':'typed_text','state_text':closing,'required_change':True},'identity_continuity':{'character_ids':[cid],'preservation':'exact'},'scene_continuity':{'scene_id':sid,'time_of_day':'雨夜','mood':'市政设备断电后仍运行','state_constraints':['钢缆连接绞盘与铁门','电闸断开后绞盘仍转']},'space_continuity':{'subject_position':'电闸在左，绞盘居中，钢缆连接右侧铁门','screen_direction':'向右揭示机械关系','crossing_policy':'不越轴'},'axis_continuity':{'camera_axis':'设备正面同一侧','framing_continuity':'工人与电闸到绞盘钢缆铁门','crossing_policy':'不越轴'},'subject_action':{'start_state':opening,'progression':action,'endpoint':{'state_text':closing,'required_change':True}},'motion_envelope':{'onset':'伸手断电','peak':'断电后绞盘仍转','settle':'工人回看绷紧钢缆','direction':'手向下断电、头向右回看','amplitude_class':'正常实时动作'},'pacing':{'cadence':'操作、揭示、停留确认','tempo_class':'正常原速','shot_duration_seconds':6},'camera_intent':{'movement':'小幅向右摇','stability':'稳定','framing_intent':camera},'camera_endpoint':{'start_framing':opening,'end_framing':closing,'position_lock':True,'orientation_lock':False},'primary_camera_motion':{'movement_kind':'pan_right','direction':'right','amplitude_class':'subtle','speed_class':'slow','start_motion_state':'stationary','end_motion_state':'settled'},'camera_subject_relation':{'subject_id':cid,'relation_kind':'reveal','start_relation':'工人和断电开关','end_relation':'工人回看仍运作机械'},'performance_intent':{'trigger':'断电后机械仍转','visible_response':'回看绞盘','gaze_target':'绞盘','body_behavior':'站稳后回头','hand_behavior':'拉下电闸后松手','terminal_performance_state':'站定看绞盘','character_directions':[{'character_id':cid,'screen_identity':identity,'role':'principal','visibility':'visible','beats':[{'phase':'throughout','trigger':'断电后机械仍转','emotion':'克制困惑','intensity':'subtle','facial_expression':'轻微皱眉','gaze_target':'绞盘','breathing':'正常','body_behavior':'操作后回看'}]}]},'visual_treatment':{'medium_look':'正常速度真人摄影','palette':'冷灰与实用灯','material_treatment':'潮湿金属和真实衣物','prohibited_visual_drift':['慢动作、闪屏、鬼影','字幕、格线、编号']},'lighting_intent':{'motivated_source':'现场实用灯','direction':'侧上方','exposure_priority':'电闸断开与钢缆关系可读','continuity_state':'现场灯不闪烁'},'ambience_intent':{'environment_bed':'持续雨声','foley_cues':['绞盘电机声','钢缆受力声'],'explicitly_silent':False},'dialogue_intent':{'mode':'none','lip_sync_required':False},'music_intent':{'mode':'none'},'reference_planning':{'facets':['slow_camera','identity_consistency','continuous_physics'],'structure':'continuous','events':events,'anchors':[{'anchor_id':'worker-identity','role':'identity','owner_id':cid,'purpose':identity}], 'selections':[{'need_id':x,'asset_id':aid} for x in ['worker-identity','start-composition','end-composition']], 'director_coverage':{'coverage_hash':ch,'unit_id':'municipal'},'preview_approval':{'approval_hash':canonical_sha256(approval)}}}
gi=GenerationIntent.model_validate(gi).model_dump(mode='json')
row={'shot':{'shot_id':'municipal','scene_id':sid,'storyboard_beat_id':'municipal','intent':prompt,'dialogue':'','duration_policy':{'mode':'fixed','seconds':6},'character_ids':[cid],'continuity_constraints':[identity,action,camera,sound],'visual_strategy':'generated_video','required_asset_roles':[{'role':'primary_visual','asset_ids':[],'allowed_asset_types':['video']}],'generated_video_rationale':'新制作市政断电后设备仍运作的连续证据'},'generation':{'references':[{'role':'character_reference','asset_id':aid,'owner_id':cid}],'intent_evidence':{'character_action_required':True,'state_change_required':True,'subject_motion_directive_present':True},'generation_intent':gi,'output_need':{'timing_mode':'content_driven','duration_seconds':6,'geometry_policy':'adaptive','aspect_ratio':'16:9','fps':None,'container_mime':'video/mp4'},'audio_need':'required','quality_need':{'objective_tier':'preview'}},'composition':{'muted':False,'source_audio_policy':'KEEP'}}
record={'kind':'task-generated-reference-observation/1','path':str(board.relative_to(REPO)),'sha256':sha(board),'generator':'image_gen.imagegen','generation_intent':str((BASE/'refs/generation-intent.json').relative_to(REPO)),'repair_intent':str((BASE/'refs/storyboard-repair-intent.json').relative_to(REPO)),'role':'soft reference; identity and visual relations in cells 01/02 only','user_preview':'approved whole storyboard; no clean frame shown','video_acceptance':'NOT_EVALUATED'}
from PIL import Image
with Image.open(board) as im: record.update(width=im.width,height=im.height,size_bytes=board.stat().st_size)
write('reference-source.json',record)
images=[{'asset_id':aid,'node_id':aid+'-node','resource_id':aid+'-local','path':str(board),'usage_license':'Task-owned fictional storyboard generated for Shizhen remake','generated_source':{'record_path':str((HERE/'reference-source.json').relative_to(REPO)),'record_sha256':sha(HERE/'reference-source.json'),'tool':{'name':'image_gen.imagegen','version':'runtime-tool-version-not-exposed'}}}]
categories={'identity':['identity_continuity'],'action':['open_state','close_state','scene_continuity','subject_action','motion_envelope','pacing'],'camera':['axis_continuity','camera_endpoint','camera_intent','camera_subject_relation','primary_camera_motion'],'performance':['performance_intent'],'space':['space_continuity'],'sound':['ambience_intent','dialogue_intent','music_intent'],'art':['visual_treatment','lighting_intent']}
obs={'identity':identity,'action':action,'camera':camera,'performance':'工人只操作和回看，不开口、不惊恐表演','space':'绞盘、连续钢缆和铁门相连，受力方向不变','sound':sound,'art':art}
data={'objective':'失帧全新开头：市政断电后绞盘仍转，钢缆拉住铁门','images':images,'characters':[{'character_id':cid,'name':'市政工人','identity':identity,'appearance_bible':'黄色安全帽、深蓝反光工作服、浅色手套','reference_asset_ids':[aid]}],'scene':{'scene_id':sid,'location':'雨夜市政铁门旁','mood':'机械反常运行'},'scene_images':[],'observations':obs,'paths':{k:[p for f in fs for p in leaves(gi[f],'generation_intent.'+f)] for k,fs in categories.items()},'fragments':{k:[prompt] for k in categories},'intent_sha256':canonical_sha256(gi),'coverage':{'coverage_hash':ch,'unit_id':'municipal'}}
write('row.json',row);write('data.json',data);(HERE/'native-prompt.zh.txt').write_text(prompt+'\n')
now=datetime.now(timezone.utc)
write('operator-bound.json',{'authority':'current-task-parent-bounded-operator','authorization_quote':approval['user_quote'],'scope':'municipal only, qualification, no activation','issued_at':now.isoformat(),'expires_at':(now+timedelta(hours=3)).isoformat(),'max_submit_count':1,'automatic_retries':0,'per_call_credit_upper_bound':1500,'quote_credits':198,'quote_evidence':str((BASE/'native/municipal-readonly.json').relative_to(REPO)),'note':'1500 internal operator ceiling, not market quote'})
print('Authored municipal contracts; no external calls')
