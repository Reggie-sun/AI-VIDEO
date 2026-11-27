"""desat.py SRC DST x0 y0 x1 y1 [...]: local fix — set the boxes to their own luma (gray, unlit), feathered 3 px."""
import sys, numpy as np, cv2
from PIL import Image
src,dst=sys.argv[1],sys.argv[2]; a=np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
mask=np.zeros(a.shape[:2],np.float32); b=list(map(int,sys.argv[3:]))
for i in range(0,len(b),4): x0,y0,x1,y1=b[i:i+4]; mask[y0:y1,x0:x1]=1
mask=cv2.GaussianBlur(mask,(7,7),0)[...,None]
y=(a@np.array([0.299,0.587,0.114],np.float32))[...,None]*np.ones(3,np.float32)
Image.fromarray((a*(1-mask)+y*0.9*mask).clip(0,255).astype(np.uint8)).save(dst)
