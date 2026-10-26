from pathlib import Path
import json,hashlib,importlib.util
from ai_video.production.final_output_contracts import FinalOutputContract,FinalOutputRequirement
from ai_video.production.visual_quality import VisualDirection,visual_requirements
H=Path(__file__).resolve().parent
raw=(H/'creative-input.txt').read_text();digest=hashlib.sha256(raw.encode()).hexdigest()
quotes={f'intent-{i:02}':v for i,v in enumerate([x for x in raw.splitlines() if x.strip() and '本轮重点解决' not in x],1)}
sp=importlib.util.spec_from_file_location('prior_authoring',H.parent/'opening-narrative-integration-20261026/authoring.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
units=[dict(unit_id='WORLD-IN',duration_seconds=3.0,beat_function='establish',objective='建立社会常态：人群正常过街，出租车等待，没有先演第二次异常',open_state='人群在斑马线上',close_state='仍有人从容过街',shot_scale='full',camera_treatment='static',camera_intent='以人的通行行为建立社会尺度；候选A使用，B省去以比较悬念速度',visible_change='人流从一侧进入另一侧，出租车等候'),*old.UNITS,dict(unit_id='WORLD-OUT',duration_seconds=6.0,beat_function='payoff',objective='回到没有察觉缺席的城市；交通继续，片名留在撤去的画面边界',open_state='同一stock机位的后续时刻，行人继续走离',close_state='车辆正常通过，完整片名跨越影像与暗场',shot_scale='full',camera_treatment='static',camera_intent='尾声以观众已经知道的缺席反衬旁人照常通行；不是城中又有人被删除',visible_change='行人自然离开、出租车驶过，城市不中断，单次编辑平面改变揭示片名')]
units[3]={**units[3],'close_state':'近景中女人仍平静地通话，不再叠片名','objective':'完整保留司机与女人的一问一答及无察觉表演','camera_intent':'维持已验证原生切镜与完整声音窗口，仅撤去旧片名'}
units=[{**u,'constraint_ids':list(quotes),'transition_out':'end' if i==len(units)-1 else 'cut'} for i,u in enumerate(units)]
groups={k:[] for k in ['must_happen','must_not_happen','preferred_performance','timing_targets','acceptable_variation']}
for k,q in quotes.items():
 g='must_not_happen' if '未经授权' in q or '重要范围' in q else 'acceptable_variation' if '不强制固定' in q else 'preferred_performance' if '最终以观众' in q else 'must_happen';groups[g].append(dict(intent_item_id=k))
coverage=dict(schema_version='4',request=dict(creative_input_kind='direction',creative_input_evidence=raw,creative_constraints=[dict(constraint_id=k,scope='global',source_text=q) for k,q in quotes.items()],target_duration_seconds=658/24,coverage_strategy='multi_shot',strategy_source='agent_directed',director_decision_rationale='A城市日常→完整事件→城市照常；B事件→城市照常。素材地理/天气缺口不关闭宏观世界目标；固定核心以保护用户已经认可的事件。',strategy_request_evidence=None,director_skill='open-video'),coverage_units=units,intent_items=[dict(intent_item_id=k,statement=q,origin='explicit_user',source_refs=[dict(source_hash=digest,locator='creative-input.txt#'+k,intent_item_id=k,quote=q,origin='explicit_user')],related_intent_ids=['intent-09'] if k=='intent-08' else []) for k,q in quotes.items()],intent_groups=groups)
direction=VisualDirection(content_kind='drama',typography='完整中文片名跨活动影像和撤去的画面边界；不压人物近景或说话，不装成路面实体，不用随机缺笔/glitch。',palette='保留核心雨夜蓝黑与钨光，不强行用调色掩盖stock干地及非同地点；正式版仍须同雨夜摄影。',layout='城市中人群的日常→两人同框与遮挡后的空位→平静回答→城市人流与车辆继续；文字只在最后介入。',style='真人摄影目标保留；核心已认可叙事与其现有CG质感分开裁决，AI生成标识保留。',holistic='观众记住关系被抹去、旁人不知情、世界继续；听完四句对白及原音乐发展。预演不是最终艺术通过。')
contract=FinalOutputContract(goal_id='shizhen-world-title',goal_version='1',user_goal=raw,requirements=tuple([FinalOutputRequirement(requirement_id=k,observable=q,proof='human' if '最终以观众' in q else 'evaluator') for k,q in quotes.items()]+list(visual_requirements(direction))))
def write(p,v):(H/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
write('director-coverage.json',coverage);write('visual-direction.json',direction.model_dump(mode='json'));write('final-output-contract.json',contract.model_dump(mode='json'))
def ref(p):return dict(path=p,sha256=hashlib.sha256((H/p).read_bytes()).hexdigest())
write('goal-binding.json',dict(schema_version='creative-goal-binding/1',authority='development_only',creative_input=ref('creative-input.txt'),coverage=ref('director-coverage.json'),final_output_contract=ref('final-output-contract.json'),bindings=[dict(intent_item_id=k,constraint_ids=[k],unit_ids=[u['unit_id'] for u in units],requirement_ids=[k]) for k in quotes]))
print('Full goal chain written; compiled during first render, not claimed pre-sealed before that render')
