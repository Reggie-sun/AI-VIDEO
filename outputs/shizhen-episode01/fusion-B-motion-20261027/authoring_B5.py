from pathlib import Path
import json,hashlib,importlib.util
from ai_video.production.final_output_contracts import FinalOutputContract,FinalOutputRequirement
from ai_video.production.visual_quality import VisualDirection,visual_requirements
H=Path(__file__).resolve().parent
raw=(H/'review-creative-input.txt').read_text();digest=hashlib.sha256(raw.encode()).hexdigest()
quotes={f'intent-{i:02}':v for i,v in enumerate([x for x in raw.splitlines() if x.strip() and '本轮重点解决' not in x],1)}
sp=importlib.util.spec_from_file_location('prior_authoring',H.parent/'opening-narrative-integration-20261026/authoring.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
units=[dict(unit_id='WORLD-IN',duration_seconds=4.5,beat_function='establish',objective='待制作：同一道路的城市生活收束到实际站棚，不使用异地街景占位',open_state='雨夜车流沿道路正常运行，站棚能在同一空间定位',close_state='两人所在站棚的朝向与原CO-A1入口一致',shot_scale='full',camera_treatment='static',camera_intent='沿实际道路关系收束，素材缺口保持未完成，不插入当前MP4',visible_change='车流、道路与站棚逐步形成可读关系'),*old.UNITS,dict(unit_id='CO-TAIL',duration_seconds=6.0,beat_function='payoff',objective='同一空位远景密度逐渐退层，雨玻璃细节与灯光保留，字形由底片局部亮度与细节逐渐显露；没有左右擦除，幸存者继续通话',open_state='站棚空位与右侧通话的女人',close_state='B负片片名在空位稳定，保留运动底片，右侧人仍正常',shot_scale='full',camera_treatment='static',camera_intent='留住观众记得而角色不记得的空间；不是新一次现实改写',visible_change='片名在原空位显现，真实立框窄幅遮挡，雨夜空间保留；不添加扫光')]
for u in units:
 if u['unit_id']=='CO-A3':u.update(duration_seconds=167/24,objective='从实际近景起点进入完整司机问答，省去跳姿态的重复全景',open_state='近景女人听电话',close_state='平静应答后继续听电话',camera_intent='以明确景别变化接近问答，保留四句对白及自然间隔')
units=[{**u,'constraint_ids':list(quotes),'transition_out':'end' if i==len(units)-1 else 'cut'} for i,u in enumerate(units)]
groups={k:[] for k in ['must_happen','must_not_happen','preferred_performance','timing_targets','acceptable_variation']}
for k,q in quotes.items():
 g='must_not_happen' if '未经授权' in q or '重要范围' in q else 'acceptable_variation' if '不强制固定' in q else 'preferred_performance' if '最终以观众' in q else 'must_happen';groups[g].append(dict(intent_item_id=k))
coverage=dict(schema_version='4',request=dict(creative_input_kind='direction',creative_input_evidence=raw,creative_constraints=[dict(constraint_id=k,scope='global',source_text=q) for k,q in quotes.items()],target_duration_seconds=489/24+4.5+3,coverage_strategy='multi_shot',strategy_source='agent_directed',director_decision_rationale='继续A的空间因果方向；宏观同地素材缺失，不填入MP4。局部版本修复同构图跳变并以同站台片名收束；不将局部完成当作宏观或真人目标完成。',strategy_request_evidence=None,director_skill='open-video'),coverage_units=units,intent_items=[dict(intent_item_id=k,statement=q,origin='explicit_user',source_refs=[dict(source_hash=digest,locator='review-creative-input.txt#'+k,intent_item_id=k,quote=q,origin='explicit_user')],related_intent_ids=['intent-09'] if k=='intent-08' else []) for k,q in quotes.items()],intent_groups=groups)
direction=VisualDirection(content_kind='drama',typography='Fusion 片名置于原空位，右侧幸存者继续通话；已选B字形、异基线与异尺度，负片密度分层显影，保留六秒阶段与终态停留，修正平灰覆盖；图像频率分离近似前后影像层次，并非真实深度分割；失与帧分处细立柱两侧，上下错落，主笔画不被立柱切断，无横向擦除或随机glitch，源AI标识保留。',palette='保留核心雨夜蓝黑与钨光，不强行用调色掩盖stock干地及非同地点；正式版仍须同雨夜摄影。',layout='目标为同地宏观→完整异常→同站台尾声；当前只交尾段六秒 Fusion 显影过程，底片明确光流慢镜、声音原速；核心事件保存在旧版中，不将局部试片标整片通过。',style='真人摄影目标保留；核心已认可叙事与其现有CG质感分开裁决，AI生成标识保留。',holistic='观众记住关系被抹去、旁人不知情、世界继续；听完四句对白及原音乐发展。预演不是最终艺术通过。')
contract=FinalOutputContract(goal_id='shizhen-world-title',goal_version='1',user_goal=raw,requirements=tuple([FinalOutputRequirement(requirement_id=k,observable=q,proof='human' if '最终以观众' in q else 'evaluator') for k,q in quotes.items()]+list(visual_requirements(direction))))
def write(p,v):(H/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
write('director-coverage.json',coverage);write('visual-direction.json',direction.model_dump(mode='json'));write('final-output-contract.json',contract.model_dump(mode='json'))
def ref(p):return dict(path=p,sha256=hashlib.sha256((H/p).read_bytes()).hexdigest())
write('goal-binding.json',dict(schema_version='creative-goal-binding/1',authority='development_only',creative_input=ref('review-creative-input.txt'),coverage=ref('director-coverage.json'),final_output_contract=ref('final-output-contract.json'),bindings=[dict(intent_item_id=k,constraint_ids=[k],unit_ids=[u['unit_id'] for u in units],requirement_ids=[k]) for k in quotes]))
print('Full goal chain written; compiled during first render, not claimed pre-sealed before that render')
