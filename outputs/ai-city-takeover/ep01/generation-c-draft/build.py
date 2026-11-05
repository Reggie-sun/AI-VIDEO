"""Prepare C source typed authoring inputs only; never opens a committer or Provider."""
from pathlib import Path
import hashlib
import json
import re
from PIL import Image
from ai_video.production.models import Scene,Shot,Character,AssetRecord,AssetRegistrySnapshot
from ai_video.production.hashing import canonical_sha256,seal_artifact,verify_artifact_hash
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.video_requirement import GenerationIntent
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.models import QaPolicy
from ai_video.production.authoring_input import authoring_input_reference,authoring_input_payload
from ai_video.production.reference_authoring import director_coverage_authoring_input
from ai_video.production.preview_approval import preview_approval_authoring_input
P=Path(__file__).resolve().parent
EP=P.parent
REPO=P.parents[3]
PROMPT='''真人电影摄影，横幅十六比九，连续六秒。以第一张已认可室内图作为场景、光线、构图与起始人物姿态的主要参考；第二张已认可正面头胸身份图控制同一女性的完整面貌、身份、左耳装置和左领极细红线，不继承身份图背景。
同一位浅肤色、极淡雀斑、浅灰蓝眼、深棕后梳低髻的年轻女性，穿炭黑高领长大衣，在原窗边设备前保持原站位。观察者看到的始终是显示器背面，保持背壳、支架和原人物相对位置；不转屏幕、不展示屏幕正面、不向背面贴图，不生成任何屏幕内容。蓝黑与钢蓝冷色，红色仅为原左领极细灯线，保持自然皮肤与衣料。
她保持原图身体朝向与设备视线，嘴唇自然静置、平静观察；允许自然呼吸、轻微自然眨眼与极轻视线反应；不说话、不唱歌、不出现说话或演唱的连续口型、不抬手、不敲键盘、不操作设备、不转身，不把她演成黑客。摄影机沿原视轴极缓慢微幅推近，保持原观察侧与人物、显示器背面的相对位置，不翻轴、不环绕、不突然变焦。末段平滑收稳，人物仍嘴唇自然静置，服装、耳挂和灯线位置不变。全镜连续原速，不切镜、不叠化、不冻结。
保持原室内与窗外冷光，保留平台正常人工智能生成标识，不删除、不遮挡它；不新增剧情字幕、片名、新闻图形、人物、屏幕或界面。新闻解释图形由独立剪辑承接，不出现在这个人物镜头中。只允许极轻房间环境声，不生成对白、旁白、演唱或音乐；成片使用独立音轨，本源片原生声音在剪辑中静音。'''

