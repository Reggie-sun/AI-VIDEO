from pathlib import Path
import subprocess,json,numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent
F='/home/reggie/.config/jianji/tools/ffmpeg/bin/ffmpeg'
def read(p):
 b=subprocess.check_output([F,'-v','error','-i',str(p),'-an','-vf','scale=480:270','-pix_fmt','rgb24','-f','rawvideo','pipe:1'])
 return np.frombuffer(b,np.uint8).reshape(-1,270,480,3)
a=read(H.parents[1]/'variant-A/失帧-独立开场-A-结构预演.mp4')
core=read(H.parents[2]/'opening-narrative-integration-20261026/focus-002/失帧-两位-关键事件重剪-002.mp4')
m=np.mean(np.abs(a[1:].astype(np.float32)-a[:-1].astype(np.float32)),axis=(1,2,3))
rows=[]
for name,ids in [('first-cut',list(range(64,77))),('event-seam',list(range(304,337)))]:
 board=Image.new('RGB',(960,((len(ids)+2)//3)*200),'#171b1d');d=ImageDraw.Draw(board)
 for i,n in enumerate(ids):
  x=i%3*320;y=i//3*200;im=Image.fromarray(a[n]);im=im.resize((320,180));board.paste(im,(x,y));d.text((x+4,y+181),f'{n/24:.3f}s f{n} delta {m[n-1]:.2f}',fill='white')
 board.save(H/(name+'.jpg'))
 rows.append({'region':name,'frames':[{'frame':n,'t':n/24,'delta_previous':float(m[n-1]),'exact_duplicate':bool(np.array_equal(a[n],a[n-1]))} for n in ids]})
# Difference of the newly rendered event vs prior core, ignoring tiny codec loss.
comparisons=[]
for n in range(304,337):
 c=n-72
 scores=[(k,float(np.mean(np.abs(a[n].astype(float)-core[k].astype(float))))) for k in range(max(0,c-4),min(len(core),c+5))]
 comparisons.append({'A_frame':n,'expected_core_frame':c,'best_core_match':min(scores,key=lambda x:x[1]),'scores':scores})
(H/'decoded-analysis.json').write_text(json.dumps({'A_frames':len(a),'regions':rows,'core_comparison':comparisons},indent=2))
print(json.dumps({'regions':[{**r,'frames':sorted(r['frames'],key=lambda x:x['delta_previous'],reverse=True)[:5]} for r in rows],'duplicates_12to14':[i for i in range(288,336) if np.array_equal(a[i],a[i-1])]},indent=2))
