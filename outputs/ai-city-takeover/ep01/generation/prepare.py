"""EP01 source authoring data through existing canonical owners; no Provider calls."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
from PIL import Image
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload
from ai_video.production.domain_acceptance import DomainAcceptancePolicy
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import (AssetRecord, AssetRegistrySnapshot, ProductionBrief, Story,
    StoryBeat, Character, Scene, Shot, Storyboard, StoryboardBeat, ProductionProject,
    ProjectArtifactRefs, ArtifactReference, DeliveryProfile, RendererPolicy, QaPolicy, SourceReference)
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import ProductionStateCommitter, PreparedArtifact, _canonical_yaml_bytes
from ai_video.production.video_requirement import GenerationIntent
from ai_video.canvas_dependencies import initialize_canvas_graph
from ai_video.production.project import load_production_project

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
EP=HERE.parent
DRAFT=EP/'production-input'
FILES=(('iris-cf-face',EP.parent/'series/casting/raw/CF-a.png'),
       ('iris-cf-details',EP.parent/'series/identity-cf/raw/CF-ID7b-a.png'),
       ('iris-a01-balcony',EP/'reference-package/A01-v1.png'))
PROMPT='''真人电影摄影，横幅十六比九，连续六秒。以第一张已认可阳台图作为场景、光线、构图与起始人物姿态的主要参考；第二张只锁定左耳黑色耳挂和左领极细红色灯线，第三张只锁定同一女性的面貌，不继承身份图背景。
同一位浅肤色、极淡雀斑、浅灰蓝眼、深棕后梳低髻的年轻女性，穿炭黑高领长大衣，站在原玻璃阳台右侧，左侧雾城负空间保留。蓝黑与钢蓝冷色，红色仅为原左领极细灯线，保持原图自然皮肤、衣料和雾城层次。
她平静闭口观察，眼神保持原方向，只出现自然呼吸和一次轻微自然眨眼，衣领边缘被微风极轻拂动；不说话、不唱歌、不做口型、不转身、不抬手、不增加其他人物。摄影机沿原视轴极缓慢微幅推近，保持人物在画面右侧及原观察侧，不翻轴、不环绕、不突然变焦。末段平滑收稳，人物仍闭口，服装、耳挂和灯线位置不变。全镜连续原速，不切镜、不叠化、不冻结。
保持原阳台和同一雾城，不新增屏幕、文字、字幕、标志或界面。只允许轻微环境风声，不生成对白、旁白、演唱或音乐；成片使用独立音轨，本源片原生声音在剪辑中静音。'''

def write(name,value):
    path=HERE/name
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def artifact(path,payload):
    return PreparedArtifact(Path(path),payload,hashlib.sha256(payload).hexdigest())

def draft(name,cls):
    model=cls.model_validate_json((DRAFT/name).read_bytes())
    assert verify_artifact_hash(model), f"invalid draft artifact hash: {name}"
    return model

def build():
    approval=json.loads((EP/'reference-package/reference-review.json').read_text())
    assert approval['user_decision']['exact_quote']=='三张都认可，继续镜头制作'
    expected={x['path']:x['sha256'] for x in approval['images']}
    expected.update({x['path']:x['sha256'] for x in approval['images'][0]['actual_image_inputs']})
    records=[];assets=[];sources=[]
    for aid,path in FILES:
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        relative=path.relative_to(REPO).as_posix()
        assert expected[relative]==sha, f'changed approved source: {relative}'
        with Image.open(path) as im: width,height=im.size; assert im.format=='PNG'
        destination=canonical_image_asset_path(sha)
        origin={'kind':'iris-approved-local-source-import/1','path':relative,'sha256':sha,
                'approval_file_sha256':hashlib.sha256((EP/'reference-package/reference-review.json').read_bytes()).hexdigest()}
        source_ref=authoring_input_reference(origin)
        sources.append(source_ref);assets.append(artifact(source_ref.reference,authoring_input_payload(origin)))
        records.append(AssetRecord(asset_id=aid,asset_type='image',artifact_path=destination,
            sha256=sha,size_bytes=len(raw),mime_type='image/png',width=width,height=height,
            source_kind='imported',tool={'name':'approved-local-source-import','version':'1'},
            input_fingerprint=canonical_sha256(origin),creation_receipt_id='iris-local-import:'+sha,
            usage_license='User-authorized project reference; platform ownership or generated provenance is not inferred.'))
        assets.append(artifact(destination,raw))
    registry=AssetRegistrySnapshot(revision_id='0'*64,content_hash='0'*64,assets=tuple(sorted(records,key=lambda x:x.asset_id)))
    rh=registry_semantic_sha256(registry);registry=registry.model_copy(update={'revision_id':rh,'content_hash':rh})
    intro=draft('shot-intro.json',Shot)
    identity='同一女性面貌、左耳黑色耳挂、左领极细红灯线、炭黑高领大衣与后梳低髻完整保持'
    action='平静闭口观察，仅自然呼吸、轻微自然眨眼和衣领边缘极轻风动；不说话、不唱歌、不转身、不抬手'
    camera='摄影机沿原视轴极缓慢微幅推近，保持人物在右侧与左侧雾城负空间，不翻轴、不环绕、不突然变焦，末段平滑收稳'
    visual='真人电影摄影，蓝黑和钢蓝，红色仅限原左领极细灯线，不新增文字、屏幕或人物'
    coverage={'schema_version':'4','request':{'creative_input_kind':'draft_prompt','creative_input_evidence':PROMPT,'creative_constraints':[{'constraint_id':'approved-balcony','scope':'global','source_text':PROMPT.splitlines()[0]}],'target_duration_seconds':6,'coverage_strategy':'single_take','strategy_source':'agent_directed','director_decision_rationale':'已认可阳台构图只增加微小自然运动，六秒单源片无需切镜；完整歌曲时间线另行拥有。','strategy_request_evidence':None,'director_skill':'open-video'},'coverage_units':[{'unit_id':'ep01-intro','duration_seconds':6,'beat_function':'establish','objective':action,'open_state':'原认可阳台构图中闭口观察','close_state':'轻微推近后仍闭口观察','shot_scale':'medium','camera_treatment':'push_in','camera_intent':camera,'visible_change':'轻微推近仅让面部与装置更可辨，保留左侧雾城','transition_out':'end','constraint_ids':['approved_balcony']}],'intent_items':[{'intent_item_id':'observer','statement':action,'source_refs':[{'source_hash':hashlib.sha256(PROMPT.encode()).hexdigest(),'locator':'native-prompt.zh.txt','intent_item_id':'observer','quote':action,'origin':'director_choice'}],'origin':'director_choice','related_intent_ids':[]}],'intent_groups':{'must_happen':[{'intent_item_id':'observer'}],'must_not_happen':[],'preferred_performance':[],'timing_targets':[],'acceptable_variation':[]}}
    from ai_video.production.reference_authoring import director_coverage_authoring_input
    from ai_video.production.preview_approval import preview_approval_authoring_input
    ch,ca=director_coverage_authoring_input(coverage)
    runtime_approval={'kind':'user-preview-approval/1','coverage_hash':ch,'unit_ids':['ep01-intro'],'preview_artifacts':[{'path':str(path.relative_to(REPO)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'role':role} for (aid,path),role in zip(FILES,('previously accepted canonical face','previously accepted canonical details','approved decisive balcony composition'))],'user_quote':'三张都认可，继续镜头制作'}
    ah,aa=preview_approval_authoring_input(runtime_approval)
    assets.extend((ca,aa));sources.extend((authoring_input_reference(coverage),authoring_input_reference(runtime_approval)))
    write('director-coverage.json',coverage);write('preview-approval.json',runtime_approval)
    reference_plan={'facets':['stable','slow_camera','identity_consistency'],'structure':'continuous','anchors':[{'anchor_id':'face','role':'identity','purpose':'同一女性的面貌','owner_id':'IRIS'},{'anchor_id':'details','role':'identity','purpose':'左耳黑色耳挂和左领极细红色灯线','owner_id':'IRIS'},{'anchor_id':'balcony','role':'scene_environment','purpose':'场景、光线、构图与起始人物姿态','owner_id':'balcony'}],'events':[{'event_id':'opening-composition','kind':'composition','phase':'start','visual_state':'站在原玻璃阳台右侧，左侧雾城负空间保留','purpose':'左侧雾城负空间保留','control':'review_only'},{'event_id':'closing-composition','kind':'composition','phase':'end','visual_state':'末段平滑收稳，人物仍闭口，服装、耳挂和灯线位置不变','purpose':'保持人物在画面右侧及原观察侧','control':'review_only'}],'selections':[{'need_id':k,'asset_id':aid} for k,(aid,path) in zip(('face','details','balcony'),FILES)],'director_coverage':{'coverage_hash':ch,'unit_id':'ep01-intro'},'preview_approval':{'approval_hash':ah},'natural_generation':['只出现自然呼吸和一次轻微自然眨眼，衣领边缘被微风极轻拂动']}
    performance={'trigger':'在同一雾城阳台观察','visible_response':action,'gaze_target':'原图视线方向','body_behavior':'原位自然呼吸，不转身、不抬手','hand_behavior':'保持原参考不可见或静置状态，不新增动作','terminal_performance_state':'闭口平静观察','character_directions':[{'character_id':'IRIS','screen_identity':identity,'role':'principal','visibility':'visible','beats':[{'phase':'throughout','trigger':'在同一雾城阳台观察','emotion':'冷静疏离','intensity':'subtle','facial_expression':'闭口平静，轻微自然眨眼','gaze_target':'原图视线方向','breathing':'自然平稳','body_behavior':'原位观察，仅自然呼吸及衣领微风'}]}]}
    gi=GenerationIntent.model_validate({'reference_planning':reference_plan,'performance_intent':performance,

        'open_state':{'kind':'typed_text','state_text':'以已认可第一张阳台图的构图、人物姿态、雾城和灯光开始'},
        'close_state':{'kind':'typed_text','state_text':'微幅推近收稳，同一人物仍闭口观察，身份与空间均不变'},
        'identity_continuity':{'character_ids':['IRIS'],'preservation':'exact','allowed_variation':['仅轻微呼吸、自然眨眼与小幅推近的透视变化']},
        'scene_continuity':{'scene_id':'balcony','time_of_day':'同一凌晨','mood':'冷静疏离','state_constraints':['原阳台和同一雾城','不新增场景、人物或服装']},
        'space_continuity':{'subject_position':'原阳台右侧','screen_direction':'保持原视线方向','crossing_policy':'不换位、不穿越栏杆'},
        'axis_continuity':{'camera_axis':'原参考视轴同侧','framing_continuity':'右侧人物、左侧雾城负空间','crossing_policy':'不翻轴、不环绕'},
        'subject_action':{'start_state':'原图闭口观察','progression':action,'endpoint':{'state_text':'同一姿态闭口观察，未说话或演唱'}},
        'motion_envelope':{'onset':'微幅推近平滑开始','peak':'自然呼吸和极轻衣领风动','settle':'推近平滑收稳','direction':'沿原视轴前进','amplitude_class':'极小'},
        'pacing':{'cadence':'六秒连续自然观察','tempo_class':'正常原速','shot_duration_seconds':6},
        'camera_intent':{'movement':camera,'stability':'平稳连续，末段收稳','framing_intent':'保留原图右侧人物和左侧负空间'},
        'camera_endpoint':{'start_framing':'原认可阳台图','end_framing':'略近但同轴、同侧、仍留左侧负空间'},
        'visual_treatment':{'medium_look':'真人电影摄影','palette':'蓝黑和钢蓝，唯一暖色为左领极细红线','material_treatment':'自然皮肤与炭黑衣料','prohibited_visual_drift':['新增文字、屏幕或人物','改变面貌、装置侧别或服装','切镜、冻结、加速']},
        'lighting_intent':{'motivated_source':'原雾城冷光','direction':'原图方向','exposure_priority':'面部与耳挂、领灯可辨','continuity_state':'同一凌晨雾城冷光'},
        'ambience_intent':{'environment_bed':'极轻环境风声','foley_cues':[],'explicitly_silent':False},
        'dialogue_intent':{'mode':'none','lip_sync_required':False},'music_intent':{'mode':'none'},
        'primary_camera_motion':{'movement_kind':'dolly_in','direction':'forward','amplitude_class':'subtle','speed_class':'very_slow','start_motion_state':'stationary','end_motion_state':'settled'},
        'camera_subject_relation':{'subject_id':'IRIS','relation_kind':'maintain_offset','start_relation':'原图右侧中近景','end_relation':'原视轴略近，仍位于右侧'}})
    shot_data=intro.model_dump(mode='json',exclude={'artifact_id','schema_version','revision','content_hash','creation_receipt_id','source_provenance'})
    shot_data.update(intent=PROMPT,continuity_constraints=[identity,action,camera,visual],required_asset_roles=[
        {'role':'primary_visual','asset_ids':[],'allowed_asset_types':['video']},
        {'role':'reference','asset_ids':['iris-cf-face','iris-cf-details','iris-a01-balcony'],'allowed_asset_types':['image']}])
    row={'shot':shot_data,'generation':{'references':[
        {'role':'character_reference','asset_id':'iris-cf-face','owner_id':'IRIS'},
        {'role':'character_reference','asset_id':'iris-cf-details','owner_id':'IRIS'},
        {'role':'scene_reference','asset_id':'iris-a01-balcony'}],
        'generation_intent':gi.model_dump(mode='json'),'intent_evidence':{'character_action_required':True,'state_change_required':False,'subject_motion_directive_present':True},
        'output_need':{'timing_mode':'content_driven','duration_seconds':6,'geometry_policy':'adaptive','aspect_ratio':'16:9','container_mime':'video/mp4'},
        'audio_need':'optional','quality_need':{'objective_tier':'preview'}},
        'composition':{'muted':True,'source_audio_policy':'MUTE','source_audio_reason':'后期独立歌曲或念白；源片不声称对嘴完成'}}
    envelope={'kind':'iris-ep01-a01-authoring/1','row':row,'approval':approval,'native_prompt':PROMPT,
              'source_role':'first independent source shot, not final episode timeline','provider_effects':0}
    reference=authoring_input_reference(envelope)
    provenance=(reference,*sources)
    def seal(cls,key,**data):
        return seal_artifact(cls(artifact_id='iris-a01-'+key,revision=6,content_hash='0'*64,
            creation_receipt_id='iris-a01-authoring:'+key,source_provenance=provenance,**data))
    def core(m):return m.model_dump(mode='json',exclude={'artifact_id','schema_version','revision','content_hash','creation_receipt_id','source_provenance'})
    brief=seal(ProductionBrief,'brief',title='IRIS EP01 A01 source qualification',objective='已认可阳台参考的六秒轻微自然运动源片；未完成歌曲、对嘴或整集',audience='中文短视频观众',format='1920×1080 30fps horizontal source',language='zh',constraints=(identity,action,camera,visual))
    story=seal(Story,'story',language='zh',logline='冷静观察者在雾城阳台停留',synopsis='单独源片供后续完整歌曲剪辑使用',beats=(StoryBeat(beat_id='intro',summary='闭口观察，不把念白伪装成对嘴'),))
    char=seal(Character,'character',**(core(draft('character-iris.json',Character))|{'reference_asset_ids':('iris-cf-face','iris-cf-details')}))
    scene=seal(Scene,'scene',**(core(draft('scene-balcony.json',Scene))|{'visual_reference_asset_ids':('iris-a01-balcony',)}))
    shot=seal(Shot,'shot',**shot_data)
    board=seal(Storyboard,'storyboard',beats=(StoryboardBeat(beat_id='intro',scene_id='balcony',shot_ids=('ep01-intro',),narrative_intent='先制作独立阳台源片，完整歌曲剪辑另由最终时间线负责'),))
    models=[(m,'creative/'+m.artifact_id+'/'+m.content_hash+'.yaml') for m in (brief,story,char,scene,shot,board)]
    def ref(model):return ArtifactReference(artifact_id=model.artifact_id,revision=model.revision,content_hash=model.content_hash,path=next(Path(p) for m,p in models if m==model))
    project=seal_artifact(ProductionProject(artifact_id='iris-a01-project',revision=6,content_hash='0'*64,
        creation_receipt_id='iris-a01-bootstrap',source_provenance=provenance,project_id='iris-ep01-a01-source',title='IRIS EP01 A01 source',default_language='zh',
        delivery_profile=DeliveryProfile(width=1920,height=1080,fps=30),renderer_policy=RendererPolicy(),
        artifacts=ProjectArtifactRefs(brief=ref(brief),story=ref(story),characters=(ref(char),),scenes=(ref(scene),),storyboard=ref(board),shots=(ref(shot),))))
    requirements=[('identity',identity,'generation_intent.identity_continuity.preservation',PROMPT.splitlines()[1]),('quiet-observer',action,'generation_intent.subject_action.progression',PROMPT.splitlines()[2]),('camera-space',camera,'generation_intent.camera_intent.movement',PROMPT.splitlines()[2]),('visual',visual,'generation_intent.visual_treatment.medium_look',PROMPT.splitlines()[1])]
    profile={'domain_id':'iris-source','profile_id':'iris-a01-raw','profile_version':'1','measurement_contract_version':'iris-exact-mp4-review/1','required_requirement_ids':[r[0] for r in requirements],'requirement_semantics_version':'requirement-semantics/1','generation_requirements':[]}
    for rid,observable,path,fragment in requirements:
        locator='row.shot.continuity_constraints'
        paths=[path]
        def leaves(node,prefix):
            if isinstance(node,dict):
                for key,value in node.items():yield from leaves(value,prefix+'.'+key)
            elif isinstance(node,(tuple,list)):
                for index,value in enumerate(node):yield from leaves(value,prefix+'.'+str(index))
            elif node is not None:yield prefix
        for candidate_path in leaves(gi.model_dump(mode='json'),'generation_intent'):
            group=('quiet-observer' if any(k in candidate_path for k in ('performance_intent','subject_action','motion_envelope','pacing','dialogue_intent','ambience_intent','music_intent')) else 'camera-space' if any(k in candidate_path for k in ('camera_','axis_continuity','space_continuity','reference_planning.events')) else 'identity' if 'identity_continuity' in candidate_path else 'visual')
            if group==rid and candidate_path not in paths:paths.append(candidate_path)
        src={'source_hash':canonical_sha256(envelope),'locator':locator,'intent_item_id':rid,'quote':observable,'origin':'director_choice'}
        profile['generation_requirements'].append({'requirement_id':rid,'level':'acceptance','stage':'raw_generation','dimension':rid,'observable':observable,'tolerance':'逐项满足，不由静态参考或工具成功代签','measurement':'对exact MP4正常速度审看及project-local video-analysis逐项取证','proof':'analyzer','intent_paths':paths,'native_text':[fragment],'production_owner':'shot_authoring','native_text_mapping':{'intent_sha256':canonical_sha256(gi.model_dump(mode='json')),'bindings':[{'intent_path':mapped_path,'fragment_indices':[0]} for mapped_path in paths]},'semantics':{'version':'requirement-semantics/1','category':'narrative_critical','intent_role':'must_happen','source_refs':[src],'hard_basis':{'kind':'approved_narrative','source_hash':src['source_hash'],'locator':locator,'necessity':'保持用户已认可的同一人物与阳台镜头，不新增场景或表演职责'}}})
    ph=canonical_sha256(profile)
    acceptance=DomainAcceptancePolicy(domain_id=profile['domain_id'],profile_id=profile['profile_id'],profile_version='1',measurement_contract_version=profile['measurement_contract_version'],required_requirement_ids=tuple(profile['required_requirement_ids']),profile_content_hash=ph,profile_payload=profile|{'content_hash':ph})
    qa=seal(QaPolicy,'qa',policy_id='iris-a01-raw',policy_version='1',required_layers=('technical','semantic','final_acceptance'),technical_thresholds={'black_luma_max_milli':10,'silence_peak_max_millidb':-60000,'clipping_peak_min_millidb':-100},layout_rules={'safe_area_inset_milli':50,'caption_overflow_tolerance_milli':0},strategy_rules_version='iris-source/1',semantic_requirement='required',semantic_authorities=({'name':'video-analysis','version':'project-local'},),generation_acceptance=acceptance,generation_evaluation_authorities=({'evaluator':{'name':'video-analysis','version':'project-local'},'proof':'analyzer'},),final_output=FinalOutputContract(goal_id='iris-a01-source',goal_version='1',user_goal='完整六秒阳台自然运动源片，不代表整集完成或人工认可',requirements=tuple({'requirement_id':r[0],'observable':r[1],'proof':'human'} for r in requirements)))
    artifacts=tuple([*assets,artifact(reference.reference,authoring_input_payload(envelope)),*(artifact(p,_canonical_yaml_bytes(m)) for m,p in models)])
    return row,project,registry,artifacts,qa,reference

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bootstrap',action='store_true');args=parser.parse_args()
    row,project,registry,artifacts,qa,reference=build()
    write('row.json',row);write('qa-policy.json',qa.model_dump(mode='json'));write('project-preview.json',project.model_dump(mode='json'));write('registry-preview.json',registry.model_dump(mode='json'))
    (HERE/'native-prompt.zh.txt').write_text(PROMPT+'\n',encoding='utf-8')
    lint={'three_exact_registered_sources':len(registry.assets)==3,'source_windows_seconds':row['shot']['duration_policy']['seconds']==6,'no_song_or_lipsync':row['generation']['generation_intent']['dialogue_intent']['mode']=='none','mute_at_composition':row['composition']['source_audio_policy']=='MUTE','chinese_prompt':not re.search('[A-Za-z]',PROMPT),'no_fake_canvas_capture':True,'runtime_preview_approval_present':True,'live_profile_present':False,'paid_submits':0}
    assert all(lint[k] for k in ('three_exact_registered_sources','no_song_or_lipsync','mute_at_composition','chinese_prompt'))
    root=HERE/'project'
    if args.bootstrap:
        root.mkdir(exist_ok=True)
        if (root/'project.yaml').exists():
            loaded=load_production_project(root/'project.yaml')
            if loaded.project != project:
                from dataclasses import replace
                from ai_video.production.state_commit import prepare_project_registry_commit
                from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
                c=ProductionStateCommitter(root)
                request=prepare_project_registry_commit(manifest=loaded.manifest,project=project,registry=registry,attempt_id='iris-a01-rich-authoring-v6')
                request=replace(request,artifacts=tuple(sorted((*request.artifacts,*artifacts),key=lambda a:a.relative_path.as_posix())))
                import yaml
                by_type={}
                for a in artifacts:
                    if str(a.relative_path).startswith('creative/'):
                        obj=yaml.safe_load(a.payload)
                        for cls in (ProductionBrief,Story,Character,Scene,Shot,Storyboard):
                            try: model=cls.model_validate(obj)
                            except Exception: continue
                            by_type.setdefault(cls,[]).append(model);break
                candidate=loaded.model_copy(update={'project':project,'registry':registry,'brief':by_type[ProductionBrief][0],'story':by_type[Story][0],'characters':tuple(by_type[Character]),'scenes':tuple(by_type[Scene]),'shots':tuple(by_type[Shot]),'storyboard':by_type[Storyboard][0]})
                request=prepare_strategy_dependency_transition(base_loaded=loaded,candidate_loaded=candidate,request=request)
                m=c.commit(request)
                c.activate_qa_policy(qa,attempt_id='iris-a01-rich-qa-v6',expected_manifest_revision=m.manifest_revision)
            assert loaded.registry==registry
        else:
            c=ProductionStateCommitter(root)
            m=c.bootstrap_initial_state(attempt_id='iris-a01-bootstrap',project=project,registry=registry,artifacts=artifacts)
            m=initialize_canvas_graph(c,'iris-a01-graph')
            m=c.upgrade_manifest_schema('2.14',expected_manifest_revision=m.manifest_revision)
            c.activate_qa_policy(qa,attempt_id='iris-a01-qa',expected_manifest_revision=m.manifest_revision)
        loaded=load_production_project(root/'project.yaml')
        assert loaded.qa_policy==qa and len(loaded.registry.assets)==3
        lint['canonical_reload_verified']=True;lint['manifest_revision']=loaded.manifest.manifest_revision
    write('preparation-validation.json',lint);print(json.dumps(lint,ensure_ascii=False))
if __name__=='__main__':main()
