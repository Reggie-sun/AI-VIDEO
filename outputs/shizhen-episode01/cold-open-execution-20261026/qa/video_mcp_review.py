"""Explicit exact-MP4 project-local MCP call, including one bound audio observation."""
from pathlib import Path
import asyncio,json,sys,base64
from audio_review import Q,ROOT
async def main():
 from mcp import ClientSession
 from mcp.client.stdio import StdioServerParameters,stdio_client
 label,file=sys.argv[1:];path=Path(file).resolve(strict=True);seal=json.loads((Q/(label+'-binding.json')).read_text());out=Q/(label+'-mcp.json');assert not out.exists()
 env={'PYTHONPATH':str(ROOT/'src'),'VIDEO_MCP_AUDIO_RUNTIME_FACTORY':'ai_video_mcp.audio_operator:build_runtime','VIDEO_MCP_AUDIO_OPERATOR_UNIT':seal['unit_dir'],'VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256':seal['intent_sha256'],'VIDEO_MCP_AUDIO_MEDIA_ROOT':str(ROOT),'VIDEO_MCP_AUDIO_MODEL_ID':'gemini-3.8-flash','VIDEO_MCP_FRAME_WIDTH':'1280'}
 server=StdioServerParameters(command=sys.executable,args=['-m','ai_video_mcp'],env=env)
 args={'video_path':str(path),'extract_frames':True,'frame_interval':0.25,'max_frames':100 if label=='CO-A3' else 40,'transcribe_audio':False,'detect_scenes':True,'understand_audio':True,'expected_sha256':seal['source_sha256']}
 (Q/(label+'-mcp-request.json')).write_text(json.dumps(args,indent=2)+'\n')
 async with stdio_client(server) as (r,w):
  async with ClientSession(r,w) as session:
   await session.initialize();result=(await session.call_tool('video_analyze',args)).model_dump(mode='json')
 with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 data=result.get('structuredContent')
 if data is None:
  data=json.loads(next(x['text'] for x in result['content'] if x['type']=='text'))
 frames=data.get('keyframes',data.get('frames',{}));folder=Q/(label+'-frames');folder.mkdir(exist_ok=False)
 def visit(node):
  if isinstance(node,dict):
   if 'base64' in node and 'timestamp_seconds' in node:
    p=folder/(f"frame-{node['timestamp_seconds']:06.3f}.jpg");p.write_bytes(base64.b64decode(node['base64']));return {k:v for k,v in node.items() if k!='base64'}
   return {k:visit(v) for k,v in node.items()}
  if isinstance(node,list):return [visit(x) for x in node]
  return node
 summary=visit(data);(Q/(label+'-summary.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
