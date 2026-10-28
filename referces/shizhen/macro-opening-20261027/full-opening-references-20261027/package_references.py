"""Task-local static reference catalogue. Does not render or submit video."""
from pathlib import Path
import hashlib
import html
import json
import os
import shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE=ROOT/'referces/shizhen/macro-opening-20261027'
CITY=BASE/'MC00-photoreal-20261027'
records=[]


def item(shot,name,source,title,basis,frame=None):
    source=Path(source)
    target=HERE/name
    if source.resolve()!=target.resolve():shutil.copyfile(source,target)
    row={'shot':shot,'file':name,'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'title':title,'basis':basis,'copy':'EXACT_BYTES','production_binding':False}
    if frame is not None:row.update(source_frame=frame,source_fps=24)
    records.append(row)


for name,title in [('02-eave-start-v1.png','屋檐滴雨与遮挡起幅'),('01-city-reveal-v1.png','横移后城市展开'),('03-descent-v2.png','沿路下降与地标定位'),('04-site-end-v1.png','市政正常末态')]:
    item('MC00','MC00-'+name,CITY/name,title,'本窗口既有写实候选；高差与连续运镜待验证')
item('MC01','MC01-normal.png',HERE/'municipal-normal-000.png','起始状态','已认可市政原片第0帧，不重生成',0)
item('MC01','MC01-control-off.png',HERE/'municipal-source-01.png','控制断开后，工作灯已灭','已认可市政原片第40帧；静态图不证明先后动作',40)
item('MC01','MC01-limit.png',HERE/'municipal-source-02.png','门到限位，工人观察','已认可市政原片第103帧',103)
item('MC02','MC02-force-before.png',HERE/'municipal-source-03.png','连接处近景前态','已认可市政原片第104帧',104)
item('MC02','MC02-force-after.png',HERE/'municipal-source-04.png','持续受力后的连接处','已认可市政原片第163帧；变化由原视频证明',163)
item('MC03','MC03-descent-side-v2.png',HERE/'MC03-descent-side-v2.png','斜侧下行，人物侧脸、直梯与窄窗门前平台','本轮新空间修订候选；仍在梯段中间，不签精确起止或动态修复')
item('MC03','MC03-arrival-reuse.png',BASE/'action-sequences-04/A2-arrival.png','既有下平台到达状态','旧静态候选，只供到达站位；不作为新直梯结构母图')
item('MC04','MC04-before-contact.png',BASE/'action-sequences-04/B0-before-contact.png','到达后，尚未触门','既有静态场次候选')
item('MC04','MC04-contact-closed.png',BASE/'door-push-repair-03/L02-push-closed.png','右手接触关闭把手','复用门向修订03，非原早期外拉图')
item('MC04','MC04-half-open.png',BASE/'action-sequences-04/B1-contact-push.png','右手向内推门，中间态','既有静态候选；门角度与接触动态待验')
item('MC04','MC04-reveal-open.png',BASE/'door-push-repair-03/L03-push-open.png','门后灭火器与旧卡箍印显露','既有门向修订03候选，不证明空间异常已动态成立')
item('MC05','MC05-reaction.png',BASE/'repair-02/L04.png','同侧扶门，核对而非解释','既有反应候选；右手、门角度及动作接点需原速核对')
item('MC06','MC06-wide-reuse.png',BASE/'T01.png','站棚远景，两人仍在','既有T01候选，不是B6实际第0帧')
item('MC06','MC06-B6-entry-comparison.png',HERE/'B6-exact-first-frame.png','与B6实际首帧比较','保护文件第0帧；保留原AI来源标识',0)
item('B6','B6-entry.png',HERE/'B6-exact-first-frame.png','完整B6的实际入点','原片复用，21.875秒、525帧，声画与片名原样保留',0)
item('SUPPORT','Dong-Wenhui-identity.png',ROOT/'referces/shizhen/character-packs-20261027/dong-wenhui/identity/identity-v1.png','董文慧身份母图','身份候选；不采用第二集scene-v3服装')
item('SUPPORT','straight-stair-geometry.png',BASE/'stair-structure-white-20261027/stair-structure-white-v1.png','独立直梯结构依据','结构辅助，不能直接当人物动作首帧')
manifest={'scope':'Full independent cold-opening static reference catalogue, MC00-MC06 and protected B6','status':'CANDIDATES_FOR_USER_REVIEW','items':records,'new_image_calls_this_scope':3,'new_video_calls':0,'all_input_and_generated_images_only_candidates':True,'media_gate_not_closed':True,'retained_not_selected':['MC03-descent-side-v1.png','MC03-exit-v1.png']}
(HERE/'references.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
descriptions={
 'MC00':('城市一镜到底','屋檐 → 横移揭示 → 沿路下降 → 市政落点。当前是四个静态视野，连续运镜、高差与接近路线未通过'),
 'MC01':('市政：控制已断','复用已认可市政片的真实状态，按停与工作灯变化不再生成'),
 'MC02':('市政：工作未停','复用同一已认可片的近景前后态，不另造设备'),
 'MC03':('董文慧：正常下楼','采用新斜侧直梯修订图，另附既有到达站位。早期两张新图的双梯段／方窗问题保留历史，未选作首尾；全程连续性与旧下楼FAIL未关闭'),
 'MC04':('董文慧：推门后又见熟悉痕迹','触门前 → 接触 → 半开 → 线索显露。沿同一右手、左轴、向内推门的候选准备'),
 'MC05':('董文慧：停步核对','同侧保持扶门，先看到差异再反应。静态人物与手别不代替原速表演通过'),
 'MC06':('站台定位：两人仍在','T01远景与B6实际首帧并列。两人位置、手机、包带和棚柱以B6原片为准'),
 'B6':('完整保留B6','完整21.875秒原文件在下方播放，不重做、不重剪、不替换原声、对白或片名'),
 'SUPPORT':('辅助身份与结构','仅为人物身份和几何辅助，不作为正式Shot画面交付')}
nav=''.join(f'<a href="#{s}">{s}</a>' for s in descriptions)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>失帧 完整宏观开场参考</title><style>body{margin:0;background:#101822;color:#e8eff8;font:17px/1.65 system-ui,sans-serif}main{max-width:1450px;margin:auto;padding:32px 24px}h1{font-size:32px}h2{margin:42px 0 8px;font-size:25px}p{color:#becddd}nav{display:flex;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:#101822ef;padding:14px 0;z-index:1}nav a{background:#26384e;color:#d9ecff;text-decoration:none;padding:5px 15px;border-radius:6px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}figure{margin:0;background:#1b2939;border-radius:8px;overflow:hidden}img,video{display:block;width:100%}figcaption{padding:14px 18px}strong{display:block}small{font-size:14px;color:#b1c4d9}section{scroll-margin-top:80px}video{max-height:760px;background:black;margin-top:24px}@media(max-width:800px){.grid{display:block}figure{margin-bottom:20px}}</style><main><h1>《失帧》完整宏观开场参考</h1><p>覆盖MC00–MC06与完整B6。所有新图和旧参考均供静态审看；已认可素材按exact源复用。没有生成新视频，楼梯FAIL和未验证接点保持。</p><nav>'''+nav+'</nav>'
for s,(title,note) in descriptions.items():
    page+=f'<section id="{s}"><h2>{s} · {title}</h2><p>{note}</p><div class="grid">'
    for r in records:
        if r['shot']==s:page+=f'<figure><a href="{r["file"]}"><img loading="lazy" src="{r["file"]}" alt="{html.escape(r["title"])}"></a><figcaption><strong>{html.escape(r["title"])}</strong><small>{html.escape(r["basis"])}</small></figcaption></figure>'
    page+='</div>'
    if s=='B6':
        source=ROOT/'outputs/shizhen-episode01/fusion-B-motion-20261027/variant-ASSEMBLY-B6/失帧-独立开场-ASSEMBLY-B6.mp4'
        page+=f'<video controls preload="metadata" playsinline src="{os.path.relpath(source,HERE)}"></video>'
    page+='</section>'
page+='<p>点击图片查看原尺寸。参考数量与静态外观不证明生成服从、完整行动、声音或连续接点通过。</p></main></html>'
(HERE/'index.html').write_text(page)
print(json.dumps({'static_images':len(records),'shot_groups':list(descriptions),'new_video_calls':0}))
