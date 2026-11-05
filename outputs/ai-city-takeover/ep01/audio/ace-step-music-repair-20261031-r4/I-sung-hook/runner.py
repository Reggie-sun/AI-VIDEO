"""One-use local ACE music-source generation, separate from final-film composition."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_bound(item):
    p = Path(item['path'])
    if sha(p) != item['sha256']:
        raise SystemExit('Bound input changed: ' + p.name)
    return json.loads(p.read_text())


def main():
    ip = Path(sys.argv[1]).resolve()
    intent = json.loads(ip.read_text())
    folder = ip.parent
    if (folder / 'consume.json').exists():
        raise SystemExit('Already consumed; inspect outcome, never replay')
    if sha(__file__) != intent['runner_sha256']:
        raise SystemExit('Runner identity changed')
    series = read_bound(intent['series'])
    ordinal = intent['ordinal']
    if not series['previous_used'] < ordinal <= series['cumulative_ceiling']:
        raise SystemExit('Finite unit ceiling exceeded')
    for prior in intent['predecessors']:
        result = read_bound(prior)
        if result.get('success') is not True or len(result.get('outputs', [])) != 1:
            raise SystemExit('Predecessor has no known successful source')
        for output in result['outputs']:
            if sha(output['path']) != output['sha256']:
                raise SystemExit('Predecessor source changed')
    original = read_bound(series['original_intent'])['fields']
    if hashlib.sha256(original['lyrics'].encode()).hexdigest() != series['original_lyrics_sha256']:
        raise SystemExit('Original lyrics identity changed')
    inputs = read_bound(intent['inputs'])
    if inputs['config']['batch_size'] != 1 or inputs['params']['thinking']:
        raise SystemExit('Source count or no-LM selection changed')
    if inputs['params']['task_type'] != 'text2music' or inputs['params']['src_audio']:
        raise SystemExit('This source experiment must not retain speech-reference latents')
    if intent['role'] == 'instrumental':
        if inputs['params']['lyrics'] != '[Instrumental]' or not inputs['params']['instrumental']:
            raise SystemExit('Instrumental source requires literal instrumental lyrics marker')
    elif intent['role'] == 'sung_hook':
        hook = original['lyrics'].split('[Chorus - sung, cold, restrained]\n')[1].split('\n\n')[0]
        if inputs['params']['lyrics'].removeprefix('[Chorus]\n').strip() != hook.strip():
            raise SystemExit('Sung hook source must retain exact original words and punctuation')
    else:
        raise SystemExit('Unsealed source role')
    root = Path(intent['runtime_root'])
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != intent['code_sha']:
        raise SystemExit('Pinned official code changed')
    weights = read_bound(intent['weights_manifest'])
    if not weights['all_files_verified'] or weights['revision'] != intent['weights_revision']:
        raise SystemExit('Pinned model verification missing')
    model = root / 'checkpoints' / intent['model']
    for item in weights['files']:
        file = model / item['path']
        synced = root / 'acestep/models/sft' / item['path']
        expected = sha(synced) if file.suffix == '.py' and synced.is_file() else item['actual_sha256']
        if sha(file) != expected:
            raise SystemExit('Model weights or pinned synchronized code changed')
    import torch
    from loguru import logger
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music
    from acestep.constants import TASK_INSTRUCTIONS
    logger.remove()
    logger.add(sys.stderr, level='WARNING')
    if not torch.cuda.is_available():
        raise SystemExit('CUDA unavailable')
    if inputs['params']['instruction'] != TASK_INSTRUCTIONS['text2music']:
        raise SystemExit('Wrong native task instruction')
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    print(json.dumps({'event':'initializing','label':intent['label'],'role':intent['role']}), flush=True)
    dit = AceStepHandler()
    message, ready = dit.initialize_service(project_root=str(root), config_path=intent['model'],
        device='cuda', use_flash_attention=False, compile_model=False, offload_to_cpu=False,
        offload_dit_to_cpu=False, quantization=None, use_mlx_dit=False)
    if not ready:
        raise RuntimeError('Initialization failed: ' + str(message))
    params, config = GenerationParams(**inputs['params']), GenerationConfig(**inputs['config'])
    text, lyric = dit.build_dit_inputs(params.task_type, params.instruction, params.caption, params.lyrics,
        {'bpm':params.bpm,'duration':params.duration,'keyscale':params.keyscale,'timesignature':params.timesignature}, params.vocal_language)
    counts = [len(dit.text_tokenizer(t, truncation=False).input_ids) for t in (text, lyric)]
    if counts[0] > 256 or counts[1] > 2048:
        raise SystemExit('Inputs would be truncated')
    (folder / 'token-preflight.json').write_text(json.dumps({'caption':counts[0],'lyrics':counts[1],'truncated':False}, indent=2)+'\n')
    consume = {'intent_sha256':sha(ip),'ordinal':ordinal,'role':intent['role'],
        'consumed_at_utc':datetime.now(timezone.utc).isoformat(),'params':params.to_dict(),
        'config':config.to_dict(),'automatic_retries':0,'remote_generation_calls':0}
    with (folder / 'consume.json').open('x') as stream:
        json.dump(consume, stream, ensure_ascii=False, indent=2)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({'event':'generation_started','ordinal':ordinal}), flush=True)
    result = generate_music(dit, None, params, config, save_dir=str(folder))
    outputs = [{'path':str(Path(a['path']).resolve()),'sha256':sha(a['path']),
        'bytes':Path(a['path']).stat().st_size} for a in result.audios]
    receipt = {'success':result.success,'error':result.error,'status_message':result.status_message,
        'outputs':outputs,'ordinal':ordinal,'role':intent['role'],'intent_sha256':sha(ip),
        'elapsed_seconds':round(time.monotonic()-start,3),
        'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated(),
        'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'human_listening':'NOT_EVALUATED','production_state_writes':0,'remote_generation_calls':0}
    (folder / 'result.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'event':'finished','success':result.success,'outputs':outputs}), flush=True)
    if not result.success or len(outputs) != 1:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
