"""Upstream music-source editing only. Never a final-film timeline or Product writer."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import soundfile as sf


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    p = Path(sys.argv[1]).resolve()
    intent = json.loads(p.read_text())
    if sha(__file__) != intent['runner_sha256']:
        raise SystemExit('Source editor changed')
    arrays = {}
    rate = intent['sample_rate']
    for name, source in intent['sources'].items():
        if sha(source['path']) != source['sha256']:
            raise SystemExit('Source changed')
        a, r = sf.read(source['path'], always_2d=True)
        if r != rate or a.shape[1] != 2:
            raise SystemExit('Expected exact source PCM stereo sample rate')
        arrays[name] = a
    def cut(name, start, end):
        return arrays[name][round(start * rate):round(end * rate)].copy()
    def join(parts, overlap):
        out = parts[0]
        for part in parts[1:]:
            n = round(overlap * rate)
            alpha = np.linspace(0, 1, n)[:, None]
            out = np.concatenate([out[:-n], out[-n:] * (1-alpha) + part[:n] * alpha, part[n:]])
        return out
    def clips(items):
        return [cut(c['source'], c['in_seconds'], c['out_seconds']) for c in items]
    lead = join(clips(intent['spoken_lead']), .005)
    hook = join(clips(intent['sung_phrase']), .008)
    pause = np.zeros((round(intent['phrase_pause_seconds'] * rate), 2))
    outro = join(clips(intent['spoken_outro']), .005)
    voice = np.concatenate([lead, pause, hook, pause, hook, pause, outro])
    count = round(intent['duration_seconds'] * rate)
    if len(voice) > count:
        raise SystemExit('Complete source voice does not fit; never crop words or speed up')
    voice = np.pad(voice, ((0, count-len(voice)),(0,0)))
    music = join(clips(intent['instrumental_edit']), .015)
    if len(music) < count:
        raise SystemExit('Music source does not cover source audition')
    music = music[:count]
    fade = round(.35 * rate)
    music[-fade:] *= np.linspace(1,0,fade)[:,None]
    # Static relative gain. Neither stem is sent back through a speech-preserving model.
    voice *= 10 ** (intent['voice_gain_db'] / 20)
    music *= 10 ** (intent['music_gain_db'] / 20)
    out = voice + music
    peak_scale = min(1., intent['peak_ceiling'] / float(abs(out).max()))
    out *= peak_scale
    folder = p.parent
    output = folder / 'IRIS-01-Music-and-Hook-preview.wav'
    if output.exists():
        raise SystemExit('Keep existing source audition; use a new scoped revision')
    sf.write(output, out, rate, subtype='PCM_16')
    sf.write(folder / 'voice-source-edit.wav', voice, rate, subtype='PCM_16')
    sf.write(folder / 'instrumental-source-edit.wav', music, rate, subtype='PCM_16')
    result = {'success':True,'outputs':[{'path':str(output),'sha256':sha(output),'bytes':output.stat().st_size}],
        'source_editor_sha256':sha(__file__),'source_edit_intent_sha256':sha(p),
        'operation':'Upstream song source editing and linear summing; no Product state or final-film composition',
        'duration_seconds':len(out)/rate,'voice_duration_before_padding':(len(lead)+2*len(hook)+len(outro)+3*len(pause))/rate,
        'phrase_seconds':len(hook)/rate,'peak_scale':peak_scale,'no_speed_change':True,
        'human_hearing':'NOT_EVALUATED','remote_generation_calls':0,'new_ACE_generations':0}
    (folder / 'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()
