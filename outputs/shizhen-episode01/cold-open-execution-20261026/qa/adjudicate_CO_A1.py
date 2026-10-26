"""Parent findings over the archived, actual MCP response and exact fetched source."""
from pathlib import Path
from types import SimpleNamespace
import asyncio,json,hashlib
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.models import ToolIdentity
from ai_video.production.generation_evaluation import GenerationEvaluationSource,GenerationObservation
from ai_video_mcp.generation_feedback import review_generation_attempt
Q=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A1';A='shizhen-CO-A1-qualification-001';SHA='b42b27040a62c6c303079e9f582534ec5d7ff7dcf9fb6c88c781de53dcde02fd'
F={
'relationship':'0–5.5s两名普通成年同事同框；女先通话，男先听见后看向湿路及同伴提醒，女在4–5s向男投去倾听目光；没有被动空镜铺垫。',
'action':'5.5s普通配送货车车头从左入近前景，6–7.25s车厢连续遮住人和棚，7.5–8s湿金属侧板满幅；无上下车、走开、透明消失，原位和包维持至遮挡。',
'identity':'33帧实际样本内成熟眼镜褐衣男在左、短卷发墨绿雨衣女在右，两包、左手手机左耳保持；实际原图与样本一致，未复用主角脸。',
'camera':'固定同一机位，遮挡前出口及脚边完整可读，货车持续向右经过；无推拉、硬切或黑屏，MCP亦报告1场景；末段是连续动态金属车身而非灰卡溶解。',
'performance':'女0–2.5s通话口型，男3–5s说话口型，女听见后才4–5s转头看他；自然重心与目光，正常实时动作，未见预知恐惧或人物僵住。此为analyzer层判断，human审美待验。',
'sound':'真实Gemini音频观察为女清楚日常呼叫、男成熟低声平稳提醒，两轮顺序及湿路轮胎/车流/引擎环境成立，未观测额外对白或配乐。Gemini对女声地点短语有不确定性；同bytes独立本地Whisper medium补证为“师父 我们在站里 两位 / 让他别急 路滑”，师父/师傅为转写同音异字，不据此误判发音。结合33帧口型角色对应判叙事声音通过，不宣称人类听审或sample级对齐。',
'story-scope':'遮挡前始终两位，未实际消失、出入、烟化；无剧情字幕、片名和准确时钟数字。平台左上AI生成标记保留，不混同剧情字幕。',
'art':'实际33帧内两名成年原创CG人物、同一站棚湿布玻璃金属、细束发丝与克制皮肤高光保持；冷雨城/暖棚灯统一。未见换成真人照片或蜡脸，用户审美仍待原速审看。'}
class ArchivedActualMCP:
 async def call_tool(self,name,args):
  assert name=='video_analyze' and args['expected_sha256']==SHA and args['understand_audio'] is True
  doc=json.loads((Q/'CO-A1-mcp.json').read_bytes());payload=json.loads(doc['content'][0]['text']);assert payload['video_path']==args['video_path'] and payload['audio_understanding']['source_sha256']==SHA
  return SimpleNamespace(model_dump=lambda **_:doc)
def judge(ctx):
 return (GenerationEvaluationSource(request_hash=ctx.request.request_input_hash,artifact_sha256=SHA,rubric_hash=ctx.recipe.rubric_hash,qa_policy_content_hash=ctx.qa_policy.content_hash,evaluator=ToolIdentity(name='codex-explicit-evaluator',version='current-session'),proof='analyzer',observations=tuple(GenerationObservation(requirement_id=k,verdict='PASS',observation=v) for k,v in F.items()),analysis_evidence=ctx.analysis),)
async def main():
 l=load_production_project(ROOT/'project.yaml');state=next(a.video_generation_state for a in l.manifest.attempts if a.attempt_id==A);p=ROOT/state.fetch_receipt.artifact_path;assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA
 assert not (Q/'CO-A1-post-media-gate.json').exists()
 result=await review_generation_attempt(committer=ProductionStateCommitter(ROOT),attempt_id=A,session=ArchivedActualMCP(),adjudicate=judge,understand_audio=True)
 (Q/'CO-A1-canonical-diagnosis.json').write_text(json.dumps(result.model_dump(mode='json'),ensure_ascii=False,indent=2)+'\n')
 gate={'shot_id':'CO-A1','attempt_id':A,'artifact_path':str(p),'artifact_sha256':SHA,'verdict':'PASS','proof':'analyzer','required_findings':[{'requirement_id':k,'verdict':'PASS','reason':v,'evidence_ref':'CO-A1-mcp.json'} for k,v in F.items()],'source_frame_count':193,'observed_terminal_state':'满幅灰白湿金属车厢仍向右经过，棚与人完全被遮住','human_acceptance':'NOT_EVALUATED','production_activation':False,'next_component':'CO-A2 eligible for exact preparation; no implicit submit','actual_new_video_submits':1}
 (Q/'CO-A1-post-media-gate.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'raw_gate':'PASS','human_acceptance':'NOT_EVALUATED','next_component':'CO-A2','diagnosis':result.model_dump(mode='json')},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