def write(name,obj):
    (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def source(name,cls):
    model=cls.model_validate_json((EP/'production-input'/name).read_bytes())
    assert verify_artifact_hash(model)
    return model

def core(model):
    return model.model_dump(mode='json',exclude={'artifact_id','schema_version','revision','content_hash','creation_receipt_id','source_provenance'})

def leaves(node,prefix):
    if isinstance(node,dict):
        for key,value in node.items():yield from leaves(value,prefix+'.'+key)
    elif isinstance(node,(tuple,list)):
        for index,value in enumerate(node):yield from leaves(value,prefix+'.'+str(index))
    elif node is not None:yield prefix

def main():
    approval=json.loads((EP/'reference-package/reference-review.json').read_text())
    approved={x['path']:x['sha256'] for x in approval['images']}
    approved.update({x['path']:x['sha256'] for x in approval['images'][2]['actual_image_inputs']})
    files=[('iris-c-interior',EP/'reference-package/A03-v1.png','approved interior composition; visible monitor back'),('iris-cf-details',EP.parent/'series/identity-cf/raw/CF-ID7b-a.png','approved full front-ish IRIS identity, face, left-ear and collar'),('iris-cf-face',EP.parent/'series/casting/raw/CF-a.png','canonical provenance only; side/back CF-a NOT selected for provider')]
    selections=[];records=[];provenance=[]
    for aid,path,role in files:
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest();rel=path.relative_to(REPO).as_posix()
        assert sha==approved[rel]
        with Image.open(path) as im:w,h=im.size;assert im.format=='PNG'
        item={'asset_id':aid,'path':rel,'sha256':sha,'size_bytes':len(raw),'width':w,'height':h,'role':role,'selected_for_provider':aid!='iris-cf-face'}
        selections.append(item)
        origin={'kind':'iris-c-source-selection/1',**item};ref=authoring_input_reference(origin)
        provenance.append(ref)
        output=P/ref.reference;output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(authoring_input_payload(origin))
        records.append(AssetRecord(asset_id=aid,asset_type='image',artifact_path=canonical_image_asset_path(sha),sha256=sha,size_bytes=len(raw),mime_type='image/png',width=w,height=h,source_kind='imported',tool={'name':'approved-local-source-import','version':'1'},input_fingerprint=canonical_sha256(origin),creation_receipt_id='iris-c-local-import:'+sha,usage_license='User-authorized project reference; no platform ownership claim.'))
    registry=AssetRegistrySnapshot(revision_id='0'*64,content_hash='0'*64,assets=tuple(sorted(records,key=lambda x:x.asset_id)))
    rh=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':rh,'content_hash':rh})
    identity='同一女性面貌、左耳黑色耳挂、左领极细红灯线、炭黑高领大衣与后梳低髻完整保持'
    observer='保持认可A03的身体朝向与设备视线，嘴唇自然静置，不出现说话或演唱的连续口型；不操作设备、不敲键盘、不抬手；自然呼吸或眨眼属可接受变化，不要求必须观察到某次事件'
    camera='沿原视轴极缓慢微幅推近，保持原观察侧与人物、显示器背面的相对位置，末段平滑收稳'
    monitor='保持显示器背面、背壳与支架，绝不转向正面或向背面贴图；新闻解释图形由独立剪辑承接'
    coverage={'schema_version':'4','request':{'creative_input_kind':'draft_prompt','creative_input_evidence':PROMPT,'creative_constraints':[{'constraint_id':'monitor-back','scope':'global','source_text':'观察者看到的始终是显示器背面'}],'target_duration_seconds':6,'coverage_strategy':'single_take','strategy_source':'agent_directed','director_decision_rationale':'认可室内画面只承担观察者反应，独立图形承担新闻解释，六秒源片不新增操作动作。','strategy_request_evidence':None,'director_skill':'open-video'},'coverage_units':[{'unit_id':'ep01-dns','duration_seconds':6,'beat_function':'reaction','objective':observer,'open_state':'原A03室内构图，嘴唇自然静置看向设备，显示器背面对观察者','close_state':'微幅推近收稳，同一人物仍嘴唇自然静置，显示器背面关系不变','shot_scale':'medium','camera_treatment':'push_in','camera_intent':camera,'visible_change':'仅自然呼吸、眨眼、极轻视线反应及微小透视变化','transition_out':'end','constraint_ids':['monitor_back']}],'intent_items':[{'intent_item_id':'monitor-back','statement':monitor,'source_refs':[{'source_hash':hashlib.sha256(PROMPT.encode()).hexdigest(),'locator':'native-prompt.zh.txt','intent_item_id':'monitor-back','quote':monitor,'origin':'director_choice'}],'origin':'director_choice','related_intent_ids':[]}],'intent_groups':{'must_happen':[{'intent_item_id':'monitor-back'}],'must_not_happen':[],'preferred_performance':[],'timing_targets':[],'acceptable_variation':[]}}
    ch,ca=director_coverage_authoring_input(coverage)
    preview={'kind':'user-preview-approval/1','coverage_hash':ch,'unit_ids':['ep01-dns'],'preview_artifacts':[{'path':x['path'],'sha256':x['sha256'],'role':x['role']} for x in selections if x['selected_for_provider']],'user_quote':approval['user_decision']['exact_quote']}
    ah,aa=preview_approval_authoring_input(preview)
    for item,prepared in ((coverage,ca),(preview,aa)):
        provenance.append(authoring_input_reference(item));out=P/prepared.relative_path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(prepared.payload)
    performance={'trigger':'原室内设备前静静观察','visible_response':observer,'gaze_target':'原参考设备方向，保持微小视线反应','body_behavior':'原位自然呼吸，不转身、不抬手','hand_behavior':'保持原参考静置或不可见状态，不敲键盘、不操作设备','terminal_performance_state':'嘴唇自然静置平静观察，显示器仍以背面朝向观察者','character_directions':[{'character_id':'IRIS','screen_identity':identity,'role':'principal','visibility':'visible','beats':[{'phase':'throughout','trigger':'原室内设备前静静观察','emotion':'冷静克制','intensity':'subtle','facial_expression':'嘴唇自然静置平静，轻微自然眨眼','gaze_target':'原设备方向','breathing':'自然平稳','body_behavior':'原位观察，仅极轻视线反应与呼吸'}]}]}
    planning={'facets':['identity_consistency','slow_camera','stable'],'structure':'continuous','anchors':[{'anchor_id':'identity','role':'identity','purpose':'同一女性的完整面貌、身份、左耳装置和左领极细红线','owner_id':'IRIS'},{'anchor_id':'interior','role':'scene_environment','purpose':'场景、光线、构图与起始人物姿态','owner_id':'interior'}],'events':[{'event_id':'open-composition','kind':'composition','phase':'start','visual_state':'观察者看到的始终是显示器背面','purpose':'保持背壳、支架和原人物相对位置','control':'review_only'},{'event_id':'close-composition','kind':'composition','phase':'end','visual_state':'末段平滑收稳，人物仍嘴唇自然静置，服装、耳挂和灯线位置不变','purpose':'保持原观察侧与人物、显示器背面的相对位置','control':'review_only'}],'selections':[{'need_id':key,'asset_id':aid} for key,aid in [('identity','iris-cf-details'),('interior','iris-c-interior')]],'natural_generation':['允许自然呼吸、轻微自然眨眼与极轻视线反应'],'director_coverage':{'coverage_hash':ch,'unit_id':'ep01-dns'},'preview_approval':{'approval_hash':ah}}
    gi=GenerationIntent.model_validate({'reference_planning':planning,'open_state':{'kind':'typed_text','state_text':'以认可A03室内图开始，同一人物嘴唇自然静置观察，显示器背面朝向观察者'},'close_state':{'kind':'typed_text','state_text':'微幅推近收稳，嘴唇自然静置观察与显示器背面关系保持'},'identity_continuity':{'character_ids':['IRIS'],'preservation':'exact','allowed_variation':['微小透视、自然呼吸、眨眼与视线反应']},'scene_continuity':{'scene_id':'interior','time_of_day':'同一凌晨','mood':'冷静精密疏离','state_constraints':[monitor,'同一室内与原窗外冷光，不新增设备或人物']},'space_continuity':{'subject_position':'原设备前，保持A03站位','screen_direction':'保持原设备方向','crossing_policy':'人物不换位，摄影机不绕到显示器正面'},'axis_continuity':{'camera_axis':'原A03观察侧与视轴','framing_continuity':'同一人物、显示器背面与原窗位置关系','crossing_policy':'不翻轴、不环绕'},'subject_action':{'start_state':'嘴唇自然静置看向原设备','progression':observer,'endpoint':{'state_text':'仍嘴唇自然静置观察，不操作设备'}},'motion_envelope':{'onset':'原轴微幅推近平滑开始','peak':'自然呼吸、轻微眨眼与极轻视线反应','settle':'推近收稳，原设备关系保持','direction':'原视轴前进','amplitude_class':'极小'},'pacing':{'cadence':'六秒连续自然观察','tempo_class':'正常原速','shot_duration_seconds':6},'camera_intent':{'movement':camera,'stability':'平稳连续，末段收稳','framing_intent':'保持A03人物与显示器背面构图'},'camera_endpoint':{'start_framing':'原A03人物与显示器背面','end_framing':'略近但仍是同一观察侧与显示器背面'},'performance_intent':performance,'visual_treatment':{'medium_look':'真人电影摄影','palette':'蓝黑钢蓝，红色仅限原左领极细灯线','material_treatment':'自然皮肤、衣料、设备背壳','prohibited_visual_drift':['向显示器背面贴图或切换正面','新增剧情字幕、新闻图形、人物或设备操作；平台正常人工智能标识保留','改变面貌、装置侧别或服装']},'lighting_intent':{'motivated_source':'原窗外冷光','direction':'原A03方向','exposure_priority':'同一面貌、耳挂与显示器背面关系可辨','continuity_state':'原凌晨室内冷光'},'ambience_intent':{'environment_bed':'极轻房间环境声','foley_cues':[],'explicitly_silent':False},'dialogue_intent':{'mode':'none','lip_sync_required':False},'music_intent':{'mode':'none'},'primary_camera_motion':{'movement_kind':'dolly_in','direction':'forward','amplitude_class':'subtle','speed_class':'very_slow','start_motion_state':'stationary','end_motion_state':'settled'},'camera_subject_relation':{'subject_id':'IRIS','relation_kind':'maintain_offset','start_relation':'原A03人物与设备背面同框','end_relation':'同轴略近，设备背面关系不变'}})
    def seal(cls,key,data):return seal_artifact(cls(artifact_id='iris-c-draft-'+key,revision=1,content_hash='0'*64,creation_receipt_id='iris-c-draft-authoring:'+key,source_provenance=tuple(provenance),**data))
    scene=seal(Scene,'scene',core(source('scene-interior.json',Scene))|{'visual_reference_asset_ids':['iris-c-interior']})
    from ai_video.production.project import load_production_project
    char=load_production_project(EP/'a01-first-frame-repair/project/project.yaml').characters[0]
    assert char.character_id=='IRIS' and 'iris-cf-details' in char.reference_asset_ids
    shot_data=core(source('shot-dns.json',Shot))|{'intent':PROMPT,'continuity_constraints':[identity,observer,camera,monitor],'required_asset_roles':[{'role':'primary_visual','asset_ids':[],'allowed_asset_types':['video']},{'role':'reference','asset_ids':[x['asset_id'] for x in selections if x['selected_for_provider']],'allowed_asset_types':['image']}]}
    shot=seal(Shot,'shot',shot_data)
    row={'shot':shot_data,'generation':{'references':[{'role':'character_reference','asset_id':'iris-cf-details','owner_id':'IRIS'},{'role':'scene_reference','asset_id':'iris-c-interior'}],'generation_intent':gi.model_dump(mode='json'),'intent_evidence':{'character_action_required':True,'state_change_required':False,'subject_motion_directive_present':True},'output_need':{'timing_mode':'content_driven','duration_seconds':6,'geometry_policy':'adaptive','aspect_ratio':'16:9','container_mime':'video/mp4'},'audio_need':'optional','quality_need':{'objective_tier':'preview'}},'composition':{'muted':True,'source_audio_policy':'MUTE','source_audio_reason':'新闻歌曲或念白由最终剪辑独立音轨承载'},'boundary':{'independent':True,'reason':'独立室内观察覆盖；非从阳台连续走入，A01与C由最终剪辑选择，不要求复制未验收前镜终态'}}
    authored={'native_prompt':PROMPT,'row':row}
    authored_ref=authoring_input_reference(authored);provenance.append(authored_ref)
    authored_path=P/authored_ref.reference;authored_path.parent.mkdir(parents=True,exist_ok=True);authored_path.write_bytes(authoring_input_payload(authored))
    rules=[('identity',identity,PROMPT.splitlines()[0]),('observer',observer,PROMPT.splitlines()[2]),('camera',camera,PROMPT.splitlines()[2]),('monitor-back',monitor,PROMPT.splitlines()[1])]
    profile={'domain_id':'iris-source','profile_id':'iris-c-raw','profile_version':'1','measurement_contract_version':'iris-exact-mp4-review/1','required_requirement_ids':[r[0] for r in rules],'requirement_semantics_version':'requirement-semantics/1','generation_requirements':[]}
    for rid,observable,fragment in rules:
        paths=[]
        for path in leaves(gi.model_dump(mode='json'),'generation_intent'):
            group='observer' if any(k in path for k in ('performance_intent','subject_action','motion_envelope','pacing','dialogue_intent','music_intent','ambience_intent')) else 'camera' if any(k in path for k in ('camera_','axis_continuity','space_continuity','reference_planning.events')) else 'identity' if 'identity_continuity' in path else 'monitor-back'
            if group==rid:paths.append(path)
        h=canonical_sha256({'native_prompt':PROMPT,'row':row});locator='row.shot.continuity_constraints'
        src={'source_hash':h,'locator':locator,'intent_item_id':rid,'quote':observable,'origin':'director_choice'}
        profile['generation_requirements'].append({'requirement_id':rid,'level':'acceptance','stage':'raw_generation','dimension':rid,'observable':observable,'tolerance':'逐项满足已认可参考与上述表演职责，未生成前不得判PASS','measurement':'exact MP4正常速度审看与project-local video-analysis逐项核对','proof':'analyzer','intent_paths':paths,'native_text':[fragment],'native_text_mapping':{'intent_sha256':canonical_sha256(gi.model_dump(mode='json')),'bindings':[{'intent_path':path,'fragment_indices':[0]} for path in paths]},'production_owner':'shot_authoring','semantics':{'version':'requirement-semantics/1','category':'narrative_critical','intent_role':'must_happen','source_refs':[src],'hard_basis':{'kind':'approved_narrative','source_hash':h,'locator':locator,'necessity':'这个摄影设置只承担已认可人物观察反应，解释图形交给独立剪辑，因此不能改变设备背面关系或新增操作。'}}})
    ph=canonical_sha256(profile);acceptance=DomainAcceptancePolicy(domain_id='iris-source',profile_id='iris-c-raw',profile_version='1',measurement_contract_version='iris-exact-mp4-review/1',required_requirement_ids=tuple(profile['required_requirement_ids']),profile_content_hash=ph,profile_payload=profile|{'content_hash':ph})
    qa=seal(QaPolicy,'qa',{'policy_id':'iris-c-raw','policy_version':'1','required_layers':['technical','semantic','final_acceptance'],'technical_thresholds':{'black_luma_max_milli':10,'silence_peak_max_millidb':-60000,'clipping_peak_min_millidb':-100},'layout_rules':{'safe_area_inset_milli':50,'caption_overflow_tolerance_milli':0},'strategy_rules_version':'iris-source/1','semantic_requirement':'required','semantic_authorities':[{'name':'video-analysis','version':'project-local'}],'generation_acceptance':acceptance,'generation_evaluation_authorities':[{'evaluator':{'name':'video-analysis','version':'project-local'},'proof':'analyzer'}],'final_output':{'goal_id':'iris-c-source','goal_version':'1','user_goal':'六秒同一人物室内观察源片，显示器始终背面；未代表整集或人工验收','requirements':[{'requirement_id':r[0],'observable':r[1],'proof':'human'} for r in rules]}})
    for name,obj in [('scene.json',scene),('character.json',char),('shot.json',shot),('qa-policy.json',qa),('registry-draft.json',registry)]:write(name,obj.model_dump(mode='json'))
    for name,obj in [('row.json',row),('director-coverage.json',coverage),('preview-approval.json',preview),('source-selections.json',selections)]:write(name,obj)
    (P/'native-prompt.zh.txt').write_text(PROMPT+'\n')
    assert not re.search('[A-Za-z]',PROMPT)
    write('validation.json',{'scope':'typed authoring draft only','typed_scene_shot_character_qa_registry':True,'source_hashes_match_user_approved_package':True,'registered_source_count':3,'provider_selected_source_count':2,'natural_lips_no_continuous_speech_or_device_operation':True,'monitor_back_preserved':True,'source_nominal_window_seconds':6,'source_audio_final_mute':True,'exact_native_order':'NOT_EVALUATED until canonical authoring and resolved_request.image_bindings','expected_order_to_verify':['iris-c-interior','iris-cf-details'],'runtime_preview_approval_payload_valid':True,'runtime_preview_approval_adopted':False,'previous_shot_gate':'canonical A01-v2 Gate must PASS before materialize apply or new submit','parent_source_project':'../a01-first-frame-repair/project','parent_attempt':'iris-ep01-a01-two-reference-repair-002','ai_label_allowed':True,'no_extra_required_pixel_breathing_or_blink_measurement':True,'canonical_project_mutations':0,'provider_calls':0,'actual_quality':'NOT_EVALUATED'})
    print('Typed C source draft valid; 3 exact approved sources; 0 canonical writes / provider calls.')
if __name__=='__main__':main()
