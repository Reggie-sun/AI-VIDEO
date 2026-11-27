"""blank.py SRC DST x0 y0 x1 y1 [...]: local fix — inside each box, replace fine detail (pseudo-text marks) with a heavy blur of the same region, 3 px feathered edge."""
import sys, numpy as np, cv2
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('RGB')).astype(np.float32); b=list(map(int,sys.argv[3:]))
blur=cv2.GaussianBlur(a,(0,0),7)
m=np.zeros(a.shape[:2],np.float32)
for i in range(0,len(b),4): x0,y0,x1,y1=b[i:i+4]; m[y0:y1,x0:x1]=1
m=cv2.GaussianBlur(m,(7,7),0)[...,None]
Image.fromarray((a*(1-m)+blur*m).clip(0,255).astype(np.uint8)).save(sys.argv[2])
