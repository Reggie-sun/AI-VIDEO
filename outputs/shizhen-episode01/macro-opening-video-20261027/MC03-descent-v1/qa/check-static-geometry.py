"""Read-only frame-region translation comparisons; no media repair or Provider call."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
Q=Path(__file__).resolve().parent
regions={'upper_wall_pipe':(40,80,400,580),'upper_window':(610,0,940,130),'foreground_rail':(100,820,620,1030),'lower_stair_right':(1510,935,1680,1060),'lower_stair_center':(1130,940,1330,1060),'lower_wall':(1710,310,1860,650)}
def arr(n):return np.asarray(Image.open(Q/'frames'/f'frame-{n:02}.png').convert('L'),dtype=np.float32)
frames={n:arr(n) for n in [11,13,14,15,16,17]};out=[]
for a,b in [(11,13),(13,15),(15,17),(14,16),(16,17)]:
 row={'pts':[0.5*(a-1),0.5*(b-1)],'regions':{}}
 for name,(x0,y0,x1,y1) in regions.items():
  ref=frames[a][y0+20:y1-20,x0+20:x1-20];ref=ref-ref.mean();den=np.linalg.norm(ref);best=(-1,None,None)
  for dy in range(-12,13):
   for dx in range(-12,13):
    cur=frames[b][y0+20+dy:y1-20+dy,x0+20+dx:x1-20+dx];cur=cur-cur.mean();score=float((ref*cur).sum()/(den*np.linalg.norm(cur)+1e-6))
    if score>best[0]:best=(score,dx,dy)
  row['regions'][name]={'best_ncc':round(best[0],5),'shift_dx_px':best[1],'shift_dy_px':best[2]}
 out.append(row)
(Q/'static-geometry-comparison.json').write_text(json.dumps({'source_sha256':'326e4fcb83b4bfcd232a3efefab44bd52f0caef6c7be2b3242a0042cca41e43e','method':'Region normalized cross-correlation translation, +-12px; excludes known subject in selected regions. Not motion acceptance or camera calibration.','regions':regions,'comparisons':out},indent=2)+'\n')
print(json.dumps(out))
