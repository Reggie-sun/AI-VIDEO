"""Seal and execute one exact song-listening call through the existing trusted MCP operator."""
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ai_video_mcp.audio_operator import prepare_operator_unit
from ai_video_mcp.audio_understanding import prepare_audio_request


ROOT = Path('/home/reggie/vscode_folder/AI-VIDEO')
SOURCE = ROOT / 'outputs/ai-city-takeover/ep01/audio/ace-step-music-repair-20261031-r4/complete-source-preview/IRIS-01-Music-and-Hook-preview.wav'
EXPECTED = '9e007d2a8d0b8a5a826c5ce1e77e4e2c3729059eece57edb03ba727be79522d8'
FOLDER = ROOT / 'outputs/ai-city-takeover/ep01/audio/iris-google-listening-20261031'


def save(name, data):
    with (FOLDER / name).open('x') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def unpack(result):
    texts = [x.text for x in result.content if x.type == 'text']
    if len(texts) != 1:
        raise RuntimeError('Expected one structured MCP response')
    return json.loads(texts[0])


async def main():
    if FOLDER.exists():
        raise SystemExit('Existing listening scope: inspect state; never replay')
    data = SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise SystemExit('Selected audio changed')
    prepared = prepare_audio_request(audio_bytes=data, source_sha256=EXPECTED,
        source_size_bytes=len(data), model_id='gemini-3.8-flash')
    now = datetime.now(timezone.utc)
    FOLDER.mkdir()
    save('preview.json', prepared.preview())
    save('scope.json', {'schema':'iris-listening-scope/1','authorization_reference':'user-20261031-iris-google-env-listening',
        'user_quote':'我记得google有key，.env','source_sha256':EXPECTED,
        'purpose':'Blind actual-audio observation, then compare music and voice to the existing song brief',
        'submit_limit':1,'operator_upper_bound_USD':0.05,'upper_bound_is_price_or_settlement':False,
        'key_route':'Existing injected dotenv-first exact supplier; no values exposed',
        'media_generation':False,'ACE_generation_count_unchanged':10,
        'new_music_generation_or_Product_state_writes':0,
        'UNKNOWN':'STOP and inspect existing outcome, no replay or remint',
        'actual_cost':'Pending settlement, not established by internal ceiling',
        'host_direct_audio_hearing':'UNAVAILABLE; Gemini model observations will be attributed'})
    receipt = prepare_operator_unit(FOLDER / 'operator-01', media_path=SOURCE, prepared=prepared,
        authorization_reference='user-20261031-iris-google-env-listening',
        issued_at=now, expires_at=now+timedelta(minutes=10), upper_bound_microunits=50_000)
    save('operator-binding.json',receipt)
    params = StdioServerParameters(command=sys.executable,args=['-m','ai_video_mcp'],cwd=str(ROOT),
        env={'PYTHONPATH':str(ROOT/'src'),'PYTHON_DOTENV_DISABLED':'1',
             'VIDEO_MCP_AUDIO_MEDIA_ROOT':str(ROOT),'VIDEO_MCP_AUDIO_MODEL_ID':'gemini-3.8-flash',
             'VIDEO_MCP_AUDIO_RUNTIME_FACTORY':'ai_video_mcp.audio_operator:build_runtime',
             'VIDEO_MCP_AUDIO_OPERATOR_UNIT':receipt['unit_dir'],
             'VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256':receipt['intent_sha256']})
    dispatched = False
    try:
        with (FOLDER/'server-stderr.log').open('w') as errors:
            async with stdio_client(params,errlog=errors) as (read,write):
                async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=90)) as session:
                    await session.initialize()
                    inventory = await session.list_tools()
                    if not any(t.name=='audio_understand' for t in inventory.tools):
                        raise RuntimeError('Expected audio tool absent')
                    save('mcp-handshake.json',{'tool_count':len(inventory.tools),'audio_understand_present':True})
                    args={'media_path':str(SOURCE),'expected_sha256':EXPECTED,'execute':False}
                    check=await session.call_tool('audio_understand',args)
                    checked=unpack(check)
                    if check.isError or checked.get('preview')!=prepared.preview():
                        save('mcp-preview-mismatch.json',checked)
                        raise RuntimeError('Fresh MCP preview does not match sealed audio')
                    save('mcp-preview.json',checked)
                    save('dispatch-intent.json',{'at_utc':datetime.now(timezone.utc).isoformat(),
                        'tool':'audio_understand','source_sha256':EXPECTED,'execute':True,'calls':1})
                    dispatched=True
                    args['execute']=True
                    result=await session.call_tool('audio_understand',args)
                    response=unpack(result)
                    save('mcp-result.json',{'isError':bool(result.isError),'result':response})
                    print(json.dumps({'event':'actual_audio_analysis_returned','isError':bool(result.isError),
                        'evidence':str(FOLDER/'mcp-result.json'),'result':response},ensure_ascii=False),flush=True)
    except Exception as exc:
        # Errors from the canonical owner are retained in its outcome; never print exception payloads.
        save('client-failure.json',{'exception_type':type(exc).__name__,'dispatch_started':dispatched,
            'action':'Inspect operator consume/outcome; no automatic retry'})
        print(json.dumps({'event':'client_failure','exception_type':type(exc).__name__,
            'dispatch_started':dispatched,'automatic_retries':0}),flush=True)
        return
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=EXPECTED:
        raise RuntimeError('Source drift after analysis')


if __name__=='__main__':
    asyncio.run(main())
