"""Parent findings over the archived, actual MCP response and exact fetched source."""
from pathlib import Path
from types import SimpleNamespace
import asyncio,json,hashlib
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.models import ToolIdentity
from ai_video.production.generation_evaluation import GenerationEvaluationSource,GenerationObservation
from ai_video_mcp.generation_feedback import review_generation_attempt
Q=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A3';A='shizhen-CO-A3-qualification-001';SHA='750326c44ba58ecd0093c52ff8c7337cb8942f4e3efd9bd61634d3cfe3b119cf'
F={'relationship': '两名同事先通话与提醒湿路，后态罗敏独自自然候车，未增加角色关系或记忆保留者。', 'action': '货车从左向右经过，7.5–9s完整遮住两名人物，10–12s揭出原棚左侧空位和右侧罗敏；未见走开、上车或透明消失。车轮/路面仍在画面底部，未字面遮满每一个像素，功能性的角色遮挡成立。', 'identity': 'FAIL:高峥从0秒起没有参考1的褐色挎包，因而没有满足既定各自包保持；罗敏的脸、雨衣、黑包和左手手机左耳保持。不能以消失后无遗留包倒签消失前包存在。', 'camera': '固定站棚全景完成两位到一位，约15.25s才切同侧罗敏胸上近景；空位先可读。MCP场景阈值报告1不覆盖实际89帧可见剪切。', 'performance': '女先报两位，男听后回应，女随后看他；后态她无寻找或惊恐，近景平常回答一位，口型归女声。原速human观感待审。', 'sound': '真实音频理解四轮语义及顺序齐全，声线平常；它把路滑提醒与电话核对都归同一Speaker2，且背景只列引擎/车内/衣料，不能据此证明电话声处理、近棚雨声或不同男性身份可辨，相关声音目标NOT_EVALUATED。', 'story-scope': '一次前一夜的失踪，角色未记忆高峥；不解释规则或泄露S01/终场反转，无鬼怪、字幕、准确数字或片名。', 'art': '89帧内保持成年原创CG与同一雨棚冷暖光，近景罗敏面部发丝及湿衣材质统一，未变真人或蜡像。'}
class ArchivedActualMCP:
 async def call_tool(self,name,args):
  assert name=='video_analyze' and args['expected_sha256']==SHA and args['understand_audio'] is True
  doc=json.loads((Q/'CO-A3-mcp.json').read_bytes());payload=json.loads(doc['content'][0]['text']);assert payload['video_path']==args['video_path'] and payload['audio_understanding']['source_sha256']==SHA
  return SimpleNamespace(model_dump=lambda **_:doc)
def judge(ctx):
 return (GenerationEvaluationSource(request_hash=ctx.request.request_input_hash,artifact_sha256=SHA,rubric_hash=ctx.recipe.rubric_hash,qa_policy_content_hash=ctx.qa_policy.content_hash,evaluator=ToolIdentity(name='codex-explicit-evaluator',version='current-session'),proof='analyzer',observations=tuple(GenerationObservation(requirement_id=k,verdict=('FAIL' if k=='identity' else 'NOT_EVALUATED' if k=='sound' else 'PASS'),observation=v) for k,v in F.items()),analysis_evidence=ctx.analysis),)
async def main():
 l=load_production_project(ROOT/'project.yaml');state=next(a.video_generation_state for a in l.manifest.attempts if a.attempt_id==A);p=ROOT/state.fetch_receipt.artifact_path;assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA
 assert not (Q/'CO-A3-post-media-gate.json').exists()
 result=await review_generation_attempt(committer=ProductionStateCommitter(ROOT),attempt_id=A,session=ArchivedActualMCP(),adjudicate=judge,understand_audio=True)
 (Q/'CO-A3-canonical-diagnosis.json').write_text(json.dumps(result.model_dump(mode='json'),ensure_ascii=False,indent=2)+'\n')
 gate={'shot_id':'CO-A3','attempt_id':A,'artifact_path':str(p),'artifact_sha256':SHA,'verdict':'FAIL','proof':'analyzer','required_findings':[{'requirement_id':k,'verdict':('FAIL' if k=='identity' else 'NOT_EVALUATED' if k=='sound' else 'PASS'),'reason':v,'evidence_ref':'CO-A3-mcp.json'} for k,v in F.items()],'source_frame_count':529,'observed_terminal_state':'罗敏同侧胸上近景，左手手机贴左耳，平常听电话','human_acceptance':'NOT_EVALUATED','production_activation':False,'next_component':'STOP new generation. Known prop failure: repair through existing accepted prefix, preserve full raw and history; no raw acceptance or Production activation','actual_new_video_submits':3}
 (Q/'CO-A3-post-media-gate.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'raw_gate':'FAIL','human_acceptance':'NOT_EVALUATED','next_component':'EDITORIAL_REPAIR_ONLY','diagnosis':result.model_dump(mode='json')},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
