"""Bounded evidence: protected source pixels and unchanged P4 sound, not art scoring."""
from pathlib import Path
from PIL import Image
import hashlib,json,subprocess
import numpy as np
h=Path(__file__).resolve().parent.parent
new=h/'variant-B4/失帧-Fusion片名试片-B4.mp4'
old=h/'variant-B3/失帧-Fusion片名试片-B3.mp4'
rows=[]
for n in (0,24,48,72,96,120,143):
 a=np.asarray(Image.open(h/f'render-B3/title_{n:04}.png').convert('RGB'),dtype=np.int16)
 b=np.asarray(Image.open(h/f'render-B4/title_{n:04}.png').convert('RGB'),dtype=np.int16)
 # Original woman + right street; no new graphical image treatment expected here.
 d=np.abs(a[120:850,1050:1920]-b[120:850,1050:1920])
 rows.append(dict(frame=n,max_channel_difference=int(d.max()),mean_channel_difference=float(d.mean())))
ff='/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg'
def pcm(p):return subprocess.check_output([ff,'-v','error','-i',str(p),'-map','0:a:0','-f','s16le','-ac','2','-ar','48000','-'])
a,b=pcm(new),pcm(old)
r=dict(candidate_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),protected_roi=[1050,120,1920,850],protected_roi_comparison=rows,decoded_audio_identical_to_B3=a==b,pcm_sha256=hashlib.sha256(a).hexdigest(),boundaries='Pixel/PCM preservation only; does not prove perceived depth, optical-flow quality, human hearing or artistic acceptance')
(h/'qa/preservation-B4.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(r,ensure_ascii=False))
