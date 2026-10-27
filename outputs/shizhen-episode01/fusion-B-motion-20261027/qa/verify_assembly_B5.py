from pathlib import Path
import json,hashlib,subprocess
import numpy as np
H=Path(__file__).resolve().parent.parent
ff='/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg'
out=H/'variant-ASSEMBLY-B5/失帧-独立开场-ASSEMBLY-B5.mp4'
base=H.parent/'opening-A-revision-20261026/variant-R3/失帧-独立开场-空位片名-R3.mp4'
b5=H/'variant-B5/失帧-Fusion片名试片-B5.mp4'
def video(p):
 b=subprocess.check_output([ff,'-v','error','-i',str(p),'-an','-vf','scale=192:108','-pix_fmt','rgb24','-f','rawvideo','-'])
 return np.frombuffer(b,np.uint8).reshape(-1,108,192,3).astype(np.int16)
a=video(out);e=video(base)[:417];t=video(b5)
def diff(x,y):
 d=np.abs(x-y);return dict(mean_absolute_8bit_error=float(d.mean()),frame_mean_error_max=float(d.mean(axis=(1,2,3)).max()))
def audio(p):
 b=subprocess.check_output([ff,'-v','error','-i',str(p),'-vn','-f','f32le','-ac','2','-ar','48000','-'])
 return np.frombuffer(b,np.float32).reshape(-1,2)
x=audio(out)[:1122000];expected=np.concatenate([audio(base)[:834000],audio(b5)[:288000]])
d=x-expected
r=dict(output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),frames=len(a),event_frames=417,title_frames=144,event_preservation=diff(a[:417],e),title_preservation=diff(a[417:],t),audio_same_window_reference_samples=len(expected),audio_rms_error=float(np.sqrt(np.mean(d*d))),audio_correlation=float(np.corrcoef(x.reshape(-1),expected.reshape(-1))[0,1]),audio_peak=float(np.abs(x).max()),input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [base,b5]},boundaries='Lossy re-encode comparison; no new actions/text/sound authored. Metrics do not replace listening or whole-film artistic review.')
(H/'qa/preservation-assembly-B5.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
