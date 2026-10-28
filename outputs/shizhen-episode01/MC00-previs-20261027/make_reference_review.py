"""Package exact static renders and a measured plan; no video generation."""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
DEST=ROOT/'referces/shizhen/macro-opening-20261027/MC00-city-layout-20261027'
DEST.mkdir(parents=True,exist_ok=True)
audit=json.loads((OUT/'scene-audit-v2.json').read_text())
samples=json.loads((OUT/'camera-samples-v2.json').read_text())
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def ft(n):return ImageFont.truetype(font,n)
im=Image.new('RGB',(1600,1400),'#121d2a')
d=ImageDraw.Draw(im)
d.text((65,40),'MC00 城市空间与相机路线',font=ft(42),fill='#eef6ff')
d.text((65,105),'新设计 · 米制平面图 · 只供静态参考审看 · 尚未生成视频',font=ft(24),fill='#aebed2')
scale=8
def xy(x,y):return (480+x*scale,720-y*scale)
def rect(bb,fill,outline):
    a=xy(bb['min_m'][0],bb['max_m'][1]);b=xy(bb['max_m'][0],bb['min_m'][1]);d.rectangle((a,b),fill=fill,outline=outline,width=3)
for x in range(-40,31,10):d.line((xy(x,-72),xy(x,65)),fill='#203044',width=1)
for y in range(-70,66,10):d.line((xy(-40,y),xy(32,y)),fill='#203044',width=1)
d.rectangle((xy(-21,65),xy(-7,-72)),fill='#293d50')
d.rectangle((xy(-40,40.5),xy(32,27.5)),fill='#293d50')
for y in range(-70,65,6):d.line((xy(-14,y),xy(-14,y+3)),fill='#7c91a3',width=2)
colors={'ENV_eave_building':('#634d44','#d6a17a'),'ENV_residence':('#634e3b','#dfb17a'),'ENV_shelter_roof':('#21666b','#72e6e0'),'ENV_gate':('#535279','#b6b0ef'),'PRP_winch_plinth':('#6b5f43','#e8d695'),'PRP_return_base':('#6b5f43','#e8d695'),'PRP_control':('#6b5f43','#e8d695')}
for name,obj in audit['objects'].items():rect(obj,*colors[name])
d.line((xy(-3.5,-.15),xy(7,-3.18)),fill='#dce6ef',width=3)
d.line((xy(7,-2.82),xy(3,3.8)),fill='#dce6ef',width=3)
points=[xy(*r['position_m'][:2]) for r in samples['samples']]
d.line(points,fill='#fdc64b',width=5)
for t,pos,aim in samples['nodes']:
    p=xy(*pos[:2]);d.ellipse((p[0]-6,p[1]-6,p[0]+6,p[1]+6),fill='#fff2c9')
    d.text((p[0]+10,p[1]-10),f'{t:g}s',font=ft(18),fill='#ffe7a1')
labels=[(-36,-64,'屋檐建筑',(-34,-59)),(5,-36,'旧住宅',(1,-30)),(10,-17,'站棚',(-5.2,-9)),(12,9,'市政铁门',(3.2,4)),(-38,11,'主路',(-14,11))]
for x,y,label,target in labels:
    p=xy(x,y);q=xy(*target);d.line((p,q),fill='#9ab0c6',width=2);d.text((p[0],p[1]-30),label,font=ft(23),fill='white')
d.text((855,230),'路线与责任',font=ft(32),fill='#f2f6fc')
notes=['① 屋檐外侧起幅，城市留一角','② 横移越过北侧外转角','③ 沿同一主路缓弧下降','④ 住宅、站棚为沿途定位','⑤ 街侧减速，交给设备与工人','','黄色线：相机位置设计','浅色双线：绞盘—滑轮—门','工人不按停，异常留给MC01','','20秒为当前轨迹设计','未渲染动态，未固定模型时长','遮挡次序与速度仍待连续预演','','地理和尺寸为新设计','市政观察侧取自已认可第0帧','B6人物、事件、原声保持原样']
for i,line in enumerate(notes):d.text((855,290+i*43),line,font=ft(23),fill='#cbd9e9')
d.text((65,1330),'北 ↑   1格=10米    起幅高度18.3米 → 末态2.6米    28mm固定焦段',font=ft(24),fill='#aebed2')
im.save(DEST/'00-city-plan.png')
items=[('01-city-overview.png','views-v2/city-overview.png','城市体块总览，不是正式美术'),('02-eave-start.png','views-v2/camera-0001.png','屋檐起幅与转角遮挡'),('03-city-reveal.png','views-v2/camera-0121.png','横移后城市与同一主路'),('04-residence-and-shelter.png','views-v2/camera-0193.png','下降阶段住宅及站棚位置'),('05-site-approach.png','views-v2/camera-0337.png','街面接近与设备落点'),('06-site-end.png','views-v2/camera-0480.png','同侧市政末态候选，不是精确匹配'),('07-accepted-MC01-entry.png','anchor/MC01-frame000.png','已认可市政第0帧，比较基准')]
refs=[]
for name,source,role in items:
    src=OUT/source;dst=DEST/name;shutil.copyfile(src,dst)
    refs.append({'file':name,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'source':str(src.relative_to(ROOT)),'role':role,'copy':'EXACT_BYTES','production_binding':False})
refs.insert(0,{'file':'00-city-plan.png','sha256':hashlib.sha256((DEST/'00-city-plan.png').read_bytes()).hexdigest(),'source':str((OUT/'scene-audit-v2.json').relative_to(ROOT)),'role':'由保存的blend实际包围盒与相机采样绘制的技术地图','production_binding':False})
(DEST/'references.json').write_text(json.dumps({'status':'STATIC_REFERENCE_CANDIDATE','new_city_geography':True,'video_generated':False,'model_submission':False,'items':refs},ensure_ascii=False,indent=2))
cards=''.join(f'<figure><a href="{r["file"]}"><img src="{r["file"]}" loading="lazy"></a><figcaption>{r["role"]}</figcaption></figure>' for r in refs)
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MC00 城市空间参考</title><style>body{margin:0;background:#111a25;color:#e9f0fa;font:17px/1.6 system-ui,sans-serif}main{max-width:1300px;margin:35px auto;padding:0 24px}h1{font-size:30px}p{color:#b9c7d8}section{display:grid;grid-template-columns:1fr 1fr;gap:24px}figure{margin:0;background:#1b2939;border-radius:10px;overflow:hidden}figure:first-child{grid-column:1/-1}img{width:100%;display:block}figure:first-child img{max-height:850px;object-fit:contain}figcaption{padding:15px}@media(max-width:800px){section{display:block}figure{margin-bottom:20px}}</style><main><h1>MC00：城市空间与静态参考</h1><p>尚未生成视频。除已认可市政第0帧外，均为本地Blender空间候选。用于审布局、观察侧、起幅与末态；不证明运动、最终美术、模型服从或接点通过。点击图片查看原尺寸。</p><section>'''+cards+'''</section><p>末态保持工人／控制盒在左、门在右，右前滑轮与双索可解释；与MC01仍有景别及门透视差异，尚未签精确接点匹配。住宅和站棚的连续显露次序、速度、声音及人工接受仍待后续验证。</p></main></html>'''
(DEST/'index.html').write_text(html)
print(json.dumps({'references':len(refs),'root':str(DEST.relative_to(ROOT)),'video_generated':False}))
