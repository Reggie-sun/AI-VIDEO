"""Small local NCC measurements; observations only, no render or Product state."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
files=sorted(ROOT.glob('playback-*.jpg'))
frames=[np.asarray(Image.open(p).convert('L'),dtype=np.float32) for p in files]
points={'bg-city':(440,140),'bg-lamp':(345,235),'bg-bridge':(145,342),'bg-window':(920,120),'body-left-shoulder':(470,360),'body-collar':(594,289),'body-redline':(740,260)}
rows=[]
for file,frame in zip(files,frames):
 row={'file':file.name,'time':float(file.stem.split('-')[-1]),'tracks':{}}
 for name,(x,y) in points.items():
  half=12;search=16
  template=frames[0][y-half:y+half,x-half:x+half];template=template-template.mean()
  region=frame[y-half-search:y+half+search,x-half-search:x+half+search]
  windows=np.lib.stride_tricks.sliding_window_view(region,template.shape)
  n=template.size;sw=windows.sum(axis=(-1,-2));sw2=(windows*windows).sum(axis=(-1,-2))
  denom=np.sqrt(np.maximum(sw2-sw*sw/n,0))*np.sqrt((template*template).sum())
  corr=np.divide((windows*template).sum(axis=(-1,-2)),denom,out=np.full(denom.shape,-1.0,dtype=np.float32),where=denom>1e-5)
  iy,ix=np.unravel_index(np.argmax(corr),corr.shape)
  row['tracks'][name]={'dx':int(ix-search),'dy':int(iy-search),'ncc':float(corr[iy,ix])}
 good=[(points[name],track) for name,track in row['tracks'].items() if name.startswith('bg-') and track['ncc']>0.8]
 if len(good)>=3:
  a=[];b=[]
  for (x,y),track in good:a.extend([[x,1,0],[y,0,1]]);b.extend([x+track['dx'],y+track['dy']])
  fit=np.linalg.lstsq(np.array(a),np.array(b),rcond=None)[0]
  row['background_similarity']={'scale':float(fit[0]),'translate_x':float(fit[1]),'translate_y':float(fit[2]),'fit_rmse_px':float(np.sqrt(np.mean((np.array(a)@fit-np.array(b))**2)))}
  for name,(x,y) in points.items():
   if name.startswith('body-'):
    track=row['tracks'][name];track['residual_dx']=float(track['dx']-((fit[0]-1)*x+fit[1]));track['residual_dy']=float(track['dy']-((fit[0]-1)*y+fit[2]))
 rows.append(row)
output={'method':'local 24x24 grayscale NCC over +/-16px at 960x540 normal-speed capture; bg similarity least squares, no learned detector','limitations':['Integer-pixel match quantization; local perspective and image synthesis may violate a global similarity model.','Residuals establish independent local motion, not a physiological cause.','NCC scale fit is background image change; it cannot distinguish an actual dolly from a digital zoom.'],'rows':rows}
(ROOT/'motion-measurements.json').write_text(json.dumps(output,indent=2)+'\n')
for row in rows:
 print(json.dumps({'t':row['time'],'bg':row.get('background_similarity'),'body':{k:{q:round(v,3) if isinstance(v,float) else v for q,v in x.items()} for k,x in row['tracks'].items() if k.startswith('body-')}},ensure_ascii=False))
