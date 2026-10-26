"""One bounded exact-mix audio observation via the existing qualified operator seam."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import asyncio
import hashlib
import json
import sys
from ai_video_mcp.audio_understanding import prepare_audio_request
from ai_video_mcp.audio_operator import prepare_operator_unit
from ai_video_mcp.tools.audio_understand import _audio_bytes

ROOT=Path.cwd();HERE=Path(__file__).resolve().parent


async def observe(path,seal):
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters,stdio_client
    env={'PYTHONPATH':str(ROOT/'src'),
         'VIDEO_MCP_AUDIO_RUNTIME_FACTORY':'ai_video_mcp.audio_operator:build_runtime',
         'VIDEO_MCP_AUDIO_OPERATOR_UNIT':seal['unit_dir'],
         'VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256':seal['intent_sha256'],
         'VIDEO_MCP_AUDIO_MEDIA_ROOT':str(ROOT),'VIDEO_MCP_AUDIO_MODEL_ID':'gemini-3.8-flash'}
    server=StdioServerParameters(command=sys.executable,args=['-m','ai_video_mcp'],env=env)
    async with stdio_client(server) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            result=await session.call_tool('audio_understand',dict(media_path=str(path),
                expected_sha256=seal['source_sha256'],execute=True))
            return result.model_dump(mode='json')


def main():
    action=sys.argv[1]
    path=HERE/'失帧-开场重构-动态预演-002.mp4'
    binding=HERE/'qa/exact-mix-audio-binding.json'
    if action=='prepare':
        raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        audio,offset=_audio_bytes(SimpleNamespace(data=raw),path.suffix)
        prepared=prepare_audio_request(audio_bytes=audio,source_sha256=digest,source_size_bytes=len(raw),audio_start_seconds=offset)
        now=datetime.now(timezone.utc)
        seal=prepare_operator_unit(HERE/'qa/exact-mix-audio-unit',media_path=path,prepared=prepared,
            authorization_reference='user-shizhen-opening-reconstruction-20261026-audio-review',
            issued_at=now,expires_at=now+timedelta(minutes=30))
        with binding.open('x') as f:json.dump(seal,f,indent=2)
        (HERE/'qa/exact-mix-audio-preview.json').write_text(json.dumps(prepared.preview(),indent=2))
        print(json.dumps(prepared.preview(),ensure_ascii=False))
    elif action=='execute':
        resultpath=HERE/'qa/exact-mix-audio-result.json'
        if resultpath.exists():raise FileExistsError('One call only; never retry a completed or unknown unit')
        seal=json.loads(binding.read_text())
        result=asyncio.run(observe(path,seal))
        with resultpath.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print(json.dumps(result,ensure_ascii=False))
    else:raise ValueError('prepare or execute')


if __name__=='__main__':main()
