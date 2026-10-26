"""Parent findings over the archived, actual MCP response and exact fetched source."""
from pathlib import Path
from types import SimpleNamespace
import asyncio,json,hashlib
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.models import ToolIdentity
from ai_video.production.generation_evaluation import GenerationEvaluationSource,GenerationObservation
from ai_video_mcp.generation_feedback import review_generation_attempt
Q=Path(__file__).resolve().parent;ROOT=Path.cwd()/'runs/shizhen-episode01-jimeng25-20261025-001/cold-open-execution/CO-A2';A='shizhen-CO-A2-qualification-001';SHA='0dabb72c98edcc3550c91d2e23292740044a193bee7079f8751bb0fb43a2060c'
F={'relationship': '同机位车尾揭开左侧空位，右侧罗敏普通候车，无寻找或异常认知。', 'action': '0–1.25s满幅湿金属侧板仍向右运动，1.5–3.5s车尾从左向右揭开原棚，3.75–4s完全驶离，左侧人和包均不在；无人出入或上车。', 'identity': '17帧样本中右侧罗敏的短卷发、墨绿雨衣、黑包和左手手机左耳保持，无高峥或多余包再出现。', 'camera': '同一固定中远景，从满幅车厢到同一站棚恢复，连续向右尾缘揭示，出口与脚边可读，无溶解、切镜或黑屏。', 'performance': '罗敏自然闭口听电话、正常站立，无向左寻找、惊恐或困惑。此为analyzer样本观察，不代替human原速审看。', 'sound': '真实音频理解无可辨人声或音乐，背景为机械/引擎低滚动声；同bytes声学补证1秒窗RMS由-29.07降到-35.39dBFS、峰值-17.6dBFS，支持车声自然远离且没有全局归零。环境在雨夜视觉中成立；工具未单独列出棚雨滴声，不声称逐种foley已人类听审。', 'story-scope': '只揭出已改写后的一位，不展示人走开、上车、透明或烟化，不留高峥衣物及包，无新规则、字幕、片名或准确数字。', 'art': '17帧内同一成年原创CG罗敏、站棚玻璃金属和湿路材质及冷暖光保持，无照片真人化或蜡脸。'}
class ArchivedActualMCP:
 async def call_tool(self,name,args):
  assert name=='video_analyze' and args['expected_sha256']==SHA and args['understand_audio'] is True
  doc=json.loads((Q/'CO-A2-mcp.json').read_bytes());payload=json.loads(doc['content'][0]['text']);assert payload['video_path']==args['video_path'] and payload['audio_understanding']['source_sha256']==SHA
  return SimpleNamespace(model_dump=lambda **_:doc)
def judge(ctx):
 return (GenerationEvaluationSource(request_hash=ctx.request.request_input_hash,artifact_sha256=SHA,rubric_hash=ctx.recipe.rubric_hash,qa_policy_content_hash=ctx.qa_policy.content_hash,evaluator=ToolIdentity(name='codex-explicit-evaluator',version='current-session'),proof='analyzer',observations=tuple(GenerationObservation(requirement_id=k,verdict='PASS',observation=v) for k,v in F.items()),analysis_evidence=ctx.analysis),)
async def main():
 l=load_production_project(ROOT/'project.yaml');state=next(a.video_generation_state for a in l.manifest.attempts if a.attempt_id==A);p=ROOT/state.fetch_receipt.artifact_path;assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA
 assert not (Q/'CO-A2-post-media-gate.json').exists()
 result=await review_generation_attempt(committer=ProductionStateCommitter(ROOT),attempt_id=A,session=ArchivedActualMCP(),adjudicate=judge,understand_audio=True)
 (Q/'CO-A2-canonical-diagnosis.json').write_text(json.dumps(result.model_dump(mode='json'),ensure_ascii=False,indent=2)+'\n')
 gate={'shot_id':'CO-A2','attempt_id':A,'artifact_path':str(p),'artifact_sha256':SHA,'verdict':'PASS','proof':'analyzer','required_findings':[{'requirement_id':k,'verdict':'PASS','reason':v,'evidence_ref':'CO-A2-mcp.json'} for k,v in F.items()],'source_frame_count':97,'observed_terminal_state':'同一站棚固定全景，罗敏在右自然听电话，左侧人和包不在','human_acceptance':'NOT_EVALUATED','production_activation':False,'next_component':'User-requested one-call whole-event CO-A3; preserve split sources as history','actual_new_video_submits':2}
 (Q/'CO-A2-post-media-gate.json').write_text(json.dumps(gate,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'raw_gate':'PASS','human_acceptance':'NOT_EVALUATED','next_component':'CO-A3','diagnosis':result.model_dump(mode='json')},ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
