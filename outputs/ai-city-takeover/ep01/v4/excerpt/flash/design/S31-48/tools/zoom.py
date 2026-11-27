import sys
from PIL import Image
# zoom.py out.jpg img x0 y0 x1 y1 [img x0 y0 x1 y1 ...] ; crops at native res, scaled to 400 tall, side by side
out=sys.argv[1]; a=sys.argv[2:]; tiles=[]
for i in range(0,len(a),5):
    im=Image.open(a[i]).convert('RGB'); x0,y0,x1,y1=map(int,a[i+1:i+5]); c=im.crop((x0,y0,x1,y1))
    tiles.append(c.resize((int(c.width*400/c.height),400),Image.LANCZOS))
W=sum(t.width+6 for t in tiles); s=Image.new('RGB',(W,400)); x=0
for t in tiles: s.paste(t,(x,0)); x+=t.width+6
s.save(out,quality=90)
