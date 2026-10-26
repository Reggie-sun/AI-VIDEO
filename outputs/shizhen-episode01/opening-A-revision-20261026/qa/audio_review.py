"""Bounded development audio observations through the existing stdio MCP."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import asyncio,json,hashlib,sys,os
from ai_video_mcp.audio_understanding import prepare_audio_request
from ai_video_mcp.audio_operator import prepare_operator_unit
from ai_video_mcp.tools.audio_understand import _audio_bytes
ROOT=Path.cwd();Q=Path(__file__).resolve().parent
async def execute(path,seal):
 from mcp import ClientSession
 from mcp.client.stdio import StdioServerParameters,stdio_client
 env={'PYTHONPATH':str(ROOT/'src'),'VIDEO_MCP_AUDIO_RUNTIME_FACTORY':'ai_video_mcp.audio_operator:build_runtime','VIDEO_MCP_AUDIO_OPERATOR_UNIT':seal['unit_dir'],'VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256':seal['intent_sha256'],'VIDEO_MCP_AUDIO_MEDIA_ROOT':str(ROOT),'VIDEO_MCP_AUDIO_MODEL_ID':'gemini-3.8-flash'}
 server=StdioServerParameters(command=sys.executable,args=['-m','ai_video_mcp'],env=env)
 async with stdio_client(server) as (reader,writer):
  async with ClientSession(reader,writer) as session:
   await session.initialize()
   result=await session.call_tool('audio_understand',{'media_path':str(path),'expected_sha256':seal['source_sha256'],'execute':True})
   return result.model_dump(mode='json')
def main():
 action,label,file=sys.argv[1:];path=Path(file).resolve(strict=True);base=Q/label
 if action=='prepare':
  raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
  if path.suffix=='.wav':audio,offset=raw,0.0
  else:
   from types import SimpleNamespace
   audio,offset=_audio_bytes(SimpleNamespace(data=raw),path.suffix)
  p=prepare_audio_request(audio_bytes=audio,source_sha256=sha,source_size_bytes=len(raw),audio_start_seconds=offset)
  now=datetime.now(timezone.utc);seal=prepare_operator_unit(base,media_path=path,prepared=p,authorization_reference='user-resume-standalone-opening-and-title-review-20261026',issued_at=now,expires_at=now+timedelta(minutes=30))
  (Q/(label+'-binding.json')).write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps({'label':label,'preview':p.preview(),'development_only':True}))
 elif action=='execute':
  seal=json.loads((Q/(label+'-binding.json')).read_text());out=Q/(label+'-result.json');assert not out.exists()
  result=asyncio.run(execute(path,seal))
  with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
  print(json.dumps(result,ensure_ascii=False))
 else:raise ValueError(action)
if __name__=='__main__':main()
