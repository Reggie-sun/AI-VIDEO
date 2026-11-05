"""Blind Gemini listening of the opening of each Suno take, one sealed operator unit per take (no replay, no retry).

  PYTHONPATH=src PYTHON_DOTENV_DISABLED=1 /home/reggie/.local/share/video-mcp/venv/bin/python \
      outputs/ai-city-takeover/ep01/v2/song-suno/listen_takes.py T1 T2 ...

Same route as ep01/audio/iris-google-listening-20261031/launcher.py: prepare_audio_request -> prepare_operator_unit
(10-minute window, internal ceiling USD 0.05, not a price) -> fresh stdio MCP with the trusted operator factory ->
offline preview must equal the sealed request -> one execute=true call. The analysed media is a <=110 s mono
24 kHz WAV window of the take (the tool accepts <=120 s); its derivation is recorded. Any failure stops the run;
an existing unit folder is never replayed. Credentials stay inside the injected supplier; nothing is printed.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ai_video_mcp.audio_operator import prepare_operator_unit
from ai_video_mcp.audio_understanding import prepare_audio_request

ROOT = Path('/home/reggie/vscode_folder/AI-VIDEO')
HERE = ROOT / 'outputs/ai-city-takeover/ep01/v2/song-suno'
LISTEN = HERE / 'listen'
AUTH = 'user-20261104-suno-take-selection'
QUOTE = '我都觉得可以,不考虑时常,你得从观众和质量角度考虑,和人物背景符合'
WINDOW_S = 110


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(folder, name, data):
    with (folder / name).open('x') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def unpack(result):
    texts = [x.text for x in result.content if x.type == 'text']
    if len(texts) != 1:
        raise RuntimeError('Expected one structured MCP response')
    return json.loads(texts[0])


async def listen(label, take):
    folder = LISTEN / label
    if folder.exists():
        raise SystemExit(f'{label}: existing listening scope; inspect it, never replay')
    src = HERE / 'takes' / take['wav']
    if sha(src) != take['wav_sha256']:
        raise SystemExit(f'{label}: take changed since fetch')
    (LISTEN / 'windows').mkdir(parents=True, exist_ok=True)
    window = LISTEN / 'windows' / f'{label}-0-{WINDOW_S}.wav'
    if not window.exists():
        subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', str(src), '-t', str(WINDOW_S), '-ac', '1', '-ar', '24000',
                        '-c:a', 'pcm_s16le', str(window)], check=True)
    data = window.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    prepared = prepare_audio_request(audio_bytes=data, source_sha256=digest, source_size_bytes=len(data), model_id='gemini-3.8-flash')
    now = datetime.now(timezone.utc)
    folder.mkdir()
    save(folder, 'preview.json', prepared.preview())
    save(folder, 'scope.json', {'schema': 'iris-listening-scope/1', 'authorization_reference': AUTH, 'user_quote': QUOTE,
        'take': {'label': label, 'clip_id': take['id'], 'wav': str(src.relative_to(ROOT)), 'wav_sha256': take['wav_sha256']},
        'window': {'path': str(window.relative_to(ROOT)), 'sha256': digest, 'start_s': 0, 'duration_s': WINDOW_S,
                   'derivation': f'ffmpeg -t {WINDOW_S} -ac 1 -ar 24000 pcm_s16le from the take WAV'},
        'purpose': 'Blind observation of voice and delivery in the opening (intro, verse 1, pre-chorus, chorus 1) to rank takes for audience, quality and fit with IRIS',
        'submit_limit': 1, 'operator_upper_bound_USD': 0.05, 'upper_bound_is_price_or_settlement': False,
        'key_route': 'Existing injected dotenv-first exact supplier; no values exposed',
        'UNKNOWN': 'STOP and inspect existing outcome, no replay or remint', 'actual_cost': 'Pending settlement',
        'host_direct_audio_hearing': 'UNAVAILABLE; Gemini model observations will be attributed'})
    receipt = prepare_operator_unit(folder / 'operator-01', media_path=window, prepared=prepared, authorization_reference=AUTH,
                                    issued_at=now, expires_at=now + timedelta(minutes=10), upper_bound_microunits=50_000)
    save(folder, 'operator-binding.json', receipt)
    params = StdioServerParameters(command=sys.executable, args=['-m', 'ai_video_mcp'], cwd=str(ROOT),
        env={'PYTHONPATH': str(ROOT / 'src'), 'PYTHON_DOTENV_DISABLED': '1',
             'VIDEO_MCP_AUDIO_MEDIA_ROOT': str(ROOT), 'VIDEO_MCP_AUDIO_MODEL_ID': 'gemini-3.8-flash',
             'VIDEO_MCP_AUDIO_RUNTIME_FACTORY': 'ai_video_mcp.audio_operator:build_runtime',
             'VIDEO_MCP_AUDIO_OPERATOR_UNIT': receipt['unit_dir'],
             'VIDEO_MCP_AUDIO_OPERATOR_INTENT_SHA256': receipt['intent_sha256']})
    dispatched = False
    try:
        with (folder / 'server-stderr.log').open('w') as errors:
            async with stdio_client(params, errlog=errors) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=120)) as session:
                    await session.initialize()
                    inventory = await session.list_tools()
                    if not any(t.name == 'audio_understand' for t in inventory.tools):
                        raise RuntimeError('Expected audio tool absent')
                    save(folder, 'mcp-handshake.json', {'tool_count': len(inventory.tools), 'audio_understand_present': True})
                    args = {'media_path': str(window), 'expected_sha256': digest, 'execute': False}
                    check = await session.call_tool('audio_understand', args)
                    checked = unpack(check)
                    if check.isError or checked.get('preview') != prepared.preview():
                        save(folder, 'mcp-preview-mismatch.json', checked)
                        raise RuntimeError('Fresh MCP preview does not match sealed audio')
                    save(folder, 'mcp-preview.json', checked)
                    save(folder, 'dispatch-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'tool': 'audio_understand',
                                                         'source_sha256': digest, 'execute': True, 'calls': 1})
                    dispatched = True
                    args['execute'] = True
                    result = await session.call_tool('audio_understand', args)
                    response = unpack(result)
                    save(folder, 'mcp-result.json', {'isError': bool(result.isError), 'result': response})
    except Exception as exc:
        save(folder, 'client-failure.json', {'exception_type': type(exc).__name__, 'dispatch_started': dispatched,
                                             'action': 'Inspect operator consume/outcome; no automatic retry'})
        print(json.dumps({'label': label, 'event': 'client_failure', 'exception_type': type(exc).__name__, 'dispatch_started': dispatched}), flush=True)
        return False
    if sha(window) != digest:
        raise RuntimeError('Window drift after analysis')
    obs = response.get('observation') or response.get('result') or response
    print(json.dumps({'label': label, 'event': 'returned', 'isError': bool(result.isError), 'keys': sorted(obs.keys()) if isinstance(obs, dict) else None}, ensure_ascii=False), flush=True)
    return not result.isError


async def main():
    takes = {f"T{t['n']}": t for t in json.loads((HERE / 'takes/takes.json').read_text())['takes']}
    for label in sys.argv[1:]:
        if not await listen(label, takes[label]):
            print(json.dumps({'stopped_at': label, 'automatic_retries': 0}), flush=True)
            return


if __name__ == '__main__':
    asyncio.run(main())
